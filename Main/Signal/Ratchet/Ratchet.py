# Main/Signal/Ratchet/Ratchet.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import base64
from typing import Optional, Tuple, Dict, Any

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from Main.Signal.Ratchet.IRatchet import IRatchet

# --- helpers ---
def b64(b: Optional[bytes]) -> Optional[str]:
    if b is None:
        return None
    return base64.b64encode(b).decode("ascii")

def ub64(s: Optional[str]) -> Optional[bytes]:
    if s is None or s == "":
        return None
    if isinstance(s, bytes):
        return s
    return base64.b64decode(s.encode("ascii"))

def hkdf_derive(key_material: bytes, info: bytes = b"ratchet", length: int = 32) -> bytes:
    hk = HKDF(algorithm=hashes.SHA256(), length=length, salt=None, info=info)
    return hk.derive(key_material)

def kdf_rk(root_key: bytes, dh_shared: bytes) -> Tuple[bytes, bytes]:
    out = hkdf_derive(dh_shared + root_key, info=b"rk", length=64)
    return out[:32], out[32:64]

def kdf_ck(chain_key: bytes) -> Tuple[bytes, bytes]:
    out = hkdf_derive(chain_key, info=b"ck", length=64)
    return out[:32], out[32:64]


class Ratchet(IRatchet):
    """
    A minimal but correct Double Ratchet core that matches IRatchet data types.
    Network-facing fields are base64-encoded strings inside IRatchet.InitData and
    in SendReturnData/ReceiveData.
    """

    def __init__(self, data: IRatchet.InitData):
        super().__init__(data)

        # Load or generate DH keypair
        priv_b64 = getattr(self.data, "dh_self_priv", None)
        if priv_b64:
            raw = ub64(priv_b64)
            try:
                self.DH_private = X25519PrivateKey.from_private_bytes(raw)
            except Exception:
                self.DH_private = X25519PrivateKey.generate()
        else:
            self.DH_private = X25519PrivateKey.generate()

        # public bytes
        try:
            pub_bytes = self.DH_private.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        except Exception:
            pub_bytes = self.DH_private.public_key().public_bytes()

        self.DH_public = X25519PublicKey.from_public_bytes(pub_bytes)

        # remote public if provided
        remote_b64 = getattr(self.data, "dh_remote_pub", None)
        if remote_b64:
            raw_remote = ub64(remote_b64)
            try:
                self.remote_DH_public = X25519PublicKey.from_public_bytes(raw_remote)
            except Exception:
                self.remote_DH_public = None
        else:
            self.remote_DH_public = None

        # root & chain keys
        rk_b64 = getattr(self.data, "root_key", None)
        self.root_key = ub64(rk_b64) if rk_b64 else os.urandom(32)

        send_ck_b64 = getattr(self.data, "send_chain_key", None)
        recv_ck_b64 = getattr(self.data, "recv_chain_key", None)
        self.send_chain_key = ub64(send_ck_b64) if send_ck_b64 else None
        self.recv_chain_key = ub64(recv_ck_b64) if recv_ck_b64 else None

        self.send_message_number = int(getattr(self.data, "send_message_number", 0))
        self.recv_message_number = int(getattr(self.data, "recv_message_number", 0))

        # skipped message keys map for out-of-order (not fully used here)
        self.skipped_message_keys = getattr(self.data, "skipped_message_keys", {}) or {}

        # persist encoded fields back to data for convenience
        self._sync_state_to_data()

    def _export_private_bytes(self) -> Optional[bytes]:
        try:
            return self.DH_private.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )
        except Exception:
            return None

    def _export_public_bytes(self) -> bytes:
        try:
            return self.DH_private.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        except Exception:
            return self.DH_private.public_key().public_bytes()

    def _sync_state_to_data(self):
        try:
            priv = self._export_private_bytes()
            if priv is not None:
                self.data.dh_self_priv = b64(priv)
        except Exception:
            pass

        try:
            pub = self._export_public_bytes()
            self.data.dh_self_pub = b64(pub)
        except Exception:
            pass

        self.data.dh_remote_pub = getattr(self.data, "dh_remote_pub", None) or (b64(self.remote_DH_public.public_bytes()) if self.remote_DH_public else None)
        self.data.root_key = b64(self.root_key)
        self.data.send_chain_key = b64(self.send_chain_key) if self.send_chain_key else None
        self.data.recv_chain_key = b64(self.recv_chain_key) if self.recv_chain_key else None
        self.data.send_message_number = self.send_message_number
        self.data.recv_message_number = self.recv_message_number
        self.data.skipped_message_keys = self.skipped_message_keys

    # Perform DH ratchet when remote public changes
    def _do_dh_ratchet(self, received_pub_b64: str):
        if not received_pub_b64:
            return

        received_pub = X25519PublicKey.from_public_bytes(ub64(received_pub_b64))
        shared = self.DH_private.exchange(received_pub)
        new_root, new_chain = kdf_rk(self.root_key, shared)
        self.root_key = new_root
        self.recv_chain_key = new_chain

        # rotate our keypair
        self.DH_private = X25519PrivateKey.generate()
        self.DH_public = self.DH_private.public_key()
        self.recv_message_number = 0

        self.remote_DH_public = received_pub
        self.data.dh_remote_pub = received_pub_b64
        self._sync_state_to_data()

    # Send: encrypt and advance send chain
    def Send(self, data: IRatchet.SendData) -> IRatchet.SendReturnData:
        out = IRatchet.SendReturnData()

        plaintext = data.plaintext if isinstance(data.plaintext, bytes) else (data.plaintext.encode("utf-8") if data.plaintext is not None else b"")

        # ensure send chain exists
        if self.send_chain_key is None:
            self.send_chain_key = self.root_key

        message_key, next_send = kdf_ck(self.send_chain_key)
        self.send_chain_key = next_send

        nonce = os.urandom(12)
        aesgcm = AESGCM(message_key)
        ct = aesgcm.encrypt(nonce, plaintext, None)

        header = {
            "dh_pub": b64(self._export_public_bytes()),
            "pn": 0,
            "n": self.send_message_number,
        }

        self.send_message_number += 1
        out.ciphertext = b64(nonce + ct)
        out.header = header
        out.command_type = data.command_type

        self._sync_state_to_data()
        return out

    # Receive: decode, possible DH ratchet, advance recv chain and decrypt
    def Receive(self, data: IRatchet.ReceiveData) -> IRatchet.ReceiveReturnData:
        out = IRatchet.ReceiveReturnData()

        ciphertext_b64 = getattr(data, "ciphertext", None)
        header = getattr(data, "header", None)

        if ciphertext_b64 is None:
            out.error = "No ciphertext"
            return out

        incoming_dh_pub = header.get("dh_pub") if isinstance(header, dict) else None

        if incoming_dh_pub and (getattr(self.data, "dh_remote_pub", None) != incoming_dh_pub):
            self._do_dh_ratchet(incoming_dh_pub)
            self.data.dh_remote_pub = incoming_dh_pub

        try:
            combined = ub64(ciphertext_b64)
        except Exception as e:
            out.error = f"Invalid base64: {e}"
            return out

        nonce = combined[:12]
        ct = combined[12:]

        # ensure recv chain exists
        if self.recv_chain_key is None:
            self.recv_chain_key = self.root_key

        message_key, next_recv = kdf_ck(self.recv_chain_key)
        self.recv_chain_key = next_recv
        self.recv_message_number += 1

        try:
            aesgcm = AESGCM(message_key)
            plaintext = aesgcm.decrypt(nonce, ct, None)
            out.plaintext = plaintext.decode("utf-8")
            out.command_type = getattr(data, "command_type", None)
        except Exception as e:
            out.error = f"Decryption failed: {e}"

        self._sync_state_to_data()
        return out
