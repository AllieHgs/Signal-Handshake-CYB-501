# -*- coding: utf-8 -*-
from __future__ import annotations
from Interfaces.INetwork import INetwork, INetworkToken
from Main.Signal.IRatchet import IRatchet
from Main.Signal.RatchetBuilder import RatchetBuilder

class SignalNetworkDecorator(INetwork):
    def __init__(self, network :INetwork, ratchetBuilder :RatchetBuilder):
        self._network = network
        self._ratchetBuilder = ratchetBuilder
        pass
    
    async def Connect(self, userId, password) -> INetwork.ConnectResult:
        result = await self._network.Connect(userId, password)
        result.token = SignalNetworkDecorator.Token(result.token, self, self._ratchetBuilder.Build())
        return result
        pass

    async def Register(self, userId, password) -> INetwork.RegisterResult:
        return await self._network.Register(userId, password)
        pass

    async def CheckIdAvalibility(self, userId) -> INetwork.CheckIdAvalibilityResult:
        return await self._network.CheckIdAvalibility(userId)
        pass
    
    
    class Token(INetworkToken):
        def __init__(self, token :INetworkToken, network :INetwork, ratchet :IRatchet):
            self._token = token
            self._network = network
            self._ratchet = ratchet
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
        
        
        
        
        
        
        