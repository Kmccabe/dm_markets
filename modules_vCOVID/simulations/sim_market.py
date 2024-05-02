import dm_agents
import env_make_agents as mkt
import dm_sim_period as simp
import dm_process_results as pr

#
# Start Initialization Here
#

debug = False  # if True prints debug info on terminal
ZID = dm_agents.ZID # an agent strategy
ZIDA = dm_agents.ZIDA # another agent strategy
trader_objects = [ZID, ZID] # used to compare up to two agent strategies, 
                            # but in this case the same
num_traders = 10 # number of traders
num_units = 8 # number of units buyers can buy and sellers can sell.  
lb = 200 # lower bound on values or costs
ub = 600 # Upper bound on values or costs
grid_size = 4 # grid is grid_size x grid_size

#
# Make Agent Traders
#
movement_error_rate = 0
agent_maker = mkt.MakeAgents(num_traders, trader_objects, num_units, 
                                grid_size, lb, ub, debug, movement_error_rate)
#agent_maker.make_test_agents()
agent_maker.make_agents()
agent_maker.make_locations()
agents = agent_maker.get_agents()
agent_maker.print_agents(agents)

# set up market
agent_maker.make_market("test_market")
agent_maker.show_equilibrium()
agent_maker.plot_market()
market = agent_maker.get_market()

#
# Set up simulation
#
sim_name = 'test'
week = 1
period = 1
num_rounds = 60
debug = False
plot_on = True
sim = simp.SimPeriod(sim_name, week, period, num_rounds, agents, 
                    market, grid_size, debug, plot_on)

# run simulation and process results
sim.run_period()
contracts = sim.get_contracts()
pr0 = pr.ProcessResults(market, sim_name, agents, contracts, debug)
pr0.plot_prices()
pr0.get_results()
pr0.display_results()

# example of longer run
num_periods = 100
sim_name = "multi_period_test"
contracts = []
sim1 = simp.SimPeriod(sim_name, week, period, num_rounds, agents, 
                market, grid_size, debug, plot_on)
for period in range(num_periods):
    sim1.run_period()
    contracts.extend(sim1.get_contracts())

pr1 = pr.ProcessResults(market, sim_name, agents, contracts, debug)
pr1.plot_prices()
pr1.get_results()
pr1.display_results()



