# Main/Signal/Ratchet/RatchetedToken.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import List, Any
from Interfaces.INetwork import INetworkToken, CommandResult, Status
from Main.Signal.NetworkCommand import NetworkCommand
from Main.Signal.Ratchet.IRatchet import IRatchet

class RatchetedToken(INetworkToken):
    """
    Wraps an INetworkToken and encrypts/decrypts NetworkCommand payloads
    using an IRatchet instance.
    """

    def __init__(self, inner_token: INetworkToken, ratchet: IRatchet):
        super().__init__()
        self._inner = inner_token
        self._ratchet = ratchet
        # propagate userId if available
        self.userId = getattr(inner_token, "userId", None)

    # ------------------------------------------------------
    # Low-level send: encrypt a NetworkCommand's serialized payload
    # ------------------------------------------------------
    async def _Send(self, command: NetworkCommand) -> CommandResult:
        """
        Expectation:
         - command is a NetworkCommand whose payload fields are the plaintext.
         - We'll serialize the whole command as JSON string, encrypt it, and
           send a wrapper network command "Encrypted" with ciphertext & header.
        """
        # Serialize entire command to JSON string
        serialized = command.Serialize()

        send_data = IRatchet.SendData(plaintext=serialized, command_type=command.Operation())
        enc = self._ratchet.Send(send_data)

        wrapper = NetworkCommand("Encrypted").With("ciphertext", enc.ciphertext).With("header", enc.header)

        # send via inner token
        return await self._inner._Send(wrapper)

    # ------------------------------------------------------
    # Low-level receive: decrypt any Encrypted commands returned
    # ------------------------------------------------------
    async def _Receive(self) -> list[NetworkCommand]:
        """
        Calls inner._Receive() which should return list[NetworkCommand] or a CommandResult.
        To be tolerant, handle both styles:
          - If inner._Receive returns CommandResult with reply containing commands,
            try to extract.
          - If returns list of NetworkCommand, treat directly.
        """
        inner_result = await self._inner._Receive()

        # If the inner returns a CommandResult-like object (status + reply)
        if isinstance(inner_result, CommandResult):
            # expecting reply to be a NetworkCommand or list
            if inner_result.status != Status.Success:
                return inner_result
            payload = inner_result.reply
            # If reply contains "inbox" list of dict items (older mock), attempt extraction:
            if hasattr(payload, "Get") and payload.Contains("inbox"):
                inbox = payload.Get("inbox") or []
                out = []
                for item in inbox:
                    # Legacy server stores {sender, receiver, message}
                    if isinstance(item, dict) and "message" in item:
                        # create synthetic NetworkCommand with message
                        nc = NetworkCommand("Mail").With("sender", item.get("sender")).With("receiver", item.get("receiver")).With("message", item.get("message"))
                        out.append(nc)
                return out
            # else fall through
            return []
        # If the inner returned a list of commands:
        commands: List[NetworkCommand] = inner_result if isinstance(inner_result, list) else []
        output: List[NetworkCommand] = []
        for cmd in commands:
            if cmd.Is("Encrypted"):
                ciphertext = cmd.Get("ciphertext")
                header = cmd.Get("header")
                recv = IRatchet.ReceiveData(ciphertext=ciphertext, header=header, command_type=cmd.Operation())
                dec = self._ratchet.Receive(recv)
                if dec.error is not None:
                    # failed to decrypt: drop or append placeholder
                    continue
                # plaintext is serialized NetworkCommand -> deserialize
                try:
                    original = NetworkCommand.Deserialize(dec.plaintext)
                    output.append(original)
                except Exception:
                    # if cannot deserialize, skip
                    continue
            else:
                # pass-through
                output.append(cmd)

        return output

    # pass-through convenience wrappers
    async def Mail(self, mail):
        # encrypt message only (older pattern)
        wrapper_cmd = NetworkCommand("mail").With("sender", mail.sender).With("receiver", mail.receiver).With("message", mail.message)
        res = await self._Send(wrapper_cmd)
        return res

    async def CheckMail(self):
        # ask inner token for inbox (older pattern)
        cmd = NetworkCommand("Get").With("key", "inbox")
        result = await self._inner._Send(cmd)
        # If result not success, return as-is
        if isinstance(result, CommandResult) and result.status != Status.Success:
            return result
        # Try to extract inbox and decrypt each message
        # Let the caller handle result shape (this matches older mocks)
        return result
