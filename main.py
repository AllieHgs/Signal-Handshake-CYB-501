# -*- coding: utf-8 -*-

from Interfaces.INetwork import Status
from Mock.MockNetwork import MockNetwork
from Main.Signal.SignalNetworkDecorator import SignalNetworkDecorator
from Main.Signal.Ratchet.RatchetBuilder import RatchetBuilder
from Main.Mail import Mail

import asyncio
import nest_asyncio
nest_asyncio.apply()

async def main():
    # 1. Build ratchet factory
    ratchetBuilder = RatchetBuilder()

    # 2. Underlying network (MockNetwork or your real network)
    baseNetwork = MockNetwork()

    # 3. Wrap it with SignalNetworkDecorator
    network = SignalNetworkDecorator(baseNetwork, ratchetBuilder)

    # ---- Normal flow below this line ----

    userA = "userA"
    userB = "userB"

    # Register users
    registerA, registerB = await asyncio.gather(
        network.Register(userA, "passA"),
        network.Register(userB, "passB")
    )
    if registerA.status == Status.Fail or registerB.status == Status.Fail:
        print("Failed to connect")
        print(registerA.reply)
        print(registerB.reply)
        return

    # Connect users — tokens returned here are *wrapped* with ratchets
    connectA, connectB = await asyncio.gather(
        network.Connect(userA, "passA"),
        network.Connect(userB, "passB")
    )

    if connectA.status == Status.Fail or connectB.status == Status.Fail:
        print("Failed to connect")
        return

    tokenA = connectA.token
    tokenB = connectB.token

    # Create mail objects
    mailA = Mail(userB, "MessageA2B")
    mailB = Mail(userA, "MessageB2A")

    # Send encrypted messages
    sendA, sendB = await asyncio.gather(
        tokenA.Mail(mailA),
        tokenB.Mail(mailB)
    )

    if sendA.status == Status.Fail or sendB.status == Status.Fail:
        print("Failed to send")
        return

    # Force retrieval
    receiveA, receiveB = await asyncio.gather(
        tokenA.CheckMail(),
        tokenB.CheckMail()
    )

    if receiveA.status == Status.Fail or receiveB.status == Status.Fail:
        print("Failed to retrieve")
        return

    print("Receiving mail...\n")

    for mail in receiveA.inbox:
        print(mail)

    for mail in receiveB.inbox:
        print(mail)

    # Disconnect users
    await asyncio.gather(
        tokenA.Disconnect(),
        tokenB.Disconnect()
    )


if __name__ == "__main__":
    asyncio.run(main())
