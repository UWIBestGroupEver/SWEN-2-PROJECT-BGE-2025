# App/controllers/application.py
from App.database import db
from App.models.application import Application
from App.models.position import Position
from App.models.student import Student
from App.models.staff import Staff
from App.models.employer import Employer
from App.models.shortlist import Shortlist
from App.models.application_status import ApplicationStatus
from App.models.states import InvalidTransitionError


def apply(student_user_id):
    student = Student.query.filter_by(user_id=student_user_id).first()
    if not student:
        raise PermissionError("Only students can submit applications.")

    new_app = Application(student_id=student.id)
    db.session.add(new_app)
    db.session.commit()
    return new_app


def shortlist(staff_user_id, application_id, position_id):
    """
    Staff shortlists an existing application to a specific position.

    - Application must exist (and normally be in APPLIED state).
    - Staff chooses a Position.
    - A Shortlist row (application_id, position_id) is created.
    - Application state transitions APPLIED → SHORTLISTED.
    """
    staff = Staff.query.filter_by(user_id=staff_user_id).first()
    if not staff:
        raise PermissionError("Only staff can shortlist applications.")

    application = Application.query.get(application_id)
    if not application:
        raise ValueError("Application not found.")

    position = Position.query.get(position_id)
    if not position:
        raise ValueError("Position not found.")

    # Optional: prevent duplicate shortlist for same application/position
    existing = Shortlist.query.filter_by(
        application_id=application.id,
        position_id=position.id
    ).first()
    if existing:
        # Already shortlisted to this position; ensure state is SHORTLISTED
        if application.status != ApplicationStatus.SHORTLISTED:
            application.shortlist()
        db.session.commit()
        return existing
    default_title = position.title 

    # Create shortlist entry
    shortlist_entry = Shortlist(
        application_id=application.id,
        position_id=position.id,
        staff_id=staff.id,
    )

    db.session.add(shortlist_entry)

    # State machine enforces APPLIED → SHORTLISTED
    application.shortlist()

    db.session.commit()
    return shortlist_entry



def decide(employer_user_id, application_id, decision):
    """
    Employer makes the final decision on an application.
    `decision` should be 'ACCEPTED' or 'REJECTED'.
    """
    employer = Employer.query.filter_by(user_id=employer_user_id).first()
    if not employer:
        raise PermissionError("Only employers can decide applications.")

    application = Application.query.get(application_id)
    if not application:
        raise ValueError("Application not found.")

    # Enforce that application has been shortlisted at least once
    if not application.shortlists:
        raise InvalidTransitionError("Application must be shortlisted before a decision.")

    normalized = decision.upper()

    if normalized == ApplicationStatus.ACCEPTED.value:
        application.accept()
    elif normalized == ApplicationStatus.REJECTED.value:
        application.reject()
    else:
        raise ValueError("Decision must be either 'ACCEPTED' or 'REJECTED'.")

    db.session.commit()
    return application


def get_status(application_id):
    application = Application.query.get(application_id)
    if not application:
        raise ValueError("Application not found.")
    return application.status.value


def get_application_json(application_id):
    application = Application.query.get(application_id)
    if not application:
        return None
    return application.toJSON()


def get_applications_by_student_json(student_user_id):
    student = Student.query.filter_by(user_id=student_user_id).first()
    if not student:
        return []
    apps = Application.query.filter_by(student_id=student.id).all()
    return [app.toJSON() for app in apps]

