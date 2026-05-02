"""
Version 3 Bargaining institution
New institutional flow:
- Gather bid orders
- Gather ask orders
- Cross bids and asks
    - Automatically or according to previous decision rule of picking a random agent
- Remove that specific bid/ask order
    - Note agents may have many such orders in the institution at the same time
    - Note each bid and ask will have a unique ID per round now to allow this type of indexing
    - "Remove" here means flag as filled in dataframe

TEMPORARY TODO REMOVE TO NEW INSTITUTION:
- Issues and asks for repayment of LOANS
    - Maybe? TODO here

Changes to datastructures:
- Lots of new data to follow in each bid, ask, and contract
    - Contracts now: property_right, item_type, bid_id, ask_id, 
- Contracts moved from dictionary to pandas dataframe
    - It became too cumbersome otherwise

New necessity of agent logic
- Agents may be shedding many quantities in each round, as many others can purchase their asks, but now agents need to decide if they would like to leave before
the week is up... so movement logic needs to reflect the fact that if you now have had all of your things purchased, you cannot trade this turn - but if you now 
think about leaving v. non-leaving, perhaps does not make sense to leave? - would need to have had quantities that you CAN trade last round and haven't traded ...
- Some more thing to think about here

Bug-fixes
- Replaced round with round_ to not conflict with restricted words
"""

import random as rnd
import pandas as pd
import numpy as np
from institutions.dm_message_model import Message

class Bargain(object):
    """Governs bargaining between agents in self.agents"""
    def __init__(self, rounds, quantity_limit = "HARD", money_limit = "HARD", market_type = "ONE_TYPE", item_types = ("C"), currency_types = ("M"),
        bidding_type = "ABSTRACT", property_rights = "SPOT", week=0, period=0, local_trades_only=True, barg_location=(0, 0), hard_clear=True):
        self.agents = []   # list of agent objects who will bargain
        self.offer_history = []    # list of offer tupples
        contract_columns = ["contract_id", "bid_id", "ask_id", "buyer_id", "seller_id", "placed_location", "accept_location", "property_right", "item_type", 
                            "currency_type", "price", "agent_id", "round", "period", "week", "barg_location"]
        self.contracts = pd.DataFrame(columns=contract_columns)   # dataframe: columns = contract_id, bid_id, ask_id, buyer_id, seller_id, bid_location, ask_location, property_right, item_type, offer_type, currency_type, price, agent_id, round, period, week
        order_columns = ["offer_id", "property_right", "item_type", "offer_type", "currency_type", "price", "agent_id", "location", "filled", "round", 
                        "period", "week", "can_fill"]
        self.order_book = pd.DataFrame(columns=order_columns)  # dataframe: columns = offer_id, property_right, item_type, offer_type, currency_type, price, agent_id, location, filled, round, period, week, can_fill
                              #         offer_type = 'BID', 'ASK'
                              #         filled = True, False (True = not available for trade)
                              #         can_fill = True, False (True indicates placer can fill with currency or quantity)
        self.historical_book = pd.DataFrame(columns=self.order_book.columns)
        self.historical_contract = pd.DataFrame(columns=self.contracts.columns)
        self.agent_arrangement = []  # list of shuffled agents. NOTE: Changed name for clarity

        self.rounds = rounds  # number of rounds of bargaining
        self.debug = False  # used to print information for debugging
        self.quantity_limit = quantity_limit # Can be HARD or SOFT - if hard need to have quantity on-hand to have asks filled
        self.money_limit = money_limit # Can be HARD or SOFT - if hard need to have money on-hand to have bids filled

        self.market_type = market_type # ONE_TYPE or TWO_TYPE - if we are in the one-market or two-market world (C v. X/Y)
        self.item_types = item_types # Note: C is a generic placeholder
        self.currency_types = currency_types # Note: M is a generic placeholder

        self.agent_currency_info = {} # Stores map of agent and currency values. Structure: {agent_id: {currency_type: q}}

        self.agent_quantity_info = {} # Stores map of agent and prop right, item type, 

        self.bidding_type = bidding_type # Can be ABSTRACT or MONETARY - if ABSTRACT uses non-monetary (utility bidding)

        self.property_rights = property_rights.split("_") # TODO change to tuple - but must be being overwritten somewhere - trace
        self.week = week
        self.period = period

        self.local_trades_only = local_trades_only

        self.barg_location = barg_location

        self.agent_lookup = {} # Dict struct: {agent_id: agent_index}

        self.debug2 = False
        self.debug3 = False

        self.hard_clear = True

    def set_location(self, loc):
        self.barg_location = loc
    
    def set_period(self, period):
        self.period = period

    def set_week(self, week):
        self.week = week

    def set_debug(self, flag):
        self.debug = flag
    
    def send_msg(self, agent, msg):
        if self.debug:
            directive = msg.get_directive()
            sender = msg.get_sender()
            receiver = msg.get_receiver()
            payload = msg.get_payload()
            print(f"message sent = {directive} from {sender} to {receiver}, \n {10*' '}{payload}")
        return_msg = agent.process_message(msg)
        return return_msg

    def make_bargaining_order(self):
        """ Shuffles agents and creates self.agent_lookup
            to get index of agent in agent_order"""

        rnd.shuffle(self.agent_arrangement)
        for k, agent in enumerate(self.agent_arrangement):
            name = agent.get_name()
            self.agent_lookup[name] = k

    def process_contract(self, contract_df): # TODO CHECK HERE
        """Remove contract parties offers and inform them that
           they have a contract

            If here, the contract is asserted to be fillable - no issue atm b/c of sequentiality
        """

        # Mark bid/ask as already filled
        c_bid = contract_df["bid_id"].values[0]
        c_ask = contract_df["ask_id"].values[0]
        if c_bid is not None:
            bid_loc = list(self.order_book[self.order_book["offer_id"]==c_bid].index)[0]
            self.order_book["filled"].loc[bid_loc] = True
        if c_ask is not None:
            ask_loc = list(self.order_book[self.order_book["offer_id"]==c_ask].index)[0]
            self.order_book["filled"].loc[ask_loc] = True

        # Reduce/increase quantity and currencies on-hand
        p_right = contract_df['property_right'].values[0]
        i_type = contract_df['item_type'].values[0]
        c_type = contract_df['currency_type'].values[0]
        buyer_id = contract_df['buyer_id'].values[0]
        seller_id = contract_df['seller_id'].values[0]
        cont_price = contract_df['price'].values[0]

        if self.bidding_type == "MONETARY":
            self.agent_currency_info[buyer_id][c_type] -= cont_price
            self.agent_currency_info[seller_id][c_type] += cont_price
        
        # Note - inc(dec)rement by 1 because all offers are for 1 quantity
        self.agent_quantity_info[buyer_id][p_right][i_type] += 1
        self.agent_quantity_info[seller_id][p_right][i_type] -= 1

        # Re-check any bids/asks by the agents involved in the contract to see if they can be filled still 
        bids = self.order_book[(self.order_book["offer_type"]=="BID")&(self.order_book["currency_type"]==c_type)]
        buyer_locs = list(bids[bids["agent_id"]==buyer_id].index)
        for b_loc in buyer_locs:
            o_price = self.order_book["price"].loc[b_loc]
            if o_price > self.agent_currency_info[buyer_id][c_type]:
                self.order_book["can_fill"].loc[b_loc] = False
        
        asks = self.order_book[(self.order_book["offer_type"]=="ASK")&(self.order_book["item_type"]==i_type)&(self.order_book["property_right"]==p_right)]
        seller_locs = list(asks[asks["agent_id"]==seller_id].index)
        for s_loc in seller_locs:
            if self.agent_quantity_info[seller_id][p_right][i_type] == 0:
                self.order_book["can_fill"].loc[s_loc] = False

        # get agent objects
        buyer_agent_index = self.agent_lookup[buyer_id]
        buyer_agent = self.agent_arrangement[buyer_agent_index]
        seller_agent_index = self.agent_lookup[seller_id]
        seller_agent = self.agent_arrangement[seller_agent_index] 

        ext_contract = False
        if ext_contract:
            ## New code to test -- Get extra contract info
            s_cur_unit = seller_agent.get_cur_unit()
            s_costs = seller_agent.get_costs()
            s_cur_cost = s_costs[s_cur_unit]

            b_cur_unit = buyer_agent.get_cur_unit()
            b_values = buyer_agent.get_values()
            b_cur_value = b_values[b_cur_unit]

            round_ = contract_df["round"].values[0]
            
            # save extended contract
            ex_contract = (round_, cont_price, c_bid, c_ask, buyer_id, seller_id, b_cur_unit, b_cur_value, s_cur_unit, s_cur_cost)

        # Send messages to buyer and seller that they have a contract
        msg = Message('CONTRACT', 'BARGAIN', buyer_id, ("BUY", contract_df))
        return_msg = buyer_agent.process_message(msg) # Send to buyer
        msg = Message('CONTRACT', 'BARGAIN', seller_id, ("SELL", contract_df))
        return_msg = seller_agent.process_message(msg)  # Send to seller

        self.contracts = pd.concat([self.contracts, contract_df]).reset_index(drop=True)

        if self.debug:
            print(contract_df)
            test_test = 1

    def reset_order_book(self):
        """Hard-clears the order-book. Allows totally new bargaining to occur."""
        self.order_book = pd.DataFrame(columns=self.order_book.columns)

    def reset_contracts(self):
        """Hard-clears the contracts. Allows totally new period to occur."""
        self.contracts = pd.DataFrame(columns=self.contracts.columns)

    def run(self):
        """Runs bargaining between self.agents
           Accepts BID ASK BUY and SELL messages
           
           Bargaining continues for self.rounds
              Each round agent order is shuffled then
                Each agent makes a BID, ASK BUY or SELL order
                Only the most recent order is kept"""
        
        if self.debug2:
            print("B.01. Ran")

        # Note: Order book resets when Bargain.run is called
        # CAN rest again at every round
        self.reset_order_book()

        if self.hard_clear:
            self.reset_contracts()
        self.agent_arrangement = self.agents

        # Initialize money info for agents
        for agent in self.agent_arrangement:
            agent_id = agent.get_name()
            for c_type in self.currency_types:
                self.agent_currency_info[agent_id] = {c_type: 0}
        
        # Inititalize quantity info for agents
        for agent in self.agent_arrangement:
            agent_id = agent.get_name()
            for p_right in self.property_rights:
                for i_type in self.item_types:
                    self.agent_quantity_info[agent_id] = {p_right: {i_type: 0}}

        if self.debug2:
            print("B.02. Init agent dicts")

        # Added for two-type market
        # Unique ID
        offer_id = 0 # Will increment by 1 for every offer processed - note will reset when run is called

        # Begin Bargaining
        for round_ in range(self.rounds):
            if self.hard_clear:
                self.reset_order_book()

            if self.debug2:
                print(f"B.03. In round {round_}")

            self.make_bargaining_order()

            # Learn Agent Quantities, Currencies
            for agent in self.agent_arrangement:

                # Get agent ID for message sending
                agent_id = agent.get_name()

                # Learn quantity positions
                for p_right in self.property_rights:
                    for i_type in self.item_types:

                        q_req = {'property_right': p_right, 'item_type': i_type}
                        msg = Message('REPORT_QUANTITY', 'BARGAIN', agent_id, q_req)
                        return_msg = self.send_msg(agent, msg)
                        q_val = return_msg.get_payload()
                        # Update quantities
                        self.agent_quantity_info[agent_id][p_right][i_type] = q_val

                if self.bidding_type == "MONETARY":
                    # Learn monetary positions for this agent
                    for c_type in self.currency_types:
                        msg = Message('REPORT_MONEY', 'BARGAIN', agent_id, c_type)
                        return_msg = self.send_msg(agent, msg)
                        c_val = return_msg.get_payload()

                        # Update money info
                        self.agent_currency_info[agent_id][c_type] = c_val
                elif self.bidding_type == "ABSTRACT": # does not use money
                    for c_type in self.currency_types:
                        # Update money info with arbitrarily large quantity - so not limiting
                        self.agent_currency_info[agent_id][c_type] = 999999999999999999999999999

            # Put in Asks and Bids
            for agent in self.agent_arrangement:

                # Get agent ID for message sending
                agent_id = agent.get_name()

                # Request and Get: BID, ASK, BUY or SELL message
                # Querries all markets sequentially - problem? TODO think
                for p_right in self.property_rights:
                    for i_type in self.item_types:
                        for c_type in self.currency_types:

                            # Subset only offfersw with this item and currency
                            these_orders = self.order_book[(self.order_book["property_right"]==p_right)&(self.order_book["item_type"]==i_type)&(self.order_book["currency_type"]==c_type)]
                            offer_payload = {'market_type': self.market_type,
                                            'property_right':p_right,
                                            'item_type': i_type,
                                            'bidding_type': self.bidding_type,
                                            'currency_type': c_type,
                                            'order_book': these_orders
                                            }

                            # Ask for offers
                            msg = Message('OFFER', 'BARGAIN', agent_id, offer_payload) ## TODO trace to agent logic
                            return_msg = self.send_msg(agent, msg)
                            directive = return_msg.get_directive()
                            sender_id = return_msg.get_sender()
                            payload = return_msg.get_payload()

                            # Indicates no offers placed
                            if directive == "NO_OFFER" or directive ==  "NULL":
                                if self.debug3:
                                    print(f"\t{agent_id} did not place offer")
                                # ignore message and continue to next agent
                                continue

                            # New Payload will have many bids/asks - So need to look at each offer within the payload (TODO think - maybe not needed?)

                            # TODO change processing if agents will send back multiple offers - for now NO
                            if directive == "PLACE_OFFER":
                                offr = return_msg.get_payload()
                                offr_price = offr[0]
                                offr_type = offr[1]

                                offr_loc = agent.get_location()
                                
                                # order_columns = ["offer_id", "property_right", "item_type", "offer_type", "currency_type", "price", "agent_id", "location", "filled", "round", 
                                #    "period", "week", "can_fill"]
                                # put order in self.order_book
                                # Assumes all placed offers CAN be filled - this gets checked later when the agent accepts a bid/ask
                                
                                offer = (offer_id, p_right, i_type, offr_type, c_type, offr_price, agent_id, offr_loc, False, round_, self.period, self.week, True)
                                
                                if self.debug3:
                                    print(f"\t{agent_id} placed {offer}")

                                offer_df = pd.DataFrame(columns = self.order_book.columns)
                                offer_df.loc[0] = offer

                                # Add offer to order book
                                self.order_book = pd.concat([self.order_book, offer_df]).reset_index(drop=True)

                                offer_id += 1

            if self.debug:
                print(self.order_book)
                print()

            # Place BUYS and SELLS in each market
            for agent in self.agent_arrangement:
                agent_id = agent.get_name()

                for p_right in self.property_rights:
                    for i_type in self.item_types:
                        for c_type in self.currency_types:
                            
                            # Request and Get: BUY or SELL message
                            this_order_book = self.order_book[(self.order_book["property_right"]==p_right)&(self.order_book["item_type"]==i_type)&(self.order_book["currency_type"]==c_type)]
                            this_order_book = this_order_book[(this_order_book['filled']==False)&(this_order_book['can_fill']==True)] # Exclude Filled and Unfillable
                            this_order_book = this_order_book[this_order_book['agent_id']!=agent_id] # Exclude own-orders
                            send_pld = {'order_book': this_order_book, 
                                        'market_type':self.market_type,
                                        'item_type': i_type,
                                        'property_right': p_right,
                                        'currency_type': c_type,
                                        'bidding_type': self.bidding_type
                                        }

                            msg = Message('TRANSACT', 'BARGAIN', agent_id, send_pld)
                            return_msg = self.send_msg(agent, msg)
                            directive = return_msg.get_directive()
                            sender_id = return_msg.get_sender()
                            payload = return_msg.get_payload()
                            
                            # Process message based on directive
                            if directive == "NULL" or directive=="NO_TRADE":
                                if self.debug3:
                                    print(f"{agent_id} did not trade")
                                # ignore message and continue to next agent
                                continue

                            # TODO change agent decisions to reflect multiple transactions possible - if want
                            if directive == "BUY" or directive == "SELL":
                                offer_id_accepted = payload
                                if self.debug3:
                                    print(f"{agent_id} trade with a {directive} on offer {offer_id_accepted}")
                            
                            this_order = self.order_book[self.order_book["offer_id"]==offer_id_accepted]
                            offer_type = this_order['offer_type'].values[0]

                            # Check the order exists and is the type required
                            try:
                                if directive == "BUY" and offer_type != "ASK": raise ValueError("Cannot buy without an ask")
                                if directive == "SELL" and offer_type != "BID": raise ValueError("Cannot sell without a bid")

                            except (KeyError, ValueError):
                                print(f"The order was not entered correctly or already filled. Sender id {sender_id}; order id {offer_id_accepted}")

                            # Check order is not already filled or flagged as unfillable
                            is_filled = this_order['filled'].values[0]
                            can_fill = this_order['can_fill'].values[0]
                            try:
                                assert is_filled == False
                                assert can_fill == True
                            except AssertionError:
                                continue

                            # Check the agents can complete contract
                            offer_price = this_order['price'].values[0]
                            placer_id = this_order['agent_id'].values[0]
                            
                            #print("Offer_type", offer_type, "by", placer_id, "accept by", agent_id, "for item", i_type)
                            #print("Quants", self.agent_quantity_info)

                            if offer_type == "ASK":
                                # Check buyer can accept ask (cash constraint), and seller can fill (quantity constraint)
                                try:
                                    if self.bidding_type == "MONETARY":
                                        assert self.agent_currency_info[agent_id][c_type] >= offer_price
                                    assert self.agent_quantity_info[placer_id][p_right][i_type] >= 1
                                except AssertionError:
                                    # If now cannot fill, mark as such - redundancy to account for potential lags in processing
                                    if can_fill:
                                        this_order_loc = this_order.index.values[0]
                                        self.order_book['can_fill'].loc[this_order_loc] = False
                                    continue

                                o_ask_id = offer_id_accepted
                                o_bid_id = None
                                o_buyer_id = agent_id
                                o_seller_id = placer_id

                            
                            if offer_type == "BID":
                                # Check seller can accept bid (quantity constraint), and buyer can fill (cash constraint)
                                try:
                                    assert self.agent_quantity_info[agent_id][p_right][i_type] >= 1
                                    if self.bidding_type == "MONETARY":
                                        assert self.agent_currency_info[placer_id][c_type] >= offer_price
                                except AssertionError:
                                    # If now cannot fill, mark as such - redundancy to account for potential lags in processing
                                    if can_fill:
                                        this_order_loc = this_order.index.values[0]
                                        self.order_book['can_fill'].loc[this_order_loc] = False
                                    continue

                                o_ask_id = None
                                o_bid_id = offer_id_accepted
                                o_buyer_id = placer_id
                                o_seller_id = agent_id

                            # Check location constraints
                            offer_location = this_order['location'].values[0] # Currently only used for post-processing
                            cur_loc = agent.get_location()
                            if self.local_trades_only:
                                try:
                                    assert cur_loc == offer_location
                                except AssertionError:
                                    continue
                            
                            # If here, should be fillable and everything 
                            if len(self.contracts) == 0:
                                last_contract_id = -1
                            else:
                                last_contract_id = np.max(self.contracts['contract_id'].values)
                            this_contract_id = last_contract_id + 1

                            this_contract = (this_contract_id, o_bid_id, o_ask_id, o_buyer_id, o_seller_id, offer_location, cur_loc, p_right, i_type, c_type, 
                                            offer_price, agent_id, round_, self.period, self.week, self.barg_location)

                            # For backwards compatibility
                            if directive=="BUY":
                                self.offer_history.append((round_, o_buyer_id, "BUY", offer_price))
                            elif directive=="SELL":
                                self.offer_history.append((round_, o_seller_id, "SELL", offer_price))
                            else:
                                return Message('BAD', agent.get_name(), 'BARGAIN',
                                            "Unrecognized Directive") 
                            
                            contract_df = pd.DataFrame(columns=self.contracts.columns)
                            contract_df.loc[0] = this_contract
                            self.process_contract(contract_df)

        if self.debug:
            print(self.contracts)
            test_test = 1

    def set_agents(self, agents):
        self.agents = agents
    
    def get_offer_history(self):
        return self.offer_history
    
    def get_contracts(self):
        return self.contracts
    
    def get_prices(self, typ, name, item_assoc=None):
        """Get all contract prices in order for a trader"""
        if typ == "BUYER":
            re_contracts = self.contracts[self.contracts["buyer_id"]==name]
            prices = list(re_contracts['price'].values)
        elif typ == "SELLER":
            re_contracts = self.contracts[self.contracts["seller_id"]==name]
            prices = list(re_contracts['price'].values)
        elif typ == "TRADER":
            assert item_assoc is not None
            buy_i = item_assoc["buy_item"]
            buy_cont = self.contracts[self.contracts["item_type"]==buy_i]
            buy_prices = list(buy_cont[buy_cont["buyer_id"]==name]["price"].values)

            sell_i = item_assoc["sell_item"]
            sell_cont = self.contracts[self.contracts["item_type"]==sell_i]
            sell_prices = list(sell_cont[sell_cont["seller_id"]==name]["price"].values)

            prices = {buy_i: buy_prices, sell_i: sell_prices}

        return prices

    def print_payoffs(self, save_to_file=False, file_name="agent_payoff_base"):
        print(f"PAYOFFS")
        print("--------")
        payoff_dict = {"agent_id": [], "agent_type":[], "agent_payoff":[]}
        for agent in self.agents:
            if agent.type == "BUYER":
                prices = self.get_prices(agent.type, agent.name)
                utility = agent.get_payoff(prices)
                print(f"Buyer {agent.name} has a utility {utility}")

            if agent.type == "SELLER":
                prices = self.get_prices(agent.type, agent.name)
                profit = agent.get_payoff(prices)
                print(f"Seller {agent.name} has a profit {profit}")
            
            if agent.type == "TRADER":
                item_assoc = {"buy_item":agent.item_buyer, "sell_item":agent.item_seller}
                prices_bs = self.get_prices(agent.type, agent.name, item_assoc=item_assoc)
                payoff = agent.get_payoff(prices=None, currency="M", prices_bs=prices_bs)
                print(f"Trader {agent.name} has a payoff of {payoff}")
            
            payoff_dict["agent_id"] = agent.name
            payoff_dict["agent_type"] = agent.type
            payoff_dict["agent_payoff"] = payoff

        payoff_df = pd.DataFrame(payoff_dict)

        if save_to_file:
            file_name_out = file_name+"_at_" + self.barg_location[0] + "_" + self.barg_location[1] +".csv"
            payoff_df.to_csv(file_name_out)

        return payoff_df