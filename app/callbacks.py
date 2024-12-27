from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import subprocess
from dash import html
from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the database URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')

def fetch_stock_info(engine):
    return pd.read_sql_table('information', engine)

def fetch_starlist_info(engine):
    return pd.read_sql_table('starlist_information', engine)

def calculate_chart_data(stock, timeframe, engine, fetch_info_func, include_stopp, log_scale=False):
    df = pd.read_sql_table(f"{stock}_daily", engine)
    df['Datetime'] = pd.to_datetime(df['Datetime'] if 'Datetime' in df.columns else df['Date'])
    df.set_index('Datetime', inplace=True)
    df['200day_MA'] = df['Open'].rolling(window=200).mean()

    end_date = datetime.now()
    start_date = {
        '1w': end_date - timedelta(days=7),
        '1m': end_date - timedelta(days=30),
        '1y': end_date - timedelta(days=365),
        'ytd': datetime(end_date.year, 1, 1),
        '5y': end_date - timedelta(days=5*365),
        '10y': end_date - timedelta(days=10*365),
        'max': df.index.min()
    }[timeframe]

    if df.index.tz is not None:
        start_date = pd.Timestamp(start_date).tz_localize(df.index.tz) if start_date.tzinfo is None else start_date.tz_convert(df.index.tz)
        end_date = pd.Timestamp(end_date).tz_localize(df.index.tz) if end_date.tzinfo is None else end_date.tz.convert(df.index.tz)

    df_filtered = df[(df.index >= start_date) & (df.index <= end_date)]

    # Find high and low points
    high_point = df_filtered['High'].idxmax()
    low_point = df_filtered['Low'].idxmin()

    # Fetch stopp value from the database if needed
    stopp_value = None
    if include_stopp:
        df_info = fetch_info_func(engine)
        stopp_value = df_info[df_info['Symbol'].str.lower() == stock]['Stopp'].values[0]

    data = [
        go.Scatter(
            x=df_filtered.index,
            y=df_filtered['Close'],
            mode='lines',
            name=stock
        ),
        go.Scatter(
            x=df_filtered.index,
            y=df.loc[df_filtered.index, '200day_MA'],
            mode='lines',
            name='200-Day MA'
        ),
        go.Scatter(
            x=[high_point],
            y=[df_filtered.loc[high_point, 'High']],
            mode='markers+text',
            text=[f"High: {df_filtered.loc[high_point, 'Close']:.2f}"],
            textposition='top right',
            marker=dict(color='red', size=10),
            name='High'
        ),
        go.Scatter(
            x=[low_point],
            y=[df_filtered.loc[low_point, 'Low']],
            mode='markers+text',
            text=[f"Low: {df_filtered.loc[low_point, 'Close']:.2f}"],
            textposition='bottom right',
            marker=dict(color='blue', size=10),
            name='Low'
        )
    ]

    if stopp_value is not None:
        data.append(
            go.Scatter(
                x=df_filtered.index,
                y=[stopp_value] * len(df_filtered.index),
                mode='lines',
                line=dict(color='orange', dash='dash'),
                name='Stopp'
            )
        )

    layout = {
        'title': f'{stock.upper()} Stock Prices ({timeframe})',
        'xaxis': {
            'rangeslider': {'visible': False},
            'tickmode': 'auto',
            'nticks': 20  # Increase the number of ticks on the x-axis
        },
        'yaxis': {
            'type': 'log' if log_scale else 'linear'
        },
        'height': 600,
        'paper_bgcolor': 'white',
        'plot_bgcolor': 'white',
        'font': {'color': 'black'}
    }

    figure = {
        'data': data,
        'layout': layout
    }
    return figure

def calculate_portfolio_value(engine):
    df_info = fetch_stock_info(engine)
    portfolio_value = pd.DataFrame()

    for _, row in df_info.iterrows():
        stock = row['Symbol'].lower()
        num_stocks = row['num_stocks']
        df_daily = pd.read_sql_table(f"{stock}_daily", engine)
        df_daily['Date'] = pd.to_datetime(df_daily['Date'])
        df_daily.set_index('Date', inplace=True)
        df_daily[f'{stock}_value'] = df_daily['Close'] * num_stocks
        if portfolio_value.empty:
            portfolio_value = df_daily[[f'{stock}_value']]
        else:
            portfolio_value = portfolio_value.join(df_daily[[f'{stock}_value']], how='outer')

    portfolio_value['Total Value'] = portfolio_value.sum(axis=1)
    portfolio_value.reset_index(inplace=True)

    figure = {
        'data': [
            go.Scatter(
                x=portfolio_value['Date'],
                y=portfolio_value['Total Value'],
                mode='lines',
                name='Total Portfolio Value'
            )
        ],
        'layout': {
            'title': 'Total Portfolio Value Over Time',
            'xaxis': {
                'rangeslider': {'visible': False},
                'tickmode': 'auto',
                'nticks': 20  # Increase the number of ticks on the x-axis
            },
            'height': 600,
            'paper_bgcolor': 'white',
            'plot_bgcolor': 'white',
            'font': {'color': 'black'}
        }
    }
    return figure

def register_callbacks(app, engine):
    @app.callback(
        Output('info-table', 'children'),
        [Input('refresh-button', 'n_clicks')]
    )
    def update_info_table(n_clicks):
        if n_clicks > 0:
            # Run the extract_and_load.py script
            subprocess.run(["python", "extract_and_load.py", "portfolio"], check=True)
        
        df_info = fetch_stock_info(engine)

        # Create table header
        header = [html.Th(col, style={'border': '1px solid black', 'padding': '10px'}) for col in df_info.columns]

        # Create table rows
        rows = []
        for i in range(len(df_info)):
            row = [html.Td(df_info.iloc[i][col], style={'border': '1px solid black', 'padding': '10px'}) for col in df_info.columns]
            rows.append(html.Tr(row))

        return [html.Thead(html.Tr(header)), html.Tbody(rows)]

    @app.callback(
        Output('starlist-table', 'children'),
        [Input('refresh-starlist-button', 'n_clicks')]
    )
    def update_starlist_table(n_clicks):
        if n_clicks > 0:
            # Run the extract_and_load.py script
            subprocess.run(["python", "extract_and_load.py", "starlist"], check=True)
        
        df_starlist = fetch_starlist_info(engine)

        # Create table header
        header = [html.Th(col, style={'border': '1px solid black', 'padding': '10px'}) for col in df_starlist.columns]

        # Create table rows
        rows = []
        for i in range(len(df_starlist)):
            row = [html.Td(df_starlist.iloc[i][col], style={'border': '1px solid black', 'padding': '10px'}) for col in df_starlist.columns]
            rows.append(html.Tr(row))

        return [html.Thead(html.Tr(header)), html.Tbody(rows)]

    @app.callback(
        Output('stock-chart', 'figure'),
        [Input('stock-dropdown', 'value'),
         Input('timeframe-radio', 'value'),
         Input('log-scale-checkbox', 'value')]
    )
    def update_chart(stock, timeframe, log_scale):
        return calculate_chart_data(stock, timeframe, engine, fetch_stock_info, include_stopp=True, log_scale=log_scale)

    @app.callback(
        Output('starlist-chart', 'figure'),
        [Input('starlist-dropdown', 'value'),
         Input('starlist-timeframe-radio', 'value'),
         Input('log-scale-checkbox', 'value')]
    )
    def update_starlist_chart(stock, timeframe, log_scale):
        return calculate_chart_data(stock, timeframe, engine, fetch_starlist_info, include_stopp=False, log_scale=log_scale)

    @app.callback(
        Output('portfolio-value-chart', 'figure'),
        [Input('refresh-button', 'n_clicks')]
    )
    def update_portfolio_value_chart(n_clicks):
        if n_clicks > 0:
            return calculate_portfolio_value(engine)
        return {}

    @app.callback(
        Output('save-db-button', 'n_clicks'),
        [Input('save-db-button', 'n_clicks')]
    )
    def save_database_to_local_file(n_clicks):
        if n_clicks > 0:
            print("Save database button clicked")
            # Ensure the backup directory exists
            backup_dir = '/home/pi/Backup'
            os.makedirs(backup_dir, exist_ok=True)
            print(f"Backup directory {backup_dir} ensured")

            # Connect to PostgreSQL database
            engine = create_engine(DATABASE_URL)
            inspector = inspect(engine)

            # List of tables to backup
            tables = inspector.get_table_names()

            # Backup each table to a CSV file
            for table in tables:
                df = pd.read_sql_table(table, engine)
                df.to_csv(f'{backup_dir}/{table}.csv', index=False)
                print(f"Table {table} saved to {backup_dir}/{table}.csv")

        return n_clicks