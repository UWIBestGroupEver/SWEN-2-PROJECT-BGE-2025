from App.database import db
from App.models.application import Application
from App.models.position import Position
from App.models.student import Student
from App.models.staff import Staff
from App.models.employer import Employer
from App.models.application_status import ApplicationStatus


def apply(student_user_id, position_id):
    """
    Create a new application for a student to a given position.
    Only valid if the user is a Student.
    """
    student = Student.query.filter_by(user_id=student_user_id).first()
    if not student:
        raise PermissionError("Only students can apply to positions.")

    position = Position.query.get(position_id)
    if not position:
        raise ValueError("Position not found.")

    new_app = Application(student_id=student.id, position_id=position.id)
    db.session.add(new_app)
    db.session.commit()
    return new_app


def shortlist(staff_user_id, application_id):
    """
    Shortlist an application.
    Only staff may perform this action.
    """
    staff = Staff.query.filter_by(user_id=staff_user_id).first()
    if not staff:
        raise PermissionError("Only staff can shortlist applications.")

    application = Application.query.get(application_id)
    if not application:
        raise ValueError("Application not found.")

    # Uses the Application model's context API (State Pattern).
    application.shortlist()
    db.session.commit()
    return application


def decide(employer_user_id, application_id, decision):
    """
    Employer makes a final decision on an application.
    `decision` should be 'ACCEPTED' or 'REJECTED'.
    """
    employer = Employer.query.filter_by(user_id=employer_user_id).first()
    if not employer:
        raise PermissionError("Only employers can decide applications.")

    application = Application.query.get(application_id)
    if not application:
        raise ValueError("Application not found.")

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
    """
    Return the current status value of an application.
    """
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
