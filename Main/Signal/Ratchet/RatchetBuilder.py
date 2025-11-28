# Main/Signal/Ratchet/RatchetBuilder.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import base64
from Main.Signal.Ratchet.IRatchet import IRatchet
from Main.Signal.Ratchet.Ratchet import Ratchet

class RatchetBuilder:
    """
    Produces Ratchet instances. Use WithInitData(...) to pass handshake data
    (base64 or bytes). Build() will ensure JSON-safe fields and return Ratchet.
    """

    def __init__(self):
        self._init_data: IRatchet.InitData | None = None

    def WithInitData(self, init_data: IRatchet.InitData) -> "RatchetBuilder":
        self._init_data = init_data
        return self

    def Build(self, init_data: IRatchet.InitData | None = None) -> Ratchet:
        """
        Build a Ratchet. You may either:
         - previously call WithInitData(init) and then Build()
         - or call Build(init_data)
        """
        data = init_data if init_data is not None else self._init_data
        if data is None:
            # empty init allowed (fresh keys)
            safe = IRatchet.InitData()
            return Ratchet(safe)

        def _enc(v):
            if v is None:
                return ""
            if isinstance(v, bytes):
                return base64.b64encode(v).decode("utf-8")
            return v

        safe = IRatchet.InitData(
            root_key=_enc(data.root_key),
            dh_self_priv=_enc(data.dh_self_priv),
            dh_self_pub=_enc(data.dh_self_pub),
            dh_remote_pub=_enc(data.dh_remote_pub),
            send_chain_key=_enc(data.send_chain_key),
            recv_chain_key=_enc(data.recv_chain_key),
        )
        return Ratchet(safe)
