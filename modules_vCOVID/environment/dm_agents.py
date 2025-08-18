import random as rnd
import numpy as np
from institutions.dm_message_model import Message

class Trader(object):
    """
    Base class for Buyers or Seller Agents
    Decision making is provided by a child class where 
        overridden methods are those called in process_message
    """
    
    def __init__(self, name, trader_type, payoff, money=None, location=None,
                 lower_bound = 0, upper_bound = 9999, num_units=8, movement_error_rate = 0, strategy_params = None, redraw_values = False,
                 group_name = None, debug=False):
        """ name = name of trader
            trader_type = BUYER or SELLER
            payoff = payoff function: utility or profit
            location = starting location of trader
        """
        self.debug = debug
        self.name = name          # unique identifier 
        self.type = trader_type   # BUYER or SELLER
        self.payoff = payoff  # utility or profit function
        self.money = money        # starting money ballance
        self.location = location  # starting location a tuple (x, y)
        self.lower_bound = lower_bound # on bids, asks, prices, values, costs
        self.upper_bound = upper_bound # on above
        self.num_units = num_units

        self.values = []  # BUYER values are set by self.set_values(list) 
        self.costs = []   # SELLER costs are set by self.set_costs(list)
        self.units_transacted = 0  # Number of units bought or sold
        self.cur_unit = 0     # current unit looking to buy or sell
        self.max_units = 0    # length of values or costs

        self.contracts = []   # list of contracts
        self.valid_directives = ["START", "MOVE_REQUESTED", "OFFER", "TRANSACT", "CONTRACT"]
        #TODO: make directives lower case (maybe)
        self.simulation = None    # get access to class SimulateMarket
        self.contract_this_period = False
        self.num_at_loc = 0

        self.movement_error_rate  = movement_error_rate

        self.strategy_params = strategy_params

        # Determines if you want to re-generate random valuations for each agent at the start of each week
        self.redraw_values = redraw_values

        self.agent_family = 'TRA'
        self.agent_class = 'TRA'

        self.set_group_name(group_name)

    def set_group_name(self, group_name):
        """Setter for agent group name."""
        
        if group_name is None:
            group_name = f't:{self.type}_c:{self.agent_class}_lb:{self.lower_bound}_ub:{self.upper_bound}_nu:{self.num_units}_mer:{self.movement_error_rate}_sp:{self.strategy_params}'
        self.group_name = group_name


    def __repr__(self):
        s = f"{self.name:10} {self.type:6} @{str(self.location)}:"
        if self.type == "BUYER" or self.type == "B":
            for k, value in enumerate(self.values):
                if k == 0:
                    s = s + f"[{value:5},"
                elif k == self.max_units-1:
                    s = s + f"{value:5}]"
                else:
                    s = s + f"{value:5},"
        elif self.type == "SELLER" or self.type == "S":
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
        print(f"strategy: {self.agent_class}")
        print(f"strategy parameters: {self.strategy_params}")
    
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

    def gen_res_values(self):
        """Stub - overwritten by child."""
        pass

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
        if self.type == "BUYER" or self.type == "B":
            utility = self.payoff(self.units_transacted, self.money, self.values, prices)
            return utility
        elif self.type == "SELLER" or self.type == "S":
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
        

class ZID(Trader):
    """ 
        Zero Intelligence variant for decentralized market
        a budget constrained ZI 
    """
    def __init__(self, name, trader_type, payoff, money=None, location=None, lower_bound=0, upper_bound=9999, num_units=8, movement_error_rate=0, strategy_params=None, redraw_values=False, group_name=None, debug=False):
        super().__init__(name, trader_type, payoff, money, location, lower_bound, upper_bound, num_units, movement_error_rate, strategy_params, redraw_values, group_name, debug)
        
        self.agent_family = 'ZID'
        self.agent_class = 'ZID'

        self.set_group_name(group_name)
    
    def gen_res_values(self):
        """Returns a sorted list of values or costs drawn from a sequence of uniform distributions"
            buyer_flag = True if a buyer else a seller
            units = number of draws
        """
        ub = self.upper_bound
        lb = self.lower_bound
        interval = 0
        # Archival - int((ub-lb)/4) # Division by four here to allow more overlap

        if self.type == "BUYER" or self.type == "B":
            values = []
            upper = ub
            lower = lb + interval
            for unit in range(self.num_units):
                value = np.random.randint(lower, upper+1)
                values.append(value)
            self.set_values(sorted(values, reverse=True))  # Insures declining marginal value
        elif self.type == "SELLER" or self.type == "S":
            costs = []
            upper = ub - interval
            lower = lb
            for unit in range(self.num_units):
                cost = np.random.randint(lower, upper+1)
                costs.append(cost)
            self.set_costs(sorted(costs, reverse=False))  # Insures increasing marginal cost

    def start(self, pl):
        """
        Sets up values for trading. Re-draws these values randomly. Previously, only reset the cur_item indicator to 0.
        Does not use payload - pl
        """
        self.units_transacted = 0
        self.cur_unit = 0
        if self.redraw_values:
            self.gen_res_values()
        if self.type == "BUYER" or self.type == "B":
            self.max_units = len(self.values)
        elif self.type == "SELLER" or self.type == "S":
            self.max_units = len(self.costs)
        return_msg = Message("Initial", self.name, self.name, "Initialized")
        self.returned_msg(return_msg)

        return return_msg


    def total_random_move(self, pl):
        """Move in a completely random direction (stay is 1/9th of cases if unblocked)."""
        
        # Reset the contract this period flag since randomly moved
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

        
        return_msg = Message("MOVE", self.name, "Travel", movement_idea)
        self.returned_msg(return_msg)
        return return_msg 


    def fetch_order_hist(self):
        
        return True

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
        
        if self.type == "BUYER" or self.type == "B":
            WTP = rnd.randint(self.lower_bound, self.values[self.cur_unit])
            return_msg = Message("BID", self.name, "BARGAIN", WTP)
            self.returned_msg(return_msg)
            return return_msg   

        elif self.type == "SELLER" or self.type == "S": # for SELLER
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
        
        if self.type == "BUYER" or self.type == "B":
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
            
        elif self.type == "SELLER" or self.type == "S": # for SELLER
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
        if self.type == 'BUYER' or self.type == "B":
            if self.get_name() != buyer_id:
                return_msg = Message("BAD", self.name, "BARGAIN", 
                                "08 Not buyer contract")
                self.returned_msg(return_msg)
                return return_msg                
            self.units_transacted += 1
            self.cur_unit += 1
        elif self.type == "SELLER" or self.type == "S":  # SELLER
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
        <==> Bias to stay in current location; Uses the strategy specified
    """

    def __init__(self, name, trader_type, payoff, money=None, location=None,
                 lower_bound = 0, upper_bound = 9999, num_units=8, movement_error_rate = 0, strategy_params = None,
                redraw_values = False, group_name=None, debug=False
            ):
        super().__init__(name, trader_type, payoff, money, location,
                 lower_bound, upper_bound, num_units, movement_error_rate, strategy_params, redraw_values, group_name, debug)
        
        self.agent_family = 'ZIDA'
        self.agent_class = 'ZIDA'

        self.set_group_name(group_name)
        
        # Trappings for movement strategy
        self.reset_flag_frequency = None
        self.current_period = None
        self.periods_traded_in = None
        self.reset_flag_min_agents = None
        self.reset_flag_min_trades = None
        self.trades_this_week = None

        if strategy_params is not None:
            self.reset_flag_frequency = strategy_params['reset_flag_frequency']
        else:
            self.reset_flag_frequency = "NONE"
        
        rf = self.reset_flag_frequency

        if rf == "WINDOW":
            self.reset_flag_window = strategy_params['reset_flag_window']  
            self.current_period = -1
            self.periods_traded_in = []
            self.reset_flag_min_trades = strategy_params['reset_flag_min_trades']
        elif rf == "MIN_AGENTS":
            self.reset_flag_min_agents = strategy_params['reset_flag_min_agents']
        elif rf == "WEEK":
            self.trades_this_week = 0
            self.reset_flag_min_trades = strategy_params['reset_flag_min_trades']


    def move_requested(self, pl, silence_log=False):
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
        
        if not silence_log:
            self.returned_msg(return_msg)
        return return_msg
    
    def start(self, pl):
        """
        Override the super to check if you need to reset movement flags.

        Otherwise proceed as in super; reset value/cost flags.
        """
        # START flag 
        if self.reset_flag_frequency == "START":
            self.set_contract_this_period(False)
        
        # WEEK flag
        if self.reset_flag_frequency == "WEEK":
            if self.trades_this_week >= self.reset_flag_min_trades:
                self.contract_this_period = True
            else:
                self.contract_this_period = False
            self.trades_this_week = 0
        
        return super().start(pl)
    

    def contract(self, pl, debug_contract=False):
        """
        Override super to keep track of trades this week and periods traded in. Otherwise proceed as in super.
        """
        
        if self.reset_flag_frequency == "WEEK":
            self.trades_this_week += 1
        elif self.reset_flag_frequency == "WINDOW":
            self.periods_traded_in.append(self.current_period)

        return super().contract(pl, debug_contract)


class ZIDP(ZID):
    """Overrides Bid and Ask Decisions"""

    def __init__(self, name, trader_type, payoff, money=None, location=None,
                lower_bound = 0, upper_bound = 9999, num_units=8, movement_error_rate = 0, strategy_params = None,
            redraw_values = False, group_name=None, debug=False
        ):
        super().__init__(name, trader_type, payoff, money, location,
                lower_bound, upper_bound, num_units, movement_error_rate, strategy_params, redraw_values, group_name, debug)
        
        self.agent_family = 'ZID'
        self.agent_class = 'ZIDP'

        self.set_group_name(group_name)


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
        
        if self.type == "BUYER" or self.type == "B":
            WTP = rnd.randint(self.lower_bound, self.values[self.cur_unit])
            # collect relevant offers
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
            
        elif self.type == "SELLER" or self.type == "S": # for SELLER
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


class ZIDPA(ZIDA, ZIDP):
    """
        Zero Intelligence variant for decentralized market
        with Affinity to staying in places where transactions possible
        <==> Bias to stay in current location
        Uses a passed movement heuristic/rule.
    """

    def __init__(self, name, trader_type, payoff, money=None, location=None,
                lower_bound = 0, upper_bound = 9999, num_units=8, movement_error_rate = 0, strategy_params = None,
            redraw_values = False, group_name=None, debug=False
        ):
        super().__init__(name, trader_type, payoff, money, location,
                lower_bound, upper_bound, num_units, movement_error_rate, strategy_params, redraw_values, group_name, debug)
        
        self.agent_family = 'ZIDA'
        self.agent_class = 'ZIDPA'

        self.set_group_name(group_name)

class ZIDPR(ZIDA, ZIDP):
    """
        Zero Intelligence variant for decentralized market
        with Affinity to staying in places where transactions possible
        <==> Bias to stay in current location
        BUT Moves Away if >2 at a point - COVID intervention
    """


    def __init__(self, name, trader_type, payoff, money=None, location=None,
                lower_bound = 0, upper_bound = 9999, num_units=8, movement_error_rate = 0, strategy_params = None,
            redraw_values = False, group_name=None, debug=False
        ):
        super().__init__(name, trader_type, payoff, money, location,
                lower_bound, upper_bound, num_units, movement_error_rate, strategy_params, redraw_values, group_name, debug)
        
        self.agent_family = 'ZIDA'
        self.agent_class = 'ZIDPR'

        self.set_group_name(group_name)


    def move_requested(self, pl):
        """
        Make a move based on the movement rule - but override move if you have too many individuals at the location
        """
        return_msg = super().move_requested(pl, silence_log=True)

        # Move away if too crowded (>2 traders)
        if self.num_at_loc > 2:
            
            # Randomly choose a new move
            found_move = False
            direction_list = [-1, 0, +1]
            while found_move == False:
                x_dir = rnd.choice(direction_list)
                y_dir = rnd.choice(direction_list)
                movement_idea = (x_dir, y_dir)
                
                # Forbidden to stay in place
                if movement_idea != (0, 0):
                    found_move = True
    
            return_msg = Message("MOVE", self.name, "Travel", movement_idea)

        self.returned_msg(return_msg)

        return return_msg


class ZIDT(ZID):


    # TODO: Implement
    def __init__(self, name, trader_type, payoff, money=None, location=None,
                lower_bound = 0, upper_bound = 9999, num_units=8, movement_error_rate = 0, strategy_params = None,
            redraw_values = False, group_name=None, debug=False
        ):
        super().__init__(name, trader_type, payoff, money, location,
                lower_bound, upper_bound, num_units, movement_error_rate, strategy_params, redraw_values, group_name, debug)
        
        self.agent_family = 'ZIDT'
        self.agent_class = 'ZIDT'

        self.set_group_name(group_name)
        raise ValueError('NOT IMPLEMENTED ZIDT')


class ZIDTR(ZIDT):


    # TODO: Implement
    def __init__(self, name, trader_type, payoff, money=None, location=None,
                lower_bound = 0, upper_bound = 9999, num_units=8, movement_error_rate = 0, strategy_params = None,
            redraw_values = False, group_name=None, debug=False
        ):
        super().__init__(name, trader_type, payoff, money, location,
                lower_bound, upper_bound, num_units, movement_error_rate, strategy_params, redraw_values, group_name, debug)
        
        self.agent_family = 'ZIDT'
        self.agent_class = 'ZIDTR'

        self.set_group_name(group_name)
        raise ValueError('NOT IMPLEMENTED ZIDT')
    
    # TODO Make ZIT (ZI+) Traders with opportunity cost calculation


class ZIM(ZID):
    """
    Bidding/asking strategy based on the work in Cliff and Bruten 1997, with the parameters as defined in Cliff and Bruten 1998 (hereafter, CB98). These agents attempt to maximize their profits by dynamically altering their profit margin, which defines the min (sellers) or max (buyers) they will quote.

    Movement strategy is random movement, same as ZID above.

    strategy_params required: (if not provided, generated as in CB98)
        learning_rate (float e[0, 1]): The rate at which agents adapt their margin. beta~U(0.1, 0.5), Ai in CB98.
        momentum_coef (float e[0, 1]): A damping rate which limits margin adaptation speed. gamma~U(0.0, 0.1), Ai in CB98.
        initial_margin (float e[-1, 0] for buyers, e[0, inf] for sellers): The initial profit margin expected by agents. 
            mu~U(-0.35, -0.05) for buyers, mu~U(0.05, 0.35) for sellers in CB98.
        max_r_step (float e[0, 1]): The maximal proportional learning step - max of distr. cR=0.05 in CB98.
        max_a_step (float e[0, 1]): The maximal non-proportional learning step - max of distr. cA=0.05 in CB98.
        initial_g (float e R): the initial value of G, part of the adjustment to margin. G=0 in CB98.
        initial_delta (float e R): the initial value of delta, part of the adjustment to margin. Initial value not specified in CB98.
            There may be a type in the CB98 formula - where Delta(t-1) has replaced Delta(t). For now assuming initial_delta = 0.

    In the CB97 case, the CDA is ordering the bids/asks (improvement rule) and their environment makes trades sequential. In our environment, we have bidding/asking phase and after a contract BUY/SELL phase. So we need a way to discretize these into time-steps. The most natural is observing all contracts after the BUY/SELL phase. Now there is a problem of ordering - because agents are ordered randomly in the bargaining order, the "last" quote is not necessarily the most powerful signal like it is in the CDA. However, this may simply slow down learning, but not eliminate it in expectation.
    """
    def __init__(self, name, trader_type, payoff, 
                 money=None, location=None,
                 lower_bound = 0, upper_bound = 9999, num_units=8,
                 movement_error_rate = 0, 
                 strategy_params = None,
                 redraw_values = False, group_name=None, debug=False
    ):
        super().__init__(name, trader_type, payoff, money, location,
                lower_bound, upper_bound, num_units, movement_error_rate, strategy_params, redraw_values, group_name, debug)
    
        self.agent_family = 'ZIM'
        self.agent_class = 'ZIM'

        # Sellers upper bound on margin is infinite, buyers it's 0
        if self.trader_type == 'SELLER' or self.trader_type == 'S':
            self.margin_ub = np.inf
        else:
            self.margin_ub = 0

        # Sellers lower bound on margin is 0, buyers it's -1
        if self.trader_type == 'SELLER' or self.trader_type == 'S':
            self.margin_lb = 0
        else:
            self.margin_lb = -1

        self.margin = strategy_params['initial_margin']
        self.learning_rate = strategy_params['learning_rate']
        self.momentum_coef = strategy_params['momentum_coef']

        self.cR = strategy_params['max_r_step']
        self.cA = strategy_params['max_a_step']

        self.G = strategy_params['initial_g']
        self.delta = strategy_params['initial_delta']
        
        self.set_group_name(group_name)
        

    def get_own_price(self):
        """Return the price this agent would bid/ask for its current (next-to-transact) unit."""
        j = self.cur_unit
        pj = self.values[j]*(1+self.margin)

        return pj

    def should_update(self, last_quote):
        """
        Check if agent should update their margin.
        
        params:
            last_quote: dict of {'type':'bid'/'ask', # Type of quote
                                'accepted': true/false, # If quote led to transaction
                                'quote': float} # Value of the quote
                In  this quote really is the last one observed, but we have a multi-agent random model, so it can be last observed or a random one
        
        returns:
            'up' (raise), 'down' (lower), 'flat' (no change) depending on the direction margin should go.
        """
        active = False
        last_type = last_quote['type']
        last_accepted = last_quote['accepted']
        last_val = last_quote['quote']
        own_quote = self.get_own_price()
        # Compare quote to what one what you would quote
        last_geq = last_val >= own_quote
        last_leq = last_val <= own_quote

        margin_dir = 'flat'

        if self.type == 'SELLER' or self.type == 'S':
            """
            Seller Raise Margin
            """
            if last_accepted and last_geq:
                margin_dir = 'up'
            elif active and ((last_type == 'ask' and last_leq) or 
                             (last_type == 'bid' and last_accepted and last_geq)):
                margin_dir = 'down'
        else:
            """
            Buyer Raise Margin
            """
            if last_accepted and last_leq:
                margin_dir = 'up'
            elif active and ((last_type == 'bid' and not last_accepted and last_geq) or (last_type == 'ask' and last_accepted and last_geq)):
                margin_dir = 'down'
        
        return margin_dir
    
    def update_profit_margin(self, margin_dir, last_quote):
        """
        ZIM traders update their profit margin according to the definition in CB97

        TODO: Consider making these variable names more natural.
        """

        q = last_quote
        p = self.get_own_price()
        j = self.get_cur_unit()
        l = self.values[j]

        last_G = self.G
        gamma = self.momentum_coef
        beta = self.learning_rate
        last_delta = self.delta

        # Draw random adjustment steps
        if margin_dir == 'up':
            R = rnd.uniform(1, 1+self.cR)
            A = rnd.uniform(0, self.cA)
        elif margin_dir == 'down':
            R = rnd.uniform(1-self.cR, 1.0)
            A = rnd.uniform(-self.cA, 0)
        elif margin_dir == 'flat':
            R = 0; A = 0
        
        # Calculate adjustment (learning)
        tau = R*q + A
        delta = beta * (tau - p)
        G = gamma*last_G + (1-gamma)*last_delta # TODO: verify this formula with Cliff and Bruten 1997 - 98 might have an error
        # In particular verify that we want last delta here and not present delta

        # Update margin
        new_margin = (p + G)/l
        # Verify boundaries
        if new_margin > self.margin_ub:
            new_margin = self.margin_ub
        elif new_margin < self.margin_lb:
            new_margin = self.margin_lb
        self.margin = new_margin

        # Store G and delta for next time this function is called
        self.G = G
        self.delta = delta

        return
    
    def offer(self, pl):
        """
        Make a bid or ask.

        Buyers bid and sellers ask. The price quoted is: price = current_value * (1 + margin). Margins are negative for buyers.
        """
        if self.debug:
            print(f"-- {self.name} has {self.units_transacted} of {self.max_units}")
            print(f"-- {self.name} working on unit {self.cur_unit}")
        if self.cur_unit >= self.max_units:
            return_msg = Message("NULL", self.name, "BARGAIN", None)
            self.returned_msg(return_msg)
            return return_msg
        
        current_offers = pl  # payload from bargain, self.order_book
        
        if self.type == "BUYER" or self.type == "B":
            WTP = rnd.randint(self.lower_bound, self.values[self.cur_unit])
            return_msg = Message("BID", self.name, "BARGAIN", WTP)
            self.returned_msg(return_msg)
            return return_msg   

        elif self.type == "SELLER" or self.type == "S": # for SELLER
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
        
        if self.type == "BUYER" or self.type == "B":
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
            
        elif self.type == "SELLER" or self.type == "S": # for SELLER
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