from .application_state import ApplicationState
from .accepted import AcceptedState
from .rejected import RejectedState
from App.models.application_status import ApplicationStatus


class ShortlistedState(ApplicationState):

    @property
    def status_value(self):
        return ApplicationStatus.SHORTLISTED

    def accept(self):
        self.context.changeState(AcceptedState())

    def reject(self):
        self.context.changeState(RejectedState())
