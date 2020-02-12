import time
import math

start_time = time.time()


def micros():
    global start_time
    return math.floor((time.time()-start_time)*1000000)


def delayMicros(t):
    time.sleep(t/1000000)
