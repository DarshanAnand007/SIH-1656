import requests

# Define the API endpoint and your API key
api_url = 'https://api.stormglass.io/v2/weather/point'
api_key = 'e3b3ed8e-6a77-11ef-a732-0242ac130004-e3b3edf2-6a77-11ef-a732-0242ac130004'

# Set the parameters for Visakhapatnam Beach (latitude and longitude)
params = {
    'lat': 17.6868,  # Latitude for Visakhapatnam Beach
    'lng': 83.2185,  # Longitude for Visakhapatnam Beach
    'params': ','.join([
        'waveHeight',       # Wave Heights
        'currentSpeed',     # Ocean Currents
        'windSpeed',        # Wind Speed
        'airTemperature',   # Air Temperature
        'waterTemperature', # Water Temperature (added this in case it’s more appropriate than air temperature)
        'tide'              # Tidal Information
    ])
}

# Set the headers, including your API key for authorization
headers = {
    'Authorization': api_key
}

# Make the GET request to the Storm Glass API
response = requests.get(api_url, params=params, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Parse the JSON response
    json_data = response.json()

    # Extract data for the first hour in the response
    first_hour = json_data['hours'][0]

    # Print the beach name and the relevant data
    beach_name = "Visakhapatnam Beach"
    print(f"Location: {beach_name}")
    print(f"Time: {first_hour['time']}")
    print(f"Wave Height: {first_hour.get('waveHeight', {}).get('sg', 'N/A')} meters")
    print(f"Ocean Currents Speed: {first_hour.get('currentSpeed', {}).get('sg', 'N/A')} m/s")
    print(f"Wind Speed: {first_hour.get('windSpeed', {}).get('sg', 'N/A')} m/s")
    print(f"Air Temperature: {first_hour.get('airTemperature', {}).get('sg', 'N/A')} °C")
    print(f"Water Temperature: {first_hour.get('waterTemperature', {}).get('sg', 'N/A')} °C")
    print(f"Tidal Information: {first_hour.get('tide', {}).get('sg', 'N/A')} meters")
else:
    # Print an error message if the request failed
    print(f"Error: Unable to fetch data, status code {response.status_code}")
