import dash
from dash import html, dcc, callback, Input, Output
from neo4j import GraphDatabase

dash.register_page(__name__, path='/neo4j')

uri = "neo4j://localhost:7687"
username = "neo4j"
password = "password"

driver = GraphDatabase.driver(uri, auth=(username, password))

# Query Neo4j to return 1 node
def query_neo4j():
    with driver.session() as session:
        query = """
        MATCH (n) 
        RETURN n LIMIT 1
        """
        result = session.run(query)
        return result.single()

layout = html.Div([
    html.H1('Neo4j Data Display'),
    html.Div('This page displays data fetched from Neo4j.'),

    html.H3('Recent Data'),
    html.Div(id='neo4j-data'),
    
    html.Button("Fetch Data", id="fetch-data-button", n_clicks=0),
])

@callback(
    Output('neo4j-data', 'children'),

    # Click button to fetch data
    Input('fetch-data-button', 'n_clicks')
)
def display_neo4j_data(n_clicks):
    if n_clicks > 0:
        data = query_neo4j()
        if not data:
            return "No data found."
        return f"Node: {data['n']}"
    return "Click the button to fetch data."

