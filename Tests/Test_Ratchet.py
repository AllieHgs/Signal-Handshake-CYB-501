# -*- coding: utf-8 -*-
from __future__ import annotations
import unittest
from Main.Signal.Ratchet.IRatchet import IRatchet
from Main.Signal.Ratchet.Ratchet import Ratchet


class Test_DoubleRatchet(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    def test_simple_pass(self):
        self.assertTrue(True)
        
    def test_constructs(self):
        initData = IRatchet.InitData()
        ratchet = Ratchet(initData)
        self.assertTrue(ratchet is not None)
        

if __name__ == '__main__':
    unittest.main()