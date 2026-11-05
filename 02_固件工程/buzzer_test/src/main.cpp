#include <Arduino.h>

namespace {
constexpr uint32_t BUZZER_PIN = PB10;  // NUCLEO-F411RE Arduino D6.
constexpr uint32_t SOUND_MS = 500;
constexpr uint32_t QUIET_MS = 1500;
}

void setup() {
  digitalWrite(BUZZER_PIN, LOW);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  Serial.setRx(PA3);
  Serial.setTx(PA2);
  Serial.begin(115200);
  Serial.println("BUZZER TEST: D6/PB10, active HIGH, 500ms ON / 1500ms OFF");
}

void loop() {
  Serial.println("BUZZER ON");
  digitalWrite(BUZZER_PIN, HIGH);
  delay(SOUND_MS);
  digitalWrite(BUZZER_PIN, LOW);
  Serial.println("BUZZER OFF");
  delay(QUIET_MS);
}
