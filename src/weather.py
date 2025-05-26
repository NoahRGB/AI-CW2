import json

import requests_cache
from retry_requests import retry
import openmeteo_requests

import pandas as pd

from date_time import DateTime

def get_weather_code(station_code, time):

    with open("../delay_data/train_station_coordinates.json") as file:
        station_coords = json.load(file)

    if station_code in station_coords:
        
        time.round_to_nearest_hour()

        cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
        retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
        openmeteo = openmeteo_requests.Client(session = retry_session)

        url = "https://archive-api.open-meteo.com/v1/archive"

        params = {
            "latitude": station_coords[station_code]["latitude"],
            "longitude": station_coords[station_code]["longitude"],
            "start_date": f"{time.get_year()}-{time.get_month()}-{time.get_day()}",
            "end_date": f"{time.get_year()}-{time.get_month()}-{time.get_day()}",
            "hourly": "weather_code"
        }

        responses = openmeteo.weather_api(url, params=params)
        
        if len(responses) > 0:
            response = responses[0]

            hourly = response.Hourly()
            hourly_weather_code = hourly.Variables(0).ValuesAsNumpy()
            
            weather_code = hourly_weather_code[int(time.get_hour())]
            return weather_code
        return None
        
if __name__ == "__main__":
    station_code = "NRW"
    current_time = DateTime(hour=14, minute=30, day=25, month=5, year=2020)

    print(get_weather_code(station_code, current_time))