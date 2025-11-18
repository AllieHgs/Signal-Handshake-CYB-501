# -*- coding: utf-8 -*-
from __future__ import annotations
from Interfaces.INetwork import INetwork, INetworkToken
from Main.SignalNetwork.IRatchet import IRatchet

class SignalNetworkDecorator(INetwork):
    def __init__(self, network :INetwork):
        self._network = network
        pass
    
    async def Connect(self, userId, password) -> INetwork.ConnectResult:
        result = await self._network.Connect(userId, password)
        result.token = SignalNetworkDecorator.Token(result.token, self)
        return result
        pass

    async def Register(self, userId, password) -> INetwork.RegisterResult:
        return await self._network.Register(userId, password)
        pass

    async def CheckIdAvalibility(self, userId) -> INetwork.CheckIdAvalibilityResult:
        return await self._network.CheckIdAvalibility(userId)
        pass
    
    
    class Token(INetworkToken):
        def __init__(self, token :INetworkToken, network :INetwork):
            self._token = token
            self._network = network
            #self._ratchet = ratchet
            pass
        
        async def Send(self, mail) -> INetworkToken.SendResult:
            return await self._token.Send(mail)
            pass
        
        async def Receive(self) -> INetworkToken.ReceiveResult:
            return await self._token.Receive()
            pass
        
        async def ClearInbox(self) -> INetworkToken.ClearInboxResult:
            return await self._token.ClearInbox()
            pass
        
        async def Disconnect(self) -> INetworkToken.DisconnectResult:
            return await self._token.Disconnect()
            pass
        
        async def Command(self, command :str) -> INetworkToken.CommandResult:
            return await self._token.Command(command)
            pass
        
        def ReceiveAddListener(self, callback :callable):
            self._token.ReceiveAddListener(callback)
            pass
        def ReceiveRemoveListener(self, callback :callable):
            self._token.ReceiveRemoveListener(callback)
            pass
        
        
        
        
        
        
        