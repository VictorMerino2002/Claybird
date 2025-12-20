from abc import ABC, abstractmethod

class ServerPort(ABC):

    @abstractmethod
    async def run(self, app, host, port):
        pass