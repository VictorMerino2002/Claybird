from claybird.application.ports.outbound.dependency_container_port import DependencyContainerPort
from claybird.infrastructure.factories.connection_handler_factory import ConnectionHandlerFactory

class ConnectionsBootstrap:

    def __init__(self, container: DependencyContainerPort):
        self.container = container
        self.connection_handler_factory = ConnectionHandlerFactory(container)

    async def load_connections_from_settings(self):
        settings = self.container.get("settings")
        for name, definition in settings.CONNECTIONS.items():
            await self.load_connection(name, definition)
    
    async def load_connection(self, name: str, definition: dict):
        engine = definition.get("engine", None)
        if engine is None:
            raise ValueError(f"Connection '{name}' has no engine configured")
        handler = self.connection_handler_factory.get_handler(engine)
        connection = await handler.start_connection(definition)
        self.container.register(f"{name}_connection", connection)