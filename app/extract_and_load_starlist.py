# app/extract_and_load_starlist.py

import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, inspect
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

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
        
        # Calculate KPIs
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

        # Append the information to the all_info DataFrame
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
        all_info = pd.concat([all_info, df_info], ignore_index=True)

    # Save all stock information to a single table in the database
    if inspector.has_table('starlist_information'):
        df_existing_info = pd.read_sql_table('starlist_information', engine)
        all_info = pd.concat([df_existing_info, all_info]).drop_duplicates(subset=['Symbol'], keep='last')
    all_info.to_sql('starlist_information', engine, if_exists='replace', index=False)
    print("All stock information saved to database")

if __name__ == "__main__":
    fetch_and_save_stock_data()