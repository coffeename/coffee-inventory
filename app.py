from flask import Flask, send_from_directory
from flask_login import LoginManager
from flask_cors import CORS
from db_connection import get_db_connection
from models import User
from datetime import timedelta
import os

app = Flask(__name__, static_folder='../coffeefront/build', static_url_path='')
app.config['SECRET_KEY'] = 'some-secret-key'
app.config['JSON_AS_ASCII'] = False
app.permanent_session_lifetime = timedelta(days=7)

# CORS для React
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    try:
        user_id = int(user_id)
    except ValueError:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role FROM users WHERE id = %s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return User(id=row[0], username=row[1], role=row[2])
    return None

# SPA fallback для React‑роутінгу
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

# ---- Імпорт Blueprints ----
from auth import auth_bp
from orders import orders_bp
from users import users_bp
from products import products_bp
from forecast_routes import forecast_bp        # прогноз ARIMA
from stock_notifications import stock_bp
from analytics_routes import analytics_bp      # новий ендпоінт /analytics/data та /analytics/chart
from alerts import alerts_bp

# ---- Реєстрація Blueprints ----
app.register_blueprint(auth_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(users_bp)
app.register_blueprint(products_bp)
app.register_blueprint(forecast_bp)
app.register_blueprint(stock_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(alerts_bp)

if __name__ == '__main__':
    app.run(debug=True)
