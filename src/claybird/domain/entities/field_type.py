from typing import NamedTuple, Any

class FieldType(NamedTuple):
    name: str
    type_: type

TEXT = FieldType(name="TEXT", type_=str)

JSON = FieldType(name="JSON", type_=Any)