/***************************************************************************
  This is a library for the BME280 humidity, temperature & pressure sensor
  Designed specifically to work with the Adafruit BME280 Breakout
  ----> http://www.adafruit.com/products/2650
  These sensors use I2C or SPI to communicate, 2 or 4 pins are required
  to interface. The device's I2C address is either 0x76 or 0x77.
  Adafruit invests time and resources providing this open source code,
  please support Adafruit andopen-source hardware by purchasing products
  from Adafruit!
  Written by Limor Fried & Kevin Townsend for Adafruit Industries.
  BSD license, all text above must be included in any redistribution
  See the LICENSE file for details.
 ***************************************************************************/
#include <Wire.h>
#include <SPI.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <SerialCommand.h>
#include <SoftwareSerial.h>


#define BME_SCK 13
#define BME_MISO 12
#define BME_MOSI 11
#define BME_CS 10
#define SEALEVELPRESSURE_HPA (1013.25)
int DEBUG=0;

Adafruit_BME280 bme; // I2C
SerialCommand SCmd;
const float VERSION = 1.2;

unsigned long delayTime;
void setup() {
    Serial.begin(9600);
    while(!Serial);    // time to get serial running
    
    unsigned status;
    // default settings
    status = bme.begin();  
    // You can also pass in a Wire library object like &Wire2
    // status = bme.begin(0x76, &Wire2)
    if (status) {
        if (DEBUG) {
          Serial.print("DEBUG: SensorID is: 0x");
          Serial.println(bme.sensorID(),16);
        }
    } else {
        Serial.println("ERROR: Could not find a valid BME280 sensor, check wiring, address, sensor ID!");
        while (1) delay(10);
    }
//    Serial.println("-- Default Test --");
    delayTime = 1000;
    Serial.println();
    SCmd.addCommand("T", teach);
    SCmd.addCommand("D", printValues);
    
}
void loop() { 
    SCmd.readSerial(); 
    delay(250);
    delay(delayTime);
}
void printValues() {
    Serial.print("{");
    Serial.print("\"temperature\": ");
    Serial.print(bme.readTemperature());
    Serial.print(",");
    Serial.print("\"pressure\": ");
    Serial.print(bme.readPressure() / 100.0F);
    Serial.print(",");
    Serial.print("\"altitude\": ");
    Serial.print(bme.readAltitude(SEALEVELPRESSURE_HPA));
    Serial.print(",");
    Serial.print("\"humidity\": ");
    Serial.print(bme.readHumidity());
    Serial.print(",");
    Serial.print("\"light\": ");
    int light = analogRead(A0); 
    Serial.print(light);
    Serial.print("}");
    Serial.println();  
}


void teach() {
  Serial.print("{\"name\": \"Environmental sensor\", \"version\": \"");
  Serial.print(VERSION);
  Serial.println("\"}");
}