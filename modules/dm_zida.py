class ZIDA(Trader):
    """
        Zero Intelligence variant for decentralized market
        with Affinity to other traders
        <==> Bias to stay in current location
    """

    def start(self, pl):
        """
        Sets up values for trading
        Does not use payload - pl
        """
        self.units_transacted = 0
        self.cur_unit = 0
        if self.type == "BUYER":
            self.max_units = len(self.values)
        else:
            self.max_units = len(self.costs)
        return_msg = Message("Initial", self.name, self.name, "Initialized")
        self.returned_msg(return_msg)
        return return_msg

    def move_requested(self, pl):
        """
        Make a move in a random direction but with bias to stay if you can still trade
        Stickiness to state quo is determined by the contract number in the last day
        """
        # get whole contract dic from class SimulateMarket
        contracts_whole = self.simulation.contracts
        # get contract dic in the last week, key = week, make it a list
        bias = 0
        if len(contracts_whole) > 0:
            contracts_week = list(contracts_whole.items())[-1][-1]
            # transfer dic to list, get the last day's contract list (second last value in the dic)
            if len(contracts_week) > 1:
                contracts_day = list(contracts_week.items())[-2][-1]
                # bias to stay = number of accumulated contract the trader make in the last day(0 in every Monday)
                for i in contracts_day:
                        if self.name == i[-1] or self.name == i[-2]:
                            bias = bias + 1
        direction_list = [-1, 0, +1] + 10 * bias * [0] #

        if self.cur_unit > self.max_units:
            return_msg = Message("MOVE", self.name, "Travel", (0, 0))
            self.returned_msg(return_msg)
            return return_msg
        else:
            x_dir = rnd.choice(direction_list)
            y_dir = rnd.choice(direction_list)
            return_msg = Message("MOVE", self.name, "Travel", (x_dir, y_dir))
            self.returned_msg(return_msg)
            return return_msg

    def action_requested(self, pl):
        """
        Make a bid or ask
        """
        if self.debug:
            print(f"-- {self.name} has {self.units_transacted} of {self.max_units}")
            print(f"-- {self.name} working on unit {self.cur_unit}")
        if self.cur_unit >= self.max_units:
            return_msg = Message("NULL", self.name, "BARGAIN", None)
            self.returned_msg(return_msg)
            return return_msg

        current_offers = pl

        if self.type == "BUYER":
            WTP = rnd.randint(self.lower_bound, self.values[self.cur_unit])
            offers = []
            for trader_id in current_offers:
                if current_offers[trader_id] == None:
                    continue
                offer_type = current_offers[trader_id][0]
                offer_amount = current_offers[trader_id][1]
                if offer_type == "ASK":
                    offers.append((trader_id, offer_amount))
            # Now find an offer
            if len(offers) > 0:
                offer = rnd.choice(offers)
                if WTP >= offer[1]:  # offer[1] = sellers willingness to accept
                    seller_id = offer[0]
                    return_msg = Message("BUY", self.name, "BARGAIN", seller_id)
                    self.returned_msg(return_msg)
                    return return_msg
                else:
                    return_msg = Message("BID", self.name, "BARGAIN", WTP)
                    self.returned_msg(return_msg)
                    return return_msg
            else:
                return_msg = Message("BID", self.name, "BARGAIN", WTP)
                self.returned_msg(return_msg)
                return return_msg

        else:  # for SELLER
            print("checking", self.cur_unit, self.costs[self.cur_unit], self.upper_bound)
            WTA = rnd.randint(self.costs[self.cur_unit], self.upper_bound)
            offers = []
            for trader_id in current_offers:
                if current_offers[trader_id] == None:
                    continue
                offer_type = current_offers[trader_id][0]
                offer_amount = current_offers[trader_id][1]
                if offer_type == "BID":
                    offers.append((trader_id, offer_amount))
            # Now find an offer
            if len(offers) > 0:
                offer = rnd.choice(offers)
                if WTA <= offer[1]:  # offer[1] = buyers willingness to pay
                    buyer_id = offer[0]
                    return_msg = Message("SELL", self.name, "BARGAIN", buyer_id)
                    self.returned_msg(return_msg)
                    return return_msg
                else:
                    return_msg = Message("ASK", self.name, "BARGAIN", WTA)
                    self.returned_msg(return_msg)
                    return return_msg
            else:
                return_msg = Message("ASK", self.name, "BARGAIN", WTA)
                self.returned_msg(return_msg)
                return return_msg

    def contract(self, pl):
        """
        Update contract information for ZID Trader
        """
        contract = pl
        price = contract[1]
        buyer_id = contract[2]
        seller_id = contract[3]
        if self.type == 'BUYER':
            if self.get_name() != buyer_id:
                return_msg = Message("BAD", self.name, "BARGAIN",
                                     "08 Not buyer contract")
                self.returned_msg(return_msg)
                return return_msg
            self.units_transacted += 1
            self.cur_unit += 1
        else:  # SELLER
            if self.get_name() != seller_id:
                return_msg = Message("BAD", self.name, "BARGAIN",
                                     "09 Not seller contract")
                self.returned_msg(return_msg)
                return return_msg
            self.units_transacted += 1
            self.cur_unit += 1

        return_msg = Message("Update", self.name, "BARGAIN",
                             "10 Units Updated")
        self.returned_msg(return_msg)
        return return_msg