import dash
from dash import html, Output, Input
#from data_producer import producer_f

dash.register_page(__name__, path='/')

data_pipe = 'Data'
broker_addr = '127.0.0.1:29092'
insert = 'False'

layout = html.Div([
    html.H1('This is our Home page'),
    html.Div('This is our Home page content.'),
    html.Button('Insert data', id='insert-button', n_clicks=0),
    html.Div(id='output-div')
])

'''@dash.callback(
    Output('output-div', 'children'),
    Input('insert-button', 'n_clicks'),
)
def insert_data(n_clicks):
    if n_clicks > 0:
        insert = 'True'
        producer_f(data_pipe, broker_addr, insert)
        return f'Data inserted'
    return ""'''