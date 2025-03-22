import dash
from dash import html, dcc, callback, Input, Output
from neo4j import GraphDatabase

dash.register_page(__name__, path='/neo4j')

uri = "neo4j://localhost:7687"
username = "neo4j"
password = "password"

driver = GraphDatabase.driver(uri, auth=(username, password))

# Query Neo4j database to get countries
def get_countries():
    with driver.session() as session:
        query = """
        MATCH (c:Country)
        RETURN c.name AS country
        """
        result = session.run(query)
        countries = [record['country'] for record in result]
        return countries

# Query Neo4j to get attacks in selected country
def query_neo4j(country):
    with driver.session() as session:
        query = """
        MATCH (a:Incident)-[:HAPPENED_IN]->(c:Country)
        WHERE c.name = $country
        RETURN a.id AS attack_id, a.year AS year, a.city AS city, a.attack_type AS attack_type
        ORDER BY a.year DESC
        """
        result = session.run(query, country=country)
        attacks = []
        for record in result:
            attacks.append({
                'attack_id': record['attack_id'],
                'year': record['year'],
                'city': record['city'],
                'attack_type': record['attack_type']
            })
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
    attacks = query_neo4j(selected_country)
    
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
