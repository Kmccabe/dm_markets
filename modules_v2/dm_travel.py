import random as rnd
from dm_message_model import Message

class Travel(object):
    """Travel Institution"""
    
    def __init__(self, grid_dimension, agents, debug_flag=False):
        self.grid_dimension = grid_dimension  # determines dimensions of a square grid  
        self.agents = agents  # list of agent objects
        self.grid = {}  #grid is a dictionary indexed by location (x,y)
        self.history = {}
        self.debug = debug_flag
 
    def start_travel(self):
        self.setup_agents_history()
        self.locate_agents()

    def setup_agents_history(self):
        for agent in self.agents:
            loc = agent.get_location()
            self.history[agent.name] = [loc]
        if self.debug:
            print("starting history", self.history)
         
    def locate_agents(self):
        """Put agents in grid"""
        for agent in self.agents:
            loc = agent.get_location()
            if loc in self.grid.keys():
                self.grid[loc].append(agent) # add agent to list of agents at loc
            else:
                self.grid[loc] = [agent]  # start a list of agents
        
    def get_grid(self):
        return self.grid

    def set_debug(self, debug):
        self.debug = debug 
    
    def run(self):
        for point in self.grid:
            agent_order =[]
            for agent in self.grid[point]:
                agent_order.append(agent)
            rnd.shuffle(agent_order)
            for agent in agent_order:
                agent.set_num_at_loc(len(agent_order))
                msg = Message('MOVE_REQUESTED', 'TRAVEL', agent.get_name(), "  ")
                return_msg = agent.process_message(msg)
                if return_msg.get_directive() == "MOVE":
                    x_dir, y_dir = return_msg.get_payload()
                    loc = agent.get_location()
                    # debug message
                    if self.debug:
                        print(f"Travel -> agent {agent.name} at {loc} moves ({x_dir, y_dir})" +
                          "to ", end = "")
                    if 0 <= loc[0] + x_dir and loc[0] + x_dir <= self.grid_dimension - 1:
                        if 0 <= loc[1] + y_dir and loc[1] + y_dir <= self.grid_dimension - 1:
                            location = loc[0] + x_dir, loc[1] + y_dir
                            if self.debug:
                                print("move good", location)
                            agent.set_location(location)
                            self.history[agent.name].append(location)
                        else:
                            agent.set_location(loc)
                            self.history[agent.name].append(loc)
                            if self.debug:
                                print("move bad", loc)
                    else:
                        agent.set_location(loc)
                        self.history[agent.name].append(loc)
                        if self.debug:
                            print("move bad", loc)
        self.grid = {}
        self.locate_agents()
               
    def print_grid(self):
        for x in range(self.grid_dimension):
            for y in range (self.grid_dimension):
                if (x, y) in self.grid.keys():
                    names = []
                    for agent in self.grid[(x, y)]:
                        names.append(agent.get_name())
                    print(f"at point {(x, y)}: {names}")

    def get_history(self):
        return self.history
