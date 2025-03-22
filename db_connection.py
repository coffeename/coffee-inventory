import pymysql

def get_db_connection():
    connection = pymysql.connect(
        host="localhost",
        user="root",
        password="CoffeeShop_2025",
        database="coffee_inventory",
        charset="utf8mb4"
    )
    return connection
