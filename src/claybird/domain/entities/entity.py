from claybird.domain.entities.field import Field

class Entity:
    def __init__(self, **kwargs):
        for name, field in self._meta["fields"].items():
            if name in kwargs:
                value = kwargs[name]

            elif field.required and field.default is None:
                raise ValueError(f"Field '{name}' is required")

            else:
                value = field.get_default(self)

            field.validate_type(value)
            setattr(self, name, value)

    def to_dict(self) -> dict:
        result = {}
        for name in self.get_keys():
            value = getattr(self, name)
            if isinstance(value, Entity):
                result[name] = value.to_dict()
            elif hasattr(value, "dict"):
                result[name] = value.dict()
            elif hasattr(value, "__dataclass_fields__"):
                result[name] = {f: getattr(value, f) for f in value.__dataclass_fields__}
            else:
                result[name] = value
        return result

    def get_keys(self):
        return tuple(self._meta["fields"].keys())

    def get_values(self):
        return tuple(getattr(self, name) for name in self.get_keys())

    @classmethod
    def get_fields(cls):
        return cls._meta["fields"]

    @classmethod
    def get_primary_key(cls):
        return cls._meta["primary_key"]

    @classmethod
    def get_primary_key_field(cls):
        pk = cls._meta["primary_key"]
        return cls._meta["fields"][pk]

    def serialize(self) -> dict:
        return self.to_dict()

    def __str__(self):
        return f"{self.__class__.__name__}({self.to_dict()})"