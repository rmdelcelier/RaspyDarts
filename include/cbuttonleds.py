"""
LED of the buttons of the cabinet (Paramétrage > LED des boutons) : the LED of the buttons
plugged on the MCP (« Led bouton ... » of Paramétrage des boutons et toys), each with :
  - its state out of games and in a game : as the game decides, always lit, always off ;
  - its blinking, the same choices for all of them :
      blink        blinks without stopping
      count_fixed  blinks N times then stays lit
      count_repeat blinks N times, a pause, again
      on           lit, no blinking
      off          off
    with how long lit, how long off (and the pause). When :
      Joueur suivant (wait) : while the game waits for its button (end of the turn) ;
      the others (press)    : blink and count_repeat as long as the game keeps it lit,
                              count_fixed at each press of its buttons.
The durations were written in the code before (Joueur suivant, put off while waiting : lit
10 ms every 350 ms ; navigation, players : off 10 ms twice) : they are the default values. Kept in
button_leds.json, in the folder of the user.
"""

import json
import os

from include import cpaths

SETTINGS_NAME = 'button_leds.json'

# The LED of the buttons, in the order of the screen
LEDS = ('LIGHT_NEXTPLAYER', 'LIGHT_NAVIGATE', 'LIGHT_VALIDATE', 'LIGHT_BACK', 'LIGHT_PLAYERS')
# When the game makes each of them blink : while waiting for its button, or at the press of its
# buttons (and as long as it is lit)
KIND = {'LIGHT_NEXTPLAYER': 'wait', 'LIGHT_NAVIGATE': 'press', 'LIGHT_PLAYERS': 'press',
        'LIGHT_VALIDATE': 'press', 'LIGHT_BACK': 'press'}
# The buttons whose press makes the LED blink (count_fixed)
PRESSES = {'LIGHT_NAVIGATE': ('PIN_LEFT', 'PIN_RIGHT', 'PIN_UP', 'PIN_DOWN', 'PIN_VALIDATE'),
           'LIGHT_PLAYERS': ('PIN_PLUS', 'PIN_MINUS'),
           'LIGHT_VALIDATE': ('PIN_VALIDATE',),
           'LIGHT_BACK': ('PIN_BACK', 'PIN_CANCEL')}
# States out of games (menus) and in a game : auto (as the game decides), on, off
STATES = ('auto', 'on', 'off')
MODES = ('blink', 'count_fixed', 'count_repeat', 'on', 'off')
# Modes which blink without stopping (while waiting, or as long as it is lit)
CONTINUOUS = ('blink', 'count_repeat')
# Durations lit and off, and the pause, set by a graduated slider (ms)
MIN_MS = 10
MAX_MS = 1000
STEP_MS = 10
MIN_PAUSE = 100
MAX_PAUSE = 5000
STEP_PAUSE = 100
FLASHES = (1, 2, 3, 4, 5, 6, 8, 10)

DEFAULTS = {
    'LIGHT_NEXTPLAYER': {'menus': 'auto', 'game': 'auto', 'mode': 'blink', 'flashes': 3,
                         'on_ms': 10, 'off_ms': 340, 'pause_ms': 1000},
    'LIGHT_NAVIGATE': {'menus': 'auto', 'game': 'auto', 'mode': 'count_fixed', 'flashes': 2,
                       'on_ms': 100, 'off_ms': 10, 'pause_ms': 1000},
    'LIGHT_PLAYERS': {'menus': 'auto', 'game': 'auto', 'mode': 'count_fixed', 'flashes': 2,
                      'on_ms': 100, 'off_ms': 10, 'pause_ms': 1000},
    'LIGHT_VALIDATE': {'menus': 'auto', 'game': 'auto', 'mode': 'on', 'flashes': 2,
                       'on_ms': 100, 'off_ms': 10, 'pause_ms': 1000},
    'LIGHT_BACK': {'menus': 'auto', 'game': 'auto', 'mode': 'on', 'flashes': 2,
                   'on_ms': 100, 'off_ms': 10, 'pause_ms': 1000},
}


def path():
    return os.path.join(cpaths.user_dir(), SETTINGS_NAME)


def defaults():
    return json.loads(json.dumps(DEFAULTS))


def load(logs=None):
    """
    The settings : those of the file over the defaults (a value missing or wrong : the default)
    """
    settings = defaults()
    try:
        with open(path(), encoding='utf-8') as file:
            saved = json.load(file)
    except FileNotFoundError:
        return settings
    except (OSError, ValueError) as error:
        if logs is not None:
            logs.warning(f"LED of the buttons : {path()} not read ({error}), defaults used")
        return settings
    for led, values in settings.items():
        own = saved.get(led) if isinstance(saved, dict) else None
        if not isinstance(own, dict):
            continue
        own = dict(own)
        # Settings of the first version : wait (blink / on / off), flashes (0 : none)
        if 'mode' not in own:
            if own.get('wait') in ('blink', 'on', 'off'):
                own['mode'] = own['wait']
            elif isinstance(own.get('flashes'), int):
                own['mode'] = 'count_fixed' if own['flashes'] > 0 else 'on'
        for key, default in values.items():
            value = own.get(key, default)
            if key in ('menus', 'game') and value in STATES or key == 'mode' and value in MODES:
                values[key] = value
            elif key in ('on_ms', 'off_ms', 'pause_ms', 'flashes') and isinstance(value, int) \
                    and not isinstance(value, bool) and 0 < value <= MAX_PAUSE:
                values[key] = value
    return settings


def save(settings, logs=None):
    """
    The settings written (True : done)
    """
    try:
        os.makedirs(os.path.dirname(path()), exist_ok=True)
        temporary = f'{path()}.tmp'
        with open(temporary, 'w', encoding='utf-8') as file:
            json.dump(settings, file, indent=1)
        os.replace(temporary, path())
        return True
    except OSError as error:
        if logs is not None:
            logs.error(f"LED of the buttons : {path()} not written ({error})")
        return False
