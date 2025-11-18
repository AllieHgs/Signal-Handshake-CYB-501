# -*- coding: utf-8 -*-
from __future__ import annotations
from Interfaces.INetwork import INetwork, INetworkToken, Status

class MockNetwork(INetwork):
    def __init__(self):
        self._users = dict()
        pass
    
    async def Connect(self, userId, password) -> INetwork.ConnectResult:
        if userId not in self._users:
            return INetwork.ConnectResult(Status.Fail)
        return INetwork.ConnectResult(Status.Success, MockNetwork.Token(self,userId))
        pass

    async def Register(self, userId, password) -> INetwork.RegisterResult:
        avalibile = await self.CheckIdAvalibility(userId)
        if not avalibile:
            return INetwork.RegisterResult(Status.Fail)
        self._users[userId] = MockNetwork._UserData()
        return INetwork.RegisterResult(Status.Success)

    async def CheckIdAvalibility(self, userId) -> INetwork.CheckIdAvalibilityResult:
        return INetwork.CheckIdAvalibilityResult(Status.Success, userId in self._users)
    
    #This information would be stored on a server
    class _UserData:
        def __init__(self, salt="", passwordHash="", inbox=None, connected=False):
            if inbox == None:
                inbox = list()
            self.salt = salt
            self.passwordHash = passwordHash
            self.inbox = inbox
            self.connected = connected
            pass
        
    class Token(INetworkToken):
        def __init__(self, network, userId, connected=True):
            self._receiveHandlers = list()
            self._network = network
            self.userId = userId
            self.connected = connected
        
        async def Send(self, mail) -> INetworkToken.SendResult:
            if not self.connected or mail.reciever not in self._network._users:
                return INetworkToken.SendResult(Status.Fail)
            
            print(f"Mock sending Message\n{mail}\n");
            self._network._users[mail.reciever].inbox.append(mail)
            return INetworkToken.SendResult(Status.Success)
        
        async def Receive(self) -> INetworkToken.ReceiveResult:
            if not self.connected or self.userId not in self._network._users:
                return INetworkToken.ReceiveResult(Status.Fail)
            
            #Note: This is unsecure, use a token in a real implementation
            inbox = self._network._users[self.userId].inbox
            
            return INetworkToken.ReceiveResult(Status.Success, inbox)
        
        async def ClearInbox(self) -> INetworkToken.ClearInboxResult:
            if not self.connected or self.userId not in self._network._users:
                return INetworkToken.ClearInboxResult(Status.Fail)
            
            #Note: This is unsecure, use a token in a real implementation
            self._network._users[self.userId].clear()
            
            return INetworkToken.ClearInboxResult(Status.Success)
            
            pass
        
        async def Disconnect(self) -> INetworkToken.DisconnectResult:
            if not self.connected or self.userId not in self._network._users:
                return INetworkToken.ClearInboxResult(Status.Fail)
            
            self.connected = False
            
            #Note: This is unsecure, use a token in a real implementation
            self._network._users[self.userId]
            
            return INetworkToken.ClearInboxResult(Status.Success)
        
        
        async def Command(self, command :str) -> INetworkToken.CommandResult:
            if not self.connected:
                return INetworkToken.CommandResult(Status.Fail)
            
            print(f"Mock Execute command: {command}")
            return INetworkToken.CommandResult(Status.Success)
            
            
        def ReceiveAddListener(self, callback :callable):
            self._receiveHandlers.add(callback)
            pass
        def ReceiveRemoveListener(self, callback :callable):
            self._receiveHandlers.remove(callback)
            pass
        
        
        
    
    
