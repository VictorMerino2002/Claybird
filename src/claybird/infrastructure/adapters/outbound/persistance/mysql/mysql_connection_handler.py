from claybird.application.ports.outbound.connection_handler_port import ConnectionHandlerPort
from claybird.application.ports.outbound.crud_repository_port import CrudRepositoryPort


class MysqlConnectionHandler(ConnectionHandlerPort):

    async def start_connection(self, definition: dict) -> dict:
        import aiomysql

        connection = {
            "engine": definition.get("engine"),
            "host": definition.get("host"),
            "port": int(definition.get("port")),
            "user": definition.get("user"),
            "password": definition.get("password"),
            "schema": definition.get("schema"),
        }

        if not all([
            connection["host"],
            connection["port"],
            connection["user"],
            connection["password"],
            connection["schema"],
        ]):
            raise ValueError("Invalid MySQL connection definition")

        connection["pool"] = await aiomysql.create_pool(
            host=connection["host"],
            port=connection["port"],
            user=connection["user"],
            password=connection["password"],
            db=connection["schema"],
            autocommit=True,
        )

        return connection

    async def get_engine_adapter(self, connection: dict, port: type):
        pool = connection.get("pool")
        if pool is None:
            raise ValueError("MySQL pool not initialized")

        if port is CrudRepositoryPort:
            from claybird.infrastructure.adapters.outbound.persistance.mysql.mysql_crud_repository import MysqlCrudRepository
            return MysqlCrudRepository(pool)

        raise KeyError(
            f"{port.__name__} is not implemented for MySQL engine"
        )