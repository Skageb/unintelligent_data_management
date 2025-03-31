import dash
from dash import html, dcc, callback, Input, Output, State, dash_table, clientside_callback, ctx
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

    # Get list of countries already in the DataFrame
    present_countries = country_counts['country'].tolist()

    # Prepare rows for missing countries
    missing_rows = []

    for c in pycountry.countries:
        if c.name not in present_countries:
            missing_rows.append({
                'country': c.name,
                'count': 0,
                'iso_code': c.alpha_3
            })

    # Append missing countries
    if missing_rows:
        country_counts = pd.concat([country_counts, pd.DataFrame(missing_rows)], ignore_index=True)

    # Optional: sort alphabetically or by iso_code
    country_counts = country_counts.sort_values(by='country').reset_index(drop=True)

    fig = px.choropleth(country_counts, locations='iso_code', color='count', hover_data=['country', 'count'], color_continuous_scale = ["#fff5eb", "#fd8d3c", "#f03b20", "#bd0026", "#800026"])

    fig.update_geos(projection_type='orthographic')

    

    fig.update_layout(
        margin=dict(l=5, r=5, t=5, b=5),
        
    )

    # Show the figure
    return fig

df_init = fetch_data_from_api()

layout = dbc.Container([html.Div([
        
        html.H1("Number of Terror Attacks in Each Country"),
        dcc.Store(id='df', data=df_init.to_dict('records')),
        dcc.Graph(id='globe-graph'),
        html.H1("Find a Scoop"),
        html.Article('Use this tool to find a news story on an attack that is unique based on the selected category.'),
        dbc.Row(children=[
            dbc.Col(dcc.Dropdown(placeholder='Select Category', id='category-input')),
            dbc.Col(dbc.Button('Find Attack on Category', id='new-attack-button')),
            dbc.Col(dbc.Button('Generate Full Report', id='generate-report-button'))
        ]
        ),
        dbc.Row(children=[
            dbc.Col(dcc.RadioItems(id='scoop-search-option'), id='scoop-search-option-col')
        ]),
        html.Div(id='attack-report'),
        html.H1("Terrorism Database"),
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
    Output('category-input', 'options'),
    Input('df', 'data')
)
def update_category_options(df_dict):
    df = pd.DataFrame(df_dict)
    return list(df.columns)

@callback(
    Output('globe-graph', 'figure'),
    Input('df', 'data')
)
def rotate_globe(df_dict):
    df = pd.DataFrame(df_dict)
    return create_globe_plot(df)


@callback(
    Output('scoop-search-option-col', 'children'),
    Input('category-input', 'value'),
    State('df', 'data')
)
def category_input_response(category, df_dict):
    df = pd.DataFrame(df_dict)
    if category not in df.columns:
        return dash.no_update
    else:
        if df.dtypes[category] == 'int64':
            options = [{'label':'High Value','value':0},{'label':'Low Value','value':1}]
        elif df.dtypes[category] == 'object':
            options = [{'label':'Frequent Value','value':0},{'label':'Rare Value','value':1}]
        return [html.Div('Value type from category:'), dbc.RadioItems(
        id="scoop-search-option",
        options=options,
        value=0,
        inline=True
    )]

@callback(
    Output('attack-report', 'children'),
    State('df', 'data'),
    State('category-input', 'value'),
    State('scoop-search-option', 'value'),
    Input('generate-report-button', 'n_clicks'),
    Input('new-attack-button', 'n_clicks')
)
def generate_report_button_response(df_dict, category, search_option, full_report_n_clicks, search_n_clicks):
    df = pd.DataFrame(df_dict)
    if ctx.triggered_id == 'generate-report-button':
        n_clicks = full_report_n_clicks
        report_format = 'full'
    elif ctx.triggered_id == 'new-attack-button':
        n_clicks = search_n_clicks
        report_format = 'short'

    else:
        return dash.no_update
    if n_clicks is None:
        return dash.no_update
    
    #Get most frequent or least frequent value:
    if df.dtypes[category] == 'object':
        value_counts = df[category].value_counts().sort_index().reset_index()
        value_counts.columns = ['value', 'count']
        sorted_counts = value_counts.sort_values('count', ascending=search_option)
        return [html.H5(f'Attack found from category {category}, value: {sorted_counts.iloc[0]['value']}')]

    
        
    
    #Get highest or lowest value
    elif df.dtypes[category] == 'int64':
        sorted_df = df.sort_values(category, ascending=search_option)
        return [html.H5(f'Attack found from category {category}, value: {sorted_df.iloc[0][category]}')]


    
    
    
    



    