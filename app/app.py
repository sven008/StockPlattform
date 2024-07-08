# app/app.py

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import create_engine

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
    
    dcc.Graph(
        id='stock-graph'
    ),

    html.Table([
        html.Tr([html.Th('Stock Name'), html.Th('Current Stock Price')]),
        html.Tr([html.Td(id='stock-name'), html.Td(id='current-price')])
    ])
])

# Callback to update the graph and stock information based on the selected stock
@app.callback(
    [Output('stock-graph', 'figure'),
     Output('stock-name', 'children'),
     Output('current-price', 'children')],
    [Input('stock-dropdown', 'value')]
)
def update_graph(selected_stock):
    df = pd.read_sql(f'SELECT * FROM {selected_stock}', engine)
    
    # Calculate the 200-day moving average
    df['200_day_MA'] = df['Close'].rolling(window=200).mean()

    # Create the figure
    fig = go.Figure()

    # Add the closing price line
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], mode='lines', name='Close'))

    # Add the 200-day moving average line
    fig.add_trace(go.Scatter(x=df['Date'], y=df['200_day_MA'], mode='lines', name='200-day MA'))

    # Update layout to automatically adjust axes
    fig.update_layout(
        title=f'{selected_stock.upper()} Stock Prices',
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        ),
        yaxis=dict(autorange=True),
        showlegend=True
    )

    # Get current stock price
    current_price = df['Close'].iloc[-1]

    return fig, selected_stock.upper(), f"${current_price:.2f}"

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050)
