import requests

# URL to fetch data
url = "https://firestore.googleapis.com/v1/projects/samundar-sathi/databases/(default)/documents/one_b?key=AIzaSyD0D2q7LPlhZHphxKMYWwekTadpNQKGZ9k"

try:
    # Sending GET request to the URL
    response = requests.get(url)
    response.raise_for_status()  # Check for request errors
    data = response.json()  # Parse response as JSON
    
    # Extract the required information
    for document in data.get("documents", []):
        name = document.get("fields", {}).get("name", {}).get("stringValue")
        safety_score = document.get("fields", {}).get("safety_report", {}).get("mapValue", {}).get("fields", {}).get("safety_score", {}).get("integerValue")
        safety_reason = document.get("fields", {}).get("safety_report", {}).get("mapValue", {}).get("fields", {}).get("reasons", {}).get("arrayValue", {}).get("values", [])[0].get("stringValue")
        
        # Print the extracted data
        print(f"Beach Name: {name}")
        print(f"Safety Score: {safety_score}")
        print(f"Safety Reason: {safety_reason}")
except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
