# Main/Signal/Ratchet/RatchetedToken.py

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class RatchetedToken:
    """
    A minimal Double Ratchet placeholder.
    For now it only rotates a symmetric AES-GCM key after each message.
    """

    def __init__(self):
        self.key = AESGCM.generate_key(bit_length=128)
        self.aes = AESGCM(self.key)

    # ---------------------------------------------------------
    # INTERNAL: rotate AES key every message
    # ---------------------------------------------------------
    def _ratchet_step(self):
        self.key = AESGCM.generate_key(bit_length=128)
        self.aes = AESGCM(self.key)

    # ---------------------------------------------------------
    # Encrypt plaintext to base64 string
    # ---------------------------------------------------------
    def encrypt(self, plaintext: str) -> str:
        if isinstance(plaintext, str):
            plaintext = plaintext.encode("utf-8")

        nonce = os.urandom(12)
        ciphertext = self.aes.encrypt(nonce, plaintext, None)
        out = nonce + ciphertext

        # Perform ratchet step
        self._ratchet_step()

        return out.hex()

    # ---------------------------------------------------------
    # Decrypt base64 string to plaintext
    # ---------------------------------------------------------
    def decrypt(self, ciphertext_hex: str) -> str:
        data = bytes.fromhex(ciphertext_hex)
        nonce = data[:12]
        ciphertext = data[12:]

        try:
            plaintext = self.aes.decrypt(nonce, ciphertext, None)
            # Ratchet step on successful decrypt
            self._ratchet_step()
            return plaintext.decode("utf-8")
        except Exception:
            return "<DECRYPT-FAIL>"
