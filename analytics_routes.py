import datetime
import pandas as pd
import pymysql
from flask import Blueprint, jsonify, send_file
from forecast_arima import get_total_sales_dataframe, build_arima_forecast
import io
import matplotlib.pyplot as plt

analytics_bp = Blueprint('analytics_bp', __name__)

def get_actual_sales():
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="CoffeeShop_2025",
        database="coffee_inventory",
        charset="utf8mb4"
    )
    cursor = conn.cursor()
    sql = """
    SELECT DATE(o.order_date) AS dt, SUM(oi.quantity) AS actual_sales
    FROM orders o
    JOIN order_items oi ON o.id = oi.order_id
    GROUP BY DATE(o.order_date)
    ORDER BY dt
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    df = pd.DataFrame(rows, columns=['dt', 'actual_sales'])
    df['dt'] = pd.to_datetime(df['dt'])
    df.set_index('dt', inplace=True)
   
    df = df.asfreq('D').fillna(0)
    return df


@analytics_bp.route('/analytics/chart', methods=['GET'])
def analytics_chart():
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import matplotlib.ticker as mticker
    import io

    df_actual = get_actual_sales()  
    forecast_series = build_arima_forecast(get_total_sales_dataframe(), forecast_days=30)
    

    plt.figure(figsize=(20, 10))
    plt.plot(df_actual.index, df_actual['actual_sales'], marker='o', color='cornflowerblue')
    plt.plot(forecast_series.index, forecast_series, marker='o', color='green')
    last_date = df_actual.index[-1]
    last_val = df_actual['actual_sales'].iloc[-1]
    first_date = forecast_series.index[0]
    first_val = forecast_series.iloc[0]

    plt.plot([last_date, first_date], [last_val, first_val], color='cornflowerblue')
    plt.ylabel('К-сть продажів/день', fontsize=16)
    plt.title('Реальні продажі vs Прогноз', fontsize=18)

    ax = plt.gca()
    ax.yaxis.set_major_locator(mticker.MultipleLocator(10))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=14))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

    plt.xticks(rotation=0)
    plt.legend()
    plt.tight_layout()

    img_io = io.BytesIO()
    plt.savefig(img_io, format='png')
    plt.close()
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')
