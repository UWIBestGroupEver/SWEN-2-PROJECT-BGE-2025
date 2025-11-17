import pytest

from App.main import create_app
from App.database import db, create_db
from App.models.student import Student
from App.models.application import Application
from App.controllers import create_user, get_user_by_username

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
    result = runner.invoke(args=['student', 'create', 'studcli', 'studpass'])
    assert result.exit_code == 0
    assert 'studcli' in result.output

    # verify Student record created
    student = Student.query.filter_by(username='studcli').first()
    assert student is not None


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
