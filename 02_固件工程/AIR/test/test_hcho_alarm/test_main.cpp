#include <unity.h>
#include "air_alarm.h"
#ifdef ARDUINO
#include <Arduino.h>
#endif

void setUp() {}
void tearDown() {}

namespace {
AirTelemetry liveSample(uint16_t value = 31) {
  AirTelemetry sample;
  sample.hasFrame = true;
  sample.lastFrameMs = 31000;
  sample.sessionStartMs = 1000;
  sample.reading.hchoUgM3 = value;
  return sample;
}

void test_strict_threshold_and_full_sensor_range() {
  const uint16_t values[] = {0, 29, 30, 31, 65535};
  const bool expected[] = {false, false, false, true, true};
  for (size_t i = 0; i < 5; ++i) {
    const AirTelemetry sample = liveSample(values[i]);
    TEST_ASSERT_EQUAL(expected[i], hchoAlarmShouldSound(sample, 31000));
  }
}

void test_warmup_uses_the_same_strict_threshold() {
  AirTelemetry sample = liveSample(30);
  sample.sessionStartMs = 31000;
  TEST_ASSERT_TRUE(sample.status(31000) == AirStatus::Warmup);
  TEST_ASSERT_FALSE(hchoAlarmShouldSound(sample, 31000));
  sample.reading.hchoUgM3 = 31;
  TEST_ASSERT_TRUE(hchoAlarmShouldSound(sample, 31000));
}

void test_no_frame_never_alarms() {
  AirTelemetry sample;
  sample.reading.hchoUgM3 = 65535;
  TEST_ASSERT_FALSE(hchoAlarmShouldSound(sample, 0));
  TEST_ASSERT_FALSE(hchoAlarmShouldSound(sample, 100000));
}

void test_sensor_error_silences_high_reading() {
  AirTelemetry sample = liveSample(65535);
  sample.reading.error = 1;
  TEST_ASSERT_FALSE(hchoAlarmShouldSound(sample, 31000));
  sample.reading.error = 0;
  sample.sessionStartMs = 31000;
  TEST_ASSERT_TRUE(hchoAlarmShouldSound(sample, 31000));
}

void test_stale_at_exactly_ten_seconds() {
  const AirTelemetry sample = liveSample();
  TEST_ASSERT_TRUE(hchoAlarmShouldSound(sample, 40999));
  TEST_ASSERT_FALSE(hchoAlarmShouldSound(sample, 41000));
}

void test_millis_rollover_does_not_keep_stale_alarm() {
  AirTelemetry sample = liveSample();
  sample.lastFrameMs = 0xFFFFFFF0u;
  sample.sessionStartMs = sample.lastFrameMs - 30000u;
  TEST_ASSERT_TRUE(hchoAlarmShouldSound(sample, 0x26FFu));
  TEST_ASSERT_FALSE(hchoAlarmShouldSound(sample, 0x2700u));
}

void test_low_reading_stops_and_fresh_high_reading_restarts() {
  AirTelemetry sample = liveSample();
  TEST_ASSERT_TRUE(hchoAlarmShouldSound(sample, 31000));
  sample.reading.hchoUgM3 = 30;
  TEST_ASSERT_FALSE(hchoAlarmShouldSound(sample, 31000));
  sample.reading.hchoUgM3 = 31;
  TEST_ASSERT_FALSE(hchoAlarmShouldSound(sample, 41000));
  sample.lastFrameMs = 41000;
  sample.sessionStartMs = 41000;
  TEST_ASSERT_TRUE(hchoAlarmShouldSound(sample, 41000));
}

void makeFrame(uint8_t (&bytes)[40], uint16_t hcho, bool checksumOk = true) {
  memset(bytes, 0, sizeof(bytes));
  bytes[0] = 0x42; bytes[1] = 0x4D; bytes[3] = 36;
  bytes[28] = hcho >> 8; bytes[29] = hcho & 0xFF;
  uint16_t sum = 0;
  for (size_t i = 0; i < 38; ++i) sum += bytes[i];
  bytes[38] = sum >> 8; bytes[39] = sum & 0xFF;
  if (!checksumOk) bytes[39] ^= 1;
}

void acceptFrame(Pms5003stParser &parser, AirTelemetry &sample,
                 const uint8_t (&bytes)[40], uint32_t started) {
  for (size_t i = 0; i < 40; ++i) {
    PmsReading reading;
    if (parser.feed(bytes[i], started + i, reading)) {
      sample.reading = reading;
      sample.hasFrame = true;
      sample.lastFrameMs = started + i;
    }
  }
}

void test_real_parser_preserves_good_value_and_recovers_after_bad_frame() {
  Pms5003stParser parser;
  AirTelemetry sample;
  sample.sessionStartMs = 1000;
  uint8_t bytes[40];
  makeFrame(bytes, 31);
  acceptFrame(parser, sample, bytes, 1000);
  TEST_ASSERT_EQUAL_UINT16(31, sample.reading.hchoUgM3);
  TEST_ASSERT_TRUE(hchoAlarmShouldSound(sample, 1039));
  makeFrame(bytes, 0, false);
  acceptFrame(parser, sample, bytes, 2000);
  TEST_ASSERT_EQUAL_UINT16(31, sample.reading.hchoUgM3);
  TEST_ASSERT_TRUE(hchoAlarmShouldSound(sample, 2039));
  TEST_ASSERT_FALSE(hchoAlarmShouldSound(sample, 11039));
  makeFrame(bytes, 30);
  acceptFrame(parser, sample, bytes, 12000);
  TEST_ASSERT_EQUAL_UINT16(30, sample.reading.hchoUgM3);
  TEST_ASSERT_FALSE(hchoAlarmShouldSound(sample, 12039));
  TEST_ASSERT_EQUAL_UINT32(2, parser.frames);
  TEST_ASSERT_EQUAL_UINT32(1, parser.checksumErrors);
}

int runTests() {
  UNITY_BEGIN();
  RUN_TEST(test_strict_threshold_and_full_sensor_range);
  RUN_TEST(test_warmup_uses_the_same_strict_threshold);
  RUN_TEST(test_no_frame_never_alarms);
  RUN_TEST(test_sensor_error_silences_high_reading);
  RUN_TEST(test_stale_at_exactly_ten_seconds);
  RUN_TEST(test_millis_rollover_does_not_keep_stale_alarm);
  RUN_TEST(test_low_reading_stops_and_fresh_high_reading_restarts);
  RUN_TEST(test_real_parser_preserves_good_value_and_recovers_after_bad_frame);
  return UNITY_END();
}
}

#ifdef ARDUINO
void setup() {
  pinMode(PB10, OUTPUT);
  digitalWrite(PB10, LOW);
  Serial.setRx(PA3);
  Serial.setTx(PA2);
  Serial.begin(115200);
  delay(2000);
  runTests();
}
void loop() {}
#else
int main() { return runTests(); }
#endif
