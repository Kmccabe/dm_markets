import environment.dm_agents as dma
import simulations.dm_sim as dm_sim
import matplotlib.pyplot as plt
import pandas as pd

def get_agent_class(class_name):
    """
    Maps a string name of dm_agent.Class to a dm_agent.Class object.
    Not necessary, but provided for user-friendliness.
    """
    class_name_map = {
        "ZID": dma.ZID,
        "ZIDA": dma.ZIDA,
        "ZIDP": dma.ZIDP,
        "ZIDPA": dma.ZIDPA,
        "ZIDPR": dma.ZIDPR,
        "ZIDT": dma.ZIDT,
        "ZIDTR": dma.ZIDTR
    }
    return class_name_map[class_name]

def get_agent_str(agent_class):
    """
    Maps a dm_agent.Class to a str representation.
    Useful for back-propagation of code.
    """
    class_name_map = {
        dma.ZID: "ZID",
        dma.ZIDA: "ZIDA",
        dma.ZIDP: "ZIDP",
        dma.ZIDPA: "ZIDPA",
        dma.ZIDPR: "ZIDPR",
        dma.ZIDT: "ZIDT",
        dma.ZIDTR: "ZIDTR"
    }
    return class_name_map[agent_class]

def agent_strategy_helper(agent_class_name=None):
    """
    Returns a list of possible agent strategies or potential strategy parameters.

    Args:
        agent_class_name (str, optional, default None): The agent class you want to print strategy parameters for. If None, prints potential agent class names instead.
    """
    class_list = ["ZID", "ZIDA", "ZIDP", "ZIDPA", "ZIDPR", "ZIDT", "ZIDTR"]

    if agent_class_name is None:
        print("Agent Classes Available")
        print(class_list)
    elif agent_class_name in ["ZID", "ZIDP"]:
        print(f"{agent_class_name} takes no strategy parameters. Pass {None} in instead.")
    elif agent_class_name in ["ZIDA", "ZIDPA"]:
        print(f"{agent_class_name} takes \"reset_flag_frequency\", representing the rule on which to resume movement, as a parameter. Additional parameters may be required, as specified below.\n")
        print("\"reset_flag_frequency\" can take the values of [\"NONE\", \"START\", \"WEEK\", \"MIN_AGENTS\", \"WINDOW\"]\n")
        print("NONE: Never resume movement after trading. No additional parameters\n")
        print("START: Resume movement at the start of each week (every time agent.start is called). No additional parameters.\n")
        print("WEEK: Resume movement is did not trade at least \"reset_flag_min_trades\" in the past week (time between agent.start is called).\n")
        print("MIN_AGENTS: Resume movement is there are less than \"reset_flag_min_agents\" agents at the same location as this agent.\n")
        print("WINDOW: Resume movement is did not trade at least \"reset_flag_min_trades\" in the last \"reset_flag_window\" periods.\n")
    elif agent_class_name == "ZIDPR":
        print(f"{agent_class_name} takes the same parameters as ZIDA, along with \"max_agents_allowed\", representing the maximum agents allowed in one location by the distancing rule.")
    elif agent_class_name == "ZIDT":
        print(f"{agent_class_name} requires the \"memory_length\" (2eta) representing how many periods the agent calculates their payoff contentness over and \"down_tolerance\" (nu) representing how significant of a decline in payoff and agent is willing to tolerate, relative to the first half of their memory.")
    elif agent_class_name == "ZIDTR":
        print(f"{agent_class_name} takes the same parameters as ZIDT, along with \"max_agents_allowed\", representing the maximum agents allowed in one location by the distancing rule.")
        

def test_agents(debug):
    """Helper function to initialize test agents"""
    b_1 = dma.ZID('B1', 'BUYER', utility, 500, (0, 0))
    b_2 = dma.ZID('B2', 'BUYER', utility, 500, (1, 2))
    b_3 = dma.ZID('B3', 'BUYER', utility, 500, (0, 0))
    b_4 = dma.ZID('B4', 'BUYER', utility, 500, (1, 2))

    s_1 = dma.ZID('S1', 'SELLER', profit, 500, (0, 0))
    s_2 = dma.ZID('S2', 'SELLER', profit, 500, (2, 1))
    s_3 = dma.ZID('S3', 'SELLER', profit, 500, (0, 0))
    s_4 = dma.ZID('S4', 'SELLER', profit, 500, (2, 1))

    b_1.set_values([100, 90, 50, 20])
    b_2.set_values([100, 90, 50, 20])
    b_3.set_values([100, 90, 50, 20])
    b_4.set_values([100, 90, 50, 20])

    s_1.set_costs([10, 20, 30, 40])
    s_2.set_costs([10, 20, 30, 40])
    s_3.set_costs([10, 20, 30, 40])
    s_4.set_costs([10, 20, 30, 40])

    agent_list = [b_1, s_1, b_2, s_2, b_3, s_3, b_4, s_4]
    
    for agent in agent_list:
        name = agent.name
        agent.set_debug(debug)
        msg = dma.Message("START", 'RUNNER', name, "No Payload")
        agent.process_message(msg)
    
    return agent_list

def utility(q, m, v, p):
    """Calculates utility payoff
       args:  q = quantity bought
              m = money
              v = list of values
              p = list of prices for goods bought
    """
    sum_v = sum(v[0:q])  # sum first q elements of v
    sum_p = sum(p[0:q])  # sum first q elements of p
    return sum_v + m - sum_p

def profit(q, m, c, p):
    """Calculates profit payoff
       args:  q = quantity sold
              m = money
              c = list of costs
              p = list of prices for goods sold
    """
    sum_c = sum(c[0:q])  # sum first q elements of c
    sum_p = sum(p[0:q])  # sum first q elements of p
    return m + sum_p - sum_c


def print_contracts(contracts, extended=True):
    if extended:
        print_contracts_extended(contracts)
    else:
        print("CONTRACTS: (round, price, buyer, seller")
        print("---------------------------------------")
        for contract in contracts:
            round = contract[0]
            price = contract[1]
            buyer = contract[2]
            seller = contract[3]
            print(f"{round:2} {price:3} {buyer:3} {seller:3}")

def print_contracts_extended(contracts):
    print("CONTRACTS:")
    print("rnd, b_cu:b_val -price- s_cos:s_cu  buyer_id, seller_id")
    print("-------------------------------------------------------")
    for contract in contracts:
        round = contract[0]
        price = contract[1]
        buyer = contract[2]
        seller = contract[3]
        b_cur = contract[4]
        b_val = contract[5]
        s_cur = contract[6]
        s_cos = contract[7]
        print(f"{round:2} {b_cur:3}:{b_val:<4}-{price:4} -{s_cos:>4}:{s_cur:<3}    {buyer:10} {seller:10}")


def pretty_print_grid(grid):
    """Prettily print the passed grid"""
    for k_loc in grid:
        print('point', k_loc,' --> ',grid[k_loc])

def get_agent_locs(agents):
    """Return agent locations"""
    x = []
    for agent in agents:
        y = agent.get_location()
        x.append(y)
    return x

def print_agent_locations(agents):
    """Print agent names and locations to the console"""
    for agent in agents:
        print(f"agent {agent.name} is at location {str(agent.get_location())}")

def chk(x, index=0):
    """Check if x if of an allowable type
    If int, return self, if a list, return the value at index.
    """
    typ = type(x)
    assert typ == int or typ == list, "bad type"
    if type(x) == int:
        return x
    elif type(x) == list:
        return x[index]

def draw_efficiency(sim_data, labels=None, title=None):
    """
    Simple drawer to create line-based efficiencies, one per simulation, with error bars. Can pass one or a list of simulations. Can define custom labels and a custom title.
    """

    # Unify types
    if type(sim_data) is not list:
        sim_data = [sim_data]
    
    # Unify types, extract labels
    if labels is not None and type(labels) is not list:
        labels = [labels]
    elif labels is None:
        labels = []
        for sd in sim_data:
            labels.append(sd['params']['sim_name'])
    
    if title is None:
        title = "Efficiencies over Weeks"
    
    # Get data to plot (xs, efficiencies, errors)
    nws = []
    eff_avgs = []
    eff_stds = []
    
    for sd in sim_data:
        nw = sd['params']['num_weeks']
        nt = sd['params']['num_trials']
        nws.append(nw)
        eff_avg, std_error, eff_min, eff_max = dm_sim.analyze_eff_data(nt, nw, sd)
        eff_avgs.append(eff_avg)
        eff_stds.append(std_error)
    

    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Plot each sim's data
    for i in range(len(sim_data)):
        x = range(1, nws[i]+1)
        e_avg = eff_avgs[i]
        e_std = eff_stds[i]
        lab = labels[i]

        ax.plot(x, e_avg, label = lab, lw =3)
        ax.errorbar(x, e_avg, yerr=e_std, fmt='.k')

    x_max = max(nws)
    ax.set_xlabel('Week', size = 'x-large') 
    ax.set_xbound(0, x_max)
    ax.set_ybound(0, 100)
    ax.grid(1)
    ax.set_ylabel('Efficiency', size = 'x-large') 
    ax.set_title(title, size = 'x-large')
    ax.legend(fontsize='x-large')
    plt.show()

def gen_agent_groups(num_agents, agent_type, agent_class, strategy_params, lower_bound, upper_bound, num_units, endowment, payoff_function=None, move_error_rate=0, starting_location=None, return_names=False):
    """
    Generate agent groups based on the passed parameters. Optionally returns generated names for these groups.

    Can be improved by duck-typing instead of checking for list type.
    """

    # Gather the variables
    varlist = [num_agents, agent_type, agent_class, strategy_params, lower_bound, upper_bound, num_units, endowment, payoff_function, move_error_rate, starting_location]

    # Check which items were sent as lists
    as_list = []
    for i in range(len(varlist)):
        as_list.append(type(varlist[i]) is list)

    # If none of the items are lists, simply set all as a list of length 1
    if not any(as_list):
        for i in range(len(varlist)):
            varlist[i] = [varlist[i]]
        list_len = 1
    
    # Otherwise, check the length of the lists are the same and broadcast non-lists
    else:
        list_len = None
        for i in range(len(varlist)):
            if as_list[i]:
                ln = len(varlist[i])
                if list_len is None:
                    list_len = ln
                elif list_len != ln:
                    raise ValueError("All lists passed to gen_agent_groups must be of the same length")
        for i in range(len(varlist)):
            if not as_list[i]:
                varlist[i] = [varlist[i]]*list_len
    
    # Create the agent_defs
    ag_groups = []
    gr_names = []
    for i in range(list_len):
        ag_vars = [x[i] for x in varlist]

        ag_groups.append(ag_vars)

        nm = f"{varlist[1][i]}_{varlist[2][i]}_gr_{i}"
        gr_names.append(nm)

    if return_names:
        return ag_groups, gr_names
    else:
        return ag_groups

def print_agents(agents, print_types=False):
    """Print the passed list of agents"""
    for agent in agents:
        if print_types:
            print(agent, type(agent))
        else:
            print(agent)

def long_class_surplus(week_df):
    """Return the 'class_surplus' and id columns as long-form DataFrame to easily analyze"""

    # TODO: refactor type_effs group_effs to class_surplus, group_surplus
    # Transform MC DataFrame to have class_surplus and group_surplus pulled out as their own "wide-wise" entries
    
    return long_x_surplus(week_df, x='class_surplus', j='agent_class')

def long_group_surplus(week_df):
    """Return the 'group_surplus' and id columns as long-form DataFrame to easily analyze"""
    
    return long_x_surplus(week_df, x='group_surplus', j='agent_group')


def dict_to_list(dict_cn):
    """Turn dictionary definitions into an organized list."""
    dl = list(dict_cn)
    sp_names = sorted(dl)
    re_vals = []

    for i in range(len(sp_names)):
        sn = sp_names[i]
        sv = dict_cn[sn]
        re_vals.append(sn)
        re_vals.append(sv)
    
    return re_vals


def long_x_surplus(week_df, x='class_surplus', j='agent_class'):
    """Return the x and id columns as long-form DataFrame to easily analyze"""
    
    id_cols = ['sim_name', 'week']

    # check if this is a MonteCarlo DataFrame
    try:
        week_df['trial']
        # Trials is part of id columns if monte carlo
        id_cols = id_cols + ['trial']
    except:
        pass

    # check if there are defined treatments
    try:
        week_df['treatment']
        # treatment is part of id columns if defined
        id_cols = id_cols + ['treatment']
    except:
        pass
    
    # Save data from surplus defs
    pref = x[:2] + '_'
    small_df = week_df[id_cols].copy()

    small_df['ls'] = week_df[x].apply(dict_to_list)

    # Organize surpluses into columns
    num_groups = int(len(small_df['ls'].iloc[0])/2)
    for i in range(num_groups):
        g_name = small_df['ls'].apply(lambda x: x[0+2*i])
        g_val = small_df['ls'].apply(lambda x: x[1+2*i])
        q_col = pref + g_name.iloc[0]
        small_df[q_col] = g_val

    small_df = small_df.drop(columns="ls")

    # Change columns from wide to long format
    re_df = pd.wide_to_long(small_df, stubnames=pref, i=id_cols, j=j, 
                            suffix='\w+').reset_index()
    re_df = re_df.rename(columns={pref:x+'_val'})

    return re_df


def summary_surplus(week_df):
    """Return a DataFrame of summary statistics at the week-level for efficiency, class_surplus, and group_surplus"""

    # Check if there are treatments within the DF
    try:
        week_df['treatment']
        has_trt = True
    except:
        has_trt = False


    # Class surpluses
    id_cols = ['sim_name', 'agent_class', 'week']
    if has_trt:
        id_cols.append('treatment')
    ac_df = long_class_surplus(week_df)
    ac_df = ac_df.drop(columns='trial')

    # Calculate avg
    avg_val = ac_df.groupby(by=id_cols).mean()
    avg_val = avg_val.rename(columns={'class_surplus_val':'csv_avg'})

    # Calculate std
    std_val = ac_df.groupby(by=id_cols).std()
    std_val = std_val.rename(columns={'class_surplus_val':'csv_std'})

    # Calculate sem
    sem_val = ac_df.groupby(by=id_cols).sem()
    sem_val = sem_val.rename(columns={'class_surplus_val':'csv_sem'})

    merged_ac = avg_val.merge(std_val, on=id_cols).reset_index()
    merged_ac = merged_ac.merge(sem_val, on=id_cols).reset_index()

    # Group surpluses
    id_cols = ['sim_name', 'agent_group', 'week']
    if has_trt:
        id_cols.append('treatment')
    ag_df = long_group_surplus(week_df)
    ag_df = ag_df.drop(columns='trial')

    # Calculate avg
    avg_val = ag_df.groupby(by=id_cols).mean()
    avg_val = avg_val.rename(columns={'group_surplus_val':'gsv_avg'})

    # Calculate std
    std_val = ag_df.groupby(by=id_cols).std()
    std_val = std_val.rename(columns={'group_surplus_val':'gsv_std'})

    # Calculate sem
    sem_val = ag_df.groupby(by=id_cols).sem()
    sem_val = sem_val.rename(columns={'group_surplus_val':'gsv_sem'})

    merged_ag = avg_val.merge(std_val, on=id_cols).reset_index()
    merged_ag = merged_ag.merge(sem_val, on=id_cols).reset_index()

    # Efficiencies
    id_cols = ['sim_name', 'week']
    if has_trt:
        id_cols.append('treatment')
    cp_cols = id_cols + ['eff']
    e_df = week_df[cp_cols].copy()

    avg_val = e_df.groupby(by=id_cols).mean()
    avg_val = avg_val.rename(columns={'eff':'eff_avg'})
    
    std_val = e_df.groupby(by=id_cols).std()
    std_val = std_val.rename(columns={'eff':'eff_std'})

    # Calculate sem
    sem_val = e_df.groupby(by=id_cols).sem()
    sem_val = sem_val.rename(columns={'eff':'eff_sem'})

    merged_eff = avg_val.merge(std_val, on=id_cols).reset_index()
    merged_eff = merged_eff.merge(sem_val, on=id_cols).reset_index()

    return merged_eff, merged_ac, merged_ag


def graph_summary(sum_df, by=None, title=None):
    """Graph surpluses or efficiencies from summary."""

    if title is not None:
        tl = title
    else:
        tl = "Comparison of Efficiencies over Weeks between Simulations"

    sim_name = sum_df['sim_name'].iloc[0]

    # Configure for type of aggregation
    if by is None:
        y_av = 'eff_avg'
        y_sm = 'eff_sem'
        yn = 'Efficiency'
        ymax = 120
        by_groups = False
        if not tl:
            tl = f"Average efficiency + std_errors across trials for {sim_name}"
    else:
        yn = 'Surplus'
        if by == 'agent_class':
            y_av = 'csv_avg'
            y_sm = 'csv_sem'
            
        elif by == 'agent_group':
            y_av = 'gsv_avg'
            y_sm = 'gsv_sem'
        else:
            raise ValueError('by value passed unknown')
        ymax = max(sum_df[y_av])*1.2
        by_groups=True
        groups = sorted(list(sum_df[by].unique()))
        if not tl:
            tl = f"Average surplus per {by} + std_errors across trials for {sim_name}"
    xn = 'Week'
    xmax = max(sum_df['week'])+1
    x = list(range(xmax))

    fig, ax = plt.subplots(figsize=(10, 8))

    if not by_groups:
        ax.plot(x, sum_df[y_av], linestyle = 'solid', lw =3)
        ax.errorbar(x, sum_df[y_av], yerr=sum_df[y_sm], color='black')

    else:
        for gr in groups:
            cut_df = sum_df[sum_df[by]==gr]

            ax.plot(x, cut_df[y_av], label = gr, linestyle = 'solid', lw =3)
            ax.errorbar(x, cut_df[y_av], yerr=cut_df[y_sm], color = 'black')

        ax.legend(fontsize='x-large')

    ax.set_xlabel(xn, size = 'x-large') 
    ax.set_xbound(0, xmax)
    ax.set_ybound(0, ymax)
    ax.grid(1)
    ax.set_ylabel(yn, size = 'x-large') 
    ax.set_title(tl, size = 'x-large')
    plt.show()


def plot_comp_efficiencies(sum_dfs, title=None, labels=None):
    """Plot a comparison of efficiencies across the passed list of summary dataframes or across the treatments within the passed summary dataframe.
    
    Note: the treatments are always processed in an alphabetically ascending way.
    """

    # Allow custom title
    if title is not None:
        tl = title
        

    # Allow custom labels
    if labels is not None:
        labs = labels

    # Check if passed a list or df with treatments
    if type(sum_dfs) is not list:
        try:
            sum_dfs['treatment']
        except:
            raise ValueError("If not passing a list of sum_df, must have treatment specified within the sum_df")
        
        treats = sorted(list(sum_dfs['treatment'].unique()))

        if title is None:
            tl = "Comparison of Efficiencies Across Treatments"
        
        cross_df = sum_dfs

    # If passed a list of df, check you have only one treatment per df or no treatments
    else:
        if title is None:
            tl = "Comparison of Efficiencies Across Simulations"

        cross_df = None
        treats = []
        for i in range(len(sum_dfs)):
            i_df = sum_dfs[i].copy()
            sn = i_df['sim_name'].iloc[0]

            if sn in treats:
                raise ValueError("If using list-of-sum_df mode, sim_names must differ")

            treats.append(sn)
            try:
                i_df['treatment']
                if len(i_df['treatment'].unique())>1:
                    raise ValueError("Cannot pass sum_dfs with >1 treatment if using list-of-sum_df mode.")

            except KeyError:
                pass
            
            # Normalize so both modes use the same type of infrastructure
            i_df['treatment'] = sn
            if cross_df is None:
                cross_df = i_df
            else:
                cross_df = pd.concat([cross_df, i_df])
    
    if labels is None:
        labs = treats
    
    y_av = 'eff_avg'
    y_sm = 'eff_sem'
    yn = 'Efficiency'
    ymax = 120

    xmax = max(cross_df['week'])+1
    x = list(range(xmax))
    xn = 'Week'

    fig, ax = plt.subplots(figsize=(10, 8))

    for i in range(len(treats)):
        cut_df = cross_df[cross_df['treatment']==treats[i]]

        ax.plot(x, cut_df[y_av], label = labs[i], linestyle = 'solid', lw =3)
        ax.errorbar(x, cut_df[y_av], yerr=cut_df[y_sm], color = 'black')
        # TODO: refactor to non-black - need to get a list of colors BEFORE

    ax.legend(fontsize='x-large')

    ax.set_xlabel(xn, size = 'x-large') 
    ax.set_xbound(0, xmax)
    ax.set_ybound(0, ymax)
    ax.grid(1)
    ax.set_ylabel(yn, size = 'x-large') 
    ax.set_title(tl, size = 'x-large')
    plt.show()


if __name__ == "__main__":

    # Run Test Simulation to make sure things are working
    debug = False
    num_periods = 7
    num_rounds = 30
    grid_size = 10

    agent_list = test_agents(debug)
    print_agents(agent_list)
