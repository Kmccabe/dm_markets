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
import dm_process_results as pr
import environment.env_make_agents as mkt

def make_sim(sim_name, num_periods, num_weeks,
             num_rounds, grid_size,
             num_traders, num_units,
             lower_bound, upper_bound,
             trader_objects):
    """Runs one complete simulation and returns data in
        effs[treatment][trial]
    """ 

    # data table for simulation
    data = {}

    # make agents
    agent_maker = mkt.MakeAgents(num_traders, trader_objects, num_units, 
                                grid_size, lower_bound, upper_bound)
    agent_maker.make_agents()
    agent_maker.set_locations(grid_size)
    agents = agent_maker.get_agents()
  
    # set up market
    agent_maker.make_market(sim_name)
    market = agent_maker.get_market()

    # run sim
    for week in range(num_weeks):
        data[week] = {}
        for agent in agents:
            agent.start(None)
        contracts = []
        sim_grids = []
        sim1 = simp.SimPeriod(sim_name, num_rounds, agents, 
               market, grid_size)
        for period in range(num_periods):
            sim1.run_period()
            grid = sim1.get_grid()
            sim_grids.append(grid)
            contracts.extend(sim1.get_contracts())
        
        data[week]['contracts'] = contracts
        data[week]['grids'] = sim_grids
        
        # process results
        pr1 = pr.ProcessResults(market, sim_name, agents, contracts)
        pr1.calc_efficiency()
        pr1.get_results()
        eff = pr1.get_efficiency()
        type_eff = pr1.get_type_surplus()
        data[week]['eff'] = eff # single item put in list to faciliatate looping through data 
        data[week]['type_effs'] = type_eff
    return data


def make_monte_carlo(sim_name, num_trials, num_periods, num_weeks,
                    num_rounds, grid_size,
                    num_traders, num_units,
                    lower_bound, upper_bound,
                    trader_objects):
    """Runs one complete simulation and returns data in
        effs[treatment][trial]
    """ 

    sim_data = {}
    sim_data['parms'] = {'sim_name': sim_name, 'num_traders': num_traders, 'num_units': num_units,
                         'num_weeks': num_weeks, 'num_periods': num_periods, 'num_rounds': num_rounds,
                         'grid_size': grid_size, 'lower_bound':lower_bound, 'upper_bound': upper_bound,
                         'trader_objects': trader_objects}

    for trial in range(num_trials):
        sim_data[trial]  = make_sim(sim_name, num_periods, num_weeks,
                                    num_rounds, grid_size,
                                    num_traders, num_units,
                                    lower_bound, upper_bound,
                                    trader_objects)
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
    trader_objects =[(ZID,10), (ZID,10)] # run simulation with just ZID agents

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
                                trader_objects)
    """
    # show data_structure for data_table
    print(trial, 'parms', data_table['parms'])
    for trial in range(num_trials):
        print(f"trial = {trial}")
        trial_data = data_table[trial]
        for week in range(num_weeks):
            print(f"week = {week}")
            week_data = trial_data[week]
            print(trial, week, 'contracts', week_data['contracts'])
            print()
            print(trial, week, 'grids', week_data['grids'])
            print()
            print(trial, week, 'eff', week_data['eff'])
            print()
            print(trial, week, 'type_effs') 
            for key in week_data['type_effs']:
                print(key, week_data['type_effs'][key])
            print()
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