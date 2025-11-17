# tests/test_state_pattern.py

import pytest

from App import create_app
from App.models.application import Application, ApplicationStatus
from App.models.states import (
    InvalidTransitionError,
)


@pytest.fixture
def app_context():
    """Provides a Flask app context for tests."""
    flask_app = create_app()
    with flask_app.app_context():
        yield


def test_valid_transitions(app_context):
    # Start in APPLIED state
    application = Application(student_id=1, position_id=10)
    assert application.status == ApplicationStatus.APPLIED

    # Applied → Shortlisted
    application.shortlist()
    assert application.status == ApplicationStatus.SHORTLISTED

    # Shortlisted → Accepted
    application.accept()
    assert application.status == ApplicationStatus.ACCEPTED


def test_invalid_transition_from_accepted(app_context):
    # Start in APPLIED → SHORTLISTED → ACCEPTED
    application = Application(student_id=1, position_id=10)
    application.shortlist()
    application.accept()

    # Now try an illegal transition
    with pytest.raises(InvalidTransitionError):
        application.shortlist()
