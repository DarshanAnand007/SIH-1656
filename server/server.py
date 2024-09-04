import logging
from flask import Flask, jsonify, request
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import google.generativeai as genai
import os

app = Flask(__name__)

# Setup logging to print errors to the console
logging.basicConfig(level=logging.DEBUG)

genai.configure(api_key="AIzaSyDq5tdo2AL7V_x1zOcBEiNRy6HyQw6sibc")

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Function to send data to Gemini and get a suitability score
def send_data_to_gemini(location, latitude, longitude, wave_height, wave_direction, wind_wave_height, wind_wave_direction,
                        swell_wave_height, swell_wave_direction, ocean_current_velocity, ocean_current_direction):
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    # Craft the prompt with location, coordinates, and weather data
    prompt = (
        f"Location: {location}\n"
        f"Coordinates: {latitude}°N, {longitude}°E\n\n"
        f"Beach conditions:\n"
        f"- Wave height: {wave_height} meters\n"
        f"- Wave direction: {wave_direction} degrees\n"
        f"- Wind wave height: {wind_wave_height} meters\n"
        f"- Wind wave direction: {wind_wave_direction} degrees\n"
        f"- Swell wave height: {swell_wave_height} meters\n"
        f"- Swell wave direction: {swell_wave_direction} degrees\n"
        f"- Ocean current velocity: {ocean_current_velocity} m/s\n"
        f"- Ocean current direction: {ocean_current_direction} degrees\n\n"
        f"Rate the suitability for visiting the beach on a scale of 1 to 10."
    )
    
    response = model.generate_content(prompt)
    
    # Extract and return the suitability score from the response
    return response.text.strip()

@app.route('/weather', methods=['GET'])
def get_weather():
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": 17.6868,  # Latitude for Visakhapatnam Beach
        "longitude": 83.2185,  # Longitude for Visakhapatnam Beach
        "hourly": ["wave_height", "wave_direction", "wind_wave_height", "wind_wave_direction",
                   "swell_wave_height", "swell_wave_direction", "ocean_current_velocity", "ocean_current_direction"],
        "models": "best_match"
    }
    
    try:
        # Fetch the weather data
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        
        # Process hourly data
        hourly = response.Hourly()
        hourly_wave_height = hourly.Variables(0).ValuesAsNumpy().astype(float)
        hourly_wave_direction = hourly.Variables(1).ValuesAsNumpy().astype(float)
        hourly_wind_wave_height = hourly.Variables(2).ValuesAsNumpy().astype(float)
        hourly_wind_wave_direction = hourly.Variables(3).ValuesAsNumpy().astype(float)
        hourly_swell_wave_height = hourly.Variables(4).ValuesAsNumpy().astype(float)
        hourly_swell_wave_direction = hourly.Variables(5).ValuesAsNumpy().astype(float)
        hourly_ocean_current_velocity = hourly.Variables(6).ValuesAsNumpy().astype(float)
        hourly_ocean_current_direction = hourly.Variables(7).ValuesAsNumpy().astype(float)
        
        # Convert the UTC timestamps to the desired timezone (e.g., Asia/Kolkata for Visakhapatnam)
        utc_times = pd.to_datetime(hourly.Time(), unit="s", utc=True)
        local_times = utc_times.tz_convert('Asia/Kolkata')
        
        # Ensure local_times is iterable
        if isinstance(local_times, pd.Timestamp):
            latest_time = local_times
        else:
            latest_time = local_times[-1]
        
        # Get the latest entry by selecting the last row
        latest_entry = {
            "date": latest_time.strftime('%Y-%m-%d %H:%M:%S'),
            "wave_height": float(hourly_wave_height[-1]),
            "wave_direction": float(hourly_wave_direction[-1]),
            "wind_wave_height": float(hourly_wind_wave_height[-1]),
            "wind_wave_direction": float(hourly_wind_wave_direction[-1]),
            "swell_wave_height": float(hourly_swell_wave_height[-1]),
            "swell_wave_direction": float(hourly_swell_wave_direction[-1]),
            "ocean_current_velocity": float(hourly_ocean_current_velocity[-1]),
            "ocean_current_direction": float(hourly_ocean_current_direction[-1])
        }
        
        # Get the suitability score from Gemini, including location and coordinates
        suitability_score = send_data_to_gemini(
            "Visakhapatnam", params["latitude"], params["longitude"],
            latest_entry["wave_height"], latest_entry["wave_direction"],
            latest_entry["wind_wave_height"], latest_entry["wind_wave_direction"],
            latest_entry["swell_wave_height"], latest_entry["swell_wave_direction"],
            latest_entry["ocean_current_velocity"], latest_entry["ocean_current_direction"]
        )
        
        # Add the suitability score to the response
        response_data = {
            "vishakapatnam": {
                "lat": response.Latitude(),
                "long": response.Longitude(),
                "wave_height": latest_entry["wave_height"],
                "wave_direction": latest_entry["wave_direction"],
                "wind_wave_height": latest_entry["wind_wave_height"],
                "wind_wave_direction": latest_entry["wind_wave_direction"],
                "swell_wave_height": latest_entry["swell_wave_height"],
                "swell_wave_direction": latest_entry["swell_wave_direction"],
                "ocean_current_velocity": latest_entry["ocean_current_velocity"],
                "ocean_current_direction": latest_entry["ocean_current_direction"],
                "suitability_score": suitability_score
            }
        }
        
        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Specify the IP and port to run the server on
    app.run(host='0.0.0.0', port=5001, debug=True)
