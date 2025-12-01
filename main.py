# -*- coding: utf-8 -*

from Abstract.Network import Network
from Main.NetworkLeaf import NetworkLeaf
from Main.Signal.SignalNetwork import SignalNetwork
from Main.Signal.RatchetNetwork import RatchetNetwork
from Mock.MockServer import MockServer
from Main.NetworkCommand import NetworkCommand, Status
from Main.Mail import Mail
import asyncio
import nest_asyncio #Needed to fix problem with asyncio in spyder
nest_asyncio.apply() # ^

async def main():
    #0-3
    NetworkCommand.verbosity = 1
    server = MockServer()
    server.log = True
    network = NetworkLeaf(server)
    network = SignalNetwork(network)
    #network = RatchetNetwork(network)
    
    userA = "userA"
    userB = "userB"
    
    registerA, registerB = await asyncio.gather(
        network.Register(userA, "passA"),
        network.Register(userB, "passB")
    )
    if registerA.IsFailed() or registerB.IsFailed():
        print("Failed to register")
        return
    
    connectA, connectB = await asyncio.gather(
        network.Connect("userA", "passA"),
        network.Connect("userB", "passB")
    )

    if connectA.IsFailed() or connectB.IsFailed():
        print("Failed to connect")
        return

    tokenA = connectA.token
    tokenB = connectB.token
    
    mailA = Mail(userB,"MessageA2B")
    mailB = Mail(userA, "MessageB2A")

    sendA,sendB = await asyncio.gather(
        tokenA.Mail(mailA),
        tokenB.Mail(mailB)
    )
    if sendA.IsFailed() or sendB.IsFailed():
        print("Failed to send")
        return
    
    # This would be called by an event normally, but I want to force it here
    receiveA, receiveB = await asyncio.gather(
        tokenA.CheckMail(),
        tokenB.CheckMail()
    )
    if receiveA.IsFailed() or receiveB.IsFailed():
        print("Failed to retrieve")
        return
    
    print(f"{userA}'s inbox:")
    for mail in receiveA.inbox:
        print(mail)
    print(f"{userB}'s inbox:")
    for mail in receiveB.inbox:
        print(mail)
    print("")
    
    await asyncio.gather(
        tokenA.Disconnect(),
        tokenB.Disconnect()
    )

  
if __name__ == "__main__":
    asyncio.run(main())