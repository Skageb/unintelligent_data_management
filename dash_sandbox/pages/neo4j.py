import dash
from dash import html, dcc, callback, Input, Output
from neo4j import GraphDatabase
import requests
import pandas as pd

dash.register_page(__name__, path='/old/neo4j')

'''uri = "neo4j://localhost:7687"
username = "neo4j"
password = "password"

driver = GraphDatabase.driver(uri, auth=(username, password))
'''
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

# HTML layout
layout = html.Div([
    html.H1('Terrorist Attacks by Country', style={'textAlign': 'center', 'marginBottom': '20px'}),
    html.Div('Select a country to see the terrorist attacks that happened there.', style={'textAlign': 'center', 'marginBottom': '40px'}),

    dcc.Dropdown(
        id='country-dropdown',
        options=[],
        placeholder="Select a country",
        style={'width': '50%', 'margin': '0 auto'}
    ),

    html.Div(id='attack-list', style={'display': 'flex', 'flexDirection': 'column', 'gap': '10px'}),
])

# Populate dropdown menu with countries from neo4j database
@callback(
    Output('country-dropdown', 'options'),
    Input('country-dropdown', 'id')
)
def populate_country_dropdown(_):
    countries = get_countries()
    return [{'label': country, 'value': country} for country in countries]

# Update the attack list from selected country
@callback(
    Output('attack-list', 'children'),
    Input('country-dropdown', 'value')
)
def display_attacks_by_country(selected_country):
    if not selected_country:
        return html.Div("Please select a country from the dropdown.", style={'textAlign': 'center'})

    # Fetch attacks from selected country
    attacks = attack_on_country_call(selected_country)
    
    if not attacks:
        return html.Div("No attacks found for this country.", style={'textAlign': 'center'})

    # Create a list of divs to display the attacks
    attack_divs = [html.H4(f"{selected_country} had {len(attacks)} attacks:")]
    for attack in attacks:
        attack_divs.append(html.Div([
            #html.H4(f"Attack ID: {attack['attack_id']}", style={'marginBottom': '5px'}),
            html.Div(f"Year: {attack['year']}", style={'marginBottom': '5px'}),
            html.Div(f"City: {attack['city']}", style={'marginBottom': '5px'}),
            html.Div(f"Attack Type: {attack['attack_type']}", style={'marginBottom': '10px'}),
            html.Hr()
        ], style={'backgroundColor': '#f9f9f9', 'padding': '10px', 'borderRadius': '8px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'}))

    return attack_divs
