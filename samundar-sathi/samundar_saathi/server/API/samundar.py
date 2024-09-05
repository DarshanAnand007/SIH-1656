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
    {"name": "Om Beach", "latitude": 14.5230, "longitude": 74.3184},  # Om Beach, Gokarna, Karnataka
    {"name": "Tarkarli Beach", "latitude": 16.0363, "longitude": 73.4702}   # Tarkarli, Maharashtra
]

# Updated Point System Algorithm with Reasons for Both Safe and Unsafe Conditions
def assess_beach_safety(wave_height, wind_wave_height, ocean_current_velocity, 
                           wave_height_max=None, wind_wave_height_max=None):
    
    # Define thresholds for each parameter
    thresholds = {
        "safe_wave_height": 1.5,
        "moderate_wave_height": 3.0,
        "safe_wind_wave_height": 1.5,
        "moderate_wind_wave_height": 3.0,
        "safe_ocean_current_velocity": 1.0,
        "moderate_ocean_current_velocity": 2.0,
        "safe_wave_height_max": 1.7,
        "moderate_wave_height_max": 3.0
    }
    
    # Start with a perfect score of 10
    safety_score = 10
    reason = []  # Reasons for the beach safety status
    unsafe_reason = []  # Collect reasons if the beach is unsafe
    safe_reason = []  # Collect reasons if the beach is safe

    # Deduct points for wave height
    if wave_height:
        if wave_height > thresholds["moderate_wave_height"]:
            safety_score -= 4  # High risk, strong deduction
            reason.append(f"Wave height is {wave_height:.2f} meters, which is highly dangerous.")
            unsafe_reason.append("The wave height is too high, increasing the risk of dangerous currents and strong waves.")
        elif wave_height > thresholds["safe_wave_height"]:
            safety_score -= 2  # Moderate risk
            reason.append(f"Wave height is {wave_height:.2f} meters, exceeding the safe limit by {wave_height - thresholds['safe_wave_height']:.2f} meters.")
            unsafe_reason.append("The wave height exceeds safe limits, which may pose a risk.")
        else:
            safe_reason.append(f"Wave height is {wave_height:.2f} meters, which is within the safe limit.")

    # Deduct points for wind wave height
    if wind_wave_height:
        if wind_wave_height > thresholds["moderate_wind_wave_height"]:
            safety_score -= 4  # High risk, strong deduction
            reason.append(f"Wind wave height is {wind_wave_height:.2f} meters, which is highly dangerous.")
            unsafe_reason.append("The wind wave height is too high, making the conditions unstable and hazardous.")
        elif wind_wave_height > thresholds["safe_wind_wave_height"]:
            safety_score -= 2  # Moderate risk
            reason.append(f"Wind wave height is {wind_wave_height:.2f} meters, exceeding the safe limit by {wind_wave_height - thresholds['safe_wind_wave_height']:.2f} meters.")
            unsafe_reason.append("The wind wave height exceeds safe limits, posing a moderate risk.")
        else:
            safe_reason.append(f"Wind wave height is {wind_wave_height:.2f} meters, which is within the safe limit.")

    # Deduct points for ocean current velocity
    if ocean_current_velocity:
        if ocean_current_velocity > thresholds["moderate_ocean_current_velocity"]:
            safety_score -= 3  # High risk
            reason.append(f"Ocean current velocity is {ocean_current_velocity:.2f} m/s, which is highly dangerous.")
            unsafe_reason.append("The ocean current velocity is too strong, increasing the risk of being swept away.")
        elif ocean_current_velocity > thresholds["safe_ocean_current_velocity"]:
            safety_score -= 1.5  # Moderate risk
            reason.append(f"Ocean current velocity is {ocean_current_velocity:.2f} m/s, exceeding the safe limit by {ocean_current_velocity - thresholds['safe_ocean_current_velocity']:.2f} m/s.")
            unsafe_reason.append("The ocean current velocity exceeds the safe limits, posing a moderate risk.")
        else:
            safe_reason.append(f"Ocean current velocity is {ocean_current_velocity:.2f} m/s, which is within the safe limit.")

    # Deduct points for max wave height
    if wave_height_max:
        if wave_height_max > thresholds["moderate_wave_height_max"]:
            safety_score -= 2  # High risk, but less frequent
            reason.append(f"Maximum daily wave height is {wave_height_max:.2f} meters, which is highly dangerous.")
            unsafe_reason.append("The maximum wave height for the day is very high, increasing the potential danger.")
        elif wave_height_max > thresholds["safe_wave_height_max"]:
            safety_score -= 1  # Moderate risk
            reason.append(f"Maximum daily wave height is {wave_height_max:.2f} meters, exceeding the safe limit by {wave_height_max - thresholds['safe_wave_height_max']:.2f} meters.")
            unsafe_reason.append("The maximum wave height exceeds safe limits, which may pose a moderate risk.")
        else:
            safe_reason.append(f"Maximum daily wave height is {wave_height_max:.2f} meters, which is within the safe limit.")

    # Ensure score stays within valid range (0-10)
    safety_score = max(min(safety_score, 10), 0)

    # Assign safety message based on the score
    if safety_score >= 8:
        safety_message = "Safe"
        reason.insert(0, "The beach is safe based on current weather conditions.")
        reason.extend(safe_reason)
    elif safety_score >= 5:
        safety_message = "Moderately safe, caution advised."
        reason.insert(0, "The beach is moderately safe, but caution is advised.")
    else:
        safety_message = "Unsafe"
        reason.insert(0, "The beach is unsafe based on current weather conditions.")
        reason.extend(unsafe_reason)
    
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
        wave_height=wave_height, wind_wave_height=wind_wave_height, 
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
