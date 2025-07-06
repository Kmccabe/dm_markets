# import random as rnd
# import operator
# import os
import matplotlib.pyplot as plt                 # import matplotlib
# import numpy as np                              # import numpy
# import time
# import copy
# import json
from scipy.stats import sem

# This works only if notebook is in same folder
# import dm_bargain
# import dm_travel
import environment.dm_agents
#import dm_env as env
# import dm_utils as dm
import simulations.dm_sim_period as simp
import utils.dm_process_results as pr
import environment.env_make_agents as agent_mkr

import copy
import pandas as pd

def make_sim(sim_name, num_weeks, num_periods, num_rounds, 
             num_traders, agent_groups, 
             grid_size=None, group_names=None,
             return_df=False, return_period_df=False, debug=False):
    
    """Runs one complete simulation and returns data in
        effs[treatment][trial]
    """ 

    if return_df:
        # Store parameters
        df_cols_param = ['sim_name', 
                         'num_weeks', 'num_periods', 'num_rounds', 
                         'num_traders', 'agent_groups',
                         'grid_size', 'group_names']
        # Store results
        df_cols_results = ['week', 'contracts', 'grids', 'eff', 'class_surplus', 'group_surplus']
        df_cols = df_cols_param + df_cols_results
        df_data = []

    if return_period_df:
        # Add columns for period data
        if return_df:
            df_period_cols = df_cols + ['period'] + ['period_locs']
            df_period_data = []
        else:
            raise ValueError("Cannot request period_df without passing return_df=True")
    
    if group_names is None:
        group_names = [None]*len(agent_groups)

    # data table for simulation
    data = {}

    # make agents
    debug = False
    agent_maker = agent_mkr.MakeAgents(debug)
    ag_df = agent_maker.gen_custom_agents(num_traders, agent_groups, grid_size, group_names)
    agent_maker.init_agents(ag_df)
    agents = agent_maker.get_agents()
  
    # set up market
    agent_maker.make_market(sim_name)
    market = agent_maker.get_market()

    # run sim
    for week in range(num_weeks):
        data[week] = {}
        for agent in agents:
            agent.start(None)

            if debug:
                print(agent.get_name(), ":", agent.get_values())

        contracts = []
        sim_grids = []
        sim1 = simp.SimPeriod(sim_name, num_rounds, agents, 
               market, grid_size)
        for period in range(num_periods):
            sim1.run_period()
            grid = sim1.get_grid()
            sim_grids.append(grid)
            pr_contracts = sim1.get_contracts()
            contracts.extend(pr_contracts)

            # NOTE: can refactor this to be more memory and compute efficient - track ONLY period and week data
            # Add in control data LATER
            # Consider casting agent_groups to str or similar before adding to DF

            # Save period-by-period data to dataframe
            if return_period_df:
                period_data = [sim_name, 
                               num_weeks, num_periods, num_rounds,
                               num_traders, agent_groups,
                               grid_size, group_names,
                               week,
                               pr_contracts, grid, 
                               None, None, None, # End week columns
                               period, copy.deepcopy(grid)]
                df_period_data.append(period_data)

                # Save the initial locations of the agents
                if week == 0 and period == 0:
                    period_data = [sim_name, 
                                   num_weeks, num_periods, num_rounds,
                                   num_traders, agent_groups,
                                   grid_size, group_names,
                                   -1, [], copy.deepcopy(sim1.get_initial_grid()),
                                   None, None, None,
                                   -1, copy.deepcopy(sim1.get_initial_grid())]
                    df_period_data.append(period_data)
        
        data[week]['contracts'] = contracts
        data[week]['grids'] = sim_grids
        
        # process results
        pr1 = pr.ProcessResults(market, sim_name, agents, contracts)
        pr1.calc_efficiency()
        pr1.get_results()
        eff = pr1.get_efficiency()
        class_surplus = pr1.get_class_surplus()
        group_surplus = pr1.get_group_surplus()
        data[week]['eff'] = eff # single item put in list to facilitate looping through data 
        data[week]['class_surplus'] = class_surplus
        data[week]['group_surplus'] = group_surplus

        # Save week-by-week data to dataframe
        if return_df:
            week_data = [sim_name,
                         num_weeks, num_periods, num_rounds,
                         num_traders, agent_groups,
                         grid_size, group_names,
                         week, contracts, sim_grids,
                         eff, class_surplus, group_surplus]
            df_data.append(week_data)
    
    if return_df:
        df_out = pd.DataFrame(data=df_data, columns=df_cols)
        if return_period_df:
            period_df_out = pd.DataFrame(data=df_period_data, columns=df_period_cols)
            return df_out, period_df_out
        else:
            return  df_out
    else:
        return data


def make_monte_carlo(sim_name=None, 
                     num_trials=None, num_weeks=None, num_periods=None, num_rounds=None, 
                     num_traders=None, agent_groups=None, grid_size=None, group_names=None, 
                     return_df=False, return_period_df=False,
                     passed_as_dict=False,
                     params_dict=None):
    """
    Runs one complete simulation and returns weekly data in
        effs[treatment][trial] or in a DataFrame. Can return period-level data in a DataFrame as well.

    Can provide the parameters as a dictionary instead, but must pass passed_as_dict = True and params_dict = dictionary of parameters.
    """ 

    # Check vals
    passed_none = [sim_name is None,
                       num_trials is None,
                       num_weeks is None,
                       num_periods is None,
                       num_rounds is None,
                       num_traders is None,
                       agent_groups is None,
                       grid_size is None] # group_names remains optional

    # If not passed_as_dict, need each val passed in
    if not passed_as_dict and any(passed_none):
        raise ValueError("If not passing values as a dictionary, you must pass all of sim_name, num_trials, num_weeks, num_periods, num_rounds, num_traders, agent_groups, grid_size.")
    
    # If passed_as_dict, check dict was passed and contains all required items
    if passed_as_dict:
        if params_dict is None:
            raise ValueError("Must pass a dictionary of parameters to params_dict if passing passed_as_dict=True")
        try:
            params_dict['sim_name']
            params_dict['num_trials']
            params_dict['num_weeks']
            params_dict['num_periods']
            params_dict['num_rounds']
            params_dict['num_traders']
            params_dict['agent_groups']
            params_dict['grid_size']
            params_dict['group_names']
        except KeyError:
            raise ValueError("params_dict must contain all of sim_name, num_trials, num_weeks, num_periods, num_rounds, num_traders, agent_groups, grid_size.")
        
        # If passing all checks - unwrap params_dict
        sim_name = params_dict['sim_name']
        num_trials = params_dict['num_trials']
        num_weeks = params_dict['num_weeks']
        num_periods = params_dict['num_periods']
        num_rounds = params_dict['num_rounds']
        num_traders = params_dict['num_traders']
        agent_groups = params_dict['agent_groups']
        grid_size = params_dict['grid_size']
        group_names = params_dict['group_names']

    if group_names is None:
        group_names = [None]*len(agent_groups)

    sim_data = {}
    sim_data['params'] = {'sim_name': sim_name, 
                          'num_trials': num_trials,
                          'num_weeks': num_weeks, 'num_periods': num_periods, 
                          'num_rounds': num_rounds,
                          'num_traders': num_traders,
                          'agent_groups': agent_groups, 'grid_size': grid_size,
                          'group_names': group_names}

    # Stubs for storing df results
    if return_df:        
        mc_df = None

        if return_period_df:
            mc_period_df = None

    # run num_trials number of simulations with the provided configuration
    for trial in range(num_trials):

        # Return non-DF
        if not return_df:
            trial_data = make_sim(sim_name, 
                                    num_weeks, num_periods, num_rounds, 
                                    num_traders, agent_groups, grid_size, group_names)
            sim_data[trial] = trial_data

        
        # Return DF
        elif return_df:

            # Return period-level DF data
            if return_period_df:
                trial_df, trial_period_df = make_sim(sim_name,
                                                         num_weeks, num_periods, num_rounds, 
                                                         num_traders, agent_groups, 
                                                         grid_size, group_names,
                                                         return_df, return_period_df)
                trial_period_df['trial'] = trial
                
                # Store trial's period DF
                if mc_period_df is None:
                    mc_period_df = trial_period_df
                else:
                    mc_period_df = pd.concat([mc_period_df, trial_period_df], ignore_index=True)

            # Keep non-period data
            elif not return_period_df:
                trial_df = make_sim(sim_name,
                                        num_weeks, num_periods, num_rounds, 
                                        num_traders, agent_groups, 
                                        grid_size, group_names,
                                        return_df)
            
            trial_df['trial'] = trial

            # Store Trial DF
            if mc_df is None:
                mc_df = trial_df
            else:
                mc_df = pd.concat([mc_df, trial_df], ignore_index=True)

    # Return results with requested 
    if return_df:
        if return_period_df:
            return mc_df, mc_period_df
        elif not return_period_df:
            return mc_df
    else:
        return sim_data

# Analyze Efficiency Data
def analyze_eff_data(num_trials, num_weeks, data_table):
    
    # Set up arrays to parse data into weeks
    week_effs = []
    eff_avg = []

    for week in range(num_weeks):
        eff_avg.append(0)
        week_effs.append([])
    
    # parse efficiencies
    data = []
    for trial in range(num_trials):
        effs = []
        trial_data = data_table[trial]
        for week in range(num_weeks):
            week_data = trial_data[week]
            effs.append(week_data['eff'])
        data.append(effs)   

    # process efficiencies
    for trial_effs in data:
        for k, eff in enumerate(trial_effs):
            eff_avg[k] += eff
            week_effs[k].append(eff)
            
    # calculate avg, min, max, and sem for each week
    std_errors = []
    eff_min = []
    eff_max = []
    for k in range(num_weeks):
        eff_avg[k] /= num_trials
        std_error = sem(week_effs[k])
        std_errors.append(std_error)
        eff_min.append(min(week_effs[k]))
        eff_max.append(max(week_effs[k]))

    return eff_avg, std_errors, eff_min, eff_max

def get_trial_week_effs(num_trials, num_weeks, data_table):

    # Set up arrays to parse data into weeks
    week_effs = []
    eff_avg = []

    for week in range(num_weeks):
        eff_avg.append(0)
        week_effs.append([])

    # parse efficiencies
    data = []
    for week in range(num_weeks):
        effs = []
        for trial in range(num_trials):
            trial_data = data_table[trial]
            week_data = trial_data[week]
            effs.append(week_data['eff'])
        data.append(effs)

    return data

if __name__ == "__main__":
    # test monte-carlo runner

    num_trials = 5
    ZID = dm_agents.ZID   # name of agent class
    trader_class_count =[(ZID,10), (ZID,10)] # run simulation with just ZID agents

    sim_name = "ZID MONTE-CARLO"
    num_periods = 7
    num_weeks = 50
    num_rounds = 5
    grid_size = 15

    num_traders = 20
    num_units = 8
    lower_bound = 200 
    upper_bound = 600
    data_table = make_monte_carlo(sim_name, num_trials, num_periods, num_weeks,
                                num_rounds, grid_size,
                                num_traders, num_units,
                                lower_bound, upper_bound,
                                trader_class_count)
    """

    """

    eff_avg_1, std_error_1, eff_min_1, eff_max_1 = analyze_eff_data(num_trials, num_weeks, data_table)
    x = range(num_weeks)
    fig, ax = plt.subplots(figsize=(10, 8))

    ax.plot(x, eff_avg_1, label = 'ZID', linestyle = 'solid', color='red', lw =3)
    ax.errorbar(x, eff_avg_1, yerr=std_error_1, fmt='.k')
    ax.plot(x, eff_min_1, label = 'min', linestyle = 'dotted', color='cyan', lw =3)
    ax.plot(x, eff_max_1, label = 'max', linestyle = 'dotted', color='cyan', lw =3)

    ax.set_xlabel('week', size = 'x-large') 
    ax.set_xbound(0, num_weeks)
    ax.set_ybound(0, 100)
    ax.grid(1)
    ax.set_ylabel('efficiency', size = 'x-large') 
    ax.set_title(f'ZIDA average efficiencies for {num_trials} trials', size = 'x-large')
    ax.legend(fontsize='x-large')
    plt.show()  