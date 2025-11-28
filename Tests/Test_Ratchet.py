# -*- coding: utf-8 -*-
import sys, os
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import os
import base64
import asyncio

from Main.Signal.Ratchet.Ratchet import Ratchet
from Main.Signal.Ratchet.RatchetBuilder import RatchetBuilder
from Main.Signal.Ratchet.IRatchet import IRatchet

print("Running Ratchet Tests...\n")

def make_init(root_key: bytes = None):
    root_key = root_key or os.urandom(32)

    init = IRatchet.InitData(
        root_key=root_key,
        dh_self_priv=None,
        dh_self_pub=None,
        dh_remote_pub=None,
        send_chain_key=None,
        recv_chain_key=None
    )
    return init

def test_basic_send_receive():
    print("Test: basic send/receive", end=" ... ")

    # shared root key so symmetric ratchet works in test
    shared_root = os.urandom(32)

    initA = make_init(shared_root)
    initB = make_init(shared_root)

    # Build ratchets using builder (builder expects InitData raw values)
    builder = RatchetBuilder()
    ratA = builder.WithInitData(initA).Build()
    ratB = builder.WithInitData(initB).Build()

    # A sends to B
    send_data = IRatchet.SendData(plaintext="Hello Bob!", command_type="MESSAGE")
    sent = ratA.Send(send_data)

    assert sent.ciphertext is not None, "No ciphertext produced"
    assert sent.header is not None, "No header produced"

    recv_input = IRatchet.ReceiveData(ciphertext=sent.ciphertext, header=sent.header, command_type=sent.command_type)
    out = ratB.Receive(recv_input)

    assert out.error is None, f"Decryption failed: {out.error}"
    assert out.plaintext == "Hello Bob!", f"Plaintext mismatch: {out.plaintext}"

    print("OK")

def test_multiple_messages():
    print("Test: multiple messages advancing chains", end=" ... ")
    shared_root = os.urandom(32)
    initA = make_init(shared_root)
    initB = make_init(shared_root)

    ratA = RatchetBuilder().WithInitData(initA).Build()
    ratB = RatchetBuilder().WithInitData(initB).Build()

    for i in range(5):
        text = f"msg-{i}"
        sent = ratA.Send(IRatchet.SendData(plaintext=text))
        out = ratB.Receive(IRatchet.ReceiveData(ciphertext=sent.ciphertext, header=sent.header))
        assert out.error is None
        assert out.plaintext == text

    print("OK")

def run_all():
    test_basic_send_receive()
    test_multiple_messages()
    print("\nAll tests passed.")

if __name__ == "__main__":
    run_all()
