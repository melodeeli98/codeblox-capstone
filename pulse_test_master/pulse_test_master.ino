#include "codeblox_driver.h"
#include <ArduinoSTL.h>
#include <functional-vlpp.h>

using namespace std;

unsigned long pulseWidth = 500UL;
int num_pulses_sent = 0;
int received_pulses = 0;

void sendSyncPulses(){
  if (num_pulses_sent < 10):
    num_pulses_sent++;
    sendPulseThen(Side_Name::right, [](){});
    waitMicrosThen(CLOCK_WIDTH, sendSyncPulses);
}

void dataTriggered(enum Side_Name s){
  if (s == Side_Name::right) {
    received_pulses++;
  }
}

void processSerialMessage(String message){
  try {
    int message_int = stoi(message);
    pulse_width = message_int;
    num_pulses_sent = 0;
    received_pulses = 0;
    sendSyncPulses();
    waitMicrosThen(CLOCK_WIDTH*20, [](){
      serialLog(String("Received ") + String(received_pulses));
    });
  } catch (invalid_argument const &e) {
    serialLog("Bad input, invalid_argument thrown");
  } catch (out_of_range const &e) {
    serialLog("Integer overflow, out_of_range thrown");
  }
}

void setup(){
  initDriver(dataTriggered);
  serialLog("Starting up!");
}


void loop(){
  updateDriver();

  if (newSerialMessage()){
    processSerialMessage(getSerialMessage());
  }
}
