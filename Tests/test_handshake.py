# Tests/test_handshake.py
import sys, os

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import asyncio
import nest_asyncio
nest_asyncio.apply()

from Interfaces.INetwork import Status
from Mock.MockNetwork import MockNetwork

from Main.Signal.Ratchet.SignalNetworkDecorator import SignalNetworkDecorator
from Main.Signal.Ratchet.RatchetBuilder import RatchetBuilder
from Main.Signal.NetworkCommand import NetworkCommand
from Main.Mail import Mail


async def run_test():
    print("\n=== Running Handshake Encryption Test ===\n")

    # Step 1 — builder + underlying mock network
    ratchet_builder = RatchetBuilder()
    base_network = MockNetwork()

    # Step 2 — wrap with decorator
    network = SignalNetworkDecorator(base_network, ratchet_builder)

    # Step 3 — register two users
    # Step 3 — register two users
    regA = await network.Register("alice", "pw")
    regB = await network.Register("bob", "pw")

    # DEBUG: print registration results (temporary)
    print("DEBUG regA.status:", regA.status, " regA.reply:", getattr(regA, "reply", None))
    print("DEBUG regB.status:", regB.status, " regB.reply:", getattr(regB, "reply", None))

    assert regA.status == Status.Success
    assert regB.status == Status.Success

    # Step 4 — connect both users
    conA = await network.Connect("alice", "pw")
    conB = await network.Connect("bob", "pw")

    assert conA.status == Status.Success
    assert conB.status == Status.Success

    tokenA = conA.token
    tokenB = conB.token

    # Step 5 — Alice sends encrypted mail to Bob
    mail = Mail(sender="alice", receiver="bob", message="Hello Bob!")
    mailResult = await tokenA.Mail(mail)

    assert mailResult.status == Status.Success, "Mail send failed"

    # Step 6 — Bob checks his inbox (decrypted by decorator)
    inboxResult = await tokenB.CheckMail()
    assert inboxResult.status == Status.Success
    assert len(inboxResult.inbox) == 1

    msg = inboxResult.inbox[0]
    print("Bob received:", msg)

    assert msg == "Hello Bob!", "Decryption failed"

    print("\n=== Test Passed: Ratchet Decorator Working ===\n")


if __name__ == "__main__":
    asyncio.run(run_test())

