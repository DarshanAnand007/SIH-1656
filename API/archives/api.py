import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import pytz

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Update coordinates for Visakhapatnam Beach
url = "https://marine-api.open-meteo.com/v1/marine"
params = {
    "latitude": 17.6868,  # Latitude for Visakhapatnam Beach
    "longitude": 83.2185,  # Longitude for Visakhapatnam Beach
    "hourly": ["wave_height", "wave_direction", "wind_wave_height", "wind_wave_direction",
               "swell_wave_height", "swell_wave_direction", "ocean_current_velocity", "ocean_current_direction"],
    "models": "best_match"
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print("Location: Visakhapatnam Beach")  # Adding a hardcoded title
print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation {response.Elevation()} m asl")
print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_wave_height = hourly.Variables(0).ValuesAsNumpy()
hourly_wave_direction = hourly.Variables(1).ValuesAsNumpy()
hourly_wind_wave_height = hourly.Variables(2).ValuesAsNumpy()
hourly_wind_wave_direction = hourly.Variables(3).ValuesAsNumpy()
hourly_swell_wave_height = hourly.Variables(4).ValuesAsNumpy()
hourly_swell_wave_direction = hourly.Variables(5).ValuesAsNumpy()
hourly_ocean_current_velocity = hourly.Variables(6).ValuesAsNumpy()
hourly_ocean_current_direction = hourly.Variables(7).ValuesAsNumpy()

# Convert the UTC timestamps to the desired timezone (e.g., Asia/Kolkata for Visakhapatnam)
utc_times = pd.to_datetime(hourly.Time(), unit="s", utc=True)
local_times = utc_times.tz_convert('Asia/Kolkata')

hourly_data = {
    "date": local_times,  # Use the converted local times here
    "wave_height": hourly_wave_height,
    "wave_direction": hourly_wave_direction,
    "wind_wave_height": hourly_wind_wave_height,
    "wind_wave_direction": hourly_wind_wave_direction,
    "swell_wave_height": hourly_swell_wave_height,
    "swell_wave_direction": hourly_swell_wave_direction,
    "ocean_current_velocity": hourly_ocean_current_velocity,
    "ocean_current_direction": hourly_ocean_current_direction
}

hourly_dataframe = pd.DataFrame(data=hourly_data)

# Add the title as part of the DataFrame output
print("\nWeather Data for Visakhapatnam Beach:")
print(hourly_dataframe)
