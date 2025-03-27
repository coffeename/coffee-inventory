from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from db_connection import get_db_connection
from rbac import role_required

users_bp = Blueprint('users_bp', __name__)

@users_bp.route('/users', methods=['POST'])
@role_required(['admin']) 
def create_user():
    try:
        data = request.get_json()
        username = data['username']
        password = data['password']
        role = data.get('role', 'barista') 

        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, password_hash, role))
        conn.commit()

        new_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({"message": "User created", "user_id": new_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@users_bp.route('/users', methods=['GET'])
@role_required(['admin'])  
def get_all_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, created_at FROM users")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        users = []
        for row in rows:
            users.append({
                "id": row[0],
                "username": row[1],
                "role": row[2],
                "created_at": str(row[3])
            })

        return jsonify(users), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@users_bp.route('/users/<int:user_id>', methods=['GET'])
@role_required(['admin'])
def get_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role, created_at FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            user = {
                "id": row[0],
                "username": row[1],
                "role": row[2],
                "created_at": str(row[3])
            }
            return jsonify(user), 200
        else:
            return jsonify({"message": "User not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@users_bp.route('/users/<int:user_id>', methods=['PUT'])
@role_required(['admin'])
def update_user(user_id):
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        existing = cursor.fetchone()
        if not existing:
            cursor.close()
            conn.close()
            return jsonify({"message": "User not found"}), 404

        update_sql = "UPDATE users SET username = %s, role = %s WHERE id = %s"
        cursor.execute(update_sql, (username, role, user_id))

        if password:
            new_hash = generate_password_hash(password)
            cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "User updated"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@users_bp.route('/users/<int:user_id>', methods=['DELETE'])
@role_required(['admin'])
def delete_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        existing = cursor.fetchone()
        if not existing:
            cursor.close()
            conn.close()
            return jsonify({"message": "User not found"}), 404

        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "User deleted"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400