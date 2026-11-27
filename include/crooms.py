"""Combine les salles rejoignables du Master et les parties actives du VPS."""
import json
import urllib.request

from include import caccount


def count(value):
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return 0


def capacity(room):
    value = count(room.get('MAXPLAYERS'))
    return value if 2 <= value <= 12 else 2


def joinable(room):
    return (not room.get('LOBBY_LIVE') and 0 < count(room.get('PLAYERS')) < capacity(room)
            and str(room.get('STATUS', 'OPEN')).upper() in ('', 'OPEN', '1')
            and not room.get('CHTIENCOURS') and bool(room.get('GAMENAME')))


def active_rooms(host):
    request = urllib.request.Request(caccount.BASE + '/joueurs-salles', headers={'Accept':'application/json'})
    with urllib.request.urlopen(request, timeout=2) as response:
        raw = response.read(262145)
    if len(raw)>262144:
        raise ValueError('Liste de salles trop volumineuse')
    data = json.loads(raw.decode('utf-8'))
    if not isinstance(data,dict) or not isinstance(data.get('rooms'),list):
        raise ValueError('Reponse des salles invalide')
    return data['rooms']


def merge_rooms(waiting, active, host, previous=()):
    # Les identifiants de salle sont propres au serveur de jeu.
    rows = {}
    for room in waiting:
        if not isinstance(room,dict) or not room.get('GAMENAME'):
            continue
        row = dict(room);row['LOBBY_LIVE'] = False
        rows[str(row['GAMENAME'])] = row
    for room in active:
        if not isinstance(room,dict) or room.get('state')!='En cours':
            continue
        server = str(room.get('server',''))
        if server.rsplit(':',1)[0].casefold()!=host.casefold():
            continue
        name=room.get('name')
        if not isinstance(name,str) or not name:
            continue
        names=room.get('players',[])
        if not isinstance(names,list):names=[]
        row={'GAMENAME':name,'GAMETYPE':str(room.get('game','?')),
             'GAMECREATOR':'','PLAYERS':count(room.get('count')),
             'LOBBY_LIVE':True,'LOBBY_NAMES':[str(x) for x in names[:26]]}
        rows[name]=row  # La partie qui demarre remplace sa ligne en attente.
    order=[str(r.get('GAMENAME')) for r in previous if isinstance(r,dict)]
    ordered=[]
    for key in order+list(rows):
        if key in rows:ordered.append(rows.pop(key))
    return ordered[:12]


def label(room, index, translate):
    game=str(room.get('GAMETYPE','?')).replace('_',' ')[:16]
    if room.get('LOBBY_LIVE'):
        import re
        names=[re.sub(r'^\d+\s*·\s*','',n) for n in room.get('LOBBY_NAMES',[])]
        versus=' VS '.join(names) if names else str(room.get('GAMENAME',''))
        return '{:02d}  {} | {} | {}'.format(index+1,game,versus,translate('online-room-playing'))
    creator=str(room.get('GAMECREATOR','?'))[:22]
    status=translate('online-room-join' if joinable(room) else 'online-room-full')
    return '{:02d}  {} | {} | {}/{} | {}'.format(index+1,game,creator,count(room.get('PLAYERS')),capacity(room),status)


def color(room, selected=False):
    """
    Colour of the theme of the line of a room : joinable (menu-ok), being played or full (menu-ko)
    """
    if selected:
        return 'menu-selected'
    return 'menu-ok' if joinable(room) else 'menu-ko'
