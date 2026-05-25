// ESP32: Connect to Wi-Fi, power GPIO 18 for 30 seconds every 3 minutes,
// and send a Firebase POST request whenever GPIO 18 is turned ON.

#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>

#define SENSOR_POWER_PIN 18

const char* WIFI_SSID = "Lordly iPhone";
const char* WIFI_PASSWORD = "hello123";

const char* FIREBASE_URL = "https://test-c7bf3-default-rtdb.firebaseio.com/alerts.json";

const char* KIT_OWNER = "ChatGPT Test";
const char* SENSOR_ID = "TEST-SENSOR-001";

const unsigned long POWER_ON_DURATION_MS = 30UL * 1000UL;        // 30 seconds
const unsigned long CYCLE_DURATION_MS = 3UL * 60UL * 1000UL;     // 3 minutes

void connectToWiFi() {
  Serial.print("Connecting to Wi-Fi: ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("Wi-Fi connected.");
  Serial.print("ESP32 IP address: ");
  Serial.println(WiFi.localIP());
}

void sendFirebasePost() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi disconnected. Reconnecting...");
    connectToWiFi();
  }

  WiFiClientSecure client;
  client.setInsecure();

  HTTPClient http;

  Serial.println("Sending POST request to Firebase...");

  http.begin(client, FIREBASE_URL);
  http.addHeader("Content-Type", "application/json");

  String jsonBody = "{";
  jsonBody += "\"kitOwner\":\"";
  jsonBody += KIT_OWNER;
  jsonBody += "\",";
  jsonBody += "\"sensorId\":\"";
  jsonBody += SENSOR_ID;
  jsonBody += "\",";
  jsonBody += "\"powerSentAt\":{";
  jsonBody += "\".sv\":\"timestamp\"";
  jsonBody += "}";
  jsonBody += "}";

  int httpResponseCode = http.POST(jsonBody);

  Serial.print("HTTP response code: ");
  Serial.println(httpResponseCode);

  String response = http.getString();
  Serial.println("Firebase response:");
  Serial.println(response);

  http.end();
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(SENSOR_POWER_PIN, OUTPUT);
  digitalWrite(SENSOR_POWER_PIN, LOW);

  connectToWiFi();

  Serial.println("System ready.");
}

void loop() {
  unsigned long cycleStartTime = millis();

  Serial.println("Turning GPIO 18 ON.");
  digitalWrite(SENSOR_POWER_PIN, HIGH);

  sendFirebasePost();

  delay(POWER_ON_DURATION_MS);

  Serial.println("Turning GPIO 18 OFF.");
  digitalWrite(SENSOR_POWER_PIN, LOW);

  unsigned long elapsedTime = millis() - cycleStartTime;

  if (elapsedTime < CYCLE_DURATION_MS) {
    unsigned long remainingTime = CYCLE_DURATION_MS - elapsedTime;

    Serial.print("Waiting before next cycle: ");
    Serial.print(remainingTime / 1000);
    Serial.println(" seconds.");

    delay(remainingTime);
  }
}
