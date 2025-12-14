from dataclasses import is_dataclass, Field as DataclassField
from pydantic import BaseModel
from claybird.core.models.fields import Field
from typing import Any, Type, Dict


class FieldUtilities:
    @staticmethod
    def is_embedded_type(type_: Type) -> bool:
        return (
            is_dataclass(type_) or
            (isinstance(type_, type) and issubclass(type_, BaseModel)) or
            (isinstance(type_, type) and issubclass(type_, Field.type_)) or
            (isinstance(type_, type) and hasattr(type_, "get_fields"))
        )

    @staticmethod
    def get_embedded_fields(type_: Type) -> dict:
        if is_dataclass(type_):
            return type_.__dataclass_fields__
        if issubclass(type_, BaseModel):
            return type_.model_fields
        if hasattr(type_, "get_fields"):
            return type_.get_fields()
        return {}

    @staticmethod
    def flatten_entity_keys(entity) -> list[str]:
        keys = []
        for name, field in entity.get_fields().items():
            if EmbeddedFieldHelper.is_embedded_type(field.type_):
                for sub_name in EmbeddedFieldHelper.get_embedded_fields(field.type_):
                    keys.append(f"{name}_{sub_name}")
            else:
                keys.append(name)
        return keys

    @staticmethod
    def flatten_entity_values(entity) -> list[Any]:
        values = []
        for name, field in entity.get_fields().items():
            value = getattr(entity, name)
            if EmbeddedFieldHelper.is_embedded_type(field.type_):
                embedded_fields = EmbeddedFieldHelper.get_embedded_fields(field.type_)
                for sub_name in embedded_fields:
                    sub_value = getattr(value, sub_name)
                    values.append(sub_value)
            else:
                values.append(value)
        return values

    @staticmethod
    def inflate_embedded_fields(entity_cls, row: Dict[str, Any]) -> dict:
        data = {}
        for name, field in entity_cls.get_fields().items():
            if EmbeddedFieldHelper.is_embedded_type(field.type_):
                embedded_fields = EmbeddedFieldHelper.get_embedded_fields(field.type_)
                sub_values = {}
                for sub_name in embedded_fields:
                    column_name = f"{name}_{sub_name}"
                    sub_values[sub_name] = row.pop(column_name)
                data[name] = field.type_(**sub_values)
            else:
                data[name] = row[name]
        return data