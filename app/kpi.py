import pandas as pd

def calculate_kpis_portfolio(df_daily, stock, stock_name, num_stocks, buy_in, stopp, pe_ratio, dividend_yield, eps, ps_ratio):
    # Calculate KPIs if df_daily is not empty
    if not df_daily.empty:
        latest_data = df_daily.iloc[-1]
        current_price = round(latest_data['Close'], 2)
        high_52w = round(df_daily['High'].rolling(window=252, min_periods=1).max().iloc[-1], 2)
        low_52w = round(df_daily['Low'].rolling(window=252, min_periods=1).min().iloc[-1], 2)
        all_time_high = round(df_daily['High'].max(), 2)
        percentage_to_ath = round(((current_price - all_time_high) / all_time_high) * 100, 2)

        roll_max = df_daily['Close'].cummax()
        drawdown = df_daily['Close'] / roll_max - 1
        max_drawdown = round(drawdown.min() * 100, 2)

        # Calculate average annual performance
        price_10_years_ago = df_daily[df_daily['Date'] == df_daily['Date'].min()]['Close'].values[0]
        avg_annual_performance = round(((current_price / price_10_years_ago) ** (1/10) - 1) * 100, 2)

        # Create a DataFrame with the KPIs
        df_info = pd.DataFrame({
            'Symbol': [stock],
            'Name': [stock_name],
            'Anzahl': [num_stocks],
            'EK': [buy_in],
            'Stopp': [stopp],
            'KGV': [round(pe_ratio, 2) if pe_ratio is not None else None],
            'Div-Rendite': [round(dividend_yield * 100, 2) if dividend_yield is not None else None],
            'Gewinn': [round(eps, 2) if eps is not None else None],
            'KUV': [round(ps_ratio, 2) if ps_ratio is not None else None],
            '⌀ % pro Jahr': [avg_annual_performance],
            'Aktueller Preis': [current_price],
            'High': [high_52w],
            'Low': [low_52w],
            'ATH': [all_time_high],
            'Abstand ATH': [percentage_to_ath],
            'Max Drawdown': [max_drawdown]
        })
        return df_info
    else:
        print(f"No data available for {stock}")
        return pd.DataFrame()

def calculate_kpis_starlist(df_daily, stock, stock_name, pe_ratio, dividend_yield, eps, ps_ratio):
    # Calculate KPIs if df_daily is not empty
    if not df_daily.empty:
        latest_data = df_daily.iloc[-1]
        current_price = round(latest_data['Close'], 2)
        high_52w = round(df_daily['High'].rolling(window=252, min_periods=1).max().iloc[-1], 2)
        low_52w = round(df_daily['Low'].rolling(window=252, min_periods=1).min().iloc[-1], 2)
        all_time_high = round(df_daily['High'].max(), 2)
        percentage_to_ath = round(((current_price - all_time_high) / all_time_high) * 100, 2)

        roll_max = df_daily['Close'].cummax()
        drawdown = df_daily['Close'] / roll_max - 1
        max_drawdown = round(drawdown.min() * 100, 2)

        # Calculate average annual performance
        price_10_years_ago = df_daily[df_daily['Date'] == df_daily['Date'].min()]['Close'].values[0]
        avg_annual_performance = round(((current_price / price_10_years_ago) ** (1/10) - 1) * 100, 2)

        # Create a DataFrame with the KPIs
        df_info = pd.DataFrame({
            'Symbol': [stock],
            'Name': [stock_name],
            'KGV': [round(pe_ratio, 2) if pe_ratio is not None else None],
            'Div-Rendite': [round(dividend_yield * 100, 2) if dividend_yield is not None else None],
            'Gewinn': [round(eps, 2) if eps is not None else None],
            'KUV': [round(ps_ratio, 2) if ps_ratio is not None else None],
            '⌀ % pro Jahr': [avg_annual_performance],
            'Aktueller Preis': [current_price],
            'High': [high_52w],
            'Low': [low_52w],
            'ATH': [all_time_high],
            'Abstand ATH': [percentage_to_ath],
            'Max Drawdown': [max_drawdown]
        })
        return df_info
    else:
        print(f"No data available for {stock}")
        return pd.DataFrame()