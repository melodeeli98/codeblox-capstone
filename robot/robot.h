//
//  Header.h
//  
//
//  Created by Joe Zhao on 1/14/19.
//  Modified by Aarohi Palkar on 2/10/20
//

#ifndef ROBOT_H
#define ROBOT_H

/**********************************************************************/
/*                                                                    */
/*                             Tile Codes                             */
/*                                                                    */
/**********************************************************************/

#define IF_T            1415
#define ELSE_T          1514
#define WHILE_T         1416
#define VAR1_T          12
#define VAR2_T          13
#define VAR3_T          14
#define VAR4_T          15
#define VAR5_T          16
#define TRUE_T          112
#define FALSE_T         113
#define NEGATIVE_T      10
#define DECIMAL_T       11
#define ADDITION_T      1212
#define SUBTRACTION_T   1313
#define DIVIDE_T        1414
#define MULTIPLY_T      1515
#define EQUAL_T         1616
#define AND_T           1717
#define OR_T            1111
#define LESSTHAN_T      1213
#define GREATERTHAN_T   1312
#define LESSTHANEQ_T    1214
#define GREATERTHANEQ_T 1412
#define WAIT_T          1215
#define LIGHTSENSOR_T   1216
#define ROBOTLEFT_T     1314
#define ROBOTRIGHT_T    1413
#define ROBOTFORWARD_T  1516
#define ROBOTREVERSE_T  1615
#define LEFTMOTOR_T     1316
#define RIGHTMOTOR_T    1613
#define NOP_T           114

/**********************************************************************/
/*                                                                    */
/*                            Tile types                              */
/*                                                                    */
/**********************************************************************/

#define CONDITIONAL     0
#define VAR             1
#define COMMAND         2
#define OPERATOR        3
#define BOOL            4
#define NOP             5
#define VALUE           6

// valid
#define TRUE            1
#define FALSE           0
#define ERROR           -1


/**********************************************************************/
/*                                                                    */
/*                          If/else state flags                       */
/*                                                                    */
/**********************************************************************/

#define IF_TAKEN_FLAG 0x1
#define IF_PASSED_FLAG 0x2
#define ERROR_FLAG 0x4


// typedefs
typedef int type_t;
typedef int resistance_t;
typedef int code_t;
typedef int state_t;

/**********************************************************************/
/*                                                                    */
/*                               Tile Funcs                           */
/*                                                                    */
/**********************************************************************/
 
/** @brief returns the value of the right resistor for given row and col
 *  @param row is the row of the tile
 *  @param col is the column of the tile
 *  @return returns the resistance of the right resistor for tile
 */
resistance_t get_right_resistance(int row, int col);

/** @brief returns the value of the left resistor for given row and col
 *  @param row is the row of the tile
 *  @param col is the column of the tile
 *  @return returns the resistance of the left resistor for tile
 */
resistance_t get_left_resistance(int row, int col);

/** @brief returns the code of the tile given its row and column
 *  @param r is the row of the tile
 *  @param c is the column of the tile
 *  @return returns the code of tile
 */
code_t get_tile_code(int r, int c);

/** @brief the type that the tile is, given its code
 *  @param tile is the code for the block
 *  @return type of the tile (conditional, etc)
 */
type_t find_tile_type(code_t code);


/** @brief returns true if block to the left is blank, false otherwise
 *  @param r is the row of the tile
 *  @param c is the column of the tile
 */
bool check_left_block(int r, int c);


/** @brief runs a block of code, starting from r_start and indent
 *  recursively calls itself upon entering an indented block
 *  exits when the current block is complete (there are blocks of lower level indent)
 *
 *  @param rows is the number of rows of the program
 *  @param cols is the number of columns of the program
 *  @param r_start is the starting row of the code block to execute
 *  @param c_start is the indentation level of the code block to execute
 *  @return true if successful execution, false if error
 */
bool run_code(int rows, int cols, int r_start, int c_start);


/** @brief evaluates expressions
 *  @param cols is number of columns of the program
 *  @param r_start is the starting row
 *  @param c_start is the starting col
 *  @param result is the result as a float
 *  @return is true if expression was valid, false otherwise
 */
bool eval_expression(int cols, int r_start, int c_start, float* result);

/** @brief calculates the output of a single two operand one operator expression
 *  @param left_operand is the left operand
 *  @param right_operand is the right operand
 *  @param operator is the operator
 *  @return is the result of the calculation
 */
float calculate(float left_operand, code_t op, float right_operand);

/** @brief returns true if two floats are almost equal
 *  @param left_operand is the first float
 *  @param right_operand is the second float
 *  @return is the result of the comparison
 */
bool almost_equal(float left_operand, float right_operand);

#endif /* ROBOT_H */
