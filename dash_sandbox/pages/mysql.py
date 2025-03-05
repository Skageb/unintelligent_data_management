import dash
from dash import html, dcc, callback, Input, Output, dash_table
import mysql.connector
import pandas as pd

dash.register_page(__name__, path='/my_sql')

# MySQL config
conn = mysql.connector.connect(
    host='127.0.0.1',
    port=13306,
    user='root',
    password='secret',
    database='odb'
)

cursor = conn.cursor()

# Function for fetching data from database
def fetch_data_from_db():
    query = "SELECT * FROM terrorism"
    cursor.execute(query)
    result = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(result, columns=columns)
    return df

df = fetch_data_from_db()

layout = html.Div([
    html.H1("Terrorism Database"),
    
    # Display the table
    dash_table.DataTable(
        id='terrorism-table',
        columns=[{"name": col, "id": col} for col in df.columns],
        data=df.to_dict('records'),
        page_size=25,
        style_table={'height': '400px', 'overflowY': 'auto'}
    ),
])
