#pragma once

const int word_size = 8;
const unsigned long clock_period = 10000UL; //uS

enum Message_Type : byte{ wakeup=0, alive=1, parent=2, tile=3, done=4, stop=5};

#include "codeblox_driver.h"

int numberOfDataWords(Message_Type m){
  switch(m){
    case parent:
      return 1;
    case tile:
      return 3;
    default:
      return 0;
  }
}

const int max_message_size = 4;

class Message {  
public:
  Message_Type type;
  byte words[max_message_size];
  int num_words;
  
  Message(enum Message_Type _type){
    type = _type;
    words[0] = type;
    num_words = 1;
  }
  Message(enum Message_Type _type, Side_Name side){
    type = _type;
    words[0] = _type;
    words[1] = (byte) side;
    num_words = 2;
  }
  Message(enum Message_Type _type, char x, char y, byte encoding){
    type = _type;
    words[0] = _type;
    words[1] = (byte) x;
    words[2] = (byte) y;
    words[3] = encoding;
    num_words = 4;
  }
  Message(int _num_words, byte _words[]){
    type = (Message_Type) _words[0];
    num_words = _num_words;
    for(int i = 0; i < _num_words; i++){
      words[i] = _words[i];
    }
  }
  String toString() const {
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
      case wakeup:
        s = "wakeup: ";
        break;
      default:
        s = "unknown message: ";
        s += String(words[0], BIN);
        s += " ";
        break;
    }
    for (int i = 1; i < num_words; i++){
      s +=  String(words[i]);
      s += " ";
    }
    return s;
  }
};


const Message done_message (Message_Type::done);
const Message stop_message (Message_Type::stop);
