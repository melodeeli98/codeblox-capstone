#include "codeblox_driver.h"
#include <functional-vlpp.h>
using namespace vl;

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

void processSerialMessage(String message)
{
  if (message == "sleep")
  {
    serialLog("Going to sleep");
    waitMicrosThen(1000000UL, []() {
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
  else if (message == "read")
  {
    static int sensor = 0;
    sensor = 0;
    static Func<void(int)> afterRead = [](int value) {
      serialLog(String("Sensor ") + String(sensor) + String(": ") + String(value));
      sensor++;
      if (sensor < numReflectiveSensors)
      {
        waitMicrosThen(1000000UL, []() {
          readReflectiveSensorRawThen(sensor, afterRead);
        });
      }
    };
    readReflectiveSensorRawThen(sensor, afterRead);
  }
}


void setup()
{
  initDriver(dataTriggered);
  serialLog("Starting up!");
}


void loop()
{
  updateDriver();

  if (newSerialMessage())
  {
    processSerialMessage(getSerialMessage());
  }
}
