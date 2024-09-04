import logging
from flask import Flask, jsonify
import openmeteo_requests
import pandas as pd
import requests
from retry_requests import retry
import os
from groq import Groq
import math

app = Flask(__name__)

# Setup logging to print errors to the console
logging.basicConfig(level=logging.DEBUG)

# Configure the Groq API
client = Groq(api_key="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")

# Setup the Open-Meteo API client without cache
retry_session = retry(requests.Session(), retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Function to clean NaN values
def clean_value(value, default_value=0):
    return default_value if pd.isnull(value) or math.isnan(value) else value

def send_data_to_groq(location, latitude, longitude, wave_height, wave_direction, wind_wave_height, 
                      wind_wave_direction, swell_wave_height=None, swell_wave_direction=None, 
                      ocean_current_velocity=None, ocean_current_direction=None):
    prompt = (
        f"Assess the safety of the beach at {location} based on the provided weather data. "
        f"Give a concise and clear reason for the safety decision and assign a safety score between 1 and 10. "
        f"The message should begin with 'Safe' or 'Unsafe' and provide a short, complete explanation in one or two sentences. "
        f"Wave height: {wave_height} meters. "
        f"Wind wave height: {wind_wave_height} meters. "
        f"Ocean current velocity: {ocean_current_velocity} m/s.\n"
        f"Provide a safety score formatted as 'x/10'."
    )

    try:
        logging.debug(f"Sending prompt to Groq: {prompt}")
        chat_completion = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": prompt
            }],
            model="llama3-8b-8192",
        )

        response = chat_completion.choices[0].message.content

        if response:
            logging.debug(f"Received response from Groq: {response}")
            
            # Initialize variables to hold safety score and message
            safety_score = None
            safety_message = None

            # Search for "safety score" in the response and extract it
            if "safety score" in response.lower():
                try:
                    score_line = [line for line in response.split("\n") if "safety score" in line.lower()]
                    if score_line:
                        safety_score_str = score_line[0].split()[-1]  # Extract the score (last part of the line)
                        safety_score = int(safety_score_str)  # Convert to integer
                except (ValueError, IndexError):
                    logging.error("Safety score extraction failed, defaulting to None.")
            
            # Set the safety score to "0/10" if not found or extracted properly
            if safety_score is None:
                safety_score = "0/10"
            else:
                safety_score = f"{safety_score}/10"

            # Extract the safety message (one-line summary)
            safety_message_lines = response.split("\n")[1:]
            if safety_message_lines:
                safety_message = " ".join(safety_message_lines).strip()

            # Assess safety as "Safe" or "Unsafe" based on score
            safety_status = "Safe" if int(safety_score.split("/")[0]) >= 6 else "Unsafe"

            # Construct a final message with the safety score formatted as "x/10"
            final_message = (
                f"{safety_status}: {safety_message.split('.')[0]}. Safety score: {safety_score}"
            )

            return {
                "safety_message": final_message,
                "safety_score": safety_score
            }

        else:
            logging.error("No valid response from AI")
            return {"safety_message": "No valid response from AI.", "safety_score": "0/10"}

    except Exception as e:
        logging.error(f"Error occurred during Groq response: {e}")
        return {"safety_message": "An error occurred while determining beach safety.", "safety_score": "0/10"}



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
        
        # Get the suitability score from Groq, including location and coordinates
        suitability_response = send_data_to_groq(
            "Visakhapatnam", params["latitude"], params["longitude"],
            clean_value(latest_hourly_data["wave_height"]),
            clean_value(latest_hourly_data["wave_direction"]),
            clean_value(latest_hourly_data["wind_wave_height"]),
            clean_value(latest_hourly_data["wind_wave_direction"]),
            clean_value(latest_hourly_data["swell_wave_height"]),
            clean_value(latest_hourly_data["swell_wave_direction"]),
            clean_value(latest_hourly_data["ocean_current_velocity"]),
            clean_value(latest_hourly_data["ocean_current_direction"])
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
            "suitability": {
                "safety_message": suitability_response  # AI-generated short suitability response
            }
        }
        
        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
