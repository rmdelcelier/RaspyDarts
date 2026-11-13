"""
Afficheur (Raspy2DMD) : how the scores are shown on it (its styles of score, Raspy2DMD 1.6.2.3).

- classic : score|X - X - X||R;G;B|O/N (as always)
- modern : score2|... (a camera on the board), its background fond2|
- duck : score1|... (the hunting dog), its background fond1|

The background of the style is sent at the start of a game (fondN|start|O/N : O, the attract
mode of Raspy2DMD as always ; N, the waiting scene of the style instead) and stopped at its end
(fondN|stop). O/N at the end of score : the GIF of the scores and of the special strokes played.

The settings : a general one (every game), then one per type of game (classic, fun, sport) and
one per game, each 'inherit' (as the level above) or its own. Kept in ~/.raspydarts/dmd_scores.json
"""

import json
import os
import re
import subprocess

from include import cpaths

STYLES = ('modern', 'duck', 'classic')
PREFIX = {'classic': 'score', 'modern': 'score2', 'duck': 'score1'}
BACKGROUND = {'modern': 'fond2', 'duck': 'fond1'}
CATEGORIES = ('classic', 'fun', 'sport')
KEYS = ('style', 'gif', 'wait')
INHERIT = 'inherit'
# Modern without GIF ; Balltrap : the hunting dog
GENERAL = {'style': 'modern', 'gif': 'N', 'wait': 'N'}
GAME_DEFAULTS = {'Balltrap': {'style': 'duck'}}
NEEDED = (1, 6, 2, 3)
LOCAL_DIR = '/Raspy2DMD'
VERSION_FILE = '/Raspy2DMD/web/VERSION'
# The values of a dart its styles know (a value unknown : the frame refused)
DART = re.compile(r'^(?:[SDT](?:[1-9]|1\d|20)|SB|DB|MISS|X)$')


def settings_file():
    return os.path.join(cpaths.user_dir(), 'dmd_scores.json')


def load():
    '''
    The settings kept : {'general': {...}, 'types': {category: {...}}, 'games': {game: {...}}}
    '''
    try:
        with open(settings_file(), encoding='utf-8') as source:
            data = json.load(source)
    except (OSError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    for key in ('general', 'types', 'games'):
        if not isinstance(data.get(key), dict):
            data[key] = {}
    return data


def save(data):
    path = settings_file()
    temporary = f'{path}.tmp'
    with open(temporary, 'w', encoding='utf-8') as target:
        json.dump(data, target, ensure_ascii=False, indent=2)
    os.replace(temporary, path)


def category_of(game):
    '''
    The type of a game (classic, fun, sport) : the folder of its file
    '''
    name = str(game).replace(' ', '_')
    for category in CATEGORIES:
        if os.path.isfile(os.path.join(cpaths.ROOT_DIR, 'games', category, f'{name}.py')):
            return category
    return None


def general(data=None):
    data = load() if data is None else data
    values = dict(GENERAL)
    values.update({key: value for key, value in data['general'].items() if key in KEYS and value != INHERIT})
    return values


def of_type(category, data=None):
    '''
    The settings of a type of game : its own, else the general ones
    '''
    data = load() if data is None else data
    values = general(data)
    own = data['types'].get(category) or {}
    values.update({key: value for key, value in own.items() if key in KEYS and value != INHERIT})
    return values


def own_of_game(game, data=None):
    '''
    The settings of a game itself, before those of its type : its defaults (Balltrap), then
    what was chosen for it ('inherit' : as its type)
    '''
    data = load() if data is None else data
    name = str(game).replace(' ', '_')
    values = dict(GAME_DEFAULTS.get(name, {}))
    values.update({key: value for key, value in (data['games'].get(name) or {}).items() if key in KEYS})
    return values


def of_game(game, data=None):
    '''
    The settings used for a game : its own, else those of its type, else the general ones
    '''
    data = load() if data is None else data
    values = of_type(category_of(game), data)
    values.update({key: value for key, value in own_of_game(game, data).items() if value != INHERIT})
    return values


def has_own(level, name, data=None):
    '''
    A type or a game which has settings of its own (shown in green)
    '''
    data = load() if data is None else data
    if level == 'types':
        return any(value != INHERIT for value in (data['types'].get(name) or {}).values())
    own = data['games'].get(str(name).replace(' ', '_'))
    if own is None:
        return str(name).replace(' ', '_') in GAME_DEFAULTS
    return any(value != INHERIT for value in own.values())


def set_value(level, name, key, value):
    '''
    A setting changed : general (name None), of a type, of a game
    '''
    data = load()
    if level == 'general':
        data['general'][key] = value
    else:
        holder = data[level].setdefault(str(name).replace(' ', '_') if level == 'games' else name, {})
        holder[key] = value
    save(data)


# ---------------------------------------------------------------------- Raspy2DMD
def local():
    '''
    Raspy2DMD installed with RaspyDarts on this Raspberry ; else on its own Raspberry (two
    Raspberry : it listens to the MQTT of the borne)
    '''
    return os.path.isdir(LOCAL_DIR)


def version_tuple(version):
    return tuple(int(number) for number in re.findall(r'\d+', str(version)))


def local_version():
    try:
        with open(VERSION_FILE, encoding='utf-8') as source:
            return source.read().strip()
    except OSError:
        return ''


def styles_known():
    '''
    True : the styles can be sent (Raspy2DMD 1.6.2.3 or more here) ; False : too old here ;
    None : not known (on another Raspberry)
    '''
    if not local():
        return None
    version = local_version()
    return bool(version) and version_tuple(version) >= NEEDED


def remote_address():
    '''
    The address of the Raspy2DMD on another Raspberry : the one connected to the MQTT of the
    borne (port 1883) from the network, None : none seen
    '''
    try:
        lines = subprocess.run(['ss', '-tnH', 'state', 'established', '( sport = :1883 )'], capture_output=True,
                               text=True, timeout=5, check=False).stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        return None
    for line in lines:
        parts = line.split()
        if len(parts) < 4:
            continue
        peer = parts[-1].rsplit(':', 1)[0].strip('[]')
        if peer.startswith('::ffff:'):
            peer = peer[len('::ffff:'):]
        if re.match(r'^\d+\.\d+\.\d+\.\d+$', peer) and not peer.startswith('127.'):
            return peer
    return None


def dart_value(touch):
    '''
    A dart as the styles know it (MISS : a dart out of the board)
    '''
    value = str(touch or 'X').strip().upper()
    if value in ('', 'NONE', '0', 'S0', 'OUT', 'BOUNCE'):
        return 'MISS'
    if re.match(r'^E(?:[1-9]|1\d|20)$', value):
        # The other part of a single (inner / outer single) : a single
        value = 'S' + value[1:]
    return value if DART.match(value) else 'MISS'
