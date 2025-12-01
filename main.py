# -*- coding: utf-8 -*

from Abstract.Network import Network
from Main.NetworkLeaf import NetworkLeaf
from Main.Signal.SignalNetwork import SignalNetwork
from Main.Signal.Ratchet.RatchetNetwork import RatchetNetwork
from Mock.MockServer import MockServer
from Main.NetworkCommand import NetworkCommand, Status
from Main.Mail import Mail

import asyncio
import nest_asyncio
nest_asyncio.apply()

import os
os.environ['PYTHONASYNCIODEBUG'] = '1'
debug = True

async def main():
    #if(debug):loop.set_debug()
    #0-3
    NetworkCommand.verbosity = 1
    NetworkCommand.HideKeys("IK", "IK_priv","IK_pub","SPK","SPK_priv","SPK_sig","SPK_pub","OPKs", "OPKs_pub", "pub_keys")
    
    server = MockServer()
    server.log = True
    network = NetworkLeaf(server)
    #network = SignalNetwork(network)
    #network = RatchetNetwork(network)
    
    userA = "userA"
    userB = "userB"

    # Register users
    registerA = await network.Register(userA, "passA")
    registerB = await network.Register(userB, "passB")
    """registerA, registerB = await asyncio.gather(
        network.Register(userA, "passA"),
        network.Register(userB, "passB")
    )"""
    if registerA.IsFailed() or registerB.IsFailed():
        print("Failed to register")
        return

    # Connect users — tokens returned here are *wrapped* with ratchets
    connectA = await network.Connect(userA, "passA")
    connectB = await network.Connect(userB, "passB")
    """connectA, connectB = await asyncio.gather(
        network.Connect(userA, "passA"),
        network.Connect(userB, "passB")
    )"""
    
    if connectA.IsFailed() or connectB.IsFailed():
        print("Failed to connect")
        return

    tokenA = connectA.token
    tokenB = connectB.token

    # Create mail objects
    mailA = Mail(userB, "MessageA2B")
    mailB = Mail(userA, "MessageB2A")

    # Send encrypted messages
    sendA = await tokenA.Mail(mailA)
    sendB = await tokenB.Mail(mailB)
    """sendA, sendB = await asyncio.gather(
        tokenA.Mail(mailA),
        tokenB.Mail(mailB)
    )"""
    if sendA.IsFailed() or sendB.IsFailed():
        print("Failed to send")
        return
    
    # This would be called by an event normally, but I want to force it here
    receiveA = await tokenA.CheckMail()
    receiveB = await tokenB.CheckMail()
    """receiveA, receiveB = await asyncio.gather(
        tokenA.CheckMail(),
        tokenB.CheckMail()
    )"""
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
    
    disconnectA = await tokenA.Disconnect()
    disconnectB = await tokenB.Disconnect()
    """await asyncio.gather(
        tokenA.Disconnect(),
        tokenB.Disconnect()
    )"""


if __name__ == "__main__":
    
    asyncio.run(main(),debug=debug)
