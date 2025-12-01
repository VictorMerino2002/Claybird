class Controller:

    controllers = []

    def __init__(self, prefix: str):
        self.prefix = prefix

    def __call__(self, cls):
        Controller.controllers.append((cls, self.prefix))