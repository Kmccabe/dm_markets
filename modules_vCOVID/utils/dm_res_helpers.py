import pandas as pd
import numpy as np
import warnings

def extract_n(period_locs):
    """Return number of occupied points in period_locs dictionary"""
    if period_locs is None:
        return 0
    else:
        return len(period_locs)
    
def extract_h(period_locs, num_agents):
    """Return agent h based on period_locs dictionary"""
    if period_locs is None:
        return 0
    else:
        h = 0
        loc_vals = list(period_locs.values())
        for i in range(len(period_locs)):
            h += (len(loc_vals[i])/num_agents)**2

        return h

def add_agent_density(df_sim, by_period=False, return_df=False):

    num_agents = df_sim['num_traders'].iloc[0]

    if by_period: # if want to return by-period data
        try:
            df_sim['tr_period']
        except KeyError:
            raise ValueError("The df_sim must have a tr_period column if by_period=True")
        np_df = df_sim.copy()
        np_df['loc_occupied'] = np_df['period_locs'].apply(extract_n)
        np_df['agent_density'] = np_df['period_locs'].apply(extract_h, args=[num_agents])

        # Calculate periods occupied point and agent h (herschfindal)
        if return_df:
            return np_df
        else:
            return np_df['loc_occupied'].values(), np_df['agent_density'].values()


    else: # if want to return by-week data
        week_grids = df_sim['grids']
        week_len = df_sim['num_periods'].iloc[0]
        week_n = np.zeros(len(df_sim))
        week_h = np.zeros(len(df_sim))

        # Calculate average weekly occupied point and agent h (herschfindal)
        period_n = np.zeros(len(df_sim)*week_len)
        period_h = np.zeros(len(df_sim)*week_len)
        for i in range(len(week_grids)):
            week_grid = week_grids[i]
            for j in range(len(week_grid)):
                period_occupied = week_grid[j].values()
                period_grid = list(period_occupied)
                n_occupied = len(period_grid)
                agent_h = 0
                for k in range(n_occupied):
                    agent_h += (len(period_grid[k])/num_agents)**2
                period_n[i*week_len+j] = n_occupied
                period_h[i*week_len+j] = agent_h
            week_n[i] = np.mean(period_n[i*week_len:(i+1)*week_len])
            week_h[i] = np.mean(period_h[i*week_len:(i+1)*week_len])

        if return_df:
            week_df = pd.DataFrame()
            week_df['trial'] = df_sim['trial']
            week_df['week'] = df_sim['week']
            week_df['week_loc_occupied'] = week_n
            week_df['week_agent_density'] = week_h
            return week_df
        else:
            return week_n, week_h
        
def calc_area_under_curve(simulation_df, metric="eff", metric_max=100):
    """Calculates the area under the curve = sum of efficiencies/sum(max efficiencies) for a particular run or set of runs - returns 1 number or df of trials: areas"""
    num_trials = simulation_df['num_trials'].valuess[0]

    if num_trials == 1:
        return simulation_df[metric].sum()/(simulation_df['num_weeks']*metric_max)
    else:
        ret_df = simulation_df.groupby('trial').sum(metric)/(simulation_df['num_weeks']*metric_max)
        return ret_df.reset_index()
    
def add_true_period(per_df):
    """Add true period (week.period) count to a period dataframe."""

    n_df = per_df.copy()
    n_df["tr_period"] = n_df["period"] + n_df["week"]*n_df["num_periods"][0]
    n_df["tr_period"] = n_df["tr_period"].apply(lambda x: -1 if x < 0 else x)
    
    return n_df

def add_period_volume(per_df, add_weekly=True):
    """Adds the contract count to the period dataframe"""
    n_df = per_df.copy()
    n_df['period_volume'] = n_df['contracts'].dropna().apply(len)
    n_df['period_volume'] = n_df['period_volume'].fillna(0)

    if add_weekly:      
        avg_contracts = n_df[['trial', 'week', 'period_volume']].groupby(['trial','week']).mean().reset_index()
        avg_contracts = avg_contracts.rename(columns={'period_volume':'avg_contracts'})
        
        n_df = n_df.merge(avg_contracts, on=['trial','week'])

        sum_contracts = n_df[['trial', 'week', 'period_volume']].groupby(['trial','week']).sum().reset_index()
        sum_contracts = sum_contracts.rename(columns={'period_volume':'sum_contracts'})
        n_df = n_df.merge(sum_contracts, on=['trial','week'])

    return n_df

def add_period_efficiency(week_df, per_df):
    """Add weekly efficiency metric to period dataframe"""
    week_cols = ['trial', 'week', 'week_eff', 'week_type_effs']
    week_rename = {'eff':'week_eff', 'type_effs':'week_type_effs'}
    w_df = week_df.rename(columns=week_rename)
    p_df = per_df.merge(w_df[week_cols], on=['trial','week'])
    
    return p_df

def get_contract_prices(contracts_list):
    if contracts_list is None or len(contracts_list) == 0:
        return np.nan
        
    prices = np.zeros(len(contracts_list))
    for i in range(len(contracts_list)):
        prices[i] = contracts_list[i][1] # contract list shape: [(_, price, _, ...)]
    return prices

def add_period_price(per_df, add_weekly=False):
    """Return overall average contract prices, across the entire grid"""
    n_df = per_df.copy()
    n_df['prices'] = n_df['contracts'].apply(get_contract_prices)
    
    with warnings.catch_warnings():
        n_df['price_avg'] = n_df['prices'].apply(np.nanmean)
        n_df['price_std'] = n_df['prices'].apply(np.nanstd)

    return n_df

def add_week_prices(per_df, return_sep_df=False):
    """Add prices at the weekly level - requires prices at the period level to have been added already."""
    n_df = per_df.copy()
    n_trials = n_df.num_trials.iloc[0]
    n_weeks = n_df.num_weeks.iloc[0]
    n_periods = n_df.num_periods.iloc[0]
    ret_df = None
    for t in range(n_trials):
        t_df = n_df[n_df['trial']==t]
        for w in range(n_weeks):
            w_df = t_df[t_df['week']==w]
            
            num_prices = 0
            for p in range(n_periods):
                p_df = w_df[w_df['period']==p]
                p_prices = p_df['prices'].iloc[0]

                if (type(p_prices) is not np.ndarray) or (p_prices is None):
                    continue
                num_prices += len(p_prices)

            ret_prices = np.zeros(num_prices)
            cur_price_index = 0
            for p in range(n_periods):
                p_df = w_df[w_df['period']==p]
                p_prices = p_df['prices'].iloc[0]
                if (type(p_prices) is not np.ndarray) or (p_prices is None):
                    continue
                for j in range(len(p_prices)):
                    ret_prices[cur_price_index] = p_prices[j]
                    cur_price_index += 1

            w_ret_df = pd.DataFrame({"trial":[t], "week":[w],"week_prices":[ret_prices]})
            if ret_df is None:
                ret_df = w_ret_df
            else:
                ret_df = pd.concat([ret_df, w_ret_df], ignore_index=True)
    
    with warnings.catch_warnings():
        ret_df['week_price_avg'] = ret_df['week_prices'].apply(np.nanmean)
        ret_df['week_price_std'] = ret_df['week_prices'].apply(np.nanstd)
    ret_df['week_volume'] = ret_df['week_prices'].apply(len)

    n_df = n_df.merge(ret_df, on=['trial','week'])

    if return_sep_df:
        return n_df, ret_df
    return n_df

def trim_initial_locations(s_df):
    """Return dataframe without the initial locations - these cannot be used in some calculations"""
    n_df = s_df.copy()
    return n_df[n_df['week'] != -1 ]

def get_loc_prices(contracts):
    """Get all prices for contracts that took place at each location within this period."""
    loc_prices = dict()
    if contracts is None or len(contracts) == 0:
        return tuple()
    for i in range(len(contracts)):
        this_cont = contracts[i]
        b_loc = this_cont[8]
        s_loc = this_cont[9]
        if b_loc != s_loc:
            raise ValueError("Ambiguous contract location when seller and buyer are not at the same location. If this is the intended behavior, must implement additional functionality/rule as to 'where' the contract is.")
        c_price = this_cont[1]

        if b_loc in loc_prices:
            loc_prices[b_loc].append(c_price)
        else:
            loc_prices[b_loc] = [c_price]

    ret_lst = []
    for loc in loc_prices:
        pr_lst = []
        for pr in loc_prices[loc]:
            pr_lst.append(pr)
        pr_tup = tuple(pr_lst)
        ret_lst.append((loc, pr_tup))
    
    ret_tup = tuple(ret_lst)
    return ret_tup

def get_loc_avg(loc_prices):
    """Return average price within each location."""
    ret_lst = []
    for i in range(len(loc_prices)):
        loc = loc_prices[i][0]
        prs = loc_prices[i][1]
        with warnings.catch_warnings():
            avg = np.nanmean(prs)
        ret_lst.append((loc, avg))
    ret_tup = tuple(ret_lst)
    return ret_tup

def get_loc_std(loc_prices):
    """Return standard deviation within each location."""
    ret_lst = []
    for i in range(len(loc_prices)):
        loc = loc_prices[i][0]
        prs = loc_prices[i][1]
        if len(prs) <= 1:
            std = np.nan
        else:
            with warnings.catch_warnings():
                std = np.nanstd(prs)
        ret_lst.append((loc, std))
    ret_tup = tuple(ret_lst)
    return ret_tup
    
def get_loc_vol(loc_prices):
    """Return the volume at each location."""
    if len(loc_prices) == 0:
        return ()
    ret_lst = []
    for i in range(len(loc_prices)):
        loc = loc_prices[i][0]
        prs = loc_prices[i][1]
        vol = len(prs)
        ret_lst.append((loc, vol))
    ret_tup = tuple(ret_lst)
    return ret_tup

def get_cross_loc_std(loc_price_avg):
    """Return the standard deviation of average prices between locations."""
    if len(loc_price_avg) <= 1:
        return np.nan
    avg_lst = []
    for i in range(len(loc_price_avg)):
        avg = loc_price_avg[i][1]
        avg_lst.append(avg)
        
    with warnings.catch_warnings():
        std = np.nanstd(avg_lst)
        
    return std

def add_location_prices(per_df):
    """Add the prices at each location, in the form ((loc x, loc y), (prices))."""
    n_df = per_df.copy()
    n_df['loc_prices'] = n_df['contracts'].apply(get_loc_prices)
    n_df['loc_price_avg'] = n_df['loc_prices'].apply(get_loc_avg)
    n_df['loc_price_std'] = n_df['loc_prices'].apply(get_loc_std)
    n_df['loc_volume'] = n_df['loc_prices'].apply(get_loc_vol)
    n_df['loc_cross_std'] = n_df['loc_price_avg'].apply(get_cross_loc_std)
    
    return n_df

def add_week_location_prices(per_df, return_sep_df=False):
    """Add weekly price location data; must have already done add_location_prices"""
    n_df = per_df.copy()
    n_trials = n_df.num_trials.iloc[0]
    n_weeks = n_df.num_weeks.iloc[0]
    n_periods = n_df.num_periods.iloc[0]
    ret_df = None
    for t in range(n_trials):
        t_df = n_df[n_df['trial']==t]
        for w in range(n_weeks):
            w_df = t_df[t_df['week']==w]
            
            week_loc_prices = dict()
            for p in range(n_periods):
                p_df = w_df[w_df['period']==p]
                p_loc_pr = p_df['loc_prices'].iloc[0]
                for i in range(len(p_loc_pr)):
                    loc = p_loc_pr[i][0]
                    prs = p_loc_pr[i][1]
                    
                    if loc in week_loc_prices:
                        week_loc_prices[loc].extend(prs)
                    else:
                        week_loc_prices[loc] = list(prs)
            week_ls = []
            for l_i in week_loc_prices:
                week_ls.append((l_i, tuple(week_loc_prices[l_i])))
            week_tup = tuple(week_ls)

            wk_df = pd.DataFrame({"trial":[t], "week":[w], "week_loc_prices":[week_tup]})
            if ret_df is None:
                ret_df = wk_df
            else:
                ret_df = pd.concat([ret_df, wk_df], ignore_index=True)
            
    ret_df['week_loc_price_avg'] = ret_df['week_loc_prices'].apply(get_loc_avg)
    ret_df['week_loc_price_std'] = ret_df['week_loc_prices'].apply(get_loc_std)
    ret_df['week_loc_volume'] = ret_df['week_loc_prices'].apply(get_loc_vol)
    ret_df['week_loc_cross_std'] = ret_df['week_loc_price_avg'].apply(get_cross_loc_std)

    n_df = n_df.merge(ret_df, on = ["trial", "week"])

    if return_sep_df:
        return n_df, ret_df
    else:
        return n_df
    
def match_density(period_locs, true_match=False, agent_types=('B','S'), by_locs=False, max_match=None, deflator_term=None, by_counts=True, agent_type_counts=None):
    """
    Implemented for 1 and multiple types of agents.
    
    true_match (boolean): default False. True match only counts TRUE matches - so if there is an exact match between the agent types, dropping the remainder. - E.g. if there are 2 agent types a match counts as 1 if there is 1 of type B and one of S, but if there are 2 of type B, there is 0 match. A point with 2 B and 1 S would also be a measure of 1. FALSE: San have false matches, discounting unclean matches If there are 1 of B and 2 of S, it counts as 1.5. If there are 1 of B and 3 of S, it will count as 1.75, so each S extra-matched will count as (1/max_match)^n, where n is the number of extra-matched S. A point with and number of B or S by themselves counts as 0 of a match - they cannot match with themselves. Partial match value depreciated additionally by the depreciation_term - by default raises the partial value to an additional power, so the first additional match in the example would count as 0.25.

    by_locs (boolean): default False. If want to return the match density by location. Only returns non-zero density locations. Otherwise returns overall match density. 

    deflator_term (float): el (0, 1). How much to deflate the value of the partial matches. Default None - if None, uses 1/max_match as the deflator term, equivalent to raising the partial match value to an additional +1 power.

    by_counts (boolean): If want the counts (or partial counts) of agents instead of the density (=count/max_counts_possible). Default True. When False, must pass tuple of (agent_type_num, ) of equal length to the agent_types tuple with the number of agents per that type.

    agent_counts (tuple): Agent counts of each of the agent types. The position in the tuples corresponds to the positions in the agent_types tuple. Determines the maximum possible count of true matches and maximal value of partial matches.
    
    """

    loc_match_d = []
    all_match_d = 0

    # Set the max_match (maximizing value fo match) if not passed
    if max_match is None:
        # 2 is the perfect match in 1 type - by assumption, can pass alternative - pass 1 if no such metric exists
        if len(agent_types):
            max_match = 2
        # Num agent types is the perfect match by assumption
        else:
            max_match = len(agent_types)

    # Set the depreciation term based on the max_match term if no other depreciation term is provided
    if deflator_term is None:
        deflator_term = 1/max_match

    if by_counts == False:
        if agent_type_counts is None:
            raise ValueError("Must pass agent_type_counts when using by_counts=False, so we can calculate the maximum possible value of the match count.")
        if len(agent_types) != len(agent_type_counts):
            raise ValueError("The length of array_types and array_counts must be the same.")
        if len(agent_types) > 1 and max_match != len(agent_types):
            raise NotImplementedError("The maximum count of matches with a max_match!=len(agent_types) is ambiguous.")
        
        # Calculate the maximum value of match density.
        part_val = 1/max_match
        if len(agent_types) == 1:
            max_tr_match = agent_type_counts[0]//max_match
            max_rem = agent_type_counts[0]%max_match
            rem_arr = np.arange(1, max_rem+1)
            max_rem_val = np.sum(np.power(part_val, rem_arr)) * deflator_term
        else:
            max_tr_match = min(agent_type_counts)
            min_c = min(agent_type_counts)
            max_rem_val = 0
            for i in range(len(agent_types)):
                a_ct = agent_type_counts[i]
                rem_c = a_ct - min_c
                rem_arr = np.arange(1, rem_c+1)
                rem_c_val = np.sum(np.power(part_val, rem_arr)) * deflator_term
                max_rem_val += rem_c_val
        max_val = max_tr_match + max_rem_val

    for lc in period_locs:
        ags = period_locs[lc]
        n_ags = len(ags)
        if n_ags <= 1 and true_match: # If only one agent at point, cannot have a true match
            continue
        else:
            if len(agent_types) == 1: # If only one agent type, they can all match against each other
                tr_match = n_ags//max_match # Full matches
                obs_d = tr_match
                if true_match:
                    pass
                elif tr_match != 0: # If there is at least one match, calc remainder values
                    rem = n_ags%max_match
                    rem_arr = np.arange(1, rem+1)
                    part_val = 1/max_match
                    rem_val = np.sum(np.power(part_val, rem_arr)) # Value of partial matches
                    obs_d += rem_val * deflator_term
            else: # If many agent types, need to match cross-group
                # Count agents per types
                type_obs = dict()
                for typ in agent_types:
                    type_obs[typ] = 0
                for ag in ags:
                    ag_typ = ag[0] # Agent type is indicated by the first character of their name
                    type_obs[ag_typ] += 1
                
                # Count matches
                min_of_types = None
                max_of_types = None
                for typ in agent_types:
                    ag_n = type_obs[typ]

                    # Record min of agents in type
                    if min_of_types is None:
                        min_of_types = ag_n
                    elif ag_n < min_of_types:
                        min_of_types = ag_n

                    # Record max of agents in type
                    if max_of_types is None:
                        max_of_types = ag_n
                    elif ag_n > max_of_types:
                        max_of_types = ag_n
                
                tr_match = min_of_types # True match count = lowest type count
                obs_d = tr_match

                if true_match or max_of_types == min_of_types:
                    pass
                elif tr_match != 0:
                    # Calculate the remainder values
                    part_val = 1/max_match
                    rem_val = 0
                    for typ in agent_types:
                        rem_ags = type_obs[typ] - min_of_types
                        if rem_ags == 0:
                            continue
                        rem_arr = np.arange(1, rem_ags+1)
                        r_val = np.sum(np.power(part_val, rem_arr)) # Value of the remainder of this type of agent
                        rem_val += r_val * deflator_term
                    obs_d += rem_val

        if not obs_d == 0:
            if not by_counts:
                obs_d = obs_d / max_val
            all_match_d += obs_d
            loc_match_d.append((lc, obs_d))
    
    if by_locs:
        return tuple(loc_match_d) # Tuple of form ((location, density), ...)
    else:
        return all_match_d
    
def add_match_density(per_df, agent_types=('B','S'), by_locs=False, max_match=None,
                      deflator_term=None, by_counts=None, agent_counts=None):
    """Add the match density to the period dataframe."""
    try:
        per_df['period_locs']
    except KeyError:
        raise ValueError("Need to have added period_locs to the period dataframe to use add_match_density.")
    
    n_df = per_df.copy()

    if by_counts is not None and by_counts == True:
        n_df['match_count'] = n_df.period_locs.apply(match_density, args=[False, agent_types, False, max_match, deflator_term, by_counts, agent_counts])
        n_df['tr_match_count'] = n_df.period_locs.apply(match_density, args=[True, agent_types, False, max_match, deflator_term, by_counts, agent_counts])

        if by_locs:
            n_df['loc_match_count'] = n_df.period_locs.apply(match_density, args=[False, agent_types, True, max_match])
            n_df['loc_tr_match_count'] = n_df.period_locs.apply(match_density, args=[True, agent_types, True, max_match])

    elif by_counts is None or by_counts == False:
        by_counts = False
        
        if agent_counts is None:
            agent_type_counts = per_df.agent_type_counts.iloc[0]

        n_df['match_density'] = n_df.period_locs.apply(match_density, args=[False, agent_types, False, max_match, deflator_term, by_counts, agent_type_counts])
        n_df['tr_match_density'] = n_df.period_locs.apply(match_density, args=[True, agent_types, False, max_match, deflator_term, by_counts, agent_type_counts])

        if by_locs:
            n_df['loc_match_density'] = n_df.period_locs.apply(match_density, args=[False, agent_types, True, max_match, deflator_term, by_counts, agent_type_counts])
            n_df['loc_tr_match_density'] = n_df.period_locs.apply(match_density, args=[True, agent_types, True, max_match, deflator_term, by_counts, agent_type_counts])

    return n_df

def add_all_metrics(week_df, period_df):
    n_df = period_df.copy()
    n_df = trim_initial_locations(n_df) # Remove the "initial locations" i.e. time period week=-1, period=-1
    n_df = add_period_efficiency(week_df, n_df) # Add weekly efficiency to period dataframe
    n_df = add_true_period(n_df) # Add true-period (cross-period index)
    n_df = add_period_volume(n_df) # Add volume of trade at period
    n_df = add_agent_density(n_df, by_period=True, return_df=True) # Add measure of agent counts at locations - by periods
    week_loc_df = add_agent_density(week_df, by_period=False, return_df=True) # Add measure of agent counts at locations - by weeks
    n_df = n_df.merge(week_loc_df, on=['trial','week'])

    n_df = add_period_price(n_df) # Add prices of contracts by period
    n_df = add_location_prices(n_df) # Add prices at different locations by period
    n_df = add_week_prices(n_df, return_sep_df=False) # Add prices by week
    n_df = add_week_location_prices(n_df, return_sep_df=False) # Add prices by week by location

    n_df = add_match_density(n_df, by_locs=True, by_counts=True) # Add match-counts 
    n_df = add_match_density(n_df, by_locs=True, by_counts=False) # Add match density

    return n_df

# TODO add location-level efficiency