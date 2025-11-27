# -*- coding: utf-8 -*-
from __future__ import annotations

from IRatchet import RatchetState
from Ratchet import Ratchet


class RatchetBuilder:
    """
    Constructs a fully initialized Ratchet instance.
    Your partner will call this AFTER the handshake,
    providing the shared secret and the peer’s DH key.
    """

    def __init__(self):
        self._root_key = None
        self._dh_pair = None
        self._their_dh = None

    def with_root_key(self, root_key: bytes) -> "RatchetBuilder":
        self._root_key = root_key
        return self

    def with_dh_pair(self, dh_pair) -> "RatchetBuilder":
        self._dh_pair = dh_pair
        return self

    def with_their_dh(self, their_dh) -> "RatchetBuilder":
        self._their_dh = their_dh
        return self

    def build(self) -> Ratchet:
        if self._root_key is None:
            raise ValueError("RatchetBuilder: root_key is missing")
        if self._dh_pair is None:
            raise ValueError("RatchetBuilder: dh_pair is missing")
        if self._their_dh is None:
            raise ValueError("RatchetBuilder: their_dh is missing")

        # initialize a clean state
        state = RatchetState()

        # create the complete Ratchet instance
        return Ratchet(
            state=state,
            root_key=self._root_key,
            dh_pair=self._dh_pair,
            their_dh=self._their_dh,
        )
