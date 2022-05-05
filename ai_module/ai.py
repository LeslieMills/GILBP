import numpy as np
from numpy.polynomial.polynomial import polyval
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import LSTM
import math
from sklearn.metrics import mean_squared_error
from numpy import array
import seaborn as sns
import time
import datetime

# def ai(df, flag):
#     df2 = df.groupby(['lat','lng','variable_1_name'])['variable_1'].count()
#     df2 = df2.reset_index()
#     if flag%2 == 1:
#         X = df2.drop('variable_1_name', axis=1)
#     else:
#         X = df2.drop(['lat','lng','variable_1_name'], axis = 1)
    
#     X_scaled = MinMaxScaler().fit_transform(X)
#     kmeans = KMeans(n_clusters=5, random_state=0).fit(X_scaled)
#     kmeans.labels_
#     label_list = list(kmeans.labels_)
#     df2['labels'] = label_list
#     return df2

# convert an array of values into a dataset matrix for training the LSTM algorithm
def create_dataset(dataset, time_step):
	dataX, dataY = [], []
	for i in range(int(len(dataset))-time_step-1):
		a = dataset[i:(i+time_step), 0]   ###i=0, 0,1,2,3-----99   100 
		dataX.append(a)
		dataY.append(dataset[i + time_step, 0])
	return np.array(dataX), np.array(dataY)
    
#this function receives a single column dataframe and use its values to predict a number of values into the future.  
# It receives also the percentage of training data and the number of previous points used to predict one value in the future
#the function returns a new dataframe with the extra predicted values and returns the testing accuracy
def  predict_future_values(df, history_length, number_of_future_values, training_percentage, extrapolation_range):
  print(len(df))
  #length of data should be greater or equal to history_length
  if(len(df)< history_length):
     return 0
  # now we determine the minimum and maximum value of the data
  data_min=df.min()
  data_max=df.max()
  data_range=data_max-data_min
  #now we adjust the minimum value of the scaler given the predicted extrapolation_range
  data_min=data_min-extrapolation_range*data_range
  data_max=data_max+extrapolation_range*data_range
  #first we scale the data using the extrapolated minimum and maximum values
  scaler=MinMaxScaler(feature_range=(0,1))
  scaler.data_min=data_min
  scaler.data_max=data_max
  df1=scaler.fit_transform(np.array(df).reshape(-1,1))
  ##splitting dataset into train and test split
  training_size=int(len(df1)*training_percentage)
  test_size=len(df1)-training_size
  train_data,test_data=df1[0:training_size,:],df1[training_size:len(df1),:1]
  #create the training set
  time_step = history_length
  X_train, y_train = create_dataset(train_data, time_step)
  if time_step >= test_size:
    time_step = test_size -2
  X_test, ytest = create_dataset(test_data, time_step)
  # reshape input to be [samples, time steps, features] as required for LSTM
  X_train =X_train.reshape(X_train.shape[0],X_train.shape[1] , 1)
  X_test = X_test.reshape(X_test.shape[0],X_test.shape[1] , 1)
  #create the LSTM Machine learning model and carry out the training
  model=Sequential()
  model.add(LSTM(50,activation='relu', return_sequences=True,input_shape=(history_length,1)))
  model.add(LSTM(50, activation='relu'))
  model.add(Dense(1))
  model.compile(optimizer='adam', loss='mean_squared_error')
  model.fit(X_train,y_train, epochs=200, verbose=1)
  #now we evaluate the accuracy of the model
  ### Lets Do the prediction and check performance metrics
  train_predict=model.predict(X_train)
  test_predict=model.predict(X_test)
  ##Transform back to original form
  train_predict=scaler.inverse_transform(train_predict)
  test_predict=scaler.inverse_transform(test_predict)
  ### Calculate RMSE performance metrics
  training_error=math.sqrt(mean_squared_error(y_train,train_predict))
  testing_error=math.sqrt(mean_squared_error(ytest,test_predict))
  #now that we have the model, we move to predict the required values
  #get the last history values
  data_length=len(test_data)
  x_input=test_data[(data_length-time_step):].reshape(1,-1)
  temp_input=list(x_input)
  temp_input=temp_input[0].tolist()
  # demonstrate prediction for next required future values
  lst_output=[]  #list of output values
  n_steps=time_step
  i=0
  while(i<number_of_future_values):
    if(len(temp_input)>n_steps):
        x_input=np.array(temp_input[1:])
        x_input=x_input.reshape(1,-1)
        x_input = x_input.reshape((1, n_steps, 1))
        yhat = model.predict(x_input, verbose=0)
        temp_input.extend(yhat[0].tolist())
        temp_input=temp_input[1:]
        lst_output.extend(yhat.tolist())
        i=i+1
    else:
        x_input = x_input.reshape((1, n_steps,1))
        yhat = model.predict(x_input, verbose=0)
        print(x_input)
        print(yhat)
        temp_input.extend(yhat[0].tolist())
        lst_output.extend(yhat.tolist())
        i=i+1
  #we now invert the scale of the output part
  predicted_data=scaler.inverse_transform(lst_output).tolist()
  predicted_data = [x[0] for x in predicted_data]
  return predicted_data