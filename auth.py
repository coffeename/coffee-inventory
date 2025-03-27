from flask import Blueprint, request, jsonify
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

    if row:
        user_id, db_username, password_hash, role = row
        if check_password_hash(password_hash, password):
            user_obj = User(id=user_id, username=db_username, role=role)
            login_user(user_obj)
            return jsonify({"message": "Logged in successfully"}), 200
        else:
            return jsonify({"error": "Invalid password"}), 401
    else:
        return jsonify({"error": "User not found"}), 404


@auth_bp.route('/logout', methods=['POST'])
def logout():
    if not current_user.is_authenticated:
        return jsonify({"error": "Not logged in"}), 401
    logout_user()
    return jsonify({"message": "Logged out"}), 200
