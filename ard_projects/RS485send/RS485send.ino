#include <SoftwareSerial.h>
#include <MQ135.h>
#include <DHT.h>
#include <string.h>

#define ID_OF_ARDUINO "1"
#define PIN_RS485_RX 12
#define PIN_RS485_TX 13
#define ENABLE_PIN 11
#define PIN_MQ135 A0 // MQ135 Analog Input Pin
#define DHTPIN 4 // DHT Digital Input Pin
#define DHTTYPE DHT11 // DHT11 or DHT22, depends on your sensor
#define PHOTOPIN A1 // Photo Resistor Analog Input Pin

SoftwareSerial Serial2(PIN_RS485_RX, PIN_RS485_TX); // RX, TX
MQ135 mq135_sensor(PIN_MQ135);
DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  Serial2.begin(9600);
  dht.begin();

  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, HIGH);

  Serial.println("Start program");
}

void loop() {
  Serial.println("Transmitting");

  String data = readSensorData();
  Serial2.println(data);
  Serial.println(data);

  delay(2000);
}

String readSensorData() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  float rzero = mq135_sensor.getRZero();
  float correctedRZero = mq135_sensor.getCorrectedRZero(temperature, humidity);
  float resistance = mq135_sensor.getResistance();
  float ppm = mq135_sensor.getPPM();
  float correctedPPM = mq135_sensor.getCorrectedPPM(temperature, humidity);
  float luminosity = analogRead(PHOTOPIN);

  // Создание строки с данными
  String data = ID_OF_ARDUINO;
  data += "/" + String(temperature);
  data += "/" + String(humidity);
  data += "/" + String(rzero);
  data += "/" + String(correctedRZero);
  data += "/" + String(resistance);
  data += "/" + String(ppm*10);
  data += "/" + String(correctedPPM*10);
  data += "/" + String(map(luminosity, 0, 1000, 1, 100)) + "\n";

  return data;
}