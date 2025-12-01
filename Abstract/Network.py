from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from Main.Mail import Mail as MailType
from Main.NetworkCommand import NetworkCommand, Status
from typing import Callable, Any
from types import SimpleNamespace
import inspect
from uuid import uuid4
from enum import Flag, auto
import asyncio
    
"""Send/Receive Handlers
can either be 
async def handler(self,command) -> CommandResult
indicating that it handles sending/recieveing
or 
[async] def handler(self,command) -> bool | None
indicating that it only modifies command

Which is used is determined by the Send/Receive subclass functions
"""
class ListenFor(Flag):
    NONE = 0
    Message = auto()
    Command = auto() # Including Messages
    Reply = auto()
    All = Message | Command | Reply
    
class Network(ABC):
    
    #Virtual Methods
    async def Send(self, command :NetworkCommand) -> NetworkCommand:
        if command.token is None: 
            await self.CreateToken().Ephemeral().Send(command)
            return command
        if hasattr(self, "network"): await self.network.Send(command)
        return command

    async def Receive(self, command :NetworkCommand) -> NetworkCommand:
        if hasattr(self, "network"): await self.network.Receive(command)
        return command
    
    async def OnSend(self, command :NetworkCommand) -> NetworkCommand:
        if command is None: return None
        op = command.Operation().lower()
        
        # pre handler
        handler = self.__class__._sendPreTable.get(op)
        if handler is not None: await handler(self, command)

        if hasattr(self, "network"): await self.network.OnSend(command)
        
        # post (standard) handler
        handler = self.__class__._sendTable.get(op)
        if handler is not None: await handler(self, command)
        
        return command
    
    async def OnReceive(self, command :NetworkCommand) -> NetworkCommand:
        if command is None: return None
        op = command.Operation().lower()
        
        #pre
        handler = handler = self.__class__._receivePreTable.get(op)
        if handler is not None: await handler(self, command)
        
        if hasattr(self, "network"): await self.network.OnReceive(command)
        
        #post
        handler = handler = self.__class__._receiveTable.get(op)
        if handler is not None: await handler(self, command)
        
        return command
    
    async def OnReply(self, command :NetworkCommand) -> NetworkCommand:
        if command is None : return None
        op = command.Operation().lower()
        #pre
        handler = handler = self.__class__._replyPreTable.get(op)
        if handler is not None: await handler(self, command)
        
        if hasattr(self, "network"): await self.network.OnReply(command)
        
        #post
        handler = handler = self.__class__._replyTable.get(op)
        if handler is not None: await handler(self, command)
        
        return command
    def CreateToken(self, **kwargs):
        return self.Token(self, **kwargs)
    #End Virtual Methods
    
    
    _sendTable = {}
    _sendPreTable = {}
    _receiveTable = {}
    _receivePreTable = {}
    _replyTable = {}
    _replyPreTable = {}
    def __init_subclass__(cls):
        super().__init_subclass__()
        cls._sendTable = {}
        cls._sendPreTable = {}
        cls._receiveTable = {}
        cls._receivePreTable = {}
        cls._replyTable = {}
        cls._replyPreTable = {}
        for name, val in cls.__dict__.items():
            if callable(val) and hasattr(val, "_network_onSend"):
                op, pre = val._network_onSend
                if pre:
                    cls._sendPreTable[op] = val
                else:
                    cls._sendTable[op] = val

            if callable(val) and hasattr(val, "_network_onReceive"):
                op, pre = val._network_onReceive
                if pre:
                    cls._receivePreTable[op] = val
                else:
                    cls._receiveTable[op] = val

            if callable(val) and hasattr(val, "_network_onReply"):
                op, pre = val._network_onReply
                if pre:
                    cls._replyPreTable[op] = val
                else:
                    cls._replyTable[op] = val
    
    @classmethod
    def sendhandler(cls, operation, pre=False):
        def decorator(func):
            func._network_onSend = (operation.lower(), pre)
            return func
        return decorator
    @classmethod
    def receivehandler(cls, operation, pre=False):
        def decorator(func):
            func._network_onReceive = (operation.lower(), pre)
            return func
        return decorator
    @classmethod
    def replyhandler(cls, operation, pre=False):
        def decorator(func):
            func._network_onReply = (operation.lower(), pre)
            return func
        return decorator
    
    
    async def Connect(self, userId, password) -> NetworkCommand:
        return await self.Send(NetworkCommand("Connect", userId=userId, password=password))
    async def Register(self, userId, password) -> NetworkCommand:
        return await self.Send(NetworkCommand("Register", userId=userId, password=password))
    async def CheckIdAvailability(self, userId) -> NetworkCommand:
        return await self.Send(NetworkCommand("CheckIdAvailability", userId=userId))
    
    def ReceiveAddListener(self, callback :Callable[[NetworkCommand], None]):
        self._receiveHandlers.append(callback)
        pass
    def ReceiveRemoveListener(self, callback :Callable[[NetworkCommand], None]):
        self._receiveHandlers = [i for i in self._receiveHandlers if i != callback]
        pass
    def InvokeReceive(self, commandResult=None):
        for callback in self._receiveHandlers:
            params = inspect.signature(callback).parameters
            args = len(params)
    
            if args == 1:
                callback(self)
            elif args == 2:
                callback(self, commandResult)
            elif args == 3:
                callback(self, self.network, commandResult)
            else:
                raise TypeError("Unsupported callback signature")
                
    
    #######################################################
    # Token
    #######################################################
    class Token():
        def __init__(self, network :Network, **kwargs):
            self.network = network
            self.kwargs = kwargs 
            self.data = {} # Data sent with command
            self._listeners = list()
            self.connected = False
            self.ephemeral = False
            pass
        
        async def Send(self, command :NetworkCommand) -> NetworkCommand:
            command.WithToken(self)
            await self.network.OnSend(command)
            await self.network.Send(command)
            await self.network.OnReply(command)
            self.RaiseListeners(command, ListenFor.Reply)
            command.Complete()
            return command.Complete()
        
        async def Receive(self, command :NetworkCommand) -> NetworkCommand:
            command.WithToken(self)
            await self.network.OnReceive(command)
            
            # Raise Receive Event
            self.RaiseListeners(command, 
                ListenFor.Command | (ListenFor.Message if command.Is("mail") else ListenFor.NONE))
            
            # Fire and forget reply 
            async def task_reply():
                reply = NetworkCommand(command.Operation()).ReplyTo(command)
                if command.IsFail(): reply.RST() 
                else: reply.ACK()
                await self.network.OnSend(reply)
                await self.network.Send(reply)
            asyncio.create_task(task_reply())
            
            return command.Complete()
        
        def With(self, key :str, value) -> Network.Token:
            self.kwargs[key] = value
            return self
        def WithData(self, key, value) -> Network.Token:
            self.data[key] = value
        def Data(self, data) -> Network.Token:
            self.data = dict(data)
            return self
        def CopyData(self, token) -> Network.Token:
            if token is not None: return self.Data(token.data)
            return self
        
        _sentinel = object()
        def Get(self, key :str, default :Any =_sentinel, setDefault :bool = False) -> Any:
            return self._Get(key, default, setDefault, self.kwargs)
        def GetParam(self, key :str, default :Any =_sentinel, setDefault :bool = False) -> Any:
            return self._Get(key, default, setDefault, self.data)
        def _Get(self, key, default, setDefault, lut):
            if default is self._sentinel:
                return lut[key]
            else:
                if setDefault and key not in lut:
                    lut[key] = default
                    return default
                return lut.get(key, default)
            pass
        
        def Ephemeral(self) -> Network.Token:
            self.ephemeral = True
            return self
        def IsEphemeral(self) -> bool:
            return self.ephemeral
        
        async def Mail(self, mail : MailType) -> NetworkCommand:
            return await self.Send(NetworkCommand("Mail", sender=mail.sender, receiver=mail.receiver, message=mail.message))
        async def CheckMail(self) -> NetworkCommand:
            command = NetworkCommand("Get", userId=self.Get("userId",""), key="inbox")
            
            userId = self.Get("userId", None)
            if userId is None: return command.Fail().With("reason", "Not logged in")
            
            await self.Send(command)
            if command.reply is not None: command.inbox = command.reply.Get("inbox", [])
            return command
        async def Disconnect(self) -> NetworkCommand:
            return await self.Send(NetworkCommand("Disconnect", userId = self.Get("userId", "")))
        async def ClearInbox(self) -> NetworkCommand:
            return await self.Send(NetworkCommand("ClearInbox", userId = self.Get("userId", "")))
        
        
        def AddListener(self, callback :Callable[NetworkCommand],
                        listenFor :ListenFor = ListenFor.Message):
            self._receiveListeners.append(
                SimpleNamespace(callback=callback), listenFor=listenFor)
            pass
        def RemoveListener(self, callback :Callable[[Network.Token], None]):
            self._listeners = [i for i in self._listeners if i.callback != callback]
            pass
        def RaiseListeners(self, commandResult=None, listenFlags :ListenFor=ListenFor.All):
            for listener in self._listeners:
                # if listener is not listening to any of lisenFlags
                if not (listener.listenFor & listenFlags):
                    continue
                
                callback = listener.callback
                params = inspect.signature(callback).parameters
                args = len(params)
        
                if args == 1:
                    callback(self)
                elif args == 2:
                    callback(self, commandResult)
                elif args == 3:
                    callback(self, self.network, commandResult)
                else: 
                    raise TypeError("Unsupported callback signature")
            pass
        
        