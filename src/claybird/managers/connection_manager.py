from claybird.core.dependency_container import DependencyContainer
from claybird.core.repositories.crud_repository_interface import CrudRepositoryInterface
from claybird.core.repositories.mysql_crud_repository import MysqlCrudRepository
from claybird.managers.settings_manager import SettingsManager
from claybird.managers.connection_handlers.mysql_connection_manager import MysqlConnectionHandler
from claybird.managers.connection_handlers.connection_handler_interface import ConnectionHandlerInterface

class ConnectionManager:

    handlers = {
        "mysql": MysqlConnectionHandler
    }

    @staticmethod
    async def load_connection_from_settings(container: DependencyContainer):
        settings = SettingsManager.get_settings()
        if not hasattr(settings, "CONNECTIONS"):
            return
        for name, definition in settings.CONNECTIONS.items():
            await ConnectionManager.load_connection(name, definition, container)

    @staticmethod
    async def load_connection(name: str, definition: dict, container: DependencyContainer):
        engine = definition.get("engine", None)
        if engine is None:
            raise KeyError("engine key not set")
        handler = ConnectionManager.get_handler(engine, container)
        connection = await handler.start_connection(definition)
        container.register(f"{name}_connection", connection)

    @staticmethod
    def get_handler(engine: str, container: DependencyContainer) -> ConnectionHandlerInterface:
        handler_cls = ConnectionManager.handlers.get(engine, None)
        if handler_cls is None:
            raise NameError(f"{engine} is not a valid engine")
        return handler_cls(container)

    @staticmethod
    async def get_engine_implementation(connection_name: str, interface, container: DependencyContainer):
        connection = container.get(f"{connection_name}_connection")
        handler = ConnectionManager.get_handler(connection["engine"], container)
        return await handler.get_engine_implementation(connection, interface)