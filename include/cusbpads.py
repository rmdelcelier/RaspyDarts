"""
USB pads : small programmable keyboards of keys and knobs (1189:8890, chip CH57x, sold as
« MiniKeyboard »). Bought, all their keys send the same letter (C, the cheat of a game) : the
game programs them with codes of their own, then reads them directly (evdev, taken for itself :
nothing reaches the desktop) and turns each key into a button of the cabinet (BTN_UP,
BTN_VALIDATE...), the one chosen for the menus or the one chosen for a game.

Codes written in the pad : key n (1 to 12) = F12 + n ; knobs : the 9 keys after F24 (Open,
Help... Copy, unknown on the keyboards of today), three each (turned left, pressed, turned
right). One code alone for each element : with Ctrl + F13..., a knob turned fast sent some of
its codes without Ctrl, read as keys (Joueur suivant counted 3 Miss). They do not depend on the
number of keys : a key keeps its name when another one is added.

Programming protocol : the one of ch57x-keyboard-tool (github.com/kriomant/ch57x-keyboard-tool,
MIT licence), model 8890. The pad tells neither its keys nor its settings : the numbers of keys
and knobs are given by the user. No serial number either : two pads are told apart by the USB
port they are plugged in.

Gamepads and « zero delay » cards (arcade buttons in USB, seen as a joystick) : read the same
way, nothing to program. Their buttons (j + code of the system), their cross or stick (up,
down, left, right) ; their settings kept by model (joy-vendor-product : any port, the same for
two gamepads alike). A press counts once, only the directions held repeat (as the buttons of
the MCP, include/cgpio_extender.py).
"""

import json
import os
import queue
import select
import subprocess
import time
from threading import Thread, Lock

from include import cpaths

# Pads known (vendor, product)
SUPPORTED = {(0x1189, 0x8890)}
MAX_KEYS = 12
MAX_KNOBS = 3
KNOB_ACTIONS = ('left', 'press', 'right')
# Columns of a knob on the screen : its codes, and its press held (not a code : measured here)
KNOB_ELEMENTS = ('left', 'press', 'long', 'right')
# Held this long : a long press
LONG_PRESS = 0.6
# Knob turned while a value is typed (Screen.input_value_item) : the notches in this time say how
# fast it turns, the steps of a number grow with it
SPEED_TIME = 0.5
SPEED_STEPS = ((12, 100), (5, 10))
SETTINGS_NAME = 'usb_pads.json'
# Pads plugged or unplugged : seen within this time
SCAN_DELAY = 2
# Screen of the settings : an element of a pad held this long (s) goes to Retour / Enregistrer
# (a pad with a knob only could not leave it : its presses are shown, not used)
EXIT_HOLD = 3.0

# Buttons a key can be : (button, text, where it is offered : menus, game)
ACTIONS = [('', 'usb-pads-none-action', True, True),
           ('BTN_VALIDATE', 'usb-pads-validate', True, False),
           ('BTN_BACK', 'usb-pads-back', True, True),
           ('BTN_UP', 'usb-pads-up', True, False),
           ('BTN_DOWN', 'usb-pads-down', True, False),
           ('BTN_LEFT', 'usb-pads-left', True, False),
           ('BTN_RIGHT', 'usb-pads-right', True, False),
           ('BTN_PLUS', 'usb-pads-plus', True, False),
           ('BTN_MINUS', 'usb-pads-minus', True, False),
           ('BTN_NEXTPLAYER', 'usb-pads-nextplayer', False, True),
           ('MISS', 'usb-pads-miss', False, True),
           ('BTN_GAMEBUTTON', 'usb-pads-stop', False, True),
           ('BTN_VOLUME_UP', 'usb-pads-volume-up', True, True),
           ('BTN_VOLUME_DOWN', 'usb-pads-volume-down', True, True),
           ('BTN_VOLUME_MUTE', 'usb-pads-volume-mute', True, True),
           ('SYSTEM_VOLUME_UP', 'usb-pads-system-volume-up', True, True),
           ('SYSTEM_VOLUME_DOWN', 'usb-pads-system-volume-down', True, True),
           # Music player (include/cmusic.py) : done wherever the game is
           ('BTN_MUSIC_PLAY', 'usb-pads-music-play', True, True),
           ('BTN_MUSIC_NEXT', 'usb-pads-music-next', True, True),
           ('BTN_MUSIC_PREVIOUS', 'usb-pads-music-previous', True, True),
           ('BTN_MUSIC_VOLUME_UP', 'usb-pads-music-volume-up', True, True),
           ('BTN_MUSIC_VOLUME_DOWN', 'usb-pads-music-volume-down', True, True),
           ('BTN_MUSIC_STOP', 'usb-pads-music-stop', True, True)]
# Volume of the system (not the one of the game) : changed by the pad itself, the game is not
# told. PipeWire (Trixie), else ALSA
SYSTEM_VOLUME = {'SYSTEM_VOLUME_UP': '5%+', 'SYSTEM_VOLUME_DOWN': '5%-'}

# Buttons given to a pad never set : keys, then each knob (left, press, right)
DEFAULT_KEYS = {'menus': ['BTN_BACK', 'BTN_UP', 'BTN_DOWN', 'BTN_VALIDATE'],
                'game': ['BTN_BACK', 'MISS', 'BTN_NEXTPLAYER', 'BTN_GAMEBUTTON']}
DEFAULT_KNOB = {'menus': ['BTN_LEFT', 'BTN_VALIDATE', 'BTN_BACK', 'BTN_RIGHT'],
                'game': ['BTN_VOLUME_DOWN', 'BTN_VOLUME_MUTE', '', 'BTN_VOLUME_UP']}

# Codes of the keyboard (HID usage) : F13 for the keys, the 9 ones after F24 for the knobs ; the
# codes the system gives for the latter (evdev)
# Gamepads and zero delay cards : buttons of a joystick or a gamepad (BTN_JOYSTICK...BTN_THUMBR,
# then BTN_TRIGGER_HAPPY...) ; a stick turned beyond half of its way is a direction, back under
# a third it is released ; a direction held repeats (as the arrows of the MCP)
JOYSTICK_BUTTONS = (range(0x120, 0x140), range(0x2c0, 0x2e8))
DIRECTIONS = ('up', 'down', 'left', 'right')
STICK_ON = 0.5
STICK_OFF = 0.3
REPEAT_DELAY = 0.5
REPEAT_EVERY = 0.15
# Buttons given to a gamepad never set : directions, then its buttons in their order
DEFAULT_JOYSTICK = {'menus': (['BTN_UP', 'BTN_DOWN', 'BTN_LEFT', 'BTN_RIGHT'], ['BTN_VALIDATE', 'BTN_BACK']),
                    'game': (['', '', '', ''], ['BTN_NEXTPLAYER', 'BTN_BACK', 'MISS'])}

HID_F13 = 0x68
HID_KNOBS = 0x74
KNOB_KEYS = ('KEY_OPEN', 'KEY_HELP', 'KEY_PROPS', 'KEY_FRONT', 'KEY_STOP', 'KEY_AGAIN', 'KEY_UNDO',
             'KEY_CUT', 'KEY_COPY')


SHARED = None


def shared(logs):
    """
    The reader of the pads, one for the game : created again (a first creation of the
    Raspberry failed), a second one would find the pads already taken
    """
    global SHARED    # pylint: disable=global-statement
    if SHARED is None:
        SHARED = UsbPads(logs)
    return SHARED


def actions(context):
    """
    Buttons offered in this context ('menus' or 'game')
    """
    return [action for action in ACTIONS if action[2 if context == 'menus' else 3]]


def elements(keys, knobs):
    """
    Names of the elements of a pad : k1, k2... then m1-left, m1-press, m1-long, m1-right...
    """
    return [f'k{key}' for key in range(1, keys + 1)] + \
           [f'm{knob}-{action}' for knob in range(1, knobs + 1) for action in KNOB_ELEMENTS]


def default_settings(keys=3, knobs=1):
    """
    Settings of a pad never set
    """
    settings = {'keys': keys, 'knobs': knobs}
    for context in ('menus', 'game'):
        defaults = DEFAULT_KEYS[context]
        settings[context] = {f'k{key}': defaults[key - 1] if key <= len(defaults) else ''
                             for key in range(1, keys + 1)}
        for knob in range(1, knobs + 1):
            for action, button in zip(KNOB_ELEMENTS, DEFAULT_KNOB[context]):
                settings[context][f'm{knob}-{action}'] = button
    return settings


def is_joystick_id(port):
    """
    True for the name of a gamepad (joy-vendor-product), False for the port of a pad
    """
    return str(port).startswith('joy-')


def joystick_buttons(device):
    """
    Codes of the buttons of a gamepad or a zero delay card, sorted ; [] for another device
    (a touch screen or a mouse : not a gamepad)
    """
    from evdev import ecodes    # pylint: disable=import-outside-toplevel
    keys = device.capabilities().get(ecodes.EV_KEY, [])
    if ecodes.BTN_TOUCH in keys or ecodes.BTN_LEFT in keys:
        return []
    return sorted(code for code in keys if any(code in codes for codes in JOYSTICK_BUTTONS))


def default_joystick(name, buttons):
    """
    Settings of a gamepad never set : its directions and its buttons (DEFAULT_JOYSTICK)
    """
    names = list(DIRECTIONS) + [f'j{code}' for code in buttons]
    settings = {'type': 'joystick', 'name': name, 'elements': names}
    for context, (directions, firsts) in DEFAULT_JOYSTICK.items():
        given = list(directions) + list(firsts)
        settings[context] = {element: given[index] if index < len(given) else ''
                             for index, element in enumerate(names)}
    return settings


def elements_of(pad):
    """
    Names of the elements of a pad or of a gamepad (settings of the screen)
    """
    if pad.get('type') == 'joystick':
        return list(pad['elements'])
    return elements(pad['keys'], pad['knobs'])


def element_of(code):
    """
    Element of a pad which sent this code (evdev), None for a code not written by the game
    """
    from evdev import ecodes    # pylint: disable=import-outside-toplevel
    if ecodes.KEY_F13 <= code <= ecodes.KEY_F24:
        return f'k{code - ecodes.KEY_F13 + 1}'
    knobs = [getattr(ecodes, name) for name in KNOB_KEYS]
    if code in knobs:
        index = knobs.index(code)
        return f'm{index // 3 + 1}-{KNOB_ACTIONS[index % 3]}'
    return None


def port_of(phys):
    """
    USB port of an input device : usb-3f980000.usb-1.3/input0 -> 1.3
    """
    return phys.split('/')[0].rsplit('-', 1)[-1]


class UsbPads:
    """
    The pads plugged : read in a thread, their keys turned into buttons
    """

    def __init__(self, logs):
        self.logs = logs
        self.file = os.path.join(cpaths.user_dir(), SETTINGS_NAME)
        self.settings = self.load()
        # 'menus' or 'game' : set by the reading of the inputs (Raspberry.read_inputs)
        self.context = 'menus'
        # Screen of the settings opened : the keys are given as they are (USBPAD:port:element)
        self.capture = False
        # A value typed (see set_value_input) ; presses of knobs held (path -> [element, port,
        # start, long press given]) ; times of the last notches turned
        self.value_input = False
        self.held = {}
        # Screen of the settings : the element held on each pad [start, port, given]
        self.capture_held = {}
        self.turns = []
        self.inputs = queue.Queue()
        self.devices = {}       # path -> (device, port)
        self.ports = {}         # port -> name of the pad (joy-vendor-product for a gamepad)
        # Gamepads : path -> their buttons, the bounds of their axes, the direction of each axis ;
        # the directions held (path -> {direction: [since, last given, port]})
        self.joysticks = {}
        self.directions = {}
        self.lock = Lock()
        self.available = True
        try:
            import evdev    # pylint: disable=import-outside-toplevel,unused-import
        except ImportError:
            self.logs.warning("USB pads : python3-evdev missing")
            self.available = False
            return
        Thread(target=self.run, daemon=True).start()

    def load(self):
        """
        Settings of the pads, by USB port
        """
        try:
            with open(self.file, encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}
        except (OSError, ValueError) as error:
            self.logs.error(f"USB pads : {self.file} not read : {error}")
            return {}

    def save(self, settings):
        """
        Settings of the pads written (all of them)
        """
        with self.lock:
            self.settings = settings
        with open(self.file, 'w', encoding='utf-8') as file:
            json.dump(settings, file, indent=1)

    def plugged(self):
        """
        Ports of the pads plugged, sorted
        """
        with self.lock:
            return sorted(set(self.ports))

    def settings_of(self, port):
        """
        Settings of the pad of this port (or of this gamepad). A pad moved to another port
        keeps those of the only pad set, if there is one
        """
        with self.lock:
            if port in self.settings:
                return self.settings[port]
            if is_joystick_id(port):
                buttons = next((info['buttons'] for info in self.joysticks.values() if info['id'] == port), [])
                return default_joystick(self.ports.get(port, port), buttons)
            pads = [settings for name, settings in self.settings.items() if not is_joystick_id(name)]
            if len(pads) == 1:
                return pads[0]
        return default_settings()

    def take(self):
        """
        Button of the next key of a pad, None if none
        """
        try:
            return self.inputs.get_nowait()
        except queue.Empty:
            return None

    def run(self):
        """
        Thread : pads looked for every few seconds, their keys read meanwhile
        """
        next_scan = 0
        while True:
            if time.monotonic() >= next_scan:
                self.scan()
                next_scan = time.monotonic() + SCAN_DELAY
            with self.lock:
                devices = {device.fd: device for device, _port in self.devices.values()}
            if not devices:
                time.sleep(SCAN_DELAY)
                continue
            # A press held : woken up when it becomes a long one ; a direction held, when it repeats
            wait = SCAN_DELAY
            if self.held:
                wait = max(0.01, min(LONG_PRESS - (time.monotonic() - held[2]) for held in list(self.held.values())))
            if self.capture_held:
                wait = max(0.01, min([wait] + [EXIT_HOLD - (time.monotonic() - held[0])
                                                for held in list(self.capture_held.values()) if not held[2]]))
            repeat = self.next_repeat()
            if repeat is not None:
                wait = max(0.01, min(wait, repeat))
            try:
                ready, _w, _x = select.select(list(devices), [], [], min(wait, SCAN_DELAY))
            except (OSError, ValueError):
                # A pad unplugged meanwhile
                self.scan()
                continue
            for descriptor in ready:
                self.read(devices[descriptor])
            self.long_presses()
            self.repeat_directions()

    def scan(self):
        """
        Pads plugged : the new ones taken for the game, the ones unplugged forgotten
        """
        import evdev    # pylint: disable=import-outside-toplevel
        with self.lock:
            known = dict(self.devices)
        paths = set(evdev.list_devices())
        for path in list(known):
            if path not in paths:
                self.forget(path)
        for path in paths - set(known):
            try:
                device = evdev.InputDevice(path)
            except OSError:
                continue
            buttons = []
            if (device.info.vendor, device.info.product) not in SUPPORTED:
                buttons = joystick_buttons(device)
                if not buttons:
                    device.close()
                    continue
            try:
                # Its keys for the game only (not typed on the desktop as well)
                device.grab()
            except OSError as error:
                self.logs.warning(f"USB pad {path} not taken : {error}")
            if buttons:
                port = f'joy-{device.info.vendor:04x}-{device.info.product:04x}'
                self.joysticks[path] = {'id': port, 'buttons': buttons, 'axes': self.axes_of(device), 'state': {}}
            else:
                port = port_of(device.phys)
            with self.lock:
                self.devices[path] = (device, port)
                self.ports[port] = device.name
            self.logs.info(f"USB {'gamepad' if buttons else 'pad'} plugged : {device.name} as {port} ({path})")

    def forget(self, path):
        """
        Pad unplugged
        """
        self.held.pop(path, None)
        self.joysticks.pop(path, None)
        self.directions.pop(path, None)
        with self.lock:
            device, port = self.devices.pop(path)
            if port not in [other for _d, other in self.devices.values()]:
                self.ports.pop(port, None)
        try:
            device.close()
        except OSError:
            pass
        self.logs.info(f"USB pad unplugged : port {port}")

    def read(self, device):
        """
        Keys of a pad, turned into buttons
        """
        from evdev import ecodes    # pylint: disable=import-outside-toplevel
        try:
            events = list(device.read())
        except OSError:
            self.forget(device.path)
            return
        with self.lock:
            port = self.devices.get(device.path, (None, None))[1]
        if device.path in self.joysticks:
            self.read_joystick(device.path, port, events)
            return
        for event in events:
            # Pressed or released (not repeated by the system)
            if event.type != ecodes.EV_KEY or event.value == 2:
                continue
            element = element_of(event.code)
            if event.value == 0:
                self.released(device.path, element)
                continue
            if self.capture:
                # Screen of the settings : the key as it is (shown lit), a pad not programmed
                # by the game too ; the press of a knob held : its long press lit too ; any
                # element held EXIT_HOLD : Retour / Enregistrer reached
                self.inputs.put(f"USBPAD:{port}:{element or 'unknown'}")
                self.capture_held[device.path] = [time.monotonic(), port, False]
                if element is not None and element.endswith('-press'):
                    self.held[device.path] = [element, port, time.monotonic(), False]
                continue
            if element is None:
                continue
            if self.value_input and element.startswith('m'):
                # A value typed : the knob changes it (Screen.input_value_item)
                self.knob_value(device.path, port, element)
            elif element.endswith('-press') and self.button(port, element.replace('-press', '-long')):
                # Its long press is set : the short one is known when released
                self.held[device.path] = [element, port, time.monotonic(), False]
            else:
                self.press(port, element)

    @staticmethod
    def axes_of(device):
        """
        Axes of a gamepad giving directions : code -> (minimum, maximum). Its cross (hat) and
        its first stick (or the joystick of a zero delay card)
        """
        from evdev import ecodes    # pylint: disable=import-outside-toplevel
        axes = {}
        for code, info in device.capabilities().get(ecodes.EV_ABS, []):
            if code in (ecodes.ABS_X, ecodes.ABS_Y, ecodes.ABS_HAT0X, ecodes.ABS_HAT0Y) and info.max > info.min:
                axes[code] = (info.min, info.max)
        return axes

    def read_joystick(self, path, port, events):
        """
        Buttons and directions of a gamepad : given once when pressed, the directions held repeat
        """
        from evdev import ecodes    # pylint: disable=import-outside-toplevel
        info = self.joysticks[path]
        for event in events:
            if event.type == ecodes.EV_KEY and event.value == 1 and \
                    any(event.code in codes for codes in JOYSTICK_BUTTONS):
                self.give(port, f'j{event.code}')
            elif event.type == ecodes.EV_ABS and event.code in info['axes']:
                low, high = info['axes'][event.code]
                # -1 .. 1 around the middle of the axis
                value = (2 * (event.value - low) / (high - low)) - 1
                vertical = event.code in (ecodes.ABS_Y, ecodes.ABS_HAT0Y)
                before = info['state'].get(event.code)
                if value >= STICK_ON:
                    now = 'down' if vertical else 'right'
                elif value <= -STICK_ON:
                    now = 'up' if vertical else 'left'
                elif abs(value) < STICK_OFF:
                    now = None
                else:
                    now = before
                if now == before:
                    continue
                info['state'][event.code] = now
                held = self.directions.setdefault(path, {})
                if before is not None:
                    held.pop(before, None)
                if now is not None:
                    held[now] = [time.monotonic(), time.monotonic(), port]
                    self.give(port, now)

    def give(self, port, element):
        """
        An element of a gamepad pressed : shown on the screen of the settings, else its button
        """
        if self.capture:
            self.inputs.put(f"USBPAD:{port}:{element}")
        else:
            self.press(port, element)

    def next_repeat(self):
        """
        Seconds until a direction held repeats, None if none is held
        """
        now = time.monotonic()
        waits = [max(REPEAT_DELAY - (now - since), REPEAT_EVERY - (now - last))
                 for held in list(self.directions.values()) for since, last, _port in list(held.values())]
        return min(waits) if waits else None

    def repeat_directions(self):
        """
        Directions held long enough : given again (to go down a list), not on the screen of the
        settings
        """
        if self.capture:
            return
        now = time.monotonic()
        for held in list(self.directions.values()):
            for times in list(held.values()):
                since, last, port = times
                if now - since >= REPEAT_DELAY and now - last >= REPEAT_EVERY:
                    times[1] = now
                    self.press(port, [name for name, value in held.items() if value is times][0])

    def button(self, port, element):
        """
        Button given to this element of the pad of this port, in the menus or in a game
        """
        settings = self.settings_of(port)
        return settings.get('game' if self.context == 'game' else 'menus', {}).get(element, '')

    def press(self, port, element):
        """
        An element of a pad used : its button given to the game, or the volume of the system
        """
        button = self.button(port, element)
        self.logs.debug(f"USB pad {port} : {element} ({self.context}) -> {button or 'nothing'}")
        if button in SYSTEM_VOLUME:
            self.system_volume(SYSTEM_VOLUME[button])
        elif button:
            self.inputs.put(button)

    def released(self, path, element):
        """
        An element released : the short press of a knob whose long press is set
        """
        self.capture_held.pop(path, None)
        held = self.held.get(path)
        if held is None or held[0] != element:
            return
        del self.held[path]
        if held[3] or self.capture:
            # Long press already given
            return
        if self.value_input:
            self.inputs.put('KNOB_PRESS')
        else:
            self.press(held[1], element)

    def long_presses(self):
        """
        Presses held long enough : their long press given at once (not when released) ; on the
        screen of the settings, an element held EXIT_HOLD : USBPAD_HOLD:port
        """
        now = time.monotonic()
        for held in list(self.capture_held.values()):
            if self.capture and not held[2] and now - held[0] >= EXIT_HOLD:
                held[2] = True
                self.inputs.put(f"USBPAD_HOLD:{held[1]}")
        for path, held in list(self.held.items()):
            element, port, start, given = held
            if given or now - start < LONG_PRESS:
                continue
            held[3] = True
            long_press = element.replace('-press', '-long')
            if self.capture:
                self.inputs.put(f"USBPAD:{port}:{long_press}")
            elif self.value_input:
                self.inputs.put('KNOB_LONG')
            else:
                self.press(port, long_press)

    def knob_value(self, path, port, element):
        """
        Knob while a value is typed : KNOB_RIGHT:step / KNOB_LEFT:step (the step grows when it
        turns fast), its press KNOB_PRESS, held KNOB_LONG
        """
        if element.endswith('-press'):
            self.held[path] = [element, port, time.monotonic(), False]
            return
        now = time.monotonic()
        self.turns = [moment for moment in self.turns if now - moment < SPEED_TIME] + [now]
        step = next((size for count, size in SPEED_STEPS if len(self.turns) >= count), 1)
        self.inputs.put(f"KNOB_{'RIGHT' if element.endswith('-right') else 'LEFT'}:{step}")

    def set_value_input(self, typing):
        """
        A value typed (Screen.input_value_item) or no more : the knob changes it
        """
        self.value_input = typing
        self.turns = []

    def system_volume(self, step):
        """
        Volume of the system changed (5%+ or 5%-), 100 % at most
        """
        for command in (['wpctl', 'set-volume', '-l', '1.0', '@DEFAULT_AUDIO_SINK@', step],
                        ['amixer', '-q', 'sset', 'Master', step]):
            try:
                if subprocess.run(command, capture_output=True, timeout=3, check=False).returncode == 0:
                    self.logs.debug(f"USB pads : volume of the system {step} ({command[0]})")
                    return
            except (OSError, subprocess.TimeoutExpired):
                continue
        self.logs.warning(f"USB pads : volume of the system not changed ({step})")

    def set_capture(self, capture):
        """
        Screen of the settings opened or closed : keys pressed before forgotten
        """
        self.capture = capture
        self.capture_held = {}
        while self.take() is not None:
            pass

    def program(self, port, keys, knobs):
        """
        Codes of the game written in the pad of this port. Returns None, or the error
        """
        try:
            import usb.core    # pylint: disable=import-outside-toplevel
            import usb.util    # pylint: disable=import-outside-toplevel
        except ImportError:
            return 'python3-usb'
        found = None
        for vendor, product in SUPPORTED:
            for device in usb.core.find(find_all=True, idVendor=vendor, idProduct=product):
                if '.'.join(str(number) for number in (device.port_numbers or ())) == port:
                    found = device
        if found is None:
            return 'not found'
        try:
            self.write_codes(found, keys, knobs)
        except usb.core.USBError as error:
            self.logs.error(f"USB pad {port} not programmed : {error}")
            return str(error)
        self.logs.info(f"USB pad {port} programmed : {keys} keys, {knobs} knobs")
        return None

    @staticmethod
    def write_codes(device, keys, knobs):
        """
        Messages of the model 8890 (64 bytes, interface 1, endpoint 2), first layer :
        for each element, start, empty key, its key, end
        """
        import usb.util    # pylint: disable=import-outside-toplevel
        interface, endpoint, layer = 1, 0x02, 1
        if device.is_kernel_driver_active(interface):
            device.detach_kernel_driver(interface)
        usb.util.claim_interface(device, interface)

        def send(message):
            device.write(endpoint, bytes(message) + bytes(64 - len(message)), 1000)

        try:
            send([])
            codes = [(key, HID_F13 + key - 1) for key in range(1, keys + 1)]
            for knob in range(knobs):
                # Identifiers 13 + 3 n : left, press, right
                codes += [(13 + 3 * knob + action, HID_KNOBS + 3 * knob + action) for action in range(3)]
            for identifier, code in codes:
                send([0x03, 0xfe, layer, 0x01, 0x01])
                send([0x03, identifier, (layer << 4) | 0x01, 1, 0])
                send([0x03, identifier, (layer << 4) | 0x01, 1, 1, 0, code])
                send([0x03, 0xaa, 0xaa])
        finally:
            usb.util.release_interface(device, interface)
