import numpy as np
import pandas as pd
import copy
import simulations.dm_sim as dm_sim
import simulations.dm_sim_period as dm_sim_period
import environment.env_make_agents as env_make_agents

import utils.dm_process_results as dm_process_results
import utils.dm_utils as dm_utils

def change_agents(agents, ratio=1, new_strategy="ZIDPR", new_strategy_params=None, new_mer=None):
    
    """
    make a copy of agents at current location and change a proportion of agents (default 1.0) to a new strategy to (default ZIDPR) or to a new strategy_parameters (default None - keep original)
    """

    new_class = dm_utils.get_agent_class(new_strategy)

    # Pick a random set of agents to mutate (randomly at passed proportion - policy compliance rate)
    rng = np.random.default_rng()
    agent_indecies = list(range(len(agents)))
    complying_num = len(agents)*ratio
    non_int_part = complying_num%1
    add_num = 0
    if non_int_part != 0:
        # Randomly draw against remainder (keeps percentages work across trials)
        if rng.random() < non_int_part:
            add_num += 1
            
    complying_num = int(complying_num) + add_num
    complying_inds = rng.choice(agent_indecies, size=complying_num, replace=False)
    
    new_agents = []
    for k, agent in enumerate(agents):
        
        # change name
        if k in complying_inds: # These ones get Transformed
            name = agent.name
            s1 = name.split('_')
            name = s1[0] + '_' + s1[1] + f'_{new_strategy}'
            trader_type = agent.type
            payoff = agent.payoff
            money = agent.money
            location = agent.location
            lower_bound = agent.lower_bound
            upper_bound = agent.upper_bound
            num_units = agent.num_units

            # Allow changing of movement_error_rate
            if new_mer is None:
                move_error_rate = agent.movement_error_rate
            else:
                move_error_rate = new_mer

            # Allow changing to new strategy parameters
            if new_strategy_params is None:
                strategy_params = agent.strategy_params
            else:
                strategy_params = new_strategy_params

            redraw_values = agent.redraw_values
            group_name = agent.group_name

            # make a new_class agent
            new_agent = new_class(name, trader_type, payoff, money, location, 
                                   lower_bound, upper_bound, num_units, move_error_rate, 
                                   strategy_params, redraw_values, group_name)

            # Copy contract flag
            cont_flag = agent.contract_this_period
            new_agent.set_contract_this_period(cont_flag)

            # Copy costs and values
            nag_typ = new_agent.get_type()
            if nag_typ == "BUYER" or nag_typ == "B":
                vals = agent.get_values()
                new_agent.set_values(vals)
            elif nag_typ == "SELLER" or nag_typ == "S":
                cos = agent.get_costs()
                new_agent.set_costs(cos)

            # Handle special values based on agent families
            agent_family = agent.agent_family

            # Handle special values for ZIDA-Derivatives
            if agent_family == 'ZIDA':
                new_agent.reset_flag_frequency = agent.reset_flag_frequency
                new_agent.current_period = agent.current_period
                new_agent.periods_traded_in = agent.periods_traded_in
                new_agent.reset_flag_min_agents = agent.reset_flag_min_agents
                new_agent.reset_flag_min_trades = agent.reset_flag_min_trades
                new_agent.trades_this_week = agent.trades_this_week

            # Handle special values for ZIDT-Derivatives
            elif agent_family == 'ZIDT':
                # TODO: implement
                raise ValueError('NOT IMPLEMENTED ZIDT')
                pass

            # For Week Flag Rule
            new_agent.trades_this_week = agent.trades_this_week
        
            # For Window flag Rule
            new_agent.current_period = agent.current_period
            new_agent.periods_traded_in = agent.periods_traded_in # test x1

        else: # These ones do not change
            new_agent = copy.deepcopy(agent)
            
        new_agents.append(new_agent)
    
    return new_agents

def change_back_agents(agents, old_strategy="ZIDPA", old_strategy_params=None, old_mer=None):
    """
    Returns agents to original agent type (default ZIDPA, no changed to strategy params or movement error rate).
    
    Always applies change to the entirety of the agent population.
    """

    return change_agents(agents, ratio=1, new_strategy=old_strategy, 
                         new_strategy_params=old_strategy_params, new_mer=old_mer)

def make_experiment(sim_vars, treatment_dict, treatment_names=None, return_period_df=False):
    """
        Runs a Monte Carlo for each treatment in treatment_names or key of treatment_dict, using sim_vars as the baseline inputs and treatment_dict[treatment] as the updates to inputs.

        Only returns as a DataFrame. Can get period-level data with return_period_df=True.
    """

    # Pull dict keys as the treatment names if not passed
    if treatment_names is None:
        treatment_names = list(treatment_names)
    
    ret_df = None
    ret_per_df = None

    for trt in treatment_names:
        trt_vars = treatment_dict[trt]

        # Make a deep copy of sim_vars in case user mis-specified treatment_dict
        cp_vars = copy.deepcopy(sim_vars)
        cp_vars.update(trt_vars)

        if return_period_df:
            trt_df, trt_pr_df = dm_sim.make_monte_carlo(return_df=True, return_period_df=True, passed_as_dict=True, params_dict=cp_vars)
            trt_pr_df['treatment'] = trt

            if ret_per_df is None:
                ret_per_df = trt_pr_df
            else:
                ret_per_df = pd.concat([ret_per_df, trt_pr_df], ignore_index=True)
        
        else:
            trt_df = dm_sim.make_monte_carlo(return_df=True, return_period_df=False, passed_as_dict=True, params_dict=cp_vars)
        trt_df['treatment'] = trt

        if ret_df is None:
            ret_df = trt_df
        else:
            ret_df = pd.concat([ret_df, trt_df], ignore_index=True)
    
    if return_period_df:
        return ret_df, ret_per_df
    else:
        return ret_df


def make_event_sim(sim_name, 
                   num_weeks, num_periods, num_rounds,
                   num_traders, agent_groups, grid_size,
                   event_begin, event_end, compliance_rate=1,
                   new_agent_class = "ZIDPR", new_strategy_params = None, new_mer = None,
                   group_names = None,
                   return_df=False, return_period_df=False,
                   debug=False):
    """
    Runs one complete event simulation, defined the same as dm_sim.make_simulation but with a transformation event between event_begin and even_end (i.e. agents change class/strategy).

    Args:
        sim_name (str) - name of the simulation.

        num_weeks (int) - Number of weeks to simulate.
        
        num_periods (int) - Number of periods within one week.
        
        num_rounds (int) - Number of bargaining rounds within one period.

        num_traders (int) - Number of traders across all agent_groups.
        
        agent_groups (list of list) - A list of lists of parameters which define Agents. See env_make_agent.
        
        grid_size (int) - Length of one side of the square grid.

        event_begin (int) - Week in which event begins (beings at start of week, before 1st period).
        
        event_end (int) - Week in which event ends (ends at start of week, before 1st period).
        
        compliance_rate (float, optional, default 1) - the ratio of agents that transform during the event period.

        new_agent_class (str, optional, default "ZIDPR") - name of the new agent class that agents change into.
        
        new_strategy_params (dict, optional) - new strategy parameters of changed agents
        
        new_mer = None (float 0<x<1, optional) - new movement error rate of changed agents

        group_names = None (list, optional) - custom names of the agent groups.

        return_df=False (bool, optional, default False) - return data as DF.
        
        return_period_df (bool, optional, default False) - return period-level data DF.
    
    Returns
        data (dict) a dictionary mapping trials to efficiencies. (If return_df = False.)
        df_out (DataFrame): a DataFrame capturing all parameters and week-level observations. (If return_df = True.)
        period_df_out (DataFrame): a DataFrame capturing all parameters and period-level observations. (If return_df = True and return_period_df = True.)


        TODO: Implement multi-event as an option - could pass it as additional keyword arg. w/ None, None for beg/end.
        This will allow us to run the "increase movement error" intervention - equivalent to decreasing movement cost - to hasten post-intervention recovery.

        TODO: Refactor this and make_sim to not double-up on saving data when using as-df
    """ 

    if group_names is None:
        group_names = [None]*len(agent_groups)

    if return_df:
        # Store parameters
        df_cols_param = ['sim_name', 
                         'num_weeks', 'num_periods', 'num_rounds', 
                         'num_traders', 'agent_groups',
                         'grid_size', 'group_names',
                         'event_begin', 'event_end',
                         'compliance_rate', 'new_agent_class',
                         'new_strategy_params',
                         'new_mer'
                         ]
        week_param_ls = [sim_name, 
                         num_weeks, num_periods, num_rounds,
                         num_traders, agent_groups,
                         grid_size, group_names,
                         event_begin, event_end,
                         compliance_rate, new_agent_class,
                         new_strategy_params,
                         new_mer]
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

    # Save data for change back agents
    # TODO will be avoided with the below fixes
    old_strategy = agent_groups[0][2]
    old_params = agent_groups[0][3]
    old_mer = agent_groups[0][9]

    # make agents
    agent_maker = env_make_agents.MakeAgents(debug)
    ag_df = agent_maker.gen_custom_agents(num_traders, agent_groups, grid_size, group_names)
    agent_maker.init_agents(ag_df)
    agents = agent_maker.get_agents()
  
    # set up market
    agent_maker.make_market(sim_name)
    market = agent_maker.get_market()

    data = {}

    # Run weeks in sim
    for week in range(num_weeks):

        # NOTE: Below only works for single-class world - all turn back to the same one class, strat param, mer
        # TODO: Implement a different version of change_agents and change_back_agents which preserves original values to roll them back later
        if week == event_begin:
            agents = change_agents(agents, compliance_rate, new_agent_class, new_strategy_params, new_mer)
            for ag in agents:
                ag
        if week == event_end:
            agents = change_back_agents(agents, old_strategy=old_strategy, 
                                        old_strategy_params=old_params, old_mer=old_mer)
        
        data[week] = {}

        # Reset agents' units
        for agent in agents:
            agent.start(None)
        contracts = []
        sim_grids = []
        sim1 = dm_sim_period.SimPeriod(sim_name, num_rounds, agents, 
               market, grid_size)
        
        # Run periods in week
        for period in range(num_periods):
            sim1.run_period()

            grid = sim1.get_grid()
            sim_grids.append(grid)
            contracts.extend(sim1.get_contracts())

            # Save period data for DF
            if return_period_df:

                # If you are at the first point in the simulation - save the initial grid at the week=-1, period=-1
                if week == 0 and period == 0: 
                    period_data = week_param_ls + [-1, (), copy.deepcopy(sim1.get_initial_grid()), 
                                                   None, None, None, -1,
                              copy.deepcopy(sim1.get_initial_grid())]
                    df_period_data.append(period_data)

                df_period_data.append(period_data)
        
        data[week]['contracts'] = contracts
        data[week]['grids'] = sim_grids
        
        # process results
        pr1 = dm_process_results.ProcessResults(market, sim_name, agents, contracts)
        pr1.calc_efficiency()
        pr1.get_results()
        eff = pr1.get_efficiency()
        class_surplus = pr1.get_class_surplus()
        group_surplus = pr1.get_group_surplus()

        data[week]['eff'] = eff # single item put in list to facilitate looping through data 
        data[week]['class_surplus'] = class_surplus
        data[week]['class_surplus'] = group_surplus

        # Save week data for DF
        if return_df:
            week_data = week_param_ls + [week, contracts, sim_grids, 
                                         eff, class_surplus, group_surplus]
            df_data.append(week_data)

    # Return df
    if return_df:
        df_out = pd.DataFrame(data=df_data, columns=df_cols)

        # Return period Df
        if return_period_df:
            period_df_out = pd.DataFrame(data=df_period_data, columns=df_period_cols)
            return df_out, period_df_out
        else:
            return df_out
        
    # Return as dictionary
    else:
        return data


def make_event_monte_carlo(sim_name=None, 
                           num_trials=None, num_weeks=None, num_periods=None, num_rounds=None,
                           num_traders=None, agent_groups=None, grid_size=None,
                           event_begin=None, event_end=None, compliance_rate=1,
                           new_agent_class = "ZIDPR", new_strategy_params = None, new_mer = None,
                           group_names = None,
                           return_df=False, return_period_df=False,
                           passed_as_dict=False, params_dict=None):
    """
    Runs a monte carlo of the event simulation.

    See make_event_sim for details on inputs.

    Additional args:
        num_trials (int): number of independent trials.

        passed_as_dict (bool, optional, default False): If passing parameters as a dictionary.

        params_dict (dict, optional): Required if passed_as_dict is true. Contains parameters to feed the simulation.

    Returns:
        dict of [trial][eff] efficiency outputs for each trial

        dataframe of weekly results (if return_df)

        dataframe of period results (if return_period_df)
    """ 
                    
    # Check vals are not None if not passing as dict
    passed_none = [sim_name is None,
                    num_trials is None,
                    num_weeks is None,
                    num_periods is None,
                    num_rounds is None,
                    num_traders is None,
                    agent_groups is None,
                    grid_size is None,
                    event_begin is None,
                    event_end is None]

    # If not passed_as_dict, need each val passed in
    if not passed_as_dict and any(passed_none):
        raise ValueError("If not passing values as a dictionary, you must pass all of sim_name, num_trials, num_weeks, num_periods, num_rounds, num_traders, agent_groups, grid_size.")
    
    # If passed_as_dict, check dict was passed and contains all required items
    if passed_as_dict:
        if params_dict is None:
            raise ValueError("Must pass a dictionary of parameters to params_dict if passing passed_as_dict=True")
        
        # Mandatory inputs
        try:
            sim_name = params_dict['sim_name']
            num_trials = params_dict['num_trials']
            num_weeks = params_dict['num_weeks']
            num_periods = params_dict['num_periods']
            num_rounds = params_dict['num_rounds']
            num_traders = params_dict['num_traders']
            agent_groups = copy.deepcopy(params_dict['agent_groups'])
            grid_size = params_dict['grid_size']
            event_begin = params_dict['event_begin']
            event_end = params_dict['event_end']
        except KeyError:
            raise ValueError("params_dict must contain all of sim_name, num_trials, num_weeks, num_periods, num_rounds, num_traders, agent_groups, grid_size.")
        
        # Optional Inputs
        try:
            new_agent_class = params_dict['new_agent_class']
        except KeyError:
            pass
        try:
            new_strategy_params = params_dict['new_strategy_params']
        except KeyError:
            pass
        try:
            new_mer = params_dict['new_mer']
        except KeyError:
            pass
        try:
            group_names = params_dict['group_names']
        except KeyError:
            pass

    sim_data = {}
    sim_data['params'] = {'sim_name': sim_name, 
                          'num_trials': num_trials,
                          'num_weeks': num_weeks, 'num_periods': num_periods, 'num_rounds': num_rounds,
                          'num_traders': num_traders, 'agent_groups': agent_groups,
                          'grid_size': grid_size,
                          'event_begin':event_begin, 'event_end': event_end,
                          'compliance_rate': compliance_rate,
                          'new_agent_class': new_agent_class,
                          'new_strategy_params': new_strategy_params,
                          'new_mer': new_mer,
                          'group_names': group_names
                          }

    # Stubs for storing df results
    if return_df:        
        mc_df = None

        if return_period_df:
            mc_period_df = None
        
        
    # Run n trials of this setup
    for trial in range(num_trials):

        # Return non-DF
        if not return_df:
            trial_data = make_event_sim(sim_name, 
                   num_weeks, num_periods, num_rounds,
                   num_traders, agent_groups, grid_size,
                   event_begin, event_end, compliance_rate=compliance_rate,
                   new_agent_class = new_agent_class, new_strategy_params = new_strategy_params, new_mer = new_mer,
                   group_names = group_names,
                   return_df=False, return_period_df=False)
            
            sim_data[trial] = trial_data
        
        # Return DF
        elif return_df:
            # Return period-level DF data
            if return_period_df:
                trial_df, trial_period_df = make_event_sim(sim_name, 
                   num_weeks, num_periods, num_rounds,
                   num_traders, agent_groups, grid_size,
                   event_begin, event_end, compliance_rate=compliance_rate,
                   new_agent_class = new_agent_class, new_strategy_params = new_strategy_params, new_mer = new_mer,
                   group_names = group_names,
                   return_df=True, return_period_df=True)
                
                trial_period_df['trial'] = trial
                
                # Store trial's period DF
                if mc_period_df is None:
                    mc_period_df = trial_period_df
                else:
                    mc_period_df = pd.concat([mc_period_df, trial_period_df], ignore_index=True)

            # Keep non-period data
            elif not return_period_df:
                trial_df = make_event_sim(sim_name, 
                   num_weeks, num_periods, num_rounds,
                   num_traders, agent_groups, grid_size,
                   event_begin, event_end, compliance_rate=compliance_rate,
                   new_agent_class = new_agent_class, new_strategy_params = new_strategy_params, new_mer = new_mer,
                   group_names = group_names,
                   return_df=True, return_period_df=False)
            
            trial_df['trial'] = trial

            # Store Trial DF
            if mc_df is None:
                mc_df = trial_df
            else:
                mc_df = pd.concat([mc_df, trial_df], ignore_index=True)

    # Return results with requested 
    if return_df:
        mc_df['num_trials'] = num_trials
        if return_period_df:
            mc_period_df['num_trials'] = num_trials
            return mc_df, mc_period_df
        elif not return_period_df:
            return mc_df
    else:
        return sim_data
