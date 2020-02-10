//
//  robot
//
//
//  Created by Joe Zhao on 1/16/19.
//

#include "robot.h"


#include <Pololu3pi.h>
#include <PololuQTRSensors.h>
#include <OrangutanMotors.h>
#include <OrangutanAnalog.h>
#include <OrangutanLEDs.h>
#include <OrangutanLCD.h>
#include <OrangutanPushbuttons.h>
#include <OrangutanBuzzer.h>

Pololu3pi robot;
#include <avr/pgmspace.h>

resistance_t l_resistors[7][5] = {14, 1, 0, 0, 0, 0, 14, 12, 16, 1, 0, 0, 16, 2, 0, 0, 0, 13, 0, 0, 0, 15, 0, 0, 0, 0, 0, 16, 0, 0, 0, 0, 13, 2, 0};
resistance_t r_resistors[7][5] = {16, 12, -1, -1, -1, -1, 15, 16, 16, 12, -1, -1, 13, 0, -1, -1, -1, 16, 0, -1, -1, 14, -1, -1, -1, -1, -1, 13, 0, -1, -1, -1, 16, 0, -1};
float vars[5] = {0, 0, 0, 0, 0};
const char welcome_line1[] PROGMEM = " Pololu";
const char welcome_line2[] PROGMEM = "3\xf7 Robot";
const int turn_time PROGMEM = 380;
const int forward_time PROGMEM = 800;
// This include file allows data to be stored in program space.  The
// ATmega168 has 16k of program space compared to 1k of RAM, so large
// pieces of static data should be stored in program space.

/** @brief pauses execution for the specified time in millis
    @param millis time in milliseconds
*/
void wait(int millis) {
  int ms = millis;
  while (ms > 0) {
    ms -= 10;
    delay(10);
  }
  return;
}

/** @brief read the center light sensor
    @return value of the light sensor
*/
float read_center_light_sensor() {
  unsigned int sensors[5]; // an array to hold sensor values
  read_line(sensors, IR_EMITTERS_ON);
  return ((sensors[2] / 10) > 50) ? 1 : 0;
}

void setup()
{
  unsigned int counter; // used as a simple timer

  // This must be called at the beginning of 3pi code, to set up the
  // sensors.  We use a value of 2000 for the timeout, which
  // corresponds to 2000*0.4 us = 0.8 ms on our 20 MHz processor.
  robot.init(2000);

  // Play welcome music and display a message
  OrangutanLCD::printFromProgramSpace(welcome_line1);
  OrangutanLCD::gotoXY(0, 1);
  OrangutanLCD::printFromProgramSpace(welcome_line2);
  delay(9000);

  // Display battery voltage and wait for button press
  while (!OrangutanPushbuttons::isPressed(BUTTON_B))
  {
    int bat = OrangutanAnalog::readBatteryMillivolts();

    OrangutanLCD::clear();
    OrangutanLCD::print(bat);
    OrangutanLCD::print("mV");
    OrangutanLCD::gotoXY(0, 1);
    OrangutanLCD::print("Press B");

    delay(100);
  }

  // Always wait for the button to be released so that 3pi doesn't
  // start moving until your hand is away from it.
  OrangutanPushbuttons::waitForRelease(BUTTON_B);
  delay(1000);

  // Auto-calibration: turn right and left while calibrating the
  // sensors.
  for (counter = 0; counter < 80; counter++)
  {
    if (counter < 20 || counter >= 60)
      OrangutanMotors::setSpeeds(40, -40);
    else
      OrangutanMotors::setSpeeds(-40, 40);

    // This function records a set of sensor readings and keeps
    // track of the minimum and maximum values encountered.  The
    // IR_EMITTERS_ON argument means that the IR LEDs will be
    // turned on during the reading, which is usually what you
    // want.
    robot.calibrateLineSensors(IR_EMITTERS_ON);

    // Since our counter runs to 80, the total delay will be
    // 80*20 = 1600 ms.
    delay(20);
  }
  OrangutanMotors::setSpeeds(0, 0);

  // Display calibrated values as a bar graph.
  while (!OrangutanPushbuttons::isPressed(BUTTON_B));
  OrangutanPushbuttons::waitForRelease(BUTTON_B);

  OrangutanLCD::clear();

  OrangutanLCD::print("Go!");

  // Play music and wait for it to finish before we start driving.
}




/** @brief returns the value of the right resistor for given row and col
    @param row is the row of the tile
    @param col is the column of the tile
    @return returns the resistance of the right resistor for tile
*/
resistance_t get_right_resistance(int row, int col) {
  return r_resistors[row][col];
}

/** @brief returns the value of the left resistor for given row and col
    @param row is the row of the tile
    @param col is the column of the tile
    @return returns the resistance of the left resistor for tile
*/
resistance_t get_left_resistance(int row, int col) {
  return l_resistors[row][col];
}

/** @brief returns the code of the tile given its row and column
    @param r is the row of the tile
    @param c is the column of the tile
    @return the code for the tile
*/
code_t get_tile_code(int r, int c) {
  return (code_t)(get_left_resistance(r, c) * 100 + get_right_resistance(r, c));
}

/** @brief the type that the tile is, given its code
    @param tile is the code for the block
    @return type of the tile (conditional, etc)
*/
type_t find_tile_type(code_t code) {
  switch (code) {
    case IF_T:
    case ELSE_T:
    case WHILE_T:
      return CONDITIONAL;
    case AND_T:
    case OR_T:
    case ADDITION_T:
    case SUBTRACTION_T:
    case DIVIDE_T:
    case MULTIPLY_T:
    case EQUAL_T:
    case LESSTHAN_T:
    case GREATERTHAN_T:
    case LESSTHANEQ_T:
    case GREATERTHANEQ_T:
      return OPERATOR;
    case VAR1_T:
    case VAR2_T:
    case VAR3_T:
    case VAR4_T:
    case VAR5_T:
      return VAR;
    case TRUE_T:
    case FALSE_T:
    case LIGHTSENSOR_T:
      return BOOL;
    case WAIT_T:
    case ROBOTLEFT_T:
    case ROBOTRIGHT_T:
    case ROBOTFORWARD_T:
    case ROBOTREVERSE_T:
    case LEFTMOTOR_T:
    case RIGHTMOTOR_T:
      return COMMAND;
    case NOP_T:
      return NOP;
    default:
      return VALUE;
  }
  return VALUE;
}

/** @brief returns true if block to the left is blank, false otherwise
    @param r is the row of the tile
    @param c is the column of the tile
*/
bool check_left_block(int r, int c) {
  if ((c - 1) >= 0) {
    if (find_tile_type(get_tile_code(r, c - 1)) != NOP) {
      return true;
    }
    else return false;
  }
  else return false;
}

/** @brief adds if taken flag to state and returns new state
    @param state is the current state
    @return is new state with updated taken flag
*/
state_t add_if_taken(state_t state) {
  return state | IF_TAKEN_FLAG;
}

/** @brief removes if taken flag to state and returns new state
    @param state is the current state
    @return is new state with updated taken flag
*/
state_t remove_if_taken(state_t state) {
  return state & (~IF_TAKEN_FLAG);
}

/** @brief adds if passed flag to state and returns new state
    @param state is the current state
    @return is new state with updated if passed flag
*/
state_t add_if_passed(state_t state) {
  return state | IF_PASSED_FLAG;
}

/** @brief removes if passed flag to state and returns new state
    @param state is the current state
    @return is new state with updated if passed flag
*/
state_t remove_if_passed(state_t state) {
  return state & (~IF_PASSED_FLAG);
}

/** @brief adds error flag to state and returns new state
    @param state is the current state
    @return is new state with updated error flag
*/
state_t add_condition_error(state_t state) {
  return state | ERROR_FLAG;
}
/** @brief returns true if state has if taken flag
    @param state is the current state
    @return true if taken and false if not
*/
bool get_if_taken(state_t state) {
  return state & IF_TAKEN_FLAG;
}

/** @brief returns true if state has if passed flag
    @param state is the current state
    @return true if passed and false if not
*/
bool get_if_passed(state_t state) {
  return state & IF_PASSED_FLAG;
}

/** @brief returns true if state has error flag
    @param state is the current state
    @return true if error and false if not
*/
bool get_error(state_t state) {
  return state & ERROR_FLAG;
}

/** @brief check condition for conditional
    @param cols is number of columns for the program
    @param r_start is the starting row for the condition
    @param c_start is the starting column for the condition
    @return TRUE for true, FALSE for false, ERROR for invalid
*/
int check_condition(int cols, int r_start, int c_start) {
  float result = 0;
  bool validity = eval_expression(cols, r_start, c_start, &result);
  result = almost_equal(result, 0.0) ? FALSE : TRUE;
  return validity ? result : -1;
}

/** @brief handles if block of code

    @param rows is the number of rows of the program
    @param cols is the number of columns of the program
    @param r_start is the starting row of the code block to execute
    @param c_start is the indentation level of the code block to execute
    @param state is the state of the current block

    @return new state of the code block
*/
state_t handle_if(int rows, int cols, int r_start, int c_start, state_t state) {
  int validity = check_condition(cols, r_start, c_start);
  if (validity == TRUE) {
    state = add_if_taken(state);
    run_code(rows, cols, r_start + 1, c_start);
  }
  else if (validity == FALSE) {
    state = add_if_passed(state);
  }
  else { // illegal condition
    state = add_condition_error(state);
  }
  return state;
}

/** @brief handles else block of code

    @param rows is the number of rows of the program
    @param cols is the number of columns of the program
    @param r_start is the starting row of the code block to execute
    @param c_start is the indentation level of the code block to execute
    @param state is the state of the current block

    @return new state of the code block
*/
state_t handle_else(int rows, int cols, int r_start, int c_start, state_t state) {
  if (get_if_passed(state)) { // if was not taken
    state = remove_if_passed(state);
    run_code(rows, cols, r_start + 1, c_start);
  }
  else if (get_if_taken(state)); // if was taken
  else { // no if existed
    state = add_condition_error(state);
  }
  return state;
}

/** @brief handles while block of code

    @param rows is the number of rows of the program
    @param cols is the number of columns of the program
    @param r_start is the starting row of the code block to execute
    @param c_start is the indentation level of the code block to execute
    @param state is the state of the current block

    @return new state of the code block
*/
state_t handle_while(int rows, int cols, int r_start, int c_start, state_t state) {
  int validity = check_condition(cols, r_start, c_start);
  if (validity == -1) {
    state = add_condition_error(state);
  }
  while (validity == 1) {
    run_code(rows, cols, r_start + 1, c_start);
    validity = check_condition(cols, r_start, c_start);
  }
  return state;
}

/** @brief handles conditional blocks of code

    @param rows is the number of rows of the program
    @param cols is the number of columns of the program
    @param r_start is the starting row of the code block to execute
    @param c_start is the indentation level of the code block to execute
    @param state is the state of the current block

    @return new state of the code block
*/
state_t handle_conditional(int rows, int cols, int r_start, int c_start, state_t state)
{
  code_t tile = get_tile_code(r_start, c_start - 1);

  switch (tile) {
    case IF_T: {
        state = handle_if(rows, cols, r_start, c_start, state);
        break;
      }
    case ELSE_T: {
        state = handle_else(rows, cols, r_start, c_start, state);
        break;
      }
    case WHILE_T: {
        state = handle_while(rows, cols, r_start, c_start, state);
      }
  }
  return state;
}

/** @brief determines of the beginnning of the statement is valid
    @param tile_type is the type of the tile
    @return true if valid, false if not
*/
bool valid_statement_start(type_t tile_type) {
  if ((tile_type != COMMAND) && (tile_type != VAR)) {
    return false;
  }
  return true;
}

/** @brief parses a number beginning with the current tile
    @param cols is number of columns
    @param r_start is starting row of number
    @param c_start is starting col of number
    @param num_val is float pointer for parsed number to be placed
    @param tiles_seen is int pointer to indicate number of tiles used by number
*/
bool parse_number(int cols, int r_start, int c_start, float* num_val, int* tiles_seen) {
  int num_decimals = 0;
  int negative = 0;
  int dec_pos = -1;
  int num_pos = 0;
  float built_num = 0;

  *tiles_seen = 0;

  while (c_start < cols) {
    resistance_t r_res = get_right_resistance(r_start, c_start);
    resistance_t l_res = get_left_resistance(r_start, c_start);
    code_t curr_code = get_tile_code(r_start, c_start);
    type_t curr_tile = find_tile_type(curr_code);

    if (curr_tile != VALUE) {
      break;
    }
    else {
      if (((l_res == NEGATIVE_T) && (num_pos != 0)) || (r_res == NEGATIVE_T)) {
        //negative sign not at beginning
        return false;
      }
      if ((((l_res == DECIMAL_T) || (r_res == DECIMAL_T)) && (num_decimals != 0)) ||
          ((l_res == DECIMAL_T) && (r_res == DECIMAL_T))) {
        //already contains decimal or too many decimals
        return false;
      }

      if (l_res == NEGATIVE_T) {
        negative = 1;
      }
      else if (l_res == DECIMAL_T) {
        dec_pos = num_pos;
        num_decimals = 1;
      }
      else if (l_res < 10) { //number values
        built_num = (built_num * 10) + l_res;
      }

      num_pos += 1;

      if (r_res == DECIMAL_T) {
        dec_pos = num_pos;
        num_decimals = 1;
      }
      else if (r_res < 10) {
        built_num = (built_num * 10) + r_res;
      }

      num_pos += 1;
      c_start++;
    }
    *tiles_seen++;
  }
  if (negative == 1) {
    built_num *= -1;
  }
  dec_pos = (dec_pos == -1) ? (num_pos - 1) : dec_pos; // if no decimal is seen, decimal is last
  int neg_exp = (num_pos - dec_pos - 1);
  for (int i = 0; i < neg_exp; i++) {
    built_num = built_num / 10;
  }
  *num_val = built_num;
  return true;
}

/** @brief handles command statements, returning false if syntax error
    @param tile is the code for the tile
    @param cols is the number of columns of the program
    @param r_start is the starting row for the command
    @param c_start is the starting column for the command
*/
bool handle_command_statement(int cols, int r_start, int c_start, code_t tile) {
  float num_val = 1;
  int tiles_seen = 0;
  static int left_speed = 0;
  static int right_speed = 0;
  code_t next_code = NOP_T;
  if (c_start < cols - 1) {
    next_code = get_tile_code(r_start, c_start + 1);
  }

  type_t next_tile = find_tile_type(next_code);

  if (next_tile == VALUE) {
    if (!parse_number(cols, r_start, c_start + 1, &num_val, &tiles_seen)) return false;
  }
  else if (next_tile != NOP) {
    return false;
  }
  switch (tile) {
    case WAIT_T:
      {
        if (num_val < 0) return false;
        else {
          wait(int(num_val * 1000));
          return true;
        }
      }
    case ROBOTLEFT_T: //values after left, right, forward, reverse are optional (1 unit of movement)
      {
        if (num_val < 0) return false;
        else {
          OrangutanMotors::setSpeeds(-40, 40);
          wait(int(num_val * turn_time));
          OrangutanMotors::setSpeeds(0, 0);
          return true;
        }
      }
    case ROBOTRIGHT_T:
      {
        if (num_val < 0) return false;
        else {
          OrangutanMotors::setSpeeds(40, -40);
          wait(int(num_val * turn_time));
          OrangutanMotors::setSpeeds(0, 0);
          return true;
        }
      }
    case ROBOTFORWARD_T:
      {
        if (num_val < 0) return false;
        else {
          OrangutanMotors::setSpeeds(50, 50);
          wait(int(num_val * forward_time));
          OrangutanMotors::setSpeeds(0, 0);
          return true;
        }
      }
    case ROBOTREVERSE_T:
      {
        if (num_val < 0) return false;
        else {
          OrangutanMotors::setSpeeds(-50, -50);
          wait(int(num_val * forward_time));
          OrangutanMotors::setSpeeds(0, 0);
          return true;
        }
      }
    case LEFTMOTOR_T:
      {
        if (next_tile != VALUE) return false;
        left_speed = int(num_val);
        OrangutanMotors::setSpeeds(left_speed, right_speed);
        return true;
      }
    case RIGHTMOTOR_T:
      {
        if (next_tile != VALUE) return false;
        right_speed = int(num_val);
        //OrangutanLCD::print(right_speed);
        OrangutanMotors::setSpeeds(left_speed, right_speed);
        return true;
      }
  }

  if (next_tile != NOP) {
    return false;
  }
  return true;
}

/** @brief returns true if two floats are almost equal
    @param left_operand is the first float
    @param right_operand is the second float
    @return is the result of the comparison
*/
bool almost_equal(float left_operand, float right_operand) {
  return fabs(left_operand - right_operand) < 0.01;
}

/** @brief calculates the output of a single two operand one operator expression
    @param left_operand is the left operand
    @param right_operand is the right operand
    @param operator is the operator
    @return is the result of the calculation
*/
float calculate(float left_operand, code_t op, float right_operand) {
  switch (op) {
    case ADDITION_T: return left_operand + right_operand;
    case SUBTRACTION_T: return left_operand - right_operand;
    case MULTIPLY_T: return left_operand * right_operand;
    case DIVIDE_T: return (right_operand == 0) ? 0 : left_operand / right_operand;
    case AND_T: return (float)((right_operand != 0) && (left_operand != 0));
    case OR_T: return (float)((right_operand != 0) || (left_operand != 0));
    case EQUAL_T: return (float)almost_equal(left_operand, right_operand);
    case LESSTHAN_T: return (float)(left_operand < right_operand);
    case GREATERTHAN_T: return (float)(left_operand > right_operand);
    case LESSTHANEQ_T: return (float)(left_operand <= right_operand);
    case GREATERTHANEQ_T: return (float)(left_operand >= right_operand);
    default: return 0;
  }
}

/** @brief evaluates expressions
    @param cols is number of columns of the program
    @param r_start is the starting row
    @param c_start is the starting col
    @param result is the result as a float
    @return is true if expression was valid, false otherwise
*/
bool eval_expression(int cols, int r_start, int c_start, float* result) {
  bool open_operator = true;
  int offset = 0;
  code_t curr_operator = 0;
  float num = 0;
  int len = 0;
  *result = 0;

  while ((c_start + offset) < cols) {
    code_t curr_code = get_tile_code(r_start, c_start + offset);
    type_t curr_type = find_tile_type(curr_code);
    if ((curr_type == VALUE) && open_operator) {
      if (!parse_number(cols, r_start, c_start + offset, &num, &len)) return false;
      if (offset == 0) {
        *result = num;
      }
      else {
        *result = calculate(*result, curr_operator, num);
      }
      open_operator = false;
    }
    else if ((curr_type == BOOL) && open_operator) {
      switch (curr_code) {
        case TRUE_T: {
            num = 1;
            break;
          }
        case FALSE_T: {
            num = 0;
            break;
          }
        case LIGHTSENSOR_T: {
            num = read_center_light_sensor();
            break;
          }
        default: num = 0;
      }
      if (offset == 0) {
        *result = num;
      }
      else {
        *result = calculate(*result, curr_operator, num);
      }
      open_operator = false;
    }
    else if ((curr_type == OPERATOR) && !open_operator) {
      curr_operator = curr_code;
      open_operator = true;
    }
    else if (curr_type == NOP) break;
    else return false;
    offset++;
  }
  if (open_operator) return false;
  else return true;
}


/** @brief handles assign statments
    @param cols is the number of columns of the program
    @param r_start is the starting row
    @param c_start is the starting col
    @param tile is the code for the tile starting the assign
    @return true if valid, false if not
*/
bool handle_assign_statement(int cols, int r_start, int c_start, code_t tile) {
  code_t curr_code = get_tile_code(r_start, c_start);
  type_t curr_tile = find_tile_type(curr_code);
  int var_index = (curr_code % 10) - 2;
  float rhs = 0;
  bool open_operator = false;

  if (c_start + 1 < cols) {
    curr_code = get_tile_code(r_start, c_start + 1);
    curr_tile = find_tile_type(curr_code);
    if (curr_code != EQUAL_T) return false;
  }
  else {
    return false;
  }

  float result = 0;
  if (!eval_expression(cols, r_start, c_start + 2, &result)) return false;
  vars[var_index] = result;
  return true;
}


/** @brief register error sends via bluetooth to the tile master the row
    that contains an error
*/


/** @brief runs a block of code, starting from r_start and indent
    recursively calls itself upon entering an indented block
    exits when the current block is complete (there are blocks of lower level indent)

    @param rows is the number of rows of the program
    @param cols is the number of columns of the program
    @param r_start is the starting row of the code block to execute
    @param c_start is the indentation level of the code block to execute
    @return true if successful execution, false if error
*/
bool run_code(int rows, int cols, int r_start, int c_start)
{
  code_t tile = 0;
  resistance_t tile_left = 0;
  resistance_t tile_right = 0;
  type_t type = 0;
  // contains state info
  state_t state = 0;

  for (int r = r_start; r < rows; r++) {
    // check if current line is lower level of indent
    if (check_left_block(r, c_start)) return true;

    tile = get_tile_code(r, c_start);
    type = find_tile_type(tile);

    // block is condition
    if (type == CONDITIONAL) {
      state = handle_conditional(rows, cols, r, c_start + 1, state);
      if (get_error(state)) {
        //register_error(r, c_start);
        return false;
      }
    }
    else if (type == NOP);
    else if (type == COMMAND) {
      handle_command_statement(cols, r, c_start, tile);
    }
    else if (type == VAR) {
      handle_assign_statement(cols, r, c_start, tile);
    }
  }

  return true;
}


void loop() {
  run_code(7, 5, 0, 0);
  delay(5000);
}
