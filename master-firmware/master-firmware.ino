#include "codeblox_driver.h"

static byte my_sensors;

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
      stopSending(side);
      break;
    case Message_Type::first_message:
      LOG("first message");
      break;
    case Message_Type::timeout:
      LOG("timeout");
      break;
    case Message_Type::done:
      LOG("DONE!");
      stopSending(side);
      break;
    case Message_Type::parent:
      stopSending(side);
      break;
    case Message_Type::tile:
      {
        char x, y;
        translateCoordinates(&x, &y , message.words[1], message.words[2], side);
        Serial.println(String((int)((char)x)) + "," + String((int)((char)y)) + ":" + String(message.words[3]));
      }
      break;
    default:
      stopSending(side);
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

    resetSides();
    Message bottomParentMessage (Message_Type::parent, Side_Name::top);
    Message rightParentMessage (Message_Type::parent, Side_Name::left);
    sendMessage(Side_Name::bottom, bottomParentMessage);
    sendMessage(Side_Name::right, rightParentMessage);
    beginTimeout();
  } else if (m == "stop"){
    stopSending(Side_Name::top);
    stopSending(Side_Name::right);
    stopSending(Side_Name::bottom);
    stopSending(Side_Name::left);
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
    stopSending(Side_Name::top);
    stopSending(Side_Name::right);
    stopSending(Side_Name::bottom);
    stopSending(Side_Name::left);
    resetSides();
    Message bottomParentMessage (Message_Type::parent, Side_Name::top);
    sendMessage(Side_Name::bottom, bottomParentMessage);
    Message rightParentMessage (Message_Type::parent, Side_Name::left);
    sendMessage(Side_Name::right, rightParentMessage);
    beginTimeout();
  }
  */
}
