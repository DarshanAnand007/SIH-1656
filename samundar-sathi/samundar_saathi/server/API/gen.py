import openmeteo_requests
import requests
import pandas as pd
from retry_requests import retry
import google.generativeai as genai
import json
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Firebase credentials
firebase_credentials = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
}

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_credentials)
    firebase_admin.initialize_app(cred)

# Initialize Firestore client
db = firestore.client()

# Initialize Open-Meteo client with retries
session = requests.Session()
retry_session = retry(session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

# Set start and end dates (YYYY-MM-DD format)
start_date = "2024-12-07"
end_date = "2024-12-08"

# Define parameters for hourly and daily data
params = {
    "latitude": 13.0500,
    "longitude": 80.2824,
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

# Fetch weather data
responses = openmeteo.weather_api("https://historical-forecast-api.open-meteo.com/v1/forecast", params=params)
response = responses[0]

# Process Hourly Data
hourly = response.Hourly()
hourly_data = {
    "date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    )
}

for i, var_name in enumerate(params["hourly"]):
    hourly_data[var_name] = hourly.Variables(i).ValuesAsNumpy()

hourly_df = pd.DataFrame(data=hourly_data)

# Process Daily Data
daily = response.Daily()
daily_data = {
    "date": pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    )
}

for i, var_name in enumerate(params["daily"]):
    daily_data[var_name] = daily.Variables(i).ValuesAsNumpy()

daily_df = pd.DataFrame(data=daily_data)

# Convert data to JSON
hourly_json = hourly_df.to_json(orient='records', date_format='iso')
daily_json = daily_df.to_json(orient='records', date_format='iso')

# Expanded Activities List
activities = {
    "Water-Based Activities": [
        "Swimming", "Snorkeling", "Surfing", "Paddleboarding", "Jet Skiing", 
        "Parasailing", "Scuba Diving", "Boating/Kayaking", "Fishing", 
        "Bodyboarding", "Kite Surfing", "Wave Watching"
    ],
    "Relaxation and Wellness": [
        "Sunbathing", "Reading", "Meditation", "Beach Yoga", "Picnicking", 
        "Stargazing", "Massage"
    ],
    "Family-Friendly Activities": [
        "Building Sandcastles", "Beachcombing", "Playing Frisbee", 
        "Beach Volleyball", "Flying Kites", "Paddle Ball", "Treasure Hunts"
    ],
    "Fitness and Sports": [
        "Running/Jogging", "Beach Football/Soccer", "Beach Cricket", 
        "Yoga and Pilates", "Sand Workouts", "Cycling"
    ],
    "Adventure and Exploration": [
        "Hiking", "Rock Climbing", "Tide Pooling", "Wildlife Watching", 
        "Photography"
    ],
    "Social and Leisure Activities": [
        "Barbecuing", "Camping", "Bonfires", "Dancing", "Music Jam", 
        "Beach Parties"
    ],
    "Cultural and Eco Activities": [
        "Art and Sand Sculptures", "Eco-Cleanups", "Educational Tours", 
        "Local Markets"
    ],
    "Romantic Activities": [
        "Watching Sunsets/Sunrises", "Dining by the Shore", 
        "Walking Along the Beach", "Boat Rides for Two"
    ],
    "Extreme Sports (for Thrill Seekers)": [
        "Windsurfing", "Paragliding", "Underwater Scooter Riding", 
        "Water Skiing"
    ],
    "Food and Drinks": [
        "Beach Cafés", "Seafood Sampling", "Ice Cream Stands"
    ],
    "Seasonal Activities": [
        "Whale Watching", "Festivals", "Sand Art Competitions"
    ]
}

# Gemini AI configuration and input preparation
genai.configure(api_key="AIzaSyDSSYR5XqnLqgXJ1DTyepmkEbgBWzCeN2I")
model = genai.GenerativeModel(
    "gemini-1.5-pro", generation_config={"response_mime_type": "application/json"}
)

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

analysis_result = model.generate_content(json.dumps(analysis_input))
analysis_result_dict = json.loads(analysis_result)

# Save results to Firebase
def save_analysis_to_firebase(collection_name, data):
    try:
        doc_ref = db.collection(collection_name).document()
        doc_ref.set(data)
        print(f"Data saved successfully in collection '{collection_name}'!")
    except Exception as e:
        print(f"Error saving data to Firebase: {e}")

save_analysis_to_firebase("active", analysis_result_dict)
