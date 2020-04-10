#include <avr/interrupt.h>
#include <avr/io.h>
#include <thread>
#include <ArduinoSTL.h>
#include <functional-vlpp.h>
using namespace std;
using namespace vl;

class Tile {
  thread embedded_thread;
  bool time_to_exit;
  bool ready_to_report;
  bool is_master;
  
  public:
    Tile(String syntax_name, bool is_master=false) {
      thread embedded_thread (run);
    }

    void serialLog(char *s) {
      if (is_master) Serial.println("Master: " + s);
      else Serial.println("Slave " + id + ": " + s);
    }

  void run() {
    
  }
}

void kill();
void waitUntilDone();
void getTiles();
