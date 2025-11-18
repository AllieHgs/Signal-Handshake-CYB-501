from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from Main.Mail import Mail

class Status(Enum):
    Pending = 0
    Fail = 1
    Success = 2
    
class INetwork(ABC):
    @abstractmethod
    async def Connect(self, userId, password) -> INetwork.ConnectResult:
        pass
    
    @abstractmethod
    async def Register(self, userId, password) -> INetwork.RegisterResult:
        pass
    
    @abstractmethod
    async def CheckIdAvalibility(self, userId) -> INetwork.CheckIdAvalibilityResult:
        pass
    
    
    class ConnectResult:
        def __init__(self, status :Status, token :INetworkToken = None):
            self.status = status
            self.token = token
            
    class RegisterResult:
        def __init__(self, status :Status):
            self.status = status

    class CheckIdAvalibilityResult:
        def __init__(self, status :Status, available :bool = False):
            self.status = status
            self.available = available
    
    
    
class INetworkToken(ABC):
    
    @abstractmethod
    async def Send(self, mail) -> INetworkToken.SendResult:
        pass
    
    @abstractmethod
    async def Receive(self) -> INetworkToken.ReceiveResult:
        pass
    
    @abstractmethod
    async def ClearInbox(self) -> INetworkToken.ClearInboxResult:
        pass
    
    @abstractmethod
    async def Disconnect(self) -> INetworkToken.DisconnectResult:
        pass
    
    @abstractmethod
    async def Command(self, command :str) -> INetworkToken.CommandResult:
        pass
    
    @abstractmethod
    def ReceiveAddListener(self, callback :callable):
        pass
    @abstractmethod
    def ReceiveRemoveListener(self, callback :callable):
        pass
   
    
    class SendResult:
        def __init__ (self, status :Status):
            self.status = status
            
    class ReceiveResult:
        def __init__(self, status :Status, inbox :list[Mail] = list()):
            self.status = status
            self.inbox = inbox
            
    class ClearInboxResult:
        def __init__(self, status :Status):
            self.status = status
    
    class DisconnectResult:
        def __init__(self, status :Status):
            self.status = status
            
    class CommandResult:
        def __init__(self, status :Status):
            self.status = status
            
            
            
"""
class MockNetwork(INetwork):
    def __init__(self):
        pass
    
    async def Connect(self, user, password) -> INetwork.ConnectResult:
        return 
        pass

    async def Register(self, user, password) -> INetwork.RegisterResult:
        pass

    async def CheckIdAvalibility(self, ID) -> INetwork.CheckIdAvalibilityResult:
        pass
    
    
    class MockNetworkToken(INetworkToken):
        
        
        def __init__(self):
            pass
        
        async def Send(self, mail) -> INetworkToken.SendResult:
            pass
        
        async def Receive(self) -> INetworkToken.ReceiveResult:
            pass
        
        async def ClearInbox(self) -> INetworkToken.ClearInboxResult:
            pass
        
        async def Disconnect(self) -> INetworkToken.DisconnectResult:
            pass
        
        async def Command(self, command :str) -> INetworkToken.CommandResult:
            pass
        
        def ReceiveAddListener(self, callback :callable):
            pass
        def ReceiveRemoveListener(self, callback :callable):
            pass
"""