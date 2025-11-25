# -*- coding: utf-8 -*-
from __future__ import annotations
import unittest
from Interfaces.INetwork import INetwork, INetworkToken, Status, CommandResult
from Main.Signal.IRatchet import IRatchet
from Main.Signal.DoubleRatchet import DoubleRatchet

class Test_DoubleRatchet(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    def test_simple_pass(self):
        self.assertTrue(True)
        
    def test_constructs(self):
        dratchet = DoubleRatchet()
        self.assertTrue(dratchet is not None)
        

if __name__ == '__main__':
    unittest.main()