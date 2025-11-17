from .application_state import ApplicationState
from App.models.application_status import ApplicationStatus


class RejectedState(ApplicationState):

    @property
    def status_value(self):
        return ApplicationStatus.REJECTED

    # No transitions → rejected is terminal
