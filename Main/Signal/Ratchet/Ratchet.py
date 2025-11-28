# -*- coding: utf-8 -*-
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519

from Main.Signal.IRatchet import IRatchet


class Ratchet(IRatchet):
    """
    Single-file real Double Ratchet implementation.
    Minimal but correct:
    - HKDF for chain keys + message keys
    - X25519 for DH ratchet steps
    - AES-GCM for encryption/decryption
    """

    # ============================================================
    # CONSTRUCTOR
    # ============================================================
    def __init__(self, data: IRatchet.InitData):
        super().__init__(data)

        # Decode input into bytes
        self.root_key = base64.b64decode(data.root_key) if data.root_key else AESGCM.generate_key(bit_length=256)

        # Local DH keypair
        if data.dh_self_priv:
            private_bytes = base64.b64decode(data.dh_self_priv)
            self.dh_self = x25519.X25519PrivateKey.from_private_bytes(private_bytes)
        else:
            self.dh_self = x25519.X25519PrivateKey.generate()

        self.dh_self_pub = self.dh_self.public_key()

        # Remote DH public key
        if data.dh_remote_pub:
            self.dh_remote_pub = x25519.X25519PublicKey.from_public_bytes(base64.b64decode(data.dh_remote_pub))
        else:
            self.dh_remote_pub = None

        # Chains
        self.send_chain = base64.b64decode(data.send_chain_key) if data.send_chain_key else None
        self.recv_chain = base64.b64decode(data.recv_chain_key) if data.recv_chain_key else None

        self.send_count = 0
        self.recv_count = 0

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================
    def hkdf(self, key_material: bytes, info: str, out_len: int = 32):
        return HKDF(
            algorithm=hashes.SHA256(),
            length=out_len,
            salt=None,
            info=info.encode()
        ).derive(key_material)

    def derive_chain_key(self, ck: bytes):
        """Chain key → next_chain_key, message_key"""
        next_ck = self.hkdf(ck, "CHAIN")
        msg_key = self.hkdf(ck, "MSG")
        return next_ck, msg_key

    # ============================================================
    # DOUBLE RATCHET DH STEP
    # ============================================================
    def ratchet_step(self, new_remote_pub: x25519.X25519PublicKey):
        shared = self.dh_self.exchange(new_remote_pub)

        self.root_key = self.hkdf(self.root_key + shared, "ROOT")
        self.send_chain = self.hkdf(self.root_key, "SEND")
        self.recv_chain = self.hkdf(self.root_key, "RECV")

        # rotate own keypair
        self.dh_self = x25519.X25519PrivateKey.generate()
        self.dh_self_pub = self.dh_self.public_key()

    # ============================================================
    # SEND
    # ============================================================
    def Send(self, data: IRatchet.SendData) -> IRatchet.SendReturnData:
        ret = IRatchet.SendReturnData()

        # initialize first chain if needed
        if self.send_chain is None:
            self.send_chain = self.hkdf(self.root_key, "SEND")

        # derive next message key
        self.send_chain, msg_key = self.derive_chain_key(self.send_chain)

        aes = AESGCM(msg_key)
        nonce = AESGCM.generate_key(bit_length=96 // 8)
        ciphertext = aes.encrypt(nonce, data.plaintext.encode(), None)

        ret.ciphertext = base64.b64encode(nonce + ciphertext).decode()

        # header includes DH pub + counters
        ret.header = {
            "dh_pub": base64.b64encode(self.dh_self_pub.public_bytes_raw()).decode(),
            "count": self.send_count
        }

        ret.command_type = data.command_type
        self.send_count += 1

        return ret

    # ============================================================
    # RECEIVE
    # ============================================================
    def Receive(self, data: IRatchet.ReceiveData) -> IRatchet.ReceiveReturnData:
        ret = IRatchet.ReceiveReturnData()

        try:
            # decode remote pub
            remote_pub = x25519.X25519PublicKey.from_public_bytes(
                base64.b64decode(data.header["dh_pub"])
            )

            # if DH changed → ratchet
            if self.dh_remote_pub is None or remote_pub.public_bytes_raw() != self.dh_remote_pub.public_bytes_raw():
                self.ratchet_step(remote_pub)
                self.dh_remote_pub = remote_pub

            # init recv chain if needed
            if self.recv_chain is None:
                self.recv_chain = self.hkdf(self.root_key, "RECV")

            # derive next message key
            self.recv_chain, msg_key = self.derive_chain_key(self.recv_chain)

            blob = base64.b64decode(data.ciphertext)
            nonce = blob[:12]
            ciphertext = blob[12:]

            aes = AESGCM(msg_key)
            plaintext = aes.decrypt(nonce, ciphertext, None).decode()

            ret.plaintext = plaintext
            ret.command_type = data.command_type
            return ret

        except Exception as e:
            ret.error = str(e)
            return ret
