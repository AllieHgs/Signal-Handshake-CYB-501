from __future__ import annotations
from typing import Optional, List

# FIXED IMPORTS
from Interfaces.INetwork import Status
from Interfaces.INetworkToken import INetworkToken
from ..NetworkCommand import NetworkCommand

from Main.Signal.Ratchet.IRatchet import IRatchet
from Main.Signal.Ratchet.Ratchet import Ratchet



class SignalNetworkDecorator(INetworkToken):
    def __init__(self, inner: INetworkToken):
        self.inner = inner
        self.ratchet: IRatchet = RatchetBuilder().Build()

    async def Send(self, command: NetworkCommand) -> NetworkCommand:
        send_data = IRatchet.SendData()
        send_data.plaintext = command.payload

        encrypted = self.ratchet.Send(send_data)

        cmd_out = NetworkCommand()
        cmd_out.command = command.command
        cmd_out.payload = encrypted.ciphertext

        return await self.inner.Send(cmd_out)

    async def Receive(self) -> List[NetworkCommand]:
        encrypted_cmds = await self.inner.Receive()
        plaintext_cmds: List[NetworkCommand] = []

        for enc in encrypted_cmds:
            recv_data = IRatchet.ReceiveData()
            recv_data.ciphertext = enc.payload

            decrypted = self.ratchet.Receive(recv_data)

            cmd_out = NetworkCommand()
            cmd_out.command = enc.command
            cmd_out.payload = decrypted.plaintext

            plaintext_cmds.append(cmd_out)

        return plaintext_cmds
