import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta

# Initialize Dash app
app = dash.Dash(__name__)

# Connect to PostgreSQL database
engine = create_engine('postgresql://postgres:postgres@db:5432/stockdata')

# Read the list of stock tickers from the file
with open('stocks.txt', 'r') as file:
    stocks = file.read().splitlines()

# Define layout
app.layout = html.Div(children=[
    html.H1(children='Stock Prices'),

    dcc.Dropdown(
        id='stock-dropdown',
        options=[{'label': stock, 'value': stock.lower()} for stock in stocks],
        value=stocks[0].lower(),
        clearable=False
    ),
    
    dcc.RadioItems(
        id='timeframe-radio',
        options=[
            {'label': '1 Day', 'value': '1d'},
            {'label': '1 Week', 'value': '1w'},
            {'label': '1 Month', 'value': '1m'},
            {'label': '1 Year', 'value': '1y'},
            {'label': 'YTD', 'value': 'ytd'},
            {'label': '5 Years', 'value': '5y'},
            {'label': 'Max', 'value': 'max'}
        ],
        value='1y'
    ),
    
    dcc.Graph(id='stock-chart'),
    html.Div(id='kpi-container')
])

@app.callback(
    Output('stock-chart', 'figure'),
    [Input('stock-dropdown', 'value'),
     Input('timeframe-radio', 'value')]
)
def update_chart(stock, timeframe):
    if timeframe in ['1d', '1w']:
        table_name = f"{stock}_minute"
    elif timeframe in ['1m', '1y', 'ytd']:
        table_name = f"{stock}_hourly"
    else:
        table_name = f"{stock}_daily"
    
    df = pd.read_sql_table(table_name, engine)
    
    # Ensure the index is a datetime object
    if 'Datetime' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        df.set_index('Datetime', inplace=True)
    elif 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
    
    end_date = datetime.now()
    if timeframe == '1d':
        start_date = end_date - timedelta(days=1)
    elif timeframe == '1w':
        start_date = end_date - timedelta(days=7)
    elif timeframe == '1m':
        start_date = end_date - timedelta(days=30)
    elif timeframe == '1y':
        start_date = end_date - timedelta(days=365)
    elif timeframe == 'ytd':
        start_date = datetime(end_date.year, 1, 1)
    elif timeframe == '5y':
        start_date = end_date - timedelta(days=5*365)
    elif timeframe == 'max':
        start_date = df.index.min()
    
    # Ensure start_date and end_date are tz-aware if df.index is tz-aware
    if df.index.tz is not None:
        start_date = pd.Timestamp(start_date).tz_convert(df.index.tz) if start_date.tzinfo else pd.Timestamp(start_date).tz_localize(df.index.tz)
        end_date = pd.Timestamp(end_date).tz_convert(df.index.tz) if end_date.tzinfo else pd.Timestamp(end_date).tz_localize(df.index.tz)
    
    df = df[(df.index >= start_date) & (df.index <= end_date)]
    
    # Calculate 200-day moving average
    df['200day_MA'] = df['Open'].rolling(window=200).mean()
    
    figure = {
        'data': [
            go.Scatter(
                x=df.index,
                y=df['Open'],
                mode='lines',
                name=stock
            ),
            go.Scatter(
                x=df.index,
                y=df['200day_MA'],
                mode='lines',
                name='200-Day MA'
            )
        ],
        'layout': {
            'title': f'{stock.upper()} Stock Prices ({timeframe})'
        }
    }
    return figure

@app.callback(
    Output('kpi-container', 'children'),
    [Input('stock-dropdown', 'value')]
)
def update_kpis(stock):
    table_name = f"{stock}_daily"
    df = pd.read_sql_table(table_name, engine)
    
    # Ensure the index is a datetime object
    if 'Datetime' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        df.set_index('Datetime', inplace=True)
    elif 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
    
    latest_data = df.iloc[-1]
    
    current_price = latest_data['Open']
    high_52w = df['High'].rolling(window=252, min_periods=1).max().iloc[-1]  # 252 trading days in a year
    low_52w = df['Low'].rolling(window=252, min_periods=1).min().iloc[-1]
    all_time_high = df['High'].max()
    percentage_to_ath = ((current_price - all_time_high) / all_time_high) * 100

    roll_max = df['Open'].cummax()
    drawdown = df['Open'] / roll_max - 1
    max_drawdown = drawdown.min() * 100
    end_date = drawdown.idxmin()
    start_date = df.loc[:end_date, 'Open'].idxmax()
    drawdown_period = f"{start_date.date()} to {end_date.date()}"

    kpis = [
        html.Div(f"Latest Open: ${current_price:.2f}"),
        html.Div(f"52-Week High: ${high_52w:.2f}"),
        html.Div(f"52-Week Low: ${low_52w:.2f}"),
        html.Div(f"All-Time High: ${all_time_high:.2f}"),
        html.Div(f"Percentage to ATH: {percentage_to_ath:.2f}%"),
        html.Div(f"Maximum Drawdown: {max_drawdown:.2f}%"),
        html.Div(f"Drawdown Period: {drawdown_period}")
    ]
    return kpis

if __name__ == "__main__":
    app.run_server(host='0.0.0.0', port=8050, debug=True)