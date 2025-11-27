# -*- coding: utf-8 -*-
class Mail:
    def __init__(self, sender, receiver, message):
        self.sender = sender
        self.receiver = receiver
        self.message = message
        
    def __init__(self, receiver, message):
        self.sender = ""
        self.receiver = receiver
        self.message = message
        
    def __str__(self):
        return f"Mail\nfrom: {self.sender}\nto: {self.reciever}\nMessage:\n{self.message}\n"

    def as_dict(self):
        return {
            "sender": self.sender,
            "receiver": self.receiver,
            "message": self.message
        }