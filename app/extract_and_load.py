import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine

def fetch_and_save_stock_data():
    # Fetch stock data for Microsoft for the last 10 years on a daily basis
    msft = yf.Ticker("MSFT")
    df = msft.history(period="10y")

    # Save to PostgreSQL database
    engine = create_engine('postgresql://postgres:postgres@db:5432/stockdata')
    df.to_sql('microsoft_stock', engine, if_exists='replace', index=True)
    print("Data saved to database")

if __name__ == "__main__":
    fetch_and_save_stock_data()