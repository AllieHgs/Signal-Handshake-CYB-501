# -*- coding: utf-8 -*-
from __future__ import annotations
import unittest
from Main.NetworkCommand import NetworkCommand

class Test_NetworkCommand(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass
        
    def test_simple_pass(self):
        self.assertTrue(True)
        
    def test_constructs(self):
        cmd = NetworkCommand()
        self.assertTrue(cmd is not None)
    
    def test_kwargs_applied(self):
        #todo test newline in key / value
        cmd = NetworkCommand("Test", a="a", b=2, c={"x":"x1", "y":"y1"}, d="::,,:;m,@").With(",,ca,::,:", "arg")
        self.assertTrue(cmd.Get("a") == "a")
        self.assertTrue(cmd.Get("b") == 2)
        self.assertTrue(cmd.Get("c") == {"x":"x1", "y":"y1"})
        self.assertTrue(cmd.Get("d") == "::,,:;m,@")
        self.assertTrue(cmd.Get(",,ca,::,:") == "arg")
        
    def test_serialize_deserialize(self):
        cmd = NetworkCommand("Test", a="a", b=2, c={"x":"x1", "y":"y1"}, d="::,,:;m,@")
        ser  = cmd.Serialize()
        dser = NetworkCommand.Deserialize(ser)
        self.assertTrue(cmd.kwargs == dser.kwargs)

if __name__ == '__main__':
    unittest.main()