
# for part 2

# given the current time of a train at any station, predict
# the arrival/departure time of this train at the next stop
# and all the following stops

# and the arrival/departure times of all other trains that
# may be affected by this train

from date_time import DateTime
import pandas as pd
import math

import numpy as np

import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler

import warnings
warnings.filterwarnings('ignore')

data = pd.read_csv("./delay_data/2022_service_details_Norwich_to_London.csv", parse_dates=["planned_arrival_time", "planned_departure_time", "actual_arrival_time", "actual_departure_time", "date_of_service"], dayfirst=True)
data = pd.read_csv("./delay_data/test_data.csv", parse_dates=["planned_arrival_time", "planned_departure_time", "actual_arrival_time", "actual_departure_time", "date_of_service"], dayfirst=True)

# data["delay"] = (data["actual_arrival_time"] - data["planned_arrival_time"]).dt.total_seconds() / 60


def calculate_delay(time1, time2):
    # takes 2 pandas datetime objects and calculates the difference between them
    # will return None if one or both of the times is NaT
    if not pd.notna(time1) or not pd.notna(time2):
        return None
    return (time1 - time2).total_seconds() / 60

training_data = []
for _, group in data.groupby("rid"):
    for i in range(0, len(group) - 1):
        current_stop = group.iloc[i]
        next_stop = group.iloc[i + 1]
        
        # find the delays for the current stop and the next stop (the target feature)
        current_stop_delay = calculate_delay(current_stop["actual_arrival_time"], current_stop["planned_arrival_time"])
        next_stop_delay = calculate_delay(next_stop["actual_arrival_time"], next_stop["planned_arrival_time"])
        
        # find the day of the week and the time of day     
        current_day = current_stop["date_of_service"].dayofweek
        if pd.notna(current_stop["planned_arrival_time"]):
            current_time = current_stop["planned_arrival_time"].hour * 60 + current_stop["planned_arrival_time"].minute
        else:    
            current_time = current_stop["planned_departure_time"].hour * 60 + current_stop["planned_departure_time"].minute
            
        if current_stop_delay and next_stop_delay:
            training_data.append({
                "current_stop": current_stop["location"],
                "next_stop": next_stop["location"],
                "time": current_time,
                "day": current_day,
                "current_delay": current_stop_delay,
                "target_delay": next_stop_delay
            })

training_data = pd.DataFrame(training_data)

X = training_data[["current_stop", "next_stop", "time", "day", "current_delay"]]
y = training_data["target_delay"]

encoder = LabelEncoder()
encoder = encoder.fit([*X["next_stop"], *X["current_stop"]])
X["current_stop"] = encoder.transform(X["current_stop"])
X["next_stop"] = encoder.transform(X["next_stop"])

scaler = StandardScaler()
X = scaler.fit_transform(X)

print(X[:5], y[:5])
print("Prepared all data")

model = models.Sequential([
    layers.Dense(64, activation="relu", input_shape=(X.shape[1],)),
    layers.Dense(32, activation="relu"),
    layers.Dense(1)
])

model.compile(optimizer="adam", loss="mse", metrics=["mae"])
# model.fit(X[:5], y[:5], epochs=10, batch_size=32, validation_split=0.2)
model.fit(X, y, epochs=10, batch_size=32, validation_split=0.2)

# doesn't work properly yet