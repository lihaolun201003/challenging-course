#include "naiwa_ui.h"

#include <Fonts/FreeMonoBold9pt7b.h>
#include <Fonts/FreeMonoBold12pt7b.h>
#include <stdio.h>
#include <string.h>
#include "naiwa_ui_assets.h"

namespace {
constexpr uint16_t rgb565(uint8_t r, uint8_t g, uint8_t b) {
  return static_cast<uint16_t>(((r & 0xf8) << 8) |
                               ((g & 0xfc) << 3) | (b >> 3));
}
constexpr uint16_t BACKGROUND = rgb565(255, 249, 233);
constexpr uint16_t INK = rgb565(72, 59, 39);
constexpr uint16_t MUTED = rgb565(121, 109, 83);
constexpr uint16_t YELLOW = rgb565(255, 232, 161);
constexpr uint16_t SIDEBAR = rgb565(255, 241, 200);
constexpr uint16_t MINT = rgb565(229, 241, 232);
constexpr uint16_t LINE = rgb565(235, 223, 194);
constexpr uint16_t GREEN = rgb565(62, 113, 85);
constexpr uint16_t AMBER = rgb565(140, 100, 28);
constexpr uint16_t RED = rgb565(165, 77, 70);
constexpr int16_t VALUE_X = 218;
constexpr int16_t VALUE_RIGHT = 304;
constexpr int16_t VALUE_WIDTH = VALUE_RIGHT - VALUE_X + 1;
constexpr int16_t VALUE_HEIGHT = 24;

// The supplied font subset contains Chinese BMP characters. ASCII is rendered
// with GFX's built-in 6x8 font, so both scripts retain deterministic widths.
uint16_t nextCodepoint(const char *&text) {
  const uint8_t first = static_cast<uint8_t>(*text++);
  if (first < 0x80) return first;
  if ((first & 0xe0) == 0xc0 && text[0]) {
    const uint8_t second = static_cast<uint8_t>(*text++);
    return static_cast<uint16_t>(((first & 0x1f) << 6) | (second & 0x3f));
  }
  if ((first & 0xf0) == 0xe0 && text[0] && text[1]) {
    const uint8_t second = static_cast<uint8_t>(*text++);
    const uint8_t third = static_cast<uint8_t>(*text++);
    return static_cast<uint16_t>(((first & 0x0f) << 12) |
                                 ((second & 0x3f) << 6) | (third & 0x3f));
  }
  return '?';
}

void copyText(char *target, size_t capacity, const char *source) {
  snprintf(target, capacity, "%s", source);
}

void formatTenths(char *out, size_t capacity, int32_t value) {
  const bool negative = value < 0;
  const uint32_t magnitude = negative ? static_cast<uint32_t>(-value)
                                      : static_cast<uint32_t>(value);
  snprintf(out, capacity, "%s%lu.%lu", negative ? "-" : "",
           static_cast<unsigned long>(magnitude / 10),
           static_cast<unsigned long>(magnitude % 10));
}
}  // namespace

void NaiwaUi::service() {
  if (service_) service_();
}

int16_t NaiwaUi::textWidth(const char *text) const {
  int16_t width = 0;
  while (*text) width += nextCodepoint(text) < 0x80 ? 6 : 12;
  return width;
}

void NaiwaUi::drawText(int16_t x, int16_t y, const char *text,
                       uint16_t color) {
  lcd_.setFont(nullptr);
  lcd_.setTextSize(1);
  lcd_.setTextColor(color);
  while (*text) {
    const uint16_t codepoint = nextCodepoint(text);
    if (codepoint < 0x80) {
      lcd_.setCursor(x, y + 2);
      lcd_.write(static_cast<uint8_t>(codepoint));
      x += 6;
      continue;
    }

    const NaiwaAssets::Glyph *glyph = nullptr;
    // There are fewer than 100 characters. Binary search also keeps status
    // updates short on slower boards; the assets are sorted by Unicode.
    size_t lo = 0, hi = NaiwaAssets::GLYPH_COUNT;
    while (lo < hi) {
      const size_t mid = lo + (hi - lo) / 2;
      const uint16_t candidate = pgm_read_word(&NaiwaAssets::glyphs[mid].unicode);
      if (candidate < codepoint) lo = mid + 1;
      else hi = mid;
    }
    if (lo < NaiwaAssets::GLYPH_COUNT &&
        pgm_read_word(&NaiwaAssets::glyphs[lo].unicode) == codepoint) {
      glyph = &NaiwaAssets::glyphs[lo];
    }
    if (glyph) {
      lcd_.startWrite();
      for (uint8_t row = 0; row < NaiwaAssets::GLYPH_HEIGHT; ++row) {
        const uint16_t bits = static_cast<uint16_t>(
            (pgm_read_byte(&glyph->bitmap[row * 2]) << 8) |
             pgm_read_byte(&glyph->bitmap[row * 2 + 1]));
        for (uint8_t column = 0; column < NaiwaAssets::GLYPH_WIDTH; ++column) {
          if (bits & (0x8000u >> column)) {
            lcd_.writePixel(x + column, y + row, color);
          }
        }
      }
      lcd_.endWrite();
    } else {
      // An absent glyph stays visible as a placeholder, never random bytes.
      lcd_.drawRect(x + 1, y + 1, 10, 10, color);
    }
    x += 12;
    service();
  }
}

void NaiwaUi::begin(void (*serviceCallback)()) {
  service_ = serviceCallback;
  memset(values_, 0, sizeof(values_));
  sideLine1_[0] = sideLine2_[0] = footerState_[0] = footerAge_[0] = '\0';
  footerBluetooth_[0] = bluetoothTag_[0] = '\0';
  sideColor_ = footerColor_ = 0;
  lastAlarm_ = false;
  lcd_.setTextWrap(false);

  // Never hold the CPU for a full-screen SPI transfer. Even during initial
  // drawing, the sensor, Bluetooth, and alarm are serviced every small strip.
  for (int16_t y = 0; y < 240; y += 16) {
    lcd_.fillRect(0, y, 320, 16, BACKGROUND);
    service();
  }
  lcd_.fillRect(0, 0, 320, 36, YELLOW);
  service();
  drawText(12, 11, "奶娃空气站", INK);
  drawText(92, 11, "AIR STATION", MUTED);
  service();
  lcd_.fillRoundRect(8, 44, 76, 164, 11, SIDEBAR);
  service();
  lcd_.drawRGBBitmap(8, 57, NaiwaAssets::mascot,
                     NaiwaAssets::MASCOT_WIDTH, NaiwaAssets::MASCOT_HEIGHT);
  service();
  lcd_.fillRoundRect(31, 192, 30, 3, 1, YELLOW);
  // PM2.5's yellow is emphasis only; no AQI or air-quality grade is inferred.
  lcd_.fillRoundRect(92, 72, 220, 26, 6, YELLOW);
  service();

  const char *labels[] = {"PM1.0", "PM2.5", "PM10", "温度", "湿度", "甲醛"};
  const char *units[] = {"ug/m3", "ug/m3", "ug/m3", "C", "%RH", "mg/m3"};
  for (uint8_t row = 0; row < 6; ++row) {
    const int16_t y = 46 + 27 * row;
    drawText(100, y + 6, labels[row], MUTED);
    const int16_t unitX = 210 - textWidth(units[row]);
    drawText(unitX, y + 6, units[row], MUTED);
    if (row == 3) {
      // Use a geometric degree sign rather than an encoding-dependent glyph.
      lcd_.drawCircle(unitX - 3, y + 9, 1, MUTED);
    }
    if (row != 1) lcd_.drawFastHLine(100, y + 25, 205, LINE);
    service();
  }
  lcd_.fillRoundRect(8, 216, 304, 18, 7, MINT);
  service();
}

void NaiwaUi::drawNumber(uint8_t row, const char *text, uint16_t color) {
  const int16_t y = 47 + 27 * row;
  const uint16_t background = row == 1 ? YELLOW : BACKGROUND;
  lcd_.fillRect(VALUE_X, y, VALUE_WIDTH, VALUE_HEIGHT, background);
  lcd_.setTextSize(1);
  lcd_.setFont(&FreeMonoBold12pt7b);

  int16_t bx, by;
  uint16_t width, height;
  lcd_.getTextBounds(text, 0, 0, &bx, &by, &width, &height);
  if (width > VALUE_WIDTH || height > VALUE_HEIGHT) {
    // The full int16/uint16 ranges, including -3276.8 and 65.535, fit at 9pt.
    lcd_.setFont(&FreeMonoBold9pt7b);
    lcd_.getTextBounds(text, 0, 0, &bx, &by, &width, &height);
  }
  lcd_.setTextColor(color);
  lcd_.setCursor(VALUE_RIGHT + 1 - static_cast<int16_t>(width) - bx,
                 y + (VALUE_HEIGHT - static_cast<int16_t>(height)) / 2 - by);
  lcd_.print(text);
  lcd_.setFont(nullptr);
  service();
}

void NaiwaUi::update(const AirTelemetry &sample, uint32_t now,
                     bool bluetoothEnabled, bool streamEnabled,
                     bool alarmSounding) {
  const AirStatus state = sample.status(now);
  const bool visible = sample.valuesVisible(now);
  char value[16];
  for (uint8_t row = 0; row < 6; ++row) {
    if (!visible) {
      copyText(value, sizeof(value), "--");
    } else {
      switch (row) {
        case 0: snprintf(value, sizeof(value), "%u", sample.reading.pm1); break;
        case 1: snprintf(value, sizeof(value), "%u", sample.reading.pm25); break;
        case 2: snprintf(value, sizeof(value), "%u", sample.reading.pm10); break;
        case 3: formatTenths(value, sizeof(value), sample.reading.temperatureTenths); break;
        case 4: formatTenths(value, sizeof(value), sample.reading.humidityTenths); break;
        case 5:
          snprintf(value, sizeof(value), "%u.%03u",
                   sample.reading.hchoUgM3 / 1000,
                   sample.reading.hchoUgM3 % 1000);
          break;
      }
    }
    if (strcmp(values_[row], value) || (row == 5 && alarmSounding != lastAlarm_)) {
      drawNumber(row, value, row == 5 && alarmSounding ? RED : INK);
      copyText(values_[row], sizeof(values_[row]), value);
    }
    service();
  }
  lastAlarm_ = alarmSounding;

  const char *first = "我在认真";
  const char *second = "采集数据";
  const char *footer = "正在采集";
  uint16_t stateColor = GREEN;
  char warmup[32];
  switch (state) {
    case AirStatus::Waiting:
    case AirStatus::NoData:
      first = "我没收到";
      second = "传感器数据";
      footer = "等待传感器";
      stateColor = state == AirStatus::Waiting ? AMBER : RED;
      break;
    case AirStatus::SensorError:
      first = "检查传感器";
      second = "稍后重试";
      footer = "传感器故障";
      stateColor = RED;
      break;
    case AirStatus::Warmup: {
      const uint32_t elapsed = static_cast<uint32_t>(now - sample.sessionStartMs);
      const uint32_t left = (AirTelemetry::WARMUP_MS - elapsed + 999) / 1000;
      snprintf(warmup, sizeof(warmup), "预热%lu秒", static_cast<unsigned long>(left));
      first = "等我醒醒";
      second = warmup;
      footer = "预热中";
      stateColor = AMBER;
      break;
    }
    case AirStatus::Live: break;
  }
  if (strcmp(sideLine1_, first) || strcmp(sideLine2_, second) ||
      sideColor_ != stateColor) {
    lcd_.fillRect(12, 147, 68, 35, SIDEBAR);
    drawText(46 - textWidth(first) / 2, 149, first, INK);
    drawText(46 - textWidth(second) / 2, 168, second, stateColor);
    copyText(sideLine1_, sizeof(sideLine1_), first);
    copyText(sideLine2_, sizeof(sideLine2_), second);
    sideColor_ = stateColor;
    service();
  }

  const uint16_t footerColor = alarmSounding ? RED : stateColor;
  if (alarmSounding) footer = "甲醛报警";
  if (strcmp(footerState_, footer) || footerColor_ != footerColor) {
    lcd_.fillRect(14, 218, 86, 14, MINT);
    drawText(16, 219, footer, footerColor);
    copyText(footerState_, sizeof(footerState_), footer);
    footerColor_ = footerColor;
    service();
  }
  char age[32];
  if (sample.hasFrame) {
    snprintf(age, sizeof(age), "更新 %lus前",
             static_cast<unsigned long>(static_cast<uint32_t>(now - sample.lastFrameMs) / 1000));
  } else {
    copyText(age, sizeof(age), "更新 --");
  }
  if (strcmp(footerAge_, age)) {
    lcd_.fillRect(110, 218, 119, 14, MINT);
    drawText(112, 219, age, MUTED);
    copyText(footerAge_, sizeof(footerAge_), age);
    service();
  }

  const char *bluetooth = !bluetoothEnabled ? "蓝牙关闭" :
                          streamEnabled ? "蓝牙上报" : "蓝牙暂停";
  if (strcmp(footerBluetooth_, bluetooth)) {
    lcd_.fillRect(244, 218, 62, 14, MINT);
    drawText(304 - textWidth(bluetooth), 219, bluetooth, MUTED);
    copyText(footerBluetooth_, sizeof(footerBluetooth_), bluetooth);
    service();
  }
  // This tag is configuration/status, not an assertion of a real BT link.
  const char *tag = !bluetoothEnabled ? "BT OFF" :
                    streamEnabled ? "BT TX" : "BT PAUSE";
  if (strcmp(bluetoothTag_, tag)) {
    lcd_.fillRoundRect(244, 10, 68, 16, 7, SIDEBAR);
    drawText(278 - textWidth(tag) / 2, 12, tag, MUTED);
    copyText(bluetoothTag_, sizeof(bluetoothTag_), tag);
    service();
  }
}
