# Tests/Test_Ratchet.py
# Minimal unit test for the Ratchet implementation.
import os
import base64
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from Main.Signal.Ratchet.IRatchet import IRatchet
from Main.Signal.Ratchet.RatchetBuilder import RatchetBuilder

def b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")

def ub64(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


def make_init_pair():
    """
    Create shared root_key and two init structures (A and B) such that
    Ratchet(A) and Ratchet(B) can successfully exchange a message.
    """
    # shared root key (32 bytes)
    root_key = os.urandom(32)

    # generate X25519 keypairs for both sides
    privA = X25519PrivateKey.generate()
    privB = X25519PrivateKey.generate()

    privA_bytes = privA.private_bytes(
        encoding = __import__("cryptography.hazmat.primitives.serialization", fromlist=["serialization"]).serialization.Encoding.Raw,
        format = __import__("cryptography.hazmat.primitives.serialization", fromlist=["serialization"]).serialization.PrivateFormat.Raw,
        encryption_algorithm = __import__("cryptography.hazmat.primitives.serialization", fromlist=["serialization"]).serialization.NoEncryption()
    )

    privB_bytes = privB.private_bytes(
        encoding = __import__("cryptography.hazmat.primitives.serialization", fromlist=["serialization"]).serialization.Encoding.Raw,
        format = __import__("cryptography.hazmat.primitives.serialization", fromlist=["serialization"]).serialization.PrivateFormat.Raw,
        encryption_algorithm = __import__("cryptography.hazmat.primitives.serialization", fromlist=["serialization"]).serialization.NoEncryption()
    )

    pubA_bytes = privA.public_key().public_bytes(
        encoding = __import__("cryptography.hazmat.primitives.serialization", fromlist=["serialization"]).serialization.Encoding.Raw,
        format = __import__("cryptography.hazmat.primitives.serialization", fromlist=["serialization"]).serialization.PublicFormat.Raw
    )

    pubB_bytes = privB.public_key().public_bytes(
        encoding = __import__("cryptography.hazmat.primitives.serialization", fromlist=["serialization"]).serialization.Encoding.Raw,
        format = __import__("cryptography.hazmat.primitives.serialization", fromlist=["serialization"]).serialization.PublicFormat.Raw
    )

    # Build InitData objects with base64-encoded fields
    initA = IRatchet.InitData(
        root_key = b64(root_key),
        dh_self_priv = b64(privA_bytes),
        dh_self_pub = b64(pubA_bytes),
        dh_remote_pub = b64(pubB_bytes),
        send_chain_key = "",
        recv_chain_key = "",
    )

    initB = IRatchet.InitData(
        root_key = b64(root_key),
        dh_self_priv = b64(privB_bytes),
        dh_self_pub = b64(pubB_bytes),
        dh_remote_pub = b64(pubA_bytes),
        send_chain_key = "",
        recv_chain_key = "",
    )

    return initA, initB


def test_basic_send_receive():
    print("Running Ratchet basic send/receive test...")

    initA, initB = make_init_pair()

    # Build ratchets using the RatchetBuilder API
    builderA = RatchetBuilder().WithInitData(initA)
    builderB = RatchetBuilder().WithInitData(initB)

    ratA = builderA.Build()
    ratB = builderB.Build()

    # A -> B
    plaintext = "Hello Bob! This is Alice."
    send_data = ratA.Send(IRatchet.SendData(plaintext=plaintext))
    assert send_data.ciphertext is not None, "Send produced no ciphertext"
    assert isinstance(send_data.header, dict), "Send produced no header"

    recv_data_obj = IRatchet.ReceiveData(ciphertext=send_data.ciphertext, header=send_data.header)
    out = ratB.Receive(recv_data_obj)

    assert out.error is None, f"Decryption failed: {out.error}"
    assert out.plaintext == plaintext, f"Decrypted plaintext mismatch: {out.plaintext!r} != {plaintext!r}"

    print("A -> B passed.")

    # B -> A (round-trip)
    plaintext2 = "Reply from Bob to Alice."
    send2 = ratB.Send(IRatchet.SendData(plaintext=plaintext2))
    assert send2.ciphertext is not None

    recv2 = ratA.Receive(IRatchet.ReceiveData(ciphertext=send2.ciphertext, header=send2.header))
    assert recv2.error is None, f"Round-trip decryption failed: {recv2.error}"
    assert recv2.plaintext == plaintext2, "Round-trip plaintext mismatch"

    print("B -> A passed.")
    print("All Ratchet tests passed.")


if __name__ == "__main__":
    test_basic_send_receive()

