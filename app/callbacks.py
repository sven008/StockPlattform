from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import subprocess
from dash import html
from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv
from pytz import UTC

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
        end_date = pd.Timestamp(end_date).tz_localize(df.index.tz) if end_date.tzinfo is None else end_date.tz_convert(df.index.tz)

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

def update_portfolio_chart(n_clicks, engine):
    # Fetch the portfolio value data from the database
    df_portfolio_value = pd.read_sql_table('portfolio_value', engine)

    # Get the current year
    current_year = datetime.now().year

    # Filter for entries from the current year
    current_year_data = df_portfolio_value[df_portfolio_value['Date'].dt.year == current_year]

    # Find the first non-null 'Total Value' entry for the current year
    ytd_value = current_year_data.loc[current_year_data['Total Value'].first_valid_index(), 'Total Value'] if not current_year_data.empty else None

    # Get the current value (last entry)
    current_value = df_portfolio_value['Total Value'].iloc[-1]

    # Calculate the Year-to-Date (YTD) performance
    if ytd_value is not None and ytd_value > 0:
        ytd_performance = ((current_value - ytd_value) / ytd_value) * 100
    else:
        ytd_performance = 0  # Avoid division by zero or if no valid YTD value.

    # Create the figure for portfolio value chart
    figure = {
        'data': [
            go.Scatter(
                x=df_portfolio_value['Date'],
                y=df_portfolio_value['Total Value'],
                mode='lines',
                name='Total Portfolio Value'
            )
        ],
        'layout': {
            'title': 'Total Portfolio Value Over Time (Current Year)',
            'xaxis': {
                'title': 'Date',
                'rangeslider': {'visible': False},
                'tickmode': 'auto',
                'nticks': 20
            },
            'yaxis': {
                'title': 'Total Value',
                'type': 'linear'
            },
            'height': 600,
            'paper_bgcolor': 'white',
            'plot_bgcolor': 'white',
            'font': {'color': 'black'}
        }
    }

    # Add YTD performance text below the graph
    ytd_text = f"YTD Performance: {ytd_performance:.2f}%"
    
    # Display the YTD performance as a separate component below the graph
    ytd_performance_component = html.Div(
        children=[
            html.H4(ytd_text, style={'color': 'green', 'textAlign': 'center'})
        ]
    )

    return figure, ytd_performance_component

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
        [Output('portfolio-value-chart', 'figure'),
         Output('portfolio-ytd-performance', 'children')],  # Added this output for YTD performance
        [Input('refresh-button', 'n_clicks')]
    )
    def refresh_portfolio_chart(n_clicks):
        figure, ytd_performance_component = update_portfolio_chart(n_clicks, engine)
        return figure, ytd_performance_component