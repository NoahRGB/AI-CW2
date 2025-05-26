import json
import pickle

import requests_cache
from retry_requests import retry
import openmeteo_requests

import pandas as pd

from date_time import DateTime

def get_weather_at(station_code, date, time):
    with open("../delay_data/train_station_coordinates.json") as file:
        station_coords = json.load(file)

    if station_code in station_coords:
        
        time.round_to_nearest_hour()

        cache_session = requests_cache.CachedSession(".cache", expire_after = -1)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        openmeteo = openmeteo_requests.Client(session = retry_session)

        url = "https://archive-api.open-meteo.com/v1/archive"

        params = {
            "latitude": station_coords[station_code]["latitude"],
            "longitude": station_coords[station_code]["longitude"],
            "start_date": f"{date.get_year()}-{date.get_month()}-{date.get_day()}",
            "end_date": f"{date.get_year()}-{date.get_month()}-{date.get_day()}",
            "hourly": "precipitation",
        }

        responses = openmeteo.weather_api(url, params=params)
        
        if len(responses) > 0:
            response = responses[0]
            
            hourly = response.Hourly()
            hourly_weather_code = hourly.Variables(0).ValuesAsNumpy()
            
            weather_code = hourly_weather_code[int(time.get_hour())]
            return weather_code
                
    return None

def save_weather_dict(station_code):
    
    weather_dict = {}

    with open("../delay_data/train_station_coordinates.json") as file:
        station_coords = json.load(file)

    if station_code in station_coords:

        cache_session = requests_cache.CachedSession(".cache", expire_after = -1)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        openmeteo = openmeteo_requests.Client(session = retry_session)

        url = "https://archive-api.open-meteo.com/v1/archive"

        params = {
            "latitude": station_coords[station_code]["latitude"],
            "longitude": station_coords[station_code]["longitude"],
            "start_date": "2020-12-31",
            "end_date": "2025-01-01",
            "hourly": "precipitation",
        }

        responses = openmeteo.weather_api(url, params=params)
        
        if len(responses) > 0:
            response = responses[0]

            daily = response.Daily()
            hourly = response.Hourly().Variables(0)
            hourly_count = hourly.ValuesLength()
            
            
            current_date = DateTime(day=31, month=12, year=2020)
            current_hourly_count = 0
            current_hourly_list = []
            
            for i in range(0,hourly_count ):
                print(f"Done {i} / {hourly_count}")
                current_hourly_count += 1
                
                current_hourly_list.append(hourly.Values(i))
                
                if current_hourly_count == 24:
                    weather_dict[current_date.get_date()] = current_hourly_list
                    current_hourly_list = []
                    current_hourly_count = 0
                    current_date.increment_day()
            
            return weather_dict
            # with open(f"../weather_data/{station_code}_weather.pickle", "wb") as file:
            #     pickle.dump(weather_dict, file)
                
        return None
       
        
if __name__ == "__main__":
    # station_codes = ["MNG", "MKT", "SNF", "LST", "SMK", "CHM", "SRA", "DIS", "INT", "IPS", "NRW", "COL", "WTM"]
    # all_station_weather = {}
    
    # for code in station_codes:
    #     station_weather_dict = save_weather_dict(code)
    #     all_station_weather[code] = station_weather_dict
    
    # with open(f"../weather_data/all_stations_weather_precipitation.pickle", "wb") as file:
    #     pickle.dump(all_station_weather, file)
    
    code = "NRW"
    date = DateTime(day=1, month=1, year=2025)
    time = DateTime(hour=12, minute=0)
    print(get_weather_at(code, date, time))