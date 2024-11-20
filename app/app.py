import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import subprocess

# Initialize Dash app
app = dash.Dash(__name__)

# Connect to PostgreSQL database
engine = create_engine('postgresql://postgres:postgres@db:5432/stockdata')

# Read the list of stock tickers from the file
with open('stocks.txt', 'r') as file:
    stocks = file.read().splitlines()

# Fetch stock information from the database
def fetch_stock_info():
    return pd.read_sql_table('information', engine)

df_info = fetch_stock_info()

# Define layout
app.layout = html.Div([
    html.H1('Dashboard for my Portfolio', style={'color': 'black'}),
    html.Button('Refresh Data', id='refresh-button', n_clicks=0),
    html.Hr(style={'borderWidth': "0.5vh", "width": "100%", "borderColor": "#F3DE8A", "opacity": "unset"}),
    html.Table([
        html.Thead(
            html.Tr([html.Th(col, style={'border': '1px solid black', 'padding': '10px'}) for col in df_info.columns])
        ),
        html.Tbody(id='info-table-body')
    ], style={'border-collapse': 'collapse', 'width': '100%', 'color': 'black'}),
    html.Hr(style={'borderWidth': "0.5vh", "width": "100%", "borderColor": "#F3DE8A", "opacity": "unset"}),
    html.H2('Detailed information on my stocks', style={'color': 'black'}),
    dcc.Dropdown(
        id='stock-dropdown',
        options=[{'label': stock.split(';')[0], 'value': stock.split(';')[0].lower()} for stock in stocks],
        value=stocks[0].split(';')[0].lower(),
        clearable=False,
        style={'color': 'black'}
    ),
    dcc.RadioItems(
        id='timeframe-radio',
        options=[
            {'label': '1 Week', 'value': '1w'},
            {'label': '1 Month', 'value': '1m'},
            {'label': '1 Year', 'value': '1y'},
            {'label': 'YTD', 'value': 'ytd'},
            {'label': '5 Years', 'value': '5y'},
            {'label': 'Max', 'value': 'max'}
        ],
        value='5y',
        style={'color': 'black'}
    ),
    dcc.Graph(id='stock-chart', style={'height': '60vh'}),
    html.Div(style={'height': '20px'})  # Add some space between the chart and the KPIs
], style={'backgroundColor': 'white', 'color': 'black'})

@app.callback(
    Output('info-table-body', 'children'),
    [Input('refresh-button', 'n_clicks')]
)
def update_info_table(n_clicks):
    if n_clicks > 0:
        # Run the extract_and_load.py script
        subprocess.run(["python", "extract_and_load.py"], check=True)
    
    df_info = fetch_stock_info()

    rows = []
    for i in range(len(df_info)):
        row = [html.Td(df_info.iloc[i][col], style={'border': '1px solid black', 'padding': '10px'}) for col in df_info.columns]
        rows.append(html.Tr(row))

    return rows

@app.callback(
    Output('stock-chart', 'figure'),
    [Input('stock-dropdown', 'value'),
     Input('timeframe-radio', 'value')]
)
def update_chart(stock, timeframe):
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
        'max': df.index.min()
    }[timeframe]

    if df.index.tz is not None:
        start_date = pd.Timestamp(start_date).tz_localize(df.index.tz) if start_date.tzinfo is None else start_date.tz_convert(df.index.tz)
        end_date = pd.Timestamp(end_date).tz_localize(df.index.tz) if end_date.tzinfo is None else end_date.tz_convert(df.index.tz)

    df_filtered = df[(df.index >= start_date) & (df.index <= end_date)]

    # Find high and low points
    high_point = df_filtered['High'].idxmax()
    low_point = df_filtered['Low'].idxmin()

    figure = {
        'data': [
            go.Candlestick(
                x=df_filtered.index,
                open=df_filtered['Open'],
                high=df_filtered['High'],
                low=df_filtered['Low'],
                close=df_filtered['Close'],
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
        ],
        'layout': {
            'title': f'{stock.upper()} Stock Prices ({timeframe})',
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

if __name__ == "__main__":
    app.run_server(host='0.0.0.0', port=8050, debug=True)