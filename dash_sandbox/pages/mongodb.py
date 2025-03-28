import dash
from dash import html, dcc, callback, Input, Output, dash_table
import requests
import dash_bootstrap_components as dbc
from pymongo import MongoClient

dash.register_page(__name__, path='/mongo_db')



def api_fetch_mongo_data():
    try:
        response = requests.get("http://localhost:5001/api/mongo_data")
        data = response.json()
        if data:
            columns = [{"name": key, "id": key} for key in data[0].keys()]
        else:
            columns = []
        return data, columns
    except Exception as e:
        print(f"Error fetching MongoDB data: {e}")
        return [], []



data, columns = api_fetch_mongo_data()
# Lazy-loaded layout
layout =html.Div([
        html.H1('MongoDB Data Landing Page'),
        dash_table.DataTable(
            data=data,
            columns=columns,
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
        )
    ])

