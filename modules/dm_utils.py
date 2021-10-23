import dm_agents as dma

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
