import logging
from flask import Flask, jsonify
import openmeteo_requests
import pandas as pd
import requests
from retry_requests import retry
import math

app = Flask(__name__)

# Setup logging to print errors to the console
logging.basicConfig(level=logging.DEBUG)

# Setup the Open-Meteo API client without cache
retry_session = retry(requests.Session(), retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Function to clean NaN values
def clean_value(value, default_value=0):
    return default_value if pd.isnull(value) or math.isnan(value) else value

# Updated beach safety assessment algorithm
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
    if wave_height > safe_wave_height:
        safety_score -= 2
        reason.append(f"Wave height is {wave_height:.2f} meters, which is higher than the safe limit.")
    
    # Check wind wave height
    if wind_wave_height > safe_wind_wave_height:
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
    if ocean_current_velocity is not None and ocean_current_velocity > safe_ocean_current_velocity:
        safety_score -= 1
        reason.append(f"Ocean current velocity is {ocean_current_velocity:.2f} m/s, which is strong.")
    
    # Check daily max wave height, if available
    if wave_height_max is not None and wave_height_max > safe_wave_height_max:
        safety_score -= 2
        reason.append(f"Maximum daily wave height is {wave_height_max:.2f} meters, which is above the safe limit.")
    
    # Check daily max wind wave height, if available
    if wind_wave_height_max is not None and wind_wave_height_max > safe_wind_wave_height_max:
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

@app.route('/weather', methods=['GET'])
def get_weather():
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": 17.7100,  # Latitude for Visakhapatnam Beach (Rama Krishna Beach)
        "longitude": 83.3162,  # Longitude for Visakhapatnam Beach (Rama Krishna Beach)
        "current": ["wave_height", "wave_direction", "wave_period", "wind_wave_height", "wind_wave_direction", 
                    "wind_wave_period", "wind_wave_peak_period", "swell_wave_height", "swell_wave_direction", 
                    "swell_wave_period", "swell_wave_peak_period", "ocean_current_velocity", "ocean_current_direction"],
        "hourly": ["wave_height", "wave_direction", "wave_period", "wind_wave_height", "wind_wave_direction", 
                   "wind_wave_period", "wind_wave_peak_period", "swell_wave_height", "swell_wave_direction", 
                   "swell_wave_period", "swell_wave_peak_period", "ocean_current_velocity", "ocean_current_direction"],
        "daily": ["wave_height_max", "wave_direction_dominant", "wave_period_max", "wind_wave_height_max", 
                  "wind_wave_direction_dominant", "wind_wave_period_max", "wind_wave_peak_period_max", 
                  "swell_wave_height_max", "swell_wave_direction_dominant", "swell_wave_period_max", 
                  "swell_wave_peak_period_max"],
        "models": "best_match"
    }
    
    try:
        # Fetch the weather data
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        
        # ---- Process Current Data ----
        current = response.Current()
        latest_current_data = {
            "current_wave_height": clean_value(current.Variables(0).Value()),
            "current_wave_direction": clean_value(current.Variables(1).Value()),
            "current_wave_period": clean_value(current.Variables(2).Value()),
            "current_wind_wave_height": clean_value(current.Variables(3).Value()),
            "current_wind_wave_direction": clean_value(current.Variables(4).Value()),
            "current_wind_wave_period": clean_value(current.Variables(5).Value()),
            "current_swell_wave_height": clean_value(current.Variables(7).Value()),
            "current_swell_wave_direction": clean_value(current.Variables(8).Value()),
            "current_ocean_current_velocity": clean_value(current.Variables(11).Value()),
            "current_ocean_current_direction": clean_value(current.Variables(12).Value())
        }
        
        # ---- Process Hourly Data (Latest Only) ----
        hourly = response.Hourly()
        hourly_wave_height = hourly.Variables(0).ValuesAsNumpy().astype(float)
        hourly_wave_direction = hourly.Variables(1).ValuesAsNumpy().astype(float)
        hourly_wind_wave_height = hourly.Variables(2).ValuesAsNumpy().astype(float)
        hourly_wind_wave_direction = hourly.Variables(3).ValuesAsNumpy().astype(float)
        hourly_swell_wave_height = hourly.Variables(4).ValuesAsNumpy().astype(float)
        hourly_swell_wave_direction = hourly.Variables(5).ValuesAsNumpy().astype(float)
        hourly_ocean_current_velocity = hourly.Variables(6).ValuesAsNumpy().astype(float)
        hourly_ocean_current_direction = hourly.Variables(7).ValuesAsNumpy().astype(float)
        
        # Convert the UTC timestamps to the desired timezone (Asia/Kolkata for Visakhapatnam)
        utc_times = pd.to_datetime(hourly.Time(), unit="s", utc=True)
        local_times = utc_times.tz_convert('Asia/Kolkata')
        
        hourly_data = {
            "date": local_times,
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
        
        # ---- Process Daily Data (Latest Only) ----
        daily = response.Daily()
        latest_daily_data = {
            "wave_height_max": clean_value(daily.Variables(0).Value()),
            "wind_wave_height_max": clean_value(daily.Variables(3).Value())
        }
        
        # Get the suitability score using the custom algorithm
        suitability_response = assess_beach_safety(
            clean_value(latest_hourly_data["wave_height"]),
            clean_value(latest_hourly_data["wave_direction"]),
            clean_value(latest_hourly_data["wind_wave_height"]),
            clean_value(latest_hourly_data["wind_wave_direction"]),
            clean_value(latest_hourly_data["swell_wave_height"]),
            clean_value(latest_hourly_data["swell_wave_direction"]),
            clean_value(latest_hourly_data["ocean_current_velocity"]),
            clean_value(latest_hourly_data["ocean_current_direction"]),
            wave_height_max=clean_value(latest_daily_data["wave_height_max"]),
            wind_wave_height_max=clean_value(latest_daily_data["wind_wave_height_max"])
        )
        
        # Add the suitability score and safety message to the response
        response_data = {
            "location": "Rama Krishna Beach, Visakhapatnam",
            "coordinates": {
                "latitude": params["latitude"],
                "longitude": params["longitude"]
            },
            "current_conditions": {
                "wave_height": latest_hourly_data["wave_height"],
                "wave_direction": latest_hourly_data["wave_direction"],
                "wind_wave_height": latest_hourly_data["wind_wave_height"],
                "wind_wave_direction": latest_hourly_data["wind_wave_direction"],
                "swell_wave_height": latest_hourly_data["swell_wave_height"],
                "swell_wave_direction": latest_hourly_data["swell_wave_direction"],
                "ocean_current_velocity": latest_hourly_data["ocean_current_velocity"],
                "ocean_current_direction": latest_hourly_data["ocean_current_direction"]
            },
            "suitability": suitability_response  # Custom algorithm-generated suitability response
        }
        
        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
