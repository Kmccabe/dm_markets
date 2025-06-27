import environment.dm_agents as dma

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
        print(f"{agent_class_name} takes \"reset_flag_frequency\", representing the rule on which to resume movement, as a parameter. Additional parameters may be required, as specified below.")
        print("\"reset_flag_frequency\" can take the values of [\"NONE\", \"START\", \"WEEK\", \"MIN_AGENTS\", \"WINDOW\"]")
        print("NONE: Never resume movement after trading. No additional parameters")
        print("START: Resume movement at the start of each week (every time agent.start is called). No additional parameters.")
        print("WEEK: Resume movement is did not trade at least \"reset_flag_min_trades\" in the past week (time between agent.start is called).")
        print("MIN_AGENTS: Resume movement is there are less than \"reset_flag_min_agents\" agents at the same location as this agent.")
        print("WINDOW: Resume movement is did not trade at least \"reset_flag_min_trades\" in the last \"reset_flag_window\" periods.")
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

def print_agents(agent_list):
    for agent in agent_list:
        print(agent)

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


def print_contracts(contracts):
    print("CONTRACTS: (round, price, buyer, seller")
    print("---------------------------------------")
    for contract in contracts:
        round = contract[0]
        price = contract[1]
        buyer = contract[2]
        seller = contract[3]
        print(f"{round:2} {price:3} {buyer:3} {seller:3}")

if __name__ == "__main__":

    # Run Test Simulation to make sure things are working
    debug = False
    num_periods = 7
    num_rounds = 30
    grid_size = 10

    agent_list = test_agents(debug)
    print_agents(agent_list)
