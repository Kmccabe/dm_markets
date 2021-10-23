import random as rnd
import operator
import matplotlib.pyplot as plt                 # import matplotlib
import numpy as np                              # import numpy
import time
import copy
import os
import json

import dm_agents
import dm_env as env


class MakeAgents(object):
    """Class to make agents to be used in centralized and decentralized trading"""
    def __init__(self, num_traders, trader_types, num_units, debug):
        self.trader_types = trader_types     # list of two trader types, should be tuple
        self.num_traders = num_traders       # number of traders divisible by two
        self.num_units = num_units           # number of units, same for all traders
        self.debug = debug                   # if True print additional information
        self.agents = []                     # contains list of agents 
        self.market = None

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

        ZID = self.trader_types[0]

        b_1 = ZID('B1', 'BUYER', self.utility, 500, (0, 0))
        b_2 = ZID('B2', 'BUYER', self.utility, 500, (1, 2))
        b_3 = ZID('B3', 'BUYER', self.utility, 500, (0, 0))
        b_4 = ZID('B4', 'BUYER', self.utility, 500, (1, 2))

        s_1 = ZID('S1', 'SELLER', self.profit, 500, (0, 0))
        s_2 = ZID('S2', 'SELLER', self.profit, 500, (2, 1))
        s_3 = ZID('S3', 'SELLER', self.profit, 500, (0, 0))
        s_4 = ZID('S4', 'SELLER', self.profit, 500, (2, 1))

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
    
    def show_equilibrium(self):
        self.market.show_equilibrium()

    def plot_market(self):
        self.market.plot_supply_demand(prices=[])
   

if __name__ == "__main__":

    ZID = dm_agents.ZID
    ZIDA = dm_agents.ZIDA

    trader_objects = [ZID, ZIDA]     # List of artificial traders length 2
    debug = False
    num_traders = 10                  # traders (multiple of two)
    num_units = 8                     # Number of units per trader

    # set up agents
    agent_maker = MakeAgents(num_traders, trader_objects, num_units, debug)
    agent_maker.make_test_agents()
    agents = agent_maker.get_agents()
    agent_maker.print_agents(agents)

    # set up market
    agent_maker.make_market("test_market")
    agent_maker.show_equilibrium()
    agent_maker.plot_market()


