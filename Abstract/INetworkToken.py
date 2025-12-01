# Interfaces/INetworkToken.py

from abc import ABC, abstractmethod

class INetworkToken(ABC):
    """
    Represents a raw, unencrypted token passed over the network.
    Your Decorator wraps one of these.
    """

    @abstractmethod
    def get_payload(self) -> bytes:
        pass

    @abstractmethod
    def set_payload(self, payload: bytes):
        pass
