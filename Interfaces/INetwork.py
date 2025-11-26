from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from Main.Mail import Mail
from Main.NetworkCommand import NetworkCommand

class Status(Enum):
    Pending = 0
    Fail = 1
    Success = 2

class CommandResult:
    def __init__(self, status :Status = Status.Pending, reply :NetworkCommand = None):
        self.status = status
        self.reply = reply
        pass
    
class INetwork(ABC):
    @abstractmethod #TODO, Send not _Command
    async def _Command(self, commandRequest :NetworkCommand) -> CommandResult:
        pass
    
    @abstractmethod #TODO command based
    async def _Connect(self, userId, password) -> ConnectResult():
        pass
    
    
    async def Command(self, commandRequest :NetworkCommand) -> CommandResult:
        return await self._Command(commandRequest)
    async def Connect(self, userId, password) -> ConnectResult():
        return await self._Connect(userId, password)
    
    
    async def Register(self, userId, password) -> CommandResult:
        return await self.Command(NetworkCommand("Register", userId=userId, password=password))
    async def CheckIdAvalibility(self, userId) -> INetwork.CommandResult:
        return await self.Command(NetworkCommand("CheckIdAvalibility", userId=userId))
    
    class ConnectResult:
        def __init__(self, status :Status = Status.Pending, token :INetworkToken = None):
            self.status = status
            self.token = token
            
    
class INetworkToken(ABC):
    
    @abstractmethod
    async def _Send(self, command :NetworkCommand) -> CommandResult:
        pass
    @abstractmethod
    async def _Receive(self, command :NetworkCommand) -> CommandResult:
        pass
    
    
    async def Send(self, command :NetworkCommand) -> CommandResult:
        result = CommandResult()
        cmd = await self._Send(command)
        # Copy to result to maintain result's pointer
        result.status = cmd.status 
        result.reply = cmd.reply
        return result
    
    async def Receive(self, command :NetworkCommand) -> CommandResult:
        return await self._Recieve(command)
    
    
    async def Mail(self, mail :Mail) -> INetworkToken.MailResult:
        result = INetworkToken.MailResult(status=Status.Pending)
        #cmd = await self.Send(NetworkCommand("mail", **mail))
        cmd = await self.Send(NetworkCommand("mail", 
                                             sender=mail.sender, 
                                             receiver=mail.receiver, 
                                             message=mail.message))
        result.status = cmd.status
        return result
    
    async def CheckMail(self) -> INetworkToken.CheckMailResult:
        result = INetworkToken.CheckMailResult()
        cmd = await self.Send(NetworkCommand("Get", userId=self.userId, key="inbox"))
        result.status = cmd.status
        if result.status == Status.Success:
            result.inbox = cmd.reply.Get("inbox")
        return result
        
    
    
    
    
    async def Disconnect(self) -> INetworkToken.DisconnectResult:
        return await self.Send(NetworkCommand("Disconnect"))
    async def ClearInbox(self) -> INetworkToken.ClearInboxResult:
        return await self.Send(NetworkCommand("ClearInbox"))
    
    
    def ReceiveAddListener(self, callback :callable):
        self._receiveHandlers.add(callback)
        pass
    def ReceiveRemoveListener(self, callback :callable):
        self._receiveHandlers.remove(callback)
        pass
    def InvokeReceive(self):
        for callback in self._receiveHandlers:
            callback(self)
    
    
    class MailResult:
        def __init__ (self, status :Status = Status.Pending):
            self.status = status
            
    class CheckMailResult:
        def __init__(self, status :Status = Status.Pending, inbox :list[Mail] = list()):
            self.status = status
            self.inbox = inbox