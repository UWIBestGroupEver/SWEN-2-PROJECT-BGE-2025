# App/models/shortlist.py
from App.database import db
from sqlalchemy import Enum as SAEnum
import enum
from datetime import datetime


class DecisionStatus(enum.Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"


class Shortlist(db.Model):
    __tablename__ = 'shortlist'

    id = db.Column(db.Integer, primary_key=True)

    # Link to the application (student application, no position here)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)

    # Position this application is being considered for
    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), nullable=False)

    # Staff member who did the shortlisting
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)

    # Employer’s decision on this shortlisted application
    status = db.Column(
        SAEnum(DecisionStatus, native_enum=False),
        nullable=False,
        default=DecisionStatus.PENDING
    )

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    application = db.relationship(
        'Application',
        backref=db.backref('shortlists', lazy=True)
    )
    position = db.relationship(
        'Position',
        backref=db.backref('shortlisted_applications', lazy=True)
    )
    staff = db.relationship(
        'Staff',
        backref=db.backref('shortlists_made', lazy=True)
    )

    def __init__(
        self,
        application_id: int,
        position_id: int,
        staff_id: int,
        status=DecisionStatus.PENDING,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.application_id = application_id
        self.position_id = position_id
        self.staff_id = staff_id

        # Allow passing either enum or string
        if isinstance(status, DecisionStatus):
            self.status = status
        else:
            self.status = DecisionStatus(status)

    # --------- Instance helpers ---------

    def update_status(self, status):
        """
        Update this shortlist entry's decision status.
        Caller (controller) is responsible for db.session.commit().
        """
        if isinstance(status, DecisionStatus):
            self.status = status
        else:
            # allow "accepted"/"rejected"/"pending" as strings
            self.status = DecisionStatus(status.upper())
        return self.status

    def toJSON(self):
        return {
            "id": self.id,
            "application_id": self.application_id,
            "position_id": self.position_id,
            "staff_id": self.staff_id,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            # Convenient accessor:
            "student_id": self.application.student_id if self.application else None,
        }
