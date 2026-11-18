"""
Paramètres > Autodarts : everything about Autodarts in one screen (as Afficheur (Raspy2DMD)).

- On the left : the QR code of its page (its account, its cameras, its calibration are set
  there : RaspyDarts never sees a password), its state ; no address yet : where Autodarts runs.
- Its settings : the reading of its darts, its address (another machine of the network : a PC,
  or a Raspberry Pi 4 or 5 in 64 bits ; RaspyDarts runs in 32 bits, Autodarts never on the
  borne), the counting of the darts (at once, or when they are taken out), the darts taken out
  = Joueur suivant.
- Its commands : a try of the reading, its page, its account.
"""

import time

import pygame

from include import cautodarts


def translate(screen, key):
    return screen.lang.translate(key)


def button(screen, rect, text, chosen, greyed=False):
    '''
    A command : a button of the colours of the menus (greyed : it cannot be done here)
    '''
    colorset = screen.colorset
    if greyed:
        # Greyed whatever the theme : its button darkened, its text grey
        back = tuple(int(part * 0.45) for part in colorset['menu-buttons'][:3])
    else:
        back = colorset['menu-selected'] if chosen else colorset['menu-buttons']
    screen.new_blit_rect2(rect, back, corners='All', border_radius=int(rect.height / 4))
    if greyed and chosen:
        pygame.draw.rect(screen.screen, colorset['menu-selected'], rect, 3, border_radius=int(rect.height / 4))
    if greyed:
        color = (130, 130, 130)
    else:
        color = colorset['menu-text-white'] if chosen else colorset['menu-text-black']
    screen.blit_text(text, rect.x, rect.y, rect.width, rect.height, color)


def page_url(settings):
    '''
    Its page (port 3180) on the machine of Autodarts
    '''
    return f"http://{str(settings.get('host') or '').strip()}:{settings.get('port') or 3180}"


def choose_address(screen, settings):
    '''
    Its address : the machine of the network where Autodarts runs (its IP or its name)
    '''
    before = '' if cautodarts.is_local(settings) else str(settings.get('host'))
    typed = screen.input_value_item('string', before, 1, 60, text='autodarts-address-type')
    if typed in (None, False, 'escape') or not str(typed).strip():
        return False
    typed = str(typed).strip()
    # An address typed with its page (http://..., :3180) : the name or the IP only
    typed = typed.split('://')[-1].split('/')[0]
    if ':' in typed:
        typed, port = typed.rsplit(':', 1)
        if port.isdigit():
            settings['port'] = int(port)
    if not all(character.isalnum() or character in '.-' for character in typed):
        screen.message([translate(screen, 'autodarts-address-bad')], 2500, screen.colorset['menu-ko'], 'middle', 'big')
        return False
    settings['host'] = typed
    return True


def choose_counting(screen, settings):
    choices = [[value, translate(screen, f'autodarts-counting-{value}')] for value in cautodarts.COUNTINGS]
    picked = screen.dropdown(screen.res['x'] * 6 / 16, 3 * screen.res_y_16, choices, navigate=settings.get('counting'),
                             width=6 * screen.res_x_16)
    if picked in cautodarts.COUNTINGS:
        settings['counting'] = picked
        return True
    return False


def try_reading(screen, reader):
    '''
    Essayer la lecture : what Autodarts answers, the darts it reads and what the game receives,
    until Retour. The reading started for the try if it is off
    '''
    from include.cscreen import ENTER_KEYS, ESCAPE_KEYS    # pylint: disable=import-outside-toplevel
    from include import cmenueditor    # pylint: disable=import-outside-toplevel
    started_here = not reader.active
    if started_here:
        reader.configure(dict(reader.settings, enabled=True))
    received = []
    unit_x, unit_y = screen.res['x'] / 16, screen.res['y'] / 16
    white = screen.colorset['menu-text-white']
    try:
        while True:
            while True:
                item = reader.take(True, 3)
                if item is None:
                    break
                received.insert(0, (time.strftime('%H:%M:%S'), item))
                del received[8:]
            screen.display_background()
            screen.menu_header(translate(screen, 'autodarts'), translate(screen, 'autodarts-test'))
            line = int(unit_y * 0.7)
            pos_y = int(2.8 * unit_y)
            state = translate(screen, 'autodarts-state-ok' if reader.connected else 'autodarts-state-ko')
            screen.blit_text(state.replace('{address}', reader.url()), int(unit_x), pos_y, int(14 * unit_x), line,
                             screen.colorset['menu-ok'] if reader.connected else screen.colorset['menu-ko'])
            pos_y += int(line * 1.3)
            if reader.connected and isinstance(reader.state, dict):
                throws = reader.state.get('throws') if isinstance(reader.state.get('throws'), list) else []
                names = ' · '.join(str((throw.get('segment') or {}).get('name', '?')) for throw in throws if isinstance(throw, dict))
                others = ', '.join(f"{key}={reader.state[key]}" for key in sorted(reader.state)
                                   if key not in ('throws', 'numThrows') and not isinstance(reader.state[key], (dict, list)))[:150]
                screen.blit_text(f"numThrows = {reader.state.get('numThrows', '?')}   {names}", int(unit_x), pos_y,
                                 int(14 * unit_x), line, white, align='Left')
                pos_y += line
                if others:
                    screen.blit_text(others, int(unit_x), pos_y, int(14 * unit_x), int(line * 0.8), white, align='Left')
                    pos_y += line
            elif reader.error:
                cmenueditor.paragraph(screen, reader.error[:200], pygame.Rect(int(unit_x), pos_y, int(14 * unit_x), int(2 * line)), white)
                pos_y += 2 * line
            # Two columns : read by Autodarts, received by the game
            pos_y += int(line * 0.5)
            for column, (title, rows) in enumerate((('autodarts-test-read', list(reader.events)),
                                                    ('autodarts-test-received', received))):
                pos_x = int((1 + column * 7.5) * unit_x)
                screen.blit_text(translate(screen, title), pos_x, pos_y, int(6.5 * unit_x), line,
                                 screen.colorset.get('menu-favorite', white))
                for index, (moment, text) in enumerate(rows[:8]):
                    label = translate(screen, 'autodarts-test-takeout') if text in ('takeout', 'PLAYERBUTTON') else text
                    screen.blit_text(f"{moment}   {label}", pos_x, pos_y + (index + 1) * line, int(6.5 * unit_x), line, white, align='Left')
            screen.blit_text(translate(screen, 'autodarts-test-help'), 0, int(13.2 * unit_y), screen.res['x'], int(line * 0.8), white)
            zones = {0: screen.display_button(True, 'back', special='escape')}
            screen.update_screen()
            key = screen.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'enter', 'single-click'], timeout=300)
            if key is False:
                # Its state shown again
                continue
            clicked = screen.is_clicked(zones, key)
            if key in ESCAPE_KEYS or key in ENTER_KEYS or key == 'escape' or clicked not in (False, None):
                return
    finally:
        if started_here:
            reader.configure(dict(reader.settings, enabled=False))


def show_qr(screen, title, url, text):
    '''
    A QR code alone with its address and a text, until a key
    '''
    from include import cmenueditor    # pylint: disable=import-outside-toplevel
    import qrcode    # pylint: disable=import-outside-toplevel
    unit_x, unit_y = screen.res['x'] / 16, screen.res['y'] / 16
    picture = qrcode.make(url)
    picture = (picture.get_image() if hasattr(picture, 'get_image') else picture).convert('RGB')
    side = int(min(6 * unit_x, screen.res['y'] * 0.45))
    code = pygame.transform.scale(pygame.image.fromstring(picture.tobytes(), picture.size, 'RGB'), (side, side))
    screen.display_background()
    screen.menu_header(translate(screen, 'autodarts'), title)
    screen.blit(code, (int(screen.res['x'] / 2 - side / 2), int(2.8 * unit_y)))
    pos_y = int(2.8 * unit_y) + side + screen.margin
    screen.blit_text(url, 0, pos_y, screen.res['x'], int(0.8 * unit_y), screen.colorset['menu-text-white'])
    cmenueditor.paragraph(screen, text, pygame.Rect(int(2 * unit_x), pos_y + int(unit_y), int(12 * unit_x), int(2.5 * unit_y)),
                          screen.colorset['menu-text-white'])
    screen.display_button(True, 'back', special='escape')
    screen.update_screen()
    screen.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'enter', 'space', 'single-click', 'PLAYERBUTTON', 'BACKUPBUTTON'])


def autodarts_menu(screen):
    '''
    The screen of Autodarts : its QR code and its state on the left, its settings, its commands
    '''
    from include import cmenueditor    # pylint: disable=import-outside-toplevel
    from include.cscreen import DOWN_KEYS, ENTER_KEYS, ESCAPE_KEYS, UP_KEYS    # pylint: disable=import-outside-toplevel
    import qrcode    # pylint: disable=import-outside-toplevel
    reader = cautodarts.shared(screen.logs)
    settings = cautodarts.load()
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

    def changed():
        cautodarts.save(settings)
        interior = screen.config.get_value('SectionAdvanced', 'interior', False)
        reader.configure(dict(settings), interior is True or str(interior) == 'True')

    while True:
        # Its address : the machine of Autodarts (none yet : the try and its page greyed)
        address_set = not cautodarts.is_local(settings)
        yes_no = lambda value: translate(screen, 'yes' if value else 'no')    # pylint: disable=unnecessary-lambda-assignment
        entries = [('setting', 'enabled', 'autodarts-enabled', yes_no(settings.get('enabled'))),
                   ('setting', 'address', 'autodarts-address',
                    str(settings.get('host')) if address_set else translate(screen, 'autodarts-address-none')),
                   ('setting', 'counting', 'autodarts-counting', translate(screen, f"autodarts-counting-{settings.get('counting')}")),
                   ('setting', 'takeout', 'autodarts-takeout-next', yes_no(settings.get('takeout_next', True))),
                   ('command', 'try', 'autodarts-test', None if address_set else 'greyed')]
        entries += [('command', 'page', 'autodarts-page', None if address_set else 'greyed'),
                    ('command', 'account', 'autodarts-account', None),
                    ('back', 'back', 'back', None)]
        # A greyed command cannot be chosen : never selected, its click ignored
        usable = [index for index, entry in enumerate(entries) if entry[3] != 'greyed']
        selected = max(0, min(selected, len(entries) - 1))
        if selected not in usable:
            selected = min(usable, key=lambda index: abs(index - selected))

        screen.display_background()
        screen.menu_header(translate(screen, 'autodarts'), translate(screen, 'autodarts-subtitle'))
        # On the left : the QR code of its page, its state, what this Raspberry can do
        side = int(min(4 * unit_x, screen.res['y'] * 0.3))
        left = pygame.Rect(int(0.5 * unit_x), int(3.0 * unit_y), int(4.2 * unit_x), int(11 * unit_y))
        line = int(unit_y * 0.7)
        text_y = left.y
        if address_set:
            url = page_url(settings)
            screen.blit(qr_code(url, side), (left.centerx - side // 2, left.y))
            text_y = left.y + side + screen.margin
            screen.blit_text(url, left.x, text_y, left.width, line, screen.colorset['menu-text-white'])
            text_y += line
        if not address_set:
            state, color = translate(screen, 'autodarts-state-no-address'), screen.colorset['menu-ko']
        elif settings.get('enabled'):
            ok = reader.connected
            state = translate(screen, 'autodarts-state-ok' if ok else 'autodarts-state-ko').replace('{address}', reader.url())
            color = screen.colorset['menu-ok' if ok else 'menu-ko']
        else:
            state, color = translate(screen, 'autodarts-state-off'), screen.colorset['menu-text-white']
        cmenueditor.paragraph(screen, state, pygame.Rect(left.x, text_y + int(unit_y * 0.2), left.width, int(1.6 * unit_y)), color)
        text_y += int(1.9 * unit_y)
        if not address_set:
            # Where Autodarts runs : another machine, its address to give
            warning = screen.colorset.get('menu-warning', screen.colorset['menu-ko'])
            cmenueditor.paragraph(screen, translate(screen, 'autodarts-elsewhere'),
                                  pygame.Rect(left.x, text_y, left.width, int(14 * unit_y) - text_y), warning)

        zones = {}
        rows = {'setting': 0, 'command': 0}
        columns = {'setting': (5.0, 5.6), 'command': (11.0, 4.5)}
        for title, kind in (('autodarts-settings', 'setting'), ('autodarts-commands', 'command')):
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
            if kind == 'setting':
                cmenueditor.value_item(screen, rect, translate(screen, text), value, index == selected)
            else:
                button(screen, rect, translate(screen, text), index == selected, greyed=value == 'greyed')
            if value != 'greyed':
                zones[index] = tuple(rect)
        screen.update_screen()

        key = screen.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'enter', 'space', 'PLAYERBUTTON', 'BACKUPBUTTON',
                                                          'GAMEBUTTON', 'single-click'], timeout=2000)
        if key is False:
            # Its state shown again (connected or not)
            continue
        clicked = screen.is_clicked(zones, key)
        if clicked is not False and clicked is not None:
            selected, key = clicked, 'enter'
        kind = entries[selected][0]
        same = [index for index in usable if entries[index][0] == kind]
        if key in ESCAPE_KEYS or key == 'escape':
            return
        if key in ('BTN_RIGHT',):
            selected = usable[(usable.index(selected) + 1) % len(usable)]
        elif key in ('BTN_LEFT',):
            selected = usable[(usable.index(selected) - 1) % len(usable)]
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
                other = [index for index in usable if entries[index][0] == ('command' if kind == 'setting' else 'setting')]
                selected = other[min(same.index(selected), len(other) - 1)]
        elif key in ENTER_KEYS + ['space']:
            ident, value = entries[selected][1], entries[selected][3]
            if value == 'greyed':
                continue
            if kind == 'back':
                return
            if ident == 'enabled':
                settings['enabled'] = not settings.get('enabled')
                changed()
            elif ident == 'address':
                if choose_address(screen, settings):
                    changed()
            elif ident == 'counting':
                if choose_counting(screen, settings):
                    changed()
            elif ident == 'takeout':
                settings['takeout_next'] = not settings.get('takeout_next', True)
                changed()
            elif ident == 'try':
                try_reading(screen, reader)
            elif ident == 'page':
                show_qr(screen, translate(screen, 'autodarts-page'), page_url(settings), translate(screen, 'autodarts-page-help'))
            elif ident == 'account':
                show_qr(screen, translate(screen, 'autodarts-account'), cautodarts.ACCOUNT_URL, translate(screen, 'autodarts-account-help'))
