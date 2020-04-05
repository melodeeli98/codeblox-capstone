
#define __AVR_ATmega328P__
#include <Arduino.h>

#include "codeblox_driver.h"

#define NEW_STATIC(type, name, value) \
  static type name;                   \
  name = value

void dataTriggered(Side_Name s)
{
  switch (s)
  {
  case Side_Name::top:
    serialLog("Top Triggered");
    break;
  case Side_Name::right:
    serialLog("Right Triggered");
    break;
  case Side_Name::bottom:
    serialLog("Bottom Triggered");
    break;
  case Side_Name::left:
    serialLog("Left Triggered");
    break;
  }
}

void setup()
{
  initDriver(dataTriggered);
}

int sensor = 20;

void processSerialMessage(String message)
{
  if (message == "sleep")
  {
    serialLog("Going to sleep");
    waitMicrosThen(10000UL, []() {
      goToSleepThen([]() {
        serialLog("I'm awake!");
      });
    });
  }
  else if (message == "top" || message == "right" || message == "bottom" || message == "left")
  {
    serialLog("toggle " + message);
    sendPulseThen(sideFromString(message), []() {
      serialLog("sent toggle");
    });
  }
  else if (message = "read")
  {
    NEW_STATIC(int, sensor, 0);
    static void (*afterRead)(int) = [](int value) {
      serialLog(String("Sensor ") + String(sensor) + String(": ") + String(value));
      sensor++;
      if (sensor < numReflectiveSensors)
      {
        readReflectiveSensorRawThen(sensor, afterRead);
      }
    };
    readReflectiveSensorRawThen(sensor, afterRead);
  }
}

void loop()
{
  updateDriver();

  if (newSerialMessage())
  {
    processSerialMessage(getSerialMessage());
  }
}
