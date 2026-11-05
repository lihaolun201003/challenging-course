#include <Arduino.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include <stdio.h>
#include "air_config.h"
#include "air_bluetooth.h"
#include "air_alarm.h"
#include "pms5003st.h"
#include "boot_animation.h"
#include "boot_display.h"
#include "naiwa_ui.h"

namespace {
constexpr uint8_t TFT_CS = PB6;   // D10
constexpr uint8_t TFT_DC = PB5;   // D4
constexpr uint8_t TFT_RST = PA8;  // D7
constexpr uint8_t BUZZER_PIN = PB10;  // D6, active HIGH; module VCC is 5V.
constexpr uint32_t TFT_SPI_HZ = 8000000;
constexpr uint32_t STALE_MS = AirTelemetry::STALE_MS;

BootDisplay lcd(&SPI, TFT_DC, TFT_CS, TFT_RST);
NaiwaUi ui(lcd);
// STM32duino 3.0 calls its concrete serial class Uart.
// PA10 receives sensor TXD. PA9 is the required UART TX pin but is UNCONNECTED.
// Never use USART1's automatic pin selection: PB6 is already LCD CS.
Uart sensor(PA10, PA9);
Pms5003stParser parser;
PmsReading latest;
#if AIR_ENABLE_BLUETOOTH
AirBluetooth bluetooth;
#if AIR_BLUETOOTH_UART6
// USART6 on direct Morpho pins: RX PA12/CN10-12, TX PA11/CN10-14.
Uart bluetoothSerial(PA12, PA11);
#else
// Reuse the core USART2 instance instead of creating another UART on it.
Uart &bluetoothSerial = Serial;
#endif
#endif
bool hasFrame = false;
uint32_t receivedBytes = 0;
uint32_t lastFrameMs = 0;
uint32_t sessionStartMs = 0;
uint32_t lastUiMs = 0;
#if AIR_ENABLE_SERIAL_LOG
uint32_t lastLogMs = 0;
#endif
bool buzzerSounding = false;

AirTelemetry telemetry() {
  AirTelemetry sample;
  sample.reading = latest;
  sample.hasFrame = hasFrame;
  sample.lastFrameMs = lastFrameMs;
  sample.sessionStartMs = sessionStartMs;
  sample.frames = parser.frames;
  sample.badFrames = parser.checksumErrors + parser.lengthErrors;
  return sample;
}

void tenths(char *out, size_t capacity, int32_t value) {
  const bool negative = value < 0;
  const uint32_t magnitude = negative ? -value : value;
  snprintf(out, capacity, "%s%lu.%lu", negative ? "-" : "",
           static_cast<unsigned long>(magnitude / 10),
           static_cast<unsigned long>(magnitude % 10));
}

void hchoText(char *out, size_t capacity, uint16_t value) {
  snprintf(out, capacity, "%u.%03u", static_cast<unsigned>(value / 1000),
           static_cast<unsigned>(value % 1000));
}

void updateUi(uint32_t now) {
#if AIR_ENABLE_BLUETOOTH
  ui.update(telemetry(), now, true, bluetooth.streamEnabled(), buzzerSounding);
#else
  ui.update(telemetry(), now, false, false, buzzerSounding);
#endif
}

void logReading() {
#if AIR_ENABLE_SERIAL_LOG
  char temperature[16], humidity[16], hcho[16], line[180];
  tenths(temperature, sizeof(temperature), latest.temperatureTenths);
  tenths(humidity, sizeof(humidity), latest.humidityTenths);
  hchoText(hcho, sizeof(hcho), latest.hchoUgM3);
  snprintf(line, sizeof(line),
           "PMS frame=%lu PM1=%u PM2.5=%u PM10=%u ug/m3 TEMP=%s C RH=%s %% HCHO=%s mg/m3 FW=%u ERR=%u",
           static_cast<unsigned long>(parser.frames), latest.pm1, latest.pm25,
           latest.pm10, temperature, humidity, hcho, latest.version, latest.error);
  Serial.println(line);
  if (parser.frames <= 2) {
    Serial.print(F("PMS RAW:"));
    const uint8_t *raw = parser.frameBytes();
    for (size_t i = 0; i < Pms5003stParser::FRAME_SIZE; ++i) {
      Serial.print(' ');
      if (raw[i] < 16) Serial.print('0');
      Serial.print(raw[i], HEX);
    }
    Serial.println();
  }
#endif
}

void readSensor() {
  while (sensor.available() > 0) {
    const int byte = sensor.read();
    if (byte < 0) break;
    ++receivedBytes;
    PmsReading reading;
    const uint32_t now = millis();
    if (parser.feed(static_cast<uint8_t>(byte), now, reading)) {
      if (!hasFrame || static_cast<uint32_t>(now - lastFrameMs) >= STALE_MS ||
          (latest.error && !reading.error)) {
        sessionStartMs = now;
      }
      latest = reading;
      hasFrame = true;
      lastFrameMs = now;
      logReading();
    }
  }
}

void updateHchoAlarm(uint32_t now) {
  const AirTelemetry sample = telemetry();
  const bool shouldSound = hchoAlarmShouldSound(sample, now);
  if (shouldSound == buzzerSounding) return;
  digitalWrite(BUZZER_PIN, shouldSound ? HIGH : LOW);
  buzzerSounding = shouldSound;
#if AIR_ENABLE_SERIAL_LOG
  char line[112];
  snprintf(line, sizeof(line),
           "HCHO ALARM %s raw_ug_m3=%u threshold_ug_m3=%u state=%s",
           shouldSound ? "ON" : "OFF", sample.reading.hchoUgM3,
           HCHO_ALARM_THRESHOLD_UG_M3, airStatusName(sample.status(now)));
  Serial.println(line);
#endif
}

// The animation also calls this service between strips and while waiting.
void serviceIo() {
  readSensor();
  // Capture time after reception so a newly published frame is never in the future.
  const uint32_t now = millis();
  updateHchoAlarm(now);
#if AIR_ENABLE_BLUETOOTH
  bluetooth.poll(bluetoothSerial, telemetry(), now);
#endif
}
}  // namespace

void setup() {
  digitalWrite(BUZZER_PIN, LOW);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  // USART2 is either the Bluetooth link or the ST-Link diagnostic console.
  Serial.setRx(PA3);
  Serial.setTx(PA2);
#if AIR_ENABLE_BLUETOOTH && !AIR_BLUETOOTH_UART6
  Serial.begin(AIR_BLUETOOTH_BAUD, SERIAL_8N1);  // HC-06, PA3 RX / PA2 TX.
#else
  Serial.begin(115200);  // ST-Link debug console, USART2 PA2/PA3.
#endif
#if AIR_ENABLE_BLUETOOTH && AIR_BLUETOOTH_UART6
  bluetoothSerial.begin(AIR_BLUETOOTH_BAUD, SERIAL_8N1);
  Serial.print(F("BLINKER UART6: module RXD -> PA11/CN10-14, TXD -> PA12/CN10-12, "));
  Serial.print(AIR_BLUETOOTH_BAUD);
  Serial.println(F(" 8N1"));
#endif
  sensor.begin(9600, SERIAL_8N1);
#if AIR_ENABLE_SERIAL_LOG
  Serial.println(F("\r\nAIR PMS5003ST monitor boot"));
  Serial.println(F("PMS TXD -> D2/PA10, VCC=5V, GND=GND; active receive only"));
  Serial.println(F("LCD CS=PB6 DC=PB5 RESET=PA8 SCK=PA5 MOSI=PA7 LED=3V3"));
  Serial.println(F("BUZZER D6/PB10 active HIGH, VCC=5V: HCHO > 0.030 mg/m3"));
#endif

  SPI.setSCLK(PA5);
  SPI.setMOSI(PA7);
  SPI.setMISO(PA6);
  lcd.begin(TFT_SPI_HZ);
  lcd.setRotation(1);
  lcd.invertDisplay(false);
  playBootAnimation(lcd, serviceIo);
  serviceIo();
  ui.begin(serviceIo);
  // Re-read after static UI rendering so status uses a current timestamp.
  serviceIo();
  lastUiMs = millis();
  updateUi(lastUiMs);
#if AIR_ENABLE_SERIAL_LOG
  Serial.println(F("UI: NAIWA_COMPANION 320x240, localized refresh"));
  Serial.println(F("BOOT monitor: ready"));
#endif
}

void loop() {
  serviceIo();
  const uint32_t now = millis();
  if (static_cast<uint32_t>(now - lastUiMs) >= 500) {
    lastUiMs = now;
    updateUi(now);
  }
#if AIR_ENABLE_SERIAL_LOG
  if (static_cast<uint32_t>(now - lastLogMs) >= 5000) {
    lastLogMs = now;
    char line[160];
    snprintf(line, sizeof(line),
             "PMS status: rx=%lu valid=%lu checksum_bad=%lu length_bad=%lu partial_timeout=%lu age_ms=%lu",
             static_cast<unsigned long>(receivedBytes),
             static_cast<unsigned long>(parser.frames),
             static_cast<unsigned long>(parser.checksumErrors),
             static_cast<unsigned long>(parser.lengthErrors),
             static_cast<unsigned long>(parser.timeouts),
             static_cast<unsigned long>(hasFrame ? now - lastFrameMs : now));
    Serial.println(line);
  }
#endif
}
