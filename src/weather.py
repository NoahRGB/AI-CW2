import openmeteo_requests

from date_time import DateTime

station_code = "NRW"
current_time = DateTime(hour=15, minute=32, day=21, month=5, year=2025)

current_time.round_to_nearest_hour()

