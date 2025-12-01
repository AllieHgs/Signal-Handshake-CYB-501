# -*- coding: utf-8 -*-

from __future__ import annotations
from Abstract.Network import Network
from Main.NetworkCommand import NetworkCommand

class RatchetNetwork(Network):
    def __init__(self, network :Network):
        self.network = network
        pass
    
    @Network.sendhandler("mail")
    async def s_mail(self, command):
        return command
    
    @Network.receivehandler("mail")
    async def r_mail(self, command):
        return command
    
    def InitToken(self, token):
        pass