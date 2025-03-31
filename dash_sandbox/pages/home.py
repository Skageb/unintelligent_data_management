import dash
from dash import html, Output, Input

dash.register_page(__name__, path='/')

layout = html.Div([
    html.H1('This is our Home page'),
    html.Div('This is our Home page content.'),
    html.Button('Insert data', id='insert-button', n_clicks=0),
    html.Div(id='output-div')
])

@dash.callback(
    Output('output-div', 'children'),
    Input('insert-button', 'n_clicks'),
)
def insert_data(n_clicks):
    if n_clicks > 0:
        return f'Prank btn. Number of times pranked: {n_clicks}'
    return ""