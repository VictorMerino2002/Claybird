from claybird.application.ports.outbound.dependency_container_port import DependencyContainerPort

class DictDependencyContainer(DependencyContainerPort):

    def __init__(self):
        self.dependencies = {}

    def register(self, key, dependency):
        self.dependencies[key] = dependency

    def get(self, key):
        if (key not in self.dependencies):
            raise KeyError(f"{key} not found no dependecy container")
        return self.dependencies[key]
    
    def has(self, key):
        return key in self.dependencies