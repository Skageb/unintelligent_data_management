
import requests
import dash_bootstrap_components as dbc
from pymongo import MongoClient

import dash
from dash import html, dcc, callback, Input, Output, State, dash_table, clientside_callback, ctx
import mysql.connector
import pandas as pd
import pycountry
import plotly.express as px
import plotly.graph_objects as go
import requests
import datetime


dash.register_page(__name__, path='/mongo_db')





# Function for fetching data from database
def fetch_data_from_api():
    response = requests.get("http://localhost:5001/api/mongo_data")
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
        dcc.Store(id='mongo-df', data=df_init.to_dict('records')),
        dcc.Graph(id='mongo-globe-graph'),
        html.H1("Find a Scoop"),
        html.Article('Use this tool to find a news story on an attack that is unique based on the selected category.'),
        dbc.Row(children=[
            dbc.Col(dcc.Dropdown(placeholder='Select Category', id='mongo-category-input')),
            dbc.Col(dbc.Button('Find Attack on Category', id='mongo-new-attack-button')),
            dbc.Col(dbc.Button('Generate Full Report', id='mongo-generate-report-button'))
        ]
        ),
        dbc.Row(children=[
            dbc.Col(dcc.RadioItems(id='mongo-scoop-search-option'), id='mongo-scoop-search-option-col')
        ]),
        html.Div(id='mongo-attack-report'),
        html.H1("Terrorism Database"),
        # Display the table
        
        html.H1('MongoDB Data Landing Page'),
        dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in df_init.columns],
            data=df_init.to_dict('records'),
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
        )

    ])
])

@callback(
    Output('mongo-category-input', 'options'),
    Input('mongo-df', 'data')
)
def update_category_options(df_dict):
    df = pd.DataFrame(df_dict)
    return list(df.columns)

@callback(
    Output('mongo-globe-graph', 'figure'),
    Input('mongo-df', 'data')
)
def rotate_globe(df_dict):
    df = pd.DataFrame(df_dict)
    return create_globe_plot(df)


@callback(
    Output('mongo-scoop-search-option-col', 'children'),
    Input('mongo-category-input', 'value'),
    State('mongo-df', 'data')
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
        id="mongo-scoop-search-option",
        options=options,
        value=0,
        inline=True
    )]

@callback(
    Output('mongo-attack-report', 'children'),
    State('mongo-df', 'data'),
    State('mongo-category-input', 'value'),
    State('mongo-scoop-search-option', 'value'),
    Input('mongo-generate-report-button', 'n_clicks'),
    Input('mongo-new-attack-button', 'n_clicks')
)
def generate_report_button_response(df_dict, category, search_option, full_report_n_clicks, search_n_clicks):
    df = pd.DataFrame(df_dict)
    if ctx.triggered_id == 'mongo-generate-report-button':
        n_clicks = full_report_n_clicks
        report_format = 'full'
    elif ctx.triggered_id == 'mongo-new-attack-button':
        n_clicks = search_n_clicks
        report_format = 'short'

    else:
        return dash.no_update
    if n_clicks is None:
        return dash.no_update
    if n_clicks < 1:
        return dash.no_update
    
    #Get most frequent or least frequent value:
    if df.dtypes[category] == 'object':
        value_counts = df[category].value_counts().sort_index().reset_index()
        value_counts.columns = ['value', 'count']
        sorted_counts = value_counts.sort_values('count', ascending=search_option)
        category_value = sorted_counts.iloc[(n_clicks-1)%len(sorted_counts)]['value']
        if report_format == 'short':
            return [html.H5(f'Attack found from category {category}, value: {category_value}')]
        elif report_format == 'full':
            result_df = df.loc[df[category] == category_value]
            row = result_df.sample(n=1).iloc[0]
            return create_HTML_report(row)
        
    
    #Get highest or lowest value
    elif df.dtypes[category] == 'int64':
        sorted_df = df.sort_values(category, ascending=search_option)
        category_value = sorted_df.iloc[(n_clicks-1)%len(sorted_df)][category]
        if report_format =='short':
            return [html.H5(f'Attack found from category {category}, value: {category_value}')]
        elif report_format == 'full':
            result_df = df.loc[df[category] == category_value]
            row = result_df.sample(n=1).iloc[0]
            return create_HTML_report(row)

def create_HTML_report(row):
    
    if row['city'] == 'Unknown' and row['country_txt'] != 'Unknown':
        headline = f'Terror report on {row['attacktype_txt']} incident in {row['country_txt']}'
    else:
        headline = f'Terror report on {row['attacktype_txt']} incident in {row['city']}, {row['country_txt']}'

    if row['attacktype_txt'] != 'Unknown':
        headline.replace('Unknown ', '')

    import time
    date =  pretty_date(row['year'], row['month'], row['day'])

    children_object = [
        html.H1(headline),
        html.H5(f'Date of Attack: {date}')
    ]
    body = f''
    if row['ransom']:
        body += f'A ransom of {row['ransom_demanded']} was demanded by the attacker'
        if row['ransom_paid'] != 0:
            body += f', where {row['ransom_paid']} was paid. '
        else:
            body += f', but not paid. '
        
    if row['motive'] != 'nan':
        body += f"{row['motive']} "
    else:
        body += f"The motive of this attack is not known. "

    if row['attacker_group'] != 'Unknown':
        body += f'It was revealed that the {row["attacker_group"]} is behind the attack. '
    damage_str = ''
    if row['fatalities'] > 0:
        damage_str += f'Further, {row["fatalities"]} has been reported killed in the attack'
        if row['wounded'] > 0: 
            damage_str += f' with another {row['wounded']} wounded'
        damage_str += '. '
    else:
        if row['wounded'] > 0: 
            damage_str += f'Further it has been reported that {row['wounded']} were wounded in the attack, but nobody was killed. '
        else:
            damage_str += f'Further it has been reported that nobody were killed or wounded in the attack. '
    body += damage_str

    if row['weapon_type_txt'] != 'Unknown':
        body += f'The attack was performed with the use of {row["weapon_type_txt"]}. '
    
    children_object.append(html.Div(body))
    return children_object
    
@callback(
    Output('mongo-new-attack-button', 'n_clicks'),
    State('mongo-new-attack-button', 'n_clicks'),
    Input('mongo-category-input', 'value'),
    Input('mongo-scoop-search-option', 'value'), prevent_initial_callback=True
)
def new_search_filter_button_reset(n_clicks, category, search_option):
    if n_clicks is None:
        return dash.no_update
    elif n_clicks < 1:
        return dash.no_update
    return 0


def pretty_date(year, month, day):
    import datetime


    date_obj = datetime.date(year, month, day)
    
        
    form = "%dth of %B, %Y"
    if str(day)[-1] == '1':
        form = "%dst of %B, %Y"
    elif str(day)[-1] == '2':
        form = "%dnd of %B, %Y"
    if str(day)[0] == '0':
        form = form[1:]

    formatted_date = date_obj.strftime(form)  # e.g. '24th of December'

    return formatted_date

