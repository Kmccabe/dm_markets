import random as rnd
from institutions.dm_message_model import Message

class Bargain(object):
    """Governs bargaining between agents in self.agents"""
    def __init__(self, rounds, bargain_hist_inst = None, round_broadcasts = False):
        self.agents = []   # list of agent objects who will bargain
        self.offer_history = []    # list of offer tuples # TODO: Deprecate
        self.contracts = []   # list of contract tuples
        self.order_book = {}  # dictionary key=trader_id, 
                              #          value = (type, amount)
                              #          type = 'BID', 'ASK' 
        self.agent_order = []  # list of shuffled agents
        self.agent_lookup = {} # dictionary key=trader_id, 
                               #         value = index into agent_order
        self.rounds = rounds  # number of rounds of bargaining
        self.debug = False  # used to print information for debugging

        # Flag to broadcast price information during bargaining (local learning)
        self.round_broadcasts = round_broadcasts

        # Institution for tracking bargaining history through the experiment
        self.bargain_hist_inst = bargain_hist_inst
        
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
            self.order_book[name] = None
            self.agent_lookup[name] = k  

    def process_contract(self, contract):
        """Remove contract parties offers and inform them that
           they have a contract"""

        #self.contracts.append(contract)  Moved down
        round, price, buyer_id, seller_id = contract

        # cancel orders after contract 
        self.order_book[buyer_id] = None
        self.order_book[seller_id] = None

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
        #ex_contract = (round, price, buyer_id, seller_id, b_cur_unit, b_cur_value, s_cur_unit, s_cur_cost)

        # get locations of contracting agents
        b_location = buyer_agent.get_location()
        s_location = seller_agent.get_location()

        # save (even more) extended contract
        ex_contract = (round, price, buyer_id, seller_id, b_cur_unit, b_cur_value, s_cur_unit, s_cur_cost, b_location, s_location)
        self.contracts.append(ex_contract)

        if self.debug:
            print(contract)
            print(ex_contract)
        test_test = 1

    def run(self, week=-1, period=-1):
        """Runs bargaining between self.agents
           Accepts BID ASK BUY and SELL messages
           
           Bargaining continues for self.rounds
              Each round agent order is shuffled then
                Each agent makes a BID, ASK BUY or SELL order
                Only the most recent order is kept"""
        
        self.agent_order = self.agents.copy()
        self.order_book = {}
        self.contracts = []
        
        # Begin Bargaining
        for round in range(self.rounds):
            self.make_bargaining_order() # Shuffle order of agent activation

            # If allowing learning between rounds, save round-level histories
            if self.round_broadcasts:
                round_offers = []
                round_contracts = []

            # Offer step - agents put in BID/ASK offers
            for agent in self.agent_order:

                # Request and Get: BID, ASK, BUY or SELL message
                agent_id = agent.get_name()
                msg = Message('OFFER', 'BARGAIN', agent_id, self.order_book)
                return_msg = self.send_msg(agent, msg)
                directive = return_msg.get_directive()
                sender_id = return_msg.get_sender()
                payload = return_msg.get_payload()
                #print(f"{sender_id}  {directive}  {payload}")
                # Process message based on directive
                if directive == "NULL":
                    # ignore message and continue to next agent
                    continue
                elif directive == "BID" or directive == "ASK":
                    # Get unique (or pseudo-unique) id for offer
                    if self.bargain_hist_inst is not None:
                        offer_id = self.bargain_hist_inst.get_offer_id()
                    else:
                        offer_id = rnd.randint(0, 1000000)
                    loc = agent.get_location()

                    # put offer in self.order_book
                    # replaces and previous offer of this agent
                    if directive == "BID":
                        offer = ("BID", payload, offer_id)
                        offer_type = "BID"
                    elif return_msg.get_directive() == "ASK":
                        offer = ("ASK", payload, offer_id)
                        offer_type = "ASK"
                    self.order_book[sender_id] = offer

                    self.offer_history.append(offer)

                    offer_full = (round, sender_id, offer_type, payload, offer_id, loc, week, period,
                                  False, # indicate if this offer was accepted
                                  False) # indicate if this is the last offer - changed by bargaining history institution when location closes

                    # Send to bargain history inst if present
                    if self.bargain_hist_inst is not None:
                        self.bargain_hist_inst.add_offers([offer_full])

                    # Record offers this round
                    if self.round_broadcasts:
                        round_offers.append(offer_full)

                else:
                    return Message('BAD', agent.get_name(), 'BARGAIN',
                                   "Unrecognized Directive")
            
            # Prints order book
            if self.debug:
                for agent in self.agent_order:
                    print(f"{self.order_book[agent.get_name()]}", end = " ")
                print()

            # Contracting step - agents accept offers with BUY/SELL messages
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
                elif directive == "BUY" or directive == "SELL":
                    # Get unique (or pseudo-unique) id for contract
                    if self.bargain_hist_inst is not None:
                        contract_id = self.bargain_hist_inst.get_contract_id()
                    else:
                        contract_id = rnd.randint(0, 1000000)
                    loc = agent.get_location()

                    if directive == "BUY":
                        # make contract if possible
                        buyer_id = sender_id  
                        seller_id = payload
                        if self.order_book[seller_id] == None:
                            # cannot make contract continue to next agent
                            continue
                        # process contract
                        price = self.order_book[seller_id][1]
                        offer_id = self.order_book[seller_id][2]
                        self.offer_history.append((round, buyer_id, "BUY", price))

                    elif directive == "SELL":
                        seller_id = sender_id  # Get Mappings to buyer_id and seller_id
                        buyer_id = payload
                        if self.order_book[buyer_id] == None:
                            # cannot contract continue to next agent
                            continue
                        # process contract
                        price = self.order_book[buyer_id][1]
                        offer_id = self.order_book[buyer_id][2]
                        self.offer_history.append((round, seller_id, "SELL", price))
                    
                    contract = (round, price, buyer_id, seller_id)

                    contract_full = (round, price, 
                                        buyer_id, seller_id, 
                                        offer_id, contract_id, 
                                        loc, # TODO: Allow location to be different for buyer and seller - add these at offer level
                                        week, period,
                                        False) # indicate if this is the last contract - changed by bargaining history institution when location closes

                    # Send to bargain history inst if present
                    if self.bargain_hist_inst is not None:
                        # Log full contract in bargain history inst.
                        self.bargain_hist_inst.add_contracts([contract_full])
                        self.bargain_hist_inst.indicate_accepted(offer_id)
                    
                    # Record contracts this round
                    if self.round_broadcasts:
                        round_contracts.append(contract_full)

                    # Process contract, transfer items
                    self.process_contract(contract)
                else:
                    return Message('BAD', agent.get_name(), 'BARGAIN',
                                   "Unrecognized Directive")
                
            # If desired, broadcast the results of bargaining at the round level, so agents can update their beliefs for the next round of bargaining
            if self.round_broadcasts:
                self.send_round_history(round_offers, round_contracts)
            
        # Close bargaining history for this period in this location
        # TODO: Allow different location for buyer and seller - here would need to determine which "side" is the side of record
        if self.bargain_hist_inst is not None:
            self.bargain_hist_inst.close_location_record(period, week, loc)
        
        # Reset the local-level round bargaining history for agents at the end of the period
        if self.round_broadcasts:
            for ag in self.agent_order:
                ag.reset_round_bargain_history()

        if self.debug:
            print(self.contracts)
        test_test = 1

        # TODO: Here can add broadcasting contracts locally and adding them to the global history; then global history would need to broadcast them when bargain step is over - but allows only broadcasting locally at the period-level. If want round-level, need to nest 1 deeper, then cannot make it equivalent across locations and globally w/o freezing the bargain institutions
        # Can have interesting question here - local v. global learning. If we broadcast the local prices at the round-level and global at the period-level, can learn quicker local v. global prices


    def send_round_history(self, round_offers, round_contracts):
        """Send the round history (offers and contracts) to the agents."""

        for agent in self.agent_order:
            agent.set_round_history(round_offers, round_contracts)

    def set_agents(self, agents):
        self.agents = agents
    
    def get_offer_history(self):
        # TODO: Deprecate
        return self.offer_history()
    
    def get_contracts(self):
        return self.contracts
    
    def get_prices(self, typ, name):
        """Get all contract prices in order for a trader"""
        prices = []
        for contract in self.contracts:
            round_t, price, buyer_id, seller_id = contract
            if typ == "BUYER" or typ == "B":
                if name == buyer_id:
                    prices.append(price)
            elif typ == "SELLER" or typ == "S":
                if name == seller_id:
                    prices.append(price)
        return prices

    def print_payoffs(self):
        print(f"PAYOFFS")
        print("--------")
        for agent in self.agents:
            if agent.type == "BUYER" or agent.type == "B":
                prices = self.get_prices(agent.type, agent.name)
                utility = agent.get_payoff(prices)
                print(f"Buyer  {agent.name} has utility {utility}")
        for agent in self.agents:
            if agent.type == "SELLER" or agent.type == "S":
                prices = self.get_prices(agent.type, agent.name)
                profit = agent.get_payoff(prices)
                print(f"Seller {agent.name} has profit  {profit}")

    