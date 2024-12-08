import os
import json
import time
import pandas as pd
import requests
import requests_cache
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from retry_requests import retry
import openmeteo_requests
import google.generativeai as genai
import schedule

# Load environment variables from .env file
load_dotenv()

# Firebase credentials from environment variables
firebase_credentials = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),  # Handle newlines in private key
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
}

# Initialize Firebase Admin SDK
cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred)
db = firestore.client()

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Define the location for weather data
latitude = 13.0500
longitude = 80.2824

# Set the start and end dates (YYYY-MM-DD format)
start_date = "2024-12-07"
end_date = "2024-12-08"

# Define parameters for hourly and daily data
params = {
    "latitude": latitude,
    "longitude": longitude,
    "start_date": start_date,
    "end_date": end_date,
    "hourly": [
        "temperature_2m", "relative_humidity_2m", "dew_point_2m", "apparent_temperature",
        "precipitation_probability", "precipitation", "rain", "showers", "snowfall", "snow_depth",
        "weather_code", "pressure_msl", "surface_pressure", "cloud_cover", "cloud_cover_low",
        "cloud_cover_mid", "cloud_cover_high", "visibility", "evapotranspiration", "et0_fao_evapotranspiration",
        "vapour_pressure_deficit", "wind_speed_10m", "wind_speed_80m", "wind_speed_120m", "wind_speed_180m",
        "wind_direction_10m", "wind_direction_80m", "wind_direction_120m", "wind_direction_180m",
        "wind_gusts_10m", "temperature_80m", "temperature_120m", "temperature_180m", "soil_temperature_0cm",
        "soil_temperature_6cm", "soil_temperature_18cm", "soil_temperature_54cm", "soil_moisture_0_to_1cm",
        "soil_moisture_1_to_3cm", "soil_moisture_3_to_9cm", "soil_moisture_9_to_27cm", "soil_moisture_27_to_81cm",
        "uv_index", "uv_index_clear_sky", "is_day", "sunshine_duration", "wet_bulb_temperature_2m",
        "total_column_integrated_water_vapour", "cape", "lifted_index", "convective_inhibition",
        "freezing_level_height", "boundary_layer_height", "hail"
    ],
    "daily": [
        "weather_code", "temperature_2m_max", "temperature_2m_min", "apparent_temperature_max", "apparent_temperature_min",
        "sunrise", "sunset", "daylight_duration", "sunshine_duration", "uv_index_max", "uv_index_clear_sky_max",
        "precipitation_sum", "rain_sum", "showers_sum", "snowfall_sum", "precipitation_hours",
        "precipitation_probability_max", "wind_speed_10m_max", "wind_gusts_10m_max", "wind_direction_10m_dominant",
        "shortwave_radiation_sum", "et0_fao_evapotranspiration"
    ],
    "temporal_resolution": "native",
    "models": "best_match"
}

# Fetch weather data from Open-Meteo API
responses = openmeteo.weather_api("https://historical-forecast-api.open-meteo.com/v1/forecast", params=params)
response = responses[0]

# Process Hourly Data
hourly = response.Hourly()
hourly_names = [
    "temperature_2m", "relative_humidity_2m", "dew_point_2m", "apparent_temperature",
    "precipitation_probability", "precipitation", "rain", "showers", "snowfall", "snow_depth",
    "weather_code", "pressure_msl", "surface_pressure", "cloud_cover", "cloud_cover_low",
    "cloud_cover_mid", "cloud_cover_high", "visibility", "evapotranspiration", "et0_fao_evapotranspiration",
    "vapour_pressure_deficit", "wind_speed_10m", "wind_speed_80m", "wind_speed_120m", "wind_speed_180m",
    "wind_direction_10m", "wind_direction_80m", "wind_direction_120m", "wind_direction_180m",
    "wind_gusts_10m", "temperature_80m", "temperature_120m", "temperature_180m", "soil_temperature_0cm",
    "soil_temperature_6cm", "soil_temperature_18cm", "soil_temperature_54cm", "soil_moisture_0_to_1cm",
    "soil_moisture_1_to_3cm", "soil_moisture_3_to_9cm", "soil_moisture_9_to_27cm", "soil_moisture_27_to_81cm",
    "uv_index", "uv_index_clear_sky", "is_day", "sunshine_duration", "wet_bulb_temperature_2m",
    "total_column_integrated_water_vapour", "cape", "lifted_index", "convective_inhibition",
    "freezing_level_height", "boundary_layer_height", "hail"
]

hourly_data = {
    "date": pd.to_datetime(hourly.Time(), unit="s", utc=True)
}

for i, var_name in enumerate(hourly_names):
    hourly_data[var_name] = hourly.Variables(i).ValuesAsNumpy()

hourly_df = pd.DataFrame(data=hourly_data)

# Process Daily Data
daily = response.Daily()
daily_names = [
    "weather_code", "temperature_2m_max", "temperature_2m_min", "apparent_temperature_max", "apparent_temperature_min",
    "sunrise", "sunset", "daylight_duration", "sunshine_duration", "uv_index_max", "uv_index_clear_sky_max",
    "precipitation_sum", "rain_sum", "showers_sum", "snowfall_sum", "precipitation_hours",
    "precipitation_probability_max", "wind_speed_10m_max", "wind_gusts_10m_max", "wind_direction_10m_dominant",
    "shortwave_radiation_sum", "et0_fao_evapotranspiration"
]

daily_data = {
    "date": pd.to_datetime(daily.Time(), unit="s", utc=True)
}

for i, var_name in enumerate(daily_names):
    daily_data[var_name] = daily.Variables(i).ValuesAsNumpy()

daily_df = pd.DataFrame(data=daily_data)

# Convert DataFrames to JSON
hourly_json = hourly_df.to_json(orient='records', date_format='iso')
daily_json = daily_df.to_json(orient='records', date_format='iso')

# Define Activities
activities = {
    "Water-Based Activities": ["Swimming", "Snorkeling", "Surfing", "Paddleboarding", "Jet Skiing", "Parasailing", "Scuba Diving", "Boating/Kayaking", "Fishing", "Bodyboarding", "Kite Surfing", "Wave Watching"],
    "Relaxation and Wellness": ["Sunbathing", "Reading", "Meditation", "Beach Yoga", "Picnicking", "Stargazing", "Massage"],
    "Family-Friendly Activities": ["Building Sandcastles", "Beachcombing", "Playing Frisbee", "Beach Volleyball", "Flying Kites", "Paddle Ball", "Treasure Hunts"],
    "Fitness and Sports": ["Running/Jogging", "Beach Football/Soccer", "Beach Cricket", "Yoga and Pilates", "Sand Workouts", "Cycling"],
    "Adventure and Exploration": ["Hiking", "Rock Climbing", "Tide Pooling", "Wildlife Watching", "Photography"],
    "Social Activities": ["Bonfires", "Music Jam", "Barbecuing", "Camping", "Dancing", "Beach Parties"],
    "Cultural and Eco Activities": ["Art and Sand Sculptures", "Eco-Cleanups", "Educational Tours", "Local Markets"],
    "Romantic Activities": ["Watching Sunsets/Sunrises", "Dining by the Shore", "Walking Along the Beach", "Boat Rides for Two"],
    "Extreme Sports": ["Windsurfing", "Paragliding", "Underwater Scooter Riding", "Water Skiing"],
    "Food and Drinks": ["Beach Cafés", "Seafood Sampling", "Ice Cream Stands"],
    "Seasonal Activities": ["Whale Watching", "Festivals", "Sand Art Competitions"]
}

# Configure Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    "gemini-1.5-pro", generation_config={"response_mime_type": "application/json"}
)

# Prepare Input for Gemini AI
analysis_input = {
    "weather_data": {
        "hourly": json.loads(hourly_json),
        "daily": json.loads(daily_json)
    },
    "activities": activities,
    "instructions": """Analyze the provided hourly weather data and suggest activities based on the following criteria:
1. Divide the day into three time slots: morning (06:00-12:00), afternoon (12:00-18:00), and evening (18:00-24:00).
2. For each hour within these slots, suggest all possible activities that the user can do based on weather conditions such as temperature, precipitation, wind speed, and UV index.
3. Highlight the single best activity for each hour considering comfort and weather suitability.
4. Use a 24-hour format for the time in the output.
5. Provide the recommendations in the following format:
   {
       "time_slot": "06:00-12:00",
       "hourly_activities": [
           {
               "time": "06:00",
               "possible_activities": ["Activity 1", "Activity 2"],
               "best_activity": "Activity 1"
           },
           ...
       ]
   }"""
}

# Generate Activity Recommendations using Gemini AI
try:
    analysis_result = model.generate_content(json.dumps(analysis_input))
    
    # Extract the content from the response object
    if hasattr(analysis_result, 'content'):
        analysis_text = analysis_result.content
    elif hasattr(analysis_result, 'text'):
        analysis_text = analysis_result.text
    else:
        raise AttributeError("The response object does not have 'content' or 'text' attributes.")
    
    # Parse the JSON content
    analysis_json = json.loads(analysis_text)
    
    print("Gemini AI Analysis:")
    print(json.dumps(analysis_json, indent=4))
except Exception as e:
    print(f"Error during AI analysis: {e}")
    analysis_json = {}

# Function to store data in Firestore
def store_activities_in_firestore(analysis_data):
    if not analysis_data:
        print("No analysis data to store.")
        return

    activities_ref = db.collection("Activities").document("ActivityRecommendations")
    activities_ref.set(analysis_data, merge=True)
    print("Activity recommendations saved to Firestore successfully.")

# Store the analysis result in Firestore
store_activities_in_firestore(analysis_json)

# Optional: Schedule periodic updates (e.g., every 6 hours)
def job():
    print("Fetching and analyzing weather data...")
    try:
        # Fetch weather data
        responses = openmeteo.weather_api("https://historical-forecast-api.open-meteo.com/v1/forecast", params=params)
        response = responses[0]

        # Process Hourly Data
        hourly = response.Hourly()
        hourly_data = {
            "date": pd.to_datetime(hourly.Time(), unit="s", utc=True)
        }
        for i, var_name in enumerate(hourly_names):
            hourly_data[var_name] = hourly.Variables(i).ValuesAsNumpy()
        hourly_df = pd.DataFrame(data=hourly_data)
        hourly_json = hourly_df.to_json(orient='records', date_format='iso')

        # Process Daily Data
        daily = response.Daily()
        daily_data = {
            "date": pd.to_datetime(daily.Time(), unit="s", utc=True)
        }
        for i, var_name in enumerate(daily_names):
            daily_data[var_name] = daily.Variables(i).ValuesAsNumpy()
        daily_df = pd.DataFrame(data=daily_data)
        daily_json = daily_df.to_json(orient='records', date_format='iso')

        # Prepare Input for Gemini AI
        analysis_input = {
            "weather_data": {
                "hourly": json.loads(hourly_json),
                "daily": json.loads(daily_json)
            },
            "activities": activities,
            "instructions": """Analyze the provided hourly weather data and suggest activities based on the following criteria:

1. **Time Slots**:
   - **Morning**: 06:00-12:00
   - **Afternoon**: 12:00-18:00
   - **Evening**: 18:00-24:00

2. **Activity Suggestions**:
   - For each hour within these time slots, suggest **up to three** suitable activities that the user can engage in based on the current weather conditions, including temperature, precipitation, wind speed, and UV index.
   - Ensure that the activities are varied and cover different interests (e.g., relaxation, adventure, social).

3. **Best Activity Highlight**:
   - Identify and highlight the **single best activity** for each hour, considering overall comfort and weather suitability.

4. **Output Format**:
   - Use a clear and concise JSON structure.
   - Present the recommendations in the following format:

```json
{
    "time_slot": "06:00-12:00",
    "hourly_activities": [
        {
            "time": "06:00",
            "possible_activities": ["Activity 1", "Activity 2", "Activity 3"],
            "best_activity": "Activity 1"
        },
        {
            "time": "07:00",
            "possible_activities": ["Activity 4", "Activity 5", "Activity 6"],
            "best_activity": "Activity 5"
        },
        ...
    ]
}
{
    "time_slot": "12:00-18:00",
    "hourly_activities": [
        ...
    ]
}
{
    "time_slot": "18:00-24:00",
    "hourly_activities": [
        ...
    ]
}

   }"""
        }

        # Generate Activity Recommendations
        analysis_result = model.generate_content(json.dumps(analysis_input))
        
        # Extract the content
        if hasattr(analysis_result, 'content'):
            analysis_text = analysis_result.content
        elif hasattr(analysis_result, 'text'):
            analysis_text = analysis_result.text
        else:
            raise AttributeError("The response object does not have 'content' or 'text' attributes.")
        
        # Parse the JSON content
        analysis_json = json.loads(analysis_text)
        print("Gemini AI Analysis:")
        print(json.dumps(analysis_json, indent=4))
        
        # Store the analysis result in Firestore
        store_activities_in_firestore(analysis_json)
        
    except Exception as e:
        print(f"Error during scheduled job: {e}")

# Schedule the job every 6 hours
schedule.every(6).hours.do(job)

print("Scheduler started. Press Ctrl+C to exit.")
try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    print("\nScheduler stopped.")
