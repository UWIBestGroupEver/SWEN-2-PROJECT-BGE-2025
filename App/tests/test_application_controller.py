# tests/test_application_flow.py
import pytest

from App.main import create_app
from App.database import db, create_db
from App.models.shortlist import Shortlist
from App.models.states import InvalidTransitionError
from App.controllers.application import (
    apply,
    shortlist,
    decide,
    get_status,
)
from App.controllers import create_user, open_position  # existing funcs


@pytest.fixture(autouse=True, scope="function")
def empty_db():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db'})
    with app.app_context():
        create_db()
        yield app.test_client()
        db.drop_all()


def test_apply_creates_application_without_position(empty_db):
    """Student apply creates APPLIED application with no position info."""
    student = create_user("stu", "pass", "student")

    app_obj = apply(student_user_id=student.id)

    assert app_obj is not None
    assert app_obj.student_id == student.id
    assert get_status(app_obj.id) == "APPLIED"


def test_full_flow_shortlist_and_accept(empty_db):
    """
    Student applies → Staff shortlists to a position → Employer accepts.
    """
    student = create_user("stu1", "pass", "student")
    staff = create_user("staff1", "pass", "staff")
    employer = create_user("emp1", "pass", "employer")
    position = open_position("Intern", employer.id, 1)

    # Student applies
    app_obj = apply(student.id)
    assert get_status(app_obj.id) == "APPLIED"

    # Staff shortlists application to position
    sl = shortlist(staff.id, app_obj.id, position.id)
    assert isinstance(sl, Shortlist)
    assert sl.application_id == app_obj.id
    assert sl.position_id == position.id
    assert get_status(app_obj.id) == "SHORTLISTED"

    # Employer accepts
    app_obj = decide(employer.id, app_obj.id, "ACCEPTED")
    assert get_status(app_obj.id) == "ACCEPTED"


def test_employer_can_reject_application(empty_db):
    """Employer can correctly reject applications after shortlist."""
    student = create_user("stu2", "pass", "student")
    staff = create_user("staff2", "pass", "staff")
    employer = create_user("emp2", "pass", "employer")
    position = open_position("Intern 2", employer.id, 1)

    app_obj = apply(student.id)
    sl = shortlist(staff.id, app_obj.id, position.id)
    assert get_status(app_obj.id) == "SHORTLISTED"

    app_obj = decide(employer.id, app_obj.id, "REJECTED")
    assert get_status(app_obj.id) == "REJECTED"


def test_invalid_users_cannot_perform_actions(empty_db):
    """Invalid users (wrong role) cause meaningful errors."""
    staff = create_user("staffX", "pass", "staff")
    employer = create_user("empX", "pass", "employer")
    student = create_user("stuX", "pass", "student")
    position = open_position("Intern X", employer.id, 1)

    # Non-student trying to apply
    with pytest.raises(PermissionError):
        apply(student_user_id=staff.id)

    # Valid application
    app_obj = apply(student.id)

    # Non-staff trying to shortlist
    with pytest.raises(PermissionError):
        shortlist(staff_user_id=student.id, application_id=app_obj.id, position_id=position.id)

    # Staff shortlists correctly
    shortlist(staff.id, app_obj.id, position.id)

    # Non-employer trying to decide
    with pytest.raises(PermissionError):
        decide(employer_user_id=student.id, application_id=app_obj.id, decision="ACCEPTED")


def test_invalid_decision_string_raises_error(empty_db):
    """Invalid decision values return meaningful errors."""
    student = create_user("stu3", "pass", "student")
    staff = create_user("staff3", "pass", "staff")
    employer = create_user("emp3", "pass", "employer")
    position = open_position("Intern 3", employer.id, 1)

    app_obj = apply(student.id)
    shortlist(staff.id, app_obj.id, position.id)

    with pytest.raises(ValueError):
        decide(employer.id, app_obj.id, "MAYBE")


def test_invalid_state_transition_in_decide(empty_db):
    """
    APPLIED → ACCEPTED directly is illegal (must go through SHORTLISTED).
    """
    from App.models.application import Application, ApplicationStatus

    employer = create_user("emp4", "pass", "employer")
    student = create_user("stu4", "pass", "student")

    # Manually create APPLIED application
    app_obj = Application(student_id=student.id, status=ApplicationStatus.APPLIED)
    db.session.add(app_obj)
    db.session.commit()

    assert get_status(app_obj.id) == "APPLIED"

    with pytest.raises(InvalidTransitionError):
        decide(employer.id, app_obj.id, "ACCEPTED")
