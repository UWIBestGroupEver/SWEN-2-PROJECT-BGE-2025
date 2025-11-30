import pytest

from App.main import create_app
from App.database import db, create_db
from App.models.user import User
from App.models.student import Student
from App.models.position import Position, PositionStatus
from App.models.employer import Employer
from App.models.application import Application
from App.models.application_status import ApplicationStatus
from App.models.shortlist import Shortlist, DecisionStatus
from App.models.states import InvalidTransitionError
from App.controllers.user import create_user, get_user_by_username
from App.controllers.student import create_student, add_gpa_to_student, add_degree_to_student
from App.controllers.position import open_position, get_all_positions_json, get_positions_by_employer
from App.controllers.application import apply, shortlist, decide, get_status


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def empty_db():
    """Create a clean test database for every test."""
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        create_db()
        yield db
        db.session.remove()
        db.drop_all()


# =============================================================================
# USER MODEL TESTS
# =============================================================================

def test_user_password_and_check(empty_db):
    user = User(username="keron", password="secret", role="student")
    db.session.add(user)
    db.session.commit()

    assert user.check_password("secret") is True
    assert user.check_password("wrong") is False


def test_create_user_creates_related_models(empty_db):
    student = create_user("aaliyah", "pass", "student")
    assert student is not False
    assert student.user is not None

    employer = create_user("deon", "pass", "employer")
    assert employer is not False
    assert employer.user is not None

    staff = create_user("shanice", "pass", "staff")
    assert staff is not False
    assert staff.user is not None


def test_duplicate_username_fails_gracefully(empty_db):
    res1 = create_user("ria", "p", "student")
    assert res1 is not False

    res2 = create_user("ria", "p2", "student")
    assert res2 is False


def test_invalid_user_type_returns_false(empty_db):
    res = create_user("sade", "p", "alienrole")
    assert res is False


def test_get_user_by_username(empty_db):
    create_user("keisha", "p", "student")
    u = get_user_by_username("keisha")
    assert u is not None
    assert u.username == "keisha"


# =============================================================================
# STUDENT MODEL TESTS
# =============================================================================

def test_student_creation_and_relationship(empty_db):
    stu = create_user("kwesi", "p", "student")
    assert stu is not False
    assert isinstance(stu, Student)
    assert stu.user is not None


def test_add_gpa_and_degree(empty_db):
    student = create_user("jelani", "p", "student")
    sid = student.id

    gpa = add_gpa_to_student(sid, 3.7)
    assert gpa == 3.7

    deg = add_degree_to_student(sid, "BSc Computer Science")
    assert deg == "BSc Computer Science"


def test_add_gpa_returns_none_when_missing(empty_db):
    res = add_gpa_to_student(9999, 3.9)
    assert res is None


# =============================================================================
# SHORTLIST MODEL TESTS
# =============================================================================

def test_shortlist_creation_and_defaults(empty_db):
    student = create_user("marlon", "p", "student")
    staff = create_user("kevin", "p", "staff")
    employer = create_user("samantha", "p", "employer")

    pos = open_position("Tech Intern", employer.user_id, 1)

    app = apply(student.user_id)
    sl = shortlist(staff.user_id, app.id, pos.id)

    assert isinstance(sl, Shortlist)
    assert sl.status == DecisionStatus.PENDING

    sl.update_status("ACCEPTED")
    assert sl.status == DecisionStatus.ACCEPTED

    sj = sl.toJSON()
    assert sj["application_id"] == app.id


# =============================================================================
# POSITION MODEL TESTS
# =============================================================================

def test_position_constructor_defaults_and_toJSON(empty_db):
    emp = create_user("tia", "p", "employer")
    pos = open_position("Junior Tester", emp.user_id, 3)

    assert pos is not False
    assert pos.status is not None

    j = pos.toJSON()
    assert j["title"] == "Junior Tester"
    assert j["number_of_positions"] == 3


def test_update_status_and_number_and_delete(empty_db):
    emp = create_user("omar", "p", "employer")
    pos = open_position("Support Analyst", emp.user_id, 1)

    new_status = pos.update_status(PositionStatus.closed)
    assert new_status == PositionStatus.closed

    new_num = pos.update_number_of_positions(4)
    assert new_num == 4

    pid = pos.id
    pos.delete_position()
    assert db.session.get(Position, pid) is None


# =============================================================================
# EMPLOYER MODEL TESTS
# =============================================================================

def test_employer_creation_and_positions(empty_db):
    emp = create_user("anika", "p", "employer")
    assert emp is not False
    assert isinstance(emp, Employer)

    pos = open_position("Developer", emp.id, 2)
    assert pos is not False

    positions = get_positions_by_employer(emp.id)
    assert any(p.id == pos.id for p in positions)


# =============================================================================
# APPLICATION CONTROLLER TESTS
# =============================================================================

def test_state_transitions_shortlist_accept_reject(empty_db):
    student = create_user("shane", "p", "student")
    staff = create_user("troy", "p", "staff")
    employer = create_user("rihanna", "p", "employer")

    pos = open_position("ICT Assistant", employer.user_id, 1)

    app = apply(student.user_id)
    assert get_status(app.id) == "APPLIED"

    shortlist(staff.user_id, app.id, pos.id)
    assert get_status(app.id) == "SHORTLISTED"

    decide(employer.user_id, app.id, "ACCEPTED")
    assert get_status(app.id) == "ACCEPTED"


def test_invalid_transition_raises(empty_db):
    employer = create_user("devon", "p", "employer")
    student = create_user("malik", "p", "student")

    app_obj = Application(student_id=student.id, status=ApplicationStatus.APPLIED)
    db.session.add(app_obj)
    db.session.commit()

    with pytest.raises(InvalidTransitionError):
        decide(employer.user_id, app_obj.id, "ACCEPTED")


# =============================================================================
# APPLICATION STATE MACHINE TESTS
# =============================================================================

def test_valid_transitions(empty_db):
    application = Application(student_id=1)
    assert application.status == ApplicationStatus.APPLIED

    application.shortlist()
    assert application.status == ApplicationStatus.SHORTLISTED

    application.accept()
    assert application.status == ApplicationStatus.ACCEPTED


def test_invalid_transition_from_accepted(empty_db):
    application = Application(student_id=1)
    application.shortlist()
    application.accept()

    with pytest.raises(InvalidTransitionError):
        application.shortlist()


def test_default_status_is_applied(empty_db):
    application = Application(student_id=1)
    assert application.status == ApplicationStatus.APPLIED


def test_rejected_flow_from_shortlisted(empty_db):
    application = Application(student_id=1)
    application.shortlist()
    application.reject()
    assert application.status == ApplicationStatus.REJECTED


def test_invalid_transition_applied_to_accepted(empty_db):
    application = Application(student_id=1)
    with pytest.raises(InvalidTransitionError):
        application.accept()


def test_invalid_transition_from_rejected(empty_db):
    application = Application(student_id=1)
    application.shortlist()
    application.reject()

    with pytest.raises(InvalidTransitionError):
        application.shortlist()

    with pytest.raises(InvalidTransitionError):
        application.accept()


def test_invalid_double_accept(empty_db):
    application = Application(student_id=1)
    application.shortlist()
    application.accept()

    with pytest.raises(InvalidTransitionError):
        application.accept()


def test_invalid_double_reject(empty_db):
    application = Application(student_id=1)
    application.shortlist()
    application.reject()

    with pytest.raises(InvalidTransitionError):
        application.reject()


def test_state_transitions_maintain_consistency(empty_db):
    app1 = Application(student_id=1)
    app2 = Application(student_id=2)
    app3 = Application(student_id=3)

    app1.shortlist()
    app1.accept()

    app2.shortlist()
    app2.reject()

    app3.shortlist()

    assert app1.status == ApplicationStatus.ACCEPTED
    assert app2.status == ApplicationStatus.REJECTED
    assert app3.status == ApplicationStatus.SHORTLISTED
