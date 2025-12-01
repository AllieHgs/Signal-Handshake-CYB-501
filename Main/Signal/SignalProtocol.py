# -*- coding: utf-8 -*-
"""
from Main.NetworkCommand import NetworkCommand, Status

import crypto_x3dh as x3dh


class SignalProtocol:
    def __init__(self, network):
        self.network = network
    
    async def EstablishSessionOnSend(self, token, sender, receiver):
        
        command = await self.GetKeyBundle(token, receiver)
        keys = command.Get("keys")
        IKb = keys.get("ik", None)
        SPKb = keys.get("spk", None)
        SIGb = keys.get("sig", None)
        OPKb = keys.get("opk", None)
        if IKb is None or SPKb is None or OPKb is None:
            return command.Fail()
        
        IKa = None
        EKa = None
        
        DH1 = self.DH(IKa, SPKb)
        DH2 = self.DH(EKa, IKb)
        DH3 = self.DH(EKa, SPKb)
        if OPKb is not None:
            DH4 = self.DH(EKa, OPKb)
            SK = self.KDF(DH1, DH2, DH3, DH3)
        else:
            SK = self.KDF(DH1, DH2, DH3)
        sharedSecret = receiver + "secret" 
        token.sessions[receiver] = sharedSecret
        AD = self.concat(IKa,IKb)
        del EKa
        token.sessions[receiver] = (AD, )
        return command.Complete()
    
    def GenerateIK(self):
        priv = Ed25519PrivateKey().generate()
        return priv, priv.public_key()
    def GenerateSPK(self):
        priv = X25519PrivateKey.generate()
        return priv, priv.public_key()
    
    def CalculateSig(ik_priv, spk_pub):
        spk_bytes = spk_pub.public_bytes(
            encoding = serialization.Encoding.Raw,
            format = serialization.PublicFormat.Raw
            )
        
        
        
        
        
        priv_pem = priv.private_bytes(
            encoding=serialization.Encoding.PEM, 
            format=serialization.PrivateFormat.PKCS8, 
            #Probably should .BestAvailableEncryption(user's password) for better security
            encryption_algorithm=serialization.NoEncryption())
        pub_pem = priv.private_bytes(
            encoding=serialization.Encoding.PEM, 
            format=serialization.PrivateFormat.PKCS8)
        return (priv_pem, pub_pem)

    def GenerateKeyPairs(self, count = 5):
        opks = []
        for i in range(0,count):
            opks.append(self.GenerateKeyPair())
        return opks
    
    
    async def SendIdentityKey(self, token) -> NetworkCommand:
        command = NetworkCommand("ik").WithToken(token)
        token.With("ik", token.Get("ik_pub"))
        return await self.network.Send(command)
    
    async def SendSignedPreKey(self, token) -> NetworkCommand:
        command = NetworkCommand("spk")
        command.With("spk", token.Get("spk_pub"))
        return await self.network.Send(command)
    
    async def SendOneTimePreKeys(self, token, count = 2) -> NetworkCommand:
        command = NetworkCommand("opk").WithToken(token)
        opks = token.Get("opks", None) or self.GenerateOneTimePreKeys(count)
        token.kwargs.setdefault("opks", list())
        token.kwargs["opks"].extend(opks)
        command.With("opks", opks)
        return await self.network.Send(command)
    
    async def SendKeyBundle(self, token) -> Status:
        sendIK = await self.SendIdentityKey(token)
        sendSPK = await self.SendSignedPreKey(token)
        await self.SendOneTimePreKeys(token)
        return Status.Success if sendIK.IsSuccess() and sendSPK.IsSuccess() else Status.Fail
    
    async def GetKeyBundle(self, token, userId) -> NetworkCommand:
        command = NetworkCommand("getkeys")
        
        return await self.network.Send(command)
    
    def DH(self, keyA, keyB):
        return
    def Sig(self, ik_pub, SPK):
        return
    def KDF(self, SK, token):
        return
    
    def concat(self, keyA, keyB):
        return 
    
    def HKDF(self, token):
        return
    def HKDFsalt(self, token):
        return
    def HKDFinfo(self, token):
        return
    
    #X25519
    def _encode(self, value):
        return
    
    #SHA-512
    def _hash(self, value):
        return
"""