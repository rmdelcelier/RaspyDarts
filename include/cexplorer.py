"""
Explorer of the files of the borne (Modifier les écrans : background of a menu, images of a
button) : the folders and the images on the left, the image chosen shown on the right ; any
folder of the card, the USB keys, the images of the theme and of the game
"""

import filecmp
import os
import shutil

import pygame

from include import cemoji
from include import cpaths

IMAGES = ('.png', '.jpg', '.jpeg')
# The USB keys : mounted in these folders
MOUNTS = ('/media', '/mnt')
# Lines of the list shown at once
ROWS = 10
# Previews kept (an image read and scaled : up to 1 s on a Pi 3)
PREVIEWS = 24
# Icons of the lines (colour emojis) ; up : a folder with an arrow, drawn
ICONS = {'dir': '\U0001F4C1', 'open': '\U0001F4C2', 'file': '\U0001F5BC', 'extra': '\U0001F3A8',
         'theme': '\U0001F3A8', 'mine': '\U0001F5BC', 'game': '\U0001F3AF', 'usb': '\U0001F4BE',
         'home': '\U0001F3E0', 'card': '\U0001F4BD', 'arrow': '\u2B06'}


def places(screen, translate):
    '''
    The first list : the folders of images of the theme, of ~/.raspydarts and of the game, the
    USB keys, the home, the whole card
    '''
    found = []
    theme_dir = getattr(screen.file_class, 'theme_dir', None)
    for path, label, icon in ((os.path.join(theme_dir, 'images') if theme_dir else None, 'explorer-theme-images', 'theme'),
                              (os.path.join(cpaths.user_dir(), 'images'), 'explorer-my-images', 'mine'),
                              (os.path.join(cpaths.ROOT_DIR, 'images'), 'explorer-game-images', 'game')):
        if path and os.path.isdir(path):
            found.append({'kind': 'dir', 'path': path, 'label': translate(label), 'icon': icon})
    for base in MOUNTS:
        for root, folders, _files in os.walk(base):
            if root.count(os.sep) - base.count(os.sep) >= 2:
                folders.clear()
            if os.path.ismount(root) and root != base:
                found.append({'kind': 'dir', 'path': root, 'icon': 'usb',
                              'label': f"{translate('editor-import-usb')} : {os.path.basename(root)}"})
    found.append({'kind': 'dir', 'path': os.path.expanduser('~'), 'label': translate('editor-import-home'), 'icon': 'home'})
    found.append({'kind': 'dir', 'path': os.sep, 'label': translate('editor-import-root'), 'icon': 'card'})
    return found


def listing(folder, translate):
    '''
    A folder : the folder above, its folders, its images
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
              for entry in entries if entry.is_file() and entry.name.lower().endswith(IMAGES)]
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


def explore(screen, title, current=None, extra=()):
    '''
    An image chosen : its full path ; or the id of one of the extra choices given first
    ((id, text[, image shown]) : the one of the theme, none...) ; None : given up. current : the
    image of the moment, the explorer opens in its folder. Back goes up to the place where the
    browsing started (the image of the moment : the place holding it), then to the places
    '''
    # pylint: disable=import-outside-toplevel
    from include.cscreen import DOWN_KEYS, ENTER_KEYS, ESCAPE_KEYS, LEFT_KEYS, RIGHT_KEYS, UP_KEYS
    translate = screen.lang.translate
    previews = {}
    folder = root = None
    selected = 0
    if current and os.path.isfile(current):
        folder = os.path.dirname(current)
        # Its place : the deepest one holding it
        holding = [place['path'] for place in places(screen, translate)
                   if folder == place['path'] or folder.startswith(place['path'].rstrip(os.sep) + os.sep)]
        root = max(holding, key=len) if holding else os.sep
    while True:
        if folder is None:
            entries = [{'kind': 'extra', 'path': choice[0], 'label': choice[1],
                        'image': choice[2] if len(choice) > 2 else None} for choice in extra]
            entries += places(screen, translate)
        else:
            entries = listing(folder, translate)
            if current:
                # The image of the moment selected first
                selected = next((index for index, entry in enumerate(entries) if entry['path'] == current), selected)
                current = None
        selected = max(0, min(selected, len(entries) - 1))
        zones = draw(screen, title, folder, entries, selected, previews, translate)
        # Drawing an image took up to 1 s : the keys repeated meanwhile dropped
        pygame.event.clear(pygame.KEYDOWN)
        key = screen.rpi.listen_inputs(['arrows'], ['escape', 'enter', 'space', 'single-click', 'PLAYERBUTTON',
                                                    'BACKUPBUTTON', 'GAMEBUTTON'])
        clicked = screen.is_clicked(zones, key)
        # (False : no click ; 0 : the first line)
        if clicked == 'escape':
            key = 'escape'
        elif clicked is not False and clicked is not None:
            if clicked == selected:
                key = 'enter'
            else:
                selected = clicked
                continue
        entry = entries[selected] if entries else None
        if key in UP_KEYS:
            selected = (selected - 1) % max(1, len(entries))
        elif key in DOWN_KEYS:
            selected = (selected + 1) % max(1, len(entries))
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
                selected = next((index for index, item in enumerate(places(screen, translate))
                                 if item['path'] == current_folder), 0) + len(extra)
            else:
                folder = os.path.dirname(folder.rstrip(os.sep)) or os.sep
                selected = next((index for index, item in enumerate(listing(folder, translate))
                                 if item['path'] == current_folder), 0)
        elif entry and (key in ENTER_KEYS + ['space'] or (key in RIGHT_KEYS and entry['kind'] == 'dir')):
            if entry['kind'] == 'dir':
                if folder is None:
                    # A place : Back comes back to the places from it
                    root = entry['path']
                folder, selected = entry['path'], 0
            elif entry['kind'] == 'file':
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


def folder_text(path, translate, counts):
    '''
    What a folder holds : its folders and its images
    '''
    if path not in counts:
        try:
            entries = [entry for entry in os.scandir(path) if not entry.name.startswith('.')]
            folders = sum(1 for entry in entries if entry.is_dir())
            images = sum(1 for entry in entries if entry.is_file() and entry.name.lower().endswith(IMAGES))
            counts[path] = translate('explorer-holds').replace('{folders}', str(folders)).replace('{images}', str(images))
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
    screen.menu_header(title, folder if folder is not None else translate('explorer-places'))
    zones = {}
    # The list
    top = max(0, min(selected - ROWS // 2, len(entries) - ROWS))
    line_h = int(unit_y * 0.9)
    for row, index in enumerate(range(top, min(top + ROWS, len(entries)))):
        entry = entries[index]
        rect = pygame.Rect(int(unit_x), int(3.2 * unit_y + row * (line_h + 4)), int(7 * unit_x), line_h)
        chosen = index == selected
        screen.new_blit_rect2(rect, colorset['menu-selected'] if chosen else colorset['menu-buttons'],
                              corners='All', border_radius=int(line_h / 4))
        kind = entry.get('icon') or ('open' if chosen and entry['kind'] == 'dir' else entry['kind'])
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
        screen.blit_text(translate('explorer-empty'), int(unit_x), int(4.5 * unit_y), int(7 * unit_x), int(unit_y),
                         colorset['menu-text-white'])
    # The preview
    box = pygame.Rect(int(8.5 * unit_x), int(3.2 * unit_y), int(6.5 * unit_x), int(8.8 * unit_y))
    screen.new_blit_rect2(box, colorset['menu-buttons'], corners='All', border_radius=int(unit_y / 4))
    entry = entries[selected] if entries else None
    caption = ''
    image = entry['path'] if entry and entry['kind'] == 'file' else (entry or {}).get('image')
    if image:
        picture = preview(image, box.inflate(-int(unit_x / 2), -int(unit_y / 2)).size, previews)
        if picture is None:
            caption = translate('explorer-unreadable')
        else:
            surface, size = picture
            screen.screen.blit(surface, surface.get_rect(center=box.center))
            caption = f"{os.path.basename(image)} · {size[0]} × {size[1]}" if entry['kind'] == 'file' else entry['label']
    elif entry:
        # A folder, a place, the folder above : a big icon, what it holds
        kind = entry.get('icon') or ('open' if entry['kind'] == 'dir' else entry['kind'])
        picture = icon(kind, int(box.h / 3), icons)
        if picture is not None:
            screen.screen.blit(picture, picture.get_rect(center=box.center))
        caption = entry['label']
        target = entry['path'] if entry['kind'] == 'dir' else (os.path.dirname(folder.rstrip(os.sep)) or os.sep
                                                               if entry['kind'] == 'up' and folder else None)
        if target:
            caption = f"{caption} · {folder_text(target, translate, counts)}"
    screen.blit_text(caption, box.x, box.bottom + int(unit_y / 4), box.w, int(0.7 * unit_y), colorset['menu-text-white'])
    zones['escape'] = screen.display_button(False, 'back', special='escape')
    screen.update_screen()
    return zones


def preview(path, size, previews):
    '''
    An image scaled to fit the box (its proportions kept), with its size ; None : not read
    '''
    key = (path, tuple(size))
    if key not in previews:
        while len(previews) > PREVIEWS:
            previews.pop(next(key for key in previews if key not in ('icons', 'counts')))
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
