# -*- coding: utf-8 -*-
from __future__ import annotations
from Abstract.Network import Network, ListenFor
from Abstract.IServer import IServer
from Main.NetworkCommand import NetworkCommand, Status
from uuid import uuid4
from types import SimpleNamespace
import asyncio
    
class NetworkLeaf(Network):
    
    def __init__(self, server :IServer):
        self.server = server
        server.SetCallback(self.Receive)
        self._pending = dict()
        self.defaultTimeout = 5
        #self.tokens :dict[str, Network.Token]= []
        pass
    
    async def Send(self, command :NetworkCommand) -> NetworkCommand:
        await super().Send(command)
        if command.reply is not None: return command
        
        futureReply = asyncio.get_event_loop().create_future()
        self._pending[command.GetUUID()] = futureReply
        
        await self.server.Send(command)
        
        reply = None
        try: # Wait for reply
            reply = await asyncio.wait_for(futureReply, 
                timeout=command.Get("timeout", self.defaultTimeout))
        except asyncio.TimeoutError: 
            # clean up pending future
            self._pending.pop(command.GetUUID(), None)
            futureReply.cancel()
            return command.Fail()
        
        if reply is None: return command.Fail()
        
        reply.ReplyTo(command).WithToken(command.token)
        command.WithReply(reply)
        return command

    
    async def Receive(self, command :NetworkCommand) -> NetworkCommand:
        #if command.IsComplete(): return
        await super().Receive(command)
        
        # Check if this is a reply to a pending Send
        cmdId = command.GetReplyUUID() or command.GetUUID()
        if cmdId in self._pending:
            pending = self._pending.pop(cmdId)
            if not pending.done(): pending.set_result(command)
            return command
        
        #Locate Token
        """
        tkn = command.Get("token", None)
        if tkn and tkn in self.tokens:
            self.tokens[tkn].Receive(command)
        """
        
        # Incomming commands
        self.RaiseListeners(command,ListenFor.Command)
        return command
    
    @Network.sendhandler("Mail")
    async def s_mail(self, command):
        command.With("sender", command.token.Get("userId", ""))
        return command
    
    @Network.receivehandler("Mail")
    async def r_mail(self, command):
        pass
    
    @Network.sendhandler("Disconnect")
    async def s_disconnect(self, command):
        command.token.connected = False
        return command
    
    @Network.replyhandler("Connect")
    async def p_connect(self, command):
        print(vars(command.token))
        tkn = command.token
        command.token = self.CreateToken(**command.Get("token", {}))
        command.token.connected = True
        command.token.With("userId", command.Get("userId", ""))
        return command
        
    def userId(self):
        return self.kwargs.get("userId", "")

    def token(self):
        return self.kwargs.get("token")
        

        

        
    