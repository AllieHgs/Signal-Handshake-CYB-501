# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Optional
import json


class NetworkCommand:
    """
    Unified command object for your Signal network layer.

    Supports two usage modes:

    1. Simple messaging:
        NetworkCommand("bob", "Hello Bob")

    2. Full operation-based commands:
        NetworkCommand(operation="handshake", key1=value1, key2=value2)
    """

    _sentinel = object()

    def __init__(
            self,
            target: Optional[str] = None,
            payload: Any = None,
            operation: str = "noop",
            **kwargs
    ):
        # Internal dict for serialization
        self.kwargs = dict(kwargs)

        # Normative fields
        self.target = target
        self.payload = payload
        self.kwargs["operation"] = operation

        # Store target/payload inside kwargs for serialization
        if target is not None:
            self.kwargs["target"] = target
        if payload is not None:
            self.kwargs["payload"] = payload

    # ----------------------------------------------------------------------
    # Mutators / Accessors
    # ----------------------------------------------------------------------
    def With(self, key: str, value: Any) -> NetworkCommand:
        self.kwargs[key] = value
        return self

    def Get(self, key: str, default: Any = _sentinel) -> Any:
        if default is self._sentinel:
            return self.kwargs[key]
        return self.kwargs.get(key, default)

    def __getitem__(self, key):
        return self.kwargs[key]

    def Contains(self, key) -> bool:
        return key in self.kwargs

    def __contains__(self, key):
        return key in self.kwargs

    # ----------------------------------------------------------------------
    # Operation handling
    # ----------------------------------------------------------------------
    def Operation(self) -> str:
        return self.kwargs.get("operation", "noop")

    def Is(self, operation: str, caseSensitive: bool = False) -> bool:
        op = self.Operation()
        return op == operation if caseSensitive else op.lower() == operation.lower()

    # ----------------------------------------------------------------------
    # Serialization
    # ----------------------------------------------------------------------
    def Serialize(self) -> str:
        return json.dumps(self.kwargs, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def Deserialize(cls, string: str) -> NetworkCommand:
        data = json.loads(string)

        if not isinstance(data, dict):
            return cls(operation="error")

        # Extract reserved fields
        target = data.pop("target", None)
        payload = data.pop("payload", None)
        operation = data.pop("operation", "noop")

        # Everything else stays as kwargs
        return cls(target=target, payload=payload, operation=operation, **data)

    # ----------------------------------------------------------------------
    def __repr__(self):
        return f"NetworkCommand(target={self.target!r}, payload={self.payload!r}, operation={self.Operation()!r}, kwargs={self.kwargs})"

    def __str__(self):
        return str(self.kwargs)
