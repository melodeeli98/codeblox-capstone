#include "codeblox_driver.h"
#include "message_manager.h"
#include <ArduinoSTL.h>
#include <MemoryFree.h>
#include <list>
using namespace std;

int numValidSides = 4;
Side_Name parentSide;
bool hasParent = false;
unsigned int tileEncoding = 0;
bool tileFlipped = false;
bool asleep = false;

// Resets tile state between compilations
void resetTile() {
  serialLog("resetting");
  asleep = true;
  goToSleep();
  asleep = false;
  mm::wakeup();
  numValidSides = 4;
  hasParent = false;
  tileFlipped = false;
  readReflectiveSensorsLater(&tileEncoding);
}

void translateCoordinates(signed char * newX, signed char * newY, signed char oldX, signed char oldY, Side_Name side, bool tileFlipped) {
  *newX = oldX;
  *newY = oldY;
  signed char multiplier = 1;
  if (tileFlipped) {
    multiplier = -1;
  }
  if (side == Side_Name::bottom) {
    *newY += 1 * multiplier;
  } else if (side == Side_Name::top) {
    *newY += -1 * multiplier;
  } else if (side == Side_Name::left) {
    *newX += -1 * multiplier;
  } else if (side == Side_Name::right) {
    *newX += 1 * multiplier;
  }
}

unsigned int flipEncoding(unsigned int encoding, bool tileFlipped) {
  unsigned int newEncoding = encoding;
  if (tileFlipped) {
    ; //TODO
  }
  return newEncoding;
}

void handleNewMessage(Message message, enum Side_Name side) {
  switch (message.type) {
    case Message_Type::stop:
      serialLog("received stop");
      numValidSides--;
      if (hasParent && parentSide == side) {
        hasParent = false;
      }
      if (numValidSides == 1 && hasParent) {
        mm::sendMessage(Message::newTileMessage(0, 0, tileEncoding), parentSide);
        mm::sendMessage(new Message(Message_Type::done), parentSide);
      }
      if (numValidSides == 0) {
        resetTile();
      }
      break;
    case Message_Type::done:
      serialLog("received done");
      mm::stop(side);
      break;
    case Message_Type::parent:
      if (hasParent) {
        serialLog("received parent request but I already have a parent");
        mm::stop(side);
      }
      else {
        hasParent = true;
        parentSide = side;

        // Adjust orientation
        unsigned int requestSide = message.getData().front();
        serialLog("received parent request from side:");
        serialLog(requestSide);
        if (side != requestSide) {
          tileFlipped = true;
        }

        // Send parent requests to all other sides
        if (parentSide != Side_Name::top) {
          mm::sendMessage(new Message(Message_Type::parent, Side_Name::bottom), Side_Name::top);
        }
        if (parentSide != Side_Name::right) {
          mm::sendMessage(new Message(Message_Type::parent, Side_Name::left), Side_Name::right);
        }
        if (parentSide != Side_Name::bottom) {
          mm::sendMessage(new Message(Message_Type::parent, Side_Name::top), Side_Name::bottom);
        }
        if (parentSide != Side_Name::left) {
          mm::sendMessage(new Message(Message_Type::parent, Side_Name::right), Side_Name::left);
        }
      }
      break;
    case Message_Type::tile:
      if (hasParent) {
        serialLog("received tile message");
        signed char oldX = (signed char) message.getData().front();
        message.getData().pop_front();
        signed char oldY = (signed char) message.getData().front();
        message.getData().pop_front();
        unsigned int encoding = message.getData().front();
        serialLog("old x: " + String(oldX) + " old y: " + String(oldY) + " encoding: " + String(encoding));
        signed char newX, newY;
        translateCoordinates(&newX, &newY, oldX, oldY, side, tileFlipped);
        mm::sendMessage(new Message(Message_Type::tile, (unsigned int) newX, (unsigned int) newY, flipEncoding(encoding, tileFlipped)), parentSide);
      }
      break;
    default:
      serialLog("invalid message type");
      mm::stop(side);
      break;
  }
}

void processSerialMessage(char *message)
{
  serialLog("freeMemory()=");
  serialLog(freeMemory());
  if (asleep) {
    asleep = false;
    mm::wakeup();
  }
  if (String(message) == "read") {
    serialLog(tileEncoding);
  }
}

void setup() {
  initDriver(mm::newBitCallback);
  serialLog("initializing");
  mm::init(handleNewMessage);
  registerSerialMessageCallback(processSerialMessage);
  serialLog("freeMemory()=");
  serialLog(freeMemory());
  resetTile();
}

void loop() {
  updateDriver();
  mm::update();
}
