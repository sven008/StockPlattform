# app/extract_and_load_portfolio.py

import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta

def fetch_and_save_stock_data():
    # Read the list of stock tickers, number of stocks, buy-in prices, and stopp values from the file
    stocks_data = pd.read_csv('stocks.txt', sep=';', header=None, names=['symbol', 'num_stocks', 'buy_in', 'stopp'])

    # Connect to PostgreSQL database
    engine = create_engine('postgresql://postgres:postgres@db:5432/stockdata')

    # Create an empty DataFrame to store all stock information
    all_info = pd.DataFrame()

    # Fetch stock data for each ticker and save it to the database
    for _, row in stocks_data.iterrows():
        stock = row['symbol']
        num_stocks = row['num_stocks']
        buy_in = row['buy_in']
        stopp = row['stopp']
        print(f"Fetching data for {stock}")
        ticker = yf.Ticker(stock)
        
        # Fetch daily stock data
        df_daily = ticker.history(period="10y", interval="1d", prepost=True)
        df_daily.reset_index(inplace=True)
        table_name_daily = f"{stock.lower()}_daily"
        df_daily.to_sql(table_name_daily, engine, if_exists='replace', index=False)
        print(f"Daily data for {stock} saved to database")
        
        # Fetch additional stock information
        info = ticker.info
        stock_name = info.get('shortName', None)
        dividend_yield = info.get('dividendYield', None)
        
        # Calculate KPIs
        latest_data = df_daily.iloc[-1]
        current_price = round(latest_data['Close'], 2)
        all_time_high = round(df_daily['High'].max(), 2)
        percentage_to_ath = round(((current_price - all_time_high) / all_time_high) * 100, 2)

        # Calculate average annual performance
        df_daily['Year'] = df_daily['Date'].dt.year
        annual_returns = df_daily.groupby('Year')['Close'].apply(lambda x: x.iloc[-1] / x.iloc[0] - 1)
        avg_annual_performance = round(annual_returns.mean() * 100, 2)

    
        # Append the information to the all_info DataFrame
        df_info = pd.DataFrame({
            'Symbol': [stock],
            'Name': [stock_name],
            'Anzahl': [num_stocks],
            'EK': [buy_in],
            'Div-Rendite': [round(dividend_yield * 100, 2) if dividend_yield is not None else None],
            'Aktueller Preis': [current_price],
            'ATH': [all_time_high],
            'Abstand ATH': [percentage_to_ath],
            'Durchschn. % pro Jahr': [avg_annual_performance],
            'Stopp': [stopp]
        })
        all_info = pd.concat([all_info, df_info], ignore_index=True)

    # Save all stock information to a single table in the database
    all_info.to_sql('information', engine, if_exists='replace', index=False)
    print("All stock information saved to database")

if __name__ == "__main__":
    fetch_and_save_stock_data()