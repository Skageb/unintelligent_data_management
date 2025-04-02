import dash
from dash import html, dcc, callback, Input, Output
from neo4j import GraphDatabase
import requests
import pandas as pd

dash.register_page(__name__, path='/neo4j')




layout = html.Div([
    html.H1('New Terrorist Attacks by Country', style={'textAlign': 'center', 'marginBottom': '20px'}),
    html.Div('Select a country to see the terrorist attacks that happened there.', style={'textAlign': 'center', 'marginBottom': '40px'}),

    dcc.Dropdown(
        id='country-dropdown',
        options=[],
        placeholder="Select a country",
        style={'width': '50%', 'margin': '0 auto'}
    ),

    html.Div(id='attack-list', style={'display': 'flex', 'flexDirection': 'column', 'gap': '10px'}),
])
























########## API CALLS ##########
# Query Neo4j database to get countries
def get_countries():
    response = requests.get("http://localhost:5001/api/neo4j_countries")
    countries = response.json()

    return countries


# Query Neo4j to get attacks in selected country
def attack_on_country_call(country):
    response = requests.get("http://localhost:5001/api/neo4j_attacks")
    attacks = response.json()
    return attacks

########## API CALLS END ###########