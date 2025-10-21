# -*- coding: utf-8 -*-
"""
Created on Tue Oct 21 08:08:31 2025

@author: 
"""

from Mock.MockNetwork import MockNetwork
from Mock.MockUser import MockUser
from Main.Mail import Mail

def main():
    network = MockNetwork()
    userA = MockUser("mockA", "passA", network)
    userB = MockUser("mockB", "passB", network)
    
    userA.Register()
    userB.Register()
    
    userA.Connect()
    userB.Connect()
    
    mail = Mail("mockB","MessageA2B")
    userA.Send(mail);
    mail = Mail("mockA", "MessageB2A")
    userB.Send(mail);
    
    userA.Disconnect()
    userB.Disconnect()
    
if __name__ == "__main__":
    main()