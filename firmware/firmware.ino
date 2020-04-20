#include "codeblox_driver.h"
#include "message_manager.h"
#include <ArduinoSTL.h>
#include <list>
using namespace std;

int numValidSides = 4;
Side_Name parentSide;
bool hasParent = false;
unsigned int tileEncoding = 0;
bool tileFlipped = false;

// Resets tile state between compilations
void resetTile() {
  LOG("resetting");
  goToSleep();
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
  unsigned int newEncoding = 0;
  if (tileFlipped) {
    newEncoding |= (encoding & 0b1) << 5;
    newEncoding |= (encoding & 0b10) << 3;
    newEncoding |= (encoding & 0b100) << 1;
    newEncoding |= (encoding & 0b1000) >> 1;
    newEncoding |= (encoding & 0b10000) >> 3;
    newEncoding |= (encoding & 0b100000) >> 5;
  }else{
    newEncoding = encoding;
  }
  return newEncoding;
}

void handleNewMessage(Message message, enum Side_Name side) {
  LOG(String("NM ") + sideToString(side) + String(": ") + message.toString());
  switch (message.type) {
    case Message_Type::stop:
      numValidSides--;
      if (hasParent && parentSide == side) {
        hasParent = false;
        mm::stop(Side_Name::top);
        mm::stop(Side_Name::right);
        mm::stop(Side_Name::bottom);
        mm::stop(Side_Name::left);
      }
      if (numValidSides == 1 && hasParent) {
        mm::sendMessage(Message::newTileMessage(0, 0, flipEncoding(tileEncoding, tileFlipped)), parentSide);
        mm::sendMessage(new Message(Message_Type::done), parentSide);
      }
      if (numValidSides == 0) {
        resetTile();
      }
      break;
    case Message_Type::done:
      mm::stop(side);
      break;
    case Message_Type::parent:
      if (hasParent) {
        LOG("already have parent");
        mm::stop(side);
      }
      else {
        hasParent = true;
        parentSide = side;

        // Adjust orientation
        unsigned int requestSide = message.getData().front();
        LOG(String("from ") + sideToString(requestSide));
        if (side != requestSide) {
          LOG("flipping");
          tileFlipped = true;
        }
        if(numValidSides > 1){
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
        } else {
          mm::sendMessage(Message::newTileMessage(0, 0, flipEncoding(tileEncoding, tileFlipped)), parentSide);
          mm::sendMessage(new Message(Message_Type::done), parentSide);
        }
      }
      break;
    case Message_Type::tile:
      if (hasParent) {
        std::list<unsigned int> data = message.getData();
        signed char oldX = (signed char) data.front();
        data.pop_front();
        signed char oldY = (signed char) data.front();
        data.pop_front();
        unsigned int encoding = data.front();
        LOG("old x: " + String(oldX) + " old y: " + String(oldY) + " encoding: " + String(encoding));
        signed char newX, newY;
        translateCoordinates(&newX, &newY, oldX, oldY, side, tileFlipped);
        LOG("new x: " + String(newX) + " new y: " + String(newY) + " encoding: " + String(encoding));
        mm::sendMessage(new Message(Message_Type::tile, (unsigned int) newX, (unsigned int) newY, encoding), parentSide);
      }
      break;
    default:
      mm::stop(side);
      break;
  }
}



void setup() {
  initDriver(mm::newBitCallback);
  LOG("initializing");
  mm::init(handleNewMessage);
  resetTile();
}

void loop() {
  updateDriver();
  mm::update();
}
