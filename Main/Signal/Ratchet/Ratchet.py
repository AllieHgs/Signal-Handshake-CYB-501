# -*- coding: utf-8 -*-
from __future__ import annotations
import base64
from Main.Signal.Ratchet.IRatchet import IRatchet


class Ratchet(IRatchet):
    """
    A temporary, IRatchet-compatible “fake” ratchet that simulates
    encoding/decoding using Base64. This version is fully reversible,
    consistent, and safe for integration tests until real crypto is added.
    """

    def __init__(self, data: IRatchet.InitData):
        super().__init__(data)

        # Example: store a counter to show statefulness
        self.send_counter = 0
        self.recv_counter = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _encode(self, raw: str) -> str:
        """Encode string -> Base64 string"""
        raw_bytes = raw.encode("utf-8")
        encoded = base64.b64encode(raw_bytes).decode("utf-8")
        return encoded

    def _decode(self, enc: str) -> str:
        """Decode Base64 string -> string"""
        enc_bytes = base64.b64decode(enc.encode("utf-8"))
        decoded = enc_bytes.decode("utf-8")
        return decoded

    # ------------------------------------------------------------------
    # IRatchet interface implementations
    # ------------------------------------------------------------------
    def Send(self, data: IRatchet.SendData) -> IRatchet.SendReturnData:
        result = IRatchet.SendReturnData()

        plaintext: str = data.plaintext
        encoded = self._encode(plaintext)

        # Fill return data
        result.ciphertext = encoded

        # Increase state (simulates evolving keys)
        self.send_counter += 1

        return result

    def Receive(self, data: IRatchet.ReceiveData) -> IRatchet.ReceiveReturnData:
        result = IRatchet.ReceiveReturnData()

        ciphertext: str = data.ciphertext
        decoded = self._decode(ciphertext)

        # Fill return data
        result.plaintext = decoded

        # Increase state (simulates evolving keys)
        self.recv_counter += 1

        return result
