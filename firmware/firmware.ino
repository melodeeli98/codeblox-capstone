#include "codeblox_driver.h"
#include "message_manager.h"
#include <ArduinoSTL.h>
#include <list>
using namespace std;

int numValidSides = 4;
Side_Name parentSide = NULL;
unsigned int tileEncoding = 0;
bool flipped = false;

// Resets tile state between compilations
void resetTile(){
  goToSleep();
  // TODO
  numValidSides = 4;
  parentSide = NULL;
  flipped = false;
  readReflectiveSensorsLater(&tileEncoding);
}

void translateCoordinates(signed char * newX, signed char * newY, signed char oldX, signed char oldY, Side_Name side, bool flipped){
  *newX = oldX;
  *newY = oldY;
  signed char multiplier = 1;
  if (flipped) {
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

void handleNewMessage(Message message, enum Side_Name side){
  switch (message) {
    case Message::stop:
      numValidSides--;
      if (parentSide == side) {
        parentSide = NULL;
      }
      if (numValidSides == 1 && parentSide != NULL) {
        mm::sendMessage(Message::newTileMessage(0, 0, tileEncoding));
        mm::sendMessage(new Message(Message_Type::done));
      }
      if (numValidSides == 0) {
        resetTile();
      }
      break;
    case Message::done:
      mm::stop(side);
      break;
    case Message::parent:
      if (parent != NULL){
        mm::stop(side);
      }
      else{

        // Adjust orientation
        unsigned int requestSide = getData().first()
        if (side != requestSide) {
          flipped = true;
        }

        parent = side;

        // Send parent requests to all other sides
        if (parent != Side_Name::top) {
          mm::sendMessage(new Message(Message_Type::parent, Side_Name::bottom));
        }
        if (parent != Side_Name::right) {
          mm::sendMessage(new Message(Message_Type::parent, Side_Name::left));
        }
        if (parent != Side_Name::bottom) {
          mm::sendMessage(new Message(Message_Type::parent, Side_Name::top));
        }
        if (parent != Side_Name::left) {
          mm::sendMessage(new Message(Message_Type::parent, Side_Name::left));
        }
      }
    case Message::tile:
      if (parent != NULL):
        data = getData();
        signed char oldX = (signed char) data.first();
        data.pop_front();
        signed char oldY = (signed char) data.first();
        data.pop_front();
        unsigned int encoding = data.first();
        signed char newX, newY;
        translateCoordinates(&newX, &newY, oldX, oldY, side, flipped);
        mm::sendMessage(new Message(Message_Type::tile, (unsigned int) newX, (unsigned int) newY, encoding));

  }
}

void setup(){
  initDriver(mm::newBitCallback);
  mm::init(handleNewMessage);
  resetTile();
}

void loop(){
  updateDriver();
  mm::update();
}
