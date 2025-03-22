from flask import Flask
from db_connection import get_db_connection

app = Flask(__name__)

@app.route('/')
def home():
    return "Test all good"

@app.route('/testdb')
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products;")
        product_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        return f"DB Connection OK! Found {product_count} products."
    except Exception as e:
        return f"Error connecting to DB: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
