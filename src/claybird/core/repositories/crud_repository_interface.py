from abc import ABC, abstractmethod
from typing import Generic, TypeVar, get_args

T = TypeVar("T")

class CrudRepositoryInterface(ABC, Generic[T]):

    @abstractmethod
    async def save(self, entity):
        pass

    @abstractmethod
    async def delete(self, id):
        pass

    @abstractmethod
    async def get(self, id):
        pass

    @abstractmethod
    async def get_all(self):
        pass