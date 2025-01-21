import pandas as pd
from datetime import timedelta

def calculate_kpis_portfolio(df_daily, stock, stock_name, num_stocks, buy_in, stopp, pe_ratio, dividend_yield, eps, ps_ratio):
    # Calculate KPIs if df_daily is not empty
    if not df_daily.empty:
        latest_data = df_daily.iloc[-1]
        current_price = round(latest_data['Close'], 2)
        high_52w = round(df_daily['High'].rolling(window=252, min_periods=1).max().iloc[-1], 2)
        low_52w = round(df_daily['Low'].rolling(window=252, min_periods=1).min().iloc[-1], 2)
        ath = round(df_daily['Close'].max(), 2)
        percentage_to_ath = round(((current_price - ath) / ath) * 100, 2)
        percentage_to_ath_str = f"{percentage_to_ath} %"

        roll_max = df_daily['Close'].cummax()
        drawdown = df_daily['Close'] / roll_max - 1
        max_drawdown = round(drawdown.min() * 100, 2)

        # Calculate the average annual performance 
        most_recent_date = df_daily['Date'].max()
        date_10_years_ago = most_recent_date - timedelta(days=10 * 365)
        available_data = df_daily[df_daily['Date'] >= date_10_years_ago]
        timeframe_years = (most_recent_date - available_data['Date'].min()).days / 365
        price_start = available_data['Close'].iloc[0]
        avg_annual_performance = round(((current_price / price_start) ** (1 / timeframe_years) - 1) * 100, 2)
        avg_annual_performance_str = f"{avg_annual_performance} %"
        
        # Calculate the value of the stocks
        current_value = round(num_stocks * current_price, 2)
        current_value_str = f"{current_value} €"

        # Create a DataFrame with the KPIs
        df_info = pd.DataFrame({
            'Symbol': [stock],
            'Name': [stock_name],
            'Anzahl': [num_stocks],
            'EK': [buy_in],
            'Aktueller Wert': [current_value_str],
            'Aktueller Preis': [current_price],
            'Stopp': [stopp],
            'KGV': [round(pe_ratio, 2) if pe_ratio is not None else None],
            'Div-Rendite': [round(dividend_yield * 100, 2) if dividend_yield is not None else None],
            '⌀ % pro Jahr': [avg_annual_performance_str],
            'High': [high_52w],
            'Low': [low_52w],
            'ATH': [ath],
            'Abstand ATH': [percentage_to_ath_str],
            'Max Drawdown': [max_drawdown]
            
        })
        return df_info
    else:
        print(f"No data available for {stock}")
        return pd.DataFrame()

def calculate_kpis_starlist(df_daily, stock, stock_name, pe_ratio, dividend_yield, eps, ps_ratio):
    # Calculate KPIs if df_daily is not empty

    latest_data = df_daily.iloc[-1]
    current_price = round(latest_data['Close'], 2)
    high_52w = round(df_daily['High'].rolling(window=252, min_periods=1).max().iloc[-1], 2)
    low_52w = round(df_daily['Low'].rolling(window=252, min_periods=1).min().iloc[-1], 2)
    all_time_high = round(df_daily['High'].max(), 2)
    percentage_to_ath = round(((current_price - all_time_high) / all_time_high) * 100, 2)
    percentage_to_ath_str = f"{percentage_to_ath} %"
        # Calculate the average annual performance 
    most_recent_date = df_daily['Date'].max()
    date_10_years_ago = most_recent_date - timedelta(days=10 * 365)
    available_data = df_daily[df_daily['Date'] >= date_10_years_ago]
    timeframe_years = (most_recent_date - available_data['Date'].min()).days / 365
    price_start = available_data['Close'].iloc[0]
    avg_annual_performance = round(((current_price / price_start) ** (1 / timeframe_years) - 1) * 100, 2)
    avg_annual_performance_str = f"{avg_annual_performance} %"
        
    roll_max = df_daily['Close'].cummax()
    drawdown = df_daily['Close'] / roll_max - 1
    max_drawdown = round(drawdown.min() * 100, 2)

        # Create a DataFrame with the KPIs
    df_info = pd.DataFrame({
        'Symbol': [stock],
        'Name': [stock_name],
        'KGV': [round(pe_ratio, 2) if pe_ratio is not None else None],
        'Div-Rendite': [round(dividend_yield * 100, 2) if dividend_yield is not None else None],
        'Gewinn': [round(eps, 2) if eps is not None else None],
        'KUV': [round(ps_ratio, 2) if ps_ratio is not None else None],
        '⌀ % pro Jahr': [avg_annual_performance_str],
        'Aktueller Preis': [current_price],
        'High': [high_52w],
        'Low': [low_52w],
        'ATH': [all_time_high],
        'Abstand ATH': [percentage_to_ath_str],
        'Max Drawdown': [max_drawdown]
    })
    return df_info
    #else:
        #print(f"No data available for {stock}")
    return pd.DataFrame()