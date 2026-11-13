"""
Paramètres > Afficheur (Raspy2DMD) : everything about the DMD display in one screen.

- Raspy2DMD installed with RaspyDarts (this Raspberry, mode « Pico seul ») or on its own
  Raspberry (two Raspberry : it listens to the MQTT of the borne) : found by the screen. In the
  second case, it can still be installed here (a change of configuration).
- Its settings : the display of the score (for every game, then by type and by game, as the
  favorite games), the texts in the colour of the player, Raspy2DMD powered off with RaspyDarts.
- Its commands : a message, the test pattern, the clock, the demo, a try of the display of the
  score ; start, update, uninstall (here) or install (on another Raspberry).
"""

import os
import socket
import threading
import time

import pygame

from include import cdmdscore


def translate(screen, key):
    return screen.lang.translate(key)


def style_label(screen, value):
    return translate(screen, f'dmd-style-{value}')


def value_label(screen, key, value):
    if key == 'style':
        return style_label(screen, value)
    return translate(screen, f'dmd-{key}-{value}')


def summary(screen, settings):
    '''
    A setting shown in a line : Moderne · sans GIF
    '''
    gif = translate(screen, 'dmd-gif-short-O' if settings.get('gif') == 'O' else 'dmd-gif-short-N')
    return f"{style_label(screen, settings.get('style'))} · {gif}"


def flag(screen, key):
    value = screen.config.get_value('SectionGlobals', key, False)
    return value is True or str(value) == 'True'


def set_flag(screen, key, value):
    screen.config.config['SectionGlobals'][key] = bool(value)
    screen.config.write_file()


def button(screen, rect, text, chosen):
    '''
    A command : a button of the colours of the menus
    '''
    colorset = screen.colorset
    screen.new_blit_rect2(rect, colorset['menu-selected'] if chosen else colorset['menu-buttons'], corners='All',
                          border_radius=int(rect.height / 4))
    screen.blit_text(text, rect.x, rect.y, rect.width, rect.height,
                     colorset['menu-text-white'] if chosen else colorset['menu-text-black'])


def try_style(screen, settings):
    '''
    The display of the score tried on the DMD : its background, three darts (a segment, a missed
    one, a segment), its background stopped ; in the background of the screen
    '''
    dmd = screen.dmd
    style = settings.get('style', 'classic')
    background = cdmdscore.BACKGROUND.get(style)

    def run():
        try:
            if background:
                dmd.send(f"{background}|start|{settings.get('wait', 'N')}")
                time.sleep(1)
            for darts in (('T20', 'X', 'X'), ('T20', 'MISS', 'X'), ('T20', 'MISS', 'S5')):
                dmd.send(dmd.score_text(list(darts), style, settings.get('gif', 'N')))
                time.sleep(4)
            if background:
                time.sleep(3)
                dmd.send(f'{background}|stop')
        except Exception as error:    # pylint: disable=broad-except
            screen.logs.warning(f"DMD : try of the score not sent ({error})")
    threading.Thread(target=run, daemon=True).start()
    screen.message([translate(screen, 'dmd-score-trying')], 1500, screen.colorset['menu-ok'], 'middle', 'big')


def version_note(screen):
    '''
    What the styles need, when the Raspy2DMD is too old or not known (another Raspberry)
    '''
    known = cdmdscore.styles_known()
    if known is True:
        return None
    if known is False:
        return translate(screen, 'dmd-version-old').format(cdmdscore.local_version() or '?')
    return translate(screen, 'dmd-version-needed')


def raspy2dmd_menu(screen, dispatcher):
    '''
    The screen of the DMD display : its QR code on the left, its settings, its commands
    '''
    # Its installation followed until its end : then its screen
    if screen.raspy2dmd_installing() and not screen.raspy2dmd_install_progress():
        return
    from include import cgallery    # pylint: disable=import-outside-toplevel
    from include import cmenueditor    # pylint: disable=import-outside-toplevel
    from include.cscreen import DOWN_KEYS, ENTER_KEYS, ESCAPE_KEYS, UP_KEYS    # pylint: disable=import-outside-toplevel
    import qrcode    # pylint: disable=import-outside-toplevel
    unit_x, unit_y = screen.res['x'] / 16, screen.res['y'] / 16
    selected = 0
    codes = {}

    def qr_code(url, side):
        if (url, side) not in codes:
            picture = qrcode.make(url)
            picture = (picture.get_image() if hasattr(picture, 'get_image') else picture).convert('RGB')
            codes[(url, side)] = pygame.transform.scale(pygame.image.fromstring(picture.tobytes(), picture.size, 'RGB'),
                                                        (side, side))
        return codes[(url, side)]

    while True:
        here = cdmdscore.local()
        running = screen.raspy2dmd_running() if here else True
        settings = [('score', 'dmd-score', summary(screen, cdmdscore.general())),
                    ('by-game', 'dmd-score-by-game', None),
                    ('color', 'dmd_player_color', translate(screen, 'yes' if flag(screen, 'dmd_player_color') else 'no')),
                    ('shutdown', 'dmd_shutdown', translate(screen, 'yes' if flag(screen, 'dmd_shutdown') else 'no'))]
        if running:
            commands = [('message', 'raspy2dmd-test-message'), ('pattern', 'raspy2dmd-test-pattern'),
                        ('clock', 'raspy2dmd-clock'), ('demo', 'raspy2dmd-demo'), ('try', 'dmd-score-try')]
        else:
            commands = [('start', 'raspy2dmd-start')]
        if here:
            commands.append(('update', 'raspy2dmd-check-update'))
            if os.path.isfile(screen.RASPY2DMD_PICO_SEUL):
                commands.append(('uninstall', 'raspy2dmd-uninstall'))
        else:
            commands.append(('install', 'raspy2dmd-install-here'))
        # In the order of reading : the settings, the commands, Retour
        entries = [('setting',) + item for item in settings] + [('command',) + item + (None,) for item in commands] + [('back', 'back', 'back', None)]
        selected = max(0, min(selected, len(entries) - 1))

        screen.display_background()
        screen.menu_header(translate(screen, 'raspy2dmd'),
                           translate(screen, 'raspy2dmd-scan' if here else 'raspy2dmd-remote'))
        # The QR code of its web page : here, the name of the Raspberry (it stays when the IP
        # changes) and its IP ; another Raspberry : the one connected to the MQTT of the borne
        side = int(min(4 * unit_x, screen.res['y'] * 0.3))
        left = pygame.Rect(int(0.5 * unit_x), int(3.0 * unit_y), int(4.2 * unit_x), int(11 * unit_y))
        line = int(unit_y * 0.8)
        text_y = left.y
        if here:
            urls = (f"http://{socket.gethostname()}.local/", f"http://{cgallery.local_ip()}/")
        else:
            address = cdmdscore.remote_address()
            urls = (f"http://{address}/",) if address else ()
        if urls:
            screen.blit(qr_code(urls[0], side), (left.centerx - side // 2, left.y))
            text_y = left.y + side + screen.margin
            for url in urls:
                screen.blit_text(url, left.x, text_y, left.width, line, screen.colorset['menu-text-white'])
                text_y += line
        else:
            cmenueditor.paragraph(screen, translate(screen, 'raspy2dmd-remote-unknown'),
                                  pygame.Rect(left.x, text_y, left.width, int(3 * unit_y)), screen.colorset['menu-text-white'])
            text_y += int(3 * unit_y)
        notes = []
        if here and not running:
            notes.append((translate(screen, 'raspy2dmd-not-running'), screen.colorset['menu-ko']))
        note = version_note(screen)
        if note:
            notes.append((note, screen.colorset['menu-warning'] if 'menu-warning' in screen.colorset else screen.colorset['menu-ko']))
        for text, color in notes:
            cmenueditor.paragraph(screen, text, pygame.Rect(left.x, text_y + int(unit_y * 0.3), left.width, int(2 * unit_y)), color)
            text_y += int(2.2 * unit_y)

        zones = {}
        rows = {'setting': 0, 'command': 0}
        columns = {'setting': (5.0, 5.6), 'command': (11.0, 4.5)}
        for title, kind in (('raspy2dmd-settings', 'setting'), ('raspy2dmd-commands', 'command')):
            pos, width = columns[kind]
            screen.blit_text(translate(screen, title), int(pos * unit_x), int(2.95 * unit_y), int(width * unit_x), int(0.7 * unit_y),
                             screen.colorset.get('menu-favorite', screen.colorset['menu-text-white']))
        for index, (kind, ident, text, value) in enumerate(entries):
            if kind == 'back':
                zones[index] = screen.display_button(index == selected, 'back', special='escape')
                continue
            pos, width = columns[kind]
            rect = pygame.Rect(int(pos * unit_x), int((3.8 + rows[kind] * 1.3) * unit_y), int(width * unit_x), int(1.05 * unit_y))
            rows[kind] += 1
            if kind == 'setting' and value is not None:
                cmenueditor.value_item(screen, rect, translate(screen, text), value, index == selected)
            else:
                button(screen, rect, translate(screen, text), index == selected)
            zones[index] = tuple(rect)
        screen.update_screen()

        key = screen.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'enter', 'space', 'PLAYERBUTTON', 'BACKUPBUTTON',
                                                          'GAMEBUTTON', 'single-click'])
        clicked = screen.is_clicked(zones, key)
        if clicked is not False and clicked is not None:
            selected, key = clicked, 'enter'
        kind = entries[selected][0]
        same = [index for index, entry in enumerate(entries) if entry[0] == kind]
        if key in ESCAPE_KEYS or key == 'escape':
            return
        if key in ('BTN_RIGHT',):
            # The wheel of a knob : in the order of reading
            selected = (selected + 1) % len(entries)
        elif key in ('BTN_LEFT',):
            selected = (selected - 1) % len(entries)
        elif key in DOWN_KEYS:
            position = same.index(selected)
            selected = same[position + 1] if position + 1 < len(same) else len(entries) - 1
        elif key in UP_KEYS:
            position = same.index(selected)
            if kind == 'back':
                selected = [index for index, entry in enumerate(entries) if entry[0] == 'setting'][-1]
            else:
                selected = same[position - 1] if position > 0 else selected
        elif key in ('left', 'right', 'S11', 'S6'):
            if kind in ('setting', 'command'):
                other = [index for index, entry in enumerate(entries) if entry[0] == ('command' if kind == 'setting' else 'setting')]
                selected = other[min(same.index(selected), len(other) - 1)]
        elif key in ENTER_KEYS + ['space']:
            kind, ident = entries[selected][0], entries[selected][1]
            if kind == 'back':
                return
            if ident == 'score':
                score_settings(screen, 'general', None)
            elif ident == 'by-game':
                score_games_menu(screen)
            elif ident == 'color':
                set_flag(screen, 'dmd_player_color', not flag(screen, 'dmd_player_color'))
            elif ident == 'shutdown':
                set_flag(screen, 'dmd_shutdown', not flag(screen, 'dmd_shutdown'))
            elif ident == 'start':
                screen.raspy2dmd_start()
            elif ident == 'update':
                screen.raspy2dmd_update()
            elif ident == 'uninstall':
                if screen.raspy2dmd_uninstall():
                    selected = 0
            elif ident == 'install':
                screen.raspy2dmd_install()
                if screen.raspy2dmd_installing():
                    screen.raspy2dmd_install_progress()
            elif ident == 'try':
                try_style(screen, cdmdscore.general())
            else:
                message = {'message': f"msg|{translate(screen, 'raspy2dmd-hello')}", 'pattern': 'pico|test_rgb',
                           'clock': 'time|start', 'demo': 'demo|gif'}[ident]
                dispatcher.mqtt_publish(screen.RASPY2DMD_TOPIC, message)
                screen.message([translate(screen, 'raspy2dmd-sent')], 1000, screen.colorset['menu-ok'], 'middle', 'big')


def level_settings(level, name, data=None):
    '''
    What a level has itself (inherit : as the level above), and what it gives
    '''
    data = cdmdscore.load() if data is None else data
    if level == 'general':
        effective = cdmdscore.general(data)
        return dict(effective), effective, None
    if level == 'types':
        own = dict(data['types'].get(name) or {})
        effective = cdmdscore.of_type(name, data)
        return own, effective, cdmdscore.general(data)
    own = cdmdscore.own_of_game(name, data)
    effective = cdmdscore.of_game(name, data)
    return own, effective, cdmdscore.of_type(cdmdscore.category_of(name), data)


def score_settings(screen, level, name):
    '''
    The display of the score of every game (general), of a type, of a game : its style, its
    GIF, what the DMD shows while waiting during the game ; saved at once. A type or a game :
    each value as the level above, or its own
    '''
    from include import cmenueditor    # pylint: disable=import-outside-toplevel
    from include.cscreen import DOWN_KEYS, ENTER_KEYS, ESCAPE_KEYS, LEFT_KEYS, RIGHT_KEYS, UP_KEYS    # pylint: disable=import-outside-toplevel
    unit_x, unit_y = screen.res['x'] / 16, screen.res['y'] / 16
    if level == 'general':
        subtitle = translate(screen, 'dmd-score-general')
        above = None
    elif level == 'types':
        subtitle = translate(screen, f'dmd-score-whole-{name}')
        above = 'dmd-inherit-general'
    else:
        subtitle = translate(screen, str(name).replace('_', ' '))
        above = 'dmd-inherit-type'
    choices = {'style': cdmdscore.STYLES, 'gif': ('N', 'O'), 'wait': ('N', 'O')}
    selected = 0
    while True:
        own, effective, upper = level_settings(level, name)
        keys = ['style', 'gif'] + (['wait'] if effective.get('style') != 'classic' else [])
        entries = keys + ['try', 'back']
        selected = min(selected, len(entries) - 1)

        def shown(key):
            value = own.get(key, cdmdscore.INHERIT if above else effective.get(key))
            if value == cdmdscore.INHERIT or value is None:
                return f"{translate(screen, above)} ({value_label(screen, key, upper.get(key))})"
            return value_label(screen, key, value)

        screen.display_background()
        screen.menu_header(translate(screen, 'dmd-score'), subtitle)
        zones = {}
        for index, key in enumerate(keys):
            rect = pygame.Rect(int(unit_x), int((3.0 + index * 1.4) * unit_y), int(8 * unit_x), int(1.1 * unit_y))
            cmenueditor.value_item(screen, rect, translate(screen, f'dmd-{key}'), shown(key), index == selected)
            zones[index] = tuple(rect)
        rect = pygame.Rect(int(unit_x), int((3.0 + len(keys) * 1.4 + 0.4) * unit_y), int(8 * unit_x), int(1.1 * unit_y))
        button(screen, rect, translate(screen, 'dmd-score-try'), selected == len(keys))
        zones[len(keys)] = tuple(rect)
        help_rect = pygame.Rect(int(9.6 * unit_x), int(3.0 * unit_y), int(5.6 * unit_x), int(7 * unit_y))
        screen.new_blit_rect2(help_rect, screen.colorset['menu-buttons'], corners='All', border_radius=int(unit_y / 4))
        cmenueditor.paragraph(screen, translate(screen, f"dmd-style-help-{effective.get('style')}"),
                              help_rect.inflate(-int(unit_x / 2), -int(unit_y / 2)), screen.colorset['menu-text-white'])
        note = version_note(screen)
        if note:
            cmenueditor.paragraph(screen, note, pygame.Rect(int(unit_x), int(11.6 * unit_y), int(14 * unit_x), int(1.2 * unit_y)),
                                  screen.colorset['menu-text-white'])
        zones[len(keys) + 1] = screen.display_button(selected == len(keys) + 1, 'back', special='escape')
        screen.update_screen()

        key = screen.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'enter', 'space', 'PLAYERBUTTON', 'BACKUPBUTTON',
                                                          'GAMEBUTTON', 'single-click'])
        clicked = screen.is_clicked(zones, key)
        if clicked is not False and clicked is not None:
            selected, key = clicked, 'enter'
        if key in ESCAPE_KEYS or key == 'escape':
            return
        if key in DOWN_KEYS + RIGHT_KEYS:
            selected = (selected + 1) % len(entries)
        elif key in UP_KEYS + LEFT_KEYS:
            selected = (selected - 1) % len(entries)
        elif key in ENTER_KEYS + ['space']:
            entry = entries[selected]
            if entry == 'back':
                return
            if entry == 'try':
                try_style(screen, effective)
                continue
            values = [[value, value_label(screen, entry, value)] for value in choices[entry]]
            if above:
                values.insert(0, [cdmdscore.INHERIT, f"{translate(screen, above)} ({value_label(screen, entry, upper.get(entry))})"])
            current = own.get(entry, cdmdscore.INHERIT if above else effective.get(entry))
            picked = screen.dropdown(unit_x, 3 * unit_y, values, navigate=current, width=8 * unit_x)
            if picked not in ('escape', None, False):
                cdmdscore.set_value(level, name, entry, picked)


def score_games_menu(screen):
    '''
    The display of the score by type and by game, as the favorite games : the tabs of the
    types, then the whole type and its games (green : a setting of its own)
    '''
    from include.cscreen import ENTER_KEYS, ESCAPE_KEYS, SAVE_KEYS    # pylint: disable=import-outside-toplevel
    category = 'classic'
    selected = 1
    tab = -2
    while True:
        games = sorted(screen.get_games_list(category=category))
        data = cdmdscore.load()
        entries = [('types', category, translate(screen, f'dmd-score-whole-{category}'))] + \
            [('games', game.replace(' ', '_'), game) for game in games]
        nb_elements = len(entries)
        click_zones = {}
        shortcuts = []
        screen.display_background()
        screen.menu_header(f"{translate(screen, 'dmd-score')} : {translate(screen, 'dmd-score-by-game').lower()}")
        for number, (tab_category, special) in enumerate((('classic', 'tab1'), ('fun', 'tab2'), ('sport', 'tab3'))):
            click_zones[f'F{number - 2}'] = screen.display_button(number - 2 == selected, f'category-{tab_category}', special=special)
            shortcuts.append(f'F{number - 2}')
        for index, (level, name, text) in enumerate(entries, 1):
            click_zones[f'F{index}'] = screen.game_item((index, nb_elements, selected),
                                                        (f'F{index}', text, cdmdscore.has_own(level, name, data)))
            shortcuts.append(f'F{index}')
        click_zones['escape'] = screen.display_button(nb_elements + 1 == selected, 'back', special='escape')
        screen.update_screen()

        key = screen.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON',
                                                          'single-click', 'enter', 'space'])
        clicked = screen.is_clicked(click_zones, key)
        if clicked:
            key = clicked
        selected = screen.navigate(selected, key, nb_elements, 1, 1, item_per_line=2, left_right=True, zero=-2, tab=tab)
        if key in shortcuts:
            selected = int(key.replace('F', ''))
            key = 'enter'
        if key in ESCAPE_KEYS + SAVE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
            return
        if selected < 1:
            category = {-2: 'classic', -1: 'fun', 0: 'sport'}[selected]
            tab = selected
            continue
        if key in ENTER_KEYS + ['space'] and 1 <= selected <= nb_elements:
            level, name, _text = entries[selected - 1]
            score_settings(screen, level, name)
