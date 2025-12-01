from claybird.core.dependency_container import DependencyContainer
from claybird.core.repositories.crud_repository_interface import CrudRepositoryInterface
from claybird.core.repositories.mysql_crud_repository import MysqlCrudRepository
from claybird.managers.settings_manager import SettingsManager

class ConnectionManager:

    @staticmethod
    async def load_connection_from_settings(container: DependencyContainer):
        settings = SettingsManager.get_settings()
        if not hasattr(settings, "CONNECTION"):
            return
        connection_definition = settings.CONNECTION
        await ConnectionManager.load_connection(connection_definition, container)

    @staticmethod
    async def load_connection(definition: dict, container: DependencyContainer):
        engine = definition["engine"]
        handler_name = f"handle_{engine}"

        if not hasattr(ConnectionManager, handler_name):
            raise KeyError(f"Connection Engine '{engine}' is not valid")
        
        handler = getattr(ConnectionManager, handler_name)
        await handler(definition, container)

    @staticmethod
    async def handle_mysql(definition: dict, container: DependencyContainer):
        import aiomysql

        host = definition.get("host")
        port = definition.get("port")
        user = definition.get("user")
        password = definition.get("password")
        schema = definition.get("schema")

        if not all([host, port, user, password, schema]):
            raise KeyError("Invalid MySQL connection definition")

        pool = await aiomysql.create_pool(
            host=host,
            port=int(port),
            user=user,
            password=password,
            db=schema,
            autocommit=True
        )

        container.register(aiomysql.Pool, pool)
        container.register(
            CrudRepositoryInterface,
            lambda: MysqlCrudRepository(container.get(aiomysql.Pool))
        )