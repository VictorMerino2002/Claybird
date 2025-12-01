from claybird.core.models.fields import Field

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

    def to_dict(self):
        return {name: getattr(self, name) for name in self.get_keys()}

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