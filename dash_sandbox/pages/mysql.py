import dash
from dash import html, dcc, callback, Input, Output, State, dash_table, clientside_callback
import dash_bootstrap_components as dbc
import mysql.connector
import pandas as pd
import pycountry
import plotly.express as px
import plotly.graph_objects as go
import requests

dash.register_page(__name__, path='/my_sql')


# Function for fetching data from database
def fetch_data_from_api():
    response = requests.get("http://localhost:5001/api/mysql_data")
    data = response.json()
    return pd.DataFrame(data)


def country_to_iso(name):
        try:
            return pycountry.countries.lookup(name).alpha_3  # or use .alpha_2 for 2-letter codes
        except LookupError:
            return 2

def create_globe_plot(df):
    country_counts = df['country_txt'].value_counts().sort_index().reset_index()
    country_counts.columns = ['country', 'count']
    country_counts['iso_code'] = country_counts['country'].apply(country_to_iso)

    fig = px.choropleth(country_counts, locations='iso_code', color='count', hover_data=['country', 'count'])

    fig.update_geos(projection_type='orthographic')

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
    )

    # Show the figure
    return fig

df_init = fetch_data_from_api()

layout = dbc.Container([html.Div([
        html.H1("Terrorism Database"),

        dcc.Store(id='df', data=df_init.to_dict('records')),
        dcc.Graph(id='globe-graph'),

        # Display the table
        dash_table.DataTable(
            id='terrorism-table',
            columns=[{"name": col, "id": col} for col in df_init.columns],
            data=df_init.to_dict('records'),
            page_size=25,
            style_table={'height': '400px', 'overflowY': 'auto'}
        ),

    ])
])

@callback(
    Output('globe-graph', 'figure'),
    Input('df', 'data'),
)
def rotate_globe(df_dict):
    df = pd.DataFrame(df_dict)
    return create_globe_plot(df)