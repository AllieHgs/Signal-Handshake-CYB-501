# -*- coding: utf-8 -*-
from __future__ import annotations
from abc import ABC, abstractmethod

class IMail(ABC):
    @abstractmethod
    def Sender(self) -> str:
        pass
    @abstractmethod
    def Reciever(self) -> str:
        pass
    @abstractmethod
    def Message(self) -> str:
        pass