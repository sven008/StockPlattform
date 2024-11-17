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

# Fetch stock information from the database
df_info = pd.read_sql_table('information', engine)


# Define layout
app.layout = html.Div([
    html.H1('Dashboard for my portfolio'),
    html.Hr(style={'borderWidth': "0.5vh", "width": "100%", "borderColor": "#F3DE8A", "opacity": "unset"}),
    html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in df_info.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(df_info.iloc[i][col], style={'border': '1px solid black'}) for col in df_info.columns
            ]) for i in range(len(df_info))
        ])
    ], style={'border-collapse': 'collapse', 'width': '100%'}),
    html.Hr(style={'borderWidth': "0.5vh", "width": "100%", "borderColor": "#F3DE8A", "opacity": "unset"}),
    html.H2('Detailed information on my stocks'),
    dcc.Dropdown(
        id='stock-dropdown',
        options=[{'label': stock, 'value': stock.lower()} for stock in stocks],
        value=stocks[0].lower(),
        clearable=False
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
        value='5y'
    ),
    dcc.Graph(id='stock-chart', style={'height': '60vh'}),
    html.Div(style={'height': '20px'}),  # Add some space between the chart and the KPIs
    html.Div(id='kpi-container')
])

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
            'height': 600
        }
    }
    return figure

@app.callback(
    Output('kpi-container', 'children'),
    [Input('stock-dropdown', 'value')]
)
def update_kpis(stock):
    df = pd.read_sql_table(f"{stock}_daily", engine)
    df['Datetime'] = pd.to_datetime(df['Datetime'] if 'Datetime' in df.columns else df['Date'])
    df.set_index('Datetime', inplace=True)

    latest_data = df.iloc[-1]
    current_price = latest_data['Close']
    high_52w = df['High'].rolling(window=252, min_periods=1).max().iloc[-1]
    low_52w = df['Low'].rolling(window=252, min_periods=1).min().iloc[-1]
    all_time_high = df['High'].max()
    percentage_to_ath = ((current_price - all_time_high) / all_time_high) * 100

    roll_max = df['Close'].cummax()
    drawdown = df['Close'] / roll_max - 1
    max_drawdown = drawdown.min() * 100
    end_date = drawdown.idxmin()
    start_date = df.loc[:end_date, 'Close'].idxmax()
    drawdown_period = f"{start_date.date()} to {end_date.date()}"

    return [
        html.Div(f"Last Price: ${current_price:.2f}"),
        html.Div(f"52-Week High: ${high_52w:.2f}"),
        html.Div(f"52-Week Low: ${low_52w:.2f}"),
        html.Div(f"All-Time High: ${all_time_high:.2f}"),
        html.Div(f"Percentage to ATH: {percentage_to_ath:.2f}%"),
        html.Div(f"Maximum Drawdown: {max_drawdown:.2f}%"),
        html.Div(f"Drawdown Period: {drawdown_period}")
    ]

if __name__ == "__main__":
    app.run_server(host='0.0.0.0', port=8050, debug=True)