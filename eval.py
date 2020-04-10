
# mappings of tile strings to python representations
variables = {"var1": 4, "var2": 49}
numbers = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4,
           "5": 5, "6": 6, "7": 7, "8": 8, "9": 9}
booleans = {"True": True, "False": False}
b_operations = {"+": {"level": 2, "fn": lambda x, y: x+y},
                "-": {"level": 2, "fn": lambda x, y: x-y},
                "*": {"level": 3, "fn": lambda x, y: x*y},
                "/": {"level": 3, "fn": lambda x, y: x/y},
                "<": {"level": 1, "fn": lambda x, y: x < y},
                "<=": {"level": 1, "fn": lambda x, y: x <= y},
                "=": {"level": 1, "fn": lambda x, y: x == y},
                "!=": {"level": 1, "fn": lambda x, y: x != y},
                ">": {"level": 1, "fn": lambda x, y: x > y},
                ">=": {"level": 1, "fn": lambda x, y: x >= y},
                "and": {"level": 3, "fn": lambda x, y: x and y},
                "or": {"level": 2, "fn": lambda x, y: x or y}}
max_level = 3
u_operations = {"not": lambda x: not x}


# helper method for eval to get the second arg in a binary operation
def getNextArg(tiles):
    if len(tiles) == 1:
        return (tiles[0]["value"], [])

    elif tiles[0]["type"] == "parenthesis":
        parenths = -1
        for r in range(1, len(tiles)):
            if tiles[r]["value"] == "(":
                parenths -= 1
            elif tiles[r]["value"] == ")":
                parenths += 1
            if parenths == 0:
                tiles[0] = eval(tiles[1: r])
                return (tiles[0]["value"], tiles[r+1:])
        raise Exception("non-balanced parenthesis")

    elif tiles[0]["type"] == "u_operation":
        f = tiles[0]["value"]
        (arg1, remainingTiles) = getNextArg(tiles[1:])
        return (f(arg1), remainingTiles)

    elif tiles[0]["type"] == "value":
        return (tiles[0]["value"], tiles[1:])

    raise Exception("invalid expression")


# evaluates a list of the python representation of each tile
def eval(tiles):
    if len(tiles) == 1:
        return tiles[0]

    elif tiles[0]["type"] == "parenthesis":
        parenths = -1
        for r in range(1, len(tiles)):
            if tiles[r]["value"] == "(":
                parenths -= 1
            elif tiles[r]["value"] == ")":
                parenths += 1
            if parenths == 0:
                tiles[0] = eval(tiles[1: r])
                return eval([tiles[0]] + tiles[r+1:])
        raise Exception("non-balanced parenthesis")

    elif tiles[0]["type"] == "u_operation":
        f = tiles[0]["value"]
        (arg1, remainingTiles) = getNextArg(tiles[1:])
        return eval([{"type": "value", "value": f(arg1)}]+remainingTiles)

    elif tiles[0]["type"] == "value":
        eval_list = [tiles[0]["value"]]
        assert tiles[1]["type"] == "b_operation"
        eval_list.append(tiles[1]["value"])
        (arg, remainingTiles) = getNextArg(tiles[2:])
        eval_list.append(arg)
        while len(remainingTiles) > 0:
            assert remainingTiles[0]["type"] == "b_operation"
            eval_list.append(remainingTiles[0]["value"])
            (arg, remainingTiles) = getNextArg(remainingTiles[1:])
            eval_list.append(arg)
        level = max_level
        while len(eval_list) > 1:
            e = 1
            while e < len(eval_list):
                if eval_list[e]["level"] == level:
                    eval_list[e -
                              1] = eval_list[e]["fn"](eval_list[e-1], eval_list[e+1])
                    eval_list = eval_list[:e] + eval_list[e+2:]
                else:
                    e += 2
            level -= 1
        return {"type": "value", "value": eval_list[0]}


# Combines number strings together to form one python number
def convertNumbers(tiles, t):
    number = 0
    start = t
    while t < len(tiles) and tiles[t] in numbers.keys():
        number = number*10 + numbers[tiles[t]]
        t += 1
    tiles[start] = {"type": "value", "value": number}
    tiles = tiles[:start+1] + tiles[t:]
    return tiles


# replace all tile strings with a python representation
def plugInPrimitives(tiles):
    t = 0
    while t < len(tiles):
        if tiles[t] in numbers.keys():
            tiles = convertNumbers(tiles, t)
        elif tiles[t] in variables.keys():
            tiles[t] = {"type": "value", "value": variables[tiles[t]]}
        elif tiles[t] in booleans.keys():
            tiles[t] = {"type": "value", "value": booleans[tiles[t]]}
        elif tiles[t] in b_operations.keys():
            tiles[t] = {"type": "b_operation", "value": b_operations[tiles[t]]}
        elif tiles[t] in u_operations.keys():
            tiles[t] = {"type": "u_operation", "value": u_operations[tiles[t]]}
        elif tiles[t] == "(" or tiles[t] == ")":
            tiles[t] = {"type": "parenthesis", "value": tiles[t]}
        t += 1
    return tiles


# Start here!  Takes in a list of tile strings like ["5", "+", "4", "2"]
def evalTiles(tiles):
    tiles = plugInPrimitives(tiles)
    return eval(tiles)["value"]


tiles = "1 + 2 * 3 = 7".split()
print(evalTiles(tiles))
"""
tiles = "not ( ( var1 + 1 2 ) * 3 < var2 )".split()
print(evalTiles(tiles))
tiles = "( var1 + 1 2 ) * 3".split()
print(evalTiles(tiles))
"""
