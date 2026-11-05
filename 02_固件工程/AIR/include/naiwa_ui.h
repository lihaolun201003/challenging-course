#pragma once

#include <Adafruit_ILI9341.h>
#include "air_bluetooth.h"

// A small, incremental renderer: the sensor and communications remain owned
// by main.cpp. The optional callback keeps their UARTs serviced while drawing.
class NaiwaUi {
 public:
  explicit NaiwaUi(Adafruit_ILI9341 &display) : lcd_(display) {}

  void begin(void (*service)() = nullptr);
  void update(const AirTelemetry &sample, uint32_t now,
              bool bluetoothEnabled, bool streamEnabled, bool alarmSounding);

 private:
  void service();
  void drawText(int16_t x, int16_t y, const char *text, uint16_t color);
  int16_t textWidth(const char *text) const;
  void drawNumber(uint8_t row, const char *text, uint16_t color);

  Adafruit_ILI9341 &lcd_;
  void (*service_)() = nullptr;
  char values_[6][16] = {};
  char sideLine1_[32] = {};
  char sideLine2_[32] = {};
  char footerState_[32] = {};
  char footerAge_[32] = {};
  char footerBluetooth_[32] = {};
  char bluetoothTag_[12] = {};
  uint16_t sideColor_ = 0;
  uint16_t footerColor_ = 0;
  bool lastAlarm_ = false;
};
