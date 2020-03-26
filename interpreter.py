# interpreter logic goes here 

from tilecodes import *
from tilegroups import *
from tileops import *
from errors import *
from conditionalops import *
from customtypes import *
import traceback

blocks = [[]]
rows = 0
cols = 0
curstate = STATE_NONE

vars = [0,0,0,0,0]


def getTileCode(r, c):
    if r < 0 or r >= rows:
        return NOP_T 
    if c < 0 or c >= cols:
        return NOP_T 

    return blocks[r][c]

def parseBool(tile):
    if tile == TRUE_T:
        return True 
    elif tile == FALSE_T:
        return False

def parseNumber(r,start,end):
    neg = False
    hasANumber = False
    val = 0

    for i in range(start,end+1):
        curtile = getTileCode(r,i)
        if curtile == NOP_T:
            break
        if curtile == NEGATIVE_T:
            neg = True 
        else:
            num = tileToNum(curtile)
            val = val*10 + num 
            hasANumber = True

    if neg:
        if hasANumber:
            val = val * -1
        else:
            raise InterpreterError(ERROR_SYNTAX, (r,start))
    
    return val 
    

def calculateOperator(func, e1, e2, loc):
    global isError, errorCode
    if func == ADDITION_T:
        return e1 + e2 
    elif func == SUBTRACTION_T:
        return e1 - e2
    elif func == DIVIDE_T:
        if e2 == 0:
            raise InterpreterError(ERROR_DIVZERO, loc)
        return e1/e2
    elif func == MULTIPLY_T:
        return e1*e2
    elif func == MOD_T:
        if e2 == 0:
            raise InterpreterError(ERROR_DIVZERO, loc)
        return e1 % e2

def calculateComp(func,e1,e2):
    if func == EQUAL_T:
        return e1 == e2 
    elif func == NOTEQUAL_T:
        return e1 != e2 
    elif func == LESSTHAN_T:
        return e1 < e2
    elif func == GREATERTHAN_T:
        return e1 > e2 
    elif func == LESSTHANEQ_T:
        return e1 <= e2 
    elif func == GREATERTHANEQ_T:
        return e1 >= e2 

def calculateLogic(func, e1, e2):
    if func == AND_T:
        return e1 and e2 
    elif func == OR_T:
        return e1 or e2 

#return a tuple (value, type)
def eval(r, start, end):
    global isError, errorCode
    #find where the function or operation is 
    functionpos = -1
    for i in range(end,start-1,-1):
        tilegroup = getTileGroup(getTileCode(r,i))
        if tilegroup == OPERATOR or tilegroup == COMPARATOR or tilegroup == LOGIC:
            functionpos = i
            break
    
    if functionpos == -1: #base case
        #check first tile and see if it's a bool or number and accordingly 
        me = getTileCode(r,start)
        mytype = getTileGroup(me)
        if mytype == BOOL:
            return (parseBool(me), TYPE_BOOL)
        elif mytype == NUMBER or mytype == NUMOPS:
            return (parseNumber(r,start,end), TYPE_NUM)
        elif mytype == VAR:
            index = getVarIndex(me)
            return vars[index]
        elif mytype == NOP:
            raise InterpreterError(ERROR_SYNTAX, (r,start))

    else:
        (e1,e1type) = eval(r,start,functionpos-1)
        (e2,e2type) = eval(r,functionpos+1,end)
        func = getTileCode(r,functionpos)
        if tilegroup == OPERATOR:
            if e1type != TYPE_NUM or e2type != TYPE_NUM:
                raise InterpreterError(ERROR_TYPE, (r,functionpos))
            return (calculateOperator(func,e1,e2, functionpos), TYPE_NUM)
        
        elif tilegroup == COMPARATOR:
            if e1type != TYPE_NUM or e2type != TYPE_NUM:
                raise InterpreterError(ERROR_TYPE, (r,functionpos))
            return (calculateComp(func,e1,e2), TYPE_BOOL)
        
        elif tilegroup == LOGIC:
            if e1type != TYPE_BOOL or e2type != TYPE_BOOL:
                raise InterpreterError(ERROR_TYPE, (r,functionpos))
            return (calculateLogic(func,e1,e2), TYPE_BOOL)

def evalExpression(r, c):
    #calculate the end of the expression
    cend = c 
    while getTileCode(r,cend+1) != NOP_T:
        cend += 1
    #make sure there is at least one thing to evaluate
    return eval(r,c,cend) #inclusive

def findExitCondition(r,indent):
    for i in range(r,rows):
        if getTileCode(i,indent-1) != NOP_T:
            return i 
    return rows

def handleIf(r, c):
    global curstate
    global isError, errorCode
    exitPos = findExitCondition(r+1,c)
    (isValid,typ) = evalExpression(r,c)
    if typ != TYPE_BOOL:
        print(isValid, typ)
        raise InterpreterError(ERROR_TYPE, (r,c))
    
    if isValid:
        curstate = STATE_IFTAKEN
        runCode(r+1, c)
    else:
        curstate = STATE_IFNOTTAKEN
    
    return exitPos

def handleElse(r, c):
    exitPos = findExitCondition(r+1,c)
    global curstate
    if curstate == STATE_IFNOTTAKEN:
        curstate = STATE_NONE
        runCode(r+1, c)
        return exitPos
    
    elif curstate == STATE_NONE:
        #going to be error here TODO
        raise InterpreterError(ERROR_SYNTAX, r,c-1)

def handleWhile(r, c):
    #find where the while loop ends
    exitPos = findExitCondition(r+1,c)
    (isValid,typ) = evalExpression(r,c)
    if typ != TYPE_BOOL:
        raise InterpreterError(ERROR_TYPE, (r,c))

    while isValid:
        runCode(r+1,c)
        (isValid,typ) = evalExpression(r,c)
        if typ != TYPE_BOOL:
            raise InterpreterError(ERROR_TYPE, (r,c))
    return exitPos

def handleConditional(tile, r, c):
    if tile == IF_T:
        return handleIf(r, c+1)
    elif tile == ELSE_T:
        return handleElse(r, c+1)
    elif tile == WHILE_T:
        return handleWhile(r, c+1)


def handleCommand(tile, r, c):
    if tile == PRINT_T:
        (val,typ) = evalExpression(r,c+1)
        print(val)


def getVarIndex(tile):
    if tile == VAR0_T:
        return 0
    elif tile == VAR1_T:
        return 1
    elif tile == VAR2_T:
        return 2
    elif tile == VAR3_T:
        return 3
    elif tile == VAR4_T:
        return 4
    #never should happen
    return -1

def handleAssign(tile, r, c):
    #print("in assign", r, c)
    index = getVarIndex(tile)
    #next tile should be equals
    nextTile = getTileCode(r,c+1)
    if nextTile == EQUAL_T:
        (val,typ) = evalExpression(r,c+2)
        vars[index] = (val,typ)
    


# runs a block of code from (r,c) position
def runCode(r, indent):
    #print(r, indent)
    tile = getTileCode(r, indent)
    
    #if tile is nop, then error: too much indentation
    if tile == NOP_T:
        raise InterpreterError(ERROR_INDENT, (r,indent))

    curr = r
    while curr < rows:
        tile = getTileCode(curr, indent)
        group = getTileGroup(tile)

        #if the block left of that is not nop, then indentation back
        # want to return new position
        if getTileCode(curr, indent-1) != NOP_T:
            return 
        
        else:
                if group == CONDITIONAL:
                    #conditional stuff
                    global curstate
                    if tile != ELSE_T:
                        curstate = STATE_NONE
                    pos = handleConditional(tile, curr, indent)
                    curr = pos
                
                elif group == COMMAND:
                    #command stuff
                    handleCommand(tile, curr, indent)
                    curr += 1

                elif group == VAR:
                    #variable stuff
                    handleAssign(tile, curr, indent)
                    curr += 1


#blocks = [[14,26,21,1,10,22,1],[41,14,-1,-1,-1,-1,-1]] # x = -10 + 1; print x
#blocks = [[14,26,1,-1,-1,-1],[13,14,30,9,-1,-1],[-1,41,14,-1,-1,-1],[-1,14,26,14,22,1]]
#blocks = [[14,26,2,-1],[11,14,26,1],[-1,41,5,-1],[12,-1,-1,-1],[-1,41,6,-1]]
#blocks = [[14,26,1,-1,-1,-1],[13,14,30,9,-1,-1],[-1,15,26,14,42,2],[-1,11,15,26,1,-1],[-1,-1,41,14,-1,-1],[-1,14,26,14,22,1]]
#blocks = [[14,26,1,10,22],[41,14,-1,-1,-1]] # x = 10 + True; error
blocks = [[14,26,1,-1,-1,-1,-1],[13,14,30,9,-1,-1,-1],[-1,11,14,42,2,26,10],[-1,-1,41,14,-1,-1,-1],[-1,14,26,14,22,1,-1]]
rows = len(blocks)
cols = len(blocks[0])
#runCode(0,0)
try:
    runCode(0,0)
except InterpreterError as e:
    if e.code == ERROR_TYPE:
        print("Type error at block "),
    elif e.code == ERROR_DIVZERO:
        print("Divide by zero error at block "),
    elif e.code == ERROR_SYNTAX:
        print("Syntax error at block "),
    elif e.code == ERROR_INDENT:
        print("Indentation error at block "),
    print(e.loc)
    #print(traceback.format_exc())
else:
    print("All good!")