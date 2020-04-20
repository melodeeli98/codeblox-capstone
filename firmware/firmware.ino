#include "codeblox_driver.h"
#include "message_manager.h"
#include <ArduinoSTL.h>
#include <list>
using namespace std;



void handleNewMessage(Message message, enum Side_Name side) {
  LOG(String("NM ") + sideToString(side) + String(": ") + message.toString());
  switch (message.type) {
    case Message_Type::stop:
      break;
    case Message_Type::done:
      LOG("DONE!");
      mm::stop(side);
      break;
    case Message_Type::parent:
      mm::stop(side);
      break;
    case Message_Type::tile:
      {
        std::list<unsigned int> data = message.getData();
        signed char x = (signed char) data.front();
        data.pop_front();
        signed char y = (signed char) data.front();
        data.pop_front();
        unsigned int encoding = data.front();
        LOG("x: " + String(x) + " y: " + String(y) + " encoding: " + String(encoding));
      }
      break;
    default:
      mm::stop(side);
      break;
  }
}

void processSerialMessage(char *message)
{
  if (String(message) == "start") {
    LOG("Starting");
    mm::wakeup();
  }
}

void setup() {
  initDriver(mm::newBitCallback);
  LOG("initializing");
  mm::init(handleNewMessage);
  registerSerialMessageCallback(processSerialMessage);
}

void loop() {
  updateDriver();
  mm::update();
}
