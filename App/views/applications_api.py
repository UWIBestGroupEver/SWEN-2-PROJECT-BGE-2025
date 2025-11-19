from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user
from App.models import Application, Student, Shortlist
from App.controllers.application import apply,decide
from App.models.application_status import ApplicationStatus
from App.controllers.shortlist import add_student_to_shortlist
from App.models.staff import Staff
from App.models.employer import Employer



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
    application = Application.query.get(application_id)
    if not application:
        return jsonify({"message": "Application not found"}), 404

    if application.status.name != "APPLIED":
        return jsonify({"message": "Application is not in APPLIED status"}), 400

    curr = current_user
    staff = Staff.query.filter_by(user_id=curr.id).first()
    if not staff:
        return jsonify({"message": "Only staff can shortlist applications"}), 403
    
    data = request.json
    position_id = data.get("position_id")

    shortlist_entry = add_student_to_shortlist(
        application.student.user_id,
        position_id,
        staff.user_id
    )

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