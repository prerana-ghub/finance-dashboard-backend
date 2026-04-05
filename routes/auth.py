from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from models.user import User
from models.session import UserSession
from models.db import db
from middleware.auth import get_current_user, login_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Your account has been deactivated. Contact admin."}), 403

    session = UserSession(user_id=user.id)
    db.session.add(session)
    db.session.commit()

    return jsonify({
        "message": "Login successful",
        "token": session.token,
        "user": user.to_dict()
    }), 200


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    session = UserSession.query.filter_by(token=token).first()
    if session:
        session.is_valid = False
        db.session.commit()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    user = get_current_user()
    return jsonify(user.to_dict()), 200
