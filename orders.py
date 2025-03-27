from flask import Blueprint, request, jsonify
from flask_login import current_user
from db_connection import get_db_connection
from rbac import role_required

orders_bp = Blueprint('orders_bp', __name__)

@orders_bp.route('/orders', methods=['POST'])
@role_required(['barista','manager','admin'])
def create_order():
    data = request.get_json()
    user_id = current_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = "INSERT INTO orders (user_id) VALUES (%s)"
    cursor.execute(sql, (user_id,))
    order_id = cursor.lastrowid

    items = data.get('items', [])
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        cursor.execute(
            "INSERT INTO order_items (order_id, product_id, quantity) VALUES (%s, %s, %s)",
            (order_id, product_id, quantity)
        )
        cursor.execute(
            "UPDATE products SET quantity = quantity - %s WHERE id = %s",
            (quantity, product_id)
        )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Order created", "order_id": order_id}), 201

@orders_bp.route('/orders', methods=['GET'])
@role_required(['manager','admin'])
def get_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, order_date FROM orders")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    orders_list = []
    for row in rows:
        orders_list.append({
            "id": row[0],
            "user_id": row[1],
            "order_date": str(row[2]) if row[2] else None
        })

    return jsonify(orders_list), 200

@orders_bp.route('/orders/<int:order_id>', methods=['GET'])
@role_required(['barista','manager','admin'])
def get_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, user_id, order_date FROM orders WHERE id = %s", (order_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return jsonify({"error": "Order not found"}), 404

    order_id_db, owner_id, order_date = row
    if current_user.role == 'barista' and owner_id != current_user.id:
        cursor.close()
        conn.close()
        return jsonify({"error": "Error: you can only see your own orders"}), 403

    cursor.execute("SELECT product_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
    items = []
    for product_id, quantity in cursor.fetchall():
        items.append({"product_id": product_id, "quantity": quantity})

    cursor.close()
    conn.close()

    return jsonify({
        "id": order_id_db,
        "user_id": owner_id,
        "order_date": str(order_date),
        "items": items
    }), 200

@orders_bp.route('/orders/<int:order_id>', methods=['PUT'])
@role_required(['manager','admin'])
def update_order(order_id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM orders WHERE id=%s", (order_id,))
    existing = cursor.fetchone()
    if not existing:
        cursor.close()
        conn.close()
        return jsonify({"error": "Order not found"}), 404

    cursor.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))

    items = data.get('items', [])
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        cursor.execute(
            "INSERT INTO order_items (order_id, product_id, quantity) VALUES (%s, %s, %s)",
            (order_id, product_id, quantity)
        )

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Order updated", "order_id": order_id}), 200

@orders_bp.route('/orders/<int:order_id>', methods=['DELETE'])
@role_required(['admin'])
def delete_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM orders WHERE id = %s", (order_id,))
    existing = cursor.fetchone()
    if not existing:
        cursor.close()
        conn.close()
        return jsonify({"error": "Order not found"}), 404

    cursor.execute("DELETE FROM order_items WHERE order_id = %s", (order_id,))
    cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Order deleted", "order_id": order_id}), 200
