#include <vector>
#include "LowPower.h"
#include "codeblox_driver.h"
using namespace std;

void resetClock();

//Reflective Sensor Output
// PortB 7

void initDriver(void (*callback)(Side_Name)) {
  // turn off reflective sensors asap
  DDRB |= 1 << PINB7;
  PORTB |= 1 << PINB7;

  resetClock();
  
  //select external reference
  analogReference(EXTERNAL);

  Serial.begin(9600);

  initSides(callback);
}

void (*wakeupCallback)(void) = NULL;
void goToSleepThen(void (*callback)(void)){
  wakeupCallback = callback;
}

String nextMessage = "";
vector<String> messages;

void updateDriver() {
  
  updateSides();
  
  //read new messages
  while (Serial.available() > 0) {
    // read the incoming byte:
    char incomingByte = (char) Serial.read();
    if (incomingByte == '\n') {
      messages.push_back(nextMessage);
      nextMessage = "";
    } else {
      message += incomingByte;
    }
  }
  
  if(wakeupCallback != NULL){
    LowPower.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF);
    void (*callback)(void) = wakeupCallback;
    wakeupCallback = NULL;
    resetClock();
    callback();
  }
  
  if (messageAvailable) {
     if (message = "read"){
      PORTB &= ~(1 << PINB7);
      delay(10);
      Serial.println(analogRead(A3));
      delay(10);
      PORTB |= 1 << PINB7;
    }
    message = "";
  }
}

const unsigned long maxTime = ~0UL;
unsigned long startTime = 0UL;

unsigned long timeMicros(){
  unsigned long currTime = micros();
  if(startTime > currTime){//aka overflow
     return (maxTime - startTime) + 1UL + currTime
  }
  return currTime - startTime;
}

void resetClock(){
  startTime = micros();
}

int interruptDepth = 0;
void disableInterrupts(){
  interruptDepth++;
}

void enableInterrupts(){
  interruptDepth--;
}

bool interruptsEnabled(){
  return interruptDepth > 0;
}

