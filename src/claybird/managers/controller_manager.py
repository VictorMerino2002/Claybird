from fastapi import APIRouter, FastAPI
from claybird.core.dependency_container import DependencyContainer
from claybird.managers.dependency_manager import DependencyManager
from claybird.core.controllers.controller import Controller
from claybird.utils.logger import Logger


class ControllerManager:

    @staticmethod
    async def load_controllers(container: DependencyContainer):
        logger = container.get(Logger)
        logger.log(f"Loading {len(Controller.controllers)} controllers")
        app: FastAPI = container.get(FastAPI)
        for controller_cls, prefix in Controller.controllers:
            controller = await DependencyManager.inject(controller_cls, container)
            router = APIRouter(prefix=prefix)
            ControllerManager.load_endpoints(router, controller)
            app.include_router(router)

    @staticmethod
    def load_endpoints(router: APIRouter, controller):
        attributes = dir(controller)
        for attr_name in attributes:
            attr = getattr(controller, attr_name)
            if callable(attr) and hasattr(attr, "_mapping_info"):
                mapping_info = getattr(attr, "_mapping_info")
                router_method = getattr(router, mapping_info["method"])
                router_method(mapping_info["path"])(attr)