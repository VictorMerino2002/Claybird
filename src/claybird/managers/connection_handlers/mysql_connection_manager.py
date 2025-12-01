from claybird.managers.connection_handlers.connection_handler_interface import ConnectionHandlerInterface
from claybird.core.repositories.crud_repository_interface import CrudRepositoryInterface

class MysqlConnectionHandler(ConnectionHandlerInterface):

    async def start_connection(self, definition: dict):
        import aiomysql

        connection = {
            "engine": definition.get("engine"),
            "host": definition.get("host"),
            "port": int(definition.get("port")),
            "user": definition.get("user"),
            "password": definition.get("password"),
            "schema": definition.get("schema"),
        }

        if not all([connection["host"], connection["port"], connection["user"], connection["password"], connection["schema"]]):
            raise KeyError("Invalid MySQL connection definition")

        connection["pool"] = await aiomysql.create_pool(
            host=connection["host"],
            port=connection["port"],
            user=connection["user"],
            password=connection["password"],
            db=connection["schema"],
            autocommit=True
        )

        return connection

    async def get_engine_implementation(self, connection: dict, interface):
        pool = connection.get("pool")
        if pool is None:
            raise ValueError("aiomysql Pool not set")
        if interface == CrudRepositoryInterface:
            from claybird.core.repositories.mysql_crud_repository import MysqlCrudRepository
            return MysqlCrudRepository(pool)
        
        raise KeyError(f"{interface} is not implemented for Mysql connection")