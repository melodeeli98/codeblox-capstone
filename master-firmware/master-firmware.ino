#include "codeblox_driver.h"

static volatile byte my_sensors;

static volatile int stopped;

void translateCoordinates(char * newX, char * newY, char oldX, char oldY, Side_Name side) {
  *newX = oldX;
  *newY = oldY;
  if (side == Side_Name::bottom) {
    *newY += 1;
  } else if (side == Side_Name::top) {
    *newY -= 1;
  } else if (side == Side_Name::left) {
    *newX -= 1;
  } else if (side == Side_Name::right) {
    *newX += 1;
  }
}


void handleNewMessage(const Message& message, enum Side_Name side) {
  LOG(String("NM ") + sideToString(side) + String(": ") + message.toString());
  switch (message.type) {
    case Message_Type::stop:
      stopped++;
      if(stopped == 4){
        Serial.println("0,0:" + String(my_sensors));
        Serial.println("done");
      }
      break;
    case Message_Type::timeout:
      Serial.println("timeout");
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
        char x, y;
        translateCoordinates(&x, &y , message.words[1], message.words[2], side);
        Serial.println(String((int)((char)x)) + "," + String((int)((char)y)) + ":" + String(message.words[3]));
      }
      break;
    default:
      stopComm(side);
      break;
  }
}

void processSerialMessage(char *message)
{
  String m (message);
  if ( m == "start") {
    readReflectiveSensorsLater(&my_sensors);
    stopped = 0;
    LOG("Starting");
    startCommAllSides();
    Message bottomParentMessage (Message_Type::parent, Side_Name::top);
    Message rightParentMessage (Message_Type::parent, Side_Name::left);
    sendMessage(Side_Name::bottom, bottomParentMessage);
    sendMessage(Side_Name::right, rightParentMessage);
  } else if (m == "stop"){
    stopComm(Side_Name::top);
    stopComm(Side_Name::right);
    stopComm(Side_Name::bottom);
    stopComm(Side_Name::left);
  }
}

void setup() {
  initDriver(handleNewMessage);
  LOG("initializing");
  registerSerialMessageCallback(processSerialMessage);
}

void loop() {
  updateDriver();
  /*
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
  }*/
}
