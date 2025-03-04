import dash
from dash import html, dcc, callback, Input, Output

dash.register_page(__name__, path='/neo4j')

layout = html.Div([
    html.H1('This is our Neo4j landing page, the app is running on Neo4j backend'),
    html.Div('This is our Neo4j page content.'),
])