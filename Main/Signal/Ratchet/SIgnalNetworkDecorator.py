# -*- coding: utf-8 -*-
# Main/Signal/Ratchet/SignalNetworkDecorator.py
from __future__ import annotations

import json
from typing import List, Optional

from Interfaces.INetwork import INetwork, INetworkToken, Status, CommandResult
from Main.Signal.NetworkCommand import NetworkCommand
from Main.Signal.Ratchet.IRatchet import IRatchet
from Main.Signal.Ratchet.RatchetBuilder import RatchetBuilder


# ------------------------------------------------------------------
# Utility: which operations are considered handshake-related and
# should NOT be encrypted by the decorator.
# ------------------------------------------------------------------
HANDSHAKE_OPERATIONS = {
    "HandshakeHello",
    "HandshakeReply",
    "HandshakeConfirm",
    "HandshakeAck",
    # Keep these lowercase-safe via .Is(...) checks.
}


# ------------------------------------------------------------------
# Token wrapper: encrypts outgoing commands and decrypts incoming.
# Implements the INetworkToken abstract interface (low-level).
# ------------------------------------------------------------------
class RatchetedTokenWrapper(INetworkToken):
    def __init__(self, inner_token: INetworkToken, ratchet: IRatchet):
        """
        inner_token : the actual INetworkToken returned from the network
        ratchet      : an IRatchet-compatible instance (implements Send/Receive)
        """
        super().__init__()
        self._inner = inner_token
        self._ratchet = ratchet

        # propagate essential attributes used by other code (userId, listeners)
        try:
            self.userId = inner_token.userId
        except Exception:
            self.userId = None
        self._receiveHandlers = getattr(inner_token, "_receiveHandlers", set())

    # -------------------------
    # Low-level send (abstract method)
    # -------------------------
    async def _Send(self, command: NetworkCommand) -> CommandResult:
        """
        Encrypt the command payload (except handshake ops) then forward to inner._Send.
        The wrapped command sent to the inner network will be:
            NetworkCommand("Encrypted").With("ciphertext", ...).With("header", ...).With("command_type", ...)
        We try to preserve the original command.Operation() by placing it in header["orig_op"]
        """
        # If this is a handshake op, pass-through unencrypted
        if command.Is_any := False:  # placeholder to help reading — replaced below
            pass

        # handshake check (case-insensitive)
        if command.Operation().lower().startswith("handshake") or any(command.Is(op) for op in HANDSHAKE_OPERATIONS):
            # Forward as-is
            return await self._inner._Send(command)

        # Build plaintext to encrypt.
        # Prefer explicit fields: "message" or "payload", else serialize full command
        if command.Contains("message"):
            plaintext = command.Get("message")
        elif command.Contains("payload"):
            plaintext = command.Get("payload")
        else:
            # fallback: serialize the full NetworkCommand
            plaintext = command.Serialize()

        if isinstance(plaintext, dict):
            plaintext_json = json.dumps(plaintext, separators=(",", ":"), ensure_ascii=False)
        elif isinstance(plaintext, str):
            plaintext_json = plaintext
        else:
            # try to serialize any JSON-serializable object
            plaintext_json = json.dumps(plaintext, default=str, separators=(",", ":"), ensure_ascii=False)

        # Create SendData for ratchet
        send_data = IRatchet.SendData(plaintext=plaintext_json, command_type=command.Operation())

        # Perform ratchet send -> returns ciphertext + header
        send_ret: IRatchet.SendReturnData = self._ratchet.Send(send_data)

        # Build encrypted network command
        enc_cmd = NetworkCommand("Encrypted") \
            .With("ciphertext", send_ret.ciphertext) \
            .With("header", send_ret.header) \
            .With("command_type", send_ret.command_type or command.Operation())

        # Keep original operation name so server / peer can route or inspect if needed
        enc_cmd.With("orig_operation", command.Operation())

        # Send via inner token (low-level)
        return await self._inner._Send(enc_cmd)

    # -------------------------
    # Low-level receive (abstract method)
    # -------------------------
    async def _Receive(self) -> List[NetworkCommand]:
        """
        Pull incoming commands from inner._Receive() and decrypt any Encrypted items.
        Returns a list of NetworkCommand objects (decrypted or passthrough).
        """
        # Depending on underlying token implementation, Receive may be low-level or wrapper.
        # We call the high-level Receive() to be safer: it returns a CommandResult or list depending on implementation.
        incoming = None
        # Try: call low-level _Receive() if exists
        try:
            incoming = await self._inner._Receive()
        except AttributeError:
            # fallback to high-level Receive()
            try:
                incoming = await self._inner.Receive()
            except Exception:
                incoming = []

        # Normalize incoming to a list of NetworkCommand-like objects
        if incoming is None:
            incoming = []
        # If CommandResult-like object returned, try to extract .reply / .inbox
        if isinstance(incoming, CommandResult):
            # attempt to extract reply or inbox
            if hasattr(incoming, "reply") and isinstance(incoming.reply, NetworkCommand):
                incoming = [incoming.reply]
            elif hasattr(incoming, "inbox"):
                incoming = incoming.inbox or []
            else:
                incoming = []

        # If it's a single NetworkCommand, wrap into list
        if isinstance(incoming, NetworkCommand):
            incoming = [incoming]

        out_cmds: List[NetworkCommand] = []

        for cmd in incoming:
            # If it's not a NetworkCommand instance, skip
            if not isinstance(cmd, NetworkCommand):
                out_cmds.append(cmd)
                continue

            # Preserve handshake commands (pass-through)
            if cmd.Operation().lower().startswith("handshake") or any(cmd.Is(op) for op in HANDSHAKE_OPERATIONS):
                out_cmds.append(cmd)
                continue

            # If it's an Encrypted envelope, attempt decryption
            if cmd.Is("Encrypted"):
                ciphertext = cmd.Get("ciphertext", None)
                header = cmd.Get("header", None)
                command_type = cmd.Get("command_type", None)

                recv_data = IRatchet.ReceiveData(ciphertext=ciphertext, header=header, command_type=command_type)
                recv_ret: IRatchet.ReceiveReturnData = self._ratchet.Receive(recv_data)

                if getattr(recv_ret, "error", None):
                    # decryption failed — leave as-is (or attach error)
                    # create a passthrough NetworkCommand that contains the encrypted payload so upper layers can inspect
                    fallback = NetworkCommand("EncryptedFailed") \
                        .With("ciphertext", ciphertext) \
                        .With("header", header) \
                        .With("error", recv_ret.error)
                    out_cmds.append(fallback)
                    continue

                plaintext = recv_ret.plaintext

                # If plaintext is JSON for a serialized NetworkCommand, reconstruct it
                try:
                    candidate = NetworkCommand.Deserialize(plaintext)
                    out_cmds.append(candidate)
                except Exception:
                    # Not JSON serialized NetworkCommand — return a simple payload NetworkCommand
                    simple = NetworkCommand("Decrypted") \
                        .With("payload", plaintext) \
                        .With("command_type", recv_ret.command_type)
                    out_cmds.append(simple)
            else:
                # Non-encrypted command — pass through
                out_cmds.append(cmd)

        return out_cmds

    # ------------------------------------------------------------
    # Convenience high-level wrappers to match older code paths:
    # they call low-level send/receive but keep behavior similar.
    # ------------------------------------------------------------
    async def Send(self, command: NetworkCommand) -> CommandResult:
        """High-level SEND wrapper used by some tests (calls low-level _Send)."""
        return await self._Send(command)

    async def Receive(self) -> List[NetworkCommand]:
        """High-level RECEIVE wrapper used by some tests (calls low-level _Receive)."""
        return await self._Receive()

    # propagate disconnect/listener if inner provides them
    async def Disconnect(self):
        return await getattr(self._inner, "Disconnect")()

    def ReceiveAddListener(self, cb: callable):
        if hasattr(self._inner, "ReceiveAddListener"):
            self._inner.ReceiveAddListener(cb)

    def ReceiveRemoveListener(self, cb: callable):
        if hasattr(self._inner, "ReceiveRemoveListener"):
            self._inner.ReceiveRemoveListener(cb)


# ------------------------------------------------------------------
# Network decorator: wraps an INetwork and returns a ratcheted token
# on Connect()
# ------------------------------------------------------------------
class SignalNetworkDecorator(INetwork):
    def __init__(self, inner_network: INetwork, ratchet_builder: RatchetBuilder):
        super().__init__()
        self._inner = inner_network
        self._ratchet_builder = ratchet_builder

    # pass through other network commands to inner network
    async def _Command(self, commandRequest: NetworkCommand) -> CommandResult:
        return await self._inner._Command(commandRequest)

    async def _Connect(self, userId, password) -> INetwork.ConnectResult:
        """
        Connect using underlying network. If successful, build a ratchet instance
        and wrap the returned token so all payloads are encrypted/decrypted.
        The decorator tries to obtain InitData either from:
          - base_result.reply.ratchet_init (if server includes it)
          - base_result.token.ratchet_init (if token contains it)
          - or uses an empty/default InitData (for local testing)
        """
        base_result = await self._inner._Connect(userId, password)

        # If connect failed, pass it through
        if base_result.status != Status.Success:
            return base_result

        # Try to find initialization data for the ratchet (optional)
        init_data = None
        try:
            # server reply may contain a ratchet_init field (partner's handshake)
            if isinstance(base_result.reply, dict) and "ratchet_init" in base_result.reply:
                init_data = base_result.reply["ratchet_init"]
            elif hasattr(base_result, "reply") and hasattr(base_result.reply, "ratchet_init"):
                init_data = base_result.reply.ratchet_init
        except Exception:
            init_data = None

        # Also try token (some flows place init data into token)
        if init_data is None and hasattr(base_result, "token") and base_result.token is not None:
            init_data = getattr(base_result.token, "ratchet_init", None)

        # Build ratchet using builder API (support multiple builder styles)
        builder = self._ratchet_builder
        ratchet = None
        try:
            # common modern builder: WithInitData(...).Build()
            if hasattr(builder, "WithInitData") and init_data is not None:
                ratchet = builder.WithInitData(init_data).Build()
            elif hasattr(builder, "WithInit") and init_data is not None:
                ratchet = builder.WithInit(init_data).Build()
            elif hasattr(builder, "WithInitData") and init_data is None:
                # create empty default IRatchet.InitData to satisfy builder
                default = IRatchet.InitData()
                ratchet = builder.WithInitData(default).Build()
            elif hasattr(builder, "Build"):
                # some builders allow Build() without init
                ratchet = builder.Build()
            elif hasattr(builder, "build"):
                ratchet = builder.build()
            else:
                raise RuntimeError("RatchetBuilder has no recognized build API")
        except Exception as e:
            # If builder fails, surface a clear error to the caller by returning ConnectResult with Fail
            res = INetwork.ConnectResult()
            res.status = Status.Fail
            # attach debug info for partner / tests
            res.debug = f"Failed to construct ratchet: {e}"
            return res

        # Wrap the returned token and return
        wrapped_token = RatchetedTokenWrapper(base_result.token, ratchet)

        out = INetwork.ConnectResult()
        out.status = base_result.status
        out.token = wrapped_token
        return out

    # Public helpers (pass-through to match old API)
    async def Register(self, userId, password):
        return await self._inner.Register(userId, password)

    async def CheckIdAvalibility(self, userId):
        return await self._inner.CheckIdAvalibility(userId)

    async def Get(self, userId, key):
        return await self._inner.Get(userId, key)

    async def Set(self, userId, key, value):
        return await self._inner.Set(userId, key, value)

    async def Disconnect(self, userId):
        return await self._inner.Disconnect(userId)
