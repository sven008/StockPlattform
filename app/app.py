import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import subprocess
from layout import layout
from callbacks import register_callbacks

# Initialize Dash app
app = dash.Dash(__name__)

# Connect to PostgreSQL database
engine = create_engine('postgresql://postgres:postgres@db:5432/stockdata')

# Set layout
app.layout = layout

# Register callbacks
register_callbacks(app, engine)

if __name__ == "__main__":
    app.run_server(host='0.0.0.0', port=8050, debug=True)