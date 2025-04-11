from flask import Blueprint, request, jsonify
from db_connection import get_db_connection
from rbac import role_required

products_bp = Blueprint('products_bp', __name__)

@products_bp.route('/products', methods=['GET'])
@role_required(['barista','manager','admin'])
def get_all_products():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Вибираємо лише активні продукти (is_active = 1)
        cursor.execute("SELECT id, name, description, price, quantity, initial_stock FROM products WHERE is_active = 1")
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
                "quantity": row[4],
                "initial_stock": row[5]
            })

        return jsonify(products), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@products_bp.route('/products', methods=['POST'])
@role_required(['manager','admin'])
def create_product():
    try:
        data = request.get_json()
        name = data['name']
        description = data.get('description', '')
        price = float(data.get('price', 0.0))
        quantity = int(data.get('quantity', 0))
        # Якщо не передане explicitly, initial_stock = quantity
        initial_stock = int(data.get('initial_stock', quantity))

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
            INSERT INTO products (name, description, price, quantity, initial_stock, is_active)
            VALUES (%s, %s, %s, %s, %s, 1)
        """
        cursor.execute(sql, (name, description, price, quantity, initial_stock))
        conn.commit()

        new_id = cursor.lastrowid
        cursor.close()
        conn.close()

        return jsonify({"message": "Product created", "product_id": new_id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@products_bp.route('/products/<int:product_id>', methods=['GET'])
@role_required(['barista','manager','admin'])
def get_product(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = """
            SELECT id, name, description, price, quantity, initial_stock 
            FROM products 
            WHERE id = %s AND is_active = 1
        """
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
                "quantity": row[4],
                "initial_stock": row[5]
            }
            return jsonify(product), 200
        else:
            return jsonify({"message": "Product not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@products_bp.route('/products/<int:product_id>', methods=['PUT'])
@role_required(['manager','admin'])
def update_product(product_id):
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        price = data.get('price')
        quantity = data.get('quantity')
        # Якщо не передано explicitly, initial_stock = quantity
        initial_stock = data.get('initial_stock', quantity)

        conn = get_db_connection()
        cursor = conn.cursor()
        check_sql = "SELECT id FROM products WHERE id = %s AND is_active = 1"
        cursor.execute(check_sql, (product_id,))
        existing = cursor.fetchone()
        if not existing:
            cursor.close()
            conn.close()
            return jsonify({"message": "Product not found"}), 404

        update_sql = """
            UPDATE products 
            SET name = %s, description = %s, price = %s, quantity = %s, initial_stock = %s 
            WHERE id = %s
        """
        cursor.execute(update_sql, (name, description, price, quantity, initial_stock, product_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Product updated"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@products_bp.route('/products/<int:product_id>', methods=['DELETE'])
@role_required(['manager','admin'])
def delete_product(product_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        check_sql = "SELECT id FROM products WHERE id = %s AND is_active = 1"
        cursor.execute(check_sql, (product_id,))
        existing = cursor.fetchone()
        if not existing:
            cursor.close()
            conn.close()
            return jsonify({"message": "Product not found or already deleted"}), 404

        # Виконуємо логічне видалення, оновлюючи поле is_active до 0.
        update_sql = "UPDATE products SET is_active = 0 WHERE id = %s"
        cursor.execute(update_sql, (product_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Product soft-deleted"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
