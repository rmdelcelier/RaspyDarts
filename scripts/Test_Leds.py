#!/usr/bin/env python3
import time
import os
# Blinka 10 : no dependency check (see include/cgpio_extender.py)
os.environ.setdefault('BLINKA_SKIP_DEPENDENCY_CHECK', '1')
import board
import neopixel
import sys

# sys.argv[0] est le nom du script... Chapeau Python...
GPIO = int(sys.argv[1])
NBLEDS = int(sys.argv[2])

if len(sys.argv)>2 :
    Time=int(sys.argv[3])
else :
    Time=1000

GO=True

if GPIO == 21 :
    PIXEL_PIN = board.D21
elif GPIO == 12 :
    PIXEL_PIN = board.D12
elif GPIO == 10 :
    PIXEL_PIN = board.D10
elif GPIO == 18 :
    PIXEL_PIN = board.D18
else :
    print("Impossible de tester les leds sur le GPIO",GPIO,flush=True)
    GO=False

if GO :
    StripLeds=neopixel.NeoPixel(PIXEL_PIN, NBLEDS)
    print("init")

    for p in range(0,NBLEDS+1):
        if p < NBLEDS :
            StripLeds[p]=(128,0,0)
        if p > 0 :
            StripLeds[p-1]=(0,0,0)
        time.sleep(Time/1000)


