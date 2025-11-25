from .user import create_user
from .shortlist import add_student_to_shortlist
from .position import open_position
from .application import apply
from App.database import db


def initialize():
    db.drop_all()
    db.create_all()

    employers=create_employers()
    staff=create_staff()
    students=create_students()

    positions=open_positions(employers)
    apply_students(students)
    assign_shortlists(students,positions,staff)

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
    users=[]
    for uname in ('george','sarah','gus','jamie','earnest'):
        u=create_user(uname, f'{uname}pass', "student")
        if u:
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
    for s in students:
        if s:
            try:
                apply(student_user_id=s.id)
            except Exception :
                pass

def assign_shortlists(students,positions,staff):
    for stdnt,pos,stf in zip(students,positions,staff):
        if stdnt and pos and stf:
            try:
                add_student_to_shortlist(
                    student_id=stdnt.id,
                    position_id=pos.id,
                    staff_id=stf.id
                )
            except Exception:
                pass