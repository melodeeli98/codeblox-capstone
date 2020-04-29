#include "codeblox_driver.h"

static volatile int numValidSides = 4;
static volatile int numAliveSides = 4;
static volatile Side_Name parentSide;
static volatile bool hasParent = false;
static byte tileEncoding = 0;
static volatile bool tileFlipped = false;

// Resets tile state between compilations
void resetTile() {
  LOG("resetting");
  goToSleep();
  //startCommAllSides happens automatically on wakeup
  
  numValidSides = 4;
  numAliveSides = 4;
  hasParent = false;
  tileFlipped = false;
  readReflectiveSensorsLater(&tileEncoding);
}

void translateCoordinates(char * newX, char * newY, char oldX, char oldY, Side_Name side, bool tileFlipped) {
  *newX = oldX;
  *newY = oldY;
  char multiplier = 1;
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

byte flipEncoding(byte encoding, bool tileFlipped) {
  byte newEncoding = 0;
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

void handleNewMessage(const Message& message, enum Side_Name side) {
  //Serial.println(String("NM ") + sideToString(side) + String(": ") + message.toString());
  switch (message.type) {
    case Message_Type::stop:
      numValidSides--;
      if (hasParent && parentSide == side) {
        hasParent = false;
        stopComm(Side_Name::top);
        stopComm(Side_Name::right);
        stopComm(Side_Name::bottom);
        stopComm(Side_Name::left);
      }
      if (numValidSides == 1 && hasParent) {
        sendMessage(parentSide, done_message);
      }
      break;

    case Message_Type::timeout:
      numAliveSides--;
      if (numAliveSides == 0) {
        resetTile();
      }
      break;
    case Message_Type::done:
      stopComm(side);
      break;
    case Message_Type::parent:
      if (hasParent) {
        LOG("already have parent");
        stopComm(side);
      }
      else {
        hasParent = true;
        parentSide = side;

        // Adjust orientation
        Side_Name requestSide = (Side_Name) message.words[1];
        LOG(String("from ") + sideToString(requestSide));
        if (side != requestSide) {
          LOG("flipping");
          tileFlipped = true;
        }
        Message selfTileMessage (Message_Type::tile, 0, 0, flipEncoding(tileEncoding, tileFlipped));
        sendMessage(parentSide, selfTileMessage);
        if(numValidSides > 1){
          // Send parent requests to all other sides
          if (parentSide != Side_Name::top) {
            Message parent_message (Message_Type::parent, tileFlipped ? Side_Name::top : Side_Name::bottom);
            sendMessage(Side_Name::top, parent_message);
          }
          if (parentSide != Side_Name::right) {
            Message parent_message (Message_Type::parent, tileFlipped ? Side_Name::right : Side_Name::left);
            sendMessage(Side_Name::right, parent_message);
          }
          if (parentSide != Side_Name::bottom) {
            Message parent_message (Message_Type::parent, tileFlipped ? Side_Name::bottom : Side_Name::top);
            sendMessage(Side_Name::bottom, parent_message);
          }
          if (parentSide != Side_Name::left) {
            Message parent_message (Message_Type::parent, tileFlipped ? Side_Name::left : Side_Name::right);
            sendMessage(Side_Name::left, parent_message);
          }
        } else {
          sendMessage(parentSide, done_message);
        }
      }
      break;
    case Message_Type::tile:
      if (hasParent) {
        char oldX = (char) message.words[1];
        char oldY = (char) message.words[2];
        byte encoding = message.words[3];
        LOG("old x: " + String(oldX) + " old y: " + String(oldY) + " encoding: " + String(encoding));
        char newX, newY;
        translateCoordinates(&newX, &newY, oldX, oldY, side, tileFlipped);
        LOG("new x: " + String(newX) + " new y: " + String(newY) + " encoding: " + String(encoding));
        Message translatedTileMessage (Message_Type::tile, newX, newY, encoding);
        sendMessage(parentSide, translatedTileMessage);
      }
      break;
    default:
      stopComm(side);
      break;
  }
}



void setup() {
  initDriver(handleNewMessage);
  LOG("initializing");
  resetTile();
}

void loop() {
  updateDriver();
}
