from gui import draw
from interpreter import interpret

# TODO: call translate from here, translate will be the one deserializing the input from
# the master tile. 
# further instructions in translate.py

# # x = -10 + 1; print x; print x + 25; print x/0
#blocks = [[14,26,21,1,10,22,1],[41,14,-1,-1,-1,-1,-1], [41,14,22,2,5,-1,-1], [41,14,24,10,-1,-1,-1]] 

# incomplete statement, throws a syntax error
#blocks = [[14,26,1,10,22],[41,14,-1,-1,-1]] # x = 10 + 

# tries to do 10+True, throws a type error
#blocks = [[14,26,1,10,22,19],[41,14,-1,-1,-1,-1]] # x = 10 + True 

# prints even numbers from 1 to 10. x = 1; while(x < 10){if x % 2 == 0 then print x; x++}
#blocks = [[14,26,1,-1,-1,-1,-1],[13,14,30,9,-1,-1,-1],[-1,11,14,42,2,26,10],[-1,-1,41,14,-1,-1,-1],[-1,14,26,14,22,1,-1]]

blocks = [[14,26,5,22,3,25,6],[41,14,-1,-1,-1,-1,-1]]
#blocks = [[]]

(filename, isErr, errLoc) = interpret(blocks)
draw(blocks, filename, isErr, errLoc)