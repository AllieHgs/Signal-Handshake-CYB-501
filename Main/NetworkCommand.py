# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any
import json
from enum import Enum
from uuid import uuid4
import Abstract.Network as Network

class Status(Enum):
    Fail = 0
    Success = 1
    Pending = 2
    
class NetworkCommand:
    verbosity = 1
    
    def __init__(self, operation :str ="noop", 
                 status :Status =Status.Pending, 
                 **kwargs):
        self.kwargs = dict(kwargs)
        self.kwargs.setdefault("version", "0.0.0")
        self.kwargs.setdefault("protocol", list()) #list[str]
        self.kwargs["commandid"] = str(uuid4())  # unique ID
        self.kwargs["operation"] = operation
        #For ease, flag is a dict[str,bool], it is more optimal to use a byte
        self.kwargs["flags"] = {"syn":False,"ack":False,"fin":False,"rst":False} 
        self.status = status
        self.token = None #Network.Token
        self.reply = None #NetworkCommand
        self.request = None #NetworkCommand, command this reply is to
        pass
    
    def With(self, key :str, value) -> NetworkCommand:
        self.kwargs[key] = value
        return self
    def Without(self, key) -> NetworkCommand:
        self.kwargs.pop(key)
        return self
    
    def WithInner(self, key, innerKey, value) -> NetworkCommand:
        self.kwargs.setdefault(key, dict())
        self.kwargs[key][innerKey] = value
        return self
    
    _sentinel = object()
    def Get(self, key :str, default :Any =_sentinel, setDefault :bool = False) -> Any:
        if default is self._sentinel:
            return self.kwargs[key]
        else:
            if setDefault and key not in self.kwargs:
                self.kwargs[key] = default
                return default
            return self.kwargs.get(key, default)
        pass
    
    def WithToken(self, token : Network.Token):
        self.token = token
        return self
    def WithReply(self, command :NetworkCommand):
        self.reply = command
        return self
    def ReplyTo(self, command :NetworkCommand):
        self.request = command
        self.With("replyto", command.Get("commandid"))
        return self
    
    def IsReply(self):
        return self.replyTo is not None
    
    def Complete(self):
        if self.status == Status.Pending:
            self.status = Status.Success
        self._ephemeralToken()
        return self
    def Fail(self):
        self.status = Status.Fail
        self._ephemeralToken()
        return self
    
    def _ephemeralToken(self):
        if self.token != None and self.token.IsEphemeral():
            self.token = None
                
    def IsPending(self):
        return self.status == Status.Pending
    def IsComplete(self):
        return not self.IsPending()
    def IsFailed(self):
        return self.status == Status.Fail
    def IsSuccess(self):
        return self.status == Status.Success
    
    def GetReplyUUID(self) -> str:
        return self.Get("replyto", None)
    def GetUUID(self) -> str:
        return self.kwargs["commandid"]
    
    def Version(self, version :str):
        self.With("version", version)
        return self
    def GetVersion(self) -> str:
        return self.kwargs["version"]
    
    def Protocol(self, protocol):
        self.kwargs["protocol"].append(protocol)
    def GetProtocol(self) -> list[str]:
        return self.Get("protocol")
    
    def SYN(self, isSet :bool =True): #Synchronize flag
        self.kwargs["flags"]["syn"] = isSet
        return self
    def ACK(self, isSet :bool =True): #Acknowledge flag
        self.kwargs["flags"]["ack"] = isSet
        return self
    def FIN(self, isSet :bool =True): # Finish flag
        self.kwargs["flags"]["fin"] = isSet
        return self
    def RST(self, isSet :bool =True): #Reset flag
        self.kwargs["flags"]["rst"] = isSet
        return self
    def GetSYN(self) -> bool: #Synchronize flag
        return self.kwargs["flags"]["syn"]
    def GetACK(self) -> bool: #Acknowledge flag
        return self.kwargs["flags"]["ack"]
    def GetFIN(self) -> bool: # Finish flag
        return self.kwargs["flags"]["fin"]
    def GetRST(self) -> bool: #Reset flag
        return self.kwargs["flags"]["rst"]    
    
    def __getitem__(self, key):
        return self.kwargs[key]
    def __setitem__(self, key, value):
        self.kwargs[key] = value
            
    def Operation(self) -> str():
        return self.kwargs.get("operation", "noop")
    def Is(self, operation :str, caseSensitive :bool =False) -> bool:
        if caseSensitive:
            return self.Operation() == operation
        else:
            return self.Operation().lower() == operation.lower()
        
    
    def Contains(self, key) -> bool:
        return key in self.kwargs
    def __contains__(self, key):
        return key in self.kwargs
    
    def Serialize(self) -> str:
        self.kwargs["token"] = self.token.data if self.token is not None and self.token.data is not None else {}
        return json.dumps(self.kwargs, separators=(',', ':'), ensure_ascii=False)

    @classmethod
    def Deserialize(cls, string: str) -> NetworkCommand:
        data = json.loads(string)
        if not isinstance(data, dict):
            return cls({"operation":"error"})
        
        return cls(**data)
    
    _dontPrintKeys = set()
    @classmethod
    def HideKeys(cls, *args):
        cls._dontPrintKeys = cls._dontPrintKeys.union(args)
        
    def hideKeys(self, *args):
        if not hasattr(self, "_dontPrintKeys"): self._dontPrintKeys = set()
        self._dontPrintKeys = self._dontPrintKeys.union(args)
    
    def __str__(self):
        """ Verbosity
        3 : all
        2 : no version/protocol
        1 : no uuids
        0 : no args, just operation + flags
        """
        s = self.kwargs["operation"] + " "
        if self.GetSYN():
            s += "SYN " if self.kwargs["flags"]["syn"] else ""
        if self.GetACK():
            s += "ACK " if self.kwargs["flags"]["ack"] else ""
        if self.GetFIN():
            s += "FIN " if self.kwargs["flags"]["fin"] else ""
        if self.GetRST():
            s += "RST " if self.kwargs["flags"]["rst"] else ""  
        
        # Use self verbosity if present, otherwise class verbosity
        verbosity = self.verbosity if hasattr(self, "verbosity") else self.__class__.verbosity
        if verbosity <= 0: return s
        
        dontPrintKeys = self._dontPrintKeys if hasattr(self, "_dontPrintKeys") else self.__class__._dontPrintKeys
        keyFilter = dontPrintKeys.union(["operation", "flags"])
        if verbosity <= 1:
            keyFilter = keyFilter.union(["commandid", "replyto", "uuid", "token"])
        if verbosity <= 2:
            keyFilter = keyFilter.union(["version", "protocol"])
        
        #print(f"Hiding Keys {keyFilter}")
        s += str(dict(filter(lambda x: x[0] not in keyFilter, self.kwargs.items())))
        return s