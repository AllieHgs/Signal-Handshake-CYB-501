# -*- coding: utf-8 -*-
from __future__ import annotations
from Main.NetworkCommand import NetworkCommand
from Abstract.IServer import IServer
import asyncio
from uuid import uuid4

class MockServer(IServer):
    def __init__(self):
        self._users = dict()
        self.callback = self.Ignore
        self.log = False

    # none of these are secure
    async def Send(self, command : NetworkCommand):
        if(self.log):
            print(f"Server Received: {command}")
        reply = None
        if command.Is("Mail"):
            reply = self._Mail(command.Get("sender", ""), command.Get("receiver", ""), command.Get("message", ""))
        elif command.Is("Connect"):
            reply = self._Connect(command.Get("userId", ""), command.Get("password", ""))
        elif command.Is("Disconnect"):
            reply = self._Disconnect(command.Get("userId", ""))
        elif command.Is("Register"):
            reply = self._Register(command.Get("userId", ""), command.Get("password", ""))
        elif command.Is("CheckIdAvalibility"):
            reply = self._CheckIdAvailability(command.Get("userId", ""))
        elif command.Is("Get"):
            reply = self._Get(command.Get("userId", ""), command.Get("key", ""))
        elif command.Is("Set"):
            reply = self._Get(command.Get("userId", ""), command.Get("key", ""), command.Get("value", ""))
        elif command.Is("GetPrekeyBundle"):
            reply = self.GetPrekeyBundle(command)
        elif command.Is("PublishKeyBundle"):
            reply = self.PublishKeyBundle(command)
            
        # default
        else:
            reply = NetworkCommand(command.Operation()).RST().With("reason","Invaild request.")
        
        reply.ReplyTo(command)
        
        if(self.log):
            print(f"Server Replied: {reply}", end="\n\n")
        asyncio.create_task(self.callback(reply))
    

    def _Mail(self, sender, receiver, message) -> NetworkCommand:
        if not self._UserIdIsRegistered(receiver):
            return NetworkCommand("mail").RST().With("reason", "Invalid request")
        self._users[receiver]["inbox"].append({"sender": sender, "receiver":receiver, "message":message})
        return NetworkCommand("mail").ACK()
    
    def _Connect(self, userId :str, password :str) -> NetworkCommand:
        if not self._UserIdIsRegistered(userId):
            return NetworkCommand("connect").RST().With("reason", "Username and/or password is incorrect")
        
        # Mock doesn't check passwords
        user = self._users[userId]
        user["connected"] = True
        
        #Create token
        token = {
            "id":str(uuid4())
        }
        return NetworkCommand("connect").ACK().With("token",token)
    
    def _Disconnect(self, userId :str) -> NetworkCommand:
        if not self._UserIdIsRegistered(userId):
            return NetworkCommand("disconnect").RST().With("reason", "Invalid Request")
        
        # Mock doesn't check tokens
        self._users[userId]["connected"] = False
        return NetworkCommand("disconnect").ACK()
        
    def _Register(self, userId, password) -> NetworkCommand:
        avaliable = not self._UserIdIsRegistered(userId)
        if not avaliable:
            return NetworkCommand("register").RST().With("reason", "UserId is not avaliable")
        # This information would be stored on a server
        self._users[userId] = {
            "userId": userId,
            "connected": False,
            "inbox": list(),
            "salt": "",
            "passwordHash": "",
            "publicKeys": list(),
            "IK":"",
            "SPK":"",
            "SPK_sig":"",
            "OPKs": list(),
        }
        return NetworkCommand("register").ACK()


    def _CheckIdAvailability(self, userId) -> NetworkCommand:
        avaliable = not self._UserIdIsRegistered(userId)
        return NetworkCommand("CheckIdAvailability", avaliable=avaliable).ACK()
    
    def _Get(self, userId, key) -> NetworkCommand:
        if not self._UserIdIsRegistered(userId):
            return NetworkCommand("get").RST()
        
        return NetworkCommand("get").ACK().With(key, self._users[userId].get(key,""))

    def _Set(self, userId, key, value) -> NetworkCommand: #SUPER not secure
        if not self._UserIdIsRegistered(userId):
            return NetworkCommand("set").RST()
        
        self._users[userId][key] = value
        return NetworkCommand("set").ACK()
    
    def GetPrekeyBundle(self, command):
        reply = NetworkCommand(command.Operation())
        user = self._users.get(command.Get("userId"))
        if user is None: return reply.RST()
        
        reply.With("bundle", {})
        reply.WithInner("bundle", "IK", user["IK"])
        reply.WithInner("bundle", "SPK", user["SPK"])
        reply.WithInner("bundle", "SPK_sig", user["SPK_sig"])
        if len(user["OPKs"]) > 0:
            reply.WithInner("bundle","OPK", user["OPKs"].pop())
        return reply
    
    def PublishKeyBundle(self, command):
        user = self._users.get(command.Get("userId"), None)
        bundle = command.Get("bundle")
        user["IK"] = bundle["IK"]
        user["SPK"] = bundle["SPK"]
        user["SPK_sig"] = bundle["SPK_sig"]
        user["OPKs"].extend(bundle.get("OPKs", []))
        return NetworkCommand(command.Operation()).ACK()
        
    
    
    def _UserIdIsRegistered(self, userId :str):
        return userId in self._users
    
    async def Ignore(command :NetworkCommand):
        pass
    
    