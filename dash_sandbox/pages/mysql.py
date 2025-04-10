import dash
from dash import html, dcc, callback, Input, Output, State, dash_table, clientside_callback, ctx
import dash_bootstrap_components as dbc
import mysql.connector
import pandas as pd
import pycountry
import plotly.express as px
import plotly.graph_objects as go
import requests
import datetime

from cache import cache


dash.register_page(__name__, path='/my_sql')





############### API CALLS #################
@cache.memoize(timeout=3600)
def fetch_data_from_api():
    response = requests.get("http://localhost:5001/api/mysql_data")
    data = response.json()
    return pd.DataFrame(data)



@cache.memoize(timeout=3600)
def fetch_by_country_stats(stat_type='ransom_demanded'):
    '''stat_type options: ['ransom_demanded', 'ransom_paid', 'num_attacks'] '''
    url = "http://localhost:5001/api/mysql/by_country_data"
    params = {"stat_type": stat_type}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error fetching stats for group '{stat_type}': {e}")

@cache.memoize(timeout=3600)
def get_sql_cols():
    url = "http://localhost:5001/api/mysql/all_attributes"
    response = requests.get(url)
    data = response.json()

    return [row.get('COLUMN_NAME') for row in data if 'COLUMN_NAME' in row]


def get_report_cols_from_event_id_sql(event_id:int):
    url = 'http://localhost:5001/api/mysql/get_report_col_from_event_id'
    params = {"event_id": event_id}
    response = requests.get(url, params=params)

    response.raise_for_status()
    data = response.json()
    return data


def get_scoop_value_and_id(category, search_option):
    '''-> category value, event_id'''
    url = 'http://localhost:5001/api/mysql/get_scoop'
    params = {"category": category, "search_option": search_option}
    response = requests.get(url, params=params)

    response.raise_for_status()
    data = response.json()

    return data['value'], data['event_id']


############### API CALLS END #############


def country_to_iso(name):
        try:
            return pycountry.countries.lookup(name).alpha_3  # or use .alpha_2 for 2-letter codes
        except LookupError:
            return 2

@cache.memoize(timeout=3600)
def create_globe_plot(df: pd.DataFrame):

    df['iso_code'] = df['country_txt'].apply(country_to_iso)

    # Get list of countries already in the DataFrame
    present_countries = df['country_txt'].unique().tolist()

    # Prepare rows for missing countries
    missing_rows = []

    col_of_interest = df.columns[1]
    

    for c in pycountry.countries:
        if c.name not in present_countries:
            missing_rows.append({
                'country_txt': c.name,
                col_of_interest : 0,
                'iso_code': c.alpha_3
            })

    # Append missing countries
    if missing_rows:
        df = pd.concat([df, pd.DataFrame(missing_rows)], ignore_index=True)

    
    labels = {
        'ransom_demanded': {col_of_interest: 'Total Ransom Demanded'},
        'ransom_paid': {col_of_interest: 'Total Ransom Paid'},
        'number_of_attacks': {col_of_interest: 'Number of Attacks'},
    }

    fig = px.choropleth(df, 
                        locations='iso_code', 
                        color=col_of_interest, 
                        hover_data=['country_txt', col_of_interest], 
                        color_continuous_scale = ["#fff5eb", "#fd8d3c", "#f03b20", "#bd0026", "#800026"],
                        labels={**{'country_txt': 'Country'}, **labels[col_of_interest]})

    fig.update_geos(projection_type='orthographic')

    

    fig.update_layout(
        margin=dict(l=5, r=5, t=5, b=5),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        coloraxis_colorbar_title=labels[col_of_interest][col_of_interest]
    )

    # Show the figure
    return fig

@cache.memoize(timeout=3600)
def create_location_graph(lat, long):
    df = pd.DataFrame({
        "lat": [lat],
        "lon": [long]
    })

    fig = px.scatter_geo(
        df,
        lat="lat",
        lon="lon",
        projection="natural earth",
    )

    fig.update_traces(marker=dict(size=10, color="red"))

    # Zoom into the location
    fig.update_geos(
        center={"lat": lat, "lon": long},
        projection_scale=4,  # Higher = more zoomed in
        showland=True,
        landcolor="lightgreen",
        showocean=True,
        oceancolor="lightblue",
        showcountries=True,
        countrywidth=0.5
    )

    # Make plot smaller and cleaner
    fig.update_layout(
        height=300,
        width=400,
        margin=dict(l=5, r=5, t=5, b=5),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig


layout = dbc.Container([html.Div([
        dbc.Row(children=[
            dbc.Col(html.H1("Number of Terror Attacks in Each Country", id='sql-globe-title')),
            dbc.Col([
            html.Label("Select Globe Statistic:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='sql-globe-dropdown',
                options=[
                    {'label': 'Number of Attacks', 'value': 'num_attacks'},
                    {'label': 'Ransom demanded by terrorists', 'value': 'ransom_demanded'},
                    {'label': 'Ransom paid to terrorists', 'value': 'ransom_paid'}
                ],
                value='num_attacks'
            )
        ], width=3)
        ]),
        
        
        dbc.Spinner(
             dcc.Graph(id='globe-graph', config={
                                        'displayModeBar': False,
                                        'displaylogo': False
                                        }
            ),
            color="primary"
        ),

        html.H1("Find a Scoop"),
        html.Article('Use this tool to find a news story on an attack that is unique based on the selected category.'),
        dbc.Row(children=[
            dbc.Col(dcc.Dropdown(placeholder='Select Category', id='category-input')),
            dbc.Col(dbc.Button('Find Attack on Category', id='new-attack-button'), width=3),
            dbc.Col(dbc.Button('Generate Full Report', id='generate-report-button'), width=3),
            dbc.Col(width=2)
        ]
        ),
        dbc.Spinner(dbc.Row(children=[
            dbc.Col(dcc.RadioItems(id='scoop-search-option'), id='scoop-search-option-col')
        ]),color="primary"),
        dbc.Spinner(html.Div(id='attack-report'),
            color="primary"),
        html.H1("Terrorism Database"),
        # Display the table
            
        
        
        dbc.Spinner(
            dash_table.DataTable(
                id='terrorism-table',
                #columns=[{"name": col, "id": col} for col in df_init.columns],
                #data=df_init.to_dict('records'),
                page_size=25,
                style_table={'height': '400px', 'overflowY': 'auto'}
            ),
            color='primary'
        )
    ])
])


@callback(
    Output('terrorism-table', 'columns'),
    Output('terrorism-table', 'data'),
    Input('url', 'pathname')
)
def fill_database_table(pathname):
    if pathname == '/my_sql':
        df = fetch_data_from_api()
        columns = [{"name": col, "id": col} for col in df.columns]
        return columns, df.to_dict('records')
    else:
        return dash.no_update, dash.no_update


@callback(
    Output('category-input', 'options'),
    Input('url', 'pathname')
)
def update_category_options(pathname):
    if pathname == '/my_sql':
        #return get_sql_cols()
        return [
            {"label": "Attack type", "value": "attack_desc"},
            {"label": "Target of attack", "value": "target_desc"},
            {"label": "Weapon Type", "value": "weapon_desc"},
            {"label": "Fatalities", "value": "fatalities"},
            {"label": "Wounded", "value": "wounded"},
            {"label": "Ransom demanded by attacker", "value": "ransom_demanded"},
            {"label": "Ransom paid to attacker", "value": "ransom_paid"},
        ]
    else:
        return dash.no_update
    


@callback(
    Output('globe-graph', 'figure'),
    Output('sql-globe-title', 'children'),
    Input('sql-globe-dropdown', 'value')
)
def rotate_globe(stat_type):
    df = fetch_by_country_stats(stat_type)
    stat_type_to_title = {
        'ransom_demanded': 'Ransom Demanded by Terrorists in Each Country',
        'ransom_paid': 'Ransom Paid to Terrorists in Each Country',
        'num_attacks': 'Number of Terror Attacks in Each Country'
    }
    return create_globe_plot(df), stat_type_to_title[stat_type]


@callback(
    Output('scoop-search-option-col', 'children'),
    Input('category-input', 'value')
)
def category_input_response(category):
    int_cats = ['fatalities', 'wounded', 'ransom_demanded', 'ransom_paid']
    str_cats = ['attack_desc', 'target_desc', 'weapon_desc']

    if category not in int_cats + str_cats:
        return dash.no_update
    elif category in int_cats:
        options = [{'label':'High Value','value':True},{'label':'Low Value','value':False}]
    elif category in str_cats:
        options = [{'label':'Frequent Value','value':True},{'label':'Rare Value','value':False}]
        
    return [html.Div('Value type from category:'), dbc.RadioItems(
        id="scoop-search-option",
        options=options,
        value=False,
        inline=True
    )]

@callback(
    Output('attack-report', 'children'),
    Output('attack-report', 'style'),
    State('category-input', 'value'),
    State('scoop-search-option', 'value'),
    Input('generate-report-button', 'n_clicks'),
    Input('new-attack-button', 'n_clicks')
)
def generate_report_button_response(category, search_option, full_report_n_clicks, search_n_clicks):
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
    if n_clicks < 1:
        return dash.no_update
    
    style = {'backgroundColor': '#f9f9f9', 'padding': '10px', 'borderRadius': '8px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'}
    
    #Get most frequent or least frequent value:
    category_value, event_id = get_scoop_value_and_id(category, search_option)
    if report_format == 'short':
        return [html.H5(f'Attack found from category {category}, value: {category_value}')], style
    elif report_format == 'full':
        row = get_report_cols_from_event_id_sql(event_id)[0]
        print(row)
        return create_HTML_report(row), style
        

def create_HTML_report(row):
    
    if row['city'] == 'Unknown' and row['country_txt'] != 'Unknown':
        headline = f'Terror report on {row['attacktype_txt']} incident in {row['country_txt']}'
    else:
        headline = f'Terror report on {row['attacktype_txt']} incident in {row['city']}, {row['country_txt']}'

    if row['attacktype_txt'] != 'Unknown':
        headline.replace('Unknown ', '')

    import time
    row['year'], row['month'], row['day'] = row['date'].split('-')
    date =  pretty_date(int(row['year']), int(row['month']), int(row['day']))

    children_object = [
        html.H2(headline),
        html.H5(f'Date of Attack: {date}'),
        html.Hr()
    ]
    body = f''
    if row['ransom_demanded']:
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
    children_object.append(html.H5('Location:'))
    children_object.append(dcc.Graph(id='report-location-map', 
                                     figure=create_location_graph(row['latitude'], row['longitude']),
                                     config={
                                        'displayModeBar': False,
                                        'displaylogo': False
                                    }))
    return children_object
    
@callback(
    Output('new-attack-button', 'n_clicks'),
    State('new-attack-button', 'n_clicks'),
    Input('category-input', 'value'),
    Input('scoop-search-option', 'value'), prevent_initial_callback=True
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
    if str(day)[-1] == '1' and str(day) != '11':
        form = "%dst of %B, %Y"
    elif str(day)[-1] == '2' and str(day) != '12':
        form = "%dnd of %B, %Y"
    elif str(day)[-1] == '3' and str(day) != '13':
        form = "%drd of %B, %Y"
    

    formatted_date = date_obj.strftime(form)  # e.g. '24th of December'

    if formatted_date[0] == '0':
        formatted_date = formatted_date[1:]

    return formatted_date


