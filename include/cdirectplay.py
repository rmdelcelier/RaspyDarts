"""
Direct launch of a game, without the menus : by the command line (raspydarts.py --jeu Cricket
--joueurs Rémi,Dimitri, RaspyDarts.sh passes its arguments on its first start), or at each start
of RaspyDarts (Personnalisation du jeu : Lancement direct, its game or favorite, with the
players of Joueurs favoris).

What is launched :
- a game : its options as saved for it (the options kept of a game : its own settings), else
  those of the game ; some changed by --option clé=valeur ;
- a numbered favorite (fav1... : a button of the main menu) : as its button does it (its game,
  its options, its players or the way they are chosen) ;
- a favorite of the list Favoris (its number in the list, or its game) : its game and its options.
Without players : the screen of the players first, then the game.
"""

import argparse
import os
import sys

from include import cfavorites
from include import cmenus
from include import cpaths

# Value of the setting direct_play_game : a game, a numbered favorite, a favorite of the list
GAME, FAVORITE, LISTED = 'game:', 'fav:', 'list:'


class Quiet:
    '''
    Logs of the command line before the game starts : warnings only, printed
    '''
    def __getattr__(self, name):
        if name in ('warning', 'error'):
            return lambda text, *args, **kwargs: print(text, file=sys.stderr)
        return lambda *args, **kwargs: None


def games():
    '''
    The games installed : [(category, file name)] (Cricket, Chti_501...)
    '''
    found = []
    games_dir = os.path.join(cpaths.ROOT_DIR, 'games')
    for category in sorted(os.listdir(games_dir)) if os.path.isdir(games_dir) else []:
        folder = os.path.join(games_dir, category)
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if name.endswith('.py') and not name.startswith('_'):
                found.append((category, name[:-3]))
    return found


def find_game(text):
    '''
    The file name of a game given as typed (Cricket, cricket, "Chti 501") ; None if unknown
    '''
    wanted = str(text or '').strip().replace(' ', '_').lower()
    for _category, name in games():
        if name.lower() == wanted:
            return name
    return None


def listed_favorite(favorites, text):
    '''
    A favorite of the list Favoris : its number in the list (1, 2...) or its game ; its entry
    {'game', 'options'}, None
    '''
    entries = favorites.unnumbered()
    text = str(text or '').strip()
    if text.isdigit():
        index = int(text) - 1
        return entries[index] if 0 <= index < len(entries) else None
    game = find_game(text)
    return next((entry for entry in entries if game and str(entry.get('game')) == game), None)


def parse(argv):
    '''
    The arguments of the command line : the request ({'game'...} or {'favorite'...}), None
    without one. --liste and --aide : printed, then the end
    '''
    parser = argparse.ArgumentParser(
        prog='raspydarts.py', add_help=False, description="RaspyDarts : lancer directement un jeu ou un favori, sans passer par les menus.",
        epilog="Exemples : raspydarts.py --jeu Cricket --joueurs Rémi,Dimitri  |  raspydarts.py --favori fav1  |  "
               "raspydarts.py --jeu Ho_One --option cle=valeur  |  raspydarts.py --liste")
    parser.add_argument('-h', '--aide', '--help', action='help', help="cette aide, puis rien d'autre")
    parser.add_argument('--jeu', '--game', dest='game', help="le jeu (son nom dans --liste : Cricket, Ho_One...)")
    parser.add_argument('--favori', '--favorite', dest='favorite',
                        help="un favori : fav1 à fav9 (boutons du menu principal), ou son numéro / son jeu dans la liste Favoris")
    parser.add_argument('--joueurs', '--players', dest='players',
                        help="les joueurs, séparés par des virgules (sans : l'écran des joueurs)")
    parser.add_argument('--option', '-o', dest='options', action='append', default=[], metavar='CLE=VALEUR',
                        help="une option du jeu (plusieurs possibles)")
    parser.add_argument('--liste', '--list', dest='list', action='store_true', help="les jeux et les favoris, puis rien d'autre")
    args, unknown = parser.parse_known_args(argv)
    if unknown:
        print(f"Arguments ignorés : {' '.join(unknown)}", file=sys.stderr)
    if args.list:
        print_list()
        sys.exit(0)
    if not args.game and not args.favorite:
        return None
    request = {'players': [name.strip() for name in str(args.players or '').split(',') if name.strip()] or None,
               'options': {}}
    for option in args.options:
        key, _sep, value = str(option).partition('=')
        if key.strip():
            request['options'][key.strip()] = value.strip()
    if args.favorite:
        request['favorite'] = str(args.favorite).strip()
    else:
        request['game'] = str(args.game).strip()
    return request


def print_list():
    '''
    --liste : the games by category, the favorites
    '''
    by_category = {}
    for category, name in games():
        by_category.setdefault(category, []).append(name)
    for category, names in by_category.items():
        print(f"{category} : {', '.join(names)}")
    favorites = cfavorites.Favorites(Quiet())
    numbered = favorites.numbered()
    if numbered:
        print("Favoris du menu principal : " + ', '.join(f"{name} ({favorite['game']})" for name, favorite in numbered))
    entries = favorites.unnumbered()
    if entries:
        print("Liste Favoris : " + ', '.join(f"{index} ({entry.get('game')})" for index, entry in enumerate(entries, 1)))


def from_setting(value, players):
    '''
    The request of the setting Lancement direct (game:Cricket, fav:fav1, list:2), the players
    of Joueurs favoris ; None if nothing chosen
    '''
    value = str(value or '')
    request = {'players': players or None, 'options': {}}
    if value.startswith(GAME) and value[len(GAME):]:
        request['game'] = value[len(GAME):]
    elif value.startswith(FAVORITE) and value[len(FAVORITE):]:
        request['favorite'] = value[len(FAVORITE):]
    elif value.startswith(LISTED) and value[len(LISTED):]:
        request['favorite'] = value[len(LISTED):]
    else:
        return None
    return request


def choices(translate, favorites):
    '''
    The values of the setting Lancement direct : the numbered favorites, those of the list
    Favoris, then every game
    '''
    values = [('', translate('direct-play-none'))]
    for name, favorite in favorites.numbered():
        values.append((f'{FAVORITE}{name}', f"{translate('direct-play-favorite')} {name[3:]} : {favorite['game'].replace('_', ' ')}"))
    for index, entry in enumerate(favorites.unnumbered(), 1):
        values.append((f'{LISTED}{index}', f"{translate('direct-play-listed')} {index} : {str(entry.get('game')).replace('_', ' ')}"))
    values += [(f'{GAME}{name}', name.replace('_', ' ')) for _category, name in games()]
    return values


def resolve(request, favorites, saved_options):
    '''
    What a request launches :
    - ('favorite', 'fav1') : a numbered favorite, launched as its button ;
    - ('game', launch, players) : launch {'game', 'category', 'options', 'direct'} ;
    - ('error', text) : nothing (a game or a favorite unknown)
    saved_options(game) : the options saved for a game (its section game-<game>), {} if none
    '''
    favorite = request.get('favorite')
    options = {}
    if favorite:
        if favorite.lower().startswith('fav') and favorite[3:].isdigit():
            return ('favorite', favorite.lower())
        entry = listed_favorite(favorites, favorite)
        if entry is None:
            return ('error', f"favori inconnu : {favorite}")
        game = str(entry.get('game'))
        options = dict(entry.get('options') or {})
    else:
        game = find_game(request.get('game'))
        if game is None:
            return ('error', f"jeu inconnu : {request.get('game')}")
    category = cmenus.game_category(game)
    if category is None:
        return ('error', f"jeu inconnu : {game}")
    if not options:
        options = dict(saved_options(game) or {})
    options.update(request.get('options') or {})
    return ('game', {'game': game, 'category': category, 'options': options, 'direct': True}, request.get('players'))
