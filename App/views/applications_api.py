from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user


applications_api = Blueprint('applications_api', __name__, url_prefix="/api/applications")

@applications_api.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "message": "pong"}), 200

