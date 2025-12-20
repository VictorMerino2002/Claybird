from abc import ABC, abstractmethod

class DependencyContainerPort(ABC):

    @abstractmethod
    def register(self, key, dependecy):
        pass

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def has(self, key):
        pass