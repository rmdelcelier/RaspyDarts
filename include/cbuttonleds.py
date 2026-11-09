"""
LED of the buttons of the cabinet (Paramétrage > LED des boutons) : the LED of the buttons
plugged on the MCP (« Led bouton ... » of Paramétrage des boutons et toys), each with :
  - its state out of games and in a game : as the game decides, always lit, always off ;
  - its blinking : while the game waits for the button Joueur suivant (that LED), or at each
    press of the buttons (navigation, players + / -) : how long lit, how long off, and for a
    press how many flashes.
The durations were written in the code before (10 ms off every 350 ms, 2 flashes of 10 ms) :
they are the default values. Kept in button_leds.json, in the folder of the user.
"""

import json
import os

from include import cpaths

SETTINGS_NAME = 'button_leds.json'

# The LED of the buttons, in the order of the screen
LEDS = ('LIGHT_NEXTPLAYER', 'LIGHT_NAVIGATE', 'LIGHT_VALIDATE', 'LIGHT_BACK', 'LIGHT_PLAYERS')
# What the game does with each of them : blinking while waiting (Joueur suivant), flashes at
# each press (navigation, players), or only lit and put off
KIND = {'LIGHT_NEXTPLAYER': 'wait', 'LIGHT_NAVIGATE': 'press', 'LIGHT_PLAYERS': 'press',
        'LIGHT_VALIDATE': 'state', 'LIGHT_BACK': 'state'}
# States out of games (menus) and in a game : auto (as the game decides), on, off
STATES = ('auto', 'on', 'off')
# While waiting for Joueur suivant : blinking, lit, off
WAIT_MODES = ('blink', 'on', 'off')
# Durations lit and off, set by a graduated slider (ms)
MIN_MS = 10
MAX_MS = 1000
STEP_MS = 10
FLASHES = (0, 1, 2, 3, 4, 5)

DEFAULTS = {
    'LIGHT_NEXTPLAYER': {'menus': 'auto', 'game': 'auto', 'wait': 'blink', 'on_ms': 340, 'off_ms': 10},
    'LIGHT_NAVIGATE': {'menus': 'auto', 'game': 'auto', 'flashes': 2, 'on_ms': 100, 'off_ms': 10},
    'LIGHT_PLAYERS': {'menus': 'auto', 'game': 'auto', 'flashes': 2, 'on_ms': 100, 'off_ms': 10},
    'LIGHT_VALIDATE': {'menus': 'auto', 'game': 'auto'},
    'LIGHT_BACK': {'menus': 'auto', 'game': 'auto'},
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
        for key, default in values.items():
            value = own.get(key, default)
            if key in ('menus', 'game') and value in STATES or key == 'wait' and value in WAIT_MODES:
                values[key] = value
            elif key in ('on_ms', 'off_ms', 'flashes') and isinstance(value, int) and 0 <= value <= 5000:
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
