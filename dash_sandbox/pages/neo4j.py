import dash
from dash import html, dcc, callback, Input, Output, State, ctx
from neo4j import GraphDatabase
import requests
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px
import pycountry

from cache import cache

dash.register_page(__name__, path='/neo4j')


########## API CALLS ##########
#Get all unique terror groups.
@cache.memoize(timeout=3600)
def get_groups():
    response = requests.get("http://localhost:5001/api/neo4j/get_terror_groups")
    countries = response.json()

    return countries

#Get the 10 most active terror groups globally with each groups number of attacks
@cache.memoize(timeout=3600)
def get_top_10_groups():
    response = requests.get("http://localhost:5001/api/neo4j/top_10_groups")
    countries = response.json()

    return pd.DataFrame(countries)

#Get number of attacks and most active terror group by country.
@cache.memoize(timeout=3600)
def get_attack_stats_on_country():
    response = requests.get("http://localhost:5001/api/neo4j/get_attack_stats_on_country")
    country_attack_data = response.json()
    return pd.DataFrame(country_attack_data)

#Get number of attacks by country for spesified group
@cache.memoize(timeout=3600)
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
    
# Get the 5 most common attack types for spesified terror group with number of attacks for with each attack type
def get_group_attack_type(group_name: str) -> pd.DataFrame:
    url = 'http://localhost:5001/api/neo4j/group_top_attack_types'
    params = {'group_name': group_name}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error fetching stats for group '{group_name}': {e}")

# Get the 5 most common cities attacked for spesified terror group with number of attacks in each city.
def get_group_city(group_name: str) -> pd.DataFrame:
    '''For a group, return the number of attacks performed in each city'''
    url = 'http://localhost:5001/api/neo4j/group_city'
    params = {'group_name': group_name}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error fetching stats for group '{group_name}': {e}")


########## API CALLS END ###########



layout = dbc.Container(html.Div([
    dbc.Row([
    dbc.Col(html.H1('Number of Terror Attacks in Each Country', style={'textAlign': 'center', 'marginBottom': '20px'}, id='neo-globe-header')),
    dbc.Col([html.Label("Select Globe Statistic:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='neo4j-globe-dropdown',
                options=[
                    {'label': 'All Terror', 'value': 'global-activity'}
                ],
                value='global-activity'
            )], width=3)
    ]),
    dbc.Spinner(dcc.Graph(id='neo-globe-graph', config={
                                        'displayModeBar': False,
                                        'displaylogo': False
                                    }, style = {'marginBottom': '20px'}), color='primary'),
    html.H1('Terror Group Activity', style={'textAlign': 'center', 'marginBottom': '20px'}),
    html.Div('Select a terror group to get an overview of their activity.', style={'textAlign': 'center', 'marginBottom': '40px'}),
    dcc.Dropdown(
        id='group-dropdown',
        options=[],
        placeholder="Select a terror group",
        style={'width': '50%', 'margin': '0 auto'}
    ),
    dbc.Spinner(dbc.Row([
        dbc.Col(id='pie-fig-attack-type-col'),
        dbc.Col(id='pie-fig-city-col')
        ], style = {'marginBottom': '20px'}),color='primary'),
    html.H1('The 10 Most Active Terror Groups Globally', style={'textAlign': 'center', 'marginBottom': '20px'}),
    dbc.Spinner(dcc.Graph(id='top-group-graph', config={'displayModeBar': False},
        style={"backgroundColor": "rgba(0,0,0,0)", "height": "300px"}), color='primary'),
    
    

    html.Div(id='attack-list', style={'display': 'flex', 'flexDirection': 'column', 'gap': '10px'}),
])
)

@callback(
    Output('neo-globe-graph', 'figure'),
    Output('neo-globe-header', 'children'),
    State('group-dropdown', 'value'),
    Input('neo4j-globe-dropdown', 'value'),
    Input('url', 'pathname')
)
def update_globe_plot(group, globe_stat_type, pathname):
    if pathname != '/neo4j':
        return dash.no_update, dash.no_update
    
    if globe_stat_type == 'global-activity':
        df = get_attack_stats_on_country()

        fig = neo_globe_graph_total_attacks(df)

        title = 'Number of Terror Attacks in Each Country'

        return fig, title
    
    elif globe_stat_type == 'group-activity':
        df = get_attack_stats_for_group(group)

        fig = neo_globe_graph_group_attacks(df)

        title = html.Span([html.I(group), ' Activity in Each Country'])

        return fig, title
    else:
        return dash.no_update, dash.no_update


@callback(
    Output('neo4j-globe-dropdown', 'options'),
    Output('neo4j-globe-dropdown', 'value'),
    Output('pie-fig-attack-type-col', 'children'),
    Output('pie-fig-city-col', 'children'),
    Input('url', 'pathname'),
    Input('group-dropdown', 'value')
)
def neo_create_globe_graph(pathname, group):
    print(group)
    if (ctx.triggered_id == 'url' and pathname == '/neo4j')  or group is None:
        
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    elif ctx.triggered_id == 'group-dropdown':
        print('New group selected.')
        
        df_pie_city = get_group_city(group)
        df_pie_attack_type = get_group_attack_type(group)

        fig_city = create_pie_chart_child(df_pie_city, type='city', group=group)
        fig_attack_type = create_pie_chart_child(df_pie_attack_type, type='attack_type', group=group)

        options = [
                    {'label': 'All Terror', 'value': 'global-activity'},
                    {'label': 'Terror by Group', 'value': 'group-activity'}
                ]

        return options, 'group-activity', fig_attack_type, fig_city
    
    else:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update


def create_pie_chart_child(df: pd.DataFrame, type: str, group: str = "") -> dcc.Graph:
    if type == "city":
        label_col = "city"
        value_col = "attack_count"
        title = f"Top Cities - {group}"
        color_sequence = px.colors.sequential.Plasma[::2]
    elif type == "attack_type":
        label_col = "attack_type"
        value_col = "attack_count"
        title = f"Attack Types - {group}"
        color_sequence = px.colors.sequential.Plasma[1::2]
    else:
        raise ValueError("Invalid type. Expected 'city' or 'attack_type'.")

    # Take top 10 entries to keep it compact
    df_sorted = df.sort_values(by=value_col, ascending=False).head(10)

    fig = px.pie(
        df_sorted,
        names=label_col,
        values=value_col,
        title=title,
        color_discrete_sequence=color_sequence,
        hole=0.4  # donut style for modern look
    )

    fig.update_layout(
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title_x=0.5,
        font=dict(size=12),
        margin=dict(t=40, b=10, l=10, r=10),
        legend=dict(orientation="h", y=-0.1)
    )

    return dcc.Graph(
        figure=fig,
        config={'displayModeBar': False},
        style={"backgroundColor": "rgba(0,0,0,0)", "height": "300px"}
    )


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
    Input('url', 'pathname')
)
def add_group_dropdown_options(pathname):
    if pathname == '/neo4j':
        groups = get_groups()
        return groups
    else:
        return dash.no_update
    


@callback(
    Output('top-group-graph', 'figure'),
    Input('url', 'pathname')
)
def create_top_10_graph(pathname):
    if pathname == '/neo4j':
        group_df = get_top_10_groups()

        fig = px.bar(
            group_df,
            y='group_name',
            x='num_attacks',
            orientation='h',
            color='num_attacks',
            color_continuous_scale=px.colors.sequential.OrRd,
        )

        fig.update_layout(
            title_x=0.5,
            xaxis_title='Number of Attacks',
            yaxis_title=None,
            yaxis=dict(
                automargin=True,
                tickfont=dict(size=12)
            ),
            xaxis=dict(
                tickfont=dict(size=12)
            ),
            coloraxis_showscale=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=50, b=10),
            font=dict(size=14),
        )

        fig.update_traces(marker_line_width=1, marker_line_color='black')

        return fig
    return dash.no_update
    



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















