#include "message_manager.h"
#include "codeblox_driver.h"
#include <ArduinoSTL.h>
#include <list>
using namespace std;

class MessageManager {
  list<unsigned int> incomingWords;
  unsigned long lastReceivedBit;
  unsigned long nextTransmissionTime;
  bool firstWordReceived;
  bool firstBit;
  enum Side_Name side;
  void (*newMessageCallback)(Message, enum Side_Name);

  public:
    list<unsigned int> outgoingWords;
    bool sendingMessages;
    MessageManager(enum Side_Name _side, void (*_newMessageCallback)(Message, enum Side_Name)){
      side = _side;
      sendingMessages = false;
      newMessageCallback = _newMessageCallback;
    }
    void update(){
      if(sendingMessages){
        if((word_size+1)*clock_period < timeMicros() - lastReceivedBit){
          //LOG("Timeout");
          stop();
        }
        if(timeMicros() > nextTransmissionTime){
          nextTransmissionTime += clock_period;
          if(outgoingWords.empty()){
            enqueueMessage(new Message(Message_Type::alive));
          }
          unsigned int next = outgoingWords.front();
          outgoingWords.pop_front();
          bool sendHigh = false;
          int sendBit = 0;
          while(next >> sendBit){
            sendBit++;
          }
          sendBit-=2;
          if((next >> sendBit) & 1){
            sendHigh = true;
          }
          next |= (1<<sendBit);
          next &= ~(1<<(sendBit+1)); 
          if(sendBit > 0){
            outgoingWords.push_front(next);
          }
          
          if(sendHigh){
            sendPulse(side); 
            if(side == Side_Name::right){
              //LOG("sending high");
            }
          }else{
            if(side == Side_Name::right){
              //LOG("sending low");
            }
          }
        }
      }
    }
    void enqueueMessage(Message *message){
      if(sendingMessages){
        for (list<unsigned int>::iterator it = message->words->begin(); it != message->words->end(); it++){
          //precede word with one to track bit to send
          //LOG(String("enqueing ") + String(*it, BIN));
          unsigned int word = *it | (1<< (word_size-1));
          outgoingWords.push_back(word);
        }
      }
      delete message;
    }
    void start(){
      sendingMessages = true;
      firstWordReceived = false;
      firstBit = true;
      enqueueMessage(new Message(Message_Type::wakeup));
      nextTransmissionTime = timeMicros() + clock_period;
      lastReceivedBit = timeMicros();
    }
    void processNewBit(){
      if(sendingMessages){
        int numBits = 1;
        if(firstBit){
          firstBit = false;
        }else{
          numBits = (timeMicros() - lastReceivedBit + clock_period/2) / clock_period;
        }
        lastReceivedBit = timeMicros();
        
        if(numBits <= 0){
          //bit sent too soon.  Failure condition
          LOG("bit sent too soon");
          stop();
          return;
        }
        if(incomingWords.empty()){
          incomingWords.push_back(1);
        }else{
          unsigned int word = incomingWords.back();
          int wordBits = 0;
          while(word >> wordBits){
            wordBits++;
          }
          //LOG("w+n= " + String(wordBits) + "+" + String(numBits));
          if(wordBits + numBits == word_size){
            word <<= (numBits-1);
            //LOG(word, BIN);
            incomingWords.pop_back();
            incomingWords.push_back(word);
            incomingWords.push_back(1);
            //check for new message
            switch(incomingWords.front()){
              case Message_Type::wakeup:
                incomingWords.pop_front();
                if(!firstWordReceived){
                  firstWordReceived = true;
                }else{
                  LOG("sent wakeup after another message");
                  stop();
                  return;
                }
                break;
              case Message_Type::alive:
                firstWordReceived = true;
                incomingWords.pop_front();
                break;
              case Message_Type::parent:
                if(incomingWords.size() >= 3){
                  firstWordReceived = true;
                  incomingWords.pop_front();
                  newMessageCallback(Message(Message_Type::parent,incomingWords.front()), side);
                  incomingWords.pop_front();
                }
                break;
              case Message_Type::tile:
                if(incomingWords.size() >= 5){
                  firstWordReceived = true;
                  incomingWords.pop_front();
                  unsigned int x = incomingWords.front();
                  incomingWords.pop_front();
                  unsigned int y = incomingWords.front();
                  incomingWords.pop_front();
                  unsigned int encoding = incomingWords.front();
                  incomingWords.pop_front();
                  newMessageCallback(Message(Message_Type::tile, x, y, encoding), side);
                }
                break;
              case Message_Type::done:
                firstWordReceived = true;
                incomingWords.pop_front();
                newMessageCallback(Message(Message_Type::done), side);
                break;
              default:
                LOG("Invalid message type");
                stop();
                return;
            }
            
          }else if(wordBits + numBits > word_size){
            LOG("Message contains too many bits");
            stop();
            return;
          }else{
            //LOG("adding to word ");
            word = (word << numBits) | 1;
            //LOG(word, BIN);
            incomingWords.pop_back();
            incomingWords.push_back(word);
          }
        }
      }
    }
    void stop(){
      if(sendingMessages){
        outgoingWords.clear();
        incomingWords.clear();
        sendingMessages = false;
        newMessageCallback(Message(Message_Type::stop), side);
      }
    }
};



MessageManager * topMessageManager;
MessageManager * rightMessageManager;
MessageManager * bottomMessageManager;
MessageManager * leftMessageManager;

class MessageManager * getMessageManager(enum Side_Name side){
  switch(side){
    case Side_Name::top:
      return topMessageManager;
    case Side_Name::right:
      return rightMessageManager;
    case Side_Name::bottom:
      return bottomMessageManager;
    case Side_Name::left:
      return leftMessageManager;
  }
  return NULL;
}

namespace mm{
  void init(void (*callback)(Message, enum Side_Name)){
    topMessageManager = new MessageManager (Side_Name::top, callback);
    rightMessageManager = new MessageManager (Side_Name::right, callback);
    bottomMessageManager = new MessageManager (Side_Name::bottom, callback);
    leftMessageManager = new MessageManager (Side_Name::left, callback);
  }
  void wakeup(){
    topMessageManager->start();
    rightMessageManager->start();
    bottomMessageManager->start();
    leftMessageManager->start();
  }
  void newBitCallback(enum Side_Name s){
    getMessageManager(s)->processNewBit();
  }
  void sendMessage(Message* m, enum Side_Name s){
    LOG(String("SM ") + sideToString(s) + String(": ") + m->toString());
    getMessageManager(s)->enqueueMessage(m);
  }
  void update(){
    topMessageManager->update();
    rightMessageManager->update();
    bottomMessageManager->update();
    leftMessageManager->update();
  }

  void stop(enum Side_Name s){
    getMessageManager(s)->stop();
  }
}
