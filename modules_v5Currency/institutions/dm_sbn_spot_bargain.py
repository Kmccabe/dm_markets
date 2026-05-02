#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 11 14:36:01 2024

@author: alex

Mimics the SB Spot Bargaining Market but allows the placement of more than one 
order of a type for each buyer or seller, allowing the transfer of more than 
one unit within one trading period.

Changes from SB:
    process contract: removes the highest/lowest (standing) bid/ask
    run: contracts are not stored one-per-agent but instead are a list (for pop)

"""

import random as rnd
from institutions.dm_message_model import Message
from institutions.dm_sb_spot_bargain import SB_Spot_Bargain

class SBN_Spot_Bargain(SB_Spot_Bargain):
    
    def __init__(self, rounds, max_orders=1):
        super().__init__(rounds)
        self.max_orders = max_orders
        
    def sort_offers(self, offers):
        type_offer = offers[0][0]
        if type_offer == "BUY":
            desc = False
        if type_offer == "SELL":
            desc = True
        
        sotred_offers = sorted(offers, key=lambda x: x[1], reverse=desc)
    
    def process_contract(self, contract):
        """Remove contract parties offers and inform them that
           they have a contract"""

        #self.contracts.append(contract)  Moved down
        round, price, buyer_id, seller_id = contract

        # cancel orders after contract
        self.order_book[buyer_id] = None
        self.order_book[seller_id] = None
            

        # get agent objects
        buyer_agent_index = self.agent_lookup[buyer_id]
        buyer_agent = self.agent_order[buyer_agent_index]
        seller_agent_index = self.agent_lookup[seller_id]
        seller_agent = self.agent_order[seller_agent_index] 

        ## New code to test -- Get extra contract info
        s_cur_unit = seller_agent.get_cur_unit()
        s_costs = seller_agent.get_costs()
        s_cur_cost = s_costs[s_cur_unit]

        b_cur_unit = buyer_agent.get_cur_unit()
        b_values = buyer_agent.get_values()
        b_cur_value = b_values[b_cur_unit]

        # Send messages to buyer and seller that they have a contract
        msg = Message('CONTRACT', 'BARGAIN', buyer_id, contract)
        return_msg = buyer_agent.process_message(msg) # Send to buyer
        msg = Message('CONTRACT', 'BARGAIN', seller_id, contract)
        return_msg = seller_agent.process_message(msg)  # Send to seller

        # save extended contract
        ex_contract = (round, price, buyer_id, seller_id, b_cur_unit, b_cur_value, s_cur_unit, s_cur_cost)
        self.contracts.append(ex_contract)

        if self.debug:
            print(contract)
            print(ex_contract)
        test_test = 1

    def run(self):
        """Runs bargaining between self.agents
           Accepts BID ASK BUY and SELL messages
           
           Bargaining continues for self.rounds
              Each round agent order is shuffled then
                Each agent makes a BID, ASK BUY or SELL order
                Only the most recent order is kept"""
        
        self.agent_order = self.agents
        self.order_book = {} # Remember - now a dict of list of list
        self.contracts = []
        
        # Begin Bargaining
        for round in range(self.rounds):
            self.make_bargaining_order()
            for agent in self.agent_order:

                # Request and Get: BID, ASK, BUY or SELL message
                agent_id = agent.get_name()
                msg = Message('OFFER', 'BARGAIN', agent_id, self.order_book)
                return_msg = self.send_msg(agent, msg)
                directive = return_msg.get_directive()
                sender_id = return_msg.get_sender()
                payload = return_msg.get_payload()
                #print(f"{sender_id}  {directive}  {payload}")
                # Process message based on directive
                if directive == "NULL":
                    # ignore message and continue to next agent
                    continue
                elif directive == "BID":
                    # put BID in self.order_book
                    offer = ("BID", payload)
                    order_list = self.order_book.get(sender_id)
                    if order_list is None:
                        self.order_book[sender_id] = [offer]
                    else:
                        order_list.append(offer)
                    
                    self.offer_history.append((round, sender_id, "BID", payload)) 
                elif return_msg.get_directive() == "ASK":
                    # put ask in self.order_book
                    offer = ("ASK", payload)
                    # TODO Messy coding here
                    order_list = self.order_book.get(sender_id)
                    if order_list is None:
                        self.order_book[sender_id] = [offer]
                    else:
                        order_list.append(offer)
                    self.offer_history.append((round, sender_id, "ASK", payload))
                else:
                    return Message('BAD', agent.get_name(), 'BARGAIN',
                                   "Unrecognized Directive")
            if self.debug:
                for agent in self.agent_order:
                    print(f"{self.order_book[agent.get_name()]}", end = " ")
                print()

            for agent in self.agent_order:

                # Request and Get: BID, ASK, BUY or SELL message
                agent_id = agent.get_name()
                msg = Message('TRANSACT', 'BARGAIN', agent_id, self.order_book)
                return_msg = self.send_msg(agent, msg)
                directive = return_msg.get_directive()
                sender_id = return_msg.get_sender()
                payload = return_msg.get_payload()

                # Process message based on directive
                if directive == "NULL":
                    # ignore message and continue to next agent
                    continue
                elif directive == "BUY":
                    # make contract if possible
                    buyer_id = sender_id  
                    seller_id = payload
                    this_buyer_offers = self.order_book.get(buyer_id)
                    
                    if this_buyer_offers is None or len(this_buyer_offers) == 0:
                        # cannot make contract continue to next agent
                        continue
                    
                    for b_offer in this_buyer_offers:
                        # process contract
                        price = b_offer[1]
                        self.offer_history.append((round, buyer_id, "BUY", price))
                        contract = (round, price, buyer_id, seller_id)
                        self.process_contract(contract)
                elif directive == "SELL":
                    seller_id = sender_id  # Get Mappings to buyer_id and seller_id
                    buyer_id = payload
                    this_seller_offers = self.order_book.get(seller_id)
                    if this_seller_offers is None or len(this_seller_offers) == 0:
                        # cannot contract continue to next agent
                        continue
                    # process contracts
                    for s_offer in this_seller_offers:
                        price = s_offer[1]
                        self.offer_history.append((round, seller_id, "SELL", price))
                        contract = (round, price, buyer_id, seller_id)
                        self.process_contract(contract)
                else:
                    return Message('BAD', agent.get_name(), 'BARGAIN',
                                   "Unrecognized Directive") 
        if self.debug:
            print(self.contracts)
        test_test = 1