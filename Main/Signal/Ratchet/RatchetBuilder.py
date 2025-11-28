# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
from Main.Signal.Ratchet.IRatchet import IRatchet
from Main.Signal.Ratchet.Ratchet import Ratchet


class RatchetBuilder:
    """
    Minimal builder for the redesigned architecture.
    """

    def __init__(self):
        self._init_data = None

    # ------------------------------------------------------------------
    def WithInitData(self, init_data: IRatchet.InitData):
        self._init_data = init_data
        return self

    # ------------------------------------------------------------------
    def Build(self) -> Ratchet:
        if self._init_data is None:
            raise ValueError("InitData must be set before calling Build()")

        # DO NOT ENCODE PRIVATE KEY
        safe_data = IRatchet.InitData(
            root_key=self._encode(self._init_data.root_key),
            dh_self_priv=self._init_data.dh_self_priv,      # <-- raw 32 bytes preserved
            dh_self_pub=self._encode(self._init_data.dh_self_pub),
            dh_remote_pub=self._encode(self._init_data.dh_remote_pub),
            send_chain_key=self._encode(self._init_data.send_chain_key),
            recv_chain_key=self._encode(self._init_data.recv_chain_key),
        )

        return Ratchet(safe_data)

    # ------------------------------------------------------------------
    @staticmethod
    def _encode(value):
        """
        Makes bytes JSON-safe except private key.
        """
        if value is None:
            return ""
        if isinstance(value, bytes):
            return base64.b64encode(value).decode("utf-8")
        return value
