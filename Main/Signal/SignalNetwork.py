# -*- coding: utf-8 -*-
from __future__ import annotations
from Interfaces.INetwork import INetwork, INetworkToken, CommandResult
from Main.Signal.Ratchet.IRatchet import IRatchet
from Main.Signal.Ratchet.RatchetBuilder import RatchetBuilder
from Main.Signal.NetworkCommand import NetworkCommand

class SignalNetwork(INetwork):
    def __init__(self, network :INetwork, ratchetBuilder :RatchetBuilder):
        self._network = network
        self._ratchetBuilder = ratchetBuilder
        pass
    
    async def _Command(self, command :NetworkCommand) -> CommandResult:
        return await self._network.Command(command)
    
    async def _Connect(self, userId, password) -> INetwork.ConnectResult:
        result = INetwork.ConnectResult()
        cmd = await self._network.Connect(userId, password)
        result.status = cmd.status
        result.token = SignalNetwork.Token(result.token, self, self._ratchetBuilder.Build())
        return result
    
    
    class Token(INetworkToken):
        def __init__(self, token :INetworkToken, network :INetwork, ratchet :IRatchet):
            self._token = token
            self._network = network
            self._ratchet = ratchet
            pass

        
        async def _Send(self, command : NetworkCommand) -> CommandResult:
            return await self._token.Command(command)
        
        async def _Receive(self) -> CommandResult:
            return await self._token.Receive()
        
        
        
        
        
        
        