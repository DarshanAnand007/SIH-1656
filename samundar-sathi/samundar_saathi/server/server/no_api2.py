import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Update coordinates for Visakhapatnam Beach and specify the parameters
url = "https://marine-api.open-meteo.com/v1/marine"
params = {
    "latitude": 17.6868,  # Latitude for Visakhapatnam Beach
    "longitude": 83.2185,  # Longitude for Visakhapatnam Beach
    "current": ["wave_height", "wave_direction", "wave_period", "wind_wave_height", "wind_wave_direction", 
                "wind_wave_period", "wind_wave_peak_period", "swell_wave_height", "swell_wave_direction", 
                "swell_wave_period", "swell_wave_peak_period", "ocean_current_velocity", "ocean_current_direction"],
    "hourly": ["wave_height", "wave_direction", "wave_period", "wind_wave_height", "wind_wave_direction", 
               "wind_wave_period", "wind_wave_peak_period", "swell_wave_height", "swell_wave_direction", 
               "swell_wave_period", "swell_wave_peak_period", "ocean_current_velocity", "ocean_current_direction"],
    "daily": ["wave_height_max", "wave_direction_dominant", "wave_period_max", "wind_wave_height_max", 
              "wind_wave_direction_dominant", "wind_wave_period_max", "wind_wave_peak_period_max", 
              "swell_wave_height_max", "swell_wave_direction_dominant", "swell_wave_period_max", 
              "swell_wave_peak_period_max"]
}
responses = openmeteo.weather_api(url, params=params)

# Process the first location
response = responses[0]
print("Location: Visakhapatnam Beach")  # Hardcoded title
print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation {response.Elevation()} m asl")
print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

# ---- Process Current Data (Latest Only) ----
current = response.Current()
latest_current_data = {
    "current_wave_height": current.Variables(0).Value(),
    "current_wave_direction": current.Variables(1).Value(),
    "current_wave_period": current.Variables(2).Value(),
    "current_wind_wave_height": current.Variables(3).Value(),
    "current_wind_wave_direction": current.Variables(4).Value(),
    "current_wind_wave_period": current.Variables(5).Value(),
    "current_swell_wave_height": current.Variables(7).Value(),
    "current_swell_wave_direction": current.Variables(8).Value(),
    "current_ocean_current_velocity": current.Variables(11).Value(),
    "current_ocean_current_direction": current.Variables(12).Value()
}

print("\nLatest Current Data:")
print(latest_current_data)

# ---- Process Hourly Data (Latest Only) ----
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

# Get the latest entry by selecting the last row
latest_hourly_data = hourly_dataframe.iloc[-1]
print("\nLatest Hourly Weather Data:")
print(latest_hourly_data)

# ---- Process Daily Data (Latest Only) ----
daily = response.Daily()
daily_wave_height_max = daily.Variables(0).ValuesAsNumpy()
daily_wave_direction_dominant = daily.Variables(1).ValuesAsNumpy()
daily_wave_period_max = daily.Variables(2).ValuesAsNumpy()
daily_wind_wave_height_max = daily.Variables(3).ValuesAsNumpy()
daily_wind_wave_direction_dominant = daily.Variables(4).ValuesAsNumpy()
daily_wind_wave_period_max = daily.Variables(5).ValuesAsNumpy()
daily_swell_wave_height_max = daily.Variables(6).ValuesAsNumpy()
daily_swell_wave_direction_dominant = daily.Variables(7).ValuesAsNumpy()
daily_swell_wave_period_max = daily.Variables(8).ValuesAsNumpy()
daily_swell_wave_peak_period_max = daily.Variables(9).ValuesAsNumpy()

daily_data = {
    "date": pd.to_datetime(daily.Time(), unit="s", utc=True),
    "wave_height_max": daily_wave_height_max,
    "wave_direction_dominant": daily_wave_direction_dominant,
    "wave_period_max": daily_wave_period_max,
    "wind_wave_height_max": daily_wind_wave_height_max,
    "wind_wave_direction_dominant": daily_wind_wave_direction_dominant,
    "wind_wave_period_max": daily_wind_wave_period_max,
    "swell_wave_height_max": daily_swell_wave_height_max,
    "swell_wave_direction_dominant": daily_swell_wave_direction_dominant,
    "swell_wave_period_max": daily_swell_wave_period_max,
    "swell_wave_peak_period_max": daily_swell_wave_peak_period_max
}

daily_dataframe = pd.DataFrame(data=daily_data)

# Get the latest entry by selecting the last row
latest_daily_data = daily_dataframe.iloc[-1]
print("\nLatest Daily Weather Data:")
print(latest_daily_data)
