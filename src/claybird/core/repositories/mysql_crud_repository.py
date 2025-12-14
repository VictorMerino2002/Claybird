from __future__ import annotations

import datetime
import uuid
import decimal
import re
from enum import Enum
from dataclasses import is_dataclass
from typing import Any, Iterable

from aiomysql.pool import Pool
from aiomysql import DictCursor
from pydantic import BaseModel
from dataclasses import is_dataclass, Field as DataclassField

from claybird.core.repositories.crud_repository_interface import CrudRepositoryInterface
from claybird.managers.event_manager import EventManager
from claybird.core.models.entity import Entity
from claybird.core.models.fields import Field
from claybird.core.models import field_type
from claybird.utils.text_formatter import camel_to_snake
from claybird.core.models.field_utilities import FieldUtilities


class MysqlCrudRepository(CrudRepositoryInterface):
    table_name: str | None = None
    schema: str | None = None
    entity_cls: type[Entity]

    _TYPE_MAP = {
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

    def __init__(self, pool: Pool):
        self.pool = pool
        self.schema = pool._conn_kwargs.get("db")

    @EventManager.on_event("start")
    async def _lazy_init(self):
        self.table_name = self.table_name or camel_to_snake(self.entity_cls.__name__)
        if not await self.table_exists():
            await self.create_table()

    async def create_table(self):
        columns = self._build_columns(self.entity_cls.get_fields())
        query = f"""
            CREATE TABLE `{self.table_name}` (
                {", ".join(columns)}
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                await conn.commit()

    def _build_columns(self, fields: dict[str, Field]) -> list[str]:
        columns: list[str] = []

        for name, field in fields.items():
            if FieldUtilities.is_embedded_type(field.type_):
                columns.extend(self._build_embedded_columns(name, field.type_))
            else:
                columns.append(self._column_sql(name, field))

        return columns

    def _build_embedded_columns(self, prefix: str, type_: type) -> list[str]:
        embedded_fields = FieldUtilities.get_embedded_fields(type_)
        columns = []

        for sub_name, sub_field in embedded_fields.items():

            if isinstance(sub_field, Field):
                field = sub_field

            elif isinstance(sub_field, DataclassField):
                field = Field(type_=sub_field.type)

            else:
                field = Field(type_=sub_field.annotation)

            columns.append(
                self._column_sql(f"{prefix}_{sub_name}", field)
            )

        return columns

    def _column_sql(self, name: str, field: Field) -> str:
        column_type = self._resolve_column_type(field.type_)
        parts = [f"`{name}` {column_type}"]

        if field.primary_key:
            parts.append("PRIMARY KEY")

        if field.required:
            parts.append("NOT NULL")

        if field.default is not None and not callable(field.default):
            default = str(field.default).replace("'", "''")
            parts.append(f"DEFAULT '{default}'")

        return " ".join(parts)

    def _resolve_column_type(self, python_type: type) -> str:
        if isinstance(python_type, type) and issubclass(python_type, Enum):
            values = "', '".join(e.value for e in python_type)
            return f"ENUM('{values}')"

        return self._TYPE_MAP.get(python_type, "VARCHAR(255)")

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
                (count,) = await cursor.fetchone()

        return count > 0

    async def save(self, entity: Entity):
        keys = FieldUtilities.flatten_entity_keys(entity)
        values = FieldUtilities.flatten_entity_values(entity)

        columns = ", ".join(f"`{k}`" for k in keys)
        placeholders = ", ".join("%s" for _ in keys)
        updates = ", ".join(f"`{k}` = VALUES(`{k}`)" for k in keys)

        query = f"""
            INSERT INTO `{self.table_name}` ({columns})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {updates}
        """

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, values)

    async def save_batch(self, entities: list[Entity]):
        if not entities:
            return

        keys = entities[0].get_keys()
        pk = self.entity_cls.get_primary_key()

        columns = ", ".join(f"`{k}`" for k in keys)
        placeholders = "(" + ", ".join("%s" for _ in keys) + ")"
        values_sql = ", ".join(placeholders for _ in entities)

        values = [v for e in entities for v in e.get_values()]
        updates = ", ".join(f"`{k}` = VALUES(`{k}`)" for k in keys if k != pk)

        query = f"""
            INSERT INTO `{self.table_name}` ({columns})
            VALUES {values_sql}
            ON DUPLICATE KEY UPDATE {updates}
        """

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, values)

    async def get(self, id_: Any):
        pk = self.entity_cls.get_primary_key()
        query = f"SELECT * FROM `{self.table_name}` WHERE `{pk}` = %s"

        async with self.pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cursor:
                await cursor.execute(query, (id_,))
                row = await cursor.fetchone()

        data = FieldUtilities.inflate_embedded_fields(self.entity_cls, row)
        return self.entity_cls(**data)

    async def delete(self, id_: Any):
        pk = self.entity_cls.get_primary_key()
        query = f"DELETE FROM `{self.table_name}` WHERE `{pk}` = %s"

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, (id_,))

    async def get_all(self):
        query = f"SELECT * FROM `{self.table_name}`"

        async with self.pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cursor:
                await cursor.execute(query)
                rows = await cursor.fetchall()

        entities = []
        for row in rows:
            data = FieldUtilities.inflate_embedded_fields(self.entity_cls, row)
            entities.append(self.entity_cls(**data))
        return entities

    def __getattr__(self, name: str):
        prefixes = {
            "find_by_": "find",
            "get_by_": "find",
            "count_by_": "count",
            "delete_by_": "delete",
        }

        for prefix, action in prefixes.items():
            if name.startswith(prefix):
                return self._build_dynamic_method(action, name[len(prefix):])

        raise AttributeError(f"{self.__class__.__name__} has no attribute {name}")

    def _build_dynamic_method(self, action: str, raw_fields: str):
        parts = re.split(r"_and_|_or_", raw_fields)
        connectors = re.findall(r"_and_|_or_", raw_fields)

        conditions = [self._parse_condition(p) for p in parts]

        async def method(*values):
            if len(values) != len(conditions):
                raise ValueError("Invalid argument count")

            where, params = self._build_where(conditions, connectors, values)
            sql = self._build_action_sql(action, where)

            async with self.pool.acquire() as conn:
                async with conn.cursor(DictCursor) as cursor:
                    await cursor.execute(sql, params)

                    if action == "find":
                        return [self.entity_cls(**r) for r in await cursor.fetchall()]
                    if action == "count":
                        return (await cursor.fetchone())["count"]
                    if action == "delete":
                        return cursor.rowcount

        return method

    @staticmethod
    def _parse_condition(part: str) -> tuple[str, str]:
        rules = {
            "_less_than": "<",
            "_greater_than": ">",
            "_before": "<",
            "_after": ">",
            "_like": "LIKE",
            "_not_like": "NOT LIKE",
            "_starts_with": "LIKE_START",
            "_ends_with": "LIKE_END",
        }

        for suffix, op in rules.items():
            if part.endswith(suffix):
                return part[:-len(suffix)], op

        return part, "="

    @staticmethod
    def _build_where(conditions, connectors, values):
        clauses, params = [], []

        for (field, op), value in zip(conditions, values):
            if op == "LIKE":
                clauses.append(f"`{field}` LIKE %s")
                params.append(f"%{value}%")
            elif op == "NOT LIKE":
                clauses.append(f"`{field}` NOT LIKE %s")
                params.append(f"%{value}%")
            elif op == "LIKE_START":
                clauses.append(f"`{field}` LIKE %s")
                params.append(f"{value}%")
            elif op == "LIKE_END":
                clauses.append(f"`{field}` LIKE %s")
                params.append(f"%{value}")
            else:
                clauses.append(f"`{field}` {op} %s")
                params.append(value)

        sql = clauses[0]
        for clause, conn in zip(clauses[1:], connectors):
            sql += f" {'AND' if '_and_' in conn else 'OR'} {clause}"

        return sql, params

    def _build_action_sql(self, action: str, where: str) -> str:
        if action == "find":
            return f"SELECT * FROM `{self.table_name}` WHERE {where}"
        if action == "count":
            return f"SELECT COUNT(*) AS count FROM `{self.table_name}` WHERE {where}"
        if action == "delete":
            return f"DELETE FROM `{self.table_name}` WHERE {where}"
        raise ValueError(f"Unknown action {action}")