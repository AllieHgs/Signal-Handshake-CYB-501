# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any
import json

class NetworkCommand:
    def __init__(self, operation :str ="noop", **kwargs):
        self.kwargs = dict(kwargs)
        self.kwargs["operation"] = operation
        pass
    
    def With(self, key :str, arg) -> NetworkCommand:
        self.kwargs[key] = arg
        return self
    
    _sentinel = object()
    def Get(self, key :str, default :Any =_sentinel) -> Any:
        if default is self._sentinel:
            return self.kwargs[key]
        else:
            return self.kwargs.get(key, default)
    def __getitem__(self, key):
        return self.kwargs[key]
    
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
        return json.dumps(self.kwargs, separators=(',', ':'), ensure_ascii=False)

    @classmethod
    def Deserialize(cls, string: str) -> NetworkCommand:
        data = json.loads(string)
        if not isinstance(data, dict):
            return cls({"operation":"error"})
        return cls(**data)
    
    
    def __str__(self):
        return str(self.kwargs)