from claybird.application.ports.inbound.controller_handler_port import ControllerHandlerPort
from claybird.infrastructure.adapters.inbound.http.routing.mapping_info import MappingInfo
from claybird.infrastructure.adapters.inbound.http.routing.controller import Controller
from fastapi import FastAPI, APIRouter

class FastAPIControllerHandler(ControllerHandlerPort):

    def __init__(
        self,
        debug: bool = False,
        title: str = "Claybird",
        summary: str | None = None,
        description: str = "",
        version: str = "0.1.0",
        openapi_url: str | None = "/openapi.json"
    ):
        self.app = FastAPI(debug=debug, title=title, summary=summary, description=description, version=version, openapi_url=openapi_url)

    def get_controllers(self):
        return Controller.controllers

    def load_controller(self, controller):
        prefix = controller._prefix
        router = APIRouter(prefix=prefix)
        mapping_infos = MappingInfo.get_mapping_infos(controller)
        for info in mapping_infos:
            router_method = getattr(router, info.method)
            router_method(info.path)(info.fn)
        self.app.include_router(router)