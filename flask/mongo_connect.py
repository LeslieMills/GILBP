import os
from pymongo import MongoClient
import gridfs

def dbInsertFile(filename, upload_directory):
    connString = os.environ['MONGODB_CONNSTRING']
    client = MongoClient(host="mongo",port=27017,username='root',password='pass',authSource='admin')
    db = client[upload_directory]
    fs = gridfs.GridFS(db)
    init_path = "users"
    filepath = os.path.join(init_path,upload_directory,filename)
    fileID = fs.put(open(filepath, 'rb'))
    return fileID

def download_gridfs(database, fileID,condition):
    connString = os.environ['MONGODB_CONNSTRING']
    client = MongoClient(host="mongo",port=27017,username='root',password='pass',authSource='admin')
    db = client[database]
    fs = gridfs.GridFS(db)
    init_path = "users"
    filepath = os.path.join(init_path,database,"temp.csv")
    with open(filepath,'wb') as gridread:
        gridread.write(fs.get(fileID).read())