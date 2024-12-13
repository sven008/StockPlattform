import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, inspect
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from kpi import calculate_kpis_starlist

# Load environment variables from .env file
load_dotenv()

# Get the database URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')

def fetch_and_save_stock_data():
    # Read the list of stock tickers from the file
    starlist_data = pd.read_csv('starlist.txt', sep=';', usecols=[0], names=['symbol'])

    # Connect to PostgreSQL database
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)

    # Create an empty DataFrame to store all stock information
    all_info = pd.DataFrame()

    # Fetch stock data for each ticker and save it to the database
    for _, row in starlist_data.iterrows():
        stock = row['symbol']
        print(f"Fetching data for {stock}")
        ticker = yf.Ticker(stock)
        
        # Fetch daily stock data
        df_daily = ticker.history(period="10y", interval="1d", prepost=True)
        df_daily.reset_index(inplace=True)
        table_name_daily = f"{stock.lower()}_daily"

        # Check if the table exists
        if inspector.has_table(table_name_daily):
            # Load existing data
            df_existing = pd.read_sql_table(table_name_daily, engine)
            # Find the last available date in the existing data
            last_date = df_existing['Date'].max()
            # Filter new data
            df_new = df_daily[df_daily['Date'] > last_date]
            if not df_new.empty:
                # Append new data to the existing data
                df_new.to_sql(table_name_daily, engine, if_exists='append', index=False)
                print(f"New data for {stock} added to database")
            else:
                print(f"No new data for {stock}")
        else:
            # Save new data to the database
            df_daily.to_sql(table_name_daily, engine, if_exists='replace', index=False)
            print(f"Daily data for {stock} saved to database")
        
        # Fetch additional stock information
        info = ticker.info
        stock_name = info.get('shortName', None)
        pe_ratio = info.get('trailingPE', None)
        dividend_yield = info.get('dividendYield', None)
        eps = info.get('trailingEps', None)
        ps_ratio = info.get('priceToSalesTrailing12Months', None)
        
        # Calculate KPIs and append to all_info DataFrame
        df_info = calculate_kpis_starlist(df_daily, stock, stock_name, pe_ratio, dividend_yield, eps, ps_ratio)
        all_info = pd.concat([all_info, df_info], ignore_index=True)

    # Save all stock information to a single table in the database
    if inspector.has_table('starlist_information'):
        df_existing_info = pd.read_sql_table('starlist_information', engine)
        all_info = pd.concat([df_existing_info, all_info]).drop_duplicates(subset=['Symbol'], keep='last')
    all_info.to_sql('starlist_information', engine, if_exists='replace', index=False)
    print("All stock information saved to database")

if __name__ == "__main__":
    fetch_and_save_stock_data()