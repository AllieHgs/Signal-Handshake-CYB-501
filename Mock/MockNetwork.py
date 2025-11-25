# -*- coding: utf-8 -*-
from __future__ import annotations
from Interfaces.INetwork import INetwork, INetworkToken, Status, CommandResult
from Main.NetworkCommand import NetworkCommand


    
class MockNetwork(INetwork):
    def __init__(self):
        self.server = MockServer()
        pass
    
    async def _Command(self, command : NetworkCommand) -> CommandResult:
        result = CommandResult()
        result.reply =  await self.server.Send(command)
        return result
    
    async def _Connect(self, userId, password) -> INetwork.ConnectResult:
        result = INetwork.ConnectResult()
        reply = await self.server.Send(
            NetworkCommand("Connect").With("userId", userId).With("password", password))
        result.status = Status.Success if reply.Get("success") else Status.Fail
        if result.status == Status.Success:
            result.token = MockNetwork.Token(self, userId)
        return result
        

    class Token(INetworkToken):
        def __init__(self, network, userId, connected=True):
            self._receiveHandlers = list()
            self._network = network
            self.userId = userId
            self.connected = connected
        
        async def _Send(self, command :NetworkCommand) -> CommandResult:
            if command.Is("mail"):
                command.With("sender", self.userId)
            
            
            result = CommandResult()
            command.With("token", self.userId)
            command.With("userId",self.userId)
            cmd = await self._network.Command(command)
            result.status = Status.Success
            result.reply = cmd.reply
            return result
        
        async def _Receive(self, command :NetworkCommand) -> CommandResult:
            return command #noop
            
            
            
        """
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
        """
            
        
#  Mock Code on server, can only communicate through Send
class MockServer():
    def __init__(self):
        self._users = dict()

    # none of these are secure
    async def Send(self, command : NetworkCommand) -> NetworkCommand:
        if command.Is("Mail"):
            return self._Mail(command.Get("sender"), command.Get("receiver"), command.Get("message"))
        if command.Is("Connect"):
            return self._Connect(command.Get("userId"), command.Get("password"))
        if command.Is("Disconnect"):
            return self._Disconnect(command.Get("userId"))
        if command.Is("Register"):
            return self._Register(command.Get("userId"), command.Get("password"))
        if command.Is("CheckIdAvalibility"):
            return self._CheckIdAvalibility(command.Get("userId"))
        if command.Is("Get"):
            return self._Get(command.Get("userId"), command.Get("key"))
        if command.Is("Set"):
            return self._Get(command.Get("userId"), command.Get("key"), command.Get("value"))
        
        # default
        return CommandResult(Status.Fail, NetworkCommand("Reply").With("reason","No such command."))
    
    
    #This information would be stored on a server
    """
    class _UserData:
        def __init__(self, userId="",salt="", passwordHash="", inbox=None, connected=False):
            if inbox == None:
                inbox = list()
            self.userId = userId
            self.salt = salt
            self.passwordHash = passwordHash
            self.inbox = inbox
            self.connected = connected
            self.publicKeys = list()
            pass
    """
    def _Mail(self, sender, receiver, message) -> NetworkCommand:
        if not self._UserIdIsRegistered(receiver):
            return NetworkCommand("ACK").With("success", False)
        self._users[receiver]["inbox"].append({"sender": sender, "receiver":receiver, "message":message})
        return NetworkCommand("ACK").With("success", True)
    
    def _Connect(self, userId :str, password :str) -> NetworkCommand:
        if not self._UserIdIsRegistered(userId):
            return NetworkCommand("ACK").With("success", False)
        
        # Mock doesn't check passwords
        user = self._users[userId]
        user["connected"] = True
        return NetworkCommand("ACK").With("success", True).With("token",userId)
    
    def _Disconnect(self, userId :str) -> NetworkCommand:
        if not self._UserIdIsRegistered(userId):
            return NetworkCommand("ACK").With("success", False)
        
        # Mock doesn't check tokens
        self._users[userId]["connected"] = False
        return NetworkCommand("ACK").With("success", True)
        
    def _Register(self, userId, password) -> CommandResult:
        avaliable = not self._UserIdIsRegistered(userId)
        if not avaliable:
            return NetworkCommand("ACK").With("success", False).With("reason", "UserId is not avaliable")
        self._users[userId] = {
            "userId": userId,
            "inbox": list()
        }
        return NetworkCommand("ACK").With("success", True)

    def _CheckIdAvalibility(self, userId) -> NetworkCommand:
        avaliable = not self._UserIdIsRegistered(userId)
        return NetworkCommand("ACK", avaliable=avaliable)
    
    def _Get(self, userId, key) -> NetworkCommand:
        return NetworkCommand("ACK").With(key, self._users[userId].get(key,""))
    
    def _Set(self, userId, key, value) -> NetworkCommand: #SUPER not secure
        self._users[userId][key] = value
        return NetworkCommand("ACK")
    
    def _UserIdIsRegistered(self, userId :str):
        return userId in self._users
        
    
    
"""
    async def _Command(self, command : NetworkCommand) -> CommandResult:
        if command.Is("Register"):
            return await self._Register(command.Get("userId"), command.Get("password"))
        if command.Is("CheckIdAvalibility"):
            return await self._CheckIdAvalibility(command.Get("userId"))
        
        # default
        return CommandResult(Status.Fail, NetworkCommand("Reply").With("reason","No such command."))
    
    async def _Connect(self, userId, password) -> INetwork.ConnectResult:
        if not self._UserIdIsRegistered(userId):
            return INetwork.ConnectResult(Status.Fail)
        # Mock doesn't check passwords
        return INetwork.ConnectResult(Status.Success, MockNetwork.Token(self,userId))
    
"""