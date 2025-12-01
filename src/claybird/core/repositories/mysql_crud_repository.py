from claybird.core.repositories.crud_repository_interface import CrudRepositoryInterface
from aiomysql.pool import Pool
from aiomysql import DictCursor
from claybird.managers.event_manager import EventManager
from claybird.core.models.entity import Entity
from claybird.core.models.fields import Field
from claybird.core.models import field_type
import datetime
import uuid
import decimal
from claybird.utils.text_formatter import camel_to_snake

class MysqlCrudRepository(CrudRepositoryInterface):

    table_name: str = None
    schema: str = None
    entity_cls: Entity

    def __init__(self, pool: Pool):
        self.pool = pool
        self.schema = self.pool._conn_kwargs.get("db")

    @EventManager.on_event("start")
    async def _lazy_init(self):

        if not self.table_name:
            self.table_name = camel_to_snake(self.entity_cls.__name__)
        if not await self.table_exists():
            await self.create_table()

    def get_column_from_field(self, name: str, field: Field) -> str:
        python_type = field.type_

        TYPE_MAP = {
            str: "VARCHAR(255)",
            field_type.TEXT: "LONGTEXT",
            int: "INT",
            float: "FLOAT",
            bool: "BOOL",
            bytes: "BLOB",

            datetime.datetime: "DATETIME",
            datetime.date: "DATE",
            uuid.UUID: "CHAR(36)",
            decimal.Decimal: "DECIMAL(20,6)",
        }

        if isinstance(python_type, type) and issubclass(python_type, enum.Enum):
            enum_values = "', '".join([e.value for e in python_type])  
            column_type = f"ENUM('{enum_values}')"
        else:
            column_type = TYPE_MAP.get(python_type, "VARCHAR(255)")

        parts = [f"`{name}` {column_type}"]

        if field.primary_key:
            parts.append("PRIMARY KEY")

        if field.required:
            parts.append("NOT NULL")

        if field.default is not None:
            default = str(field.default).replace("'", "''")
            parts.append(f"DEFAULT '{default}'")

        return " ".join(parts)

    async def create_table(self):
        fields = self.entity_cls.get_fields()
        columns = []

        for name, field in fields.items():
            columns.append(self.get_column_from_field(name, field))

        query = f"""
            CREATE TABLE `{self.table_name}` (
                {",".join(columns)}
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                await conn.commit()


    async def table_exists(self) -> bool:
        query = """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = %s
              AND table_name = %s
        """

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (self.schema, self.table_name))
                (result,) = await cursor.fetchone()

        return result >= 1

    async def save(self, entity: Entity):
        keys = entity.get_keys()
        values = entity.get_values()

        columns = ", ".join(f"`{k}`" for k in keys)
        placeholders = ", ".join(["%s"] * len(keys))

        update_clause = ", ".join(f"`{k}` = VALUES(`{k}`)" for k in keys)

        query = (
            f"INSERT INTO `{self.table_name}` ({columns}) "
            f"VALUES ({placeholders}) "
            f"ON DUPLICATE KEY UPDATE {update_clause}"
        )

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, values)

    async def get(self, id):
        pk = self.entity_cls.get_primary_key()
        query = f"SELECT * FROM {self.table_name} WHERE {pk} = %s"

        async with self.pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cursor:
                await cursor.execute(query, (id, ))
                entity = await cursor.fetchone()
        if entity is None: return None
        return self.entity_cls(**entity)

    async def delete(self, id):
        pk = self.entity_cls.get_primary_key()
        query = f"DELETE FROM {self.table_name} WHERE {pk} = %s"

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (id, ))

    async def get_all(self):
        query = f"SELECT * FROM {self.table_name}"

        async with self.pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cursor:
                await cursor.execute(query)
                entities = await cursor.fetchall()
        return [self.entity_cls(**e) for e in entities]