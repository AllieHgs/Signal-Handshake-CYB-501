# -*- coding: utf-8 -*-
from Interfaces.IMail import IMail

class Mail(IMail):
    message = None
    reciever = None
    sender = None
    
    def __init__(self, sender, receiver, message):
        self.sender = sender
        self.receiver = receiver
        self.message = message
    
    def __init__(self, reciever, message):
        self.reciever = reciever
        self.message = message
        
    def __str__(self):
        return f"Mail\nfrom: {self.sender}\nto: {self.reciever}\nMessage:\n{self.message}\n"

    def Sender(self) -> str:
        return self.sender
    def Reciever(self) -> str:
        return self.receiver
    def Message(self) -> str:
        return self.message
    