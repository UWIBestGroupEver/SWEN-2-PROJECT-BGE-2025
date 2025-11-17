# App/models/application.py
from App.database import db
from sqlalchemy import Enum
from sqlalchemy.orm import reconstructor
from datetime import datetime

from App.models.application_status import ApplicationStatus
from App.models.states import (
    ApplicationState,
    AppliedState,
    ShortlistedState,
    AcceptedState,
    RejectedState,
)


class Application(db.Model):
    __tablename__ = 'application'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)

    status = db.Column(
        Enum(ApplicationStatus, native_enum=False),
        nullable=False,
        default=ApplicationStatus.APPLIED
    )

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # relationships
    student = db.relationship('Student', backref=db.backref('applications', lazy=True))

    # State pattern runtime object
    _state = None

    def __init__(self, student_id, status=ApplicationStatus.APPLIED, **kwargs):
        super().__init__(**kwargs)

        self.student_id = student_id

        if isinstance(status, ApplicationStatus):
            self.status = status
        else:
            self.status = ApplicationStatus(status)

        self._init_state_from_status()

    @reconstructor
    def init_on_load(self):
        self._init_state_from_status()

    def _init_state_from_status(self):
        mapping = {
            ApplicationStatus.APPLIED: AppliedState,
            ApplicationStatus.SHORTLISTED: ShortlistedState,
            ApplicationStatus.ACCEPTED: AcceptedState,
            ApplicationStatus.REJECTED: RejectedState,
        }
        state_cls = mapping.get(self.status, AppliedState)
        self._state = state_cls()
        self._state.setContext(self)

    def changeState(self, new_state: ApplicationState):
        self._state = new_state
        self._state.setContext(self)
        self.status = new_state.status_value

    # ---- state API ----
    def shortlist(self):
        if self._state is None:
            self._init_state_from_status()
        self._state.shortlist()

    def accept(self):
        if self._state is None:
            self._init_state_from_status()
        self._state.accept()

    def reject(self):
        if self._state is None:
            self._init_state_from_status()
        self._state.reject()

    def toJSON(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "status": self.status.value if self.status else None,
            "created_at": None if not self.created_at else self.created_at.isoformat(),
            "updated_at": None if not self.updated_at else self.updated_at.isoformat(),
        }
