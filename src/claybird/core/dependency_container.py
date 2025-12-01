class DependencyContainer:

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