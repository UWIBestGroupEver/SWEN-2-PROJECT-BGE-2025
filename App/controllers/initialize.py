from .user import create_user
from .shortlist import add_student_to_shortlist
from .position import open_position
from .application import apply
from .application import shortlist
from App.models.application import Application
from App.models.student import Student
from App.database import db

import random


def initialize():
    db.drop_all()
    db.create_all()

    employers=create_employers()
    staff=create_staff()
    students=create_students()

    positions=open_positions(employers)
    apply_students(students)
    assign_shortlist(students,positions,staff)

def create_employers():
    users=[]
    for uname in ('frank','tyler','earl','syd','dom'):
        u=create_user(uname, f'{uname}pass', "employer")
        if u:
            users.append(u)
    return users

def create_staff():
    users=[]
    for uname in ('kevin','matt','ciaran','joba','merlyn'):
        u=create_user(uname, f'{uname}pass', "staff")
        if u:
            users.append(u)
    return users

def create_students():
    names=['george','sarah','gus','jamie','earnest']
    gpas=[3.5,3.7,3.2,3.8,4.0]
    degrees=['Computer Science','Mechanical Engineering','Design','Design','Database Management']

    random.shuffle(gpas)
    #random.shuffle(degrees)

    users=[]
    for name,gpa,deg in zip(names,gpas,degrees):
        u=create_user(name, f'{name}pass', "student",gpa=gpa,degree=deg)
        if not u:
            continue
        
        users.append(u)
    return users

def open_positions(employers):
    positions=[]

    titles=['Software Engineer', 'Mechanical Engineer', 'UI Designer', 'UX Designer', 'Database Engineer']
    num_positions=[3,3,2,2,3]
    for emp,title,num in zip(employers,titles,num_positions):
        if emp:
            pos=open_position(
                title=title,
                user_id=emp.id,
                number_of_positions=num
                )
            if pos:
                positions.append(pos)
    return positions

def apply_students(students):
    for s in students[:2]:
        if not s:
            continue
        try:
            apply(student_user_id=s.user_id)
        except Exception as e:
            print(f"Error applying student {s.id}: {e}")

def assign_shortlist(students,positions,staff):
    std=students[0]
    pos=positions[0]
    stf=staff[0]

    app = Application.query.filter_by(student_id=std.id).order_by(Application.id.desc()).first()
    if not app:
        try:
            app=apply(student_user_id=std.id)
            if not app:
                print(f"Could not create application for student {std.id}")
                return
        except Exception as e:
            print(f"Error applying student {std.id}: {e}")
            return
        
    try:
        shortlist(
            staff_user_id=stf.user_id,
            application_id=app.id,
            position_id=pos.id
        )
    except Exception as e:
        print(f"Error shortlisting application {app.id}: {e}")