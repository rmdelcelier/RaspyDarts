#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gallery of the memories (photos and clips of the webcam), served on the local network.

Runs as its own service (see ensure_running) : available even when the game is not.
Each game is a folder of the pictures and of the videos (see ccamera.folder_tree) :
    <date>/<game>  or  <game>/<date>   (directory_order of [Camera])
Pages : all the games, one game ; each memory can be seen, downloaded, printed, deleted,
a game can be downloaded (one by one, or a ZIP) or deleted. In the language of the borne.

Password : set on the gallery screen of the borne. Only its hash is kept, in password of
[Gallery] (any character can be used, '%' included). Without one, all is allowed and every
page says so. The QR codes shown by the borne carry a key (see token) : being in front of
it is enough to see and download ; typing the address asks for the password. Deleting
always asks for it.

Usage :
    python3 include/cgallery.py          the server (port PORT)
"""

import configparser
import gettext
import hashlib
import hmac
import html
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import urllib.parse
import zipfile
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
from include import cpaths  # noqa: E402

PORT = 8080
PHOTOS = ('.jpg', '.jpeg', '.png')
VIDEOS = ('.mp4',)
THUMB_SIZE = 360
CACHE_DIR = os.path.join(cpaths.user_dir(), 'gallery_cache')
COOKIE = 'raspydarts_gallery'
HASH = 'pbkdf2_sha256'
# About 0.3 s on a Pi 3 : only when the password is set or typed
ITERATIONS = 60000
LANGUAGES = {'fr': 'fr_FR', 'en': 'en_GB', 'de': 'de_DE', 'es': 'es_ES', 'it': 'it_IT', 'nl': 'nl_NL'}


# ------------------------------------------------------------------ shared with the game
def secret():
    '''
    Salt of the keys : different on each borne
    '''
    try:
        with open('/etc/machine-id') as file:
            return file.read().strip()
    except OSError:
        return socket.gethostname()


def hash_password(password):
    '''
    What is kept in the configuration : the hash, never the password
    '''
    salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), ITERATIONS).hex()
    return f"{HASH}${ITERATIONS}${salt}${digest}"


def check_password(password, stored):
    try:
        kind, iterations, salt, digest = stored.split('$')
    except ValueError:
        return False
    if kind != HASH:
        return False
    computed = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), int(iterations)).hex()
    return hmac.compare_digest(computed, digest)


def token(stored):
    '''
    Key given by the QR codes of the borne, and kept by the browser once logged in.
    Made from the hash : it changes with the password
    '''
    return hashlib.sha256(f"{secret()}:{stored}".encode()).hexdigest()[:24]


def partie_id(date, game):
    '''
    Identifier of a game in the addresses (date first, whatever the folder order)
    '''
    return urllib.parse.quote(f"{date}/{game}", safe='')


def address(ip, partie=None, stored=''):
    '''
    Address of the gallery (or of one game) for a QR code of the borne
    '''
    path = f"/p/{partie}" if partie else "/"
    key = f"?k={token(stored)}" if stored else ""
    return f"http://{ip}:{PORT}{path}{key}"


def local_ip():
    '''
    Address of the borne on the local network (no packet is sent)
    '''
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(('192.0.2.1', 9))
            return probe.getsockname()[0]
    except OSError:
        return f"{socket.gethostname()}.local"


def running():
    try:
        with socket.create_connection(('127.0.0.1', PORT), timeout=0.3):
            return True
    except OSError:
        return False


def ensure_running(logs=None):
    '''
    Started by the game if it does not run. As its own systemd unit : started from the
    service of the game, it would be stopped with it
    '''
    if running():
        return
    script = os.path.abspath(__file__)
    try:
        result = subprocess.run(['systemd-run', '--user', '--unit=raspydarts-gallery', '--collect',
                                 '--quiet', sys.executable, '-u', script], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return
        if logs is not None:
            logs.warning(f"Gallery : systemd-run refused ({result.stderr.strip()}), started with the game")
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        log = open(os.path.join(ROOT_DIR, 'logs', 'gallery.log'), 'a')
        subprocess.Popen([sys.executable, '-u', script], stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                         start_new_session=True)
    except OSError as error:
        if logs is not None:
            logs.error(f"Gallery not started : {error}")


# ------------------------------------------------------------------ the memories
_translators = {}


def translator(locale):
    '''
    Texts in the language of the borne (the translations of the game)
    '''
    language = LANGUAGES.get(str(locale)[:2].lower(), 'en_GB')
    if language not in _translators:
        try:
            _translators[language] = gettext.translation('pydarts', os.path.join(ROOT_DIR, 'locales'),
                                                         [f'{language}.UTF-8']).gettext
        except OSError:
            _translators[language] = lambda text: text
    return _translators[language]


def settings():
    '''
    Configuration of the borne, read at each request : changes apply at once
    '''
    config = configparser.ConfigParser(inline_comment_prefixes='#', interpolation=None)
    config.optionxform = str
    path = os.path.join(cpaths.user_dir(), cpaths.CONFIG_NAME)
    if not os.path.isfile(path):
        path = os.path.join(cpaths.user_dir(), cpaths.OLD_CONFIG_NAME)
    config.read(path, encoding='utf-8')
    camera = dict(config['Camera']) if config.has_section('Camera') else {}
    gallery = dict(config['Gallery']) if config.has_section('Gallery') else {}
    locale = config['SectionGlobals'].get('locale', 'fr_FR') if config.has_section('SectionGlobals') else 'fr_FR'
    home = cpaths.user_home()
    return {
        'pictures': cpaths.usable_dir(camera.get('picture_path', ''), os.path.join(home, 'Pictures')),
        'videos': cpaths.usable_dir(camera.get('video_path', ''), os.path.join(home, 'Videos')),
        'order': camera.get('directory_order', '0').strip(),
        'password': gallery.get('password', '').strip(),
        '_': translator(locale),
        'lang': str(locale)[:2].lower(),
    }


def folders(conf, date, game):
    '''
    Folders of a game : pictures and videos
    '''
    relative = os.path.join(date, game) if conf['order'] != '1' else os.path.join(game, date)
    return [os.path.join(conf['pictures'], relative), os.path.join(conf['videos'], relative)]


def parties(conf):
    '''
    All the games with memories : [(last change, date, game, files)], newest first
    '''
    found = set()
    for root in (conf['pictures'], conf['videos']):
        if not os.path.isdir(root):
            continue
        for first in os.listdir(root):
            path = os.path.join(root, first)
            if not os.path.isdir(path):
                continue
            for second in os.listdir(path):
                if os.path.isdir(os.path.join(path, second)):
                    found.add((first, second) if conf['order'] != '1' else (second, first))
    result = []
    for date, game in found:
        files = memories(conf, date, game)
        if files:
            result.append((max(os.path.getmtime(path) for _name, path in files), date, game, files))
    return sorted(result, reverse=True)


def memories(conf, date, game):
    '''
    Files of a game : [(name, path)], in the order they were taken
    '''
    files = []
    for folder in folders(conf, date, game):
        if os.path.isdir(folder):
            for name in os.listdir(folder):
                if name.lower().endswith(PHOTOS + VIDEOS):
                    files.append((name, os.path.join(folder, name)))
    return sorted(files, key=lambda item: os.path.getmtime(item[1]))


def find(conf, partie, name=None):
    '''
    (date, game, path of name) from an address, None if it is not a memory
    '''
    date, _, game = urllib.parse.unquote(partie).partition('/')
    if not date or not game or '/' in game or '..' in (date, game):
        return None
    if name is None:
        return date, game, None
    for file_name, path in memories(conf, date, game):
        if file_name == name:
            return date, game, path
    return None


def delete_partie(conf, date, game):
    '''
    All the memories of a game, and the date (or game) folder left empty
    '''
    for folder in folders(conf, date, game):
        shutil.rmtree(folder, ignore_errors=True)
        parent = os.path.dirname(folder)
        if os.path.isdir(parent) and not os.listdir(parent):
            os.rmdir(parent)


def thumbnail(path):
    '''
    Small JPEG of a photo or of the first second of a clip, kept in CACHE_DIR
    '''
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = hashlib.md5(f"{path}:{os.path.getmtime(path)}".encode()).hexdigest()
    cached = os.path.join(CACHE_DIR, f"{key}.jpg")
    if not os.path.exists(cached):
        if path.lower().endswith(VIDEOS):
            subprocess.run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-ss', '1', '-i', path,
                            '-frames:v', '1', '-vf', f'scale={THUMB_SIZE}:-2', cached], timeout=30)
        else:
            from PIL import Image
            with Image.open(path) as picture:
                picture.thumbnail((THUMB_SIZE, THUMB_SIZE))
                picture.convert('RGB').save(cached, 'JPEG', quality=80)
    return cached


# ------------------------------------------------------------------ pages
STYLE = """
body{margin:0;font-family:sans-serif;background:#141414;color:#eee}
header{padding:12px 16px;background:#202020;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
header a{color:#eee;text-decoration:none;font-weight:bold}
h1{font-size:1.2em;margin:0}
.warning{background:#7a2b1e;padding:8px 16px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px;padding:16px}
.card{background:#202020;border-radius:6px;overflow:hidden}
.card img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block}
.card .name{padding:6px 8px;font-size:.85em;word-break:break-word}
.actions{display:flex;flex-wrap:wrap;gap:6px;padding:0 8px 8px}
.actions a,.actions button,.big a,.big button{background:#333;color:#eee;border:0;border-radius:4px;
 padding:6px 10px;font-size:.85em;text-decoration:none;cursor:pointer}
.actions .delete,.big .delete{background:#7a2b1e}
.big{display:flex;flex-wrap:wrap;gap:8px;padding:0 16px}
.big form{margin:0}
form.login{padding:24px 16px}
input{font-size:1em;padding:8px}
.card{position:relative}
.pick{position:absolute;top:6px;left:6px}
.pick input{width:22px;height:22px}
button:disabled{opacity:.4}
.big{margin-top:12px}
.folder{display:block;padding:18px 28px 6px}
.folder svg{width:100%;height:auto;display:block}
@media print{header,.actions,.warning,.big{display:none}}
"""
# Deleting : sent by the script, then the page shown REPLACES the deleted one in the
# history (location.replace) : the back button of a phone can not come back to it. A page
# shown again from the memory of the browser (back/forward cache, Safari keeps even
# no-store pages) is asked again : a deleted game sends to the list
SCRIPT = ('<script>function send(f){fetch(f.action,{method:"POST",body:new URLSearchParams(new FormData(f))})'
          '.then(function(r){if(r.status==403){r.text().then(function(t){document.open();document.write(t);'
          'document.close();});}else{location.replace(r.url);}});return false;}'
          'window.addEventListener("pageshow",function(e){if(e.persisted)location.reload();});</script>')
FOLDER = ('<svg viewBox="0 0 64 48"><path d="M2 8a4 4 0 0 1 4-4h16l6 6h30a4 4 0 0 1 4 4v28a4 4 0 0 1-4 4H6'
          'a4 4 0 0 1-4-4z" fill="#d9a441"/><path d="M2 16h60v26a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4z" fill="#f0c05a"/></svg>')


def page(conf, title, body, back=True):
    _ = conf['_']
    warning = '' if conf['password'] else f'<div class="warning">{html.escape(_("gallery-warning"))}</div>'
    home = f'<a href="/">&larr; {html.escape(_("gallery-all"))}</a>' if back else ''
    return (f'<!doctype html><html lang="{conf["lang"]}"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(title)}</title><style>{STYLE}</style>{SCRIPT}</head><body>'
            f'<header>{home}<h1>{html.escape(title)}</h1></header>{warning}{body}</body></html>')


def describe(date, game):
    '''
    "High Score - 15/10/2026 10:50" from the folders
    '''
    name, _, stamp = game.rpartition('_')
    if len(stamp) >= 12 and stamp.isdigit():
        return f"{name} - {stamp[6:8]}/{stamp[4:6]}/{stamp[0:4]} {stamp[8:10]}:{stamp[10:12]}"
    return f"{game} - {date.replace('_', '/')}"


class Handler(BaseHTTPRequestHandler):
    server_version = 'RaspyDarts'

    def log_message(self, format, *args):
        pass

    # -- answers
    def send(self, code, content, kind='text/html; charset=utf-8', headers=None):
        data = content.encode('utf-8') if isinstance(content, str) else content
        self.send_response(code)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(data)))
        if kind.startswith('text/html'):
            # Going back after a deletion asks the page again (no deleted game shown)
            self.send_header('Cache-Control', 'no-store')
        for header, value in (headers or {}).items():
            self.send_header(header, value)
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(data)

    def redirect(self, location, headers=None):
        self.send_response(303)
        self.send_header('Location', location)
        for header, value in (headers or {}).items():
            self.send_header(header, value)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def not_found(self, conf, text='gallery-notfound'):
        _ = conf['_']
        self.send(404, page(conf, _('gallery-notfound'), f'<p class="big">{html.escape(_(text))}</p>'))

    def send_file(self, path, kind, download_name=None):
        '''
        With byte ranges : video players (Safari above all) ask for parts
        '''
        size = os.path.getsize(path)
        start, end = 0, size - 1
        ranged = self.headers.get('Range', '')
        if ranged.startswith('bytes='):
            first, _, last = ranged[6:].split(',')[0].partition('-')
            if first:
                start = int(first)
                end = int(last) if last else size - 1
            elif last:
                start = max(0, size - int(last))
            end = min(end, size - 1)
            self.send_response(206)
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        else:
            self.send_response(200)
        self.send_header('Content-Type', kind)
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Length', str(end - start + 1))
        if download_name:
            quoted = urllib.parse.quote(download_name)
            self.send_header('Content-Disposition', f"attachment; filename*=UTF-8''{quoted}")
        self.end_headers()
        if self.command == 'HEAD':
            return
        with open(path, 'rb') as file:
            file.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk = file.read(min(65536, remaining))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    return
                remaining -= len(chunk)

    # -- access
    def logged_in(self, conf):
        good = token(conf['password'])
        return {'Set-Cookie': f'{COOKIE}={good}; Path=/; Max-Age=31536000; SameSite=Lax'}

    def allowed(self, conf, query):
        '''
        True if no password, or the right key (QR code, cookie). A key in the address is
        kept as a cookie, then removed from the address. None : already answered
        '''
        if not conf['password']:
            return True
        good = token(conf['password'])
        if query.get('k', [''])[0] == good:
            self.redirect(self.path.split('?')[0], self.logged_in(conf))
            return None
        jar = cookies.SimpleCookie(self.headers.get('Cookie', ''))
        return COOKIE in jar and hmac.compare_digest(jar[COOKIE].value, good)

    def login_page(self, conf, wrong=False):
        _ = conf['_']
        message = f'<p>{html.escape(_("gallery-wrong"))}</p>' if wrong else ''
        body = (f'<form class="login" method="post" action="/login?next={urllib.parse.quote(self.path)}">'
                f'{message}<p>{html.escape(_("gallery-password-label"))}</p>'
                f'<input type="password" name="password" autofocus> <button>{html.escape(_("gallery-enter"))}</button></form>')
        self.send(200, page(conf, _('gallery-title'), body, back=False))

    # -- routes
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        conf = settings()
        _ = conf['_']
        url = urllib.parse.urlsplit(self.path)
        access = self.allowed(conf, urllib.parse.parse_qs(url.query))
        if access is None:
            return
        if not access:
            return self.login_page(conf)
        parts = [urllib.parse.unquote(part) for part in url.path.strip('/').split('/') if part]
        try:
            if not parts:
                return self.home(conf)
            if parts[0] == 'p' and len(parts) == 2:
                return self.partie(conf, parts[1])
            if parts[0] in ('f', 't', 'd', 'print') and len(parts) == 3:
                found = find(conf, urllib.parse.quote(parts[1], safe=''), parts[2])
                if found is None:
                    return self.not_found(conf, 'gallery-gone')
                path = found[2]
                kind = 'video/mp4' if path.lower().endswith(VIDEOS) else (
                    'image/png' if path.lower().endswith('.png') else 'image/jpeg')
                if parts[0] == 'f':
                    return self.send_file(path, kind)
                if parts[0] == 'd':
                    return self.send_file(path, kind, download_name=parts[2])
                if parts[0] == 't':
                    return self.send_file(thumbnail(path), 'image/jpeg')
                source = f"/f/{urllib.parse.quote(parts[1], safe='')}/{urllib.parse.quote(parts[2])}"
                return self.send(200, f'<!doctype html><html><body style="margin:0" onload="window.print()">'
                                      f'<img src="{source}" style="width:100%"></body></html>')
            if parts[0] == 'zip' and len(parts) == 2:
                return self.zip(conf, parts[1])
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            return self.send(500, page(conf, _('gallery-error'), f'<p class="big">{html.escape(str(error))}</p>'))
        self.not_found(conf)

    def do_POST(self):
        conf = settings()
        url = urllib.parse.urlsplit(self.path)
        query = urllib.parse.parse_qs(url.query)
        length = int(self.headers.get('Content-Length', '0') or 0)
        form = urllib.parse.parse_qs(self.rfile.read(length).decode('utf-8', 'replace')) if length else {}
        if url.path == '/login':
            target = query.get('next', ['/'])[0]
            if not target.startswith('/'):
                target = '/'
            if conf['password'] and check_password(form.get('password', [''])[0], conf['password']):
                return self.redirect(target, self.logged_in(conf))
            return self.login_page(conf, wrong=True)
        if not self.allowed(conf, {}):
            return self.login_page(conf)
        parts = [urllib.parse.unquote(part) for part in url.path.strip('/').split('/') if part]
        if parts and parts[0] == 'delete' and len(parts) in (2, 3):
            partie = urllib.parse.quote(parts[1], safe='')
            # The key of a QR code lets see and download, not delete
            if conf['password'] and not check_password(form.get('password', [''])[0], conf['password']):
                _ = conf['_']
                back = f"/p/{partie}" if len(parts) == 3 else '/'
                return self.send(403, page(conf, _('gallery-wrong'), f'<p class="big"><a href="{back}">&larr; {html.escape(_("gallery-back"))}</a></p>'))
            if len(parts) == 3:
                found = find(conf, partie, parts[2])
                if found is not None:
                    os.remove(found[2])
                    if not memories(conf, found[0], found[1]):
                        # Its last memory : the game goes, back to the list
                        delete_partie(conf, found[0], found[1])
                        return self.redirect('/')
                return self.redirect(f"/p/{partie}")
            found = find(conf, partie)
            if found is not None:
                delete_partie(conf, found[0], found[1])
            return self.redirect('/')
        if parts == ['delete-many']:
            if conf['password'] and not check_password(form.get('password', [''])[0], conf['password']):
                _ = conf['_']
                return self.send(403, page(conf, _('gallery-wrong'), f'<p class="big"><a href="/">&larr; {html.escape(_("gallery-back"))}</a></p>'))
            for raw in form.get('p', []):
                found = find(conf, urllib.parse.quote(raw, safe=''))
                if found is not None:
                    delete_partie(conf, found[0], found[1])
            return self.redirect('/')
        self.not_found(conf)

    def home(self, conf):
        _ = conf['_']
        cards = []
        for _changed, date, game, files in parties(conf):
            ident = partie_id(date, game)
            photos = sum(1 for name, _p in files if name.lower().endswith(PHOTOS))
            count = _('gallery-counts').replace('{photos}', str(photos)).replace('{videos}', str(len(files) - photos))
            cards.append(f'<div class="card"><label class="pick"><input type="checkbox" name="p" value="{html.escape(f"{date}/{game}")}" onchange="picked()"></label>'
                         f'<a href="/p/{ident}" class="folder">{FOLDER}</a>'
                         f'<div class="name"><b>{html.escape(describe(date, game))}</b><br>{html.escape(count)}</div></div>')
        if cards:
            confirm = self.confirmation(conf, 'gallery-delete-selected')
            script = ('<script>function picked(){document.getElementById("many").disabled='
                      '!document.querySelector("input[name=p]:checked");}</script>')
            body = (f'<form method="post" action="/delete-many" onsubmit="{confirm}"><input type="hidden" name="password">'
                    f'<div class="big"><button class="delete" id="many" disabled>{html.escape(_("gallery-delete-selection"))}</button></div>'
                    f'<div class="grid">{"".join(cards)}</div></form>{script}')
        else:
            body = f'<p class="big">{html.escape(_("gallery-none"))}</p>'
        self.send(200, page(conf, _('gallery-title'), body, back=False))

    def partie(self, conf, raw):
        _ = conf['_']
        ident = urllib.parse.quote(raw, safe='')
        found = find(conf, ident)
        files = memories(conf, found[0], found[1]) if found is not None else []
        if not files:
            # Deleted (back button, old QR code) : the list of the games
            return self.redirect('/')
        date, game, _path = found
        texts = {key: html.escape(_(key)) for key in ('gallery-download', 'gallery-print', 'gallery-delete')}
        confirm_one, confirm_all = self.confirmation(conf, 'gallery-delete-one'), self.confirmation(conf, 'gallery-delete-all')
        cards = []
        for name, _path in files:
            quoted = urllib.parse.quote(name)
            if name.lower().endswith(VIDEOS):
                view = f'<video controls preload="none" poster="/t/{ident}/{quoted}" src="/f/{ident}/{quoted}" style="width:100%"></video>'
                printing = ''
            else:
                view = f'<a href="/f/{ident}/{quoted}"><img loading="lazy" src="/t/{ident}/{quoted}"></a>'
                printing = f'<a href="/print/{ident}/{quoted}" target="_blank">{texts["gallery-print"]}</a>'
            cards.append(f'<div class="card">{view}'
                         f'<div class="name">{html.escape(os.path.splitext(name)[0])}</div><div class="actions">'
                         f'<a href="/d/{ident}/{quoted}">{texts["gallery-download"]}</a>{printing}'
                         f'<form method="post" action="/delete/{ident}/{quoted}" onsubmit="{confirm_one}"><input type="hidden" name="password">'
                         f'<button class="delete">{texts["gallery-delete"]}</button></form></div></div>')
        # On a phone : each file downloaded in turn (sharing them all needs HTTPS)
        downloads = json.dumps([f"/d/{ident}/{urllib.parse.quote(name)}" for name, _p in files])
        script = (f'<script>async function downloadAll(){{for(const url of {downloads}){{'
                  f'const a=document.createElement("a");a.href=url;a.download="";document.body.appendChild(a);'
                  f'a.click();a.remove();await new Promise(r=>setTimeout(r,1200));}}}}</script>')
        actions = (f'<div class="big"><button onclick="downloadAll()">{html.escape(_("gallery-download-all"))}</button>'
                   f'<a href="/zip/{ident}">{html.escape(_("gallery-zip"))}</a>'
                   f'<form method="post" action="/delete/{ident}" onsubmit="{confirm_all}"><input type="hidden" name="password">'
                   f'<button class="delete">{html.escape(_("gallery-delete-game"))}</button></form></div>')
        grid = f'<div class="grid">{"".join(cards)}</div>' if cards else f'<p class="big">{html.escape(_("gallery-empty"))}</p>'
        self.send(200, page(conf, describe(date, game), actions + grid + script))

    def confirmation(self, conf, question):
        '''
        Script of a delete button : the password is asked when there is one, else a
        simple confirmation
        '''
        _ = conf['_']
        if conf['password']:
            text = json.dumps(f"{_(question)}\n{_('gallery-delete-password')}")
            return html.escape(f"var p=prompt({text});if(p===null)return false;this.password.value=p;return send(this);")
        return html.escape(f"if(!confirm({json.dumps(_(question))}))return false;return send(this);")

    def zip(self, conf, raw):
        found = find(conf, urllib.parse.quote(raw, safe=''))
        if found is None:
            return self.not_found(conf)
        date, game, _path = found
        with tempfile.TemporaryFile() as archive:
            # Stored, not compressed : photos and videos are already
            with zipfile.ZipFile(archive, 'w', zipfile.ZIP_STORED) as content:
                for name, path in memories(conf, date, game):
                    content.write(path, name)
            size = archive.tell()
            archive.seek(0)
            self.send_response(200)
            self.send_header('Content-Type', 'application/zip')
            self.send_header('Content-Length', str(size))
            name = urllib.parse.quote(f"{game}.zip")
            self.send_header('Content-Disposition', f"attachment; filename*=UTF-8''{name}")
            self.end_headers()
            shutil.copyfileobj(archive, self.wfile)


def main():
    server = ThreadingHTTPServer(('0.0.0.0', PORT), Handler)
    server.daemon_threads = True
    print(f"Gallery on port {PORT}", flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
