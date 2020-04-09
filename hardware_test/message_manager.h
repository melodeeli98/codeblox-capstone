#pragma once

#include "codeblox_driver.h"
#include <ArduinoSTL.h>
#include <functional-vlpp.h>
#include <list>

enum Message_Type : unsigned int{ wakeup=0b100000000, alive=0b100000001, generic=0b100000010, stop=0b100000011};

class Message {
    public:
      std::list<unsigned int> *words;
      enum Message_Type type;
      Message(enum Message_Type _type, std::list<unsigned int> *_words){
        _words->push_front(type);
        words = _words;
        type = _type;
      }
      
      Message(enum Message_Type _type,unsigned int _word){
        words = new std::list<unsigned int>();
        words->push_front(type);
        words->push_back(_word);
        type = _type;
      }

      Message(enum Message_Type _type){
        words = new std::list<unsigned int>();
        words->push_front(type);
        type = _type;
      }

      String toString(){
        String s = "";
        if(type == generic){
          s = "generic: ";
        }
        for (std::list<unsigned int>::iterator it = words->begin(); it != words->end(); it++){
          s = s +  String(*it, BIN) + " ";
        }
        return s;
      }
};

namespace mm {
  void init(void (*)(Message*, enum Side_Name));
  void wakeup();
  void newBit(enum Side_Name);
  void sendMessage(Message*, enum Side_Name);
}

