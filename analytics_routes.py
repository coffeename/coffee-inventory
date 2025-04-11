import io
import pandas as pd
import pymysql
from flask import Blueprint, jsonify, send_file
from flask_login import current_user
from rbac import role_required
from forecast_arima import get_total_sales_dataframe, build_arima_forecast
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from db_connection import get_db_connection

analytics_bp = Blueprint('analytics_bp', __name__)

def get_actual_sales():
    # Підключення до БД з реальними параметрами
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="CoffeeShop_2025",
        database="coffee_inventory",
        charset="utf8mb4"
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DATE(o.order_date) AS dt, SUM(oi.quantity) AS actual_sales
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        GROUP BY DATE(o.order_date)
        ORDER BY dt
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    df = pd.DataFrame(rows, columns=['dt', 'actual_sales'])
    df['dt'] = pd.to_datetime(df['dt'])
    df.set_index('dt', inplace=True)
    # Заповнюємо пропуски нулями, щоб мати щоденний індекс
    return df.asfreq('D').fillna(0)

@analytics_bp.route('/analytics/chart', methods=['GET'])
def analytics_chart():
    df_actual = get_actual_sales()
    forecast_series = build_arima_forecast(get_total_sales_dataframe(), forecast_days=30)

    plt.figure(figsize=(20, 10))
    plt.plot(df_actual.index, df_actual['actual_sales'], marker='o', label='Реальні продажі')
    plt.plot(forecast_series.index, forecast_series, marker='o', label='Прогноз')

    plt.ylabel('К-сть продажів/день', fontsize=16)
    plt.title('Реальні продажі vs Прогноз', fontsize=18)

    ax = plt.gca()
    ax.yaxis.set_major_locator(mticker.MultipleLocator(10))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=14))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=0)
    plt.legend()
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    return send_file(img, mimetype='image/png')

@analytics_bp.route('/analytics/data', methods=['GET'])
@role_required(['manager','admin'])
def analytics_data():
    # Підготовка фактичних даних
    df_act = get_actual_sales().reset_index().rename(columns={'dt':'date','actual_sales':'actual'})
    df_act['date'] = df_act['date'].dt.strftime('%Y-%m-%d')
    actual = df_act.to_dict(orient='records')

    # Підготовка прогнозу
    forecast_df = build_arima_forecast(get_total_sales_dataframe(), forecast_days=30).reset_index()
    forecast_df.columns = ['date','forecast']
    forecast_df['date'] = forecast_df['date'].dt.strftime('%Y-%m-%d')
    forecast = forecast_df.to_dict(orient='records')

    return jsonify({
        'actual': actual,
        'forecast': forecast
    }), 200

@analytics_bp.route('/analytics/top-products', methods=['GET'])
@role_required(['manager','admin'])
def top_products():
    """
    Топ‑7 найпопулярніших продуктів за всю історію.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
      SELECT
        p.name AS product_name,
        SUM(oi.quantity) AS count
      FROM order_items oi
      JOIN products p ON p.id = oi.product_id
      GROUP BY p.id, p.name
      ORDER BY count DESC
      LIMIT 7
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    result = [
        {"productName": name, "count": cnt}
        for name, cnt in rows
    ]
    return jsonify(result), 200

@analytics_bp.route('/analytics/orders-by-barista', methods=['GET'])
@role_required(['manager','admin'])
def orders_by_barista():
    """
    Кількість оформлених замовлень за весь час по кожному баристі.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
      SELECT
        u.username AS barista,
        COUNT(o.id) AS count
      FROM orders o
      JOIN users u ON u.id = o.user_id
      WHERE u.role = 'barista'
      GROUP BY u.id, u.username
      ORDER BY count DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    result = [
        {"barista": username, "count": cnt}
        for username, cnt in rows
    ]
    return jsonify(result), 200