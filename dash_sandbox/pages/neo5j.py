import dash
from dash import html, dcc, callback, Input, Output, ctx
from neo4j import GraphDatabase
import requests
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px
import pycountry

dash.register_page(__name__, path='/neo4j')


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

def get_groups():
    response = requests.get("http://localhost:5001/api/neo4j/get_terror_groups")
    countries = response.json()

    return countries

def get_top_10_groups():
    response = requests.get("http://localhost:5001/api/neo4j/top_10_groups")
    countries = response.json()

    return pd.DataFrame(countries)

def get_attack_stats_on_country():
    response = requests.get("http://localhost:5001/api/neo4j/get_attack_stats_on_country")
    country_attack_data = response.json()
    return pd.DataFrame(country_attack_data)

def get_attack_stats_for_group(group_name: str) -> pd.DataFrame:
    url = "http://localhost:5001/api/neo4j/group_attacks_by_country"
    params = {"group_name": group_name}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error fetching stats for group '{group_name}': {e}")
        return pd.DataFrame(columns=["country", "attack_count"])

########## API CALLS END ###########
# Query Neo4j database to get countries

    

layout = html.Div([
    html.H1('Number of Terror Attacks in Each Country', style={'textAlign': 'center', 'marginBottom': '20px'}, id='neo-globe-header'),
    dcc.Store(id='neo-globe-df', data=get_attack_stats_on_country().to_dict('records')),
    dcc.Graph(id='neo-globe-graph', config={
                                        'displayModeBar': False,
                                        'displaylogo': False
                                    }),
    dcc.Graph(id='top-group-graph'),
    html.H1('Terror Group Activity', style={'textAlign': 'center', 'marginBottom': '20px'}),
    html.Div('Select a terror group to get an overview of their activity.', style={'textAlign': 'center', 'marginBottom': '40px'}),
    dcc.Store(id = 'terror-group-list', data=get_groups()),

    dcc.Dropdown(
        id='group-dropdown',
        options=[],
        placeholder="Select a terror group",
        style={'width': '50%', 'margin': '0 auto'}
    ),

    html.Div(id='attack-list', style={'display': 'flex', 'flexDirection': 'column', 'gap': '10px'}),
])



@callback(
    Output('neo-globe-graph', 'figure'),
    Output('neo-globe-header', 'children'),
    Input('neo-globe-df', 'data'),
    Input('group-dropdown', 'value')
)
def neo_create_globe_graph(df_dict, group):
    print(group)
    if ctx.triggered_id == 'neo-globe-df' or group is None:
        df = pd.DataFrame(df_dict)

        fig = neo_globe_graph_total_attacks(df)
        return fig, dash.no_update
    
    elif ctx.triggered_id == 'group-dropdown':
        print('New group selected.')
        
        df = get_attack_stats_for_group(group)
        print('Dataframe created')
        print(df.head())
        
        fig = neo_globe_graph_group_attacks(df)

        print('Returning dash update')

        return fig, f'{group} Activity in Each Country'
    
    else:
        print(f'Not updating, triggered by: {ctx.triggered_id}')
        return dash.no_update, dash.no_update


def neo_globe_graph_group_attacks(df):
    df['iso_code'] = df['country'].apply(country_to_iso)
            
    existing = set(df['country'])
    missing_rows = []

    for c in pycountry.countries:
        if c.name not in existing:
            missing_rows.append({
                'country': c.name,
                'attack_count': 0,
                'iso_code': c.alpha_3
            })

    if missing_rows:
        df = pd.concat([df, pd.DataFrame(missing_rows)], ignore_index=True)

    df_globe = df.sort_values(by='country').reset_index(drop=True)

    fig = px.choropleth(
        df_globe, 
        locations='iso_code',
        color='attack_count',
        hover_data=['country', 'attack_count'],
        color_continuous_scale=["#fff5eb", "#fd8d3c", "#f03b20", "#bd0026", "#800026"],
        labels={'total_attacks': 'Attacks by Group'}
    )

    fig.update_geos(projection_type='orthographic')

    fig.update_layout(
        margin=dict(l=5, r=5, t=5, b=5),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        coloraxis_colorbar_title='Attacks by Group'
    )

    return fig




@callback(
    Output('group-dropdown', 'options'),
    Input('terror-group-list', 'data')
)
def add_group_dropdown_options(terror_groups):
    return terror_groups


@callback(
    Output('top-group-graph', 'figure'),
    Input('terror-group-list', 'data')
)
def create_top_10_graph(df):
    group_df = get_top_10_groups()
    group_df = group_df.sort_values('num_attacks', ascending=False)
    fig = px.bar(group_df, y='group_name', x='num_attacks', orientation='h')

    return fig
    



def country_to_iso(name):
        try:
            return pycountry.countries.lookup(name).alpha_3  # or use .alpha_2 for 2-letter codes
        except LookupError:
            return 2


#def neo_globe_graph_total_attacks(df):
    

def neo_globe_graph_total_attacks(df):
    df['iso_code'] = df['country'].apply(country_to_iso)
            
    existing = set(df['country'])
    missing_rows = []

    for c in pycountry.countries:
        if c.name not in existing:
            missing_rows.append({
                'country': c.name,
                'most_active_group': None,
                'total_attacks': 0,
                'iso_code': c.alpha_3
            })

    if missing_rows:
        df = pd.concat([df, pd.DataFrame(missing_rows)], ignore_index=True)

    df_globe = df.sort_values(by='country').reset_index(drop=True)

    fig = px.choropleth(
        df_globe, 
        locations='iso_code',
        color='total_attacks',
        hover_data=['country', 'total_attacks', 'most_active_group'],
        color_continuous_scale=["#fff5eb", "#fd8d3c", "#f03b20", "#bd0026", "#800026"],
        labels={'total_attacks': 'Number of Attacks', 'most_active_group': 'Most active group'}
    )

    fig.update_geos(projection_type='orthographic')

    fig.update_layout(
        margin=dict(l=5, r=5, t=5, b=5),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        coloraxis_colorbar_title='Number of Attacks'
    )

    return fig















