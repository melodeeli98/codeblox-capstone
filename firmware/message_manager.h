#pragma once

#include "codeblox_driver.h"
#include <ArduinoSTL.h>
#include <list>


const int word_size = 10;
const long clock_period = 100000UL; //uS

enum Message_Type : unsigned int{ wakeup=0b100000000, alive=0b100000001, parent=0b100000010, tile=0b100000011, done=0b100000100, stop=0b100000101};

class Message {
    public:
      std::list<unsigned int> *words;
      enum Message_Type type;

      Message(enum Message_Type _type, unsigned int _x, unsigned int _y, unsigned int _encoding){
        words = new std::list<unsigned int>();
        words->push_front(_type);
        words->push_back(_x | (1<<(word_size-2)));
        words->push_back(_y | (1<<(word_size-2)));
        words->push_back(_encoding | (1<<(word_size-2)));
        type = _type;
      }
      
      Message(enum Message_Type _type, unsigned int _word){
        words = new std::list<unsigned int>();
        words->push_front(_type);
        words->push_back(_word | (1<<(word_size-2)));
        type = _type;
      }

      Message(enum Message_Type _type){
        words = new std::list<unsigned int>();
        words->push_front(_type);
        type = _type;
      }
      ~Message(){
        delete words;
      }

      static Message * newTileMessage(signed char x, signed char y, unsigned int encoding){
        return new Message(Message_Type::tile, (unsigned int)((unsigned char) x), (unsigned int) ((unsigned char) y), encoding);
      }

      String toString(){
        String s = "";
        switch(type){
          case tile:
            s = "tile: ";
            break;
          case parent:
            s = "parent: ";
            break;
          case alive:
            s = "alive: ";
            break;
          case done:
            s = "done: ";
            break;
          case stop:
            s = "stop: ";
            break;
          default:
            s = "unknown message: ";
            break;
        }
        for (std::list<unsigned int>::iterator it = words->begin(); it != words->end(); it++){
          s +=  String(*it, BIN);
          s += " ";
        }
        return s;
      }

      std::list<unsigned int> getData(){
        std::list<unsigned int>::iterator it = words->begin();
        it++;
        std::list<unsigned int> data;
        for (; it != words->end(); it++){
          data.push_back((*it) &  (~(1<<(word_size-2))));
        }
        return data;
      }
};

namespace mm {
  void init(void (*)(Message, enum Side_Name));
  void wakeup();
  void newBitCallback(enum Side_Name);
  void stop(enum Side_Name);
  void sendMessage(Message*, enum Side_Name);
  void update();
}
