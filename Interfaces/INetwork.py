# -*- coding: utf-8 -*-
from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from Main.Mail import Mail
from Main.Signal.NetworkCommand import NetworkCommand


# ============================================================
# STATUS ENUM — stable and correct
# ============================================================

class Status(Enum):
    Pending = 0
    Fail = 1
    Success = 2


# ============================================================
# COMMAND RESULT
# ============================================================

class CommandResult:
    def __init__(self, status: Status = Status.Pending, reply: NetworkCommand = None):
        self.status = status
        self.reply = reply


# ============================================================
# INetwork (abstract)
# ============================================================

class INetwork(ABC):

    @abstractmethod
    async def _Command(self, commandRequest: NetworkCommand) -> CommandResult:
        pass

    @abstractmethod
    async def _Connect(self, userId, password) -> "INetwork.ConnectResult":
        pass

    async def Command(self, commandRequest: NetworkCommand) -> CommandResult:
        return await self._Command(commandRequest)

    async def Connect(self, userId, password) -> "INetwork.ConnectResult":
        return await self._Connect(userId, password)

    async def Register(self, userId, password) -> CommandResult:
        return await self.Command(NetworkCommand("Register", userId=userId, password=password))

    async def CheckIdAvalibility(self, userId) -> CommandResult:
        return await self.Command(NetworkCommand("CheckIdAvalibility", userId=userId))

    class ConnectResult:
        def __init__(self, status: Status = Status.Pending, token: "INetworkToken" = None):
            self.status = status
            self.token = token


# ============================================================
# INetworkToken (abstract)
# ============================================================

class INetworkToken(ABC):

    # ------------------------------------------------------------
    # REQUIRED ABSTRACT METHODS
    # ------------------------------------------------------------

    @abstractmethod
    async def _Send(self, command: NetworkCommand) -> CommandResult:
        """Send a command (implemented by concrete token)"""
        pass

    @abstractmethod
    async def _Receive(self) -> list[NetworkCommand]:
        """Receive pending commands (implemented by concrete token)"""
        pass

    # ------------------------------------------------------------
    # WRAPPERS AROUND ABSTRACT METHODS
    # ------------------------------------------------------------

    async def Send(self, command: NetworkCommand) -> CommandResult:
        result = await self._Send(command)
        return result

    async def Receive(self) -> list[NetworkCommand]:
        return await self._Receive()

    # ------------------------------------------------------------
    # MAIL FUNCTIONS (unchanged, still work)
    # ------------------------------------------------------------

    async def Mail(self, mail: Mail) -> "INetworkToken.MailResult":
        result = INetworkToken.MailResult(status=Status.Pending)
        cmd = await self.Send(NetworkCommand("mail",
                                             sender=mail.sender,
                                             receiver=mail.receiver,
                                             message=mail.message))
        result.status = cmd.status
        return result

    async def CheckMail(self) -> "INetworkToken.CheckMailResult":
        result = INetworkToken.CheckMailResult()
        cmd = await self.Send(NetworkCommand("Get", userId=self.userId, key="inbox"))
        result.status = cmd.status
        if result.status == Status.Success:
            result.inbox = cmd.reply.Get("inbox")
        return result

    async def Disconnect(self):
        return await self.Send(NetworkCommand("Disconnect"))

    async def ClearInbox(self):
        return await self.Send(NetworkCommand("ClearInbox"))

    # ------------------------------------------------------------
    # RECEIVE LISTENERS
    # ------------------------------------------------------------

    def __init__(self):
        self._receiveHandlers = set()
        self.userId = None

    def ReceiveAddListener(self, callback: callable):
        self._receiveHandlers.add(callback)

    def ReceiveRemoveListener(self, callback: callable):
        self._receiveHandlers.remove(callback)

    def InvokeReceive(self):
        for callback in self._receiveHandlers:
            callback(self)

    # ------------------------------------------------------------
    # INNER RESULT TYPES
    # ------------------------------------------------------------

    class MailResult:
        def __init__(self, status: Status = Status.Pending):
            self.status = status

    class CheckMailResult:
        def __init__(self, status: Status = Status.Pending, inbox=None):
            self.status = status
            self.inbox = inbox if inbox is not None else []
