#pragma once

#include "air_bluetooth.h"

// PMS5003ST reports HCHO in ug/m3: 30 ug/m3 is exactly 0.030 mg/m3.
constexpr uint16_t HCHO_ALARM_THRESHOLD_UG_M3 = 30;

inline bool hchoAlarmShouldSound(const AirTelemetry &sample, uint32_t now) {
  return sample.valuesVisible(now) &&
         sample.reading.hchoUgM3 > HCHO_ALARM_THRESHOLD_UG_M3;
}
