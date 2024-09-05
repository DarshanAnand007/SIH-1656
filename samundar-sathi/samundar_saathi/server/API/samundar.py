import os
from dotenv import load_dotenv
from firebase_admin import credentials, firestore
import firebase_admin
import openmeteo_requests
import requests_cache
import schedule
import time
from retry_requests import retry

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

beaches = [
    {"name": "Marina Beach", "latitude": 13.0500, "longitude": 80.2824},  # Chennai, Tamil Nadu
    {"name": "Kovalam Beach", "latitude": 8.3772, "longitude": 76.9460},  # Kovalam, Kerala
    {"name": "Calangute Beach", "latitude": 15.5445, "longitude": 73.7553},  # Calangute, Goa
    {"name": "Rushikonda Beach", "latitude": 17.7696, "longitude": 83.3858},  # Visakhapatnam, Andhra Pradesh
    {"name": "Baga Beach", "latitude": 15.5526, "longitude": 73.7672},  # Baga, Goa
    {"name": "Varkala Beach", "latitude": 8.7379, "longitude": 76.7010},  # Varkala, Kerala
    {"name": "Palolem Beach", "latitude": 15.0131, "longitude": 74.0235},  # Palolem, Goa
    {"name": "Radhanagar Beach", "latitude": 12.0120, "longitude": 92.9907},  # Havelock Island, Andaman and Nicobar
    {"name": "Gokarna Beach", "latitude": 14.5502, "longitude": 74.3185},  # Gokarna, Karnataka
    {"name": "Tarkarli Beach", "latitude": 16.0363, "longitude": 73.4702}   # Tarkarli, Maharashtra
]


# Function to assess beach safety based on weather data with improved pointing system
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

    # Weights for different parameters to adjust impact on safety score
    wave_weight = 1.5
    wind_wave_weight = 1.2
    current_weight = 1.3

    # Initialize safety score and reason
    safety_score = 10
    reason = []
    
    # Check current wave height
    if wave_height and wave_height > safe_wave_height:
        penalty = min((wave_height - safe_wave_height) * wave_weight, 5)
        safety_score -= penalty
        reason.append(f"Wave height is {wave_height:.2f} meters, which exceeds the safe limit by {wave_height - safe_wave_height:.2f} meters.")
    
    # Check wind wave height
    if wind_wave_height and wind_wave_height > safe_wind_wave_height:
        if wind_wave_height > very_high_wind_wave_height_threshold:
            penalty = 5  # Strong penalty for very high wind wave height
            safety_score -= penalty
            reason.append(f"Wind wave height is {wind_wave_height:.2f} meters, which is extremely high and dangerous.")
        elif wind_wave_height > high_wind_wave_height_threshold:
            penalty = 4  # Strong penalty for high wind wave height
            safety_score -= penalty
            reason.append(f"Wind wave height is {wind_wave_height:.2f} meters, which is higher than the safe limit.")
        else:
            penalty = (wind_wave_height - safe_wind_wave_height) * wind_wave_weight
            safety_score -= penalty
            reason.append(f"Wind wave height is {wind_wave_height:.2f} meters, which is higher than the safe limit.")
    
    # Check ocean current velocity, if available
    if ocean_current_velocity and ocean_current_velocity > safe_ocean_current_velocity:
        penalty = (ocean_current_velocity - safe_ocean_current_velocity) * current_weight
        safety_score -= penalty
        reason.append(f"Ocean current velocity is {ocean_current_velocity:.2f} m/s, which exceeds the safe limit by {ocean_current_velocity - safe_ocean_current_velocity:.2f} m/s.")
    
    # Check daily max wave height, if available
    if wave_height_max and wave_height_max > safe_wave_height_max:
        penalty = min((wave_height_max - safe_wave_height_max) * wave_weight, 2)
        safety_score -= penalty
        reason.append(f"Maximum daily wave height is {wave_height_max:.2f} meters, which is above the safe limit.")
    
    # Check daily max wind wave height, if available
    if wind_wave_height_max and wind_wave_height_max > safe_wind_wave_height_max:
        penalty = min((wind_wave_height_max - safe_wind_wave_height_max) * wind_wave_weight, 2)
        safety_score -= penalty
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
    
# Function to safely extract variables from the Open-Meteo API response
def safe_get_variable(response, index):
    try:
        return response.Current().Variables(index).Value()
    except (IndexError, AttributeError, TypeError):
        return None

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

    # Safely retrieve data
    wave_height = safe_get_variable(response, 0)
    wave_direction = safe_get_variable(response, 1)
    wind_wave_height = safe_get_variable(response, 3)
    wind_wave_direction = safe_get_variable(response, 4)
    ocean_current_velocity = safe_get_variable(response, 5)  # Handle missing data safely

    wave_height_max = safe_get_variable(response, 0)  # Assuming the index for max wave height
    wind_wave_height_max = safe_get_variable(response, 3)  # Assuming the index for max wind wave height

    # Check if values are available
    if not wave_height or not wind_wave_height:
        print(f"Warning: No data available for {beach['name']}")
        return

    current_data = {
        "wave_height": wave_height,
        "wave_direction": wave_direction,
        "wind_wave_height": wind_wave_height,
        "wind_wave_direction": wind_wave_direction,
        "ocean_current_velocity": ocean_current_velocity,
        "wave_height_max": wave_height_max,
        "wind_wave_height_max": wind_wave_height_max
    }

    # Assess beach safety based on the weather data
    safety_report = assess_beach_safety(
        wave_height=wave_height, wave_direction=wave_direction, 
        wind_wave_height=wind_wave_height, wind_wave_direction=wind_wave_direction,
        ocean_current_velocity=ocean_current_velocity, wave_height_max=wave_height_max, 
        wind_wave_height_max=wind_wave_height_max
    )

    # Print the data being sent to Firestore (for terminal output)
    print(f"\nStoring data for {beach['name']}:")
    print(f"Current Weather Data: {current_data}")
    print(f"Safety Report: {safety_report}")

    # Store in Firestore
    store_weather_and_safety_data_in_firestore(beach, current_data, safety_report)

# Function to store weather and safety data in Firestore
def store_weather_and_safety_data_in_firestore(beach, weather_data, safety_report):
    beach_ref = db.collection("samundar_data").document(beach['name'])  # Collection name: 'samundar_data'
    
    # Update the document with the new weather and safety data
    beach_ref.set({
        'name': beach['name'],
        'weather': weather_data,
        'safety_report': safety_report,
        'timestamp': firestore.SERVER_TIMESTAMP
    }, merge=True)

    print(f"Weather and safety data for {beach['name']} added to Firestore successfully.")

def fetch_weather_data():
    # Fetch data immediately
    for beach in beaches:
        fetch_and_store_weather_data_for_beach(beach)

    # Set the interval in minutes (e.g., 30 minutes)
    interval_minutes = 30  # Set your desired interval here, e.g., 30 for 30 minutes
    schedule.every(interval_minutes).minutes.do(lambda: [fetch_and_store_weather_data_for_beach(beach) for beach in beaches])

    return interval_minutes

# Function to display the countdown timer
def countdown_timer(minutes):
    total_seconds = minutes * 60
    while total_seconds > 0:
        minutes_left = total_seconds // 60
        seconds_left = total_seconds % 60
        print(f"\r 🌊 Beach Data updating in {minutes_left:02d}:{seconds_left:02d} minutes 🏖️", end="")
        time.sleep(1)
        total_seconds -= 1
    print("\nFetching data now...\n")
    
# Main script execution
if __name__ == "__main__":
    # Start by fetching data immediately
    interval = fetch_weather_data()

    # Run the scheduler in a loop
    while True:
        # Run the countdown timer until the next fetch
        countdown_timer(interval)

        # Run pending scheduled jobs
        schedule.run_pending()
