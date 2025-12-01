from claybird.managers.connection_manager import ConnectionManager
from claybird.managers.controller_manager import ControllerManager
from claybird.managers.event_manager import EventManager
from claybird.utils.logger import Logger
from fastapi import FastAPI
from claybird.core.dependency_container import DependencyContainer

class Claybird:

    def __init__(
        self,
        dependency_container: DependencyContainer | None = None,
        debug: bool = False,
        title: str = "Claybird",
        summary: str | None = None,
        description: str = "",
        version: str = "0.1.0",
        openapi_url: str | None = "/openapi.json",
    ):
        self.app = FastAPI(debug=debug, title=title, summary=summary, description=description, version=version, openapi_url=openapi_url)
        self.container = dependency_container if dependency_container else DependencyContainer()
        self.container.register(Logger, Logger())
        self.container.register(FastAPI, self.app)
        self.logger: Logger = self.container.get(Logger)
        
    async def _load_app(self):
        await ConnectionManager.load_connection_from_settings(self.container)
        await ControllerManager.load_controllers(self.container)
        await EventManager.emit("start")

    async def run(self):
        import uvicorn
        await self._load_app()
        config = uvicorn.Config(self.app, host="127.0.0.1", port=8000)
        server = uvicorn.Server(config)
        await server.serve()