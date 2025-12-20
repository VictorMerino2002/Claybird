from dataclasses import dataclass
from typing import Callable

@dataclass
class MappingInfo:
    method: str
    path: str
    fn: Callable | None = None

    @staticmethod
    def get_mapping_infos(controller) -> list["MappingInfo"]:
        attrs = dir(controller)
        mapped_infos = []
        for name in attrs:
            attr = getattr(controller, name)
            if callable(attr) and hasattr(attr, "_mapping_info"):
                mapping_info: MappingInfo = getattr(attr, "_mapping_info")
                mapping_info.fn = attr
                mapped_infos.append(mapping_info)
        return mapped_infos