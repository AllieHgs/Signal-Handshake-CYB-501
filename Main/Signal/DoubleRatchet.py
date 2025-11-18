# -*- coding: utf-8 -*-
from __future__ import annotations
from Main.Signal.IRatchet import IRatchet
from Main.Signal.RatchetHeader import RatchetHeader
from Main.Signal.SignalMail import SignalMail

class DoubleRatchet(IRatchet):
    def __init__(self):
        pass
    
    def Encode(self, mail: SignalMail):
        pass
    
    def Decode(self, mail: SignalMail):
        pass
    