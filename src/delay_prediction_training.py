
# for part 2

# given the current time of a train at any station, predict
# the arrival/departure time of this train at the next stop
# and all the following stops

# and the arrival/departure times of all other trains that
# may be affected by this train

from date_time import DateTime
import pandas as pd
import math

import pickle

import numpy as np

import matplotlib.pyplot as plt

import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping

from sklearn import neighbors
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

import warnings
warnings.filterwarnings('ignore')

SEED = 0 # for any randomness


norwich_to_london = ["NRW", "DIS", "SMK", "IPS", "MNG", "COL", "CHM", "SRA", "LST"]
london_to_norwich = ["LST", "SRA", "CHM", "COL", "MNG", "IPS", "SMK", "DIS", "NRW"]


def calculate_delay(time1, time2):
    # takes 2 pandas datetime objects and calculates the difference between them
    # will return None if one or both of the times is NaT
    if not pd.notna(time1) or not pd.notna(time2):
        return None
    return (time1 - time2).total_seconds() / 60

def encode_user_data(data):
    encoded_data = {}
    data = pd.DataFrame([data]).iloc[0]

    encoded_data["current_delay"] = data["current_delay"]

    hour = int(data["time"].get_hour())
    minute = int(data["time"].get_min())
    encoded_data["sin_time"] = sin_time = np.sin(2 * np.pi * (hour * 60 + minute) / 1440)
    encoded_data["cos_time"] = cos_time = np.cos(2 * np.pi * (hour * 60 + minute) / 1440)
    
    direction = london_to_norwich if data["to_nrw"] else norwich_to_london

    if data["current_stop"] not in direction: return False
    encoded_data["current_stop"] = data["current_stop"]
    
    index = direction.index(data["current_stop"])
    if (index + 1) == len(direction): return False
    encoded_data["next_stop"] = direction[index + 1]
    
    return encoded_data

def one_hot_encode(X):
    categorical_columns = X.select_dtypes(include=['object']).columns.tolist() # get columns that are categorical and need to be encoded
    
    # encoder = OneHotEncoder(sparse_output=False)
    with open("../delay_data/one_hot_encoder.pickle", "rb") as file:
        encoder = pickle.load(file)
    
    one_hot_encoded = encoder.transform(X[categorical_columns])
    one_hot_df = pd.DataFrame(one_hot_encoded, columns=encoder.get_feature_names_out(categorical_columns)) # turn encoded columns into a dataframe
    X_encoded = pd.concat([X, one_hot_df], axis=1) # add new encoded columns to old dataframe
    X_encoded = X_encoded.drop(categorical_columns, axis=1) # delete the old non-encoded columns from the original dataframe
    return X_encoded

# only run the following IF this python file was directly run and not imported
# i.e. 'python delay_prediction_training.py'

if __name__ == "__main__":

    # /////////////// PREPARING DATA ////////////////////
    
    # data = pd.read_csv("../delay_data/2022_service_details_Norwich_to_London.csv", parse_dates=["planned_arrival_time", "planned_departure_time", "actual_arrival_time", "actual_departure_time", "date_of_service"], dayfirst=True)
    # data = pd.read_csv("../delay_data/all_Norwich_to_London.csv", parse_dates=["planned_arrival_time", "planned_departure_time", "actual_arrival_time", "actual_departure_time", "date_of_service"], dayfirst=True)
    # data = pd.read_csv("../delay_data/all_London_to_Norwich.csv", parse_dates=["planned_arrival_time", "planned_departure_time", "actual_arrival_time", "actual_departure_time", "date_of_service"], dayfirst=False)

    # training_data = []
    # for _, group in data.groupby("rid"): # will ensure data rows are grouped by train journey (i.e. their train id/RID)
    #     for i in range(0, len(group) - 1): # for every row of data...
            
    #         # get the current/next data rows
    #         current_stop = group.iloc[i]
    #         next_stop = group.iloc[i + 1]
            
    #         # find the delays for the current stop and the next stop (the target feature)
    #         current_stop_delay = calculate_delay(current_stop["actual_arrival_time"], current_stop["planned_arrival_time"])
    #         next_stop_delay = calculate_delay(next_stop["actual_arrival_time"], next_stop["planned_arrival_time"])
            
    #         # find the day of the week and the time of day using sin and cos so it has an understanding of how time cycles    
    #         current_day = current_stop["date_of_service"].dayofweek
    #         if pd.notna(current_stop["planned_arrival_time"]):
    #             sin_time = np.sin(2 * np.pi * (current_stop["planned_arrival_time"].hour * 60 + current_stop["planned_arrival_time"].minute) / 1440)
    #             cos_time = np.cos(2 * np.pi * (current_stop["planned_arrival_time"].hour * 60 + current_stop["planned_arrival_time"].minute) / 1440)
    #         else:
    #             sin_time = np.sin(2 * np.pi * (current_stop["planned_departure_time"].hour * 60 + current_stop["planned_departure_time"].minute) / 1440)
    #             cos_time = np.cos(2 * np.pi * (current_stop["planned_departure_time"].hour * 60 + current_stop["planned_departure_time"].minute) / 1440)
                
    #         if current_stop_delay and next_stop_delay:
    #             # add all the data as one 'training row'
    #             training_data.append({
    #                 "current_stop": current_stop["location"],
    #                 "next_stop": next_stop["location"],
    #                 "sin_time": sin_time,
    #                 "cos_time": cos_time,
    #                 "day": current_day,
    #                 "current_delay": current_stop_delay,
    #                 "target_delay": next_stop_delay
    #             })
    # training_data = pd.DataFrame(training_data)
    


    # # remove outliers since the data is full of them and it heavily impacts results
    # training_data["current_delay"] = training_data["current_delay"].clip(lower=-30, upper=120)
    # training_data["target_delay"] = training_data["target_delay"].clip(lower=-30, upper=120)

    # # pick the training features and target features that will be used from the training data
    # X = training_data[["current_delay", "sin_time", "cos_time", "current_stop", "next_stop"]]
    # y = training_data["target_delay"]

    # # encode categorical data using one hot encoding
    # X = one_hot_encode(X)
    
    # print(X)
    
    # with open("../delay_data/nrw_to_lst_training_data.pickle", "wb") as file:
    #     pickle.dump(X, file)
        
    # with open("../delay_data/nrw_to_lst_target_data.pickle", "wb") as file:
    #     pickle.dump(y, file)
        
    with open("../delay_data/nrw_to_lst_training_data.pickle", "rb") as file:
        X = pickle.load(file)
        
    with open("../delay_data/nrw_to_lst_target_data.pickle", "rb") as file:
        y = pickle.load(file)

    # split data into training/testing/validation
    X_train_val, X_test, y_train_val, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED)
    X_train, X_val, y_train, y_val = train_test_split(X_train_val, y_train_val, test_size=0.2, random_state=SEED)

    print("Prepared all data successfully")




    # /////////////// TRAINING MODELS & MAKING PREDICTIONS ///////////////////

    # MAE = mean absolute error
    # MSE = mean squared error


    # model = models.Sequential([
    #     layers.Dense(128, activation="relu", input_shape=(X.shape[1],)),
    #     layers.Dense(64, activation="relu"),
    #     layers.Dense(32, activation="relu"),
    #     layers.Dense(16, activation="relu"),
    #     layers.Dense(1, activation="linear")
    # ])

    # early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    # model.compile(optimizer=Adam(), loss="mse", metrics=["mae"])
    # model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=50, batch_size=32, callbacks=[early_stopping])

    # nn_predictions = model.predict(X_test)
    # nn_MAE = mean_absolute_error(y_test, nn_predictions)
    # nn_MSE = mean_squared_error(y_test, nn_predictions)



    # baseline_predictions = [y_test.mean()] * len(y_test)
    # baseline_mean_absolute_err = mean_absolute_error(y_test, baseline_predictions)
    # baseline_mean_squared_err = mean_squared_error(y_test, baseline_predictions)

    baseline_predictions = [y.mean()] * len(y)
    baseline_mean_absolute_err = mean_absolute_error(y, baseline_predictions)
    baseline_mean_squared_err = mean_squared_error(y, baseline_predictions)




    # knn = neighbors.KNeighborsRegressor(3, weights="uniform")
    # knn = knn.fit(X_train, y_train)
    # knn_predictions = knn.predict(X_test)
    # knn_MAE = mean_absolute_error(y_test, knn_predictions)

    rf = RandomForestRegressor(n_estimators=100, random_state=SEED)
    rf.fit(X, y)
    rf_predictions = rf.predict(X)
    rf_MAE = mean_absolute_error(y, rf_predictions)

    # print(f"NN MSE: {nn_MAE}")
    # print(f"NN MAE: {nn_MSE}")
    print(f"Baseline mean absolute error: {baseline_mean_absolute_err}")
    print(f"Baseline mean squared error: {baseline_mean_squared_err}")
    # print(f"KNN MAE: {knn_MAE}")
    print(f"RF MAE: {rf_MAE}")

    # with open("../delay_data/london_to_norwich.pickle", "wb") as file:
    #     pickle.dump(rf, file)

    # plt.figure(figsize=(20, 20))
    # plt.scatter(X["day"], y, color="black", label="training data", s=5)
    # plt.xlabel("Day")
    # plt.ylabel("Target delay (mins) (e.g. the next station's delay)")
    # # plt.plot(X["tar"], y, color="red", label="predicted")
    # plt.show()