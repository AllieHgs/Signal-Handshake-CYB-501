# -*- coding: utf-8 -*-

class MockMessages():
    messages = dict()
    
    def __init__(self, messages):
        self.messages = messages
        
    def From(self, targetId):
        return self.messages[targetId]