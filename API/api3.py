from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# Set up Selenium WebDriver (Assuming you have ChromeDriver installed)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode
service = Service('/path/to/chromedriver')  # Update path to your chromedriver
driver = webdriver.Chrome(service=service, options=chrome_options)

# Navigate to the INCOIS wave data page
url = 'https://incois.gov.in/portal/waveForecast.jsp'
driver.get(url)

# Wait for the page to load
time.sleep(5)  # You may need to adjust this depending on the page load time

# Example: Scrape data from a specific element
wave_data_element = driver.find_element_by_id('waveDataTable')  # Replace with actual element ID
print(wave_data_element.text)

# Clean up and close the driver
driver.quit()
