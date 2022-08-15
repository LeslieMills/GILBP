import dash
# from flask_caching import Cache
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc

app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.SANDSTONE])
server = app.server

app.layout = html.Div([
                dcc.Location(id='url', refresh=True),
                html.Div(id='page-content'),
                dcc.Store(data='', id='session-id',storage_type='session'),
                dcc.Store(data='', id='file-id',storage_type='session'),
                dcc.Store(data='', id='file-id2',storage_type='session'),
                dcc.Store(data={'admin_test':[{"label": "Demo file", "value": "202004-divvy-tripdata"}]},id='options',storage_type='session')
                ])
