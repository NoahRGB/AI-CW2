
# for part 2

# given the current time of a train at any station, predict
# the arrival/departure time of this train at the next stop
# and all the following stops

# and the arrival/departure times of all other trains that
# may be affected by this train

from date_time import DateTime
import pandas as pd
import math

data = pd.read_csv("./delay_data/2022_service_details_Norwich_to_London.csv")

for i in range(data.size-1): # for every train journey in the data
    pat = data["planned_arrival_time"][i] # planned arrival time
    aat = data["actual_arrival_time"][i] # actual arrival time
    if not (isinstance(pat, float) and math.isnan(pat)) and not (isinstance(aat, float) and math.isnan(aat)):
        # turn them into DateTime objects 
        pat = DateTime.find_valid_time(str(pat))
        aat = DateTime.find_valid_time(str(aat))
        
        # find actual arrival time - planned arrival time
        # and use that to train the neural network ?
        
        # diff represents how many minutes of delay there was between
        # the planned arrival time and the actual arrival time
        # if diff is negative, then the train arrived before it was planned to
        diff = aat - pat
        print(aat.get_time(), pat.get_time(), diff)