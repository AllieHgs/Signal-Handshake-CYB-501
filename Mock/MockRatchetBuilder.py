class MockRatchet:
    def encrypt(self, plaintext):
        return f"[MOCK_ENC]{plaintext}"
    def decrypt(self, ciphertext):
        return ciphertext.replace("[MOCK_ENC]", "")

class MockRatchetBuilder:
    def build(self):
        return MockRatchet()
