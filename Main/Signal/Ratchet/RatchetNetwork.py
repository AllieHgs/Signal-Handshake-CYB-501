# -*- coding: utf-8 -*-

from __future__ import annotations
from Abstract.Network import Network
from Main.NetworkCommand import NetworkCommand
from Main.Signal.Ratchet.Ratchet import Ratchet
from Main.Signal.Ratchet.IRatchet import IRatchet
import Main.Signal.crypto_x3dh as x3dh

class RatchetNetwork(Network):
    
    @Network.sendhandler("mail")
    async def s_mail(self, command):
        
        if not hasattr(command.token, "ratchet"):
            command.token = self.buildRatchet(command)

        class SendReturnData:
            def __init__(self):
                self.ciphertext = None
                self.header = None
                self.command_type = None
        dataIn = IRatchet.SendData(
            plaintext = command.Get("message", ""),
            command_type = command.Get("ratchet_command_type", "MESSAGE")
            )
        
        dataOut = await command.token.ratchet.Send(dataIn)
        
        command.Without("message")
        command.With("ratchet_ciphertext", dataOut.ciphertext) # (bytes or base64)
        command.With("ratchet_header", dataOut.header) # (dict of ratchet metadata)
        command.With("ratchet_command_type", dataOut.commandType)
        
        return command
    
    @Network.receivehandler("mail")
    async def r_mail(self, command):
        dataIn = IRatchet.ReceiveData(
            ciphertext = command.Get("ratchet_ciphertext"),
            header = command.Get("ratchet_header"),
            command_type = command.Get("ratchet_command_type", "MESSAGE")
            )
        
        dataOut = command.token.ratchet()
        
        command.With("message", dataOut.plaintext)
        command.With("ratchet_command_type", dataOut.command_type)
        command.With("ratchet_error", dataOut.error)
        
        return command
    
    def init_ratchet_responder(
            ik_priv, #other
            spk_priv, #other
            ik_pub, #self
            e_pub, #self
            opk = None #self
            ):
        #sk = x3dh.compute_x3dh_shared_secret_initiator(ik_a_priv, e_a_priv, ik_b_pub_bytes, spk_b_pub_bytes)
        #sk = x3dh.compute_x3dh_shared_secret_initiator(ik_priv, e_priv, ik_pub, spk_pub)
        
        #info = ""
        #root_key = Ratchet.hkdf(self, sk, info)
        
        
        pass
    def init_ratchet_initiator(
            ik_priv, #self
            e_priv, #self
            spk_pub, #other
            ik_pub, #other
            opk_pub = None, #other
            ):
        pass
        
    def InitToken(self, token):
        initData = IRatchet.InitData(
            root_key = None, # bytes | str = "",
            dh_self_priv = token.IK_priv.encode().hex(), # bytes | str = "",
            dh_self_pub = token.IK_pub.encode().hex(), # bytes | str = "",
            dh_remote_pub = None, # bytes | str = "",
            send_chain_key = None, # bytes | str = "",
            recv_chain_key = None, # bytes | str = ""
        )
        token.ratchet = Ratchet(initData)
        return token