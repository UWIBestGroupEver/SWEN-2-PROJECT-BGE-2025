from App.database import db
from sqlalchemy import Enum
import enum
from datetime import datetime


class ApplicationStatus(enum.Enum):
    APPLIED = "APPLIED"
    SHORTLISTED = "SHORTLISTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


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


    def __init__(self, student_id, position_id, status=ApplicationStatus.APPLIED):
        self.student_id = student_id
        self.position_id = position_id

        # allow passing either ApplicationStatus or string
        if isinstance(status, ApplicationStatus):
            self.status = status
        else:
            # fail fast on invalid values
            self.status = ApplicationStatus(status)


    # ----------------------------------------------------------------------
    # Context API methods for State Pattern
    # ----------------------------------------------------------------------
    # These methods represent the public actions that can be performed on an
    # Application. At this stage, they simply update the status directly.
    #
    # Later, when the State Pattern is added, these methods will delegate
    # the action to a State object instead of modifying status directly.
    # ----------------------------------------------------------------------

    def shortlist(self):
        """Simple placeholder: change status directly (state logic added later)."""
        self.status = ApplicationStatus.SHORTLISTED

    def accept(self):
        """Simple placeholder: change status directly (state logic added later)."""
        self.status = ApplicationStatus.ACCEPTED

    def reject(self):
        """Simple placeholder: change status directly (state logic added later)."""
        self.status = ApplicationStatus.REJECTED

    def toJSON(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "position_id": self.position_id,
            "status": self.status.value if self.status else None,
            "created_at": None if not self.created_at else self.created_at.isoformat(),
            "updated_at": None if not self.updated_at else self.updated_at.isoformat(),
        }
