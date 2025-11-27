import pytest
from App.controllers.application import apply, shortlist, decide, get_status
from App.controllers.position import open_position, get_positions_by_employer_json
from App.models import Position, Shortlist
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
# 1. Full Student Application Workflow
# ==============================================================================

def test_full_application_workflow_applied_to_accepted(empty_db):
    """Test complete workflow: Student applies → Staff shortlists → Employer accepts"""
    student_user = create_user("Keron", "student_pass123", "student")
    employer_user = create_user("Marlon", "employer_pass123", "employer")
    staff_user = create_user("Sade", "staff_pass123", "staff")
    
    position = open_position("Software Engineer", employer_user.user_id, 3)
    initial_positions = position.number_of_positions
    
    application = apply(student_user.user_id)
    assert get_status(application.id) == "APPLIED"
    
    shortlist_entry = shortlist(staff_user.user_id, application.id, position.id)
    assert shortlist_entry is not None
    assert get_status(application.id) == "SHORTLISTED"
    
    result = decide(employer_user.user_id, application.id, "ACCEPTED")
    assert result is not None
    assert get_status(application.id) == "ACCEPTED"
    
    updated_position = Position.query.get(position.id)
    assert updated_position.number_of_positions == initial_positions - 1
    
    updated_shortlist = Shortlist.query.get(shortlist_entry.id)
    assert updated_shortlist.status.value == "ACCEPTED"


def test_full_application_workflow_multiple_students(empty_db):
    """Test that multiple students can apply and be processed independently."""
    employer_user = create_user("Kwesi", "employer_pass123", "employer")
    staff_user = create_user("Jelani", "staff_pass123", "staff")
    
    first_student = create_user("Shanice", "student_pass123", "student")
    second_student = create_user("Aaliyah", "student_pass123", "student")
    third_student = create_user("Deon", "student_pass123", "student")
    
    position = open_position("Data Scientist", employer_user.user_id, 2)
    
    first_application = apply(first_student.user_id)
    second_application = apply(second_student.user_id)
    third_application = apply(third_student.user_id)
    
    shortlist(staff_user.user_id, first_application.id, position.id)
    shortlist(staff_user.user_id, second_application.id, position.id)
    shortlist(staff_user.user_id, third_application.id, position.id)
    
    decide(employer_user.user_id, first_application.id, "ACCEPTED")
    decide(employer_user.user_id, second_application.id, "ACCEPTED")
    decide(employer_user.user_id, third_application.id, "REJECTED")
    
    assert get_status(first_application.id) == "ACCEPTED"
    assert get_status(second_application.id) == "ACCEPTED"
    assert get_status(third_application.id) == "REJECTED"
    
    updated_position = Position.query.get(position.id)
    assert updated_position.number_of_positions == 0


# ==============================================================================
# 2. Reject Flow
# ==============================================================================

def test_reject_flow(empty_db):
    """Test rejection workflow"""
    student_user = create_user("Ria", "student_pass123", "student")
    employer_user = create_user("Keisha", "employer_pass123", "employer")
    staff_user = create_user("Sade", "staff_pass123", "staff")
    
    position = open_position("Project Manager", employer_user.user_id, 2)
    initial_positions = position.number_of_positions
    
    application = apply(student_user.user_id)
    shortlist_entry = shortlist(staff_user.user_id, application.id, position.id)
    
    result = decide(employer_user.user_id, application.id, "REJECTED")
    assert result is not None
    
    assert get_status(application.id) == "REJECTED"
    
    updated_position = Position.query.get(position.id)
    assert updated_position.number_of_positions == initial_positions
    
    updated_shortlist = Shortlist.query.get(shortlist_entry.id)
    assert updated_shortlist.status.value == "REJECTED"


def test_reject_flow_does_not_decrement_positions(empty_db):
    """Test that rejection doesn't decrement position availability."""
    employer_user = create_user("Marlon", "employer_pass123", "employer")
    staff_user = create_user("Jelani", "staff_pass123", "staff")
    first_student = create_user("Keron", "student_pass123", "student")
    second_student = create_user("Shanice", "student_pass123", "student")
    
    position = open_position("HR Specialist", employer_user.user_id, 1)
    
    first_application = apply(first_student.user_id)
    second_application = apply(second_student.user_id)
    
    shortlist(staff_user.user_id, first_application.id, position.id)
    shortlist(staff_user.user_id, second_application.id, position.id)
    
    decide(employer_user.user_id, first_application.id, "ACCEPTED")
    decide(employer_user.user_id, second_application.id, "REJECTED")
    
    updated_position = Position.query.get(position.id)
    assert updated_position.number_of_positions == 0


def test_multiple_rejections_do_not_affect_position_count(empty_db):
    """Test that multiple rejections don't affect position availability."""
    employer_user = create_user("Kwesi", "employer_pass123", "employer")
    staff_user = create_user("Keisha", "staff_pass123", "staff")
    
    position = open_position("QA Engineer", employer_user.user_id, 5)
    initial_count = position.number_of_positions
    
    for i in range(3):
        student_user = create_user(f"student_user{i}", "student_pass123", "student")
        application = apply(student_user.user_id)
        shortlist(staff_user.user_id, application.id, position.id)
        decide(employer_user.user_id, application.id, "REJECTED")
    
    updated_position = Position.query.get(position.id)
    assert updated_position.number_of_positions == initial_count


# ==============================================================================
# 3. Prevent Invalid Transitions
# ==============================================================================

def test_employer_cannot_accept_without_shortlisting(empty_db):
    """Test that employer cannot accept without shortlisting."""
    student_user = create_user("Aaliyah", "student_pass123", "student")
    employer_user = create_user("Sade", "employer_pass123", "employer")
    
    application = apply(student_user.user_id)
    
    with pytest.raises(InvalidTransitionError):
        decide(employer_user.user_id, application.id, "ACCEPTED")


def test_cannot_shortlist_after_accept(empty_db):
    """Test that shortlisting after accept doesn't corrupt state."""
    student_user = create_user("Deon", "student_pass123", "student")
    employer_user = create_user("Marlon", "employer_pass123", "employer")
    staff_user = create_user("Jelani", "staff_pass123", "staff")
    
    first_position = open_position("Backend Developer", employer_user.user_id, 1)
    application = apply(student_user.user_id)
    
    shortlist(staff_user.user_id, application.id, first_position.id)
    decide(employer_user.user_id, application.id, "ACCEPTED")
    
    assert get_status(application.id) == "ACCEPTED"
    
    second_position = open_position("Frontend Developer", employer_user.user_id, 1)
    
    try:
        result = shortlist(staff_user.user_id, application.id, second_position.id)
        assert get_status(application.id) == "ACCEPTED"
    except (InvalidTransitionError, ValueError):
        assert get_status(application.id) == "ACCEPTED"


def test_cannot_shortlist_before_apply(empty_db):
    """Test that you can't shortlist a non-existent application."""
    staff_user = create_user("Keisha", "staff_pass123", "staff")
    employer_user = create_user("Kwesi", "employer_pass123", "employer")
    
    position = open_position("DevOps Engineer", employer_user.user_id, 1)
    
    with pytest.raises(ValueError):
        shortlist(staff_user.user_id, 9999, position.id)


def test_invalid_decision_value_raises_error(empty_db):
    """Test that invalid decision values raise ValueError."""
    student_user = create_user("Ria", "student_pass123", "student")
    employer_user = create_user("Sade", "employer_pass123", "employer")
    staff_user = create_user("Jelani", "staff_pass123", "staff")
    
    position = open_position("Machine Learning Engineer", employer_user.user_id, 1)
    application = apply(student_user.user_id)
    shortlist(staff_user.user_id, application.id, position.id)
    
    with pytest.raises(ValueError):
        decide(employer_user.user_id, application.id, "MAYBE_LATER")


# ==============================================================================
# 4. Duplicate Shortlisting Handling
# ==============================================================================

def test_duplicate_shortlisting_returns_existing_record(empty_db):
    """Test that shortlisting same application-position twice returns existing record"""
    student_user = create_user("Keron", "student_pass123", "student")
    employer_user = create_user("Marlon", "employer_pass123", "employer")
    staff_user = create_user("Keisha", "staff_pass123", "staff")
    
    position = open_position("Solutions Architect", employer_user.user_id, 1)
    application = apply(student_user.user_id)
    
    first_shortlist = shortlist(staff_user.user_id, application.id, position.id)
    assert first_shortlist is not None
    assert get_status(application.id) == "SHORTLISTED"
    
    second_shortlist = shortlist(staff_user.user_id, application.id, position.id)
    
    assert first_shortlist.id == second_shortlist.id
    assert get_status(application.id) == "SHORTLISTED"


# ==============================================================================
# 5. Multi-Employer Boundary Test
# ==============================================================================

def test_different_employers_independent_positions(empty_db):
    """Test that Employer A's positions are independent from Employer B's positions."""
    first_employer = create_user("Kwesi", "employer_pass123", "employer")
    second_employer = create_user("Sade", "employer_pass123", "employer")
    staff_user = create_user("Jelani", "staff_pass123", "staff")
    
    student_user = create_user("Shanice", "student_pass123", "student")
    
    first_position = open_position("Position from First Company", first_employer.user_id, 1)
    second_position = open_position("Position from Second Company", second_employer.user_id, 1)
    
    assert first_position.id != second_position.id
    assert first_position.employer_id == first_employer.id
    assert second_position.employer_id == second_employer.id
    
    application = apply(student_user.user_id)
    shortlist(staff_user.user_id, application.id, first_position.id)
    
    decide(first_employer.user_id, application.id, "ACCEPTED")
    
    updated_first_position = Position.query.get(first_position.id)
    updated_second_position = Position.query.get(second_position.id)
    
    assert updated_first_position.number_of_positions == 0
    assert updated_second_position.number_of_positions == 1