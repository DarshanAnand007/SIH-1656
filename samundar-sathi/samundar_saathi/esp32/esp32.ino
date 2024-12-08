#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Wi-Fi credentials
const char* ssid = "ANAND N";        // Replace with your Wi-Fi SSID
const char* password = "8971878807";  // Replace with your Wi-Fi password

// API endpoint
const char* url = "https://v1.nocodeapi.com/samundarsuraksha/fbsdk/OjCtcgqEGzplhVcp/firestore/allDocuments?collectionName=one_b";

// LED and Buzzer pins
const int greenLED = 4;   // Pin for green LED
const int yellowLED = 2;  // Pin for yellow LED
const int redLED = 15;    // Pin for red LED
const int buzzer = 19;    // Pin for the buzzer

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Set up LED and Buzzer pins
  pinMode(greenLED, OUTPUT);
  pinMode(yellowLED, OUTPUT);
  pinMode(redLED, OUTPUT);
  pinMode(buzzer, OUTPUT);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");

  // Fetch and print beach safety data
  fetchData();
}

void fetchData() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(url);

    int httpResponseCode = http.GET();

    if (httpResponseCode > 0) {
      String payload = http.getString();
      Serial.println("Data fetched successfully!");

      // Parsing JSON response
      DynamicJsonDocument doc(1024);
      deserializeJson(doc, payload);

      // Extract data
      const char* beachName = doc[0]["_fieldsProto"]["name"]["stringValue"];
      int safetyScore = doc[0]["_fieldsProto"]["safety_report"]["mapValue"]["fields"]["safety_score"]["integerValue"].as<int>();
      const char* safetyMessage = doc[0]["_fieldsProto"]["safety_report"]["mapValue"]["fields"]["safety_message"]["stringValue"];
      const char* firstReason = doc[0]["_fieldsProto"]["safety_report"]["mapValue"]["fields"]["reasons"]["arrayValue"]["values"][0]["stringValue"];

      // Print data
      Serial.print("Beach Name: ");
      Serial.println(beachName);
      Serial.print("Safety Score: ");
      Serial.println(safetyScore);
      Serial.print("Safety Message: ");
      Serial.println(safetyMessage);
      Serial.print("Reason: ");
      Serial.println(firstReason);

      // Set LED and buzzer based on safety score
      if (safetyScore > 8) { // Green: Safe
        digitalWrite(greenLED, HIGH);
        digitalWrite(yellowLED, LOW);
        digitalWrite(redLED, LOW);
        digitalWrite(buzzer, LOW);  // Deactivate buzzer
      } else if (safetyScore > 5 && safetyScore <= 8) { // Yellow: Moderate caution
        digitalWrite(greenLED, LOW);
        digitalWrite(yellowLED, HIGH);
        digitalWrite(redLED, LOW);
        digitalWrite(buzzer, LOW);  // Deactivate buzzer
      } else { // Red: High caution
        digitalWrite(greenLED, LOW);
        digitalWrite(yellowLED, LOW);
        digitalWrite(redLED, HIGH);
        digitalWrite(buzzer, HIGH); // Activate buzzer
      }

    } else {
      Serial.print("Error in HTTP request: ");
      Serial.println(httpResponseCode);
    }
    http.end();
  } else {
    Serial.println("WiFi Disconnected");
  }
}

void loop() {
  // Call fetchData() in the loop at intervals to keep updating the LED and buzzer
  delay(300000);  // Delay 5 minutes (300000 ms) between fetches
  fetchData();
}