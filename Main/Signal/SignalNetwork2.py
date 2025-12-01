# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
from __future__ import annotations
from Abstract.Network import Network
from Main.NetworkCommand import NetworkCommand
from Main.Signal.SignalProtocol import SignalProtocol

class SignalNetwork1(Network):
    def __init__(self, network :Network):
        self.network = network
        self.protocol = SignalProtocol()
        pass
    
    
    @Network.sendhandler("mail")
    async def s_mail(self, command):
        receiver = command.Get("receiver", None)
        if receiver is None : return command.Fail()
        if command.token.sessions.contains(receiver):
            pass
        return command
    
    @Network.receivehandler("mail")
    async def r_mail(self, command):
        
        return command
    
    @Network.replyhandler("register")
    async def p_register(self, command):
        await command.token.PublishKeyBundle()
        pass
    
    
    def InitToken(self, token):
        ik_priv, ik_pub = self.protocol.GenerateKeyPair()
        token.With("ik_priv", ik_priv) # Ed25519 signing key (identity)
        token.With("ik_pub", ik_pub)
        spk_priv, spk_pub = self.protocol.GenerateKeyPair()
        token.With("spk_priv", spk_priv) # X25519 ephemeral signed prekey
        token.With("spk_pub", spk_pub)
        token.With("opks", self.protocol.GenerateKeyPairs(5))
        
        # Sessions with peers: peer_id -> master secret
        token.sessions = {}
        
        def KeyBundle(self):
            return {
                "IK": self.IK_pub.encode().hex(),
                "SPK": self.SPK_pub.encode().hex(),
                "SPK_sig": self.SPK_signature.hex(),
                "OPKs": [k.encode().hex() for k in self.OPKs_pub]
            }
        Network.Token.KeyBundle = KeyBundle
        
        async def PublishKeyBundle(self):
            pub_keys = self.KeyBundle()
            command = NetworkCommand("PublishKeyBundle").With("pub_keys",pub_keys)
            return await self.Send(command)
        Network.Token.PublishKeyBundle = PublishKeyBundle

        
        
    
        
    
        
        