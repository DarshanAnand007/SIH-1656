import requests
from bs4 import BeautifulSoup

# URL of the INCOIS water quality page
url = "https://incois.gov.in/portal/wqns/water_quality.jsp"

# Send a GET request to the URL
response = requests.get(url)

# Parse the HTML content of the page
soup = BeautifulSoup(response.content, "html.parser")

# Extract specific data
# For this example, I'm assuming you want to extract data from paragraphs <p> tags
# You can modify this based on the actual HTML structure of the page
water_quality_data = soup.find_all('p')  # Adjust the tag and class based on the actual HTML structure

# Print the extracted data
for item in water_quality_data:
    print(item.text)
