from .application_state import ApplicationState
from App.models.application_status import ApplicationStatus


class AcceptedState(ApplicationState):

    @property
    def status_value(self):
        return ApplicationStatus.ACCEPTED

    # No transitions → accepted is terminal
