import dash
from dash import html, dcc, callback, Input, Output, State, ctx
import dash_bootstrap_components as dbc


dash.register_page(__name__, path='/')

layout = dbc.Container(
    dbc.Card(
        dbc.CardBody([
            html.H1('Welcome to the Global Terrorism Application', className='text-center mb-4'),
            html.H4('Please select a backend to get started.', className='text-center mb-5'),

            dbc.Row([
                dbc.Col(
                    dbc.Button(
                        'MySQL',
                        id='select-sql-button',
                        href='/my_sql',
                        color='primary',
                        className='w-100 d-flex align-items-center justify-content-center',
                        style={'fontSize': '36px', 'fontWeight': 'bold', 'aspectRatio': '1 / 1'}
                    ),
                    xs=4
                ),
                dbc.Col(
                    dbc.Button(
                        'MongoDB',
                        id='select-mongo-button',
                        href='/mongo_db',
                        color='success',
                        className='w-100 d-flex align-items-center justify-content-center',
                        style={'fontSize': '36px', 'fontWeight': 'bold', 'aspectRatio': '1 / 1'}
                    ),
                    xs=4
                ),
                dbc.Col(
                    dbc.Button(
                        'Neo4j',
                        id='select-neo-button',
                        href='/neo4j',
                        color='danger',
                        className='w-100 d-flex align-items-center justify-content-center',
                        style={'fontSize': '36px', 'fontWeight': 'bold', 'aspectRatio': '1 / 1'}
                    ),
                    xs=4
                ),
            ], className='mb-5'),

            html.H5(html.I('Powered by the Unintelligent Data Management Group'), className='text-center text-muted')
        ]),
        className='shadow p-5 rounded bg-light'
    )
)

