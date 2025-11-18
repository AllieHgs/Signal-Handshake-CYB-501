# -*- coding: utf-8 -*-
from __future__ import annotations
from abc import ABC, abstractmethod
from Main.SignalNetwork import SignalMail

class IRatchet(ABC):
    @abstractmethod
    def Encode(self, mail: SignalMail):
        pass
    
    @abstractmethod
    def Decode(self, mail: SignalMail):
        pass
    
