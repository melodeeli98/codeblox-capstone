#include "message_manager.h"
#include "codeblox_driver.h"
#include <ArduinoSTL.h>
#include <functional-vlpp.h>
#include <map>
#include <list>
using namespace std;
using namespace vl;


const int word_size = 10;
const int clock_period = 1000000UL; //uS


void sendMessages(Side_Name side);

void waitSideMessages(enum Side_Name side);


void sendTopMessages(){
  sendMessages(Side_Name::top);
}
void sendRightMessages(){
  sendMessages(Side_Name::right);
}
void sendBottomMessages(){
  sendMessages(Side_Name::bottom);
}
void sendLeftMessages(){
  sendMessages(Side_Name::left);
}

void waitSideMessages(enum Side_Name side){
  switch(side){
    case Side_Name::top:
      waitMicrosThen(clock_period, sendTopMessages);
      break;
    case Side_Name::right:
      waitMicrosThen(clock_period, sendRightMessages);
      break;
    case Side_Name::bottom:
      waitMicrosThen(clock_period, sendBottomMessages);
      break;
    case Side_Name::left:
      waitMicrosThen(clock_period, sendLeftMessages);
      break;
  }
}

class MessageManager {
  list<unsigned int> incomingWords;
  unsigned long lastReceivedBit;
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
    void enqueueMessage(Message *message){
      for (list<unsigned int>::iterator it = message->words->begin(); it != message->words->end(); it++){
        //precede word with one to track bit to send
        unsigned int word = *it | (1<< (word_size-1));
        outgoingWords.push_back(word);
        serialLog(String("enqueing ") + String(word, BIN));
      }
      delete message->words;
      delete message;
    }
    void start(){
      sendingMessages = true;
      firstWord = true;
      firstBit = true;
      waitSideMessages(side);
    }
    void processNewBit(){
      if(sendingMessages){
        int numBits = 1;
        if(firstBit){
          firstBit = false;
        }else{
          numBits = (timeMicros() - lastReceivedBit + clock_period/2) / clock_period;
        }
        serialLog(String("Num bits: ") + String(numBits));
        lastReceivedBit = timeMicros();
        unsigned long _lastReceivedBit = lastReceivedBit;
        waitMicrosThen((word_size+1)*clock_period ,[_lastReceivedBit, this](){
            if(lastReceivedBit == _lastReceivedBit){
              serialLog("Timeout");
              stop();
            }
        });
        if(numBits <= 0){
          //bit sent too soon.  Failure condition
          serialLog("bit sent too soon");
          stop();
          return;
        }
        if(incomingWords.empty()){
          serialLog("empty incoming words");
          incomingWords.push_back(1);
        }else{
          serialLog("non-empty incoming words");
          unsigned int word = incomingWords.back();
          int wordBits = 0;
          while(word >> wordBits){
            wordBits++;
          }
          if(wordBits + numBits == word_size){
            serialLog("word full");
            word <<= (numBits-1);
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
                if(incomingWords.size() >= 2){
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
            serialLog(String("adding to word ") + String(word, BIN));
            word = (word << numBits) | 1;
            incomingWords.pop_back();
            incomingWords.push_back(word);
          }
        }
      }
    }
    void stop(){
      outgoingWords.clear();
      incomingWords.clear();
      sendingMessages = false;
      newMessageCallback(new Message(Message_Type::stop), side);
    }
};



std::map<enum Side_Name, MessageManager *> messageManagers;

void sendMessages(Side_Name side){
  if(messageManagers[side]->sendingMessages){
    
    waitSideMessages(side);
    
    if(messageManagers[side]->outgoingWords.empty()){
      messageManagers[side]->enqueueMessage(new Message(Message_Type::alive));
    }
    unsigned int next = messageManagers[side]->outgoingWords.front();
    messageManagers[side]->outgoingWords.pop_front();
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
      messageManagers[side]->outgoingWords.push_front(next);
    }
    
    if(sendHigh){
      sendPulseThen(side, [](){}); 
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

namespace mm{
  void init(void (*callback)(Message*, enum Side_Name)){
    //messageManagers[Side_Name::top] = new MessageManager (Side_Name::top, callback);
    messageManagers[Side_Name::right] = new MessageManager (Side_Name::right, callback);
    //messageManagers[Side_Name::bottom] = new MessageManager (Side_Name::bottom, callback);
    //messageManagers[Side_Name::left] = new MessageManager (Side_Name::left, callback);
  }
  void wakeup(){
    //messageManagers[Side_Name::top]->start();
    messageManagers[Side_Name::right]->start();
    //messageManagers[Side_Name::bottom]->start();
    //messageManagers[Side_Name::left]->start();
  }
  void newBit(enum Side_Name s){
    messageManagers[s]->processNewBit();
  }
  void sendMessage(Message* m, enum Side_Name s){
    messageManagers[s]->enqueueMessage(m);
  }
}

