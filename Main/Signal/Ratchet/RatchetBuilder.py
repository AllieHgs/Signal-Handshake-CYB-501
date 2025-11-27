# -*- coding: utf-8 -*-
from __future__ import annotations

from Main.Signal.Ratchet.IRatchet import IRatchet
from Main.Signal.Ratchet.Ratchet import Ratchet


class RatchetBuilder:
    """
    Simple builder that constructs a new Ratchet instance.
    The real cryptographic parameters will be added later
    once your partner completes the handshake layer.
    """

    def __init__(self):
        pass

    def build(self) -> IRatchet:
        return Ratchet(None)
