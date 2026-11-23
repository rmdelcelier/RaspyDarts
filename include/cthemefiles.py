"""
Modifier les écrans > Thème : export and import of a theme.

A theme is the folder ~/.raspydarts/themes/<name> : other/Colorset.cfg (its colours),
other/Colorset_perso.cfg (Personnaliser le thème), menu/menus.yaml (its menus), images/, font/,
videos/, sounds/.

Export : a zip <name>/... of that folder (its videos and sounds if wanted : they are most of its
size), the images of ~/.raspydarts/images its menus use (placed in the theme : found first on
another borne), and theme.json (name, date, version). Made in the background, followed by the
activity window ; written on a USB key or in ~/Exports.

Import : a zip, a folder, or a download from RaspyHub (include/cthemecatalog.py) ; the theme is
the folder holding other/Colorset.cfg (or Colorset.cfg) ; copied in ~/.raspydarts/themes (a theme
of the same name : replaced, the old one kept aside, or the new one renamed), then used if wanted.
A theme of RaspyHub keeps there raspyhub.json (its id, its version : « Mise à jour disponible »).
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
# A theme imported bigger than this is refused (a zip bomb, the card filled) ; the old themes with
# their videos go up to 2.3 GB
IMPORT_LIMIT = 4 * 1024 ** 3
# What RaspyHub knows of a theme downloaded from it (never exported again with it)
HUB_FILE = 'raspyhub.json'


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


def theme_colorset_text(theme_dir):
    '''
    A theme without its own colours (no Colorset.cfg) : the game draws it with those built in
    (ColorSet['clear'], Screen.init_colorset), and its colours chosen over them. Their
    Colorset.cfg, written in its zip so that it looks the same on another borne. None : the theme
    has its Colorset.cfg
    '''
    if any(os.path.isfile(os.path.join(theme_dir, *place)) for place in (('other', 'Colorset.cfg'), ('Colorset.cfg',))):
        return None
    from include.ColorSets import ColorSet    # pylint: disable=import-outside-toplevel
    lines = ['[Colorset]', '', '# The colours built in the game (the theme had no Colorset.cfg of its own)']
    lines += [f"{key}: {value!r}" for key, value in ColorSet['clear'].items() if key != 'font']
    return chr(10).join(lines) + chr(10)


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
                if name.endswith(('.bak', '.tmp')) or '.avant-' in name or (relative_root == '.' and name == HUB_FILE):
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
                colours = theme_colorset_text(self.theme_dir)
                if colours is not None:
                    archive.writestr(f"{self.theme}/other/Colorset.cfg", colours)
                    self.logs.info(f"Theme {self.theme} : no Colorset.cfg, the colours built in the game written in its zip")
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
    # Where : a folder or a USB key, or RaspyHub (shared with the other bornes)
    choices = [['folder', translate('theme-export-to-folder')], ['raspyhub', translate('theme-export-to-raspyhub')]]
    picked = screen.dropdown(screen.res['x'] * 6 / 16, 3 * screen.res_y_16, choices, navigate='folder',
                             width=6 * screen.res_x_16)
    if picked == 'raspyhub':
        from include import cthemehub    # pylint: disable=import-outside-toplevel
        cthemehub.export_screen(screen)
        return
    if picked != 'folder':
        return
    current = getattr(screen, 'theme_export', None)
    if current is not None and current.state == 'running':
        screen.message([translate('theme-export-running')], 2500, None, 'middle', 'big')
        return
    # Where : a folder chosen in the explorer (a USB key, the home...) ; Back : nothing done
    from include import cexplorer    # pylint: disable=import-outside-toplevel
    chosen = cexplorer.explore(screen, translate('theme-export-where'), None, kinds=(), pick_folder=True,
                               subtitle=translate('theme-export-where-hint'))
    if not chosen or not os.path.isdir(chosen):
        return
    if not os.access(chosen, os.W_OK):
        screen.message([translate('theme-export-readonly')], 3000, 'menu-ko', 'middle', 'big')
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
    # One line (two drawn over each other) : the name of the file, its folder in the window of activity
    screen.message([f"{translate('theme-export-started')} {os.path.basename(export.target)}"], 2500, None, 'middle')


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
    A theme imported : a zip, a folder, or a download from RaspyHub ; then used if wanted
    '''
    from include import cexplorer    # pylint: disable=import-outside-toplevel
    translate = screen.lang.translate
    # One explorer : a zip chosen, a folder (Choisir ce dossier), or RaspyHub first ; Back : nothing.
    # Leaving Télécharger depuis RaspyHub : back to this explorer
    while True:
        source = cexplorer.explore(screen, translate('theme-import'), None, [('raspyhub', translate('theme-import-raspyhub'))],
                                   kinds=('.zip',), pick_folder=True, subtitle=translate('theme-import-hint'))
        if source != 'raspyhub':
            break
        from include import cthemecatalog    # pylint: disable=import-outside-toplevel
        cthemecatalog.catalog_screen(screen)
    if not source or not os.path.exists(source):
        return
    install(screen, source)


def install(screen, source, origin=None, name=None):
    '''
    A zip or a folder copied in the themes, then used if wanted ; origin : what RaspyHub knows of
    it (written in HUB_FILE) ; name : its name (that of the catalogue) instead of the folder of the
    zip. Returns its name, or
    None (not a theme, refused, failed)
    '''
    translate = screen.lang.translate
    work = os.path.join(themes_dir(screen), '.import')
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work, exist_ok=True)
    try:
        screen.message([translate('theme-import-reading')], 0, None, 'middle', 'big')
        if os.path.isfile(source):
            safe_extract(source, work)
            root = theme_root(work)
            name = name or (os.path.basename(root) if root and root != work else os.path.splitext(os.path.basename(source))[0])
        else:
            if folder_size(source) > IMPORT_LIMIT:
                raise ValueError('too big')
            root = theme_root(source)
            name = os.path.basename(root.rstrip(os.sep)) if root else None
        if root is None:
            screen.message([translate('theme-import-not-theme')], 3500, 'menu-ko', 'middle', 'big')
            return None
        name = re.sub(r'[^\w.-]+', '_', name.replace('theme_', '', 1)).strip('._') or 'theme'
        if name == 'clear':
            name = 'clear_importe'
        target = os.path.join(themes_dir(screen), name)
        if os.path.exists(target):
            answer = screen.ask_yes_no(translate('theme-import-exists').replace('{theme}', name),
                                       translate('theme-import-exists-explain'), cancel=True)
            if answer is None:
                return None
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
        if origin:
            with open(os.path.join(target, HUB_FILE), 'w', encoding='utf-8') as written:
                json.dump(origin, written, indent=2, ensure_ascii=False)
        screen.logs.info(f"Theme {name} imported from {source}")
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        screen.logs.error(f"Theme not imported from {source} ({error})")
        screen.message([translate('theme-import-failed')], 3500, 'menu-ko', 'middle', 'big')
        return None
    finally:
        shutil.rmtree(work, ignore_errors=True)
    if screen.ask_yes_no(translate('theme-import-use').replace('{theme}', name)):
        screen.apply_look(theme=name)
    return name


# ---------------------------------------------------------------------- creating, deleting
THEME_NAME_MOST = 40


class Copy:
    '''
    A theme copied whole in the background (Créer un thème à partir de celui-ci) : state
    running, done, failed ; done, total in bytes
    '''

    def __init__(self, logs, source, target):
        self.logs = logs
        self.source = source
        self.target = target
        self.total = max(1, folder_size(source))
        self.done = 0
        self.state = 'running'
        threading.Thread(target=self.run, daemon=True).start()

    def copy_file(self, source, target, **_kwargs):
        shutil.copy2(source, target)
        try:
            self.done += os.path.getsize(source)
        except OSError:
            pass
        return target

    def run(self):
        try:
            # The mark of a theme downloaded from RaspyHub stays with the theme of RaspyHub : the
            # copy is a theme of its own
            shutil.copytree(self.source, self.target, copy_function=self.copy_file,
                            ignore=shutil.ignore_patterns(HUB_FILE, '*.bak', '*.tmp'))
            # A theme without Colorset.cfg of its own : the copy keeps the colours it is drawn with
            colours = theme_colorset_text(self.target)
            if colours is not None:
                os.makedirs(os.path.join(self.target, 'other'), exist_ok=True)
                with open(os.path.join(self.target, 'other', 'Colorset.cfg'), 'w', encoding='utf-8') as file:
                    file.write(colours)
            self.state = 'done'
            self.logs.info(f"Theme {os.path.basename(self.target)} created from {self.source} ({self.total // 1048576} MB)")
        except Exception as error:    # pylint: disable=broad-except
            self.state = 'failed'
            self.logs.error(f"Theme {os.path.basename(self.target)} not created from {self.source} ({error})")
            shutil.rmtree(self.target, ignore_errors=True)


def user_themes(screen):
    '''
    The folders of ~/.raspydarts/themes : their names
    '''
    try:
        return sorted(entry.name for entry in os.scandir(screen.config.themes_dir) if entry.is_dir())
    except OSError:
        return []


def create_theme(screen, keys):    # pylint: disable=unused-argument
    '''
    Créer un thème à partir de celui-ci : its name asked, the theme of the moment copied whole
    (menus, colours, colours chosen, images, sounds, videos, font), then the new one used
    '''
    translate = screen.lang.translate
    theme = str(screen.config.get_value('SectionGlobals', 'colorset') or '')
    source = getattr(screen.file_class, 'theme_dir', None)
    if not theme or not source or not os.path.isdir(source):
        screen.message([translate('theme-export-none')], 2500, 'menu-ko', 'middle', 'big')
        return
    typed = screen.input_value_item('string', '', 1, THEME_NAME_MOST,
                                    text=translate('theme-create-name').replace('{theme}', theme))
    if typed in (None, False, 'escape'):
        return
    name = ' '.join(str(typed).split())
    if not name or len(name) > THEME_NAME_MOST or not re.fullmatch(r'[\w\- ]+', name) or name.startswith('.'):
        screen.message([translate('theme-create-bad').replace('{most}', str(THEME_NAME_MOST))], 3000, 'menu-ko', 'middle', 'big')
        return
    taken = [existing.casefold() for existing in user_themes(screen)] + ['clear']
    if name.casefold() in taken:
        screen.message([translate('theme-create-exists')], 2500, 'menu-ko', 'middle', 'big')
        return
    target = os.path.join(screen.config.themes_dir, name)
    size = folder_size(source)
    try:
        free = shutil.disk_usage(screen.config.themes_dir).free
    except OSError:
        free = size * 2
    # Room left for the game afterwards (100 MB)
    if size + 100 * 1048576 > free:
        screen.message([translate('theme-create-space').replace('{size}', f"{size / 1048576:.0f}")], 3500, 'menu-ko', 'middle', 'big')
        return
    copy = Copy(screen.logs, source, target)
    while copy.state == 'running':
        screen.message([f"{translate('theme-create-copying')} {int(copy.done * 100 / copy.total)} %"], 0, None, 'middle', 'big')
        time.sleep(0.3)
    if copy.state != 'done':
        screen.message([translate('theme-create-failed')], 3000, 'menu-ko', 'middle', 'big')
        return
    screen.apply_look(theme=name)
    screen.message([translate('theme-create-done').replace('{name}', name).replace('{theme}', theme)], 2500, 'menu-ok', 'middle', 'big')


def delete_theme(screen, keys):    # pylint: disable=unused-argument
    '''
    Supprimer un thème : any theme but the one used (clear included : the game keeps its colours
    built in, ColorSet['clear']), after a question
    '''
    translate = screen.lang.translate
    current = str(screen.config.get_value('SectionGlobals', 'colorset') or '')
    choices = [(name, name) for name in user_themes(screen) if name.casefold() != current.casefold()]
    if not choices:
        screen.message([translate('theme-delete-none')], 3000, None, 'middle', 'big')
        return
    picked = screen.dropdown(screen.res['x'] * 6 / 16, 3 * screen.res_y_16, choices, width=6 * screen.res_x_16)
    if picked in (None, 'escape') or picked not in [name for name, _text in choices]:
        return
    if not screen.ask_yes_no(translate('theme-delete-question').replace('{name}', picked), translate('theme-delete-explain')):
        return
    try:
        shutil.rmtree(os.path.join(screen.config.themes_dir, picked))
        screen.logs.info(f"Theme {picked} deleted")
        screen.message([translate('theme-delete-done').replace('{name}', picked)], 2000, 'menu-ok', 'middle', 'big')
    except OSError as error:
        screen.logs.error(f"Theme {picked} not deleted ({error})")
        screen.message([translate('theme-create-failed')], 3000, 'menu-ko', 'middle', 'big')
