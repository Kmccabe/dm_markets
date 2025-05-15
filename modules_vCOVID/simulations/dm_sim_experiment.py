import sys
sys.path.insert(0, '..') # add modules folder (parent folder) into this notebook's path
import environment.dm_agents as dm_agents
import numpy as np
import pandas as pd
import copy
import simulations.dm_sim as simulate
import utils.dm_process_results as results
import environment.env_make_agents as make_env

def change_agents(agents, ratio=1):
    ZIDPR = dm_agents.ZIDPR
    """
    make a copy of agents at current location and change strategy to ZIDPR
    """

    # Pick a random set of agents to mutate (randomly at passed proportion - policy compliance rate)
    rn = np.random.default_rng()
    agent_indecies = list(range(len(agents)))
    complying_num = len(agents)*ratio
    non_int_part = complying_num%1
    add_num = 0
    if non_int_part != 0:
        # Randomly draw against remainder (keeps percetanges work across trials)
        if rn.random() < non_int_part:
            add_num += 1
            
    complying_num = int(complying_num) + add_num
    complying_inds = rn.choice(agent_indecies, size=complying_num)
    
    new_agents = []
    for k, agent in enumerate(agents):
        # change name
        if k in complying_inds: # These ones get Transformed
            name = agent.name
            s1 = name.split('_')
            name = s1[0] + '_' + s1[1] + '_ZIDPR'

            trader_type = agent.type
            payoff = agent.payoff
            money = agent.money
            location = agent.location
            lower_bound = agent.lower_bound
            upper_bound = agent.upper_bound
            move_error_rate = agent.movement_error_rate 
            # Added New
            cont_flag = agent.contract_this_period
            reset_flag_frequency = agent.reset_flag_frequency
            reset_flag_min_agents = agent.reset_flag_min_agents
            reset_flag_on_random = agent.reset_flag_on_random
            reset_flag_window = agent.reset_flag_window
            reset_flag_min_trades = agent.reset_flag_min_trades
            # make a ZIDPR agent
            new_agent = dm_agents.ZIDPR(name, trader_type, payoff, money, location, 
                                   lower_bound, upper_bound, move_error_rate, reset_flag_frequency, reset_flag_min_agents,
                                    reset_flag_on_random, reset_flag_window, reset_flag_min_trades)

            # For Week Flag Rule
            new_agent.trades_this_week = agent.trades_this_week
        
            # For Window flag Rule
            new_agent.current_period = agent.current_period
            new_agent.periods_traded_in = agent.periods_traded_in # test x1
            
            new_agent.set_contract_this_period(cont_flag)
        
            nag_typ = new_agent.get_type()
            if nag_typ == "BUYER" or nag_typ == "B":
                vals = agent.get_values()
                new_agent.set_values(vals)
            elif nag_typ == "SELLER" or nag_typ == "S":
                cos = agent.get_costs()
                new_agent.set_costs(cos)
        else: # These ones do not
            new_agent = copy.deepcopy(agent)
            
        new_agents.append(new_agent)
        
    return new_agents

def change_back_agents(agents):
    
    ZIDPA = dm_agents.ZIDPA
    """Returns agents to type ZIDPA"""
    new_agents = []
    
    for k, agent in enumerate(agents):
        # change name
        name = agent.name
        s1 = name.split('_')
        name = s1[0] + '_' + s1[1] + '_ZIDPA'

        trader_type = agent.type
        payoff = agent.payoff
        money = agent.money
        location = agent.location
        lower_bound = agent.lower_bound
        upper_bound = agent.upper_bound
        cont_flag = agent.contract_this_period
        move_error_rate = agent.movement_error_rate 
        
        # Determine the rule (of thumb, here) by which to reset the flag for satisfaction with location (i.e. move or not)
        reset_flag_frequency = agent.reset_flag_frequency
        reset_flag_min_agents = agent.reset_flag_min_agents
        reset_flag_on_random = agent.reset_flag_on_random
        reset_flag_window = agent.reset_flag_window
        reset_flag_min_trades = agent.reset_flag_min_trades
        # make a ZIDPA agent
        new_agent = dm_agents.ZIDPA(name, trader_type, payoff, money, location, 
                                   lower_bound, upper_bound, move_error_rate, reset_flag_frequency, reset_flag_min_agents,
                                    reset_flag_on_random, reset_flag_window, reset_flag_min_trades)
        
        new_agent.set_contract_this_period(cont_flag)

        # For Week Flag Rule
        new_agent.trades_this_week = agent.trades_this_week
        
        # For Window flag Rule
        new_agent.current_period = agent.current_period
        new_agent.periods_traded_in = agent.periods_traded_in # test x1
        
        nag_typ = new_agent.get_type()
        if nag_typ == "BUYER" or nag_typ == "B":
            vals = agent.get_values()
            new_agent.set_values(vals)
        elif nag_typ == "SELLER" or nag_typ == "S":
            cos = agent.get_costs()
            new_agent.set_costs(cos)
        
        new_agents.append(new_agent)
        
    return new_agents

# TODO redo adding data to the dataframe using CONCAT instead of building a long string and then adding - speed increase probable
def make_event_sim(sim_name, num_periods, num_weeks,
             event_begin, event_end, market, agents,
             num_rounds, grid_size,
             num_traders, num_units,
             lower_bound, upper_bound,
             trader_class_count, movement_error_rate=0, compliance_rate=1, return_df=False, return_period_df=False, reset_flag_frequency=None, reset_flag_min_agents=None,
             reset_flag_on_random=False, reset_flag_window=None, reset_flag_min_trades=1,
             agent_types=None, agent_type_counts=None, agent_endows=None, agent_payoffs=None):
    """Runs one complete simulation and returns data in
        effs[treatment][trial].  Causes epidemic event from event_begin to event_end
        return_df = True -> return as dataframe
    """ 

    # Added for backwards compatibility
    if agent_types is None:
        agent_types = ('B','S')
        agent_type_counts = (num_traders//2, num_traders//2)
        agent_endows = (500, 0)
        agent_payoffs = ('utility', 'profit')

    if return_df:
        # Store parameters
        df_cols_param = ['sim_name', 'num_traders', 'num_units', 'num_weeks', 'num_periods', 'num_rounds', 'grid_size', 'lower_bound', 'upper_bound', 'trader_class_count', 'movement_error_rate', 'compliance_rate', 
                         'event_begin', 'event_end', 'agent_types', 'agent_type_counts', 'agent_endows', 'agent_payoffs']
        # Store results
        df_cols_results = ['week', 'contracts', 'grids', 'eff', 'type_effs']
        df_cols = df_cols_param + df_cols_results
        df_data = []

    if return_period_df:
        if return_df:
            df_period_cols = df_cols + ['period'] + ['period_locs']
            df_period_data = []
        else:
            raise ValueError("Need to pass return_df=True with return_period_df=True")
    
    data = {}
    for week in range(num_weeks):
        
        if week == event_begin:
            agents = change_agents(agents, compliance_rate)
        if week == event_end:
            agents = change_back_agents(agents)
            
        data[week] = {}
        for agent in agents:
            agent.start(None)
        contracts = []
        sim_grids = []
        sim1 = simulate.SimPeriod(sim_name, num_rounds, agents, 
               market, grid_size)
        
        for period in range(num_periods):
            sim1.run_period()
            grid = sim1.get_grid()
            sim_grids.append(grid)
            contracts.extend(sim1.get_contracts())

            if return_period_df:
                if week == 0 and period == 0: # If you are at the first point in the simulation - save the initial grid at the week=-1, period=-1
                    period_data = [sim_name, num_traders, num_units, num_weeks, num_periods, num_rounds, grid_size, lower_bound, upper_bound, trader_class_count, movement_error_rate, compliance_rate, event_begin, event_end, agent_types, agent_type_counts, agent_endows, agent_payoffs, -1, 
                             (), copy.deepcopy(sim1.get_initial_grid()), None, None, -1, copy.deepcopy(sim1.get_initial_grid())]
                    df_period_data.append(period_data)

                period_data = [sim_name, num_traders, num_units, num_weeks, num_periods, num_rounds, grid_size, lower_bound, upper_bound, trader_class_count, movement_error_rate, compliance_rate, event_begin, event_end, agent_types, agent_type_counts, agent_endows, agent_payoffs, week, 
                         sim1.get_contracts(), grid, None, None, period, copy.deepcopy(grid)]
                df_period_data.append(period_data)
        
        data[week]['contracts'] = contracts
        data[week]['grids'] = sim_grids
        
        # process results
        pr1 = results.ProcessResults(market, sim_name, agents, contracts)
        pr1.calc_efficiency()
        pr1.get_results()
        eff = pr1.get_efficiency()
        type_eff = pr1.get_type_surplus()
        data[week]['eff'] = eff # single item put in list to faciliatate looping through data 
        data[week]['type_effs'] = type_eff

        if return_df:
            week_data = [sim_name, num_traders, num_units, num_weeks, num_periods, num_rounds, grid_size, lower_bound, upper_bound, trader_class_count, movement_error_rate, compliance_rate, event_begin, event_end, agent_types, agent_type_counts, agent_endows, agent_payoffs, week, 
                         contracts, sim_grids, eff, type_eff]
            df_data.append(week_data)

    if return_df:
        df_out = pd.DataFrame(data=df_data, columns=df_cols)
        if return_period_df:
            period_df_out = pd.DataFrame(data=df_period_data, columns=df_period_cols)
            return df_out, period_df_out
        else:
            return df_out
    else:
        return data


def make_event_monte_carlo(sim_name, num_trials, num_periods, num_weeks,
                    event_begin, event_end,
                    num_rounds, grid_size,
                    num_traders, num_units,
                    lower_bound, upper_bound,
                    trader_class_count, movement_error_rate=0, compliance_rate=1, return_df=False, return_period_df=False, reset_flag_frequency=None, reset_flag_min_agents=None,
                    reset_flag_on_random=False, reset_flag_window=None, reset_flag_min_trades=1, agent_types=None, agent_type_counts=None, agent_endows=None, agent_payoffs=None):
    """Runs one complete simulation and returns data in
        effs[treatment][trial]
        compliance_rate = ratio of agents complying with social distancing, e[0, 1]
        movement_error_rate = ratio of FULLY random moves, not employing strategy of movement, e[0, 1]
        return_df = True -> return as dataframe
    """ 

    # Added for backwards compatibility
    if agent_types is None:
        agent_types = ('B','S')
        agent_type_counts = (num_traders//2, num_traders//2)
        agent_endows = (500, 0)
        agent_payoffs = ('utility', 'profit')

    sim_data = {}
    sim_data['parms'] = {'sim_name': sim_name, 'num_traders': num_traders, 'num_units': num_units,
                         'num_weeks': num_weeks, 'num_periods': num_periods, 'num_rounds': num_rounds,
                         'grid_size': grid_size, 'lower_bound':lower_bound, 'upper_bound': upper_bound,
                         'trader_class_count': trader_class_count, 'movement_error_rate': movement_error_rate, 'compliance_rate': compliance_rate,
                         'agent_types': agent_types, 'agent_type_counts':agent_type_counts, 'agent_endows':agent_endows, 'agent_payoffs':agent_payoffs}

    if return_df:
        # Store parameters
        df_cols_param = ['sim_name', 'num_traders', 'num_units', 'num_weeks', 'num_periods', 'num_rounds', 'grid_size', 'lower_bound', 'upper_bound', 'trader_class_count', 'movement_error_rate', 'compliance_rate',
                        'event_begin', 'event_end', 'agent_types', 'agent_type_counts', 'agent_endows', 'agent_payoffs']
        # Store outputs
        df_cols_results = ['week', 'contracts', 'grids', 'eff', 'type_effs']
        df_cols_trial = ['trial']
        df_cols = df_cols_param + df_cols_results + df_cols_trial
        df_out = pd.DataFrame(columns=df_cols)

    if return_period_df:
        if return_df:
            period_out_df = pd.DataFrame(columns=df_out.columns)
        else:
            raise ValueError("Need to be in return_df=True mode to get period details")
        
    # Run n trials of this setup
    for trial in range(num_trials):

        agent_maker = make_env.MakeAgents(num_traders, trader_class_count, num_units, 
                                            grid_size, lower_bound, upper_bound, False, movement_error_rate, reset_flag_frequency=reset_flag_frequency, 
                                            reset_flag_min_agents=reset_flag_min_agents, reset_flag_on_random=reset_flag_on_random, reset_flag_window=reset_flag_window, 
                                          reset_flag_min_trades=reset_flag_min_trades, agent_types=None, agent_type_counts=None, agent_endows=None, agent_payoffs=None)
        agent_maker.make_agents()
        agent_maker.set_locations(grid_size)
        agents = agent_maker.get_agents()

        # set up market
        agent_maker.make_market(sim_name)
        market = agent_maker.get_market()

        if not return_period_df: # If only want the week-by-week results
            trial_data = make_event_sim(sim_name, num_periods, num_weeks, 
                                        event_begin, event_end, market, agents,
                                        num_rounds, grid_size,
                                        num_traders, num_units,
                                        lower_bound, upper_bound,
                                        trader_class_count, movement_error_rate, compliance_rate, return_df, reset_flag_frequency=reset_flag_frequency, 
                                            reset_flag_min_agents=reset_flag_min_agents, reset_flag_on_random=reset_flag_on_random, reset_flag_window=reset_flag_window, 
                                        reset_flag_min_trades=reset_flag_min_trades, 
                                        agent_types=agent_types, agent_type_counts=agent_type_counts, agent_endows=agent_endows, agent_payoffs=agent_endows)
        else: # If want the period-by-period results
            trial_data, trial_period_data = make_event_sim(sim_name, num_periods, num_weeks, 
                            event_begin, event_end, market, agents,
                            num_rounds, grid_size,
                            num_traders, num_units,
                            lower_bound, upper_bound,
                            trader_class_count, movement_error_rate, compliance_rate, return_df, return_period_df, reset_flag_frequency=reset_flag_frequency, 
                                            reset_flag_min_agents=reset_flag_min_agents, reset_flag_on_random=reset_flag_on_random, reset_flag_window=reset_flag_window, 
                                                           reset_flag_min_trades=reset_flag_min_trades,
                                                           agent_types=agent_types, agent_type_counts=agent_type_counts, agent_endows=agent_endows, agent_payoffs=agent_endows)
            
        sim_data[trial] = trial_data

        if return_df:
            trial_data['trial'] = trial
            if len(df_out) == 0:
                df_out = trial_data
            else:
                df_out = pd.concat([df_out, trial_data], ignore_index=True)
                
        if return_period_df:
            trial_period_data['trial'] = trial
            if len(period_out_df) == 0:
                period_out_df = trial_period_data
            else:
                period_out_df = pd.concat([period_out_df, trial_period_data], ignore_index=True)
    
    if return_df:
        df_out = df_out.reset_index(drop=True)
        df_out['num_trials'] = num_trials
        if return_period_df:
            period_out_df = period_out_df.reset_index(drop=True)
            period_out_df['num_trials'] = num_trials
            return df_out, period_out_df
        else:
            return df_out
    else:
        return sim_data

