#include <avr/interrupt.h>
#include <avr/io.h>
#include <vector>
#include <map>
#include "codeblox_driver.h"
using namespace std;

//IR inputs
//topPin = 4; // External, INT0
//rightPin = // PortD 4, PCINT20
//bottomPin = 9; // PortB 6, PCINT6
//leftPin = 6; 5; // External, INT1

//IR outputs
// T arduino pin 5
// R arduino pin 8
// B arduino pin 7
// L arduino pin 6

enum Int_Type {PCINT, INT};

bool flipped = false;

class Side{
    Side_Name sideName;
    void (*dataCallback)(Side_Name);
    void (*toggleCallback)(void);
    unsigned long toggleTime;
    volatile bool triggered;
    Int_Type intType;
    const unsigned long pulseWidth = 500UL;//uS
  public:
    Side(Side_Name n, void (*callback)(Side_Name)){
      sideName = n;
      toggleCallback = NULL;
      toggleTime = 0UL;
      triggered = false;
      dataCallback = callback;
      if(n == Side_Name::top || n == Side_Name::left){
        intType = Int_Type::INT;
      }else{
        intType = Int_Type::PCINT;
      }
    };
    void update(){
      if(toggleCallback != NULL && toggleTime < micros()){
        setData(LOW);
        void (*callback)(void) = toggleCallback;
        toggleCallback = NULL;
        callback();
      }
      if(interruptsEnabled() && triggered){
        triggered = false;
        if(!flipped){
          dataCallback(sideName);
        }else{
          dataCallback(opposite(sideName));
        }
      }
    }
    void trigger(){
      if (intType == Int_Type::INT || readData() == HIGH) {
        triggered = true;
      }
    }
    void toggleDataThen(void (*callback)(void)){
      if(toggleCallback != NULL){
        serialLog("Error: overlapping toggle");
      }
      setData(HIGH);
      toggleCallback = callback;
      toggleTime = micros()+pulseWidth;
    }
    void setData(int value){
      if (sideName == Side_Name::top) {
        digitalWrite(5, value);
      } else if (sideName == Side_Name::right) {
        digitalWrite(8, value);
      } else if (sideName == Side_Name::bottom) {
        digitalWrite(7, value);
      } else if (sideName == Side_Name::left) {
        digitalWrite(6, value);
      }
    }
    int readData(){
      int value = 0
      if (sideName == Side_Name::top) {
        value = digitalRead(2);
      } else if (sideName == Side_Name::right) {
        value = PIND & (1 << PIND4);
      } else if (sideName == Side_Name::bottom) {
        value = PINB & (1 << PINB6);
      } else if (sideName == Side_Name::left) {
        value = digitalRead(3);
      }
      if (value) {
        return HIGH;
      }else{
        return LOW;
      }
    }
}


Side_Name opposite(Side_Name side){
  switch(side){
    case Side_Name::top:
      return Side_Name::bottom;
    case Side_Name::right:
      return Side_Name::left;
    case Side_Name::bottom:
      return Side_Name::top;
    case Side_Name::left:
      return Side_Name::right;
    default:
      return Side_Name::top;
  }
}

Side_Name sideFromString(String side){
  
}

void (*dataCallback)(Side_Name) = NULL;

map<Side_Name, Side*> sides;
sides[Side_Name::top] = new Side(Side_Name::top, dataCallback);
sides[Side_Name::right] = new Side(Side_Name::right, dataCallback);
sides[Side_Name::bottom] = new Side(Side_Name::bottom, dataCallback);
sides[Side_Name::left] = new Side(Side_Name::left, dataCallback);

void topTrigger(){
  sides[Side_Name::top]->trigger();
}

void rightTrigger(){
  sides[Side_Name::right]->trigger();
}

//bottom Trigger
ISR(PCINT0_vect) {
  sides[Side_Name::bottom]->trigger();
}

//left Trigger
ISR(PCINT2_vect) {
  sides[Side_Name::left]->trigger();
}

void initSides(void (*callback)(Side_Name)) {
  dataCallback = callback;
  
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
  pinMode(7, OUTPUT);
  pinMode(8, OUTPUT);  

  //attach interrupts to IR receivers
  cli();
  DDRB &= ~(1 << PINB6);
  DDRD &= ~(1 << PIND4);
  PORTB &= ~(1 << PINB6);
  PORTD &= ~(1 << PIND4);
  PCICR  |= 0b00000101; // Enables Ports B and D Pin Change Interrupts
  PCMSK0 |= 0b01000000; // PCINT6
  PCMSK2 |= 0b00010000; // PCINT20
  pinMode(2, INPUT);
  pinMode(3, INPUT);
  attachInterrupt(0, topTrigger, RISING);
  attachInterrupt(1, rightTrigger, RISING);
  sei();
}


void updateSides(){
  sides[Side_Name::top]->update()
  sides[Side_Name::right]->update()
  sides[Side_Name::bottom]->update()
  sides[Side_Name::left]->update()
}


void flipTile(){
  flipped = !flipped;
}


void sendPulseThen(Side_Name side, void (*callback)(void)){
  Side_Name s = side;
  if(flipped){
    side = opposite(side);
  }
  sides[side]->toggleDataThen(callback);
}


