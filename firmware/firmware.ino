#include "codeblox_driver.h"
#include "message_manager.h"
#include <ArduinoSTL.h>
#include <list>
#include <MemoryFree.h>
using namespace std;



bool asleep = true;


void newMessage(Message message, enum Side_Name side){
  serialLog(sideToString(side));
  serialLog(message.toString());
  if(message.type == Message_Type::generic){
    mm::stop(side);
    serialLog("Received Message!!!");
    serialLog(message.getData().front());
  }
}

void dataTriggered(Side_Name s)
{
  serialLog("data Triggered!");
  if(asleep){
    asleep = false;
    mm::wakeup();
  }
  mm::newBit(s);
}

void processSerialMessage(char *message)
{
  serialLog("freeMemory()=");
  serialLog(freeMemory());
  unsigned int v = (unsigned int) String(message).toInt();
  if(v){
    if(asleep){
      asleep = false;
      mm::wakeup();
    }
    mm::sendMessage(new Message(Message_Type::generic, v), Side_Name::right);
  }
}


void setup()
{
  initDriver(dataTriggered);
  listenForSerialMessages(processSerialMessage);
  mm::init(newMessage);
  serialLog("Restarted");
  serialLog("freeMemory()=");
  serialLog(freeMemory());
  
  asleep = true;
}


void loop()
{
  updateDriver();
  mm::update();
}
