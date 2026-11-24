"""
Coin acceptor (monnayeur) : a pulse for each coin accepted (comparator of the front door,
12 V), turned by a relay into a contact closed on an input of a MCP23017 or on a GPIO of the
Raspberry still free (common ground, as the buttons). Two more inputs if wanted : a contact which
adds the credits (or the minutes) of a coin, one which puts the credits back to 0 (a key of the
owner).

Each pulse is counted, never lost : the MCP keeps it itself (its interrupt on change : the state
captured at the edge, kept until read), read by a thread of its own every 20 ms (a GPIO : its level,
read as often), apart from the loop of the game (stopped during a video or the drawing of a screen : a pulse of 0.1 s was
missed, read several times, or the pin banned as a button held down).

Modes : off (free), games (a coin gives credits ; a game costs a price by game or by type of
game, times the players by group : 4 players, a game for 2 = 2 credits), time (a coin gives
minutes, counted during the games). Its settings and the hash of its password are kept apart
from raspydarts.cfg, the file locked (chattr +i) ; the credits, the time left and the count of
the coins in a file of their own (kept when the cabinet is switched off).
"""

import hashlib
import json
import math
import os
import secrets
import subprocess
import threading
import time

from include import cpaths

try:
    from RPi import GPIO as gpio
except (ImportError, RuntimeError):    # not on a Raspberry
    gpio = None

SETTINGS = os.path.join(cpaths.user_dir(), 'monnayeur.json')
STATE = os.path.join(cpaths.user_dir(), 'monnayeur_etat.json')
DEFAULTS = {
    'mode': 'off',                  # off, games, time
    'mcp': '',                      # its input : A0..B7, C0..D7 (MCP), GPIO17... ; '' : none
    'add_input': '',                # a contact which adds the credits of a coin (not counted)
    'reset_input': '',              # a contact which puts the credits (the time) back to 0
    'credits_per_coin': 1,
    'players_per_credit': 0,        # 0 : any number of players for a credit
    'minutes_per_coin': 5,
    'types': {'local': 1, 'network': 1},    # price of a game by type (0 : free)
    'games': {},                    # price of a game for this game (over its type)
    'password': '',                 # pbkdf2$iterations$salt$hash
    'badge_position': 'top-right',  # strip of the credits : top-right, top-center, top-left,
    'badge_size': 'medium',         # bottom-right, bottom-left ; small, medium, large
}
# Password forgotten : an empty file of this name (Windows may add .txt) on the boot partition of
# the SD card, the one read by Windows ; at the start, the password is erased, the file removed
RESET_FILES = [os.path.join(boot, name) for boot in ('/boot/firmware', '/boot')
               for name in ('monnayeur-reinit', 'monnayeur-reinit.txt')]
BADGE_POSITIONS = ('top-right', 'top-center', 'top-left', 'bottom-right', 'bottom-left')
# Strip of the credits : (part of the width, part of the height) of the screen
BADGE_SIZES = {'small': (0.14, 1 / 20), 'medium': (0.2, 1 / 15), 'large': (0.28, 1 / 10)}
TYPES = ('local', 'network')
NETWORK = ('netcreate', 'netjoin')
# The MCP read this often (a pulse of the relay : 0.1 s at least, « slow »)
MCP_POLL = 0.02
# The inputs of the coin acceptor (setting -> what a contact closed does)
INPUTS = {'mcp': 'coin', 'add_input': 'add', 'reset_input': 'reset'}
# A contact of a key (add, reset) : its bounces taken once
KEY_DELAY = 0.5
# Registers of the MCP23017 (IOCON.BANK = 0, as the library leaves it) : bank A, B is the next one
GPINTEN, INTCON, INTF, INTCAP = 0x04, 0x08, 0x0E, 0x10
# Shared with the buttons : two threads on the bus mixed their transfers
I2C_LOCK = threading.Lock()
PASSWORD_ROUNDS = 60000
SHARED = None


def shared(logs, extender=None):
    """
    The coin acceptor, one for the game : the Raspberry created again (a first creation
    failed) would read its input twice
    """
    global SHARED    # pylint: disable=global-statement
    if SHARED is None:
        SHARED = Coins(logs, extender)
    return SHARED


class Coins:
    """
    The coin acceptor : its settings, the credits, the coins counted
    """

    def __init__(self, logs, extender=None):
        self.logs = logs
        self.extender = extender
        self.lock = threading.Lock()
        self.settings = self.read(SETTINGS, DEFAULTS)
        self.state = self.read(STATE, {'credits': 0, 'seconds': 0, 'coins': 0})
        # A coin arrived since the screen was drawn (its strip of credits drawn again)
        self.changed = False
        self.last_coin = None
        # Mode time : the last turn counted, the part of a second not counted yet
        self.last_tick = None
        self.elapsed = 0.0
        self.reader = None
        self.stop_event = threading.Event()
        self.reset_from_boot()
        self.start()

    def reset_from_boot(self):
        """
        Password forgotten (see RESET_FILES) : erased, the other settings kept ; the next
        opening of its screen asks a new one. Only who can take the SD card out can do it
        """
        found = [path for path in RESET_FILES if os.path.exists(path)]
        if not found:
            return
        if self.settings.get('password'):
            settings = dict(self.settings)
            settings['password'] = ''
            self.save_settings(settings)
        for path in found:
            subprocess.run(['sudo', '-n', 'rm', '-f', path], capture_output=True, timeout=10, check=False)
        self.logs.warning(f"Coin acceptor : password erased ({', '.join(found)})")

    # ------------------------------------------------------------------ files
    def read(self, path, defaults):
        """
        A file of settings or of state, completed by its defaults
        """
        values = json.loads(json.dumps(defaults))
        try:
            with open(path, encoding='utf-8') as file:
                values.update(json.load(file))
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as error:
            self.logs.error(f"Coin acceptor : {path} not read ({error})")
        return values

    def save_state(self):
        """
        Credits, time left, coins counted
        """
        try:
            with open(f"{STATE}.tmp", 'w', encoding='utf-8') as file:
                json.dump(self.state, file)
            os.replace(f"{STATE}.tmp", STATE)
        except OSError as error:
            self.logs.error(f"Coin acceptor : state not saved ({error})")

    def save_settings(self, settings):
        """
        Its settings written in their locked file (unlocked for the time of the writing)
        """
        self.settings = settings
        chattr = lambda flag: subprocess.run(['sudo', '-n', 'chattr', flag, SETTINGS], capture_output=True,
                                             timeout=10, check=False)
        if os.path.exists(SETTINGS):
            chattr('-i')
        try:
            with open(SETTINGS, 'w', encoding='utf-8') as file:
                json.dump(settings, file, indent=1)
        finally:
            chattr('+i')
        self.start()

    # ------------------------------------------------------------------ password
    @staticmethod
    def hash_password(password):
        """
        Its hash : pbkdf2$rounds$salt$hash
        """
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), PASSWORD_ROUNDS).hex()
        return f"pbkdf2${PASSWORD_ROUNDS}${salt}${digest}"

    def check_password(self, password):
        """
        The password typed is the one set
        """
        try:
            _name, rounds, salt, digest = self.settings.get('password', '').split('$')
        except ValueError:
            return False
        typed = hashlib.pbkdf2_hmac('sha256', str(password).encode(), bytes.fromhex(salt), int(rounds)).hex()
        return secrets.compare_digest(typed, digest)

    # ------------------------------------------------------------------ reading the coins
    def start(self):
        """
        Its inputs read (again after a change of the settings) : pins of a MCP or GPIO of the
        Raspberry, all by one thread
        """
        self.stop()
        if self.settings.get('mode') == 'off':
            return
        watched = []
        for setting, action in INPUTS.items():
            name = str(self.settings.get(setting) or '').strip().upper()
            if not name:
                continue
            watch = self.watch_gpio(name, action) if name.startswith('GPIO') else self.watch_mcp(name, action)
            if watch is not None:
                watched.append(watch)
        if watched:
            self.reader = threading.Thread(target=self.read_inputs, args=(watched, self.stop_event), daemon=True)
            self.reader.start()

    def stop(self):
        """
        Its inputs no more read
        """
        self.stop_event.set()
        if self.reader is not None:
            self.reader.join(timeout=1)
            self.reader = None
        self.stop_event = threading.Event()

    def watch_mcp(self, name, action):
        """
        A pin of a MCP : its interrupt on change (the state kept at the edge). Its watch, None
        """
        if self.extender is None or not getattr(self.extender, 'chips', None):
            self.logs.error(f"Coin acceptor : no MCP found for {name}")
            return None
        _io, pin_number, index = self.extender.decode(name)
        if pin_number is None:
            self.logs.error(f"Coin acceptor : MCP pin '{name}' unknown")
            return None
        chip = self.extender.chips[index]
        bank, bit = divmod(pin_number, 8)
        try:
            with I2C_LOCK:
                # Interrupt on change of the pin (compared with its previous value), cleared
                chip._write_u8(GPINTEN + bank, chip._read_u8(GPINTEN + bank) | (1 << bit))    # pylint: disable=protected-access
                chip._write_u8(INTCON + bank, chip._read_u8(INTCON + bank) & ~(1 << bit))    # pylint: disable=protected-access
                chip._read_u8(INTCAP + bank)    # pylint: disable=protected-access
        except OSError as error:
            self.logs.error(f"Coin acceptor : MCP pin {name} not set ({error})")
            return None
        self.logs.info(f"Coin acceptor : {action} read on MCP pin {name}")
        return {'kind': 'mcp', 'chip': chip, 'bank': bank, 'bit': bit, 'action': action, 'last': 0.0}

    def watch_gpio(self, name, action):
        """
        A GPIO of the Raspberry (GPIO17) : an input pulled up, its level read. Its watch, None
        """
        text = name[4:].strip()
        if gpio is None or not text.isdigit():
            self.logs.error(f"Coin acceptor : {name} not usable here")
            return None
        pin = int(text)
        try:
            gpio.setmode(gpio.BCM)
            gpio.setup(pin, gpio.IN, pull_up_down=gpio.PUD_UP)
            high = bool(gpio.input(pin))
        except Exception as error:    # pylint: disable=broad-except
            self.logs.error(f"Coin acceptor : GPIO {pin} not set ({error})")
            return None
        self.logs.info(f"Coin acceptor : {action} read on GPIO {pin}")
        return {'kind': 'gpio', 'pin': pin, 'high': high, 'action': action, 'last': 0.0}

    def read_inputs(self, watched, stop_event):
        """
        Thread : the edges kept by the MCP, the levels of the GPIO ; a contact closed (pin low) :
        a coin, credits added, the credits back to 0
        """
        actions = {'coin': self.coin, 'add': self.add_coin, 'reset': self.reset_credits}
        while not stop_event.wait(MCP_POLL):
            for watch in watched:
                if not self.closed(watch):
                    continue
                now = time.monotonic()
                if watch['action'] != 'coin' and now - watch['last'] < KEY_DELAY:
                    continue
                watch['last'] = now
                actions[watch['action']]()

    @staticmethod
    def closed(watch):
        """
        The contact of this input closed since the last look
        """
        try:
            if watch['kind'] == 'gpio':
                high = bool(gpio.input(watch['pin']))
                fell = watch['high'] and not high
                watch['high'] = high
                return fell
            chip, bank, bit = watch['chip'], watch['bank'], watch['bit']
            with I2C_LOCK:
                if not chip._read_u8(INTF + bank) & (1 << bit):    # pylint: disable=protected-access
                    return False
                # Reading the capture clears the interrupt
                captured = chip._read_u8(INTCAP + bank)    # pylint: disable=protected-access
            return not captured & (1 << bit)
        except Exception:    # pylint: disable=broad-except
            return False

    def coin(self):
        """
        A coin accepted : its credits or its minutes
        """
        with self.lock:
            self.state['coins'] = int(self.state.get('coins', 0)) + 1
            mode = self.settings.get('mode')
            if mode == 'games':
                self.state['credits'] = int(self.state.get('credits', 0)) + int(self.settings.get('credits_per_coin', 1))
            elif mode == 'time':
                self.state['seconds'] = int(self.state.get('seconds', 0)) + 60 * int(self.settings.get('minutes_per_coin', 1))
            self.save_state()
            self.last_coin = time.monotonic()
            self.changed = True
        self.logs.info(f"Coin acceptor : coin {self.state['coins']} ({self.state['credits']} credits, {self.state['seconds']} s)")

    # ------------------------------------------------------------------ credits
    def active(self):
        """
        The games are paid for
        """
        return self.settings.get('mode') in ('games', 'time')

    def price(self, game, game_type):
        """
        Price of a game (0 : free) : the one of this game, else the one of its type
        """
        games = self.settings.get('games') or {}
        name = str(game or '').replace(' ', '_')
        if name in games:
            return int(games[name])
        kind = 'network' if game_type in NETWORK else 'local'
        return int((self.settings.get('types') or {}).get(kind, 1))

    def cost(self, game, game_type, players):
        """
        Credits of a game : its price times the groups of players (a game for 2 : 4 players,
        2 games). In time : its price only (0 : free, else the time runs)
        """
        if not self.active():
            return 0
        price = self.price(game, game_type)
        group = int(self.settings.get('players_per_credit', 0) or 0)
        if self.settings.get('mode') == 'time' or group <= 0:
            return price
        return price * math.ceil(max(1, players) / group)

    def can_pay(self, cost):
        """
        Enough credits (games), time left (time)
        """
        if cost <= 0 or not self.active():
            return True
        if self.settings.get('mode') == 'time':
            return int(self.state.get('seconds', 0)) > 0
        return int(self.state.get('credits', 0)) >= cost

    def pay(self, cost):
        """
        A game started : its credits taken (time : counted during the game)
        """
        if cost <= 0 or self.settings.get('mode') != 'games':
            return
        with self.lock:
            self.state['credits'] = max(0, int(self.state.get('credits', 0)) - cost)
            self.save_state()
            self.changed = True

    def spend(self, seconds):
        """
        Time of a game counted (time) ; the time left
        """
        with self.lock:
            left = max(0, int(self.state.get('seconds', 0)) - int(seconds))
            if left != self.state.get('seconds'):
                self.state['seconds'] = left
                # Written every 10 s (not each second on the SD card) : at most 10 s lost
                if left % 10 == 0:
                    self.save_state()
                self.changed = True
            return left

    def tick(self, in_game):
        """
        Mode time : the time of a game counted (called by each turn of the reading of the
        inputs ; in the menus, nothing counted)
        """
        now = time.monotonic()
        if not in_game or self.settings.get('mode') != 'time':
            self.last_tick = None
            return
        if self.last_tick is not None:
            self.elapsed += now - self.last_tick
            if self.elapsed >= 1:
                whole = int(self.elapsed)
                self.elapsed -= whole
                self.spend(whole)
        self.last_tick = now

    def time_up(self):
        """
        Mode time : no time left (the game stops at the end of the turn, unless a coin)
        """
        return self.settings.get('mode') == 'time' and int(self.state.get('seconds', 0)) <= 0

    def add(self, credits=0, seconds=0):
        """
        Credits or time given by the owner (screen of the settings)
        """
        with self.lock:
            self.state['credits'] = int(self.state.get('credits', 0)) + int(credits)
            self.state['seconds'] = int(self.state.get('seconds', 0)) + int(seconds)
            self.save_state()
            self.changed = True

    def add_coin(self):
        """
        The contact of the credits added (a key of the owner) : the credits or the minutes of a
        coin, not counted as a coin
        """
        mode = self.settings.get('mode')
        if mode == 'games':
            self.add(credits=int(self.settings.get('credits_per_coin', 1)))
        elif mode == 'time':
            self.add(seconds=60 * int(self.settings.get('minutes_per_coin', 1)))
        self.logs.info("Coin acceptor : credits added by its contact")

    def reset_credits(self):
        """
        Credits and time left back to 0 (its screen, or its contact)
        """
        with self.lock:
            self.state['credits'] = 0
            self.state['seconds'] = 0
            self.save_state()
            self.changed = True
        self.logs.info("Coin acceptor : credits back to 0")

    def reset_count(self):
        """
        Count of the coins back to 0
        """
        with self.lock:
            self.state['coins'] = 0
            self.save_state()

    def left(self):
        """
        What is left : ('games', credits), ('time', seconds), None when free
        """
        mode = self.settings.get('mode')
        if mode == 'games':
            return 'games', int(self.state.get('credits', 0))
        if mode == 'time':
            return 'time', int(self.state.get('seconds', 0))
        return None
