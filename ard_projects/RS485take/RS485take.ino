#include <SoftwareSerial.h>
#include <ESP8266WiFi.h>
#include <WiFiClient.h>

#define PIN_RS485_RX 12
#define PIN_RS485_TX 13
#define ENABLE_PIN 14
#define WIFI_SSID "HUAWEI-A1-VV3CNJ_HiLink"
#define WIFI_PASS "65206647"
#define HOST "192.168.1.7"
#define PORT 8888

unsigned long previousSendTime = 0;
const unsigned long sendInterval = 1 * 60 * 1000; // Интервал отправки данных (5 минут)

SoftwareSerial Serial2(PIN_RS485_RX, PIN_RS485_TX); // RX, TX

void setup() {
  delay(10000);
  Serial.begin (9600);
  Serial2.begin (9600);

  connectToWiFi();

  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW);

  Serial.println ("Start ESP");
}

void loop() {
  Serial.print("received String: ");
  String receivedString = "";
  String sendString = "";

  if (Serial2.available() > 0){
    receivedString = Serial2.readStringUntil('\n');
    Serial.print(receivedString);
  }
  Serial.print("\n");

  if (receivedString.length() > 0){
    sendString = receivedString;
  }

  unsigned long currentTime = millis();
  if (currentTime - previousSendTime >= sendInterval) {
    sendSensorData(sendString);
    previousSendTime = currentTime;
  }
  
  delay(1000);
}

void connectToWiFi() {
  Serial.print("Connecting to Wi-Fi...");
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("Connected");
  Serial.println(WiFi.localIP());
}

void sendSensorData(String data) {
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    if (client.connect(HOST, PORT)) {
      Serial.println("Sending sensor data...");
      client.println(data);
      client.stop();
      Serial.println("Sensor data sent!");
    }
    else {
      Serial.println("Failed to connect to the host.");
    }
  }
  else {
    Serial.println("Wi-Fi not connected. Try to connect...");
    connectToWiFi();
  }
}