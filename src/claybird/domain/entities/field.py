import inspect
from claybird.domain.entities.field_type import FieldType
from uuid import UUID

class Field:
    __slots__ = ("type_", "required", "default", "primary_key", "name")

    def __init__(self, *, type_=str, required=False, default=None, primary_key=False):
        self.type_ = type_
        self.required = required
        self.default = default
        self.primary_key = primary_key
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

        if not hasattr(owner, "_meta"):
            owner._meta = {"fields": {}, "primary_key": None}

        owner._meta["fields"][name] = self

        if self.primary_key:
            if owner._meta["primary_key"] is not None:
                raise ValueError(
                    f"Primary key already exists: {owner._meta['primary_key']}"
                )
            owner._meta["primary_key"] = name

    def get_default(self, instance):
        if callable(self.default):
            sig = inspect.signature(self.default)
            if len(sig.parameters) == 0:
                return self.default()
            elif len(sig.parameters) == 1:
                return self.default(instance)
            else:
                raise TypeError(
                    f"Default function for '{self.name}' must accept 0 or 1 argument"
                )

        return self.default

    def validate_type(self, value):
        if value is None:
            return

        if isinstance(self.type_, FieldType):
            expected_type = self.type_.type_
        else:
            expected_type = self.type_

        if expected_type is UUID and isinstance(value, str):
            value = UUID(value)

        if not isinstance(value, expected_type):
            raise TypeError(
                f"Field '{self.name}' must be of type {expected_type.__name__}, "
                f"but got {type(value).__name__}"
            )

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if self.name in instance.__dict__:
            return instance.__dict__[self.name]

        value = self.get_default(instance)
        self.validate_type(value)
        instance.__dict__[self.name] = value
        return value

    def __set__(self, instance, value):
        self.validate_type(value)
        instance.__dict__[self.name] = value


def field(**kwargs):
    return Field(**kwargs)