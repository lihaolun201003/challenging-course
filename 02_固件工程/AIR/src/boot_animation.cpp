#include "boot_animation.h"
#include "air_config.h"
#include "boot_gif_data.h"
#include <Arduino.h>
#include <SPI.h>
#include <Adafruit_ILI9341.h>
#include <tjpgd.h>
#include <algorithm>
#include <cstring>

namespace {
constexpr uint16_t INK = 0x1082;
constexpr uint16_t GREY = 0xAD55;
constexpr uint16_t TRACK = 0xE71C;
constexpr uint16_t TEAL = 0x04B2;
constexpr int16_t IMAGE_X = 6;
constexpr int16_t IMAGE_Y = 12;
constexpr uint16_t STRIP_ROWS = 8;

// The LCD retains the visible frame while the next frame is decoded here.
// Bytes are prepared in RGB565 wire order, so transfers need no pixel swapping.
alignas(4) uint8_t framePixels[BOOT_GIF_WIDTH * BOOT_GIF_HEIGHT * 2];
alignas(4) uint8_t jpegWorkspace[16384];
uint16_t transferErrors = 0;

static_assert(BOOT_GIF_FRAME_COUNT == 74 && BOOT_GIF_DURATION_MS == 7400,
              "The complete source animation must remain 74 frames / 7.4 s");
static_assert(IMAGE_X + BOOT_GIF_WIDTH <= 176 &&
              IMAGE_Y + BOOT_GIF_HEIGHT <= 240,
              "The animation must fit beside the existing boot labels");
static_assert(sizeof(BOOT_GIF_FRAME_OFFSETS) / sizeof(uint32_t) ==
              BOOT_GIF_FRAME_COUNT + 1, "Missing JPEG offset sentinel");

struct JpegInput {
  const uint8_t *data;
  size_t size;
  size_t position;
  void (*service)();
};

size_t readJpeg(JDEC *decoder, uint8_t *destination, size_t requested) {
  JpegInput &input = *static_cast<JpegInput *>(decoder->device);
  const size_t count = std::min(requested, input.size - input.position);
  if (destination && count) {
    std::memcpy(destination, input.data + input.position, count);
  }
  input.position += count;
  input.service();
  return count;
}

int storeJpegBlock(JDEC *decoder, void *bitmap, JRECT *rectangle) {
  if (rectangle->right >= BOOT_GIF_WIDTH ||
      rectangle->bottom >= BOOT_GIF_HEIGHT) return 0;
  const uint16_t *source = static_cast<const uint16_t *>(bitmap);
  for (uint16_t y = rectangle->top; y <= rectangle->bottom; ++y) {
    uint8_t *destination = framePixels +
        (y * BOOT_GIF_WIDTH + rectangle->left) * 2;
    for (uint16_t x = rectangle->left; x <= rectangle->right; ++x) {
      const uint16_t pixel = *source++;
      *destination++ = pixel >> 8;
      *destination++ = pixel & 0xFF;
    }
  }
  static_cast<JpegInput *>(decoder->device)->service();
  return 1;
}

bool decodeFrame(uint16_t frame, void (*service)()) {
  const uint32_t begin = BOOT_GIF_FRAME_OFFSETS[frame];
  const uint32_t end = BOOT_GIF_FRAME_OFFSETS[frame + 1];
  if (end <= begin || end > sizeof(BOOT_GIF_JPEG_DATA)) return false;
  JpegInput input{BOOT_GIF_JPEG_DATA + begin, end - begin, 0, service};
  JDEC decoder{};
  JRESULT result = jd_prepare(&decoder, readJpeg, jpegWorkspace,
                              sizeof(jpegWorkspace), &input);
  if (result == JDR_OK && decoder.width == BOOT_GIF_WIDTH &&
      decoder.height == BOOT_GIF_HEIGHT) {
    result = jd_decomp(&decoder, storeJpegBlock, 0);
  } else if (result == JDR_OK) {
    result = JDR_FMT1;
  }
#if AIR_ENABLE_SERIAL_LOG
  if (result != JDR_OK) {
    Serial.print(F("BOOT GIF decode error frame="));
    Serial.print(frame);
    Serial.print(F(" code="));
    Serial.println(static_cast<int>(result));
  }
#endif
  return result == JDR_OK;
}

void transferStrip(Adafruit_ILI9341 &lcd, uint16_t x, uint16_t y,
                   uint16_t width, uint16_t rows, const uint8_t *pixels,
                   void (*service)()) {
  lcd.startWrite();
  lcd.setAddrWindow(x, y, width, rows);
  // The core's generic full-duplex transfer polls a clock on every byte.
  // This write-only LCD has no MISO wire; HAL's transmit-only bulk path also
  // drains the unused receive state and avoids that per-byte overhead.
  if (HAL_SPI_Transmit(SPI.getHandle(), const_cast<uint8_t *>(pixels),
                       width * rows * 2, 100) != HAL_OK) {
    ++transferErrors;
  }
  lcd.endWrite();
  // Preserve the existing sensor, buzzer and Bluetooth service unchanged.
  service();
}

void clearBackground(Adafruit_ILI9341 &lcd, void (*service)()) {
  std::memset(framePixels, 0xFF, sizeof(framePixels));
  for (uint16_t y = 0; y < 240; y += STRIP_ROWS) {
    transferStrip(lcd, 0, y, 320,
                  std::min<uint16_t>(STRIP_ROWS, 240 - y), framePixels, service);
  }
}

uint32_t presentFrame(Adafruit_ILI9341 &lcd, void (*service)()) {
  const uint32_t begin = millis();
  for (uint16_t y = 0; y < BOOT_GIF_HEIGHT; y += STRIP_ROWS) {
    transferStrip(lcd, IMAGE_X, IMAGE_Y + y, BOOT_GIF_WIDTH,
                  std::min<uint16_t>(STRIP_ROWS, BOOT_GIF_HEIGHT - y),
                  framePixels + y * BOOT_GIF_WIDTH * 2, service);
  }
  return millis() - begin;
}

void label(Adafruit_ILI9341 &lcd, int16_t x, int16_t y, uint8_t size,
           uint16_t color, const char *text) {
  lcd.setCursor(x, y);
  lcd.setTextSize(size);
  lcd.setTextColor(color);
  lcd.print(text);
}

void waitUntil(uint32_t start, uint32_t deadline, void (*service)()) {
  while (static_cast<uint32_t>(millis() - start) < deadline) {
    service();
    delay(1);
  }
}
}  // namespace

void playBootAnimation(Adafruit_ILI9341 &lcd, void (*service)()) {
  transferErrors = 0;
  // Use a faster clock only for the boot movie; monitoring keeps its original
  // 8 MHz request. On this 100 MHz SPI bus, 25 MHz is an exact prescaler.
  lcd.setSPISpeed(25000000);
  lcd.setTextWrap(false);
  // BootDisplay keeps output OFF until the complete first frame is ready.
  clearBackground(lcd, service);
  label(lcd, 178, 64, 4, INK, "AIR");
  label(lcd, 178, 105, 2, INK, "MONITOR");
  label(lcd, 178, 137, 1, GREY, "HELLO!");
  label(lcd, 178, 202, 1, GREY, "STARTING UP");
  lcd.fillRoundRect(176, 183, 120, 5, 2, TRACK);
  for (uint8_t dot = 0; dot < 3; ++dot) {
    lcd.fillCircle(186 + dot * 18, 165, 3, dot == 0 ? TEAL : TRACK);
  }

  uint32_t decodeStart = millis();
  const bool firstFrameOk = decodeFrame(0, service);
  uint32_t maxDecodeMs = millis() - decodeStart;
  uint32_t maxPresentMs = presentFrame(lcd, service);
  uint32_t maxLateMs = 0;
  uint16_t renderedFrames = firstFrameOk ? 1 : 0;
  uint16_t decodeErrors = firstFrameOk ? 0 : 1;
  lcd.sendCommand(ILI9341_DISPON);
  const uint32_t start = millis();
#if AIR_ENABLE_SERIAL_LOG
  Serial.print(F("BOOT GIF start frames=74 duration_ms=7400 uptime_ms="));
  Serial.println(start);
#endif

  uint32_t boundary = 0;
  uint8_t lastDot = 0;
  for (uint16_t frame = 1; frame < BOOT_GIF_FRAME_COUNT; ++frame) {
    boundary += BOOT_GIF_FRAME_DURATIONS_MS[frame - 1];
    decodeStart = millis();
    const bool frameOk = decodeFrame(frame, service);
    maxDecodeMs = std::max(maxDecodeMs, millis() - decodeStart);
    // Finish each transfer at its source timestamp. Decoding happens while
    // the previous frame remains visible; deadlines never drift with work time.
    const uint32_t lead = maxPresentMs + 1;
    waitUntil(start, boundary > lead ? boundary - lead : 0, service);
    if (frameOk) {
      maxPresentMs = std::max(maxPresentMs, presentFrame(lcd, service));
      ++renderedFrames;
    } else {
      ++decodeErrors;
    }
    const uint32_t elapsed = millis() - start;
    if (elapsed > boundary) maxLateMs = std::max(maxLateMs, elapsed - boundary);
    const uint8_t activeDot = (boundary / 180) % 3;
    if (activeDot != lastDot) {
      for (uint8_t dot = 0; dot < 3; ++dot) {
        lcd.fillCircle(186 + dot * 18, 165, 3, dot == activeDot ? TEAL : TRACK);
      }
      lastDot = activeDot;
    }
    lcd.fillRect(176, 183, boundary * 120 / BOOT_GIF_DURATION_MS, 5, TEAL);
    service();
  }
  // Include the last frame's hold time; there is no extra post-animation delay.
  waitUntil(start, BOOT_GIF_DURATION_MS, service);
  lcd.fillRect(176, 183, 120, 5, TEAL);
  lcd.setSPISpeed(8000000);
#if AIR_ENABLE_SERIAL_LOG
  Serial.print(F("BOOT GIF done duration_ms="));
  Serial.print(millis() - start);
  Serial.print(F(" frames="));
  Serial.print(renderedFrames);
  Serial.print(F(" decode_errors="));
  Serial.print(decodeErrors);
  Serial.print(F(" transfer_errors="));
  Serial.print(transferErrors);
  Serial.print(F(" max_decode_ms="));
  Serial.print(maxDecodeMs);
  Serial.print(F(" max_transfer_ms="));
  Serial.print(maxPresentMs);
  Serial.print(F(" max_late_ms="));
  Serial.println(maxLateMs);
#endif
}
