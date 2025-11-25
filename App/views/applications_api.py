from flask import Blueprint, jsonify, request,flash
from flask_jwt_extended import jwt_required, current_user
from App.models import Application, Student, Shortlist
from App.controllers.application import apply,decide,shortlist
from App.models.application_status import ApplicationStatus
from App.controllers.user import create_user
from App.controllers.position import open_position
from App.models.staff import Staff
from App.models.employer import Employer
from App.models.position import Position
from App.controllers.student import add_degree_to_student, add_gpa_to_student
from flask_jwt_extended import jwt_required, current_user, unset_jwt_cookies, set_access_cookies
from App.controllers import login


applications_api = Blueprint('applications_api', __name__, url_prefix="/api/applications")

api = Blueprint('api', __name__, url_prefix="/api")

@applications_api.route("/ping", methods=['GET'])
def ping():
    return jsonify({"status": "ok", "message": "pong"}), 200

@applications_api.route("/student_apply", methods=['POST'])
@jwt_required()
def student_apply():
    data = request.json
    curr = current_user
    students = Student.query.all()
    
    applications = Application.query.all()
    for app in applications:
        if app.student.user_id == curr.id:
            return jsonify({"message": f"Student with user id {app.student.user_id} has already sent in an application"}), 400
    
    for student in students:
        if student.user_id == curr.id:
            application = apply(curr.id)
            return jsonify({"message": f"Application submitted successfully for student number {student.id}. Application status: Applied"}), 201
    return jsonify({"message": "Only students can submit applications"}), 403


@applications_api.route("/all_applications", methods=['GET'])
@jwt_required()
def get_applications():
    applications = Application.query.all()
    applications_list = []
    for app in applications:
        applications_list.append({
            "application_id": app.id,
            "student_id": app.student_id,
            "status": app.status.name
        })
    return jsonify(applications_list), 200

@applications_api.route("/<int:application_id>", methods=['GET'])
@jwt_required()
def get_application(application_id):
    application = Application.query.get(application_id)
    if not application:
        return jsonify({"message": "Application not found"}), 404
    
    if application.status.name == "APPLIED": 
        application_data = {
            "application_id": application.id,
            "student_id": application.student_id,
            "status": application.status.name
        }
    
    if application.status.name == "SHORTLISTED":
        shortlist = Shortlist.query.filter_by(application_id=application.id).first()
        position = shortlist.position
        application_data = {
            "application_id": application.id,
            "student_id": application.student_id,
            "status": application.status.name,
            "position": {
                "position_id": position.id,
                "title": position.title
            }
        }
    
    if application.status.name == "ACCEPTED" or application.status.name == "REJECTED":
        shortlist = Shortlist.query.filter_by(application_id=application.id).first()
        position = shortlist.position
        application_data = {
            "application_id": application.id,
            "student_id": application.student_id,
            "status": application.status.name,
            "position": {
                "position_id": position.id,
                "title": position.title
            },  
        }
    
    
    return jsonify(application_data), 200

@applications_api.route("/<int:application_id>/shortlist", methods=['POST'])
@jwt_required()
def get_shortlist_info(application_id):
    
    curr = current_user
    staff = Staff.query.filter_by(user_id=curr.id).first()
    if not staff:
        return jsonify({"message": "Only staff can shortlist applications"}), 403
    
    application = Application.query.get(application_id)
    if not application:
        return jsonify({"message": "Application not found"}), 404

    if application.status.name != "APPLIED":
        return jsonify({"message": "Application is not in APPLIED status"}), 400

    
    
    data = request.json
    position_id = data.get("position_id")

    shortlist_entry = shortlist(curr.id, application_id, position_id)

    if not shortlist_entry:
        return jsonify({"message": "Failed to shortlist student"}), 400

    return jsonify({
        "message": f"Student with user id {application.student.user_id} shortlisted successfully to shortlist {shortlist_entry.id}"
    }), 201

@applications_api.route("/<int:application_id>/decision", methods=['POST'])
@jwt_required()
def make_decision(application_id):
    application = Application.query.get(application_id)
    if not application:
       return jsonify({"message": "Application not found"}), 404
    curr = current_user
    if current_user.role != "employer":
        return jsonify({"message": "Only employers can make decisions on applications"}), 403
    if application.status.name != "SHORTLISTED":
        return jsonify({"message": "Application is not in SHORTLISTED status"}), 400
    data = request.json
    decision = data.get("decision")
    if decision not in ["ACCEPTED", "REJECTED"]:
        return jsonify({"message": "Decision must be either 'ACCEPTED' or 'REJECTED'"}), 400
    application = decide(curr.id, application_id, decision)
    return jsonify({"message": f"Application {application_id} has been {decision.lower()}."}), 200

@api.route("/signup", methods=['POST'])
def api_signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    user_type = data.get("type")
    if not username or not password or not user_type:
        return jsonify({"message": "Username, password, and role are required"}), 400
    
    if user_type not in ["student", "employer", "staff"]:
        return jsonify({"message": "Role must be either 'student', 'employer', or 'staff'"}), 400
    
    if user_type == "student":
        gpa = data.get("gpa")
        degree = data.get("degree")
        if gpa is None or degree is None:
            return jsonify({"message": "GPA and degree are required for student signup"}), 400
        status = create_user(username, password, user_type)
        if not status:
            return jsonify({"message": "Signup failed, username taken!"}), 401
        else:
            token = login(data['username'], data['password'])
            flash('Signup Successful')
            response = jsonify(access_token=token)
            set_access_cookies(response, token) 
            add_degree_to_student(status.id, degree)
            add_gpa_to_student(status.id, gpa)
            return response
    
    status = create_user(username, password, user_type)
    if not status:
        return jsonify({"message": "Signup failed, username taken!"}), 401
    else:
        token = login(data['username'], data['password'])
        flash('Signup Successful')
        response = jsonify(access_token=token)
        set_access_cookies(response, token) 
        return response

@api.route("/openings/<int:id>", methods=['POST'])
@jwt_required()
def create_opening(id):
    curr = current_user
    if curr.role != "employer":
        return jsonify({"message": "Only employers can create job openings"}), 403
    
    data = request.json
    title = data.get("title")
    number = data.get("number")
    if not title or not number:
        return jsonify({"message": "Title and number of positions are required"}), 400
    opening = open_position(title,curr.id, number)
    if not opening:
        return jsonify({"message": "Failed to create job opening"}), 400
    return jsonify({"message": "Job opening created successfully", "opening_id": opening.id}), 201

@api.route("/openings", methods=['GET'])
@jwt_required()
def list_openings():
    positions = Position.query.all()
    positions_list = []
    for pos in positions:
        positions_list.append({
            "position_id": pos.id,
            "title": pos.title,
            "number_of_positions": pos.number_of_positions,
            "employer_id": pos.employer_id
        })
    return jsonify(positions_list), 200