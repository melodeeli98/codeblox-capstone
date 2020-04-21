#include "codeblox_driver.h"

void handleNewMessage(const Message& message, enum Side_Name side) {
  LOG(String("NM ") + sideToString(side) + String(": ") + message.toString());
  switch (message.type) {
    case Message_Type::stop:
      break;
    case Message_Type::done:
      LOG("DONE!");
      stopComm(side);
      break;
    case Message_Type::parent:
      stopComm(side);
      break;
    case Message_Type::tile:
      {
        char x = (char) message.words[1];
        char y = (char) message.words[2];
        byte encoding = message.words[3];
        LOG("x: " + String(x) + " y: " + String(y) + " encoding: " + String(encoding));
      }
      break;
    default:
      stopComm(side);
      break;
  }
}

void processSerialMessage(char *message)
{
  if (String(message) == "start") {
    LOG("Starting");
    startCommAllSides();
    Message parentMessage (Message_Type::parent, Side_Name::top);
    sendMessage(Side_Name::bottom, parentMessage);
  }
}

void setup() {
  initDriver(handleNewMessage);
  LOG("initializing");
  registerSerialMessageCallback(processSerialMessage);
}

void loop() {
  updateDriver();
  static unsigned long t = timeMicros();
  if(timeMicros() - t > 20000000UL){
    t = timeMicros();
    stopComm(Side_Name::top);
    stopComm(Side_Name::right);
    stopComm(Side_Name::bottom);
    stopComm(Side_Name::left);
    startCommAllSides();
    Message parentMessage (Message_Type::parent, Side_Name::top);
    sendMessage(Side_Name::bottom, parentMessage);
  }
}
