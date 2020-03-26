# get tile type, get left, check valid all go here 

from tilecodes import *
from tilegroups import *

def getTileGroup(tilecode):
    switcher = {
        ONE_T           : NUMBER,
        TWO_T           : NUMBER,
        THREE_T         : NUMBER,
        FOUR_T          : NUMBER,
        FIVE_T          : NUMBER,
        SIX_T           : NUMBER,
        SEVEN_T         : NUMBER,
        EIGHT_T         : NUMBER,
        NINE_T          : NUMBER,
        ZERO_T          : NUMBER,

        IF_T            : CONDITIONAL,
        ELSE_T          : CONDITIONAL,
        WHILE_T         : CONDITIONAL,

        VAR0_T          : VAR,
        VAR1_T          : VAR,
        VAR2_T          : VAR,
        VAR3_T          : VAR,
        VAR4_T          : VAR,

        TRUE_T          : BOOL,
        FALSE_T         : BOOL,

        NEGATIVE_T      : NUMOPS,

        ADDITION_T      : OPERATOR,
        SUBTRACTION_T   : OPERATOR,
        DIVIDE_T        : OPERATOR,
        MULTIPLY_T      : OPERATOR,
        MOD_T           : OPERATOR,

        AND_T           : LOGIC,
        OR_T            : LOGIC,

        EQUAL_T         : COMPARATOR,
        NOTEQUAL_T      : COMPARATOR,
        LESSTHAN_T      : COMPARATOR,
        GREATERTHAN_T   : COMPARATOR,
        LESSTHANEQ_T    : COMPARATOR,
        GREATERTHANEQ_T : COMPARATOR,

        WAIT_T          : COMMAND,
        ROBOTLEFT_T     : COMMAND,
        ROBOTRIGHT_T    : COMMAND,
        ROBOTFORWARD_T  : COMMAND,
        ROBOTREVERSE_T  : COMMAND,
        LEFTMOTOR_T     : COMMAND,
        RIGHTMOTOR_T    : COMMAND,
        PRINT_T         : COMMAND,

        NOP_T           : NOP
    }
    return switcher.get(tilecode, NOP)

def tileToNum(tilecode):
    switcher = {
        ONE_T           : 1,
        TWO_T           : 2,
        THREE_T         : 3,
        FOUR_T          : 4,
        FIVE_T          : 5,
        SIX_T           : 6,
        SEVEN_T         : 7,
        EIGHT_T         : 8,
        NINE_T          : 9,
        ZERO_T          : 0
    }
    return switcher.get(tilecode, -1)