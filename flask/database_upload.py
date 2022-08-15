import os
from pymongo import MongoClient
import gridfs
from shutil import copy, rmtree

def dbInsertFile(filename, upload_directory):
    client = MongoClient(host="mongo",port=27017,username='root',password='pass',authSource='admin')
    # client = MongoClient()
    db = client[upload_directory]
    fs = gridfs.GridFS(db)
    init_path = "users"
    filepath = os.path.join(init_path,upload_directory,filename)
    fileID = fs.put(open(filepath, 'rb'))
    return fileID

def delete_file(fileID,upload_directory):
    client = MongoClient(host="mongo",port=27017,username='root',password='pass',authSource='admin')
    # client = MongoClient()
    db = client[upload_directory]
    fs = gridfs.GridFS(db)
    fs.delete(fileID)

def delete_database(upload_directory):
    client = MongoClient(host="mongo",port=27017,username='root',password='pass',authSource='admin')
    # client = MongoClient()
    client.drop_database(upload_directory)

# Function to create a demp file. This function creates a directory for the logged in user, 
# then finds the demp file which is part of the directory and copies the demo file into the newly
# created folder
def create_demo_file(filename, upload_directory):
    # create a path variable
    init_path = "users"
    # create a directory path
    dirpath = os.path.join(init_path,upload_directory)
    # craete directory if it doesn't exist
    os.makedirs(dirpath, exist_ok=True)
    # copy the file in the directory path specified
    copy(filename, dirpath)

def delete_working_files(user_directory):
    dirpath = os.path.join("users",user_directory)
    rmtree(dirpath,ignore_errors=True)