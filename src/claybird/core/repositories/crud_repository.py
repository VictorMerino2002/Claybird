import inspect
import functools
from typing import Generic, TypeVar, get_origin, get_args
from claybird.core.repositories.crud_repository_interface import CrudRepositoryInterface

T = TypeVar("T")

class CrudRepository(CrudRepositoryInterface, Generic[T]):

    table_name: str = None

    def __init__(self, impl: CrudRepositoryInterface):
        entity_cls = self._get_entity_cls()
        if entity_cls:
            impl.entity_cls = entity_cls

        impl.table_name = self.table_name
        self.impl = impl

    def _get_entity_cls(self):
        for base in getattr(self.__class__, "__orig_bases__", []):
            origin = get_origin(base)
            if origin is CrudRepository:
                args = get_args(base)
                if args:
                    return args[0]
        raise ValueError("Cannot resolve Entity")

    async def save(self, entity):
        return await self.impl.save(entity)
    
    async def delete(self, id):
        return await self.impl.delete(id)
    
    async def get(self, id):
        return await self.impl.get(id)
    
    async def get_all(self):
        return await self.impl.get_all()

    def __getattr__(self, name):
        attr = getattr(self.impl, name)

        if not callable(attr):
            return attr

        if inspect.iscoroutinefunction(attr):
            return attr

        @functools.wraps(attr)
        async def async_wrapper(*args, **kwargs):
            result = attr(*args, **kwargs)
            return result

        return async_wrapper
