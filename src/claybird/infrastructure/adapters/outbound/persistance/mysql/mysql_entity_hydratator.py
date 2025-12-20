from typing import Any, Type, Dict
from dataclasses import is_dataclass
from pydantic import BaseModel
from claybird.domain.entities import Entity, Field


class MysqlEntityHydratator:

    def __init__(self, entity_cls):
        self.entity_cls = entity_cls

    def deshydrate(self, entity: Any, prefix: str = "") -> Dict[str, Any]:
        result = {}

        fields = (
            entity.get_fields()
            if hasattr(entity, "get_fields")
            else self.get_embedded_fields(type(entity))
        )

        for name, field in fields.items():
            value = getattr(entity, name)
            key = f"{prefix}{name}"

            if value is None:
                result[key] = None
                continue

            field_type = field.type_ if hasattr(field, "type_") else type(value)

            if self.is_embedded_type(field_type):
                nested = self.deshydrate(value, prefix=f"{key}_")
                result.update(nested)
            else:
                result[key] = value

        return result

    def hydrate(self, data: dict, target_cls=None, prefix="") -> Entity:
        if target_cls is None:
            target_cls = self.entity_cls

        result = {}

        fields = (
            target_cls.get_fields()
            if hasattr(target_cls, "get_fields")
            else self.get_embedded_fields(target_cls)
        )

        for name, field in fields.items():
            key = f"{prefix}{name}"
            field_type = field.type_ if hasattr(field, "type_") else type(field)

            if self.is_embedded_type(field_type):
                result[name] = self.hydrate(data, field_type, prefix=f"{key}_")
            elif key in data:
                result[name] = data[key]
            else:
                result[name] = None  
        return target_cls(**result)

    def is_embedded_type(self, type_: Type) -> bool:
        return (
            isinstance(type_, type)
            and (
                is_dataclass(type_)
                or issubclass(type_, BaseModel)
                or issubclass(type_, Entity)
                or hasattr(type_, "get_fields")
            )
        )

    def get_embedded_fields(self, type_: Type) -> Dict:
        if is_dataclass(type_):
            return type_.__dataclass_fields__
        if isinstance(type_, type) and issubclass(type_, BaseModel):
            return type_.model_fields
        if hasattr(type_, "get_fields"):
            return type_.get_fields()
        return {}