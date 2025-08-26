"""
This file contains institutions which allow agents to track the evolution of 
"""

import pandas as pd

class BargainHistory(object):
    """
    This institution, BargainHistory stores the offers (quotes) and contracts created during a run of DM markets. Quotes and contracts are stored with as many details as possible, including assigning an ID to quotes, to map quotes-to-contracts directly.

    Importantly these cannot be stored by the DM Bargain institution - as that institution is initiated each round and at each location individuals can trade at - thus it cannot also store a persistent history.

    key params:
        project_global (bool, default False): If the institution should send all histories globally. If False, sends only history at the individual location.

        include_locations (bool, default False): If the institution should include locations in the quote and contract histories.

        history_duration (int, default 0): How many periods back of history to include in transmission. By default only the 0th period (the present period, for which bargaining just ended) is included.

    """
    def __init__(self, num_periods, 
                 project_global=False, include_locations=False, history_duration=0):
        
        self.num_periods = num_periods # Number of periods in a week

        self.project_global = project_global
        self.include_locations = include_locations
        self.history_duration = history_duration

        # Stores quotes at the week-period-round-location level
        # Each quote is assigned a unique ID - for simplicity just counting up from 0
        # Stored as DataFrame of quote ID + offer_tuple
        # TODO: harmonize quote and offer
        # TODO: add quote ID to quote
        self.offer_history = None # TODO: check on the behavior of empty df - can we declare this here?
        self.next_offer_id = 0

        # Stores contracts at the week-period-round-location level
        # Contracts contain ID for which quote they relate to
        # Stored as dictionary of contract ID + contract tuple
        # TODO: add quote ID to contract
        # TODO: add contract ID to contract
        self.contract_history = None # TODO: Same as above
        self.next_contract_id = 0

    def get_histories(self, cur_week, cur_period, cur_loc):
        """
        Return the quote history and contract history at the location (or globally if global version) for the last history_duration periods. Quote and contract history may include locations, if those are to be provided.

        parameters:
            cur_week: current week.
            cur_period: current period.
            cur_loc: the tuple location of the agent.

        returns:
            q_hist_local (list) a list of quotes at the location
            c_hist_local (list) a list of contracts at the location
            q_hist_global (list) a list of quotes globally or None
            c_hist_global (list) a list of contracts globally or None
        """

        # Number of periods before current week required
        period_before_week = cur_period - self.history_duration

        # Number of weeks before current week required
        weeks_back = (-1*period_before_week)//self.num_periods

        # Week to start at
        start_week = max(0, cur_week-weeks_back)

        # Period to start at (within a week)
        if period_before_week < 0:
            start_period = cur_period - self.history_duration + self.num_periods
        else:
            start_period = max(0, cur_period-self.history_duration)

        # Subset offer history
        qh_df = self.offer_history
        rec_qs = qh_df[(qh_df['week']>=start_week)&(qh_df['period']>=start_period)]
        q_hist_local = rec_qs[rec_qs['location']==cur_loc]

        # Subset contract history
        ch_df = self.contract_history
        rec_cs = ch_df[(ch_df['week']>=start_week)&(ch_df['period']>=start_period)]
        c_hist_local = rec_cs[rec_qs['location']==cur_loc]

        # If do not want global price info, returns Nones
        if not self.project_global:
            q_hist_global = None
            c_hist_global = None
        # If do not include location data, replace with None
        elif not self.include_locations:
            q_hist_global = rec_qs.copy()
            q_hist_global['location'] = None

            c_hist_global = rec_cs.copy()
            c_hist_global['location'] = None
        # Otherwise return full most recent offer and contract info
        else:
            q_hist_global = rec_qs
            c_hist_global = rec_cs

        return q_hist_local, c_hist_local, q_hist_global, c_hist_global
    
    def get_offer_id(self):
        """Return the current next offer ID number and increment internally"""
        id = self.next_offer_id
        self.next_offer_id += 1
        return id
    
    def get_contract_id(self):
        """Return the current next contract ID number and increment internally"""
        id = self.next_contract_id
        self.next_contract_id += 1
        return id
    
    def add_offers(self, offers_tuples):
        """Add the list of offer tuples to the history"""

        # offer structure (round, sender_id, offer_type, payload, offer_id, loc, week, period)
        colns = ['round', 'sender_id', 'offer_type', 'price', 'offer_id', 'loc', 'week', 'period', 'accepted', 'is_last']
        new_offers = pd.DataFrame(data=offers_tuples, columns=colns)

        if self.offer_history is None:
            self.offer_history = new_offers
        else:
            self.offer_history = pd.concat(self.offer_history, new_offers)

    def add_contracts(self, contract_tuples):
        """Add the list of contract tuples to the history"""

        # contract structure (round, price, buyer_id, seller_id, offer_id, contract_id, loc, week, period)
        colns = ['round', 'price', 'buyer_id', 'seller_id', 'offer_id', 'contract_id', 'loc', 'week', 'period', 'is_last']
        new_contracts = pd.DataFrame(data=contract_tuples, columns=colns)

        if self.contract_history == None:
            self.contract_history = new_contracts
        else:
            self.contract_history = pd.concat(self.contract_history, new_contracts)

    def close_location_record(self, week, period, loc):
        """Close the bargaining history at this location - indicate the present last quote and contract are the last ones"""

        # If week is passed as -1, skip this step
        if week == -1:
            return

        # Get index last offer (quote)
        oh = self.offer_history
        ohl_ind = oh[(oh['week']==week)&(oh['period']==period)&(oh['location']==loc)].iloc[-1].name
        # Set flag to indicate last quote
        self.offer_history.loc[ohl_ind, 'is_last'] = True

        # Get index last contract
        ch = self.contract_history
        chl_ind = ch[(ch['week']==week)&(ch['period']==period)&(ch['location']==loc)].iloc[-1].name
        # Set flag to indicate last contract
        self.contract_history.loc[chl_ind, 'is_last'] = True

    def indicate_accepted(self, offer_id):
        # Get index of offer
        oh = self.offer_history
        ohi_ind = oh[(oh['offer_id']==offer_id)].iloc[0].name
        # Set flag to indicate last quote
        self.offer_history.loc[ohi_ind, 'accepted'] = True