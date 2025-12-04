import inspect
from claybird.core.dependency_container import DependencyContainer
from claybird.core.repositories.crud_repository_interface import CrudRepositoryInterface
from claybird.managers.connection_manager import ConnectionManager

class DependencyManager:
    @staticmethod
    async def inject(cls_to_inject, container: DependencyContainer):
        instance = await DependencyManager.instance_cls(cls_to_inject, container)
        return await DependencyManager.inject_attrs(instance, container)

    @staticmethod
    async def instance_cls(cls_to_instance, container: DependencyContainer):
        if not inspect.isclass(cls_to_instance):
            return cls_to_instance

        sig = inspect.signature(cls_to_instance.__init__)
        kwargs = {}

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            param_type = param.annotation
            if param_type is inspect.Parameter.empty:
                continue

            if DependencyManager.is_repository(param_type):
                implementation = await DependencyManager.handle_repository(cls_to_instance, param, container)
                kwargs[param_name] = implementation
                continue

            if container.has(param_type):
                implementation = container.get(param_type)

                if callable(implementation) and not inspect.isclass(implementation):
                    implementation = implementation()

                elif inspect.isclass(implementation):
                    implementation = await DependencyManager.inject(implementation, container)

                kwargs[param_name] = implementation
            else:
                kwargs[param_name] = await DependencyManager.inject(param_type, container)

        return cls_to_instance(**kwargs)

    @staticmethod
    async def inject_attrs(instance_to_inject, container: DependencyContainer):
        annotations = getattr(instance_to_inject, "__annotations__", {})

        for attr_name, attr_type in annotations.items():
            if hasattr(instance_to_inject, attr_name):
                continue

            if container.has(attr_type):
                dep = container.get(attr_type)

                if callable(dep) and not inspect.isclass(dep):
                    dep = dep()

                elif inspect.isclass(dep):
                    dep = await DependencyManager.inject(dep, container)

                setattr(instance_to_inject, attr_name, dep)
            else:
                setattr(
                    instance_to_inject,
                    attr_name,
                    await DependencyManager.inject(attr_type, container)
                )

        return instance_to_inject

    @staticmethod
    def is_repository(cls):
        return cls == CrudRepositoryInterface

    @staticmethod
    async def handle_repository(cls_to_instance, param, container: DependencyContainer):
        if hasattr(cls_to_instance, "connection"):
            connection_name = getattr(cls_to_instance, "connection")
        else:
            connection_name = "default"
        return await ConnectionManager.get_engine_implementation(connection_name, param.annotation, container)