from dash import dcc, html
import dash_uploader as du
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
from database_download import download_gridfs
from database_upload import dbInsertFile, delete_file, delete_database, create_demo_file, delete_working_files
# from app import app, cache
from app import app
from index import Users
from flask_login import login_user
from werkzeug.security import check_password_hash
import requests
import plotly.express as px
import os
from ai import ai
from layouts import main_layout, login_layout, login_failed,logout
from flask_login import login_user, logout_user, current_user, LoginManager, UserMixin
from bson import ObjectId

# def get_dataframe(session_id,value,flag):
#     download_gridfs(session_id, value)

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
#         cleaned_df = file_work(df)
#         cleaned_df.reset_index(inplace=True)
#         return cleaned_df.to_json(default_handler=str, orient="records", lines=True)
#     df = pd.DataFrame([])
#     i = 1
#     for chunk in pd.read_json(query_and_serialize_data(session_id),orient="records",lines=True,chunksize=10000,nrows=20000000):
#         print(i)
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

@app.callback(
    Output('url', 'pathname'),
    Output('session-id','data'),
    Output('file-id','data'), 
    Input('login-button', 'n_clicks'),
    State('uname-box', 'value'), 
    State('pwd-box', 'value'),
    prevent_initial_call=True)
def successful(n_clicks, input1, input2):
    user = Users.query.filter_by(username=input1).first()
    if user is not None:
        if check_password_hash(user.password, input2):
            login_user(user)
            print(input1+" is logged in!")
            delete_database(input1)
            delete_working_files(input1)
            print("existing database and working files of {} cleaned!".format(input1))
            create_demo_file("202004-divvy-tripdata.csv",input1)
            fileID = dbInsertFile("202004-divvy-tripdata.csv",input1)
            download_gridfs(input1, fileID)
            print("Demo file uploaded to MongoDB and working file created")
            # print("entered here too")
            # url = "http://ai_module:5000/"
            # res = requests.get(url)
            # dictFromServer = res.json()
            # print(dictFromServer['message'])
            return "/success", input1, str(fileID)
        else:
            raise PreventUpdate
    else:
        raise PreventUpdate

@app.callback(
    Output('output-state', 'children')
    , [Input('login-button', 'n_clicks')]
    , [State('uname-box', 'value'), State('pwd-box', 'value')],
                prevent_initial_call=True)
def update_output(n_clicks, input1, input2):
    # print(n_clicks)
    if n_clicks > 0:
        user = Users.query.filter_by(username=input1).first()
        if user:
            if check_password_hash(user.password, input2):
                return ''
            else:
                return 'Incorrect password'
        else:
            return 'Incorrect username'
    else:
        return ''

# @app.callback(
#     Output('url', 'pathname')
#     , [Input('back-button', 'n_clicks')],
#                 prevent_initial_call=True)
# def logout_dashboard(n_clicks):
#     if n_clicks > 0:
#         return '/'

# @app.callback(
#     Output('url_login_df', 'pathname')
#     , [Input('back-button', 'n_clicks')],
#                 prevent_initial_call=True)
# def logout_dashboard(n_clicks):
#     if n_clicks > 0:
#         return '/'

# @app.callback(
#     Output('url', 'pathname')
#     , [Input('back-button', 'n_clicks')],
#                 prevent_initial_call=True)
# def logout_dashboard(n_clicks):
#     if n_clicks > 0:
#         return '/'

@app.callback(
    Output('dd-output-container', 'children'),
    Input('dynamic-dropdown', 'value'),
    Input('file-id','data'),
    prevent_initial_call=True
)
def dropdown_output(value,fileID):
    print(fileID)
    return 'You have selected "{}"! Click load to continue'.format(value)

@app.callback( Output('initiate','n_clicks'),
                Output('my-date-picker-range', 'min_date_allowed'),
                Output('my-date-picker-range', 'max_date_allowed'),
                Output('my-date-picker-range','start_date'),
                Output('my-date-picker-range','end_date'),
                Output('my-date-picker-range','initial_visible_month'),
                Output('loading-1','children'),
                Output('analyze', 'hidden'),
                Output('map','selectedData'),
                State('dynamic-dropdown', 'value'),
                Input('initiate','n_clicks'),
                Input('session-id', 'data'),
                Input('file-id','data'),
                Input('file-id2','data'),
                prevent_initial_call=True)
def initiate_page(value, n_clicks,session_id,fileID,fileID2):
    # if fileID2 != "":
    #     print("enters here")
    #     fileID = fileID2
    if value == "202004-divvy-tripdata" or fileID2 == "":
        print("This is printed" + fileID2)
        fileID = ObjectId(fileID)
    else:
        print("That is printed")
        fileID = ObjectId(fileID2)
    if value is not None:
        if n_clicks >= 1:
            flag = 1
            path = os.path.join(session_id,'temp.csv')
            cleaned_df = pd.read_csv(path)
            # cleaned_df = get_dataframe(session_id, fileID, flag)     
            min_date, max_date = date_minmax(cleaned_df)
            cleaned_df = latlong(cleaned_df)
            text = "Loading complete!"
            return 0,min_date,max_date,min_date,max_date,min_date, html.Div(text,id="loading-output-1", style={'textAlign':'center'}),False, None
    raise PreventUpdate

@app.callback(
    Output('output-container-date-picker-range', 'children'),
    Output('output-container-max-date-range','children'),
    Output('map', 'figure'),
    Output('loading-5','children'),
    Output('map_placeholder','children'),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date'),
    State('my-date-picker-range', 'min_date_allowed'),
    State('my-date-picker-range', 'max_date_allowed'),
    State('session-id', 'data'),
    State('dynamic-dropdown', 'value'),
    prevent_initial_call=True
    )
def update_output(start_date, end_date, min_date, max_date,session_id,value):
    # cleaned_df = get_dataframe(session_id, value,0)
    path = os.path.join(session_id,'temp.csv')
    cleaned_df = pd.read_csv(path)

    cleaned_df = latlong(cleaned_df)
    map_df = cleaned_df[cleaned_df['date']>=start_date]
    map_df = map_df[map_df['date']<=end_date]
    fig = px.scatter_mapbox(map_df, lat="lat", lon="lng", hover_name="variable_1_name", hover_data=["variable_1"],
                    color="variable_1", zoom=9, height=800, animation_frame="date", animation_group="variable_1_name", size = 'variable_1',
                    color_continuous_scale='sunsetdark')    
    fig.update_layout(mapbox_style="carto-darkmatter")
    fig.update_layout(legend_orientation="h")
    fig.update_layout(margin={"r":5,"t":10,"l":5,"b":10})
    fig.update_layout(paper_bgcolor = 'rgba(0,0,0,0)')
    fig.update_layout(plot_bgcolor = 'rgba(0,0,0,0)')

    date_range = f"Selected Date Range: {start_date.split('T')[0]} to {end_date.split('T')[0]}"
    max_range = f"Max. Date Range: {min_date.split('T')[0]} to {max_date.split('T')[0]}"
    text = ""
    return date_range, max_range, fig, text, text
      
@app.callback(Output('download-dataframe-csv', 'data'),
                Output('btn_csv', "n_clicks"),
                State('my-date-picker-range', 'start_date'),
                State('my-date-picker-range', 'end_date'),
                Input("btn_csv", "n_clicks"),
                State('session-id', 'data'),
                State('dynamic-dropdown', 'value'),
                prevent_initial_call=True)
def download(start_date, end_date, n_clicks,session_id,value):
    if n_clicks == 1:
        path = os.path.join(session_id,'temp.csv')
        cleaned_df = pd.read_csv(path)
        # cleaned_df = get_dataframe(session_id, value,0)
        cleaned_df = latlong(cleaned_df)
        download_df = cleaned_df[cleaned_df['date']>=start_date]
        download_df = download_df[download_df['date']<=end_date]
        return dcc.send_data_frame(download_df.to_csv, "mydf.csv", index=False),0
    else:
        raise PreventUpdate

@app.callback(Output('graph', 'figure'),
                Output('loading-4','children'),
                Output('graph_placeholder','children'),
                Input("map", "clickData"),
                State('my-date-picker-range', 'start_date'),
                State('my-date-picker-range', 'end_date'),
                State('session-id', 'data'),
                State('dynamic-dropdown', 'value'),
                prevent_initial_call=True)
def on_click(clickdata,start_date, end_date,session_id,value):
    path = os.path.join(session_id,'temp.csv')
    cleaned_df = pd.read_csv(path)
    # cleaned_df = get_dataframe(session_id, fileID, flag)     

    # cleaned_df = get_dataframe(session_id, value,0)
    cleaned_df = latlong(cleaned_df)
    graph_df = cleaned_df[cleaned_df['date']>=start_date]
    graph_df = graph_df[graph_df['date']<=end_date]
    graph_df = graph_df[graph_df['variable_1_name']==clickdata['points'][0]['id']]
    fig2 = px.bar(graph_df,x="variable_1",y='date',hover_data=['variable_1','variable_1_name'], color='variable_1',labels={'pop': 'variable_1_name'}, height=800, orientation='h')
    fig2.update_layout(legend_orientation="h")
    fig2.update_layout(
            yaxis={
               'tickformat': '%Y-%m-%d',
                'tickmode': 'auto',
                'tick0':pd.to_datetime(start_date),
                'dtick':86400000
            })
    fig2.update_layout(margin={"r":5,"t":10,"l":5,"b":10})
    fig2.update_layout(paper_bgcolor = 'rgba(0,0,0,0)')
    fig2.update_layout(plot_bgcolor = 'rgba(0,0,0,0)')
    text = ""   
    return fig2, text, text

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
                print("deleted last file from options")
                file = x['value']+".csv"
                file_path = os.path.join("users",sessionid,file)
                os.remove(file_path)
                print("deleted last file from memory")
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
            print("upload and fileID swap complete")
        return options[sessionid], str(fileID2)
    raise PreventUpdate

@app.callback(  Output('cluster','figure'),
                Output('loading-2','children'),
                Output('postAI_placeholder','children'),
                Input('analyze', 'n_clicks'),
                State('map','selectedData'),
                State('dynamic-dropdown', 'value'),
                State('session-id', 'data'),
                State('my-date-picker-range', 'start_date'),
                State('my-date-picker-range', 'end_date'),
                prevent_initial_call=True)
def on_analyze(n_clicks,selectedData,value,session_id,start_date,end_date):
    if n_clicks >= 1 and selectedData is not None:
        lat = []
        lon = []
        name = []
        variable = []
        for point in selectedData['points']:
            lat.append(point['lat'])
            lon.append(point['lon'])
            name.append(point['id'])
            variable.append(point['customdata'][0])
            # new_df = pd.DataFrame(list(zip(lat,lon,name,variable)),columns=['lat','lng','variable_1_name','variable_1'])
        path = os.path.join(session_id,'temp.csv')
        cleaned_df = pd.read_csv(path)
        # cleaned_df = get_dataframe(session_id, fileID, flag)     

        # cleaned_df = get_dataframe(session_id, value,0)
        cleaned_df = latlong(cleaned_df)
        # cleaned_df = cleaned_df[cleaned_df['lat'].isin(lat)]
        # cleaned_df = cleaned_df[cleaned_df['lng'].isin(lon)]
        cleaned_df = cleaned_df[cleaned_df['variable_1_name'].isin(name)]
        cleaned_df = cleaned_df[cleaned_df['date']>=start_date]
        cleaned_df = cleaned_df[cleaned_df['date']<=end_date]
        print(len(cleaned_df))
        # condition = {
        # "start_station_name" : { "$in": name },
        # }
        # clusters_df = ai(latlong(file_work(download_data('boosterpack_test',value,condition))),n_clicks)
        # download_gridfs(sessionid,value)
        # init_path = "users"
        # filepath = os.path.join(init_path,sessionid,"temp.csv")
        # df = pd.read_csv(filepath)

        clusters_df = ai(latlong(cleaned_df),n_clicks)

        fig = px.scatter_mapbox(clusters_df, lat="lat", lon="lng", hover_name="variable_1_name", hover_data=["labels"],
                        color="labels", zoom=9, height=800, color_continuous_scale='sunsetdark')    
        fig.update_layout(mapbox_style="carto-darkmatter")
        fig.update_layout(legend_orientation="h")
        fig.update_layout(paper_bgcolor = 'rgba(0,0,0,0)')
        fig.update_layout(plot_bgcolor = 'rgba(0,0,0,0)')
        fig.update_layout(margin={"r":5,"t":10,"l":5,"b":10})
        fig.update_layout(legend={
                                'yanchor':"bottom",
                                'y':0.99,
                                'xanchor':"left",
                                'x':0.01,
                            })
        text = "Analysis Complete!"
        return fig, html.Div(text,id="loading-output-1", style={'textAlign':'center'}),""
    raise PreventUpdate

