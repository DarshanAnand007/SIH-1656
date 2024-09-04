import requests

# Define the API endpoint and your API key
api_url = 'https://api.stormglass.io/v2/weather/point'
api_key = 'e3b3ed8e-6a77-11ef-a732-0242ac130004-e3b3edf2-6a77-11ef-a732-0242ac130004'

# Define a list of beaches with their names and coordinates
beaches = [
    {"name": "Visakhapatnam Beach", "lat": 17.6868, "lng": 83.2185},
    {"name": "Marina Beach, Chennai", "lat": 13.0500, "lng": 80.2824},
    {"name": "Elliot's Beach, Chennai", "lat": 12.9907, "lng": 80.2664},
    {"name": "Thiruvanmiyur Beach, Chennai", "lat": 12.9793, "lng": 80.2597}
]

# Loop through each beach and fetch the wave height data
for beach in beaches:
    # Set the parameters for the current beach
    params = {
        'lat': beach['lat'],
        'lng': beach['lng'],
        'params': 'waveHeight',  # Parameter(s) you want to retrieve
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

        # Extract the wave height for the first hour in the response
        first_hour = json_data['hours'][0]  # Get the data for the first hour
        wave_height = first_hour['waveHeight']['sg']  # Extract the wave height from Storm Glass ('sg')

        # Print the beach name and wave height
        print(f"Location: {beach['name']}")
        print(f"Wave Height at {first_hour['time']}: {wave_height} meters")
        print("")  # Print a newline for readability
    else:
        # Print an error message if the request failed
        print(f"Error: Unable to fetch data for {beach['name']}, status code {response.status_code}")
        print("")  # Print a newline for readability
