from typing import NamedTuple

class FieldType(NamedTuple):
    name: str
    type_: type

TEXT = FieldType(name="TEXT", type_=str)