"""
Autodarts (its cameras read the darts) : its settings, the reading of its darts.

- Autodarts is a program of its own (https://autodarts.io), on another machine of the network
  (a PC, or a Raspberry Pi 4 or 5 with a 64 bits system) : RaspyDarts runs on a 32 bits system,
  Autodarts needs 64 bits, it is never installed on the borne. RaspyDarts only reads what its
  board says on its port 3180 (/api/state : numThrows, throws[].segment), 10 times a second.
- Its darts come to the game as the darts of the target (Craspberry.read_inputs) : every game
  plays with them. Counted at once (live), or the three of a turn when they are taken out of
  the target (takeout), which leaves the time to correct them in Autodarts.
- The darts taken out : Joueur suivant, if the game waits for it, or if the turn is not over
  (an early Joueur suivant, as the button). Never on the turn of the next player.
- Its account, its cameras, its calibration : in Autodarts itself (its page on the port 3180,
  or its command « autodarts » in a terminal). RaspyDarts never sees a password.
"""

import collections
import json
import os
import queue
import threading
import time
import urllib.request

from include import cpaths

SETTINGS_FILE = os.path.join(cpaths.user_dir(), 'autodarts.json')
# host : the machine of Autodarts on the network ('' : none yet ; 127.0.0.1 : the setting of before, none)
DEFAULTS = {'enabled': False, 'host': '', 'port': 3180, 'counting': 'live', 'takeout_next': True}
COUNTINGS = ('live', 'takeout')
LOCAL_HOSTS = ('127.0.0.1', 'localhost', '')

ACCOUNT_URL = 'https://autodarts.io'


def load():
    '''
    Its settings (those by default for what is missing)
    '''
    settings = dict(DEFAULTS)
    try:
        with open(SETTINGS_FILE, encoding='utf-8') as file:
            data = json.load(file)
        if isinstance(data, dict):
            settings.update({key: data[key] for key in DEFAULTS if key in data})
    except (OSError, ValueError):
        pass
    if settings['counting'] not in COUNTINGS:
        settings['counting'] = DEFAULTS['counting']
    try:
        settings['port'] = int(settings['port'])
    except (TypeError, ValueError):
        settings['port'] = DEFAULTS['port']
    return settings


def save(settings):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    temporary = f'{SETTINGS_FILE}.tmp'
    with open(temporary, 'w', encoding='utf-8') as file:
        json.dump({key: settings.get(key, DEFAULTS[key]) for key in DEFAULTS}, file, indent=2)
    os.replace(temporary, SETTINGS_FILE)


def is_local(settings):
    '''
    No address of Autodarts yet (empty, or this Raspberry : never possible, Autodarts needs 64 bits)
    '''
    return str(settings.get('host') or '').strip() in LOCAL_HOSTS


def segment_code(throw, interior=False):
    '''
    A dart of Autodarts as the game names it : S20, s20 (inner single, when the target has
    them), D20, T20, SB, DB ; MISS (out of the target) ; None : unknown
    '''
    segment = throw.get('segment') if isinstance(throw, dict) else None
    if not isinstance(segment, dict):
        return None
    try:
        number = int(segment.get('number') or 0)
        multiplier = int(segment.get('multiplier') or 0)
    except (TypeError, ValueError):
        number, multiplier = 0, 0
    name = str(segment.get('name') or '').upper()
    bed = str(segment.get('bed') or '')
    if number == 25 or name in ('BULL', 'BULLSEYE', '25', '50', 'SB', 'DB'):
        return 'DB' if multiplier == 2 or name in ('BULLSEYE', '50', 'DB') else 'SB'
    if multiplier <= 0 or number <= 0 or name.startswith('M'):
        return 'MISS'
    if not 1 <= number <= 20 or multiplier > 3:
        return None
    if multiplier == 1:
        return f's{number}' if interior and 'inner' in bed.lower() else f'S{number}'
    return f"{'D' if multiplier == 2 else 'T'}{number}"


class Reader:
    '''
    The reading of Autodarts, in a thread of its own : its darts and its darts taken out, given
    to the game by take()
    '''
    # Its state read this often (seconds), and given up after this long (its board busy)
    PERIOD = 0.1
    TIMEOUT = 0.5
    TAKEOUT = 'TAKEOUT'

    def __init__(self, logs):
        self.logs = logs
        self.settings = load()
        self.interior = False
        self.items = queue.Queue()
        self.pending = []
        self.last = None
        self.turn_darts = 0
        # Darts taken out before the end of the turn : the game counts the others missed, then
        # waits for Joueur suivant again ; given at once (the darts were taken out once)
        self.early = False
        # What the screen of its settings shows : its last answer, its error, the darts read
        self.connected = False
        self.error = None
        self.state = None
        self.seen = None
        self.events = collections.deque(maxlen=8)
        self.thread = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

    @property
    def active(self):
        return bool(self.settings.get('enabled')) and self.thread is not None

    def url(self):
        host = str(self.settings.get('host') or '127.0.0.1').strip() or '127.0.0.1'
        return f"http://{host}:{self.settings.get('port') or 3180}/api/state"

    def configure(self, settings=None, interior=None):
        '''
        Its settings changed : the reading started, stopped or started again
        '''
        if settings is not None:
            self.settings = dict(settings)
        if interior is not None:
            self.interior = bool(interior)
        self.stop()
        # Read only from the machine of Autodarts (none given : nothing to read)
        if self.settings.get('enabled') and not is_local(self.settings):
            self.stop_event = threading.Event()
            self.last = None
            self.pending = []
            self.thread = threading.Thread(target=self.run, args=(self.stop_event,), daemon=True)
            self.thread.start()
            self.logs.info(f"Autodarts : read on {self.url()} ({self.settings.get('counting')})")

    def stop(self):
        if self.thread is not None:
            self.stop_event.set()
            self.thread = None
        self.connected = False
        self.drop()

    def drop(self):
        '''
        What was read and not played yet forgotten (a game starts, the settings change)
        '''
        with self.lock:
            while not self.items.empty():
                try:
                    self.items.get_nowait()
                except queue.Empty:
                    break
            self.pending = []
            self.turn_darts = 0
            self.early = False

    def note(self, text):
        self.events.appendleft((time.strftime('%H:%M:%S'), text))

    def run(self, stop_event):
        url = self.url()
        while not stop_event.is_set():
            started = time.monotonic()
            try:
                with urllib.request.urlopen(url, timeout=self.TIMEOUT) as response:
                    data = json.loads(response.read().decode('utf-8'))
                if not self.connected:
                    self.logs.info(f"Autodarts : connected ({url})")
                self.connected, self.error, self.state, self.seen = True, None, data, time.time()
                self.read_state(data if isinstance(data, dict) else {})
            except Exception as error:    # pylint: disable=broad-except
                if self.connected or self.error is None:
                    self.logs.warning(f"Autodarts : no answer from {url} ({error})")
                self.connected, self.error = False, str(error)
                # A board which does not answer : asked less often
                stop_event.wait(1.0)
            stop_event.wait(max(0.0, self.PERIOD - (time.monotonic() - started)))

    def read_state(self, data):
        try:
            count = int(data.get('numThrows') or 0)
        except (TypeError, ValueError):
            count = 0
        throws = data.get('throws') if isinstance(data.get('throws'), list) else []
        with self.lock:
            if self.last is None:
                # The darts already in the target when the reading starts : not played
                self.last = count
                return
            if count > self.last:
                for index in range(self.last, min(count, len(throws))):
                    code = segment_code(throws[index], self.interior)
                    if code is None:
                        self.logs.warning(f"Autodarts : dart not understood ({throws[index]})")
                        continue
                    self.note(code)
                    if self.settings.get('counting') == 'takeout':
                        self.pending.append(code)
                    else:
                        self.items.put(code)
                self.last = count
            elif count < self.last:
                if count == 0:
                    self.taken_out()
                self.last = count

    def taken_out(self):
        '''
        The darts taken out of the target : those kept played (takeout), then Joueur suivant
        '''
        self.note('takeout')
        if self.settings.get('counting') == 'takeout' and self.pending:
            darts = self.pending[:3]
            darts += ['MISS'] * (3 - len(darts))
            for code in darts:
                self.items.put(code)
            self.pending = []
        if self.settings.get('takeout_next', True):
            self.items.put(self.TAKEOUT)

    def take(self, waiting_next=False, darts_per_turn=3):
        '''
        The next dart for the game (S20, MISS, PLAYERBUTTON), None : none. The darts taken
        out : Joueur suivant when the game waits for it, or before the end of the turn
        (an early Joueur suivant) ; never once the turn is over (the game went on by itself)
        '''
        with self.lock:
            if self.early and waiting_next:
                self.early = False
                return 'PLAYERBUTTON'
            while True:
                try:
                    item = self.items.get_nowait()
                except queue.Empty:
                    return None
                if item != self.TAKEOUT:
                    self.turn_darts += 1
                    self.early = False
                    return item
                darts, self.turn_darts = self.turn_darts, 0
                if waiting_next:
                    return 'PLAYERBUTTON'
                if 0 < darts < darts_per_turn:
                    self.early = True
                    return 'PLAYERBUTTON'


SHARED = {}


def shared(logs):
    '''
    The reader of the game (one for every screen)
    '''
    if 'reader' not in SHARED:
        SHARED['reader'] = Reader(logs)
    return SHARED['reader']
