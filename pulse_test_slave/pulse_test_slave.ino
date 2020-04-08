#include "codeblox_driver.h"
#include <ArduinoSTL.h>
#include <functional-vlpp.h>

using namespace std;

unsigned long pulseWidth = 500UL;

void dataTriggered(enum Side_Name side){
  sendPulseThen(side, [](){});
  serialLog("Sending pulse back");
}

void setup(){
  initDriver(dataTriggered);
  serialLog("Starting up!");
  goToSleepThen([](){});
}


void loop(){
  updateDriver();
}
