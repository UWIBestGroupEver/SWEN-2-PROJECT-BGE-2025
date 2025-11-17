import pytest

from App.main import create_app
from App.database import db, create_db
from App.models import Position, Student, Employer
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
    """
    Fresh test database per test.
    If any DB/boot/runtime error occurs, tests will fail here,
    satisfying the 'App boots / DB operations succeed' criterion.
    """
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db'})
    with app.app_context():
        create_db()
        yield app.test_client()
        db.drop_all()


def test_apply_creates_application(empty_db):
    """Application creation works for valid students."""
    student = create_user("stu", "pass", "student")
    employer = create_user("emp", "pass", "employer")
    position = open_position("Intern", employer.id, 1)

    app_obj = apply(student_user_id=student.id, position_id=position.id)

    assert app_obj is not None
    assert app_obj.student_id == student.id
    assert app_obj.position_id == position.id
    assert get_status(app_obj.id) == "APPLIED"


def test_shortlist_and_accept_flow(empty_db):
    """Staff can shortlist, employer can accept."""
    student = create_user("stu", "pass", "student")
    staff = create_user("staff", "pass", "staff")
    employer = create_user("emp", "pass", "employer")
    position = open_position("Intern", employer.id, 1)

    app_obj = apply(student.id, position.id)
    assert get_status(app_obj.id) == "APPLIED"

    # Staff shortlists
    app_obj = shortlist(staff.id, app_obj.id)
    assert get_status(app_obj.id) == "SHORTLISTED"

    # Employer accepts
    app_obj = decide(employer.id, app_obj.id, "ACCEPTED")
    assert get_status(app_obj.id) == "ACCEPTED"


def test_employer_can_reject_application(empty_db):
    """Employers can correctly reject applications."""
    student = create_user("stu2", "pass", "student")
    staff = create_user("staff2", "pass", "staff")
    employer = create_user("emp2", "pass", "employer")
    position = open_position("Intern 2", employer.id, 1)

    app_obj = apply(student.id, position.id)
    app_obj = shortlist(staff.id, app_obj.id)
    assert get_status(app_obj.id) == "SHORTLISTED"

    # Employer rejects
    app_obj = decide(employer.id, app_obj.id, "REJECTED")
    assert get_status(app_obj.id) == "REJECTED"


def test_invalid_users_cannot_perform_actions(empty_db):
    """Invalid users (wrong role) cause meaningful errors."""
    # Create a staff and employer but use wrong roles intentionally
    staff = create_user("staffX", "pass", "staff")
    employer = create_user("empX", "pass", "employer")
    student = create_user("stuX", "pass", "student")
    position = open_position("Intern X", employer.id, 1)

    # Non-student trying to apply
    with pytest.raises(PermissionError):
        apply(student_user_id=staff.id, position_id=position.id)

    # Non-staff trying to shortlist (use employer id instead of staff id)
    app_obj = apply(student.id, position.id)
    with pytest.raises(PermissionError):
        shortlist(staff_user_id=student.id, application_id=app_obj.id)

    # Non-employer trying to decide (use student id instead of employer id)
    with pytest.raises(PermissionError):
        decide(employer_user_id=student.id, application_id=app_obj.id, decision="ACCEPTED")


def test_invalid_decision_string_raises_error(empty_db):
    """Invalid decision values return meaningful errors."""
    student = create_user("stu3", "pass", "student")
    staff = create_user("staff3", "pass", "staff")
    employer = create_user("emp3", "pass", "employer")
    position = open_position("Intern 3", employer.id, 1)

    app_obj = apply(student.id, position.id)
    app_obj = shortlist(staff.id, app_obj.id)

    with pytest.raises(ValueError):
        decide(employer.id, app_obj.id, "MAYBE")  # invalid decision string


def test_invalid_state_transition_in_decide(empty_db):
    """
    Invalid transitions (e.g., ACCEPT without SHORTLIST) propagate as meaningful errors
    from the state pattern.
    """
    student = create_user("stu4", "pass", "student")
    employer = create_user("emp4", "pass", "employer")
    position = open_position("Intern 4", employer.id, 1)

    app_obj = apply(student.id, position.id)
    assert get_status(app_obj.id) == "APPLIED"

    # State pattern should reject APPLIED → ACCEPTED directly
    with pytest.raises(InvalidTransitionError):
        decide(employer.id, app_obj.id, "ACCEPTED")
