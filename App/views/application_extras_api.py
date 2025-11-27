from flask import Blueprint, jsonify, request
from App.models.employer import Employer
from flask_jwt_extended import jwt_required, current_user

from App.models import Application, Student, Shortlist
from App.models.application_status import ApplicationStatus
from App.models.position import Position
from App.models.staff import Staff

# Extra endpoints for applications
application_extras_api = Blueprint(
    "application_extras_api",
    __name__,
    url_prefix="/api/applications"
)

# Extra endpoints for openings
openings_extras_api = Blueprint(
    "openings_extras_api",
    __name__,
    url_prefix="/api/openings"
)


def _serialize_application(application):
    """
    Serialize an Application similar to your /api/applications/<id> endpoint.
    Adds position info when SHORTLISTED / ACCEPTED / REJECTED.
    """
    data = {
        "application_id": application.id,
        "student_id": application.student_id,
        "status": application.status.name
    }

    if application.status.name == "APPLIED":
        return data

    # For SHORTLISTED / ACCEPTED / REJECTED, attach position info (via Shortlist)
    shortlist_entry = Shortlist.query.filter_by(application_id=application.id).first()
    if shortlist_entry and shortlist_entry.position:
        position = shortlist_entry.position
        data["position"] = {
            "position_id": position.id,
            "title": position.title
        }

    return data


# ===================== APPLICATION EXTRAS =====================

@application_extras_api.route("/my", methods=["GET"])
@jwt_required()
def get_my_application():
    """
    GET /api/applications/my
    - Only students
    - Returns the single application for the logged-in student
    """
    curr = current_user

    # Ensure user is a student
    student = Student.query.filter_by(user_id=curr.id).first()
    if not student:
        return jsonify({"message": "Only students can access their application"}), 403

    # One application per student
    application = Application.query.filter_by(student_id=student.id).first()
    if not application:
        return jsonify({"message": "No application found for this student"}), 404

    return jsonify(_serialize_application(application)), 200


@application_extras_api.route("/status/<string:status_name>", methods=["GET"])
@jwt_required()
def get_applications_by_status(status_name):
    """
    GET /api/applications/status/<status_name>
    - Intended primarily for staff
    - status_name examples: APPLIED, SHORTLISTED, ACCEPTED, REJECTED
    """
    curr = current_user

    # Check staff via Staff model (consistent with your shortlist endpoint)
    staff = Staff.query.filter_by(user_id=curr.id).first()
    if not staff:
        return jsonify({"message": "Only staff can filter applications by status"}), 403

    # Normalize and validate status
    status_key = status_name.upper()
    try:
        status_enum = ApplicationStatus[status_key]
    except KeyError:
        return jsonify({
            "message": "Invalid status. Use one of: APPLIED, SHORTLISTED, ACCEPTED, REJECTED"
        }), 400

    applications = Application.query.filter_by(status=status_enum).all()
    serialized = [_serialize_application(app) for app in applications]

    return jsonify(serialized), 200


# ===================== OPENINGS EXTRAS =====================
@openings_extras_api.route("/my", methods=["GET"])
@jwt_required()
def get_my_openings():
    """
    GET /api/openings/my
    - Only employers
    - Returns positions created by the logged-in employer
    """
    curr = current_user

    if curr.role != "employer":
        return jsonify({"message": "Only employers can view their openings"}), 403
    employer = Employer.query.filter_by(user_id=curr.id).first()
    if not employer:
        return jsonify({"message": "Employer record not found for this user"}), 404

    # Now filter positions by employer.id (NOT user id)
    positions = Position.query.filter_by(employer_id=employer.id).all()

    positions_list = []
    for pos in positions:
        positions_list.append({
            "position_id": pos.id,
            "title": pos.title,
            "number_of_positions": pos.number_of_positions,
            "employer_id": pos.employer_id
        })

    return jsonify(positions_list), 200



@openings_extras_api.route("/<int:position_id>/applications", methods=["GET"])
@jwt_required()
def get_applications_for_opening(position_id):
    """
    GET /api/openings/<position_id>/applications
    - Only the employer who owns this opening
    - Returns all applications that have been shortlisted to this position
    """
    curr = current_user

    if curr.role != "employer":
        return jsonify({"message": "Only employers can view applications for an opening"}), 403

    # Find the employer record linked to this user
    employer = Employer.query.filter_by(user_id=curr.id).first()
    if not employer:
        return jsonify({"message": "Employer record not found for this user"}), 404

    position = Position.query.get(position_id)
    if not position:
        return jsonify({"message": "Position not found"}), 404

    # Ensure the logged-in employer owns this position
    if position.employer_id != employer.id:
        return jsonify({"message": "You are not authorized to view applications for this opening"}), 403

    # Get all shortlists for this position and collect applications
    shortlists = Shortlist.query.filter_by(position_id=position.id).all()

    applications_list = []
    for s in shortlists:
        application = s.application  # assumes relationship on Shortlist -> Application
        applications_list.append({
            "application_id": application.id,
            "student_id": application.student_id,
            "status": application.status.name
        })

    return jsonify(applications_list), 200

