# -*- coding: utf-8 -*-

class RecieveEvent():  
    #delegate RecieveHandler(mail)
    handlers = list()
    
    def Invoke(self, mail):
        for handler in self.handlers:
            handler(mail)
            
    def __call__(self, mail):
        self.Invoke(mail)
    
    def AddListener(self, handler):
        self.handlers.Add(handler)
        
    def RemoveListener(self, handler):
        self.handlers = [item for item in self.handlers if item != handler]
    
    def Clear(self):
        self.handlers = list()