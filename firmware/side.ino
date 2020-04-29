#include <avr/interrupt.h>
#include <avr/io.h>
#include "codeblox_driver.h"
#include "message.h"
#include "ring_buffer.h"


static volatile bool asleep;
void (*newMessageCallback)(const Message &, enum Side_Name);
static volatile unsigned long interruptReceivedTime;

class Side{
  enum Side_Name sideName;
  volatile int currOutBit;
  volatile byte currOutWord;
  volatile unsigned int currInWord;
  volatile int timeout;
  volatile bool receivedFirstBit;
  volatile bool receivedWakeup;
  volatile unsigned long lastReceivedBit;
  volatile bool sentStop;
  volatile bool didTimeout;
  volatile bool sentTimeout;
  RingBuffer outBuffer;
  RingBuffer inBuffer;
  volatile bool receiving;
  volatile bool sending;
  

  void stopReceiving(){
    receiving = false;//must happen first
  }
  void stopSending(){
    sending = false;//must happen first
  }

  void setTimeout(){
    receiving = false;
    didTimeout = true;
    stopSending();
    stopReceiving();
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

  void startSending(){
    currOutBit = word_size;
    currOutWord = Message_Type::wakeup;

    //must be last
    sending = true;
  }

public:

  Side(enum Side_Name n){
    sideName = n;
    reset();
  };

  void reset(){
    inBuffer.clear();
    outBuffer.clear();
    currInWord = 0;
    timeout = 0;
    receivedFirstBit = false;
    receivedWakeup = false;
    sentStop = false;
    sentTimeout = false;
    didTimeout = false;
    
    receiving = false;
    sending = false;
  }
  
  void update(){
    if(receiving){
      bool usableMessage = false;
      while(inBuffer.size() > 0){
          Message_Type m = (Message_Type) inBuffer.peek();
          if(m == Message_Type::wakeup || m == Message_Type::alive){
            inBuffer.dequeue();
          } else {
            usableMessage = true;
            break;
          }
      }
      if(usableMessage){
        Message_Type m = (Message_Type) inBuffer.peek();
        int messageSize = numberOfDataWords(m);
        if(messageSize < 0){ //i.e. unusable message
          stopReceiving();
        }else if(inBuffer.size() >= messageSize){
          byte words [messageSize];
          for(int i = 0; i < messageSize; i++){
            words[i] = inBuffer.dequeue();
          }
          Message receivedMessage (messageSize, words);
          newMessageCallback(receivedMessage, sideName);
        }
      }
    } else if(receivedFirstBit && !sentStop){
      sentStop = true;
      newMessageCallback(stop_message, sideName);
    }
    if(didTimeout && !sentTimeout){
      sentTimeout = true;
      newMessageCallback(timeout_message, sideName);
    }
  }

  void sendMessage(const Message& m){
    if(!sending){
      startSending();
    }
    for(int i = 0; i < m.num_words; i++){
      outBuffer.enqueue(m.words[i]);
    }
  }

  //new data bit trigger
  void trigger(){
    bool isFirstBit = false;
    if(!receivedFirstBit){
      receivedFirstBit = true;
      receiving = true;
      isFirstBit = true;
    }
    if(!didTimeout){
      timeout = 0;
    }
    if(receiving){
      int numBits = 1;
      if(!isFirstBit){
        numBits = (interruptReceivedTime - lastReceivedBit + clock_period/2) / clock_period;
      }
      lastReceivedBit = interruptReceivedTime;
      
      if(numBits <= 0){
        //do nothing.  no need to fail here
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
          stopReceiving();
        } else {
          receivedWakeup = true;
          inBuffer.enqueue(currInWord);
        }
        currInWord = 1;
        
      }else if(currWordBits + numBits > word_size + 2){
        stopReceiving();
        return;
      }else{
        currInWord = (currInWord << numBits) | 1;
      }
    } 
  }
  
  //time to send data bit
  void sendBit(){
    if(receiving && !didTimeout){
      timeout++;
      if(timeout > word_size + 5){
        setTimeout();
      }
    }
    if(sending){
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
    }
  }

  
};


static String sideToString(Side_Name side){
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


static Side topSide (Side_Name::top);
static Side rightSide (Side_Name::right);
static Side bottomSide (Side_Name::bottom);
static Side leftSide (Side_Name::left);

static class Side * getSide(enum Side_Name side){
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



inline void wakeupIfAsleep(){
  if(asleep){
    asleep = false;
    resetClock();
    topSide.reset();
    rightSide.reset();
    bottomSide.reset();
    leftSide.reset();
    //start send timer
    TCNT1 = 0;
    TIMSK1 = (1<<OCIE1A);
  }
}

void topTrigger()
{
  interruptReceivedTime = timeMicros();
  wakeupIfAsleep();
  topSide.trigger();
}

void leftTrigger()
{
  interruptReceivedTime = timeMicros();
  wakeupIfAsleep();
  leftSide.trigger();
}


//bottom Trigger
ISR(PCINT0_vect)
{
  interruptReceivedTime = timeMicros();
  bool falling = !(PINB & (1 << PINB6));
  wakeupIfAsleep();
  if(falling){
    bottomSide.trigger();
  }
}

//right Trigger
ISR(PCINT2_vect)
{ 
  interruptReceivedTime = timeMicros();
  bool falling = !(PIND & (1 << PIND4));
  wakeupIfAsleep();
  if(falling){
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
  attachInterrupt(0, topTrigger, RISING);
  attachInterrupt(1, leftTrigger, RISING);

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
  TCNT1 = 0;
  TIMSK1 = (1<<OCIE1A);
  sei();
}



void putSidesToSleep(){
  //stop send timer
  TIMSK1 = 0;
  delay(1000);
  topSide.reset();
  rightSide.reset();
  bottomSide.reset();
  leftSide.reset();
  asleep = true;
}


void updateSides(){
  topSide.update();
  rightSide.update();
  bottomSide.update();
  leftSide.update();
}


void sendMessage(Side_Name s, const Message& m){
  //Serial.println(String("SM ") + sideToString(s) + String(": ") + m.toString());
  Side *side = getSide(s);
  side->sendMessage(m);
}


