#include "codeblox_driver.h"
#include "message_manager.h"
#include <ArduinoSTL.h>
#include <functional-vlpp.h>
#include <MemoryFree.h>
using namespace vl;
using namespace std;



bool asleep = true;


void newMessage(Message* message, enum Side_Name side){
  serialLog(sideToString(side));
  serialLog(message->toString());
  delete message->words;
  delete message;
}

void dataTriggered(Side_Name s)
{
  if(asleep){
    asleep = false;
    mm::wakeup();
  }
  mm::newBit(s);
}

void processSerialMessage(String message)
{
  if(message.toInt()){
    if(asleep){
      asleep = false;
      mm::wakeup();
    }
    mm::sendMessage(new Message(Message_Type::generic, (unsigned int) message.toInt()), Side_Name::right);
  }
}


void setup()
{
  initDriver(dataTriggered);
  serialLog("Starting up!");
  serialLog("freeMemory()=");
  serialLog(String(freeMemory()));
  mm::init(newMessage);
  serialLog("freeMemory()=");
  serialLog(String(freeMemory()));
  asleep = true;
  
}


void loop()
{
  updateDriver();

  if (newSerialMessage())
  {
    serialLog("freeMemory()=");
    serialLog(String(freeMemory()));
    processSerialMessage(getSerialMessage());
  }
}
