from abc import ABC, abstractmethod
from typing import Any

class ControllerHandlerPort(ABC):

    app: Any

    @abstractmethod
    def get_controllers(self) -> list:
        pass

    @abstractmethod
    def load_controller(self, controller):
        pass