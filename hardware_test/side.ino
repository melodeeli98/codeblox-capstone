#include <avr/interrupt.h>
#include <avr/io.h>
#include <ArduinoSTL.h>
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

enum Int_Type
{
  PCINT,
  INT
};

bool flipped = false;

class Side
{
  enum Side_Name sideName;
  void (*dataCallback)(enum Side_Name);
  volatile bool triggered;
  Int_Type intType;
  const unsigned long pulseWidth = 50UL; //uS
public:
  Side(enum Side_Name n, void (*callback)(enum Side_Name))
  {
    sideName = n;
    triggered = false;
    dataCallback = callback;
    if (n == Side_Name::top || n == Side_Name::left)
    {
      intType = Int_Type::INT;
    }
    else
    {
      intType = Int_Type::PCINT;
    }
  };
  void update()
  {
    if (interruptsEnabled() && triggered)
    {
      triggered = false;
      if (!flipped)
      {
        dataCallback(sideName);
      }
      else
      {
        dataCallback(opposite(sideName));
      }
    }
  }
  void trigger()
  {
    if (intType == Int_Type::INT || readData() == HIGH)
    {
      triggered = true;
    }
  }
  void toggleData()
  {
    setData(HIGH);
    delayMicroseconds(pulseWidth);
    setData(LOW);
  }
  void setData(int value)
  {
    if (sideName == Side_Name::top)
    {
      digitalWrite(5, value);
    }
    else if (sideName == Side_Name::right)
    {
      digitalWrite(8, value);
    }
    else if (sideName == Side_Name::bottom)
    {
      digitalWrite(7, value);
    }
    else if (sideName == Side_Name::left)
    {
      digitalWrite(6, value);
    }
  }
  int readData()
  {
    int value = 0;
    if (sideName == Side_Name::top)
    {
      value = digitalRead(2);
    }
    else if (sideName == Side_Name::right)
    {
      value = PIND & (1 << PIND4);
    }
    else if (sideName == Side_Name::bottom)
    {
      value = PINB & (1 << PINB6);
    }
    else if (sideName == Side_Name::left)
    {
      value = digitalRead(3);
    }
    if (value)
    {
      return HIGH;
    }
    else
    {
      return LOW;
    }
  }
};

enum Side_Name
opposite(enum Side_Name side)
{
  switch (side)
  {
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

String sideToString(Side_Name side){
  switch (side)
  {
  case Side_Name::top:
    return String("top");
  case Side_Name::right:
    return String("right");
  case Side_Name::bottom:
    return String("bottom");
  case Side_Name::left:
    return String("left");
  default:
    return String("idk");
  }
}

Side_Name
sideFromString(String side)
{
  if (side == "top")
  {
    return Side_Name::top;
  }
  else if (side == "right")
  {
    return Side_Name::right;
  }
  else if (side == "bottom")
  {
    return Side_Name::bottom;
  }
  else
  {
    return Side_Name::left;
  }
}


Side * topSide;
Side * rightSide;
Side * bottomSide;
Side * leftSide;

class Side * getSide(enum Side_Name side){
  switch(side){
    case Side_Name::top:
      return topSide;
    case Side_Name::right:
      return rightSide;
    case Side_Name::bottom:
      return bottomSide;
    case Side_Name::left:
      return leftSide;
  }
}

void topTrigger()
{
  topSide->trigger();
}

void leftTrigger()
{
  leftSide->trigger();
}

//bottom Trigger
ISR(PCINT0_vect)
{
  bottomSide->trigger();
}

//right Trigger
ISR(PCINT2_vect)
{
  rightSide->trigger();
}

void initSides(void (*dataCallback)(enum Side_Name))
{

  topSide = new Side(Side_Name::top, dataCallback);
  rightSide = new Side(Side_Name::right, dataCallback);
  bottomSide = new Side(Side_Name::bottom, dataCallback);
  leftSide = new Side(Side_Name::left, dataCallback);

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
  PCICR |= 0b00000101;  // Enables Ports B and D Pin Change Interrupts
  PCMSK0 |= 0b01000000; // PCINT6
  PCMSK2 |= 0b00010000; // PCINT20
  pinMode(2, INPUT);
  pinMode(3, INPUT);
  attachInterrupt(0, topTrigger, RISING);
  attachInterrupt(1, leftTrigger, RISING);
  sei();
}

void updateSides()
{
  topSide->update();
  rightSide->update();
  bottomSide->update();
  leftSide->update();
}

void flipTile()
{
  flipped = !flipped;
}

void sendPulse(Side_Name side)
{
  if (flipped)
  {
    side = opposite(side);
  }
  getSide(side)->toggleData();
}

