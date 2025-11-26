# -*- coding: utf-8 -*-
from __future__ import annotations
from abc import ABC, abstractmethod
from Main.NetworkCommand import NetworkCommand

class IRatchet(ABC):
    """ Modify
    the data classes' __init__ functions 
    to be initialized with any data that you need for the function.
    Please use typehints.
    Note: The data types must be json serializable.
    """
    class InitData: # Data needed to initalize
        def __init__(self):
            pass
    class SendData: # Input data for Send (Encoding)
        def __init__(self):
            pass
    class SendReturnData: # Output data for Send (Encoded)
        def __init__(self):
            pass
    class ReceiveData: # Input data for Receive (Decoding)
        def __init__(self):
            pass
    class ReceiveReturnData: # Output data for Receive (Decoded)
        def __init__(self):
            pass
    
    """ Don't Modify past this """
    
    #Abstract constructor
    def  __init__(self, data :InitData):
        self.data = data
        
    @abstractmethod
    def Send(self, data :SendData) -> SendReturnData: #Encodes
        pass
    
    @abstractmethod
    def Receive(self, data :ReceiveData) -> ReceiveReturnData: #Decodes
        pass
    
