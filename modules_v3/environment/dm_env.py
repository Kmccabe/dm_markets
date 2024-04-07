import random as rnd
import operator
import matplotlib.pyplot as plt                 # import matplotlib
import numpy as np                              # import numpy
import time
import copy
import os
import json
import pandas as pd

class SpotMarketEnvironment(object):
    """ A class that makes a market environment consisting of buyers who make
        up the demand curve and sellers who make up the supply curve.  This
        class will also calculate market equilibria and plot the supply and
        demand curves and as an option contract prices."""

    def __init__(self, name="example", num_buyers=2, num_sellers=3, item_types=("C"), market_type="ONE_TYPE"):
        """ name (str) = the name of the market
            num_Buyers (int) = the number of buyers in the market
            num_sellers(int) = the number of sellers in the market
            Builds buyers and sellers dictioanry entries
        """
        self.name = name
        self.num_buyers = num_buyers
        self.num_sellers = num_sellers
        self.demand = []
        self.supply = []
        self.buyers = {}
        self.sellers = {}

        # equilibrium calculations made in calc_equilibrium
        self.eq_price_low = None
        self.eq_price_high = None
        self.eq_units = None
        self.eq_max_surplus = None

        for buyer_number in range(self.num_buyers):
            buyer_id = "buyer" + str(buyer_number)
            self.buyers[buyer_id] = []  # Empty list of values for buyer_id

        for seller_number in range(self.num_sellers):
            seller_id = "seller" + str(seller_number)
            self.sellers[seller_id] = []  # Empty list of costs for seller_id

        self.market_type = market_type
        self.item_types = item_types

        # TWO_TYPE
        self.i_num_buyers = {}
        self.i_num_sellers = {}
        self.i_demand = {}
        self.i_supply = {}
        self.i_buyers = {}
        self.i_sellers = {}
        self.i_eq_units = {}
        self.i_eq_price_low = {}
        self.i_eq_price_high = {}
        self.i_max_surplus = {}
        for i_type in self.item_types:
            self.i_num_buyers[i_type] = num_buyers
            self.i_num_sellers[i_type] = num_sellers
            self.i_demand[i_type] = []
            self.i_supply[i_type] = []
            self.i_buyers[i_type] = {}
            self.i_sellers[i_type] = {}
            self.i_eq_units[i_type] = None
            self.i_eq_price_low[i_type] = None
            self.i_eq_price_high[i_type] = None
            self.i_max_surplus[i_type] = None

        for i_type in self.item_types:            
            for buyer_number in range(self.i_num_buyers[i_type] ):
                buyer_id = "buyer" + str(buyer_number)
                self.i_buyers[buyer_id] = []  # Empty list of values for buyer_id

            for seller_number in range(self.i_num_sellers[i_type]):
                seller_id = "seller" + str(seller_number)
                self.i_sellers[seller_id] = []  # Empty list of costs for seller_id

    def show_market(self):
        """Prints market name, number of buyers and number of sellers
        """
        print(f"I am market {self.name} with {self.num_buyers} buyers and " \
              f"{self.num_sellers} sellers")
        print("")

    def show_participants(self):
        """Prints buyers and sellers info
        """
        print("Market Participants")
        print("-------------------")
        print("BUYERS")
        print("------")
        for buyer_number in range(self.num_buyers):
            buyer_id = "buyer" + str(buyer_number)
            print(f"{buyer_id} has values {self.buyers[buyer_id]}")
        print()
        print("SELLERS")
        print("-------")
        for seller_number in range(self.num_sellers):
            seller_id = "seller" + str(seller_number)
            print(f"{seller_id} has costs {self.sellers[seller_id]}")
        print("")

    def add_buyer(self, buyer_number, values, item_type="C"):
        """Adds a list of buyer_number's values to the self.buyers dictionary
        """

        # TODO change buyer and seller adder and getter to be uniformed
        if self.market_type == "ONE_TYPE":
            buyer_id = "buyer" + str(buyer_number)
            self.buyers[buyer_id] = values
        elif self.market_type == "TWO_TYPE":
            buyer_id = "buyer" + str(buyer_number)
            self.i_buyers[item_type][buyer_id] = values
            # self.buyers[buyer_id] = values

    def get_buyer_values(self, buyer_number, item_type):
        """Returns buyer_number's values
        """
        if self.market_type == "ONE_TYPE":
            buyer_id = "buyer" + str(buyer_number)
            return self.buyers[buyer_id]
        elif self.market_type == "TWO_TYPE":
            buyer_id = "buyer" + str(buyer_number)
            return self.i_buyers[item_type][buyer_id]

    def get_buyers(self):
        return self.buyers

    def add_seller(self, seller_number, costs, item_type="C"):
        """Adds a list of seller_number's costs to the self.seller dictionary
        """
        if self.market_type == "ONE_TYPE":
            seller_id = "seller" + str(seller_number)
            self.sellers[seller_id] = costs
        elif self.market_type == "TWO_TYPE":
            seller_id = "seller" + str(seller_number)
            self.i_sellers[item_type][seller_id] = costs

            

    def get_seller_costs(self, seller_number, item_type="C"):
        """Returns seller_number_s costs
        """
        if self.market_type == "ONE_TYPE":
            seller_id = "seller" + str(seller_number)
            return self.sellers[seller_id]
        elif self.market_type == "TWO_TYPE":
            seller_id = "seller" + str(seller_number)
            return self.i_sellers[item_type][seller_id]

    def get_sellers(self):
        return self.sellers

    def make_demand(self, avg_two=True):
        """ Makes demand list by adding participant values to the demand list
            and sorting the list from high to low.
        """
        if self.market_type == "ONE_TYPE":
            self.demand = []
            for buyer_id in self.buyers.keys():
                for value in self.buyers[buyer_id]:
                    self.demand.append((buyer_id, value))
            self.demand = sorted(self.demand, key=operator.itemgetter(1), \
                                reverse=True)
        elif self.market_type == "TWO_TYPE":
            for i_type in self.item_types:
                demand = []
                for buyer_id in self.i_buyers[i_type].keys():
                    for value in self.i_buyers[i_type][buyer_id]:
                        demand.append((buyer_id, value))
                demand = sorted(demand, key=operator.itemgetter(1), \
                    reverse=True)
                self.i_demand[i_type] = demand
            if avg_two:
                d1 = pd.DataFrame(np.array(self.i_demand[self.item_types[0]]))
                d1 = d1.rename(columns={0:'t_id', 1:'val'})
                d1 = d1['val'].apply(int).values
                d2 = pd.DataFrame(np.array(self.i_demand[self.item_types[1]]))
                d2 = d2.rename(columns={0:'t_id', 1:'val'})
                d2 = d2['val'].apply(int).values
                avg_d = list((d1+d2)/2)
                names = ["Buyer N/A"]*len(avg_d)
                out = list(zip(names, avg_d))

                self.demand = out

    def make_supply(self, avg_two=True):
        """ Makes supply list by adding participant costs to the supply list
            and sorting the list from low to high.
        """
        if self.market_type == "ONE_TYPE":
            self.supply = []
            for seller_id in self.sellers.keys():
                for cost in self.sellers[seller_id]:
                    self.supply.append((seller_id, cost))
            self.supply = sorted(self.supply, key=operator.itemgetter(1), \
                                reverse=False)
        elif self.market_type == "TWO_TYPE":
            for i_type in self.item_types:
                supply = []
                for seller_id in self.i_sellers[i_type].keys():
                    for value in self.i_sellers[i_type][seller_id]:
                        supply.append((seller_id, value))
                supply = sorted(supply, key=operator.itemgetter(1), \
                    reverse=False)
                self.i_supply[i_type] = supply
            
            if avg_two:
                s1 = pd.DataFrame(np.array(self.i_supply[self.item_types[0]]))
                s1 = s1.rename(columns={0:'t_id', 1:'val'})
                s1 = s1['val'].apply(int).values
                s2 = pd.DataFrame(np.array(self.i_supply[self.item_types[1]]))
                s2 = s2.rename(columns={0:'t_id', 1:'val'})
                s2 = s2['val'].apply(int).values
                avg_s = list((s1+s2)/2)
                names = ["Buyer N/A"]*len(avg_s)
                out = list(zip(names, avg_s))

                self.supply = out

    def show_supply_demand(self, item_types=["C"], avg_two=False):
        """Prints supply and demand in a table where each row represnts a
           price from high to low.
        """

        # TODO implement for non-avg

        supply_and_demand = self.supply + self.demand
        supply_and_demand = sorted(supply_and_demand, key=operator.itemgetter(1), reverse=True)

        print("Unit    ID       Cost  | Value     ID")
        print("---------------------------------------------------------")
        for index, unit in enumerate(supply_and_demand):
            if unit[0][0] == "b":
                print(f"{index + 1:3}{' ' * 20}| {unit[1]:5}    {unit[0]}")
            if unit[0][0] == "s":
                print(f"{index + 1:3}{' ' * 2}{unit[0]}    {unit[1]:5}  |")
        print("")

    def calc_equilibrium(self):
        """ Calculate Competitive Equilbrium information:
            eq_price_high
            eq_price_low
            eq_units
            max_surplus
        """

        if self.market_type == "ONE_TYPE":
            self.max_surplus = 0
            self.eq_units = 0
            last_accepted_value = 0
            last_accepted_cost = 0
            first_rejected_value = 0
            first_rejected_cost = 999999999  # big number > max cost ever

            for buy_unit, sell_unit in zip(self.demand, self.supply):
                buyid, value = buy_unit
                sellid, cost = sell_unit
                if value >= cost:
                    self.eq_units += 1
                    self.max_surplus += value - cost
                    last_accepted_value = value
                    last_accepted_cost = cost
                else:
                    first_rejected_value = value
                    first_rejected_cost = cost
        
            #  Now caluclate equilibrium price range
            if self.eq_units > 1:
                self.eq_price_high = min(last_accepted_value, first_rejected_cost)
                self.eq_price_low = max(last_accepted_cost, first_rejected_value)
            else:
                print("No Equilibrium") # TODO HERE`

        if self.market_type == "TWO_TYPE":
            max_surps = []
            eqs_us = []
            plows = []
            phighs = []
            for i_type in self.item_types:
                max_surplus = 0 # 
                eq_units = 0 # 
                last_accepted_value = 0
                last_accepted_cost = 0
                first_rejected_value = 0
                first_rejected_cost = 999999999  # big number > max cost ever

                for buy_unit, sell_unit in zip(self.i_demand[i_type], self.i_supply[i_type]):
                    buyid, value = buy_unit
                    sellid, cost = sell_unit
                    if value >= cost:
                        eq_units += 1
                        max_surplus += value - cost
                        last_accepted_value = value
                        last_accepted_cost = cost
                    else:
                        first_rejected_value = value
                        first_rejected_cost = cost
                
                self.i_max_surplus[i_type] = max_surplus
                self.i_eq_units[i_type] = eq_units
                max_surps.append(max_surplus)
                eqs_us.append(eq_units)

                #  Now caluclate equilibrium price range
                if eq_units > 1:
                    self.i_eq_price_high[i_type] = min(last_accepted_value, first_rejected_cost)
                    self.i_eq_price_low[i_type] = max(last_accepted_cost, first_rejected_value)
                phighs.append(self.i_eq_price_high[i_type])
                plows.append(self.i_eq_price_low[i_type])

            self.max_surplus = sum(max_surps)/len(max_surps)
            self.eq_units = sum(eqs_us)/len(eqs_us)
            self.eq_price_high = sum(phighs)/len(phighs)
            self.eq_price_low = sum(plows)/len(plows)


    def show_equilibrium(self):
        #  Print out market equilibrium numbers
        print()
        print("When market {} is in equilibrium we have:".format(self.name))
        print("equilibrium price    = {} - {}".format(self.eq_price_low, self.eq_price_high))
        print("equilibrium quantity = {}".format(self.eq_units))
        print("maximum surplus      = {}".format(self.max_surplus))
        print()

    def get_equilibrium(self, item_type="C"):
        if item_type == "C":
            return self.eq_units, self.eq_price_low, self.eq_price_high, self.max_surplus
        else:
            return self.i_eq_units[item_type], self.i_eq_price_low[item_type], self.i_eq_price_high[item_type], self.i_max_surplus[item_type]

    def plot_supply_demand(self, prices=[]):

        """
        First define supply and demand curves
        """
        # make x-axis arrays for demand_units and supply_units
        dunits = [units for units in range(len(self.demand) + 2)]
        sunits = [units for units in range(len(self.supply) + 1)]
        munits = max(len(dunits), len(sunits))

        # make demand values
        max_value = 0
        for buyerid, value in self.demand:
            if value > max_value:  # find the maximum demand value
                max_value = value
        demand_values = [max_value + 1]  # first element is upper range in graph

        for buyerid, value in self.demand:  # get demand tuples
            demand_values.append(value)  # and pull out second element to get value
        demand_values.append(0)  # pull graph down to x axes

        # make suppl values the same way
        supply_costs = [0]  # note first elemnt is used to create lower range of supply values
        for sellerid, cost in self.supply:  # get supply tupples
            supply_costs.append(cost)  # and pull out second element to get cost

        """
        Set up plot
        """
        plt.figure(figsize=(10, 7.5))  # Set plot dimensions
        ax = plt.subplot(111)
        ax.spines["top"].set_visible(False)
        ax.spines["bottom"].set_visible(True)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_visible(True)
        ax.get_xaxis().tick_bottom()
        ax.get_yaxis().tick_left()
        plt.yticks(fontsize=14)
        plt.xticks(fontsize=14)

        """
        Made a bunch of small changes here
        """
        plt.step(dunits, demand_values, label='Demand')
        plt.step(sunits, supply_costs, label='Supply')

        if len(prices) > 0:
            prices.insert(0, prices[0])  # needed to get line segment for the first price
            punits = [unit for unit in range(len(prices))]
            plt.step(punits, prices, label='Prices')

        ax = plt.gca()
        plt.legend(loc='upper center', frameon=False)
        plt.title('Supply and Demand')
        plt.xlabel('units')
        plt.ylabel('currrency')

        # Save figure in the working directory
        #plt.savefig(self.name+'supply_demand.jpg')

        plt.xlim(0, munits)
        plt.ylim(0, max(demand_values + supply_costs))
        plt.show()
