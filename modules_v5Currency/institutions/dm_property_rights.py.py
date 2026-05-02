#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 12 13:40:55 2024

@author: alex
"""

import random as rnd
from institutions.dm_message_model import Message
from institutions.dm_sb_spot_bargain import SB_Spot_Bargain

class Property_Right(object):
    """ The base class which defines property rights in the dm system"""
    def __init__(self, owner=None, private=True, transferable=True):
        self.owner = owner
        self.private = private
        self.transferable = transferable
        