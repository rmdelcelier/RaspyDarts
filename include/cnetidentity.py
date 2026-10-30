"""Un compte authentifie par borne reseau ; aucun nom saisi librement."""
import json
import queue
import re
import ssl
import threading
import time
import urllib.request


def server_user(session):
    from include.caccount import BASE, COOKIE
    token = session.get('token', '')
    if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{30,128}', token):
        return None
    request = urllib.request.Request(BASE + '/joueurs-auth/me', headers={
        'Cookie': COOKIE + '=' + token, 'Cache-Control': 'no-store'})
    with urllib.request.urlopen(request, timeout=8, context=ssl.create_default_context()) as response:
        data = json.loads(response.read(8192).decode('utf-8'))
    user = data.get('user')
    if user is None:
        return None
    if (not isinstance(user, dict) or type(user.get('id')) is not int or user['id'] < 1
            or not isinstance(user.get('username'), str)
            or not re.fullmatch(r'[A-Za-z0-9_-]{3,18}', user['username'])):
        raise ValueError('Identite du serveur invalide')
    return {'id': user['id'], 'username': user['username']}


def wait_user(display, session):
    """
    Account of the session checked by the server, while the screen says it (back : given up)
    """
    from include.caccount import wait_screen
    results = queue.Queue(maxsize=1)
    def worker():
        try:
            results.put((server_user(session), False))
        except Exception:
            results.put((None, True))
    threading.Thread(target=worker, daemon=True).start()
    previous = getattr(display, '_lobby_auth_open', False)
    display._lobby_auth_open = True
    try:
        user, failed = wait_screen(display, ('online-title', 'online-checking-account', 'online-escape-back'), results)
        if user is None and failed is None:
            raise RuntimeError('online-check-cancelled')
        if failed:
            raise RuntimeError('online-error-unreachable')
        return user
    finally:
        display._lobby_auth_open = previous


def network_players(display, players_bank=None, players_color=None):
    from include import caccount as accounts
    from include.cchat import ensure_session
    session = getattr(display, '_lobby_account_session', None) or accounts.load_session()
    for attempt in range(2):
        if not isinstance(session, dict) or session.get('expires', 0) <= time.time():
            session = accounts.login_dialog(display)
        if not session:
            return 1, 'escape', False
        try:
            user = wait_user(display, session)
        except RuntimeError as error:
            display.message([display.lang.translate(str(error))], wait=2200)
            return 1, 'escape', False
        if user is not None:
            break
        # Session refusee par le VPS : ne jamais utiliser son identite locale.
        current = getattr(display, '_lobby_chat_client', None)
        if current is not None:
            current.stop()
        display._lobby_chat_client = None
        display._lobby_account_session = None
        accounts.forget_session()
        session = None
    else:
        display.message([display.lang.translate('online-account-retry')], wait=1800)
        return 1, 'escape', False
    session = dict(session, user=user)
    current = getattr(display, '_lobby_chat_client', None)
    if current is not None and (current.token != session['token'] or current.auth_failed):
        current.stop()
        display._lobby_chat_client = None
    display._lobby_account_session = session
    display._lobby_ready_online = True
    display._lobby_chat_retry = 0
    if ensure_session(display, prompt=False) is None:
        display.message([display.lang.translate('online-chat-impossible')], wait=1800)
        return 1, 'escape', False
    label = '{:03d} · {}'.format(user['id'], user['username'])
    display.message([display.lang.translate('online-network-player') + ' ' + label], wait=1000)
    # ChtiDarts : un compte authentifie et des joueurs invites.
    # Le premier joueur reste toujours l'identite verifiee par le VPS.
    sets, selected, _, colors = display.players_menu(
        [label],
        context='netcreate',
        bank=players_bank,
        sets=None,
        players_color=players_color
    )

    if selected == 'escape':
        return 1, 'escape', False

    # Les invites ne peuvent pas remplacer le compte authentifie.
    guests = []
    for name in selected:
        if not isinstance(name, str):
            continue
        name = name.strip()
        if not name or name.casefold() == label.casefold():
            continue
        if name.casefold() not in [g.casefold() for g in guests]:
            guests.append(name)
    guests = guests[:15]

    return 1, [label] + guests, False
