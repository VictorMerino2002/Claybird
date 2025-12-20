from claybird.application.ports.outbound.dependency_container_port import DependencyContainerPort
from claybird.application.ports.outbound.dependency_injector_port import DependencyInjectorPort
from claybird.application.ports.inbound.controller_handler_port import ControllerHandlerPort

class ControllersBootstrap:

    def __init__(self, container: DependencyContainerPort):
        self.container = container
        self.dependency_injector: DependencyInjectorPort = self.container.get(DependencyInjectorPort)
        self.controller_handler: ControllerHandlerPort = self.container.get(ControllerHandlerPort)

    async def load_controllers(self):
        controllers = self.controller_handler.get_controllers()
        for controller in controllers:
            injected_controller = await self.dependency_injector.inject(controller)
            self.controller_handler.load_controller(injected_controller)