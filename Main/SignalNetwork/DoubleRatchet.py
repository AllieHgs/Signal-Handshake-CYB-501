# -*- coding: utf-8 -*-
from __future__ import annotations
from Interfaces.IRatchet import IRatchet, RatchetHeader
from Main.SignalNetwork.SignalMail import SignalMail

class DoubleRatchet(IRatchet):
    def __init__(self):
        pass
    
    def Encode(self, mail: SignalMail):
        pass
    
    def Decode(self, mail: SignalMail):
        pass
    