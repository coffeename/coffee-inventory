from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from db_connection import get_db_connection
from models import User

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT id, username, password_hash, role FROM users WHERE username = %s"
    cursor.execute(sql, (username,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return jsonify({"error": "User not found"}), 404

    user_id, db_username, db_password_hash, role = row
    if not check_password_hash(db_password_hash, password):
        return jsonify({"error": "Invalid password"}), 401

    # Зробити сесію постійною
    session.permanent = True
    session['user_id'] = user_id
    session['role'] = role

    # Викликаємо login_user для встановлення current_user
    user_obj = User(id=user_id, username=db_username, role=role)
    login_user(user_obj)

    return jsonify({"message": "Login successful", "role": role}), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    if not current_user.is_authenticated:
        return jsonify({"error": "Not logged in"}), 401
    logout_user()
    session.clear()
    return jsonify({"message": "Logged out"}), 200

@auth_bp.route('/current_user', methods=['GET'])
def current_user_info():
    if current_user.is_authenticated:
        return jsonify({
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role
        }), 200
    else:
        return jsonify({"error": "Not logged in"}), 401
