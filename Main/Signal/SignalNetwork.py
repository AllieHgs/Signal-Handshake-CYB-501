# -*- coding: utf-8 -*-
from __future__ import annotations
from Abstract.Network import Network
from Main.NetworkCommand import NetworkCommand

from nacl.public import PrivateKey, PublicKey
from nacl.signing import SigningKey, VerifyKey

from Main.Signal.crypto_x3dh import compute_x3dh_shared_secret_initiator, compute_x3dh_shared_secret_responder
from nacl.secret import SecretBox
from nacl.utils import random


class SignalNetwork(Network):
    
    @Network.sendhandler("mail")
    async def s_mail(self, command):
        recipient = command.Get("receiver")
        
        # if no session, do X3DH
        if recipient not in command.token.sessions:
            bundle_cmd = await self.Send(NetworkCommand("GetPrekeyBundle", userId=recipient))
            bundle = bundle_cmd.reply.Get("bundle")
            
            # decode keys from hex
            IK_B = VerifyKey(bytes.fromhex(bundle["IK"]))
            SPK_B = PublicKey(bytes.fromhex(bundle["SPK"]))
            SPK_sig = bytes.fromhex(bundle["SPK_sig"])
            # TODO: OPKs if used
            # verify SPK signature
            IK_B.verify(SPK_B.encode(), SPK_sig)
            
            # ephemeral key
            E_priv = PrivateKey.generate()
            E_pub = E_priv.public_key
            
            master_secret = compute_x3dh_shared_secret_initiator(
                IK_A=command.token.IK_priv.to_curve25519_private_key(),
                SPK_B=SPK_B,
                IK_B=IK_B.to_curve25519_public_key(),
                E_A=E_priv,
            )
            
            command.token.sessions[recipient] = master_secret
            # encrypt message
            key = master_secret[:32]  # first 32 bytes
            box = SecretBox(key)
            ciphertext = box.encrypt(command.Get("message").encode())
            command.With("message", ciphertext.hex())
        
        return command
    
    @Network.receivehandler("mail")
    async def r_mail(self, command):
        sender = command.Get("sender")
        if sender not in self.sessions:
            master_secret = compute_x3dh_shared_secret_responder(
                IK_B=self.IK_priv.to_curve25519_private_key(),
                SPK_B=self.SPK_priv,
                OPK_B=None,  # optional
                IK_A=PublicKey(bytes.fromhex(command.Get("IK_A"))),
                E_A=PublicKey(bytes.fromhex(command.Get("E_A"))),
            )
            self.sessions[sender] = master_secret
            
            key = master_secret[:32]
            box = SecretBox(key)
            ciphertext = bytes.fromhex(command.Get("message"))
            plaintext = box.decrypt(ciphertext).decode()
            command.With("message", plaintext)
        
        return command
        
    @Network.replyhandler("register")
    async def p_register(self, command):
        if command.IsFailed(): return command
        print()
        bundle = await command.token.PublishKeyBundle()
        return command
    
    
    def InitToken(self, token):
        token.IK_priv = SigningKey.generate()      # Ed25519 signing key (identity)
        token.IK_pub = token.IK_priv.verify_key
        token.SPK_priv = PrivateKey.generate()     # X25519 ephemeral signed prekey
        token.SPK_pub = token.SPK_priv.public_key
        token.SPK_signature = token.IK_priv.sign(token.SPK_pub.encode())  # sign SPK
        token.OPKs = [PrivateKey.generate() for _ in range(5)]  # optional prekeys
        token.OPKs_pub = [k.public_key for k in token.OPKs]
        
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
            bundle = self.KeyBundle()
            command = NetworkCommand("PublishKeyBundle").With("bundle", bundle).With("userId", token.Get("userId"))
            return await self.Send(command)
        Network.Token.PublishKeyBundle = PublishKeyBundle

        
        
    
        
    
        
        