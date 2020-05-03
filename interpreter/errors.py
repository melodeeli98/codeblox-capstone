# error codes go here 
ERROR_NONE = 0
ERROR_TYPE = 1
ERROR_DIVZERO = 2
ERROR_SYNTAX = 3
ERROR_INDENT = 4
ERROR_OVERFLOW = 5
ERROR_UNDEFINED = 6
ERROR_INDENTCOND = 7

class InterpreterError(Exception):
    def __init__(self, code, loc):
        self.code = code
        self.loc = loc 