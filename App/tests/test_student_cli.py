import pytest

from App.main import create_app
from App.database import db, create_db
from App.models.student import Student
from App.models.application import Application
from App.controllers import create_user, get_user_by_username, open_position
from App.controllers.application import apply, shortlist, decide

import wsgi as wsgi_module


@pytest.fixture(autouse=True, scope="function")
def app_with_db():
    # Create a test app with an isolated SQLite DB
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db'})
    with app.app_context():
        create_db()
        # register CLI groups from wsgi so test app has the commands
        app.cli.add_command(wsgi_module.user_cli)
        app.cli.add_command(wsgi_module.student_cli)
        yield app
        db.drop_all()


def test_student_create_cli(app_with_db):
    runner = app_with_db.test_cli_runner()
    # The updated CLI `student create` reads interactive input in order:
    # username, password, gpa, degree
    input_payload = 'studcli\nstudpass\n3.75\nComputer Science\n'
    result = runner.invoke(args=['student', 'create'], input=input_payload)
    assert result.exit_code == 0
    assert 'studcli' in result.output

    # verify Student record created and fields saved
    student = Student.query.filter_by(username='studcli').first()
    assert student is not None
    # degree should be the string provided
    assert student.degree == 'Computer Science'
    # gpa column is Float; allow approximate comparison
    assert float(student.gpa) == pytest.approx(3.75)


def test_student_apply_cli(app_with_db):
    # create a student via controller so we have a User/Student pair
    student_user = create_user('applystu', 'apass', 'student')

    runner = app_with_db.test_cli_runner()
    # pass the user id (User.id) to the CLI apply command
    result = runner.invoke(args=['student', 'apply', str(student_user.id)])
    assert result.exit_code == 0
    assert 'Application' in result.output
    assert 'applystu' in result.output

    # verify an Application row exists
    app_obj = Application.query.first()
    assert app_obj is not None


def test_application_status_cli_applied(app_with_db):
    # create a student and an application
    student = create_user('statstu', 'pass', 'student')
    app_obj = apply(student.id)

    runner = app_with_db.test_cli_runner()
    result = runner.invoke(args=['student', 'applicationStatus', str(app_obj.id)])

    assert result.exit_code == 0
    assert f'Application {app_obj.id} status is APPLIED' in result.output


def test_application_status_cli_nonexistent(app_with_db):
    runner = app_with_db.test_cli_runner()
    result = runner.invoke(args=['student', 'applicationStatus', '9999'])

    assert result.exit_code == 0
    assert 'Application 9999 does not exist' in result.output


def test_application_status_cli_after_shortlist_and_decide(app_with_db):
    # create student, staff, employer, position, and progress an application
    student = create_user('flowstu', 'pass', 'student')
    staff = create_user('flowstaff', 'pass', 'staff')
    employer = create_user('flowemp', 'pass', 'employer')
    position = open_position('Intern Test', employer.id, 1)

    app_obj = apply(student.id)
    sl = shortlist(staff.id, app_obj.id, position.id)
    # after shortlist, status should be SHORTLISTED
    runner = app_with_db.test_cli_runner()
    result1 = runner.invoke(args=['student', 'applicationStatus', str(app_obj.id)])
    assert result1.exit_code == 0
    assert 'SHORTLISTED' in result1.output

    # decide to accept
    decided = decide(employer.id, app_obj.id, 'ACCEPTED')
    
    result2 = runner.invoke(args=['student', 'applicationStatus', str(app_obj.id)])

    assert result2.exit_code == 0
    assert 'ACCEPTED' in result2.output
