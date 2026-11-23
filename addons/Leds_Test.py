"""
Leds_Test.py : the LED tried by the wizard of the first start (cwizard.setup_leds), before any
LED server runs. Launched with sudo, it reads its orders on stdin, one per line :
    rainbow                 a rainbow going round
    red                     all red (RGB / GRB : red if the order is the right one)
    bri <1-100>             brightness
    count <n>               number of LED (the strip : the first n lit, the others off)
    type <rgb|grb>          order of the colours
    off                     all off
    quit                    all off, the end
Usage : sudo python3 Leds_Test.py <pin> <count> <brightness 1-100> <rgb|grb> <dma> [<pins to release>]
pins to release : GPIO sharing the generator of this pin (PWM0 : 12 and 18), left on it by a former
use : put back as outputs held low first, else the signal comes out on them too. The pin tried is
released the same way at the end
"""

import subprocess
import sys
import threading
import time

from rpi_ws281x import PixelStrip, Color, WS2811_STRIP_RGB, WS2811_STRIP_GRB

FREQ = 800000
MAX_LEDS = 1000
# Black sent to this many LED at the start and at the end : more than any target or strip (the
# LED keep the last colour they got : those of a former try, longer, or lit by a line left
# floating, stayed lit)
CLEAR_LEDS = 600


class Tester:
    def __init__(self, pin, count, brightness, kind, dma):
        self.pin, self.count, self.brightness, self.kind, self.dma = pin, count, brightness, kind, dma
        self.mode = 'rainbow'
        self.strip = None
        self.lock = threading.Lock()
        self.clear_all()
        self.build()

    def make(self, count):
        channel = 1 if self.pin in (13, 19, 41, 45, 53) else 0
        order = WS2811_STRIP_RGB if self.kind == 'rgb' else WS2811_STRIP_GRB
        strip = PixelStrip(count, self.pin, FREQ, self.dma, False, self.level(), channel, strip_type=order)
        strip.begin()
        return strip

    def drop(self):
        if self.strip is not None:
            try:
                self.strip._cleanup()    # pylint: disable=protected-access
            except Exception:    # pylint: disable=broad-except
                pass
            self.strip = None

    def clear_all(self):
        '''
        All the LED of the line off, as many as there may be (CLEAR_LEDS)
        '''
        self.drop()
        self.strip = self.make(CLEAR_LEDS)
        self.fill(Color(0, 0, 0))
        time.sleep(0.05)
        self.drop()

    def build(self):
        '''
        The strip made again (its length or its colour order changed) : the LED of the former
        one off first (a shorter one left the others lit)
        '''
        if self.strip is not None:
            self.fill(Color(0, 0, 0), show=True)
        self.clear_all()
        self.strip = self.make(self.count)

    def level(self):
        return max(1, min(255, int(self.brightness * 255 / 100)))

    def fill(self, color, show=True):
        for index in range(self.strip.numPixels()):
            self.strip.setPixelColor(index, color)
        if show:
            self.strip.show()

    @staticmethod
    def wheel(position):
        position %= 256
        if position < 85:
            return Color(255 - position * 3, position * 3, 0)
        if position < 170:
            position -= 85
            return Color(0, 255 - position * 3, position * 3)
        position -= 170
        return Color(position * 3, 0, 255 - position * 3)

    def run(self):
        step = 0
        while True:
            with self.lock:
                if self.mode == 'quit':
                    self.fill(Color(0, 0, 0))
                    return
                if self.mode == 'rainbow':
                    count = self.strip.numPixels()
                    for index in range(count):
                        self.strip.setPixelColor(index, self.wheel(int(index * 256 / max(count, 1)) + step))
                    self.strip.show()
                    step = (step + 4) % 256
            time.sleep(0.03)

    def order(self, line):
        words = line.split()
        if not words:
            return
        with self.lock:
            if words[0] == 'rainbow':
                self.mode = 'rainbow'
            elif words[0] == 'red':
                self.mode = 'red'
                self.fill(Color(255, 0, 0))
            elif words[0] == 'off':
                self.mode = 'off'
                self.fill(Color(0, 0, 0))
            elif words[0] == 'bri' and len(words) > 1:
                self.brightness = max(1, min(100, int(words[1])))
                self.strip.setBrightness(self.level())
                if self.mode == 'red':
                    self.fill(Color(255, 0, 0))
                elif self.mode != 'rainbow':
                    self.strip.show()
            elif words[0] == 'count' and len(words) > 1:
                self.count = max(1, min(MAX_LEDS, int(words[1])))
                self.build()
                if self.mode == 'red':
                    self.fill(Color(255, 0, 0))
            elif words[0] == 'type' and len(words) > 1 and words[1] in ('rgb', 'grb'):
                self.kind = words[1]
                self.build()
                if self.mode == 'red':
                    self.fill(Color(255, 0, 0))
            elif words[0] == 'quit':
                self.mode = 'quit'
            print(f"ok {line}", flush=True)


def release(pins):
    '''
    These GPIO as plain outputs held low : no signal of the LED on them, and not « in the air »
    (an input left floating made the LED wired on it light up at random)
    '''
    for pin in pins:
        try:
            subprocess.run(['pinctrl', 'set', str(pin), 'op', 'dl'], check=False, timeout=3,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError):
            pass


def main():
    pin, count, brightness, kind, dma = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], int(sys.argv[5])
    siblings = [int(value) for value in sys.argv[6].split(',') if value.strip()] if len(sys.argv) > 6 else []
    release(siblings)
    tester = Tester(pin, count, brightness, kind, dma)
    thread = threading.Thread(target=tester.run, daemon=True)
    thread.start()
    print("ready", flush=True)
    for line in sys.stdin:
        tester.order(line.strip())
        if line.strip() == 'quit':
            break
    tester.order('quit')
    thread.join(2)
    # All off (as many LED as there may be), then the line held low
    with tester.lock:
        tester.clear_all()
    release([pin])


if __name__ == '__main__':
    main()
