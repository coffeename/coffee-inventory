import warnings
import pandas as pd
import pymysql
from pmdarima import auto_arima

warnings.filterwarnings(
    'ignore',
    '.*force_all_finite.*',
    category=FutureWarning
)

pd.set_option('display.max_rows', None)

HOLIDAYS = [
    "2024-12-25",
    "2024-12-31",
    "2025-01-01",
    "2025-01-06"
]

def mark_holidays(df):
    """ Додає колонку is_holiday=1, якщо дата входить до HOLIDAYS, інакше 0. """
    df['is_holiday'] = df.index.strftime('%Y-%m-%d').isin(HOLIDAYS).astype(int)
    return df

def get_total_sales_dataframe():
    """ 
    Витягує суму продажів по всіх товарах (за датою), 
    повертає DataFrame з індексом-датою і колонками:
      - total_sold
      - is_holiday (0/1)
    """
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="CoffeeShop_2025",
        database="coffee_inventory",
        charset="utf8mb4"
    )
    cursor = conn.cursor()

    sql = """
    SELECT
        DATE(o.order_date) AS dt,
        SUM(oi.quantity) AS total_sold
    FROM orders o
    JOIN order_items oi ON o.id = oi.order_id
    GROUP BY DATE(o.order_date)
    ORDER BY dt
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    df = pd.DataFrame(rows, columns=['dt','total_sold'])
    df['dt'] = pd.to_datetime(df['dt'])
    df.set_index('dt', inplace=True)
    df = df.asfreq('D')
    df['total_sold'] = df['total_sold'].fillna(0)
    df = mark_holidays(df)

    return df

def build_arima_forecast(df, forecast_days=30):
    """
    Приймає DataFrame з колонками: total_sold, is_holiday.
    Використовує auto_arima з exogenous, повертає прогноз на forecast_days.
    """
    ts = df['total_sold']
    exog = df[['is_holiday']]

    model = auto_arima(
        ts,
        X=exog,
        start_p=1, start_q=1,
        max_p=5, max_q=5,
        d=1,
        seasonal=False,
        trace=True,             
        error_action='ignore',
        suppress_warnings=True,
        stepwise=True
    )

    last_date = df.index[-1]
    future_index = pd.date_range(last_date + pd.Timedelta(days=1), periods=forecast_days, freq='D')
    future_exog = pd.DataFrame(index=future_index)

    future_exog['is_holiday'] = future_exog.index.strftime('%Y-%m-%d').isin(HOLIDAYS).astype(int)

    forecast_array = model.predict(n_periods=forecast_days, X=future_exog[['is_holiday']])
    forecast_series = pd.Series(forecast_array, index=future_index, name='forecast')

    return forecast_series

if __name__ == '__main__':
    df_sales = get_total_sales_dataframe()
    print(df_sales)
    
    forecast_series = build_arima_forecast(df_sales, forecast_days=30)
    print("\n=== Прогноз (30 днів) ===")
    print(forecast_series)
