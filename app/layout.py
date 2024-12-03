from dash import dcc, html
import pandas as pd
import yfinance as yf

# Read the list of stock tickers and names from the file
stocks_data = pd.read_csv('stocks.txt', sep=';', header=None, names=['symbol', 'num_stocks', 'buy_in', 'stopp'])
stocks = stocks_data['symbol'].tolist()
stock_names = stocks_data['symbol'].apply(lambda x: yf.Ticker(x).info.get('shortName', x)).tolist()

# Read the list of starlist tickers and names from the file
starlist_data = pd.read_csv('starlist.txt', sep=';', usecols=[0], names=['symbol'])
starlist_stocks = starlist_data['symbol'].tolist()
starlist_names = starlist_data['symbol'].apply(lambda x: yf.Ticker(x).info.get('shortName', x)).tolist()

layout = html.Div([
    html.H1('Dashboard for my Portfolio', style={'color': 'black'}),
    dcc.Link(html.Button('Go to Star-List', id='star-list-button'), href='/star-list'),
    html.Button('Refresh Stock-Data', id='refresh-button', n_clicks=0),
    html.Hr(style={'borderWidth': "0.5vh", "width": "100%", "borderColor": "#F3DE8A", "opacity": "unset"}),
    html.Table(id='info-table', style={'border-collapse': 'collapse', 'width': '100%', 'color': 'black'}),
    html.Hr(style={'borderWidth': "0.5vh", "width": "100%", "borderColor": "#F3DE8A", "opacity": "unset"}),
    html.H2('Detailed information on my stocks', style={'color': 'black'}),
    dcc.Dropdown(
        id='stock-dropdown',
        options=[{'label': f"{name} ({symbol})", 'value': symbol.lower()} for name, symbol in zip(stock_names, stocks)],
        value=stocks[0].lower(),
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

star_list_layout = html.Div([
    html.H1('Star-List', style={'color': 'black'}),
    dcc.Link(html.Button('Go to Dashboard', id='dashboard-button'), href='/'),
    html.Button('Refresh Starlist-Data', id='refresh-button', n_clicks=0),
    html.Hr(style={'borderWidth': "0.5vh", "width": "100%", "borderColor": "#F3DE8A", "opacity": "unset"}),
    html.Table(id='starlist-table', style={'border-collapse': 'collapse', 'width': '100%', 'color': 'black'}),
    html.Hr(style={'borderWidth': "0.5vh", "width": "100%", "borderColor": "#F3DE8A", "opacity": "unset"}),
    dcc.Dropdown(
        id='starlist-dropdown',
        options=[{'label': f"{name} ({symbol})", 'value': symbol.lower()} for name, symbol in zip(starlist_names, starlist_stocks)],
        value=starlist_stocks[0].lower(),
        clearable=False,
        style={'color': 'black'}
    ),
    dcc.RadioItems(
        id='starlist-timeframe-radio',
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
    dcc.Graph(id='starlist-chart', style={'height': '60vh'}),
    html.Div(style={'height': '20px'})  # Add some space between the chart and the KPIs
], style={'backgroundColor': 'white', 'color': 'black'})