# Imports needed
from flask_login import login_user, logout_user, current_user, LoginManager, UserMixin
from sqlalchemy import Table, create_engine, MetaData, select
import os
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import warnings
import configparser
from dash import dcc, html, callback_context
import dash_uploader as du
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
# from app import app, server, cache
from app import app, server
import requests
import plotly.express as px
from layouts import main_layout, login_layout, login_failed,logout
from bson import ObjectId
import json

# importing code to download file from Mongo
from database_download import download_gridfs

# importing code to upload file to MongoDB and other operations
from database_upload import dbInsertFile, delete_file, delete_database, create_demo_file, delete_working_files

# password checking function import
from werkzeug.security import check_password_hash

# import the clustering ML function
from cluster_ai import cluster

# Setting for dash 
warnings.filterwarnings("ignore")

# settings and connection to SQLITE db which holds user authentication data
conn = sqlite3.connect('data.sqlite')
engine = create_engine('sqlite:///data.sqlite')
db = SQLAlchemy()
config = configparser.ConfigParser()

server.config.update(
    SECRET_KEY=os.urandom(12),
    SQLALCHEMY_DATABASE_URI='sqlite:///data.sqlite',
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

# initiating SQLITE db
db.init_app(server)

# Setup the LoginManager for the server
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = '/login'
login_manager.refresh_view = '/login'

# create class to import SQLITE user records
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable = False)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))

Users_tbl = Table('users', Users.metadata)

class Users(UserMixin, Users):
    pass

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# def get_dataframe(session_id,value,flag,demo_file_flag):
#     if flag == 1:
#         cache.clear()
#     @cache.memoize()
#     def query_and_serialize_data(session_id):
#         condition = {}
#         # df = download_data('boosterpack_test', value, condition)
#         download_gridfs(session_id, value)
#         init_path = "users"
#         filepath = os.path.join(init_path,session_id,"temp.csv")
#         df = pd.read_csv(filepath)
#         print("\n\n\n\n\n")
#         print(demo_file_flag)
#         print("\n\n\n\n\n")
#         if demo_file_flag == 1: 
#             cleaned_df = file_work(df)
#             cleaned_df.reset_index(inplace=True)
#         else:
#             cleaned_df = df
#         return cleaned_df.to_json(default_handler=str, orient="records", lines=True)
#     df = pd.DataFrame([])
#     i = 1
#     for chunk in pd.read_json(query_and_serialize_data(session_id),orient="records",lines=True,chunksize=10000,nrows=20000000):
#         # print(i)
#         i = i+1
#         df = df.append(chunk)
#     return df

def date_minmax(df):
    min_date = min(df['date'])
    max_date = max(df['date'])
    return min_date,max_date

def latlong(df):
    df['lat'] = df['lat'].astype(float)
    df['lng'] = df['lng'].astype(float)
    df_geo = df.dropna(subset=['lat', 'lng'], axis=0, inplace=False)
    df_geo['date'] = df_geo['date'].astype(str)
    return df_geo

def file_work(df):
    df['started_at'] = pd.to_datetime(df['started_at'])
    df['ended_at'] = pd.to_datetime(df['ended_at'])
    df = df.groupby(['start_station_id','start_station_name','start_lat','start_lng','started_at'])['ride_id'].count()
    df = df.reset_index()
    df = pd.concat({g: x.set_index("started_at").resample("D")['ride_id'].count()
                    for g, x in df.groupby(['start_station_id','start_station_name','start_lat','start_lng'])})
    df = df.reset_index()
    df = df.rename(columns={'level_2':'lat','level_3':'lng','ride_id':'variable_1','level_1':'variable_1_name','level_0':'variable_1_id',"started_at":"date"})
    return df

@app.callback(Output('page-content', 'children'),               
              Input('url', 'pathname'),
              prevent_initial_call=True)
def display_page(pathname):
    if pathname == '/':
        return login_layout
    elif pathname == '/login':
        return login_layout
    elif pathname == '/success':
        # print("pre authentication")
        if current_user.is_authenticated:
            # print("post authentication")
            return main_layout
        else:
            return login_failed
    elif pathname == '/logout':
        if current_user.is_authenticated:
            logout_user()
            return logout
        else:
            return logout
    else:
        return '404'

# callback function that runs when Login button clicked. This function takes action to authenticate and 
# log a user in. 
# It also performs administrative tasks of setting up the users initial demo file and file directory on server
# The user interaction on username and password verification is provided by another function

@app.callback(
                Output('url', 'pathname'),
                Output('session-id','data'),
                Output('file-id','data'), 
                Input('login-button', 'n_clicks'),
                Input('logout','n_clicks'),
                State('uname-box', 'value'), 
                State('pwd-box', 'value'),
                prevent_initial_call=True
            )

def on_login_click(login_n_clicks, logout_n_clicks,username, password):

    ctx = callback_context
    if not ctx.triggered:
        action_id = 'No clicks yet'
    else:
        action_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(action_id)
    if logout_n_clicks>=1 and action_id == 'logout':
        return '/logout',None, None
    #Retrieve the user object with the name that is same as the username input
    user = Users.query.filter_by(username=username).first()
    #Check if user is found
    if user is not None:
        #Check if password is a match
        if check_password_hash(user.password, password):
            # Log the user in. This is an inbuilt flask-login library function
            login_user(user)
            # Print to console
            print(username+" is logged in!")
            # clear all existing databases and working file related to this user. if the user requires an option to
            # save their working files, these functions can be not run
            delete_database(username)
            delete_working_files(username)
            # Print to console
            print("existing database and working files of {} cleaned!".format(username))
            # Run the function that creates a demo file for the user
            create_demo_file("202004-divvy-tripdata.csv",username)
            # Upload the original demo file to MongoDB
            fileID = dbInsertFile("202004-divvy-tripdata.csv",username)
            # Download the demo file from MongoDB and create a working copy of the file 
            download_gridfs(username, fileID)
            # return the username and fileid of the demo file to temporary storage so that other functions can access it
            # return the string success to the page URL pathname
            # this will act to call the callback function to bring up the dashboard layout to the user
            return "/success", username, str(fileID)
        else:
            raise PreventUpdate
    else:
        raise PreventUpdate

#callback function that runs when login button is clicked. It handles the user interaction and authentication of 
# username and password entered by tge user

@app.callback(
                Output('output-state', 'children'), 
                Input('login-button', 'n_clicks'), 
                State('uname-box', 'value'), 
                State('pwd-box', 'value'),
                prevent_initial_call=True
            )

def login_button_user_interaction(login_n_clicks, username, password):
    # check if login button is clicked
    if login_n_clicks > 0:
        #Retrieve the user object with the name that is same as the username input
        user = Users.query.filter_by(username=username).first()
        # check if null was returned. If not username is valid
        if user:
            #check the password. Return nothing if success
            if check_password_hash(user.password, password):
                return ''
            else:
                return 'Incorrect password'
        else:
            return 'Incorrect username'
    else:
        return ''

# Callback function to update on the dashboard the name of the file the user has selected to Load
# reterieves value from the file selection dropdown and display on the screen below the dropdown
@app.callback(
                Output('dd-output-container', 'children'),
                Input('dynamic-dropdown', 'value'),
                prevent_initial_call=True
            )

def dropdown_output(value):
    return 'You have selected "{}"! Click load to continue'.format(value)

# callback to initiate the dashboard page when the load button is clicked. This function loads the information in the
# demo file or uploaded file into dataframes that are used as the datasource for the maps and graphs within the 
# dashboard. post that this function retreives the min and max dates from the data and sets that as output to the
# data range selector

@app.callback( 
                Output('load','n_clicks'),
                Output('my-date-picker-range', 'min_date_allowed'),
                Output('my-date-picker-range', 'max_date_allowed'),
                Output('my-date-picker-range','start_date'),
                Output('my-date-picker-range','end_date'),
                Output('my-date-picker-range','initial_visible_month'),
                Output('loading-1','children'),
                Output('btn_csv','hidden'),
                Input('load','n_clicks'),
                State('dynamic-dropdown', 'value'),
                State('session-id', 'data'),
                State('file-id','data'),
                State('file-id2','data'),
                prevent_initial_call=True
                )

def initiate_page(n_clicks, value,session_id,fileID,fileID2):
    # check if the demofile is the input or user uploaded file
    try:
        if value.split('-')[1] =="divvy":
                demo_file_flag=1
        else:
                demo_file_flag=0
    except:
        demo_file_flag=0
    if value == "202004-divvy-tripdata" or fileID2 == "":
        fileID = ObjectId(fileID)
        
    else:
        fileID = ObjectId(fileID2)
        
    # if dropdown selected value is not empty
    if value is not None:
        # if load button was clicked
        if n_clicks >= 1:
            # flag to clear existing redis cache
            flag = 1
            # function to retreive dataframe of the current selected file
            path = os.path.join('users',session_id,value+'.csv')
            df = pd.read_csv(path)
            if demo_file_flag == 1:
                df = file_work(df)
                df.reset_index(inplace=True)
            # df = get_dataframe(session_id, fileID, flag,demo_file_flag)     
            # retreive the min and max dates
            min_date, max_date = date_minmax(df)
            # clean up the latlong field 
            text = ""
            return 0,min_date,max_date,min_date,max_date,min_date, html.Div(text,id="loading-output-1", style={'textAlign':'center'}), False
    raise PreventUpdate

# callback function that is called each time the date ranges are updated. This function updates the data that is mapped
# and displays back to the user, the max date range and the selected date range

@app.callback(
                Output('output-container-date-picker-range', 'children'),
                Output('output-container-max-date-range','children'),
                Output('map', 'figure'),
                Output('loading-5','children'),
                Input('my-date-picker-range', 'start_date'),
                Input('my-date-picker-range', 'end_date'),
                Input('my-date-picker-range', 'min_date_allowed'),
                Input('my-date-picker-range', 'max_date_allowed'),
                State('session-id', 'data'),
                State('dynamic-dropdown', 'value'),
                prevent_initial_call=True
            )

def update_map(start_date, end_date, min_date, max_date,session_id,value):
    # function to retreive working dataframe from cache
    # path = os.path.join('users',session_id,'temp.csv')
    path = os.path.join('users',session_id,value+'.csv')
    cleaned_df = pd.read_csv(path)
    try:
        if value.split('-')[1] =="divvy":
                cleaned_df = file_work(cleaned_df)
    except:
        pass
    # cleaned_df = get_dataframe(session_id, value,0,0)
    # clean up the latitude and longitude columns
    cleaned_df = latlong(cleaned_df)
    # crate a working dataframe for the map. This dataframe is a subset of the working dataframe 
    map_df = cleaned_df[cleaned_df['date']>=start_date]
    map_df = map_df[map_df['date']<=end_date]

    # plot the data on the map in a scatter point style. use the date field as the animation frame and the variable name column as the animation group
    # set the scatter point size to match intensity of variable from file
    fig = px.scatter_mapbox(map_df, lat="lat", lon="lng", hover_name="variable_1_name", hover_data=["variable_1"],
                    color="variable_1", zoom=9, animation_frame="date", height=800, animation_group="variable_1_name", size = 'variable_1',
                    color_continuous_scale='emrld')    
    # update the plot settings
    fig.update_layout(mapbox_style="carto-positron")
    fig.update_layout(legend_orientation="h")
    fig.update_layout(margin={"r":5,"t":10,"l":5,"b":10})
    # fig.update_layout(paper_bgcolor = 'rgba(0,0,0,0)')
    # fig.update_layout(plot_bgcolor = 'rgba(0,0,0,0)')
    # create output string of max date range and user selected date range
    date_range = f"Selected Date Range: {start_date.split('T')[0]} to {end_date.split('T')[0]}"
    max_range = f"Max. Date Range: {min_date.split('T')[0]} to {max_date.split('T')[0]}"
    text = ""
    return date_range, max_range, fig, text
      

@app.callback(Output('download-dataframe-csv', 'data'),
                Output('btn_csv', "n_clicks"),
                Output('sample','n_clicks'),
                State('my-date-picker-range', 'start_date'),
                State('my-date-picker-range', 'end_date'),
                Input('sample','n_clicks'),
                Input("btn_csv", "n_clicks"),
                State('session-id', 'data'),
                State('dynamic-dropdown', 'value'),
                prevent_initial_call=True)
def download(start_date, end_date, n_clicks_file,n_clicks_sample,session_id,value):
    ctx = callback_context
    if not ctx.triggered:
        action_id = 'No clicks yet'
    else:
        action_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if action_id == 'btn_csv':
        # path = os.path.join(session_id,'temp.csv')
        path = os.path.join('users',session_id,value+'.csv')
        cleaned_df = pd.read_csv(path)
        try:
            if value.split('-')[1] =="divvy":
                cleaned_df = file_work(cleaned_df)
        except:
            pass
        # cleaned_df = get_dataframe(session_id, value,0,0)
        cleaned_df = latlong(cleaned_df)
        download_df = cleaned_df[cleaned_df['date']>=start_date]
        download_df = download_df[download_df['date']<=end_date]
        return dcc.send_data_frame(download_df.to_csv, "working_data.csv", index=False),0,0
    if action_id == 'sample':
        sample_df = pd.read_csv('sample.csv')
        return dcc.send_data_frame(sample_df.to_csv, "sample.csv", index=False),0,0

@app.callback(Output('graph', 'figure'),
                Output('loading-4','children'),
                Output('predict_single_location','hidden'),
                Output('predict_multiple_locations','hidden'),
                Input("map", "clickData"),
                Input("map","selectedData"),
                State('my-date-picker-range', 'start_date'),
                State('my-date-picker-range', 'end_date'),
                State('session-id', 'data'),
                State('dynamic-dropdown', 'value'),
                prevent_initial_call=True)
def on_map_click(clickdata, selectedData,start_date, end_date,session_id,value):
    # path = os.path.join(session_id,'temp.csv')
    path = os.path.join('users',session_id,value+'.csv')
    cleaned_df = pd.read_csv(path)
    try:
        if value.split('-')[1] =="divvy":
            cleaned_df = file_work(cleaned_df)
    except:
        pass
    # cleaned_df = get_dataframe(session_id, value,0,0)
    cleaned_df = latlong(cleaned_df)
    graph_df = cleaned_df[cleaned_df['date']>=start_date]
    graph_df = graph_df[graph_df['date']<=end_date]
    ctx = callback_context

    if not ctx.triggered:
        action_id = 'No clicks yet'
    else:
        action_id = ctx.triggered[0]['prop_id'].split('.')[1]

    if action_id =='clickData':
        graph_df = graph_df[graph_df['variable_1_name']==clickdata['points'][0]['id']]
        fig2 = px.bar(graph_df,y="variable_1",x='date',hover_data=['variable_1','variable_1_name'], 
                        color='variable_1',labels={'pop': 'variable_1_name'}, height=400, orientation='v', color_continuous_scale='emrld')
        fig2.update_layout(legend_orientation="h")
        fig2.update_layout(
                yaxis={
                'tickformat': '%Y-%m-%d',
                    'tickmode': 'auto',
                    'tick0':pd.to_datetime(start_date),
                    'dtick':86400000
                })
        fig2.update_layout(margin={"r":5,"t":10,"l":5,"b":10})
        # fig2.update_layout(paper_bgcolor = 'rgba(0,0,0,0)')
        # fig2.update_layout(plot_bgcolor = 'rgba(0,0,0,0)')
        text = ""   
        return fig2, text, False, True

    if action_id == 'selectedData':
        lat = []
        lon = []
        name = []
        variable = []
        for point in selectedData['points']:
            lat.append(point['lat'])
            lon.append(point['lon'])
            name.append(point['id'])
            variable.append(point['customdata'][0])
        new_df = pd.DataFrame(list(zip(lat,lon,name,variable)),columns=['lat','lng','variable_1_name','variable_1'])
        graph_df = graph_df.merge(new_df, on='variable_1_name', how = 'inner',suffixes=[None,'_y'])
        graph_df = graph_df.groupby('date').agg({'variable_1':'sum','lat':'mean','lng':'mean'})
        graph_df.reset_index(inplace=True)
        fig2 = px.bar(graph_df,y="variable_1",x='date',hover_data=['variable_1'], 
                        color='variable_1',labels={'pop': 'variable_1_name'}, height=400, orientation='v',color_continuous_scale='emrld')


        fig2.update_layout(legend_orientation="h")
        fig2.update_layout(
                yaxis={
                'tickformat': '%Y-%m-%d',
                    'tickmode': 'auto',
                    'tick0':pd.to_datetime(start_date),
                    'dtick':86400000
                })
        fig2.update_layout(margin={"r":5,"t":10,"l":5,"b":10})
        # fig2.update_layout(paper_bgcolor = 'rgba(0,0,0,0)')
        # fig2.update_layout(plot_bgcolor = 'rgba(0,0,0,0)')
        text = ""   
        return fig2, text,True, False

@app.callback(
    Output('dynamic-dropdown','options'),
    Output('file-id2','data'),
    State('session-id', 'data'),
    State('file-id2','data'),
    State('options','data'),
    [Input('dash-uploader', 'isCompleted')],
    [State('dash-uploader', 'fileNames')],
                prevent_initial_call=True)
def upload_complete(sessionid,fileID2, options,isCompleted, filename):
    if(isCompleted):
        for x in options[sessionid]:
            if x['label'] != "Demo file":
                options[sessionid].pop()
                # print("deleted last file from options")
                file = x['value']+".csv"
                file_path = os.path.join("users",sessionid,file)
                os.remove(file_path)
                # print("deleted last file from memory")
        for file in filename:
            options[sessionid].append({"label": file.split('.')[0], "value": file.split('.')[0]}) 
            # options.append({sessionid:{"label": file.split('.')[0], "value": file.split('.')[0]}})
            init = os.path.join("uploads",file)
            fin = os.path.join("users",sessionid,file)
            os.rename(init,fin)
            fileID = dbInsertFile(file,sessionid)
            if fileID2 != "":
                delete_file(fileID2,sessionid)
            fileID2 = ObjectId(fileID)
            # print("upload and fileID swap complete")
        return options[sessionid], str(fileID2)
    raise PreventUpdate

@app.callback(  Output('AI_output','figure'),
                Output('loading-2','children'),
                Input('cluster_locations','n_clicks'),
                Input('predict_single_location','n_clicks'),
                Input('predict_multiple_locations','n_clicks'),
                State('map','selectedData'),
                State('map','clickData'),
                State('dynamic-dropdown', 'value'),
                State('session-id', 'data'),
                State('my-date-picker-range', 'start_date'),
                State('my-date-picker-range', 'end_date'),
                State('num_predict','value'),
                prevent_initial_call=True)
def on_analyze(cluster_clicks,single_click,multi_click,selectedData,clickData,value,session_id,start_date,end_date,num_predict):
    ctx = callback_context
    if not ctx.triggered:
        action_id = 'No clicks yet'
        raise PreventUpdate
    else:
        action_id = ctx.triggered[0]['prop_id'].split('.')[0]
        print(action_id)
        if num_predict is None:
            num_predict = 5
        # path = os.path.join(session_id,'temp.csv')
        path = os.path.join('users',session_id,value+'.csv')
        cleaned_df = pd.read_csv(path)
        try:
            if value.split('-')[1] =="divvy":
                cleaned_df = file_work(cleaned_df)
        except:
            pass
        # cleaned_df = get_dataframe(session_id, value,0,0)
        cleaned_df = latlong(cleaned_df)
        cleaned_df = cleaned_df[cleaned_df['date']>=start_date]
        graph_df = cleaned_df[cleaned_df['date']<=end_date]

        if action_id == 'cluster_locations':
            result_df = cluster(graph_df,0)
            fig = px.scatter_mapbox(result_df, lat="lat", lon="lng", hover_name="variable_1_name", hover_data=["labels"],
                        color="labels", zoom=8, height=400, color_continuous_scale='sunsetdark')  
            fig.update_layout(mapbox_style="carto-positron")
            fig.update_layout(legend_orientation="h")
            fig.update_layout(margin={"r":5,"t":10,"l":5,"b":10})

            return fig, " " 

        if action_id == 'predict_single_location':
            if clickData is not None:
                graph_df = graph_df[graph_df['variable_1_name']==clickData['points'][0]['id']]
                graph_df['variable_1'].to_csv('selected_point.csv')
                url = f"http://ai_module:5000/upload?filename=selected_point"
                with open('selected_point.csv', 'rb') as f:
                    requests.post(url, data=f)

                url = f"http://ai_module:5000/?filename=selected_point&predict={num_predict}"
                res = requests.get(url)
                pred = res.json()['message']
                initial_series = graph_df['variable_1']
                initial_len = len(initial_series)
                for i in range(len(pred)):
                    initial_series[initial_len+i+1] = pred[i]
                final_df= pd.DataFrame(initial_series)
                final_df.reset_index(inplace=True)
                flag=[]
                for i in range(len(final_df)):
                    if i<initial_len:
                        flag.append("Actual")
                    else:
                        flag.append("Predicted")
                final_df['flag'] = flag
                fig = px.bar(final_df,y="variable_1",hover_data=['variable_1'], 
                        color='flag',labels={'pop': 'variable_1_name'}, height=450, orientation='v',color_continuous_scale='emrld')
                fig.update_layout(legend_orientation="h")
                fig.update_layout(margin={"r":5,"t":10,"l":5,"b":10})

            return fig, " "
        if action_id == 'predict_multiple_locations':
            if selectedData is not None:
                lat = []
                lon = []
                name = []
                variable = []
                for point in selectedData['points']:
                    lat.append(point['lat'])
                    lon.append(point['lon'])
                    name.append(point['id'])
                    variable.append(point['customdata'][0])
                new_df = pd.DataFrame(list(zip(lat,lon,name,variable)),columns=['lat','lng','variable_1_name','variable_1'])
                graph_df = graph_df.merge(new_df, on='variable_1_name', how = 'inner',suffixes=[None,'_y'])
                graph_df = graph_df.groupby('date').agg({'variable_1':'sum','lat':'mean','lng':'mean'})
                graph_df.reset_index(inplace=True)

                graph_df['variable_1'].to_csv('selected_polygon.csv')
                url = "http://ai_module:5000/upload?filename=selected_polygon"
                    # res = requests.get(url)
                with open('selected_polygon.csv', 'rb') as f:
                    requests.post(url, data=f)

                url = f"http://ai_module:5000/?filename=selected_polygon&predict={num_predict}"
                res = requests.get(url)
                pred = res.json()['message']
                initial_series = graph_df['variable_1']
                initial_len = len(initial_series)
                for i in range(len(pred)):
                    initial_series[initial_len+i+1] = pred[i]
                final_df= pd.DataFrame(initial_series)
                final_df.reset_index(inplace=True)
                flag=[]
                for i in range(len(final_df)):
                    if i<initial_len:
                        flag.append("Actual")
                    else:
                        flag.append("Predicted")
                final_df['flag'] = flag
                fig = px.bar(final_df,y="variable_1",hover_data=['variable_1'], 
                        color='flag',labels={'pop': 'variable_1_name'}, height=450, orientation='v',color_continuous_scale='emrld')
                fig.update_layout(legend_orientation="h")
                fig.update_layout(margin={"r":5,"t":10,"l":5,"b":10})

            return fig, " "

        # if n_clicks >=1 and clickData is not None:
        #     graph_df = cleaned_df[cleaned_df['variable_1_name']==clickData['points'][0]['id']]
        #     graph_df.to_csv('selected_point.csv')
        #     url = f"http://ai_module:5000/upload?filename=selected_point"
        #     print(url)
        #         # res = requests.get(url)
        #     with open('selected_point.csv', 'rb') as f:
        #         requests.post(url, data=f)

        #     url = f"http://ai_module:5000/?filename=selected_point&predict={num_predict}"
        #     res = requests.get(url)
        #     # dictFromServer = res.json()
        #     # message = 'message'
        #     print(res.text)
        #     # pred_list = res.text.message
        #     # pred_list = [item for sublist in pred_list for item in sublist]
        #     # combined = graph_df['variable_1'].append(pred_list)
        #     # combo_df = pd.DataFrame(combined)
        #     fig2 = px.bar(graph_df,y="variable_1",hover_data=['variable_1','variable_1_name'], 
        #                     color='variable_1',labels={'pop': 'variable_1_name'}, height=450, orientation='v',color_continuous_scale='emrld')
        #     fig2.update_layout(legend_orientation="h")
        #     # fig2.add_trace(px.line(combo_df,x='variable_1'))
        #     fig2.update_layout(margin={"r":5,"t":10,"l":5,"b":10})
        #     # fig2.update_layout(paper_bgcolor = 'rgba(0,0,0,0)')
        #     # fig2.update_layout(plot_bgcolor = 'rgba(0,0,0,0)')

        # if n_clicks >= 1 and selectedData is not None:
        #     lat = []
        #     lon = []
        #     name = []
        #     variable = []
        #     for point in selectedData['points']:
        #         lat.append(point['lat'])
        #         lon.append(point['lon'])
        #         name.append(point['id'])
        #         variable.append(point['customdata'][0])
        #     new_df = pd.DataFrame(list(zip(lat,lon,name,variable)),columns=['lat','lng','variable_1_name','variable_1'])
        #     # cleaned_df = get_dataframe(session_id, value,0)
        #     # cleaned_df = latlong(cleaned_df)
        #     # cleaned_df = cleaned_df[cleaned_df['lat'].isin(lat)]
        #     # cleaned_df = cleaned_df[cleaned_df['lng'].isin(lon)]
        #     cleaned_df = cleaned_df[cleaned_df['variable_1_name'].isin(name)]
        #     # cleaned_df = cleaned_df[cleaned_df['date']>=start_date]
        #     # cleaned_df = cleaned_df[cleaned_df['date']<=end_date]
        #     # print(len(cleaned_df))
        #     # condition = {
        #     # "start_station_name" : { "$in": name },
        #     # }
        #     # clusters_df = ai(latlong(file_work(download_data('boosterpack_test',value,condition))),n_clicks)
        #     # download_gridfs(sessionid,value)
        #     # init_path = "users"
        #     # filepath = os.path.join(init_path,sessionid,"temp.csv")
        #     # df = pd.read_csv(filepath)

        #     clusters_df = ai(latlong(cleaned_df),n_clicks)

        #     new_df.to_csv('selected_polygon.csv')
        #     url = "http://ai_module:5000/upload?filename=selected_polygon"
        #         # res = requests.get(url)
        #     with open('selected_polygon.csv', 'rb') as f:
        #         requests.post(url, data=f)

        #     url = f"http://ai_module:5000/?filename=selected_polygon&predict={num_predict}"
        #     res = requests.get(url)
        #     # dictFromServer = res.json()
        #     # message = 'message'
            
        #     pred_list = res.text.message
        #     pred_list = [item for sublist in pred_list for item in sublist]

        #     combined = new_df['variable_1'].append(pred_list)
        #     combo_df = pd.DataFrame(combined)
        #     fig2 = px.line(new_df,y="variable_1",hover_data=['variable_1','variable_1_name'], color='variable_1', height=400, orientation='h')
        #     fig2.update_layout(legend_orientation="h")
        #     fig2.add_trace(px.line(combo_df,x='variable_1'))
        #     fig2.update_layout(margin={"r":5,"t":10,"l":5,"b":10})
        #     # fig2.update_layout(paper_bgcolor = 'rgba(0,0,0,0)')
        #     # fig2.update_layout(plot_bgcolor = 'rgba(0,0,0,0)')


        #     # fig = px.scatter_mapbox(clusters_df, lat="lat", lon="lng", hover_name="variable_1_name", hover_data=["labels"],
        #     #                 color="labels", zoom=9, height=800, color_continuous_scale='sunsetdark')    
        #     # fig.update_layout(mapbox_style="carto-darkmatter")
        #     # fig.update_layout(legend_orientation="h")
        #     # fig.update_layout(paper_bgcolor = 'rgba(0,0,0,0)')
        #     # fig.update_layout(plot_bgcolor = 'rgba(0,0,0,0)')
        #     # fig.update_layout(margin={"r":5,"t":10,"l":5,"b":10})
        #     # fig.update_layout(legend={
        #     #                         'yanchor':"bottom",
        #     #                         'y':0.99,
        #     #                         'xanchor':"left",
        #     #                         'x':0.01,
        #     #                     })
            text = "AI prediction Complete!"
            return fig2, html.Div(text,id="loading-output-1", style={'textAlign':'center'}),""
        raise PreventUpdate

# if __name__ == '__main__':
#     app.run_server('0.0.0.0',debug=True)