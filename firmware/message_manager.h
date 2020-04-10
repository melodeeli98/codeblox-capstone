#pragma once

#include "codeblox_driver.h"
#include <ArduinoSTL.h>
#include <list>


const int word_size = 10;
const long clock_period = 1000000UL; //uS

enum Message_Type : unsigned int{ wakeup=0b100000000, alive=0b100000001, generic=0b100000010, stop=0b100000011};

class Message {
    public:
      std::list<unsigned int> *words;
      enum Message_Type type;
      
      Message(enum Message_Type _type,unsigned int _word){
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

      String toString(){
        String s = "";
        if(type == generic){
          s = "generic: ";
        }
        for (std::list<unsigned int>::iterator it = words->begin(); it != words->end(); it++){
          s +=  String(*it, BIN);
          s += " ";
        }
        return s;
      }
};

namespace mm {
  void init(void (*)(Message*, enum Side_Name));
  void wakeup();
  void newBit(enum Side_Name);
  void stop(enum Side_Name);
  void sendMessage(Message*, enum Side_Name);
  void update();
}

