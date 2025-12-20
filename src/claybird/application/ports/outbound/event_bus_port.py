from abc import ABC, abstractmethod

class EventBusPort(ABC):

    @classmethod
    @abstractmethod
    def on(cls):
        """Register an event listener."""
        pass

    @classmethod
    @abstractmethod
    async def emit(cls):
        """Emit an event asynchronously."""
        pass