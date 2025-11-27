import asyncio
import nest_asyncio
nest_asyncio.apply()

from Interfaces.INetwork import Status, NetworkCommand
from Mock.MockNetwork import MockNetwork
from Main.Signal.SignalNetworkDecorator import SignalNetworkDecorator
from Main.Signal.Ratchet.RatchetBuilder import RatchetBuilder


async def test_handshake():
    # Build ratchet + decorated network
    ratchet_builder = RatchetBuilder()
    network = SignalNetworkDecorator(MockNetwork(), ratchet_builder)

    # Register users
    await network.Register("alice", "passA")
    await network.Register("bob", "passB")

    # Connect
    connectA = await network.Connect("alice", "passA")
    connectB = await network.Connect("bob", "passB")

    assert connectA.status == Status.Ok
    assert connectB.status == Status.Ok

    tokenA = connectA.token
    tokenB = connectB.token

    # Build a command from Alice → Bob
    cmd = NetworkCommand()
    cmd.to = "bob"
    cmd.payload = "Hello Bob!"

    # Send via DOUBLE-RATCHET WRAPPED token
    await tokenA.Send(cmd)

    # Bob receives
    inbox_result = await tokenB.Receive()
    assert inbox_result.status == Status.Ok

    print("\n--- Received Commands ---")
    for c in inbox_result.inbox:
        print("ciphertext→plaintext:", c.payload)

    print("\nTEST COMPLETE")


if __name__ == "__main__":
    asyncio.run(test_handshake())
