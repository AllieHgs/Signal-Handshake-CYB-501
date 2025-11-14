# -*- coding: utf-8 -*-

class Mail():
    message = None
    reciever = None
    sender = None
    
    def __init__(self, sender, reciever, message):
        self.sender = sender
        self.reciever = reciever
        self.message = message
    
    def __init__(self, reciever, message):
        self.reciever = reciever
        self.message = message
        
    def __str__(self):
        return f"Mail\nfrom: {self.sender}\nto: {self.reciever}\nMessage:\n{self.message}\n"

    