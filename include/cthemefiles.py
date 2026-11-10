"""
Modifier les écrans > Thème : export and import of a theme.

A theme is the folder ~/.raspydarts/themes/<name> : other/Colorset.cfg (its colours),
other/Colorset_perso.cfg (Personnaliser le thème), menu/menus.yaml (its menus), images/, font/,
videos/, sounds/.

Export : a zip <name>/... of that folder (its videos and sounds if wanted : they are most of its
size), the images of ~/.raspydarts/images its menus use (placed in the theme : found first on
another borne), and theme.json (name, date, version). Made in the background, followed by the
activity window ; written on a USB key or in ~/Exports.

Import : a zip, a folder, or (later) a download from Raspyhub ; the theme is the folder holding
other/Colorset.cfg (or Colorset.cfg) ; copied in ~/.raspydarts/themes (a theme of the same name :
replaced, the old one kept aside, or the new one renamed), then used if wanted.
"""

import json
import os
import re
import shutil
import threading
import time
import zipfile

from include import cpaths

MEDIA = ('videos', 'sounds')
# Files already compressed : stored as they are in the zip (quicker on a Pi)
STORED = ('.mp4', '.mkv', '.webm', '.avi', '.mov', '.gif', '.png', '.jpg', '.jpeg', '.mp3', '.ogg', '.wav', '.ttf',
          '.otf', '.zip')
# A theme imported bigger than this is refused (a zip bomb, the card filled)
IMPORT_LIMIT = 2 * 1024 ** 3


def themes_dir(screen):
    return screen.config.themes_dir


def folder_size(path):
    total = 0
    for root, _folders, files in os.walk(path):
        for name in files:
            try:
                total += os.path.getsize(os.path.join(root, name))
            except OSError:
                pass
    return total


def destinations(translate):
    '''
    Where to write the export : the USB keys, else the folder Exports of the home
    '''
    from include import cexplorer    # pylint: disable=import-outside-toplevel
    found = []
    for base in cexplorer.MOUNTS:
        for root, folders, _files in os.walk(base):
            if root.count(os.sep) - base.count(os.sep) >= 2:
                folders.clear()
            if os.path.ismount(root) and root != base and os.access(root, os.W_OK):
                found.append((root, f"{translate('editor-import-usb')} : {os.path.basename(root)}"))
    # Visible in the explorer (Dossier personnel > Exports) : imported again from there
    found.append((os.path.expanduser('~/Exports'), translate('theme-export-home')))
    return found


def used_images(theme_dir):
    '''
    The images of ~/.raspydarts named by the menus of the theme (images/...) and not in it
    '''
    menus = os.path.join(theme_dir, 'menu', 'menus.yaml')
    try:
        with open(menus, encoding='utf-8') as source:
            text = source.read()
    except OSError:
        return []
    found = []
    for relative in sorted(set(re.findall(r'images/[^\s"\'\]\},]+', text))):
        if os.path.exists(os.path.join(theme_dir, relative)):
            continue
        mine = os.path.join(cpaths.user_dir(), relative)
        if os.path.isfile(mine):
            found.append(relative)
    return found


class Export:
    '''
    The zip of a theme written in the background : progress() (done, total in bytes) ; state :
    running, done, failed ; target : the file written
    '''

    def __init__(self, logs, theme, theme_dir, folder, media, version):
        self.logs = logs
        self.theme = theme
        self.theme_dir = theme_dir
        self.media = media
        self.version = version
        self.target = os.path.join(folder, f"theme_{theme}_{time.strftime('%Y%m%d_%H%M')}.zip")
        self.folder = folder
        self.done = 0
        self.total = 1
        self.state = 'running'
        threading.Thread(target=self.run, daemon=True).start()

    def files(self):
        listed = []
        for root, folders, files in os.walk(self.theme_dir):
            relative_root = os.path.relpath(root, self.theme_dir)
            top = relative_root.split(os.sep)[0]
            if not self.media and top in MEDIA:
                folders.clear()
                continue
            for name in files:
                if name.endswith(('.bak', '.tmp')) or '.avant-' in name:
                    continue
                path = os.path.join(root, name)
                listed.append((path, os.path.normpath(os.path.join(relative_root, name))))
        for relative in used_images(self.theme_dir):
            listed.append((os.path.join(cpaths.user_dir(), relative), relative))
        return listed

    def run(self):
        partial = self.target + '.part'
        try:
            os.makedirs(self.folder, exist_ok=True)
            listed = self.files()
            self.total = max(1, sum(os.path.getsize(path) for path, _relative in listed))
            with zipfile.ZipFile(partial, 'w') as archive:
                info = {'name': self.theme, 'created': time.strftime('%Y-%m-%d %H:%M'),
                        'raspydarts_version': self.version, 'with_media': self.media}
                archive.writestr(f"{self.theme}/theme.json", json.dumps(info, indent=2, ensure_ascii=False))
                for path, relative in listed:
                    method = zipfile.ZIP_STORED if path.lower().endswith(STORED) else zipfile.ZIP_DEFLATED
                    archive.write(path, f"{self.theme}/{relative.replace(os.sep, '/')}", compress_type=method)
                    self.done += os.path.getsize(path)
            os.replace(partial, self.target)
            # A USB key : written for good before it is taken away
            os.sync()
            self.state = 'done'
            self.logs.info(f"Theme {self.theme} exported in {self.target} ({self.total // 1048576} MB)")
        except Exception as error:    # pylint: disable=broad-except
            self.state = 'failed'
            self.logs.error(f"Theme {self.theme} not exported ({error})")
            try:
                os.remove(partial)
            except OSError:
                pass


def export_theme(screen, keys):
    '''
    The theme of the moment exported : where, with its videos and sounds or not ; then in the
    background (the activity window follows it)
    '''
    translate = screen.lang.translate
    theme = str(screen.config.get_value('SectionGlobals', 'colorset') or '')
    theme_dir = getattr(screen.file_class, 'theme_dir', None)
    if not theme or not theme_dir or not os.path.isdir(theme_dir):
        screen.message([translate('theme-export-none')], 2500, 'menu-ko', 'middle', 'big')
        return
    current = getattr(screen, 'theme_export', None)
    if current is not None and current.state == 'running':
        screen.message([translate('theme-export-running')], 2500, None, 'middle', 'big')
        return
    places = destinations(translate)
    chosen = screen.dropdown(screen.res['x'] * 5 / 16, 3 * screen.res_y_16, [[path, text] for path, text in places],
                             width=screen.res['x'] * 6 / 16)
    if chosen == 'escape':
        return
    media_size = sum(folder_size(os.path.join(theme_dir, name)) for name in MEDIA)
    media = False
    if media_size > 0:
        answer = screen.ask_yes_no(translate('theme-export-media').replace('{size}', f"{media_size / 1048576:.0f}"),
                                   translate('theme-export-media-explain'), cancel=True)
        if answer is None:
            return
        media = bool(answer)
    version = getattr(screen.config, 'pyDartsVersion', '')
    try:
        from include import cupdate    # pylint: disable=import-outside-toplevel
        version = cupdate.get_version(screen.logs)
    except Exception:    # pylint: disable=broad-except
        pass
    export = Export(screen.logs, theme, theme_dir, chosen, media, version)
    screen.theme_export = export

    def state():
        if export.state == 'running':
            fraction = export.done / export.total
            return {'text': f"{translate('activity-theme-export').replace('{theme}', theme)} {int(fraction * 100)} %",
                    'fraction': fraction}
        if export.state == 'done':
            return {'text': translate('activity-theme-export-done').replace('{file}', os.path.basename(export.target)),
                    'final': True}
        return {'text': translate('activity-theme-export-failed'), 'final': True}

    screen.activities.add('theme-export', state)
    screen.message([translate('theme-export-started'), export.target], 3000, None, 'middle', 'big')


# ---------------------------------------------------------------------- import
def theme_root(folder):
    '''
    The folder of a theme inside this one (itself or below, two levels at most) : the one with
    other/Colorset.cfg or Colorset.cfg ; None : no theme
    '''
    for root, folders, files in os.walk(folder):
        depth = os.path.relpath(root, folder).count(os.sep) + (0 if root == folder else 1)
        if depth > 2:
            folders.clear()
            continue
        if 'Colorset.cfg' in files or os.path.isfile(os.path.join(root, 'other', 'Colorset.cfg')):
            return root
    return None


def safe_extract(path, target):
    '''
    A zip unpacked in target : no path out of it, no link, its size limited. Raises ValueError
    '''
    with zipfile.ZipFile(path) as archive:
        total = 0
        for member in archive.infolist():
            name = member.filename
            if name.startswith(('/', '\\')) or '..' in name.replace('\\', '/').split('/') or ':' in name:
                raise ValueError(f"unexpected path {name}")
            # Links (unix mode in the high bits) refused
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError(f"link {name}")
            total += member.file_size
            if total > IMPORT_LIMIT:
                raise ValueError('too big')
        archive.extractall(target)


def import_theme(screen, keys):
    '''
    A theme imported : a zip, a folder, or a download from Raspyhub (later) ; then used if
    wanted
    '''
    from include import cexplorer    # pylint: disable=import-outside-toplevel
    translate = screen.lang.translate
    choice = screen.dropdown(screen.res['x'] * 5 / 16, 3 * screen.res_y_16,
                             [['zip', translate('theme-import-zip')], ['folder', translate('theme-import-folder')],
                              ['raspyhub', translate('theme-import-raspyhub')]], width=screen.res['x'] * 6 / 16)
    if choice == 'escape':
        return
    if choice == 'raspyhub':
        screen.message([translate('theme-import-raspyhub-soon')], 3500, None, 'middle', 'big')
        return
    if choice == 'zip':
        source = cexplorer.explore(screen, translate('theme-import-zip'), None, kinds=('.zip',))
    else:
        source = cexplorer.explore(screen, translate('theme-import-folder'), None, kinds=(), pick_folder=True)
    if not source or not os.path.exists(source):
        return
    work = os.path.join(themes_dir(screen), '.import')
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work, exist_ok=True)
    try:
        screen.message([translate('theme-import-reading')], 0, None, 'middle', 'big')
        if os.path.isfile(source):
            safe_extract(source, work)
            root = theme_root(work)
            name = os.path.basename(root) if root and root != work else os.path.splitext(os.path.basename(source))[0]
        else:
            if folder_size(source) > IMPORT_LIMIT:
                raise ValueError('too big')
            root = theme_root(source)
            name = os.path.basename(root.rstrip(os.sep)) if root else None
        if root is None:
            screen.message([translate('theme-import-not-theme')], 3500, 'menu-ko', 'middle', 'big')
            return
        name = re.sub(r'[^\w.-]+', '_', name.replace('theme_', '', 1)).strip('._') or 'theme'
        if name == 'clear':
            name = 'clear_importe'
        target = os.path.join(themes_dir(screen), name)
        if os.path.exists(target):
            answer = screen.ask_yes_no(translate('theme-import-exists').replace('{theme}', name),
                                       translate('theme-import-exists-explain'), cancel=True)
            if answer is None:
                return
            if answer:
                kept = f"{target}.avant-import-{time.strftime('%Y%m%d_%H%M')}"
                os.rename(target, kept)
                screen.logs.info(f"Theme {name} replaced : the old one kept in {kept}")
            else:
                number = 2
                while os.path.exists(f"{target}_{number}"):
                    number += 1
                name, target = f"{name}_{number}", f"{target}_{number}"
        screen.message([translate('theme-import-copying')], 0, None, 'middle', 'big')
        if os.path.isfile(source):
            shutil.move(root, target)
        else:
            shutil.copytree(root, target, ignore=shutil.ignore_patterns('*.bak', '*.tmp'))
        screen.logs.info(f"Theme {name} imported from {source}")
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        screen.logs.error(f"Theme not imported from {source} ({error})")
        screen.message([translate('theme-import-failed')], 3500, 'menu-ko', 'middle', 'big')
        return
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if screen.ask_yes_no(translate('theme-import-use').replace('{theme}', name)):
        screen.apply_look(theme=name)
