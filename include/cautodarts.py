"""
Autodarts (its cameras read the darts) : its settings, the reading of its darts, its installation.

- Autodarts is a program of its own (https://autodarts.io) : on this Raspberry (a Pi 4 or a
  Pi 5, 64 bits) or on another machine of the network. RaspyDarts only reads what its board
  says on its port 3180 (/api/state), 10 times a second. Two forms of its darts : Autodarts 1
  (numThrows, throws[].segment {name, number, multiplier, bed}) and Autodarts 2 (no numThrows,
  throws[] flat : segmentName, segmentNumber, multiplier, bed, bouncer ; no throws when the
  target is empty).
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
import platform
import queue
import subprocess
import threading
import time
import urllib.request

from include import cpaths

SETTINGS_FILE = os.path.join(cpaths.user_dir(), 'autodarts.json')
# host 127.0.0.1 : Autodarts on this Raspberry
DEFAULTS = {'enabled': False, 'host': '127.0.0.1', 'port': 3180, 'counting': 'live', 'takeout_next': True}
COUNTINGS = ('live', 'takeout')
LOCAL_HOSTS = ('127.0.0.1', 'localhost', '')

# Its installation : the headless board of Autodarts v2, by its own script (get.autodarts.io,
# without a terminal, would install the old v1). As the user of the game : its files in
# ~/.local/share/autodarts, its command ~/.local/bin/autodarts
INSTALLER = 'https://autodarts.sh'
INSTALL_COMMAND = f'curl -fsSL {INSTALLER} | bash -s -- --headless --no-color'
INSTALL_UNIT = 'autodarts-install'
INSTALL_LOG = os.path.join(cpaths.ROOT_DIR, 'logs', 'autodarts_install.log')
INSTALL_DONE = 'Installed Autodarts'
BINARY = os.path.expanduser('~/.local/bin/autodarts')
# Its service, started with the session of the game (its installer installs none : its own
# screen offers it ; same name and place as the one it writes)
UNIT_NAME = 'autodarts.service'
UNIT_FILE = os.path.expanduser(f'~/.config/systemd/user/{UNIT_NAME}')
UNIT_TEXT = """[Unit]
Description=Autodarts (board), started for RaspyDarts
After=network-online.target

[Service]
ExecStart=%h/.local/bin/autodarts run
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
"""
# Installed by an older way : a service of the system
SYSTEM_UNIT_FILE = '/etc/systemd/system/autodarts.service'
# RaspyDarts installed again on a Raspberry able to run Autodarts
RASPYDARTS_INSTALL = 'curl -fsSL https://raw.githubusercontent.com/rmdelcelier/RaspyDarts/main/install.sh | sudo bash'
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
    return str(settings.get('host') or '').strip() in LOCAL_HOSTS


def machine():
    '''
    This Raspberry : its model (its text, its number : 3, 4, 5, None) and a 64 bits system
    '''
    model = ''
    try:
        with open('/proc/device-tree/model', encoding='utf-8', errors='ignore') as file:
            model = file.read().strip('\x00\n ')
    except OSError:
        pass
    number = None
    for candidate in (5, 4, 3, 2):
        if f'Raspberry Pi {candidate}' in model or (candidate == 5 and 'Compute Module 5' in model) \
                or (candidate == 4 and ('Compute Module 4' in model or 'Pi 400' in model)):
            number = candidate
            break
    # The system, not the kernel : a 64 bits kernel can run a 32 bits system
    bits64 = platform.architecture()[0] == '64bit' and platform.machine() in ('aarch64', 'arm64', 'x86_64')
    return {'model': model, 'number': number, 'bits64': bits64}


def capable(info=None):
    '''
    Autodarts can run here : a Raspberry Pi 4 or 5 with a 64 bits system. None if it can, else
    why not : 'model' (an older Raspberry), 'bits' (a 32 bits system)
    '''
    info = info or machine()
    if info['number'] is not None and info['number'] < 4:
        return 'model'
    if not info['bits64']:
        return 'bits'
    return None


def installed():
    return os.path.exists(BINARY) or os.path.isfile(SYSTEM_UNIT_FILE)


def has_service():
    return os.path.isfile(UNIT_FILE) or os.path.isfile(SYSTEM_UNIT_FILE)


def service_active():
    '''
    Its service running (of the session of the game, or of the system)
    '''
    for command in (['systemctl', '--user', 'is-active', '--quiet', UNIT_NAME],
                    ['systemctl', 'is-active', '--quiet', UNIT_NAME]):
        try:
            if subprocess.run(command, check=False, timeout=5).returncode == 0:
                return True
        except Exception:    # pylint: disable=broad-except
            pass
    return False


def installing():
    try:
        return subprocess.run(['systemctl', '--user', 'is-active', '--quiet', INSTALL_UNIT],
                              check=False, timeout=5).returncode == 0
    except Exception:    # pylint: disable=broad-except
        return False


def launch_install(logs):
    '''
    Its installation launched in the background, in a unit of the session of the game (it goes
    on if the game is restarted). True : launched
    '''
    os.makedirs(os.path.dirname(INSTALL_LOG), exist_ok=True)
    command = f"{INSTALL_COMMAND} > {INSTALL_LOG} 2>&1"
    try:
        subprocess.run(['systemd-run', '--user', f'--unit={INSTALL_UNIT}', '--collect', '/bin/bash', '-c', command],
                       check=True, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logs.info(f"Autodarts : installation launched ({command})")
        return True
    except Exception as error:    # pylint: disable=broad-except
        logs.error(f"Autodarts : installation not launched : {error}")
        return False


def install_log():
    '''
    The lines of its log of installation, without the colours of the terminal
    '''
    import re    # pylint: disable=import-outside-toplevel
    try:
        with open(INSTALL_LOG, encoding='utf-8', errors='ignore') as file:
            text = file.read()
    except OSError:
        return []
    lines = [re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line).strip() for line in text.replace('\r', '\n').split('\n')]
    return [line for line in lines if line]


def install_succeeded():
    return installed() and any(INSTALL_DONE in line for line in install_log()[-40:])


def install_service(logs):
    '''
    Its service : started with the session of the game, at once. True : running
    '''
    try:
        if not os.path.isfile(SYSTEM_UNIT_FILE):
            os.makedirs(os.path.dirname(UNIT_FILE), exist_ok=True)
            if not os.path.isfile(UNIT_FILE):
                with open(UNIT_FILE, 'w', encoding='utf-8') as file:
                    file.write(UNIT_TEXT)
            subprocess.run(['systemctl', '--user', 'daemon-reload'], check=False, timeout=30)
            subprocess.run(['systemctl', '--user', 'enable', '--now', UNIT_NAME], check=False, timeout=60,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(['sudo', '-n', 'systemctl', 'restart', UNIT_NAME], check=False, timeout=60,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as error:    # pylint: disable=broad-except
        logs.error(f"Autodarts : service not started : {error}")
    return service_active()


def restart_service(logs):
    '''
    Autodarts started again (its service), or its service installed if it has none
    '''
    if not has_service():
        return install_service(logs)
    if os.path.isfile(UNIT_FILE):
        command = ['systemctl', '--user', 'restart', UNIT_NAME]
    else:
        command = ['sudo', '-n', 'systemctl', 'restart', UNIT_NAME]
    try:
        subprocess.run(command, check=False, timeout=60, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as error:    # pylint: disable=broad-except
        logs.error(f"Autodarts : not started again : {error}")
    return service_active()


def segment_of(throw):
    '''
    The segment of a dart of Autodarts : {name, number, multiplier, bed, bouncer}, from its
    segment (Autodarts 1) or from the dart itself (Autodarts 2 : segmentName, segmentNumber...).
    None : not a dart
    '''
    if not isinstance(throw, dict):
        return None
    if isinstance(throw.get('segment'), dict):
        segment = dict(throw['segment'])
    elif any(key in throw for key in ('segmentName', 'segmentNumber', 'name', 'number')):
        segment = dict(throw)
    else:
        return None
    for new, old in (('segmentName', 'name'), ('segmentNumber', 'number'), ('segmentMultiplier', 'multiplier'),
                     ('segmentBed', 'bed')):
        if segment.get(old) is None and new in segment:
            segment[old] = segment[new]
    return segment


def throws_of(data):
    '''
    The darts in the target : (their number, their list). Autodarts 1 gives numThrows,
    Autodarts 2 only its list (none when the target is empty)
    '''
    throws = data.get('throws') if isinstance(data.get('throws'), list) else []
    try:
        count = int(data['numThrows']) if data.get('numThrows') is not None else len(throws)
    except (TypeError, ValueError):
        count = len(throws)
    return count, throws


def segment_code(throw, interior=False):
    '''
    A dart of Autodarts as the game names it : S20, s20 (inner single, when the target has
    them), D20, T20, SB, DB ; MISS (out of the target, bounced out) ; None : unknown
    '''
    segment = segment_of(throw)
    if segment is None:
        return None
    if segment.get('bouncer') is True or (isinstance(throw, dict) and throw.get('bouncer') is True):
        return 'MISS'
    try:
        number = int(segment.get('number') or 0)
        multiplier = int(segment.get('multiplier') or 0)
    except (TypeError, ValueError):
        number, multiplier = 0, 0
    name = str(segment.get('name') or '').upper()
    bed = str(segment.get('bed') or '')
    if 'outside' in bed.lower() or 'miss' in bed.lower():
        return 'MISS'
    if number in (25, 50) or name in ('BULL', 'BULLSEYE', '25', '50', 'SB', 'DB'):
        return 'DB' if multiplier == 2 or number == 50 or name in ('BULLSEYE', '50', 'DB') else 'SB'
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
        if self.settings.get('enabled'):
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
        count, throws = throws_of(data)
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
