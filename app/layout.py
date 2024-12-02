from dash import dcc, html

# Read the list of stock tickers from the file
with open('stocks.txt', 'r') as file:
    stocks = file.read().splitlines()

# Read the list of starlist tickers from the file
with open('starlist.txt', 'r') as file:
    starlist_stocks = file.read().splitlines()

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

star_list_layout = html.Div([
    html.H1('Star-List', style={'color': 'black'}),
    dcc.Link(html.Button('Go to Dashboard', id='dashboard-button'), href='/'),
    html.Button('Refresh Starlist-Data', id='refresh-button', n_clicks=0),
    html.Hr(style={'borderWidth': "0.5vh", "width": "100%", "borderColor": "#F3DE8A", "opacity": "unset"}),
    html.Table(id='starlist-table', style={'border-collapse': 'collapse', 'width': '100%', 'color': 'black'}),
    html.Hr(style={'borderWidth': "0.5vh", "width": "100%", "borderColor": "#F3DE8A", "opacity": "unset"}),
    dcc.Dropdown(
        id='starlist-dropdown',
        options=[{'label': stock.split(';')[0], 'value': stock.split(';')[0].lower()} for stock in starlist_stocks],
        value=starlist_stocks[0].split(';')[0].lower(),
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