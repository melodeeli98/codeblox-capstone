// **** INCLUDES *****
#include "codeblox_driver.h"

void dataTriggered(Side_Name s){
  switch(s){
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

void setup() {
  initDriver(dataTriggered);
}

void processSerialMessage(String message){
  if (message == "sleep") {
      serialLog("Going to sleep");
      waitMicrosThen(10000, [](){
        goToSleepThen([](){
          serialLog("I'm awake!");
        });
      });
    } else if (message == "top" || message == "right" || message == "bottom" || message == "left") {
      serialLog("toggle " + message);
      getSide(message).toggleDataThen([](){;});
    } else if (message = "read"){
      int sensor = 0;
      void (*afterRead)(int) = [&sensor](int value){
        serialLog("Sensor "+ sensor + ": " + value);
        sensor++;
        if(sensor < numReflectiveSensors){
          readReflectiveSensorRawThen(sensor, afterRead);
        }
      }
      readReflectiveSensorRawThen(sensor, afterRead);
    }
}

void loop() {
  updateDriver();
  
  if (newSerialMessage()) {
    processSerialMessage(getSerialMessage());
  }
}
