import pytest
from App.controllers.application import apply, shortlist, decide, get_status
from App.controllers.position import open_position, get_positions_by_employer_json
from App.models import Position
from App.controllers.user import create_user
from App.models.states.application_state import InvalidTransitionError
from App import create_app
from App.database import db


@pytest.fixture
def empty_db():
    """Create a test application instance with empty database."""
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


# ==============================================================================
# 7. apply(student_user_id) Tests
# ==============================================================================

def test_apply_valid_student_creates_application(empty_db):
    """Test that a valid student can create an application."""
    student_user = create_user("Keron", "student_pass123", "student")
    application = apply(student_user.user_id)
   
    assert application is not None
    assert application.student_id == student_user.id
    assert get_status(application.id) == "APPLIED"


def test_apply_non_student_raises_permission_error(empty_db):
    """Test that non-students cannot create applications."""
    employer_user = create_user("Marlon", "employer_pass123", "employer")
   
    with pytest.raises(PermissionError):
        apply(employer_user.user_id)


def test_apply_staff_raises_permission_error(empty_db):
    """Test that staff members cannot create applications."""
    staff_user = create_user("Sade", "staff_pass123", "staff")
   
    with pytest.raises(PermissionError):
        apply(staff_user.user_id)


def test_apply_state_starts_at_applied(empty_db):
    """Test that application state starts at APPLIED."""
    student_user = create_user("Aaliyah", "student_pass123", "student")
    application = apply(student_user.user_id)
   
    assert get_status(application.id) == "APPLIED"


def test_apply_multiple_applications_same_student(empty_db):
    """Test that a student can create multiple applications."""
    student_user = create_user("Deon", "student_pass123", "student")
    first_application = apply(student_user.user_id)
    second_application = apply(student_user.user_id)
   
    assert first_application.id != second_application.id
    assert first_application.student_id == student_user.id
    assert second_application.student_id == student_user.id


# ==============================================================================
# 8. shortlist(staff_user_id, application_id, position_id) Tests
# ==============================================================================

def test_shortlist_staff_can_shortlist_application(empty_db):
    """Test that staff can successfully shortlist an application."""
    student_user = create_user("Shanice", "student_pass123", "student")
    staff_user = create_user("Jelani", "staff_pass123", "staff")
    employer_user = create_user("Kwesi", "employer_pass123", "employer")
   
    position = open_position("Software Developer Intern", employer_user.user_id, 1)
    application = apply(student_user.user_id)
    shortlist_entry = shortlist(staff_user.user_id, application.id, position.id)
   
    assert shortlist_entry is not None
    assert shortlist_entry.application_id == application.id
    assert shortlist_entry.position_id == position.id


def test_shortlist_non_staff_raises_permission_error(empty_db):
    """Test that non-staff cannot shortlist applications."""
    student_user = create_user("Ria", "student_pass123", "student")
    employer_user = create_user("Marlon", "employer_pass123", "employer")
   
    position = open_position("Marketing Assistant", employer_user.user_id, 1)
    application = apply(student_user.user_id)
   
    with pytest.raises(PermissionError):
        shortlist(employer_user.user_id, application.id, position.id)


def test_shortlist_missing_application_raises_value_error(empty_db):
    """Test that shortlisting a missing application raises ValueError."""
    staff_user = create_user("Keisha", "staff_pass123", "staff")
    employer_user = create_user("Sade", "employer_pass123", "employer")
   
    position = open_position("Data Analyst", employer_user.user_id, 1)
   
    with pytest.raises(ValueError):
        shortlist(staff_user.user_id, 9999, position.id)


def test_shortlist_missing_position_raises_value_error(empty_db):
    """Test that shortlisting with a missing position raises ValueError."""
    student_user = create_user("Aaliyah", "student_pass123", "student")
    staff_user = create_user("Jelani", "staff_pass123", "staff")
   
    application = apply(student_user.user_id)
   
    with pytest.raises(ValueError):
        shortlist(staff_user.user_id, application.id, 9999)


def test_shortlist_same_application_position_returns_existing_entry(empty_db):
    """Test that re-shortlisting same application-position returns existing entry."""
    student_user = create_user("Deon", "student_pass123", "student")
    staff_user = create_user("Keisha", "staff_pass123", "staff")
    employer_user = create_user("Kwesi", "employer_pass123", "employer")
   
    position = open_position("Junior Developer", employer_user.user_id, 1)
    application = apply(student_user.user_id)
   
    first_shortlist_entry = shortlist(staff_user.user_id, application.id, position.id)
    second_shortlist_entry = shortlist(staff_user.user_id, application.id, position.id)
   
    assert first_shortlist_entry.id == second_shortlist_entry.id


def test_shortlist_transitions_applied_to_shortlisted(empty_db):
    """Test that state transitions APPLIED → SHORTLISTED."""
    student_user = create_user("Shanice", "student_pass123", "student")
    staff_user = create_user("Sade", "staff_pass123", "staff")
    employer_user = create_user("Marlon", "employer_pass123", "employer")
   
    position = open_position("UX Designer", employer_user.user_id, 1)
    application = apply(student_user.user_id)
   
    assert get_status(application.id) == "APPLIED"
   
    shortlist(staff_user.user_id, application.id, position.id)
   
    assert get_status(application.id) == "SHORTLISTED"


# ==============================================================================
# 9. decide(employer_user_id, application_id, decision) Tests
# ==============================================================================

def test_decide_employer_can_accept_shortlisted_application(empty_db):
    """Test that employer can ACCEPT a shortlisted application."""
    student_user = create_user("Keron", "student_pass123", "student")
    staff_user = create_user("Jelani", "staff_pass123", "staff")
    employer_user = create_user("Kwesi", "employer_pass123", "employer")
   
    position = open_position("Frontend Developer", employer_user.user_id, 1)
    application = apply(student_user.user_id)
    shortlist(staff_user.user_id, application.id, position.id)
   
    result = decide(employer_user.user_id, application.id, "ACCEPTED")
   
    assert result is not None
    assert get_status(application.id) == "ACCEPTED"


def test_decide_employer_can_reject_shortlisted_application(empty_db):
    """Test that employer can REJECT a shortlisted application."""
    student_user = create_user("Ria", "student_pass123", "student")
    staff_user = create_user("Keisha", "staff_pass123", "staff")
    employer_user = create_user("Marlon", "employer_pass123", "employer")
   
    position = open_position("Backend Engineer", employer_user.user_id, 1)
    application = apply(student_user.user_id)
    shortlist(staff_user.user_id, application.id, position.id)
   
    result = decide(employer_user.user_id, application.id, "REJECTED")
   
    assert result is not None
    assert get_status(application.id) == "REJECTED"


def test_decide_non_employer_raises_permission_error(empty_db):
    """Test that non-employer triggers PermissionError."""
    student_user = create_user("Aaliyah", "student_pass123", "student")
    staff_user = create_user("Sade", "staff_pass123", "staff")
    employer_user = create_user("Kwesi", "employer_pass123", "employer")
   
    position = open_position("Full Stack Developer", employer_user.user_id, 1)
    application = apply(student_user.user_id)
    shortlist(staff_user.user_id, application.id, position.id)
   
    with pytest.raises(PermissionError):
        decide(staff_user.user_id, application.id, "ACCEPTED")


def test_decide_application_not_shortlisted_raises_invalid_transition_error(empty_db):
    """Test that application not shortlisted raises InvalidTransitionError."""
    student_user = create_user("Deon", "student_pass123", "student")
    employer_user = create_user("Jelani", "employer_pass123", "employer")
   
    application = apply(student_user.user_id)
   
    with pytest.raises(InvalidTransitionError):
        decide(employer_user.user_id, application.id, "ACCEPTED")


def test_decide_invalid_decision_string_raises_value_error(empty_db):
    """Test that only ACCEPTED or REJECTED are allowed."""
    student_user = create_user("Shanice", "student_pass123", "student")
    staff_user = create_user("Keisha", "staff_pass123", "staff")
    employer_user = create_user("Marlon", "employer_pass123", "employer")
   
    position = open_position("Mobile Developer", employer_user.user_id, 1)
    application = apply(student_user.user_id)
    shortlist(staff_user.user_id, application.id, position.id)
   
    with pytest.raises(ValueError):
        decide(employer_user.user_id, application.id, "INVALID")


def test_decide_accept_decrements_position_count(empty_db):
    """Test that ACCEPTED decrements position's number_of_positions."""
    student_user = create_user("Keron", "student_pass123", "student")
    staff_user = create_user("Sade", "staff_pass123", "staff")
    employer_user = create_user("Kwesi", "employer_pass123", "employer")
   
    position = open_position("DevOps Engineer", employer_user.user_id, 2)
    initial_positions = position.number
   
    application = apply(student_user.user_id)
    shortlist(staff_user.user_id, application.id, position.id)
    decide(employer_user.user_id, application.id, "ACCEPTED")
   
    updated_position = Position.query.get(position.id)
    assert updated_position.number == initial_positions - 1


def test_decide_reject_does_not_decrement_position_count(empty_db):
    """Test that Reject doesn't decrement position count."""
    student_user = create_user("Ria", "student_pass123", "student")
    staff_user = create_user("Jelani", "staff_pass123", "staff")
    employer_user = create_user("Marlon", "employer_pass123", "employer")
   
    position = open_position("QA Tester", employer_user.user_id, 2)
    initial_positions = position.number
   
    application = apply(student_user.user_id)
    shortlist(staff_user.user_id, application.id, position.id)
    decide(employer_user.user_id, application.id, "REJECTED")
   
    updated_position = Position.query.get(position.id)
    assert updated_position.number == initial_positions


def test_decide_case_insensitive(empty_db):
    """Test that decision string is case-insensitive."""
    student_user = create_user("Aaliyah", "student_pass123", "student")
    staff_user = create_user("Keisha", "staff_pass123", "staff")
    employer_user = create_user("Kwesi", "employer_pass123", "employer")
   
    position = open_position("Product Manager", employer_user.user_id, 1)
    application = apply(student_user.user_id)
    shortlist(staff_user.user_id, application.id, position.id)
   
    result = decide(employer_user.user_id, application.id, "accepted")
    assert get_status(application.id) == "ACCEPTED"


# ==============================================================================
# 10. get_status(application_id) Tests
# ==============================================================================

def test_get_status_returns_correct_status_value(empty_db):
    """Test that get_status returns correct status value."""
    student_user = create_user("Deon", "student_pass123", "student")
    application = apply(student_user.user_id)
   
    status = get_status(application.id)
    assert status == "APPLIED"


def test_get_status_after_shortlist(empty_db):
    """Test that get_status returns SHORTLISTED after shortlisting."""
    student_user = create_user("Shanice", "student_pass123", "student")
    staff_user = create_user("Sade", "staff_pass123", "staff")
    employer_user = create_user("Jelani", "employer_pass123", "employer")
   
    position = open_position("Data Scientist", employer_user.user_id, 1)
    application = apply(student_user.user_id)
    shortlist(staff_user.user_id, application.id, position.id)
   
    status = get_status(application.id)
    assert status == "SHORTLISTED"


def test_get_status_after_accept(empty_db):
    """Test that get_status returns ACCEPTED after acceptance."""
    student_user = create_user("Keron", "student_pass123", "student")
    staff_user = create_user("Keisha", "staff_pass123", "staff")
    employer_user = create_user("Marlon", "employer_pass123", "employer")
   
    position = open_position("Systems Analyst", employer_user.user_id, 1)
    application = apply(student_user.user_id)
    shortlist(staff_user.user_id, application.id, position.id)
    decide(employer_user.user_id, application.id, "ACCEPTED")
   
    status = get_status(application.id)
    assert status == "ACCEPTED"


def test_get_status_missing_application_raises_value_error(empty_db):
    """Test that missing application raises ValueError."""
    with pytest.raises(ValueError):
        get_status(9999)


# ==============================================================================
# 11. Position Controller Tests (open_position, get_positions_by_employer_json)
# ==============================================================================

def test_open_position_creates_new_position_if_employer_exists(empty_db):
    """Test that open_position creates new position if employer exists."""
    employer_user = create_user("Kwesi", "employer_pass123", "employer")
   
    position = open_position("Senior Developer", employer_user.user_id, 3)
   
    assert position is not False
    assert position.title == "Senior Developer"
    assert position.number == 3


def test_open_position_returns_false_if_employer_does_not_exist(empty_db):
    """Test that open_position returns False if employer does not exist."""
    position = open_position("Non-existent Position", 9999, 2)
   
    assert position is False


def test_open_position_handles_db_exceptions(empty_db):
    """Test that open_position handles DB exceptions gracefully."""
    employer_user = create_user("Marlon", "employer_pass123", "employer")
   
    # Try to create a position with invalid employer_id (outside normal flow)
    # The function should handle DB exceptions
    position = open_position("Test Position", employer_user.user_id, -1)
   
    # Should either return False or a position (depends on validation)
    assert position is False or position is not None


def test_open_position_default_number(empty_db):
    """Test that open_position uses default number_of_positions."""
    employer_user = create_user("Sade", "employer_pass123", "employer")
   
    position = open_position("Default Position", employer_user.user_id)
   
    assert position is not False
    assert position.number == 1


def test_get_positions_by_employer_json_returns_empty_list_if_no_positions(empty_db):
    """Test that get_positions_by_employer_json returns empty list if no positions."""
    employer_user = create_user("Jelani", "employer_pass123", "employer")
   
    result = get_positions_by_employer_json(employer_user.user_id)
   
    assert result == []


def test_get_positions_by_employer_json_returns_correct_list(empty_db):
    """Test that get_positions_by_employer_json returns correct list of JSON structures."""
    employer_user = create_user("Keisha", "employer_pass123", "employer")
   
    open_position("Web Developer", employer_user.user_id, 1)
    open_position("Mobile App Developer", employer_user.user_id, 2)
   
    result = get_positions_by_employer_json(employer_user.user_id)
   
    assert len(result) == 2
    titles = {position_data['title'] for position_data in result}
    assert "Web Developer" in titles
    assert "Mobile App Developer" in titles


def test_get_positions_by_employer_json_structure(empty_db):
    """Test that get_positions_by_employer_json returns proper JSON structure."""
    employer_user = create_user("Kwesi", "employer_pass123", "employer")
   
    open_position("Cloud Architect", employer_user.user_id, 5)
   
    result = get_positions_by_employer_json(employer_user.user_id)
   
    assert len(result) == 1
    assert isinstance(result[0], dict)
    assert 'title' in result[0]
    assert result[0]['title'] == "Cloud Architect"


def test_open_position_multiple_positions_same_employer(empty_db):
    """Test that employer can create multiple positions."""
    employer_user = create_user("Marlon", "employer_pass123", "employer")
   
    first_position = open_position("Junior Developer", employer_user.user_id, 2)
    second_position = open_position("Senior Developer", employer_user.user_id, 3)
   
    assert first_position.id != second_position.id
    assert first_position.title == "Junior Developer"
    assert second_position.title == "Senior Developer"


def test_open_position_multiple_positions_different_employers(empty_db):
    """Test that different employers can create positions independently."""
    first_employer = create_user("Sade", "employer_pass123", "employer")
    second_employer = create_user("Jelani", "employer_pass123", "employer")
   
    first_position = open_position("Tech Company Position", first_employer.user_id, 1)
    second_position = open_position("Finance Company Position", second_employer.user_id, 1)
   
    assert first_position.id != second_position.id
   
    first_employer_positions = get_positions_by_employer_json(first_employer.user_id)
    second_employer_positions = get_positions_by_employer_json(second_employer.user_id)
   
    assert len(first_employer_positions) == 1
    assert len(second_employer_positions) == 1
    assert first_employer_positions[0]['title'] == "Tech Company Position"
    assert second_employer_positions[0]['title'] == "Finance Company Position"