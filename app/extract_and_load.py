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

    # Create an empty DataFrame to store all stock information
    all_info = pd.DataFrame()

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
        
        # Fetch additional stock information
        info = ticker.info
        stock_name = info.get('shortName', None)
        pe_ratio = info.get('trailingPE', None)
        dividend_yield = info.get('dividendYield', None)
        eps = info.get('trailingEps', None)
        ps_ratio = info.get('priceToSalesTrailing12Months', None)
        
        # Append the information to the all_info DataFrame
        df_info = pd.DataFrame({
            'Symbol': [stock],
            'Aktienname': [stock_name],
            'KGV': [pe_ratio],
            'Dividendenrendite': [dividend_yield],
            'Gewinn': [eps],
            'KUV': [ps_ratio]
        })
        all_info = pd.concat([all_info, df_info], ignore_index=True)

    # Save all stock information to a single table in the database
    all_info.to_sql('information', engine, if_exists='replace', index=False)
    print("All stock information saved to database")

if __name__ == "__main__":
    fetch_and_save_stock_data()