from flask import Blueprint, jsonify
from flask_login import current_user
from rbac import role_required
from forecast_arima import get_total_sales_dataframe, build_arima_forecast

forecast_bp = Blueprint('forecast_bp', __name__)

@forecast_bp.route('/forecast', methods=['GET'])
@role_required(['manager','admin'])
def get_forecast():
    df_sales = get_total_sales_dataframe()
    forecast_series = build_arima_forecast(df_sales, forecast_days=30)
    forecast_df = forecast_series.reset_index()
    forecast_df.columns = ['date', 'forecast']
    data = forecast_df.to_dict(orient='records')
    return jsonify(data), 200