# App/controllers/shortlist.py

from App.models import Shortlist, Position, Staff, Student, Application
from App.models.shortlist import DecisionStatus
from App.database import db


def add_student_to_shortlist(student_id, position_id, staff_id):
    """
    Add a student to a shortlist for a given position.

    - student_id: Student.user_id
    - staff_id:   Staff.user_id
    - position_id: Position.id
    """
    teacher = db.session.query(Staff).filter_by(user_id=staff_id).first()
    student = db.session.query(Student).filter_by(user_id=student_id).first()
    if student is None or teacher is None:
        return False

    # Find or create an Application for this student
    application = (
        db.session.query(Application)
        .filter_by(student_id=student.id)
        .first()
    )
    if application is None:
        application = Application(student_id=student.id)
        db.session.add(application)
        db.session.flush()  # get application.id without full commit

    # Check if this application is already shortlisted for this position
    existing = (
        db.session.query(Shortlist)
        .filter_by(application_id=application.id, position_id=position_id)
        .first()
    )

    position = (
        db.session.query(Position)
        .filter(
            Position.id == position_id,
            Position.number_of_positions > 0,
            Position.status == "open",
        )
        .first()
    )

    if teacher and not existing and position:
        shortlist = Shortlist(
            application_id=application.id,
            position_id=position.id,
            staff_id=teacher.id,
        )
        db.session.add(shortlist)

        # Move application to SHORTLISTED (state pattern)
        application.shortlist()

        db.session.commit()
        return shortlist

    return False


def decide_shortlist(student_id, position_id, decision):
    """
    Employer/staff decides on a shortlist entry for a given student + position.

    - student_id: Student.user_id
    - decision: 'ACCEPTED' or 'REJECTED' (case-insensitive)
    """
    student = db.session.query(Student).filter_by(user_id=student_id).first()
    if student is None:
        return False

    # Find applications for this student
    applications = (
        db.session.query(Application)
        .filter_by(student_id=student.id)
        .all()
    )
    if not applications:
        return False

    app_ids = [a.id for a in applications]

    shortlist = (
        db.session.query(Shortlist)
        .filter(
            Shortlist.application_id.in_(app_ids),
            Shortlist.position_id == position_id,
            Shortlist.status == DecisionStatus.PENDING,
        )
        .first()
    )

    position = (
        db.session.query(Position)
        .filter(
            Position.id == position_id,
            Position.number_of_positions > 0,
        )
        .first()
    )

    if shortlist and position:
        normalized = decision.upper()
        if normalized not in ("ACCEPTED", "REJECTED"):
            return False

        # Update shortlist enum
        shortlist.update_status(normalized)

        # Update position count if accepted
        if normalized == "ACCEPTED":
            position.update_number_of_positions(position.number_of_positions - 1)

        # Also move Application state (via state pattern)
        application = shortlist.application
        if normalized == "ACCEPTED":
            application.accept()
        else:
            application.reject()

        db.session.commit()
        return shortlist

    return False


def get_shortlist_by_student(student_id):
    """
    Get shortlist entries for a student by their user_id.
    """
    student = db.session.query(Student).filter_by(user_id=student_id).first()
    if student is None:
        return []

    return (
        db.session.query(Shortlist)
        .join(Application, Shortlist.application_id == Application.id)
        .filter(Application.student_id == student.id)
        .all()
    )


def get_shortlist_by_position(position_id):
    """
    Get all shortlist entries for a given position.
    """
    return db.session.query(Shortlist).filter_by(position_id=position_id).all()
