# -*- coding: utf-8 -*-
from __future__ import annotations
from Interfaces.IMail import IMail
from Main.Signal.RatchetHeader import RatchetHeader

class SignalMail(IMail):
    def __init__(self, mail:IMail, ratchetHeader:RatchetHeader=None):
        self.mail = mail
        self.ratchetHeader = ratchetHeader
    
    def Sender(self) -> str:
        return self.mail.sender
    def Reciever(self) -> str:
        return self.mail.receiver
    def Message(self) -> str:
        return self.mail.message
    