from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import subprocess
from dash import html

def fetch_stock_info(engine):
    return pd.read_sql_table('information', engine)

def register_callbacks(app, engine):
    @app.callback(
        Output('info-table', 'children'),
        [Input('refresh-button', 'n_clicks')]
    )
    def update_info_table(n_clicks):
        if n_clicks > 0:
            # Run the extract_and_load.py script
            subprocess.run(["python", "extract_and_load_portfolio.py"], check=True)
        
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
            end_date = pd.Timestamp(end_date).tz_localize(df.index.tz) if end_date.tzinfo is None else end_date.tz.convert(df.index.tz)

        df_filtered = df[(df.index >= start_date) & (df.index <= end_date)]

        # Find high and low points
        high_point = df_filtered['High'].idxmax()
        low_point = df_filtered['Low'].idxmin()

        # Fetch stopp value from the database
        df_info = fetch_stock_info(engine)
        stopp_value = df_info[df_info['Symbol'].str.lower() == stock]['Stopp'].values[0]

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
                ),
                go.Scatter(
                    x=df_filtered.index,
                    y=[stopp_value] * len(df_filtered.index),
                    mode='lines',
                    line=dict(color='orange', dash='dash'),
                    name='Stopp'
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