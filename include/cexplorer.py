"""
Explorer of the files of the borne (Modifier les écrans : background of a menu, images of a
button, video of the animated background) : the folders and the files on the left, the file
chosen shown on the right (a video : played in its box) ; any folder of the card, the USB keys,
the images of the theme and of the game
"""

import filecmp
import os
import shutil
import subprocess
import threading
import time

import pygame

from include import cemoji
from include import cpaths

IMAGES = ('.png', '.jpg', '.jpeg')
# The videos (animated background) : read by ffmpeg
VIDEOS = ('.mp4', '.gif', '.webm', '.mkv', '.mov', '.m4v', '.avi')
# The USB keys : mounted in these folders
MOUNTS = ('/media', '/mnt')
# Lines of the list shown at once
ROWS = 10
# Previews kept (an image read and scaled : up to 1 s on a Pi 3)
PREVIEWS = 24
# Icons of the lines (colour emojis) ; up : a folder with an arrow, drawn
ICONS = {'dir': '\U0001F4C1', 'open': '\U0001F4C2', 'file': '\U0001F5BC', 'extra': '\U0001F3A8',
         'theme': '\U0001F3A8', 'mine': '\U0001F5BC', 'game': '\U0001F3AF', 'usb': '\U0001F4BE',
         'home': '\U0001F3E0', 'card': '\U0001F4BD', 'arrow': '\u2B06', 'none': '\U0001F6AB',
         'video': '\U0001F3AC', 'pick': '\u2705', 'effect': '\u2728', 'scenes': '\U0001F30C',
         'rate': '\u23F1', 'scene': '\U0001F320'}


def places(screen, translate, kinds=IMAGES):
    '''
    The first list : the folders of images of the theme, of ~/.raspydarts and of the game (the
    videos of the theme for the videos ; none for a path or a zip), the USB keys, the home, the
    whole card
    '''
    found = []
    theme_dir = getattr(screen.file_class, 'theme_dir', None)
    if kinds == IMAGES:
        folders = ((os.path.join(theme_dir, 'images') if theme_dir else None, 'explorer-theme-images', 'theme'),
                   (os.path.join(cpaths.user_dir(), 'images'), 'explorer-my-images', 'mine'),
                   (os.path.join(cpaths.ROOT_DIR, 'images'), 'explorer-game-images', 'game'))
    elif kinds == VIDEOS:
        folders = ((os.path.join(theme_dir, 'videos') if theme_dir else None, 'explorer-theme-videos', 'theme'),
                   (os.path.join(cpaths.user_dir(), 'images', 'fond_anime'), 'explorer-my-videos', 'mine'))
    else:
        folders = ()
    for path, label, icon in folders:
        if path and os.path.isdir(path):
            found.append({'kind': 'dir', 'path': path, 'label': translate(label), 'icon': icon})
    for base in MOUNTS:
        for root, folders, _files in os.walk(base):
            if root.count(os.sep) - base.count(os.sep) >= 2:
                folders.clear()
            if os.path.ismount(root) and root != base:
                found.append({'kind': 'dir', 'path': root, 'icon': 'usb',
                              'label': f"{translate('editor-import-usb')} : {os.path.basename(root)}"})
    home = os.path.expanduser('~')
    found.append({'kind': 'dir', 'path': home, 'label': f"{translate('editor-import-home')} ({home})", 'icon': 'home'})
    found.append({'kind': 'dir', 'path': os.sep, 'label': translate('editor-import-root'), 'icon': 'card'})
    return found


def listing(folder, translate, kinds=IMAGES):
    '''
    A folder : the folder above, its folders, its files of these kinds (images, videos)
    '''
    try:
        entries = sorted((entry for entry in os.scandir(folder) if not entry.name.startswith('.')),
                         key=lambda entry: entry.name.lower())
    except OSError:
        entries = []
    found = [{'kind': 'up', 'path': None, 'label': translate('editor-import-up')}]
    found += [{'kind': 'dir', 'path': entry.path, 'label': entry.name}
              for entry in entries if entry.is_dir() and not loops(entry, folder)]
    found += [{'kind': 'file', 'path': entry.path, 'label': entry.name}
              for entry in entries if entry.is_file() and entry.name.lower().endswith(kinds)]
    return found


def loops(entry, folder):
    '''
    A link to this folder or to a folder above it (/usr/bin/X11 -> .) : opened, it showed the
    same folder again and again
    '''
    if not entry.is_symlink():
        return False
    target = os.path.realpath(entry.path)
    here = os.path.realpath(folder)
    return here == target or here.startswith(target.rstrip(os.sep) + os.sep)


def explore(screen, title, current=None, extra=(), kinds=IMAGES, pick_folder=False, places_shown=True, subtitle=None,
            initial=None):
    '''
    An image chosen : its full path ; or the id of one of the extra choices given first
    ((id, text[, image shown]) : the one of the theme, none...) ; None : given up. current : the
    image of the moment, the explorer opens in its folder. Back goes up to the place where the
    browsing started (the image of the moment : the place holding it), then to the places.
    kinds : the files shown (IMAGES, VIDEOS : a video is played in the box of the preview) ;
    pick_folder : a folder can be chosen (the button « Choisir ce dossier » over Back, in a folder) ;
    an extra choice (id, text, image, preview) : preview(screen, box) gives what is played in the
    box while it is selected (see VideoPreview) ; places_shown False : the extra choices only
    '''
    translate = screen.lang.translate
    previews = {'kinds': kinds, 'subtitle': subtitle, 'pick': pick_folder}
    folder = root = None
    # An extra choice selected first (initial : its id)
    selected = next((index for index, choice in enumerate(extra) if choice[0] == initial), 0)
    if current and os.path.isfile(current):
        folder = os.path.dirname(current)
        # Its place : the deepest one holding it
        holding = [place['path'] for place in places(screen, translate, kinds)
                   if folder == place['path'] or folder.startswith(place['path'].rstrip(os.sep) + os.sep)]
        root = max(holding, key=len) if holding else os.sep
    try:
        return browse(screen, title, current, extra, kinds, previews, folder, root, selected, pick_folder, places_shown)
    finally:
        player = previews.get('player')
        if player is not None:
            player.stop()
        screen.idle_hook = None


def browse(screen, title, current, extra, kinds, previews, folder, root, selected, pick_folder=False, places_shown=True):
    '''
    The browsing of explore (its video played until it returns)
    '''
    # pylint: disable=import-outside-toplevel,too-many-arguments
    from include.cscreen import DOWN_KEYS, ENTER_KEYS, ESCAPE_KEYS, LEFT_KEYS, RIGHT_KEYS, UP_KEYS
    translate = screen.lang.translate
    while True:
        if folder is None:
            # (no image : its own icon)
            entries = [{'kind': 'extra', 'path': choice[0], 'label': choice[1],
                        'image': choice[2] if len(choice) > 2 else None,
                        'preview': choice[3] if len(choice) > 3 else None,
                        'icon': choice[0] if choice[0] in ICONS else ('scene' if len(choice) > 3 and choice[3] else None)}
                       for choice in extra]
            if places_shown:
                entries += places(screen, translate, kinds)
        else:
            entries = listing(folder, translate, kinds)
            if current:
                # The image of the moment selected first
                selected = next((index for index, entry in enumerate(entries) if entry['path'] == current), selected)
                current = None
        # The button « Choisir ce dossier » : after the lines (in a folder)
        picking = pick_folder and folder is not None
        count = len(entries) + (1 if picking else 0)
        selected = max(0, min(selected, count - 1))
        started = time.perf_counter()
        zones = draw(screen, title, folder, entries, selected, previews, translate)
        spent = time.perf_counter() - started
        if spent > 0.5:
            screen.logs.warning(f"Explorer : drawn in {spent:.1f} s ({folder or 'places'}, line {selected})")
        # Drawing an image took up to 1 s : the keys repeated meanwhile dropped
        pygame.event.clear(pygame.KEYDOWN)
        key = screen.rpi.listen_inputs(['arrows'], ['escape', 'enter', 'space', 'single-click', 'PLAYERBUTTON',
                                                    'BACKUPBUTTON', 'GAMEBUTTON'])
        clicked = screen.is_clicked(zones, key)
        # (False : no click ; 0 : the first line)
        if clicked == 'escape':
            key = 'escape'
        elif clicked == 'pick':
            return folder
        elif clicked is not False and clicked is not None:
            if clicked == selected:
                key = 'enter'
            else:
                selected = clicked
                continue
        # The wheel of a knob : the lines (its press opens, held : back)
        if key == 'BTN_RIGHT':
            key = 'down'
        elif key == 'BTN_LEFT':
            key = 'up'
        entry = entries[selected] if selected < len(entries) else None
        if picking and selected == len(entries) and key in ENTER_KEYS + ['space']:
            return folder
        if key in UP_KEYS:
            selected = (selected - 1) % max(1, count)
        elif key in DOWN_KEYS:
            selected = (selected + 1) % max(1, count)
        elif key in ESCAPE_KEYS + LEFT_KEYS or (key in ENTER_KEYS + ['space'] and entry and entry['kind'] == 'up'):
            if folder is None:
                if key in ESCAPE_KEYS:
                    return None
                continue
            # The folder above, the one left selected ; above the place where the browsing
            # started : the places, this one selected
            current_folder = folder
            if folder == root or folder == os.sep:
                folder = root = None
                selected = next((index for index, item in enumerate(places(screen, translate, kinds))
                                 if item['path'] == current_folder), 0) + len(extra)
            else:
                folder = os.path.dirname(folder.rstrip(os.sep)) or os.sep
                selected = next((index for index, item in enumerate(listing(folder, translate, kinds))
                                 if item['path'] == current_folder), 0)
        elif entry and (key in ENTER_KEYS + ['space'] or (key in RIGHT_KEYS and entry['kind'] == 'dir')):
            if entry['kind'] == 'dir':
                if folder is None:
                    # A place : Back comes back to the places from it
                    root = entry['path']
                folder, selected = entry['path'], 0
            elif entry['kind'] in ('file', 'pick'):
                return entry['path']
            elif entry['kind'] == 'extra':
                return entry['path']


def icon(kind, size, icons):
    '''
    The icon of a line at this height (an emoji ; up : a folder and an arrow), None without
    the emoji font
    '''
    key = (kind, size)
    if key not in icons:
        font = cemoji.emoji_font()
        surface = None
        if font is not None:
            def emoji(char, height):
                picture = font.render(char, True, (255, 255, 255))
                return pygame.transform.smoothscale(picture, (max(1, round(picture.get_width() * height / picture.get_height())),
                                                              height))
            surface = emoji(ICONS['dir' if kind == 'up' else kind], size)
            if kind == 'up':
                # The folder above : an arrow over the folder
                arrow = emoji(ICONS['arrow'], int(size * 0.62))
                surface = surface.copy()
                surface.blit(arrow, ((surface.get_width() - arrow.get_width()) // 2, int(size * 0.3)))
        icons[key] = surface
    return icons[key]


def folder_text(path, translate, counts, kinds=IMAGES):
    '''
    What a folder holds : its folders and its images (its videos)
    '''
    if path not in counts:
        try:
            entries = [entry for entry in os.scandir(path) if not entry.name.startswith('.')]
            folders = sum(1 for entry in entries if entry.is_dir())
            files = sum(1 for entry in entries if entry.is_file() and entry.name.lower().endswith(kinds))
            text = translate({VIDEOS: 'explorer-holds-videos', IMAGES: 'explorer-holds'}.get(kinds, 'explorer-holds-files'))
            counts[path] = text.replace('{folders}', str(folders)).replace('{images}', str(files)) \
                .replace('{videos}', str(files)).replace('{files}', str(files))
        except OSError:
            counts[path] = ''
    return counts[path]


def draw(screen, title, folder, entries, selected, previews, translate):
    '''
    The explorer : the list on the left (around the line selected, each line with its icon),
    the preview on the right (an image, or what a folder holds). Returns the places to click :
    the lines (their index) and Back
    '''
    colorset = screen.colorset
    res_x, res_y = screen.res['x'], screen.res['y']
    unit_x, unit_y = res_x / 16, res_y / 16
    icons = previews.setdefault('icons', {})
    counts = previews.setdefault('counts', {})
    screen.display_background()
    screen.menu_header(title, folder if folder is not None else (previews.get('subtitle') or translate('explorer-places')))
    zones = {}
    # The list
    picking = previews.get('pick') and folder is not None
    top = max(0, min(min(selected, len(entries) - 1) - ROWS // 2, len(entries) - ROWS))
    unit_x, unit_y = res_x / 16, res_y / 16
    line_h = int(unit_y * 0.9)
    for row, index in enumerate(range(top, min(top + ROWS, len(entries)))):
        entry = entries[index]
        rect = pygame.Rect(int(unit_x), int(3.2 * unit_y + row * (line_h + 4)), int(7 * unit_x), line_h)
        chosen = index == selected
        screen.new_blit_rect2(rect, colorset['menu-selected'] if chosen else colorset['menu-buttons'],
                              corners='All', border_radius=int(line_h / 4))
        kind = entry.get('icon') or ('open' if chosen and entry['kind'] == 'dir' else entry['kind'])
        if kind == 'file' and entry['path'].lower().endswith(VIDEOS):
            kind = 'video'
        picture = icon(kind, int(line_h * 0.72), icons)
        text_x = rect.x + int(unit_x / 4)
        if picture is not None:
            screen.screen.blit(picture, (text_x, rect.centery - picture.get_height() // 2))
            text_x += picture.get_width() + int(unit_x / 4)
        if entry['kind'] != 'up' or picture is None:
            # The folder above : its icon only
            screen.blit_text(entry['label'], text_x, rect.y, rect.right - text_x - int(unit_x / 4), rect.h,
                             colorset['menu-text-white'] if chosen else colorset['menu-text-black'], align='Left')
        zones[index] = tuple(rect)
    if not entries or all(entry['kind'] == 'up' for entry in entries):
        # Nothing to choose here : said for what is looked for
        kinds = previews.get('kinds', IMAGES)
        empty = 'explorer-empty' if kinds == IMAGES else ('explorer-empty-pick' if picking else 'explorer-empty-files')
        screen.blit_text(translate(empty), int(unit_x), int(4.5 * unit_y), int(7 * unit_x), int(unit_y),
                         colorset['menu-text-white'])
    # The preview
    box = pygame.Rect(int(8.5 * unit_x), int(3.2 * unit_y), int(6.5 * unit_x), int(8.8 * unit_y))
    screen.new_blit_rect2(box, colorset['menu-buttons'], corners='All', border_radius=int(unit_y / 4))
    entry = entries[selected] if selected < len(entries) else None
    if picking:
        # « Choisir ce dossier » : over Back, in the middle of the list
        button = pygame.Rect(int(2.5 * unit_x), int(13.05 * unit_y), int(4 * unit_x), int(0.95 * unit_y))
        chosen = selected == len(entries)
        screen.new_blit_rect2(button, colorset['menu-selected'] if chosen else colorset['menu-buttons'], corners='All',
                              border_radius=int(button.height / 2))
        screen.blit_text(translate('explorer-pick-folder'), button.x, button.y, button.width, button.height,
                         colorset['menu-text-white'] if chosen else colorset['menu-text-black'])
        zones['pick'] = tuple(button)
        if chosen:
            entry = {'kind': 'dir', 'path': folder, 'label': os.path.basename(folder.rstrip(os.sep)) or folder}
    caption = ''
    image = entry['path'] if entry and entry['kind'] == 'file' else (entry or {}).get('image')
    # A video : played in the box (see VideoPreview), its name, its size and its length
    player = previews.get('player')
    video = image if image and image.lower().endswith(VIDEOS) else None
    maker, played = None, None
    if video:
        maker, played = (lambda screen_, inner: VideoPreview(screen_, video, inner)), video
    elif entry is not None and entry.get('preview') is not None:
        maker, played = entry['preview'], ('extra', entry['path'])
    if player is not None and (maker is None or player.path != played):
        player.stop()
        previews['player'] = player = None
        screen.idle_hook = None
    if maker is not None:
        if player is None:
            player = maker(screen, box.inflate(-int(unit_x / 2), -int(unit_y / 2)))
            player.path = played
            previews['player'] = player
            screen.idle_hook = player.tick
        caption = player.caption(translate) or (entry['label'] if entry else '')
        image = None
        video = video or played
    if image:
        picture = preview(image, box.inflate(-int(unit_x / 2), -int(unit_y / 2)).size, previews)
        if picture is None:
            caption = translate('explorer-unreadable')
        else:
            surface, size = picture
            screen.screen.blit(surface, surface.get_rect(center=box.center))
            caption = f"{os.path.basename(image)} · {size[0]} × {size[1]}" if entry['kind'] == 'file' else entry['label']
    elif entry and not video:
        # A folder, a place, the folder above : a big icon, what it holds
        kind = entry.get('icon') or ('open' if entry['kind'] == 'dir' else entry['kind'])
        picture = icon(kind, int(box.h / 3), icons)
        if picture is not None:
            screen.screen.blit(picture, picture.get_rect(center=box.center))
        caption = entry['label']
        target = entry['path'] if entry['kind'] in ('dir', 'pick') else (os.path.dirname(folder.rstrip(os.sep)) or os.sep
                                                               if entry['kind'] == 'up' and folder else None)
        if target:
            caption = f"{caption} · {folder_text(target, translate, counts, previews.get('kinds', IMAGES))}"
    screen.blit_text(caption, box.x, box.bottom + int(unit_y / 4), box.w, int(0.7 * unit_y), colorset['menu-text-white'])
    zones['escape'] = screen.display_button(False, 'back', special='escape')
    screen.update_screen()
    return zones


class VideoPreview:
    '''
    A video played in the box of the preview while it is selected : ffmpeg at the size of the
    box (its proportions kept), at its own pace, looping, at the lowest priority ; its last
    frame drawn at each turn of the reading of the inputs (tick). Nothing prepared : on a Pi 3,
    10 to 15 frames a second
    '''
    RATE = 15

    def __init__(self, screen, path, box):
        self.screen = screen
        self.path = path
        self.box = pygame.Rect(box)
        self.size = None
        self.length = None
        self.latest = None
        self.shown = None
        self.drawn = False
        self.process = None
        self.stopped = False
        self.probe()
        threading.Thread(target=self.run, daemon=True).start()

    def probe(self):
        try:
            out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                  'stream=width,height:format=duration', '-of', 'default=nw=1', self.path],
                                 capture_output=True, text=True, timeout=15, check=False).stdout
            values = dict(line.split('=', 1) for line in out.splitlines() if '=' in line)
            self.size = (int(values['width']), int(values['height']))
            self.length = float(values.get('duration') or 0) or None
        except (OSError, ValueError, KeyError, subprocess.SubprocessError):
            self.size = None

    def caption(self, translate):
        parts = [os.path.basename(self.path)]
        if self.size:
            parts.append(f"{self.size[0]} × {self.size[1]}")
        if self.length:
            parts.append(f"{self.length:.0f} s")
        return ' · '.join(parts) if self.size else f"{parts[0]} · {translate('explorer-video-loading')}"

    def run(self):
        if self.stopped or not self.size:
            return
        ratio = min(self.box.w / self.size[0], self.box.h / self.size[1])
        width, height = max(2, int(self.size[0] * ratio) // 2 * 2), max(2, int(self.size[1] * ratio) // 2 * 2)
        frame = width * height * 4

        def lowest():
            os.nice(15)
        try:
            self.process = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-threads', '1', '-re', '-stream_loop', '-1',  # pylint: disable=consider-using-with
                                             '-i', self.path, '-an', '-vf', f"fps={self.RATE},scale={width}:{height}",
                                             '-pix_fmt', 'rgb0', '-f', 'rawvideo', '-'],
                                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                                            preexec_fn=lowest)
        except OSError:
            return
        if self.stopped:
            self.stop()
            return
        while not self.stopped:
            data = self.process.stdout.read(frame)
            if len(data) < frame:
                return
            self.latest = (data, (width, height))

    def tick(self):
        '''
        The last frame read drawn in its box (once the box is drawn)
        '''
        latest = self.latest
        if latest is None or latest is self.shown or self.stopped:
            return
        self.shown = latest
        data, size = latest
        picture = pygame.image.frombuffer(data, size, 'RGBX')
        rect = picture.get_rect(center=self.box.center)
        self.screen.screen.blit(picture, rect)
        self.screen.update_screen(rect=rect)

    def stop(self):
        self.stopped = True
        process = self.process
        if process is not None and process.poll() is None:
            process.kill()
            try:
                process.wait(timeout=2)
            except subprocess.SubprocessError:
                pass


def preview(path, size, previews):
    '''
    An image scaled to fit the box (its proportions kept), with its size ; None : not read
    '''
    key = (path, tuple(size))
    if key not in previews:
        while len(previews) > PREVIEWS:
            previews.pop(next(key for key in previews if key not in ('icons', 'counts', 'kinds', 'player', 'subtitle')))
        try:
            picture = pygame.image.load(path)
            width, height = picture.get_size()
            ratio = min(size[0] / width, size[1] / height)
            scaled = pygame.transform.smoothscale(picture.convert_alpha(),
                                                  (max(1, int(width * ratio)), max(1, int(height * ratio))))
            previews[key] = (scaled, (width, height))
        except Exception:    # pylint: disable=broad-except
            previews[key] = None
    return previews[key]


def portable(screen, path, kind):
    '''
    An image chosen, written as the menus find it : from the folder of the theme, of
    ~/.raspydarts or of the game ; elsewhere (a USB key...) : copied in ~/.raspydarts/images/<kind>
    (a name taken by another image : numbered). None : not copied
    '''
    theme_dir = getattr(screen.file_class, 'theme_dir', None)
    full = os.path.realpath(path)
    for base in (theme_dir, cpaths.user_dir(), cpaths.ROOT_DIR):
        if base and full.startswith(os.path.realpath(base) + os.sep):
            return os.path.relpath(full, os.path.realpath(base)).replace(os.sep, '/')
    try:
        target_dir = os.path.join(cpaths.user_dir(), 'images', kind)
        os.makedirs(target_dir, exist_ok=True)
        stem, extension = os.path.splitext(os.path.basename(path))
        name, number = f'{stem}{extension}', 1
        while os.path.exists(os.path.join(target_dir, name)) and \
                not filecmp.cmp(path, os.path.join(target_dir, name), shallow=False):
            number += 1
            name = f'{stem}_{number}{extension}'
        shutil.copyfile(path, os.path.join(target_dir, name))
    except OSError as error:
        screen.logs.error(f"Menus : image {path} not copied ({error})")
        screen.message([screen.lang.translate('editor-import-failed')], 2500, 'menu-ko', 'middle', 'big')
        return None
    screen.logs.info(f"Menus : image {path} copied as images/{kind}/{name}")
    return f'images/{kind}/{name}'
