
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

from delay_prediction_training import calculate_delay, encode_user_data, one_hot_encode

import warnings
warnings.filterwarnings('ignore')

with open("../delay_data/london_to_norwich.pickle", "rb") as file:
    rf_regressor = pickle.load(file)

def find_remaining_delays(data):
    delays = {}
    encoded_data = encode_user_data(data)
    while encoded_data:
        ready_to_predict = one_hot_encode(pd.DataFrame([encoded_data]))
        predicted_delay = rf_regressor.predict(ready_to_predict)[0]
        delays[encoded_data["next_stop"]] = round(predicted_delay, 1)
        encoded_data = encode_user_data({
            "current_stop": encoded_data["next_stop"],
            "time": data["time"],
            "to_nrw": data["to_nrw"],
            "current_delay": predicted_delay
        })
    return delays

if __name__ == "__main__":
    data = {
        "current_stop": "SRA",
        "time": DateTime(hour=15, minute=30),
        "to_nrw": True,
        "current_delay": 2
    }
    find_remaining_delays(data)