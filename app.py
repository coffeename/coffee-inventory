from flask import Flask, request, jsonify
from db_connection import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

@app.route('/')
def home():
    return "Все ок, їїї. ?!"


@app.route('/products', methods=['POST'])
def create_product():
    try:
        data = request.get_json()
        name = data['name']
        description = data.get('description', '')
        price = float(data.get('price', 0.0))
        quantity = int(data.get('quantity', 0))

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = "INSERT INTO products (name, description, price, quantity) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (name, description, price, quantity))
        conn.commit()

        new_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({"message": "Product created", "product_id": new_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/products', methods=['GET'])
def get_all_products():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, price, quantity FROM products")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        products = []
        for row in rows:
            products.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "price": float(row[3]),
                "quantity": row[4]
            })

        return jsonify(products), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "SELECT id, name, description, price, quantity FROM products WHERE id = %s"
        cursor.execute(sql, (product_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            product = {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "price": float(row[3]),
                "quantity": row[4]
            }
            return jsonify(product), 200
        else:
            return jsonify({"message": "Product not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        price = data.get('price')
        quantity = data.get('quantity')
        conn = get_db_connection()
        cursor = conn.cursor()
        check_sql = "SELECT id FROM products WHERE id = %s"
        cursor.execute(check_sql, (product_id,))
        existing = cursor.fetchone()
        if not existing:
            cursor.close()
            conn.close()
            return jsonify({"message": "Product not found"}), 404

        update_sql = """
            UPDATE products 
            SET name = %s, description = %s, price = %s, quantity = %s 
            WHERE id = %s
        """
        cursor.execute(update_sql, (name, description, price, quantity, product_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Product updated"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        check_sql = "SELECT id FROM products WHERE id = %s"
        cursor.execute(check_sql, (product_id,))
        existing = cursor.fetchone()
        if not existing:
            cursor.close()
            conn.close()
            return jsonify({"message": "Product not found"}), 404

        delete_sql = "DELETE FROM products WHERE id = %s"
        cursor.execute(delete_sql, (product_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Product deleted"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/users', methods=['POST'])
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

@app.route('/users', methods=['GET'])
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

@app.route('/users/<int:user_id>', methods=['GET'])
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

@app.route('/users/<int:user_id>', methods=['PUT'])
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

@app.route('/users/<int:user_id>', methods=['DELETE'])
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

if __name__ == '__main__':
    app.run(debug=True)
