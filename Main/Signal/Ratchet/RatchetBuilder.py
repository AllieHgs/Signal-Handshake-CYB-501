# -*- coding: utf-8 -*-
from __future__ import annotations
from Main.Signal.Ratchet.IRatchet import IRatchet
from Main.Signal.Ratchet.Ratchet import Ratchet

class RatchetBuilder():
    def __init__(self): 
        pass
    
    def Build(self) -> IRatchet:
        ratchet = Ratchet(None)
        
        return ratchet