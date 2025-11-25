import click, pytest, sys
from flask.cli import with_appcontext, AppGroup

from App.database import db, get_migrate
from App.models import User, Position, Student, Employer, Staff, Application, Shortlist
from App.models.application_status import ApplicationStatus
from App.models.position import PositionStatus
from App.main import create_app
from App.controllers import ( create_user, get_all_users_json, get_all_users, initialize, open_position, add_student_to_shortlist, decide_shortlist, get_shortlist_by_student, get_shortlist_by_position, get_positions_by_employer)
from App.controllers.application import (apply, shortlist, decide)
from App.controllers.student import add_gpa_to_student, add_degree_to_student, create_student
from App.controllers.user import get_user
from App.models.shortlist import DecisionStatus


# This commands file allow you to create convenient CLI commands for testing controllers
#--------------------------------------------App Commands--------------------------------------------##
app = create_app()
migrate = get_migrate(app)

# This command creates and initializes the database
@app.cli.command("init", help="Creates and initializes the database")
def init():
    initialize()
    print('database intialized')

#command to list all users
@app.cli.command("list_users", help="Lists all users in the database")
def list_users():
    print('\nUsers:\n')
    users = User.query.all()
    for user in users:
        print(f'UserID: {user.id}, Username: {user.username}, Role: {user.role}')
    print("\n")


#command to list all students
@app.cli.command("list_students", help="Lists all students in the database")
def list_students():
    print('\nStudents:\n')
    students = Student.query.all()
    for student in students:
        print(f'UserID: {student.user_id}, Username: {student.username}, GPA: {student.gpa}, Degree: {student.degree}')
    print("\n")


#command to list all employers
@app.cli.command("list_employers", help="Lists all employers in the database")
def list_employers():
    print('\nEmployers:\n')
    employers = Employer.query.all()
    for employer in employers:
        print(f'UserID: {employer.user_id}, Username: {employer.username}')
    print("\n")


#command to list all staff
@app.cli.command("list_staff", help="Lists all staff in the database")
def list_staff():
    print('\nStaff:\n')
    staff_members = Staff.query.all()
    for staff in staff_members:
        print(f'UserID: {staff.user_id}, Username: {staff.username}')
    print("\n")


#command to list all positions
@app.cli.command("list_positions", help="Lists all positions in the database")
def list_positions():
    print('\nPositions:\n')
    positions = Position.query.all()
    for position in positions:
        print(f'PositionID: {position.id}, Title: {position.title}, Number of Positions: {position.number_of_positions}, Status: {position.status.value}, EmployerID: {position.employer_id}')
    print("\n")


#command to list all applications
@app.cli.command("list_applications", help="Lists all applications in the database")
def list_applications():
    print('\nApplications:\n')
    applications = Application.query.all()
    for application in applications:
        print(f'ApplicationID: {application.id}, StudentID: {application.student.user_id if application.student else "Unknown"}, Status: {application.status.value}')
    print("\n")


#command to list all shortlists
@app.cli.command("list_shortlist", help="Lists all shortlists in the database")
def list_shortlists():
    print('\nShortlisted Applications:\n')
    shortlists = Shortlist.query.all()
    for shortlist in shortlists:
        print(f'ShortlistID: {shortlist.id}, ApplicationID: {shortlist.application_id}, PositionID: {shortlist.position_id}, StaffID: {shortlist.staff.user_id if shortlist.staff else "Unknown"}, Status: {shortlist.status.value}')
    print("\n")


#command to list all approved applications
@app.cli.command("view_approved_applications", help="Lists all approved applications in the database")
def view_approved_applications():
    print('\nApproved Applications:\n')
    applications = Application.query.filter_by(status=ApplicationStatus.APPROVED).all()
    for application in applications:
        print(f'ApplicationID: {application.id}, StudentID: {application.student.user_id if application.student else "Unknown"}, Status: {application.status.value}')
    print("\n")


#command to list all rejected applications
@app.cli.command("view_rejected_applications", help="Lists all rejected applications in the database")
def view_rejected_applications():
    print('\nRejected Applications:\n')
    applications = Application.query.filter_by(status=ApplicationStatus.REJECTED).all()
    for application in applications:
        print(f'ApplicationID: {application.id}, StudentID: {application.student.user_id if application.student else "Unknown"}, Status: {application.status.value}')


@app.cli.command("view_pending_applications", help="Lists all pending applications in the database")
def view_pending_applications():
    print("\nPending Applications:\n")
    applications = Application.query.filter_by(status=ApplicationStatus.APPLIED).all()
    for application in applications:
        print(f'ApplicationID: {application.id}, StudentID: {application.student.user_id if application.student else "Unknown"}, Status: {application.status.value}')
    print("\n")

##--------------------------------------------Student Commands--------------------------------------------##



student_cli = AppGroup('student', help='Student object commands')

@student_cli.command("create", help="Creates a student user")
def create_student_command():

    username = input("Enter username: ")
    password = input("Enter password: ")
    gpa = input("Enter GPA: ")
    degree = input("Enter Degree: ")
    
    result = create_user(username, password, "student")

    add_degree_to_student(result.id, degree)
    add_gpa_to_student(result.id, gpa)
    

    if result:
        try:
            print(f'Student {username} created with userID {result.user_id}!')
        except Exception:
            print(f'Student {username} created!')
    else:
        print("Student creation failed")
        
        
@student_cli.command("apply", help="Student sends in an application")

def apply_command():
    student_id = input("Enter student userID: ")
    try:
        application = apply(student_id)
        student = Student.query.filter_by(user_id=student_id).first()
        username = student.username if student else "Unknown"
        print(f'Application created for student {username}, ApplicationID: {application.id}!')

    except PermissionError as e:
        print(str(e))

@student_cli.command("application_status", help="Get the status of an application")
def application_status_command():
    application_id = input("Enter application ID: ")
    application = Application.query.get(application_id)
    if application:
        print(f'Application {application.id} status is {application.status.value}')
    else:
        print(f'Application {application_id} does not exist')

app.cli.add_command(student_cli)



##--------------------------------------------Staff Commands--------------------------------------------##
staff_cli = AppGroup('staff', help='Staff object commands')

@staff_cli.command("create", help="Creates a staff user")
def create_staff_command():
    username = input("Enter username: ")
    password = input("Enter password: ")
    
    result = create_user(username, password, "staff")
    
    if result:
        try:
            print(f'Staff {username} created with userID {result.user_id}!')
        except Exception:
            print(f'Staff {username} created!')
    else:
        print("Staff creation failed")


@staff_cli.command("shortlist", help="Staff shortlists an application")
def shortlist_command():
    
    print("\n")
    staff_id = input("Please Enter staff userID: ")

    # Check if staff exists
    if not Staff.query.filter_by(user_id=staff_id).first():
        print(f"Only Staff members can shortlist applications. No staff found with user ID {staff_id}.")
        return
    
    # Only show applications that are in the APPLIED state
    apps = Application.query.filter_by(status=ApplicationStatus.APPLIED).order_by(Application.id).all()
    if not apps:
        print('No applications found')
        return

    print("\nApplications:")
    for a in apps:
        student_name = a.student.username if getattr(a, 'student', None) else 'Unknown'
        student_user_id = a.student.user_id if getattr(a, 'student', None) else 'Unknown'
        student_gpa = a.student.gpa if getattr(a, 'student', None) else 'Unknown'
        student_degree = a.student.degree if getattr(a, 'student', None) else 'Unknown'
        print(f'ApplicationID: {a.id}: Student {student_name} (UserID: {student_user_id}), Degree: {student_degree}, GPA: {student_gpa} — Status: {a.status.value}')

    # Show all OPEN positions
    open_positions = Position.query.filter_by(status=PositionStatus.open).order_by(Position.id).all()

    print("\nOpen Positions:")
    if not open_positions:
        print("No open positions available.")
        return

    for p in open_positions:
        print(f'Position {p.id}: {p.title} — Openings: {p.number_of_positions} (Employer {p.employer_id})')

    application_id = input("\nEnter application ID: ")
    position_id = input("Enter position ID: ")

    name = Position.query.get(position_id).title if Position.query.get(position_id) else "Unknown"
    studentname = Application.query.get(application_id).student.username if Application.query.get(application_id) and Application.query.get(application_id).student else "Unknown"
    staff = get_user(staff_id) 
    staffname = staff.username if User else "Unknown"
    try:
        sl = shortlist(staff_id, application_id, position_id)
        print(f'\nApplication {sl.application_id} ({studentname}) shortlisted for position {name} (ID:{sl.position_id}) by {staffname} (StaffID:{staff_id})!\n')
    except PermissionError as e:
        print(str(e))


app.cli.add_command(staff_cli)


##-----------------------------------------Employer Commands-----------------------------------------##

employer_cli = AppGroup('employer', help='Employer object commands')

@employer_cli.command("create", help="Creates an employer user")
def create_employer_command():
    username = input("Enter username: ")
    password = input("Enter password: ")
    
    result = create_user(username, password, "employer")
    
    if result:
        try:
            print(f'Employer {username} created with userID {result.user_id}!')
        except Exception:
            print(f'Employer {username} created!')
    else:
        print("Employer creation failed")


@employer_cli.command("open_position", help="Employer opens a position")
def open_position_command():
    employer_id = input("Enter employer userID: ")
    
    if not Employer.query.filter_by(user_id=employer_id).first():
        print(f"No employer found with user ID {employer_id}.")
        return
    
    title = input("Enter position title: ")
    number = input("Enter number of positions: ")
    
    position = open_position(title, employer_id, int(number))
    if position:
        print(f'Position {title} created!')
    else:
        print(f'Employer {employer_id} does not exist')



@employer_cli.command("decide", help="Employer accepts or denies an application")
def decide_application_command():
    employer_id = input("Enter employer ID: ")
    
    # Retrieve the employer
    employer = Employer.query.filter_by(user_id=employer_id).first()
    if not employer:
        print(f"No employer found with user ID {employer_id}.")
        return
    
    # Get all positions for this employer
    positions = Position.query.filter_by(employer_id=employer.id).all()
    if not positions:
        print(f"No positions found for employer {employer.username} (User ID: {employer_id}).")
        return
    
    # Display shortlisted applications for the employer's positions
    print(f"\nShortlisted Applications for Positions Offered by {employer.username} (Employer User ID: {employer_id}):")
    shortlisted_found = False
    for position in positions:
        shortlists = Shortlist.query.filter_by(position_id=position.id, status=DecisionStatus.PENDING).all()
        if shortlists:
            shortlisted_found = True
            print(f"\nPosition: {position.title} (ID: {position.id}, Openings: {position.number_of_positions})")
            for sl in shortlists:
                application = sl.application
                if application and application.student:
                    student = application.student
                    print(f"  - Application ID: {application.id}, Student: {student.username} (User ID: {student.user_id}), Degree: {student.degree}, GPA: {student.gpa}, Status: {sl.status.value}")
                else:
                    print(f"  - Application ID: {application.id} (Student details unavailable), Status: {sl.status.value}")
    
    if not shortlisted_found:
        print("No shortlisted applications pending decision for your positions.")
        return
    
    application_id = input("\nEnter application ID to make a decision on: ")
    descesion = input("Enter decision (Accept = 1 /Reject = 0): ")
    if descesion not in ["1", "0"]:
        print("Invalid decision. Please enter '1' for Accept or '0' for Reject.")
        return
    if descesion == "1":
        verdict = "ACCEPTED"
    if descesion == "0":
        verdict = "REJECTED"
    application=decide(employer_id,application_id, verdict)
    if application:
        print(f'Application {application_id} {verdict}!')
        print("\n\n__________________________________________________________________________\n\n")
    else:
        print(f'Application {application_id} could not be {verdict}')
        print("\n\n__________________________________________________________________________\n\n")
   

app.cli.add_command(employer_cli) # add the group to the cli


'''
Test Commands
'''

test = AppGroup('test', help='Testing commands') 

@test.command("all", help="Run all tests")
def all_tests_command():
    """Run all unit and integration tests"""
    sys.exit(pytest.main([
        "App/tests/unit_controller_tests.py",
        "App/tests/unit_model_tests.py", 
        "App/tests/integration_tests.py",
        "-v"
    ]))

@test.command("unitcontroller", help="Run all controller tests")
def controller_tests_command():
    """Run unit controller tests only"""
    sys.exit(pytest.main(["App/tests/unit_controller_tests.py", "-v"]))

@test.command("unitmodel", help="Run all model tests")
def model_tests_command():
    """Run unit model tests only"""
    sys.exit(pytest.main(["App/tests/unit_model_tests.py", "-v"]))

@test.command("integration", help="Run integration tests")
def integration_tests_command():
    """Run integration tests only"""
    sys.exit(pytest.main(["App/tests/integration_tests.py", "-v"]))


app.cli.add_command(test)