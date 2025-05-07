
import pickle

from sklearn.ensemble import RandomForestRegressor





with open("../delay_data/norwich_to_london.pickle", "rb") as file:
    rf_regressor = pickle.load(file)
    
