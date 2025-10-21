# -*- coding: utf-8 -*-

from Interfaces.IUser import IUser

class MockUser(IUser):
    def GetMessages(self): 
        return None
    
    def Send(self, mail): #void
        mail.sender = self.ID
        self.network.Send(mail)
    
    def Recieve(self, mail): #void
        print(f"{self.ID} recieved mail from {mail.sender}:\n{mail.message}\n")
        pass