# -*- coding: utf-8 -*-
"""
Yum Yum - Inspire du jeu "YUM YUM DX" des bornes DARTSLIVE

La partie se compose de N manches (8 par defaut). A chaque manche, un mini-jeu
est tire au sort parmi 20. Le ou les perdants de la manche recoivent des
"Drink Points" (penalites). La derniere manche compte double et le DEVIL MODE
peut s'activer au hasard pour un joueur (regles plus dures, penalite doublee).
Le vainqueur est celui qui a le moins de Drink Points a la fin de la partie.

En solo, chaque mini-jeu a un objectif (SOLO_GOALS) : le joueur boit s'il ne
l'atteint pas. Avec l'option choose_game, le mini-jeu de chaque manche est
choisi en lancant une flechette sur son numero (Bull = hasard).

Adaptations RaspyDarts (pas d'ecran tactile, pas de capteur de vitesse) :
  - MOVING BULL / MOVING OUT BOARD / SPINNING TARGET : les zones sont
    materialisees par les leds de la cible et affichees a l'ecran.
  - ZERO STOP : compte a rebours de 10 s dessine a l'ecran, masque a partir
    de 5 s (3 s en devil) mais qui continue de tourner.
  - SPEED CHALLENGE : zone de 3 segments allumee qui se deplace (pas de
    capteur de vitesse), le plus de touches dans la zone gagne.
"""

import os
import random
import time
from functools import lru_cache
import pygame
try:
    from pygame import gfxdraw
except ImportError:
    gfxdraw = None
from include import cplayer
from include import cgame

#
VERSION = '1.00'
LOGO = 'Yum_Yum.png'  # Background image - relative to images folder
HEADERS = ['D1', 'D2', 'D3', 'Cible', 'Manche', 'Devil', 'Drink']  # Columns headers - Must be a string
OPTIONS = {'theme': 'default', 'max_round': 8, 'devil': True, 'devil_chance': 20, 'timing_games': True,
           'choose_game': False}
NB_DARTS = 3
GAME_RECORDS = {'Drink Points': 'ASC', 'Lost Rounds': 'ASC', 'Devil Modes': 'DESC'}

# Penalites
PENALTY = 1          # Drink points pour un perdant de manche
LAST_ROUND_MULT = 2  # Derniere manche : penalites doublees
DEVIL_MULT = 2       # Devil mode : penalite doublee
WORST_SCORE = -10000 # Score "pire que tout" (fleche non lancee pour les jeux de timing)

# Catalogue des mini-jeux
#   darts : nombre de flechettes de la manche
#   mode  : 'low'  -> le(s) plus petit(s) score(s) de la manche boivent
#           'fail' -> chaque joueur qui echoue boit
#   timing : jeu base sur le temps (desactive en partie online)
MINI_GAMES = {
    'BULL_CHALLENGE': {'name': 'BULL CHALLENGE', 'darts': 3, 'mode': 'low',
        'rule': "Touchez le Bull un max de fois (DB = 2)",
        'devil': "Seul le Double Bull compte"},
    'DOUBLE_CHALLENGE': {'name': 'DOUBLE CHALLENGE', 'darts': 3, 'mode': 'low',
        'rule': "Touchez les doubles allumes : {targets}",
        'devil': "Un seul double valide : {targets}"},
    'TRIPLE_CHALLENGE': {'name': 'TRIPLE CHALLENGE', 'darts': 3, 'mode': 'low',
        'rule': "Touchez les triples allumes : {targets}",
        'devil': "Un seul triple valide : {targets}"},
    'NO_BULL_COUNT_UP': {'name': 'NO BULL COUNT-UP', 'darts': 3, 'mode': 'low',
        'rule': "Count-Up, mais le Bull efface votre manche !",
        'devil': "Le Bull efface la manche et termine le tour"},
    'MOVING_BULL': {'name': 'MOVING BULL', 'darts': 3, 'mode': 'low',
        'rule': "Touchez le {target} (S=1 D=2 T=3)",
        'devil': "Seuls double et triple du {target} comptent"},
    'MOVING_OUT_BOARD': {'name': 'MOVING OUT BOARD', 'darts': 3, 'mode': 'fail',
        'rule': "Evitez les {count} segments rouges (OUT), la zone grandit !",
        'devil': "Evitez les {count} segments rouges, il n'en restera qu'un !"},
    'COUNT_UP': {'name': 'COUNT-UP', 'darts': 3, 'mode': 'low',
        'rule': "Marquez un maximum de points",
        'devil': "Les simples valent 0"},
    'CENTER_COUNT_UP': {'name': 'CENTER COUNT-UP', 'darts': 3, 'mode': 'low',
        'rule': "Pres du centre = points (DB100 SB80 T50 S40 D10)",
        'devil': "Seuls les Bulls comptent"},
    'COUNT_UP_ONLY': {'name': 'COUNT-UP ONLY {target}', 'darts': 3, 'mode': 'low',
        'rule': "Seul le {target} rapporte des points",
        'devil': "Seuls double et triple du {target} comptent"},
    'FORTUNE_COUNT_UP': {'name': 'FORTUNE COUNT-UP', 'darts': 3, 'mode': 'low',
        'rule': "Multiplicateur de cette flechette : x{mult}",
        'devil': "Multiplicateur (risque !) : x{mult}"},
    'MULTIPLE_COUNT_UP': {'name': 'MULTIPLE COUNT-UP', 'darts': 3, 'mode': 'low',
        'rule': "D/T/Bull doublent le multiplicateur : x{mult}",
        'devil': "Un simple casse la chaine : x{mult}"},
    'PLUS_MINUS_COUNT_UP': {'name': '+- COUNT-UP', 'darts': 3, 'mode': 'low',
        'rule': "Vert = +points / Rouge = -points",
        'devil': "Rouge = -points x2"},
    'HIGH_OR_LOW': {'name': 'HIGH OR LOW', 'darts': 3, 'mode': 'fail',
        'rule': "{condition} : faites {sign} {target} en 3 flechettes",
        'devil': "{condition} (cible durcie) : faites {sign} {target}"},
    'SPINNING_TARGET': {'name': 'SPINNING TARGET', 'darts': 3, 'mode': 'low',
        'rule': "Or x4 : {gold} / Bleu x2 : {blue}",
        'devil': "Or x4 : {gold} / Bleu x2 : {blue} / reste x0"},
    'FORTUNE_DIGITS': {'name': 'FORTUNE DIGITS', 'darts': 3, 'mode': 'low', 'timing': True,
        'rule': "Chaque flechette fige un chiffre : unites, dizaines, centaines",
        'devil': "Les compteurs defilent plus vite !"},
    'ZERO_STOP': {'name': 'ZERO STOP', 'darts': 1, 'mode': 'low', 'timing': True,
        'rule': "Arretez le compteur au plus pres de 0 sans depasser !",
        'devil': "Compteur masque des 3 s - penalite doublee !"},
    'SPEED_CHALLENGE': {'name': 'SPEED CHALLENGE', 'darts': 3, 'mode': 'low', 'timing': True,
        'rule': "Touchez la zone verte un max de fois, elle bouge toutes les 2 s",
        'devil': "Touchez la zone verte un max de fois, elle bouge chaque seconde"},
    'ONE_SHOT': {'name': 'ONE SHOT', 'darts': 1, 'mode': 'fail',
        'rule': "Une seule flechette : touchez le {target}",
        'devil': "Une seule flechette : double ou triple {target}"},
    'ONE_DART_COUNT_UP': {'name': 'ONE DART COUNT-UP', 'darts': 1, 'mode': 'low',
        'rule': "Une seule flechette : max de points",
        'devil': "Une seule flechette : les simples valent 0"},
    'ONE_DART_CENTER_COUNT_UP': {'name': 'ONE DART CENTER COUNT-UP', 'darts': 1, 'mode': 'low',
        'rule': "Une seule flechette, au plus pres du centre",
        'devil': "Une seule flechette : seuls les Bulls comptent"},
}

# Solo : score minimum de la manche pour ne pas boire (mini-jeux 'low' uniquement)
# COUNT_UP_ONLY : objectif = 2 x le numero tire
# ZERO_STOP : score = -centiemes (ex: -50 = 0.50 s)
SOLO_GOALS = {
    'BULL_CHALLENGE': 1,
    'DOUBLE_CHALLENGE': 1,
    'TRIPLE_CHALLENGE': 1,
    'NO_BULL_COUNT_UP': 60,
    'MOVING_BULL': 2,
    'COUNT_UP': 60,
    'CENTER_COUNT_UP': 130,
    'COUNT_UP_ONLY': None,
    'FORTUNE_COUNT_UP': 60,
    'MULTIPLE_COUNT_UP': 100,
    'PLUS_MINUS_COUNT_UP': 30,
    'SPINNING_TARGET': 80,
    'FORTUNE_DIGITS': 500,
    'ZERO_STOP': -50,
    'SPEED_CHALLENGE': 2,
    'ONE_DART_COUNT_UP': 20,
    'ONE_DART_CENTER_COUNT_UP': 50,
}

CENTER_POINTS = {'DB': 100, 'SB': 80, 'T': 50, 'S': 40, 'D': 10}
CHOICE_COLUMNS = 3  # Colonnes du menu de choix du mini-jeu
CHOICE_WIDTH = 0.7  # Taille de la fenetre du menu de choix (part de l'ecran)
CHOICE_HEIGHT = 0.75
CHOICE_BACK = 'BACK'  # Choix 'Retour' : la partie est abandonnee
SPEED_ZONE_SIZE = 3            # Speed Challenge : nombre de segments cote a cote de la zone
SPEED_ZONE_PERIOD = 2          # La zone se deplace toutes les ... secondes
SPEED_ZONE_PERIOD_DEVIL = 1    # Idem en devil mode
SPEED_MAX_LIFE = 120           # La zone ne bouge plus au dela (securite)
OUT_START = 7                  # Moving Out Board : segments OUT au depart
OUT_GROW = 1                   # Segments ajoutes a chaque flechette
OUT_START_DEVIL = 15           # Idem en devil mode (15, 17, 19 : il ne reste qu'un segment)
OUT_GROW_DEVIL = 2
SILENT_HIT_GAMES = ('ZERO_STOP', 'FORTUNE_DIGITS')  # La touche n'est ni annoncee ni affichee sur le DMD
SILENT_HIT_SOUND = 'target_hit'                    # Son neutre d'impact joue a la place de la voix
ZERO_STOP_DURATION = 10   # Compte a rebours du Zero Stop (secondes)
ZERO_STOP_HIDE = 5        # Le compteur est masque apres ce temps (secondes)
ZERO_STOP_HIDE_DEVIL = 3  # Idem en devil mode
ZERO_STOP_MAX_LIFE = 15   # Le compteur n'est plus dessine au dela (securite)
DIGITS_SPEEDS = (4, 7, 12)  # Fortune Digits : chiffres par seconde (unites, dizaines, centaines)
DIGITS_DEVIL_FACTOR = 1.5   # Devil mode : compteurs plus rapides
DIGITS_MAX_LIFE = 120       # Les compteurs ne sont plus dessines au dela (securite)
ANIMATION_TICK = 60         # Rafraichissement des animations (ms)
def rolling_digit(elapsed, index, devil=False):
    """
    Fortune Digits : digit displayed after 'elapsed' seconds (index 0=units, 1=tens, 2=hundreds)
    """
    speed = DIGITS_SPEEDS[index] * (DIGITS_DEVIL_FACTOR if devil else 1)
    return int(elapsed * speed) % 10

# Speed Challenge palette (dark glass panel, works with every theme)
CD_PANEL = (11, 17, 30)
CD_MINT = (52, 211, 153)
CD_MUTED = (148, 163, 184)

# LED console palette (dark screen in a steel frame, works with every theme)
LED_SCREEN = (5, 8, 13)
LED_LIME = (205, 255, 70)
LED_AMBER = (255, 186, 32)
LED_RED = (255, 72, 72)
LED_RED_DIM = (120, 34, 38)
LED_CYAN = (80, 220, 255)
LED_WHITE = (245, 247, 250)
LED_MUTED = (130, 140, 158)
STEEL_LIGHT = (214, 220, 230)
STEEL_DARK = (40, 45, 56)
LED_SKEW = 0.07         # Italic of the 7 segment digits (part of the digit height)
LED_GHOST = 0.10        # Brightness of the switched off segments
LED_RATIO = 0.56        # Digit width / digit height
CONSOLE_WIDTH = 0.38    # Console size (part of the screen)
CONSOLE_HEIGHT = 0.30
CONSOLE_TOP = 0.235     # Console top (part of the screen height) : under the rule, over the player cards
CONSOLE_FONT = 'Impact.ttf'  # Labels font (fonts folder), the theme font is used if missing
BAR_LEDS = 20           # Zero Stop : leds of the time bar

# Lit segments of each character
#  aaa
# f   b
#  ggg
# e   c
#  ddd
SEGMENTS = {'0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc', '5': 'afgcd',
            '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg', '-': 'g', ' ': ''}

def mix(color_a, color_b, amount):
    """
    Blend two (r, g, b) colours : amount 0 gives color_a, 1 gives color_b
    """
    return tuple(int(a + (b - a) * amount) for a, b in zip(color_a, color_b))

def disc(surface, color, center_x, center_y, radius):
    """
    Filled circle, anti-aliased when pygame.gfxdraw is available
    """
    if radius < 1:
        return
    try:
        gfxdraw.aacircle(surface, center_x, center_y, radius, color)
        gfxdraw.filled_circle(surface, center_x, center_y, radius, color)
    except Exception: # pylint: disable=broad-except
        # gfxdraw missing, or it refused the coordinates
        pygame.draw.circle(surface, color, (center_x, center_y), radius)

def rounded_panel(width, height, radius, fill, border=None, border_width=0, scale=3):
    """
    Rounded rectangle with an optional border, drawn big then scaled down (smooth corners).
    Built once : draw it with a simple blit afterwards.
    Surfaces are 32 bits : the cabinet screen is 16 bits and smoothscale refuses 16 bit surfaces.
    """
    big_w, big_h = width * scale, height * scale
    surface = pygame.Surface((big_w, big_h), pygame.SRCALPHA, 32)
    surface.fill(tuple(border or fill) + (0,))

    def shape(color, inset, rad):
        w, h = big_w - 2 * inset, big_h - 2 * inset
        pygame.draw.rect(surface, color, (inset + rad, inset, w - 2 * rad, h))
        pygame.draw.rect(surface, color, (inset, inset + rad, w, h - 2 * rad))
        for center_x in (inset + rad, inset + w - rad - 1):
            for center_y in (inset + rad, inset + h - rad - 1):
                pygame.draw.circle(surface, color, (center_x, center_y), rad)

    inset = 0
    if border:
        shape(tuple(border) + (255,), 0, radius * scale)
        inset = border_width * scale
    shape(tuple(fill) + (255,), inset, max(radius * scale - inset, 1))
    return pygame.transform.smoothscale(surface, (width, height))

def vertical_gradient(width, height, top, bottom):
    """
    Opaque surface going from colour 'top' to colour 'bottom'
    """
    surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
    for line in range(height):
        color = mix(top, bottom, line / max(height - 1, 1))
        pygame.draw.line(surface, color + (255,), (0, line), (width - 1, line))
    return surface

def rounded_mask(surface, radius):
    """
    Make the corners of a surface transparent (rounded rectangle).
    The mask is drawn at twice the size only : big masks are slow to scale down on the Raspberry
    """
    mask = rounded_panel(surface.get_width(), surface.get_height(), max(int(radius), 1), (255, 255, 255), scale=2)
    surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return surface

def segment_polygons(width, height):
    """
    Polygons of the 7 segments of a digit drawn in a width x height box (slanted)
    """
    body = width - height * LED_SKEW
    half = body * 0.2 / 2
    gap = half * 0.28

    def slant(points):
        return [(pos_x + (height - pos_y) * LED_SKEW, pos_y) for pos_x, pos_y in points]

    def horizontal(pos_y):
        left, right = half + gap, body - half - gap
        return slant([(left, pos_y), (left + half, pos_y - half), (right - half, pos_y - half), \
                (right, pos_y), (right - half, pos_y + half), (left + half, pos_y + half)])

    def vertical(pos_x, top, bottom):
        return slant([(pos_x, top), (pos_x + half, top + half), (pos_x + half, bottom - half), \
                (pos_x, bottom), (pos_x - half, bottom - half), (pos_x - half, top + half)])

    middle = height / 2
    return {'a': horizontal(half), 'g': horizontal(middle), 'd': horizontal(height - half),
            'f': vertical(half, half + gap, middle - gap), 'b': vertical(body - half, half + gap, middle - gap),
            'e': vertical(half, middle + gap, height - half - gap),
            'c': vertical(body - half, middle + gap, height - half - gap)}

@lru_cache(maxsize=512)
def led_glyph(char, width, height, color, glow=True):
    """
    7 segment character ('0'-'9', '-', ' ', '.') with dim switched off segments and a soft halo.
    The surface is bigger than width x height (room for the halo) : center it on its cell.
    Surfaces are cached : never draw on them.
    """
    scale = 3
    halo = max(int(height * 0.12), 2)
    full_w, full_h = width + 2 * halo, height + 2 * halo
    big = pygame.Surface((full_w * scale, full_h * scale), pygame.SRCALPHA, 32)
    big.fill(color + (0,))
    lit = big.copy()
    if char == '.':
        center = (int((halo + width * 0.35) * scale), int((halo + height - width * 0.32) * scale))
        for surface in (big, lit):
            pygame.draw.circle(surface, color + (255,), center, int(width * 0.32 * scale))
    else:
        off = mix(LED_SCREEN, color, LED_GHOST) + (255,)
        for name, points in segment_polygons(width * scale, height * scale).items():
            points = [(pos_x + halo * scale, pos_y + halo * scale) for pos_x, pos_y in points]
            if name in SEGMENTS.get(char, ''):
                pygame.draw.polygon(big, color + (255,), points)
                pygame.draw.polygon(lit, color + (255,), points)
            else:
                pygame.draw.polygon(big, off, points)
    image = pygame.transform.smoothscale(big, (full_w, full_h))
    if not glow:
        return fast(image)
    # Halo : the lit segments, blurred by a strong shrink / enlarge
    small = pygame.transform.smoothscale(lit, (max(int(full_w / 10), 1), max(int(full_h / 10), 1)))
    result = pygame.transform.smoothscale(small, (full_w, full_h))
    result.fill((255, 255, 255, 150), special_flags=pygame.BLEND_RGBA_MULT)
    result.blit(image, (0, 0))
    return fast(result)

def fast(surface):
    """
    Surface in the screen pixel format (faster blits on the Raspberry)
    """
    try:
        return surface.convert_alpha()
    except pygame.error:
        # No display mode set
        return surface

@lru_cache(maxsize=32)
def label_font(path, size):
    """
    Font of the console labels (kept in memory)
    """
    return pygame.font.Font(path, max(int(size), 8))

class Overlay:
    """
    Animation drawn in the middle of the screen while the game waits for a dart.
    pygame / X11 are not thread safe : frames are drawn by the main loop only,
    each time the dart wait times out (see Game.time / ANIMATION_TICK).
    """
    def __init__(self, display, start, max_life):
        self.display = display
        self.start_time = start
        self.max_life = max_life
        self.width = int(display.res_x / 3)
        self.height = int(display.res_y / 4)
        self.pos_x = int((display.res_x - self.width) / 2)
        self.pos_y = int((display.res_y - self.height) / 2)
        self.background = display.colorset.get('game-bg') or (0, 0, 0)
        # Time of the last frame displayed (what the player saw)
        self.last_elapsed = None

    def draw(self, elapsed):
        """
        Draw the content of a frame (implemented by subclasses)
        """

    def paint_background(self, elapsed):
        """
        Draw the panel under the frame content (subclasses may replace it)
        """
        self.display.blit_rect(self.pos_x, self.pos_y, self.width, self.height, \
                self.background, border=4, Alpha=235)

    def frame(self):
        """
        Draw one frame. Return False when the animation is over
        """
        elapsed = time.monotonic() - self.start_time
        if elapsed > self.max_life:
            return False
        self.paint_background(elapsed)
        self.draw(elapsed)
        self.display.update_screen((self.pos_x, self.pos_y, self.width, self.height))
        self.last_elapsed = elapsed
        return True

class Console(Overlay):
    """
    LED console : steel frame, dark screen, title plate, 7 segment digits.
    Subclasses draw in self.content (area under the title plate).
    The previous plain panel and texts are kept if the console cannot be built.
    """
    # Panels already built (about 1 s on the Raspberry) : (size, accent, title) -> surface
    panels = {}

    def __init__(self, display, start, max_life, accent, title):
        super().__init__(display, start, max_life)
        self.width = int(display.res_x * CONSOLE_WIDTH)
        self.height = int(display.res_y * CONSOLE_HEIGHT)
        self.pos_x = int((display.res_x - self.width) / 2)
        self.pos_y = int(display.res_y * CONSOLE_TOP)
        self.accent = accent
        self.title = title
        self.bezel = max(int(self.height * 0.055), 4)
        self.pad = max(int(self.height * 0.045), 3)
        self.plate_height = int(self.height * 0.14)
        self.label_height = int(self.height * 0.085)
        top = self.pos_y + self.bezel + self.pad + self.plate_height + self.pad
        self.content = pygame.Rect(self.pos_x + self.bezel + 2 * self.pad, top, \
                self.width - 2 * (self.bezel + 2 * self.pad), self.pos_y + self.height - self.bezel - self.pad - top)
        self.font_path = console_font(display)
        self.panel = None
        try:
            key = (self.width, self.height, accent, title, self.font_path)
            if key not in Console.panels:
                Console.panels[key] = self.build_panel()
            self.panel = Console.panels[key]
            self.build()
        except Exception as exception: # pylint: disable=broad-except
            self.panel = None
            display.logs.log("ERROR", f"Yum Yum : LED console unavailable : {exception}")

    def build_panel(self):
        """
        Steel frame, screen and title plate, rendered once
        """
        width, height, bezel = self.width, self.height, self.bezel
        radius = int(height * 0.09)
        panel = rounded_mask(vertical_gradient(width, height, STEEL_LIGHT, STEEL_DARK), radius)
        # Bevel : reversed gradient inside the frame
        inset = int(bezel * 0.4)
        bevel = vertical_gradient(width - 2 * inset, height - 2 * inset, STEEL_DARK, mix(STEEL_LIGHT, STEEL_DARK, 0.35))
        panel.blit(rounded_mask(bevel, radius - inset), (inset, inset))
        # Screen, with a thin accent rim, scanlines and a gloss on the top
        screen_w, screen_h = width - 2 * bezel, height - 2 * bezel
        screen_radius = max(radius - bezel, 4)
        panel.blit(rounded_panel(screen_w, screen_h, screen_radius, mix(LED_SCREEN, self.accent, 0.55)), (bezel, bezel))
        screen = vertical_gradient(screen_w - 4, screen_h - 4, mix(LED_SCREEN, self.accent, 0.10), LED_SCREEN)
        lines = pygame.Surface(screen.get_size(), pygame.SRCALPHA, 32)
        lines.fill((0, 0, 0, 0))
        for line in range(0, screen_h, 3):
            pygame.draw.line(lines, (0, 0, 0, 90), (0, line), (screen_w, line))
        gloss_h = int(screen_h * 0.4)
        for line in range(gloss_h):
            pygame.draw.line(lines, (255, 255, 255, int(16 * (1 - line / gloss_h))), (0, line), (screen_w, line))
        screen.blit(lines, (0, 0))
        panel.blit(rounded_mask(screen, screen_radius - 2), (bezel + 2, bezel + 2))
        # Title plate
        font = label_font(self.font_path, self.plate_height * 0.78)
        text = font.render(self.title, True, LED_SCREEN)
        plate_w = min(text.get_width() + 2 * self.plate_height, screen_w - 2 * self.pad)
        plate = vertical_gradient(plate_w, self.plate_height, mix(self.accent, LED_WHITE, 0.45), self.accent)
        plate = rounded_mask(plate, int(self.plate_height / 2))
        if text.get_width() > plate_w - self.plate_height:
            text = pygame.transform.smoothscale(text, (plate_w - self.plate_height, text.get_height()))
        plate.blit(text, (int((plate_w - text.get_width()) / 2), int((self.plate_height - text.get_height()) / 2)))
        panel.blit(plate, (int((width - plate_w) / 2), bezel + self.pad))
        return fast(panel)

    def build(self):
        """
        Pre-render what does not change (subclasses)
        """

    def paint_background(self, elapsed):
        if self.panel is None:
            return super().paint_background(elapsed)
        self.display.blit(self.panel, (self.pos_x, self.pos_y))

    def draw(self, elapsed):
        if self.panel is None:
            return self.draw_classic(elapsed)
        return self.draw_console(elapsed)

    def draw_console(self, elapsed):
        """
        Content of the console (subclasses)
        """

    def draw_classic(self, elapsed):
        """
        Plain look, when the console is unavailable (subclasses)
        """

    def label(self, text, color, rect, align='Left'):
        """
        Small text in a rect
        """
        if not text:
            return
        image = label_font(self.font_path, rect.height).render(str(text), True, color)
        if image.get_width() > rect.width:
            image = pygame.transform.smoothscale(image, (rect.width, image.get_height()))
        if align == 'Left':
            pos_x = rect.x
        elif align == 'Right':
            pos_x = rect.right - image.get_width()
        else:
            pos_x = rect.centerx - int(image.get_width() / 2)
        self.display.blit(image, (pos_x, rect.centery - int(image.get_height() / 2)))

    @staticmethod
    def cell_width(char, height):
        """
        Width of a 7 segment cell
        """
        if char == '.':
            return int(height * 0.24)
        return int(height * LED_RATIO)

    def led_layout(self, text, rect):
        """
        Fixed-width cells of a 7 segment text centered in rect : the number does not shake
        while it changes. Return the digit height and a list of (char, center_x, cell_width)
        """
        height = rect.height
        while True:
            gap = int(height * 0.08)
            widths = [self.cell_width(char, height) for char in text]
            total = sum(widths) + gap * (len(text) - 1)
            if total <= rect.width or height < 10:
                break
            height = int(height * rect.width / total)
        cells = []
        pos_x = rect.centerx - int(total / 2)
        for char, width in zip(text, widths):
            cells.append((char, pos_x + int(width / 2), width))
            pos_x += width + gap
        return height, cells

    def led_text(self, text, color, rect, glow=True):
        """
        7 segment text centered in rect
        """
        height, cells = self.led_layout(text, rect)
        for char, center_x, width in cells:
            image = led_glyph(char, width, height, color, glow)
            self.display.blit(image, (center_x - int(image.get_width() / 2), \
                    rect.centery - int(image.get_height() / 2)))

    def prime(self, sample, chars, color, rect):
        """
        Render the glyphs used by led_text(sample-like text, color, rect) before the first
        frame (no lag when the animation starts)
        """
        height = self.led_layout(sample, rect)[0]
        for char in chars:
            led_glyph(char, self.cell_width(char, height), height, color, True)

class DigitsRoller(Console):
    """
    Fortune Digits : 3 rolling digits.
    Each dart freezes a digit (units, then tens, then hundreds)
    """
    CAPTIONS = {2: 'x100', 1: 'x10', 0: 'x1'}

    def __init__(self, display, start, devil):
        self.devil = devil
        self.frozen = {}
        self.windows = {}
        super().__init__(display, start, DIGITS_MAX_LIFE, LED_RED if devil else LED_AMBER, \
                'FORTUNE DIGITS' + (' - DEVIL' if devil else ''))

    def build(self):
        content = self.content
        self.window_gap = int(content.width * 0.06)
        self.window_w = int((content.width - 2 * self.window_gap) / 3)
        self.window_h = content.height - self.label_height - int(self.pad / 2)
        radius = int(self.window_h / 10)
        for state, rim in (('idle', mix(LED_SCREEN, STEEL_LIGHT, 0.25)), ('active', self.accent), ('frozen', LED_LIME)):
            self.windows[state] = fast(rounded_panel(self.window_w, self.window_h, radius, \
                    mix(LED_SCREEN, rim, 0.08), mix(LED_SCREEN, rim, 0.8), 3))
        self.digit_rect = pygame.Rect(0, 0, int(self.window_w * 0.8), int(self.window_h * 0.78))
        for color in (self.accent, LED_LIME):
            self.prime('0', '0123456789', color, self.digit_rect)

    def freeze(self, index, digit):
        """
        Freeze a digit
        """
        self.frozen[index] = digit

    def draw_console(self, elapsed):
        content = self.content
        active = len(self.frozen)
        blink = int(elapsed * 4) % 2 == 0
        # Hundreds on the left, units on the right
        for column, index in enumerate((2, 1, 0)):
            pos_x = content.x + column * (self.window_w + self.window_gap)
            frozen = index in self.frozen
            if frozen:
                state = 'frozen'
            else:
                state = 'active' if index == active and blink else 'idle'
            self.display.blit(self.windows[state], (pos_x, content.y))
            digit = self.frozen[index] if frozen else rolling_digit(elapsed, index, self.devil)
            rect = self.digit_rect.copy()
            rect.center = (pos_x + int(self.window_w / 2), content.y + int(self.window_h / 2))
            self.led_text(str(digit), LED_LIME if frozen else self.accent, rect)
            color = LED_LIME if frozen else (self.accent if index == active else LED_MUTED)
            self.label(self.CAPTIONS[index], color, pygame.Rect(pos_x, content.bottom - self.label_height, \
                    self.window_w, self.label_height), align='Center')

    def draw_classic(self, elapsed):
        display = self.display
        cell = int(self.width / 3)
        # Hundreds on the left, units on the right
        for column, index in enumerate((2, 1, 0)):
            cell_x = self.pos_x + column * cell
            if index in self.frozen:
                digit = self.frozen[index]
                display.blit_rect(cell_x + 4, self.pos_y + 4, cell - 8, self.height - 8, (0, 110, 0), Alpha=255)
            else:
                digit = rolling_digit(elapsed, index, self.devil)
            display.blit_text(str(digit), cell_x, self.pos_y, cell, self.height, \
                    color=display.colorset['game-title2'])

class GlassOverlay(Overlay):
    """
    Overlay with the same dark rounded panel as the countdown.
    The classic panel is kept if the modern one cannot be built.
    """
    def __init__(self, display, start, max_life, rim):
        super().__init__(display, start, max_life)
        self.rim = rim
        self.pad = int(self.width / 24)
        self.label_height = int(self.height / 9)
        self.panel = None
        self.glyphs = {}
        try:
            self.panel = rounded_panel(self.width, self.height, int(self.height / 9), CD_PANEL, \
                    mix(CD_PANEL, rim, 0.5), 3)
            self.build()
        except Exception as exception: # pylint: disable=broad-except
            self.panel = None
            display.logs.log("ERROR", f"Yum Yum : modern panel unavailable : {exception}")

    def build(self):
        """
        Pre-render what does not change (subclasses)
        """

    def paint_background(self, elapsed):
        if self.panel is None:
            return super().paint_background(elapsed)
        self.display.blit(self.panel, (self.pos_x, self.pos_y))

    def glyph(self, font, char, color):
        """
        Rendered character (kept in memory)
        """
        key = (id(font), char, color)
        if key not in self.glyphs:
            self.glyphs[key] = font.render(char, True, color)
        return self.glyphs[key]

    def caption(self, text, pos_x, pos_y, width, color=CD_MUTED, align='Left'):
        """
        Small label
        """
        self.display.blit_text(text, pos_x, pos_y, width, self.label_height, color=color, \
                align=align, margin=False, divider=1.2)

class SpeedOverlay(GlassOverlay):
    """
    Speed Challenge : current zone (the same as the one lit on the board)
    """
    def __init__(self, display, start, zone):
        # zone() returns the numbers of the zone currently lit
        self.zone = zone
        super().__init__(display, start, SPEED_MAX_LIFE, CD_MINT)

    def draw(self, elapsed):
        zone = ' - '.join(str(num) for num in self.zone())
        if self.panel is None:
            return self.display.blit_text(zone, self.pos_x, self.pos_y, self.width, self.height, \
                    color=self.display.colorset['game-green'])
        self.caption('ZONE', self.pos_x + self.pad, self.pos_y + int(self.pad * 0.8), self.width - 2 * self.pad)
        top = self.pos_y + self.pad + self.label_height
        self.display.blit_text(zone, self.pos_x + self.pad, top, self.width - 2 * self.pad, \
                self.height - 2 * self.pad - self.label_height, color=CD_MINT)

class Countdown(Console):
    """
    Zero Stop countdown, hidden after a while.
    7 segment digits, led bar going from lime to red, objective leds (solo),
    a red light scanning the bar once the counter is hidden.
    """
    def __init__(self, display, start, hide_after, goal=None, labels=None, devil=False):
        self.hide_after = hide_after
        self.goal = goal    # Objective in seconds (solo) or None
        labels = labels or {}
        self.labels = {'time': labels.get('time', 'TEMPS RESTANT'),
                       'hidden': labels.get('hidden', 'CHRONO MASQUE'),
                       'goal': labels.get('goal', 'OBJECTIF'),
                       'title': labels.get('title', 'STOP A 0.00')}
        self.leds = {}
        super().__init__(display, start, ZERO_STOP_MAX_LIFE, LED_RED if devil else LED_LIME, \
                self.labels['title'] + (' - DEVIL' if devil else ''))

    def build(self):
        content = self.content
        self.caption_rect = pygame.Rect(content.x, content.y, content.width, self.label_height)
        bar_h = max(int(content.height * 0.11), 6)
        self.led_gap = max(int(content.width / 160), 2)
        self.led_w = int((content.width - (BAR_LEDS - 1) * self.led_gap) / BAR_LEDS)
        self.bar_x = content.x + int((content.width - BAR_LEDS * self.led_w - (BAR_LEDS - 1) * self.led_gap) / 2)
        self.bar_y = content.bottom - bar_h
        self.digits_rect = pygame.Rect(content.x, self.caption_rect.bottom + int(self.pad / 2), content.width, \
                self.bar_y - self.caption_rect.bottom - self.pad)
        radius = max(int(bar_h / 4), 1)
        for color in (LED_LIME, LED_AMBER, LED_RED):
            self.leds[color] = fast(rounded_panel(self.led_w, bar_h, radius, color, mix(color, LED_WHITE, 0.4), 1))
            self.leds[('off', color)] = fast(rounded_panel(self.led_w, bar_h, radius, mix(LED_SCREEN, color, 0.16)))
        for color in (LED_LIME, LED_AMBER):
            self.prime('00.00', '0123456789.', color, self.digits_rect)
        self.prime('00.00', '-.', LED_RED, self.digits_rect)
        height = self.led_layout('00.00', self.digits_rect)[0]
        for char in '-.':
            led_glyph(char, self.cell_width(char, height), height, LED_RED_DIM, False)

    def led_color(self, index):
        """
        Colour of a bar led : the left of the bar (close to 0) turns red
        """
        if index < BAR_LEDS * 0.2:
            return LED_RED
        if index < BAR_LEDS * 0.45:
            return LED_AMBER
        return LED_LIME

    def draw_console(self, elapsed):
        hidden = elapsed >= self.hide_after
        remaining = max(ZERO_STOP_DURATION - elapsed, 0)
        # Captions
        self.label(self.labels['hidden'] if hidden else self.labels['time'], LED_RED if hidden else LED_MUTED, \
                self.caption_rect, align='Left')
        if self.goal:
            self.label(f"{self.labels['goal']} <= {self.goal:.2f} s", LED_LIME, self.caption_rect, align='Right')
        # Digits
        if hidden:
            bright = int(elapsed * 2) % 2 == 0
            self.led_text('--.--', LED_RED if bright else LED_RED_DIM, self.digits_rect, glow=bright)
        else:
            color = LED_LIME if elapsed < self.hide_after * 0.6 else LED_AMBER
            self.led_text(f"{remaining:05.2f}", color, self.digits_rect)
        # Led bar
        if hidden:
            # A light scans the bar : the counter still runs, but nothing tells how long is left
            phase = (elapsed * 0.8) % 2.0
            head = (BAR_LEDS - 1) * (phase if phase <= 1.0 else 2.0 - phase)
            lit = [index for index in range(BAR_LEDS) if abs(index - head) < 1.5]
        else:
            lit = range(0, int(BAR_LEDS * remaining / ZERO_STOP_DURATION + 0.999))
        goal_leds = int(BAR_LEDS * self.goal / ZERO_STOP_DURATION + 0.999) if self.goal and not hidden else 0
        for index in range(BAR_LEDS):
            color = LED_RED if hidden else self.led_color(index)
            image = self.leds[color] if index in lit else self.leds[('off', color)]
            pos_x = self.bar_x + index * (self.led_w + self.led_gap)
            self.display.blit(image, (pos_x, self.bar_y))
            if index < goal_leds:
                # Objective zone : a mark above the leds
                pygame.draw.rect(self.display.screen, LED_LIME, (pos_x, self.bar_y - 4, self.led_w, 2))

    def draw_classic(self, elapsed):
        display = self.display
        margin = int(self.height / 12)
        bar_height = int(self.height / 10)
        if elapsed < self.hide_after:
            remaining = ZERO_STOP_DURATION - elapsed
            text = f"{remaining:05.2f}"
            color = display.colorset['game-title2']
            bar_width = int((self.width - 2 * margin) * remaining / ZERO_STOP_DURATION)
            display.blit_rect(self.pos_x + margin, self.pos_y + self.height - margin - bar_height, \
                    bar_width, bar_height, display.colorset['game-green'], Alpha=255)
        else:
            text = "??.??"
            color = display.colorset['game-red']
        display.blit_text(text, self.pos_x, self.pos_y, self.width, self.height - bar_height - margin, color=color)

##############
# Arcade game screen : top strip with tags, rule, one card per player
##############
ARCADE_PLAYER_COLORS = [(52, 211, 153), (244, 114, 182), (96, 165, 250), (167, 139, 250),
                        (251, 146, 60), (45, 212, 191), (163, 230, 53), (232, 121, 249)]
ARCADE_MINI_GAME = (94, 234, 212)   # Mini-game tag (red in devil mode)
LED_CHARS = set(SEGMENTS) | {'.'}

def console_font(display):
    """
    Labels font of the LED consoles and of the arcade screen
    """
    font = os.path.join(os.path.dirname(display.defaultfontpath), CONSOLE_FONT)
    return font if os.path.isfile(font) else display.defaultfontpath

@lru_cache(maxsize=64)
def tag_surface(text, color, height, font, max_width=0):
    """
    Light pill with dark text (cached)
    """
    image = label_font(font, height * 0.62).render(text, True, LED_SCREEN)
    if max_width and image.get_width() > max_width - height:
        image = pygame.transform.smoothscale(image, (max_width - height, image.get_height()))
    width = image.get_width() + height
    plate = rounded_mask(vertical_gradient(width, height, mix(color, LED_WHITE, 0.45), color), int(height / 2))
    plate.blit(image, (int((width - image.get_width()) / 2), int((height - image.get_height()) / 2)))
    return fast(plate)

@lru_cache(maxsize=128)
def dark_tag_surface(text, color, height, font, max_width=0):
    """
    Dark pill with a coloured rim and coloured text (cached)
    """
    image = label_font(font, height * 0.6).render(text, True, color)
    if max_width and image.get_width() > max_width - height:
        image = pygame.transform.smoothscale(image, (max_width - height, image.get_height()))
    width = image.get_width() + height
    plate = rounded_panel(width, height, int(height / 2), LED_SCREEN, mix(LED_SCREEN, color, 0.6), 2)
    plate.blit(image, (int((width - image.get_width()) / 2), int((height - image.get_height()) / 2)))
    return fast(plate)

@lru_cache(maxsize=32)
def card_surface(width, height, color, active):
    """
    Player card : steel (gold when active) frame, dark screen, header in the player colour (cached)
    """
    radius = max(int(height * 0.07), 4)
    bezel = max(int(height * 0.024), 3)
    rim = LED_AMBER if active else STEEL_LIGHT
    card = rounded_mask(vertical_gradient(width, height, mix(rim, LED_WHITE, 0.3), mix(rim, STEEL_DARK, 0.55)), radius)
    inner = vertical_gradient(width - 2 * bezel, height - 2 * bezel, mix(LED_SCREEN, color, 0.12), LED_SCREEN)
    card.blit(rounded_mask(inner, radius - bezel), (bezel, bezel))
    head_h = int(height * 0.26)
    head = rounded_mask(vertical_gradient(width - 2 * bezel, head_h, mix(color, LED_WHITE, 0.4), color), radius - bezel)
    # Square bottom corners of the header
    pygame.draw.rect(head, color + (255,), (0, head_h - radius, width, radius))
    card.blit(head, (bezel, bezel))
    return fast(card)

def led_layout(text, rect):
    """
    Fixed-width cells of a 7 segment text fitting in rect.
    Return the digit height and a list of (char, center_x offset, cell_width), offsets from the text left
    """
    height = rect.height
    while True:
        gap = int(height * 0.08)
        widths = [int(height * (0.24 if char == '.' else LED_RATIO)) for char in text]
        total = sum(widths) + gap * (len(text) - 1)
        if total <= rect.width or height < 10:
            break
        height = int(height * rect.width / total)
    cells = []
    pos_x = 0
    for char, width in zip(text, widths):
        cells.append((char, pos_x + int(width / 2), width))
        pos_x += width + gap
    return height, cells, total

class ArcadeScreen:
    """
    Draw the Yum Yum game screen : tags on the top, rule, LED player cards on the bottom
    """
    def __init__(self, display):
        self.display = display
        self.scale = display.res_y / 1080
        self.font = console_font(display)

    def size(self, value):
        """
        Size designed for a 1080 pixels high screen
        """
        return max(int(value * self.scale), 1)

    def text(self, words, height, color, pos_x, center_y, align='Left'):
        """
        Text from the console font, vertically centered on center_y
        """
        image = label_font(self.font, height).render(str(words), True, color)
        if align == 'Right':
            pos_x -= image.get_width()
        elif align == 'Center':
            pos_x -= int(image.get_width() / 2)
        self.display.blit(image, (pos_x, center_y - int(image.get_height() / 2)))
        return image.get_width()

    def led(self, words, color, rect):
        """
        7 segment text right-aligned in rect
        """
        height, cells, total = led_layout(words, rect)
        left = rect.right - total
        for char, center_x, width in cells:
            image = led_glyph(char, width, height, color, True)
            self.display.blit(image, (left + center_x - int(image.get_width() / 2), \
                    rect.centery - int(image.get_height() / 2)))

    def blit_tag(self, surface, pos_x, pos_y, align='Left'):
        """
        Blit a pill, return its width
        """
        if align == 'Right':
            pos_x -= surface.get_width()
        elif align == 'Center':
            pos_x -= int(surface.get_width() / 2)
        self.display.blit(surface, (pos_x, pos_y))
        return surface.get_width()

    def top(self, round_text, mini_game, devil, options, game_type, rule):
        """
        Top strip : round and mini-game on the left, options on the right, rule below
        """
        display = self.display
        height, pos_y, margin = self.size(54), self.size(24), self.size(28)
        pos_x = margin
        pos_x += self.blit_tag(tag_surface(round_text, LED_AMBER, height, self.font), pos_x, pos_y) + self.size(14)
        self.blit_tag(tag_surface(mini_game, LED_RED if devil else ARCADE_MINI_GAME, height, self.font, \
                int(display.res_x / 2) - pos_x), pos_x, pos_y)
        right = display.res_x - margin
        for words, color in options:
            right -= self.blit_tag(dark_tag_surface(words, color, self.size(46), self.font), right, \
                    pos_y + self.size(4), align='Right') + self.size(12)
        if game_type:
            self.text(game_type, self.size(26), display.colorset['game-type'], int(display.res_x / 2), \
                    self.size(112), align='Center')
        if rule:
            self.blit_tag(dark_tag_surface(rule, LED_WHITE, self.size(54), self.font, display.res_x - 2 * margin), \
                    int(display.res_x / 2), self.size(150), align='Center')

    def cards(self, cards, active_label):
        """
        One card per player, on 1 row (up to 4 players) or 2 rows
        """
        display = self.display
        rows = 1 if len(cards) <= 4 else 2
        per_row = int((len(cards) + rows - 1) / rows)
        gap, margin = self.size(24), self.size(40)
        card_w = min(self.size(440), int((display.res_x - 2 * margin - (per_row - 1) * gap) / per_row))
        card_h = self.size(250) if rows == 1 else self.size(200)
        row_gap = self.size(16)
        for index, card in enumerate(cards):
            row, column = divmod(index, per_row)
            in_row = min(per_row, len(cards) - row * per_row)
            left = int((display.res_x - in_row * card_w - (in_row - 1) * gap) / 2)
            pos_x = left + column * (card_w + gap)
            pos_y = display.res_y - self.size(22) - (rows - row) * card_h - (rows - row - 1) * row_gap
            if card['active'] and rows == 1:
                pos_y -= self.size(22)
                self.blit_tag(tag_surface(active_label, LED_AMBER, self.size(40), self.font), \
                        pos_x + int(card_w / 2), pos_y - self.size(44), align='Center')
            self.card(card, pos_x, pos_y, card_w, card_h)

    def card(self, card, pos_x, pos_y, width, height):
        """
        One player card
        """
        color = card['color']
        bezel = max(int(height * 0.024), 3)
        head_h = int(height * 0.26)
        self.display.blit(card_surface(width, height, color, card['active']), (pos_x, pos_y))
        # Header : name, devil tag
        head_y = pos_y + bezel + int(head_h / 2)
        name_w = width - 2 * bezel - int(height * 0.1)
        if card['devil']:
            tag = tag_surface('DEVIL', LED_RED, int(head_h * 0.55), self.font)
            name_w -= tag.get_width() + int(height * 0.05)
            self.blit_tag(tag, pos_x + width - bezel - int(height * 0.05), head_y - int(tag.get_height() / 2), \
                    align='Right')
        name = label_font(self.font, head_h * 0.62).render(card['name'], True, mix(color, (0, 0, 0), 0.78))
        if name.get_width() > name_w:
            name = pygame.transform.smoothscale(name, (name_w, name.get_height()))
        self.display.blit(name, (pos_x + bezel + int(height * 0.07), head_y - int(name.get_height() / 2)))
        # Round score : 7 segments, or text if it has other characters ('OUT', '12>90'...)
        body = pygame.Rect(pos_x + int(height * 0.08), pos_y + bezel + head_h + int(height * 0.04), \
                width - int(height * 0.16), int(height * 0.36))
        score_color = LED_AMBER if card['active'] else mix(LED_AMBER, LED_SCREEN, 0.25)
        if set(card['score']) <= LED_CHARS:
            self.led(f"{card['score']:>3}", score_color, body)
        else:
            self.text(card['score'], int(body.height * 0.8), score_color, body.right, body.centery, align='Right')
        if card['target']:
            self.text(card['target'], int(height * 0.1), LED_MUTED, body.x, body.y + int(height * 0.06))
        # Footer : darts of the round, drink points
        pill_h = int(height * 0.16)
        foot_y = pos_y + height - bezel - int(height * 0.06) - pill_h
        dart_x = pos_x + bezel + int(height * 0.056)
        for dart in card['darts']:
            dart_x += self.blit_tag(dark_tag_surface(dart, LED_MUTED if dart == '-' else LED_LIME, pill_h, self.font), \
                    dart_x, foot_y) + int(height * 0.032)
        self.text(card['drinks'], int(height * 0.136), LED_RED if card['drinking'] else LED_MUTED, \
                pos_x + width - bezel - int(height * 0.064), foot_y + int(pill_h / 2), align='Right')

def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
    """
    return 1 <= nb_players <= 8, VERSION, 8

def to_bool(value):
    """
    Options may be received as bool or as string
    """
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('true', '1', 'yes', 'on')

class CPlayerExtended(cplayer.Player):
    """
    Extended Player class
    """
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        self.lost_rounds = 0
        self.devil_count = 0
        # State of the current manche (stored on player to survive backups)
        self.yy_round = 0
        self.yy_score = 0
        self.yy_failed = False
        self.yy_chain = 1
        self.yy_digits = []
        self.yy_launches = []
        self.yy_chrono = None
        self.yy_display = ''
        # Init Player Records to zero
        for game_record in GAME_RECORDS:
            self.stats[game_record] = '0'

class Game(cgame.Game):
    """
    Yum Yum game class
    """
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.logo = LOGO
        self.headers = HEADERS
        self.game_records = GAME_RECORDS
        # All the texts of the game in the thin strip of the hit banner (Screen.ribbon_message) :
        # the arcade screen does not go through Screen.refresh_game_screen, which sets it too
        display.ribbon_messages = True
        self.nb_darts = NB_DARTS
        self.options = options
        self.nb_players = nb_players
        self.max_round = int(options['max_round'])
        self.devil = to_bool(options['devil'])
        self.devil_chance = int(options['devil_chance'])
        # Timing games cannot be synchronised in online games
        online = getattr(self.display, 'game_type', None) == 'online'
        self.timing_games = to_bool(options['timing_games']) and not online
        # Choice of mini-games is not synchronised in online games
        self.choose_game = to_bool(options.get('choose_game', False)) and not online
        self.solo = nb_players == 1
        self.chosen = []

        # Seed shared with network clients (see get_random / set_random)
        self.seed = random.randint(1, 999999999)
        self.rng = random.Random(self.seed)

        self.programme = None
        self.round_params = {}
        self.turn_params = {}
        self.dart_params = {}
        self.resolved = []
        self.current_launch = 1
        self.chrono_pending = False
        # Current animation (Zero Stop / Fortune Digits), drawn on main loop timeouts
        self.overlay = None
        # Speed Challenge : zone positions per player turn, and zone currently lit
        self.speed_centers = {}
        self.speed_zone_shown = []
        self.tick = False
        self.last_pre_dart = None
        self.click_zones = None
        self.current_round = 1
        self.dart_time = None
        self.winner = -1

    ##############
    # Helpers
    ##############
    def tr(self, key, default):
        """
        Translate with a fallback when the key is missing from the locale
        """
        text = self.display.lang.translate(key)
        return default if text == key else text

    def mini_game(self, actual_round):
        """
        Return mini-game id of a round
        """
        return self.programme[min(actual_round, len(self.programme)) - 1]

    def is_devil(self, player, actual_round):
        """
        Is devil mode active for this player on this round ?
        """
        return self.turn_params.get((actual_round, player.ident), {}).get('devil', False)

    @staticmethod
    def number(hit):
        """
        Return the number of a hit ('T20' -> 20, 'SB' -> 'B')
        """
        if hit[1:] == 'B':
            return 'B'
        return int(hit[1:])

    @staticmethod
    def is_single(hit):
        """
        Single but not bull
        """
        return hit[:1] == 'S' and hit != 'SB'

    @staticmethod
    def is_bull(hit):
        """
        Bull or double bull
        """
        return hit in ('SB', 'DB')

    def start_overlay(self, overlay, keep_time=False, player=None):
        """
        Start an animation : the main loop will call us back every ANIMATION_TICK ms
        (or after self.time ms if already set and keep_time).
        With a player, its chrono restarts now : the time spent rendering the console is not lost
        """
        self.overlay = overlay
        if player is not None:
            player.yy_chrono = time.monotonic()
            overlay.start_time = player.yy_chrono
        if not keep_time:
            self.time = ANIMATION_TICK
        self.overlay.frame()

    def stop_overlay(self):
        """
        Stop the current animation
        """
        self.overlay = None
        self.time = 0

    @staticmethod
    def elapsed(player):
        """
        Time since the beginning of the player's chrono (0 if not started)
        """
        if player.yy_chrono is None:
            return 0
        return time.monotonic() - player.yy_chrono

    def speed_zone(self, actual_round, player, elapsed):
        """
        Speed Challenge : zone (adjacent numbers) displayed after 'elapsed' seconds
        """
        devil = self.is_devil(player, actual_round)
        period = SPEED_ZONE_PERIOD_DEVIL if devil else SPEED_ZONE_PERIOD
        step = int(elapsed / period)
        centers = self.speed_centers.setdefault((actual_round, player.ident), [])
        while len(centers) <= step:
            center = self.rng.randint(0, 19)
            # The zone must move far enough to be a new target
            while centers and min((center - centers[-1]) % 20, (centers[-1] - center) % 20) < SPEED_ZONE_SIZE:
                center = self.rng.randint(0, 19)
            centers.append(center)
        first = centers[step] - SPEED_ZONE_SIZE // 2
        return [self.target_order[(first + index) % 20] for index in range(SPEED_ZONE_SIZE)]

    def update_speed_zone(self, actual_round, player):
        """
        Speed Challenge : light the current zone and wake up the main loop only when
        the zone has to move (each wake up resends the leds to the leds server, so
        frequent wake ups would make the leds lag behind)
        """
        elapsed = self.elapsed(player)
        zone = self.speed_zone(actual_round, player, elapsed)
        if zone != self.speed_zone_shown:
            self.speed_zone_shown = zone
            self.rpi.set_target_leds('|'.join(self.leds(zone, 'green')))
        period = SPEED_ZONE_PERIOD_DEVIL if self.is_devil(player, actual_round) else SPEED_ZONE_PERIOD
        self.time = max(20, int((period - elapsed % period) * 1000) + 20)

    def draw_overlay(self):
        """
        Draw a frame of the current animation (stop it when it is over)
        """
        if self.overlay is not None and not self.overlay.frame():
            self.stop_overlay()

    def freeze_digit(self, player, actual_round, digit):
        """
        Fortune Digits : record the digit stopped by a dart (or 0 for a missed dart)
        """
        index = len(player.yy_digits)
        if index > 2:
            return
        player.yy_digits.append(digit)
        if isinstance(self.overlay, DigitsRoller):
            self.overlay.freeze(index, digit)
        player.yy_score = sum(value * 10 ** position for position, value in enumerate(player.yy_digits))
        player.yy_display = f"{player.yy_score:03d}"

    def send_dmd(self, player, actual_round):
        """
        DMD after a dart of a timing game, sent by the game itself (see display_dmd) :
        Fortune Digits : the frozen digits, hundreds on the left ('X - 7 - 5')
        Zero Stop : counter when the dart hit the board
        Always text messages : the DMD ignores the score format after a text message (tested on the cabinet)
        """
        try:
            if self.mini_game(actual_round) == 'FORTUNE_DIGITS':
                digits = ['X'] * (3 - len(player.yy_digits)) + [str(digit) for digit in reversed(player.yy_digits)]
                self.dmd.send_text(' - '.join(digits))
            elif player.yy_display in ('', '-'):
                self.dmd.send_text('-')
            else:
                self.dmd.send_text(f"{player.yy_display} s")
        except Exception as exception: # pylint: disable=broad-except
            self.logs.log("ERROR", f"Yum Yum : unable to send to DMD : {exception}")

    def display_segment(self):
        """
        No hit message over the timing games displays
        """
        if self.programme is not None and self.mini_game(self.current_round) in SILENT_HIT_GAMES:
            return False
        return self.show_segment

    def display_dmd(self):
        """
        The timing games send their own DMD text (see send_dmd) : the hit is not sent
        """
        if self.programme is not None and self.mini_game(self.current_round) in SILENT_HIT_GAMES:
            return False
        return self.show_dmd

    def build_programme(self, players):
        """
        Draw the mini-games of the whole game
        """
        pool = [key for key, value in MINI_GAMES.items()
                if self.timing_games or not value.get('timing', False)]
        self.programme = self.rng.sample(pool, min(self.max_round, len(pool)))
        while len(self.programme) < self.max_round:
            self.programme.append(self.rng.choice(pool))
        self.round_params = {}
        self.turn_params = {}
        self.dart_params = {}
        self.speed_centers = {}
        self.resolved = []
        self.chosen = []
        self.winner = -1
        for player in players:
            player.score = 0
            player.lost_rounds = 0
            player.devil_count = 0
            player.reset_rounds(self.max_round)
            player.columns[6] = ('', 'txt')
        self.logs.log("DEBUG", f"Yum Yum programme : {self.programme}")

    def solo_goal(self, actual_round):
        """
        Solo : minimum score of the manche (None if not relevant)
        """
        if not self.solo:
            return None
        mini_game = self.mini_game(actual_round)
        if MINI_GAMES[mini_game]['mode'] != 'low':
            return None
        if mini_game == 'COUNT_UP_ONLY':
            return 2 * self.get_round_params(actual_round)['target']
        return SOLO_GOALS.get(mini_game)

    def solo_goal_text(self, actual_round):
        """
        Solo goal as displayed ('>=60', '<=0.50s')
        """
        goal = self.solo_goal(actual_round)
        if goal is None:
            return ''
        if self.mini_game(actual_round) == 'ZERO_STOP':
            return f"<={-goal / 100:.2f}s"
        return f">={goal}"

    def choice_labels(self):
        """
        Labels of the choice menu : 20 mini-games + random
        """
        labels = []
        for index, key in enumerate(MINI_GAMES):
            name = self.tr(f'Yum_Yum-name-{key}', MINI_GAMES[key]['name']).replace('{target}', 'X')
            labels.append((key, f"{index + 1}. {name}"))
        labels.append((None, f"Bull. {self.tr('Yum_Yum-random', 'HASARD')}"))
        return labels

    def draw_choice_menu(self, actual_round, labels, allowed, selected):
        """
        Draw the mini-game choice menu in a centered window, return click zones
        """
        display = self.display
        if actual_round == 1:
            # No game screen yet behind the window
            display.display_background()
        box_w = int(display.res_x * CHOICE_WIDTH)
        box_h = int(display.res_y * CHOICE_HEIGHT)
        box_x = int((display.res_x - box_w) / 2)
        box_y = int((display.res_y - box_h) / 2)
        padding = int(box_h / 40)
        title_h = int(box_h * 0.09)
        help_h = int(box_h * 0.06)
        back_h = int(box_h * 0.09)
        text_color = display.colorset['game-title2']
        display.blit_rect(box_x, box_y, box_w, box_h, (15, 15, 15), border=4, Alpha=240)
        display.blit_text(self.tr('Yum_Yum-choose-title', 'Manche {round}/{max} : choisissez le mini-jeu').format(
                round=actual_round, max=self.max_round), box_x, box_y + padding, box_w, title_h, color=text_color)
        display.blit_text(self.tr('Yum_Yum-choose-help', 'Lancez une flechette sur le numero du jeu (Bull = hasard)'),
                box_x, box_y + padding + title_h, box_w, help_h, color=text_color)

        rows = -(-len(labels) // CHOICE_COLUMNS)
        grid_y = box_y + 2 * padding + title_h + help_h
        grid_h = box_h - (grid_y - box_y) - back_h - 2 * padding
        cell_w = int((box_w - 2 * padding) / CHOICE_COLUMNS)
        cell_h = int(grid_h / rows)
        zones = {}
        for index, (key, label) in enumerate(labels):
            pos_x = box_x + padding + (index % CHOICE_COLUMNS) * cell_w
            pos_y = grid_y + (index // CHOICE_COLUMNS) * cell_h
            background = (0, 110, 0) if index + 1 == selected else (40, 40, 40)
            display.blit_rect(pos_x + 2, pos_y + 2, cell_w - 4, cell_h - 4, background, border=2, Alpha=255)
            enabled = key is None or key in allowed
            display.blit_text(label, pos_x + 2, pos_y + 2, cell_w - 4, cell_h - 4, \
                    color=text_color if enabled else (110, 110, 110))
            zones[str(index + 1)] = (pos_x, pos_y, cell_w, cell_h)

        # Back button : cancel the game
        back_w = int(box_w / 3)
        back_x = box_x + int((box_w - back_w) / 2)
        back_y = box_y + box_h - back_h - padding
        background = (130, 0, 0) if selected == len(labels) + 1 else (40, 40, 40)
        display.blit_rect(back_x, back_y, back_w, back_h, background, border=2, Alpha=255)
        display.blit_text(self.tr('Yum_Yum-back', 'Retour'), back_x, back_y, back_w, back_h, color=text_color)
        zones['back'] = (back_x, back_y, back_w, back_h)

        display.update_screen()
        return zones

    def choose_mini_game(self, actual_round):
        """
        Let the players choose the mini-game of the manche.
        Dart on a number (1-20) = mini-game, Bull = random. Keyboard arrows / enter / click also work.
        Return CHOICE_BACK if the players want to leave the game.
        """
        labels = self.choice_labels()
        allowed = [key for key, value in MINI_GAMES.items()
                   if self.timing_games or not value.get('timing', False)]
        back = len(labels) + 1
        selected = 1
        while True:
            zones = self.draw_choice_menu(actual_round, labels, allowed, selected)
            key = self.rpi.listen_inputs(['arrows'],
                    ['enter', 'single-click', 'PLAYERBUTTON', 'GAMEBUTTON', 'resize', 'TOGGLEFULLSCREEN'],
                    context='game')
            choice = False
            by_dart = False
            if isinstance(key, tuple):
                clicked = self.display.is_clicked(zones, key)
                if clicked == 'back':
                    return CHOICE_BACK
                if clicked:
                    selected = int(clicked)
                    choice = labels[selected - 1][0]
            elif isinstance(key, str):
                hit = key.upper()
                if key in ('GAMEBUTTON', 'BTN_GAMEBUTTON', 'BTN_BACK', 'BTN_CANCEL', 'escape'):
                    return CHOICE_BACK
                if hit in ('SB', 'DB'):
                    choice, by_dart = None, True
                elif len(hit) > 1 and hit[0] in 'SDT' and hit[1:].isdigit() and 1 <= int(hit[1:]) <= 20:
                    choice, by_dart = labels[int(hit[1:]) - 1][0], True
                elif key in ('enter', 'PLAYERBUTTON', 'BTN_VALIDATE', 'BTN_NEXTPLAYER'):
                    if selected == back:
                        return CHOICE_BACK
                    choice = labels[selected - 1][0]
                elif key in ('left', 'BTN_LEFT'):
                    selected = (selected - 2) % back + 1
                elif key in ('right', 'BTN_RIGHT'):
                    selected = selected % back + 1
                elif key in ('up', 'BTN_UP'):
                    if selected == back:
                        selected = len(labels)
                    else:
                        selected = back if selected <= CHOICE_COLUMNS else selected - CHOICE_COLUMNS
                elif key in ('down', 'BTN_DOWN'):
                    if selected == back:
                        selected = 1
                    else:
                        selected = back if selected + CHOICE_COLUMNS > len(labels) else selected + CHOICE_COLUMNS
            if choice is False:
                continue
            if choice is None:
                choice = self.rng.choice(allowed)
            elif choice not in allowed:
                self.display.play_sound('plouf')
                continue
            self.display.play_sound('next_player')
            if by_dart:
                # The dart used to choose must be removed before playing
                self.display.press_player(self.tr('Yum_Yum-remove-dart', 'Retirez la flechette et appuyez sur Joueur'))
                while self.rpi.listen_inputs([], ['enter', 'PLAYERBUTTON'], context='game') \
                        not in ('enter', 'PLAYERBUTTON', 'BTN_VALIDATE', 'BTN_NEXTPLAYER'):
                    pass
            self.logs.log("DEBUG", f"Yum Yum : round {actual_round} chosen mini-game {choice}")
            return choice

    def leave_game(self):
        """
        Back button of the choice menu : interrupt the game like the Game button does
        (RaspyDarts then goes back to its main menu). A Game button key press is
        simulated, the main loop reads it while waiting for the next dart.
        """
        self.logs.log("DEBUG", "Yum Yum : game left from the mini-game choice menu")
        try:
            import pygame # pylint: disable=import-outside-toplevel
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode='', mod=0))
        except Exception as exception: # pylint: disable=broad-except
            self.logs.log("ERROR", f"Yum Yum : unable to leave the game : {exception}")

    def get_round_params(self, actual_round):
        """
        Random values shared by all players of a manche
        """
        if actual_round not in self.round_params:
            mini_game = self.mini_game(actual_round)
            params = {}
            if mini_game in ('DOUBLE_CHALLENGE', 'TRIPLE_CHALLENGE'):
                params['targets'] = self.rng.sample(range(1, 21), 3)
            elif mini_game in ('COUNT_UP_ONLY', 'ONE_SHOT'):
                params['target'] = self.rng.randint(1, 20)
            elif mini_game == 'PLUS_MINUS_COUNT_UP':
                params['plus'] = self.rng.sample(range(1, 21), 10)
            self.round_params[actual_round] = params
        return self.round_params[actual_round]

    def get_turn_params(self, actual_round, player):
        """
        Random values for a player's turn
        """
        key = (actual_round, player.ident)
        if key not in self.turn_params:
            mini_game = self.mini_game(actual_round)
            params = {'devil': self.devil and self.rng.randint(1, 100) <= self.devil_chance}
            if mini_game == 'HIGH_OR_LOW':
                params['condition'] = self.rng.choice(['HIGH', 'LOW'])
                if params['condition'] == 'HIGH':
                    params['target'] = self.rng.randrange(90, 155, 5) + (30 if params['devil'] else 0)
                else:
                    params['target'] = self.rng.randint(15, 30) - (6 if params['devil'] else 0)
            self.turn_params[key] = params
        return self.turn_params[key]

    def get_dart_params(self, actual_round, player, player_launch):
        """
        Random values for a single dart
        """
        key = (actual_round, player.ident, player_launch)
        if key not in self.dart_params:
            mini_game = self.mini_game(actual_round)
            devil = self.is_devil(player, actual_round)
            params = {}
            if mini_game == 'FORTUNE_COUNT_UP':
                pool = [-1, 0, 1, 2, 3, 5] if devil else [0, 1, 1, 2, 2, 3, 5]
                params['mult'] = self.rng.choice(pool)
            elif mini_game == 'MOVING_BULL':
                params['target'] = self.rng.randint(1, 20)
            elif mini_game == 'MOVING_OUT_BOARD':
                # The OUT zone grows each dart
                if player_launch == 1:
                    size = OUT_START_DEVIL if devil else OUT_START
                    params['out'] = self.rng.sample(range(1, 21), size)
                else:
                    previous = self.get_dart_params(actual_round, player, player_launch - 1)['out']
                    free = [num for num in range(1, 21) if num not in previous]
                    grow = OUT_GROW_DEVIL if devil else OUT_GROW
                    params['out'] = previous + self.rng.sample(free, min(grow, len(free) - 1))
            elif mini_game == 'SPINNING_TARGET':
                numbers = self.rng.sample(range(1, 21), 5)
                params['gold'] = numbers[:2]
                params['blue'] = numbers[2:]
            self.dart_params[key] = params
        return self.dart_params[key]

    def rule_text(self, players, actual_round, actual_player, player_launch):
        """
        Return (title, rule) for current dart
        """
        mini_game = self.mini_game(actual_round)
        player = players[actual_player]
        devil = self.is_devil(player, actual_round)
        values = {}
        values.update(self.get_round_params(actual_round))
        values.update(self.get_turn_params(actual_round, player))
        values.update(self.get_dart_params(actual_round, player, player_launch))
        if devil and mini_game in ('DOUBLE_CHALLENGE', 'TRIPLE_CHALLENGE'):
            values['targets'] = values['targets'][:1]
        if 'out' in values:
            values['count'] = len(values['out'])
        if mini_game == 'MULTIPLE_COUNT_UP':
            values['mult'] = player.yy_chain
        if mini_game == 'HIGH_OR_LOW':
            values['sign'] = self.tr('Yum_Yum-more-than', 'plus de') if values['condition'] == 'HIGH' \
                    else self.tr('Yum_Yum-less-than', 'moins de')
        for key in ('targets', 'gold', 'blue', 'out'):
            if key in values:
                values[key] = ' '.join(str(num) for num in values[key])
        if 'out' in values:
            values['targets'] = values['out']

        title = self.tr(f'Yum_Yum-name-{mini_game}', MINI_GAMES[mini_game]['name'])
        if devil:
            rule = self.tr(f'Yum_Yum-devil-{mini_game}', MINI_GAMES[mini_game]['devil'])
        else:
            rule = self.tr(f'Yum_Yum-rule-{mini_game}', MINI_GAMES[mini_game]['rule'])
        try:
            title = title.format(**values)
            rule = rule.format(**values)
        except (KeyError, IndexError, ValueError):
            pass
        if self.solo_goal(actual_round) is not None:
            rule = f"{rule} ({self.tr('Yum_Yum-goal', 'objectif')} {self.solo_goal_text(actual_round)})"
        if devil:
            title = f'DEVIL - {title}'
        if actual_round >= self.max_round:
            title = f"{title} - {self.tr('Yum_Yum-last-round', 'LAST ROUND x2')}"
        return title, rule

    def leds(self, numbers, color, mults='SDT'):
        """
        Build leds list for numbers ('B' for bull)
        """
        result = []
        for num in numbers:
            if num == 'B':
                result += [f'SB#{color}', f'DB#{color}']
            else:
                result += [f'{mult}{num}#{color}' for mult in mults]
        return result

    def set_leds(self, players, actual_round, actual_player, player_launch):
        """
        Light the target according to the mini-game
        """
        mini_game = self.mini_game(actual_round)
        player = players[actual_player]
        devil = self.is_devil(player, actual_round)
        round_params = self.get_round_params(actual_round)
        dart_params = self.get_dart_params(actual_round, player, player_launch)
        leds = []
        blink = []
        if mini_game == 'BULL_CHALLENGE':
            leds = ['DB#green'] if devil else self.leds(['B'], 'green')
        elif mini_game in ('DOUBLE_CHALLENGE', 'TRIPLE_CHALLENGE'):
            targets = round_params['targets'][:1] if devil else round_params['targets']
            leds = self.leds(targets, 'red' if devil else 'green', mini_game[0])
        elif mini_game == 'NO_BULL_COUNT_UP':
            blink = self.leds(['B'], 'red')
        elif mini_game in ('CENTER_COUNT_UP', 'ONE_DART_CENTER_COUNT_UP'):
            leds = self.leds(['B'], 'green')
        elif mini_game == 'COUNT_UP_ONLY':
            leds = self.leds([round_params['target']], 'green', 'DT' if devil else 'SDT')
        elif mini_game == 'ONE_SHOT':
            blink = self.leds([round_params['target']], 'green', 'DT' if devil else 'SDT')
        elif mini_game == 'PLUS_MINUS_COUNT_UP':
            leds = self.leds(round_params['plus'], 'green') \
                    + self.leds([num for num in range(1, 21) if num not in round_params['plus']], 'red')
        elif mini_game == 'MOVING_BULL':
            blink = self.leds([dart_params['target']], 'gold', 'DT' if devil else 'SDT')
        elif mini_game == 'MOVING_OUT_BOARD':
            leds = self.leds(dart_params['out'], 'red')
        elif mini_game == 'SPINNING_TARGET':
            leds = self.leds(dart_params['gold'], 'gold') + self.leds(dart_params['blue'], 'blue')
        elif mini_game == 'SPEED_CHALLENGE':
            self.speed_zone_shown = self.speed_zone(actual_round, player, self.elapsed(player))
            leds = self.leds(self.speed_zone_shown, 'green')
        self.rpi.set_target_leds('|'.join(leds))
        self.rpi.set_target_leds_blink('|'.join(blink))

    def col_display(self, player):
        """
        Display manche score in column 4
        """
        if player.yy_display != '':
            player.columns[4] = (player.yy_display, 'str')
        else:
            player.columns[4] = (player.yy_score, 'int')

    ##############
    # Scoring
    ##############
    def score_dart(self, hit, player, actual_round, player_launch):
        """
        Compute a dart. Return (value displayed, good hit, end of turn)
        """
        mini_game = self.mini_game(actual_round)
        devil = self.is_devil(player, actual_round)
        round_params = self.get_round_params(actual_round)
        turn_params = self.get_turn_params(actual_round, player)
        dart_params = self.get_dart_params(actual_round, player, player_launch)
        points = self.get_score_from_hit(hit)
        mult, _ = self.split_key(hit, multiplier=True)
        number = self.number(hit)
        value = 0
        end_turn = False

        if mini_game == 'BULL_CHALLENGE':
            if hit == 'DB':
                value = 2
            elif hit == 'SB' and not devil:
                value = 1
            player.yy_score += value

        elif mini_game in ('DOUBLE_CHALLENGE', 'TRIPLE_CHALLENGE'):
            targets = round_params['targets'][:1] if devil else round_params['targets']
            if hit[:1] == mini_game[0] and number in targets:
                value = 1
            player.yy_score += value

        elif mini_game == 'NO_BULL_COUNT_UP':
            if self.is_bull(hit):
                player.yy_score = 0
                end_turn = devil
                self.col_display(player)
                return 'BULL', False, end_turn
            value = points
            player.yy_score += value

        elif mini_game in ('COUNT_UP', 'ONE_DART_COUNT_UP'):
            value = 0 if devil and self.is_single(hit) else points
            player.yy_score += value

        elif mini_game in ('CENTER_COUNT_UP', 'ONE_DART_CENTER_COUNT_UP'):
            if self.is_bull(hit):
                value = CENTER_POINTS[hit]
            elif not devil:
                value = CENTER_POINTS[hit[:1]]
            player.yy_score += value

        elif mini_game == 'COUNT_UP_ONLY':
            if number == round_params['target'] and not (devil and self.is_single(hit)):
                value = points
            player.yy_score += value

        elif mini_game == 'FORTUNE_COUNT_UP':
            value = points * dart_params['mult']
            player.yy_score += value

        elif mini_game == 'MULTIPLE_COUNT_UP':
            value = points * player.yy_chain
            player.yy_score += value
            if hit[:1] in ('D', 'T') or self.is_bull(hit):
                player.yy_chain *= 2
            elif devil:
                player.yy_chain = 1

        elif mini_game == 'PLUS_MINUS_COUNT_UP':
            if number == 'B' or number in round_params['plus']:
                value = points
            else:
                value = -points * (2 if devil else 1)
            player.yy_score += value

        elif mini_game == 'HIGH_OR_LOW':
            value = points
            player.yy_score += value
            sign = '>' if turn_params['condition'] == 'HIGH' else '<'
            if turn_params['condition'] == 'LOW' and player.yy_score >= turn_params['target']:
                # Already lost
                player.yy_failed = True
                end_turn = True
            player.yy_display = f"{player.yy_score}{sign}{turn_params['target']}"

        elif mini_game == 'MOVING_BULL':
            if number == dart_params['target'] and not (devil and mult == 1):
                value = mult
            player.yy_score += value

        elif mini_game == 'MOVING_OUT_BOARD':
            if number in dart_params['out']:
                player.yy_failed = True
                player.yy_display = 'OUT'
                self.col_display(player)
                return 'OUT', False, True
            value = points
            player.yy_score += value

        elif mini_game == 'SPINNING_TARGET':
            if number in dart_params['gold']:
                factor = 4
            elif number in dart_params['blue']:
                factor = 2
            else:
                factor = 0 if devil else 1
            value = points * factor
            player.yy_score += value

        elif mini_game == 'FORTUNE_DIGITS':
            # 1st dart : units, 2nd : tens, 3rd : hundreds
            if isinstance(self.overlay, DigitsRoller) and self.overlay.last_elapsed is not None:
                # The digit displayed when the dart hit the board
                value = rolling_digit(self.overlay.last_elapsed, len(player.yy_digits), devil)
            elif player.yy_chrono is None:
                value = 0
            else:
                value = rolling_digit(self.dart_time - player.yy_chrono, len(player.yy_digits), devil)
            self.freeze_digit(player, actual_round, value)
            self.col_display(player)
            return value, True, False

        elif mini_game == 'ZERO_STOP':
            if player.yy_chrono is None:
                remaining = None
            else:
                remaining = ZERO_STOP_DURATION - (self.dart_time - player.yy_chrono)
            if remaining is None:
                player.yy_score = WORST_SCORE
                player.yy_display = '-'
            elif remaining >= 0:
                player.yy_score = -int(remaining * 100)
                player.yy_display = f"{remaining:.2f}"
            else:
                # Too late : ranked after all players who stopped in time
                player.yy_score = WORST_SCORE + 1000 + int(remaining * 100)
                player.yy_display = f"{remaining:.2f}"
            self.col_display(player)
            return player.yy_display, remaining is not None and remaining >= 0, True

        elif mini_game == 'SPEED_CHALLENGE':
            # The zone lit when the dart hit the board
            if number in self.speed_zone_shown:
                value = 1
            player.yy_score += value

        elif mini_game == 'ONE_SHOT':
            if number == round_params['target'] and not (devil and mult == 1):
                value = 1
                player.yy_score = 1

        self.col_display(player)
        return value, value > 0, end_turn

    def apply_miss(self, player, actual_round, player_launch):
        """
        Effects of a missed (or not thrown) dart
        """
        if player_launch in player.yy_launches or player.yy_round != actual_round:
            return
        player.yy_launches.append(player_launch)
        player.columns[player_launch - 1] = ('MISS', 'str')
        mini_game = self.mini_game(actual_round)
        if mini_game == 'MOVING_OUT_BOARD':
            player.yy_failed = True
            player.yy_display = 'OUT'
        elif mini_game == 'HIGH_OR_LOW' \
                and self.get_turn_params(actual_round, player)['condition'] == 'LOW':
            # In LOW, every dart must land on the board
            player.yy_failed = True
        elif mini_game == 'MULTIPLE_COUNT_UP':
            player.yy_chain = 1
        elif mini_game == 'FORTUNE_DIGITS':
            self.freeze_digit(player, actual_round, 0)
        self.col_display(player)

    def player_failed(self, player, actual_round):
        """
        For 'fail' mini-games : did the player fail ?
        """
        if player.yy_round != actual_round:
            return True
        mini_game = self.mini_game(actual_round)
        if mini_game == 'MOVING_OUT_BOARD':
            return player.yy_failed
        if mini_game == 'HIGH_OR_LOW':
            turn_params = self.get_turn_params(actual_round, player)
            if player.yy_failed:
                return True
            if turn_params['condition'] == 'HIGH':
                return player.yy_score <= turn_params['target']
            return player.yy_score >= turn_params['target']
        if mini_game == 'ONE_SHOT':
            return player.yy_score < 1
        return False

    def end_of_turn(self, players, actual_round, actual_player):
        """
        Player's turn is over.
        Return 3 (winner) or 2 (deuce) at the end of the game, 1 otherwise
        """
        player = players[actual_player]
        if self.mini_game(actual_round) == 'FORTUNE_DIGITS' and self.overlay is not None:
            self.stop_overlay()
            self.display.message([player.yy_display], 2000, 'game-green', 'middle', 'huge')
        if isinstance(self.overlay, SpeedOverlay):
            self.stop_overlay()

        if actual_round >= self.max_round and actual_player == len(players) - 1:
            self.resolve_round(players, actual_round)
            return 3 if self.winner not in (None, -1) else 2
        return 1

    def resolve_round(self, players, actual_round):
        """
        Give drink points to the losers of the manche (only once per manche)
        """
        if actual_round in self.resolved or self.programme is None:
            return
        self.resolved.append(actual_round)
        mini_game = self.mini_game(actual_round)

        if MINI_GAMES[mini_game]['mode'] == 'fail':
            losers = [player for player in players if self.player_failed(player, actual_round)]
        elif self.solo:
            goal = self.solo_goal(actual_round)
            losers = [player for player in players
                      if player.yy_round != actual_round or player.yy_score < goal]
        else:
            scores = {player.ident: (player.yy_score if player.yy_round == actual_round else WORST_SCORE)
                      for player in players}
            lowest = min(scores.values())
            losers = [player for player in players if scores[player.ident] == lowest]

        messages = [self.mini_game_name(actual_round)]
        for player in players:
            devil = self.is_devil(player, actual_round)
            if devil:
                player.devil_count += 1
            if player in losers:
                penalty = PENALTY
                if actual_round >= self.max_round:
                    penalty *= LAST_ROUND_MULT
                if devil:
                    penalty *= DEVIL_MULT
                player.score += penalty
                player.lost_rounds += 1
                player.columns[6] = (f'+{penalty}', 'str', 'game-red')
                messages.append(f"{player.name} : +{penalty} Drink")
            else:
                player.columns[6] = ('', 'txt')
        if len(losers) == 0:
            messages.append(self.tr('Yum_Yum-nobody-drinks', 'Personne ne boit !'))

        self.logs.log("DEBUG", f"Yum Yum round {actual_round} ({mini_game}) : {' / '.join(messages)}")
        self.refresh_stats(players, actual_round)
        if actual_round >= self.max_round:
            self.winner = self.find_winner(players)
        self.display.play_sound('whatamess' if losers else 'next_player')
        # DMD : result of the manche until the next player (see dmd_turn_text)
        try:
            self.dmd.send_text(' / '.join(messages[1:]))
        except Exception as exception: # pylint: disable=broad-except
            self.logs.log("ERROR", f"Yum Yum : unable to send to DMD : {exception}")
        self.display.message(messages, 3500, None, 'middle', None)

    def mini_game_name(self, actual_round):
        """
        Name of the mini-game of a manche ('COUNT-UP ONLY 20')
        """
        mini_game = self.mini_game(actual_round)
        return self.tr(f'Yum_Yum-name-{mini_game}', MINI_GAMES[mini_game]['name']).replace(
            '{target}', str(self.get_round_params(actual_round).get('target', '')))

    def dmd_turn_text(self, players, actual_round, actual_player):
        """
        DMD before the first dart of a player : player and mini-game ('Kekus - ZERO STOP')
        """
        name = players[actual_player].name
        if self.programme is None:
            return name
        try:
            return f"{name} - {self.mini_game_name(actual_round)}"
        except Exception as exception: # pylint: disable=broad-except
            self.logs.log("ERROR", f"Yum Yum : unable to build the DMD text : {exception}")
            return name

    def find_winner(self, players):
        """
        Fewest drink points wins (tie-break : fewest lost manches)
        """
        ranking = sorted(players, key=lambda player: (player.score, player.lost_rounds))
        if len(ranking) > 1 and (ranking[0].score, ranking[0].lost_rounds) \
                == (ranking[1].score, ranking[1].lost_rounds):
            return None
        return ranking[0].ident

    ##############
    # Game methods
    ##############
    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Before each throw - update screen, display score, etc...
        """
        self.infos = ''
        # Animation tick : the main loop calls pre_dart_check again (same dart) when
        # the dart wait times out (self.time > 0). Only the animation is redrawn.
        if self.overlay is not None and self.last_pre_dart == (actual_round, actual_player, player_launch):
            self.tick = True
            return 0
        self.last_pre_dart = (actual_round, actual_player, player_launch)
        player = players[actual_player]

        # New game (or new set)
        if self.programme is None or (actual_round == 1 and actual_player == 0 \
                and player_launch == 1 and len(self.resolved) > 0):
            self.build_programme(players)

        # Previous manche may not be resolved (if last player stopped early)
        if actual_round > 1:
            self.resolve_round(players, actual_round - 1)

        # Players choose the mini-game at the beginning of the manche
        if self.choose_game and actual_player == 0 and player_launch == 1 \
                and actual_round not in self.chosen:
            choice = self.choose_mini_game(actual_round)
            if choice == CHOICE_BACK:
                self.leave_game()
                return 0
            self.programme[actual_round - 1] = choice
            self.chosen.append(actual_round)
            self.round_params.pop(actual_round, None)

        mini_game = self.mini_game(actual_round)
        self.nb_darts = MINI_GAMES[mini_game]['darts']
        self.current_launch = player_launch
        self.current_round = actual_round

        if player_launch == 1:
            self.stop_overlay()
            player.reset_darts()
            self.save_turn(players)
            player.yy_round = actual_round
            player.yy_score = WORST_SCORE if mini_game == 'ZERO_STOP' else 0
            player.yy_failed = False
            player.yy_chain = 1
            player.yy_digits = []
            player.yy_launches = []
            player.yy_chrono = None
            player.yy_display = ''
            for column in range(0, 5):
                player.columns[column] = ('', 'txt')

            turn_params = self.get_turn_params(actual_round, player)
            if turn_params['devil']:
                player.columns[5] = ('DEVIL', 'str', 'game-red')
            else:
                player.columns[5] = ('', 'txt')
            if mini_game == 'HIGH_OR_LOW':
                sign = '>' if turn_params['condition'] == 'HIGH' else '<'
                player.columns[3] = (f"{sign}{turn_params['target']}", 'str')
            elif self.solo_goal(actual_round) is not None:
                player.columns[3] = (self.solo_goal_text(actual_round), 'str')
            elif mini_game in ('COUNT_UP_ONLY', 'ONE_SHOT'):
                player.columns[3] = (self.get_round_params(actual_round)['target'], 'int')

            # No announcement of the manche : round, mini-game and rule are on the game screen (top strip)
            if turn_params['devil']:
                self.display.play_sound('penality')
                self.display.message(['DEVIL MODE !', player.name], 2000, 'game-red', 'middle', 'big')

            if MINI_GAMES[mini_game].get('timing', False):
                # Chrono starts when the game screen is displayed
                self.chrono_pending = True

        self.set_leds(players, actual_round, actual_player, player_launch)
        self.logs.log("DEBUG", f"Yum Yum : round {actual_round} {mini_game} / player {actual_player} / dart {player_launch}")
        return 0

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        After each dart
        """
        # Keep the exact time of the dart before anything else (timing games)
        self.dart_time = time.monotonic()
        self.last_pre_dart = None
        if isinstance(self.overlay, Countdown):
            self.stop_overlay()
        handler = self.init_handler()
        player = players[actual_player]

        if player_launch in player.yy_launches:
            return handler
        player.yy_launches.append(player_launch)

        value, good, end_turn = self.score_dart(hit, player, actual_round, player_launch)

        if self.mini_game(actual_round) == 'ZERO_STOP' and player.yy_chrono is not None:
            if good:
                self.display.message([f"{player.yy_display} s"], 2000, 'game-green', 'middle', 'big')
            else:
                self.display.message([self.tr('Yum_Yum-too-late', 'TROP TARD !'), f"{player.yy_display} s"], \
                        2000, 'game-red', 'middle', 'big')

        if isinstance(value, int):
            player.columns[player_launch - 1] = (value, 'int')
            player.add_dart(actual_round, player_launch, hit, score=value)
            player.points += value
        else:
            player.columns[player_launch - 1] = (value, 'str')
            player.add_dart(actual_round, player_launch, hit)

        handler['sound'] = hit if good else 'plouf'
        if self.mini_game(actual_round) in SILENT_HIT_GAMES:
            # The hit does not count : no voice saying it, a neutral impact sound instead
            handler['sound'] = SILENT_HIT_SOUND if good else 'plouf'
            self.send_dmd(player, actual_round)

        if end_turn or player_launch >= self.nb_darts:
            # Not thrown darts are missed darts
            for launch in range(player_launch + 1, self.nb_darts + 1):
                self.apply_miss(player, actual_round, launch)
            return_code = self.end_of_turn(players, actual_round, actual_player)
            if return_code in (2, 3) or end_turn:
                handler['return_code'] = return_code

        self.refresh_stats(players, actual_round)
        return handler

    def post_round_check(self, players, actual_round, actual_player):
        """
        All players have played the manche
        """
        self.resolve_round(players, actual_round)
        if actual_round >= self.max_round:
            return self.winner if self.winner not in (None, -1) else -1
        return -2

    def early_player_button(self, players, actual_player, actual_round):
        """
        Player button pushed before last dart : remaining darts are missed
        """
        self.last_pre_dart = None
        if isinstance(self.overlay, Countdown):
            self.stop_overlay()
        player = players[actual_player]
        for launch in range(self.current_launch, self.nb_darts + 1):
            self.apply_miss(player, actual_round, launch)
        return self.end_of_turn(players, actual_round, actual_player)

    def miss_button(self, players, actual_player, actual_round, player_launch):
        """
        Missed dart
        """
        self.last_pre_dart = None
        if isinstance(self.overlay, Countdown):
            self.stop_overlay()
        player = players[actual_player]
        already_done = player_launch in player.yy_launches
        self.apply_miss(player, actual_round, player_launch)
        player.darts_thrown += 1
        if player_launch >= self.nb_darts and not already_done:
            return_code = self.end_of_turn(players, actual_round, actual_player)
            if return_code in (2, 3):
                return return_code
        return 0

    def refresh_game_screen(self, players, actual_round, max_round, rem_darts, nb_darts, logo, headers, actual_player, TxtOnLogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
        """
        Standard screen + current mini-game rules under the title
        """
        self.display.ribbon_messages = True
        if self.tick:
            # Animation tick : only redraw the animation (fast, keeps the board reading responsive)
            self.tick = False
            if isinstance(self.overlay, SpeedOverlay):
                self.update_speed_zone(actual_round, players[actual_player])
            self.draw_overlay()
            return self.click_zones

        result = None
        arcade = self.programme is not None and not end_of_game and endOfSet is None
        if arcade:
            try:
                result = self.arcade_screen(players, actual_round, logo, actual_player, OnScreenButtons)
                if Wait:
                    pygame.time.wait(Wait)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.log("ERROR", f"Yum Yum : arcade screen unavailable : {exception}")
                arcade = False
        if not arcade:
            result = self.classic_screen(players, actual_round, max_round, rem_darts, nb_darts, logo, headers, \
                    actual_player, TxtOnLogo, Wait, OnScreenButtons, showScores, end_of_game, endOfSet, Set, MaxSet)
        self.start_animations(players, actual_round, actual_player, rem_darts, end_of_game, endOfSet)
        self.click_zones = result
        return result

    def arcade_screen(self, players, actual_round, logo, actual_player, onscreen_buttons):
        """
        Game screen : tags on the top, rule, one LED card per player (see ArcadeScreen)
        """
        display = self.display
        display.define_constants(len(players))
        display.reset_background()
        background = display.file_class.get_full_filename(f"background_{logo.replace(' ', '_').split('.')[0]}", \
                'images')
        if background is not None:
            display.display_background(image=background)
        else:
            display.display_background()
        if display.colorset['game-bg'] is not None:
            display.blit_rect(0, 0, display.res_x, display.res_y, display.colorset['game-bg'])
        if display.game_type == 'online' and display.t_event is not None:
            display.create_thread(rect_array=[(int(display.res_x / 2 - 110), display.margin + int(display.res_y / 5), \
                    int(display.res_y / 36), int(display.res_y / 36))])

        player = players[actual_player]
        mini_game = self.mini_game(actual_round)
        devil = self.is_devil(player, actual_round)
        title, rule = self.rule_text(players, actual_round, actual_player, self.current_launch)
        options = []
        if self.devil:
            options.append((f"DEVIL {self.devil_chance} %", LED_RED))
        if self.timing_games:
            options.append(('TIMING', LED_CYAN))
        if self.choose_game:
            options.append((self.tr('Yum_Yum-choice-tag', 'CHOIX DES MINI-JEUX'), LED_MUTED))
        game_type = f"{display.game_type} game" if display.colorset.get('game-type') is not None else ''
        screen = ArcadeScreen(display)
        screen.top(f"{self.tr('Yum_Yum-round', 'Manche').upper()} {actual_round} / {self.max_round}", title, devil, \
                options, game_type, rule)

        nb_darts = MINI_GAMES[mini_game]['darts']
        cards = []
        for index, other in enumerate(players):
            this_round = other.yy_round == actual_round
            darts = []
            for launch in range(nb_darts):
                value = other.columns[launch][0] if this_round else ''
                darts.append(str(value) if value not in ('', None) else '-')
            score = other.columns[4][0] if this_round else ''
            target = other.columns[3][0] if this_round else ''
            cards.append({'name': other.name, 'color': ARCADE_PLAYER_COLORS[index % len(ARCADE_PLAYER_COLORS)],
                          'active': index == actual_player, 'devil': self.is_devil(other, actual_round),
                          'score': str(score) if score not in ('', None) else '',
                          'target': f"{self.tr('Yum_Yum-target', 'CIBLE')} {target}" if target not in ('', None) else '',
                          'darts': darts, 'drinks': f"DRINK {other.score}", 'drinking': other.score > 0})
        screen.cards(cards, self.tr('Yum_Yum-your-turn', 'A TOI'))

        click = None
        if onscreen_buttons is True or display.is_true(display.config.get_value('SectionGlobals', 'onscreenbuttons')):
            click = display.onscreen_buttons()
        display.save_background()
        display.update_screen()
        return click

    def classic_screen(self, players, actual_round, max_round, rem_darts, nb_darts, logo, headers, actual_player, \
            TxtOnLogo, Wait, OnScreenButtons, showScores, end_of_game, endOfSet, Set, MaxSet):
        """
        Standard screen + current mini-game rules under the title (end of game, or if the arcade screen fails)
        """
        result = self.display.refresh_game_screen(players, actual_round, max_round, rem_darts, \
                          nb_darts, logo, headers, actual_player, TxtOnLogo, Wait, OnScreenButtons, \
                          showScores, end_of_game, endOfSet, Set, MaxSet)

        if self.programme is not None and not end_of_game and endOfSet is None:
            try:
                title, rule = self.rule_text(players, actual_round, actual_player, self.current_launch)
                display = self.display
                pos_x = int(display.res_x / 2 - display.res_x / 6)
                width = int(display.res_x / 3)
                pos_y = display.margin + int(display.res_y / 5) + int(display.res_y / 36)
                height = int(display.res_y / 16)
                color = display.colorset['game-red'] if self.is_devil(players[actual_player], actual_round) \
                        else display.colorset['game-title2']
                display.blit_text(title, pos_x, pos_y, width, height, color=color)
                display.blit_text(rule, pos_x, pos_y + height, width, int(height * 0.8), \
                        color=display.colorset['game-title2'])
                display.update_screen()
            except Exception as exception: # pylint: disable=broad-except
                self.logs.log("ERROR", f"Yum Yum : unable to display rules : {exception}")
        return result

    def start_animations(self, players, actual_round, actual_player, rem_darts, end_of_game, endOfSet):
        """
        Start the chrono and the LED console of timing games once the screen is displayed,
        or draw the running animation over the refreshed screen
        """
        if self.chrono_pending and rem_darts > 0:
            self.chrono_pending = False
            players[actual_player].yy_chrono = time.monotonic()
            if self.mini_game(actual_round) == 'ZERO_STOP':
                hide_after = ZERO_STOP_HIDE_DEVIL if self.is_devil(players[actual_player], actual_round) \
                        else ZERO_STOP_HIDE
                goal = -SOLO_GOALS['ZERO_STOP'] / 100 if self.solo else None
                self.start_overlay(Countdown(self.display, players[actual_player].yy_chrono, hide_after, goal=goal, \
                        labels={'time': self.tr('Yum_Yum-time-left', 'TEMPS RESTANT'), \
                                'hidden': self.tr('Yum_Yum-timer-hidden', 'CHRONO MASQUE'), \
                                'goal': self.tr('Yum_Yum-goal', 'OBJECTIF'), \
                                'title': self.tr('Yum_Yum-stop-at', 'STOP A 0.00')}, \
                        devil=self.is_devil(players[actual_player], actual_round)), player=players[actual_player])
            elif self.mini_game(actual_round) == 'FORTUNE_DIGITS':
                self.start_overlay(DigitsRoller(self.display, players[actual_player].yy_chrono, \
                        self.is_devil(players[actual_player], actual_round)), player=players[actual_player])
            elif self.mini_game(actual_round) == 'SPEED_CHALLENGE':
                self.update_speed_zone(actual_round, players[actual_player])
                self.start_overlay(SpeedOverlay(self.display, players[actual_player].yy_chrono, \
                        lambda: self.speed_zone_shown), keep_time=True)
        elif not end_of_game and endOfSet is None:
            # Keep the animation over the refreshed screen
            if isinstance(self.overlay, SpeedOverlay):
                self.update_speed_zone(actual_round, players[actual_player])
            self.draw_overlay()

    def get_random(self, players, actual_round, actual_player, player_launch):
        """
        Network game : the master sends its seed
        """
        return self.seed

    def set_random(self, players, actual_round, actual_player, player_launch, data):
        """
        Network game : slaves use the master's seed (before the programme is drawn)
        """
        if data is not None and self.programme is None and data != self.seed:
            self.seed = data
            self.rng = random.Random(self.seed)

    def next_set_order(self, players, new_order=None):
        """
        Fewest drink points plays first
        """
        if new_order is not None:
            players.sort(key=lambda x: new_order.index(x.name))
        else:
            players.sort(key=lambda player: player.score)

    def refresh_stats(self, players, actual_round):
        """
        Method to refresh players' stats
        """
        for player in players:
            player.stats['Drink Points'] = player.score
            player.stats['Lost Rounds'] = player.lost_rounds
            player.stats['Devil Modes'] = player.devil_count
