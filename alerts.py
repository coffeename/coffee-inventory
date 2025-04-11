from flask import Blueprint, jsonify
from flask_login import current_user
from db_connection import get_db_connection
from rbac import role_required

alerts_bp = Blueprint('alerts_bp', __name__)

@alerts_bp.route('/alerts', methods=['GET'])
@role_required(['manager','admin'])
def get_alerts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Приклад запиту, що з'єднує inventory_alerts з таблицями products та users
        query = """
            SELECT ia.id,
                   p.name AS product_name,
                   ia.alert_message,
                   ia.alert_datetime,
                   u.username AS barista,
                   ia.current_quantity
            FROM inventory_alerts ia
            JOIN products p ON ia.product_id = p.id
            JOIN users u ON ia.barista_id = u.id
            ORDER BY ia.alert_datetime DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        alerts_list = []
        for row in rows:
            alerts_list.append({
                "id": row[0],
                "product_name": row[1],
                "alert_message": row[2],
                "alert_datetime": str(row[3]),
                "barista": row[4],
                "current_quantity": row[5]
            })

        return jsonify(alerts_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
