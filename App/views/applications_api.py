from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user
from App.models import Application, Student, Shortlist
from App.controllers.application import apply
from App.models.application_status import ApplicationStatus


applications_api = Blueprint('applications_api', __name__, url_prefix="/api/applications")

@applications_api.route("/ping", methods=['GET'])
def ping():
    return jsonify({"status": "ok", "message": "pong"}), 200

@applications_api.route("/student_apply", methods=['POST'])
@jwt_required()
def student_apply():
    data = request.json
    curr = current_user
    students = Student.query.all()
    for student in students:
        if student.user_id == curr.id:
            apply(student.id)
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