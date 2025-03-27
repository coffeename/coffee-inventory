import datetime, random
import pymysql


def generate_sales():
    start_date = datetime.date(2024, 10, 15)
    end_date = datetime.date(2025, 9, 15)

    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="CoffeeShop_2025",
        database="coffee_inventory",
        charset="utf8mb4"
    )
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM products")
    product_ids = [row[0] for row in cursor.fetchall()]

    current_date = start_date
    while current_date <= end_date:
        cursor.execute("SELECT user_id FROM shifts WHERE shift_date = %s", (current_date,))
        row = cursor.fetchone()
        if not row:
            current_date += datetime.timedelta(days=1)
            continue
        barista_id = row[0]

        orders_per_day = random.randint(2, 10)

        for _ in range(orders_per_day):
            hour = random.randint(9, 20)
            minute = random.randint(0, 59)
            order_datetime = datetime.datetime(
                current_date.year, current_date.month, current_date.day,
                hour, minute
            )

            sql_orders = """
                INSERT INTO orders (user_id, order_date)
                VALUES (%s, %s)
            """
            cursor.execute(sql_orders, (barista_id, order_datetime))
            order_id = cursor.lastrowid

            items_count = random.randint(1, 5)
            for _i in range(items_count):
                product_id = random.choice(product_ids)
                quantity = random.randint(1, 5)

                sql_items = """
                    INSERT INTO order_items (order_id, product_id, quantity)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(sql_items, (order_id, product_id, quantity))

        current_date += datetime.timedelta(days=1)

    conn.commit()
    cursor.close()
    conn.close()
    print("Sales data generated successfully.")

if __name__ == '__main__':
    generate_sales()
