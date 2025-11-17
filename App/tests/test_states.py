# Test cases for application state transitions to ensure correctness of the State Pattern implementation.

import pytest

from App import create_app
from App.models.application import Application, ApplicationStatus
from App.models.states import InvalidTransitionError


@pytest.fixture
def app_context():
    """Provides a Flask app context for tests."""
    flask_app = create_app()
    with flask_app.app_context():
        yield


def test_valid_transitions(app_context):
    # Start in APPLIED state
    application = Application(student_id=1)
    assert application.status == ApplicationStatus.APPLIED

    # APPLIED → SHORTLISTED
    application.shortlist()
    assert application.status == ApplicationStatus.SHORTLISTED

    # SHORTLISTED → ACCEPTED
    application.accept()
    assert application.status == ApplicationStatus.ACCEPTED


def test_invalid_transition_from_accepted(app_context):
    # APPLIED → SHORTLISTED → ACCEPTED
    application = Application(student_id=1)
    application.shortlist()
    application.accept()
    assert application.status == ApplicationStatus.ACCEPTED

    # Now try an illegal transition
    with pytest.raises(InvalidTransitionError):
        application.shortlist()


def test_default_status_is_applied(app_context):
    application = Application(student_id=1)
    assert application.status == ApplicationStatus.APPLIED


def test_rejected_flow_from_shortlisted(app_context):
    # APPLIED → SHORTLISTED → REJECTED
    application = Application(student_id=1)
    application.shortlist()
    assert application.status == ApplicationStatus.SHORTLISTED

    application.reject()
    assert application.status == ApplicationStatus.REJECTED


def test_invalid_transition_applied_to_accepted(app_context):
    # Should NOT be able to jump APPLIED → ACCEPTED directly
    application = Application(student_id=1)

    with pytest.raises(InvalidTransitionError):
        application.accept()


def test_invalid_transition_from_rejected(app_context):
    # APPLIED → SHORTLISTED → REJECTED
    application = Application(student_id=1)
    application.shortlist()
    application.reject()
    assert application.status == ApplicationStatus.REJECTED

    # All further moves should be invalid
    with pytest.raises(InvalidTransitionError):
        application.shortlist()

    with pytest.raises(InvalidTransitionError):
        application.accept()


def test_invalid_double_accept(app_context):
    application = Application(student_id=1)
    application.shortlist()
    application.accept()
    assert application.status == ApplicationStatus.ACCEPTED

    # Accepting again should not be allowed
    with pytest.raises(InvalidTransitionError):
        application.accept()
