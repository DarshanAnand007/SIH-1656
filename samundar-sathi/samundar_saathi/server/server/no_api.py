import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# List of beaches with their coordinates (latitude, longitude)
beaches = [
    {"name": "Visakhapatnam Beach", "latitude": 17.6868, "longitude": 83.2185},
    {"name": "Ramakrishna Beach", "latitude": 17.7196, "longitude": 83.3189},
    {"name": "Marina Beach", "latitude": 13.0500, "longitude": 80.2824},
    {"name": "Kovalam Beach", "latitude": 8.3772, "longitude": 76.9460},
    {"name": "Calangute Beach", "latitude": 15.5445, "longitude": 73.7553}
]

# Function to assess beach safety based on weather data
def assess_beach_safety(wave_height, wave_direction, wind_wave_height, wind_wave_direction, 
                        swell_wave_height=None, swell_wave_direction=None, 
                        ocean_current_velocity=None, ocean_current_direction=None,
                        wave_height_max=None, wind_wave_height_max=None):
    # Define threshold values for safety
    safe_wave_height = 1.5  # in meters, considered safe if below this value
    safe_wind_wave_height = 1.5  # in meters, considered safe if below this value
    high_wind_wave_height_threshold = 5.0  # Wind wave height above this value should lower safety significantly
    very_high_wind_wave_height_threshold = 7.0  # Extremely high wind wave height
    safe_ocean_current_velocity = 1.0  # in meters per second, considered safe if below this value
    safe_wave_height_max = 1.7  # Maximum wave height considered safe
    safe_wind_wave_height_max = 1.0  # Maximum wind wave height considered safe

    # Initialize safety score and reason
    safety_score = 10
    reason = []
    
    # Check current wave height
    if wave_height and wave_height > safe_wave_height:
        safety_score -= 2
        reason.append(f"Wave height is {wave_height:.2f} meters, which is higher than the safe limit.")
    
    # Check wind wave height
    if wind_wave_height and wind_wave_height > safe_wind_wave_height:
        if wind_wave_height > very_high_wind_wave_height_threshold:
            safety_score -= 5  # Strong penalty for very high wind wave height
            reason.append(f"Wind wave height is {wind_wave_height:.2f} meters, which is extremely high and dangerous.")
        elif wind_wave_height > high_wind_wave_height_threshold:
            safety_score -= 4  # Strong penalty for high wind wave height
            reason.append(f"Wind wave height is {wind_wave_height:.2f} meters, which is higher than the safe limit.")
        else:
            safety_score -= 2  # Moderate penalty for slightly high wind wave height
            reason.append(f"Wind wave height is {wind_wave_height:.2f} meters, which is higher than the safe limit.")
    
    # Check ocean current velocity, if available
    if ocean_current_velocity and ocean_current_velocity > safe_ocean_current_velocity:
        safety_score -= 1
        reason.append(f"Ocean current velocity is {ocean_current_velocity:.2f} m/s, which is strong.")
    
    # Check daily max wave height, if available
    if wave_height_max and wave_height_max > safe_wave_height_max:
        safety_score -= 2
        reason.append(f"Maximum daily wave height is {wave_height_max:.2f} meters, which is above the safe limit.")
    
    # Check daily max wind wave height, if available
    if wind_wave_height_max and wind_wave_height_max > safe_wind_wave_height_max:
        safety_score -= 1
        reason.append(f"Maximum daily wind wave height is {wind_wave_height_max:.2f} meters, which is above the safe limit.")
    
    # Compile safety message
    if safety_score >= 8:
        safety_message = "Safe"
        reason.insert(0, "The beach is safe based on current weather conditions.")
    elif safety_score >= 5:
        safety_message = "Moderately safe"
        reason.insert(0, "The beach is moderately safe, but caution is advised.")
    else:
        safety_message = "Unsafe"
        reason.insert(0, "The beach is unsafe based on current weather conditions.")
    
    # Return the result
    return {
        "safety_message": safety_message,
        "safety_score": safety_score,
        "reasons": reason
    }

# Function to process the weather data for each beach
def fetch_weather_data_for_beach(beach):
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": beach["latitude"],
        "longitude": beach["longitude"],
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

    # Fetch the weather data
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]  # Assume first response is the one we need

    # Process current data safely
    current = response.Current()
    
    # Define a function to safely get variables by index
    def get_variable(var_index):
        try:
            return current.Variables(var_index).Value()
        except (IndexError, TypeError):
            return None

    wave_height = get_variable(0)
    wave_direction = get_variable(1)
    wind_wave_height = get_variable(3)
    wind_wave_direction = get_variable(4)
    ocean_current_velocity = get_variable(11)
    ocean_current_direction = get_variable(12)

    daily = response.Daily()
    wave_height_max = daily.Variables(0).ValuesAsNumpy()[-1]  # Assuming latest
    wind_wave_height_max = daily.Variables(3).ValuesAsNumpy()[-1]  # Assuming latest

    # Assess safety using the assess_beach_safety function
    safety_report = assess_beach_safety(
        wave_height=wave_height, wave_direction=wave_direction, 
        wind_wave_height=wind_wave_height, wind_wave_direction=wind_wave_direction,
        ocean_current_velocity=ocean_current_velocity, ocean_current_direction=ocean_current_direction,
        wave_height_max=wave_height_max, wind_wave_height_max=wind_wave_height_max
    )

    # Print the safety report
    print(f"\nLocation: {beach['name']}")
    print(f"Safety Message: {safety_report['safety_message']}")
    print(f"Safety Score: {safety_report['safety_score']}")
    print("Reasons:")
    for reason in safety_report['reasons']:
        print(f"- {reason}")

# Loop through each beach and fetch the weather data
for beach in beaches:
    fetch_weather_data_for_beach(beach)
