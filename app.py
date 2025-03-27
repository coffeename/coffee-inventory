from flask import Flask
from flask_login import LoginManager
from db_connection import get_db_connection
from models import User


app = Flask(__name__)
app.config['SECRET_KEY'] = 'some-secret-key'
app.config['JSON_AS_ASCII'] = False

login_manager = LoginManager()
login_manager.init_app(app)

    
@login_manager.user_loader
def load_user(user_id):
    user_id = int(user_id)

    conn = get_db_connection()
    cursor = conn.cursor()
    sql = "SELECT id, username, role FROM users WHERE id = %s"
    cursor.execute(sql, (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        return User(id=row[0], username=row[1], role=row[2])
    else:
        return None
    
@app.route('/')
def home():
    return "Все ок, їїї. ?!"

from auth import auth_bp
from orders import orders_bp
from users import users_bp
from products import products_bp
from forecast_routes import forecast_bp
from stock_notifications import stock_bp
from analytics_routes import analytics_bp

app.register_blueprint(auth_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(users_bp)
app.register_blueprint(products_bp)
app.register_blueprint(forecast_bp)
app.register_blueprint(stock_bp)
app.register_blueprint(analytics_bp)

if __name__ == '__main__':
    app.run(debug=True)
