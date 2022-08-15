import os
from pymongo import MongoClient
import gridfs

def download_gridfs(database, fileID):
    client = MongoClient(host="mongo",port=27017,username='root',password='pass',authSource='admin')
    # client = MongoClient()
    db = client[database]
    fs = gridfs.GridFS(db)
    init_path = "users"
    filepath = os.path.join(init_path,database,"temp.csv")
    with open(filepath,'wb') as gridread:
        gridread.write(fs.get(fileID).read())