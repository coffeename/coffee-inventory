from flask import Blueprint, request, jsonify
from flask_login import current_user
from db_connection import get_db_connection
from rbac import role_required

orders_bp = Blueprint('orders_bp', __name__)

@orders_bp.route('/orders', methods=['POST'])
@role_required(['barista', 'manager', 'admin'])
def create_order():
    try:
        data = request.get_json()
        user_role = current_user.role.lower()
        user_id = current_user.id
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Починаємо транзакцію
        cursor.execute("START TRANSACTION")
        
        items = data.get('items', [])
        
        # Перевірка кожного товару замовлення
        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            
            # Блокуємо рядок продукту для атомарного оновлення, отримуємо також initial_stock
            cursor.execute(
                "SELECT quantity, name, initial_stock FROM products WHERE id = %s FOR UPDATE",
                (product_id,)
            )
            row = cursor.fetchone()
            if not row:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({"error": "Product not found"}), 404
            
            current_qty, product_name, init_stock = row
            new_qty = current_qty - quantity
            
            if new_qty < 0:
                # Якщо запас недостатній (new_qty від'ємний), не створюємо замовлення:
                if user_role in ['manager', 'admin']:
                    # Для manager/admin: оновлюємо запас до початкового значення (init_stock)
                    cursor.execute("UPDATE products SET quantity = %s WHERE id = %s", (init_stock, product_id))
                    alert_message = f"{product_name} щойно прибув на склад в кількості {init_stock} шт. Перевірте!"
                    cursor.execute("""
                        INSERT INTO inventory_alerts (product_id, alert_message, barista_id, current_quantity)
                        VALUES (%s, %s, %s, %s)
                    """, (product_id, alert_message, current_user.id, init_stock))
                    conn.commit()
                    cursor.close()
                    conn.close()
                    return jsonify({"push_message": alert_message}), 400
                else:  # Для barista
                    conn.rollback()
                    cursor.close()
                    conn.close()
                    return jsonify({
                        "push_message": f"{product_name} наразі немає в наявності. Зверніться до менеджера, щоб він виправив це."
                    }), 400
            
            # Якщо new_qty >= 0, але менше 3 — для всіх ролей генеруємо додаткове попередження
            elif 0 <= new_qty < 3:
                alert_message = f"{product_name} закінчується."
                cursor.execute("""
                    INSERT INTO inventory_alerts (product_id, alert_message, barista_id, current_quantity)
                    VALUES (%s, %s, %s, %s)
                """, (product_id, alert_message, current_user.id, new_qty))
                # Продовжуємо перевірку (замовлення дозволено)
        
        # Якщо всі товари пройшли перевірку, створюємо замовлення
        sql_order = "INSERT INTO orders (user_id, order_date) VALUES (%s, NOW())"
        cursor.execute(sql_order, (user_id,))
        order_id = cursor.lastrowid
        
        # Додаємо позиції замовлення та оновлюємо залишки для кожного товару
        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity)
                VALUES (%s, %s, %s)
            """, (order_id, product_id, quantity))
            # Оновлюємо запас: отримуємо поточну кількість, обчислюємо new_qty, оновлюємо
            cursor.execute("SELECT quantity FROM products WHERE id = %s", (product_id,))
            current_qty = cursor.fetchone()[0]
            new_qty = current_qty - quantity
            cursor.execute("UPDATE products SET quantity = %s WHERE id = %s", (new_qty, product_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Order created"}), 201

    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"error": str(e)}), 400

@orders_bp.route('/orders', methods=['GET'])
@role_required(['manager', 'admin'])
def get_orders():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, order_date FROM orders ORDER BY order_date DESC")
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
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@orders_bp.route('/orders/<int:order_id>', methods=['GET'])
@role_required(['barista', 'manager', 'admin'])
def get_order(order_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, order_date FROM orders WHERE id = %s", (order_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return jsonify({"error": "Order not found"}), 404

        order_id_db, owner_id, order_date = row
        if current_user.role.lower() == 'barista' and owner_id != current_user.id:
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
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@orders_bp.route('/orders/<int:order_id>', methods=['PUT'])
@role_required(['manager', 'admin'])
def update_order(order_id):
    try:
        data = request.get_json()
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM orders WHERE id = %s", (order_id,))
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
            cursor.execute("INSERT INTO order_items (order_id, product_id, quantity) VALUES (%s, %s, %s)",
                           (order_id, product_id, quantity))
            sql_update = "UPDATE products SET quantity = quantity - %s WHERE id = %s"
            cursor.execute(sql_update, (quantity, product_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Order updated", "order_id": order_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@orders_bp.route('/orders/<int:order_id>', methods=['DELETE'])
@role_required(['admin', 'manager'])
def delete_order(order_id):
    try:
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
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Новий ендпоінт для історії замовлень
@orders_bp.route('/orders/history', methods=['GET'])
@role_required(['barista', 'manager', 'admin'])
def order_history():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        user_role = current_user.role.lower()
        user_id = current_user.id

        # Базовий запит із join’ами; тепер вибираємо username користувача, який створив замовлення
        base_sql = """
            SELECT o.id AS order_id, p.name AS product_name, oi.quantity, u.username AS creator_username, o.order_date
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON p.id = oi.product_id
            JOIN users u ON u.id = o.user_id
        """
        # Фільтрація замовлень за останні 7 днів
        date_filter = " o.order_date >= DATE_SUB(NOW(), INTERVAL 7 DAY) "
        
        if user_role == 'barista':
            # Barista бачить лише свої замовлення
            base_sql += f" WHERE o.user_id = %s AND {date_filter}"
            params = (user_id,)
        elif user_role == 'manager':
            # Manager бачить свої замовлення та замовлення користувачів з роллю barista
            base_sql += f" WHERE (o.user_id = %s OR u.role = 'barista') AND {date_filter}"
            params = (user_id,)
        else:  # admin
            base_sql += f" WHERE {date_filter}"
            params = ()

        base_sql += " ORDER BY o.id DESC"

        cursor.execute(base_sql, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        orders_list = []
        if user_role == 'barista':
            # Для barista повертаємо три поля
            for row in rows:
                orders_list.append({
                    "id": row[0],
                    "product_name": row[1],
                    "quantity": row[2]
                })
        else:
            # Для manager і admin повертаємо п'ять полів, де "creator_username" містить username творця замовлення,
            # а "order_date" – дату/час створення.
            for row in rows:
                orders_list.append({
                    "id": row[0],
                    "product_name": row[1],
                    "quantity": row[2],
                    "creator_username": row[3],
                    "order_date": str(row[4]) if row[4] else None
                })

        return jsonify(orders_list), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400