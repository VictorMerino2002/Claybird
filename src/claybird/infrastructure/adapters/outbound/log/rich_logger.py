from rich.console import Console

class RichLogger:

    def __init__(self):
        self.console = Console()

    def info(self, message):
        self.console.print(f"INFO: {message}")

    def error(self, error):
        self.console.print(error)