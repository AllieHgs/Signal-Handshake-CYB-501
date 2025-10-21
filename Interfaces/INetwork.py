from abc import ABC, abstractmethod

class INetwork(ABC):
    @abstractmethod
    def Send(self, mail):
        pass
    
    @abstractmethod
    def GetRecieveEvent(self, user) -> callable:
        pass
    
    @abstractmethod
    def CheckIdAvalibility(self, ID) -> bool:
        pass
    
    @abstractmethod
    def Register(self, user) -> bool():
        pass
    
    @abstractmethod
    def Connect(self, user) -> bool:
        pass
    
    @abstractmethod
    def Disconnect(self, user):
        pass