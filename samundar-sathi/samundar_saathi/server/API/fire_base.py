import os
from dotenv import load_dotenv
from firebase_admin import credentials
import firebase_admin
from firebase_admin import credentials, firestore
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import schedule
import time

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
#Initialize Firebase Admin SDK
cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred)
db = firestore.client()

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

# Function to fetch and store weather data for each beach
def fetch_and_store_weather_data_for_beach(beach):
    url = "https://marine-api.open-meteo.com/v1/marine"
    params = {
        "latitude": beach["latitude"],
        "longitude": beach["longitude"],
        "current": ["wave_height", "wave_direction", "wave_period", "wind_wave_height", "wind_wave_direction"],
        "hourly": ["wave_height", "wave_direction", "wave_period", "wind_wave_height", "wind_wave_direction"],
        "daily": ["wave_height_max", "wave_direction_dominant", "wave_period_max", "wind_wave_height_max", 
                  "wind_wave_direction_dominant"]
    }

    # Fetch the weather data
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]  # Assume first response is the one we need

    # Process the current data
    current_data = {
        "wave_height": response.Current().Variables(0).Value(),
        "wave_direction": response.Current().Variables(1).Value(),
        "wave_period": response.Current().Variables(2).Value(),
        "wind_wave_height": response.Current().Variables(3).Value(),
        "wind_wave_direction": response.Current().Variables(4).Value()
    }

    # Print the data being sent to Firestore (for terminal output)
    print(f"\nStoring data for {beach['name']}:")
    print(f"Current Weather Data: {current_data}")

    # Store in Firestore
    store_weather_data_in_firestore(beach, current_data)

# Function to store data in Firestore
def store_weather_data_in_firestore(beach, weather_data):
    beach_ref = db.collection("beach_weather").document(beach['name'])  # Collection name: 'beach_weather'
    
    # Update the document with the new weather data
    beach_ref.set({
        'name': beach['name'],
        'weather': weather_data
    }, merge=True)

    print(f"Weather data for {beach['name']} added to Firestore successfully.")

# Function to fetch data immediately and then set the interval
def fetch_weather_data():
    # Fetch data immediately
    for beach in beaches:
        fetch_and_store_weather_data_for_beach(beach)

    # Set the interval in minutes (e.g., 2 minutes for testing)
    interval_minutes = 30  # Set your desired interval here, e.g., 30 for 30 minutes
    schedule.every(interval_minutes).minutes.do(lambda: [fetch_and_store_weather_data_for_beach(beach) for beach in beaches])

# Main script execution
if __name__ == "__main__":
    # Start by fetching data immediately
    fetch_weather_data()

    # Run the scheduler in a loop
    while True:
        schedule.run_pending()
        time.sleep(1)
