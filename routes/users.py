from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from models.user import User
from models.db import db
from middleware.auth import login_required, role_required

users_bp = Blueprint("users", __name__)

VALID_ROLES = ["viewer", "analyst", "admin"]


@users_bp.route("/", methods=["GET"])
@role_required("admin")
def get_all_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200


@users_bp.route("/<int:user_id>", methods=["GET"])
@login_required
def get_user(user_id):
    from middleware.auth import get_current_user
    current_user = get_current_user()
    # Non-admins can only view their own profile
    if current_user.role != "admin" and current_user.id != user_id:
        return jsonify({"error": "Access denied"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200


@users_bp.route("/", methods=["POST"])
@role_required("admin")
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    role = data.get("role", "viewer")

    if not name or not email or not password:
        return jsonify({"error": "name, email, and password are required"}), 400

    if role not in VALID_ROLES:
        return jsonify({"error": f"Invalid role. Choose from: {', '.join(VALID_ROLES)}"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "A user with this email already exists"}), 409

    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role=role
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User created successfully", "user": user.to_dict()}), 201


@users_bp.route("/<int:user_id>/role", methods=["PATCH"])
@role_required("admin")
def update_role(user_id):
    data = request.get_json()
    role = data.get("role", "")

    if role not in VALID_ROLES:
        return jsonify({"error": f"Invalid role. Choose from: {', '.join(VALID_ROLES)}"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.role = role
    db.session.commit()
    return jsonify({"message": "Role updated", "user": user.to_dict()}), 200


@users_bp.route("/<int:user_id>/status", methods=["PATCH"])
@role_required("admin")
def update_status(user_id):
    data = request.get_json()
    is_active = data.get("is_active")

    if is_active is None or not isinstance(is_active, bool):
        return jsonify({"error": "is_active must be a boolean (true or false)"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.is_active = is_active
    db.session.commit()
    return jsonify({"message": "User status updated", "user": user.to_dict()}), 200


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@role_required("admin")
def delete_user(user_id):
    from middleware.auth import get_current_user
    current_user = get_current_user()
    if current_user.id == user_id:
        return jsonify({"error": "You cannot delete your own account"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"}), 200
