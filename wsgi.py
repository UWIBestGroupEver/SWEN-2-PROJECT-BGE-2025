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

# This commands file allow you to create convenient CLI commands for testing controllers

app = create_app()
migrate = get_migrate(app)

# This command creates and initializes the database
@app.cli.command("init", help="Creates and initializes the database")
def init():
    initialize()
    print('database intialized')

'''
User Commands
'''

# Commands can be organized using groups

# create a group, it would be the first argument of the comand
# eg : flask user <command>
user_cli = AppGroup('user', help='User object commands') 

# Then define the command and any parameters and annotate it with the group (@)
@user_cli.command("create", help="Creates a user")
@click.argument("username", default="rob")
@click.argument("password", default="robpass")
@click.argument("user_type", default="student")
def create_user_command(username, password, user_type):
    result = create_user(username, password, user_type)
    # `create_user` now returns the created User object on success, or False on failure
    if result:
        try:
            print(f'{username} created with id {result.id}!')
        except Exception:
            # fallback if a truthy non-user value is returned
            print(f'{username} created!')
    else:
        print("User creation failed")

# this command will be : flask user create bob bobpass

@user_cli.command("list", help="Lists users in the database")
@click.argument("format", default="string")
def list_user_command(format):
    if format == 'string':
        print(get_all_users())
    else:
        print(get_all_users_json())

@user_cli.command("add_position", help="Adds a position")
@click.argument("title", default="Software Engineer")
@click.argument("employer_id", default=1)
@click.argument("number", default=1)
def add_position_command(title, employer_id, number):
    position = open_position(title, employer_id, number)
    if position:
        print(f'{title} created!')
    else:
        print(f'Employer {employer_id} does not exist')

@user_cli.command("add_to_shortlist", help="Adds a student to a shortlist")
@click.argument("student_id", default=1)
@click.argument("position_id", default=1)
@click.argument("staff_id", default=1)
def add_to_shortlist_command(student_id, position_id, staff_id):
    test = add_student_to_shortlist(student_id, position_id, staff_id)
    if test:
        print(f'Student {student_id} added to shortlist for position {position_id}')
        print("\n\n__________________________________________________________________________\n\n")
    else:
        print('One of the following is the issue:')
        print(f'    Position {position_id} is not open')
        print(f'    Student {student_id} already in shortlist for position {position_id}')
        print(f'    There is no more open slots for position {position_id}')
        print("\n\n__________________________________________________________________________\n\n")

@user_cli.command("decide_shortlist", help="Decides on a shortlist")
@click.argument("student_id", default=1)
@click.argument("position_id", default=1)
@click.argument("decision", default="accepted")
def decide_shortlist_command(student_id, position_id, decision):
    test = decide_shortlist(student_id, position_id, decision)
    if test:
        print(f'Student {student_id} is {decision} for position {position_id}')
        print("\n\n__________________________________________________________________________\n\n")
    else:
        print(f'Student {student_id} not in shortlist for position {position_id}')
        print("\n\n__________________________________________________________________________\n\n")

@user_cli.command("get_shortlist", help="Gets a shortlist for a student")
@click.argument("student_id", default=1)
def get_shortlist_command(student_id):
    list = get_shortlist_by_student(student_id)
    if list:
        for item in list:
            print(f'Student {item.student_id} is {item.status.value} for position {item.position_id}')

        print("\n\n__________________________________________________________________________\n\n")
    else:
        print(f'Student {student_id} has no shortlists')
        print("\n\n__________________________________________________________________________\n\n")

@user_cli.command("get_shortlist_by_position", help="Gets a shortlist for a position")
@click.argument("position_id", default=1)
def get_shortlist_by_position_command(position_id):
    list = get_shortlist_by_position(position_id)
    if list:
        for item in list:
            print(f'Student {item.student_id} is {item.status.value} for {item.position.title} id: {item.position_id}')
            print(f'    Staff {item.staff_id} added this student to the shortlist')
            print(f'    Position {item.position_id} is {item.position.status.value}')
            print(f'    Position {item.position_id} has {item.position.number_of_positions} slots')
            print(f'    Position {item.position_id} is for {item.position.title}')
            print("\n\n__________________________________________________________________________\n\n")

    else:
        print(f'Position {position_id} has no shortlists')
        print("\n\n__________________________________________________________________________\n\n")

@user_cli.command("get_positions_by_employer", help="Gets all positions for an employer")
@click.argument("employer_id", default=1)
def get_positions_by_employer_command(employer_id):
    list = get_positions_by_employer(employer_id)
    if list:
        for item in list:
            print(f'Position {item.id} is {item.status.value}')
            print(f'    Position {item.id} has {item.number_of_positions} slots')
            print(f'    Position {item.id} is for {item.title}')
            print("\n\n__________________________________________________________________________\n\n")
    else:
            print(f'Employer {employer_id} has no positions')
            print("\n\n__________________________________________________________________________\n\n")
            
app.cli.add_command(user_cli) # add the group to the cli




##==========================================================================================================================================##
employer_cli = AppGroup('employer', help='Employer object commands')

@user_cli.command("accept_application", help="Employer accepts an application")
@click.argument("employer_id", default=1)
@click.argument("application_id", default=1)
def accept_application_command(employer_id,application_id):
    application=decide(employer_id,application_id,"accepted")
    if application:
        print(f'Application {application_id} accepted!')
        print("\n\n__________________________________________________________________________\n\n")
    else:
        print(f'Application {application_id} could not be accepted')
        print("\n\n__________________________________________________________________________\n\n")

@user_cli.command("reject_application", help="Employer rejects an application")
@click.argument("employer_id", default=1)
@click.argument("application_id", default=1)
def reject_application_command(employer_id,application_id):
    application=decide(employer_id,application_id,"rejected")
    if application:
        print(f'Application {application_id} rejected.')
        print("\n\n__________________________________________________________________________\n\n")
    else:
        print(f'Application {application_id} could not be rejected')
        print("\n\n__________________________________________________________________________\n\n")

app.cli.add_command(employer_cli) # add the group to the cli

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

@student_cli.command("applicationStatus", help="Get the status of an application")
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

























'''
Test Commands
'''

test = AppGroup('test', help='Testing commands') 

@test.command("user", help="Run User tests")
@click.argument("type", default="all")
def user_tests_command(type):
    if type == "unit":
        sys.exit(pytest.main(["-k", "UserUnitTests"]))
    elif type == "int":
        sys.exit(pytest.main(["-k", "UserIntegrationTests"]))
    else:
        sys.exit(pytest.main(["-k", "App"]))
    

app.cli.add_command(test)