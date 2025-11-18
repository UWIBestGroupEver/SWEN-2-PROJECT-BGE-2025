from App.models import Shortlist, Position, Staff, Student, Application
from App.database import db



def create_student(username, user_id):
    student = Student(username=username, user_id=user_id)
    db.session.add(student)
    db.session.commit()
    return student

def add_gpa_to_student(student_id, gpa):
    student = Student.query.get(student_id)
    if student:
        student.gpa = gpa
        db.session.commit()
        return student.gpa
    return None

def add_degree_to_student(student_id, degree):
    student = Student.query.get(student_id)
    if student:
        student.degree = degree
        db.session.commit()
        return student.degree
    return None
