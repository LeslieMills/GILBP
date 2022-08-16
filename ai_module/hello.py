from flask import Flask, jsonify, request, Request
import requests
import pandas as pd
import werkzeug
from ai import predict_future_values, create_dataset

app = Flask(__name__)

@app.route('/')
def hello_world():
    filename = request.args.get('filename')
    num_predict = request.args.get('predict')
    df = pd.read_csv(filename+'.csv')
    df = pd.DataFrame(df['variable_1'])
    pred_df = predict_future_values(df,len(df)//2,int(num_predict),0.8,0.2)
    return jsonify({'message': pred_df})

@app.route("/upload", methods=['POST'])
def upload_file():
    filename = request.args.get('filename')+'.csv'
    from werkzeug.datastructures import FileStorage
    FileStorage(request.stream).save(filename)
    return 'OK', 200


if __name__=='__main__':
    app.run(debug=True, host='0.0.0.0',port='5000')