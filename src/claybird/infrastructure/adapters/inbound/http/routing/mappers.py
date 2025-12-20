from claybird.infrastructure.adapters.inbound.http.routing.mapping_info import MappingInfo
from typing import Callable

class Mapping:
    def __init__(self, method: str, path: str):
        self.method = method.lower()
        self.path = path

    def __call__(self, func: Callable):
        func._mapping_info = MappingInfo(method=self.method, path=self.path)
        return func
    
class GetMapping(Mapping):
    def __init__(self, path):
        super().__init__("get", path)

class PostMapping(Mapping):
    def __init__(self, path):
        super().__init__("post", path)

class DeleteMapping(Mapping):
    def __init__(self, path):
        super().__init__("delete", path)

class PutMapping(Mapping):
    def __init__(self, path):
        super().__init__("put", path)

class PatchMapping(Mapping):
    def __init__(self, path):
        super().__init__("patch", path)