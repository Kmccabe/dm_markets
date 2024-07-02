import random as rnd
import numpy as np
from institutions.dm_message_model import Message
#from dm_zida import ZIDA

class Trader(object):
    """Base class for Buyers or Seller Agents
       Decision making is provided by a child class where 
       overridden methods are those called in process_message
    """
    
    def __init__(self, name, trader_type, payoff, money, location,
                 lower_bound = 0, upper_bound = 9999, movement_error_rate = 0,
                 reset_flag_frequency=None, reset_flag_min_agents=None,
                reset_flag_on_random=False, reset_flag_window=None, reset_flag_min_trades=1):
        """ name = name of trader
            trader_type = BUYER or SELLER
            payoff = payoff function: utility or profit
            location = starting location of trader
        """
        self.debug = False
        self.name = name          # unique identifier 
        self.type = trader_type   # BUYER or SELLER
        self.payoff = payoff  # utility or profit function
        self.money = money        # starting money ballance
        self.location = location  # starting location a tuple (x, y)
        self.lower_bound = lower_bound # on bids, asks, prices, values, costs
        self.upper_bound = upper_bound # on above

        self.values = []  # BUYER values are set by self.set_values(list) 
        self.costs = []   # SELLER costs are set by self.set_costs(list)
        self.units_transacted = 0  # Number of units bought or sold
        self.cur_unit = 0     # current unit looking to buy or sell
        self.max_units = 0    # length of values or costs

        self.contracts = []   # list of contracts
        self.valid_directives = ["START", "MOVE_REQUESTED", "OFFER", "TRANSACT", "CONTRACT"]
        #TODO: make directives lower case (maybe)
        self.simulation = None    # get access to class SimulateMarket
        #TODO: explain above better and why the flag below
        self.contract_this_period = False
        self.num_at_loc = 0

        self.movement_error_rate  = movement_error_rate

        self.reset_flag_frequency = reset_flag_frequency
        self.reset_flag_min_agents = reset_flag_min_agents
        self.reset_flag_on_random = reset_flag_on_random

        # Used if reset_flag_frequency = WINDOW
        self.reset_flag_window = reset_flag_window
        if self.reset_flag_frequency == "WINDOW":
            if self.reset_flag_window is None:
                raise ValueError("Cannot have undefined window size with window reset frequency")
            self.current_period = -1
            self.periods_traded_in = []
        
        self.reset_flag_min_trades = reset_flag_min_trades

        # Used if reset_flag_frequency = WEEK
        self.trades_this_week = 0

    
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
        else:
            for k, cost in enumerate(self.costs):
                if k == 0:
                    s = s + f"[{cost:5},"
                elif k == self.max_units-1:
                    s = s + f"{cost:5}]"
                else:
                    s = s + f"{cost:5},"
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

    def set_contract_this_period(self, flag, debug_contract=False):
        if debug_contract:
            print("$$$ CONTRACT_THIS_PERIOD_MANUAL TO:", flag)
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

    def update_flag_window(self):
        period_span = np.arange(np.max(self.current_period-self.reset_flag_window, 0), self.current_period+1)
        trades_in_window = 0
        for p in period_span:
            if p in self.periods_traded_in:
                trades_in_window += 1
        if trades_in_window >= self.reset_flag_min_trades:
            self.contract_this_period = True
        else:
            self.contract_this_period = False
        
        #print(period_span)
        #print(self.periods_traded_in)
        #print(self.contract_this_period)


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

        # START flag 
        if self.reset_flag_frequency == "START":
            self.set_contract_this_period(False) # TODO: Consider case of trade THIS WEEK - rolling window
        
        # WEEK flag
        if self.reset_flag_frequency == "WEEK":
            if self.trades_this_week >= self.reset_flag_min_trades:
                self.contract_this_period = True
            else:
                self.contract_this_period = False
            self.trades_this_week = 0

        return return_msg


    def total_random_move(self, pl):
        if self.reset_flag_on_random:
            self.set_contract_this_period(False)
        direction_list = [-1, 0, +1]
        x_dir = rnd.choice(direction_list)
        y_dir = rnd.choice(direction_list)
        movement_idea = (x_dir, y_dir)
        return movement_idea


    def move_requested(self, pl):
        """
        Make a move in a random direction if you can still trade 
        """
        movement_idea = None # How to move

        # If draw below the error rate randomly, have a COMPLETELY random movement
        np_rand = np.random.default_rng()
        if np_rand.random() < self.movement_error_rate:
            movement_idea = self.total_random_move(pl)
            self.set_contract_this_period(False)
        
        # otherwise employ the movement strategy
        else:
            direction_list = [-1, 0, +1] # 
            if self.cur_unit > self.max_units:
                movement_idea = (0, 0)
            else:
                x_dir = rnd.choice(direction_list)
                y_dir = rnd.choice(direction_list)
                movement_idea = (x_dir, y_dir)
        
        if self.reset_flag_frequency == "PERIOD":
            self.contract_this_period = False  # Use this to see if you get a contract this period
        
        return_msg = Message("MOVE", self.name, "Travel", movement_idea)
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

        else: # for SELLER
            WTA = rnd.randint(self.costs[self.cur_unit], self.upper_bound)
            return_msg = Message("ASK", self.name, "BARGAIN", WTA)
            self.returned_msg(return_msg)
            return return_msg  

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
            
        else: # for SELLER
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
                 

    def contract(self, pl, debug_contract=False):
        """
        Update contract information for ZID Trader
        """
        if debug_contract:
            if self.contract_this_period == False:
                print("#### Contract FLIPPED")
            if self.contract_this_period == True:
                print("@@@@ contract NO FLIP")
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

        if self.reset_flag_frequency == "WEEK":
            self.trades_this_week += 1
        elif self.reset_flag_frequency == "WINDOW":
            self.periods_traded_in.append(self.current_period)

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

        # Check if traded enough in the last window 
        if self.reset_flag_frequency == "WINDOW":
            self.update_flag_window()

            self.current_period += 1

        movement_idea = None # How to move

        # If draw below the error rate randomly, have a COMPLETELY random movement
        np_rand = np.random.default_rng()
        
        if np_rand.random() < self.movement_error_rate:
            movement_idea = self.total_random_move(pl)
        
        # otherwise employ the movement strategy
        else:
            if self.contract_this_period:
                direction_list = [0, 0, 0]
                
                # MIN_AGENTS Move if less than required agents
                if self.reset_flag_frequency == "MIN_AGENTS" and self.num_at_loc < self.reset_flag_min_agents:
                    direction_list = [-1, 0, +1]    
                    self.set_contract_this_period(False)

            else:
                direction_list = [-1, 0, +1]
            if self.cur_unit > self.max_units:
                movement_idea = (0, 0)
            else:
                x_dir = rnd.choice(direction_list)
                y_dir = rnd.choice(direction_list)
                movement_idea = (x_dir, y_dir)
        
        return_msg = Message("MOVE", self.name, "Travel", movement_idea)
        
        if self.reset_flag_frequency == "PERIOD":
            self.contract_this_period = False
        
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

        # Check if traded enough in the last window 
        if self.reset_flag_frequency == "WINDOW":
            self.update_flag_window()

            self.current_period += 1

        movement_idea = None # How to move

        # If draw below the error rate randomly, have a COMPLETELY random movement
        np_rand = np.random.default_rng()
        rand_draw = np_rand.random()
        # print(rand_draw)
        if rand_draw < self.movement_error_rate:
            movement_idea = self.total_random_move(pl)
            self.set_contract_this_period(False)
        
        # otherwise employ the movement strategy
        else:
            # Note: Contract this period is NEVER reset regularly - only if the random error is called
            # Change: Check if there is not too few at location - if so, reset the contract_this_period
            if self.contract_this_period:
                direction_list = [0, 0, 0]
                
                # MIN_AGENTS Move if less than required agents
                if self.reset_flag_frequency == "MIN_AGENTS" and self.num_at_loc < self.reset_flag_min_agents:
                    direction_list = [-1, 0, +1]    
                    self.set_contract_this_period(False)
            else:
                direction_list = [-1, 0, +1]
            if self.cur_unit > self.max_units:
                movement_idea = (0, 0)
            else:
                x_dir = rnd.choice(direction_list)
                y_dir = rnd.choice(direction_list)
                movement_idea = (x_dir, y_dir)

        return_msg = Message("MOVE", self.name, "Travel", movement_idea)
        self.returned_msg(return_msg)

        if self.reset_flag_frequency == "PERIOD":
            self.contract_this_period = False

        return return_msg

class ZIDPR(ZIDP):
    """
        Zero Intelligence variant for decentralized market
        with Affinity to other traders
        <==> Bias to stay in current location
        BUT Moves Away if >2 at a point - COVID intervention
    """

    def move_requested(self, pl):
        """
        Make a move in a random direction but with bias to stay if you can still trade
        Stickiness to state quo is determined by the contract number in the last day
        """

        # Check if traded enough in the last window 
        if self.reset_flag_frequency == "WINDOW":
            self.update_flag_window()

            self.current_period += 1

        movement_idea = None # How to move

        # If draw below the error rate randomly, have a COMPLETELY random movement
        np_rand = np.random.default_rng()
        if np_rand.random() < self.movement_error_rate:
            movement_idea = self.total_random_move(pl)
        
        # otherwise employ the movement strategy
        else:
            # Note: Contract this period is NEVER reset regularly - only if the random error is called
            # Change: Check if there is not too few at location - if so, reset the contract_this_period
            if self.contract_this_period:
                direction_list = [0, 0, 0]

                # MIN_AGENTS Move if less than required agents
                if self.reset_flag_frequency == "MIN_AGENTS" and self.num_at_loc < self.reset_flag_min_agents:
                    direction_list = [-1, 0, +1]    
                    self.set_contract_this_period(False)

            else:
                direction_list = [-1, 0, +1]
            
            # Move away if too crowded (>2 traders)
            if self.num_at_loc > 2:
                #print('NUMBER AT g', self.num_at_loc)
                direction_list = [-1, +1]
            if self.cur_unit > self.max_units:
                movement_idea = (0, 0)
            else:
                x_dir = rnd.choice(direction_list)
                y_dir = rnd.choice(direction_list)
                movement_idea = (x_dir, y_dir)
    
        return_msg = Message("MOVE", self.name, "Travel", movement_idea)
        self.returned_msg(return_msg)

        if self.reset_flag_frequency == "PERIOD":
            self.contract_this_period = False

        return return_msg
