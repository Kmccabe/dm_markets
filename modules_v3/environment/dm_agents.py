"""
Version 3 Trader Agents
Added in this version:
- TRADER type traders can now submit both bids and asks
- Traders have a current quantity (of stored or available-to-trade items) (self.quantities)
    - Structure {"property_right": {"item_type": q}}
    - Items are in a nested dictionary
    - Types of property rights: [SPOT, RENT, DURABLE]
    - Types of items: [C, X, Y] - C is a generic, all users would have util/can produce, [X, Y] are two seperate two-sided markets
- Traders have value structures for utility items as a dictionary (self.valuations)
    - Structure: {"property_right": {"item_type": [uX1, uX2, uX3, ...]}}
    - Note: Base utilities (stored here) are for SPOT consumption - other utilities are computed
        - The current utility positiion is the sum of the least
- Traders have a currency position for all currencies (assumed 0 otherwise) (self.currencies)
    - Structure: {"currency_type": q} 
- Traders have a reputation token position - this is a more general reputation, a global reputation, that the agent has
    - Note: there are many reputation positions with each Node X Agent having a particular reputation
    - The global default reputation can be controlled here - or it would in any case be one way to do this

In future versions:
- Traders have a mental map of the world and their position in it
    - They know the shape of the world (i.e. map) and their position
    - They remember their path and nodes they have encountered
    - They add recent information onto this map - like prices in other markets, or from other agents
- Traders can employ more advanced movement logic
    - They can path towards a particular area (adds additional weight for those directions)
- Traders may spontaneously move randomly
    - Either locally or choose a spontaneous other point to path towards
    - Controlled by an exogenous random error parameter
"""

import random as rnd
import numpy as np
from institutions.dm_message_model import Message
#from dm_zida import ZIDA

class Trader(object):
    """Base class for Buyers or Seller Agents
       Decision making is provided by a child class where 
       overridden methods are those called in process_message
    """
    
    def __init__(self, name, trader_type="TRADER", payoff=None, money=0, location=(0, 0),
                 lower_bound = 0, upper_bound = 9999, item_buyer="C", item_seller="C", default_rep=100):
        """ name = name of trader
            trader_type = BUYER or SELLER
            payoff = payoff function: utility or profit
            location = starting location of trader
        """
        self.debug = False
        self.name = name          # unique identifier 
        self.type = trader_type   # BUYER or SELLER or TRADER (Trader can place buys and sells - but can have especific perscribed types they sell or buy)
        self.payoff = payoff  # utility or profit function
        self.money = money        # starting money ballance - Note this is superseeded by local currencies dict when local currencies employed
        self.location = location  # starting location a tuple (x, y)
        self.lower_bound = lower_bound # on bids, asks, prices, values, costs
        self.upper_bound = upper_bound # on above

        self.values = []  # BUYER values are set by self.set_values(list) 
        self.costs = []   # SELLER costs are set by self.set_costs(list)
        self.units_transacted = 0  # Number of units bought or sold
        self.cur_unit = 0     # current unit looking to buy or sell
        self.max_units = 0    # length of values or costs

        self.contracts = []   # list of contracts
        self.valid_directives = ["START", "MOVE_REQUESTED", "OFFER", "TRANSACT", "CONTRACT", "REPORT_QUANTITY", "REPORT_MONEY", "REQUEST_MONEY", "REPAY_LOAN"]
        #TODO: make directives lower case (maybe)
        self.simulation = None    # get access to class SimulateMarket
        #TODO: explain above better and why the flag below
        self.contract_this_period = False
        self.num_at_loc = 0

        # NOTE: for PRODUCTION decisions these quantities also reflect ability-to-produce - so it is similar to the previous approach
        # Also means the quantities start at the max-units for sellers of an item
        self.quantities = {}

        # Stores current quantities of local currencies at the disposal of the agent - if not-in-dictionary, presumed 0
        self.currencies = {}

        # Stores valuations of all the types of items the agent can buy/sell
        self.valuations = {}
        self.item_buyer = item_buyer
        self.item_seller = item_seller

        self.rep_tokens = default_rep
    
    def __repr__(self):
        s = f"{self.name:10} {self.type:6} @{str(self.location)}:"
        if self.type == "BUYER":
            for k, value in enumerate(self.values):
                if k == 0:
                    s = s + f"[{value:5},"
                elif k == self.max_units-1:
                    s = s + f"{value:5}]"
                else:
                    s = s + f"{value:5},"
        elif self.type == "SELLER":
            for k, cost in enumerate(self.costs):
                if k == 0:
                    s = s + f"[{cost:5},"
                elif k == self.max_units-1:
                    s = s + f"{cost:5}]"
                else:
                    s = s + f"{cost:5},"
        elif self.type == "TRADER":
            return f"""STILL WORKING ON REPRESENTING TRADERS EXACTLY: But this ID is {self.name}, seller of {self.item_seller}, buyer of {self.item_buyer}, 
                    vals for buying items: {self.valuations["SPOT"][self.item_seller]}, vals for selling items {self.valuations["SPOT"][self.item_buyer]},
                    current quantities {self.quantities}, current currencies {self.currencies}, current location {self.location}"""
        s = s + f"cu = {self.cur_unit}"
        return s

    def help(self):
        print("strategy - ZID")
        print("period move: randomly one step")
        print("round offer: bid ~ [lower_bound, current_value]") 
        print("             ask ~ [current_cost, upper_bound]") 
    
    #TODO: Check on this.  Is it needed.
    def get_simulation(self, simulation):
        self.simulation = simulation
        return self.simulation

    def set_debug(self, flag):
        self.debug = flag

    def set_contract_this_period(self, flag):
        self.contract_this_period = flag
 
    def set_values(self, v):
        """
        Set self.values for buyer from list v 
        """
        self.values = v
        self.max_units = len(v) 
        self.cur_unit = 0 
    
    def set_costs(self, c):
        """
        Set self.costs for seller from list c 
        """
        self.costs = c
        self.max_units = len(c)
        self.cur_unit = 0
        
    def set_location(self, loc):
        """
        Set traders location  
        """
        self.location = loc
        
    def set_units_transacted(self, q):
        """
        Set number of units bought or sold by trader
        """
        self.units_transacted = q

    def set_num_at_loc(self, q):
        """Set number of agents at location"""
        self.num_at_loc = q
        
    def received_msg(self, msg):
        if self.debug:
            directive, sender, receiver, payload = msg.unpack()
            print(f" * message received = {directive} from {sender} to {receiver}, \n {10*' '}{payload}")
     
    def returned_msg(self, msg):
        if self.debug:
            directive, sender, receiver, payload = msg.unpack()
            print(f" ** message returned = {directive} from {sender} to {receiver}, \n {10*' '}{payload}")
           
    def process_message(self, message):
        """Process message and call corresponding method
           returns new message to caller"""
        self.received_msg(message)
        me = message.get_receiver()
        sender = message.get_sender()
        
        if me != self.name:
            return_msg = Message("Bad", self.name, sender, "01 Wrong Receiver")
            self.returned_msg(return_msg)
            return return_msg
        directive = message.get_directive()
        if directive not in self.valid_directives:
            return_msg = Message("Bad", self.name, sender, f"02 Unexpected Directive - {directive}")
            self.returned_msg(return_msg)
            return return_msg
        
        payload = message.get_payload()
        if directive == "START":
            msg = self.start(payload)
        elif directive == "MOVE_REQUESTED":
            msg = self.move_requested(payload)
        elif directive == "OFFER":
            msg = self.offer(payload)
        elif directive == "TRANSACT":
            msg = self.transact(payload)
        elif directive == "CONTRACT":
            msg = self.contract(payload)
        elif directive == "REPORT_QUANTITY":
            msg = self.report_quantity(payload)
        elif directive == "REPORT_MONEY":
            msg = self.report_money(payload)
        elif directive == "REQUEST_MONEY":
            msg = self.request_money(payload)
        elif directive == "REPAY_LOAN":
            msg = self.repay_loan(payload)

        self.returned_msg(msg)
        return(msg)
          
    def start(self, payload):
        """
        Overridden by child
        """
        pass
        return Message("Stub", self.name, self.name, "02 from start")

    def move_requested(self, pl):
        """Overridden by child
        """
        pass
        return Message("Stub", self.name, self.name, "03 Stub from move_requested")
    
    def get_name(self):
        return self.name
    
    def get_payoff(self, prices):
        if self.type == "BUYER":
            utility = self.payoff(self.units_transacted, self.money, self.values, prices)
            return utility
        if self.type == "SELLER":
            profit = self.payoff(self.units_transacted, self.money, self.costs, prices)
            return profit
        
    def get_location(self):
        return self.location
    
    def get_values(self):
        return self.values
    
    def get_costs(self):
        return self.costs
    
    def get_units_transacted(self):
        return self.units_transacted

    def get_type(self):
        return self.type
    
    def get_num_units(self):
        return self.max_units
    
    def get_cur_unit(self):
        return self.cur_unit

    def report_quantity(self, payload):
        """Returns the amount of the item type with that property right this agent owns"""
        p_right = payload['property_right']
        item_type = payload['item_type']
        try:
            return_val = self.quantities[p_right][item_type]
        except KeyError:
            if p_right in self.quantities.keys():
                self.quantities[p_right][item_type] = 0
            else:
                self.quantities[p_right] = {}
                self.quantities[p_right][item_type] = 0
            return_val = 0

        return_msg = Message(p_right+"|"+item_type, self.name, "REPORT_QUANTITY", return_val)
        return return_msg
    
    def request_money(self, payload):
        """Request currency moneys - total requested is the total amount of money required to purchase all buy-desired at a valuation of util-currency of 1"""
        cur_type = payload # What currency to request

        # Add up values this agent wants to buy and request that much currency
        if self.type == "TRADER":
            # See current currency position 
            try:
                cur_val = self.currencies[cur_type]
            except KeyError:
                self.currencies[cur_type] = 0
                cur_val = 0

            total_desire = sum(self.valuations[self.item_buyer]) # the total desired is total willing to spend on buying items
            req_desire = total_desire - cur_val

        # Currently all moneys are effectively local because they cannot be transported or communicated at a distance - so just using M type right now
        return_msg = Message(cur_type, self.name, "REQUEST_MONEY", req_desire)
        return return_msg

    def report_money(self, payload):
        """Returns the amount of currency of this type this agent owns"""
        cur_type = payload['currency']
        try:
            return_val = self.currencies[cur_type]
        except KeyError:
            self.currencies[cur_type] = 0
            return_val = 0

        return_msg = Message(cur_type, self.name, "REPORT_MONEY", return_val)
        return return_msg

    def repay_loan(self, payload):
        """Returns the requested currency to the currency issuer - currently returns the TOTAL amount of the currency, not just how much was borrowed
            This simplifying assumption alows us to not worry about monetary inflation, only worrying about real prices"""
        cur_type = payload # Currently - repays ALL of the given currency - allows us to not worry about inter-period inflation and only care about real prices
        try:
            onhand_currency = self.currencies[cur_type]
        except KeyError:
            self.currencies[cur_type] = 0
            onhand_currency = 0
        
        return_msg = Message(cur_type, self.name, "REPAY_LOAN", onhand_currency)
        return return_msg


class ZID(Trader):
    """ 
        Zero Intelligence variant for decentralized market
        a budget constrained ZI 
    """
    
    def start(self, pl):
        """
        Sets up values for trading
        Does not use payload - pl
        """
        self.units_transacted = 0
        self.cur_unit = 0
        if self.type == "BUYER":
            self.max_units = len(self.values)
        else:
            self.max_units = len(self.costs)
        return_msg = Message("Initial", self.name, self.name, "Initialized")
        self.returned_msg(return_msg)
        return return_msg

    def move_requested(self, pl):
        """
        Make a move in a random direction if you can still trade 
        """
        self.contract_this_period = False  # Use this to see if you get a contract this period
        direction_list = [-1, 0, +1] # 
        if self.cur_unit > self.max_units:
            return_msg = Message("MOVE", self.name, "Travel", (0, 0))
            self.returned_msg(return_msg)
            return return_msg 
        else:
            x_dir = rnd.choice(direction_list)
            y_dir = rnd.choice(direction_list)
            return_msg = Message("MOVE", self.name, "Travel", (x_dir, y_dir))
            self.returned_msg(return_msg)
            return return_msg 

    def offer(self, pl):
        """
        Make a bid or ask 
        """
        if self.debug:
            print(f"-- {self.name} has {self.units_transacted} of {self.max_units}")
            print(f"-- {self.name} working on unit {self.cur_unit}")
        if self.cur_unit >= self.max_units:
            return_msg = Message("NULL", self.name, "BARGAIN", None)
            self.returned_msg(return_msg)
            return return_msg
            
        current_offers = pl  # payload from bargain, self.order_book
        
        if self.type == "BUYER":
            WTP = rnd.randint(self.lower_bound, self.values[self.cur_unit])
            return_msg = Message("BID", self.name, "BARGAIN", WTP)
            self.returned_msg(return_msg)
            return return_msg   

        elif self.type == "SELLER": # for SELLER
            WTA = rnd.randint(self.costs[self.cur_unit], self.upper_bound)
            return_msg = Message("ASK", self.name, "BARGAIN", WTA)
            self.returned_msg(return_msg)
            return return_msg

        elif self.type == "TRADER":
            pass

    def transact(self, pl):
        """
        Make a buy or sell order
        """
        if self.debug:
            print(f"-- {self.name} has {self.units_transacted} of {self.max_units}")
            print(f"-- {self.name} working on unit {self.cur_unit}")
        if self.cur_unit >= self.max_units:
            return_msg = Message("NULL", self.name, "BARGAIN", None)
            self.returned_msg(return_msg)
            return return_msg
            
        current_offers = pl  # payload from bargain, self.order_book
        
        if self.type == "BUYER":
            WTP = rnd.randint(self.lower_bound, self.values[self.cur_unit])
            offers = []
            for trader_id in current_offers:
                if current_offers[trader_id] == None:
                    continue
                offer_type = current_offers[trader_id][0]
                offer_amount = current_offers[trader_id][1]
                if offer_type == "ASK":
                    offers.append((trader_id, offer_amount))
            # Now find an offer    
            if len(offers) > 0:
                offer = rnd.choice(offers)
                if WTP >= offer[1]:  # offer[1] = sellers willingness to accept
                    seller_id = offer[0]
                    return_msg = Message("BUY", self.name, "BARGAIN", seller_id)
                    self.returned_msg(return_msg)
                    return return_msg    
                else:
                    return_msg = Message("NULL", self.name, "BARGAIN", None)
                    self.returned_msg(return_msg)
                    return return_msg   
            else:
                return_msg = Message("NULL", self.name, "BARGAIN", None)
                self.returned_msg(return_msg)
                return return_msg
            
        elif self.type == "SELLER": # for SELLER
            WTA = rnd.randint(self.costs[self.cur_unit], self.upper_bound)
            offers = []
            for trader_id in current_offers:
                if current_offers[trader_id] == None:
                    continue
                offer_type = current_offers[trader_id][0]
                offer_amount = current_offers[trader_id][1]
                if offer_type == "BID":
                    offers.append((trader_id, offer_amount))
            # Now find an offer    
            if len(offers) > 0:
                offer = rnd.choice(offers)
                if WTA <= offer[1]:  # offer[1] = buyers willingness to pay
                    buyer_id = offer[0]
                    return_msg = Message("SELL", self.name, "BARGAIN", buyer_id)
                    self.returned_msg(return_msg)
                    return return_msg    
                else:
                    return_msg = Message("NULL", self.name, "BARGAIN", None)
                    self.returned_msg(return_msg)
                    return return_msg   
            else:
                return_msg = Message("NULL", self.name, "BARGAIN", None)
                self.returned_msg(return_msg)
                return return_msg

        elif self.type == "TRADER": # Trader is a combo of buyer and seller - accepts both bids and asks - sometimes only one for each type of market
            pass
                 

    def contract(self, pl):
        """
        Update contract information for ZID Trader
        """
        self.contract_this_period = True  # Got a contract this period
        contract = pl
        price = contract[1]
        buyer_id = contract[2]
        seller_id = contract[3]
        if self.type == 'BUYER':
            if self.get_name() != buyer_id:
                return_msg = Message("BAD", self.name, "BARGAIN", 
                                "08 Not buyer contract")
                self.returned_msg(return_msg)
                return return_msg                
            self.units_transacted += 1
            self.cur_unit += 1
        else:  # SELLER
            if self.get_name() != seller_id:
                return_msg = Message("BAD", self.name, "BARGAIN", 
                       "09 Not seller contract")
                self.returned_msg(return_msg)
                return return_msg
            self.units_transacted += 1
            self.cur_unit += 1
            
        return_msg = Message("Update", self.name, "BARGAIN", 
                             "10 Units Updated")
        self.returned_msg(return_msg)
        return return_msg

class ZIDA(ZID):
    """
        Zero Intelligence variant for decentralized market
        with Affinity to other traders
        <==> Bias to stay in current location
    """

    def move_requested(self, pl):
        """
        Make a move in a random direction but with bias to stay if you can still trade
        Stickiness to state quo is determined by the contract number in the last day
        """
        if self.contract_this_period:
            direction_list = [0, 0, 0]
        else:
            direction_list = [-1, 0, +1]
        if self.cur_unit > self.max_units:
            return_msg = Message("MOVE", self.name, "Travel", (0, 0))
            self.returned_msg(return_msg)
            return return_msg
        else:
            x_dir = rnd.choice(direction_list)
            y_dir = rnd.choice(direction_list)
            return_msg = Message("MOVE", self.name, "Travel", (x_dir, y_dir))
            #self.contract_this_period = False
            self.returned_msg(return_msg)
            return return_msg

class ZIDP(ZID):
    """Overrides Bid and Ask Decisions"""

    def find_opt(self, m_type, offers):
        """returns offer with min ask or max bid to action_requested
           m_type = 'min' or 'max'
           offers = (id, amount) either all bids or all asks"""

        y_found = offers[0]
        for x, y in offers:
            if m_type == 'max' and y > y_found[1]:
                y_found = (x, y)
            if m_type == 'min' and y < y_found[1]:    
                y_found = (x, y)
        return y_found
    
    def transact(self, pl):
        """
        Make a buy or sell 
        """
        if self.debug:
            print(f"-- {self.name} has {self.units_transacted} of {self.max_units}")
            print(f"-- {self.name} working on unit {self.cur_unit}")
        if self.cur_unit >= self.max_units:
            return_msg = Message("NULL", self.name, "BARGAIN", None)
            self.returned_msg(return_msg)
            return return_msg
            
        current_offers = pl  # payload from bargain, self.order_book
        
        if self.type == "BUYER":
            WTP = rnd.randint(self.lower_bound, self.values[self.cur_unit])
            # collect relavent offers
            offers = []
            for trader_id in current_offers:
                if current_offers[trader_id] == None:
                    continue
                offer_type = current_offers[trader_id][0]
                offer_amount = current_offers[trader_id][1]
                if offer_type == "ASK":
                    offers.append((trader_id, offer_amount))
            # Now find an offer to accept    
            if len(offers) > 0:
                offer = self.find_opt('min', offers)
                if WTP >= offer[1]:  # offer[1] = sellers willingness to accept
                    seller_id = offer[0]
                    return_msg = Message("BUY", self.name, "BARGAIN", seller_id)
                    self.returned_msg(return_msg)
                    return return_msg    
                else:
                    return_msg = Message("NULL", self.name, "BARGAIN", None)
                    self.returned_msg(return_msg)
                    return return_msg   
            else:
                return_msg = Message("NULL", self.name, "BARGAIN", None)
                self.returned_msg(return_msg)
                return return_msg
            
        else: # for SELLER
            WTA = rnd.randint(self.costs[self.cur_unit], self.upper_bound)
            # collect relavent offers
            offers = []
            for trader_id in current_offers:
                if current_offers[trader_id] == None:
                    continue
                offer_type = current_offers[trader_id][0]
                offer_amount = current_offers[trader_id][1]
                if offer_type == "BID":
                    offers.append((trader_id, offer_amount))
            # Now find an offer    
            if len(offers) > 0:
                offer = self.find_opt('max', offers)
                if WTA <= offer[1]:  # offer[1] = buyers willingness to pay
                    buyer_id = offer[0]
                    return_msg = Message("SELL", self.name, "BARGAIN", buyer_id)
                    self.returned_msg(return_msg)
                    return return_msg    
                else:
                    return_msg = Message("NULL", self.name, "BARGAIN", None)
                    self.returned_msg(return_msg)
                    return return_msg   
            else:
                return_msg = Message("NULL", self.name, "BARGAIN", None)
                self.returned_msg(return_msg)
                return return_msg  
 
class ZIDPA(ZIDP):
    """
        Zero Intelligence variant for decentralized market
        with Affinity to other traders
        <==> Bias to stay in current location
    """

    def move_requested(self, pl):
        """
        Make a move in a random direction but with bias to stay if you made a contract in the past.
        """
        if self.contract_this_period:
            direction_list = [0, 0, 0]
        else:
            direction_list = [-1, 0, +1]
        if self.cur_unit > self.max_units:
            return_msg = Message("MOVE", self.name, "Travel", (0, 0))
            self.returned_msg(return_msg)
            return return_msg
        else:
            x_dir = rnd.choice(direction_list)
            y_dir = rnd.choice(direction_list)
            return_msg = Message("MOVE", self.name, "Travel", (x_dir, y_dir))
            self.returned_msg(return_msg)
            #self.contract_this_period = False
            return return_msg

class ZIDPR(ZIDP):
    """
        Zero Intelligence variant for decentralized market
        with Affinity to other traders
        <==> Bias to stay in current location
    """

    def move_requested(self, pl):
        """
        Make a move in a random direction but with bias to stay if you can still trade
        Stickiness to state quo is determined by the contract number in the last day
        """

        if self.contract_this_period:
            direction_list = [0, 0, 0]
        else:
            direction_list = [-1, 0, +1]
        if self.num_at_loc > 2:
            #print('NUMBER AT g', self.num_at_loc)
            direction_list = [-1, +1]
        if self.cur_unit > self.max_units:
            return_msg = Message("MOVE", self.name, "Travel", (0, 0))
            self.returned_msg(return_msg)
            return return_msg
        else:
            x_dir = rnd.choice(direction_list)
            y_dir = rnd.choice(direction_list)
            return_msg = Message("MOVE", self.name, "Travel", (x_dir, y_dir))
            self.returned_msg(return_msg)
            #self.contract_this_period = False
            return return_msg
        