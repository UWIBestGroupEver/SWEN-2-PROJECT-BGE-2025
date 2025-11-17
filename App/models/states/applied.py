from .application_state import ApplicationState
from .shortlisted import ShortlistedState
from App.models.application_status import ApplicationStatus

class AppliedState(ApplicationState):

    def status_value(self):
        return ApplicationStatus.APPLIED

    def shortlist(self):
        self.context.changeState(ShortlistedState())