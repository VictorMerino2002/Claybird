from abc import ABC, abstractmethod
from claybird.application.ports.outbound.dependency_container_port import DependencyContainerPort

class ConnectionHandlerPort:

    def __init__(self, container: DependencyContainerPort):
        self.container = container

    @abstractmethod
    async def start_connection(self, definition: dict) -> dict:
        pass

    @abstractmethod
    async def get_engine_adapter(self, connection: dict, port):
        pass