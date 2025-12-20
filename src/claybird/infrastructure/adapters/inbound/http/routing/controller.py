class Controller:

    controllers = []

    def __init__(self, prefix: str):
        self.prefix = prefix

    def __call__(self, cls):
        cls._prefix = self.prefix
        Controller.controllers.append(cls)