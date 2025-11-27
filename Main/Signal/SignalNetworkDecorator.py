# -*- coding: utf-8 -*-
from Interfaces.INetwork import Status
from Main.Signal.Ratchet.IRatchet import IRatchet
from Main.Signal.Ratchet.Ratchet import Ratchet

class SignalNetworkDecorator:
    """
    Decorates a network so all NetworkCommand.payload fields
    are encrypted/decrypted by an IRatchet implementation.
    """

    def __init__(self, network, ratchet_builder):
        self.network = network
        self.ratchet_builder = ratchet_builder
        self.tokens = {}  # username -> ratchet instance

    async def Register(self, username: str, password: str):
        return await self.network.Register(username, password)

    async def Connect(self, username: str, password: str):
        """
        Connects to the underlying network and wraps the returned token
        with a ratcheted token wrapper so all Send/Receive calls
        use the Double Ratchet transparently.
        """
        result = await self.network.Connect(username, password)

        if result.status == Status.Ok:
            ratchet_instance = self.ratchet_builder.build()

            # Wrap INetworkToken with a ratcheted version
            result.token = RatchetedTokenWrapper(result.token, ratchet_instance)

            self.tokens[username] = ratchet_instance

        return result


class RatchetedTokenWrapper:
    """
    Wraps an INetworkToken so:
        Send() → Ratchet.Send() → encrypted payload
        Receive() → Ratchet.Receive() → decrypted payload
    """

    def __init__(self, inner_token, ratchet: IRatchet):
        self.inner_token = inner_token
        self.ratchet = ratchet

    async def Send(self, command):
        """
        Take NetworkCommand and encrypt its payload using Ratchet.Send()
        """
        # Build SendData
        send_data = IRatchet.SendData()
        send_data.plaintext = command.payload  # must be JSON-serializable

        # Get encrypted result
        result: IRatchet.SendReturnData = self.ratchet.Send(send_data)

        # Replace payload with ciphertext
        command.payload = result.ciphertext

        # Send encrypted command over network
        return await self.inner_token.Send(command)

    async def Receive(self):
        """
        Receive from network, decrypt all command.payload items.
        """
        response = await self.inner_token.Receive()

        if response.status != Status.Ok:
            return response

        for cmd in response.inbox:
            recv_data = IRatchet.ReceiveData()
            recv_data.ciphertext = cmd.payload

            # Decrypt
            result: IRatchet.ReceiveReturnData = self.ratchet.Receive(recv_data)

            cmd.payload = result.plaintext

        return response

    async def Disconnect(self):
        return await self.inner_token.Disconnect()