from flask import Blueprint, jsonify
from flask_login import current_user
from db_connection import get_db_connection

stock_bp = Blueprint('stock_bp', __name__)

INITIAL_STOCKS = {
    "Ванільний цукор": 20,
    "Круасан класичний": 25,
    "Круасан шоколадний": 25,
    "Круасан мигдалевий": 25,
    "Сінабон класичний": 25,
    "Чизкейк класичний": 25,
    "Чизкейк ягідний": 25,
    "Чизкейк карамельний": 25,
    "Брауні шоколадний": 25,
    "Морквяний торт": 25,
    "Макарони": 25,
    "Банановий кекс": 25,
    "Шок. печиво": 25,
    "Тірамісу": 25,
    "Мафін шоколадний": 25,
    "Мафін ягідний": 25,
    "Сендвіч з куркою": 20,
    "Сендвіч з тунцем": 20,
    "Сендвіч овочевий": 20,
    "Бейгл з лососем": 20,
    "Тост з авокадо": 20,
    "Гранола з йогуртом": 20,
    "Кіш зі шпинатом": 20,
    "Вівсянка з фруктами": 20,
    "Брускета томатна": 20,
    "Брускета прошуто": 20,
    "Брускета сирна": 20,
    "Веган сендвіч": 20,
    "Боул веганський": 20,
    "Салат в стакані": 20,
    "Кава зернова": 500,
    "Кава зернова (без кофеїну)": 500,
    "Кава зернова (фільтр)": 500,
    "Кава розчинна": 500,
    "Матча порошок": 300,
    "Какао порошок": 300,
    "Чай чорний": 300,
    "Чай зелений": 300,
    "Чай фруктовий": 300,
    "Чай трав’яний": 300,
    "Молоко": 60,
    "Молоко рослинне": 20,
    "Вершки": 45,
    "Імбир свіжий": 10,
    "М'ята свіжа": 10,
    "Цитрусові": 25,
    "Мед квіт": 20,
    "Мед акац": 20,
    "Сиропи": 20,
    "Комбуча": 20,
    "Цукровий сироп": 20,
    "Шоколадний соус": 20
}

@stock_bp.route('/stock-notifications', methods=['GET'])
def stock_notifications():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, quantity FROM products")
    products = cursor.fetchall()
    
    notifications = []
    
    # Перевіряємо роль користувача (якщо користувач не авторизований, можна повернути загальне повідомлення)
    user_role = current_user.role.lower() if current_user.is_authenticated else None
    
    for prod in products:
        prod_id, name, qty = prod
        
        # Якщо кількість більше 0, але менше 3
        if 0 < qty < 3:
            notifications.append(f"Продукт {name} закінчується.")
        
        # Якщо кількість дорівнює 0
        if qty == 0:
            initial_qty = INITIAL_STOCKS.get(name, 0)
            if user_role in ['manager', 'admin']:
                cursor.execute("UPDATE products SET quantity = %s WHERE id = %s", (initial_qty, prod_id))
                conn.commit()
                notifications.append(f"Продукт {name} щойно прибув на склад в кількості {initial_qty} шт.")
            elif user_role == 'barista':
                notifications.append(f"Продукту {name} наразі немає в наявності. Зверніться до менеджера.")
    
    cursor.close()
    conn.close()
    return jsonify(notifications), 200
