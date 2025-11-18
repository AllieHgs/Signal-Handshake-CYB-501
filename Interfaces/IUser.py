# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod

# Obsolete
class IUser(ABC):
    network = None
    ID = None
    password = None
    connected = False
    
    def __init__(self, ID, password, network):
        self.ID = ID
        self.password = password
        self.network = network
    
    def Register(self) -> bool:
        return self.network.Register(self)
    def Connect(self) -> bool: #returns true if successful
        if self.network.Connect(self):
            self.connected = True
        pass
    
    def Disconnect(self): #void
        self.network.Disconnect(self)
        self.connected = False;
        pass
    
    @abstractmethod
    def GetMessages(self): #Messages Object
        pass
    
    @abstractmethod
    def Send(self, mail): #void
        self.network.Send(self, mail)
        pass
    
    @abstractmethod
    def Recieve(self, mail): #void
        pass