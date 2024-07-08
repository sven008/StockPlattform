# app/extract_and_load.py

import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine

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
        df = ticker.history(period="10y")
        
        # Save to PostgreSQL database
        table_name = stock.lower()
        df.to_sql(table_name, engine, if_exists='replace', index=True)
        print(f"Data for {stock} saved to database")

if __name__ == "__main__":
    fetch_and_save_stock_data()
