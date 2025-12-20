from abc import ABC, abstractmethod

class DependencyInjectorPort:

    @abstractmethod
    def inject(self, target):
        pass