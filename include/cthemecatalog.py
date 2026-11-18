"""
Modifier les écrans > Importer un thème > Télécharger depuis RaspyHub : the themes validated on
RaspyHub (the API of the themes, include/cthemehub.py).

- The catalogue read again at each opening : on the left its themes (the most recent first ; the
  one installed here, or its update), on the right their captures (one after the other every few
  seconds, or with the arrows), what is known of the theme under them.
- Télécharger : the zip through the address given by the catalogue (it can lead elsewhere :
  Google Drive), then installed as an imported theme (include/cthemefiles.py), its id and its
  version kept with it, then « Appliquer le thème ? ».
- The captures kept in ~/.raspydarts/raspyhub/cache (CACHE_MOST at most, the oldest deleted) ;
  never an address kept : the catalogue gives them each time.
"""

import html
import os
import re
import shutil
import threading
import time

import pygame

from include import cpaths
from include import cthemehub

CACHE_MOST = 50 * 1024 ** 2
# A capture shown this long, then the next one
TURN = 4.0
# A theme bigger than this : its size said before it is downloaded
BIG = 100 * 1024 ** 2
# The wheel of a knob : through the themes and the buttons (the arrows of the keyboard : the captures)
WHEEL = {'BTN_RIGHT': 1, 'BTN_LEFT': -1}


def translate(screen, key):
    return screen.lang.translate(key)


def cache_dir():
    return os.path.join(cpaths.user_dir(), 'raspyhub', 'cache')


def version_tuple(text):
    return tuple(int(part) for part in re.findall(r'\d+', str(text or '')))


def installed(screen):
    '''
    The themes of RaspyHub installed here : their id -> (version, folder)
    '''
    import json    # pylint: disable=import-outside-toplevel
    from include import cthemefiles    # pylint: disable=import-outside-toplevel
    found = {}
    folder = cthemefiles.themes_dir(screen)
    try:
        names = os.listdir(folder)
    except OSError:
        return found
    for name in names:
        try:
            with open(os.path.join(folder, name, cthemefiles.HUB_FILE), encoding='utf-8') as source:
                origin = json.load(source)
            found[origin['id']] = (int(origin.get('version') or 0), name)
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return found


def read_catalog(logs):
    '''
    The themes validated (a list), None : not read
    '''
    try:
        import requests    # pylint: disable=import-outside-toplevel
        answer = requests.get(cthemehub.API, timeout=10)
        answer.raise_for_status()
        themes = answer.json().get('themes')
        return [theme for theme in themes if isinstance(theme, dict) and theme.get('id') is not None]
    except Exception as error:    # pylint: disable=broad-except
        logs.error(f"RaspyHub : catalogue not read ({error})")
        return None


def trim_cache():
    '''
    The cache of the captures kept under CACHE_MOST : the oldest deleted
    '''
    try:
        files = [os.path.join(cache_dir(), name) for name in os.listdir(cache_dir())]
        files = sorted((os.path.getmtime(path), os.path.getsize(path), path) for path in files if os.path.isfile(path))
    except OSError:
        return
    total = sum(size for _when, size, _path in files)
    for _when, size, path in files:
        if total <= CACHE_MOST:
            break
        try:
            os.remove(path)
            total -= size
        except OSError:
            pass


class Captures:
    '''
    The captures of the catalogue : read in the background, kept in the cache ; path() : the file
    when it is there, else None (asked)
    '''

    def __init__(self, logs):
        self.logs = logs
        self.asked = set()
        self.failed = set()
        os.makedirs(cache_dir(), exist_ok=True)

    @staticmethod
    def file(theme, number):
        return os.path.join(cache_dir(), f"{theme['id']}-v{theme.get('version') or 1}-{number}.jpg")

    def path(self, theme, number):
        path = self.file(theme, number)
        if os.path.isfile(path):
            return path
        urls = theme.get('capture_urls') or []
        if number <= len(urls) and path not in self.asked:
            self.asked.add(path)
            threading.Thread(target=self.fetch, args=(urls[number - 1], path), daemon=True).start()
        return None

    def fetch(self, url, path):
        try:
            import requests    # pylint: disable=import-outside-toplevel
            answer = requests.get(url, timeout=15)
            answer.raise_for_status()
            with open(path + '.part', 'wb') as written:
                written.write(answer.content)
            os.replace(path + '.part', path)
            trim_cache()
        except Exception as error:    # pylint: disable=broad-except
            self.failed.add(path)
            self.logs.warning(f"RaspyHub : capture {url} not read ({error})")


def past_warning(session, answer):
    '''
    A big file of Google Drive : a page « impossible to scan it for viruses » comes first, its
    form sent again gives the file. Any other answer : as it is
    '''
    if 'text/html' not in answer.headers.get('Content-Type', ''):
        return answer
    page = answer.text
    answer.close()
    form = re.search(r'<form[^>]*action="([^"]+)"[^>]*>(.*?)</form>', page, re.S)
    if not form:
        raise ValueError('a page instead of the zip')
    fields = dict(re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]*)"', form.group(2)))
    return session.get(html.unescape(form.group(1)), params=fields, stream=True, timeout=(10, 60))


def download(screen, theme):
    '''
    The zip of the theme read (the address of the catalogue, its redirections followed), its
    progress shown ; returns its file, or None
    '''
    from include import cthemefiles    # pylint: disable=import-outside-toplevel
    folder = os.path.join(cthemefiles.themes_dir(screen), '.download')
    shutil.rmtree(folder, ignore_errors=True)
    os.makedirs(folder, exist_ok=True)
    target = os.path.join(folder, f"raspyhub-{theme['id']}.zip")
    state = {'done': 0, 'total': int(theme.get('size') or 0), 'error': None, 'finished': False}

    def run():
        try:
            import requests    # pylint: disable=import-outside-toplevel
            session = requests.Session()
            answer = session.get(theme['download_url'], stream=True, timeout=(10, 60), allow_redirects=True)
            answer = past_warning(session, answer)
            with answer:
                answer.raise_for_status()
                if 'text/html' in answer.headers.get('Content-Type', ''):
                    raise ValueError('a page instead of the zip')
                state['total'] = int(answer.headers.get('Content-Length') or state['total'] or 0)
                with open(target, 'wb') as written:
                    for block in answer.iter_content(256 * 1024):
                        written.write(block)
                        state['done'] += len(block)
                        if state['done'] > cthemefiles.IMPORT_LIMIT:
                            raise ValueError('too big')
        except Exception as error:    # pylint: disable=broad-except
            state['error'] = error
        state['finished'] = True

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    while not state['finished']:
        percent = int(100 * state['done'] / state['total']) if state['total'] else 0
        screen.message([translate(screen, 'hub-downloading').replace('{percent}', str(min(percent, 100)))], 0, None,
                       'middle', 'big')
        worker.join(0.3)
    if state['error'] is not None:
        screen.logs.error(f"RaspyHub : theme {theme.get('name')} (id {theme['id']}) not downloaded ({state['error']})")
        shutil.rmtree(folder, ignore_errors=True)
        screen.message([translate(screen, 'hub-download-failed')], 3500, 'menu-ko', 'middle', 'big')
        return None
    screen.logs.info(f"RaspyHub : theme {theme.get('name')} (id {theme['id']}, version {theme.get('version')}) "
                     f"downloaded ({state['done'] // 1024} KB)")
    return target


def take(screen, theme):
    '''
    Télécharger : the theme downloaded, installed (its id and version kept), applied if wanted
    '''
    from include import cthemefiles    # pylint: disable=import-outside-toplevel
    needed = theme.get('raspydarts_min_version')
    if needed and version_tuple(needed) > version_tuple(cthemehub.theme_version(screen)):
        if not screen.ask_yes_no(translate(screen, 'hub-needs-version').replace('{version}', str(needed)),
                                 translate(screen, 'hub-needs-version-explain')):
            return
    # A big theme (its videos) : its size said first, the room on the card checked (the zip, then
    # the theme unpacked beside it)
    size = int(theme.get('size') or 0)
    try:
        free = shutil.disk_usage(cthemefiles.themes_dir(screen)).free
    except OSError:
        free = None
    if free is not None and free < 2.2 * size + 200 * 1024 ** 2:
        screen.message([translate(screen, 'hub-no-room').replace('{size}', f"{size / 1048576:.0f}")
                        .replace('{free}', f"{free / 1048576:.0f}")], 5000, 'menu-ko', 'middle', 'big')
        return
    if size > BIG and not screen.ask_yes_no(translate(screen, 'hub-download-big').replace('{size}', f"{size / 1048576:.0f}"),
                                            translate(screen, 'hub-download-big-explain')):
        return
    zip_path = download(screen, theme)
    if zip_path is None:
        return
    name = re.sub(r'[^\w.-]+', '_', str(theme.get('name') or '')).strip('._') or None
    origin = {'id': theme['id'], 'version': theme.get('version'), 'name': theme.get('name'),
              'author': theme.get('author'), 'installed': time.strftime('%Y-%m-%d %H:%M')}
    try:
        cthemefiles.install(screen, zip_path, origin=origin, name=name)
    finally:
        shutil.rmtree(os.path.dirname(zip_path), ignore_errors=True)


def details(screen, theme, here):
    '''
    What is known of a theme : its author, its date, its size, its media ; installed here or not
    '''
    date = str(theme.get('updated_at') or theme.get('created_at') or '')[:10]
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
        date = '/'.join(reversed(date.split('-')))
    parts = [translate(screen, 'hub-by').replace('{author}', str(theme.get('author') or '?')),
             translate(screen, 'hub-updated').replace('{date}', date),
             translate(screen, 'hub-size').replace('{size}', f"{int(theme.get('size') or 0) / 1048576:.1f}"),
             translate(screen, 'hub-with-media' if theme.get('with_media') else 'hub-without-media')]
    return ' - '.join(parts), status(screen, theme, here)


def status(screen, theme, here):
    '''
    Installed here, its update, or nothing
    '''
    if theme['id'] not in here:
        return ''
    version = here[theme['id']][0]
    return translate(screen, 'hub-update-available' if int(theme.get('version') or 0) > version else 'hub-installed')


def catalog_screen(screen):
    '''
    Télécharger depuis RaspyHub : the list of the themes, their captures, Télécharger
    '''
    from include import cautodartsmenu    # pylint: disable=import-outside-toplevel
    from include import cmenueditor    # pylint: disable=import-outside-toplevel
    from include.cscreen import DOWN_KEYS, ENTER_KEYS, ESCAPE_KEYS, LEFT_KEYS, RIGHT_KEYS, UP_KEYS    # pylint: disable=import-outside-toplevel
    screen.message([translate(screen, 'hub-catalog-loading')], 0, None, 'middle', 'big')
    themes = read_catalog(screen.logs)
    if themes is None:
        screen.message([translate(screen, 'hub-catalog-failed')], 3500, 'menu-ko', 'middle', 'big')
        return
    if not themes:
        screen.message([translate(screen, 'hub-catalog-empty')], 3500, None, 'middle', 'big')
        return
    captures = Captures(screen.logs)
    here = installed(screen)
    unit_x, unit_y = screen.res['x'] / 16, screen.res['y'] / 16
    selected, number, focus = 0, 1, 'list'
    turned = time.time()
    shown = {}
    rows_shown = 8
    while True:
        theme = themes[selected]
        count = max(1, int(theme.get('captures') or len(theme.get('capture_urls') or []) or 1))
        number = max(1, min(number, count))
        screen.display_background()
        screen.menu_header(translate(screen, 'theme-import-raspyhub'),
                           translate(screen, 'hub-catalog-count').replace('{count}', str(len(themes))))
        zones = {}
        # On the left : the themes
        first = max(0, min(selected - rows_shown + 1, len(themes) - rows_shown)) if selected >= rows_shown else 0
        for row, index in enumerate(range(first, min(len(themes), first + rows_shown))):
            rect = pygame.Rect(int(0.5 * unit_x), int((3.0 + row * 1.25) * unit_y), int(5.0 * unit_x), int(1.05 * unit_y))
            label = str(themes[index].get('name') or '?')
            mark = status(screen, themes[index], here)
            if mark:
                label = f"{label} ({mark})"
            cautodartsmenu.button(screen, rect, label, index == selected and focus == 'list')
            if index == selected and focus != 'list':
                pygame.draw.rect(screen.screen, screen.colorset['menu-selected'], rect, 3, border_radius=int(rect.height / 4))
            zones[('theme', index)] = tuple(rect)
        # On the right : its capture, what is known of it
        area = pygame.Rect(int(6.0 * unit_x), int(3.0 * unit_y), int(9.5 * unit_x), int(7.6 * unit_y))
        path = captures.path(theme, number)
        if path is not None:
            key = (path, area.size)
            if key not in shown:
                if len(shown) > 12:
                    shown.clear()
                shown[key] = cthemehub.picture(path, area.size)
            image = shown[key]
        else:
            image = None
        if image is not None:
            screen.blit(image, image.get_rect(center=area.center))
        else:
            waiting = 'hub-capture-unavailable' if captures.file(theme, number) in captures.failed else 'hub-capture-loading'
            cmenueditor.paragraph(screen, translate(screen, waiting), area, screen.colorset['menu-text-white'])
        zones['previous'] = (area.x, area.y, area.width // 2, area.height)
        zones['next'] = (area.centerx, area.y, area.width - area.width // 2, area.height)
        line = int(0.55 * unit_y)
        info, mark = details(screen, theme, here)
        screen.blit_text(f"< {number} / {count} >", area.x, area.bottom + int(0.1 * unit_y), area.width, line,
                         screen.colorset['menu-text-white'])
        screen.blit_text(info, area.x, area.bottom + int(0.75 * unit_y), area.width, line, screen.colorset['menu-text-white'])
        if mark:
            screen.blit_text(mark, area.x, area.bottom + int(1.35 * unit_y), area.width, line, screen.colorset['menu-ok'])
        rect = pygame.Rect(int(8.75 * unit_x), int(12.4 * unit_y), int(4.0 * unit_x), int(1.0 * unit_y))
        cautodartsmenu.button(screen, rect, translate(screen, 'hub-download-button'), focus == 'download')
        zones['download'] = tuple(rect)
        screen.blit_text(translate(screen, 'hub-catalog-help'), 0, int(13.6 * unit_y), screen.res['x'], int(0.5 * unit_y),
                         screen.colorset['menu-text-white'])
        zones['back'] = screen.display_button(focus == 'back', 'back', special='escape')
        screen.update_screen()

        key = screen.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'enter', 'space', 'BACKUPBUTTON', 'single-click', 'resize'],
                                       timeout=300)
        if key is False or key is None or key == 'resize':
            # Nothing pressed : the next capture after a while
            if time.time() - turned >= TURN and count > 1:
                number = number % count + 1
                turned = time.time()
            continue
        clicked = screen.is_clicked(zones, key)
        if clicked is not False and clicked is not None:
            if isinstance(clicked, tuple):
                # A theme touched : chosen ; touched again : Télécharger chosen (as Valider)
                focus = 'download' if clicked[1] == selected else 'list'
                if clicked[1] != selected:
                    selected, number, turned = clicked[1], 1, time.time()
                continue
            if clicked in ('previous', 'next'):
                key = 'left' if clicked == 'previous' else 'right'
            else:
                focus, key = clicked, 'enter'
        if key in ESCAPE_KEYS or key == 'escape':
            return
        if key in WHEEL:
            # The wheel of a knob : the themes, then Retour, then Télécharger (and round again)
            places = [('list', index) for index in range(len(themes))] + [('back', None), ('download', None)]
            here_at = places.index(('list', selected)) if focus == 'list' else places.index((focus, None))
            focus, index = places[(here_at + WHEEL[key]) % len(places)]
            if focus == 'list' and index != selected:
                selected, number, turned = index, 1, time.time()
        elif key in LEFT_KEYS:
            number = (number - 2) % count + 1
            turned = time.time()
        elif key in RIGHT_KEYS:
            number = number % count + 1
            turned = time.time()
        elif key in DOWN_KEYS:
            if focus == 'list' and selected + 1 < len(themes):
                selected, number, turned = selected + 1, 1, time.time()
            elif focus == 'list':
                focus = 'download'
            elif focus == 'download':
                focus = 'back'
        elif key in UP_KEYS:
            if focus == 'back':
                focus = 'download'
            elif focus == 'download':
                focus = 'list'
            elif selected > 0:
                selected, number, turned = selected - 1, 1, time.time()
        elif key in ENTER_KEYS + ['space']:
            if focus == 'back':
                return
            if focus == 'list':
                # Valider on a theme : Télécharger chosen (one more Valider downloads it)
                focus = 'download'
                continue
            take(screen, theme)
            here = installed(screen)
            turned = time.time()
