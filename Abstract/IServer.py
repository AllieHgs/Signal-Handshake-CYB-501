# -*- coding: utf-8 -*-
from __future__ import annotations
from abc import ABC, abstractmethod
from Main.NetworkCommand import NetworkCommand
from typing import Callable 

class IServer(ABC):
    @abstractmethod
    async def Send(self, command : NetworkCommand) -> None:
        pass
    
    # callback is async
    def SetCallback(self, callback : Callable[NetworkCommand]): 
        self.callback = callback
        pass