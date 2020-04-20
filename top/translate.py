from itertools import chain

# output format: n x m matrix
# every CodeBlox tile has a positive number associated with tileops
# every other tile is -1 (NOP). 

def get_translation(stream):
    if len(stream) == 0:
        return []
    
    numtiles = stream[0]
    stream = stream[1:]

    tiles = []
    xval = []
    yval = []
    #get every third, this is type of tile
    for i in range(0,len(stream),3):
        xval.append(stream[i])
        yval.append(stream[i+1])
        tiles.append(stream[i+2])

    #find highest x and y, this is size 
    maxx = max(xval)
    maxy = max(yval)

    config = [[-1]*(maxy+1) for _ in range(maxx+1)]

    for i in range(len(tiles)):
        config[xval[i]][yval[i]] = tiles[i]

    return config



stream1 = [2,0,0,37,0,1,1]
stream2 = [4,0,0,37,0,1,1,1,0,38,1,1,1]
stream3 = [6,0,0,13,0,1,19,1,1,37,1,2,1,2,1,38,2,2,1]

print(get_translation(stream3))