from abc import ABC, abstractmethod

class LoggerPort:

    @abstractmethod
    def info(self, message):
        pass

    @abstractmethod
    def error(self, error):
        pass