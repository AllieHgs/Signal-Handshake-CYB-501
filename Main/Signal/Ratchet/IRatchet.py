# Main/Signal/Ratchet/IRatchet.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from abc import ABC, abstractmethod
from Main.Signal.NetworkCommand import NetworkCommand

class IRatchet(ABC):
    """
    Data classes and interface for ratchet implementations.

    Only modify the data classes' __init__ if you need extra JSON-safe fields.
    """

    class InitData:
        def __init__(
            self,
            root_key: str | bytes = "",
            dh_self_priv: str | bytes = "",
            dh_self_pub: str | bytes = "",
            dh_remote_pub: str | bytes = "",
            send_chain_key: str | bytes = "",
            recv_chain_key: str | bytes = "",
        ):
            # All fields should be JSON-serializable (strings/base64)
            self.root_key = root_key
            self.dh_self_priv = dh_self_priv
            self.dh_self_pub = dh_self_pub
            self.dh_remote_pub = dh_remote_pub
            self.send_chain_key = send_chain_key
            self.recv_chain_key = recv_chain_key

    class SendData:
        def __init__(self, plaintext: str | bytes, command_type: str = "MESSAGE"):
            self.plaintext = plaintext
            self.command_type = command_type

    class SendReturnData:
        def __init__(self):
            # these are JSON-safe (strings/base64/dict)
            self.ciphertext = None    # #Send
            self.header = None        # #Send
            self.command_type = None  # #Send

    class ReceiveData:
        def __init__(self, ciphertext: str, header: dict, command_type: str = "MESSAGE"):
            self.ciphertext = ciphertext   # #Receive
            self.header = header           # #Receive
            self.command_type = command_type

    class ReceiveReturnData:
        def __init__(self):
            self.plaintext = None
            self.command_type = None
            self.error = None

    def __init__(self, data: InitData):
        self.data = data

    @abstractmethod
    def Send(self, data: SendData) -> SendReturnData:
        pass

    @abstractmethod
    def Receive(self, data: ReceiveData) -> ReceiveReturnData:
        pass
