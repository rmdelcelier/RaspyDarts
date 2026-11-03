#!/usr/bin/python3
import time
import os
# Blinka 10 : no dependency check (see include/cgpio_extender.py)
os.environ.setdefault('BLINKA_SKIP_DEPENDENCY_CHECK', '1')
from digitalio import Direction, Pull
import board
import busio
from adafruit_mcp230xx.mcp23017 import MCP23017

def decode(value):
    """
    Decode string to numeric (B3 => 11)
    """
    try:
        return (ord(value[0]) - 65) * 8 + int(value[1::])
    except: # pylint: disable=bare-except
        return None

i2c = busio.I2C(board.SCL, board.SDA)
mcp = MCP23017(i2c)
pin = mcp.get_pin(decode('B7'))

pin.direction = Direction.INPUT
pin.pull = Pull.UP

try:
    vibration = 1
    print("Start vibrating...waiting...")
    while True:
        value = hex(mcp.gpio)
        #print("value ", value)
        if int(value, 16) & 2**7:
            print("MISSDART ", vibration)
            vibration = vibration + 1
        time.sleep(0.1)

except KeyboardInterrupt:
    print("End vibrating")