import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_uploader as du
import plotly.graph_objects as go
from app import app

du.configure_upload(app,"uploads",use_upload_id=False)

def get_upload_component(id):
    
    return du.Upload(
        id=id,
        text="Click here to upload",
        pause_button=True,
        text_completed='Uploaded: ',
        max_file_size=1800,  # 1800 Mb
        filetypes=['csv', 'json'],
        default_style=None,
    )

main_layout = html.Div([
                        html.Div(className="app-div--titlenav",children=
                                html.Nav(className="navbar navbar-expand-lg navbar-dark bg-primary ",children=
                                        html.Div(className="container-fluid", children=[
                                            html.A("Boosterpack Sample", className="navbar-brand", href="#"),
                                            html.Button('Login',n_clicks=0,
                                            id='login-button',className='btn btn-primary',hidden=True), 

                                            html.Button('Logout', id='logout', n_clicks=0,className="btn btn-secondary my-2 my-sm-0",),
                                        ])
                                ),
                        ),
                        html.Br(),
                        html.Div(className = "block flex-container", children=[
                                html.Div(className="block flex-container-options text-white bg-primary",children=[
                                        html.Div(className="block item1-options",children=[
                                                html.H4("Dataset selection options"),
                                                dcc.Dropdown(id="dynamic-dropdown",options=[{'label':'Demo file','value':'202004-divvy-tripdata'}], 
                                                             placeholder="Select a dataset",
                                                             style=dict(width='100%',verticalAlign="middle", fontcolor="black")),
                                                html.Div(html.Button('Load', id='load', n_clicks=0,className="myButton2", style={'width': '100%'}
                                                                    ),style={'textAlign':'center'}),
                                                html.Div(id='dd-output-container',style={'textAlign':'center'}),
                                                html.Ul(id="file-list",children=[]),
                                                ]),
                                        html.Div(className="item2-options", children=[
                                                html.H4("Date options"),
                                                dcc.DatePickerRange(id='my-date-picker-range', style={'textAlign':'center','font-size':'5vw;','width':'100%'}),
                                                html.Div(id='output-container-date-picker-range', children=[],className='text-warning',style={'textAlign':'center'}),
                                                html.Div(id='output-container-max-date-range', children=[],className='text-warning',style={'textAlign':'center'}),

                                                ],style={'flex-direction':'columns'}),
                                        html.Div(className="item3-options",children=[
                                                html.H4("AI prediction options"),
                                                dcc.Input(id='num_predict', placeholder='Enter number of values to predict',type='number', className="form-control"),
                                                html.Br(),
                                                html.Div([html.Button('Predict multiple locations', id='predict_multiple_locations', n_clicks=0,
                                                                     className="myButton2", style={'width': 'auto'},hidden=True),
                                                          html.Br(),
                                                          html.Br(),
                                                          html.Button('Predict single location', id='predict_single_location', n_clicks=0,
                                                                    className="myButton2", style={'width': 'auto','textAlign':'center'}, hidden=True)],
                                                         style={'flex-direction':'row','textAlign':'center'}),]),
                                        html.Div(className='item4-options',children=[
                                                html.H4("AI clustering options"),
                                                html.Div(html.Button('Cluster locations', id='cluster_locations', n_clicks=0, hidden = False,
                                                                    className="myButton2", style={'width': 'auto'}),style={'textAlign':'center'}),]),                                        
                                        html.Div(className='item5-options',children=[
                                                html.H4("Download options"),
                                                html.Div([
                                                    html.Button('Download working data', id='btn_csv', n_clicks=0, hidden = True,
                                                                      className="myButton2",style={'width': 'auto'}
                                                        ),
                                                      html.Br(),
                                                          html.Br(),
                                                        
                                                    html.Button('Download Sample file', id='sample', n_clicks=0,className="myButton2",style={'width': 'auto'}),
                                                          html.Br(),
                                                          html.Br(),
                                                          ],style={'flex-direction':'column','textAlign':'center'}),
                                                ]),
                                        html.Div(className="item6-options",children=[
                                                html.H4("File upload options"),
                                                html.Div([get_upload_component(id='dash-uploader'),]),],
                                                style={'flex-direction':'row','width':'100%'})
                                    ]),
                                    html.Div(className="block item2 text-white bg-primary", children=[
                                                    dcc.Graph(id='map', className="tab-pane fade show active",
                                                                config={
                                                                    'displayModeBar': 'hover',
                                                                    'modeBarButtonsToAdd':['select2d'],
                                                                    'autosizable':True
                                                                },
                                                                figure={
                                                                    'data': [],
                                                                    'layout': go.Layout(
                                                                        xaxis={
                                                                            'showticklabels': False,
                                                                            'ticks': '',
                                                                            'showgrid': False,
                                                                            'zeroline': False
                                                                        },
                                                                        yaxis={
                                                                            'showticklabels': False,
                                                                            'ticks': '',
                                                                            'showgrid': False,
                                                                            'zeroline': False
                                                                        },
                                                                        paper_bgcolor='rgba(224,224,224,0.6)',
                                                                        plot_bgcolor='rgba(224,224,224,0.6)',
                                                                        )}
                                                            )
                                                ],),
                                    html.Div(className="block item3 text-white bg-primary",children=[
                                            dcc.Graph(
                                                        id='graph', 
                                                        config={
                                                            'displayModeBar': 'hover',
                                                            'modeBarButtonsToAdd':['select2d'],
                                                        },
                                                        figure={
                                                            'data': [],
                                                            'layout': go.Layout(
                                                                xaxis={
                                                                    'showticklabels': False,
                                                                    'ticks': '',
                                                                    'showgrid': False,
                                                                    'zeroline': False
                                                                },
                                                                yaxis={
                                                                    'showticklabels': False,
                                                                    'ticks': '',
                                                                    'showgrid': False,
                                                                    'zeroline': False
                                                                },
                                                                paper_bgcolor='rgba(224,224,224,0.6)',
                                                                plot_bgcolor='rgba(224,224,224,0.6)',
                                                                )}
                                                    ),
                                            dcc.Graph(
                                                        id='AI_output', 
                                                        config={
                                                            'displayModeBar': 'hover',
                                                            'modeBarButtonsToAdd':['select2d'],
                                                        },
                                                        figure={
                                                            'data': [],
                                                            'layout': go.Layout(
                                                                xaxis={
                                                                    'showticklabels': False,
                                                                    'ticks': '',
                                                                    'showgrid': False,
                                                                    'zeroline': False
                                                                },
                                                                yaxis={
                                                                    'showticklabels': False,
                                                                    'ticks': '',
                                                                    'showgrid': False,
                                                                    'zeroline': False
                                                                },
                                                                paper_bgcolor='rgba(224,224,224,0.6)',
                                                                plot_bgcolor='rgba(224,224,224,0.6)',
                                                                )}
                                                    )
                                        ]),
                                        html.Div(dcc.Download(id="download-dataframe-csv")),

                                        dcc.Loading(
                                            id="loading-1",
                                            type="circle",
                                            fullscreen=True,
                                            children=html.Div(id="loading-output-12", style={'textAlign':'center'})
                                            ),
                                        dcc.Loading(
                                            id="loading-3",
                                            type="circle",
                                            fullscreen=True,
                                            children=html.Div(id="loading-output-3", style={'textAlign':'center'})
                                            ),
                                        dcc.Loading(
                                            id="loading-2",
                                            type="circle",
                                            fullscreen=True,
                                            children=html.Div(id="loading-output-2"),style={'textAlign':'center'}
                                            ),
                                        dcc.Loading(
                                            id="loading-4",
                                            type="circle",
                                            fullscreen=True,
                                            children=html.Div(id="loading-output-4"),style={'textAlign':'center'}
                                            ),
                                        dcc.Loading(
                                            id="loading-5",
                                            type="circle",
                                            fullscreen=True,
                                            children=html.Div(id="loading-output-5"),style={'textAlign':'center'}
                                            ),
                                        dcc.Input(placeholder='Enter your username',
                                        value = "",
                                        type='hidden',
                                        id='uname-box'), 
                                    dcc.Input(placeholder='Enter your password',
                                        type='hidden',
                                        value="",
                                        id='pwd-box'),
                                    ]),
                                ])
login_layout = html.Div([html.Div(className="app-div--titlenav",children=
                                html.Nav(className="navbar navbar-expand-lg navbar-dark bg-primary ",children=
                                        html.Div(className="container-fluid", children=[
                                            html.A("Boosterpack Sample", className="navbar-brand", href="#"),
                                            html.Button('Logout', id='logout', n_clicks=0,className="btn btn-secondary my-2 my-sm-0",hidden=True),
                                        ])
                                ),
                        ),
                        html.Hr(),
                        dbc.Row([
                            dbc.Col([
                                    html.H2('''Please log in to continue:''', id='h1'),
                                    html.Hr(),
                                    
                                    dcc.Input(placeholder='Enter your username',
                                        value = "",
                                        type='text',
                                        id='uname-box'), 
                                    html.Hr(),

                                    dcc.Input(placeholder='Enter your password',
                                        type='password',
                                        value="",
                                        id='pwd-box'),
                                    html.Hr(),

                                    html.Div(
                                        html.Button('Login',n_clicks=0,
                                            id='login-button',className='btn btn-primary'),className="d-grid gap-2 d-md-flex justify-content-md-center"), 
                                    html.Div(children='', id='output-state')
                                ], className='card text-dark bg-light mb-3',width=3,style={'padding':'10px'})
                            ], className="text-center",justify='center')
                    ])

login_failed = html.Div([ 
                    html.Div([
                        html.Div([login_layout]), 
                        html.H2('Log in Failed. Please try again.'), 

                    ]) 
                ])

logout = html.Div([
                        html.Div(className="app-div--titlenav",children=
                                html.Nav(className="navbar navbar-expand-lg navbar-dark bg-primary ",children=
                                        html.Div(className="container-fluid", children=[
                                            html.A("Boosterpack Sample", className="navbar-brand", href="#"),
                                            

                                        ])
                                ),),
                            html.Br(),
                            html.Hr(),
                    html.Div([
                        html.H2('You have been logged out!')])
                            ,
                        
                    
                ],className="text-center")