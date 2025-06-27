import random as rnd
import operator
import matplotlib.pyplot as plt                 # import matplotlib
import numpy as np                              # import numpy
import types
import time
import copy
import os
import json
import pandas as pd

import environment.dm_agents as dm_agents
import environment.dm_env as env
import utils.dm_utils as dm_utils

# Flag for debugging
debug = False

class MakeAgents(object):
    """
    Class to make agents to be used in centralized and decentralized trading.
    
    To create agents, first initialize an instance of MakeAgents, then pass a DataFrame specifying the Agent specifications to init_agents().

    If you do not want to make the DataFrame by hand, you can use two of the methods documented below, which will return a DataFrame formatted as would be required by the init_agents() function

    gen_default_agents (Default Trader Specification)
    1. Default Traders defined by only their trader strategy type, with full symmetry and an equal number of buyers and sellers. Num_traders must equal to the sum across trader types. Requires EVEN trader counts, so num_traders and each class count in trader_class_counts must be even.

    gen_custom_agents (Custom Trader Specification)
    2. Custom Traders for which you can specify value/cost bounds, number of buyers and sellers, endowments, movement error rates, custom strategy behavior (for ZIDA derivatives). Num_traders must equal to the count of all defined traders. 
        
    """
    def __init__(self, debug=False):
        """
        Initialize the MakeAgents objects which allows the creation of agents.

        params
            debug (bool, optional - default = False): Set equal to true if you want to see debug strings printed to the console.
        """

        self.debug = debug  # if True print additional information
        self.agents = [] # Stores agents in the environment
    
    # - TODO: Create a helper function which provides example agents, instead of doing it this way as below!!!!

    def gen_loc(self, grid_size):
        return (np.random.randint(grid_size), np.random.randint(grid_size))

    def get_payoff(self, payoff_name):
        """
        Map a string name for payoff function to the callable payoff function.
        """
        px_map = {
            "utility": self.utility,
            "profit": self.profit
        }
        return px_map[payoff_name]
        

    def gen_default_agents(self, num_traders, trader_class_counts, num_units,
                 grid_size, lower_bound, upper_bound, movement_error_rate=0, strategy_params=None):
        """
        Generate the baseline agents used to test the effects of grid parameters and agent strategy in an otherwise homogenous environment.

        Agents are assumed to be symmetric in all supplied parameters, with the exception of half of each agent class being buyers and half being sellers. Agents also vary in strategy, according to their class.

        Utilizes the gen_custom_agents function. Pushes constructed agent-group level data to the gen_custom_agents function.

        Args:
            num_traders (int): Total number of traders. Must be even. Must be the sum of all values in trader_class_counts
            trader_class_counts: tuple of tuple of (str, int). Format of ((str count),). Defines the number of agents which are of one agent strategy type (agent/trader class). Each count must be even. Half of each kind of agent will be buyers and half sellers. Can also pass a dm_agents.Class instead for niceness.
            num_units (int): The number of units each trader demands (buyers) or supplies (sellers) per week.
            grid_size (int): s as in the sxs dimension of the grid.
            lower_bound (int): The lowest amount that would be demanded for a unit/lowest cost of a unit.
            upper_bound (int): The highest utility for a unit / highest cost for a unit.
            movement_error_rate (double in [0, 1], optional - default 0): The probability that the agent will make a completely random movement decision. Such moves supersede the agent's inherent movement strategy.

        Returns:
            pandas.DataFrame: a dataframe with defined per-agent initialization data. Named ag_df within the function.
            , 
                 reset_flag_frequency="WINDOW", reset_flag_min_agents=None, reset_flag_on_random=True,
                 reset_flag_window=None, reset_flag_min_trades=1):
        """

        """
        ZID = dm_agents.ZID
        ZIDA = dm_agents.ZIDA

        trader_class_counts = [(ZID, 2), (ZIDA, 8)]     # List of artificial traders length 2
        debug = False
        num_traders = 10                  # traders (multiple of two)
        num_units = 4                     # Number of units per trader
        grid_size = 4
        lb = 200  # lower bound of values and costs
        ub = 600  # upper bound of values and costs
        """

        # Check numbers add up correctly, are even
        counted = 0
        if num_traders%2 != 0:
            raise ValueError("The number of traders must be even")
        for tc_i in range(len(trader_class_counts)):
            ag_cl, ag_num = trader_class_counts[tc_i]
            if ag_num%2 != 0:
                raise ValueError("Each agent class definition must contain an even number of agents")
            counted += ag_num
        if num_traders != counted:
            raise ValueError("The number of traders must add up to the number in each type")


        # Translate the traditional agent class definitions to the agent group definitions
        group_defs = []
        for tc_i in range(len(trader_class_counts)):
            ag_cl, ag_num = trader_class_counts[tc_i]

            if type(ag_cl) is not str:
                ag_cl = dm_utils.get_agent_str(ag_cl)
            
            # Divide the trader-class definition group into 2
            g_num = ag_num/2

            # Strategy params only necessary for derivatives of ZIDA and ZIDT
            if strategy_params is None:
                if ag_cl in ['ZIDA', 'ZIDPA', 'ZIDPR']:
                    s_params = {'reset_flag_frequency': 'WINDOW',
                                'reset_flag_window': num_units, # Default window = num units - for lack of a better option (but should be = week length, passed on)
                                'reset_flag_min_trades': 1 # Default at least one trade in window
                    }
                elif ag_cl in ['ZIDT', 'ZIDTR']:
                    pass
            else:
                s_params = strategy_params
                    
            # Define group of Buyers
            gr_b = (g_num, "B", ag_cl, s_params, lower_bound, upper_bound, num_units, 500, "utility", movement_error_rate, None)
            group_defs.append(gr_b)

            # Define group of Sellers
            gr_s = (g_num, "S", ag_cl, s_params, lower_bound, upper_bound, num_units, 0, "profit", movement_error_rate, None)
            group_defs.append(gr_s)
        
        if self.debug:
             print(f"gen_default_agents: Creating Default agents with definitions of: {group_defs}")

        cust_def = self.gen_custom_agents(num_traders, group_defs, grid_size)

        return cust_def

    def gen_custom_agents(self, num_traders, agent_groups, grid_size=None):
        """
        Creates a custom dataframe for advanced agent creation. Requires detailed specification of agent types at the agent-group level.
        
        Specify the num_traders, which is the total number of agents, I. Sum of all counts of groups of group_i agents must sum to I.

        Agent groups are defined as a set of group_i (int count) agents which are all of the same agent_type (buyer, seller), trader_class (strategy), strategy_params (parameters used for strategy-specific configuration), lower_bound, upper_bound, num_units, endowment, payoff_function (str, optional if specifying agent_type, then default to corresponding), movement_error_rate (float optional, default 0), agent_location (optional if specifying grid_size, default None).

        If you do not specify agent_location for agent groups, it is mandatory to specify the grid_size, corresponding to the dimension s of 
        
        Args:
            num_traders (int): 

            agent_groups (tuple of tuple of (group_i (int), agent_type (str), trader_class (str), strategy_params (list), lower_bound (int), upper_bound (int), num_units (int), endowment (int), payoff_function (callable, optional, default None), movement_error_rate (float 0-1, optional default 0), agent_location (tuple of (int, int), optional, default None).

            grid_size (int, optional, default None): s as in the sxs dimension of the grid. Required if any agent_location not specified.

        Returns:
            pandas.DataFrame: a dataframe with defined per-agent initialization data. Named ag_df within the function.
        """

        # Verify number of agents in groups add up to the number of traders
        counted = 0
        for ag_i in range(len(agent_groups)):
            ag_n = agent_groups[ag_i][0]
            counted += ag_n

        agent_defs = []
        ag_j = 0
        # Go over each agent group definition and create the agents
        for ag_i in range(len(agent_groups)):
            ag_group = agent_groups[ag_i]
            ag_n = ag_group[0] # Number of Agents
            ag_t = ag_group[1] # Agent Type (Buyer/Seller)
            ag_cl = ag_group[2] # Agent Class (strategy)
            # Handle the passing of dm_agent classes as class names instead
            if type(ag_cl) is not str:
                ag_cl = dm_utils.get_agent_str(ag_cl)

            ag_sp = ag_group[3] # Agent strategy parameters
            ag_lb = ag_group[4] # Agent lower bound
            ag_ub = ag_group[5] # Agent upper bound
            ag_un = ag_group[6] # Agent's num units
            ag_edw = ag_group[7] # Agent endowment - not used in base model, other than to account for endowment value of selling
            ag_fx = ag_group[8] # Agent payoff function - can be None if agent type is S/Seller or B/Buyer
            if ag_fx is None:
                if ag_t == 'S' or ag_t == 'SELLER':
                    ag_fx = "profit"
                elif ag_t == 'B' or ag_t == 'BUYER':
                    ag_fx = "utility"
            
            ag_me = ag_group[9] # Agent movement error - can be None or 0
            ag_loc = ag_group[10] # Agent location - can be None (if grid_size specified)

            # Create each agent entry for a DF creation
            for li in range(ag_n):
                if ag_loc is None:
                    if grid_size is None:
                        raise ValueError("Cannot provide undefined agent locations without defining the grid_size")
                    al = self.gen_loc(grid_size)
                else:
                    al = ag_loc
                
                # Agent name (Type, index, class)
                ag_nm = f"{ag_t}_{ag_j}_{ag_cl}"
                
                one_row = [ag_nm, ag_t, ag_cl, ag_sp, ag_lb, ag_ub, ag_un, ag_edw, ag_fx, ag_me, al]

                agent_defs.append(one_row)

                ag_j += 1
            
        print(agent_defs)
        ag_df = pd.DataFrame(data = agent_defs, columns=['name', 'type', 'class', 'strategy_params', 'lower_bound', 'upper_bound', 'num_units', 'endowment', 'payoff_function', 'movement_error_rate', 'location'])

        return ag_df


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
        
        """
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

        self.agents = [b_1, s_1, b_2, s_2, b_3, s_3, b_4, s_4]"""
        raise ValueError("env_make_agents.make_test_agents. Unimplemented for new design")

    def randomize_agent_locations(self, grid_size):
        """Initialize trader locations for make_agents."""

        if debug:
            print("env_make_agents: Called make_locations")

        for ag in self.agents:
            x = np.random.randint(0,grid_size) # TODO: Refactor with numpy generator class
            y = np.random.randint(0,grid_size)
            ag.set_location((x, y))
    
    def make_locations(self):
        raise ValueError("env_make_agents.make_locations Deprecated")

    def set_locations(self, grid_size):
        """self.grid_size = grid_size
        self.make_locations()
        for loc, agent in zip(self.location_list, self.agents):
            agent.set_location(loc)"""
        raise ValueError("env_make_agents.set_locations Deprecated")
     
    
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

        raise ValueError("env_make_agents.gen_res_values Deprecated. This function is deprecated. Use the one in agent class.")
    
    def init_agents(self, trader_data):
        """
        Builds the set of agents for the simulation based on the passed agent_defs DataFrame.

        The DataFrame should be structured as such:
            agent_name | type | agent_class | strategy_params |  lower_bound |   upper_bound | endowment | payoff_function | movement_error_rate | location
        """

        # Iterate over the trader_data DataFrame and initiate each agent
        # Agents stored in self.agents (a list)
        self.agents = []
        for ri in range(len(trader_data)):
            r_df = trader_data.iloc[ri]
            n = r_df['name']
            t = r_df['type']
            cl = r_df['class']
            sp = r_df['strategy_params']
            lb = r_df['lower_bound']
            ub = r_df['upper_bound']
            nu = r_df['num_units']
            en = r_df['endowment']
            pf = r_df['payoff_function']
            me = r_df['movement_error_rate']
            loc = r_df['location']

            self.make_one_agent(n, t, cl, sp, lb, ub, nu, en, pf, me, loc)
        
        if self.debug:
            print("Initiated agents in env_make_agents")

    def make_one_agent(self, name, trader_role, agent_class, strat_params,
                       lower_bound, upper_bound, num_units, endow, payoff_fx,
                       mv_error, location):
        """
        Create one agent based on the passed parameters and append it to self.agents.
        """

        """(self, name, trader_type, payoff, money=None, location=None,
                 lower_bound = 0, upper_bound = 9999, num_units=8, movement_error_rate = 0, strategy_params = None, redraw_values = False):"""
        
        ag_cl = dm_utils.get_agent_class(agent_class)
        ag_fx = self.get_payoff(payoff_fx)
        new_agent = ag_cl(name, trader_role, ag_fx, endow, location,
                        lower_bound, upper_bound, num_units,
                        mv_error, strat_params, False)
        new_agent.gen_res_values()
        self.agents.append(new_agent)

    def make_agents(self):
        """
        build list self.agents of agent objects
        """
        
        """if debug:
            print("At make agents in make_env")
            print(f"\tMaking off of {self.trader_class_counts}")

        self.make_locations() # Put traders at random grid point
        # replicate trade_object total_traders//2 times and put in traders list
        # make a shuffled list of trader objects for trader roles
        traders = []
        for ri in trader_data:
             trader
        for agent_name_number in self.trader_class_counts:
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
                sname = f"{ag_typ}_{j+1}"
                name = f"{sname}_{agent_kind}" # Name is Type + NumInType (1-indexed)
                trader_role = ag_typ
                payoff = self.agent_payoffs[t]
                money = self.agent_endows[t]
                agent_model = traders[t] # Get agent class
                agent_kind = str(agent_model.__name__) # Get class name
                
                location = self.location_list[t]   # get initial location
                # initialize agent with info constructed above
                lb = self.lb[t]; ub = self.ub[t]

                
                                reset_flag_frequency=self.reset_flag_frequency, 
                                reset_flag_min_agents=self.reset_flag_min_agents,
                                reset_flag_on_random=self.reset_flag_on_random,
                                reset_flag_window = self.reset_flag_window,
                                reset_flag_min_trades = self.reset_flag_min_trades)
                
                # Make Value list or cost list - now inside the agent model
                agent.gen_res_values() # Required for EQ calculation - note now equilibrium is only ex ante equivalent to the realized b/c res values redrawn

                # add agent to self.agents list
                self.agents.append(agent)  # List of agent objects
                t += 1
            """
        raise ValueError("env_make_agents.make_agents Deprecated")

    def get_agents(self):
        """Getter for agents list"""
        return self.agents
       
    def print_agents(self, agent_list):
        """Print agents."""
        for agent in agent_list:
            print(agent)

    def make_market(self, market_name="env_spot_market"):
        """
        Make MarketEnviornment object from traders.
        
        This market is a spot market with all agents in the same location - gives the max efficiency (globally).
        """
        
        # Count number of buyers and sellers
        b_num = 0; s_num = 0
        for ag in self.agents:
            tp = ag.get_type()
            if tp in ['B', 'BUYER']:
                b_num+=1
            elif tp in ['S', 'SELLER']:
                s_num+=1
        
        # Create the spot market
        self.market = env.SpotMarketEnvironment(name = market_name, num_buyers = b_num, num_sellers = s_num)
        b_ind = 0; s_ind = 0
        for index, trader in enumerate(self.agents):
            t_typ = trader.get_type()
            
            # Add a buyer
            if t_typ == "BUYER" or t_typ == "B":
                values = trader.get_values()
                self.market.add_buyer(b_ind, values)
                b_ind += 1
            
            # Add a seller
            elif t_typ == "SELLER" or t_typ == "S":
                costs = trader.get_costs()
                self.market.add_seller(s_ind, costs)
                s_ind += 1

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

    trader_class_counts = [("ZID", 10)]     # List of artificial traders length 2
    debug = True
    num_traders = 10                  # traders (multiple of two)
    num_units = 4                     # Number of units per trader
    grid_size = 4
    lb = 200  # lower bound of values and costs
    ub = 600  # upper bound of values and costs

    #
    # ZID test agents
    #

    # set up agents
    ag1 = MakeAgents(debug)
    ag_df = ag1.gen_default_agents(num_traders, trader_class_counts, num_units, grid_size, lb, ub)
    ag1.init_agents(ag_df)
    # agent_maker.make_test_agents()
    agents = ag1.get_agents()
    ag1.print_agents(agents)
    # agent_maker.make_locations()

    # set up market
    ag1.make_market("test_market")
    ag1.show_equilibrium()
    ag1.plot_market()

    #
    # ZIDA test agents
    #

    trader_class_counts = [("ZIDA", 10)]

    # set up agents
    ag2 = MakeAgents(debug)
    ag_df = ag2.gen_default_agents(num_traders, trader_class_counts, num_units, grid_size, lb, ub)
    ag2.init_agents(ag_df)
    # agent_maker.make_test_agents()
    agents = ag2.get_agents()
    ag2.print_agents(agents)

    # set up market
    ag2.make_market("test_market")
    ag2.show_equilibrium()
    ag2.plot_market()

    # Custom ZIDA agents
    ag3 = MakeAgents(debug)
    ag_df = ag3.gen_default_agents(num_traders, trader_class_counts, num_units, grid_size, lb, ub)




