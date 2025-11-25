# -*- coding: utf-8 -*-
from __future__ import annotations
from abc import ABC, abstractmethod
from Main.NetworkCommand import NetworkCommand

class IRatchet(ABC):
    @abstractmethod
    def Encode(self, command: NetworkCommand):
        pass
    
    @abstractmethod
    def Decode(self, command: NetworkCommand):
        pass
    
