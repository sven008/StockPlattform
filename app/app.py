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
        html.Tr([html.Th('Stock Name'), html.Td(id='stock-name')]),
        html.Tr([html.Th('Current Stock Price'), html.Td(id='current-price')]),
        html.Tr([html.Th('52-Week High'), html.Td(id='52w-high')]),
        html.Tr([html.Th('52-Week Low'), html.Td(id='52w-low')]),
        html.Tr([html.Th('Percentage to ATH'), html.Td(id='percentage-ath')]),
        html.Tr([html.Th('Maximum Drawdown'), html.Td(id='max-drawdown')]),
        html.Tr([html.Th('Drawdown Period'), html.Td(id='drawdown-period')])
    ], style={'border': '1px solid black', 'border-collapse': 'collapse', 'width': '50%', 'margin': 'auto'})
])

# Callback to update the graph and stock information based on the selected stock
@app.callback(
    [Output('stock-graph', 'figure'),
     Output('stock-name', 'children'),
     Output('current-price', 'children'),
     Output('52w-high', 'children'),
     Output('52w-low', 'children'),
     Output('percentage-ath', 'children'),
     Output('max-drawdown', 'children'),
     Output('drawdown-period', 'children')],
    [Input('stock-dropdown', 'value'),
     Input('stock-graph', 'relayoutData')]
)
def update_graph(selected_stock, relayoutData):
    df = pd.read_sql(f'SELECT * FROM {selected_stock}', engine)
    df['Date'] = pd.to_datetime(df['Date'])  # Ensure 'Date' is a datetime object
    df.set_index('Date', inplace=True)  # Set 'Date' as index for easier manipulation

    # Calculate the 200-day moving average
    df['200_day_MA'] = df['Close'].rolling(window=200).mean()

    # Default to the full date range
    filtered_df = df

    # Check if relayoutData is provided and contains 'xaxis.range'
    if relayoutData and 'xaxis.range[0]' in relayoutData and 'xaxis.range[1]' in relayoutData:
        x0 = pd.to_datetime(relayoutData['xaxis.range[0]'])
        x1 = pd.to_datetime(relayoutData['xaxis.range[1]'])
        filtered_df = df.loc[x0:x1]

    # Create the figure
    fig = go.Figure()

    # Add the candlestick chart with the filtered data
    fig.add_trace(go.Candlestick(x=filtered_df.index,
                                 open=filtered_df['Open'],
                                 high=filtered_df['High'],
                                 low=filtered_df['Low'],
                                 close=filtered_df['Close'],
                                 name='Candlestick'))

    # Add the 200-day moving average line
    fig.add_trace(go.Scatter(x=filtered_df.index, y=filtered_df['200_day_MA'], mode='lines', name='200-day MA'))

    # Update layout
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
            ),
            rangeslider=dict(visible=False)
        ),
        yaxis=dict(autorange=True),
        showlegend=True
    )

    # Adjust y-axis range based on filtered data
    y_min = filtered_df['Low'].min()
    y_max = filtered_df['High'].max()
    fig.update_yaxes(range=[y_min, y_max])

    # Calculate current stock price, 52-week high, 52-week low, all-time high, percentage to ATH, and maximum drawdown
    current_price = df['Close'].iloc[-1]
    high_52w = df['High'].rolling(window=252, min_periods=1).max().iloc[-1]  # 252 trading days in a year
    low_52w = df['Low'].rolling(window=252, min_periods=1).min().iloc[-1]
    all_time_high = df['High'].max()
    percentage_to_ath = ((current_price - all_time_high) / all_time_high) * 100

    # Calculate maximum drawdown and the drawdown period
    roll_max = df['Close'].cummax()
    drawdown = df['Close'] / roll_max - 1
    max_drawdown = drawdown.min() * 100
    end_date = drawdown.idxmin()
    start_date = df.loc[:end_date, 'Close'].idxmax()
    drawdown_period = f"{start_date.date()} to {end_date.date()}"

    return fig, selected_stock.upper(), f"${current_price:.2f}", f"${high_52w:.2f}", f"${low_52w:.2f}", f"{percentage_to_ath:.2f}%", f"{max_drawdown:.2f}%", drawdown_period

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
