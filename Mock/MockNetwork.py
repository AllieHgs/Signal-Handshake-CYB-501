# -*- coding: utf-8 -*-
from __future__ import annotations

from Interfaces.INetwork import (
    INetwork,
    INetworkToken,
    Status,
    CommandResult
)
from Main.Signal.NetworkCommand import NetworkCommand


class MockNetwork(INetwork):
    """
    Mock network simulating a server and connection protocol.
    """

    def __init__(self):
        self.server = MockServer()

    # ---------------------------------------------------------
    # NETWORK-LEVEL API
    # ---------------------------------------------------------
    async def _Command(self, command: NetworkCommand) -> CommandResult:
        reply = await self.server.Send(command)
        return CommandResult(Status.Success, reply)

    async def _Connect(self, userId, password) -> INetwork.ConnectResult:
        reply = await self.server.Send(
            NetworkCommand("Connect")
            .With("userId", userId)
            .With("password", password)
        )

        result = INetwork.ConnectResult()
        if reply.Get("success"):
            result.status = Status.Success
            result.token = MockNetwork.Token(self, userId)
        else:
            result.status = Status.Fail

        return result

    # ---------------------------------------------------------
    # TOKEN (client connection)
    # ---------------------------------------------------------
    class Token(INetworkToken):
        """
        Represents a connected user's session.
        """

        def __init__(self, network, userId, connected=True):
            self._network = network
            self.userId = userId
            self.connected = connected
            self._receiveHandlers = set()

        # -----------------------------------------
        # LOW LEVEL SEND
        # -----------------------------------------
        async def _Send(self, command: NetworkCommand) -> CommandResult:
            # Auto-fill common fields
            command.With("token", self.userId)
            command.With("userId", self.userId)

            # Special handling: mail command
            if command.Is("mail"):
                command.With("sender", self.userId)

            reply = await self._network.Command(command)
            result = CommandResult(Status.Success, reply.reply)
            return result

        # -----------------------------------------
        # LOW LEVEL RECEIVE (Mock just returns the input)
        # -----------------------------------------
        async def _Receive(self, command: NetworkCommand) -> CommandResult:
            return CommandResult(Status.Success, command)


# ======================================================================
# MOCK SERVER (simulates database + endpoints)
# ======================================================================

class MockServer:
    def __init__(self):
        self._users = {}  # userId → dict

    async def Send(self, command: NetworkCommand) -> NetworkCommand:
        """
        Every command the client sends is routed here.
        """

        if command.Is("Mail"):
            return self._Mail(
                command.Get("sender"),
                command.Get("receiver"),
                command.Get("message")
            )

        if command.Is("Connect"):
            return self._Connect(
                command.Get("userId"),
                command.Get("password")
            )

        if command.Is("Disconnect"):
            return self._Disconnect(command.Get("userId"))

        if command.Is("Register"):
            return self._Register(
                command.Get("userId"),
                command.Get("password")
            )

        if command.Is("CheckIdAvalibility"):
            return self._CheckIdAvalibility(
                command.Get("userId")
            )

        if command.Is("Get"):
            return self._Get(
                command.Get("userId"),
                command.Get("key")
            )

        if command.Is("Set"):
            return self._Set(
                command.Get("userId"),
                command.Get("key"),
                command.Get("value")
            )

        # Default: unknown command
        return NetworkCommand("ACK").With("success", False).With("reason", "Unknown command")

    # ==================================================================
    # SERVER OPERATIONS
    # ==================================================================

    def _Mail(self, sender, receiver, message):
        if receiver not in self._users:
            return NetworkCommand("ACK").With("success", False)

        self._users[receiver]["inbox"].append({
            "sender": sender,
            "receiver": receiver,
            "message": message
        })
        return NetworkCommand("ACK").With("success", True)

    def _Connect(self, userId, password):
        if userId not in self._users:
            return NetworkCommand("ACK").With("success", False)

        self._users[userId]["connected"] = True
        return NetworkCommand("ACK").With("success", True).With("token", userId)

    def _Disconnect(self, userId):
        if userId not in self._users:
            return NetworkCommand("ACK").With("success", False)

        self._users[userId]["connected"] = False
        return NetworkCommand("ACK").With("success", True)

    def _Register(self, userId, password):
        if userId in self._users:
            return NetworkCommand("ACK").With("success", False).With("reason", "Taken")

        self._users[userId] = {
            "userId": userId,
            "inbox": [],
            "connected": False
        }
        return NetworkCommand("ACK").With("success", True)

    def _CheckIdAvalibility(self, userId):
        available = userId not in self._users
        return NetworkCommand("ACK").With("available", available)

    def _Get(self, userId, key):
        return NetworkCommand("ACK").With(key, self._users[userId].get(key, ""))

    def _Set(self, userId, key, value):
        self._users[userId][key] = value
        return NetworkCommand("ACK").With("success", True)
