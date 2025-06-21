import random as rnd
import operator
import matplotlib.pyplot as plt                 # import matplotlib
import numpy as np                              # import numpy
import types
import time
import copy
import os
import json

import environment.dm_agents as dm_agents
import environment.dm_env as env

# Flag for debugging
debug = False

class MakeAgents(object):
    """
    Class to make agents to be used in centralized and decentralized trading
    
    Traders can be specified in two ways
    1. Default Traders defined by only their trader type, with symmetric lower_bound, upper_bound, 
        - TODO: Create a helper function which provides example agents, instead of doing it this way as below!!!!
        
    """
    def __init__(self):
        pass
        
    def gen_default_agents(self, num_traders, trader_class_count, num_units,
                 grid_size, lower_bound, upper_bound, debug=False, movement_error_rate=0, 
                 reset_flag_frequency="WINDOW", reset_flag_min_agents=None, reset_flag_on_random=True,
                 reset_flag_window=None, reset_flag_min_trades=1, agent_types=None, agent_type_counts=None, agent_endows=None, agent_payoffs=None):

        self.trader_class_count = trader_class_count     # list of trader types, should be tuple
        self.num_traders = num_traders       # number of traders, summed across types
        self.num_units = num_units           # number of units, same for all traders
        self.debug = debug                   # if True print additional information
        self.grid_size = grid_size           # grid is grid_size x grid_size
        
        self.agents = []                     # contains list of agents
        self.location_list = []
        self.market = None
        self.movement_error_rate = movement_error_rate
        self.reset_flag_frequency = reset_flag_frequency
        self.reset_flag_min_agents = reset_flag_min_agents
        self.reset_flag_on_random = reset_flag_on_random

        self.reset_flag_window = reset_flag_window
        self.reset_flag_min_trades = reset_flag_min_trades

        # Added to allow different mix of agents than 1/2 Buyers and 1/2 Sellers
        # If not provided, uses default of 1/2 B and 1/2 S - backwards compatibility
        if agent_types is None:
            self.agent_types = ('B', 'S')
            self.agent_type_counts = (self.num_traders//2, self.num_traders//2) # // for clarity - should always be int anyhow
            agent_endows = (500, 0) # Buyers start with 500 cash, sellers 0
            agent_payoffs = (self.utility, self.profit) # Buyers have utility, sellers have profit
            if num_traders%2 != 0:
                raise ValueError("The number of agents passed does not conform to the default agent types requirement of being divisible by 2. If you want custom agent type counts, pass in agent_types and agent_type_counts.")
        else:
            if agent_type_counts is None:
                raise ValueError("You must pass the agent_type_counts in if you want to specify custom agent_types.")
            self.agent_types = agent_types
            self.agent_type_counts = agent_type_counts
        
        # Allow lower and upper bound to differ for agent types (type heterogeneity) or by agent (agent heterogeneity)
        if type(lower_bound) is int or type(lower_bound) is float:
            self.lb = (lower_bound,)*self.num_traders
        elif type(lower_bound) is tuple or type(lower_bound) is list:
            if len(lower_bound) == self.num_traders:
                self.lb = lower_bound
            elif len(lower_bound) == len(self.agent_types):
                self.lb = self.relist_to_types(self.agent_types, self.agent_type_counts, lower_bound)
            else:
                raise ValueError("Length of lower_bound on agent values must be the number of agents or agent_types.")
        else:
            raise ValueError("Ambiguous lower_bound on agent values.")
        
        if type(upper_bound) is int or type(upper_bound) is float:
            self.ub = (upper_bound,)*self.num_traders
        elif type(upper_bound) is tuple or type(upper_bound) is list:
            if len(upper_bound) == self.num_traders:
                self.ub = upper_bound
            elif len(upper_bound) == len(self.agent_types):
                self.ub = self.relist_to_types(self.agent_types, self.agent_type_counts, upper_bound)
            else:
                raise ValueError("Length of upper_bound on agent values must be the number of agents or agent_types.")
        else:
            raise ValueError("Ambiguous upper_bound on agent values.")


        # Save agent endowments (money) that they will begin with
        if agent_endows is None:
            raise ValueError("Must specify custom agent_endows when specifying custom agent_types.")
        elif type(agent_endows) is int or type(agent_endows) is float: # Symmetric endowments
            self.agent_endows = (agent_endows,)*self.num_traders
        elif len(agent_endows) == self.num_traders: # Individual endowments per agent
            self.agent_endows = agent_endows
        elif self.agent_types is not None and len(agent_endows) == len(self.agent_types): # Endowments based on type of agent
            self.agent_endows = self.relist_to_types(self.agent_types, self.agent_type_counts, agent_endows)
        else:
            raise ValueError("Cannot pass a list of agent_endows with a length not equal to number of types or number of agents.")

        # Save agent payoffs that they will optimize (or be evaluated against)
        # Note: not duck-typed
        if agent_payoffs is None:
            raise ValueError("Must specify custom agent_payoffs when specifying custom agent_types.")
        elif type(agent_payoffs) is str and (agent_payoffs=="utility" or agent_payoffs=="profit"):
            if agent_payoffs=="utility":
                self.agent_payoffs = (self.utility,)*self.num_traders
            elif agent_payoffs=="profit":
                self.agent_payoffs = (self.profit,)*self.num_traders
        elif type(agent_payoffs) is types.FunctionType:
            self.agent_payoffs = (agent_payoffs, )*self.num_traders
        elif type(agent_payoffs) is tuple or type(agent_payoffs) is list:
            ag_payoffs = []
            p1 = agent_payoffs[0]
            if len(agent_payoffs) == self.num_traders:
                if type(p1) is str:
                    for pn in agent_payoffs:
                        if pn == "utility":
                            ag_payoffs.append(self.utility)
                        elif pn == "profit":
                            ag_payoffs.append(self.profit)
                elif callable(p1):
                    for pn in agent_payoffs:
                        ag_payoffs.append(pn)
            elif len(agent_payoffs) == len(self.agent_types):
                for i in range(len(self.agent_types)):
                    typ_num = self.agent_type_counts[i]
                    for j in range(typ_num):
                        pt = agent_payoffs[i]
                        if type(p1) is str:
                            if pt == "utility":
                                ag_payoffs.append(self.utility)
                            elif pt == "profit":
                                ag_payoffs.append(self.profit)
                        elif callable(p1):
                            ag_payoffs.append(pt)
            self.agent_payoffs = tuple(ag_payoffs)
        else:
            raise ValueError("Ambigiuous defintion for agent_payoffs.")

    def gen_advanced_agents(self, agent_defs, debug=False):
        """
         num_traders, trader_class_count, num_units,
                 grid_size, lower_bound, upper_bound, debug=False, movement_error_rate=0, 
                 reset_flag_frequency="WINDOW", reset_flag_min_agents=None, reset_flag_on_random=True,
                 reset_flag_window=None, reset_flag_min_trades=1, agent_types=None, agent_type_counts=None, agent_endows=None, agent_payoffs=None

        Builds the set of agents for the simulation based on the passed agent_defs DataFrame.
        The DataFrame should be structured as such:
            number_of | type |  lower_bound |   upper_bound | endowment |   strategy | strategy_params | payoff_function
        """
        pass

    def relist_to_types(self, agent_types, agent_type_counts, relist_item):
        blank = np.zeros(self.num_traders)
        t = 0
        for i in range(len(agent_types)):
            typ_num = agent_type_counts[i]
            typ_endow = relist_item[i]
            for j in range(typ_num):
                blank[t] = typ_endow
                t += 1
        return tuple(blank)

    def utility(self, q, m, v, p):
        """Calculates utility payoff
        args:  q = quantity bought
                m = money
                v = list of values
                p = list of prices for goods bought
        """
        sum_v = sum(v[0:q])  # sum first q elements of v
        sum_p = sum(p[0:q])  # sum first q elements of p
        return sum_v + m - sum_p

    def profit(self, q, m, c, p):
        """Calculates profit payoff
        args:  q = quantity sold
                m = money
                c = list of costs
                p = list of prices for goods sold
        """
        sum_c = sum(c[0:q])  # sum first q elements of c
        sum_p = sum(p[0:q])  # sum first q elements of p
        return m + sum_p - sum_c

    def make_test_agents(self):
        """Helper function to initialize test agents"""

        ZID = dm_agents.ZID

        b_1 = ZID('B1', 'BUYER', self.utility, 500, (0, 0), 20, 100)
        b_2 = ZID('B2', 'BUYER', self.utility, 500, (0, 0), 20, 100)
        b_3 = ZID('B3', 'BUYER', self.utility, 500, (0, 0), 20, 100)
        b_4 = ZID('B4', 'BUYER', self.utility, 500, (0, 0), 20, 100)

        s_1 = ZID('S1', 'SELLER', self.profit, 500, (0, 0), 20, 100)
        s_2 = ZID('S2', 'SELLER', self.profit, 500, (0, 0), 20, 100)
        s_3 = ZID('S3', 'SELLER', self.profit, 500, (0, 0), 20, 100)
        s_4 = ZID('S4', 'SELLER', self.profit, 500, (0, 0), 20, 100)

        b_1.set_values([100, 90, 50, 20])
        b_2.set_values([100, 90, 50, 20])
        b_3.set_values([100, 90, 50, 20])
        b_4.set_values([100, 90, 50, 20])

        s_1.set_costs([10, 20, 30, 40])
        s_2.set_costs([10, 20, 30, 40])
        s_3.set_costs([10, 20, 30, 40])
        s_4.set_costs([10, 20, 30, 40])

        self.num_traders = 8
        self.num_units = 4

        self.agents = [b_1, s_1, b_2, s_2, b_3, s_3, b_4, s_4]

    def make_locations(self):
        """Initialize trader locations for make_agents."""
        self.location_list = []
        for i in range(self.num_traders):
            x = rnd.randint(0,self.grid_size-1)
            y = rnd.randint(0,self.grid_size-1)
            self.location_list.append((x, y))
    
    def set_locations(self, grid_size):
        self.grid_size = grid_size
        self.make_locations()
        for loc, agent in zip(self.location_list, self.agents):
            agent.set_location(loc)
     
    
    def gen_res_values(self):
        """Returns a sorted list of values or costs drawn from a sequence of uniform distributions"
            buyer_flag = True if a buyer else a seller
            units = number of draws
        """

        """
        # print("XXX")
        ub = self.ub[agent_index]
        lb = self.lb[agent_index]
        interval = int((ub-lb)/4) # TODO figure out why dividing by 4 here
        if buyer_flag:
            values = []
            upper = ub
            lower = lb + interval
            for unit in range(self.num_units):
                value = np.random.randint(lower, upper+1)
                values.append(value)
            return sorted(values, reverse=True)  # Insures declining marginal value
        else:
            costs = []
            upper = ub - interval
            lower = lb
            for unit in range(self.num_units):
                cost = np.random.randint(lower, upper+1)
                costs.append(cost)
            return sorted(costs, reverse=False)  # Insures increasing marginal cost
        """

        raise ValueError("This function is deprecated. Use the one in agent class.")
    
    def make_agents(self):
        """
        build list self.agents of agent objects
        """

        if debug:
            print("At make agents in make_env")
            print(f"\tMaking off of {self.trader_class_count}")

        self.make_locations() # Put traders at random grid point
        # replicate trade_object total_traders//2 times and put in traders list
        # make a shuffled list of trader objects for trader roles
        traders = []
        for agent_name_number in self.trader_class_count:
            t_name, t_num = agent_name_number
            for k in range(t_num):
                traders.append(t_name)
        assert len(traders) == self.num_traders, f"num_traders {self.num_traders} != length of traders"
        # randomize trader strategies one for each agent
        np.random.shuffle(traders)

        # Assign trader objects to agent type roles and assign values and costs
        self.agents = []
        t = 0 # Agent index (across types)
        for i in range(len(self.agent_types)):
            ag_typ = self.agent_types[i] # Type of agent this is
            typ_ct = self.agent_type_counts[i] # Count of these types of agents
            for j in range(typ_ct):
                sname = f"{ag_typ}_{j+1}" # Name is Type + NumInType (1-indexed)
                trader_role = ag_typ
                payoff = self.agent_payoffs[t]
                money = self.agent_endows[t]
                agent_model = traders[t] # Get agent class
                agent_kind = str(agent_model.__name__) # Get class name
                name = f"{sname}_{agent_kind}"
                location = self.location_list[t]   # get initial location
                # initialize agent with info constructed above
                lb = self.lb[t]; ub = self.ub[t]
                agent = agent_model(name, trader_role, payoff, money, location, 
                                lower_bound = lb, upper_bound = ub,
                                num_units = self.num_units,
                                movement_error_rate=self.movement_error_rate,
                                reset_flag_frequency=self.reset_flag_frequency, 
                                reset_flag_min_agents=self.reset_flag_min_agents,
                                reset_flag_on_random=self.reset_flag_on_random,
                                reset_flag_window = self.reset_flag_window,
                                reset_flag_min_trades = self.reset_flag_min_trades)
                
                # Make Value list or cost list - now inside the agent model
                agent.gen_res_values() # Required for EQ calculation - note now equilibrium is only ex ante equivalent to the realized b/c res values redrawn

                """
                if trader_role == "BUYER" or trader_role == "B":
                    values = self.gen_res_values(True, t)
                    agent.set_values(values)
                elif trader_role == "SELLER" or trader_role == "S":
                    costs = self.gen_res_values(False, t)
                    agent.set_costs(costs)
                """

                # add agent to self.agents list
                self.agents.append(agent)  # List of agent objects
                t += 1


    def get_agents(self):
        return self.agents
       
    def print_agents(self, agent_list):
        for agent in agent_list:
            print(agent)

    def make_market(self, market_name):
        """Make MarketEnviornment object from traders
        """
        # self.build_traders()
        num_side = self.num_traders // 2
        self.market = env.SpotMarketEnvironment(name = market_name, num_buyers = num_side, num_sellers = num_side)
        for index, trader in enumerate(self.agents):
            t_typ = trader.get_type()
            if t_typ == "BUYER" or t_typ == "B":
                values = trader.get_values()
                self.market.add_buyer(index, values)
            if t_typ == "SELER" or t_typ == "S":  # this is a seller
                seller_index = index - num_side  # sellers start at 0 in market environment
                costs = trader.get_costs()
                self.market.add_seller(seller_index, costs)
        self.market.make_demand()
        self.market.make_supply()
        self.market.calc_equilibrium()
    
    def get_market(self):
        return self.market
        
    def show_equilibrium(self):
        self.market.show_equilibrium()

    def plot_market(self):
        self.market.plot_supply_demand(prices=[])
   

if __name__ == "__main__":

    ZID = dm_agents.ZID
    ZIDA = dm_agents.ZIDA

    trader_class_count = [(ZID, 2), (ZIDA, 8)]     # List of artificial traders length 2
    debug = False
    num_traders = 10                  # traders (multiple of two)
    num_units = 4                     # Number of units per trader
    grid_size = 4
    lb = 200  # lower bound of values and costs
    ub = 600  # upper bound of values and costs

    #
    # test agents
    #

    # set up agents
    agent_maker = MakeAgents(num_traders, trader_class_count, num_units, grid_size, lb, ub, debug)
    agent_maker.make_test_agents()
    agents = agent_maker.get_agents()
    agent_maker.print_agents(agents)
    agent_maker.make_locations()

    # set up market
    agent_maker.make_market("test_market")
    agent_maker.show_equilibrium()
    agent_maker.plot_market()

    #
    # random agents
    #

    # set up agents
    agent_r = MakeAgents(num_traders, trader_class_count, num_units, grid_size, lb, ub, debug)
    agent_r.make_agents()
    agents = agent_r.get_agents()
    agent_r.print_agents(agents)

    # set up market
    agent_r.make_market("test_market")
    agent_r.show_equilibrium()
    agent_r.plot_market()



