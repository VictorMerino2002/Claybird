import inspect
from claybird.core.dependency_container import DependencyContainer
from claybird.core.repositories.crud_repository_interface import CrudRepositoryInterface

class DependencyManager:
    @staticmethod
    def inject(cls_to_inject, container: DependencyContainer):
        instance = DependencyManager.instance_cls(cls_to_inject, container)
        return DependencyManager.inject_attrs(instance, container)

    @staticmethod
    def instance_cls(cls_to_instance, container: DependencyContainer):
        if not inspect.isclass(cls_to_instance):
            return cls_to_instance

        sig = inspect.signature(cls_to_instance.__init__)
        kwargs = {}

        for name, param in sig.parameters.items():
            if name == "self":
                continue

            dep_type = param.annotation
            if dep_type is inspect.Parameter.empty:
                continue

            if DependencyManager.is_repository(dep_type):
                dep = DependencyManager.handle_repository(cls_to_instance ,param)

            if container.has(dep_type):
                dep = container.get(dep_type)

                if callable(dep) and not inspect.isclass(dep):
                    dep = dep()

                elif inspect.isclass(dep):
                    dep = DependencyManager.inject(dep, container)

                kwargs[name] = dep
            else:
                kwargs[name] = DependencyManager.inject(dep_type, container)

        return cls_to_instance(**kwargs)

    @staticmethod
    def inject_attrs(instance_to_inject, container: DependencyContainer):
        annotations = getattr(instance_to_inject, "__annotations__", {})

        for attr_name, attr_type in annotations.items():
            if hasattr(instance_to_inject, attr_name):
                continue

            if container.has(attr_type):
                dep = container.get(attr_type)

                if callable(dep) and not inspect.isclass(dep):
                    dep = dep()

                elif inspect.isclass(dep):
                    dep = DependencyManager.inject(dep, container)

                setattr(instance_to_inject, attr_name, dep)
            else:
                setattr(
                    instance_to_inject,
                    attr_name,
                    DependencyManager.inject(attr_type, container)
                )

        return instance_to_inject

    @staticmethod
    def is_repository(cls):
        return cls == CrudRepositoryInterface

    @staticmethod
    def handle_repository(cls_to_instance ,param):
        print(cls_to_instance)
        print(param)