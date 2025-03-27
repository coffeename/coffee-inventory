from flask import jsonify
from flask_login import current_user
from functools import wraps

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Unauthorized access."}), 401
            if current_user.role not in allowed_roles:
                return jsonify({"error": "Not allowed for you."}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator