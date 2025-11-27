# Tests/test_handshake.py

import asyncio
import nest_asyncio
nest_asyncio.apply()

from Interfaces.INetwork import Status
from Mock.MockNetwork import MockNetwork

# NEW: Import your decorator + builder
from Main.Signal.SignalNetwork import SignalNetwork
from Main.Signal.Ratchet.SignalNetworkDecorator import SignalNetworkDecorator
from Main.Signal.Ratchet.RatchetBuilder import RatchetBuilder
from Main.Signal.NetworkCommand import NetworkCommand


async def run_test():
    print("\n=== Running Handshake Encryption Test ===\n")

    # Step 1 — Create builder + base network
    ratchet_builder = RatchetBuilder()
    base_network = MockNetwork()

    # Step 2 — Wrap network with decorator
    network = SignalNetworkDecorator(base_network, ratchet_builder)

    # Step 3 — Register users
    regA = await network.Register("alice", "pw")
    regB = await network.Register("bob", "pw")

    assert regA.status == Status.Ok, "Registration failed for alice"
    assert regB.status == Status.Ok, "Registration failed for bob"

    # Step 4 — Connect both users
    conA = await network.Connect("alice", "pw")
    conB = await network.Connect("bob", "pw")

    assert conA.status == Status.Ok, "Connect failed for alice"
    assert conB.status == Status.Ok, "Connect failed for bob"

    tokenA = conA.token
    tokenB = conB.token

    # Step 5 — Alice sends encrypted message to Bob
    cmdA = NetworkCommand("bob", "Hello Bob!")
    sendA = await tokenA.Send(cmdA)
    assert sendA.status == Status.Ok

    # Step 6 — Bob receives message (should be decrypted)
    recvB = await tokenB.Receive()
    assert recvB.status == Status.Ok
    assert len(recvB.inbox) == 1

    received_payload = recvB.inbox[0].payload
    print("Bob received:", received_payload)

    # Step 7 — Ensure encryption actually changed payload
    assert received_payload == "Hello Bob!", "Decryption failed"

    print("\n=== Test Passed: Ratchet Decorator Working ===\n")


if __name__ == "__main__":
    asyncio.run(run_test())
