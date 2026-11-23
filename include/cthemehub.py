"""
Modifier les écrans > Exporter le thème > Vers RaspyHub : a theme shared on raspyhub.fr.

- Its name (the one of the theme, changed if wanted), its author : a player of the borne (he gets
  the trophy « Participation à la création artistique » when it is sent), shown with his name
  and/or a pseudo (RaspyHub adds # and 6 characters of the identifier of the borne : no double).
- Its captures : 3 asked (the main screen, Paramètres, Choix du jeu in Classique) and 6 at most
  chosen among the other pages of the menus and the captures taken by the player (mode capture :
  include/ccapture.py), everything in ~/.raspydarts/raspyhub/export/<theme>.
- The mention on the images (their author alone answers for them), the checks (Internet, the zip
  read again, the limits of the server), then the sending : the API of the themes (Serveur
  Télémétrie, raspythemes/README.md), the theme waiting there to be validated ; sent, its player
  gets the trophy.
- Only the address of the catalogue is written here : the captures and the downloads are given by
  it (include/cthemecatalog.py).
"""

import json
import os
import re
import socket
import threading
import time
import zipfile

import pygame

from include import ccapture
from include import cpaths

EXTRA_MOST = 6
# The API of the themes : the catalogue (read by every borne), the sending (with its key)
API = 'https://raspystats.raspyhub.fr/api/v1/raspydarts/themes'
API_KEY = 'raspydarts_themes_2026'
HUB_HOST = 'raspystats.raspyhub.fr'
# The limits of the server (GET .../limits) : these ones when it cannot be read
LIMITS = {'max_zip_mb': 50, 'max_unzipped_mb': 400, 'min_captures': 3, 'max_captures': 9, 'max_capture_mb': 5,
          'uploads_per_day': 5, 'name_max': 40, 'author_max': 40}
TROPHY = 'CREATION_ARTISTIQUE'
# The refusals of the server shown in the language of the borne (the others : its message, in French)
ERRORS = {'name_taken': 'hub-error-name-taken', 'too_many_uploads': 'hub-error-too-many',
          'theme_removed': 'hub-error-removed', 'too_large': 'hub-error-too-large',
          'capture_too_large': 'hub-error-too-large'}


def translate(screen, key):
    return screen.lang.translate(key)


def hub_dir(theme):
    return os.path.join(cpaths.user_dir(), 'raspyhub', 'export', theme)


def limits(logs):
    '''
    The limits of the server (size of the zip, captures, lengths) ; LIMITS when it cannot be read
    '''
    found = dict(LIMITS)
    try:
        import requests    # pylint: disable=import-outside-toplevel
        answer = requests.get(f"{API}/limits", timeout=8)
        answer.raise_for_status()
        found.update({key: value for key, value in answer.json().items() if isinstance(value, (int, float))})
    except Exception as error:    # pylint: disable=broad-except
        logs.warning(f"RaspyHub : limits not read ({error}), those of the borne used")
    return found


class Draft:
    '''
    What is prepared for a theme : its name, its player, its author, the mention read, the
    captures chosen (kept in draft.json, next to its captures)
    '''

    def __init__(self, theme):
        self.theme = theme
        self.folder = hub_dir(theme)
        self.data = {'name': theme, 'player': '', 'author': '', 'rights': False, 'chosen': []}
        try:
            with open(os.path.join(self.folder, 'draft.json'), encoding='utf-8') as source:
                self.data.update(json.load(source))
        except (OSError, ValueError):
            pass

    def save(self):
        os.makedirs(self.folder, exist_ok=True)
        path = os.path.join(self.folder, 'draft.json')
        with open(path + '.tmp', 'w', encoding='utf-8') as target:
            json.dump(self.data, target, indent=2, ensure_ascii=False)
        os.replace(path + '.tmp', path)

    def captures(self):
        '''
        The captures there : those of the pages (in the order of PAGES), then those taken
        '''
        try:
            names = set(os.listdir(self.folder))
        except OSError:
            names = set()
        pages = [f'auto-{name}.jpg' for name, _kind in ccapture.PAGES if f'auto-{name}.jpg' in names]
        free = sorted(name for name in names if name.startswith('free-') and name.endswith('.jpg'))
        return pages + free

    @staticmethod
    def mandatory(name):
        return name in [f'auto-{page}.jpg' for page in ccapture.MANDATORY]

    def chosen(self):
        '''
        The captures chosen beyond the 3 asked (those still there, EXTRA_MOST at most)
        '''
        there = self.captures()
        return [name for name in self.data.get('chosen', []) if name in there and not self.mandatory(name)][:EXTRA_MOST]

    def missing(self):
        '''
        The captures asked not made yet
        '''
        there = self.captures()
        return [page for page in ccapture.MANDATORY if f'auto-{page}.jpg' not in there]

    def sent(self):
        '''
        The captures sent : the 3 asked, then those chosen
        '''
        return [f'auto-{page}.jpg' for page in ccapture.MANDATORY] + self.chosen()


def players(screen):
    '''
    The players of the borne : those it knows (favorites, bank of firstnames), then those of
    the trophies
    '''
    names = list(screen.known_players())
    try:
        with open(cpaths.trophies_file(), encoding='utf-8') as source:
            for name in json.load(source):
                name = str(name).strip()
                # Not the totals of the file (_global_stats) nor the players without a name (Joueur 3)
                if not name or name.startswith('_') or re.fullmatch(r'(Joueur|Player|Spieler|Jugador|Giocatore|Speler) \d+', name):
                    continue
                if name.casefold() not in [known.casefold() for known in names]:
                    names.append(name)
    except (OSError, ValueError):
        pass
    return names


def picture(path, size):
    '''
    A capture made the size given (its proportions kept) ; None : unreadable
    '''
    try:
        from PIL import Image    # pylint: disable=import-outside-toplevel
        with Image.open(path) as source:
            image = source.convert('RGB')
            image.thumbnail(size)
            return pygame.image.fromstring(image.tobytes(), image.size, 'RGB')
    except Exception:    # pylint: disable=broad-except
        return None


def award(screen, player):
    '''
    The theme sent : its player gets the trophy « Participation à la création artistique »
    '''
    from include import ctrophies    # pylint: disable=import-outside-toplevel
    try:
        ctrophies.save_unlocked_trophy(player, TROPHY)
    except Exception as error:    # pylint: disable=broad-except
        screen.logs.error(f"Trophy {TROPHY} for {player} : {error}")


# ---------------------------------------------------------------------- the screen
def generate(screen, draft):
    '''
    Générer les captures : each page of the menus drawn and captured with the theme
    '''
    screen.message([translate(screen, 'hub-generating')], 1200, None, 'middle', 'big')
    written = ccapture.generate(screen, draft.folder, screen.logs)
    # The pages chosen first : the extras made now, while there is room
    chosen = draft.chosen()
    for name, _kind in ccapture.PAGES:
        file_name = f'auto-{name}.jpg'
        if name in written and not draft.mandatory(file_name) and file_name not in chosen and len(chosen) < EXTRA_MOST:
            chosen.append(file_name)
    draft.data['chosen'] = chosen
    draft.save()
    if len(written) < len(ccapture.PAGES):
        screen.message([translate(screen, 'hub-generate-partial')], 2500, 'menu-ko', 'middle', 'big')


def start_capture(screen, draft):
    '''
    Prendre des captures : the mode capture, back to this screen when it ends (from a menu)
    '''
    def ended(taken):
        chosen = draft.chosen()
        for name in taken:
            if len(chosen) < EXTRA_MOST:
                chosen.append(name)
        draft.data['chosen'] = chosen
        draft.save()
        # Back to the screen of the export at the next turn of a menu (Screen.idle_turn)
        screen.hub_return = draft.theme

    if not screen.ask_yes_no(translate(screen, 'hub-capture-question'), translate(screen, 'hub-capture-explain')):
        return False
    os.makedirs(draft.folder, exist_ok=True)
    ccapture.CaptureMode(screen, draft.folder, ended)
    return True


def ready(screen, draft):
    '''
    What is missing before the sending (texts), [] : it can be sent
    '''
    missing = []
    if not str(draft.data.get('name') or '').strip():
        missing.append(translate(screen, 'hub-missing-name'))
    if not draft.data.get('player'):
        missing.append(translate(screen, 'hub-missing-player'))
    if not str(draft.data.get('author') or '').strip():
        missing.append(translate(screen, 'hub-missing-author'))
    if draft.missing():
        missing.append(translate(screen, 'hub-missing-captures'))
    if not draft.data.get('rights'):
        missing.append(translate(screen, 'hub-missing-rights'))
    return missing


def check_zip(path, theme):
    '''
    The zip read again : its files whole, its theme there. Raises ValueError
    '''
    with zipfile.ZipFile(path) as archive:
        broken = archive.testzip()
        if broken is not None:
            raise ValueError(f"damaged file {broken}")
        names = archive.namelist()
    if not any(name in (f'{theme}/other/Colorset.cfg', f'{theme}/Colorset.cfg') for name in names):
        raise ValueError('no Colorset.cfg')


def send(screen, draft):
    '''
    Envoyer vers RaspyHub : checks, the zip made and read again, then sent (upload)
    '''
    from include import cthemefiles    # pylint: disable=import-outside-toplevel
    missing = ready(screen, draft)
    if missing:
        screen.message([f"{translate(screen, 'hub-missing')} {', '.join(missing)}"], 4000, 'menu-ko', 'middle', 'big')
        return
    try:
        socket.create_connection((HUB_HOST, 443), timeout=5).close()
    except OSError:
        screen.message([translate(screen, 'hub-no-internet')], 3000, 'menu-ko', 'middle', 'big')
        return
    most = limits(screen.logs)
    theme_dir = getattr(screen.file_class, 'theme_dir', None)
    if not theme_dir or not os.path.isdir(theme_dir):
        screen.message([translate(screen, 'theme-export-none')], 2500, 'menu-ko', 'middle', 'big')
        return
    media_size = sum(cthemefiles.folder_size(os.path.join(theme_dir, name)) for name in cthemefiles.MEDIA)
    media = False
    if media_size > 0:
        answer = screen.ask_yes_no(translate(screen, 'theme-export-media').replace('{size}', f"{media_size / 1048576:.0f}"),
                                   translate(screen, 'hub-media-explain').replace('{limit}', str(most['max_zip_mb'])),
                                   cancel=True)
        if answer is None:
            return
        media = bool(answer)
    folder = os.path.join(draft.folder, 'envoi')
    try:
        for name in os.listdir(folder):
            os.remove(os.path.join(folder, name))
    except OSError:
        pass
    export = cthemefiles.Export(screen.logs, draft.theme, theme_dir, folder, media, theme_version(screen))
    # The zip made : its progress shown
    while export.state == 'running':
        fraction = export.done / export.total
        screen.message([f"{translate(screen, 'hub-zipping')} {int(fraction * 100)} %"], 0, None, 'middle', 'big')
        time.sleep(0.3)
    if export.state != 'done':
        screen.message([translate(screen, 'hub-zip-failed')], 3000, 'menu-ko', 'middle', 'big')
        return
    try:
        check_zip(export.target, draft.theme)
    except (ValueError, zipfile.BadZipFile, OSError) as error:
        screen.logs.error(f"RaspyHub : zip {export.target} refused ({error})")
        screen.message([translate(screen, 'hub-zip-failed')], 3000, 'menu-ko', 'middle', 'big')
        return
    size = os.path.getsize(export.target)
    if size > most['max_zip_mb'] * 1024 ** 2:
        screen.message([translate(screen, 'hub-too-big').replace('{size}', f"{size / 1048576:.0f}")
                        .replace('{limit}', str(most['max_zip_mb']))], 4000, 'menu-ko', 'middle', 'big')
        return
    upload(screen, draft, export.target)


def post(draft, zip_path, version, outcome):
    '''
    The theme sent (in a thread) : outcome gets status (the HTTP code, 0 : not reached), answer
    (the JSON of the server) or error
    '''
    files = []
    try:
        import requests    # pylint: disable=import-outside-toplevel
        from include import cupdate    # pylint: disable=import-outside-toplevel
        fields = {'machine_id': cupdate.machine_id(), 'name': str(draft.data.get('name') or '').strip(),
                  'author': str(draft.data.get('author') or '').strip(), 'raspydarts_version': version,
                  'accept_terms': '1'}
        files.append(('theme', (os.path.basename(zip_path), open(zip_path, 'rb'), 'application/zip')))
        for name in draft.sent():
            files.append(('captures', (name, open(os.path.join(draft.folder, name), 'rb'), 'image/jpeg')))
        answer = requests.post(API, data=fields, files=files, headers={'X-API-Key': API_KEY}, timeout=(10, 600))
        outcome['status'] = answer.status_code
        try:
            outcome['answer'] = answer.json()
        except ValueError:
            outcome['answer'] = {}
    except Exception as error:    # pylint: disable=broad-except
        outcome['status'] = 0
        outcome['error'] = str(error)
    finally:
        for _field, (_name, handle, _kind) in files:
            handle.close()


def upload(screen, draft, zip_path):
    '''
    Envoyer : the theme and its captures sent to the API, the time shown ; sent : kept in the
    draft (id, version, date), the trophy to its player
    '''
    outcome = {}
    worker = threading.Thread(target=post, args=(draft, zip_path, theme_version(screen), outcome), daemon=True)
    started = time.time()
    worker.start()
    while worker.is_alive():
        screen.message([translate(screen, 'hub-sending').replace('{seconds}', str(int(time.time() - started)))],
                       0, None, 'middle', 'big')
        worker.join(0.5)
    status, answer = outcome.get('status', 0), outcome.get('answer') or {}
    if status == 201:
        draft.data['sent'] = {'id': answer.get('id'), 'version': answer.get('version'), 'date': time.strftime('%Y-%m-%d %H:%M')}
        draft.save()
        screen.logs.info(f"RaspyHub : theme {draft.data.get('name')} sent (id {answer.get('id')}, version "
                         f"{answer.get('version')}, {answer.get('state')})")
        screen.message([translate(screen, 'hub-sent')], 4000, 'menu-ok', 'middle', 'big')
        award(screen, draft.data.get('player'))
        # Its decision watched (said when it comes, wherever the borne is)
        check_news(screen)
        return
    code = str(answer.get('error') or '')
    screen.logs.error(f"RaspyHub : theme {draft.data.get('name')} not sent (HTTP {status}, {code or outcome.get('error')} "
                      f"{answer.get('message') or ''})")
    if status == 0:
        text = translate(screen, 'hub-send-failed')
    elif code in ERRORS:
        text = translate(screen, ERRORS[code])
    else:
        text = translate(screen, 'hub-send-refused').replace('{message}', str(answer.get('message') or code or status))
    screen.message([text], 5000, 'menu-ko', 'middle', 'big')


def theme_version(screen):
    try:
        from include import cupdate    # pylint: disable=import-outside-toplevel
        return cupdate.get_version(screen.logs)
    except Exception:    # pylint: disable=broad-except
        return getattr(screen.config, 'pyDartsVersion', '')


def choose_player(screen, draft):
    names = players(screen)
    if not names:
        screen.message([translate(screen, 'hub-no-player')], 2500, 'menu-ko', 'middle', 'big')
        return
    picked = screen.dropdown(screen.res['x'] * 6 / 16, 3 * screen.res_y_16, [[name, name] for name in names],
                             navigate=draft.data.get('player') or None, width=5 * screen.res_x_16)
    if picked in (None, False, 'escape') or picked not in names:
        return
    before = draft.data.get('player')
    draft.data['player'] = picked
    # The author : his name, unless another one was typed
    if not draft.data.get('author') or draft.data.get('author') == before:
        draft.data['author'] = picked
    draft.save()


def type_text(screen, value, most, key):
    typed = screen.input_value_item('string', str(value or ''), 1, most, text=key)
    if typed in (None, False, 'escape') or not str(typed).strip():
        return None
    return ' '.join(str(typed).split())[:most]


def export_screen(screen):
    '''
    Exporter le thème vers RaspyHub : on the left the main capture and the mention on the images,
    its settings, its commands
    '''
    from include import cmenueditor    # pylint: disable=import-outside-toplevel
    from include import cautodartsmenu    # pylint: disable=import-outside-toplevel
    from include.cscreen import DOWN_KEYS, ENTER_KEYS, ESCAPE_KEYS, UP_KEYS    # pylint: disable=import-outside-toplevel
    theme = str(screen.config.get_value('SectionGlobals', 'colorset') or '')
    if not theme or not os.path.isdir(getattr(screen.file_class, 'theme_dir', '') or ''):
        screen.message([translate(screen, 'theme-export-none')], 2500, 'menu-ko', 'middle', 'big')
        return
    draft = Draft(theme)
    unit_x, unit_y = screen.res['x'] / 16, screen.res['y'] / 16
    selected = 0
    shown_cache = {}
    while True:
        yes_no = translate(screen, 'yes' if draft.data.get('rights') else 'no')
        chosen = draft.chosen()
        entries = [('setting', 'name', 'hub-theme-name', str(draft.data.get('name') or '')),
                   ('setting', 'player', 'hub-player', draft.data.get('player') or translate(screen, 'hub-to-choose')),
                   ('setting', 'author', 'hub-author', str(draft.data.get('author') or '').strip() or translate(screen, 'hub-to-choose')),
                   ('setting', 'rights', 'hub-rights', yes_no),
                   ('command', 'generate', 'hub-generate', None),
                   ('command', 'choose', 'hub-choose', None if draft.captures() else 'greyed'),
                   ('command', 'capture', 'hub-capture', None),
                   ('command', 'send', 'hub-send', None),
                   ('back', 'back', 'back', None)]
        usable = [index for index, entry in enumerate(entries) if entry[3] != 'greyed']
        if selected not in usable:
            selected = min(usable, key=lambda index: abs(index - selected))

        screen.display_background()
        screen.menu_header(translate(screen, 'hub-export'), theme)
        # On the left : the main capture, the captures sent, the mention on the images
        left = pygame.Rect(int(0.5 * unit_x), int(3.0 * unit_y), int(4.2 * unit_x), int(11 * unit_y))
        line = int(unit_y * 0.6)
        main = os.path.join(draft.folder, 'auto-main.jpg')
        size = (left.width, int(left.width * 9 / 16))
        key = (main, os.path.getmtime(main) if os.path.isfile(main) else 0, size)
        if key not in shown_cache:
            shown_cache.clear()
            shown_cache[key] = picture(main, size) if os.path.isfile(main) else None
        text_y = left.y
        if shown_cache[key] is not None:
            image = shown_cache[key]
            screen.blit(image, (left.centerx - image.get_width() // 2, left.y))
            text_y += image.get_height() + screen.margin
        else:
            cmenueditor.paragraph(screen, translate(screen, 'hub-no-capture'), pygame.Rect(left.x, left.y, left.width, size[1]),
                                  screen.colorset['menu-text-white'])
            text_y += size[1] + screen.margin
        screen.blit_text(translate(screen, 'hub-captures-count').replace('{chosen}', str(len(chosen)))
                         .replace('{most}', str(EXTRA_MOST)), left.x, text_y, left.width, line, screen.colorset['menu-text-white'])
        text_y += line + screen.margin
        sent = draft.data.get('sent') or {}
        if sent.get('date'):
            # Sent before : sent again, its new version replaces it once validated
            screen.blit_text(translate(screen, 'hub-sent-on').replace('{date}', str(sent['date'])[:10])
                             .replace('{version}', str(sent.get('version') or 1)), left.x, text_y, left.width, line,
                             screen.colorset['menu-ok'])
            text_y += line + screen.margin
        warning = screen.colorset.get('menu-warning', screen.colorset['menu-ko'])
        cmenueditor.paragraph(screen, translate(screen, 'hub-rights-mention'),
                              pygame.Rect(left.x, text_y, left.width, int(14 * unit_y) - text_y), warning)

        zones = {}
        rows = {'setting': 0, 'command': 0}
        columns = {'setting': (5.0, 5.6), 'command': (11.0, 4.5)}
        for title, kind in (('hub-settings', 'setting'), ('hub-commands', 'command')):
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
                label = translate(screen, text)
                if ident == 'choose':
                    label = f"{label} ({len(chosen)}/{EXTRA_MOST})"
                cautodartsmenu.button(screen, rect, label, index == selected, greyed=value == 'greyed')
            if value != 'greyed':
                zones[index] = tuple(rect)
        screen.update_screen()

        key = screen.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'enter', 'space', 'PLAYERBUTTON', 'BACKUPBUTTON',
                                                          'GAMEBUTTON', 'single-click', 'resize'])
        if key == 'resize':
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
                selected = [index for index in usable if entries[index][0] == 'setting'][-1]
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
            if ident == 'name':
                typed = type_text(screen, draft.data.get('name'), 40, 'hub-theme-name-type')
                if typed:
                    draft.data['name'] = typed
                    draft.save()
            elif ident == 'player':
                choose_player(screen, draft)
            elif ident == 'author':
                typed = type_text(screen, draft.data.get('author'), 30, 'hub-author-type')
                if typed:
                    draft.data['author'] = typed.replace('#', '')
                    draft.save()
            elif ident == 'rights':
                draft.data['rights'] = not draft.data.get('rights')
                draft.save()
            elif ident == 'generate':
                generate(screen, draft)
            elif ident == 'choose':
                choose_captures(screen, draft)
            elif ident == 'capture':
                if start_capture(screen, draft):
                    # Back to the screens : the player goes where he wants
                    return
            elif ident == 'send':
                send(screen, draft)


def choose_captures(screen, draft):
    '''
    Choisir les captures : the captures there as tiles ; the 3 asked always sent, the others
    chosen (EXTRA_MOST at most) ; a capture taken can be deleted (Supprimer, Moins)
    '''
    from include.cscreen import DOWN_KEYS, ENTER_KEYS, ESCAPE_KEYS, LEFT_KEYS, RIGHT_KEYS, UP_KEYS    # pylint: disable=import-outside-toplevel
    columns = 4
    selected = 0
    thumbs = {}
    unit_x, unit_y = screen.res['x'] / 16, screen.res['y'] / 16
    while True:
        names = draft.captures()
        if not names:
            return
        chosen = draft.chosen()
        selected = max(0, min(selected, len(names)))
        screen.display_background()
        screen.menu_header(translate(screen, 'hub-choose'),
                           translate(screen, 'hub-captures-count').replace('{chosen}', str(len(chosen))).replace('{most}', str(EXTRA_MOST)))
        gap = int(unit_x * 0.3)
        width = int((screen.res['x'] - 2 * unit_x - (columns - 1) * gap) / columns)
        height = int(width * 9 / 16)
        rows_shown = max(1, int((11.2 * unit_y) // (height + gap + 0.5 * unit_y)))
        first_row = max(0, min(selected, len(names) - 1) // columns - rows_shown + 1)
        zones = {}
        for index, name in enumerate(names):
            row, column = divmod(index, columns)
            if not first_row <= row < first_row + rows_shown:
                continue
            rect = pygame.Rect(int(unit_x + column * (width + gap)), int(2.9 * unit_y + (row - first_row) * (height + gap + 0.5 * unit_y)),
                               width, height)
            path = os.path.join(draft.folder, name)
            stamp = (name, os.path.getmtime(path) if os.path.isfile(path) else 0)
            if stamp not in thumbs:
                thumbs[stamp] = picture(path, (width, height))
            image = thumbs[stamp]
            mandatory = draft.mandatory(name)
            on = mandatory or name in chosen
            if image is not None:
                if not on:
                    image = image.copy()
                    image.fill((90, 90, 90), special_flags=pygame.BLEND_RGB_MULT)
                screen.blit(image, image.get_rect(center=rect.center))
            color = ccapture.FRAME if mandatory else screen.colorset['menu-ok'] if on else (110, 110, 110)
            pygame.draw.rect(screen.screen, color, rect, 4 if on else 2)
            if index == selected:
                pygame.draw.rect(screen.screen, screen.colorset['menu-selected'], rect.inflate(10, 10), 4)
            label = translate(screen, 'hub-capture-asked' if mandatory else 'hub-capture-chosen' if on else 'hub-capture-not-chosen')
            screen.blit_text(label, rect.x, rect.bottom, rect.width, int(0.45 * unit_y), color, margin=False)
            zones[index] = tuple(rect)
        screen.blit_text(translate(screen, 'hub-choose-help'), 0, int(13.6 * unit_y), screen.res['x'], int(0.5 * unit_y),
                         screen.colorset['menu-text-white'])
        zones[len(names)] = screen.display_button(selected == len(names), 'back', special='escape')
        screen.update_screen()
        key = screen.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'enter', 'space', 'BACKUPBUTTON', 'single-click', 'delete',
                                                          'backspace', 'resize'])
        clicked = screen.is_clicked(zones, key)
        if clicked is not False and clicked is not None:
            selected, key = clicked, 'enter'
        if key in ESCAPE_KEYS or key == 'escape':
            return
        if key in RIGHT_KEYS:
            selected = min(len(names), selected + 1)
        elif key in LEFT_KEYS:
            selected = max(0, selected - 1)
        elif key in DOWN_KEYS:
            selected = min(len(names), selected + columns)
        elif key in UP_KEYS:
            selected = max(0, selected - columns) if selected < len(names) else len(names) - 1
        elif key in ENTER_KEYS + ['space']:
            if selected == len(names):
                return
            name = names[selected]
            if draft.mandatory(name):
                screen.message([translate(screen, 'hub-capture-asked-why')], 2000, None, 'middle', 'big')
            elif name in chosen:
                chosen.remove(name)
            elif len(chosen) >= EXTRA_MOST:
                screen.message([translate(screen, 'hub-choose-full').replace('{most}', str(EXTRA_MOST))], 2500, 'menu-ko',
                               'middle', 'big')
            else:
                chosen.append(name)
            draft.data['chosen'] = chosen
            draft.save()
        elif key in ('delete', 'backspace', 'BTN_MINUS', 'VOLUME-DOWN', 'BTN_VOLUME_DOWN') and selected < len(names):
            name = names[selected]
            if not name.startswith('free-'):
                screen.message([translate(screen, 'hub-delete-only-free')], 2000, None, 'middle', 'big')
            elif screen.wait_validation(translate(screen, 'hub-delete-question')):
                try:
                    os.remove(os.path.join(draft.folder, name))
                except OSError:
                    pass
                draft.data['chosen'] = [item for item in chosen if item != name]
                draft.save()


# ---------------------------------------------------------------------- the themes of this borne
# The decisions on its themes already said (accepted, refused) : {"<id>:<version>": state}
NEWS_FILE = os.path.join(cpaths.user_dir(), 'raspyhub', 'notified.json')


def has_sent():
    '''
    A theme was sent from this borne (draft.json of an export with « sent ») : only then the
    server is asked about its themes
    '''
    folder = os.path.join(cpaths.user_dir(), 'raspyhub', 'export')
    try:
        names = os.listdir(folder)
    except OSError:
        return False
    for name in names:
        try:
            with open(os.path.join(folder, name, 'draft.json'), encoding='utf-8') as source:
                if json.load(source).get('sent'):
                    return True
        except (OSError, ValueError, AttributeError):
            continue
    return False


def mine(logs):
    '''
    The themes sent from this borne, as the server knows them (GET .../mine) : [{id, name,
    version, state (pending, published, refused, removed), reason, published_version, sent_at,
    decided_at}] ; None : not read
    '''
    try:
        import requests    # pylint: disable=import-outside-toplevel
        from include import cupdate    # pylint: disable=import-outside-toplevel
        machine = cupdate.machine_id()
        if not machine:
            return None
        answer = requests.get(f"{API}/mine", params={'machine_id': machine}, headers={'X-API-Key': API_KEY}, timeout=8)
        answer.raise_for_status()
        themes = answer.json().get('themes')
        return [theme for theme in themes if isinstance(theme, dict) and theme.get('id') is not None]
    except Exception as error:    # pylint: disable=broad-except
        logs.warning(f"RaspyHub : themes of this borne not read ({error})")
        return None


def delete_hub(logs, theme_id):
    '''
    A theme of this borne deleted from RaspyHub (DELETE .../<id>) : for good, all its versions.
    (True, '') when done ; (False, the error : not_owner, not_found, the message...)
    '''
    try:
        import requests    # pylint: disable=import-outside-toplevel
        from include import cupdate    # pylint: disable=import-outside-toplevel
        answer = requests.delete(f"{API}/{int(theme_id)}", json={'machine_id': cupdate.machine_id()},
                                 headers={'X-API-Key': API_KEY}, timeout=15)
        if answer.status_code == 200:
            logs.info(f"RaspyHub : theme {theme_id} deleted")
            return True, ''
        try:
            code = answer.json().get('error') or str(answer.status_code)
        except ValueError:
            code = str(answer.status_code)
        logs.error(f"RaspyHub : theme {theme_id} not deleted (HTTP {answer.status_code}, {code})")
        return False, code
    except Exception as error:    # pylint: disable=broad-except
        logs.error(f"RaspyHub : theme {theme_id} not deleted ({error})")
        return False, str(error)


def news(themes):
    '''
    The decisions not said yet on the themes of this borne : [(name, state, reason, key)], state
    published or refused, once by version (see said)
    '''
    try:
        with open(NEWS_FILE, encoding='utf-8') as source:
            known = json.load(source)
    except (OSError, ValueError):
        known = {}
    found = []
    for theme in themes or []:
        state = theme.get('state')
        if state not in ('published', 'refused') or not theme.get('decided_at'):
            continue
        key = f"{theme.get('id')}:{theme.get('version')}"
        if known.get(key) == state:
            continue
        found.append((str(theme.get('name') or '?'), state, theme.get('reason'), key))
    return found


def said(items):
    '''
    These decisions said : not again
    '''
    try:
        with open(NEWS_FILE, encoding='utf-8') as source:
            known = json.load(source)
    except (OSError, ValueError):
        known = {}
    for _name, state, _reason, key in items:
        known[key] = state
    try:
        os.makedirs(os.path.dirname(NEWS_FILE), exist_ok=True)
        with open(NEWS_FILE + '.tmp', 'w', encoding='utf-8') as target:
            json.dump(known, target, indent=1)
        os.replace(NEWS_FILE + '.tmp', NEWS_FILE)
    except OSError:
        pass


def news_text(screen, item):
    '''
    The window of a decision : accepted (in Télécharger depuis RaspyHub), refused (its reason)
    '''
    name, state, reason, _key = item
    if state == 'published':
        return translate(screen, 'hub-news-published').replace('{name}', name)
    if reason:
        return translate(screen, 'hub-news-refused-reason').replace('{name}', name).replace('{reason}', str(reason))
    return translate(screen, 'hub-news-refused').replace('{name}', name)


def show_news(screen, items):
    '''
    The decisions shown one after the other, then marked as said
    '''
    for item in items:
        screen.message([news_text(screen, item)], 5000, 'menu-ok' if item[1] == 'published' else 'menu-ko', 'middle', 'big')
    said(items)


def news_short(screen, item):
    '''
    A decision in the activity indicator (a corner of the screen) : a few words
    '''
    name, state, _reason, _key = item
    return translate(screen, f'hub-news-{state}-short').replace('{name}', name)


def show_news_corner(screen, items):
    '''
    A screen which is not a menu (settings, Modifier les écrans...) : the decisions in the
    activity indicator, a while, then marked as said (a window would hide the screen)
    '''
    for item in items:
        text = news_short(screen, item)
        screen.activities.add(f'hub-news-{item[3]}',
                              lambda text=text: {'text': text, 'final': True, 'final_time': NEWS_CORNER_TIME})
    said(items)


# A theme of this borne waiting : the server asked again this often (seconds)
WATCH_EVERY = 300
NEWS_CORNER_TIME = 20
_watching = threading.Lock()


def check_news(screen):
    '''
    At the start, and after a theme is sent : the themes of this borne asked in the background
    (only when it sent one), again every WATCH_EVERY while one waits for its decision ; the
    decisions given to the screen (screen.hub_news), said wherever the borne is out of the
    games (Screen.idle_turn)
    '''
    if not has_sent() or not _watching.acquire(blocking=False):
        return

    def watch():
        try:
            while True:
                themes = mine(screen.logs)
                found = news(themes)
                if found:
                    screen.hub_news = found
                if themes is not None and not any(theme.get('state') == 'pending' for theme in themes):
                    return
                time.sleep(WATCH_EVERY)
        finally:
            _watching.release()
    threading.Thread(target=watch, daemon=True).start()
