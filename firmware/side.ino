#include <avr/interrupt.h>
#include <avr/io.h>
#include "codeblox_driver.h"
#include "message.h"

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

volatile bool asleep;

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
    if(start > end){
      return buf_size - start + end;
    }else{
      return end-start;
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

static void startSendTimer();

void (*newMessageCallback)(const Message &, enum Side_Name);

class Side{
  enum Side_Name sideName;
  volatile int currOutBit;
  volatile byte currOutWord;
  volatile byte currInWord;
  volatile int timeout;
  volatile bool receivedFirstBit;
  volatile bool receivedWakeup;
  volatile unsigned long lastReceivedBit;
  volatile bool sentStop;
public:
  RingBuffer outBuffer;
  RingBuffer inBuffer;
  volatile bool neighborIsValid;

  Side(enum Side_Name n){
    sideName = n;
    neighborIsValid = false;
  };

  void startSending(){
    outBuffer.clear();
    inBuffer.clear();
    currOutBit = word_size;
    currOutWord = Message_Type::wakeup;
    currInWord = 0;
    timeout = 0;
    receivedFirstBit = false;
    receivedWakeup = false;
    sentStop = false;

    //must be last
    neighborIsValid = true;
  }

  void stop(){
    neighborIsValid = false;//must happen first
  }

  void update(){
    if(neighborIsValid){
      if(inBuffer.size() > 0){
        Message_Type m = (Message_Type) inBuffer.peek();
        int messageSize = numberOfDataWords(m) + 1;
        if(inBuffer.size() >= messageSize){
          byte words [messageSize];
          for(int i = 0; i < messageSize; i++){
            words[i] = inBuffer.dequeue();
          }
          Message receivedMessage (messageSize, words);
          newMessageCallback(receivedMessage, sideName);
        }
      }
    } else if(!sentStop){
      sentStop = true;
      newMessageCallback(stop_message, sideName);
    }
  }

  //new data bit trigger
  void trigger(){
    if(neighborIsValid || asleep){
      if(asleep){
        resetClock();
        startCommAllSides();
        startSendTimer();
        asleep = false;
      }
      timeout = 0;
      int numBits = 1;
      if(!receivedFirstBit){
        receivedFirstBit = true;
      }else{
        numBits = (timeMicros() - lastReceivedBit + clock_period/2) / clock_period;
      }
      lastReceivedBit = timeMicros();
      
      if(numBits <= 0){
        //bit sent too soon.  Failure condition
        stop();
        return;
      }
      int currWordBits = 0;
      while(currInWord >> currWordBits){
        currWordBits++;
      }
      if(currWordBits + numBits == word_size + 2){
        currInWord <<= (numBits-1);
        currInWord &= ~(1<<word_size);
        if(!receivedWakeup && currInWord != Message_Type::wakeup){
          stop();
        }else if (receivedWakeup && currInWord == Message_Type::wakeup){
          stop();
        } else {
          receivedWakeup = true;
          if( currInWord != Message_Type::alive && currInWord != Message_Type::wakeup){
            inBuffer.enqueue(currInWord);
          }
        }
        currInWord = 1;
        
      }else if(currWordBits + numBits > word_size + 2){
        stop();
        return;
      }else{
        currInWord = (currInWord << numBits) | 1;
      }
    } 
  }
  
  //time to send data bit
  void sendBit(){
    if(neighborIsValid){
      if(currOutBit == word_size){
        setData(HIGH);
      }else{
        if(currOutWord & (1 << currOutBit)){
          setData(HIGH);
        }
      }
      currOutBit--;
      if(currOutBit < 0){
        if(outBuffer.size() > 0){
          currOutWord = outBuffer.dequeue();
        }else{
          currOutWord = Message_Type::alive;
        }
        currOutBit = word_size;        
      }
      timeout++;
      if(timeout > word_size + 3){
        stop();
      }
    }
  }

  void setData(int value){
    if (sideName == Side_Name::top){
      digitalWrite(5, value);
    } else if (sideName == Side_Name::right){
      digitalWrite(8, value);
    } else if (sideName == Side_Name::bottom){
      digitalWrite(7, value);
    } else if (sideName == Side_Name::left){
      digitalWrite(6, value);
    }
  }
};


String sideToString(Side_Name side){
  switch (side){
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


Side topSide (Side_Name::top);
Side rightSide (Side_Name::right);
Side bottomSide (Side_Name::bottom);
Side leftSide (Side_Name::left);

class Side * getSide(enum Side_Name side){
  switch(side){
    case Side_Name::top:
      return &topSide;
    case Side_Name::right:
      return &rightSide;
    case Side_Name::bottom:
      return &bottomSide;
    case Side_Name::left:
      return &leftSide;
  }
  return NULL;
}

void topTrigger()
{
  topSide.trigger();
}

void leftTrigger()
{
  leftSide.trigger();
}

//bottom Trigger
ISR(PCINT0_vect)
{
  if(!(PINB & (1 << PINB6))){
    bottomSide.trigger();
  }
}

//right Trigger
ISR(PCINT2_vect)
{
  if(!(PIND & (1 << PIND4))){
    rightSide.trigger();
  }
}

//timer interrupt
ISR(TIMER1_COMPA_vect)
{
  topSide.sendBit();
  rightSide.sendBit();
  bottomSide.sendBit();
  leftSide.sendBit();
  delayMicroseconds(100UL);
  topSide.setData(LOW);
  rightSide.setData(LOW);
  bottomSide.setData(LOW);
  leftSide.setData(LOW);
}


void initSides(void (*callback)(const Message &, enum Side_Name)){
  asleep = false;

  newMessageCallback = callback;
  
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
  attachInterrupt(0, topTrigger, FALLING);
  attachInterrupt(1, leftTrigger, FALLING);

  //reset timer1 control reg A
  TCCR1A = 0;
  //no prescaler
  TCCR1B &= ~(1<<CS12);
  TCCR1B |= (1<<CS11);
  TCCR1B &= ~(1<<CS10);
  const unsigned long pre_scaler = 8;
  // Set CTC mode
  TCCR1B |= (1<<WGM12);
  TCCR1B &= ~(1<<WGM13);
  //reset timer and set compare value
  OCR1A = clock_period/pre_scaler;
  //enable timer compare interrupt
  startSendTimer();
  sei();
}

void updateSides(){
  topSide.update();
  rightSide.update();
  bottomSide.update();
  leftSide.update();
}


static void startSendTimer(){
  TCNT1 = 0;
  TIMSK1 = (1<<OCIE1A);
}

void stopSendTimer(){
  TIMSK1 = 0;
  asleep = true;
}

void sendMessage(Side_Name s, const Message& m){
  Side *side = getSide(s);
  for(int i = 0; i < m.num_words; i++){
    side->outBuffer.enqueue(m.words[i]);
  }
}

void startCommAllSides(){
  topSide.startSending();
  rightSide.startSending();
  bottomSide.startSending();
  leftSide.startSending();
}

void stopComm(Side_Name side_name){
  getSide(side_name)->stop();
}

