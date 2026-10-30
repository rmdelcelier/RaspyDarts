
"""
Manage MCP2307 I/O

light_buttons and toys_buttons are a dictionnary of tuples:
        {
        'TOY1': ('C3', address, 4),
        'PIN_UP': ('B2', address, 10),
        ...
        }
"""

import time
import board
import busio

from digitalio import Direction, Pull
from adafruit_mcp230xx.mcp23017 import MCP23017
from threading import Thread
from .ccoins import I2C_LOCK

LAST_BUTTON = None
COUNT_BUTTON = 0

# Register of the MCP23017 used to recognise it : input polarity of the bank A (0 for the
# game). Another chip on 0x20-0x27 (PCF8574 of a LCD, ...) does not give back what is written
_IPOLA = 0x02


def is_mcp23017(chip):
    '''
    The chip answering on the address is a MCP23017 : a value written in IPOLA is read back
    '''
    try:
        chip._write_u8(_IPOLA, 0xA5)
        found = chip._read_u8(_IPOLA) == 0xA5
        chip._write_u8(_IPOLA, 0x00)
        return found
    except OSError:
        return False

DEFAULTS = {
    'PIN_UP': 'A0',
    'PIN_DOWN': 'A1',
    'PIN_LEFT': 'A2',
    'PIN_RIGHT': 'A3',
    'PIN_PLUS': 'A4',
    'PIN_MINUS': 'A5',
    'PIN_VALIDATE': 'A6',
    'PIN_CANCEL':'A7',
    'PIN_NEXTPLAYER':'B0',
    'PIN_BACK':'B1',
    'PIN_GAMEBUTTON':'B2',
    'PIN_VOLUME_UP':'B3',
    'PIN_VOLUME_DOWN':'B4',
    'PIN_VOLUME_MUTE':'B5',
    'PIN_CPTPLAYER':'B6',
    # A shock sensor is rare : on a free pin (read as pressed, its logic is reversed) it
    # was banned at each start
    'PIN_MISSDART':'',
    'LIGHT_NEXTPLAYER':'',
    'LIGHT_BACK':'',
    'LIGHT_NAVIGATE':'',
    'LIGHT_VALIDATE':'',
    'LIGHT_LASER':'',
    'LIGHT_FLASH':'',
    'LIGHT_PLAYERS':'',
    'LIGHT_CELEBRATION':'',
    'LIGHT_CELEBRATION2':'',
    'LIGHT_LIGHT':'',
    'TOY1':'C0',
    'TOY2':'C1',
    'TOY3':'C2',
    'TOY4':'C3',
    'TOY5':'C4',
    'TOY6':'C5',
    'TOY7':'C6',
    'TOY8':'C7',
    'TOY9':'D0',
    'TOY10':'D1',
    'TOY11':'D2',
    'TOY12':'D3',
    'TOY13':'D4',
    'TOY14':'D5',
    'TOY15':'D6',
    'TOY16':'D7'
}

class Gpio_extender:
    """
    Manage MCP2307 I/O
    """

    def __init__(self, logs, buttons=None):
        """
        Every MCP23017 found (addresses 0x20 to 0x27). The n-th one found has the letters
        A/B, the next one C/D, then E/F... (8 pins each). All their pins start as inputs.
        The other chips of the bus are only told in the log : nothing is written to them
        """
        self.logs = logs
        i2c = busio.I2C(board.SCL, board.SDA)
        self.chips = []
        self.all_io = None

        addresses = []
        try:
            while not i2c.try_lock():
                time.sleep(0.01)
            try:
                addresses = i2c.scan()
            finally:
                i2c.unlock()
        except Exception as error: # pylint: disable=broad-except
            self.logs.warning(f"I2C bus not read : {error}")
        self.logs.info(f"I2C devices : {' '.join(hex(address) for address in addresses) or 'none'}")

        for address in addresses:
            if not 0x20 <= address <= 0x27:
                self.logs.info(f"I2C device at {hex(address)} : not a MCP23017 address")
                continue
            try:
                chip = MCP23017(i2c, address=address, reset=False)
                if not is_mcp23017(chip):
                    self.logs.warning(f"I2C device at {hex(address)} is not a MCP23017 : left aside")
                    continue
                # Now only, the reset of the library (all inputs, no pull-up...)
                self.chips.append(MCP23017(i2c, address=address))
                self.logs.info(f"MCP found at {hex(address)}")
            except Exception as error: # pylint: disable=broad-except
                self.logs.warning(f"I2C device at {hex(address)} : {error}")
        # Names kept : the first one tells there is an extension card
        self.mcp1 = self.chips[0] if self.chips else None
        self.mcp2 = self.chips[1] if len(self.chips) > 1 else None

        if self.chips:
            self.all_io = []
            for index, chip in enumerate(self.chips):
                for pin in range(0, 16):
                    # Inputs to begin with : set_io makes outputs of the toys. (With a
                    # second card, the pins of the FIRST one were made outputs, low)
                    io = chip.get_pin(pin)
                    io.direction = Direction.INPUT
                    io.pull = Pull.UP
                self.all_io += self.pins_of(index)

            # Apply configuration
            if buttons:
                self.set_io(buttons)
            else:
                self.buttons_list = {}
                self.toys_list = {}
                self.pin_switcher = {}
        else:
            self.logs.info("No MCP found (addresses 0x20 to 0x27)")

        self.banned_button = None
        # TODO REMOVE RD
        #self._gpio_read_total = 0.0
        #self._gpio_read_count = 0

    # TODO REMOVE RD
    #def __del__(self):
    #    if self._gpio_read_count:
    #        avg_ms = (self._gpio_read_total / self._gpio_read_count) * 1000
    #        print(f"(TIME MANAGER - DEL CALLING) average extended GPIO read duration: {avg_ms:.3f} ms over {self._gpio_read_count} reads")
    #        self.logs.debug(
    #            f"(TIME MANAGER - DEL CALLING) average extended GPIO read duration: {avg_ms:.3f} ms over {self._gpio_read_count} reads"
    #        )
    # TODO REMOVE RD
    
    @staticmethod
    def pins_of(index):
        '''
        Names of the pins of the index-th card : A0..B7, C0..D7, E0..F7...
        '''
        return [f"{chr(65 + 2 * index + bank)}{number}" for bank in (0, 1) for number in range(0, 8)]

    def decode(self, value):
        """
        Decode a name : B3 => (pin of the card, its number 0-15 on the card, card index)
        """
        if value not in (self.all_io or []):
            return None, None, None

        try:
            letter = ord(value[:1:]) - 65
            index = letter // 2
            pin_number = (letter % 2) * 8 + int(value[1::])
            return self.chips[index].get_pin(pin_number), pin_number, index
        except Exception: # pylint: disable=broad-except
            return None, None, None

    def set_io(self, buttons):
        """
        Init self.buttons_list (list of inputs)
        Init self.toys_list (list of outputs)

        {['TOY1', 'C3', address], [],...}
        """
        self.buttons_list = {}
        self.toys_list = {}
        self.pin_switcher = {}

        if self.mcp1 is None:
            return None

        for button in buttons:
            value = str(buttons[button]).upper()
            address, pin_number, index = self.decode(value)
            if address is not None:
                if button.startswith('PIN_'):
                    self.buttons_list[button] = (value, address, pin_number)
                    self.pin_switcher[(index, pin_number)] = button
                    address.direction = Direction.INPUT
                    address.pull = Pull.UP

                elif button.startswith('LIGHT_') or button.startswith('TOY'):
                    self.toys_list[button] = (value, address, pin_number)
                    address.direction = Direction.OUTPUT
                    address.value = 0

        return True

    def get_defaults(self):
        """
        Get default configuration
        """
        return DEFAULTS

    def set_defaults(self):
        """
        Set default configuration
        """
        self.set_io(DEFAULTS)

    def read_entries(self):
        """
        Read the cards holding buttons
        """
        global LAST_BUTTON
        global COUNT_BUTTON
        # False/0 si appuie sur le bouton
        return_value = None
        ban_value = None
        
        # TODO REMOVE RD
        #t0 = time.perf_counter()
        # One read per card holding buttons
        # (the bus shared with the thread of the coin acceptor : include/ccoins.py)
        with I2C_LOCK:
            values = {index: self.chips[index].gpio for index in {index for index, _pin in self.pin_switcher}}
        #t1 = time.perf_counter()
        
        ## Update cumulative stats (keep total in seconds)
        #self._gpio_read_total += (t1 - t0)
        #self._gpio_read_count += 1

        ## Compute duration in milliseconds
        #duration_ms = (t1 - t0) * 1000

        ## Only log when the read took longer than 10 ms
        #if duration_ms > 10.0:
        #    print(f"(TIME MANAGER - EXCESSIVE READING) extended GPIO read duration: {duration_ms:.3f} ms")
        #    self.logs.debug(
        #        f"(TIME MANAGER - EXCESSIVE READING) extended GPIO read duration: {duration_ms:.3f} ms"
        #    )
        # TODO REMOVE RD

        for (index, pin), button in self.pin_switcher.items():
            value = values[index]
            if ((not value & 2**pin and button != 'PIN_MISSDART')
                or (value & 2**pin and button == 'PIN_MISSDART')):
                if button != self.banned_button:
                    return_value = button
                else:
                    ban_value = button

        if return_value is not None and return_value == LAST_BUTTON:
            COUNT_BUTTON += 1
            if COUNT_BUTTON > 30:
                self.banned_button = return_value
                self.logs.warning(f"Button {self.banned_button} is banned !")
        elif ban_value is None:
            COUNT_BUTTON = 0
            LAST_BUTTON = return_value
            self.banned_button = None

        return return_value

    def test_entries(self):
        """
        Read self.mcp1 and returns list of pressed buttons ['A0'[,'B1']]
        """
        # False/0 si appuie sur le bouton
        pressed_buttons = []

        for button in self.buttons_list:
            with I2C_LOCK:
                value = self.buttons_list[button][1].value
            # False/0 si appuie sur le bouton ; True/1 au choc pour le capteur (as read_entries)
            pressed = value if button == 'PIN_MISSDART' else not value
            if pressed:
                # Compute A0..B7
                pressed_buttons.append(self.buttons_list[button][0])

        return pressed_buttons

    def thread_toy(self, iterations, pin, delay_on, delay_off):
        """
        Light a toy
        """
        for iteration in range(iterations):

            with I2C_LOCK:
                pin.value = not(pin.value)
            time.sleep(delay_on / 1000)

            with I2C_LOCK:
                pin.value = not(pin.value)
            if iteration + 1 < iterations:
                time.sleep(delay_off / 1000)

    def strobe_toys(self, toys, iterations=3, delay_on=10, delay_off=100):
        """
        Strobe light
        Return an array of threads
        """
        threads = []
        for toy in toys:
            try:
                element = self.toys_list.get(toy, None)
                if element is not None:
                    threads += [Thread(target=self.thread_toy, args=(iterations, element[1], delay_on, delay_off))]
                else:
                    pass
            except Exception as error: # pylint: disable=bare-except
                self.logs.error(f"Decode error for {toy} : {error}")

        for thread in threads:
            thread.start()
        return threads

    def light_toys(self, toys, light=True):
        """
        Light a toy
        """
        pins = []
        for toy in toys:
            try:
                element = self.toys_list.get(toy, None)
                if element is not None:
                    pins.append(element[1])
            except Exception as error: # pylint: disable=bare-except
                self.logs.error(f"Error during light of {toy}")
                pass

        for pin in pins :
            with I2C_LOCK:
                pin.value = 1 if light else 0
