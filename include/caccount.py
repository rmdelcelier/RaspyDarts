"""Compte du joueur en ligne de la borne : TLS, mot de passe masqué, session privée."""
import json
import os
import queue
import ssl
import threading
import time
import urllib.request
import urllib.error
from http.cookies import SimpleCookie
from pathlib import Path

from include import cpaths

# Server of the online games (accounts, chat, rooms) : the first of the favorite servers
# (Divers > Favoris), chosen again in the online games screen
SERVER = 'video.chtiraspycard.fr'
BASE = 'https://' + SERVER
COOKIE = '__Host-chti_session'


def set_server(host):
    """
    Server of the online games (a favorite server : name, or name:port of the former network
    games, the port left out), the default one if none given
    """
    global SERVER, BASE
    host = str(host or '').strip().rstrip('/')
    for prefix in ('https://', 'http://', 'wss://'):
        if host.startswith(prefix):
            host = host[len(prefix):]
    host = host.split('/')[0].split(':')[0]
    if host and host not in ('False', 'None'):
        SERVER = host
        BASE = 'https://' + SERVER


def session_file():
    return Path(cpaths.user_dir()) / 'online_account.json'


def forget_session():
    try:
        session_file().unlink()
    except FileNotFoundError:
        pass


def load_session():
    try:
        data = json.loads(session_file().read_text(encoding='utf-8'))
        if (isinstance(data, dict) and isinstance(data.get('token'), str)
                and 30 <= len(data['token']) <= 128
                and all(c.isalnum() or c in '_-' for c in data['token'])
                and isinstance(data.get('user'), dict)
                and isinstance(data['user'].get('id'), int)
                and isinstance(data['user'].get('username'), str)
                and data.get('expires', 0) > time.time()
                # An account of this server (sessions of before : asked again)
                and data.get('server') == SERVER):
            return data
    except (OSError, ValueError, TypeError):
        pass
    return None


def save_session(data):
    path = session_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name+'.tmp')
    fd = os.open(str(temp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as file:
            json.dump(data, file)
        os.replace(str(temp), str(path))
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass


def authenticate(username, password, remember=False):
    """Le mot de passe n'est ni enregistré ni inclus dans les journaux."""
    payload = json.dumps({'username':username, 'password':password,
                          'remember':bool(remember)}).encode('utf-8')
    request = urllib.request.Request(BASE+'/joueurs-auth/login', data=payload,
        headers={'Content-Type':'application/json', 'Origin':BASE}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=10, context=ssl.create_default_context()) as response:
            data = json.loads(response.read(8192).decode('utf-8'))
            cookie = SimpleCookie()
            for value in response.headers.get_all('Set-Cookie', []):
                cookie.load(value)
            token = cookie[COOKIE].value
        return {'token':token, 'user':data['user'], 'server':SERVER,
                'expires':time.time()+(30*86400 if remember else 12*3600)}
    except urllib.error.HTTPError as error:
        if error.code == 401:
            raise ValueError('online-error-credentials')
        if error.code == 429:
            raise ValueError('online-error-attempts')
        if error.code == 400:
            raise ValueError('online-error-rules')
        raise ValueError('online-error-unavailable')
    except (OSError, ValueError, KeyError):
        raise ValueError('online-error-unreachable')


def wait_screen(display, texts, results):
    """
    Texts shown (keys of the translations) while a request runs in a thread, until its result
    is in results : (result, error). Back : None, None (the request ends alone)
    """
    import pygame
    from include.cchat import draw_line
    from include.cscreen import ESCAPE_KEYS
    w, h = display.res['x'], display.res['y']
    display.display_background()
    for index, text in enumerate(texts):
        draw_line(display, display.lang.translate(text), pygame.Rect(int(w*.1), int(h*(.3+index*.13)), int(w*.8), int(h*.08)),
                  display.colorset['menu-text-white'], align='Center')
    display.update_screen()
    while True:
        try:
            return results.get_nowait()
        except queue.Empty:
            pass
        if display.rpi.listen_inputs(['arrows'], ['escape'], timeout=100) in ESCAPE_KEYS:
            return None, None


def login_dialog(display):
    """
    Account of the borne asked by the input of the game (keyboard, keyboard on the screen,
    knob of a USB pad, buttons) : pseudo, password (hidden), kept or not on the borne.
    The session, None : given up
    """
    translate = display.lang.translate
    # Account required : a QR code to create one with a phone
    if not display.online_account_screen(BASE + '/joueurs'):
        return None
    name = ''
    while True:
        name = display.input_value_item('string', name, 3, 18, text='online-username')
        if name in (None, False, 'escape'):
            return None
        if not all(c.isascii() and (c.isalnum() or c in '_-') for c in name):
            display.message([translate('online-username-rules')], 2500, display.colorset['menu-ko'])
            continue
        password = display.input_value_item('string', '', 10, 128, text='online-password', hidden=True)
        if password in (None, False, 'escape'):
            return None
        remember = display.ask_yes_no(translate('online-remember'), cancel=True)
        if remember is None:
            return None
        results = queue.Queue(maxsize=1)

        def worker(name=name, password=password, remember=remember):
            try:
                results.put((authenticate(name, password, remember), None))
            except Exception as error:
                results.put((None, str(error)))
        threading.Thread(target=worker, daemon=True).start()
        password = ''
        result, error = wait_screen(display, ('online-checking-account', 'online-escape-back'), results)
        if result:
            try:
                if remember:
                    save_session(result)
                else:
                    forget_session()
            except OSError:
                # Connexion valide, conservation limitée à la mémoire.
                pass
            user = result.get('user') or {}
            display.message([translate('online-logged-in').format(name=user.get('username', name))],
                            2000, display.colorset['menu-ok'])
            return result
        if error is None:
            return None
        display.message([translate(error)], 2500, display.colorset['menu-ko'])


def logout(display):
    session = getattr(display, '_lobby_account_session', None)
    client = getattr(display, '_lobby_chat_client', None)
    if client:
        client.stop()
    display._lobby_chat_client = None
    display._lobby_account_session = None
    display._lobby_ready_online = False
    display._lobby_chat_status = 'online-account-required'
    display._lobby_chat_retry = 0
    try:
        forget_session()
    except OSError:
        pass
    if session:
        def revoke():
            request=urllib.request.Request(BASE+'/joueurs-auth/logout',data=b'{}',
                headers={'Origin':BASE,'Content-Type':'application/json',
                         'Cookie':COOKIE+'='+session['token']},method='POST')
            try:
                urllib.request.urlopen(request,timeout=8,context=ssl.create_default_context()).close()
            except Exception:
                pass
        threading.Thread(target=revoke,daemon=True).start()
