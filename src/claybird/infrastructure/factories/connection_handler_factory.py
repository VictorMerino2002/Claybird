from claybird.application.ports.outbound.connection_handler_port import ConnectionHandlerPort
from claybird.application.ports.outbound.dependency_container_port import DependencyContainerPort
from claybird.infrastructure.adapters.outbound.persistance.mysql.mysql_connection_handler import MysqlConnectionHandler

class ConnectionHandlerFactory:

    _handlers = {
        "mysql": MysqlConnectionHandler
    }

    def __init__(self, container: DependencyContainerPort):
        self.container = container

    def get_handler(self, engine: str) -> ConnectionHandlerPort:
        handler = self._handlers.get(engine, None)
        if handler is None:
            raise KeyError(f"{engine} is not a valid engine")
        return handler(self.container)