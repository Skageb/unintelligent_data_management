import dash
from dash import html, dcc, callback, Input, Output

dash.register_page(__name__, path='/mongo_db')

layout = html.Div([
    html.H1('This is our MongoDB landing page, the app is running on mongoDB backend'),
    html.Div('This is our MongoDB page content.'),
])