import dash
# from flask_caching import Cache
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_core_components as dcc

app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.SANDSTONE])
server = app.server

# cache = Cache(app.server, config={
#     'CACHE_TYPE': 'redis',
#     # Note that filesystem cache doesn't work on systems with ephemeral
#     # filesystems like Heroku.
#     'CACHE_TYPE': 'filesystem',
#     'CACHE_DIR': 'cache-directory',

#     # should be equal to maximum number of users on the app at a single time
#     # higher numbers will store more data in the filesystem / redis cache
#     'CACHE_THRESHOLD': 10
# })

app.layout = html.Div([
                dcc.Location(id='url', refresh=True),
                html.Div(id='page-content'),
                dcc.Store(data='', id='session-id',storage_type='session'),
                dcc.Store(data='', id='file-id',storage_type='session'),
                dcc.Store(data='', id='file-id2',storage_type='session'),
                dcc.Store(data={'hello':[{"label": "Demo file", "value": "202004-divvy-tripdata"}]},id='options',storage_type='session')
                ])
