"""
Spectators of an online game : a light copy of the match, sent by the thread of the chat
(include/cchat.py), nothing on the network from the thread of the game
"""
import math

# Columns of a Cricket, players sent at most
CRICKET_COLUMNS = 7
MOST_PLAYERS = 26


def cricket_snapshot(game, players):
    '''
    The real columns of a Cricket (its score is not computed again), None for another game
    '''
    name = f'{getattr(game, "logo", "")} {type(game).__module__}'
    if 'cricket' not in name.lower():
        return None
    targets = getattr(game, 'headers', ())
    if not isinstance(targets, (list, tuple)) or len(targets) != CRICKET_COLUMNS:
        return None
    targets = [str(value) for value in targets]
    if any(value != 'B' and value not in [str(number) for number in range(1, 21)] for value in targets):
        return None
    try:
        # Before the first dart, a column can still be empty
        marks = [[max(0, min(3, int(player.columns[column][0] or 0))) for column in range(CRICKET_COLUMNS)]
                 for player in players[:MOST_PLAYERS]]
    except (TypeError, ValueError, AttributeError, IndexError, OverflowError):
        return None
    return {'targets': targets, 'marks': marks,
            'cutthroat': bool(getattr(game, 'cutthroat', False)),
            'crazy': bool(getattr(game, 'crazy', False))}


def publish(display, game, players, room, server, actual_round, actual_player, set_number, nb_sets):
    '''
    The state of the match given to the client of the chat, which sends it when it can. The
    borne which created the game is the source for all the players
    '''
    client = getattr(display, '_lobby_chat_client', None)
    if client is None or game is None or not players:
        return
    roster = []
    for player in players[:MOST_PLAYERS]:
        score = getattr(player, 'score', None)
        if isinstance(score, (int, float)) and not isinstance(score, bool) and math.isfinite(score):
            score = str(round(score, 2))[:16]
        else:
            score = None
        roster.append({'name': str(player.name)[:40], 'score': score})
    data = {'type': 'match_live', 'room': str(room)[:80], 'server': str(server)[:160],
            'round': int(actual_round), 'max_round': int(getattr(game, 'max_round', 0) or 0),
            'active': int(actual_player), 'set': int(set_number), 'max_sets': int(nb_sets),
            'players': roster}
    # The darts of the turn of the active player
    darts = getattr(players[actual_player], 'darts', []) if 0 <= actual_player < len(players) else []
    if not isinstance(darts, (list, tuple)):
        darts = []
    data['darts'] = [str(hit)[:8] if hit is not None else '' for hit in darts[:3]]
    data['darts'] += [''] * (3 - len(data['darts']))
    cricket = cricket_snapshot(game, players)
    if cricket is not None:
        data['cricket'] = cricket
    with client.lock:
        activity = client.game_activity
        names = [row['name'] for row in roster]
        if activity.get('playing') and activity.get('players') != names:
            client.game_activity = dict(activity, players=names)
            client.activity_version += 1
        client.match_live = data
