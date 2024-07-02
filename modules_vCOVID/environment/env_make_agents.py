import random as rnd
import operator
import matplotlib.pyplot as plt                 # import matplotlib
import numpy as np                              # import numpy
import time
import copy
import os
import json

import environment.dm_agents as dm_agents
import environment.dm_env as env

# Flag for debugging
debug = False

class MakeAgents(object):
    """Class to make agents to be used in centralized and decentralized trading"""
    def __init__(self, num_traders, trader_types, num_units,
                 grid_size, lower_bound, upper_bound, debug=False, movement_error_rate=0, 
                 reset_flag_frequency=None, reset_flag_min_agents=None, reset_flag_on_random=None,
                 reset_flag_window=None, reset_flag_min_trades=1):

        self.trader_types = trader_types     # list of two trader types, should be tuple
        self.num_traders = num_traders       # number of traders divisible by two
        self.num_units = num_units           # number of units, same for all traders
        self.debug = debug                   # if True print additional information
        self.grid_size = grid_size           # grid is grid_size x grid_size
        self.lb = lower_bound
        self.ub = upper_bound
        self.agents = []                     # contains list of agents
        self.location_list = []
        self.market = None
        self.movement_error_rate = movement_error_rate
        self.reset_flag_frequency = reset_flag_frequency
        self.reset_flag_min_agents = reset_flag_min_agents
        self.reset_flag_on_random = reset_flag_on_random

        self.reset_flag_window = reset_flag_window
        self.reset_flag_min_trades = reset_flag_min_trades
        

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
     
    
    def gen_res_values(self, buyer_flag):
        """Returns a sorted list of values or costs drawn from a sequence of uniform distributions"
            buyer_flag = True if a buyer else a seller
            units = number of draws
        """
        interval = int((self.ub-self.lb)/4)
        if buyer_flag:
            values = []
            upper = self.ub
            lower = self.lb + interval
            for unit in range(self.num_units):
                value = np.random.randint(lower, upper+1)
                values.append(value)
            return sorted(values, reverse=True)  # Insures declining marginal value
        else:
            costs = []
            upper = self.ub - interval
            lower = self.lb
            for unit in range(self.num_units):
                cost = np.random.randint(lower, upper+1)
                costs.append(cost)
            return sorted(costs, reverse=False)  # Insures increasing marginal cost

    def make_agents(self):
        """
        build list self.agents of agent objects
        """

        if debug:
            print("At make agents in make_env")
            print(f"\tMaking off of {self.trader_types}")

        self.make_locations() # Put traders at random grid point
        # replicate trade_object total_traders//2 times and put in traders list
        # make a shuffled list of trader objects for trader roles
        traders = []
        for agent_name_number in self.trader_types:
            t_name, t_num = agent_name_number
            for k in range(t_num):
                traders.append(t_name)
        assert len(traders) == self.num_traders, f"num_traders {self.num_traders} != length of traders"
        # randomize trader strategies one for each agent
        np.random.shuffle(traders)

        # Assign trader objects to buyer/seller roles and assign values and costs
        self.agents = []
        for t in range(self.num_traders):
            # make buyer and seller name, intitialize type, set money endowment
            name = f"B_{t+1}"
            trader_role = "BUYER"
            payoff = self.utility  
            money = 500
            if t >= self.num_traders // 2:
                name = f"S_{t + 1 - self.num_traders // 2}"
                trader_role = "SELLER"
                payoff = self.profit            
            agent_model = traders[t] # Get agent class  
            # Get agent class name
            agent_kind = str(agent_model.__name__)
            name = f"{name}_{agent_kind}"
            location = self.location_list[t]   # get initial location
            # initialize agent with info constructed above
            agent = agent_model(name, trader_role, payoff, money, location, 
                                lower_bound = self.lb, upper_bound = self.ub, 
                                movement_error_rate=self.movement_error_rate,
                                reset_flag_frequency=self.reset_flag_frequency, 
                                reset_flag_min_agents=self.reset_flag_min_agents,
                                reset_flag_on_random=self.reset_flag_on_random,
                                reset_flag_window = self.reset_flag_window,
                                reset_flag_min_trades = self.reset_flag_min_trades)
            # Make Value list or cost list
            if agent.get_type() == "BUYER":
                values = self.gen_res_values(True)
                agent.set_values(values)
            else:
                costs = self.gen_res_values(False)
                agent.set_costs(costs)
            # add agent to self.agents list
            self.agents.append(agent)  # List of agent objects


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
            if trader.get_type() == "BUYER":
                values = trader.get_values()
                self.market.add_buyer(index, values)
            else:  # this is a seller
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

    trader_objects = [(ZID, 2), (ZIDA, 8)]     # List of artificial traders length 2
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
    agent_maker = MakeAgents(num_traders, trader_objects, num_units, grid_size, lb, ub, debug)
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
    agent_r = MakeAgents(num_traders, trader_objects, num_units, grid_size, lb, ub, debug)
    agent_r.make_agents()
    agents = agent_r.get_agents()
    agent_r.print_agents(agents)

    # set up market
    agent_r.make_market("test_market")
    agent_r.show_equilibrium()
    agent_r.plot_market()



