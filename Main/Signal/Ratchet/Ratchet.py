# -*- coding: utf-8 -*-
from Main.Signal.Ratchet.IRatchet import IRatchet
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64
from typing import Optional, Dict, Any


# ---------------------------
# Helpers: base64 helpers
# ---------------------------
def b64(b: Optional[bytes]) -> Optional[str]:
    if b is None:
        return None
    return base64.b64encode(b).decode("ascii")


def ub64(s: Optional[str]) -> Optional[bytes]:
    if s is None:
        return None
    return base64.b64decode(s.encode("ascii"))


# ---------------------------
# Simple HKDF wrapper
# ---------------------------
def hkdf_derive(key_material: bytes, info: bytes = b"ratchet", length: int = 32) -> bytes:
    hkdf = HKDF(algorithm=SHA256(), length=length, salt=None, info=info)
    return hkdf.derive(key_material)


# ---------------------------
# KDF for root -> chain split (returns (new_root, new_chain))
# ---------------------------
def kdf_rk(root_key: bytes, dh_shared: bytes) -> (bytes, bytes):
    # combine shared + root, then HKDF to 64 bytes and split
    material = dh_shared + root_key
    out = hkdf_derive(material, info=b"rk", length=64)
    return out[:32], out[32:64]


# ---------------------------
# KDF for chain -> message key + next chain
# ---------------------------
def kdf_ck(chain_key: bytes) -> (bytes, bytes):
    out = hkdf_derive(chain_key, info=b"ck", length=64)
    return out[:32], out[32:64]  # message_key, next_chain_key


# ---------------------------
# Ratchet class
# ---------------------------
class Ratchet(IRatchet):
    """
    IRatchet-compliant Double Ratchet wrapper.

    - Keeps state in self.data (IRatchet.InitData)
    - Send() takes IRatchet.SendData and returns IRatchet.SendReturnData
    - Receive() takes IRatchet.ReceiveData and returns IRatchet.ReceiveReturnData

    NOTE: For JSON-safety all bytes in headers/ciphertext are base64-encoded strings.
    """

    def __init__(self, data: IRatchet.InitData):
        super().__init__(data)

        # Initialize or generate DH pair
        if getattr(self.data, "dh_self_priv", ""):
            try:
                # If provided as base64 string, decode and load
                raw = ub64(self.data.dh_self_priv) if isinstance(self.data.dh_self_priv, str) else self.data.dh_self_priv
                self.DH_private = X25519PrivateKey.from_private_bytes(raw)
                # public may have been provided
                if getattr(self.data, "dh_self_pub", ""):
                    rawpub = ub64(self.data.dh_self_pub) if isinstance(self.data.dh_self_pub, str) else self.data.dh_self_pub
                    self.DH_public = X25519PublicKey.from_public_bytes(rawpub)
                else:
                    self.DH_public = self.DH_private.public_key()
            except Exception:
                # fallback: generate new pair
                self.DH_private = X25519PrivateKey.generate()
                self.DH_public = self.DH_private.public_key()
        else:
            self.DH_private = X25519PrivateKey.generate()
            self.DH_public = self.DH_private.public_key()

        # remote DH pub (may be empty at start)
        if getattr(self.data, "dh_remote_pub", ""):
            raw = ub64(self.data.dh_remote_pub) if isinstance(self.data.dh_remote_pub, str) else self.data.dh_remote_pub
            try:
                self.remote_DH_public = X25519PublicKey.from_public_bytes(raw)
            except Exception:
                self.remote_DH_public = None
        else:
            self.remote_DH_public = None

        # root key and chain keys
        # accept base64 strings or bytes or empty
        if getattr(self.data, "root_key", ""):
            self.root_key = ub64(self.data.root_key) if isinstance(self.data.root_key, str) else self.data.root_key
        else:
            self.root_key = os.urandom(32)

        if getattr(self.data, "send_chain_key", ""):
            self.send_chain_key = ub64(self.data.send_chain_key) if isinstance(self.data.send_chain_key, str) else self.data.send_chain_key
        else:
            self.send_chain_key = self.root_key

        if getattr(self.data, "recv_chain_key", ""):
            self.recv_chain_key = ub64(self.data.recv_chain_key) if isinstance(self.data.recv_chain_key, str) else self.data.recv_chain_key
        else:
            self.recv_chain_key = self.root_key

        # message counters
        self.send_message_number = int(getattr(self.data, "send_message_number", 0))
        self.recv_message_number = int(getattr(self.data, "recv_message_number", 0))

        # simple skipped messages map: {(dh_pub_b64, msgnum): message_key_b64}
        self.skipped_message_keys: Dict[(str, int), str] = {}

        # AESGCM doesn't need persistent state beyond keys
        # Ensure public bytes available
        self._update_data_public_fields()

    def _update_data_public_fields(self):
        # keep data's dh_self_pub consistent for possible persistence
        try:
            pub_bytes = self.DH_public.public_bytes()
        except TypeError:
            # cryptography's public_bytes requires args; handle robustly
            pub_bytes = self.DH_public.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
        # store as base64 on self.data for potential persistence
        self.data.dh_self_pub = b64(pub_bytes)
        self.data.root_key = b64(self.root_key)
        self.data.send_chain_key = b64(self.send_chain_key)
        self.data.recv_chain_key = b64(self.recv_chain_key)
        # private key saved as base64 for persistence if needed
        try:
            priv_bytes = self.DH_private.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )
            self.data.dh_self_priv = b64(priv_bytes)
        except Exception:
            # Not critical for runtime operation if private bytes can't be exported here
            pass

    # -------------------------
    # Low level: ratchet step when we learn new remote public key
    # -------------------------
    def ratchet_step(self, received_public_b64: str):
        """
        Perform a DH ratchet step using the received public key (base64 string).
        This updates root_key and resets send/recv chain keys to derived values,
        and rotates our DH keypair.
        """
        if received_public_b64 is None:
            return

        received_public = X25519PublicKey.from_public_bytes(ub64(received_public_b64))
        # compute shared secret using our current private key
        shared = self.DH_private.exchange(received_public)

        # derive new root and chain material
        new_root, new_chain = kdf_rk(self.root_key, shared)

        # For simplicity, assign new_chain to recv_chain_key (we are receiving side)
        self.root_key = new_root
        self.recv_chain_key = new_chain
        # also set send_chain_key to root (simple symmetric behavior)
        self.send_chain_key = new_root

        # rotate our DH keypair (generate new ephemeral)
        self.DH_private = X25519PrivateKey.generate()
        self.DH_public = self.DH_private.public_key()

        # update stored remote pub and persisted fields
        self.remote_DH_public = received_public
        self._update_data_public_fields()

        # reset recv message number (we expect next message n=0 on new chain)
        self.recv_message_number = 0

    # -------------------------
    # Send: encrypt a plaintext and advance send chain
    # -------------------------
    def Send(self, data: IRatchet.SendData) -> IRatchet.SendReturnData:
        out = IRatchet.SendReturnData()

        # Ensure plaintext exists
        plaintext = data.plaintext if hasattr(data, "plaintext") else ""
        if isinstance(plaintext, str):
            plaintext_bytes = plaintext.encode("utf-8")
        else:
            plaintext_bytes = plaintext

        # Advance send chain: derive message key and next chain key
        message_key, next_chain = kdf_ck(self.send_chain_key)
        self.send_chain_key = next_chain

        # AES-GCM encrypt
        nonce = os.urandom(12)
        aesgcm = AESGCM(message_key)
        ct = aesgcm.encrypt(nonce, plaintext_bytes, None)

        # Build header: include our current dh public (base64), and message number (n)
        try:
            pub_bytes = self.DH_public.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        except Exception:
            # fallback: try to call without args (some environments)
            pub_bytes = self.DH_public.public_bytes()

        header = {
            "dh_pub": b64(pub_bytes),
            "n": self.send_message_number,
        }

        # increment send counter after using current number
        self.send_message_number += 1

        # Package ciphertext as base64 of nonce + ct for JSON safety
        out.ciphertext = b64(nonce + ct)
        out.header = header
        out.command_type = getattr(data, "command_type", "MESSAGE")

        # update persistable fields
        self._update_data_public_fields()

        return out

    # -------------------------
    # Receive: decrypt ciphertext, possibly ratchet if header's DH is new
    # -------------------------
    def Receive(self, data: IRatchet.ReceiveData) -> IRatchet.ReceiveReturnData:
        out = IRatchet.ReceiveReturnData()

        ciphertext_b64 = getattr(data, "ciphertext", None)
        header = getattr(data, "header", None)

        if ciphertext_b64 is None:
            out.error = "No ciphertext provided"
            return out

        # If header contains a DH pub different from our recorded remote, perform ratchet step
        incoming_dh_pub = header.get("dh_pub") if isinstance(header, dict) else None
        if incoming_dh_pub and (self.data.dh_remote_pub != incoming_dh_pub):
            # perform ratchet step using incoming pub
            self.ratchet_step(incoming_dh_pub)
            # store remote pub base64 for future comparisons/persistence
            self.data.dh_remote_pub = incoming_dh_pub

        # decode ciphertext
        combined = ub64(ciphertext_b64)
        nonce = combined[:12]
        ct = combined[12:]

        # Derive message key from recv_chain_key
        message_key, next_recv_chain = kdf_ck(self.recv_chain_key)

        # Advance recv chain
        self.recv_chain_key = next_recv_chain
        self.recv_message_number += 1

        # Try decrypt
        try:
            aesgcm = AESGCM(message_key)
            plaintext = aesgcm.decrypt(nonce, ct, None)
            out.plaintext = plaintext.decode("utf-8")
            out.command_type = getattr(data, "command_type", "MESSAGE")
        except Exception as e:
            out.plaintext = None
            out.error = f"Decryption failed: {str(e)}"

        # update persisted fields
        self._update_data_public_fields()

        return out
