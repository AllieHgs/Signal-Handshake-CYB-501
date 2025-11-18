# -*- coding: utf-8 -*-
from __future__ import annotations
from Main.Signal.IRatchet import IRatchet
from Main.Signal.DoubleRatchet import DoubleRatchet

class RatchetBuilder():
    def __init__(self): #Required Parameters
        pass
    
    #Optional Parameters
    '''
    def WithSomething(self, something :str) -> RatchetBuilder:
        self.something = something
        return self
    '''
    
    def Build(self) -> IRatchet:
        # Create & configure
        ratchet = DoubleRatchet()
        
        return ratchet
        pass