# -*- coding: utf-8 -*-

from Interfaces.INetwork import INetwork
from Main.RecieveEvent import RecieveEvent

class MockNetwork(INetwork):
    recieveEvent = RecieveEvent()
    users = dict()
    
    def Send(self, mail):
        print(f"Mock sending Message\nfrom: {mail.sender}\nto: {mail.reciever}\nMessage:\n{mail.message}\n");
        self.users[mail.reciever].Recieve(mail)
        pass
    
    def GetRecieveEvent(self, ID):
        return self.recieveEvent
    
    def CheckIdAvalibility(self, ID):
        return ID not in self.users
    
    def Register(self, user) -> bool():
        pass
    
    def Connect(self, user):
        self.users[user.ID] = user
        return True
    
    def Disconnect(self, user):
        del self.users[user.ID]