from Main.Signal.Ratchet.IRatchet import IRatchet


class Ratchet(IRatchet):
    def __init__(self, data : IRatchet.InitData):
        super().__init__(data)
        # Additional Initialization
        
        pass
    
    def Send(self, data :IRatchet.SendData) -> IRatchet.SendReturnData:
        result = IRatchet.SendReturnData()
        # Encoding
        
        
        return result
    
    def Receive(self, data : IRatchet.ReceiveData) -> IRatchet.ReceiveReturnData:
        result = IRatchet.ReceiveReturnData()
        # Decoding
        
        
        return result