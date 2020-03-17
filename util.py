"""
def binaryStringToInt(s):
    num = 0
    for i in range(len(s[1:])):
        num = num + int(s[i + 1])
        num = num * 2
    num = int(num / 2)
    return -num if s[0] == "1" else num
"""

def binaryListToUnsignedInt(l):
    num = 0
    for i in range(len(l)):
        num = num + int(l[i + 1])
        num = num * 2
    num = int(num / 2)
    return num

def binaryListToSignedInt(l):
    num = 0
    for i in range(len(l[1:])):
        num = num + int(l[i + 1])
        num = num * 2
    num = int(num / 2)
    return -num if l[0] == 1 else num

def intToSignedBinaryList(num):
    s = "{0:05b}".format(abs(num))
    if (num < 0):
        s = "1" + s
    else:
        s = "0" + s
    return [int(char) for char in s]

def intToUnsignedBinaryList(num):
    s = "{0:06b}".format(num)
    return [int(char) for char in s]