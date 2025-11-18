# -*- coding: utf-8 -*-
from __future__ import annotations
import unittest
from Interfaces.INetwork import INetwork, INetworkToken, Status
from Main.SignalNetwork.IRatchet import IRatchet, RatchetHeader
from Main.SignalNetwork.DoubleRatchet import DoubleRatchet

class DoubleRatchetTests(unittest.TestCase):
    def simple_pass(self):
        self.assertTrue(True)
        
    def construct(self):
        dratchet = DoubleRatchet()
        self.assertTrue(dratchet is not None)