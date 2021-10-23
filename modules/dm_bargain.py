import random as rnd
from dm_message_model import Message

class Bargain(object):
    """Governs bargaining between agents in self.agents"""
    def __init__(self, rounds):
        self.agents = []   # list of agent objects who will bargain
        self.offer_history = []    # list of offer tupples
        self.contracts = []   # list of contract tupples
        self.order_book = {}  # dictionary key=trader_id, 
                              #          value = (type, amount)
                              #          type = 'BID', 'ASK' 
        self.agent_order = []  # list of shuffled agents
        self.agent_lookup = {} # dictionary key=trader_id, 
                               #         value = index into agent_order
        self.rounds = rounds  # number of rounds of bargaining
        self.debug = False  # used to print information for debugging
        
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
        ex_contract = (round, price, buyer_id, seller_id, b_cur_unit, b_cur_value, s_cur_unit, s_cur_cost)
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
        
        self.agent_order = self.agents
        self.order_book = {}
        self.contracts = []
        
        # Begin Bargaining
        for round in range(self.rounds):
            self.make_bargaining_order()
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
                elif directive == "BID":
                    # put BID in self.order_book
                    offer = ("BID", payload)
                    self.order_book[sender_id] = offer
                    self.offer_history.append((round, sender_id, "BID", payload)) 
                elif return_msg.get_directive() == "ASK":
                    # put ask in self.order_book
                    offer = ("ASK", payload)
                    self.order_book[sender_id] = offer
                    self.offer_history.append((round, sender_id, "ASK", payload))
                else:
                    return Message('BAD', agent.get_name(), 'BARGAIN',
                                   "Unrecognized Directive")
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
                elif directive == "BUY":
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

    