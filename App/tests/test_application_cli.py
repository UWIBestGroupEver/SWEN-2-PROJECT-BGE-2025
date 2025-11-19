#tests/test_application_cli.py
import pytest

from App.main import create_app
from App.database import db
from App.models import Application, ApplicationStatus,Employer
from App.controllers.application import apply, shortlist, decide, get_status
from App.controllers import create_user, open_position 

@pytest.fixture(scope="function") #setup a new database for each test
def app():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///test.db'})
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def setup_data(app):
    with app.app_context():
        staff=create_user("staff1", "pass", "staff")
        employer=create_user("emp1", "pass", "employer")
        student=create_user("stu1", "pass", "student")
        position=open_position("Intern", employer.user_id, 1)

        return{
            'staff.id':staff.user_id,
            'employer.id':employer.user_id,
            'student.id':student.user_id,
            'position.id':position.id if position else None
        }

def test_employer_accepts_application_cli(runner,app,setup_data): #retreive necessary IDs from the setup data
    employer_id = setup_data['employer.id']
    staff_id = setup_data['staff.id']
    student_id = setup_data['student.id']
    position_id = setup_data['position.id']

    with app.app_context():
        #1) student applies
        application=apply(student_id)
        application_id=application.id

        assert application.status==ApplicationStatus.APPLIED #verify initial state

        #2) staff shortlists the application
        shortlist(staff_id,application_id,position_id) #staff shortlists the application
        app_post_shortlist=Application.query.get(application_id)

        assert app_post_shortlist.status==ApplicationStatus.SHORTLISTED #verify shortlisted state

        #3) employer accepts the application
        assert Employer.query.filter_by(user_id=employer_id).first() is not None
        result=runner.invoke(
            args=['employer','accept_application',str(employer_id),str(application_id)],
        )

        assert 'accepted!' in result.output #verify output message
        assert result.exit_code==0

        final_app=Application.query.get(application_id)
        assert final_app.status==ApplicationStatus.ACCEPTED #verify final accepted state

def test_employer_rejects_application_cli(runner,app,setup_data):
    employer_id = setup_data['employer.id']
    staff_id = setup_data['staff.id']
    student_id = setup_data['student.id']
    position_id = setup_data['position.id']

    with app.app_context():
        #1) student applies
        application=apply(student_id)
        application_id=application.id

        assert application.status==ApplicationStatus.APPLIED #verify initial state

        #2) staff shortlists the application
        shortlist(staff_id,application_id,position_id) #staff shortlists the application
        app_post_shortlist=Application.query.get(application_id)

        assert app_post_shortlist.status==ApplicationStatus.SHORTLISTED #verify shortlisted state

        #3) employer rejects the application
        result=runner.invoke(
            args=['employer','reject_application',str(employer_id),str(application_id)],
        )

        assert 'rejected.' in result.output #verify output message
        assert result.exit_code==0

        final_app=Application.query.get(application_id)
        assert final_app.status==ApplicationStatus.REJECTED #verify final rejected state