# -*- coding: utf-8 -*-
from __future__ import annotations
from abc import ABC, abstractmethod
from Main.NetworkCommand import NetworkCommand

class IRatchet(ABC):
    """
    Modify ONLY the data classes' __init__ functions.
    These are now fully defined for a Double Ratchet implementation.

    IMPORTANT:
    - All fields MUST be JSON-serializable.
    - If a variable should be transmitted over the network:
        add "#Send" next to it in SendReturnData
        add "#Receive" next to it in ReceiveData
    """

    # ----------------------------------------------------------------------
    # Data used to initialize the ratchet state
    # ----------------------------------------------------------------------
    class InitData:
        def __init__(
            self,
            root_key: bytes | str = "",
            dh_self_priv: bytes | str = "",
            dh_self_pub: bytes | str = "",
            dh_remote_pub: bytes | str = "",
            send_chain_key: bytes | str = "",
            recv_chain_key: bytes | str = ""
        ):
            # All converted to base64 strings or hex strings by the builder to ensure JSON safety.
            self.root_key = root_key
            self.dh_self_priv = dh_self_priv
            self.dh_self_pub = dh_self_pub
            self.dh_remote_pub = dh_remote_pub
            self.send_chain_key = send_chain_key
            self.recv_chain_key = recv_chain_key

    # ----------------------------------------------------------------------
    # Data that Ratchet.Send() receives before encoding
    # ----------------------------------------------------------------------
    class SendData:
        def __init__(self, plaintext: str, command_type: str = "MESSAGE"):
            self.plaintext = plaintext
            self.command_type = command_type

    # ----------------------------------------------------------------------
    # Data that Ratchet.Send() outputs for transmission
    # ----------------------------------------------------------------------
    class SendReturnData:
        def __init__(self):
            self.ciphertext = None       # #Send (bytes or base64)
            self.header = None           # #Send (dict of ratchet metadata)
            self.command_type = None     # #Send

    # ----------------------------------------------------------------------
    # Data that Ratchet.Receive() receives (ciphertext + ratchet header)
    # ----------------------------------------------------------------------
    class ReceiveData:
        def __init__(self, ciphertext, header, command_type="MESSAGE"):
            self.ciphertext = ciphertext   # #Receive
            self.header = header           # #Receive
            self.command_type = command_type

    # ----------------------------------------------------------------------
    # Data that Ratchet.Receive() outputs after decryption
    # ----------------------------------------------------------------------
    class ReceiveReturnData:
        def __init__(self):
            self.plaintext = None
            self.command_type = None
            self.error = None

    # ----------------------------------------------------------------------
    # Do NOT modify below this line
    # ----------------------------------------------------------------------

    def __init__(self, data: InitData):
        self.data = data

    @abstractmethod
    def Send(self, data: SendData) -> SendReturnData:
        pass

    @abstractmethod
    def Receive(self, data: ReceiveData) -> ReceiveReturnData:
        pass

    
