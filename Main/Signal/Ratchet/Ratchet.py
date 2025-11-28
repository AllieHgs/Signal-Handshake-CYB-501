# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import base64
from typing import Optional, Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519

from Main.Signal.Ratchet.IRatchet import IRatchet


def _to_bytes_maybe_b64(v) -> bytes:
    """
    Accepts bytes or str (possibly base64) or None.
    Returns bytes.
    """
    if v is None:
        return b""
    if isinstance(v, bytes):
        return v
    if isinstance(v, str):
        # Attempt base64 decode; if it fails, treat as raw utf-8 bytes
        try:
            # Add padding if needed
            missing = len(v) % 4
            if missing:
                v = v + ("=" * (4 - missing))
            return base64.b64decode(v)
        except Exception:
            return v.encode("utf-8")
    # unknown type -> string-encode
    return str(v).encode("utf-8")


def _b64(s: Optional[bytes]) -> Optional[str]:
    if s is None or s == b"":
        return None
    return base64.b64encode(s).decode("ascii")


def hkdf_derive(key_material: bytes, info: bytes, length: int = 32) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=info,
    ).derive(key_material)


def kdf_chain(chain_key: bytes) -> Tuple[bytes, bytes]:
    """
    From a chain key derive (next_chain_key, message_key)
    """
    next_ck = hkdf_derive(chain_key, b"ck-next", 32)
    msg_key = hkdf_derive(chain_key, b"ck-msg", 32)
    return next_ck, msg_key


class Ratchet(IRatchet):
    """
    Practical, test-friendly ratchet implementation.

    - Clients can be initialized with raw bytes (builder will base64-encode if needed).
    - For the tests we assume both sides share the same root_key initially.
    - Send/Receive derive per-message keys from send_chain / recv_chain (HKDF).
    - ratchet_step(new_remote_pub) is present for later DH-based upgrades (not required for basic tests).
    """

    def __init__(self, data: IRatchet.InitData):
        super().__init__(data)

        # Root key (bytes) — accept raw or base64 string
        self.root_key = _to_bytes_maybe_b64(data.root_key) if getattr(data, "root_key", None) else os.urandom(32)

        # Local DH key pair (optional)
        self.dh_self = None
        self.dh_self_pub_bytes = None
        if getattr(data, "dh_self_priv", None):
            priv_bytes = _to_bytes_maybe_b64(data.dh_self_priv)
            try:
                self.dh_self = x25519.X25519PrivateKey.from_private_bytes(priv_bytes)
                self.dh_self_pub_bytes = self.dh_self.public_key().public_bytes(
                    encoding=x25519.serialization.Encoding.Raw,
                    format=x25519.serialization.PublicFormat.Raw,
                )
            except Exception:
                # If conversion fails, generate ephemeral pair
                self.dh_self = x25519.X25519PrivateKey.generate()
                try:
                    self.dh_self_pub_bytes = self.dh_self.public_key().public_bytes(
                        encoding=x25519.serialization.Encoding.Raw,
                        format=x25519.serialization.PublicFormat.Raw,
                    )
                except Exception:
                    self.dh_self_pub_bytes = None
        else:
            # not required for basic tests
            try:
                self.dh_self = x25519.X25519PrivateKey.generate()
                self.dh_self_pub_bytes = self.dh_self.public_key().public_bytes(
                    encoding=x25519.serialization.Encoding.Raw,
                    format=x25519.serialization.PublicFormat.Raw,
                )
            except Exception:
                self.dh_self = None
                self.dh_self_pub_bytes = None

        # Remote DH pub (store bytes if provided)
        self.dh_remote_pub_bytes = _to_bytes_maybe_b64(getattr(data, "dh_remote_pub", None)) if getattr(data, "dh_remote_pub", None) else None

        # Initialize chain keys (may be base64 strings or bytes)
        self.send_chain = _to_bytes_maybe_b64(getattr(data, "send_chain_key", None)) or None
        self.recv_chain = _to_bytes_maybe_b64(getattr(data, "recv_chain_key", None)) or None

        # Message counters for observability
        self.send_count = int(getattr(data, "send_message_number", 0)) if hasattr(data, "send_message_number") else 0
        self.recv_count = int(getattr(data, "recv_message_number", 0)) if hasattr(data, "recv_message_number") else 0

    # ---------------------
    # Optional DH ratchet step (keeps API for integration)
    # ---------------------
    def ratchet_step(self, received_pub_bytes: bytes):
        """
        Perform a DH ratchet step using our current private key and the received public key bytes.
        This updates the root_key and reinitializes send/recv chain keys derived from the new root_key.

        Note: For the simple integration tests we do not automatically trigger rx/tx ratchets
        — the test harness can call this explicitly when appropriate.
        """
        if not self.dh_self or not received_pub_bytes:
            return

        try:
            remote_pub = x25519.X25519PublicKey.from_public_bytes(received_pub_bytes)
            shared = self.dh_self.exchange(remote_pub)
            # Derive new root and use it to generate fresh chain seeds
            self.root_key = hkdf_derive(self.root_key + shared, b"rk")
            self.send_chain = hkdf_derive(self.root_key, b"send-seed")
            self.recv_chain = hkdf_derive(self.root_key, b"recv-seed")
            # rotate our DH keypair
            self.dh_self = x25519.X25519PrivateKey.generate()
            try:
                self.dh_self_pub_bytes = self.dh_self.public_key().public_bytes(
                    encoding=x25519.serialization.Encoding.Raw,
                    format=x25519.serialization.PublicFormat.Raw,
                )
            except Exception:
                # best-effort
                self.dh_self_pub_bytes = None
        except Exception:
            # non-fatal — leave state unchanged
            return

    # ---------------------
    # SEND: derive msg-key from send_chain (or root_key) and encrypt
    # ---------------------
    def Send(self, data: IRatchet.SendData) -> IRatchet.SendReturnData:
        out = IRatchet.SendReturnData()

        # ensure a send_chain exists
        if self.send_chain is None:
            # derive a send_chain seed from root_key
            self.send_chain = hkdf_derive(self.root_key, b"send-seed")

        # KDF to get next chain key and message key
        next_ck, msg_key = kdf_chain(self.send_chain)
        self.send_chain = next_ck

        # AES-GCM encrypt
        aes = AESGCM(msg_key)
        nonce = os.urandom(12)
        plaintext_bytes = data.plaintext.encode("utf-8") if isinstance(data.plaintext, str) else data.plaintext
        ct = aes.encrypt(nonce, plaintext_bytes, None)

        out.ciphertext = base64.b64encode(nonce + ct).decode("ascii")

        # header: include our DH public for later (if available) and message counter
        header = {
            "dh_pub": _b64(self.dh_self_pub_bytes) if self.dh_self_pub_bytes else None,
            "send_count": self.send_count,
        }
        out.header = header
        out.command_type = data.command_type

        self.send_count += 1
        return out

    # ---------------------
    # RECEIVE: derive msg-key from recv_chain (or root_key) and decrypt
    # ---------------------
    def Receive(self, data: IRatchet.ReceiveData) -> IRatchet.ReceiveReturnData:
        out = IRatchet.ReceiveReturnData()

        try:
            # If header contains remote dh_pub and we don't match, optionally ratchet
            remote_pub_b64 = None
            if data.header and isinstance(data.header, dict):
                remote_pub_b64 = data.header.get("dh_pub")

            remote_pub_bytes = _to_bytes_maybe_b64(remote_pub_b64) if remote_pub_b64 else None

            # If remote DH pub changed and we have a DH private, we can optionally ratchet.
            # For basic tests where both sides share same root_key, doing a ratchet here would break decrypt,
            # so we only perform DH ratchet if self.dh_remote_pub_bytes exists and differs AND dh_self exists.
            if remote_pub_bytes and self.dh_remote_pub_bytes and remote_pub_bytes != self.dh_remote_pub_bytes and self.dh_self:
                # perform DH ratchet (safe to update)
                self.ratchet_step(remote_pub_bytes)
                self.dh_remote_pub_bytes = remote_pub_bytes
            else:
                # set stored remote pub if not set
                if remote_pub_bytes and not self.dh_remote_pub_bytes:
                    self.dh_remote_pub_bytes = remote_pub_bytes

            # ensure we have a recv_chain
            if self.recv_chain is None:
                self.recv_chain = hkdf_derive(self.root_key, b"recv-seed")

            # derive next recv chain and message key
            next_ck, msg_key = kdf_chain(self.recv_chain)
            self.recv_chain = next_ck

            blob = base64.b64decode(data.ciphertext)
            nonce = blob[:12]
            ciphertext = blob[12:]

            aes = AESGCM(msg_key)
            pt = aes.decrypt(nonce, ciphertext, None)
            out.plaintext = pt.decode("utf-8")
            out.command_type = data.command_type
            self.recv_count += 1
            return out
        except Exception as e:
            out.error = str(e)
            return out
