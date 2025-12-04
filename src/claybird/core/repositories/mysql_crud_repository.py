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
        
    async def save_batch(self, entities: list[Entity]):
        if not entities:
            return

        pk = self.entity_cls.get_primary_key()
        keys = entities[0].get_keys()
        columns = ", ".join(f"`{k}`" for k in keys)

        placeholders = ", ".join(["%s"] * len(keys))

        value_groups = ", ".join(f"({placeholders})" for _ in entities)

        values = [value for e in entities for value in e.get_values()]

        update_keys = [k for k in keys if k != pk]
        update_clause = ", ".join(f"`{k}` = VALUES(`{k}`)" for k in update_keys)

        query = (
            f"INSERT INTO `{self.table_name}` ({columns}) "
            f"VALUES {value_groups} "
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

    def __getattr__(self, name):
        """
        Crea métodos dinámicos tipo Spring Data JPA:
        find_by_field, find_by_field1_and_field2, delete_by_field, etc.
        """
        patterns = [
            ("find_by_", "find"),
            ("get_by_", "find"),
            ("count_by_", "count"),
            ("delete_by_", "delete"),
        ]

        for prefix, action in patterns:
            if name.startswith(prefix):
                query_fields = name[len(prefix):]
                return self._build_dynamic_method(action, query_fields)

        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")


    def _build_dynamic_method(self, action, query_fields_raw):
        import re

        parts = re.split(r"_and_|_or_", query_fields_raw)
        connectors = re.findall(r"_and_|_or_", query_fields_raw)

        conditions = []

        for part in parts:
            op = "="

            if part.endswith("_less_than"):
                field = part[:-11]
                op = "<"

            elif part.endswith("_greater_than"):
                field = part[:-14]
                op = ">"

            elif part.endswith("_before"):
                field = part[:-7]
                op = "<"

            elif part.endswith("_after"):
                field = part[:-6]
                op = ">"

            elif part.endswith("_like"):
                field = part[:-5]
                op = "LIKE"

            elif part.endswith("_not_like"):
                field = part[:-9]
                op = "NOT LIKE"

            elif part.endswith("_starts_with"):
                field = part[:-13]
                op = "LIKE_START"

            elif part.endswith("_ends_with"):
                field = part[:-11]
                op = "LIKE_END"

            else:
                field = part

            conditions.append((field, op))

        async def method(*values):
            if len(values) != len(conditions):
                raise ValueError("Argument count does not match dynamic query definition")

            where_clauses = []
            params = []

            for (field, op), value in zip(conditions, values):

                if op == "LIKE":
                    where_clauses.append(f"`{field}` LIKE %s")
                    params.append(f"%{value}%")

                elif op == "NOT LIKE":
                    where_clauses.append(f"`{field}` NOT LIKE %s")
                    params.append(f"%{value}%")

                elif op == "LIKE_START":
                    where_clauses.append(f"`{field}` LIKE %s")
                    params.append(f"{value}%")

                elif op == "LIKE_END":
                    where_clauses.append(f"`{field}` LIKE %s")
                    params.append(f"%{value}")

                else:
                    where_clauses.append(f"`{field}` {op} %s")
                    params.append(value)

            sql_where = where_clauses[0]
            for cond, conn in zip(where_clauses[1:], connectors):
                sql_where += f" {'AND' if '_and_' in conn else 'OR'} {cond}"

            if action == "find":
                sql = f"SELECT * FROM `{self.table_name}` WHERE {sql_where}"

            elif action == "count":
                sql = f"SELECT COUNT(*) AS count FROM `{self.table_name}` WHERE {sql_where}"

            elif action == "delete":
                sql = f"DELETE FROM `{self.table_name}` WHERE {sql_where}"

            async with self.pool.acquire() as conn:
                async with conn.cursor(DictCursor) as cursor:
                    await cursor.execute(sql, params)

                    if action == "find":
                        rows = await cursor.fetchall()
                        return [self.entity_cls(**r) for r in rows]

                    if action == "count":
                        result = await cursor.fetchone()
                        return result["count"]

                    if action == "delete":
                        return cursor.rowcount

        return method