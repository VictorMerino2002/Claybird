import inspect
from typing import Any

from claybird.application.ports.outbound.dependency_injector_port import DependencyInjectorPort
from claybird.application.ports.outbound.dependency_container_port import DependencyContainerPort
from claybird.application.ports.outbound.crud_repository_port import CrudRepositoryPort

from claybird.infrastructure.factories.connection_handler_factory import ConnectionHandlerFactory


class DependencyInjector(DependencyInjectorPort):

    def __init__(self, container: DependencyContainerPort):
        self.container = container
        self.connection_handler_factory = ConnectionHandlerFactory(container)

    async def inject(self, target: Any):
        instance = await self._inject_on_constructor(target)
        return await self._inject_on_attrs(instance)

    async def _inject_on_constructor(self, target: Any):
        if not inspect.isclass(target):
            return target

        signature = inspect.signature(target.__init__)
        kwargs = {}

        for name, param in signature.parameters.items():
            if name == "self":
                continue

            port = param.annotation
            if port is inspect.Parameter.empty:
                continue

            # Repository injection (special case)
            if self._is_repository(port):
                kwargs[name] = await self._handle_repository(target, port)
                continue

            # Registered dependency
            if self.container.has(port):
                adapter = self.container.get(port)
                kwargs[name] = await self._resolve(adapter)
            else:
                # Recursive resolution
                kwargs[name] = await self.inject(port)

        return target(**kwargs)

    async def _inject_on_attrs(self, target: Any):
        annotations = getattr(target, "__annotations__", {})

        for attr_name, port in annotations.items():
            if hasattr(target, attr_name):
                continue

            if self.container.has(port):
                adapter = self.container.get(port)
                value = await self._resolve(adapter)
            else:
                value = await self.inject(port)

            setattr(target, attr_name, value)

        return target

    async def _resolve(self, adapter: Any):
        if inspect.isclass(adapter):
            return await self.inject(adapter)

        if callable(adapter):
            return adapter()

        return adapter

    def _is_repository(self, annotation: Any) -> bool:
        return (
            inspect.isclass(annotation)
            and issubclass(annotation, CrudRepositoryPort)
        )

    async def _handle_repository(self, target: Any, port: type):
        connection_name = getattr(target, "connection", "default")

        connection = self.container.get(f"{connection_name}_connection")

        handler = self.connection_handler_factory.get_handler(
            connection["engine"]
        )

        return await handler.get_engine_adapter(connection, port)