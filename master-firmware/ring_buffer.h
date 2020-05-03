#pragma once

class RingBuffer{
  const static int buf_size = 64;
  volatile byte buf[buf_size];
  volatile int start;
  volatile int end;
  volatile int currBit;
public:
  RingBuffer(){
    start = 0;
    end = 0;
  }
  void enqueue(byte w){
     buf[end] = w;
     end = (end+1) % buf_size;
  } 
  int size(){
    int _start = start;
    int _end = end;
    if(_start > _end){
      return buf_size - _start + _end;
    }else{
      return _end-_start;
    }
  }
  byte peek(){
    return buf[start];
  }
  byte dequeue(){
    byte w = buf[start];
    start = (start+1) % buf_size;
    return w;
  }  
  void clear(){
    start = end;
  }
};

