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
                 lower_bound = 0, upper_bound = 9999, item_buyer="C", item_seller="C", default_rep=100, payoffs=None, cur_local=False, gamma=1):
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
        if self.type == "BUYER" or self.type == "SELLER":
            self.quantities = {"SPOT": {item_buyer: 0}}
        elif self.type == "TRADER":
            self.quantities = {"SPOT": {item_buyer: 0, item_seller: 0}}

        # Stores current quantities of local currencies at the disposal of the agent - if not-in-dictionary, presumed 0
        self.currencies = {"M": 0} # Currently only one currency

        # Stores valuations of all the types of items the agent can buy/sell
        self.valuations = {item_buyer:[], item_seller:[]} # Structure {B: [values], S: [costs]}
        self.item_buyer = item_buyer
        self.item_seller = item_seller

        self.trx_units = {item_buyer:0, item_seller:0} # Structure {B: units_transacted, S: units_transacted}
        self.cur_units = {item_buyer:0, item_seller:0} # Structure {B: cur_unit, S: cur_unit}
        self.unit_maxs = {item_buyer:0, item_seller:0} # Structure {B: max_unit, S: max_unit}

        self.rep_tokens = default_rep
        self.payoffs = payoffs # Structure {B: units_transacted, S: units_transacted}

        self.debug3 = False
        self.move_debug = False
        self.trade_debug = False

        self.cur_local = cur_local
        self.owes_money = False
        self.loans = {}
        self.loans["M"] = 0 # TODO fix up currency stuff to other institutions
        self.gamma = gamma
    
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
            return f"""TRADER: {self.name}
                    \n\tSells: {self.item_seller}, at costs: {self.valuations[self.item_buyer]}
                    \n\tBuys: {self.item_buyer}, at vals: {self.valuations[self.item_seller]}
                    \n\tQuantities: {self.quantities}
                    \n\tCurrencies: {self.currencies}
                    \n\tLocation: {self.location}"""
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
        if self.type == "BUYER":
            self.values = v
            self.max_units = len(v) 
            self.cur_unit = 0
        elif self.type == "TRADER":
            buying_item = self.item_buyer
            self.values = v
            self.valuations[buying_item] = v
            self.unit_maxs[buying_item] = len(v)
            self.cur_units[buying_item] = 0

        # Update starting quantity
        self.quantities["SPOT"][self.item_buyer] = 0
    
    def set_costs(self, c):
        """
        Set self.costs for seller from list c 
        """
        if self.type == "SELLER":
            self.costs = c
            self.max_units = len(c)
            self.cur_unit = 0
        elif self.type == "TRADER":
            selling_item = self.item_seller
            self.costs = c
            self.valuations[selling_item] = c
            self.unit_maxs[selling_item] = len(c)
            self.cur_units[selling_item] = 0
        
        # Update starting quantity
        self.quantities["SPOT"][self.item_seller] = len(c)
        
    def set_location(self, loc):
        """
        Set traders location  
        """
        self.location = loc
        
    def set_units_transacted(self, q):
        """
        Set number of units bought or sold by trader
        """
        if self.type == "BUYER" or self.type == "SELLER":
            self.units_transacted = q
        elif self.type == "TRADER":
            self.trx_units[self.item_buyer] = q
            self.trx_units[self.item_seller] = q

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
        elif directive == "REQUEST_MONEY": # TODO finish
            msg = self.request_money(payload)
        elif directive == "REPAY_LOAN": # TODO finish
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
    
    def get_payoff(self, prices, currency="M", prices_bs=None):

        if self.type == "BUYER" or self.type == "SELLER":
            agent_roles = [self.type]
            agent_items = ["C"]
        elif self.type == "TRADER":
            agent_roles = ["BUYER", "SELLER"]
            agent_items = [self.item_buyer, self.item_seller]
            assert prices_bs is not None

        for i, role in enumerate(agent_roles):
            if role == "BUYER":
                if agent_items[i] == "C":
                    vs = self.values
                    q = self.units_transacted
                    m = self.money
                    utility = self.payoff(q, m, vs, prices)
                else:
                    vs = self.valuations[agent_items[i]]
                    q = self.trx_units[agent_items[i]]
                    m = self.currencies[currency]/2 # Currently local-non-named. Avoids double-counting
                    utility = self.payoffs[self.item_buyer](q, m, vs, prices_bs[self.item_buyer])

                
        
            if role == "SELLER":
                if agent_items[i] == "C":
                    cs = self.costs
                    q = self.units_transacted
                    m = self.money
                    profit = self.payoff(q, m, cs, prices)
                else:
                    cs = self.valuations[agent_items[i]]
                    q = self.trx_units[agent_items[i]]
                    m = self.currencies[currency]/2 # Local non-named TODO generalize
                    profit = self.payoffs[self.item_seller](q, m, cs, prices_bs[self.item_seller])

        if self.type == "BUYER":
            return utility
        if self.type == "SELLER":
            return profit
        if self.type == "TRADER":
            return utility + profit
        
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

        return_msg = Message("REPORT_QUANTITY", self.name, "BARGAIN", return_val)
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
        #else:
        #    return_msg = Message("NULL", self.name, "BARGAIN", 99999999999999)    

        return req_desire

        # Currently all moneys are effectively local because they cannot be transported or communicated at a distance - so just using M type right now
        # return_msg = Message("REQUEST_MONEY", self.name, "BARGAIN", req_desire)
        # return return_msg

    def get_rep(self):
        return self.rep_tokens

    def set_money(self, m_type, m_val):
        self.loans[m_type] = m_val
        self.currencies[m_type] = m_val

    def report_money(self, payload="M"):
        """Returns the amount of currency of this type this agent owns"""
        cur_type = payload
        try:
            return_val = self.currencies[cur_type]
        except KeyError:
            self.currencies[cur_type] = 0
            return_val = 0

        return_msg = Message(cur_type, self.name, "REPORT_MONEY", return_val)
        return return_msg

    def repay_loan(self, payload="M"):
        """Returns the requested currency to the currency issuer - currently returns the TOTAL amount of the currency, not just how much was borrowed
            This simplifying assumption alows us to not worry about monetary inflation, only worrying about real prices"""
        cur_type = payload # Currently - repays ALL of the given currency - allows us to not worry about inter-period inflation and only care about real prices
        try:
            onhand_currency = self.currencies[cur_type]
        except KeyError:
            self.currencies[cur_type] = 0
            onhand_currency = 0
        
        repaid = False
        if onhand_currency > self.loans[payload]:
            repaid = True
        else:
            self.rep_tokens = self.rep_tokens - self.gamma*(onhand_currency - self.loans[payload])

        self.currencies[cur_type] = 0
        self.loans[cur_type] = 0
        self.owes_money = False

        if repaid:
            return True
        return False

        
        #return_msg = Message("REPAY_LOAN", self.name, "BARGAIN", onhand_currency)
        #return return_msg

    def get_type_valuation(self, i_type="C", market_type="ONE_TYPE"):
        # Get valuations, types
        if market_type == "ONE_TYPE":
            agent_role = self.type
            if agent_role == "BUYER":
                item_val = self.values[self.cur_unit]
            if agent_role == "SELLER":
                item_val = self.costs[self.cur_unit]
        # Need to determine the trader role at this moment for two-type market
        elif market_type == "TWO_TYPE":
            if i_type == self.item_buyer:
                agent_role = "BUYER"
            elif i_type == self.item_seller:
                agent_role = "SELLER"
            item_val = self.valuations[i_type][self.cur_units[i_type]]
        
        return agent_role, item_val

    def check_contract(self, contracted_to, contract_df, give_detail=False):
        # Check if this is the right kind of contract for this agent
        good_contract = False
        if self.type == 'BUYER' or self.type == "SELLER":
            agent_role = self.type 
        elif self.type == "TRADER":
            item_type = contract_df["item_type"].values[0]
            if item_type == self.item_buyer:
                agent_role = "BUYER"
            elif item_type == self.item_seller:
                agent_role = "SELLER"
        if contracted_to == "BUY" and agent_role == "BUYER":
            good_contract = True
        elif contracted_to == "SELL" and agent_role == "SELLER":
            good_contract = True
        
        if not good_contract:
            if give_detail:
                return False, "Not the right kind of contract"
            return False
        elif good_contract:
            if give_detail:
                return True, "All good"
            return True

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
            self.quantities["SPOT"][self.item_buyer] = 0
        elif self.type == "SELLER":
            self.max_units = len(self.costs)
            self.quantities["SPOT"][self.item_seller] = self.max_units
        elif self.type == "TRADER":
            self.unit_maxs[self.item_buyer] = len(self.values)
            self.unit_maxs[self.item_seller] = len(self.costs)
            self.cur_units[self.item_buyer] = 0
            self.cur_units[self.item_seller] = 0
            self.trx_units[self.item_buyer] = 0
            self.trx_units[self.item_seller] = 0
            self.quantities["SPOT"][self.item_buyer] = 0
            self.quantities["SPOT"][self.item_seller] = len(self.costs)
        self.currencies["M"] = 0

        return_msg = Message("Initial", self.name, self.name, "Initialized")
        self.returned_msg(return_msg)
        return return_msg

    def move_requested(self, pl):
        """
        Make a move in a random direction if you can still trade 
        """
        self.contract_this_period = False  # Use this to see if you get a contract this period
        direction_list = [-1, 0, +1]

        # Check if out of units
        done_trading = False
        if self.type == "SELLER" or self.type == "BUYER":
            if self.cur_unit >= self.max_units:
                done_trading = True
        elif self.type == "TRADER": # note BIGGER barrier to moving away and to not trading
            if self.cur_units[self.item_buyer] >= self.unit_maxs[self.item_buyer] and self.cur_units[self.item_seller] >= self.unit_maxs[self.item_seller]:
                done_trading = True

        if done_trading: # Do not move if over-traded - this flag should NEVER be true
            return_msg = Message("MOVE", self.name, "Travel", (0, 0))
            
        else:
            x_dir = rnd.choice(direction_list)
            y_dir = rnd.choice(direction_list)
            return_msg = Message("MOVE", self.name, "Travel", (x_dir, y_dir))

        # TODO TEMP
        if self.move_debug:
            if return_msg.get_payload() == (0,0):
                print("Not Moving")
            else:
                print("Moving by", return_msg.get_payload())

        self.returned_msg(return_msg)
        #self.contract_this_period = False
        return return_msg

    def offer(self, pl):
        """
        Make a bid or ask 
        """
        if self.debug:
            print(f"-- {self.name} has {self.units_transacted} of {self.max_units}")
            print(f"-- {self.name} working on unit {self.cur_unit}")
        
        # Do not put in offers if already satiated with trading
        done_trading = False
        i_type = pl['item_type']
        if self.type == "SELLER" or self.type == "BUYER":
            if self.cur_unit >= self.max_units:
                done_trading = True
        elif self.type == "TRADER": # note BIGGER barrier to moving away and to not trading
            if self.cur_units[i_type] >= self.unit_maxs[i_type]:
                done_trading = True
        if done_trading:
            return_msg = Message("NO_OFFER", self.name, "BARGAIN", None)
            if self.trade_debug:
                print("\t\tDone Offering")
            self.returned_msg(return_msg)
            return return_msg
        
        if self.trade_debug:
            print("Still Offering")
        
        # Here if not done trading
        p_type = pl['property_right'] # currently only SPOT market
        current_offers = pl['order_book']  # order_book
        market_type = pl['market_type']
        bidding_type = pl['bidding_type']
        c_type = pl['currency_type']

        agent_role, item_val = self.get_type_valuation(i_type, market_type)
        
        # Determine Bid
        if agent_role == "BUYER":
            if bidding_type == "MONETARY": # determine if cash-constrained
                cash_on_hand = self.currencies[c_type]
                max_bid = int(min(cash_on_hand, item_val)) # Cannot bid above cash-on-hand
            else:
                max_bid = self.values[self.cur_unit]
            if self.lower_bound > max_bid:
                return_msg = Message("NO_OFFER", self.name, "BARGAIN", None)
                self.returned_msg(return_msg)
                return return_msg
            send_price = rnd.randint(self.lower_bound, max_bid)
            o_type = "BID"

        # Determine Ask
        elif agent_role == "SELLER":
            send_price = rnd.randint(item_val, self.upper_bound)
            o_type = "ASK"

        return_msg = Message("PLACE_OFFER", self.name, "BARGAIN", (send_price, o_type))
        self.returned_msg(return_msg)
        return return_msg

    def transact(self, pl):
        """
        Make a buy or sell order
        """
        if self.debug:
            print(f"-- {self.name} has {self.units_transacted} of {self.max_units}")
            print(f"-- {self.name} working on unit {self.cur_unit}")

        # Do not put in offers if already satiated with trading
        done_trading = False
        i_type = pl['item_type']
        if self.type == "SELLER" or self.type == "BUYER":
            if self.cur_unit >= self.max_units:
                done_trading = True
        elif self.type == "TRADER":
            if self.cur_units[i_type] >= self.unit_maxs[i_type]:
                done_trading = True
        if done_trading:
            return_msg = Message("NO_TRADE", self.name, "BARGAIN", None)
            if False: #self.trade_debug:
                print("Done Trading")
            self.returned_msg(return_msg)
            return return_msg
        
        if False: #self.trade_debug:
                print("Still trading")

        order_book = pl['order_book']  # payload from bargain, self.order_book
        market_type = pl['market_type']
        p_type = pl['property_right'] # Currently only SPOT 
        bid_type = pl['bidding_type']
        c_type = pl['currency_type']

        agent_role, item_val = self.get_type_valuation(i_type, market_type)
        
        if bid_type == "MONETARY":
            currency_limit = self.currencies[c_type]
        else:
            currency_limit = 9999999999999999999999

        sent_order = False # Flag to return NO_TRADE

        # Try to buy
        if agent_role == "BUYER":
            if bid_type == "MONETARY":
                max_bid = int(min(item_val, currency_limit))
            else:
                max_bid = item_val
            if self.lower_bound > max_bid:
                return_msg = Message("NO_TRADE", self.name, "BARGAIN", None)
                self.returned_msg(return_msg)
                return return_msg
            WTP = rnd.randint(self.lower_bound, max_bid)
            current_offers = order_book[order_book['offer_type']=="ASK"]
            if self.debug3:
                print(WTP)
                print(current_offers)

            # current_offers = current_offers[current_offers['price']<=WTP] # Exclude non-satisficing offers - not included for now - not ZID
            if len(current_offers) > 0:
                offer_id_chosen = rnd.choice(list(current_offers['offer_id'].values))
                offer_chosen = order_book[order_book['offer_id']== offer_id_chosen]
                if self.debug3:
                    print(offer_id_chosen, offer_chosen)
                if WTP >= offer_chosen['price'].values[0]:
                    return_msg = Message("BUY", self.name, "BARGAIN", offer_id_chosen) # note: now uses the offer_id not seller id
                    sent_order = True
        
        # Try to sell
        elif agent_role == "SELLER": # for SELLER
            WTA = rnd.randint(item_val, self.upper_bound)
            current_offers = order_book[order_book['offer_type']=="BID"]
            if self.debug3:
                print(WTA)
                print(current_offers)
            if len(current_offers) > 0:
                offer_id_chosen = rnd.choice(list(current_offers['offer_id'].values))
                offer_chosen = order_book[order_book['offer_id']== offer_id_chosen]
                if self.debug3:
                    print(offer_id_chosen, offer_chosen)
                if WTA <= offer_chosen['price'].values[0]:
                    return_msg = Message("SELL", self.name, "BARGAIN", offer_id_chosen)
                    sent_order = True

        if not sent_order:
            return_msg = Message("NO_TRADE", self.name, "BARGAIN", None)
        
        self.returned_msg(return_msg)
        return return_msg

    def contract(self, pl):
        """
        Update contract information for ZID Trader
        """

        # Unpack payload
        contracted_to = pl[0]
        contract_df = pl[1]

        good_contract, error_code = self.check_contract(contracted_to, contract_df, True)
        if not good_contract:
            return_msg = Message("BAD", self.name, "BARGAIN", error_code)
            self.returned_msg(return_msg)
            return return_msg

        self.contract_this_period = True  # Got a contract this period

        # Update item quantities
        p_right = contract_df["property_right"].values[0]
        i_type = contract_df["item_type"].values[0]

        if self.type == "BUYER" or self.type == "SELLER":
            self.units_transacted += 1
            self.cur_unit += 1
        elif self.type == "TRADER":
            if contracted_to == "BUY":
                self.quantities[p_right][i_type] += 1
            elif contracted_to == "SELL":
                self.quantities[p_right][i_type] -= 1
            self.trx_units[i_type] += 1
            self.cur_units[i_type] += 1
        
        cont_price = contract_df['price'].values[0]
        cont_currency = contract_df['currency_type'].values[0]

        # Update money balances
        if self.type == "BUYER" or self.type == "SELLER":
            pass # NOTE In the v2 there is a money balance passed by environment, but it is never updated 
        elif self.type == "TRADER":
            if contracted_to == "BUY":
                self.currencies[cont_currency] -= cont_price
            elif contracted_to == "SELL":
                self.currencies[cont_currency] += cont_price
            
        return_msg = Message("Update", self.name, "BARGAIN", 
                             "10. Units Updated")
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
        
        # Check if out of units
        done_trading = False
        if self.type == "SELLER" or self.type == "BUYER":
            if self.cur_unit >= self.max_units:
                done_trading = True
        elif self.type == "TRADER": # note BIGGER barrier to moving away and to not trading
            if self.cur_units[self.item_buyer] >= self.unit_maxs[self.item_buyer] and self.cur_units[self.item_seller] >= self.unit_maxs[self.item_seller]:
                done_trading = True
        
        if done_trading:
            return_msg = Message("MOVE", self.name, "Travel", (0, 0))
        else:
            x_dir = rnd.choice(direction_list)
            y_dir = rnd.choice(direction_list)
            return_msg = Message("MOVE", self.name, "Travel", (x_dir, y_dir))
        
        # TODO TEMP
        if self.move_debug:
            if return_msg.get_payload() == (0,0):
                print("Not Moving")
            else:
                print("Moving by", return_msg.get_payload())
        
        # If moving, must repay
        if not return_msg.get_payload() == (0,0) and self.owes_money and self.cur_local:
            self.repay_loan()

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

        # Do not put in offers if already satiated with trading
        done_trading = False
        i_type = pl['item_type']
        if self.type == "SELLER" or self.type == "BUYER":
            if self.cur_unit >= self.max_units:
                done_trading = True
        elif self.type == "TRADER": # note BIGGER barrier to moving away and to not trading
            if self.cur_units[i_type] >= self.unit_maxs[i_type]:
                done_trading = True
        if done_trading:
            return_msg = Message("NO_TRADE", self.name, "BARGAIN", None)
            self.returned_msg(return_msg)
            return return_msg


        order_book = pl['order_book']  # payload from bargain, self.order_book
        market_type = pl['market_type']
        p_type = pl['property_right'] # Currently only SPOT 
        bid_type = pl['bidding_type']
        c_type = pl['currency_type']
        
        agent_role, item_val = self.get_type_valuation(i_type, market_type)
        
        if bid_type == "MONETARY":
            currency_limit = self.currencies[c_type]
        else:
            currency_limit = 9999999999999999999999

        sent_order = False # Flag to return NO_TRADE

        # Try to buy
        if agent_role == "BUYER":
            if bid_type == "MONETARY":
                max_bid = np.min(item_val, currency_limit)
            else:
                max_bid = item_val
            WTP = rnd.randint(self.lower_bound, max_bid)
            current_offers = order_book[order_book['offer_type']=="ASK"]
            if len(current_offers) > 0:
                sorted_offs = current_offers.sort_values(by='price') # Ascending by default
                offer_id_chosen = sorted_offs['offer_id'].values[0]
                offer_chosen = order_book[order_book['offer_id']== offer_id_chosen]
                if WTP >= offer_chosen['price'].values[0]:
                    return_msg = Message("BUY", self.name, "BARGAIN", offer_id_chosen) # note: now uses the offer_id not seller id
                    sent_order = True
                
        # Try to sell
        elif agent_role == "SELLER": # for SELLER
            WTA = rnd.randint(item_val, self.upper_bound)
            current_offers = order_book[order_book['offer_type']=="BID"]

            if len(current_offers) > 0:
                sorted_offs = current_offers.sort_values(by='price', ascending=False) # Ascending by default
                offer_id_chosen = sorted_offs['offer_id'].values[0]
                offer_chosen = order_book[order_book['offer_id']== offer_id_chosen]
                if WTA <= offer_chosen['price'].values[0]:
                    return_msg = Message("SELL", self.name, "BARGAIN", offer_id_chosen)
                    sent_order = True

        if not sent_order:
            return_msg = Message("NO_TRADE", self.name, "BARGAIN", None)
        
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
        else:
            x_dir = rnd.choice(direction_list)
            y_dir = rnd.choice(direction_list)
            return_msg = Message("MOVE", self.name, "Travel", (x_dir, y_dir))

        # TODO TEMP
        if self.move_debug:
            if return_msg.get_payload() == (0,0):
                print("Not Moving")
            else:
                print("Moving by", return_msg.get_payload())

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
        else:
            x_dir = rnd.choice(direction_list)
            y_dir = rnd.choice(direction_list)
            return_msg = Message("MOVE", self.name, "Travel", (x_dir, y_dir))

        # TODO TEMP
        if self.move_debug:
            if return_msg.get_payload() == (0,0):
                print("Not Moving")
            else:
                print("Moving by", return_msg.get_payload())

        self.returned_msg(return_msg)
        #self.contract_this_period = False
        return return_msg
        