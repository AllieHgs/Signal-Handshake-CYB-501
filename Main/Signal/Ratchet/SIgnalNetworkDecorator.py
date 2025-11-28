# Main/Signal/Ratchet/SignalNetworkDecorator.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from Interfaces.INetwork import INetwork, INetworkToken, CommandResult, Status
from Main.Signal.NetworkCommand import NetworkCommand
from Main.Signal.Ratchet.RatchetedToken import RatchetedToken
from Main.Signal.Ratchet.RatchetBuilder import RatchetBuilder

class SignalNetworkDecorator(INetwork):
    """
    Decorates an INetwork so that Connect() returns a ratcheted token
    (RatchetedToken) which encrypts/decrypts messages automatically.
    """

    def __init__(self, inner_network: INetwork, ratchet_builder: RatchetBuilder):
        super().__init__()
        self._inner = inner_network
        self._ratchet_builder = ratchet_builder

    async def _Command(self, commandRequest: NetworkCommand) -> CommandResult:
        # pass-through to actual network
        return await self._inner._Command(commandRequest)

    async def _Connect(self, userId, password) -> INetwork.ConnectResult:
        base = await self._inner._Connect(userId, password)

        result = INetwork.ConnectResult()
        result.status = base.status

        if base.status != Status.Success:
            return result

        # Build ratchet (builder may supply InitData if previously configured)
        ratchet = self._ratchet_builder.Build() if hasattr(self._ratchet_builder, "Build") else self._ratchet_builder.build()

        # Wrap low-level token
        wrapped = RatchetedToken(base.token, ratchet)
        result.token = wrapped
        return result

    # convenience pass-through overloads (so tests that call Register/Connect on decorator work)
    async def Register(self, userId, password):
        return await self._inner.Register(userId, password)

    async def Connect(self, userId, password):
        return await self._Connect(userId, password)

    async def CheckIdAvalibility(self, userId):
        return await self._inner.CheckIdAvalibility(userId)

    async def Get(self, userId, key):
        return await self._inner.Get(userId, key)

    async def Set(self, userId, key, value):
        return await self._inner.Set(userId, key, value)

    async def Disconnect(self, userId):
        return await self._inner.Disconnect(userId)
