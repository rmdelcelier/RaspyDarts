"""
Wizard of the first start, its easier steps :
- choose_card : the interface card chosen on tiles, as on the installation page of the web site
  (photo of the card when there is one, else a circuit drawn ; its maker), the old cards of
  Jimmy and Joffrey on a second screen, « other card » for a home-made wiring
- learn_buttons : the buttons wired on the extension cards (MCP23017) learnt by pressing them :
  a button pressed is detected, then the segment of its function touched on the target (drawn
  with the functions on its segments), or chosen with the arrows ; SB or DB : done
"""

import math
import os
import subprocess
import sys
import time

import pygame

from include import cpaths

IMAGES = os.path.join(cpaths.ROOT_DIR, 'images', 'wizard')

# The cards : name, maker, photo (images/wizard/<photo>.jpg) ; names as on the web site
CARDS = {
    'Ch': ('La Chti Raspycard', 'Pascal (ChtiDarts)', 'carte-ch'),
    'Lk': ('Linker', 'Julien', 'carte-linker'),
    'Lk+': ('Linker+', 'Julien', 'carte-linker-plus'),
    'Jt': ('Carte de Julien V1', 'Julien', None),
    'Jt2': ('Carte de Julien V2', 'Julien', None),
    'Mm': ('MM-Workshop DartCab', 'MM-Workshop', 'carte-mm'),
    'MMWVdarts': ('MM-Workshop VDarts', 'MM-Workshop', 'carte-mmwvdarts'),
    'Re': ('DartBoard', '', None),
    'Ji': ('RaspyCard', 'Jimmy', None),
    'Jiz': ('RaspyZcard', 'Jimmy', None),
    'Ji3': ('RaspYDartsCard', 'Jimmy', None),
    'Ji2': ('RaspyCard V4', 'Jimmy', None),
    'GB': ('RaspyBoard', 'Jimmy', None),
    'ED': ('ED900', 'Jimmy', None),
    'Jo': ('Cible ED110 7*10', 'Joffrey', None),
    'Jo416': ('Cible Pro 4*16', 'Joffrey', None),
}
CURRENT = ['Ch', 'Lk', 'Lk+', 'Mm', 'MMWVdarts', 'Re']
OLD = ['Ji', 'Jiz', 'Ji3', 'Ji2', 'GB', 'ED', 'Jo', 'Jo416', 'Jt', 'Jt2']
OTHER, OLD_TILE = 'Au', 'old'

# The functions of the buttons on the segments of the target : the 4 directions where they
# point (as the darts in the menus), Valider, Joueur suivant and Annuler on the diagonals, then
# a few more
BUTTON_SEGMENTS = {20: 'PIN_UP', 6: 'PIN_RIGHT', 3: 'PIN_DOWN', 11: 'PIN_LEFT',
                   4: 'PIN_VALIDATE', 2: 'PIN_NEXTPLAYER', 12: 'PIN_CANCEL',
                   16: 'PIN_BACK', 8: 'PIN_GAMEBUTTON', 13: 'PIN_VOLUME_UP',
                   10: 'PIN_VOLUME_DOWN', 17: 'PIN_VOLUME_MUTE', 1: 'PIN_PLUS', 5: 'PIN_MINUS'}
# In the order of the target (the arrows go round it)
FUNCTIONS = [BUTTON_SEGMENTS[number] for number in [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]
             if number in BUTTON_SEGMENTS]
# Names said by the wizard (what the button does) instead of the short names of the settings
WIZARD_LABELS = {'PIN_CANCEL': 'btnwiz-cancel', 'PIN_BACK': 'btnwiz-back', 'PIN_GAMEBUTTON': 'btnwiz-game'}
# The numbers of the target clockwise from the top
ORDER = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]
POLL = 0.02


def color(screen, name, default):
    value = screen.colorset.get(name)
    return tuple(value[:3]) if value else default


def keys_of_events(screen):
    '''
    Keyboard, mouse and touch of the moment : 'up', 'down', 'left', 'right', 'enter', 'escape',
    or a position (x, y) clicked
    '''
    found = []
    events = pygame.event.get()
    # The fingers read here : said to the reading of the inputs (the pointer stays hidden)
    if hasattr(screen, 'finger_seen'):
        screen.finger_seen(events)
    for event in events:
        if event.type == pygame.KEYDOWN:
            names = {pygame.K_UP: 'up', pygame.K_DOWN: 'down', pygame.K_LEFT: 'left', pygame.K_RIGHT: 'right',
                     pygame.K_RETURN: 'enter', pygame.K_KP_ENTER: 'enter', pygame.K_SPACE: 'enter',
                     pygame.K_ESCAPE: 'escape', pygame.K_BACKSPACE: 'escape'}
            if event.key in names:
                found.append(names[event.key])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and not getattr(event, 'touch', False):
            # (a touch : its FINGERUP below, not the mouse event SDL makes of it too)
            found.append(tuple(event.pos))
        elif event.type == getattr(pygame, 'FINGERUP', -1):
            found.append((int(event.x * screen.res_x), int(event.y * screen.res_y)))
    return found


# ---------------------------------------------------------------------------- the cards
def circuit(width, height):
    '''
    A card without photo : a circuit drawn (as on the web site)
    '''
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    board = pygame.Rect(int(width * 0.04), int(height * 0.06), int(width * 0.92), int(height * 0.88))
    pygame.draw.rect(surface, (29, 90, 56), board, border_radius=int(height * 0.07))
    gold = (217, 180, 74)
    for index in range(12):
        x = board.x + int(board.width * (0.08 + index * 0.072))
        pygame.draw.rect(surface, gold, (x, board.y + int(board.height * 0.06), int(board.width * 0.035), int(board.height * 0.09)))
    chip = pygame.Rect(board.x + int(board.width * 0.12), board.y + int(board.height * 0.38), int(board.width * 0.24), int(board.height * 0.36))
    pygame.draw.rect(surface, (21, 23, 28), chip, border_radius=4)
    for index in range(5):
        x = chip.x + int(chip.width * (0.12 + index * 0.18))
        pygame.draw.line(surface, gold, (x, chip.y), (x, chip.y - int(height * 0.04)), 2)
        pygame.draw.line(surface, gold, (x, chip.bottom), (x, chip.bottom + int(height * 0.04)), 2)
    for index in range(6):
        y = board.y + int(board.height * (0.3 + index * 0.1))
        pygame.draw.rect(surface, (42, 140, 82), (board.x + int(board.width * 0.72), y, int(board.width * 0.18), int(board.height * 0.05)))
    pygame.draw.lines(surface, (127, 208, 143), False, [(chip.right, chip.centery - 6), (board.x + int(board.width * 0.55), chip.centery - 6),
                                                         (board.x + int(board.width * 0.55), board.y + int(board.height * 0.3)),
                                                         (board.x + int(board.width * 0.7), board.y + int(board.height * 0.3))], 2)
    return surface


def symbol(width, height, kind):
    '''
    Tile without card : « other card » (a +) or « old cards » (cards one on the other)
    '''
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    if kind == OTHER:
        frame = pygame.Rect(int(width * 0.06), int(height * 0.08), int(width * 0.88), int(height * 0.84))
        pygame.draw.rect(surface, (200, 200, 200), frame, 3, border_radius=int(height * 0.08))
        size = int(min(width, height) * 0.16)
        pygame.draw.line(surface, (200, 200, 200), (frame.centerx - size, frame.centery), (frame.centerx + size, frame.centery), 6)
        pygame.draw.line(surface, (200, 200, 200), (frame.centerx, frame.centery - size), (frame.centerx, frame.centery + size), 6)
    else:
        for index, alpha in enumerate((110, 180, 255)):
            card = pygame.Rect(int(width * (0.22 - index * 0.06)), int(height * (0.14 + index * 0.1)), int(width * 0.6), int(height * 0.6))
            pygame.draw.rect(surface, (29, 90, 56, alpha), card, border_radius=int(height * 0.06))
    return surface


class Tiles:
    '''
    Tiles of a screen of the wizard : a visual, a name, a line under it ; one selected
    '''

    def __init__(self, screen, entries):
        self.screen = screen
        self.entries = entries    # [(code, visual surface maker, name, maker)]
        self.cache = {}

    def visual(self, code, width, height):
        key = (code, width, height)
        if key not in self.cache:
            photo = CARDS.get(code, (None, None, None))[2]
            path = os.path.join(IMAGES, f'{photo}.jpg') if photo else None
            if path and os.path.isfile(path):
                image = pygame.image.load(path)
                ratio = min(width / image.get_width(), height / image.get_height())
                surface = pygame.transform.smoothscale(image, (int(image.get_width() * ratio), int(image.get_height() * ratio)))
            elif code in (OTHER, OLD_TILE):
                surface = symbol(width, height, code)
            else:
                surface = circuit(width, height)
            self.cache[key] = surface
        return self.cache[key]

    def draw(self, selected, title, subtitle, back=False):
        screen = self.screen
        screen.display_background()
        screen.menu_header(title, subtitle)
        count = len(self.entries)
        columns = 4 if count > 6 else 3
        rows = math.ceil(count / columns)
        top = int(screen.res_y * 0.24)
        bottom = int(screen.res_y * 0.85)
        margin = int(screen.res_x * 0.015)
        width = int((screen.res_x * 0.9 - margin * (columns - 1)) / columns)
        height = int((bottom - top - margin * (rows - 1)) / rows)
        left = int((screen.res_x - (width * columns + margin * (columns - 1))) / 2)
        zones = {}
        text = color(screen, 'menu-text-white', (240, 240, 240))
        for index, (code, name, maker) in enumerate(self.entries):
            row, column = divmod(index, columns)
            rect = pygame.Rect(left + column * (width + margin), top + row * (height + margin), width, height)
            zones[index] = rect
            chosen = index == selected
            pygame.draw.rect(screen.screen, (36, 38, 44), rect, border_radius=int(height * 0.06))
            pygame.draw.rect(screen.screen, color(screen, 'menu-selected', (112, 156, 118)) if chosen else (70, 72, 80),
                             rect, 6 if chosen else 2, border_radius=int(height * 0.06))
            visual_h = int(height * 0.62)
            image = self.visual(code, int(width * 0.86), int(visual_h * 0.9))
            screen.screen.blit(image, image.get_rect(center=(rect.centerx, rect.y + int(visual_h * 0.55))))
            screen.blit_text(name, rect.x + 8, rect.y + visual_h, rect.width - 16, int(height * 0.2), color=text)
            if maker:
                screen.blit_text(maker, rect.x + 8, rect.y + visual_h + int(height * 0.19), rect.width - 16, int(height * 0.14),
                                 color=(170, 172, 180))
        help_text = screen.lang.translate('wizard-card-help' if back else 'wizard-card-help-first')
        screen.blit_text(help_text, 0, int(screen.res_y * 0.92), screen.res_x, int(screen.res_y * 0.06), color=(170, 172, 180))
        # Retour, or Quitter on the first screen (the desktop, the shutdown or cancel)
        button = 'back' if back else 'quit'
        zones[button] = back_button(screen, focused=selected == button, label='wizard-back' if back else 'wizard-quit')
        screen.update_screen()
        return zones, columns

    def choose(self, title, subtitle, initial=0, back=False):
        '''
        The code chosen, BACK (when back), or QUIT (the first screen of the wizard : its Quitter
        button or Escape)
        '''
        from include import cscreen    # pylint: disable=import-outside-toplevel
        selected = initial
        zones, _columns = self.draw(selected, title, subtitle, back)
        while True:
            # The inputs of the menus : keyboard, buttons of the cabinet, mouse and touch
            key = self.screen.rpi.listen_inputs(['arrows'], ['escape', 'enter', 'space', 'single-click', 'resize'])
            if isinstance(key, tuple):
                for index, rect in zones.items():
                    if rect.collidepoint(key):
                        return {'back': BACK, 'quit': QUIT}.get(index) or self.entries[index][0]
                continue
            if key in cscreen.ESCAPE_KEYS:
                return BACK if back else QUIT
            if key in cscreen.ENTER_KEYS or key == 'space':
                return {'back': BACK, 'quit': QUIT}.get(selected) or self.entries[selected][0]
            arrows = cscreen.UP_KEYS + cscreen.DOWN_KEYS + cscreen.LEFT_KEYS + cscreen.RIGHT_KEYS
            if key not in arrows and key != 'resize':
                continue
            if key in arrows:
                # The closest tile in the direction, Retour (or Quitter) with them (the last row
                # not full : the column was lost, the button never reached)
                selected = self.screen.spatial_step(list(zones.items()), selected, key)
            zones, _columns = self.draw(selected, title, subtitle, back)


def choose_card(screen):
    '''
    The interface card : its code (as the wizard knows them : Ch, Lk, Ji...), 'Au' for another
    card (the first screen of the wizard : no Retour)
    '''
    translate = screen.lang.translate
    main = [(code, CARDS[code][0], CARDS[code][1]) for code in CURRENT]
    main.append((OTHER, translate('wizard-card-other'), translate('wizard-card-other-sub')))
    main.append((OLD_TILE, translate('wizard-card-old'), translate('wizard-card-old-sub')))
    old = [(code, CARDS[code][0], CARDS[code][1]) for code in OLD]
    initial = 0
    while True:
        code = Tiles(screen, main).choose(translate('wizard-card-title'), translate('wizard-card-sub'), initial)
        if code == QUIT:
            leave(screen)
            continue
        if code != OLD_TILE:
            return code
        initial = len(main) - 1
        code = Tiles(screen, old).choose(translate('wizard-card-old'), translate('wizard-card-old-sub'), back=True)
        if code != BACK:
            return code


def leave(screen):
    '''
    Quitter on the first screen : back to the desktop, the cabinet shut down, or cancel (back to
    the cards). Nothing written : the wizard comes again at the next start
    '''
    answer = ask(screen, 'wizard-quit', 'wizard-quit-question',
                 [('desktop', 'back-to-desktop', None), ('shutdown', 'wizard-quit-shutdown', None),
                  ('cancel', 'wizard-quit-cancel', None)], back=False, initial=2, escape='cancel')
    if answer == 'cancel':
        return
    screen.display_background()
    screen.update_screen()
    if answer == 'shutdown':
        # As the game does it (raspydarts.py : game_type 'shutdown')
        subprocess.call(['poweroff'], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Out at once, code 0 : RaspyDarts.sh does not start it again (the desktop)
    pygame.quit()
    sys.stdout.flush()
    os._exit(0)    # pylint: disable=protected-access


# ---------------------------------------------------------------------------- the questions
BACK = 'back'
QUIT = 'quit'


def back_button(screen, focused=False, label='wizard-back'):
    '''
    The Retour button (or another label : Quitter) at the bottom left of the screens of the
    wizard : its rectangle
    '''
    rect = pygame.Rect(int(screen.res_x * 0.03), int(screen.res_y * 0.88), int(screen.res_x * 0.16), int(screen.res_y * 0.08))
    pygame.draw.rect(screen.screen, (60, 62, 68), rect, border_radius=14)
    pygame.draw.rect(screen.screen, (255, 255, 255) if focused else (110, 112, 120), rect, 5 if focused else 2, border_radius=14)
    screen.blit_text(screen.lang.translate(label), rect.x, rect.y, rect.width, rect.height, color=(240, 240, 240))
    return rect


def wrap(screen, text, size, width):
    '''
    The lines of a text in this size of the font, none wider than width
    '''
    font = screen.font(screen.defaultfontpath, size)
    lines, line = [], ''
    for word in str(text).split():
        trial = f'{line} {word}'.strip()
        if line and font.size(trial)[0] > width:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    return font, lines


def tire_drawing(kind):
    '''
    A drawing of the wiring of the LED of the target (DartCab) : the Raspberry, the wire, the
    tire (outer ring), the quarters and the bull, numbered in the order the wire goes through them
    '''
    def draw(surface, rect):
        orange, blue, red, white = (240, 150, 40), (70, 120, 210), (210, 50, 50), (245, 245, 245)
        # The Raspberry on the left
        pi = pygame.Rect(rect.x, rect.centery - rect.height // 6, rect.width // 5, rect.height // 3)
        pygame.draw.rect(surface, (29, 110, 60), pi, border_radius=8)
        for index in range(6):
            pygame.draw.rect(surface, (217, 180, 74), (pi.x + 6 + index * (pi.width - 12) // 6, pi.y + 4, max(3, pi.width // 12), 6))
        pygame.draw.circle(surface, (200, 40, 70), (pi.centerx, pi.centery + 4), max(4, pi.height // 6))
        # The target on the right : the tire (a ring), the quarters, the bull
        center = (rect.x + int(rect.width * 0.66), rect.centery)
        outer = int(min(rect.width * 0.32, rect.height * 0.46))
        has_tire = kind != 'none'
        quarters_r = int(outer * (0.74 if has_tire else 1.0))
        if has_tire:
            pygame.draw.circle(surface, orange, center, outer)
            pygame.draw.circle(surface, (25, 26, 30), center, int(outer * 0.8))
        for quarter in range(4):
            start = math.radians(quarter * 90 + 4)
            points = [center] + [(center[0] + quarters_r * math.cos(start + math.radians(82) * step / 8),
                                  center[1] + quarters_r * math.sin(start + math.radians(82) * step / 8)) for step in range(9)]
            pygame.draw.polygon(surface, blue, points)
        bull_r = max(6, quarters_r // 4)
        pygame.draw.circle(surface, (25, 26, 30), center, bull_r + 5)
        pygame.draw.circle(surface, red, center, bull_r)
        # The order of the wire, and where each part is
        places = {'tire': (center[0] - int(outer * 0.9), center[1]),
                  'quarters': (center[0] - int(quarters_r * 0.5), center[1] - int(quarters_r * 0.5)),
                  'bull': center}
        order = {'none': ['quarters', 'bull'], 'before': ['tire', 'quarters', 'bull'], 'after': ['quarters', 'bull', 'tire']}[kind]
        previous = (pi.right, pi.centery)
        for number, part in enumerate(order, 1):
            point = places[part]
            pygame.draw.line(surface, white, previous, point, 4)
            previous = point
        font = pygame.font.Font(None, max(18, rect.height // 7))
        for number, part in enumerate(order, 1):
            point = places[part]
            pygame.draw.circle(surface, white, point, max(11, rect.height // 13))
            label = font.render(str(number), True, (20, 20, 24))
            surface.blit(label, label.get_rect(center=point))
    return draw


def ask(screen, title, question, choices, back=True, initial=0, escape=None):
    '''
    A question of the wizard : the question big, its answers side by side (a drawing above the
    label of an answer when it has one), Retour. choices : [(value, label key, drawing or None)].
    Returns the value chosen, or BACK ; escape : the value Escape gives (else BACK when back)
    '''
    from include import cscreen    # pylint: disable=import-outside-toplevel
    translate = screen.lang.translate
    selected = initial
    with_drawings = any(drawing for _value, _label, drawing in choices)

    def draw():
        screen.display_background()
        screen.menu_header(translate(title))
        text = (245, 247, 250)
        accent = color(screen, 'menu-selected', (112, 156, 118))
        # The question, big, on as many lines as needed
        size = int(screen.res_y * 0.065)
        font, lines = wrap(screen, translate(question), size, int(screen.res_x * 0.86))
        y = int(screen.res_y * 0.17)
        for line in lines:
            rendered = font.render(line, True, text)
            screen.screen.blit(rendered, rendered.get_rect(midtop=(screen.res_x // 2, y)))
            y += int(size * 1.15)
        # The answers side by side
        count = len(choices)
        gap = int(screen.res_x * 0.03)
        width = min(int(screen.res_x * 0.28), int((screen.res_x * 0.9 - gap * (count - 1)) / count))
        height = int(screen.res_y * (0.5 if with_drawings else 0.2))
        top = max(y + int(screen.res_y * 0.04), int(screen.res_y * (0.3 if with_drawings else 0.45)))
        left = int((screen.res_x - (width * count + gap * (count - 1))) / 2)
        zones = {}
        for index, (_value, label, drawing) in enumerate(choices):
            rect = pygame.Rect(left + index * (width + gap), top, width, height)
            zones[index] = rect
            chosen = index == selected
            pygame.draw.rect(screen.screen, (36, 38, 44), rect, border_radius=18)
            pygame.draw.rect(screen.screen, accent if chosen else (90, 92, 100), rect, 7 if chosen else 2, border_radius=18)
            label_h = int(height * (0.26 if drawing else 1.0))
            if drawing:
                area = pygame.Rect(rect.x + 16, rect.y + 16, rect.width - 32, rect.height - label_h - 24)
                drawing(screen.screen, area)
            label_font, label_lines = wrap(screen, translate(label), int(screen.res_y * (0.04 if drawing else 0.07)), rect.width - 30)
            line_h = label_font.get_linesize()
            label_y = rect.bottom - label_h + (label_h - line_h * len(label_lines)) // 2
            for line in label_lines:
                rendered = label_font.render(line, True, text)
                screen.screen.blit(rendered, rendered.get_rect(midtop=(rect.centerx, label_y)))
                label_y += line_h
        back_rect = back_button(screen, focused=selected == BACK) if back else None
        screen.update_screen()
        return zones, back_rect

    zones, back_rect = draw()
    while True:
        key = screen.rpi.listen_inputs(['arrows'], ['escape', 'enter', 'space', 'single-click', 'resize'])
        if isinstance(key, tuple):
            if back_rect is not None and back_rect.collidepoint(key):
                return BACK
            hit = next((index for index, rect in zones.items() if rect.collidepoint(key)), None)
            if hit is not None:
                return choices[hit][0]
            continue
        if key in cscreen.ESCAPE_KEYS:
            if escape is not None:
                return escape
            if back:
                return BACK
            continue
        if key in cscreen.ENTER_KEYS or key == 'space':
            return BACK if selected == BACK else choices[selected][0]
        if key in cscreen.UP_KEYS + cscreen.DOWN_KEYS + cscreen.LEFT_KEYS + cscreen.RIGHT_KEYS:
            # The closest answer in the direction, Retour with them (it was reached by Escape only)
            selected = screen.spatial_step(list(zones.items()) + [(BACK, back_rect)], selected, key)
        elif key != 'resize':
            continue
        zones, back_rect = draw()


# ---------------------------------------------------------------------------- the pins
# The 40 pins of the Raspberry as seen from above, its connector along the top edge : the outer
# row (even pins) above, the inner row (odd pins, pin 1 on the left) below. A number : a GPIO
# (its BCM number, as the settings keep it) ; else what the pin carries
HEADER = {1: '3V3', 2: '5V', 3: 2, 4: '5V', 5: 3, 6: 'GND', 7: 4, 8: 14, 9: 'GND', 10: 15,
          11: 17, 12: 18, 13: 27, 14: 'GND', 15: 22, 16: 23, 17: '3V3', 18: 24, 19: 10, 20: 'GND',
          21: 9, 22: 25, 23: 11, 24: 8, 25: 'GND', 26: 7, 27: 'ID', 28: 'ID', 29: 5, 30: 'GND',
          31: 6, 32: 12, 33: 13, 34: 'GND', 35: 19, 36: 16, 37: 26, 38: 20, 39: 'GND', 40: 21}
# What some GPIO are used for elsewhere (a hint under them) : the extension cards, the LED
PIN_HINTS = {2: 'I2C', 3: 'I2C', 10: 'LED', 12: 'LED', 18: 'LED', 21: 'LED'}
POWER_COLORS = {'5V': (200, 60, 60), '3V3': (230, 140, 50), 'GND': (16, 16, 18), 'ID': (70, 72, 80)}
PIN_COLUMNS = 20


def pick_pins(screen, title, item, names, others, initial=()):
    '''
    The pins of a list of wires (the outputs or the inputs of another card), one after the
    other : the pin of each wire touched on the connector of the Raspberry drawn (or chosen
    with the arrows). Terminer : no other wire ; Retour : the wire before (on the first : the
    step before). item : the key of the name of a wire ('pinwiz-out-item', a « {} » for its
    number) ; others : {pin : short name} of the pins already given (another list) ; initial :
    the pins of this list given before. Returns the pins in the order of the wires, or None
    '''
    from include import cscreen    # pylint: disable=import-outside-toplevel
    translate = screen.lang.translate
    chosen = [str(pin) for pin in initial][:len(names)]
    short = translate(item).format('').strip()[:1].upper()
    # The focus : ['pin', physical number], ['finish'] or ['back']
    focus = ['finish'] if chosen and len(chosen) >= len(names) else ['pin', 11]
    state = {'warning': None}

    def label(index):
        return translate(item).format(index + 1)

    def pin_rect(number):
        column = (number - 1) // 2
        row = 0 if number % 2 == 0 else 1
        gap = int(screen.res_x * 0.004)
        width = int((screen.res_x * 0.94 - gap * (PIN_COLUMNS - 1)) / PIN_COLUMNS)
        height = int(screen.res_y * 0.13)
        left = int((screen.res_x - (width * PIN_COLUMNS + gap * (PIN_COLUMNS - 1))) / 2)
        top = int(screen.res_y * 0.33)
        return pygame.Rect(left + column * (width + gap), top + row * (height + gap), width, height)

    def owner(pin):
        '''
        Who has this GPIO : a short name (this list : S3 ; another : what it gave), else None
        '''
        if str(pin) in chosen:
            return f'{short}{chosen.index(str(pin)) + 1}'
        return others.get(str(pin))

    def draw():
        screen.display_background()
        screen.menu_header(translate(title), translate('pinwiz-sub'))
        text = (245, 247, 250)
        grey = (170, 172, 180)
        accent = color(screen, 'menu-selected', (112, 156, 118))
        # The question : the wire of the moment (or all given)
        if state['warning']:
            question, tint = state['warning'], (235, 90, 90)
        elif len(chosen) < len(names):
            question, tint = translate('pinwiz-question').format(label(len(chosen))), text
        else:
            question, tint = translate('pinwiz-all'), accent
        font = screen.font(screen.defaultfontpath, int(screen.res_y * 0.06))
        rendered = font.render(question, True, tint)
        screen.screen.blit(rendered, rendered.get_rect(center=(screen.res_x // 2, int(screen.res_y * 0.255))))
        zones = {}
        # The connector : the board under it, then its 40 pins
        first, last = pin_rect(2), pin_rect(39)
        board = pygame.Rect(first.x - 14, first.y - 14, last.right - first.x + 28, last.bottom - first.y + 28)
        pygame.draw.rect(screen.screen, (29, 90, 56), board, border_radius=16)
        small = screen.font(screen.defaultfontpath, int(screen.res_y * 0.022))
        big = screen.font(screen.defaultfontpath, int(screen.res_y * 0.05))
        for number, what in HEADER.items():
            rect = pin_rect(number)
            focused = focus == ['pin', number]
            if isinstance(what, int):
                taken = owner(what)
                mine = str(what) in chosen
                fill = (52, 76, 62) if mine else ((44, 46, 52) if taken else (36, 38, 44))
                pygame.draw.rect(screen.screen, fill, rect, border_radius=10)
                border = (255, 255, 255) if focused else (accent if mine else (90, 92, 100))
                pygame.draw.rect(screen.screen, border, rect, 6 if focused else 2, border_radius=10)
                top = small.render('GPIO', True, grey)
                screen.screen.blit(top, top.get_rect(midtop=(rect.centerx, rect.y + 6)))
                value = big.render(str(what), True, text if not taken or mine else (130, 132, 140))
                screen.screen.blit(value, value.get_rect(center=(rect.centerx, rect.centery + 2)))
                under = taken or PIN_HINTS.get(what)
                if under:
                    hint = small.render(under, True, accent if mine else grey)
                    screen.screen.blit(hint, hint.get_rect(midbottom=(rect.centerx, rect.bottom - 5)))
                zones[('pin', number)] = rect
            else:
                inner = rect.inflate(-int(rect.width * 0.3), -int(rect.height * 0.45))
                pygame.draw.rect(screen.screen, POWER_COLORS[what], inner, border_radius=8)
                pygame.draw.rect(screen.screen, (90, 92, 100), inner, 1, border_radius=8)
                name = small.render(what, True, (230, 230, 230))
                screen.screen.blit(name, name.get_rect(center=inner.center))
        # The wires and their pins, in rows
        per_row = 8 if len(names) > 10 else max(1, len(names))
        rows = math.ceil(len(names) / per_row)
        gap = int(screen.res_x * 0.008)
        chip_w = int((screen.res_x * 0.8 - gap * (per_row - 1)) / per_row)
        chip_h = int(screen.res_y * 0.06)
        left = int((screen.res_x - (chip_w * per_row + gap * (per_row - 1))) / 2)
        top = int(screen.res_y * (0.66 if rows > 1 else 0.7))
        chip_font = screen.font(screen.defaultfontpath, int(screen.res_y * 0.032))
        for index in range(len(names)):
            row, column = divmod(index, per_row)
            rect = pygame.Rect(left + column * (chip_w + gap), top + row * (chip_h + gap), chip_w, chip_h)
            current = index == len(chosen)
            done = index < len(chosen)
            pygame.draw.rect(screen.screen, (52, 76, 62) if done else (36, 38, 44), rect, border_radius=chip_h // 2)
            pygame.draw.rect(screen.screen, (255, 255, 255) if current else (accent if done else (70, 72, 80)), rect,
                             4 if current else 2, border_radius=chip_h // 2)
            words = f"{label(index)} : {chosen[index]}" if done else label(index)
            rendered = chip_font.render(words, True, text if done or current else (150, 152, 160))
            screen.screen.blit(rendered, rendered.get_rect(center=rect.center))
        # Retour, the help, Terminer (once a wire has its pin)
        zones[('back',)] = back_button(screen, focused=focus == ['back'])
        screen.blit_text(translate('wizard-card-help'), int(screen.res_x * 0.2), int(screen.res_y * 0.89),
                         int(screen.res_x * 0.6), int(screen.res_y * 0.06), color=grey)
        rect = pygame.Rect(int(screen.res_x * 0.81), int(screen.res_y * 0.88), int(screen.res_x * 0.16), int(screen.res_y * 0.08))
        enabled = bool(chosen)
        focused = focus == ['finish']
        pygame.draw.rect(screen.screen, (60, 62, 68) if enabled else (44, 46, 52), rect, border_radius=14)
        pygame.draw.rect(screen.screen, (255, 255, 255) if focused else (110, 112, 120), rect, 5 if focused else 2, border_radius=14)
        screen.blit_text(translate('pinwiz-finish'), rect.x, rect.y, rect.width, rect.height,
                         color=(240, 240, 240) if enabled else (120, 122, 130))
        if enabled:
            zones[('finish',)] = rect
        screen.update_screen()
        return zones

    def give(number):
        '''
        This pin for the wire of the moment : refused when taken ; True : all given
        '''
        pin = HEADER[number]
        if len(chosen) >= len(names):
            return False
        if owner(pin):
            state['warning'] = translate('pinwiz-taken').format(pin, owner(pin))
            return False
        chosen.append(str(pin))
        return len(chosen) >= len(names)

    zones = draw()
    while True:
        key = screen.rpi.listen_inputs(['arrows'], ['escape', 'enter', 'space', 'single-click', 'resize'])
        state['warning'] = None
        if isinstance(key, tuple):
            hit = next((name for name, rect in zones.items() if rect.collidepoint(key)), None)
            if hit is None:
                continue
            focus[:] = list(hit)
            key = 'enter'
        validate = key in cscreen.ENTER_KEYS or key in ('enter', 'space')
        if key in cscreen.ESCAPE_KEYS or (validate and focus == ['back']):
            # Retour : the wire before (its pin given again), on the first : the step before
            if not chosen:
                return None
            chosen.pop()
            if not chosen and focus == ['finish']:
                focus[:] = ['back']
        elif validate:
            if focus == ['finish'] and chosen:
                return chosen
            if focus[0] == 'pin' and give(focus[1]):
                return chosen
        elif key in cscreen.UP_KEYS + cscreen.DOWN_KEYS + cscreen.LEFT_KEYS + cscreen.RIGHT_KEYS:
            # The closest GPIO or button drawn in the direction (the edges went nowhere, up from
            # the buttons always onto pin 11) ; right and left in reading order : the outer row,
            # the inner one, then Retour and Terminer
            focus[:] = list(screen.spatial_step(list(zones.items()), tuple(focus), key))
        elif key != 'resize':
            continue
        zones = draw()


# ---------------------------------------------------------------------------- the LED
# The only GPIO of a Raspberry for the LED (as the LED servers take them)
LED_PINS = ('10', '12', '18', '21')
NO_LED = '0'
# The target tried with this many LED (more than any target has : the others are not there)
TARGET_TEST_LEDS = 300
LED_DMA = {'target': 10, 'strip': 9}
# GPIO sharing the same generator (PWM0) : the other one put back as an input before a try,
# else the signal came out on it too (the strip on 12 lit when 18 was tried)
PWM_SIBLINGS = {'12': ('18',), '18': ('12',)}


class LedTester:
    '''
    addons/Leds_Test.py run with sudo on the pin tried : its orders sent on its stdin
    '''

    def __init__(self, logs):
        self.logs = logs
        self.process = None
        self.pin = None

    def start(self, pin, count, brightness, kind, dma, release=()):
        import subprocess    # pylint: disable=import-outside-toplevel
        self.stop()
        script = os.path.join(cpaths.ROOT_DIR, 'addons', 'Leds_Test.py')
        try:
            self.process = subprocess.Popen(['sudo', 'python3', script, str(pin), str(count), str(brightness), kind, str(dma),
                                             ','.join(release)],
                                            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
            self.pin = pin
            self.logs.info(f"Wizard : LED tried on GPIO {pin} ({count} LED, {brightness} %, {kind})")
        except OSError as error:
            self.logs.error(f"Wizard : LED not tried ({error})")
            self.process = None

    def send(self, order):
        if self.process is None or self.process.poll() is not None:
            return
        try:
            self.process.stdin.write(order + '\n')
            self.process.stdin.flush()
        except OSError:
            pass

    def stop(self):
        if self.process is not None:
            self.send('quit')
            try:
                self.process.wait(timeout=3)
            except Exception:    # pylint: disable=broad-except
                self.process.kill()
        self.process = None
        self.pin = None


def bar_track(rect):
    '''
    The part of the brightness bar where the knob goes (the same for the drawing and a touch)
    '''
    # The knob's centre goes from one end to the other, the knob staying in the bar
    height = rect.height - 8
    return pygame.Rect(rect.x + 4 + height // 2, rect.y + 4, rect.width - 8 - height, height)


def number(value, default):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def setup_leds(screen, kind, taken, current):
    '''
    The LED of the target (kind 'target') or of the strip ('strip') : the GPIO tried at a touch
    (a rainbow on it), the order of the colours (all red : red if it is the right one), the
    brightness (seen at once), the number of LED of the strip. taken : GPIO used elsewhere.
    current : {'pin', 'bri', 'typ', 'nbr'}. Returns the same, pin '0' for none ; None : Escape
    '''
    from include import cscreen    # pylint: disable=import-outside-toplevel
    translate = screen.lang.translate
    values = {'pin': str(current.get('pin') or NO_LED), 'bri': max(1, min(100, number(current.get('bri'), 50))),
              'typ': current.get('typ') if current.get('typ') in ('rgb', 'grb') else 'grb',
              'nbr': number(current.get('nbr'), 60)}
    if values['nbr'] <= 0:
        # No strip set yet (a new configuration : 0) : a usual length to start from
        values['nbr'] = 60
    if values['bri'] <= 1 and str(current.get('bri')).startswith('0.'):
        values['bri'] = int(float(current.get('bri')) * 100)
    if values['pin'] not in LED_PINS:
        values['pin'] = NO_LED
    tester = LedTester(screen.logs)
    red_said = False

    def count():
        return values['nbr'] if kind == 'strip' else TARGET_TEST_LEDS

    def try_pin():
        if values['pin'] == NO_LED:
            tester.stop()
        else:
            release = [pin for pin in PWM_SIBLINGS.get(values['pin'], ()) if pin not in taken]
            tester.start(values['pin'], count(), values['bri'], values['typ'], LED_DMA[kind], release)

    # The rows : (name, [items]) ; an item : (action, label)
    rows = [('pin', [(pin, f'GPIO {pin}') for pin in LED_PINS] + [(NO_LED, translate('ledwiz-none'))]),
            ('typ', [('rgb', 'RGB'), ('grb', 'GRB')]),
            ('bri', [('bri-', '-'), ('bri', ''), ('bri+', '+')])]
    if kind == 'strip':
        rows.append(('nbr', [('nbr-100', '-100'), ('nbr-10', '-10'), ('nbr-', '-'), ('nbr', ''), ('nbr+', '+'),
                             ('nbr+10', '+10'), ('nbr+100', '+100')]))
    rows.append(('end', [('valid', translate('ledwiz-valid'))]))

    def disabled(row, action):
        if row == 'pin':
            return action in taken
        return row in ('typ', 'bri', 'nbr') and values['pin'] == NO_LED

    # The focus first on the output chosen, else on the first one free
    pins = [action for action, _label in rows[0][1]]
    free = [index for index, action in enumerate(pins) if not disabled('pin', action)]
    # (row, column) of a box, or 'back'
    focus = (0, pins.index(values['pin']) if values['pin'] in pins and not disabled('pin', values['pin']) else free[0])

    def draw():
        screen.display_background()
        screen.menu_header(translate('ledwiz-target' if kind == 'target' else 'ledwiz-strip'),
                           translate('ledwiz-red') if red_said else translate('ledwiz-sub'))
        surface = screen.screen
        accent = color(screen, 'menu-selected', (112, 156, 118))
        text = color(screen, 'menu-text-white', (240, 240, 240))
        top = int(screen.res_y * 0.26)
        row_h = int(screen.res_y * 0.6 / len(rows))
        label_x, label_w = int(screen.res_x * 0.05), int(screen.res_x * 0.25)
        start_x, area_w = int(screen.res_x * 0.32), int(screen.res_x * 0.63)
        zones = {}
        for row_index, (row, items) in enumerate(rows):
            y = top + row_index * row_h
            height = int(row_h * 0.7)
            if row != 'end':
                screen.blit_text(translate(f'ledwiz-{row}'), label_x, y, label_w, height, color=text, align='Left')
            if row in ('bri', 'nbr'):
                widths = {'bri-': 0.12, 'bri': 0.6, 'bri+': 0.12, 'nbr-100': 0.12, 'nbr-10': 0.1, 'nbr-': 0.08, 'nbr': 0.2,
                          'nbr+': 0.08, 'nbr+10': 0.1, 'nbr+100': 0.12}
            elif row == 'end':
                widths = {'valid': 0.36}
            else:
                widths = {action: min(0.18, 0.9 / len(items)) for action, _label in items}
            x = start_x
            if row == 'end':
                # Valider : twice as wide, in the middle of the screen
                x = int((screen.res_x - area_w * 0.36) / 2)
            for col_index, (action, label) in enumerate(items):
                width = int(area_w * widths[action])
                rect = pygame.Rect(x, y, width, height)
                x += width + int(area_w * 0.02)
                zones[(row_index, col_index)] = rect
                off = disabled(row, action)
                chosen = (row == 'pin' and values['pin'] == action) or (row == 'typ' and values['typ'] == action)
                focused = focus == (row_index, col_index)
                fill = (60, 62, 68) if not off else (34, 35, 38)
                if chosen:
                    fill = accent
                if action == 'bri':
                    # The bar : filled from its left end up to the knob, which carries the value
                    # (a touch puts it there)
                    pygame.draw.rect(surface, (40, 42, 48), rect, border_radius=height // 2)
                    track = bar_track(rect)
                    knob_r = track.height // 2
                    knob_x = track.x + int(track.width * values['bri'] / 100)
                    filled = pygame.Rect(track.x - knob_r, track.y, knob_x - track.x + 2 * knob_r, track.height)
                    pygame.draw.rect(surface, accent if not off else (70, 70, 70), filled, border_radius=knob_r)
                    pygame.draw.circle(surface, (255, 255, 255) if not off else (110, 110, 115), (knob_x, track.centery), knob_r)
                    # The value in the knob (it hid it)
                    screen.blit_text(str(values['bri']), knob_x - knob_r, rect.centery - knob_r, knob_r * 2, knob_r * 2,
                                     color=(20, 20, 24))
                    label = ''
                elif action == 'nbr':
                    pygame.draw.rect(surface, (40, 42, 48), rect, border_radius=12)
                    label = str(values['nbr'])
                else:
                    pygame.draw.rect(surface, fill, rect, border_radius=12)
                pygame.draw.rect(surface, (255, 255, 255) if focused else (90, 92, 100), rect, 5 if focused else 2, border_radius=12)
                screen.blit_text(label, rect.x, rect.y, rect.width, rect.height, color=text if not off else (110, 110, 115))
        zones['back'] = back_button(screen, focused=focus == 'back')
        screen.update_screen()
        return zones

    def reachable():
        '''
        The boxes the arrows go to, as drawn : not the outputs greyed (taken), nor the settings
        without output, nor the bar and the number (Entrée does nothing on them : their - and +
        change them) ; Retour with them
        '''
        items = []
        for place, rect in zones.items():
            if place != 'back':
                row, items_of_row = rows[place[0]]
                action = items_of_row[place[1]][0]
                # (the box touched last kept : the arrows go on from it)
                if (disabled(row, action) or action in ('bri', 'nbr')) and place != focus:
                    continue
            items.append((place, rect))
        return items

    def act(row_index, col_index):
        '''
        An item chosen : what it does ; True : the form is done
        '''
        nonlocal red_said
        row, items = rows[row_index]
        action = items[col_index][0]
        if disabled(row, action):
            return False
        if row == 'pin':
            values['pin'] = action
            red_said = False
            try_pin()
        elif row == 'typ':
            values['typ'] = action
            tester.send(f'type {action}')
            tester.send('red')
            red_said = True
        elif action in ('bri-', 'bri+'):
            values['bri'] = max(1, min(100, values['bri'] + (1 if action == 'bri+' else -1)))
            tester.send(f"bri {values['bri']}")
        elif action.startswith('nbr') and action != 'nbr':
            step = {'nbr-100': -100, 'nbr-10': -10, 'nbr-': -1, 'nbr+': 1, 'nbr+10': 10, 'nbr+100': 100}[action]
            values['nbr'] = max(1, min(1000, values['nbr'] + step))
            tester.send(f"count {values['nbr']}")
        elif action == 'valid':
            return True
        return False

    zones = draw()
    try:
        while True:
            key = screen.rpi.listen_inputs(['arrows'], ['escape', 'enter', 'space', 'single-click', 'resize'])
            if isinstance(key, tuple):
                hit = next((place for place, rect in zones.items() if rect.collidepoint(key)), None)
                if hit is None:
                    continue
                if hit == 'back':
                    return None
                focus = hit
                row, items = rows[hit[0]]
                if items[hit[1]][0] == 'bri':
                    # A touch on the bar : the brightness of this place (the knob comes there)
                    track = bar_track(zones[hit])
                    values['bri'] = max(1, min(100, round((key[0] - track.x) * 100 / max(track.width, 1))))
                    tester.send(f"bri {values['bri']}")
                elif act(*hit):
                    break
            elif key in cscreen.ESCAPE_KEYS:
                return None
            elif key in cscreen.ENTER_KEYS or key == 'space':
                if focus == 'back':
                    return None
                if act(*focus):
                    break
            elif key in cscreen.UP_KEYS + cscreen.DOWN_KEYS + cscreen.LEFT_KEYS + cscreen.RIGHT_KEYS:
                # The arrows move the selection between the boxes drawn, Entrée does what the box
                # does (on Luminosité and Nombre, right and left changed the value and did not
                # move ; up and down kept the number of the column ; Retour never reached)
                focus = screen.spatial_step(reachable(), focus, key)
            elif key != 'resize':
                continue
            zones = draw()
    finally:
        tester.stop()
    if values['pin'] == NO_LED:
        return {'pin': NO_LED, 'bri': 0, 'typ': 'grb', 'nbr': 0}
    return values


# ---------------------------------------------------------------------------- the buttons
def function_label(screen, name):
    return screen.lang.translate(WIZARD_LABELS.get(name, name))


def segment_at(center, radius, position):
    '''
    The number of the target under a position (in the ring of the numbers' segments), or 'B'
    for the bull, None elsewhere
    '''
    dx, dy = position[0] - center[0], position[1] - center[1]
    distance = math.hypot(dx, dy)
    if distance <= radius * 0.26:
        return 'B'
    if distance > radius:
        return None
    angle = (math.degrees(math.atan2(dy, dx)) + 90 + 9) % 360
    return ORDER[int(angle // 18)]


def pill(screen, text, center_x, center_y, height, fill, text_color, align):
    '''
    A label on a dark rounded box (readable on any background) ; its rectangle
    '''
    font = screen.font(screen.defaultfontpath, int(height * 0.8))
    width = font.size(text)[0] + height
    if align == 'Left':
        rect = pygame.Rect(int(center_x), int(center_y - height / 2), width, height)
    elif align == 'Right':
        rect = pygame.Rect(int(center_x - width), int(center_y - height / 2), width, height)
    else:
        rect = pygame.Rect(int(center_x - width / 2), int(center_y - height / 2), width, height)
    pygame.draw.rect(screen.screen, fill, rect, border_radius=height // 2)
    rendered = font.render(text, True, text_color)
    screen.screen.blit(rendered, rendered.get_rect(center=rect.center))
    return rect


def draw_buttons(screen, assigned, detected, selected, found, blink=True):
    '''
    The screen of the buttons : the target in the middle, as big as the screen allows, each
    function on its segment in a big label (with the pin of its button once set) ; the button
    detected in a band over the header. found : what is read (« 2 MCP boards », « 12 free GPIO »)
    '''
    translate = screen.lang.translate
    screen.display_background()
    if detected is None:
        screen.menu_header(translate('btnwiz-press'), translate('btnwiz-press-sub'))
    else:
        screen.menu_header(translate('btnwiz-detected').replace('{pin}', detected), translate('btnwiz-detected-sub'))
    surface = screen.screen
    accent = color(screen, 'menu-selected', (112, 156, 118))
    text = (245, 247, 250)
    top = int(screen.res_y * 0.19)
    area_h = int(screen.res_y * 0.985) - top
    center = (screen.res_x // 2, top + area_h // 2)
    # The outer labels (1.4 times the radius) just inside the area
    radius = int(area_h * 0.355)
    zones = {}
    # The target : the numbers' segments, those of the functions coloured, the bull (done)
    for index, number in enumerate(ORDER):
        start = math.radians(-90 - 9 + index * 18)
        end = start + math.radians(18)
        points = [center] + [(center[0] + radius * math.cos(start + (end - start) * step / 6),
                              center[1] + radius * math.sin(start + (end - start) * step / 6)) for step in range(7)]
        function = BUTTON_SEGMENTS.get(number)
        if function is None:
            fill = (46, 48, 54) if index % 2 else (30, 32, 36)
        elif function in assigned:
            fill = accent
        else:
            fill = (70, 110, 180)
        pygame.draw.polygon(surface, fill, points)
        pygame.draw.polygon(surface, (15, 15, 18), points, 2)
        if function is not None and selected < len(FUNCTIONS) and FUNCTIONS[selected] == function:
            pygame.draw.polygon(surface, (255, 255, 255), points, 6)
        middle = math.radians(-90 + index * 18)
        # Its number, big (near the outer edge, where the segment is wide)
        size = int(radius * 0.17)
        number_pos = (center[0] + radius * 0.8 * math.cos(middle), center[1] + radius * 0.8 * math.sin(middle))
        font = screen.font(screen.defaultfontpath, size)
        rendered = font.render(str(number), True, text)
        surface.blit(rendered, rendered.get_rect(center=(int(number_pos[0]), int(number_pos[1]))))
        if function is not None:
            # Its label outside the target, one in two further out (they do not overlap)
            label = function_label(screen, function)
            if function in assigned:
                label = f"{label}  {assigned[function]}"
            far = radius * (1.13 if index % 2 == 0 else 1.4)
            label_x = center[0] + far * math.cos(middle)
            label_y = center[1] + far * math.sin(middle)
            align = 'Left' if math.cos(middle) > 0.25 else ('Right' if math.cos(middle) < -0.25 else 'Center')
            # An arrow from the label to the outer edge of its segment
            line_color = accent if function in assigned else (230, 232, 240)
            tip = (center[0] + radius * 1.01 * math.cos(middle), center[1] + radius * 1.01 * math.sin(middle))
            pygame.draw.line(surface, line_color, (label_x, label_y), tip, 4)
            head = radius * 0.06
            back = (tip[0] + head * math.cos(middle), tip[1] + head * math.sin(middle))
            side = (-math.sin(middle) * head * 0.6, math.cos(middle) * head * 0.6)
            pygame.draw.polygon(surface, line_color, [tip, (back[0] + side[0], back[1] + side[1]), (back[0] - side[0], back[1] - side[1])])
            rect = pill(screen, label, label_x, label_y, int(screen.res_y * 0.05),
                        accent if function in assigned else (20, 22, 28), text, align)
            zones[FUNCTIONS.index(function)] = rect
    # The bull : Terminer, written big
    bull = int(radius * 0.26)
    pygame.draw.circle(surface, (190, 40, 40) if selected != len(FUNCTIONS) else (230, 80, 80), center, bull)
    if selected == len(FUNCTIONS):
        pygame.draw.circle(surface, (255, 255, 255), center, bull, 5)
    screen.blit_text(translate('btnwiz-finish'), center[0] - int(bull * 0.9), center[1] - bull // 2, int(bull * 1.8), bull,
                     color=text)
    screen.blit_text(found, int(screen.res_x * 0.02), top, int(screen.res_x * 0.3), int(screen.res_y * 0.04),
                     color=(200, 202, 210), align='Left')
    # The button detected : a band over the header, blinking
    if detected is not None:
        band_h = int(screen.res_y * 0.12)
        band = pygame.Rect(int(screen.res_x * 0.04), int(screen.res_y * 0.035), int(screen.res_x * 0.92), band_h)
        pygame.draw.rect(surface, accent if blink else (200, 140, 30), band, border_radius=band_h // 2)
        screen.blit_text(translate('btnwiz-detected').replace('{pin}', detected), band.x, band.y, band.width, band.height,
                         color=(10, 10, 12))
    # Retour : after Terminer in the order of the arrows
    zones['back'] = back_button(screen, focused=selected == len(FUNCTIONS) + 1)
    screen.update_screen()
    return center, radius, zones


def read_segment(rpi):
    '''
    A dart of the target ('S20', 'DB'...), None : none
    '''
    try:
        segment = rpi.read_target()
    except Exception:    # pylint: disable=broad-except
        return None
    return segment if isinstance(segment, str) and segment else None


def gpio_reader(screen, pins):
    '''
    The free GPIO of the Raspberry as inputs with their pull-up : a function giving the names of
    those pressed (« GPIO9 »), and the pins kept. A pin read low at rest (wired to the ground, a
    pull-down) is left aside : it would look pressed
    '''
    from include import craspberry    # pylint: disable=import-outside-toplevel
    gpio = craspberry.gpio
    kept = []
    for pin in pins:
        try:
            gpio.setup(pin, gpio.IN, pull_up_down=gpio.PUD_UP)
        except Exception:    # pylint: disable=broad-except
            continue
        kept.append(pin)
    time.sleep(0.05)
    kept = [pin for pin in kept if gpio.input(pin)]
    screen.logs.info(f"Buttons : free GPIO read {kept}")

    def pressed():
        found = set()
        for pin in kept:
            try:
                if not gpio.input(pin):
                    found.add(f'GPIO{pin}')
            except Exception:    # pylint: disable=broad-except
                pass
        return found
    return pressed, kept


def mcp_reader(screen, outputs):
    '''
    The inputs of the MCP boards (their pull-up) : a function giving the names of those pressed
    (« B3 »). outputs : the pins read low at rest (lights, toys), not buttons
    '''
    gpio = screen.rpi.gpio
    chips = list(gpio.chips)
    names = [gpio.pins_of(index) for index in range(len(chips))]

    def pressed():
        found = set()
        for index, chip in enumerate(chips):
            try:
                value = chip.gpio
            except OSError:
                continue
            for bit in range(16):
                name = names[index][bit]
                if name not in outputs and not value & (1 << bit):
                    found.add(name)
        return found
    return pressed, chips


def learn_buttons(screen, outputs=(), gpio_pins=None):
    '''
    The buttons learnt by pressing them : {PIN_UP: 'A0', ...} on the MCP boards, or, gpio_pins
    given (no MCP board), {PIN_UP: 'GPIO9', ...} on these free GPIO of the Raspberry. None : left,
    nothing changed. outputs : the MCP pins read low at rest (lights, toys), not buttons
    '''
    translate = screen.lang.translate
    if gpio_pins is None:
        read_pressed, chips = mcp_reader(screen, outputs)
        found = translate('btnwiz-mcp').replace('{count}', str(len(chips)))
    else:
        read_pressed, kept = gpio_reader(screen, gpio_pins)
        found = translate('btnwiz-gpio-free').replace('{count}', str(len(kept)))
    assigned = {}
    detected = None
    selected = 0
    pressed_before = read_pressed()
    last_blink = True
    center, radius, zones = draw_buttons(screen, assigned, detected, selected, found)

    def assign(function):
        nonlocal detected
        for other in [name for name, pin in assigned.items() if pin == detected]:
            del assigned[other]
        assigned[function] = detected
        screen.play_sound('Blaster')
        screen.logs.info(f"Buttons : {detected} = {function}")
        detected = None

    while True:
        changed = False
        # A button pressed : an input read low (its pull-up), a new one
        pressed = read_pressed()
        new = sorted(pressed - pressed_before)
        pressed_before = pressed
        if new:
            detected = new[0]
            changed = True
        # A dart : the function of the button detected ; SB / DB : done
        segment = read_segment(screen.rpi)
        if segment in ('SB', 'DB'):
            return assigned
        if segment and detected is not None:
            try:
                function = BUTTON_SEGMENTS.get(int(segment[1:]))
            except ValueError:
                function = None
            if function is not None:
                assign(function)
                changed = True
        # Keyboard, mouse, touch
        for key in keys_of_events(screen):
            if isinstance(key, tuple):
                hit = next((index for index, rect in zones.items() if rect.collidepoint(key)), None)
                if hit == 'back':
                    return None
                if hit is None:
                    number = segment_at(center, radius, key)
                    if number == 'B':
                        return assigned
                    if number in BUTTON_SEGMENTS:
                        hit = FUNCTIONS.index(BUTTON_SEGMENTS[number])
                if hit is not None:
                    selected = hit
                    key = 'enter'
                else:
                    continue
            if key == 'escape':
                if detected is None:
                    return None
                detected = None
            elif key in ('up', 'left'):
                # Round the target, then Terminer (the bull), then Retour (it was reached by
                # Escape only)
                selected = (selected - 1) % (len(FUNCTIONS) + 2)
            elif key in ('down', 'right'):
                selected = (selected + 1) % (len(FUNCTIONS) + 2)
            elif key == 'enter':
                if selected == len(FUNCTIONS) + 1:
                    return None
                if selected == len(FUNCTIONS):
                    return assigned
                if detected is not None:
                    assign(FUNCTIONS[selected])
            changed = True
        blink = int(time.monotonic() * 2) % 2 == 0
        if detected is not None and blink != last_blink:
            changed = True
        last_blink = blink
        if changed:
            center, radius, zones = draw_buttons(screen, assigned, detected, selected, found, blink)
        time.sleep(POLL)
