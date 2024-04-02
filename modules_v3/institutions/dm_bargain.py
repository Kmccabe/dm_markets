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
        - So the order book is now indexed by {order_id: type, price, agent} (all for quantity of 1 - avoids odd-lots problem)
        - And another directory maps agent-to-order, too

New necessity of agent logic
- Agents may be shedding many quantities in each round, as many others can purchase their asks, but now agents need to decide if they would like to leave before
the week is up... so movement logic needs to reflect the fact that if you now have had all of your things purchased, you cannot trade this turn - but if you now 
think about leaving v. non-leaving, perhaps does not make sense to leave? - would need to have had quantities that you CAN trade last round and haven't traded ...
- Some more thing to think about here
"""

import random as rnd
from institutions.dm_message_model import Message

class Bargain(object):
    """Governs bargaining between agents in self.agents"""
    def __init__(self, rounds, quantity_limit = "HARD", money_limit = "HARD", market_type = "ONE_TYPE", market_items = "C", currency_types = "M",
        bidding_type = "ABSTRACT"):
        self.agents = []   # list of agent objects who will bargain
        self.offer_history = []    # list of offer tupples
        self.contracts = []   # list of contract tupples
        self.order_book = {}  # dictionary key= order_id, 
                              #          value = [(type, price, agent_id), ...]
                              #          type = 'BID', 'ASK'
        self.agent_order_map = {} # Maps agent -> [order, ...]
        self.agent_order = []  # list of shuffled agents
        self.agent_lookup = {} # dictionary key=trader_id, 
                               #         value = index into agent_order
        self.rounds = rounds  # number of rounds of bargaining
        self.debug = False  # used to print information for debugging
        self.quantity_limit = quantity_limit # Can be HARD or SOFT - if hard need to have quantity on-hand to have asks filled
        self.money_limit = money_limit # Can be HARD or SOFT - if hard need to have money on-hand to have bids filled

        self.market_type = market_type # ONE_TYPE or TWO_TYPE - if we are in the one-market or two-market world (C v. X/Y)
        self.market_items = list(market_items) # Note: C is a generic placeholder
        self.currency_types = list(currency_types) # Note: M is a generic placeholder

        self.bidding_type = bidding_type # Can be ABSTRACT or MONETARY - if ABSTRACT uses non-monetary (utility bidding)
        
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

        rnd.shuffle(self.agent_order)
        for k, agent in enumerate(self.agent_order):
            name = agent.get_name()
            self.agent_order_map[name] = {} # Will have id's of contracts
            self.agent_lookup[name] = k 

    def process_contract(self, acceptor_id, order_id): # TODO CHECK HERE
        """Remove contract parties offers and inform them that
           they have a contract"""

        #self.contracts.append(contract)  Moved down
        round, price, bid_id, ask_id, buyer_id, seller_id = contract


        # cancel orders after contract
        # buyer_id = self.order_book[bid_id][3]
        # seller_id = self.order_book[ask_id][3]

        # Cancel the bid and ask after they are crossed
        self.order_book[bid_id] = None
        self.order_book[ask_id] = None

        # get agent objects
        buyer_agent_index = self.agent_lookup[buyer_id]
        buyer_agent = self.agent_order[buyer_agent_index]
        seller_agent_index = self.agent_lookup[seller_id]
        seller_agent = self.agent_order[seller_agent_index] 

        ## New code to test -- Get extra contract info
        s_cur_unit = seller_agent.get_cur_unit()
        s_costs = seller_agent.get_costs()
        s_cur_cost = s_costs[s_cur_unit]

        b_cur_unit = buyer_agent.get_cur_unit()
        b_values = buyer_agent.get_values()
        b_cur_value = b_values[b_cur_unit]

        # Send messages to buyer and seller that they have a contract
        msg = Message('CONTRACT', 'BARGAIN', buyer_id, contract)
        return_msg = buyer_agent.process_message(msg) # Send to buyer
        msg = Message('CONTRACT', 'BARGAIN', seller_id, contract)
        return_msg = seller_agent.process_message(msg)  # Send to seller

        # save extended contract
        ex_contract = (round, price, bid_id, ask_id, buyer_id, seller_id, b_cur_unit, b_cur_value, s_cur_unit, s_cur_cost)
        self.contracts.append(ex_contract)

        if self.debug:
            print(contract)
            print(ex_contract)
        test_test = 1

    def run(self):
        """Runs bargaining between self.agents
           Accepts BID ASK BUY and SELL messages
           
           Bargaining continues for self.rounds
              Each round agent order is shuffled then
                Each agent makes a BID, ASK BUY or SELL order
                Only the most recent order is kept"""
        
        # Note: Order book resets when Bargain.run is called, and again at every round
        self.agent_order = self.agents
        self.order_book = {}
        self.contracts = []
        self.agent_order_map = {}
        offer_id = 0 # Will increment by 1 for every offer processed - note will reset when run is called

        # Begin Bargaining
        for round in range(self.rounds):
            self.make_bargaining_order()
            for agent in self.agent_order:

                # Get agent ID for message sending
                agent_id = agent.get_name()

                # Learn quantity positions
                # Learn monetary positions
                msg = Message('OFFER', 'BARGAIN', agent_id, {'order_book': self.order_book, 'item_type': market_type}) ## TODO trace to agent logic
                

                # Request and Get: BID, ASK, BUY or SELL message
                msg = Message('OFFER', 'BARGAIN', agent_id, self.order_book) ## TODO trace to agent logic
                return_msg = self.send_msg(agent, msg)
                directive = return_msg.get_directive()
                sender_id = return_msg.get_sender()
                payload = return_msg.get_payload()
                #print(f"{sender_id}  {directive}  {payload}")

                # Indicates no offers placed
                if directive == "NULL":
                    # ignore message and continue to next agent
                    continue

                # New Payload will have many bids/asks - So need to look at each offer within the payload

                # TODO change agent processing so that agents will send back multiple offers
                for offr in payload:
                    offr_type = offr['type']
                    offr_price = offr['price']

                    # put order in self.order_book
                    offer = (offr_type, offr_price, sender_id)

                    self.order_book[offer_id] = offer
                    self.offer_history.append((round, offer_id, offr_type, offr_price, sender_id))

                    offer_id += 1

            if self.debug:
                for agent in self.agent_order:
                    print(f"{self.order_book[agent.get_name()]}", end = " ")
                print()

            for agent in self.agent_order:

                # Request and Get: BID, ASK, BUY or SELL message
                agent_id = agent.get_name()
                msg = Message('TRANSACT', 'BARGAIN', agent_id, self.order_book)
                return_msg = self.send_msg(agent, msg)
                directive = return_msg.get_directive()
                sender_id = return_msg.get_sender()
                payload = return_msg.get_payload()

                # Process message based on directive
                if directive == "NULL":
                    # ignore message and continue to next agent
                    continue

                # TODO change agent decisions to reflect multiple transactions possible 
                for trnsct in payload:
                    trnsct_type = trnsct['type']
                    trnsct_order_id = trnsct['order_id']

                    # Check the order exists and is the type required
                    try:
                        order_type = self.order_book[trnsct_order_id][0]
                        order_price = self.order_book[trnsct_order_id][1]
                        order_placer_id = self.order_book[trnsct_order_id][2]

                        if trnsct_type == "BUY" and order_type != "ASK": raise ValueError("Cannot buy without an ask")
                        if trnsct_type == "SELL" and order_type != "BID": raise ValueError("Cannot sell without a bid")

                    except (KeyError, ValueError):
                        print(f"The order was not entered correctly or already filled. Sender id {sender_id}; order id {trnsct_order_id}")

                    

                    if trnsct_type == "BUY":
                        # make contract if possible
                        buyer_id = sender_id  
                        seller_id = payload
                        if self.order_book[seller_id] == None:
                            # cannot make contract continue to next agent
                            continue
                        # process contract
                        price = self.order_book[seller_id][1]
                        self.offer_history.append((round, buyer_id, "BUY", price))
                        contract = (round, price, buyer_id, seller_id)
                        self.process_contract(contract)
                    elif directive == "SELL":
                        seller_id = sender_id  # Get Mappings to buyer_id and seller_id
                        buyer_id = payload
                        if self.order_book[buyer_id] == None:
                            # cannot contract continue to next agent
                            continue
                        # process contract
                        price = self.order_book[buyer_id][1]
                        self.offer_history.append((round, seller_id, "SELL", price))
                        contract = (round, price, buyer_id, seller_id)
                        self.process_contract(contract)
                    else:
                        return Message('BAD', agent.get_name(), 'BARGAIN',
                                    "Unrecognized Directive") 
        if self.debug:
            print(self.contracts)
        test_test = 1

    def set_agents(self, agents):
        self.agents = agents
    
    def get_offer_history(self):
        return self.offer_history()
    
    def get_contracts(self):
        return self.contracts
    
    def get_prices(self, typ, name):
        """Get all contract prices in order for a trader"""
        prices = []
        for contract in self.contracts:
            round_t, price, buyer_id, seller_id = contract
            if typ == "BUYER":
                if name == buyer_id:
                    prices.append(price)
            elif typ == "SELLER":
                if name == seller_id:
                    prices.append(price)
        return prices

    def print_payoffs(self):
        print(f"PAYOFFS")
        print("--------")
        for agent in self.agents:
            if agent.type == "BUYER":
                prices = self.get_prices(agent.type, agent.name)
                utility = agent.get_payoff(prices)
                print(f"Buyer  {agent.name} has utility {utility}")
        for agent in self.agents:
            if agent.type == "SELLER":
                prices = self.get_prices(agent.type, agent.name)
                profit = agent.get_payoff(prices)
                print(f"Seller {agent.name} has profit  {profit}")

    