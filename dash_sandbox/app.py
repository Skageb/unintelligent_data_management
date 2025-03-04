import dash
from dash import Dash, html, dcc, callback, Input, Output, _dash_renderer, ctx
import dash_bootstrap_components as dbc




app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dcc.Location(id="url", refresh=False),
dbc.DropdownMenu(
        [
            dbc.DropdownMenuItem("MySQL", href="/my_sql"),
            dbc.DropdownMenuItem("MongoDB", href="/mongo_db"),
            dbc.DropdownMenuItem("Neo4j", href="/neo4j"),
        ],
        label="Select Backend",
        id="dropdown-menu",
    ),
    dash.page_container
], fluid= True)


@app.callback(
    Output("dropdown-menu", "label"),
    Input("url", "pathname"),
)
def update_dropdown_label(pathname):
    """
    Check which path is active and update the dropdown label accordingly.
    """
    if pathname == "/my_sql":
        return "Selected Backend: MySQL"
    elif pathname == "/mongo_db":
        return "Selected Backend: MongoDB"
    elif pathname == "/neo4j":
        return "Selected Backend: Neo4j"
    else:
        # If it's just the base URL or unrecognized path, default to "Select Backend"
        return "Select Backend"


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8080)
    