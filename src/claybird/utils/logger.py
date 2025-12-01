from rich.console import Console

class Logger:

    def __init__(self):
        self.console = Console()

    def log(self, message):
        self.console.print(f"INFO: {message}")

    def error(self, error):
        self.console.print(error)
