#include "message_manager.h"
#include "codeblox_driver.h"
#include <ArduinoSTL.h>
#include <MemoryFree.h>
#include <list>
using namespace std;

class MessageManager {
  list<unsigned int> incomingWords;
  unsigned long lastReceivedBit;
  unsigned long nextTransmissionTime;
  bool firstWord;
  bool firstBit;
  enum Side_Name side;
  void (*newMessageCallback)(Message*, enum Side_Name);

  public:
    list<unsigned int> outgoingWords;
    bool sendingMessages;
    MessageManager(enum Side_Name _side, void (*_newMessageCallback)(Message*, enum Side_Name)){
      side = _side;
      sendingMessages = false;
      newMessageCallback = _newMessageCallback;
    }
    void update(){
      if(sendingMessages){
        if((word_size+1)*clock_period < timeMicros() - lastReceivedBit){
          serialLog("Timeout");
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
              serialLog("sending high");
            }
          }else{
            if(side == Side_Name::right){
              serialLog("sending low");
            }
          }
        }
      }
    }
    void enqueueMessage(Message *message){
      for (list<unsigned int>::iterator it = message->words->begin(); it != message->words->end(); it++){
        //precede word with one to track bit to send
        serialLog(String("enqueing ") + String(*it, BIN));
        unsigned int word = *it | (1<< (word_size-1));
        outgoingWords.push_back(word);
      }
      delete message->words;
      delete message;
    }
    void start(){
      sendingMessages = true;
      firstWord = true;
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
          serialLog("bit sent too soon");
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
          serialLog("w+n= " + String(wordBits) + "+" + String(numBits));
          if(wordBits + numBits == word_size){
            word <<= (numBits-1);
            serialLog(word, BIN);
            incomingWords.pop_back();
            incomingWords.push_back(word);
            incomingWords.push_back(1);
            //check for new message
            switch(incomingWords.front()){
              case Message_Type::wakeup:
                incomingWords.pop_front();
                if(firstWord){
                  firstWord = false;
                }else{
                  serialLog("sent wakeup after another message");
                  stop();
                  return;
                }
                break;
              case Message_Type::alive:
                firstWord = false;
                incomingWords.pop_front();
                break;
              case Message_Type::generic:
                if(incomingWords.size() >= 3){
                  firstWord = false;
                  incomingWords.pop_front();
                  newMessageCallback(new Message(Message_Type::generic,incomingWords.front()), side);
                  incomingWords.pop_front();
                }
                break;
              default:
                serialLog("Invalid message type");
                stop();
                return;
            }
            
          }else if(wordBits + numBits > word_size){
            serialLog("Message contains too many bits");
            stop();
            return;
          }else{
            serialLog("adding to word ");
            word = (word << numBits) | 1;
            serialLog(word, BIN);
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
        newMessageCallback(new Message(Message_Type::stop), side);
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
}

namespace mm{
  void init(void (*callback)(Message*, enum Side_Name)){
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
  void newBit(enum Side_Name s){
    getMessageManager(s)->processNewBit();
  }
  void sendMessage(Message* m, enum Side_Name s){
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

