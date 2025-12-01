# -*- coding: utf-8 -*-
from __future__ import annotations
from Abstract.Network import Network
from Main.NetworkCommand import NetworkCommand

from nacl.public import PrivateKey, PublicKey
from nacl.signing import SigningKey, VerifyKey

from Main.Signal.crypto_x3dh import compute_x3dh_shared_secret_initiator
from nacl.secret import SecretBox
from nacl.utils import random


class SignalNetwork(Network):
    def __init__(self, network :Network):
        self.network = network
        pass
    
    
    @Network.sendhandler("mail")
    async def sig_s_mail(self, command):
        recipient = command.Get("receiver")
        
        # if no session, do X3DH
        if recipient not in command.token.sessions:
            bundle_cmd = await self.Send(NetworkCommand("GetPrekeyBundle", userId=recipient))
            
            bundle = bundle_cmd.Get("bundle")
            
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
            command.WithInner("bundle","E", E_pub.encode().hex())
        return command
    
    @Network.receivehandler("mail")
    async def sig_r_mail(self, command):
        sender = command.Get("sender")
        
        # If we don't have a session, derive it from initiator's ephemeral key
        if sender not in command.token.sessions:
            bundle = command.Get("bundle")
            # decode keys
            IK_A = VerifyKey(bytes.fromhex(bundle["IK"]))
            E_A = PublicKey(bytes.fromhex(bundle["E"]))  # ephemeral key from sender
            
            master_secret = compute_x3dh_shared_secret_initiator(
                IK_B=command.token.IK_priv.to_curve25519_private_key(),
                SPK_B=command.token.SPK_priv,
                IK_A=IK_A.to_curve25519_public_key(),
                E_A=E_A
            )
            
            command.token.sessions[sender] = master_secret
    
        # Decrypt message
        key = command.token.sessions[sender][:32]
        box = SecretBox(key)
        decrypted = box.decrypt(bytes.fromhex(command.Get("message")))
        command.With("message", decrypted.decode())
        return command
    
    @Network.replyhandler("register")
    async def p_register(self, command):
        await command.token.PublishKeyBundle()
        pass

    class Token(Network.Token):
        def __init__(self, network: Network, **kwargs):
            super().__init__(network, **kwargs)
            self.IK_priv = SigningKey.generate()      # Ed25519 signing key (identity)
            self.IK_pub = self.IK_priv.verify_key
            self.SPK_priv = PrivateKey.generate()     # X25519 ephemeral signed prekey
            self.SPK_pub = self.SPK_priv.public_key
            self.SPK_signature = self.IK_priv.sign(self.SPK_pub.encode())  # sign SPK
            self.OPKs = [PrivateKey.generate() for _ in range(5)]  # optional prekeys
            self.OPKs_pub = [k.public_key for k in self.OPKs]
            
            # Sessions with peers: peer_id -> master secret
            self.sessions = {}
        
        def KeyBundle(self):
            return {
                "IK": self.IK_pub.encode().hex(),
                "SPK": self.SPK_pub.encode().hex(),
                "SPK_sig": self.SPK_signature.hex(),
                "OPKs": [k.encode().hex() for k in self.OPKs_pub]
            }
    
        async def PublishKeyBundle(self):
            pub_keys = self.KeyBundle()
            command = NetworkCommand().With("pub_keys",pub_keys)
            return await self.Send(command)
    
        
        