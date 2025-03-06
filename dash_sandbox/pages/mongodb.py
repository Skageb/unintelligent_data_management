import dash
from dash import html, dcc, callback, Input, Output, dash_table
from pymongo import MongoClient

dash.register_page(__name__, path='/mongo_db')

MONGO_URI = "mongodb://root:secret@127.0.0.1:27017/admin"

client = MongoClient(MONGO_URI)
odb_db = client["odb"]
collection = odb_db["gtd"]

data = list(collection.find().limit(10))

for doc in data:
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])

if data:
    columns = [{"name": key, "id": key} for key in data[0].keys()]
else:
    columns = []

layout = html.Div([
    html.H1('MongoDB Data Landing Page'),
    html.Div('Displaying the first 10 records from the ODB.gdt collection'),
    dash_table.DataTable(
        data=data,
        columns=columns,
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
    )
])