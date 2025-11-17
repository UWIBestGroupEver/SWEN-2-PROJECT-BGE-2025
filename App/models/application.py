from App.database import db
from sqlalchemy import Enum
from sqlalchemy.orm import reconstructor  
import enum
from datetime import datetime
from typing import Optional
from App.models.application_status import ApplicationStatus 

from App.models.states import (
    ApplicationState,
    AppliedState,
    ShortlistedState,
    AcceptedState,
    RejectedState,
    InvalidTransitionError,
)


class Application(db.Model):
    """Represents a student's application to a position/internship."""
    __tablename__ = 'application'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), nullable=False)

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
    position = db.relationship('Position', backref=db.backref('applications', lazy=True))


 # ------------------------------------------------------------------
    # non-persisted runtime state object (State Pattern)
    # ------------------------------------------------------------------
    _state = None

    def __init__(self, student_id, position_id, status=ApplicationStatus.APPLIED, **kwargs):
        super().__init__(**kwargs)

        self.student_id = student_id
        self.position_id = position_id

        # allow passing either ApplicationStatus or string
        if isinstance(status, ApplicationStatus):
            self.status = status
        else:
            self.status = ApplicationStatus(status)

        # create the initial state object based on status
        self._init_state_from_status()

    @reconstructor
    def init_on_load(self):
        """
        Called by SQLAlchemy after loading an instance from the DB.
        We use this to rebuild the _state object from the stored status.
        """
        self._init_state_from_status()

    # ------------------------------------------------------------------
    # State Pattern plumbing
    # ------------------------------------------------------------------

    def _init_state_from_status(self):
        """Internal helper: build correct state object from current status enum."""
        mapping = {
            ApplicationStatus.APPLIED: AppliedState,
            ApplicationStatus.SHORTLISTED: ShortlistedState,
            ApplicationStatus.ACCEPTED: AcceptedState,
            ApplicationStatus.REJECTED: RejectedState,
        }
        state_cls = mapping.get(self.status, AppliedState)  # default safety
        self._state = state_cls()
        self._state.setContext(self)

    def changeState(self, new_state: ApplicationState):
        self._state = new_state
        self._state.setContext(self)
        self.status = new_state.status_value

    # ------------------------------------------------------------------
    # Public API methods for State Pattern (delegate to state object)
    # ------------------------------------------------------------------

    def shortlist(self):
        """Ask the current state to perform a shortlist transition."""
        if self._state is None:
            self._init_state_from_status()
        self._state.shortlist()

    def accept(self):
        """Ask the current state to perform an accept transition."""
        if self._state is None:
            self._init_state_from_status()
        self._state.accept()

    def reject(self):
        """Ask the current state to perform a reject transition."""
        if self._state is None:
            self._init_state_from_status()
        self._state.reject()

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def toJSON(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "position_id": self.position_id,
            "status": self.status.value if self.status else None,
            "created_at": None if not self.created_at else self.created_at.isoformat(),
            "updated_at": None if not self.updated_at else self.updated_at.isoformat(),
        }
