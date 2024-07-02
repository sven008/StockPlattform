import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
from sqlalchemy import create_engine

# Initialize Dash app
app = dash.Dash(__name__)

# Connect to PostgreSQL database
engine = create_engine('postgresql://postgres:postgres@db:5432/stockdata')

# Query stock data
df = pd.read_sql('SELECT * FROM microsoft_stock', engine)

# Create a line chart
fig = px.line(df, x='Date', y='Close', title='Microsoft Stock Prices Over the Last 10 Years')

# Define layout
app.layout = html.Div(children=[
    html.H1(children='Microsoft Stock Prices'),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050)