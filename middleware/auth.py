from flask import request, jsonify
from functools import wraps
from models.session import UserSession
from models.user import User


def get_current_user():
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not token:
        return None
    session = UserSession.query.filter_by(token=token, is_valid=True).first()
    if not session:
        return None
    user = User.query.get(session.user_id)
    if not user or not user.is_active:
        return None
    return user


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({"error": "Unauthorized. Please log in."}), 401
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """Usage: @role_required('admin') or @role_required('admin', 'analyst')"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({"error": "Unauthorized. Please log in."}), 401
            if user.role not in roles:
                return jsonify({"error": f"Access denied. Required role: {', '.join(roles)}"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
