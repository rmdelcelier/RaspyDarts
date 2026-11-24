"""
Menus described by files (docs/menu/menus.md) : the defaults of the game, then the menus of
the theme chosen (themes/<theme>/menu/menus.yaml). What a menu shows, in which order, with which look,
which shortcuts, and the action of each button
"""

import os
import shutil
import time

from include import cpaths

try:
    import yaml
    LOADER = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
except ImportError:    # the menus of the game (defaults.yaml) cannot be read either
    yaml = None
    LOADER = None

DEFAULTS_FILE = os.path.join(cpaths.ROOT_DIR, 'menus', 'defaults.yaml')
FILE_NAME = 'menus.yaml'
# The menus of a theme : in its folder menu (themes/<theme>/menu/menus.yaml), its images in
# its folder images ; several themes, several menus
THEME_FILE = os.path.join('menu', FILE_NAME)

# Actions known by the game, and what the menu returns to the main loop for each of them.
# A file cannot invent an action : an unknown one is ignored
# Buttons of the files which replace older ones : a file which still has one of the older ones
# keeps it (it opens the same screen), the new one is not added to it
REPLACES = {'network': ('netjoin', 'netcreate')}

ACTIONS = {
    'local_game': 'local',
    'network': 'network',
    # Panel of the players online (a button placed by the editor) : validated, Partie en réseau
    'online_players': 'network',
    # Before the online games screen (a file may still have them) : they open it as well
    'network_join': 'netjoin',
    'network_create': 'netcreate',
    'trophies': 'trophees',
    'gallery': 'gallery',
    # Lecteur MP3 (include/cmusic.py)
    'mp3': 'mp3',
    'infos': 'infos',
    'restart': 'restart',
    'desktop': 'quit',
    'shutdown': 'shutdown',
    'favorite_players': 'firstnames',
    'favorite_games': 'games',
    'favorite_servers': 'servers',
    'customization': 'customization',
    'animations': 'animations',
    'players_bank': 'firstname-bank',
    'backups': 'backups',
    'exhibition': 'exhibition',
    'raspy2dmd': 'raspy2dmd',
    # Autodarts : its cameras read the darts (include/cautodartsmenu.py)
    'autodarts': 'autodarts',
    'edit_screens': 'edit-screens',
    'usb_pads': 'usb-pads',
    'button_leds': 'button-leds',
    'coins': 'coins',
    'update': 'update',
    # A network game waiting in the background : its screen again (include/cnetwait.py)
    'netresume': 'netresume',
    'back': 'escape',
    'setup_buttons': 'setup-buttons',
    'setup_pins_leds': 'setup-pinleds',
    'setup_leds': 'setup-leds',
    'setup_segment_colors': 'setup-couleurs-segments',
    'setup_camera': 'setup-cam',
    'test_buttons': 'test-buttons',
    'test_target': 'test-target',
    'test_toys': 'test-toys',
    'reset': 'reset',
}
# Menus opened by the main loop : what it is given for each of them
MENU_RESULTS = {'settings': 'setup'}
ACTION_PREFIXES = ('menu:', 'category:', 'game:', 'favorite:')
# Categories of games : what the main loop is given (category:<name>)
CATEGORY_RESULTS = {'favorites': 'favoris'}

# Keys of the file (btn:..., dart:...) : names given by the inputs of the game
BUTTON_KEYS = {'btn:up': 'BTN_UP', 'btn:down': 'BTN_DOWN', 'btn:left': 'BTN_LEFT', 'btn:right': 'BTN_RIGHT',
               'btn:validate': 'BTN_VALIDATE', 'btn:back': 'BTN_BACK', 'btn:cancel': 'BTN_CANCEL',
               'btn:plus': 'BTN_PLUS', 'btn:minus': 'BTN_MINUS', 'btn:nextplayer': 'BTN_NEXTPLAYER',
               'btn:game': 'BTN_GAMEBUTTON'}


# Paramétrage of the theme « sombre » as delivered (3 columns, each button placed by hand,
# 03/11/2026) : moved to 4 columns arranged by themselves, with LED des boutons (4.6.4) ; a
# page changed in the editor of the screens is left as it is
SHIPPED_SETTINGS_PLACES = {
    'setup-buttons': (0.1427, 0.1546), 'setup-pinleds': (0.3828, 0.1546), 'setup-leds': (0.6229, 0.1546),
    'setup-couleurs-segments': (0.1427, 0.338), 'setup-cam': (0.3828, 0.338), 'usb-pads': (0.6229, 0.338),
    'test-buttons': (0.6229, 0.5213), 'test-target': (0.1427, 0.5213), 'test-toys': (0.3828, 0.5213),
    'reset': (0.8531, 0.8787), 'coins': (0.3828, 0.7046)}
SETTINGS_ORDER = ('setup-buttons', 'setup-pinleds', 'setup-leds', 'setup-couleurs-segments', 'setup-cam', 'usb-pads',
                  'coins', 'button-leds', 'test-buttons', 'test-target', 'test-toys', 'reset')


def migrate_settings_page(logs, themes_dir):
    '''
    The page Paramétrage of the themes (themes/<theme>/menu/menus.yaml) still as delivered :
    4 columns arranged by themselves, the button LED des boutons before the tests (Réinitialiser
    keeps its place). The file before kept as menus.yaml.avant-4-colonnes. Done once : the page
    changed is no longer the delivered one
    '''
    if yaml is None or not os.path.isdir(themes_dir):
        return
    for theme in sorted(os.listdir(themes_dir)):
        path = os.path.join(themes_dir, theme, THEME_FILE)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding='utf-8') as file:
                content = yaml.safe_load(file) or {}
            menu = (content.get('menus') or {}).get('settings')
            if not isinstance(menu, dict) or not isinstance(menu.get('buttons'), list):
                continue
            buttons = [button for button in menu['buttons'] if isinstance(button, dict)]
            placed = {str(button.get('id')): button.get('place') for button in buttons if not button.get('footer')}
            delivered = set(placed) == set(SHIPPED_SETTINGS_PLACES) and all(
                isinstance(place, dict) and (place.get('x'), place.get('y')) == SHIPPED_SETTINGS_PLACES[ident]
                for ident, place in placed.items())
            if not delivered:
                continue
            by_id = {str(button.get('id')): dict(button) for button in buttons}
            used = {button.get('shortcut') for button in buttons if button.get('shortcut')}
            leds = {'id': 'button-leds', 'action': 'button_leds', 'text': 'button-leds'}
            free = next((key for key in ('F10', 'F11', 'F12') if key not in used), None)
            if free:
                leds['shortcut'] = free
            by_id['button-leds'] = leds
            ordered = []
            for ident in SETTINGS_ORDER:
                button = by_id.pop(ident)
                if ident != 'reset':
                    button.pop('place', None)
                ordered.append(button)
            # The buttons at the bottom (Retour) after the others
            ordered += [button for button in by_id.values()]
            menu['buttons'] = ordered
            menu['columns'] = 4
            menu['layout'] = 'tiles'
            shutil.copyfile(path, f'{path}.avant-4-colonnes')
            temporary = f'{path}.tmp'
            with open(temporary, 'w', encoding='utf-8') as file:
                yaml.safe_dump(content, file, allow_unicode=True, sort_keys=False, default_flow_style=False)
            os.replace(temporary, path)
            logs.info(f"Menus : Paramétrage of the theme {theme} moved to 4 columns with LED des boutons ({path})")
        except Exception as error:    # pylint: disable=broad-except
            logs.warning(f"Menus : Paramétrage of the theme {theme} not moved to 4 columns ({error})")


def free_place(shown, gap, beside=None):
    '''
    A free place for a new button among buttons placed by hand (parts of the screen) : of the
    size of the one before it (else of the last one), beside it (right, below, left, above),
    else beside another one ; inside the screen, between the title and the buttons at the
    bottom, over none. None : no room
    '''
    def box(button):
        place = button.get('place') if isinstance(button, dict) else None
        try:
            return tuple(float(place[key]) for key in ('x', 'y', 'width', 'height'))
        except (TypeError, KeyError, ValueError):
            return None
    boxes = [box(button) for button in shown]
    if not boxes or any(item is None for item in boxes):
        return None
    model = box(beside) if beside is not None else boxes[-1]
    width, height = model[2], model[3]
    gap = gap if isinstance(gap, dict) else {}
    try:
        gap_x, gap_y = float(gap.get('x', 0.005)), float(gap.get('y', 0.005))
    except (TypeError, ValueError):
        gap_x, gap_y = 0.005, 0.005
    top, bottom, side = 0.12, 0.88, 0.01

    def free(x, y):
        if x < side or y < top or x + width > 1 - side or y + height > bottom:
            return False
        return all(x + width <= other[0] + 1e-4 or other[0] + other[2] <= x + 1e-4 or
                   y + height <= other[1] + 1e-4 or other[1] + other[3] <= y + 1e-4 for other in boxes)
    anchors = ([model] if beside is not None else []) + sorted(boxes, key=lambda item: (item[1], item[0]))
    for anchor in anchors:
        for x, y in ((anchor[0] + anchor[2] + gap_x, anchor[1]), (anchor[0], anchor[1] + anchor[3] + gap_y),
                     (anchor[0] - width - gap_x, anchor[1]), (anchor[0], anchor[1] - height - gap_y)):
            if free(x, y):
                return {'x': round(x, 4), 'y': round(y, 4), 'width': round(width, 4), 'height': round(height, 4)}
    # A grid whose last row is not full (a button alone, centred) : its buttons on the columns
    # of the rows above, the new one in the column left (the places of the others shown
    # changed, not their file)
    same = [button for button, item in zip(shown, boxes) if abs(item[2] - width) < 1e-3 and abs(item[3] - height) < 1e-3]
    if same:
        last_y = max(box(button)[1] for button in same)
        row = sorted((button for button in same if abs(box(button)[1] - last_y) < 1e-3), key=lambda button: box(button)[0])
        # The columns : those of the rows above
        columns = sorted({round(box(button)[0], 4) for button in same if button not in row})
        if 2 <= len(columns) and len(row) < len(columns):
            others = [box(button) for button in shown if button not in row]
            places = [(x, last_y) for x in columns]
            if all(all(x + width <= other[0] + 1e-4 or other[0] + other[2] <= x + 1e-4 or
                       y + height <= other[1] + 1e-4 or other[1] + other[3] <= y + 1e-4 for other in others)
                   for x, y in places):
                for button, (x, y) in zip(row, places):
                    button['place'] = dict(button['place'], x=x, y=y)
                x, y = places[len(row)]
                return {'x': x, 'y': round(y, 4), 'width': round(width, 4), 'height': round(height, 4)}
    return None


def merge(base, top):
    '''
    The values of top over the ones of base : dictionaries key by key, lists replaced,
    None removes the value
    '''
    if not isinstance(base, dict) or not isinstance(top, dict):
        return top
    result = dict(base)
    for key, value in top.items():
        if value is None:
            result.pop(key, None)
        elif isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


def key_name(key):
    '''
    A key of the file (F1, enter, btn:up, dart:S20...) as the inputs of the game give it
    '''
    key = str(key)
    if key.startswith('btn:'):
        return BUTTON_KEYS.get(key.lower())
    if key.startswith('dart:'):
        return key[5:]
    return key


def game_category(name):
    '''
    Category of a game (folder of games/ holding <name>.py), None if unknown
    '''
    file_name = f"{str(name).replace(' ', '_')}.py"
    games_dir = os.path.join(cpaths.ROOT_DIR, 'games')
    for category in sorted(os.listdir(games_dir)) if os.path.isdir(games_dir) else []:
        if os.path.isfile(os.path.join(games_dir, category, file_name)):
            return category
    return None


def as_list(value):
    '''
    One value or a list of values : a list
    '''
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


class Menus:
    '''
    The menus of the game : read once, drawn by Screen
    '''

    def __init__(self, logs, theme_dir, user_dir):
        self.logs = logs
        self.errors = []
        self.data = {}
        paths = [DEFAULTS_FILE]
        if theme_dir:
            paths += [os.path.join(theme_dir, FILE_NAME), os.path.join(theme_dir, THEME_FILE)]
        for path in paths:
            self.data = self.add_file(self.data, path)
        self.navigation = {name: [key_name(key) for key in as_list(keys)]
                           for name, keys in (self.data.get('navigation') or {}).items()}

    def add_file(self, data, path):
        '''
        The values of a file over the ones read before. A file which cannot be read is left
        aside : the menus stay those of the files before
        '''
        if not os.path.isfile(path):
            return data
        started = time.perf_counter()
        try:
            if yaml is None:
                raise RuntimeError("PyYAML is missing (python3-yaml)")
            with open(path, encoding='utf-8') as file:
                content = yaml.load(file, Loader=LOADER) or {}
            if not isinstance(content, dict):
                raise ValueError("not a description of menus")
        except Exception as error:    # pylint: disable=broad-except
            self.logs.error(f"Menus : {path} ignored ({error})")
            self.errors.append(path)
            return data
        # Changes of a few buttons, without the whole list
        for name, menu in (content.get('menus') or {}).items():
            changes = (menu or {}).pop('button_changes', None) if isinstance(menu, dict) else None
            if changes and 'buttons' not in menu:
                buttons = [dict(button) for button in (data.get('menus', {}).get(name, {}).get('buttons') or [])]
                for button in buttons:
                    change = changes.get(self.button_id(button))
                    if isinstance(change, dict):
                        button.update(change)
                menu['buttons'] = buttons
        # A list of buttons of the file : the buttons of the files before which it does not
        # name (a button of a newer version of the game) are added after the one before them in
        # those files (else after its own, before those at the bottom of the screen), unless it
        # removed them (removed: [ids])
        for name, menu in (content.get('menus') or {}).items():
            if not isinstance(menu, dict):
                continue
            removed = {str(item) for item in as_list(menu.pop('removed', None))}
            if not isinstance(menu.get('buttons'), list):
                continue
            named = {self.button_id(button) for button in menu['buttons'] if isinstance(button, dict)}
            before = (data.get('menus', {}).get(name) or {}).get('buttons') or []
            self.inherit_shortcuts(menu['buttons'], before)
            extra = [dict(button) for button in before if isinstance(button, dict) and
                     self.button_id(button) not in named and self.button_id(button) not in removed
                     and not named & set(REPLACES.get(self.button_id(button), ()))]
            # Every button placed by hand (place : the editor of the screens) : a new one which asks
            # it (place_free in the files of the game) takes a free place of its size beside the
            # others (beside the one before it first) ; the others, or none free : left to
            # « Ajouter un bouton » of the editor (in the first cell of the grid, it was drawn over
            # another one)
            shown = [button for button in menu['buttons'] if isinstance(button, dict)
                     and not button.get('footer') and button.get('visible', True) is not False]
            if extra and shown and all(isinstance(button.get('place'), dict) for button in shown):
                order = [self.button_id(other) if isinstance(other, dict) else None for other in before]
                kept = []
                for button in extra:
                    if not button.pop('place_free', False):
                        self.logs.info(f"Menus : {name} placed by hand, new button left to the editor : {self.button_id(button)}")
                        continue
                    previous = order[:order.index(self.button_id(button))]
                    place = free_place(shown, menu.get('gap'), next(
                        (other for other_id in reversed(previous) for other in shown if self.button_id(other) == other_id), None))
                    if place is None:
                        self.logs.info(f"Menus : {name} placed by hand, no free place : {self.button_id(button)} left to the editor")
                        continue
                    button['place'] = place
                    shown.append(button)
                    kept.append(button)
                    self.logs.info(f"Menus : {name} placed by hand, {self.button_id(button)} put in a free place {place}")
                extra = kept
            for button in extra:
                ids = [self.button_id(other) if isinstance(other, dict) else None for other in menu['buttons']]
                # Its shortcut already taken by a button of the file (the files moved them) : none
                # (one without shortcut : nothing to compare, other buttons may have none either)
                if button.get('shortcut') and \
                        button.get('shortcut') in {other.get('shortcut') for other in menu['buttons'] if isinstance(other, dict)}:
                    button.pop('shortcut')
                # The button before it in the files, already in this list : just after it
                order = [self.button_id(other) if isinstance(other, dict) else None for other in before]
                previous = order[:order.index(self.button_id(button))]
                at = next((ids.index(other) + 1 for other in reversed(previous) if other in ids), None)
                if at is None:
                    at = next((index for index, other in enumerate(menu['buttons'])
                               if isinstance(other, dict) and other.get('footer')), len(menu['buttons']))
                menu['buttons'].insert(at, button)
        self.logs.debug(f"Menus : {path} read in {(time.perf_counter() - started) * 1000:.0f} ms")
        return merge(data, content)

    def inherit_shortcuts(self, buttons, before):
        '''
        A button of a file without shortcut (no key shortcut at all) : the one of the same button
        in the files before (same id, else the only one with its action), unless another button of
        the list has that key. A list written without any (a theme made by hand) kept Échap
        (Retour, Quitter) and F4 (Divers : the way out of the exhibition mode) of the game ; a
        shortcut removed in the editor is written empty (shortcut: []) and stays removed
        '''
        olds = [button for button in before if isinstance(button, dict) and button.get('shortcut')]
        used = {key for button in buttons if isinstance(button, dict) for key in as_list(button.get('shortcut'))}
        for button in buttons:
            if not isinstance(button, dict) or 'shortcut' in button:
                continue
            old = next((other for other in olds if self.button_id(other) == self.button_id(button)), None)
            if old is None and button.get('action'):
                same = [other for other in olds if other.get('action') == button.get('action')]
                old = same[0] if len(same) == 1 else None
            if old is None:
                continue
            keys = [key for key in as_list(old.get('shortcut')) if key not in used]
            if keys:
                button['shortcut'] = keys[0] if len(keys) == 1 else keys
                used.update(keys)

    @staticmethod
    def button_id(button):
        '''
        Name of a button in its menu : its id, else its action
        '''
        return str(button.get('id') or button.get('action'))

    def menu(self, name):
        '''
        Description of a menu, the defaults included
        '''
        return merge(self.data.get('defaults') or {}, (self.data.get('menus') or {}).get(name) or {})

    def buttons(self, name):
        '''
        Buttons of a menu whose action is known (the others are said in the log once)
        '''
        result = []
        for button in self.menu(name).get('buttons') or []:
            if not isinstance(button, dict):
                continue
            action = str(button.get('action') or '')
            if action.startswith('game:') and game_category(action[5:]) is None:
                if action not in self.errors:
                    self.errors.append(action)
                    self.logs.warning(f"Menus : unknown game '{action[5:]}' in the menu {name}")
            elif action in ACTIONS or action.startswith(ACTION_PREFIXES):
                result.append(button)
            elif action not in self.errors:
                self.errors.append(action)
                self.logs.warning(f"Menus : unknown action '{action}' in the menu {name}")
        return result

    @staticmethod
    def result(button):
        '''
        What the menu returns to the main loop for a button
        '''
        action = str(button.get('action'))
        if action.startswith('menu:'):
            menu = action[5:].split('/')[-1]
            return MENU_RESULTS.get(menu, menu)
        if action.startswith('category:'):
            category = action[9:]
            return CATEGORY_RESULTS.get(category, category)
        return ACTIONS[action]

    @staticmethod
    def target(action):
        '''
        Destination of a button skipping screens : ('game', 'classic.Cricket'),
        ('category', 'favoris'), ('favorite', 'fav1') or None
        '''
        action = str(action or '')
        if action.startswith('favorite:'):
            return ('favorite', action[9:])
        if action.startswith('game:'):
            name = action[5:]
            category = game_category(name)
            return ('game', f"{category}.{name.replace('_', ' ')}") if category else None
        if action.startswith('category:'):
            category = action[9:]
            return ('category', CATEGORY_RESULTS.get(category, category))
        return None

    def start(self):
        '''
        First screen : 'main' (the main menu), or an action whose screen replaces it
        (local_game : the players ; game:<Name>, category:<name> : the players, then the game
        or the games of the category)
        '''
        start = str(self.data.get('start') or 'main')
        # Not a favorite : its game would start again at each return to the first screen
        if start in ('main', 'local_game') or (self.target(start) is not None and not start.startswith('favorite:')):
            return start
        self.logs.warning(f"Menus : start '{start}' unknown, the main menu is shown")
        return 'main'

    def keys(self, name):
        '''
        Keys of the navigation (up, down, validate, back...)
        '''
        return self.navigation.get(name, [])
