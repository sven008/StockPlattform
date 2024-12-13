import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import subprocess
from layout import layout, star_list_layout
from callbacks import register_callbacks
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the database URL from environment variables
DATABASE_URL = os.getenv('DATABASE_URL')

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Connect to PostgreSQL database
engine = create_engine(DATABASE_URL)

# Set layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Register callbacks
register_callbacks(app, engine)

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/star-list':
        return star_list_layout
    else:
        return layout

if __name__ == "__main__":
    app.run_server(host='0.0.0.0', port=8050, debug=True)