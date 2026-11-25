import pygame
import os
import json
import re
from include import craspberry

# --- MAPPING DES TOUCHES MATÉRIELLES / CLAVIER ---
ENTER_KEYS = ['enter', 'return', 'space', 'GAMEBUTTON', 'BTN_VALIDATE', 'VALIDATE', 'BTN_GAMEBUTTON', 'SB', 'DB', 'BTN_NEXTPLAYER']
ESCAPE_KEYS = ['escape', 'BTN_BACK', 'BACK', 'CANCEL', 'BTN_CANCEL']
# Right and left go through the lists too (a knob set on them)
UP_KEYS = ['up', 'BTN_UP', 'S20']
DOWN_KEYS = ['down', 'BTN_DOWN', 'S3']
LEFT_KEYS = ['left', 'BTN_LEFT', 'S11']
RIGHT_KEYS = ['right', 'BTN_RIGHT', 'S6']
DELETE_KEYS = ['delete', 'BTN_MINUS', 'VOLUME-DOWN', 'BTN_VOLUME_DOWN', 's', 'S']
INSERT_KEYS = ['insert', 'BTN_PLUS', 'VOLUME-UP', 'BTN_VOLUME_UP', 'm', 'M']

# Fichiers
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Dans le dossier du joueur (~/.raspydarts), avec ses scores et sa configuration
from include import cfonts
from include import cpaths
from include.ctrophies import average_ppd
DATA_FILE = cpaths.trophies_file()


# --- TRADUCTION : le texte français sert de clé (Lang.translate le rend tel quel sans traduction) ---
_translate = None


def set_translator(translate):
    global _translate
    _translate = translate


def tr(text, *values, **named):
    '''
    Un texte des écrans dans la langue de la borne (le français sans traduction), ses valeurs
    mises à leur place ({0}, {player}...)
    '''
    translated = text
    if _translate is not None:
        try:
            translated = _translate(text) or text
        except Exception:    # pylint: disable=broad-except
            translated = text
    if not values and not named:
        return translated
    try:
        return translated.format(*values, **named)
    except (KeyError, IndexError, ValueError):
        return text.format(*values, **named)


# Descriptions et noms des trophées faits sur le même modèle : traduits par leur modèle
TROPHY_PATTERNS = [
    (r'Toucher 3x (\S+) en une volée', 'Toucher 3x {0} en une volée'),
    (r'Terminer en finissant par (\S+)', 'Terminer en finissant par {0}'),
    (r'Terminer le (\d+) en (\d+) fléchettes', 'Terminer le {0} en {1} fléchettes'),
    (r'Terminer le (\d+) en (\d+) fléchettes \(Perfect\)', 'Terminer le {0} en {1} fléchettes (Perfect)'),
    (r'Valider le défi (\d+) de Routine', 'Valider le défi {0} de Routine'),
    (r'Réaliser (\d+) marques au (Cricket|Mickey)', 'Réaliser {0} marques au {1}'),
    (r'Marquer (\d+) points', 'Marquer {0} points'),
    (r'Score total entre (\d+) et (\d+) points', 'Score total entre {0} et {1} points'),
    (r'Lancer (\d+) fléchettes', 'Lancer {0} fléchettes'),
    (r'Gagner (\d+) parties', 'Gagner {0} parties'),
    (r'Toucher le simple bull (\d+) fois', 'Toucher le simple bull {0} fois'),
    (r'Toucher le double bull (\d+) fois', 'Toucher le double bull {0} fois'),
    (r'Toucher le bull (\d+) fois', 'Toucher le bull {0} fois'),
    (r'Atteindre le bull (\d+) fois', 'Atteindre le bull {0} fois'),
    (r'Toucher un double (\d+) fois', 'Toucher un double {0} fois'),
    (r'Toucher un triple (\d+) fois', 'Toucher un triple {0} fois'),
    (r'Toucher (\w+), (\w+), (\w+)', 'Toucher {0}, {1}, {2}'),
    (r'Toucher (\w+), (\w+), (\w+) \(Tous ordres?\)', 'Toucher {0}, {1}, {2} (dans n\'importe quel ordre)'),
    (r'Ho-One - Finir par (\S+)', 'Ho-One - Finir par {0}'),
    (r'(\d+) - (\d+) fléchettes', '{0} - {1} fléchettes'),
    (r'Routine - Niveau (\d+)', 'Routine - Niveau {0}'),
    (r'Fl[éè]ches Lancées \((\w+)\)', 'Flèches lancées ({0})'),
]


def trophy_text(text):
    '''
    Le nom ou la description d'un trophée dans la langue de la borne : sa traduction, sinon celle
    de son modèle, sinon le français
    '''
    translated = tr(text)
    if translated != text:
        return translated
    for pattern, model in TROPHY_PATTERNS:
        found = re.fullmatch(pattern, str(text))
        if found:
            return tr(model, *found.groups())
    return text


def level_text(name):
    '''
    Un niveau (Régulier III) dans la langue de la borne : son nom traduit, son numéro gardé
    '''
    found = re.fullmatch(r'(.+?) ([IVX]+)', str(name))
    if found:
        return f"{tr(found.group(1))} {found.group(2)}"
    return tr(name)


# --- SOURIS ET TACTILE : ce que les écrans partagent ---
def ui_scale(screen):
    '''
    Taille des éléments : 1 pour un écran de 1280 x 720 (le plus petit côté compte)
    '''
    width, height = screen.get_size()
    return min(width / 1280.0, height / 720.0)


def click_of(inp):
    '''
    Un clic ou un toucher lu par listen_inputs : sa position (x, y) ; None sinon
    '''
    if isinstance(inp, tuple) and len(inp) == 2 and all(isinstance(value, (int, float)) for value in inp):
        return (int(inp[0]), int(inp[1]))
    return None


def draw_button(surface, rect, text, font, chosen=False):
    '''
    Un bouton cliquable (Retour, pages, défilement...) : son rectangle
    '''
    rect = pygame.Rect(rect)
    radius = max(4, rect.height // 4)
    pygame.draw.rect(surface, (55, 70, 105) if chosen else (40, 48, 66), rect, border_radius=radius)
    pygame.draw.rect(surface, (100, 150, 255) if chosen else (90, 105, 135), rect, 2, border_radius=radius)
    label = font.render(text, True, (255, 255, 255))
    if label.get_width() > rect.width - 8:
        label = pygame.transform.smoothscale(label, (max(1, rect.width - 8), label.get_height()))
    surface.blit(label, label.get_rect(center=rect.center))
    return rect


def wrap_text(font, text, width, most=2):
    '''
    Un texte coupé entre les mots en lignes de cette largeur (most lignes au plus, la dernière
    terminée par … si le texte est plus long)
    '''
    words, lines, line = str(text).split(), [], ''
    for word in words:
        attempt = f"{line} {word}".strip()
        if font.size(attempt)[0] <= width or not line:
            line = attempt
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    if len(lines) > most:
        lines = lines[:most]
        lines[-1] = lines[-1].rstrip('.,;') + '…'
    return lines

ALL_TROPHIES = [
    # --- 1. Combinaisons et figures de fléchettes ---
    {"id": "BAIL_OUT", "name": "Bail Out", "desc": "La 3ème fléchette est un gros triple", "img": "bail out", "category": "Combinaisons et figures"},
    {"id": "BLACK_HAT_THREE_IN_THE_BLACK", "name": "Black Hat", "desc": "Toucher 3 Double Bull", "img": "black hat", "category": "Combinaisons et figures"},
    {"id": "BREAKFAST", "name": "Breakfast", "desc": "Toucher S1, S5, S20 (Tous ordre)", "img": "breakfast", "category": "Combinaisons et figures"},
    {"id": "BUCKET_OF_NAILS", "name": "Bucket of Nails", "desc": "Toucher S1, S1, S1", "img": "bucket of nail", "category": "Combinaisons et figures"},
    {"id": "CHAMPAGNE_BREAKFAST", "name": "Champagne Breakfast", "desc": "Toucher T1, T5, T20 (Tous ordres)", "img": "champagne breakfast", "category": "Combinaisons et figures"},
    {"id": "DEVIL", "name": "Devil", "desc": "Toucher S6, S6, S6", "img": "devil", "category": "Combinaisons et figures"},
    {"id": "HAT_TRICK", "name": "Hat Trick", "desc": "Toucher n'importe quel Bull 3x", "img": "hat trick", "category": "Combinaisons et figures"},
    {"id": "LIPSTICK", "name": "Lipstick", "desc": "Toucher un T20 dans la volée", "img": "lipstick", "category": "Combinaisons et figures"},
    {"id": "MAXIMUM_TON_80", "name": "Maximum Ton 80", "desc": "Toucher T20, T20, T20", "img": "maximum ton", "category": "Combinaisons et figures"},
    {"id": "NOT_OLD", "name": "Not Old", "desc": "Toucher S5, S12, S20 (Tous ordres)", "img": "not old", "category": "Combinaisons et figures"},
    {"id": "RED_HAT", "name": "Red Hat", "desc": "Toucher 3 simple bull", "img": "red hat", "category": "Combinaisons et figures"},
    {"id": "ROUND_OF_TERMS", "name": "Round of Terms", "desc": "Toucher n'importe quel Triple 3x", "img": "round of term", "category": "Combinaisons et figures"},
    {"id": "THREE_IN_A_BED", "name": "Three in a Bed", "desc": "3 fois le même chiffre", "img": "three on the bed", "category": "Combinaisons et figures"},
    {"id": "TRIPLE_DEVIL", "name": "Triple Devil", "desc": "Toucher T6, T6, T6", "img": "devil_triple", "category": "Combinaisons et figures"},
    {"id": "WHITE_HORSE", "name": "White Horse", "desc": "Toucher 3 Triples différents au Cricket ou à Mickey", "img": "white horse", "category": "Combinaisons et figures"},
    {"id": "MISS", "name": "3 Miss", "desc": "Rater ses 3 flèches (3 Miss)", "img": "miss", "category": "Combinaisons et figures"},

    # --- 2. Scores spécifiques de volée / Tons ---
    {"id": "2_FAT_LADIES", "name": "2 Fat Ladies", "desc": "Marquer 88 points", "img": "2fat ladies", "category": "Scores spécifiques"},
    {"id": "BABY_TON", "name": "Baby Ton", "desc": "Marquer 95 points", "img": "baby_ton", "category": "Scores spécifiques"},
    {"id": "BAG_O_NUTS", "name": "Bag O Nuts", "desc": "Marquer 45 points", "img": "bag o nuts", "category": "Scores spécifiques"},
    {"id": "FEATHERS", "name": "Feathers", "desc": "Marquer 33 points", "img": "FEATHERS", "category": "Scores spécifiques"},
    {"id": "HAPPY_MEAL", "name": "Happy Meal", "desc": "Marquer 69 points", "img": "happy meal", "category": "Scores spécifiques"},
    {"id": "HIGH_TON", "name": "High Ton", "desc": "Score total entre 151 et 179 points", "img": "high ton", "category": "Scores spécifiques"},
    {"id": "LOW_TON", "name": "Low Ton", "desc": "Score total entre 101 et 149 points", "img": "low ton", "category": "Scores spécifiques"},
    {"id": "ROUTE_66", "name": "Route 66", "desc": "Marquer 66 points", "img": "route 66", "category": "Scores spécifiques"},
    {"id": "SUNSET_STRIP", "name": "Sunset Strip", "desc": "Marquer 77 points", "img": "sunset strip", "category": "Scores spécifiques"},
    {"id": "SWAN_LAKE", "name": "Swan Lake", "desc": "Marquer 22 points", "img": "swan lake", "category": "Scores spécifiques"},
    {"id": "TON", "name": "Ton", "desc": "Marquer 100 points", "img": "TON", "category": "Scores spécifiques"},
    {"id": "TON_10", "name": "Ton 10", "desc": "Marquer 110 points", "img": "TON10", "category": "Scores spécifiques"},
    {"id": "TON_20", "name": "Ton 20", "desc": "Marquer 120 points", "img": "TON20", "category": "Scores spécifiques"},
    {"id": "TON_30", "name": "Ton 30", "desc": "Marquer 130 points", "img": "TON30", "category": "Scores spécifiques"},
    {"id": "TON_40", "name": "Ton 40", "desc": "Marquer 140 points", "img": "ton40", "category": "Scores spécifiques"},
    {"id": "TON_50", "name": "Ton 50", "desc": "Marquer 150 points", "img": "ton50", "category": "Scores spécifiques"},
    {"id": "TON_60", "name": "Ton 60", "desc": "Marquer 160 points", "img": "ton60", "category": "Scores spécifiques"},
    {"id": "TON_70", "name": "Ton 70", "desc": "Marquer 170 points", "img": "ton70", "category": "Scores spécifiques"},
    {"id": "TON_80", "name": "Ton 80", "desc": "Réaliser un 180 aux fléchettes", "img": "ton80", "category": "Scores spécifiques"},

    # --- 3. Doubles ---
    {"id": "DOUBLE_3X_D1", "name": "Double - 3x D1", "desc": "Toucher 3x D1 en une volée", "img": "double - 3xd1", "category": "Doubles"},
    {"id": "DOUBLE_3X_D2", "name": "Double - 3x D2", "desc": "Toucher 3x D2 en une volée", "img": "double - 3xd2", "category": "Doubles"},
    {"id": "DOUBLE_3X_D3", "name": "Double - 3x D3", "desc": "Toucher 3x D3 en une volée", "img": "double - 3xd3", "category": "Doubles"},
    {"id": "DOUBLE_3X_D4", "name": "Double - 3x D4", "desc": "Toucher 3x D4 en une volée", "img": "double - 3xd4", "category": "Doubles"},
    {"id": "DOUBLE_3X_D5", "name": "Double - 3x D5", "desc": "Toucher 3x D5 en une volée", "img": "double - 3xd5", "category": "Doubles"},
    {"id": "DOUBLE_3X_D6", "name": "Double - 3x D6", "desc": "Toucher 3x D6 en une volée", "img": "double - 3xd6", "category": "Doubles"},
    {"id": "DOUBLE_3X_D7", "name": "Double - 3x D7", "desc": "Toucher 3x D7 en une volée", "img": "double - 3xd7", "category": "Doubles"},
    {"id": "DOUBLE_3X_D8", "name": "Double - 3x D8", "desc": "Toucher 3x D8 en une volée", "img": "double - 3xd8", "category": "Doubles"},
    {"id": "DOUBLE_3X_D9", "name": "Double - 3x D9", "desc": "Toucher 3x D9 en une volée", "img": "double - 3xd9", "category": "Doubles"},
    {"id": "DOUBLE_3X_D10", "name": "Double - 3x D10", "desc": "Toucher 3x D10 en une volée", "img": "double - 3xd10", "category": "Doubles"},
    {"id": "DOUBLE_3X_D11", "name": "Double - 3x D11", "desc": "Toucher 3x D11 en une volée", "img": "double - 3xd11", "category": "Doubles"},
    {"id": "DOUBLE_3X_D12", "name": "Double - 3x D12", "desc": "Toucher 3x D12 en une volée", "img": "double - 3xd12", "category": "Doubles"},
    {"id": "DOUBLE_3X_D13", "name": "Double - 3x D13", "desc": "Toucher 3x D13 en une volée", "img": "double - 3xd13", "category": "Doubles"},
    {"id": "DOUBLE_3X_D14", "name": "Double - 3x D14", "desc": "Toucher 3x D14 en une volée", "img": "double - 3xd14", "category": "Doubles"},
    {"id": "DOUBLE_3X_D15", "name": "Double - 3x D15", "desc": "Toucher 3x D15 en une volée", "img": "double - 3xd15", "category": "Doubles"},
    {"id": "DOUBLE_3X_D16", "name": "Double - 3x D16", "desc": "Toucher 3x D16 en une volée", "img": "double - 3xd16", "category": "Doubles"},
    {"id": "DOUBLE_3X_D17", "name": "Double - 3x D17", "desc": "Toucher 3x D17 en une volée", "img": "double - 3xd17", "category": "Doubles"},
    {"id": "DOUBLE_3X_D18", "name": "Double - 3x D18", "desc": "Toucher 3x D18 en une volée", "img": "double - 3xd18", "category": "Doubles"},
    {"id": "DOUBLE_3X_D19", "name": "Double - 3x D19", "desc": "Toucher 3x D19 en une volée", "img": "double - 3xd19", "category": "Doubles"},
    {"id": "DOUBLE_3X_D20", "name": "Double - 3x D20", "desc": "Toucher 3x D20 en une volée", "img": "double - 3xd20", "category": "Doubles"},

    # --- 4. Triples ---
    {"id": "TRIPLE_3X_T1", "name": "Triple - 3x T1", "desc": "Toucher 3x T1 en une volée", "img": "triple - 3xt1", "category": "Triples"},
    {"id": "TRIPLE_3X_T2", "name": "Triple - 3x T2", "desc": "Toucher 3x T2 en une volée", "img": "triple - 3xt2", "category": "Triples"},
    {"id": "TRIPLE_3X_T3", "name": "Triple - 3x T3", "desc": "Toucher 3x T3 en une volée", "img": "triple - 3xt3", "category": "Triples"},
    {"id": "TRIPLE_3X_T4", "name": "Triple - 3x T4", "desc": "Toucher 3x T4 en une volée", "img": "triple - 3xt4", "category": "Triples"},
    {"id": "TRIPLE_3X_T5", "name": "Triple - 3x T5", "desc": "Toucher 3x T5 en une volée", "img": "triple - 3xt5", "category": "Triples"},
    {"id": "TRIPLE_3X_T6", "name": "Triple - 3x T6", "desc": "Toucher 3x T6 en une volée", "img": "triple - 3xt6", "category": "Triples"},
    {"id": "TRIPLE_3X_T7", "name": "Triple - 3x T7", "desc": "Toucher 3x T7 en une volée", "img": "triple - 3xt7", "category": "Triples"},
    {"id": "TRIPLE_3X_T8", "name": "Triple - 3x T8", "desc": "Toucher 3x T8 en une volée", "img": "triple - 3xt8", "category": "Triples"},
    {"id": "TRIPLE_3X_T9", "name": "Triple - 3x T9", "desc": "Toucher 3x T9 en une volée", "img": "triple - 3xt9", "category": "Triples"},
    {"id": "TRIPLE_3X_T10", "name": "Triple - 3x T10", "desc": "Toucher 3x T10 en une volée", "img": "triple - 3xt10", "category": "Triples"},
    {"id": "TRIPLE_3X_T11", "name": "Triple - 3x T11", "desc": "Toucher 3x T11 en une volée", "img": "triple - 3xt11", "category": "Triples"},
    {"id": "TRIPLE_3X_T12", "name": "Triple - 3x T12", "desc": "Toucher 3x T12 en une volée", "img": "triple - 3xt12", "category": "Triples"},
    {"id": "TRIPLE_3X_T13", "name": "Triple - 3x T13", "desc": "Toucher 3x T13 en une volée", "img": "triple - 3xt13", "category": "Triples"},
    {"id": "TRIPLE_3X_T14", "name": "Triple - 3x T14", "desc": "Toucher 3x T14 en une volée", "img": "triple - 3xt14", "category": "Triples"},
    {"id": "TRIPLE_3X_T15", "name": "Triple - 3x T15", "desc": "Toucher 3x T15 en une volée", "img": "triple - 3xt15", "category": "Triples"},
    {"id": "TRIPLE_3X_T16", "name": "Triple - 3x T16", "desc": "Toucher 3x T16 en une volée", "img": "triple - 3xt16", "category": "Triples"},
    {"id": "TRIPLE_3X_T17", "name": "Triple - 3x T17", "desc": "Toucher 3x T17 en une volée", "img": "triple - 3xt17", "category": "Triples"},
    {"id": "TRIPLE_3X_T18", "name": "Triple - 3x T18", "desc": "Toucher 3x T18 en une volée", "img": "triple - 3xt18", "category": "Triples"},
    {"id": "TRIPLE_3X_T19", "name": "Triple - 3x T19", "desc": "Toucher 3x T19 en une volée", "img": "triple - 3xt19", "category": "Triples"},
    {"id": "TRIPLE_3X_T20", "name": "Triple - 3x T20", "desc": "Toucher 3x T20 en une volée", "img": "triple - 3xt20", "category": "Triples"},

    # --- 5. Ho-One ---
    {"id": "HO_ONE_FINIR_PAR_D1", "name": "Ho-One - Finir par D1", "desc": "Terminer en finissant par D1", "img": "ho-one - finish d1", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D2", "name": "Ho-One - Finir par D2", "desc": "Terminer en finissant par D2", "img": "ho-one - finish d2", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D3", "name": "Ho-One - Finir par D3", "desc": "Terminer en finissant par D3", "img": "ho-one - finish d3", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D4", "name": "Ho-One - Finir par D4", "desc": "Terminer en finissant par D4", "img": "ho-one - finish d4", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D5", "name": "Ho-One - Finir par D5", "desc": "Terminer en finissant par D5", "img": "ho-one - finish d5", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D6", "name": "Ho-One - Finir par D6", "desc": "Terminer en finissant par D6", "img": "ho-one - finish d6", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D7", "name": "Ho-One - Finir par D7", "desc": "Terminer en finissant par D7", "img": "ho-one - finish d7", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D8", "name": "Ho-One - Finir par D8", "desc": "Terminer en finissant par D8", "img": "ho-one - finish d8", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D9", "name": "Ho-One - Finir par D9", "desc": "Terminer en finissant par D9", "img": "ho-one - finish d9", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D10", "name": "Ho-One - Finir par D10", "desc": "Terminer en finissant par D10", "img": "ho-one - finish d10", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D11", "name": "Ho-One - Finir par D11", "desc": "Terminer en finissant par D11", "img": "ho-one - finish d11", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D12", "name": "Ho-One - Finir par D12", "desc": "Terminer en finissant par D12", "img": "ho-one - finish d12", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D13", "name": "Ho-One - Finir par D13", "desc": "Terminer en finissant par D13", "img": "ho-one - finish d13", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D14", "name": "Ho-One - Finir par D14", "desc": "Terminer en finissant par D14", "img": "ho-one - finish d14", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D15", "name": "Ho-One - Finir par D15", "desc": "Terminer en finissant par D15", "img": "ho-one - finish d15", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D16", "name": "Ho-One - Finir par D16", "desc": "Terminer en finissant par D16", "img": "ho-one - finish d16", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D17", "name": "Ho-One - Finir par D17", "desc": "Terminer en finissant par D17", "img": "ho-one - finish d17", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D18", "name": "Ho-One - Finir par D18", "desc": "Terminer en finissant par D18", "img": "ho-one - finish d18", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D19", "name": "Ho-One - Finir par D19", "desc": "Terminer en finissant par D19", "img": "ho-one - finish d19", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D20", "name": "Ho-One - Finir par D20", "desc": "Terminer en finissant par D20", "img": "ho-one - finish d20", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_DB", "name": "Ho-One - Finir par DB", "desc": "Terminer en finissant par DB", "img": "ho-one - finish db", "category": "Ho-One"},
    {"id": "HO_ONE_301_6_DARTS", "name": "301 - 6 fléchettes", "desc": "Terminer le 301 en 6 fléchettes", "img": "ho-one - 301 - 6  fleches", "category": "Ho-One"},
    {"id": "HO_ONE_301_7_DARTS", "name": "301 - 7 fléchettes", "desc": "Terminer le 301 en 7 fléchettes", "img": "ho-one - 301 - 7  fleches", "category": "Ho-One"},
    {"id": "HO_ONE_301_8_DARTS", "name": "301 - 8 fléchettes", "desc": "Terminer le 301 en 8 fléchettes", "img": "ho-one - 301 - 8  fleches", "category": "Ho-One"},
    {"id": "HO_ONE_301_9_DARTS", "name": "301 - 9 fléchettes", "desc": "Terminer le 301 en 9 fléchettes", "img": "ho-one - 301 - 9  fleches", "category": "Ho-One"},
    {"id": "HO_ONE_301_12_DARTS", "name": "301 - 12 fléchettes", "desc": "Terminer le 301 en 12 fléchettes", "img": "ho-one - 301 - 12 fleches", "category": "Ho-One"},
    {"id": "HO_ONE_501_9_DARTS", "name": "501 - 9 fléchettes", "desc": "Terminer le 501 en 9 fléchettes (Perfect)", "img": "ho-one - 501 - 9 fleches", "category": "Ho-One"},
    {"id": "HO_ONE_501_10_DARTS", "name": "501 - 10 fléchettes", "desc": "Terminer le 501 en 10 fléchettes", "img": "ho-one - 501 - 10 fleches", "category": "Ho-One"},
    {"id": "HO_ONE_501_11_DARTS", "name": "501 - 11 fléchettes", "desc": "Terminer le 501 en 11 fléchettes", "img": "ho-one - 501 - 11 fleches", "category": "Ho-One"},
    {"id": "HO_ONE_501_12_DARTS", "name": "501 - 12 fléchettes", "desc": "Terminer le 501 en 12 fléchettes", "img": "ho-one - 501 - 12 fleches", "category": "Ho-One"},
    {"id": "HO_ONE_501_15_DARTS", "name": "501 - 15 fléchettes", "desc": "Terminer le 501 en 15 fléchettes", "img": "ho-one - 501 - 15 fleches", "category": "Ho-One"},

    # --- 6. Succès de progression ---
    {"id": "FLECHES_LANCEES_100", "name": "Fléches Lancées (I)", "desc": "Lancer 100 fléchettes", "img": "fleches lancees - 100", "category": "Succès de progression"},
    {"id": "WINNER_10", "name": "Winner (I)", "desc": "Gagner 10 parties", "img": "winner - 10", "category": "Succès de progression"},
    {"id": "BULLS_10", "name": "Simple Bull (I)", "desc": "Toucher le simple bull 10 fois", "img": "bulls 10", "category": "Succès de progression"},
    {"id": "BULLS_50", "name": "Simple Bull (II)", "desc": "Atteindre le bull 50 fois", "img": "bulls 50", "category": "Succès de progression"},
    {"id": "BULLS_100", "name": "Simple Bull (III)", "desc": "Toucher le bull 100 fois", "img": "bulls 100", "category": "Succès de progression"},
    {"id": "FLECHES_LANCEES_500", "name": "Fléches Lancées (II)", "desc": "Lancer 500 fléchettes", "img": "fleches lancees - 500", "category": "Succès de progression"},
    {"id": "WINNER_50", "name": "Winner (II)", "desc": "Gagner 50 parties", "img": "winner - 50", "category": "Succès de progression"},
    {"id": "DBULLS_10", "name": "Double Bull (I)", "desc": "Toucher le double bull 10 fois", "img": "dbulls 10", "category": "Succès de progression"},
    {"id": "DBULLS_50", "name": "Double Bull (II)", "desc": "Toucher le double bull 50 fois", "img": "dbulls 50", "category": "Succès de progression"},
    {"id": "DBULLS_100", "name": "Double Bull (III)", "desc": "Toucher le double bull 100 fois", "img": "dbulls 100", "category": "Succès de progression"},
    {"id": "FLECHES_LANCEES_1000", "name": "Fléches Lancées (III)", "desc": "Lancer 1000 fléchettes", "img": "fleches lancees - 1000", "category": "Succès de progression"},
    {"id": "WINNER_100", "name": "Winner (III)", "desc": "Gagner 100 parties", "img": "winner - 100", "category": "Succès de progression"},
    {"id": "TOUCH_DOUBLE_10", "name": "Double (I)", "desc": "Toucher un double 10 fois", "img": "double - 10", "category": "Succès de progression"},
    {"id": "TOUCH_DOUBLE_50", "name": "Double (II)", "desc": "Toucher un double 50 fois", "img": "double - 50", "category": "Succès de progression"},
    {"id": "TOUCH_DOUBLE_100", "name": "Double (III)", "desc": "Toucher un double 100 fois", "img": "double - 100", "category": "Succès de progression"},
    {"id": "FLECHES_LANCEES_2500", "name": "Fléches Lancées (IV)", "desc": "Lancer 2500 fléchettes", "img": "fleches lancees - 2500", "category": "Succès de progression"},
    {"id": "WINNER_250", "name": "Winner (IV)", "desc": "Gagner 250 parties", "img": "winner - 250", "category": "Succès de progression"},
    {"id": "TOUCH_TRIPLE_10", "name": "Triple (I)", "desc": "Toucher un triple 10 fois", "img": "triple - 10", "category": "Succès de progression"},
    {"id": "TOUCH_TRIPLE_50", "name": "Triple (II)", "desc": "Toucher un triple 50 fois", "img": "triple - 50", "category": "Succès de progression"},
    {"id": "TOUCH_TRIPLE_100", "name": "Triple (III)", "desc": "Toucher un triple 100 fois", "img": "triple - 100", "category": "Succès de progression"},
    {"id": "CREATION_ARTISTIQUE", "name": "Création artistique", "desc": "Participation à la création artistique : partager un thème sur RaspyHub", "img": "creation artistique", "category": "Succès de progression"},

    # --- 8. CRICKET ---
    {"id": "3_MARK_CRICKET", "name": "3 Mark Cricket", "desc": "Réaliser 3 marques au Cricket", "img": "cricket 3 mark", "category": "Cricket / Mickey"},
    {"id": "4_MARK_CRICKET", "name": "4 Mark Cricket", "desc": "Réaliser 4 marques au Cricket", "img": "cricket 4 mark", "category": "Cricket / Mickey"},
    {"id": "5_MARK_CRICKET", "name": "5 Mark Cricket", "desc": "Réaliser 5 marques au Cricket", "img": "cricket 5 mark", "category": "Cricket / Mickey"},
    {"id": "6_MARK_CRICKET", "name": "6 Mark Cricket", "desc": "Réaliser 6 marques au Cricket", "img": "cricket 6 mark", "category": "Cricket / Mickey"},
    {"id": "7_MARK_CRICKET", "name": "7 Mark Cricket", "desc": "Réaliser 7 marques au Cricket", "img": "cricket 7 mark", "category": "Cricket / Mickey"},
    {"id": "8_MARK_CRICKET", "name": "8 Mark Cricket", "desc": "Réaliser 8 marques au Cricket", "img": "cricket 8 mark", "category": "Cricket / Mickey"},
    {"id": "9_MARK_CRICKET", "name": "9 Mark Cricket", "desc": "Réaliser 9 marques au Cricket", "img": "cricket 9 mark", "category": "Cricket / Mickey"},
    {"id": "3_MARK_MICKEY", "name": "3 Mark Mickey", "desc": "Réaliser 3 marques au Mickey", "img": "mickey 3 mark", "category": "Cricket / Mickey"},
    {"id": "4_MARK_MICKEY", "name": "4 Mark Mickey", "desc": "Réaliser 4 marques au Mickey", "img": "mickey 4 mark", "category": "Cricket / Mickey"},
    {"id": "5_MARK_MICKEY", "name": "5 Mark Mickey", "desc": "Réaliser 5 marques au Mickey", "img": "mickey 5 mark", "category": "Cricket / Mickey"},
    {"id": "6_MARK_MICKEY", "name": "6 Mark Mickey", "desc": "Réaliser 6 marques au Mickey", "img": "mickey 6 mark", "category": "Cricket / Mickey"},
    {"id": "7_MARK_MICKEY", "name": "7 Mark Mickey", "desc": "Réaliser 7 marques au Mickey", "img": "mickey 7 mark", "category": "Cricket / Mickey"},
    {"id": "8_MARK_MICKEY", "name": "8 Mark Mickey", "desc": "Réaliser 8 marques au Mickey", "img": "mickey 8 mark", "category": "Cricket / Mickey"},
    {"id": "9_MARK_MICKEY", "name": "9 Mark Mickey", "desc": "Réaliser 9 marques au Mickey", "img": "mickey 9 mark", "category": "Cricket / Mickey"},

# --- 9. ROUTINE ---
    {"id": "ROUTINE_NV1", "name": "Routine - Niveau 1", "desc": "Valider le défi 1 de Routine", "img": "routine_nv1", "category": "Routine"},
    {"id": "ROUTINE_NV2", "name": "Routine - Niveau 2", "desc": "Valider le défi 2 de Routine", "img": "routine_nv2", "category": "Routine"},
    {"id": "ROUTINE_NV3", "name": "Routine - Niveau 3", "desc": "Valider le défi 3 de Routine", "img": "routine_nv3", "category": "Routine"},
    {"id": "ROUTINE_NV4", "name": "Routine - Niveau 4", "desc": "Valider le défi 4 de Routine", "img": "routine_nv4", "category": "Routine"},
    {"id": "ROUTINE_NV5", "name": "Routine - Niveau 5", "desc": "Valider le défi 5 de Routine", "img": "routine_nv5", "category": "Routine"},
    {"id": "ROUTINE_NV6", "name": "Routine - Niveau 6", "desc": "Valider le défi 6 de Routine", "img": "routine_nv6", "category": "Routine"},
    {"id": "ROUTINE_NV7", "name": "Routine - Niveau 7", "desc": "Valider le défi 7 de Routine", "img": "routine_nv7", "category": "Routine"},
    {"id": "ROUTINE_NV8", "name": "Routine - Niveau 8", "desc": "Valider le défi 8 de Routine", "img": "routine_nv8", "category": "Routine"},
    {"id": "ROUTINE_NV9", "name": "Routine - Niveau 9", "desc": "Valider le défi 9 de Routine", "img": "routine_nv9", "category": "Routine"},
    {"id": "ROUTINE_NV10", "name": "Routine - Niveau 10", "desc": "Valider le défi 10 de Routine", "img": "routine_nv10", "category": "Routine"},
    {"id": "ROUTINE_NV11", "name": "Routine - Niveau 11", "desc": "Valider le défi 11 de Routine", "img": "routine_nv11", "category": "Routine"},
    {"id": "ROUTINE_NV12", "name": "Routine - Niveau 12", "desc": "Valider le défi 12 de Routine", "img": "routine_nv12", "category": "Routine"},
    {"id": "ROUTINE_NV13", "name": "Routine - Niveau 13", "desc": "Valider le défi 13 de Routine", "img": "routine_nv13", "category": "Routine"},
    {"id": "ROUTINE_NV14", "name": "Routine - Niveau 14", "desc": "Valider le défi 14 de Routine", "img": "routine_nv14", "category": "Routine"},
    {"id": "ROUTINE_NV15", "name": "Routine - Niveau 15", "desc": "Valider le défi 15 de Routine", "img": "routine_nv15", "category": "Routine"},
    {"id": "ROUTINE_NV16", "name": "Routine - Niveau 16", "desc": "Valider le défi 16 de Routine", "img": "routine_nv16", "category": "Routine"},
    {"id": "ROUTINE_NV17", "name": "Routine - Niveau 17", "desc": "Valider le défi 17 de Routine", "img": "routine_nv17", "category": "Routine"},
    {"id": "ROUTINE_NV18", "name": "Routine - Niveau 18", "desc": "Valider le défi 18 de Routine", "img": "routine_nv18", "category": "Routine"},
    {"id": "ROUTINE_NV19", "name": "Routine - Niveau 19", "desc": "Valider le défi 19 de Routine", "img": "routine_nv19", "category": "Routine"},
    {"id": "ROUTINE_NV20", "name": "Routine - Niveau 20", "desc": "Valider le défi 20 de Routine", "img": "routine_nv20", "category": "Routine"},
    {"id": "ROUTINE_NV21", "name": "Routine - Niveau 21", "desc": "Valider le défi 21 de Routine", "img": "routine_nv21", "category": "Routine"},
    {"id": "ROUTINE_NV22", "name": "Routine - Niveau 22", "desc": "Valider le défi 22 de Routine", "img": "routine_nv22", "category": "Routine"},
    {"id": "ROUTINE_NV23", "name": "Routine - Niveau 23", "desc": "Valider le défi 23 de Routine", "img": "routine_nv23", "category": "Routine"},
    {"id": "ROUTINE_NV24", "name": "Routine - Niveau 24", "desc": "Valider le défi 24 de Routine", "img": "routine_nv24", "category": "Routine"},
    {"id": "ROUTINE_NV25", "name": "Routine - Niveau 25", "desc": "Valider le défi 25 de Routine", "img": "routine_nv25", "category": "Routine"},
    {"id": "ROUTINE_NV26", "name": "Routine - Niveau 26", "desc": "Valider le défi 26 de Routine", "img": "routine_nv26", "category": "Routine"},
    {"id": "ROUTINE_NV27", "name": "Routine - Niveau 27", "desc": "Valider le défi 27 de Routine", "img": "routine_nv27", "category": "Routine"},
    {"id": "ROUTINE_NV28", "name": "Routine - Niveau 28", "desc": "Valider le défi 28 de Routine", "img": "routine_nv28", "category": "Routine"},
    {"id": "ROUTINE_NV29", "name": "Routine - Niveau 29", "desc": "Valider le défi 29 de Routine", "img": "routine_nv29", "category": "Routine"},
    {"id": "ROUTINE_NV30", "name": "Routine - Niveau 30", "desc": "Valider le défi 30 de Routine", "img": "routine_nv30", "category": "Routine"},
    {"id": "ROUTINE_NV31", "name": "Routine - Niveau 31", "desc": "Valider le défi 31 de Routine", "img": "routine_nv31", "category": "Routine"},
    {"id": "ROUTINE_NV32", "name": "Routine - Niveau 32", "desc": "Valider le défi 32 de Routine", "img": "routine_nv32", "category": "Routine"},
    {"id": "ROUTINE_NV33", "name": "Routine - Niveau 33", "desc": "Valider le défi 33 de Routine", "img": "routine_nv33", "category": "Routine"},
    {"id": "ROUTINE_NV34", "name": "Routine - Niveau 34", "desc": "Valider le défi 34 de Routine", "img": "routine_nv34", "category": "Routine"},
    {"id": "ROUTINE_NV35", "name": "Routine - Niveau 35", "desc": "Valider le défi 35 de Routine", "img": "routine_nv35", "category": "Routine"}

]


NAMES_LEVELS = {
    1: "Novice I",
    2: "Novice II",
    3: "Amateur I",
    4: "Amateur II",
    5: "Amateur III",
    6: "Amateur IV",
    7: "Amateur V",
    8: "Régulier I",
    9: "Régulier II",
    10: "Régulier III",
    11: "Régulier IV",
    12: "Régulier V",
    13: "Confirmé I",
    14: "Confirmé II",
    15: "Confirmé III",
    16: "Vétéran I",
    17: "Vétéran II",
    18: "Vétéran III",
    19: "Expert I",
    20: "Expert II",
    21: "Expert III",
    22: "Maître I",
    23: "Maître II",
    24: "Maître III",
    25: "Grand Maître",
    26: "Élite",
    27: "Légende",
    28: "Champion",
    29: "Grand Champion",
    30: "Ultime Légende"
}


def average_ppd_or_others(stats, game):
    """
    PPD moyen à ce jeu, sinon la moyenne de ceux des autres jeux
    """
    ppd = average_ppd(stats, game)
    if ppd:
        return ppd
    games = {key.split('_', 2)[2] for key in stats if key.startswith(('moyenne_ppd_', 'moyenne_ppr_', 'ppr_moyen_'))}
    values = [value for value in (average_ppd(stats, other) for other in games) if isinstance(value, (int, float)) and value > 0]
    return sum(values) / len(values) if values else 0.0


def get_level_from_ppd(ppd_value):
    """
    Niveau du joueur d'après son PPD (Points Per Dart)
    """
    if ppd_value is None:
        return 1

    if ppd_value <= 10.64: return 1
    elif ppd_value <= 11.89: return 2
    elif ppd_value <= 13.14: return 3
    elif ppd_value <= 14.39: return 4
    elif ppd_value <= 15.64: return 5
    elif ppd_value <= 16.89: return 6
    elif ppd_value <= 18.14: return 7
    elif ppd_value <= 19.44: return 8
    elif ppd_value <= 20.74: return 9
    elif ppd_value <= 22.04: return 10
    elif ppd_value <= 23.34: return 11
    elif ppd_value <= 24.64: return 12
    elif ppd_value <= 25.94: return 13
    elif ppd_value <= 27.29: return 14
    elif ppd_value <= 28.64: return 15
    elif ppd_value <= 29.99: return 16
    elif ppd_value <= 31.34: return 17
    elif ppd_value <= 32.69: return 18
    elif ppd_value <= 34.04: return 19
    elif ppd_value <= 35.39: return 20
    elif ppd_value <= 36.79: return 21
    elif ppd_value <= 38.19: return 22
    elif ppd_value <= 39.59: return 23
    elif ppd_value <= 40.99: return 24
    elif ppd_value <= 42.39: return 25
    elif ppd_value <= 43.79: return 26
    elif ppd_value <= 45.19: return 27
    elif ppd_value <= 46.59: return 28
    elif ppd_value <= 47.99: return 29
    else: return 30

def get_level_from_mpr(mpr_value):
    if mpr_value <= 1.09: return 1
    elif mpr_value <= 1.19: return 2
    elif mpr_value <= 1.30: return 3
    elif mpr_value <= 1.45: return 4
    elif mpr_value <= 1.60: return 5
    elif mpr_value <= 1.75: return 6
    elif mpr_value <= 1.90: return 7
    elif mpr_value <= 2.05: return 8
    elif mpr_value <= 2.20: return 9
    elif mpr_value <= 2.35: return 10
    elif mpr_value <= 2.50: return 11
    elif mpr_value <= 2.65: return 12
    elif mpr_value <= 2.80: return 13
    elif mpr_value <= 2.95: return 14
    elif mpr_value <= 3.10: return 15
    elif mpr_value <= 3.25: return 16
    elif mpr_value <= 3.40: return 17
    elif mpr_value <= 3.56: return 18
    elif mpr_value <= 3.70: return 19
    elif mpr_value <= 3.85: return 20
    elif mpr_value <= 4.06: return 21
    elif mpr_value <= 4.27: return 22
    elif mpr_value <= 4.48: return 23
    elif mpr_value <= 4.69: return 24
    elif mpr_value <= 4.95: return 25
    elif mpr_value <= 5.21: return 26
    elif mpr_value <= 5.47: return 27
    elif mpr_value <= 5.73: return 28
    elif mpr_value <= 5.99: return 29
    else: return 30


def get_base_name_from_online(online_name):
    """
    Extrait le pseudo de base en supprimant le préfixe numérique et les symboles/séparateurs
    (dont l'espace, l'étoile, le tiret, le point médian '·' / '\u00b7', etc.).
    """
    cleaned = re.sub(r'^[0-9\s\*\-\.\_\/·\u00b7]+', '', online_name).strip()
    return cleaned if cleaned else online_name


def merge_online_player_to_base(online_name, target_name=None):
    """
    Fusionne les stats et trophées d'un joueur (online_name) vers un joueur cible
    (target_name si fourni, sinon le pseudo de base extrait automatiquement).
    """
    data = load_player_data()

    online_key = None
    for k in data.keys():
        if k.strip().lower() == online_name.strip().lower():
            online_key = k
            break

    if not online_key or online_key == "_global_stats":
        print(f"[MERGE] Joueur source introuvable : {online_name}")
        return False

    base_name = target_name.strip() if target_name else get_base_name_from_online(online_key)
    if not base_name:
        print(f"[MERGE] Cible invalide pour : {online_name}")
        return False

    base_key = None
    for k in data.keys():
        if k.strip().lower() == base_name.strip().lower() and k != online_key:
            base_key = k
            break

    if not base_key:
        data[base_name] = data.pop(online_key)
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print("[ERREUR RENOMMAGE JOUEUR] :", e)
            return False

    online_data = data[online_key]
    base_data = data[base_key]

    # 1. Fusion des trophées
    online_trophies = online_data.get("trophies", [])
    base_trophies = base_data.get("trophies", [])
    base_data["trophies"] = list(set(base_trophies + online_trophies))

    # 2. Fusion des statistiques
    online_stats = online_data.get("stats", {})
    base_stats = base_data.get("stats", {})

    for stat_key, val in online_stats.items():
        if "moyenne_" in stat_key or "mpr_moyen_" in stat_key or "cumul_" in stat_key or "parties_ppd_" in stat_key or "parties_mpr_" in stat_key:
            continue

        if isinstance(val, (int, float)):
            base_stats[stat_key] = base_stats.get(stat_key, 0) + val
        elif isinstance(val, dict):
            if stat_key not in base_stats:
                base_stats[stat_key] = {}
            for sub_k, sub_v in val.items():
                if isinstance(sub_v, (int, float)):
                    base_stats[stat_key][sub_k] = base_stats[stat_key].get(sub_k, 0) + sub_v

    all_stat_keys = set(list(online_stats.keys()) + list(base_stats.keys()))

    for key in all_stat_keys:
        if key.startswith("moyenne_ppd_"):
            game_name = key.replace("moyenne_ppd_", "")
            cumul_key = f"cumul_ppd_{game_name}"
            parties_key = f"parties_ppd_{game_name}"

            base_cumul = base_stats.get(cumul_key, 0.0) + online_stats.get(cumul_key, 0.0)
            base_parties = base_stats.get(parties_key, 0) + online_stats.get(parties_key, 0)
            if base_parties <= 0:
                base_parties = base_stats.get(f"parties_jouees_{game_name}", 0)

            base_stats[cumul_key] = round(base_cumul, 4)
            base_stats[parties_key] = base_parties

            if base_parties > 0 and base_cumul > 0:
                base_stats[key] = round(base_cumul / base_parties, 2)
            else:
                base_stats[key] = round(online_stats.get(key, base_stats.get(key, 0.0)), 2)

        elif key.startswith("moyenne_mpr_") or key.startswith("mpr_moyen_"):
            game_name = key.replace("moyenne_mpr_", "").replace("mpr_moyen_", "")
            cumul_key = f"cumul_mpr_{game_name}"
            parties_key = f"parties_mpr_{game_name}"

            if cumul_key in online_stats or cumul_key in base_stats:
                base_cumul = base_stats.get(cumul_key, 0.0) + online_stats.get(cumul_key, 0.0)
                base_parties = base_stats.get(parties_key, 0) + online_stats.get(parties_key, 0)
                if base_parties <= 0:
                    base_parties = base_stats.get(f"parties_jouees_{game_name}", 0)

                base_stats[cumul_key] = round(base_cumul, 4)
                base_stats[parties_key] = base_parties

                if base_parties > 0 and base_cumul > 0:
                    base_stats[key] = round(base_cumul / base_parties, 2)
                else:
                    base_stats[key] = round(online_stats.get(key, base_stats.get(key, 0.0)), 2)
            else:
                p_base = base_stats.get(f"parties_jouees_{game_name}", 0)
                p_online = online_stats.get(f"parties_jouees_{game_name}", 0)
                m_base = base_stats.get(key, 0.0)
                m_online = online_stats.get(key, 0.0)
                if (p_base + p_online) > 0:
                    base_stats[key] = round((m_base * p_base + m_online * p_online) / (p_base + p_online), 2)

    base_data["stats"] = base_stats
    del data[online_key]

    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[MERGE OK] '{online_key}' fusionné dans '{base_key}'.")
        return True
    except Exception as e:
        print("[ERREUR FUSION JOUEUR] :", e)
        return False



def delete_player(name):
    data = load_player_data()
    target_key = None

    # 1. Trouver la clé exacte du joueur (insensible à la casse)
    for k in data.keys():
        if k.lower() == name.lower():
            target_key = k
            break

    if target_key and target_key in data:
        player_data = data[target_key]
        player_stats = player_data.get("stats", {})

        # 2. Récupérer _global_stats s'il existe
        global_stats = data.get("_global_stats", {})

        if global_stats:
            # A. Décrémenter le nombre total de parties jouées par le joueur
            # (On regarde soit le total direct, soit la somme des parties par jeu)
            total_player_parties = player_stats.get('total_parties_jouees', 0)

            # S'il y a des clés de parties par jeu dans les stats du joueur
            game_keys = set()
            for key in player_stats.keys():
                if key.startswith("parties_jouees_"):
                    game_keys.add(key.replace("parties_jouees_", ""))

            # Si le total global n'est pas explicite, on le somme depuis les jeux du joueur
            if total_player_parties == 0 and game_keys:
                total_player_parties = sum(player_stats.get(f"parties_jouees_{g}", 0) for g in game_keys)

            # Soustraire du total général des parties de la machine
            if 'total_machine_parties' in global_stats and total_player_parties > 0:
                global_stats['total_machine_parties'] = max(0, global_stats['total_machine_parties'] - total_player_parties)

            # B. Décrémenter les compteurs spécifiques par jeu (ex: parties_reelles_highscore, etc.)
            for g in game_keys:
                p_count = player_stats.get(f"parties_jouees_{g}", 0)
                if p_count > 0:
                    # Dans _global_stats, les clés sont souvent préfixées par 'parties_reelles_'
                    global_key = f"parties_reelles_{g}"
                    if global_key in global_stats:
                        global_stats[global_key] = max(0, global_stats[global_key] - p_count)
                        # Si le compteur tombe à 0, on peut éventuellement nettoyer ou le laisser à 0

        # 3. Supprimer le joueur du dictionnaire
        del data[target_key]

        # 4. Sauvegarder les modifications dans le fichier JSON
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print("[ERREUR SUPPRESSION JOUEUR] :", e)

    return False


def load_player_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def load_favorite_names():
    data = load_player_data()
    formatted_names = [name.strip().capitalize() for name in data.keys() if name.strip() and name != "_global_stats"]
    return sorted(formatted_names, key=lambda n: n.lower())


def ensure_player_exists(name):
    data = load_player_data()
    original_key = None
    for k in data.keys():
        if k.lower() == name.lower():
            original_key = k
            break

    if original_key is None:
        data[name] = {"trophies": [], "stats": {}}
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass


# --- ÉCRAN 1 : SÉLECTION DU JOUEUR (AVEC TABLEAU DÉTAILLÉ) ---
# DEPLACER AU DESSUS DE MAIN

# --- ÉCRAN 1.5 : SÉLECTION DE LA CATÉGORIE ---
class CategorySelectionScreen:
    def __init__(self, screen, current_player, rpi=None):
        self.screen = screen
        self.current_player = current_player
        self.rpi = rpi
        self.selected_index = 0
        self.categories = [
            "Statistiques",
            "Succès de progression",
            "Combinaisons et figures",
            "Scores spécifiques",
            "Cricket / Mickey",
            "Ho-One",
            "Routine",
            "Doubles",
            "Triples"
        ]
        all_data = load_player_data()
        player_info = {}
        for k, v in all_data.items():
            if k.strip().lower() == self.current_player.strip().lower():
                player_info = v
                break
        self.unlocked_trophies_list = player_info.get("trophies", [])

    def get_trophy_counts_for_category(self, category_name):
        if category_name == "Statistiques":
            return None, None

        total_in_cat = 0
        unlocked_in_cat = 0

        for trophy in ALL_TROPHIES:
            if trophy.get("category") == category_name:
                total_in_cat += 1
                if trophy["id"] in self.unlocked_trophies_list:
                    unlocked_in_cat += 1

        return unlocked_in_cat, total_in_cat

    def run(self):
        clock = pygame.time.Clock()
        width, height = self.screen.get_size()
        scale = ui_scale(self.screen)

        try:
            title_font = cfonts.font(int(40 * scale), bold=True)
            text_font = cfonts.font(int(26 * scale), bold=True)
            footer_font = cfonts.font(int(20 * scale))
        except Exception:
            title_font = pygame.font.Font(None, 40)
            text_font = pygame.font.Font(None, 26)
            footer_font = pygame.font.Font(None, 20)

        total_cats = len(self.categories)
        running = True

        while running:
            self.screen.fill((20, 24, 33))

            title_text = shrink(title_font.render(tr("{player} - CHOISIR UNE CATEGORIE", player=self.current_player), True, (255, 255, 255)), width - int(40 * scale))
            title_rect = title_text.get_rect(center=(width // 2, int(50 * scale)))
            self.screen.blit(title_text, title_rect)

            start_y = int(95 * scale)
            button_width = int(650 * scale)
            # The buttons share the height between the title and Retour
            button_height = int(min(50 * scale, (height - start_y - int(110 * scale)) / total_cats - 12 * scale))
            button_x = (width - button_width) // 2
            zones = {}

            for idx, cat_name in enumerate(self.categories):
                by = start_y + idx * (button_height + int(12 * scale))
                b_rect = pygame.Rect(button_x, by, button_width, button_height)

                is_highlighted = (idx == self.selected_index)
                bg_color = (55, 70, 105) if is_highlighted else (35, 42, 58)
                border_color = (100, 150, 255) if is_highlighted else (60, 72, 98)
                text_color = (255, 255, 255) if is_highlighted else (200, 205, 215)
                border_width = int(3 * scale) if is_highlighted else int(2 * scale)

                pygame.draw.rect(self.screen, bg_color, b_rect, border_radius=int(8 * scale))
                pygame.draw.rect(self.screen, border_color, b_rect, border_width, border_radius=int(8 * scale))

                unlocked, total = self.get_trophy_counts_for_category(cat_name)
                if cat_name == "Statistiques":
                    display_text = tr("Statistiques Générales & Par Jeu")
                else:
                    display_text = f"{tr(cat_name)}  -  ({unlocked}/{total})"

                text_surface = text_font.render(display_text, True, text_color)
                text_rect = text_surface.get_rect(center=b_rect.center)
                self.screen.blit(text_surface, text_rect)
                zones[idx] = b_rect

            back_rect = draw_button(self.screen, (int(30 * scale), height - int(62 * scale), int(180 * scale), int(44 * scale)),
                                    tr("Retour"), footer_font)
            footer_text = footer_font.render(tr("HAUT / BAS (S20/S3) pour naviguer | ENTRÉE (Bull) ou toucher pour valider | ÉCHAP pour retour"), True, (150, 150, 150))
            # Right of Retour, smaller if needed ; else over it (centred on the screen, a wide
            # font went over Retour)
            room = pygame.Rect(back_rect.right + int(20 * scale), back_rect.y, width - back_rect.right - int(50 * scale), back_rect.height)
            footer_rect = fit_text(footer_text, room)
            if footer_rect is None:
                footer_rect = fit_text(footer_text, pygame.Rect(int(30 * scale), back_rect.y - back_rect.height - int(8 * scale),
                                                                width - int(60 * scale), back_rect.height), smallest=0.3)
            if footer_rect is not None:
                self.screen.blit(pygame.transform.smoothscale(footer_text, footer_rect.size), footer_rect)

            pygame.display.flip()

            navigation = 0
            action_pressed = None
            back_pressed = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "QUIT", None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        back_pressed = True
                    elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                        navigation = 1
                    elif event.key in (pygame.K_UP, pygame.K_LEFT):
                        navigation = -1
                    elif event.key == pygame.K_RETURN:
                        action_pressed = "SELECT"


            if self.rpi and hasattr(self.rpi, "listen_inputs"):
                try:
                    inp = self.rpi.listen_inputs()
                    position = click_of(inp)
                    if position is not None:
                        # A click or a touch : a category, or Retour
                        if back_rect.collidepoint(position):
                            back_pressed = True
                        for idx, rect in zones.items():
                            if rect.collidepoint(position):
                                self.selected_index = idx
                                action_pressed = "SELECT"
                    elif inp:
                        key_str = str(inp).strip()
                        if key_str in UP_KEYS + LEFT_KEYS:
                            navigation = -1
                        elif key_str in DOWN_KEYS + RIGHT_KEYS:
                            navigation = 1
                        elif key_str in ENTER_KEYS:
                            action_pressed = "SELECT"
                        elif key_str in ESCAPE_KEYS:
                            back_pressed = True

                except Exception as e:
                    print("[ERREUR LISTEN_INPUTS] :", e)

            if navigation != 0:
                self.selected_index = (self.selected_index + navigation) % total_cats


            if back_pressed:
                return "BACK", None

            if action_pressed == "SELECT":
                chosen_cat = self.categories[self.selected_index]
                return "SELECT", chosen_cat

            clock.tick(30)

        return "QUIT", None


# --- ÉCRAN 1.6 : AFFICHAGE DES TROPHÉES ---
class TrophiesScreen:
    def __init__(self, screen, current_player, category, rpi=None):
        self.screen = screen
        self.current_player = current_player
        self.category = category
        self.rpi = rpi

        all_data = load_player_data()
        player_info = {}
        for k, v in all_data.items():
            if k.strip().lower() == self.current_player.strip().lower():
                player_info = v
                break
        self.unlocked_trophies = player_info.get("trophies", [])

        self.filtered_trophies = [t for t in ALL_TROPHIES if t["category"] == self.category]
        if self.category.lower() == "ho-one":
            self.items_per_page = 21
        else:
            self.items_per_page = 20
        self.current_page = 0
        self.total_pages = max(1, (len(self.filtered_trophies) + self.items_per_page - 1) // self.items_per_page)

    def run(self):
        clock = pygame.time.Clock()
        width, height = self.screen.get_size()
        scale = ui_scale(self.screen)

        try:
            title_font = cfonts.font(int(35 * scale), bold=True)
            text_font = cfonts.font(int(20 * scale), bold=True)
            small_font = cfonts.font(int(15 * scale))
            footer_font = cfonts.font(int(19 * scale))
        except Exception:
            title_font = pygame.font.Font(None, 35)
            text_font = pygame.font.Font(None, 20)
            small_font = pygame.font.Font(None, 15)
            footer_font = pygame.font.Font(None, 19)

        running = True
        back_rect = previous_rect = next_rect = None
        while running:
            try:
                self.screen.fill((20, 24, 33))

                title_text = shrink(title_font.render(f"{self.current_player} - {tr(self.category).upper()}", True, (255, 255, 255)), width - int(40 * scale))
                title_rect = title_text.get_rect(center=(width // 2, int(45 * scale)))
                self.screen.blit(title_text, title_rect)

                start_idx = self.current_page * self.items_per_page
                end_idx = start_idx + self.items_per_page
                current_trophies = self.filtered_trophies[start_idx:end_idx]

                left_margin = int(25 * scale)
                column_gap = int(12 * scale)
                col_width = (width - (left_margin * 2) - (column_gap * 4)) // 5
                start_y = int(90 * scale)
                # The rows share the height between the title and the buttons at the bottom
                rows = max(1, (self.items_per_page + 4) // 5)
                row_height = int(min(130 * scale, (height - start_y - int(90 * scale)) / rows))
                box_height = int(row_height * 0.86)

                for i, trophy in enumerate(current_trophies):
                    col = i % 5
                    row = i // 5
                    x = left_margin + col * (col_width + column_gap)
                    y = start_y + row * row_height

                    box_rect = pygame.Rect(x, y, col_width, box_height)
                    is_unlocked = trophy["id"] in self.unlocked_trophies

                    box_bg = (35, 42, 58) if is_unlocked else (25, 28, 35)
                    box_border = (60, 72, 98) if is_unlocked else (40, 45, 55)

                    pygame.draw.rect(self.screen, box_bg, box_rect, border_radius=int(6 * scale))
                    pygame.draw.rect(self.screen, box_border, box_rect, int(2 * scale), border_radius=int(6 * scale))

                    self.screen.set_clip(box_rect)

                    img_width = int(36 * scale)
                    img_height = int(51 * scale)
                    img_x = x + int(10 * scale)
                    img_y = y + (box_height - img_height) // 2

                    img_name = trophy["img"] if "." in trophy["img"] else trophy["img"] + ".png"
                    img_path = os.path.join(BASE_DIR, "images_trophees", img_name)
                    has_image = False
                    if os.path.exists(img_path):
                        try:
                            trophy_img = pygame.image.load(img_path).convert_alpha()
                            trophy_img = pygame.transform.smoothscale(trophy_img, (img_width, img_height))
                            if not is_unlocked:
                                trophy_img.fill((80, 80, 80, 0), special_flags=pygame.BLEND_RGBA_MULT)
                            self.screen.blit(trophy_img, (img_x, img_y))
                            has_image = True
                        except:
                            pass

                    if not has_image:
                        pygame.draw.rect(self.screen, (80, 80, 80), (img_x, img_y, img_width, img_height))

                    text_x = img_x + img_width + int(10 * scale)
                    text_color = (240, 240, 240) if is_unlocked else (100, 110, 120)
                    desc_color = (170, 180, 200) if is_unlocked else (80, 85, 95)

                    name_surface = text_font.render(trophy_text(trophy["name"]), True, text_color)
                    text_width = x + col_width - text_x - int(6 * scale)
                    if name_surface.get_width() > text_width:
                        name_surface = pygame.transform.smoothscale(name_surface, (max(1, text_width), name_surface.get_height()))
                    lines = wrap_text(small_font, trophy_text(trophy["desc"]), text_width)
                    block = name_surface.get_height() + int(4 * scale) + len(lines) * small_font.get_linesize()
                    line_y = y + max(int(4 * scale), (box_height - block) // 2)
                    self.screen.blit(name_surface, (text_x, line_y))
                    line_y += name_surface.get_height() + int(4 * scale)
                    for line in lines:
                        self.screen.blit(small_font.render(line, True, desc_color), (text_x, line_y))
                        line_y += small_font.get_linesize()
                    self.screen.set_clip(None)

                button_h = int(44 * scale)
                button_y = height - int(62 * scale)
                back_rect = draw_button(self.screen, (int(30 * scale), button_y, int(180 * scale), button_h), tr("Retour"), footer_font)
                previous_rect = next_rect = None
                if self.total_pages > 1:
                    page_info = tr("Page {0} / {1} (GAUCHE / DROITE ou S11 / S6)", self.current_page + 1, self.total_pages)
                    page_surf = footer_font.render(page_info, True, (200, 200, 100))
                    button_w = int(150 * scale)
                    # Between Retour and the buttons of the pages, smaller if needed (a wide font
                    # pushed « < Page » over Retour)
                    side = button_w + int(20 * scale)
                    room = pygame.Rect(back_rect.right + int(20 * scale) + side, button_y,
                                       width - int(30 * scale) - side - (back_rect.right + int(20 * scale) + side), button_h)
                    page_rect = fit_text(page_surf, room, smallest=0.2) or pygame.Rect(room.centerx, room.centery, 1, 1)
                    self.screen.blit(pygame.transform.smoothscale(page_surf, page_rect.size), page_rect)
                    if self.current_page > 0:
                        previous_rect = draw_button(self.screen, (page_rect.x - button_w - int(20 * scale), button_y, button_w, button_h),
                                                    tr("< Page"), footer_font)
                    if self.current_page < self.total_pages - 1:
                        next_rect = draw_button(self.screen, (page_rect.right + int(20 * scale), button_y, button_w, button_h),
                                                tr("Page >"), footer_font)
                else:
                    footer_surface = footer_font.render(tr("ÉCHAP (ou bouton retour) pour retourner aux catégories"), True, (150, 150, 150))
                    # Right of Retour, smaller if needed (never on it)
                    room = pygame.Rect(back_rect.right + int(20 * scale), button_y, width - back_rect.right - int(50 * scale), button_h)
                    footer_rect = fit_text(footer_surface, room, smallest=0.3)
                    if footer_rect is not None:
                        self.screen.blit(pygame.transform.smoothscale(footer_surface, footer_rect.size), footer_rect)

                pygame.display.flip()

            except Exception as e:
                print("[ERREUR DESSIN TROPHÉES] :", e)

            page_change = 0
            back_pressed = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "BACK"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        back_pressed = True
                    elif event.key == pygame.K_RIGHT:
                        page_change = 1
                    elif event.key == pygame.K_LEFT:
                        page_change = -1

            if self.rpi and hasattr(self.rpi, "listen_inputs"):
                try:
                    inp = self.rpi.listen_inputs()
                    position = click_of(inp)
                    if position is not None:
                        # A click or a touch : Retour, the pages
                        if back_rect is not None and back_rect.collidepoint(position):
                            back_pressed = True
                        elif previous_rect is not None and previous_rect.collidepoint(position):
                            page_change = -1
                        elif next_rect is not None and next_rect.collidepoint(position):
                            page_change = 1
                    elif inp:
                        key_str = str(inp).strip()
                        if key_str in RIGHT_KEYS + DOWN_KEYS:
                            page_change = 1
                        elif key_str in LEFT_KEYS + UP_KEYS:
                            page_change = -1
                        elif key_str in ESCAPE_KEYS:
                            back_pressed = True
                except Exception as e:
                    print("[ERREUR LISTEN_INPUTS] :", e)

            if page_change != 0:
                new_page = self.current_page + page_change
                if 0 <= new_page < self.total_pages:
                    self.current_page = new_page

            if back_pressed:
                return "BACK"

            clock.tick(30)

        return "BACK"


# --- ÉCRAN 2 : AFFICHAGE DES STATISTIQUES ---
def shrink(surface, max_width, max_height=None):
    '''
    A text rendered no wider than max_width (nor higher than max_height) : smaller as a whole,
    not squeezed (a wide font went over its neighbours)
    '''
    factor = min(1.0, max(1, max_width) / max(1, surface.get_width()))
    if max_height is not None:
        factor = min(factor, max(1, max_height) / max(1, surface.get_height()))
    if factor >= 1.0:
        return surface
    return pygame.transform.smoothscale(surface, (max(1, int(surface.get_width() * factor)), max(1, int(surface.get_height() * factor))))


def fit_text(surface, room, smallest=0.6):
    '''
    Where a text rendered goes in a room : centred, smaller as a whole if it does not hold (not
    under smallest of its size : None, too small to be read there)
    '''
    if room.width <= 0 or room.height <= 0:
        return None
    factor = min(1.0, room.width / max(1, surface.get_width()), room.height / max(1, surface.get_height()))
    if factor < smallest:
        return None
    rect = pygame.Rect(0, 0, max(1, int(surface.get_width() * factor)), max(1, int(surface.get_height() * factor)))
    rect.center = room.center
    return rect


class StatisticsScreen:
    def __init__(self, screen, current_player, rpi=None):
        self.screen = screen
        self.current_player = current_player
        self.rpi = rpi

        all_data = load_player_data()
        self.global_data = all_data.get("_global_stats", {})
        player_info = {}
        for k, v in all_data.items():
            if k.strip().lower() == self.current_player.strip().lower():
                player_info = v
                break
        self.stats = player_info.get("stats", {})
        self.scroll_offset = 0
        self.max_scroll = 0

    def run(self):
        clock = pygame.time.Clock()
        width, height = self.screen.get_size()
        scale = ui_scale(self.screen)

        # Chargement unique du JSON avant la boucle principale (évite 2 lectures disque par frame)
        all_players_data = load_player_data()
        global_stats_dict = all_players_data.get("_global_stats", {})
        total_machine_parties = global_stats_dict.get('total_machine_parties', 0)

        player_trophies_list = []
        for k, v in all_players_data.items():
            if k != "_global_stats" and k.strip().lower() == self.current_player.strip().lower():
                player_trophies_list = v.get("trophies", [])
                if "stats" in v:
                    self.stats = v.get("stats", self.stats)
                break

        unlocked_count = len(player_trophies_list)
        total_trophies_count = len(ALL_TROPHIES)

        if self.current_player and self.current_player not in all_players_data:
            all_players_data[self.current_player] = {"stats": self.stats}

        # Pré-calcul des statistiques globales du joueur courant
        total_parties = self.stats.get('total_parties_jouees', 0)
        total_flechettes = self.stats.get('total_darts', self.stats.get('total_flechettes', 0))

        wins = self.stats.get('wins', 0)
        losses = self.stats.get('losses', 0)

        simple_bulls = self.stats.get('sbulls_count', self.stats.get('simple_bulls_count', 0))
        double_bulls = self.stats.get('dbulls_count', self.stats.get('total_double_bulls', 0))
        total_bulls = simple_bulls + double_bulls

        doubles = self.stats.get('doubles_count', self.stats.get('total_doubles', 0))
        triples = self.stats.get('triples_count', self.stats.get('total_triples', 0))
        simples = self.stats.get('singles_count', 0)

        # misses = total_flechettes - doubles - triples - simples - double_bulls - simple_bulls
        misses = self.stats.get('misses_count', self.stats.get('total_misses', 0))

        p_win = (wins / total_parties * 100) if total_parties > 0 else 0
        p_loss = (losses / total_parties * 100) if total_parties > 0 else 0

        p_misses = (misses / total_flechettes * 100) if total_flechettes > 0 else 0
        p_simple_bulls = (simple_bulls / total_flechettes * 100) if total_flechettes > 0 else 0
        p_double_bulls = (double_bulls / total_flechettes * 100) if total_flechettes > 0 else 0
        p_bulls = (total_bulls / total_flechettes * 100) if total_flechettes > 0 else 0

        p_simples = (simples / total_flechettes * 100) if total_flechettes > 0 else 0
        p_doubles = (doubles / total_flechettes * 100) if total_flechettes > 0 else 0
        p_triples = (triples / total_flechettes * 100) if total_flechettes > 0 else 0

        def fmt_pct(val):
            return f"{val:.1f}".replace('.', ',')

        global_stats = [
            ("FLÉCHETTES", f"{total_flechettes}", ""),
            ("PARTIES", f"{total_parties}", f"/{total_machine_parties}" if total_machine_parties > 0 else ""),
            ("Victoires", f"{wins}", f"({fmt_pct(p_win)}%)" if total_parties > 0 else ""),
            ("Défaites", f"{losses}", f"({fmt_pct(p_loss)}%)" if total_parties > 0 else ""),

            ("Simples", f"{simples}", f"({fmt_pct(p_simples)}%)" if total_flechettes > 0 else ""),
            ("Doubles", f"{doubles}", f"({fmt_pct(p_doubles)}%)" if total_flechettes > 0 else ""),
            ("Triples", f"{triples}", f"({fmt_pct(p_triples)}%)" if total_flechettes > 0 else ""),
            ("MISS", f"{misses}", f"({fmt_pct(p_misses)}%)" if total_flechettes > 0 else ""),

            ("Bulls", f"{total_bulls}", f"({fmt_pct(p_bulls)}%)" if total_flechettes > 0 else ""),
            ("Simple Bull", f"{simple_bulls}", f"({fmt_pct(p_simple_bulls)}%)" if total_flechettes > 0 else ""),
            ("Double Bull", f"{double_bulls}", f"({fmt_pct(p_double_bulls)}%)" if total_flechettes > 0 else ""),
            ("", "", "")
        ]

        game_keys = set()
        for key in self.stats.keys():
            if key.startswith("parties_jouees_"):
                game_keys.add(key.replace("parties_jouees_", ""))
            elif key.startswith("victoire_"):
                game_keys.add(key.replace("victoire_", ""))
            elif key.startswith("defaite_"):
                game_keys.add(key.replace("defaite_", ""))

        player_summaries = []
        for p_name, p_content in all_players_data.items():
            if p_name == "_global_stats":
                continue
            p_st = p_content.get("stats", p_content)
            p_games = p_st.get('total_parties_jouees', 0)
            p_w = p_st.get('wins', sum(p_st.get(f"victoire_{g}", 0) for g in game_keys))
            p_l = p_st.get('losses', sum(p_st.get(f"defaite_{g}", 0) for g in game_keys))
            player_summaries.append((p_name, p_games, p_w, p_l))

        top_games = sorted(player_summaries, key=lambda x: x[1], reverse=True)[:3]
        top_wins = sorted(player_summaries, key=lambda x: x[2], reverse=True)[:3]
        top_losses = sorted(player_summaries, key=lambda x: x[3], reverse=True)[:3]

        top_played_games = []
        global_game_counts = {}

        for k, v in global_stats_dict.items():
            if k.startswith("parties_reelles_"):
                g_key = k.replace("parties_reelles_", "")
                global_game_counts[g_key] = v

        if not global_game_counts:
            for p_name, p_content in all_players_data.items():
                if p_name == "_global_stats":
                    continue
                p_st = p_content.get("stats", p_content)
                for k, v in p_st.items():
                    if k.startswith("parties_jouees_"):
                        g_key = k.replace("parties_jouees_", "")
                        global_game_counts[g_key] = global_game_counts.get(g_key, 0) + v

        sorted_global_games = sorted(global_game_counts.items(), key=lambda x: x[1], reverse=True)
        for g_name, g_val in sorted_global_games[:3]:
            formatted_name = g_name.lower().capitalize()
            if len(formatted_name) > 10:
                formatted_name = formatted_name[:9] + "."
            top_played_games.append((formatted_name, g_val))

        # Pré-calcul du meilleur joueur par jeu
        best_player_by_game = {}
        for game in game_keys:
            best_player_name = "-"
            max_vic = -1
            for p_name, p_content in all_players_data.items():
                if p_name == "_global_stats":
                    continue
                p_st = p_content.get("stats", p_content)
                p_vics_game = p_st.get(f"victoire_{game}", 0)
                if p_vics_game > max_vic:
                    max_vic = p_vics_game
                    best_player_name = p_name
            best_player_by_game[game] = best_player_name

        sorted_games = sorted(list(game_keys))

        # The fonts : sizes of the screen (ui_scale), the font of the theme (cfonts)
        title_font = cfonts.font(int(34 * scale))
        small_title_font = cfonts.font(int(20 * scale))
        label_font = cfonts.font(int(20 * scale))
        value_font = cfonts.font(int(34 * scale))
        pct_font = cfonts.font(int(18 * scale))
        panel_title_font = cfonts.font(int(24 * scale))
        rank_font = cfonts.font(int(19 * scale))
        game_title_font = cfonts.font(int(24 * scale))
        game_font = cfonts.font(int(19 * scale))
        button_font = cfonts.font(int(19 * scale))

        def blit_parts(parts, x, y, font, max_x=None):
            # A line of texts of several colours, side by side ; smaller as a whole when it goes
            # over max_x
            surfaces = [font.render(text, True, color) for text, color in parts]
            total = sum(surface.get_width() for surface in surfaces)
            factor = 1.0 if max_x is None or total <= max_x - x else max(0.1, (max_x - x) / max(1, total))
            for surface in surfaces:
                if factor < 1.0:
                    surface = pygame.transform.smoothscale(surface, (max(1, int(surface.get_width() * factor)),
                                                                     max(1, int(surface.get_height() * factor))))
                self.screen.blit(surface, (x, y))
                x += surface.get_width()
            return x

        back_rect = up_rect = down_rect = None
        scroll_step = int(60 * scale)
        running = True
        while running:
            self.screen.fill((20, 24, 33))
            margin = int(30 * scale)
            gap = int(12 * scale)

            # Title, its number of trophies beside it
            title_surf = title_font.render(tr("STATISTIQUES DE : {player}", player=self.current_player.upper()), True, (255, 255, 255))
            sub_surf = small_title_font.render("  " + tr("(Trophées : {0}/{1})", unlocked_count, total_trophies_count), True, (180, 190, 210))
            # Both on the width of the screen (a wide font cut the title)
            room = width - 2 * margin
            if title_surf.get_width() + sub_surf.get_width() > room:
                share = room / (title_surf.get_width() + sub_surf.get_width())
                title_surf = shrink(title_surf, int(title_surf.get_width() * share))
                sub_surf = shrink(sub_surf, int(sub_surf.get_width() * share))
            self.screen.blit(title_surf, (margin, int(12 * scale)))
            self.screen.blit(sub_surf, (margin + title_surf.get_width(),
                                        int(12 * scale) + (title_surf.get_height() - sub_surf.get_height()) // 2))

            # --- Top : the numbers of the player (left), the rankings (right) ---
            top_y = int(12 * scale) + title_surf.get_height() + gap
            top_h = int(height * 0.40)
            grid_w = int((width - 2 * margin) * 0.56)
            g_cols, g_rows = 4, 3
            g_box_w = (grid_w - (g_cols - 1) * gap) // g_cols
            g_box_h = (top_h - (g_rows - 1) * gap) // g_rows
            for idx, item in enumerate(global_stats):
                label, main_val, pct_val = (list(item) + ['', '', ''])[:3]
                if not label:
                    continue
                bx = margin + (idx % g_cols) * (g_box_w + gap)
                by = top_y + (idx // g_cols) * (g_box_h + gap)
                pygame.draw.rect(self.screen, (30, 35, 45), (bx, by, g_box_w, g_box_h), border_radius=8)
                pygame.draw.rect(self.screen, (60, 70, 90), (bx, by, g_box_w, g_box_h), 1, border_radius=8)
                lbl_surf = shrink(label_font.render(tr(label), True, (180, 180, 180)), g_box_w - int(20 * scale))
                self.screen.blit(lbl_surf, (bx + int(10 * scale), by + int(8 * scale)))
                # The number in big at the bottom right, its percentage before it
                val_surf = value_font.render(str(main_val), True, (0, 220, 120))
                val_x = bx + g_box_w - val_surf.get_width() - int(10 * scale)
                val_y = by + g_box_h - val_surf.get_height() - int(6 * scale)
                self.screen.blit(val_surf, (val_x, val_y))
                if pct_val:
                    pct_surf = pct_font.render(pct_val, True, (140, 180, 160))
                    self.screen.blit(pct_surf, (val_x - pct_surf.get_width() - int(8 * scale),
                                                val_y + val_surf.get_height() - pct_surf.get_height() - int(4 * scale)))

            panel_x = margin + grid_w + int(20 * scale)
            panel_w = width - margin - panel_x
            border_color = (70, 90, 120)
            pygame.draw.rect(self.screen, (25, 30, 40), (panel_x, top_y, panel_w, top_h), border_radius=8)
            pygame.draw.rect(self.screen, border_color, (panel_x, top_y, panel_w, top_h), 1, border_radius=8)
            panel_title = shrink(panel_title_font.render(tr("CLASSEMENTS"), True, (255, 200, 50)), panel_w - int(12 * scale))
            self.screen.blit(panel_title, (panel_x + (panel_w - panel_title.get_width()) // 2, top_y + int(6 * scale)))
            columns_y = top_y + panel_title.get_height() + int(12 * scale)
            col_w = panel_w // 4
            podium_colors = [(255, 215, 0), (200, 200, 200), (205, 127, 50)]

            def draw_mini_top(title, data_list, val_idx, col_index):
                c_x = panel_x + col_index * col_w
                pygame.draw.rect(self.screen, (32, 38, 50), (c_x, columns_y, col_w, top_y + top_h - columns_y))
                pygame.draw.rect(self.screen, border_color, (c_x, columns_y, col_w, top_y + top_h - columns_y), 1)
                t_surf = shrink(rank_font.render(tr(title), True, (200, 200, 220)), col_w - int(8 * scale))
                self.screen.blit(t_surf, (c_x + (col_w - t_surf.get_width()) // 2, columns_y + int(6 * scale)))
                line_y = columns_y + t_surf.get_height() + int(12 * scale)
                pygame.draw.line(self.screen, border_color, (c_x + 4, line_y), (c_x + col_w - 4, line_y), 1)
                step = (top_y + top_h - line_y - int(8 * scale)) / 3
                for i, row_data in enumerate(data_list[:3]):
                    item_surf = rank_font.render(f"{i + 1}. {row_data[0]} ({row_data[val_idx]})", True,
                                                 podium_colors[i] if i < 3 else (150, 220, 255))
                    item_surf = shrink(item_surf, col_w - int(12 * scale))
                    self.screen.blit(item_surf, (c_x + int(6 * scale), int(line_y + int(8 * scale) + step * i)))

            draw_mini_top("+ de Parties", top_games, 1, 0)
            draw_mini_top("+ de Victoires", top_wins, 2, 1)
            draw_mini_top("+ de Défaites", top_losses, 3, 2)
            draw_mini_top("Top jeux", top_played_games, 1, 3)

            # --- Below : a panel by game, on the rest of the height, scrolled when it goes over ---
            buttons_h = int(46 * scale)
            buttons_y = height - buttons_h - int(14 * scale)
            area_top = top_y + top_h + int(18 * scale)
            area = pygame.Rect(margin, area_top, width - 2 * margin, buttons_y - int(12 * scale) - area_top)
            cols = 3
            box_w = (area.width - (cols - 1) * gap) // cols
            box_h = int(game_title_font.get_linesize() + 2 * game_font.get_linesize() + int(22 * scale))
            total_rows = (len(sorted_games) + cols - 1) // cols
            self.max_scroll = max(0, total_rows * (box_h + gap) - gap - area.height)
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
            self.screen.set_clip(area)
            for index, game in enumerate(sorted_games):
                box_x = area.x + (index % cols) * (box_w + gap)
                box_y = area.y + (index // cols) * (box_h + gap) - self.scroll_offset
                if box_y + box_h < area.y or box_y > area.bottom:
                    continue
                pygame.draw.rect(self.screen, (35, 40, 50), (box_x, box_y, box_w, box_h), border_radius=8)
                pygame.draw.rect(self.screen, (90, 100, 130), (box_x, box_y, box_w, box_h), 2, border_radius=8)
                text_x = box_x + int(12 * scale)
                line_y = box_y + int(8 * scale)
                self.screen.blit(shrink(game_title_font.render(game.upper(), True, (255, 200, 50)), box_w - int(24 * scale)), (text_x, line_y))
                line_y += game_title_font.get_linesize()

                p_jouees = self.stats.get(f"parties_jouees_{game}", 0)
                victoires = self.stats.get(f"victoire_{game}", 0)
                defaites = self.stats.get(f"defaite_{game}", 0)
                vic_color = (0, 220, 120) if victoires > defaites else ((255, 80, 80) if victoires < defaites else (210, 210, 210))
                grey = (210, 210, 210)
                blit_parts([(tr("Parties : {0}", p_jouees) + "  •  " + tr("Victoires : "), grey), (str(victoires), vic_color),
                            ("  •  " + tr("Défaites : {0}", defaites), grey)], text_x, line_y, game_font, box_x + box_w - int(12 * scale))
                line_y += game_font.get_linesize()

                parts = []
                game_lower = game.lower()
                if game_lower in ["cricket", "mickey"]:
                    mpr_val = self.stats.get(f"moyenne_mpr_{game}", self.stats.get(f"mpr_moyen_{game}", 0.0))
                    parts += [(tr("MPR : "), grey), (f"{mpr_val:.2f}".replace('.', ','), (0, 220, 255)), ("  •  ", grey)]
                elif game_lower in ["321_zlip", "batard", "highscore", "shoot-out", "up_and_down", "sabotage", "chaos", "low_score", "ho-one"]:
                    ppd_val = average_ppd(self.stats, game_lower)
                    parts += [(tr("PPD : "), grey), (f"{ppd_val:.2f}".replace('.', ','), (0, 220, 255)), ("  •  ", grey)]
                parts += [(tr("Meilleur joueur : "), grey), (f"{best_player_by_game.get(game, '-')}", (0, 220, 255))]
                blit_parts(parts, text_x, line_y, game_font, box_x + box_w - int(12 * scale))
            self.screen.set_clip(None)

            # --- Buttons : Retour, and the scrolling when the games go over ---
            back_rect = draw_button(self.screen, (margin, buttons_y, int(180 * scale), buttons_h), tr("Retour"), button_font)
            up_rect = down_rect = None
            if self.max_scroll > 0:
                arrow_w = int(110 * scale)
                down_rect = draw_button(self.screen, (width - margin - arrow_w, buttons_y, arrow_w, buttons_h), "▼", button_font)
                up_rect = draw_button(self.screen, (down_rect.x - gap - arrow_w, buttons_y, arrow_w, buttons_h), "▲", button_font)
            hint_surf = pct_font.render(tr("Échap : retour  |  Haut / Bas ou S20 / S3 : défiler  |  toucher les boutons"), True, (150, 150, 170))
            # Between the buttons, smaller if needed (the games are over them) ; never on them :
            # centred on the line, a wide font went over Retour
            room = pygame.Rect(back_rect.right + gap, buttons_y, (up_rect.x if up_rect else width - margin) - gap - back_rect.right - gap, buttons_h)
            hint_rect = fit_text(hint_surf, room, smallest=0.35)
            if hint_rect is not None:
                self.screen.blit(pygame.transform.smoothscale(hint_surf, hint_rect.size), hint_rect)

            pygame.display.flip()

            back_pressed = False
            navigation = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "BACK"
                elif event.type == pygame.MOUSEWHEEL:
                    navigation = -event.y
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        back_pressed = True
                    elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                        navigation = 1
                    elif event.key in (pygame.K_UP, pygame.K_LEFT):
                        navigation = -1

            if self.rpi and hasattr(self.rpi, "listen_inputs"):
                try:
                    inp = self.rpi.listen_inputs()
                    position = click_of(inp)
                    if position is not None:
                        # A click or a touch : Retour, the scrolling
                        if back_rect.collidepoint(position):
                            back_pressed = True
                        elif up_rect is not None and up_rect.collidepoint(position):
                            navigation = -1
                        elif down_rect is not None and down_rect.collidepoint(position):
                            navigation = 1
                    elif inp:
                        key_str = str(inp).strip()
                        if key_str in DOWN_KEYS + RIGHT_KEYS:
                            navigation = 1
                        elif key_str in UP_KEYS + LEFT_KEYS:
                            navigation = -1
                        elif key_str in ESCAPE_KEYS:
                            back_pressed = True
                except Exception as e:
                    print("[ERREUR LISTEN_INPUTS] :", e)

            if navigation != 0:
                self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset + navigation * scroll_step))

            if back_pressed:
                return "BACK"

            clock.tick(30)

        return "BACK"

def get_player_logo(player_name, scale, game_type="ho-one", all_players_data=None):
    """
    Récupère et charge le logo du joueur en fonction de son niveau calculé (1 à 30),
    en respectant le format d'origine 136x52.
    """
    try:
        player_stats = {}

        # Recherche sécurisée des données et extraction de la sous-clé "stats"
        if all_players_data and isinstance(all_players_data, dict):
            p_content = None
            for k, v in all_players_data.items():
                if k.strip().lower() == player_name.strip().lower():
                    p_content = v
                    break

            if p_content:
                if isinstance(p_content, dict) and "stats" in p_content:
                    player_stats = p_content["stats"]
                else:
                    player_stats = p_content

        game_lower = game_type.lower()
        level = 1

        # Calcul du niveau selon le jeu
        if "cricket" in game_lower:
            mpr_value = player_stats.get("moyenne_mpr_cricket", player_stats.get("mpr_moyen_cricket", 0.0))
            level = get_level_from_mpr(mpr_value)

        elif "mickey" in game_lower:
            mpr_value = player_stats.get("moyenne_mpr_mickey", player_stats.get("mpr_moyen_mickey", 0.0))
            level = get_level_from_mpr(mpr_value)

        elif "highscore" in game_lower:
            level = get_level_from_ppd(average_ppd_or_others(player_stats, "highscore"))


        else:
            # Ho-One / X01
            level = get_level_from_ppd(average_ppd_or_others(player_stats, "ho-one"))

        # Chargement de l'image correspondante
        logo_filename = f"{level}.png"
        logo_path = os.path.join(BASE_DIR, "images_trophees", "logos", logo_filename)

        if os.path.exists(logo_path):
            logo_img = pygame.image.load(logo_path).convert_alpha()

            # Redimensionnement basé sur le ratio d'origine (136x52)
            orig_w, orig_h = 136, 52
            target_height = int(32 * scale)
            target_width = int(target_height * (orig_w / orig_h))

            logo_img = pygame.transform.smoothscale(logo_img, (target_width, target_height))
            return logo_img
        else:
            return None

    except Exception as e:
        print(f"[DEBUG LOGO] -> Erreur critique : {e}")
        return None

class PlayerSelectionScreen:
    def __init__(self, screen, rpi=None):
        self.screen = screen
        self.rpi = rpi
        self.selected_index = 0
        self.popup_scroll_offset = 0

    def run(self):
        clock = pygame.time.Clock()
        width, height = self.screen.get_size()
        scale = ui_scale(self.screen)

        try:
            title_font = cfonts.font(int(35 * scale), bold=True)
            text_font = cfonts.font(int(22 * scale))
            bold_font = cfonts.font(int(22 * scale), bold=True)
            footer_font = cfonts.font(int(19 * scale))
            small_font = cfonts.font(int(16 * scale))
            tiny_font = cfonts.font(int(15 * scale))
            error_font = cfonts.font(int(20 * scale))
            confirm_font = cfonts.font(int(24 * scale), bold=True)
        except Exception:
            title_font = pygame.font.Font(None, 35)
            text_font = pygame.font.Font(None, 22)
            bold_font = pygame.font.Font(None, 22)
            footer_font = pygame.font.Font(None, 16)
            small_font = pygame.font.Font(None, 12)
            tiny_font = pygame.font.Font(None, 11)
            error_font = pygame.font.Font(None, 20)
            confirm_font = pygame.font.Font(None, 24)

        max_visible_items = 6
        running = True

        # États : "NORMAL", "INFO_POPUP", "SELECT_MERGE_TARGET", "CONFIRM_MERGE", "CONFIRM_DELETE"
        screen_state = "NORMAL"
        player_target = None
        target_base_name = None
        confirm_choice = 0

        # Variables pour le choix du joueur cible lors de la fusion
        merge_candidates = []
        merge_target_index = 0
        merge_target_rects = []

        # Seuils PPD et MPR (30 niveaux)
        ppd_thresholds_list = [
            "<10.64", "<11.89", "<13.14", "<14.39", "<15.64", "<16.89", "<18.14", "<19.44", "<20.74", "<22.04",
            "<23.34", "<24.64", "<25.94", "<27.29", "<28.64", "<29.99", "<31.34", "<32.69", "<34.04", "<35.39",
            "<36.79", "<38.19", "<39.59", "<40.99", "<42.39", "<43.79", "<45.19", "<46.59", "<47.99", ">47.99"
        ]
        mpr_thresholds_list = [
            "<1.09", "<1.19", "<1.30", "<1.45", "<1.60", "<1.75", "<1.90", "<2.05", "<2.20", "<2.35",
            "<2.50", "<2.65", "<2.80", "<2.95", "<3.10", "<3.25", "<3.40", "<3.56", "<3.70", "<3.85",
            "<4.06", "<4.27", "<4.48", "<4.69", "<4.95", "<5.21", "<5.47", "<5.73", "<5.99", ">5.99"
        ]

        while running:
            players = load_favorite_names()
            total_players = len(players)

            if total_players > 0:
                self.selected_index = self.selected_index % total_players
            else:
                self.selected_index = 0

            self.screen.fill((20, 24, 33))

            title_text = shrink(title_font.render(tr("CHOISIR UN JOUEUR"), True, (255, 255, 255)), width - int(40 * scale))
            title_rect = title_text.get_rect(center=(width // 2, int(45 * scale)))
            self.screen.blit(title_text, title_rect)

            player_rects = []
            all_data = load_player_data()

            if total_players == 0:
                err_surf = error_font.render(tr("Erreur : Aucun joueur trouvé dans '{0}'.", DATA_FILE), True, (255, 100, 100))
                err_rect = err_surf.get_rect(center=(width // 2, height // 2))
                self.screen.blit(err_surf, err_rect)
            else:
                start_offset = 0
                if total_players > max_visible_items:
                    start_offset = self.selected_index - (max_visible_items // 2)
                    if start_offset < 0:
                        start_offset = 0
                    elif start_offset > total_players - max_visible_items:
                        start_offset = total_players - max_visible_items

                end_offset = min(start_offset + max_visible_items, total_players)
                visible_players = players[start_offset:end_offset]

                # --- TABLEAU DE SÉLECTION PRINCIPAL ---
                table_width = int(1100 * scale)
                table_x = (width - table_width) // 2
                start_y = int(100 * scale)

                header_rect = pygame.Rect(table_x, start_y, table_width, int(40 * scale))
                pygame.draw.rect(self.screen, (45, 55, 75), header_rect, border_radius=6)
                pygame.draw.rect(self.screen, (90, 110, 150), header_rect, 1, border_radius=6)

                col_name_center = table_x + int(110 * scale)
                col_hoone_center = table_x + int(360 * scale)
                col_highscore_center = table_x + int(590 * scale)
                col_cricket_center = table_x + int(820 * scale)
                col_mickey_center = table_x + int(1010 * scale)

                headers = [
                    (tr("NOM DU JOUEUR"), col_name_center),
                    ("PPD (Ho-One)", col_hoone_center),
                    ("PPD (Highscore)", col_highscore_center),
                    ("MPR (Cricket)", col_cricket_center),
                    ("MPR (Mickey)", col_mickey_center)
                ]

                for h_text, h_x in headers:
                    h_surf = shrink(bold_font.render(h_text, True, (255, 200, 50)), int(180 * scale))
                    self.screen.blit(h_surf, (h_x - h_surf.get_width() // 2, start_y + int(10 * scale)))

                row_y = start_y + int(48 * scale)
                row_height = int(68 * scale)

                blink_factor = abs((pygame.time.get_ticks() // 300) % 2)

                for idx, player_name in enumerate(visible_players):
                    real_index = start_offset + idx
                    is_highlighted = (real_index == self.selected_index)

                    r_rect = pygame.Rect(table_x, row_y, table_width, row_height)
                    player_rects.append((r_rect, real_index))

                    if is_highlighted:
                        bg_color = (65, 85, 125) if blink_factor == 1 else (45, 60, 95)
                        border_color = (255, 220, 100) if blink_factor == 1 else (100, 150, 255)
                        border_w = int(3 * scale)
                    else:
                        bg_color = (30, 36, 48)
                        border_color = (50, 60, 80)
                        border_w = 1

                    pygame.draw.rect(self.screen, bg_color, r_rect, border_radius=6)
                    pygame.draw.rect(self.screen, border_color, r_rect, border_w, border_radius=6)

                    name_color = (255, 255, 255) if is_highlighted else (210, 215, 225)
                    name_surf = shrink(bold_font.render(player_name.upper(), True, name_color), int(200 * scale))
                    self.screen.blit(name_surf, (col_name_center - name_surf.get_width() // 2, row_y + (row_height - name_surf.get_height()) // 2))

                    p_content = next((v for k, v in all_data.items() if k.strip().lower() == player_name.strip().lower()), {})
                    p_st = p_content.get("stats", {}) if isinstance(p_content, dict) else {}

                    # Ho-One
                    ppd_val = average_ppd(p_st, "ho-one")
                    lvl_num = get_level_from_ppd(ppd_val)
                    rank_name = level_text(NAMES_LEVELS.get(lvl_num, "Débutant"))
                    score_hoone_surf = small_font.render(f"{ppd_val:.2f}".replace('.', ','), True, (0, 220, 255))
                    level_text_surf = tiny_font.render(rank_name, True, (180, 190, 210))
                    logo_hoone = get_player_logo(player_name, scale, game_type="ho-one", all_players_data=all_data)
                    if ppd_val == 0.0:
                        logo_hoone = None

                    if logo_hoone:
                        spacing = int(6 * scale)
                        combined_w = logo_hoone.get_width() + spacing + score_hoone_surf.get_width()
                        block_left_x = col_hoone_center - combined_w // 2
                        top_h = max(logo_hoone.get_height(), score_hoone_surf.get_height())
                        inner_spacing = int(3 * scale)
                        text_h = level_text_surf.get_height()
                        total_content_h = top_h + inner_spacing + text_h
                        block_y = row_y + (row_height - total_content_h) // 2
                        self.screen.blit(logo_hoone, (block_left_x, block_y))
                        score_y = block_y + (logo_hoone.get_height() - score_hoone_surf.get_height()) // 2 + int(6 * scale)
                        self.screen.blit(score_hoone_surf, (block_left_x + logo_hoone.get_width() + spacing, score_y))
                        text_x = block_left_x + (logo_hoone.get_width() - level_text_surf.get_width()) // 2
                        self.screen.blit(level_text_surf, (text_x, block_y + top_h + inner_spacing))
                    else:
                        no_logo_text = tiny_font.render(tr("Débutant"), True, (150, 150, 150))
                        fallback_spacing = int(2 * scale)
                        fallback_total_h = no_logo_text.get_height() + fallback_spacing + score_hoone_surf.get_height()
                        fallback_y = row_y + (row_height - fallback_total_h) // 2
                        self.screen.blit(no_logo_text, (col_hoone_center - no_logo_text.get_width() // 2, fallback_y))
                        self.screen.blit(score_hoone_surf, (col_hoone_center - score_hoone_surf.get_width() // 2, fallback_y + no_logo_text.get_height() + fallback_spacing))

                    # Highscore
                    ppd_hs_val = average_ppd(p_st, "highscore")
                    score_hs_surf = small_font.render(f"{ppd_hs_val:.2f}".replace('.', ','), True, (0, 220, 255))
                    level_text_hs_surf = tiny_font.render(level_text(NAMES_LEVELS.get(get_level_from_ppd(ppd_hs_val), "")), True, (180, 190, 210))
                    logo_hs = get_player_logo(player_name, scale, game_type="highscore", all_players_data=all_data)
                    if ppd_hs_val == 0.0:
                        logo_hs = None
                    if logo_hs:
                        spacing = int(6 * scale)
                        combined_w = logo_hs.get_width() + spacing + score_hs_surf.get_width()
                        block_left_x = col_highscore_center - combined_w // 2
                        top_h = max(logo_hs.get_height(), score_hs_surf.get_height())
                        inner_spacing = int(3 * scale)
                        text_h = level_text_hs_surf.get_height()
                        total_content_h = top_h + inner_spacing + text_h
                        block_y = row_y + (row_height - total_content_h) // 2
                        self.screen.blit(logo_hs, (block_left_x, block_y))
                        score_y = block_y + (logo_hs.get_height() - score_hs_surf.get_height()) // 2 + int(6 * scale)
                        self.screen.blit(score_hs_surf, (block_left_x + logo_hs.get_width() + spacing, score_y))
                        text_x = block_left_x + (logo_hs.get_width() - level_text_hs_surf.get_width()) // 2
                        self.screen.blit(level_text_hs_surf, (text_x, block_y + top_h + inner_spacing))
                    else:
                        self.screen.blit(score_hs_surf, (col_highscore_center - score_hs_surf.get_width() // 2, row_y + (row_height - score_hs_surf.get_height()) // 2))

                    # Cricket
                    mpr_val = p_st.get('moyenne_mpr_cricket', p_st.get('mpr_moyen_cricket', 0.0))
                    score_cricket_surf = small_font.render(f"{mpr_val:.2f}".replace('.', ','), True, (0, 220, 255))
                    level_text_c_surf = tiny_font.render(level_text(NAMES_LEVELS.get(get_level_from_mpr(mpr_val), "")), True, (180, 190, 210))
                    logo_cricket = get_player_logo(player_name, scale, game_type="cricket", all_players_data=all_data)
                    if mpr_val == 0.0:
                        logo_cricket = None
                    if logo_cricket:
                        spacing = int(6 * scale)
                        combined_w = logo_cricket.get_width() + spacing + score_cricket_surf.get_width()
                        block_left_x = col_cricket_center - combined_w // 2
                        top_h = max(logo_cricket.get_height(), score_cricket_surf.get_height())
                        inner_spacing = int(3 * scale)
                        text_h = level_text_c_surf.get_height()
                        total_content_h = top_h + inner_spacing + text_h
                        block_y = row_y + (row_height - total_content_h) // 2
                        self.screen.blit(logo_cricket, (block_left_x, block_y))
                        score_y = block_y + (logo_cricket.get_height() - score_cricket_surf.get_height()) // 2 + int(6 * scale)
                        self.screen.blit(score_cricket_surf, (block_left_x + logo_cricket.get_width() + spacing, score_y))
                        text_x = block_left_x + (logo_cricket.get_width() - level_text_c_surf.get_width()) // 2
                        self.screen.blit(level_text_c_surf, (text_x, block_y + top_h + inner_spacing))
                    else:
                        self.screen.blit(score_cricket_surf, (col_cricket_center - score_cricket_surf.get_width() // 2, row_y + (row_height - score_cricket_surf.get_height()) // 2))

                    # Mickey
                    mpr_m_val = p_st.get('moyenne_mpr_mickey', p_st.get('mpr_moyen_mickey', 0.0))
                    score_mickey_surf = small_font.render(f"{mpr_m_val:.2f}".replace('.', ','), True, (0, 220, 255))
                    level_text_m_surf = tiny_font.render(level_text(NAMES_LEVELS.get(get_level_from_mpr(mpr_m_val), "")), True, (180, 190, 210))
                    logo_mickey = get_player_logo(player_name, scale, game_type="mickey", all_players_data=all_data)
                    if mpr_m_val == 0.0:
                        logo_mickey = None
                    if logo_mickey:
                        spacing = int(6 * scale)
                        combined_w = logo_mickey.get_width() + spacing + score_mickey_surf.get_width()
                        block_left_x = col_mickey_center - combined_w // 2
                        top_h = max(logo_mickey.get_height(), score_mickey_surf.get_height())
                        inner_spacing = int(3 * scale)
                        text_h = level_text_m_surf.get_height()
                        total_content_h = top_h + inner_spacing + text_h
                        block_y = row_y + (row_height - total_content_h) // 2
                        self.screen.blit(logo_mickey, (block_left_x, block_y))
                        score_y = block_y + (logo_mickey.get_height() - score_mickey_surf.get_height()) // 2 + int(6 * scale)
                        self.screen.blit(score_mickey_surf, (block_left_x + logo_mickey.get_width() + spacing, score_y))
                        text_x = block_left_x + (logo_mickey.get_width() - level_text_m_surf.get_width()) // 2
                        self.screen.blit(level_text_m_surf, (text_x, block_y + top_h + inner_spacing))
                    else:
                        self.screen.blit(score_mickey_surf, (col_mickey_center - score_mickey_surf.get_width() // 2, row_y + (row_height - score_mickey_surf.get_height()) // 2))

                    row_y += row_height + int(8 * scale)

                if total_players > max_visible_items:
                    scroll_info = f"({self.selected_index + 1} / {total_players})"
                    scroll_surf = footer_font.render(scroll_info, True, (120, 130, 150))
                    scroll_rect = scroll_surf.get_rect(center=(width // 2, height - int(75 * scale)))
                    self.screen.blit(scroll_surf, scroll_rect)

            btn_cancel_rect = None
            btn_conf_rect = None
            merge_target_rects = []

            # --- POP-UP D'INFORMATIONS ---
            if screen_state == "INFO_POPUP":
                overlay = pygame.Surface((width, height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 190))
                self.screen.blit(overlay, (0, 0))

                box_w = int(1240 * scale)
                box_h = int(720 * scale)
                box_x = (width - box_w) // 2
                box_y = (height - box_h) // 2
                box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

                pygame.draw.rect(self.screen, (25, 32, 48), box_rect, border_radius=12)
                pygame.draw.rect(self.screen, (0, 220, 255), box_rect, 3, border_radius=12)

                p_content = next((v for k, v in all_data.items() if k.strip().lower() == player_target.strip().lower()), {})
                p_st = p_content.get("stats", {}) if isinstance(p_content, dict) else {}

                user_ppd_hoone = average_ppd(p_st, "ho-one")
                user_ppd_hs = average_ppd(p_st, "highscore")
                user_mpr_cricket = p_st.get('moyenne_mpr_cricket', p_st.get('mpr_moyen_cricket', 0.0))
                user_mpr_mickey = p_st.get('moyenne_mpr_mickey', p_st.get('mpr_moyen_mickey', 0.0))

                lvl_hoone = get_level_from_ppd(user_ppd_hoone)
                lvl_hs = get_level_from_ppd(user_ppd_hs)
                lvl_cricket = get_level_from_mpr(user_mpr_cricket)
                lvl_mickey = get_level_from_mpr(user_mpr_mickey)

                name_hoone = level_text(NAMES_LEVELS.get(lvl_hoone, "Débutant"))
                name_hs = level_text(NAMES_LEVELS.get(lvl_hs, "Débutant"))
                name_cricket = level_text(NAMES_LEVELS.get(lvl_cricket, "Débutant"))
                name_mickey = level_text(NAMES_LEVELS.get(lvl_mickey, "Débutant"))

                info_title = shrink(confirm_font.render(tr("TABLEAU DES NIVEAUX - PROFIL DE {player}", player=player_target.upper()), True, (255, 220, 50)), box_w - int(30 * scale))
                self.screen.blit(info_title, info_title.get_rect(center=(box_x + box_w // 2, box_y + int(25 * scale))))

                sub_title_font = cfonts.font(int(15 * scale), bold=True) if hasattr(cfonts, 'font') else pygame.font.Font(None, 18)

                sub_col_w = int(270 * scale)
                col_gap = int(10 * scale)
                block_w = (sub_col_w * 2) + col_gap

                total_content_w = (block_w * 2) + int(40 * scale)
                start_x_blocks = box_x + (box_w - total_content_w) // 2

                main_col1_x = start_x_blocks
                main_col2_x = main_col1_x + block_w + int(40 * scale)

                frame_padding = int(10 * scale)
                frame_y = box_y + int(52 * scale)
                frame_h = int(605 * scale)
                frame_rect1 = pygame.Rect(main_col1_x - frame_padding, frame_y, block_w + (frame_padding * 2), frame_h)
                frame_rect2 = pygame.Rect(main_col2_x - frame_padding, frame_y, block_w + (frame_padding * 2), frame_h)

                pygame.draw.rect(self.screen, (0, 220, 255), frame_rect1, 2, border_radius=8)
                pygame.draw.rect(self.screen, (0, 220, 255), frame_rect2, 2, border_radius=8)

                head1 = shrink(sub_title_font.render(tr("Points Par Flèche (PPD)"), True, (0, 220, 255)), block_w)
                head2 = shrink(sub_title_font.render(tr("Mark Per Round (MPR)"), True, (0, 220, 255)), block_w)

                self.screen.blit(head1, (main_col1_x + (block_w - head1.get_width()) // 2, box_y + int(60 * scale)))
                self.screen.blit(head2, (main_col2_x + (block_w - head2.get_width()) // 2, box_y + int(60 * scale)))

                subhead_hoone = shrink(tiny_font.render(f"Ho-one - {tr("Nv")} {lvl_hoone} : {user_ppd_hoone:.2f} - {name_hoone}", True, (255, 200, 50)), sub_col_w - int(6 * scale))
                subhead_hs = shrink(tiny_font.render(f"Highscore - {tr("Nv")} {lvl_hs} : {user_ppd_hs:.2f} - {name_hs}", True, (255, 200, 50)), sub_col_w - int(6 * scale))
                subhead_cricket = shrink(tiny_font.render(f"Cricket - {tr("Nv")} {lvl_cricket} : {user_mpr_cricket:.2f} - {name_cricket}", True, (255, 200, 50)), sub_col_w - int(6 * scale))
                subhead_mickey = shrink(tiny_font.render(f"Mickey - {tr("Nv")} {lvl_mickey} : {user_mpr_mickey:.2f} - {name_mickey}", True, (255, 200, 50)), sub_col_w - int(6 * scale))

                col_hoone_x = main_col1_x
                col_hs_x = main_col1_x + sub_col_w + col_gap
                col_cricket_x = main_col2_x
                col_mickey_x = main_col2_x + sub_col_w + col_gap

                self.screen.blit(subhead_hoone, (col_hoone_x + (sub_col_w - subhead_hoone.get_width()) // 2, box_y + int(85 * scale)))
                self.screen.blit(subhead_hs, (col_hs_x + (sub_col_w - subhead_hs.get_width()) // 2, box_y + int(85 * scale)))
                self.screen.blit(subhead_cricket, (col_cricket_x + (sub_col_w - subhead_cricket.get_width()) // 2, box_y + int(85 * scale)))
                self.screen.blit(subhead_mickey, (col_mickey_x + (sub_col_w - subhead_mickey.get_width()) // 2, box_y + int(85 * scale)))

                list_area_y = box_y + int(115 * scale)
                list_area_h = int(530 * scale)

                old_clip = self.screen.get_clip()
                clip_rect = pygame.Rect(box_x + int(15 * scale), list_area_y, box_w - int(30 * scale), list_area_h)
                self.screen.set_clip(clip_rect)

                is_blink = (pygame.time.get_ticks() // 300) % 2 == 0
                row_h = int(34 * scale)

                def draw_sub_column(start_x, thresholds, user_lvl):
                    for lvl in range(1, 31):
                        ry = list_area_y + (lvl - 1) * row_h - self.popup_scroll_offset
                        r_box = pygame.Rect(start_x, ry, sub_col_w, row_h - int(4 * scale))

                        is_current = (lvl == user_lvl)
                        if is_current:
                            if is_blink:
                                row_bg = (70, 110, 160)
                                border_col = (255, 220, 50)
                            else:
                                row_bg = (40, 60, 95)
                                border_col = (0, 255, 150)
                        else:
                            row_bg = (32, 40, 56) if lvl % 2 == 0 else (28, 35, 48)
                            border_col = (50, 65, 90)

                        pygame.draw.rect(self.screen, row_bg, r_box, border_radius=4)
                        pygame.draw.rect(self.screen, border_col, r_box, 1, border_radius=4)

                        lvl_label = f"{tr('Niv')} {lvl:2d} :"
                        seuil_str = thresholds[lvl - 1]
                        rank_title = level_text(NAMES_LEVELS.get(lvl, "Amateur"))

                        line_str = f"{lvl_label} {seuil_str} {rank_title}"
                        # Room left by the logo at the end of the line
                        line_txt = shrink(small_font.render(line_str, True, (255, 255, 255) if not is_current else (255, 230, 100)),
                                          sub_col_w - int(40 * scale))

                        text_y = r_box.y + (r_box.height - line_txt.get_height()) // 2
                        self.screen.blit(line_txt, (r_box.x + int(6 * scale), text_y))

                        logo_filename = f"{lvl}.png"
                        logo_path = os.path.join(BASE_DIR, "images_trophees", "logos", logo_filename)
                        if os.path.exists(logo_path):
                            try:
                                l_img = pygame.image.load(logo_path).convert_alpha()
                                target_h = int(18 * scale)
                                target_w = int(target_h * (136 / 52))
                                l_img = pygame.transform.smoothscale(l_img, (target_w, target_h))
                                text_end_x = r_box.x + int(6 * scale) + line_txt.get_width() + int(4 * scale)
                                logo_y = r_box.y + (r_box.height - target_h) // 2
                                self.screen.blit(l_img, (text_end_x, logo_y))
                            except Exception:
                                pass

                draw_sub_column(col_hoone_x, ppd_thresholds_list, lvl_hoone)
                draw_sub_column(col_hs_x, ppd_thresholds_list, lvl_hs)
                draw_sub_column(col_cricket_x, mpr_thresholds_list, lvl_cricket)
                draw_sub_column(col_mickey_x, mpr_thresholds_list, lvl_mickey)

                self.screen.set_clip(old_clip)

            # --- POP-UP DE CHOIX DU JOUEUR CIBLE POUR LA FUSION ---
            elif screen_state == "SELECT_MERGE_TARGET":
                overlay = pygame.Surface((width, height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 175))
                self.screen.blit(overlay, (0, 0))

                box_w = int(680 * scale)
                box_h = int(520 * scale)
                box_x = (width - box_w) // 2
                box_y = (height - box_h) // 2
                box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

                pygame.draw.rect(self.screen, (30, 38, 54), box_rect, border_radius=12)
                pygame.draw.rect(self.screen, (0, 220, 255), box_rect, 3, border_radius=12)

                m_title = confirm_font.render(tr("FUSIONNER '{player}' AVEC :", player=player_target.upper()), True, (255, 220, 50))
                self.screen.blit(m_title, m_title.get_rect(center=(box_x + box_w // 2, box_y + int(32 * scale))))

                if not merge_candidates:
                    empty_surf = text_font.render(tr("Aucun autre joueur disponible."), True, (220, 100, 100))
                    self.screen.blit(empty_surf, empty_surf.get_rect(center=(box_x + box_w // 2, box_y + box_h // 2)))
                else:
                    max_m_vis = 6
                    m_start = 0
                    if len(merge_candidates) > max_m_vis:
                        m_start = max(0, min(merge_target_index - (max_m_vis // 2), len(merge_candidates) - max_m_vis))
                    m_end = min(m_start + max_m_vis, len(merge_candidates))

                    item_w = int(560 * scale)
                    item_h = int(52 * scale)
                    item_x = box_x + (box_w - item_w) // 2
                    cur_y = box_y + int(75 * scale)

                    for i in range(m_start, m_end):
                        cand_name = merge_candidates[i]
                        is_sel = (i == merge_target_index)
                        ir = pygame.Rect(item_x, cur_y, item_w, item_h)
                        merge_target_rects.append((ir, i))

                        bg_c = (60, 90, 140) if is_sel else (40, 48, 66)
                        bd_c = (0, 220, 255) if is_sel else (70, 85, 110)
                        pygame.draw.rect(self.screen, bg_c, ir, border_radius=8)
                        pygame.draw.rect(self.screen, bd_c, ir, int(2.5 * scale) if is_sel else 1, border_radius=8)

                        c_surf = bold_font.render(cand_name.upper(), True, (255, 255, 255) if is_sel else (200, 210, 225))
                        self.screen.blit(c_surf, c_surf.get_rect(center=ir.center))
                        cur_y += item_h + int(8 * scale)

                hint_m = small_font.render(tr("HAUT/BAS : Choisir | ENTRÉE : Valider | ÉCHAP : Annuler"), True, (170, 185, 210))
                self.screen.blit(hint_m, hint_m.get_rect(center=(box_x + box_w // 2, box_y + box_h - int(25 * scale))))

            # --- POP-UP DE CONFIRMATION DE SUPPRESSION ---
            elif screen_state == "CONFIRM_DELETE":
                overlay = pygame.Surface((width, height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                self.screen.blit(overlay, (0, 0))

                box_w = int(600 * scale)
                box_h = int(250 * scale)
                box_x = (width - box_w) // 2
                box_y = (height - box_h) // 2
                box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

                pygame.draw.rect(self.screen, (35, 42, 60), box_rect, border_radius=12)
                pygame.draw.rect(self.screen, (220, 80, 80), box_rect, 3, border_radius=12)

                msg_text = tr("Effacer le joueur '{player}' ?", player=player_target) if player_target else tr("Effacer le joueur ?")
                msg_surf = confirm_font.render(msg_text, True, (255, 255, 255))
                self.screen.blit(msg_surf, (box_x + (box_w - msg_surf.get_width()) // 2, box_y + int(35 * scale)))

                sub_msg = small_font.render(tr("Cette action est irréversible (stats & trophées perdus)."), True, (200, 180, 180))
                self.screen.blit(sub_msg, (box_x + (box_w - sub_msg.get_width()) // 2, box_y + int(75 * scale)))

                btn_w = int(220 * scale)
                btn_h = int(50 * scale)
                btn_y = box_y + int(145 * scale)

                btn_cancel_rect = pygame.Rect(box_x + int(50 * scale), btn_y, btn_w, btn_h)
                c_bg = (70, 85, 110) if confirm_choice == 0 else (45, 55, 75)
                c_border = (120, 160, 220) if confirm_choice == 0 else (70, 85, 110)
                pygame.draw.rect(self.screen, c_bg, btn_cancel_rect, border_radius=8)
                pygame.draw.rect(self.screen, c_border, btn_cancel_rect, 2, border_radius=8)
                txt_cancel = bold_font.render(tr("ANNULER"), True, (255, 255, 255))
                self.screen.blit(txt_cancel, txt_cancel.get_rect(center=btn_cancel_rect.center))

                btn_conf_rect = pygame.Rect(box_x + box_w - btn_w - int(50 * scale), btn_y, btn_w, btn_h)
                f_bg = (200, 60, 60) if confirm_choice == 1 else (120, 40, 40)
                f_border = (255, 120, 120) if confirm_choice == 1 else (180, 60, 60)
                pygame.draw.rect(self.screen, f_bg, btn_conf_rect, border_radius=8)
                pygame.draw.rect(self.screen, f_border, btn_conf_rect, 2, border_radius=8)
                txt_conf = bold_font.render(tr("EFFACER"), True, (255, 255, 255))
                self.screen.blit(txt_conf, txt_conf.get_rect(center=btn_conf_rect.center))

            # --- POP-UP DE CONFIRMATION DE FUSION ---
            elif screen_state == "CONFIRM_MERGE":
                overlay = pygame.Surface((width, height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                self.screen.blit(overlay, (0, 0))

                box_w = int(750 * scale)
                box_h = int(260 * scale)
                box_x = (width - box_w) // 2
                box_y = (height - box_h) // 2
                box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

                pygame.draw.rect(self.screen, (35, 42, 60), box_rect, border_radius=12)
                pygame.draw.rect(self.screen, (100, 180, 255), box_rect, 3, border_radius=12)

                msg_text = tr("pseudo : {player} va être fusionné", player=player_target)
                msg_surf = confirm_font.render(msg_text, True, (255, 255, 255))
                self.screen.blit(msg_surf, (box_x + (box_w - msg_surf.get_width()) // 2, box_y + int(30 * scale)))

                msg_text2 = tr("avec pseudo : {player}", player=target_base_name)
                msg_surf2 = confirm_font.render(msg_text2, True, (0, 220, 255))
                self.screen.blit(msg_surf2, (box_x + (box_w - msg_surf2.get_width()) // 2, box_y + int(70 * scale)))

                btn_w = int(220 * scale)
                btn_h = int(50 * scale)
                btn_y = box_y + int(155 * scale)

                btn_cancel_rect = pygame.Rect(box_x + int(50 * scale), btn_y, btn_w, btn_h)
                c_bg = (70, 85, 110) if confirm_choice == 0 else (45, 55, 75)
                c_border = (120, 160, 220) if confirm_choice == 0 else (70, 85, 110)
                pygame.draw.rect(self.screen, c_bg, btn_cancel_rect, border_radius=8)
                pygame.draw.rect(self.screen, c_border, btn_cancel_rect, 2, border_radius=8)
                txt_cancel = bold_font.render(tr("ANNULER"), True, (255, 255, 255))
                self.screen.blit(txt_cancel, txt_cancel.get_rect(center=btn_cancel_rect.center))

                btn_conf_rect = pygame.Rect(box_x + box_w - btn_w - int(50 * scale), btn_y, btn_w, btn_h)
                f_bg = (60, 160, 100) if confirm_choice == 1 else (40, 100, 60)
                f_border = (120, 220, 160) if confirm_choice == 1 else (60, 140, 90)
                pygame.draw.rect(self.screen, f_bg, btn_conf_rect, border_radius=8)
                pygame.draw.rect(self.screen, f_border, btn_conf_rect, 2, border_radius=8)
                txt_conf = bold_font.render(tr("FUSIONNER"), True, (255, 255, 255))
                self.screen.blit(txt_conf, txt_conf.get_rect(center=btn_conf_rect.center))

            footer_text_str = tr("HAUT/BAS : Naviguer | GAUCHE/DROITE : Infos Joueur | ENTRÉE : Valider | M : Fusion | S : Supprimer | ÉCHAP : Quitter")
            if screen_state in ("CONFIRM_DELETE", "CONFIRM_MERGE"):
                footer_text_str = tr("GAUCHE/DROITE : Choisir | ENTRÉE : Valider | ÉCHAP : Annuler")
            elif screen_state == "SELECT_MERGE_TARGET":
                footer_text_str = tr("HAUT/BAS : Choisir la cible | ENTRÉE : Confirmer | ÉCHAP : Annuler")
            elif screen_state == "INFO_POPUP":
                footer_text_str = tr("HAUT/BAS : Défiler le tableau | GAUCHE/DROITE (ou ÉCHAP) : Fermer le popup")

            # The commands as buttons (a mouse, a touchscreen) : Retour and, for the player
            # chosen, its information, the merge, the deletion
            action_rects = {}
            buttons_h = int(44 * scale)
            buttons_y = height - buttons_h - int(14 * scale)
            if screen_state == "NORMAL":
                action_rects['back'] = draw_button(self.screen, (int(30 * scale), buttons_y, int(170 * scale), buttons_h), tr("Retour"), footer_font)
                if total_players > 0:
                    button_w = int(190 * scale)
                    right = width - int(30 * scale)
                    for name, text in (('delete', tr("Supprimer")), ('merge', tr("Fusionner")), ('info', tr("Infos joueur"))):
                        right -= button_w
                        action_rects[name] = draw_button(self.screen, (right, buttons_y, button_w, buttons_h), text, footer_font)
                        right -= int(12 * scale)
                footer_y = buttons_y - int(26 * scale)
            else:
                footer_y = height - int(35 * scale)
            footer_text = footer_font.render(footer_text_str, True, (150, 150, 150))
            # Over the buttons, its bottom above them (its middle was set : a high font went on
            # them), as wide as the screen allows (smaller as a whole, not squeezed)
            if screen_state == "NORMAL":
                room = pygame.Rect(int(20 * scale), buttons_y - int(6 * scale) - int(34 * scale), width - int(40 * scale), int(34 * scale))
            else:
                room = pygame.Rect(int(20 * scale), height - int(52 * scale), width - int(40 * scale), int(34 * scale))
            footer_rect = fit_text(footer_text, room, smallest=0.3)
            if footer_rect is not None:
                self.screen.blit(pygame.transform.smoothscale(footer_text, footer_rect.size), footer_rect)

            pygame.display.flip()

            action_pressed = None
            navigation = 0
            horizontal_nav = 0
            trigger_delete_popup = False
            trigger_merge_popup = False
            toggle_info_popup = False
            popup_scroll_change = 0
            merge_nav = 0
            merge_confirm_target = False
            # The clicks and touches of this turn (pygame, listen_inputs)
            clicks = []

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "QUIT", None
                elif event.type == pygame.MOUSEWHEEL:
                    if screen_state == "INFO_POPUP":
                        self.popup_scroll_offset -= event.y * 30
                        if self.popup_scroll_offset < 0:
                            self.popup_scroll_offset = 0
                        max_s = max(0, (30 * int(34 * scale)) - int(490 * scale))
                        if self.popup_scroll_offset > max_s:
                            self.popup_scroll_offset = max_s
                    elif screen_state == "SELECT_MERGE_TARGET" and len(merge_candidates) > 0:
                        merge_target_index = (merge_target_index - event.y) % len(merge_candidates)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicks.append(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if screen_state in ("CONFIRM_DELETE", "CONFIRM_MERGE", "INFO_POPUP", "SELECT_MERGE_TARGET"):
                            screen_state = "NORMAL"
                        else:
                            return "QUIT", None
                    elif event.key == pygame.K_DOWN:
                        if screen_state == "NORMAL":
                            navigation = 1
                        elif screen_state == "INFO_POPUP":
                            popup_scroll_change = int(170 * scale)
                        elif screen_state == "SELECT_MERGE_TARGET":
                            merge_nav = 1
                    elif event.key == pygame.K_UP:
                        if screen_state == "NORMAL":
                            navigation = -1
                        elif screen_state == "INFO_POPUP":
                            popup_scroll_change = int(-170 * scale)
                        elif screen_state == "SELECT_MERGE_TARGET":
                            merge_nav = -1
                    elif event.key in (pygame.K_RIGHT, pygame.K_LEFT):
                        if screen_state == "NORMAL" and total_players > 0:
                            toggle_info_popup = True
                            self.popup_scroll_offset = 0
                        elif screen_state == "INFO_POPUP":
                            screen_state = "NORMAL"
                        elif screen_state in ("CONFIRM_DELETE", "CONFIRM_MERGE"):
                            horizontal_nav = 1 if event.key == pygame.K_RIGHT else -1
                    elif event.key == pygame.K_RETURN:
                        if screen_state == "INFO_POPUP":
                            screen_state = "NORMAL"
                        elif screen_state == "SELECT_MERGE_TARGET":
                            merge_confirm_target = True
                        else:
                            action_pressed = "SELECT"
                    elif event.key == pygame.K_s:
                        if screen_state == "NORMAL" and total_players > 0:
                            trigger_delete_popup = True
                    elif event.key in (pygame.K_f, pygame.K_m):
                        if screen_state == "NORMAL" and total_players > 0:
                            trigger_merge_popup = True

            if self.rpi and hasattr(self.rpi, "listen_inputs"):
                try:
                    inp = self.rpi.listen_inputs()
                    if click_of(inp) is not None:
                        clicks.append(click_of(inp))
                    elif inp:
                        key_str = str(inp).strip()
                        if key_str in UP_KEYS:
                            if screen_state == "NORMAL":
                                navigation = -1
                            elif screen_state == "INFO_POPUP":
                                popup_scroll_change = int(-170 * scale)
                            elif screen_state == "SELECT_MERGE_TARGET":
                                merge_nav = -1
                        elif key_str in DOWN_KEYS:
                            if screen_state == "NORMAL":
                                navigation = 1
                            elif screen_state == "INFO_POPUP":
                                popup_scroll_change = int(170 * scale)
                            elif screen_state == "SELECT_MERGE_TARGET":
                                merge_nav = 1
                        elif key_str in RIGHT_KEYS + LEFT_KEYS:
                            if screen_state == "NORMAL" and total_players > 0:
                                toggle_info_popup = True
                                self.popup_scroll_offset = 0
                            elif screen_state == "INFO_POPUP":
                                screen_state = "NORMAL"
                            elif screen_state in ("CONFIRM_DELETE", "CONFIRM_MERGE"):
                                horizontal_nav = 1
                        elif key_str in ENTER_KEYS:
                            if screen_state == "INFO_POPUP":
                                screen_state = "NORMAL"
                            elif screen_state == "SELECT_MERGE_TARGET":
                                merge_confirm_target = True
                            else:
                                action_pressed = "SELECT"
                        elif key_str in ESCAPE_KEYS:
                            if screen_state in ("CONFIRM_DELETE", "CONFIRM_MERGE", "INFO_POPUP", "SELECT_MERGE_TARGET"):
                                screen_state = "NORMAL"
                            else:
                                return "QUIT", None
                        elif key_str in DELETE_KEYS:
                            if screen_state == "NORMAL" and total_players > 0:
                                trigger_delete_popup = True
                        elif key_str in INSERT_KEYS:
                            if screen_state == "NORMAL" and total_players > 0:
                                trigger_merge_popup = True
                except Exception as e:
                    print("[ERREUR LISTEN_INPUTS] :", e)

            for mouse_pos in clicks:
                if screen_state == "NORMAL":
                    # The buttons at the bottom, then the players of the list
                    hit = next((name for name, rect in action_rects.items() if rect.collidepoint(mouse_pos)), None)
                    if hit == 'back':
                        return "QUIT", None
                    if hit == 'info':
                        toggle_info_popup = True
                        self.popup_scroll_offset = 0
                        continue
                    if hit == 'merge':
                        trigger_merge_popup = True
                        continue
                    if hit == 'delete':
                        trigger_delete_popup = True
                        continue
                    for r_rect, r_idx in player_rects:
                        if r_rect.collidepoint(mouse_pos):
                            if self.selected_index == r_idx:
                                action_pressed = "SELECT"
                            else:
                                self.selected_index = r_idx
                            break
                elif screen_state == "INFO_POPUP":
                    if btn_cancel_rect and btn_cancel_rect.collidepoint(mouse_pos):
                        screen_state = "NORMAL"
                elif screen_state == "SELECT_MERGE_TARGET":
                    for ir, m_idx in merge_target_rects:
                        if ir.collidepoint(mouse_pos):
                            merge_target_index = m_idx
                            target_base_name = merge_candidates[merge_target_index]
                            confirm_choice = 0
                            screen_state = "CONFIRM_MERGE"
                            break
                elif screen_state in ("CONFIRM_DELETE", "CONFIRM_MERGE"):
                    if btn_cancel_rect and btn_cancel_rect.collidepoint(mouse_pos):
                        screen_state = "NORMAL"
                    elif btn_conf_rect and btn_conf_rect.collidepoint(mouse_pos):
                        if screen_state == "CONFIRM_DELETE":
                            delete_player(player_target)
                            if self.selected_index >= len(players) - 1:
                                self.selected_index = max(0, len(players) - 2)
                        elif screen_state == "CONFIRM_MERGE":
                            merge_online_player_to_base(player_target, target_base_name)
                        screen_state = "NORMAL"

            if popup_scroll_change != 0 and screen_state == "INFO_POPUP":
                self.popup_scroll_offset += popup_scroll_change
                if self.popup_scroll_offset < 0:
                    self.popup_scroll_offset = 0
                max_s = max(0, (30 * int(34 * scale)) - int(490 * scale))
                if self.popup_scroll_offset > max_s:
                    self.popup_scroll_offset = max_s

            if toggle_info_popup:
                if screen_state == "NORMAL":
                    screen_state = "INFO_POPUP"
                    player_target = players[self.selected_index]
                elif screen_state == "INFO_POPUP":
                    screen_state = "NORMAL"

            if trigger_delete_popup:
                screen_state = "CONFIRM_DELETE"
                player_target = players[self.selected_index]
                confirm_choice = 0

            if trigger_merge_popup:
                player_target = players[self.selected_index]
                merge_candidates = [p for p in players if p.strip().lower() != player_target.strip().lower()]
                merge_target_index = 0
                screen_state = "SELECT_MERGE_TARGET"

            if screen_state == "NORMAL":
                if navigation != 0 and total_players > 0:
                    self.selected_index = (self.selected_index + navigation) % total_players

                if action_pressed == "SELECT" and total_players > 0:
                    chosen_player = players[self.selected_index]
                    return "SELECT", chosen_player

            elif screen_state == "SELECT_MERGE_TARGET":
                if merge_nav != 0 and len(merge_candidates) > 0:
                    merge_target_index = (merge_target_index + merge_nav) % len(merge_candidates)

                if merge_confirm_target:
                    if len(merge_candidates) > 0:
                        target_base_name = merge_candidates[merge_target_index]
                        confirm_choice = 0
                        screen_state = "CONFIRM_MERGE"
                    else:
                        screen_state = "NORMAL"

            elif screen_state in ("CONFIRM_DELETE", "CONFIRM_MERGE"):
                if horizontal_nav != 0:
                    confirm_choice = 1 - confirm_choice

                if action_pressed == "SELECT":
                    if confirm_choice == 1:
                        if screen_state == "CONFIRM_DELETE":
                            delete_player(player_target)
                            if self.selected_index >= len(players) - 1:
                                self.selected_index = max(0, len(players) - 2)
                        elif screen_state == "CONFIRM_MERGE":
                            merge_online_player_to_base(player_target, target_base_name)
                    screen_state = "NORMAL"

            clock.tick(30)

        return "QUIT", None

# --- FONCTION PRINCIPALE ---
def main(rpi=None, translate=None):
    set_translator(translate)
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)

    pygame.display.set_caption("Gestionnaire de Trophées Fléchettes")

    current_state = "PLAYER_SELECT"
    active_player = None
    active_category = None
    running = True

    while running:
        if current_state == "PLAYER_SELECT":
            selector = PlayerSelectionScreen(screen, rpi=rpi)
            action, active_player = selector.run()

            if action == "SELECT" and active_player:
                current_state = "CATEGORY_SELECT"
            else:
                running = False

        elif current_state == "CATEGORY_SELECT":
            cat_selector = CategorySelectionScreen(screen, active_player, rpi=rpi)
            action, active_category = cat_selector.run()

            if action == "SELECT" and active_category:
                if active_category == "Statistiques":
                    current_state = "STATISTICS"
                else:
                    current_state = "TROPHIES"
            elif action == "BACK":
                current_state = "PLAYER_SELECT"
            else:
                running = False

        elif current_state == "STATISTICS":
            stats_screen = StatisticsScreen(screen, current_player=active_player, rpi=rpi)
            action = stats_screen.run()

            if action == "BACK":
                current_state = "CATEGORY_SELECT"
            else:
                running = False

        elif current_state == "TROPHIES":
            trophy_screen = TrophiesScreen(screen, current_player=active_player, category=active_category, rpi=rpi)
            action = trophy_screen.run()

            if action == "BACK":
                current_state = "CATEGORY_SELECT"
            else:
                running = False


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    main()
    pygame.quit()
