# Application state interface and base class for State Pattern

from abc import ABC, abstractmethod

class InvalidTransitionError(Exception):
    pass

class ApplicationState(ABC):

    def __init__(self):
        self.context = None

    def setContext(self, context):
        self.context = context

    def accept(self):
        raise InvalidTransitionError(
            f"Cannot accept from {self.__class__.__name__}"
        )

    def reject(self):
        raise InvalidTransitionError(
            f"Cannot reject from {self.__class__.__name__}"
        )

    def shortlist(self):
        raise InvalidTransitionError(
            f"Cannot shortlist from {self.__class__.__name__}"
        )
