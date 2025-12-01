from abc import ABC, abstractmethod
from claybird.core.dependency_container import DependencyContainer

class ConnectionHandlerInterface:

    def __init__(self, container: DependencyContainer):
        self.container = container

    @abstractmethod
    async def start_connection(self) -> dict:
        pass

    @abstractmethod
    async def get_engine_implementation(self, connection: dict, interface):
        pass