# app/extract_and_load.py

import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta

def fetch_and_save_stock_data():
    # Read the list of stock tickers from the file
    with open('stocks.txt', 'r') as file:
        stocks = file.read().splitlines()

    # Connect to PostgreSQL database
    engine = create_engine('postgresql://postgres:postgres@db:5432/stockdata')

    # Fetch stock data for each ticker and save it to the database
    for stock in stocks:
        print(f"Fetching data for {stock}")
        ticker = yf.Ticker(stock)
        
        # Fetch daily stock data
        df_daily = ticker.history(period="10y", interval="1d", prepost=True)
        df_daily.reset_index(inplace=True)
        table_name_daily = f"{stock.lower()}_daily"
        df_daily.to_sql(table_name_daily, engine, if_exists='replace', index=False)
        print(f"Daily data for {stock} saved to database")
        
        # Fetch hourly stock data (limited to the last 700 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=700)
        df_hourly = ticker.history(start=start_date, end=end_date, interval="1h", prepost=True)
        df_hourly.reset_index(inplace=True)
        table_name_hourly = f"{stock.lower()}_hourly"
        df_hourly.to_sql(table_name_hourly, engine, if_exists='replace', index=False)
        print(f"Hourly data for {stock} saved to database")
        
        # Fetch minute stock data for the last 7 days (1 week)
        start_date = end_date - timedelta(days=7)
        df_minute = ticker.history(start=start_date, end=end_date, interval="1m", prepost=True)
        df_minute.reset_index(inplace=True)
        table_name_minute = f"{stock.lower()}_minute"
        df_minute.to_sql(table_name_minute, engine, if_exists='replace', index=False)
        print(f"Minute data for {stock} saved to database")

if __name__ == "__main__":
    fetch_and_save_stock_data()