# -*- coding: utf-8 -*-

from Interfaces.INetwork import Status
from Mock.MockNetwork import MockNetwork
from Main.Signal.SignalNetworkDecorator import SignalNetworkDecorator
from Main.Signal.RatchetBuilder import RatchetBuilder
from Main.Mail import Mail
import asyncio
import nest_asyncio #Needed to fix problem with asyncio in spyder
nest_asyncio.apply() # ^

async def main():
    # Instantiate using builder
    ratchetBuilder = RatchetBuilder()
    
    
    #network = MockNetwork()
    network = SignalNetworkDecorator(MockNetwork(), ratchetBuilder)
    
    userA = "userA"
    userB = "userB"
    
    registerA, registerB = await asyncio.gather(
        network.Register(userA, "passA"),
        network.Register(userB, "passB")
    )
    if registerA.status == Status.Fail or registerB.status == Status.Fail:
        print("Failed to connect")
        return
    
    connectA, connectB = await asyncio.gather(
        network.Connect("userA", "passA"),
        network.Connect("userB", "passB")
    )
    if connectA.status == Status.Fail or connectB.status == Status.Fail:
        print("Failed to connect")
        return
    tokenA = connectA.token
    tokenB = connectB.token
    
    mailA = Mail(userA,"MessageA2B")
    mailB = Mail(userB, "MessageB2A")
    sendB = ""
    sendA,sendB = await asyncio.gather(
        tokenA.Send(mailA),
        tokenB.Send(mailB)
    )
    if sendA.status == Status.Fail or sendB.status == Status.Fail:
        print("Failed to send")
        return
    
    # This would be called by an event normally, but I want to force it here
    recieveA, recieveB = await asyncio.gather(
        tokenA.Receive(),
        tokenB.Receive()
    )
    if recieveA.status == Status.Fail or recieveB == Status.Fail:
        print("Failed to retrieve")
        return
    
    print("Recieving mail...\n")
    for mail in recieveA.inbox:
        print(mail)
    for mail in recieveB.inbox:
        print(mail)
    
    await asyncio.gather(
        tokenA.Disconnect(),
        tokenB.Disconnect()
    )

  
if __name__ == "__main__":
    asyncio.run(main())