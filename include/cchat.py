"""Client du salon des joueurs en ligne (Python 3.7+, websocket-client)."""
import json
import queue
import ssl
import threading
import time
from collections import deque

from include import caccount
from include.cscreen import ENTER_KEYS, ESCAPE_KEYS, UP_KEYS, DOWN_KEYS, LEFT_KEYS, RIGHT_KEYS


def lobby_url():
    return 'wss://' + caccount.SERVER + '/borne-lobby'


class ChatClient:
    def __init__(self, name, token, visible=True):
        self.name, self.token = name, token
        self.visible = visible
        self.auth_failed = False
        self.match_live = None  # Spectators (not used yet)
        self.game_activity = {'playing': False}
        self.activity_version = 0
        self.commands = queue.Queue(maxsize=30)
        self.lock = threading.Lock()
        self.stopped = threading.Event()
        self.ws = None
        self.ident = None
        self.players = []
        self.events = deque(maxlen=150)
        # Keys of the translations : online-connecting, online-connected, online-account-required,
        # online-offline-retry
        self.status = 'online-connecting'
        self.thread = threading.Thread(target=self.run, daemon=True)

    def set_activity(self, data):
        with self.lock:
            if not data.get('playing'):
                self.match_live = None
            self.game_activity = dict(data)
            self.activity_version += 1

    def start(self):
        self.thread.start()

    def snapshot(self):
        with self.lock:
            return self.status, self.ident, list(self.players), list(self.events)

    def command(self, data):
        with self.lock:
            if self.status != 'online-connected':
                return False
        try:
            self.commands.put_nowait(data)
            return True
        except queue.Full:
            return False

    def stop(self):
        self.stopped.set()
        if self.ws:
            try:
                self.ws.close(timeout=1)
            except Exception:
                pass

    def run(self):
        import websocket
        while not self.stopped.is_set():
            connection = None
            try:
                connection = websocket.create_connection(
                    lobby_url(), timeout=4,
                    header=['Authorization: Bearer ' + self.token],
                    sslopt={'cert_reqs': ssl.CERT_REQUIRED})
                self.ws = connection
                if self.stopped.is_set():
                    break
                if self.visible:
                    connection.send(json.dumps({'type': 'hello', 'name': self.name}))
                activity_sent = -1
                next_activity = 0
                next_live = 0
                last_live = None
                last_live_at = 0
                connection.settimeout(0.2)
                while not self.stopped.is_set():
                    with self.lock:
                        version = self.activity_version
                        data = dict(self.game_activity)
                    if version != activity_sent or time.monotonic() >= next_activity:
                        data.update(type='activity', visible=self.visible)
                        connection.send(json.dumps(data))
                        activity_sent = version
                        next_activity = time.monotonic() + 15
                    with self.lock:
                        live = self.match_live if self.game_activity.get('playing') else None
                    now = time.monotonic()
                    if live is not None and now >= next_live and (live != last_live or now-last_live_at >= 5):
                        payload = json.dumps(live, ensure_ascii=False)
                        if len(payload.encode('utf-8')) <= 3900:
                            connection.send(payload)
                        next_live = now + 0.6
                        last_live_at = now
                        last_live = live
                    try:
                        command = self.commands.get_nowait()
                    except queue.Empty:
                        command = None
                    if command is not None:
                        connection.send(json.dumps(command))
                    try:
                        raw = connection.recv()
                    except websocket.WebSocketTimeoutException:
                        continue
                    if not raw:
                        raise ConnectionError('Deconnexion')
                    event = json.loads(raw)
                    if not isinstance(event, dict):
                        continue
                    with self.lock:
                        kind = event.get('type')
                        if kind == 'welcome':
                            self.ident = event.get('id')
                            account = event.get('account')
                            if isinstance(account, dict):
                                self.name = '{:03d} · {} (borne)'.format(account['id'], account['username'])
                        elif kind == 'presence':
                            incoming = event.get('players', [])
                            incoming = [p for p in incoming if isinstance(p, dict) and p.get('id')]
                            previous = {p['id'] for p in self.players}
                            # La premiere liste sert de reference ; pas de son pour soi-meme.
                            if self.status == 'online-connected':
                                for player in incoming:
                                    if player['id'] != self.ident and player['id'] not in previous:
                                        self.events.append({'type': 'joined', 'from': player['id'],
                                                            'name': player.get('name', '?'),
                                                            '_received': time.monotonic()})
                            self.players = incoming
                            self.status = 'online-connected'
                        else:
                            event['_received'] = time.monotonic()
                            self.events.append(event)
            except Exception as error:
                denied = getattr(error, 'status_code', None) in (401, 403)
                if denied:
                    self.auth_failed = True
                    self.stopped.set()
                    try:
                        from include.caccount import forget_session
                        forget_session()
                    except OSError:
                        pass
                with self.lock:
                    self.status = 'online-account-required' if denied else 'online-offline-retry'
                    self.players = []
                    self.ident = None
                    self.events.clear()
                while True:
                    try:
                        self.commands.get_nowait()
                    except queue.Empty:
                        break
            finally:
                if connection:
                    try:
                        connection.close(timeout=1)
                    except Exception:
                        pass
                self.ws = None
            self.stopped.wait(3)


# Notifications, screens of the chat (the look of the theme, the inputs of the game)

def draw_line(display, value, rect, color, size=None, align='Left'):
    """
    A line of text in the font of the theme, cut to the width of its box (the fonts are kept
    once loaded : display.get_font)
    """
    font = display.get_font(int(size or rect.height * .7))
    value = ' '.join(str(value).split())
    if font.size(value)[0] > rect.width:
        while value and font.size(value + '...')[0] > rect.width:
            value = value[:-1]
        value += '...'
    image = font.render(value, True, color)
    x = rect.x if align == 'Left' else rect.x + (rect.width - image.get_width()) // 2
    display.screen.blit(image, (x, rect.y + (rect.height - image.get_height()) // 2))


def shortcuts(display, name):
    """
    {id: (shortcut, text)} of the buttons of an online screen : menus online_lobby and
    online_chat of the files of menus (the screen draws them itself)
    """
    buttons = {}
    for button in display.menus().menu(name).get('buttons') or []:
        if isinstance(button, dict) and button.get('id'):
            buttons[str(button['id'])] = (button.get('shortcut'), str(button.get('text') or button['id']))
    return buttons


def draw_button(display, rect, button, menu_name, background, text=None):
    """
    A button of an online screen : its background, its text (translated), its shortcut in its
    corner as in the menus of the game (hidden when the theme hides them, c shows them)
    """
    import pygame
    shortcut, label = button
    display.new_blit_rect2(rect, background, corners='All', border_radius=int(rect.height * .15), alpha=255)
    draw_line(display, display.lang.translate(text or label), rect.inflate(-int(rect.width * .08), -int(rect.height * .45)),
              display.colorset['menu-text-black'], align='Center')
    # Shown as in the menus of the theme : main-sub-menu-shortcuts None (sombre) hides them
    # (c shows them), the menu of the files decides over it
    settings = dict(show=display.colorset.get('main-sub-menu-shortcuts') is not None)
    settings.update(display.menus().menu(menu_name).get('shortcuts') or {})
    key = display.button_label({'shortcut': shortcut}, {'shortcuts': settings})
    if key:
        draw_line(display, key, pygame.Rect(rect.x + 6, rect.y + 3, rect.width // 3, int(rect.height * .3)),
                  display.colorset['menu-shortcut'])


def _notify(display, invitation=False, connexion=False):
    name = ('chat_connexion' if connexion else
            'chat_invitation' if invitation else 'chat_message')
    try:
        # Sound of the theme (sounds/chat_message...), the default one otherwise
        channel = display.play_sound(name)
        if channel is None:
            print('[LOBBY CHAT] Lecture non confirmee : ' + name, flush=True)
    except Exception as error:
        print('[LOBBY CHAT] ' + name + ' : ' + str(error), flush=True)


def _new_events(display, client, seen):
    events = client.snapshot()[3]
    fresh = []
    for event in events:
        signature = (event.get('_received'), event.get('type'), event.get('invitation'),
                     event.get('from'), bool(event.get('outgoing')), event.get('text'))
        if signature in seen:
            continue
        seen.add(signature)
        fresh.append(event)
        if not event.get('outgoing'):
            if event.get('type') == 'joined':
                _notify(display, connexion=True)
            elif event.get('type') in ('chat', 'invite'):
                _notify(display, invitation=event.get('type') == 'invite')
    if len(seen) > 600:
        seen.intersection_update({(e.get('_received'), e.get('type'), e.get('invitation'),
                                  e.get('from'), bool(e.get('outgoing')), e.get('text')) for e in events})
    return fresh


def compose_message(display, recipient):
    """
    A message typed by the input of the game (keyboard, keyboard on the screen, knob of a
    USB pad). None : given up
    """
    title = display.lang.translate('online-message-for').format(name=recipient)
    text = display.input_value_item('string', '', 1, 160, text=title, align='Left')
    if text in (None, False, 'escape') or not str(text).strip():
        return None
    return str(text).strip()


def ensure_session(display, prompt=False):
    """Connexion uniquement avec un compte enregistré ; aucun accès invité."""
    if getattr(display, '_lobby_auth_open', False):
        return None
    current = getattr(display, '_lobby_chat_client', None)
    ready = bool(getattr(display, '_lobby_ready_online', False))
    if current is not None and current.auth_failed:
        display._lobby_account_session = None
        display._lobby_chat_status = 'online-account-required'
    if current is not None and not current.stopped.is_set():
        if current.visible == ready:
            return current
        current.stop()
    display._lobby_chat_client = None
    now = time.monotonic()
    if not prompt and now < getattr(display, '_lobby_chat_retry', 0):
        return None
    display._lobby_chat_retry = now + 3
    try:
        import websocket
        from include.caccount import load_session, login_dialog
        session = getattr(display, '_lobby_account_session', None)
        if session is None:
            session = load_session()
        if session and session.get('expires', 0) <= time.time():
            session = None
        if session is None and prompt:
            display._lobby_auth_open = True
            try:
                session = login_dialog(display)
            finally:
                display._lobby_auth_open = False
        if not session:
            display._lobby_chat_status = 'online-account-required'
            return None
        display._lobby_account_session = session
        account = session['user']
        name = '{:03d} · {} (borne)'.format(account['id'], account['username'])
        current = ChatClient(name, session['token'], visible=ready)
        display._lobby_chat_client = current
        display._lobby_chat_seen = set()
        display._lobby_chat_resolved = set()
        display._lobby_chat_unread = 0
        current.set_activity(getattr(display, '_lobby_game_activity', {'playing': False}))
        current.start()
        import atexit
        atexit.register(current.stop)
        return current
    except Exception as error:
        display._lobby_chat_status = 'online-chat-unavailable'
        import traceback
        display.logs.warning('Online games : session unavailable ({}) {}'.format(
            type(error).__name__, ' | '.join(traceback.format_exc(limit=-3).splitlines())))
        if prompt:
            display.message([display.lang.translate('online-chat-unavailable-check')])
        # Aucun mot de passe ni jeton dans les logs.
        print('[LOBBY PRESENCE] Connexion au compte indisponible', flush=True)
        return None


def set_ready(display, ready):
    """
    The borne seen online by the others (ready) or not : its chat connected again so
    """
    if bool(getattr(display, '_lobby_ready_online', False)) != bool(ready):
        toggle_ready(display)


def toggle_ready(display):
    previous = bool(getattr(display, '_lobby_ready_online', False))
    display._lobby_ready_online = not previous
    display._lobby_chat_retry = 0
    current = getattr(display, '_lobby_chat_client', None)
    if current is not None:
        current.stop()
        display._lobby_chat_client = None
    client = ensure_session(display, prompt=not previous)
    if client is None:
        display._lobby_ready_online = previous
        display._lobby_chat_retry = 0
        ensure_session(display)
    return bool(getattr(display, '_lobby_ready_online', False))


def pump_presence(display):
    """Notifications sur le thread d'affichage, jamais dans le thread reseau."""
    if getattr(display, '_lobby_chat_open', False):
        return
    now = time.monotonic()
    if now < getattr(display, '_lobby_chat_next_pump', 0):
        return
    display._lobby_chat_next_pump = now + .1
    client = getattr(display, '_lobby_chat_client', None)
    if client is None:
        return
    for event in _new_events(display, client, display._lobby_chat_seen):
        if not event.get('outgoing') and event.get('type') in ('chat', 'invite'):
            display._lobby_chat_unread = min(99, display._lobby_chat_unread + 1)


# Keys of the translations of the quick replies
QUICK_REPLIES = ('online-reply-1', 'online-reply-2', 'online-reply-3',
                 'online-reply-4', 'online-reply-5', 'online-reply-6')


def choose_quick_reply(display, client, recipient_id, recipient):
    """
    A quick reply chosen in a menu of the game (its look, its inputs). None : given up
    """
    items = [{'id': 'reply{}'.format(index), 'action': 'reply', 'text': text, 'shortcut': 'F{}'.format(index + 1)}
             for index, text in enumerate(QUICK_REPLIES)]
    back = {'id': 'back', 'action': 'back', 'text': 'back', 'footer': 'left', 'shortcut': 'escape'}
    title = display.lang.translate('online-message-for').format(name=recipient)
    choice = display.run_menu('online_quick', items + [back], items + [back], title=title).get('id')
    if choice == 'back':
        return None
    status, ident, players, events = client.snapshot()
    if status != 'online-connected' or not any(p.get('id') == recipient_id for p in players):
        display.message([display.lang.translate('online-player-gone')])
        return None
    # Sent in the language of the borne which writes it
    return display.lang.translate(QUICK_REPLIES[int(choice[5:])])


def show(display):
    import pygame
    translate = display.lang.translate
    colors = display.colorset
    buttons = shortcuts(display, 'online_chat')
    lobby = shortcuts(display, 'online_lobby')
    if not getattr(display, '_lobby_ready_online', False):
        display.message([translate('online-chat-needs-ready').format(key=lobby.get('ready', ('F8',))[0])])
        return
    client = ensure_session(display, prompt=True)
    if client is None:
        return
    display._lobby_chat_open = True
    display._lobby_chat_unread = 0
    selected = None
    action_index = 0
    # Where the arrows are : a button at the bottom (its name), 'logout', or 'player' (the list
    # of the players : the one selected)
    focus = None
    resolved = display._lobby_chat_resolved
    seen_events = display._lobby_chat_seen
    note = translate('online-chat-hint')
    # Buttons at the bottom, in this order (left / right go from one to the next)
    order = [name for name in ('write', 'quick', 'invite', 'accept', 'refuse', 'back') if name in buttons]
    keys = {buttons[name][0]: name for name in buttons if buttons[name][0]}
    focus = order[0] if order else 'player'
    try:
        while True:
            for event in _new_events(display, client, seen_events):
                kind = event.get('type')
                if kind == 'error':
                    note = event.get('message', translate('online-send-error'))
                elif kind == 'reply':
                    note = translate('online-invitation-accepted' if event.get('answer') == 'accept'
                                     else 'online-invitation-refused').format(name=event.get('name', '?'))
                elif event.get('outgoing') and kind == 'chat':
                    note = translate('online-message-sent')
                elif event.get('outgoing') and kind == 'invite':
                    note = translate('online-invitation-sent')
            status, ident, players, events = client.snapshot()
            if client.auth_failed:
                display._lobby_account_session = None
                display.message([translate('online-session-expired')])
                return
            players = [p for p in players if isinstance(p, dict) and p.get('id') != ident]
            ids = [p['id'] for p in players]
            if selected not in ids:
                selected = ids[0] if ids else None
            pending = [e for e in events if e.get('type') == 'invite'
                       and not e.get('outgoing') and e.get('invitation') not in resolved
                       and time.monotonic() - e['_received'] < e.get('ttl', 90)]
            for e in events:
                if e.get('type') == 'reply':
                    resolved.add(e.get('invitation'))
            pending = [e for e in pending if e.get('invitation') not in resolved]
            invitation = pending[0] if pending else None

            w, h = display.res['x'], display.res['y']
            display.display_background()
            radius = int(h * .012)
            display.blit_text2('online-chat-title', pygame.Rect(int(w*.03), int(h*.02), int(w*.94), int(h*.08)),
                               colors['menu-text-white'], align='Left')
            draw_line(display, client.name + ' | ' + translate(status),
                      pygame.Rect(int(w*.03), int(h*.105), int(w*.70), int(h*.05)), colors['menu-text-white'])
            zones = {}
            if 'logout' in buttons:
                logout_rect = pygame.Rect(int(w*.76), int(h*.105), int(w*.21), int(h*.05))
                zones['logout'] = logout_rect
                draw_button(display, logout_rect, buttons['logout'], 'online_chat',
                            colors['menu-selected'] if focus == 'logout' else colors['menu-buttons'])
            players_rect = pygame.Rect(int(w*.03), int(h*.18), int(w*.30), int(h*.55))
            display.new_blit_rect2(players_rect, colors['menu-header'], corners='All', border_radius=radius, alpha=255)
            # Text of a panel : menu-text ; of a button or of the line chosen : menu-text-black
            draw_line(display, translate('online-players-connected'),
                      pygame.Rect(int(w*.045), int(h*.195), int(w*.27), int(h*.045)), colors['menu-text'])
            offset = max(0, ids.index(selected)-7) if selected in ids else 0
            for row, player in enumerate(players[offset:offset+8]):
                rect = pygame.Rect(int(w*.04), int(h*(.26+row*.055)), int(w*.28), int(h*.049))
                zones['player|'+player['id']] = rect
                if player['id'] == selected:
                    display.new_blit_rect2(rect, colors['menu-selected'], corners='All', border_radius=radius, alpha=255)
                    if focus == 'player':
                        # The arrows on the list : its frame
                        pygame.draw.rect(display.screen, colors['menu-text-white'], rect, 3, border_radius=radius)
                draw_line(display, player['name'], rect.inflate(-12, -8),
                          colors['menu-text-black'] if player['id'] == selected else colors['menu-text'])
            if not players:
                draw_line(display, translate('online-no-other-player'),
                          pygame.Rect(int(w*.045), int(h*.27), int(w*.27), int(h*.045)), colors['menu-inactive'])
            log_rect = pygame.Rect(int(w*.35), int(h*.18), int(w*.62), int(h*.55))
            display.new_blit_rect2(log_rect, colors['menu-header'], corners='All', border_radius=radius, alpha=255)
            lines = []
            for event in events:
                kind = event.get('type')
                who = translate('online-me') if event.get('outgoing') else event.get('name', '?')
                if kind in ('chat', 'invite'):
                    dest = next((p['name'] for p in players if p['id'] == event.get('to')), '?')
                    prefix = (who + ' -> ' + dest) if event.get('outgoing') else who
                    lines.append(prefix + ': ' + event.get('text', ''))
                elif kind == 'reply':
                    lines.append(translate('online-invitation-accepted' if event.get('answer') == 'accept'
                                           else 'online-invitation-refused').format(name=who))
                elif kind == 'joined':
                    lines.append(translate('online-player-joined').format(name=event.get('name', '?')))
                elif kind == 'error':
                    lines.append(event.get('message', translate('online-send-error')))
            # Le journal contient seulement les messages envoyes/reçus par cette borne.
            font = display.get_font(int(h * .033))
            wrapped = []
            for line in lines:
                words, current = line.split(), ''
                for word in words:
                    candidate = (current+' '+word).strip()
                    if current and font.size(candidate)[0] > w*.58:
                        wrapped.append(current)
                        current = word
                    else:
                        current = candidate
                if current:
                    wrapped.append(current)
            for row, line in enumerate(wrapped[-10:]):
                draw_line(display, line, pygame.Rect(int(w*.37), int(h*(.20+row*.051)), int(w*.58), int(h*.047)),
                          colors['menu-text'], size=h*.033)
            if invitation:
                note = translate('online-invitation-received').format(
                    name=invitation.get('name', '?'), accept=buttons.get('accept', ('',))[0] or '',
                    refuse=buttons.get('refuse', ('',))[0] or '')
            draw_line(display, note, pygame.Rect(int(w*.03), int(h*.745), int(w*.94), int(h*.05)), colors['menu-text-white'])
            for i, name in enumerate(order):
                rect = pygame.Rect(int(w*(.03+(i%3)*.32)), int(h*(.805+(i//3)*.08)), int(w*.30), int(h*.068))
                zones[name] = rect
                draw_button(display, rect, buttons[name], 'online_chat',
                            colors['menu-selected'] if i == action_index and focus in (name, 'player') else colors['menu-buttons'])
            draw_line(display, translate('online-chat-keys'), pygame.Rect(int(w*.03), int(h*.955), int(w*.94), int(h*.04)),
                      colors['menu-text-white'])
            display.update_screen()
            key = display.rpi.listen_inputs(['arrows', 'fx', 'alpha'],
                                           ['enter', 'escape', 'space', 'single-click'], timeout=150)
            clicked = display.is_clicked(zones, key)
            if clicked:
                key = clicked
            elif key in keys:
                key = keys[key]
            if key == display.REVEAL_KEY:
                # As in the menus : the shortcuts shown, even when the theme hides them
                display.reveal_shortcuts()
                continue
            if key == 'logout':
                from include.caccount import logout
                logout(display)
                return
            if key in ESCAPE_KEYS or key == 'back':
                return
            if isinstance(key, str) and key.startswith('player|'):
                selected = key.split('|', 1)[1]
                focus = 'player'
                continue
            if key in UP_KEYS + DOWN_KEYS + LEFT_KEYS + RIGHT_KEYS:
                index = ids.index(selected) if selected in ids else None
                step = -1 if key in UP_KEYS else 1
                if focus == 'player' and key in UP_KEYS + DOWN_KEYS and index is not None and 0 <= index + step < len(ids)                         and 'player|' + ids[index + step] not in zones:
                    # The list scrolled : the player above or under the 8 shown
                    selected = ids[index + step]
                    continue
                # The closest one in the direction, as drawn (the players, Déconnexion, the two
                # rows of buttons : they were gone through in a line) ; right and left (the wheel
                # of a knob) : in the order of reading
                current = 'player|' + selected if focus == 'player' and selected else focus
                moved = display.spatial_step(list(zones.items()), current, key)
                if moved.startswith('player|'):
                    selected, focus = moved.split('|', 1)[1], 'player'
                else:
                    focus = moved
                    if moved in order:
                        action_index = order.index(moved)
                continue
            if key in ENTER_KEYS:
                if focus == 'logout':
                    from include.caccount import logout
                    logout(display)
                    return
                # On the list : the button chosen last (as Entrée did with the arrows on the list)
                key = order[action_index]
            if key == 'back':
                # Retour chosen, then validated
                return
            if key in ('write', 'invite', 'quick'):
                if not selected:
                    note = translate('online-no-player-selected')
                    continue
                recipient = next((p['name'] for p in players if p['id'] == selected), '?')
                content = translate('online-invitation-text')
                if key == 'write':
                    content = compose_message(display, recipient)
                elif key == 'quick':
                    content = choose_quick_reply(display, client, selected, recipient)
                if content is None:
                    continue
                ok = client.command({'type': 'invite' if key == 'invite' else 'chat',
                                     'to': selected, 'text': content})
                note = translate('online-sending' if ok else 'online-chat-disconnected')
            elif key in ('accept', 'refuse'):
                if not invitation:
                    note = translate('online-no-invitation')
                    continue
                ok = client.command({'type': 'reply', 'invitation': invitation['invitation'],
                                     'answer': 'accept' if key == 'accept' else 'refuse'})
                if ok:
                    resolved.add(invitation['invitation'])
                    note = translate('online-you-accepted' if key == 'accept' else 'online-you-refused')
                else:
                    note = translate('online-chat-disconnected')
    finally:
        display._lobby_chat_open = False
        display._lobby_chat_unread = 0


def set_game_activity(display, playing=False, room='', game='', server='', players=()):
    """Appelé par le match ; aucune requête réseau sur le thread du jeu."""
    data = {'playing':bool(playing),'room':str(room),'game':str(game),
            'server':str(server),'players':list(players)[:26]}
    display._lobby_game_activity = data
    client = getattr(display, '_lobby_chat_client', None)
    if client is None and playing:
        client = ensure_session(display, prompt=False)
    if client is not None:
        client.set_activity(data)
