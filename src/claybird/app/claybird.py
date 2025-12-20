from claybird.application.ports.outbound.dependency_container_port import DependencyContainerPort
from claybird.application.ports.outbound.dependency_injector_port import DependencyInjectorPort
from claybird.application.ports.outbound.logger_port import LoggerPort
from claybird.application.ports.inbound.controller_handler_port import ControllerHandlerPort
from claybird.application.ports.inbound.server_port import ServerPort


from fastapi import FastAPI
from claybird.infrastructure.adapters.outbound.events import EventBus
from claybird.infrastructure.adapters.outbound.log.rich_logger import RichLogger
from claybird.infrastructure.adapters.outbound.dependencies.dict_dependency_container import DictDependencyContainer
from claybird.infrastructure.adapters.outbound.dependencies.dependency_injector import DependencyInjector
from claybird.infrastructure.adapters.inbound.http.fastapi_controller_handler import FastAPIControllerHandler
from claybird.infrastructure.adapters.inbound.http.uvicorn_server import UvicorServer


from claybird.infrastructure.bootstrap.settings_bootstrap import SettingsBootstrap
from claybird.infrastructure.bootstrap.connections_bootstrap import ConnectionsBootstrap
from claybird.infrastructure.bootstrap.controllers_bootstrap import ControllersBootstrap

class Claybird:

    def __init__(
        self,
        dependency_container: DependencyContainerPort | None = None,
        debug: bool = False,
        title: str = "Claybird",
        summary: str | None = None,
        description: str = "",
        version: str = "0.1.0",
        openapi_url: str | None = "/openapi.json",
        settings_path: str = "settings.py"
    ):
        self.settings_path = settings_path
        
        #DEFAULT DEPS
        self.container = dependency_container if dependency_container else DictDependencyContainer()

        if not self.container.has(LoggerPort):
            logger = RichLogger()
            self.container.register(LoggerPort, logger)

        if not self.container.has(DependencyInjectorPort):
            dependency_injector = DependencyInjector(self.container)
            self.container.register(DependencyInjectorPort, dependency_injector)

        if not self.container.has(ControllerHandlerPort):
            controller_handler = FastAPIControllerHandler(debug=debug, title=title, summary=summary, description=description, version=version, openapi_url=openapi_url)
            self.container.register(ControllerHandlerPort, controller_handler)

        if not self.container.has(ServerPort):
            server = UvicorServer()
            self.container.register(ServerPort, server)


    async def bootstrap(self):
        settings_bootstrap = SettingsBootstrap(self.container)
        settings_bootstrap.load_settings(self.settings_path)

        connections_bootstrap = ConnectionsBootstrap(self.container)
        await connections_bootstrap.load_connections_from_settings()

        controllers_bootstrap = ControllersBootstrap(self.container)
        await controllers_bootstrap.load_controllers()
        
        await EventBus.emit("start")

    async def run(self, host: str = "127.0.0.1", port: int | str = 8000):
        await self.bootstrap()
        
        controller_handler: ControllerHandlerPort = self.container.get(ControllerHandlerPort)
        server: ServerPort = self.container.get(ServerPort)
        
        await server.run(
            app=controller_handler.app,
            host=host, 
            port=port
        )

        