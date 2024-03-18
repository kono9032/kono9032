#include <SoftwareSerial.h>
#include <Wire.h>
#include <Adafruit_MLX90614.h>
#include <MsTimer2.h>
#include <SPI.h>
#include <MFRC522.h>
#include "U8glib.h"
#define SS_PIN 10
#define RST_PIN 9
U8GLIB_SSD1306_128X64 u8g(U8G_I2C_OPT_NONE);

SoftwareSerial BTSerial(5, 4); //TXD,RXD
Adafruit_MLX90614 mlx = Adafruit_MLX90614();
MFRC522 rfid(SS_PIN, RST_PIN);
MFRC522::MIFARE_Key key;

String RFID_uid;
int t , count, count2, temperature_button , ic = 0;
float list[3], value;
byte nuidPICC[4];

const uint8_t icon[] PROGMEM = {
  0xFE, 0x00, 0x03, 0x00, 0x92, 0x00, 0x02, 0x80, 0x54, 0x00, 0x0A, 0x40, 0x38, 0x04, 0x06, 0x80,
  0x10, 0x14, 0x03, 0x00, 0x10, 0x54, 0x06, 0x80, 0x11, 0x54, 0x0A, 0x40, 0x15, 0x54, 0x02, 0x80,
  0x15, 0x54, 0x03, 0x00,
};

void setup() {
  oled_boot();
  attachInterrupt(digitalPinToInterrupt(2), interrupt, RISING);
  pinMode(2, INPUT_PULLUP);
  pinMode(6, OUTPUT);
  Serial.begin(9600);
  BTSerial.begin(9600);
  SPI.begin();
  rfid.PCD_Init();
  mlx.begin();
  Vibration_boot();
  oled_image();
  Serial.println("Ready");
  temperature_button = 0;
}

void flash() {
  Serial.println(count);
  count ++;
  count2 = 1;
}

void interrupt() {
  temperature_button = 1;
}

void printDec(byte *buffer, byte bufferSize) {
  BTSerial.print("BC");
  RFID_uid = "";
  for (byte i = 0; i < bufferSize; i++) {
    char c[2];
    ltoa(buffer[i], c, 16);
    if (buffer[i] < 0x10)
    {
      RFID_uid = RFID_uid + "0";
    }
    RFID_uid = RFID_uid + c;
    BTSerial.print(buffer[i] < 0x10 ? "0" : "");
    BTSerial.print(buffer[i], HEX);
  }
  BTSerial.print("Z");
}

void loop() {
  if (temperature_button != 0) {
    if (ic == 0) {
      for (int i = 0; i < 3; i++) {
        list[i] = i;
      }
      MsTimer2::set(1000, flash);
      MsTimer2::start();
      ic = 1;
    }
    float tmp = mlx.readObjectTempC()*0.75;
    if (tmp > 20) list[count] = tmp;
    if (int(list[0]) == int(list[1]) && int(list[1]) == int(list[2]))
    {
      if (t == 0) {
        value = (list[0] + list[1] + list[2]) / 3.0;
        BTSerial.println("BT" + String(value) + "Z");
        Serial.print("Object = "); Serial.println(value);
        MsTimer2::stop();
        t = 1;
        temperature_button = 0;
        ic = 0;
        count = 0;
        count2 = 0;
        Vibration_measuring();
        oled_image();
      } else {
        t = 0;
      }
    }
    else if (count2 == 1)
    {
      digitalWrite(6, HIGH);
      delay(50);
      digitalWrite(6, LOW);
      count2 = 0;
    }
  }
  if (count == 3) {
    count = 0;
  }

  if ( ! rfid.PICC_IsNewCardPresent())
    return;
  if ( ! rfid.PICC_ReadCardSerial())
    return;
  printDec(rfid.uid.uidByte, rfid.uid.size);
  Serial.println();
  BTSerial.println();
  Vibration_measuring();
  oled_image();
  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}
