"""Instantane du match : copie legere, transport sur le thread du chat."""
import math



def _cricket_snapshot(game, players):
    """Lit les colonnes reelles du jeu, sans recalculer le score du Cricket."""
    name = str(getattr(game, 'logo', '')) + ' ' + type(game).__module__
    if 'cricket' not in name.lower():
        return None
    targets = getattr(game, 'headers', ())
    if not isinstance(targets, (list, tuple)) or len(targets) != 7:
        return None
    targets = [str(value) for value in targets]
    if any(value != 'B' and value not in [str(i) for i in range(1,21)] for value in targets):
        return None
    marks = []
    try:
        for player in players[:26]:
            columns = player.columns
            if len(columns) < 7:
                return None
            marks.append([max(0,min(3,int(columns[i][0]))) for i in range(7)])
    except (TypeError, ValueError, AttributeError, IndexError, OverflowError):
        return None
    return {'targets': targets, 'marks': marks,
            'cutthroat': bool(getattr(game, 'cutthroat', False)),
            'crazy': bool(getattr(game, 'crazy', False))}

def publish(display, context):
    # La borne qui cree la partie est la source commune aux deux joueurs.
    if context.get('net_status') != 'YOUAREMASTER':
        return
    if context.get('game_type') not in ('netcreate', 'netjoin'):
        return
    client = getattr(display, '_lobby_chat_client', None)
    game = context.get('game')
    players = context.get('players', ())
    if client is None or game is None or not players:
        return
    roster = []
    for player in players[:26]:
        score = getattr(player, 'score', None)
        if isinstance(score, (int, float)) and not isinstance(score, bool) and math.isfinite(score):
            score = str(round(score, 2))[:16]
        else:
            score = None
        roster.append({'name': str(player.name)[:40], 'score': score})
    data = {'type': 'match_live', 'room': str(context.get('netgamename', ''))[:80],
            'server': '{}:{}'.format(context.get('servername', ''), context.get('serverport', ''))[:160],
            'round': int(context.get('actual_round', 1)),
            'max_round': int(getattr(game, 'max_round', 0) or 0),
            'active': int(context.get('actual_player', 0)),
            'set': int(context.get('Set', 1)), 'max_sets': int(context.get('nb_sets', 1)),
            'players': roster}
    # CHTI MINI DMD V1 : les flechettes du tour du joueur actif.
    active = data['active']
    darts = getattr(players[active], 'darts', []) if 0 <= active < len(players) else []
    if not isinstance(darts, (list, tuple)):
        darts = []
    data['darts'] = [str(hit)[:8] if hit is not None else '' for hit in darts[:3]]
    data['darts'] += [''] * (3-len(data['darts']))
    # CHTI CRICKET LIVE V1
    cricket = _cricket_snapshot(game, players)
    if cricket is not None:
        data['cricket'] = cricket
    with client.lock:
        activity = client.game_activity
        names = [row['name'] for row in roster]
        if activity.get('playing') and activity.get('players') != names:
            client.game_activity = dict(activity, players=names)
            client.activity_version += 1
        client.match_live = data
