import dash
from dash import html, dcc, callback, Input, Output
import numpy as np
import plotly.express as px

def sine(x):
    return np.sin(x)

def create_sine_graph():
    x = np.linspace(0, 10, 100)
    y = sine(x)
    return dcc.Graph(
        id='sine-graph',
        figure={
            'data': [
                {'x': x, 'y': y, 'type': 'line', 'name': 'Sine Wave'}
            ],
            'layout': {
                'title': 'Sine Wave',
                'xaxis': {'title': 'X-axis'},
                'yaxis': {'title': 'Y-axis'}
            }
        }
    )

dash.register_page(__name__, path='/my_sql')

def US_Graph():
    import plotly.graph_objects as go

    import pandas as pd
    df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/2011_us_ag_exports.csv')

    for col in df.columns:
        df[col] = df[col].astype(str)

    df['text'] = df['state'] + '<br>' + \
        'Beef ' + df['beef'] + ' Dairy ' + df['dairy'] + '<br>' + \
        'Fruits ' + df['total fruits'] + ' Veggies ' + df['total veggies'] + '<br>' + \
        'Wheat ' + df['wheat'] + ' Corn ' + df['corn']

    fig = go.Figure(data=go.Choropleth(
        locations=df['code'],
        z=df['total exports'].astype(float),
        locationmode='USA-states',
        colorscale='Reds',
        autocolorscale=False,
        text=df['text'], # hover text
        marker_line_color='white', # line markers between states
        colorbar=dict(
            title=dict(
                text="Millions USD"
                )
        )
    ))

    fig.update_layout(
        title_text='2011 US Agriculture Exports by State<br>(Hover for breakdown)',
        geo = dict(
            scope='usa',
            projection=go.layout.geo.Projection(type = 'albers usa'),
            showlakes=True, # lakes
            lakecolor='rgb(255, 255, 255)'),
    )
    return dcc.Graph(id='US_Graph', figure=fig, style={'width': '100%', 'height': '100vh'})


layout = html.Div([
    html.H1('This is our MySQL landing page, the app is running on MySQL backend'),
    html.Div('This is our MySQL page content.'),
    create_sine_graph(),
    US_Graph()
])  
