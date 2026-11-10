"""
Modifier les écrans > Personnaliser le thème : the colours of the theme (Colorset) changed on
plates showing each screen (main menu, lists of settings, description of a game, messages,
screen of a game, players, colours of games, Bob's 27, Fighters, shortcuts and texts). Each plate
is a mock-up drawn with the colours of the moment, the tags of the Colorset on each side with an
arrow to what they colour (as the document « Personnalisation du Colorset ») : a tag chosen, its
colour is chosen in a palette, then set finely (red, green, blue), or back to the colour of the
theme, or none (for the tags which can be None).

The colours chosen are kept in other/Colorset_perso.cfg of the theme, over its own Colorset.cfg
(left as it is) : the colour of the theme again = the tag removed from this file. Read by
Screen.init_colorset after the theme, for every theme (also those the game knows by name)
"""

import ast
import configparser
import os
import shutil

import pygame

PERSO_NAME = 'Colorset_perso.cfg'
# Frame of the tag chosen
CHOSEN = (255, 200, 0)
ARROW = (255, 200, 0)
# Palette : rows of 6
PALETTE = [(255, 255, 255), (214, 214, 214), (160, 160, 160), (100, 100, 100), (48, 48, 48), (0, 0, 0),
           (255, 0, 0), (194, 1, 1), (128, 0, 0), (255, 128, 0), (255, 215, 0), (255, 255, 0),
           (128, 255, 0), (0, 255, 0), (0, 128, 0), (0, 128, 128), (0, 255, 255), (107, 134, 176),
           (0, 128, 255), (0, 0, 255), (0, 0, 128), (128, 0, 255), (255, 0, 255), (255, 105, 180),
           (139, 69, 19), (205, 127, 50), (213, 206, 186), (112, 156, 118), (205, 144, 110), (189, 108, 109)]
# Tags which can be None (the code draws nothing then)
NONE_ALLOWED = ('menu-header', 'game-bg', 'game-option', 'game-type', 'game-darts', 'fighters-dead-player',
                'suggestion-color-allplayer')
# Shortcuts and alignment of the texts (not colours)
SHORTCUT_TAGS = ('main-sub-menu-shortcuts', 'parametrage-menu-shortcuts', 'players-menu-shortcuts',
                 'game-options-menu-shortcuts')
ALIGN_TAGS = ('main-sub-menu-text-align', 'parametrage-menu-text-align', 'players-menu-text-align',
              'game-options-menu-text-align')
SHORTCUT_CHOICES = (('', 'theme-shortcut-keys'), (None, 'theme-shortcut-none'), ('>', '>'), ('-', '-'),
                    ('*', '*'), ('+', '+'))
ALIGN_CHOICES = (('Left', 'theme-align-left'), ('Center', 'theme-align-center'), ('Right', 'theme-align-right'))
# Shapes (not colours) : thickness of the border and margin of the item chosen, rounding of the
# buttons and frames of the menus and of the buttons at the bottom ('max' : round)
SHAPE_TAGS = ('border-size', 'padding', 'border-radius', 'button-radius')
RADIUS_TAGS = ('border-radius', 'button-radius')
SHAPE_LIMITS = {'border-size': 15, 'padding': 15, 'border-radius': 40, 'button-radius': 40}

# Plates : (name, drawer, tags on the left [(tag, x, y)], tags on the right) ; x, y : the point
# of the mock-up the arrow goes to (parts of the mock-up)
PLATES = (
    ('theme-plate-menus', 'draw_menus',
     [('menu-header', 0.15, 0.06), ('menu-text', 0.5, 0.06), ('menu-shortcut', 0.24, 0.23),
      ('menu-border', 0.2, 0.28), ('menu-favorite', 0.55, 0.71), ('menu-inactive', 0.85, 0.87)],
     [('menu-selected', 0.8, 0.23), ('menu-text-white', 0.55, 0.23), ('menu-buttons', 0.85, 0.39),
      ('menu-text-black', 0.6, 0.39)]),
    ('theme-plate-settings', 'draw_settings',
     [('menu-alternate', 0.2, 0.22), ('menu-item-black', 0.12, 0.62), ('menu-item-white', 0.5, 0.6)],
     [('menu-ok', 0.8, 0.82), ('menu-warning', 0.8, 0.88), ('menu-ko', 0.8, 0.94)]),
    ('theme-plate-description', 'draw_description',
     [('description-bg', 0.62, 0.7)],
     [('description-game', 0.75, 0.2), ('description-text', 0.75, 0.42)]),
    ('theme-plate-messages', 'draw_messages',
     [('message-bg', 0.2, 0.5)],
     [('message-text', 0.6, 0.5)]),
    ('theme-plate-game', 'draw_game',
     [('game-bg', 0.05, 0.5), ('bg-round-nb-header', 0.12, 0.08), ('bg-round-nb', 0.12, 0.2),
      ('game-round', 0.12, 0.2), ('bg-darts-nb-header', 0.12, 0.36), ('bg-darts-nb', 0.12, 0.47),
      ('game-darts', 0.12, 0.47), ('game-type', 0.12, 0.66), ('game-option', 0.12, 0.74)],
     [('game-headers', 0.6, 0.06), ('game-alt-headers', 0.85, 0.06), ('game-player', 0.85, 0.2),
      ('game-player-name', 0.5, 0.2), ('game-score', 0.95, 0.2), ('game-inactive', 0.85, 0.34),
      ('game-dead', 0.85, 0.48), ('game-table', 0.6, 0.66), ('game-text', 0.75, 0.8),
      ('game-title1', 0.6, 0.93), ('game-title2', 0.6, 0.93)]),
    ('theme-plate-players', 'draw_players',
     [(f'player{index}', 0.08 + 0.17 * ((index - 1) % 6), 0.3 if index <= 6 else 0.7) for index in range(1, 7)],
     [(f'player{index}', 0.08 + 0.17 * ((index - 1) % 6), 0.7) for index in range(7, 13)]),
    ('theme-plate-games', 'draw_swatches',
     [('game-red', 0.1, 0.3), ('game-green', 0.3, 0.3), ('game-blue', 0.5, 0.3), ('game-purple', 0.7, 0.3),
      ('game-grey', 0.9, 0.3)],
     [('game-grey2', 0.1, 0.7), ('game-gold', 0.3, 0.7), ('game-silver', 0.5, 0.7), ('game-bronze', 0.7, 0.7),
      ('suggestion-color-allplayer', 0.9, 0.7)]),
    ('theme-plate-bob27', 'draw_bob27',
     [('bob27-bg', 0.05, 0.5), ('bob27-blue', 0.3, 0.25), ('bob27-green', 0.3, 0.5), ('bob27-red', 0.3, 0.75)],
     [('bob27-hit', 0.7, 0.25), ('bob27-miss', 0.7, 0.5), ('bob27-text', 0.62, 0.75)]),
    ('theme-plate-fighters', 'draw_fighters',
     [('fighters-actual-player', 0.3, 0.15), ('fighters-alive-player', 0.3, 0.35),
      ('fighters-dead-player', 0.3, 0.55), ('fighters-medic', 0.3, 0.75)],
     [('fighters-targets', 0.75, 0.15), ('fighters-scores', 0.75, 0.35), ('fighters-darts', 0.75, 0.55),
      ('fighters-round', 0.75, 0.75)]),
    ('theme-plate-borders', 'draw_borders',
     [('border-size', 0.25, 0.26), ('padding', 0.3, 0.32)],
     [('border-radius', 0.88, 0.5), ('button-radius', 0.8, 0.84)]),
    ('theme-plate-shortcuts', 'draw_shortcuts',
     [('main-sub-menu-shortcuts', 0.08, 0.15), ('parametrage-menu-shortcuts', 0.08, 0.4),
      ('players-menu-shortcuts', 0.08, 0.65), ('game-options-menu-shortcuts', 0.08, 0.88)],
     [('main-sub-menu-text-align', 0.7, 0.15), ('parametrage-menu-text-align', 0.7, 0.4),
      ('players-menu-text-align', 0.7, 0.65), ('game-options-menu-text-align', 0.7, 0.88)]),
)


# The plates by use : those of the menus, those of the games (a panel each on the first page)
GROUPS = (('theme-group-menus', ('theme-plate-menus', 'theme-plate-settings', 'theme-plate-description',
                                 'theme-plate-messages', 'theme-plate-shortcuts', 'theme-plate-borders')),
          ('theme-group-games', ('theme-plate-game', 'theme-plate-players', 'theme-plate-games',
                                 'theme-plate-bob27', 'theme-plate-fighters')))


def perso_path(screen):
    theme_dir = getattr(screen.file_class, 'theme_dir', None)
    return os.path.join(theme_dir, 'other', PERSO_NAME) if theme_dir else None


def read_perso(path):
    """
    The colours chosen for a theme : {tag: value}, {} if none
    """
    if not path or not os.path.isfile(path):
        return {}
    parser = configparser.ConfigParser(inline_comment_prefixes='#', interpolation=None)
    parser.optionxform = str
    try:
        parser.read(path, encoding='utf-8')
        values = {}
        for key, value in (parser['Colorset'].items() if parser.has_section('Colorset') else []):
            try:
                values[key] = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                continue
        return values
    except configparser.Error:
        return {}


def write_perso(path, values):
    """
    The colours chosen written (the file before kept as .bak) ; none : the file removed
    """
    if os.path.isfile(path):
        shutil.copyfile(path, f'{path}.bak')
    if not values:
        if os.path.isfile(path):
            os.remove(path)
        return
    lines = ['[Colorset]', '# Couleurs choisies dans Modifier les écrans > Personnaliser le thème,',
             '# par-dessus Colorset.cfg (retirer une ligne : la couleur du thème revient)']
    lines += [f'{key}: {value!r}' for key, value in sorted(values.items())]
    temporary = f'{path}.tmp'
    with open(temporary, 'w', encoding='utf-8') as file:
        file.write('\n'.join(lines) + '\n')
    os.replace(temporary, path)


def pick_color(screen, keys, title, current, buttons, label, panel=None, hover=None, redraw=None):
    '''
    The palette (Personnaliser le thème, Fond animé) : the colours in rows of 6, then the buttons
    ('fine' : Réglage fin ; the others returned as they are) and Retour. Gone through with the
    arrows or the wheel of a knob (in the order of reading). panel : where (the middle else) ;
    hover(value) : the colour or the button gone to (a preview follows it) ; redraw() : the screen
    under it. Returns a colour, the name of a button, or 'back'
    '''
    width, height = screen.screen.get_size()
    buttons = list(buttons) + ['back']
    cells = len(PALETTE) + len(buttons)
    current = tuple(current[:3]) if isinstance(current, (tuple, list)) else current
    if current in PALETTE:
        selected = PALETTE.index(current)
    elif current in buttons:
        selected = len(PALETTE) + buttons.index(current)
    else:
        selected = 0
    columns = 6
    panel = pygame.Rect(panel) if panel is not None else \
        pygame.Rect(int(width * 4 / 16), int(height * 2.2 / 16), int(width * 8 / 16), int(height * 11 / 16))
    shown = None
    while True:
        value = PALETTE[selected] if selected < len(PALETTE) else buttons[selected - len(PALETTE)]
        if hover is not None and value != shown:
            shown = value
            hover(value)
        # The screen under it, drawn again (the window of Réglage fin closed left its drawing)
        if redraw is not None:
            redraw()
        pygame.draw.rect(screen.screen, (20, 20, 20), panel, border_radius=16)
        pygame.draw.rect(screen.screen, (200, 200, 200), panel, 2, border_radius=16)
        title_rect = pygame.Rect(panel.x, panel.y + 8, panel.width, int(height * 0.8 / 16))
        screen.blit_text(f"{title}", title_rect.x, title_rect.y, title_rect.width, title_rect.height, (255, 255, 255))
        gap = int(panel.width / 40)
        size = int((panel.width - gap * (columns + 1)) / columns)
        row_h = int(size * 0.55)
        zones = {}
        for index, color in enumerate(PALETTE):
            cell = pygame.Rect(panel.x + gap + (index % columns) * (size + gap),
                               title_rect.bottom + 10 + (index // columns) * (row_h + gap), size, row_h)
            pygame.draw.rect(screen.screen, color, cell, border_radius=6)
            pygame.draw.rect(screen.screen, CHOSEN if index == selected else (90, 90, 90), cell,
                             4 if index == selected else 1, border_radius=6)
            zones[index] = cell
        row_y = title_rect.bottom + 10 + (len(PALETTE) // columns) * (row_h + gap) + gap
        # Two rows of buttons when they do not hold in one
        per_row = len(buttons) if len(buttons) <= 4 else (len(buttons) + 1) // 2
        button_w = int((panel.width - gap * (per_row + 1)) / per_row)
        button_h = int(height * 0.8 / 16)
        for number, name in enumerate(buttons):
            index = len(PALETTE) + number
            rect = pygame.Rect(panel.x + gap + (number % per_row) * (button_w + gap),
                               row_y + (number // per_row) * (button_h + gap), button_w, button_h)
            pygame.draw.rect(screen.screen, (90, 80, 30) if index == selected else (70, 70, 70), rect, border_radius=10)
            if index == selected:
                pygame.draw.rect(screen.screen, CHOSEN, rect, 3, border_radius=10)
            screen.blit_text(label(name), rect.x, rect.y, rect.width, rect.height, (255, 255, 255))
            zones[index] = rect
        screen.update_screen(rect_array=[panel]) if redraw is None else screen.update_screen()
        key = screen.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'enter', 'space', 'single-click',
                                                           'PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON'])
        if isinstance(key, tuple):
            hit = next((index for index, rect in zones.items() if rect.collidepoint(key)), None)
            if hit is None:
                continue
            selected, key = hit, 'enter'
        if key in keys['escape']:
            return 'back'
        if key in ('right', 'BTN_RIGHT', 'S6'):
            selected = (selected + 1) % cells
        elif key in ('left', 'BTN_LEFT', 'S11'):
            selected = (selected - 1) % cells
        elif key in ('down', 'BTN_DOWN', 'S3'):
            selected = min(selected + columns, cells - 1) if selected < len(PALETTE) else 0
        elif key in ('up', 'BTN_UP', 'S20'):
            selected = selected - columns if columns <= selected < len(PALETTE) else \
                (len(PALETTE) - columns if selected >= len(PALETTE) else cells - 1)
        elif key in keys['enter'] + ['space']:
            if selected < len(PALETTE):
                return PALETTE[selected]
            name = buttons[selected - len(PALETTE)]
            if name != 'fine':
                return name
            before = current if isinstance(current, tuple) else (128, 128, 128)
            fine = fine_color(screen, f"{title} · {label('fine')}", before, panel, hover)
            if fine is not None:
                return fine
            shown = None


def fine_color(screen, title, before, panel=None, hover=None):
    '''
    Réglage fin : a window with the sliders red, green, blue (dragged or clicked with the
    mouse ; up / down : a slider, left / right : its value by 5), the colour they give next
    to the one before, OK and Annuler (Entrée, Échap). hover(colour) : each colour given (a
    preview follows it). Returns the colour, None : cancelled
    '''
    width, height = screen.screen.get_size()
    translate = screen.lang.translate
    before = tuple(before[:3])
    color = list(before)
    names = ('theme-red', 'theme-green', 'theme-blue')
    tints = ((220, 40, 40), (40, 200, 60), (50, 90, 230))
    active = 0
    dragging = None
    clock = pygame.time.Clock()
    panel = pygame.Rect(panel) if panel is not None else \
        pygame.Rect(int(width * 3.5 / 16), int(height * 3.2 / 16), int(width * 9 / 16), int(height * 9 / 16))
    bars = [pygame.Rect(panel.x + int(panel.width * 0.2), panel.y + int(panel.height * (0.22 + 0.17 * index)),
                        int(panel.width * 0.5), int(panel.height * 0.06)) for index in range(3)]
    preview = pygame.Rect(panel.x + int(panel.width * 0.76), panel.y + int(panel.height * 0.2),
                          int(panel.width * 0.2), int(panel.height * 0.5))
    ok = pygame.Rect(panel.right - int(panel.width * 0.42), panel.bottom - int(panel.height * 0.16),
                     int(panel.width * 0.18), int(panel.height * 0.11))
    cancel = pygame.Rect(panel.right - int(panel.width * 0.22), ok.y, ok.width, ok.height)
    font = screen.font(screen.defaultfontpath, max(12, int(min(panel.height, panel.width * 0.6) * 0.06)))
    shown = [None]

    def value_at(index, pos_x):
        bar = bars[index]
        return max(0, min(255, round((pos_x - bar.x) / bar.width * 255)))

    def draw():
        if hover is not None and tuple(color) != shown[0]:
            shown[0] = tuple(color)
            hover(shown[0])
        pygame.draw.rect(screen.screen, (20, 20, 20), panel, border_radius=16)
        pygame.draw.rect(screen.screen, (200, 200, 200), panel, 2, border_radius=16)
        screen.screen.blit(font.render(title, True, (255, 255, 255)), (panel.x + 20, panel.y + 14))
        for index, bar in enumerate(bars):
            label = font.render(translate(names[index]), True, tints[index])
            screen.screen.blit(label, (panel.x + 20, bar.centery - label.get_height() // 2))
            # The bar shaded from 0 to 255 for this component, the others as they are
            for step in range(0, bar.width, 4):
                shade = list(color)
                shade[index] = int(step / bar.width * 255)
                pygame.draw.rect(screen.screen, shade, (bar.x + step, bar.y, 4, bar.height))
            pygame.draw.rect(screen.screen, CHOSEN if index == active else (120, 120, 120), bar, 3 if index == active else 1)
            knob_x = bar.x + int(color[index] / 255 * bar.width)
            pygame.draw.circle(screen.screen, (255, 255, 255), (knob_x, bar.centery), bar.height)
            pygame.draw.circle(screen.screen, (0, 0, 0), (knob_x, bar.centery), bar.height, 2)
            number = font.render(str(color[index]), True, (255, 255, 255))
            screen.screen.blit(number, (bar.right + bar.height + 14, bar.centery - number.get_height() // 2))
        # The colour before (top) and the one given (bottom)
        half = preview.height // 2
        pygame.draw.rect(screen.screen, before, (preview.x, preview.y, preview.width, half))
        pygame.draw.rect(screen.screen, tuple(color), (preview.x, preview.y + half, preview.width, preview.height - half))
        pygame.draw.rect(screen.screen, (255, 255, 255), preview, 2)
        code = font.render(f"({color[0]}, {color[1]}, {color[2]})", True, (255, 255, 255))
        screen.screen.blit(code, (preview.centerx - code.get_width() // 2, preview.bottom + 8))
        for rect, text in ((ok, 'OK'), (cancel, translate('theme-cancel'))):
            pygame.draw.rect(screen.screen, (70, 70, 70), rect, border_radius=10)
            rendered = font.render(text, True, (255, 255, 255))
            screen.screen.blit(rendered, rendered.get_rect(center=rect.center))
        screen.update_screen(rect_array=[panel])

    pygame.event.clear()
    while True:
        draw()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if ok.collidepoint(event.pos):
                    return tuple(color)
                if cancel.collidepoint(event.pos):
                    return None
                for index, bar in enumerate(bars):
                    if bar.inflate(0, bar.height * 2).collidepoint(event.pos):
                        active, dragging = index, index
                        color[index] = value_at(index, event.pos[0])
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = None
            elif event.type == pygame.MOUSEMOTION and dragging is not None:
                color[dragging] = value_at(dragging, event.pos[0])
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return tuple(color)
                if event.key == pygame.K_UP:
                    active = (active - 1) % 3
                elif event.key == pygame.K_DOWN:
                    active = (active + 1) % 3
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    step = 1 if event.mod & pygame.KMOD_SHIFT else 5
                    color[active] = max(0, min(255, color[active] + (step if event.key == pygame.K_RIGHT else -step)))
        # What is shown under it going on (the preview of Fond animé)
        if screen.idle_hook is not None:
            screen.idle_turn()
        clock.tick(30)


class ThemeEditor:
    '''
    The editor of the colours of the theme, drawn and driven by the Screen of the game
    '''

    def __init__(self, screen, keys):
        self.screen = screen
        self.keys = keys
        self.path = perso_path(screen)
        self.perso = read_perso(self.path)
        # The colours of the theme itself (without the colours chosen : kept by init_colorset),
        # and those of the moment
        self.base = dict(getattr(screen, 'theme_colorset', None) or screen.colorset)
        self.work = dict(self.base)
        self.work.update(self.perso)
        self.changed = False
        self.size = screen.screen.get_size()

    def translate(self, key):
        return self.screen.lang.translate(key)

    def color(self, tag):
        value = self.work.get(tag)
        if isinstance(value, (tuple, list)) and len(value) >= 3:
            return tuple(int(part) for part in value[:3])
        return None

    # ------------------------------------------------------------------ main loop
    def run(self):
        '''
        The first page : the plates in two panels (menus, games), Quitter sans enregistrer and
        Enregistrer et quitter at the bottom ; a plate chosen, then this page again
        '''
        entries = [name for _group, names in GROUPS for name in names] + ['quit', 'save']
        selected = 0
        while True:
            zones = self.draw_first_page(entries, selected)
            key = self.listen()
            if isinstance(key, tuple):
                hit = next((index for index, rect in zones.items() if pygame.Rect(rect).collidepoint(key)), None)
                if hit is None:
                    continue
                selected, key = hit, 'enter'
            if key in self.keys['escape']:
                if self.changed and self.screen.ask_yes_no(self.translate('theme-save-question')):
                    self.save()
                return
            # Two columns (the panels) of their own lengths, then the two buttons at the bottom
            first = len(GROUPS[0][1])
            plates = first + len(GROUPS[1][1])
            if key in ('down', 'BTN_DOWN'):
                selected = (selected + 1) % len(entries)
            elif key in ('up', 'BTN_UP'):
                selected = (selected - 1) % len(entries)
            elif key in ('right', 'BTN_RIGHT') and selected < first:
                selected = min(first + selected, plates - 1)
            elif key in ('left', 'BTN_LEFT') and first <= selected < plates:
                selected = min(selected - first, first - 1)
            elif key in ('right', 'BTN_RIGHT', 'left', 'BTN_LEFT') and selected >= plates:
                selected = plates + 1 if selected == plates else plates
            elif key in self.keys['enter'] + ['space']:
                entry = entries[selected]
                if entry == 'quit':
                    return
                if entry == 'save':
                    self.save()
                    return
                self.plate(next(plate for plate in PLATES if plate[0] == entry))

    def listen(self):
        return self.screen.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'enter', 'space', 'single-click',
                                                                 'PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON'])

    def banner(self):
        '''
        This screen is used with a keyboard and a mouse : said in a band under the title
        '''
        width, height = self.size
        band = pygame.Rect(0, int(height * 2.0 / 16), width, int(height * 0.85 / 16))
        pygame.draw.rect(self.screen.screen, (255, 200, 0), band)
        self.screen.blit_text(self.translate('theme-keyboard-mouse'), band.x, band.y, band.width, band.height, (0, 0, 0))

    def draw_first_page(self, entries, selected):
        '''
        Two panels (menus, games) of buttons, the buttons at the bottom. Returns the zones
        '''
        screen = self.screen
        width, height = self.size
        screen.display_background()
        screen.menu_header(self.translate('theme-customize'))
        self.banner()
        zones = {}
        index = 0
        for number, (group, names) in enumerate(GROUPS):
            panel = pygame.Rect(int(width * (1 + number * 7.25) / 16), int(height * 3.3 / 16),
                                int(width * 6.75 / 16), int(height * 9.8 / 16))
            pygame.draw.rect(screen.screen, (30, 30, 30), panel, border_radius=18)
            pygame.draw.rect(screen.screen, (140, 140, 140), panel, 2, border_radius=18)
            title = pygame.Rect(panel.x, panel.y + int(height * 0.2 / 16), panel.width, int(height * 0.9 / 16))
            screen.blit_text(self.translate(group), title.x, title.y, title.width, title.height, (255, 200, 0))
            step = (panel.bottom - title.bottom - int(height * 0.3 / 16)) / len(names)
            for row, name in enumerate(names):
                rect = pygame.Rect(panel.x + int(width * 0.4 / 16), int(title.bottom + row * step + step * 0.12),
                                   panel.width - int(width * 0.8 / 16), int(step * 0.76))
                chosen = index == selected
                pygame.draw.rect(screen.screen, (90, 80, 30) if chosen else (70, 70, 70), rect, border_radius=12)
                if chosen:
                    pygame.draw.rect(screen.screen, CHOSEN, rect, 3, border_radius=12)
                screen.blit_text(self.translate(name), rect.x, rect.y, rect.width, rect.height, (255, 255, 255))
                zones[index] = rect
                index += 1
        zones[index] = screen.display_button(index == selected, 'editor-quit', special='escape')
        zones[index + 1] = screen.display_button(index + 1 == selected, 'editor-save-quit', special='return')
        screen.update_screen()
        return zones

    def plate(self, plate):
        '''
        A plate : its mock-up and its tags ; arrows (or the knob) go from a tag to the next, Valider
        changes its colour, Retour goes back to the plates
        '''
        name, drawer, left, right = plate
        tags = self.place_tags(left + right)
        left = [tag for tag in tags if tag[3] == 'left']
        right = [tag for tag in tags if tag[3] == 'right']
        selected = 0
        while True:
            self.redraw = lambda: self.draw_plate(name, drawer, tags, selected, update=False)
            zones = self.draw_plate(name, drawer, tags, selected)
            key = self.listen()
            if isinstance(key, tuple):
                hit = next((index for index, rect in zones.items() if pygame.Rect(rect).collidepoint(key)), None)
                if hit is None:
                    continue
                selected, key = hit, 'enter'
            if key in self.keys['escape']:
                return
            count = len(tags)
            left_count = len(left)
            if key in ('down', 'BTN_DOWN', 'right', 'BTN_RIGHT', 'S3', 'S6'):
                if key in ('right', 'BTN_RIGHT', 'S6') and selected < left_count and right:
                    # Right from the left column : the same height on the right one (a knob : the next)
                    selected = min(left_count + selected, count - 1) if key == 'right' else (selected + 1) % count
                else:
                    selected = (selected + 1) % count
            elif key in ('up', 'BTN_UP', 'left', 'BTN_LEFT', 'S20', 'S11'):
                if key == 'left' and selected >= left_count:
                    selected = min(selected - left_count, left_count - 1)
                else:
                    selected = (selected - 1) % count
            elif key in self.keys['enter'] + ['space']:
                self.choose(tags[selected][0])

    def place_tags(self, points):
        '''
        The tags of a plate placed so that their arrows do not cross : each on the side of what
        it colours (the sides balanced when one has too many), in the order of the heights of
        their points. Returns [(tag, x, y, side)] in the order of the screen (left, then right)
        '''
        mockup = self.mockup_rect()
        width, height = self.size
        tag_h = max(20, int(height * 0.55 / 16))
        room = max(1, int((height * 10.2 / 16) / (tag_h + 4)))
        ordered = sorted(points, key=lambda point: point[1])
        left = [point for point in ordered if point[1] < 0.5]
        right = [point for point in ordered if point[1] >= 0.5]
        # Too many on a side : those nearest the middle go to the other one
        while len(left) > room and len(right) < room:
            right.append(left.pop(max(range(len(left)), key=lambda index: left[index][1])))
        while len(right) > room and len(left) < room:
            left.append(right.pop(min(range(len(right)), key=lambda index: right[index][1])))
        placed = []
        for side, items in (('left', left), ('right', right)):
            items = sorted(items, key=lambda point: (point[2], point[1] if side == 'left' else -point[1]))
            placed += [(tag, x, y, side) for tag, x, y in items]
        return placed

    def tag_heights(self, items, mockup, tag_h):
        '''
        The tops of the tags of a side : each at the height of its point, moved apart just
        enough not to overlap, kept between the title and the help
        '''
        width, height = self.size
        low, high = int(height * 3.0 / 16), int(height * 13.5 / 16) - tag_h
        gap = 4
        tops = [min(high, max(low, int(mockup.y + mockup.height * y - tag_h / 2))) for _tag, _x, y, _side in items]
        for index in range(1, len(tops)):
            tops[index] = max(tops[index], tops[index - 1] + tag_h + gap)
        if tops and tops[-1] > high:
            tops[-1] = high
            for index in range(len(tops) - 2, -1, -1):
                tops[index] = min(tops[index], tops[index + 1] - tag_h - gap)
        return tops

    # ------------------------------------------------------------------ drawing of a plate
    def mockup_rect(self):
        width, height = self.size
        return pygame.Rect(int(width * 4.2 / 16), int(height * 3.4 / 16), int(width * 7.6 / 16), int(height * 9.9 / 16))

    def draw_plate(self, name, drawer, tags, selected, update=True):
        '''
        The plate drawn : title, mock-up, tags with their colour and their arrow, help. Returns
        the zones of the tags {index: rect}
        '''
        screen = self.screen
        width, height = self.size
        screen.screen.fill((24, 24, 24))
        screen.menu_header(f"{self.translate('theme-customize')} : {self.translate(name)}")
        self.banner()
        mockup = self.mockup_rect()
        getattr(self, drawer)(mockup)
        pygame.draw.rect(screen.screen, (90, 90, 90), mockup, 2)
        zones = {}
        sides = {'left': [tag for tag in tags if tag[3] == 'left'], 'right': [tag for tag in tags if tag[3] == 'right']}
        tag_w, tag_h = int(width * 3.6 / 16), max(20, int(height * 0.55 / 16))
        font = screen.font(screen.defaultfontpath, int(tag_h * 0.62))
        for side, items in sides.items():
            if not items:
                continue
            tops = self.tag_heights(items, mockup, tag_h)
            for number, (tag, point_x, point_y, _side) in enumerate(items):
                index = tags.index((tag, point_x, point_y, side))
                tag_x = int(width * 0.2 / 16) if side == 'left' else int(width * 12.2 / 16)
                tag_y = tops[number]
                rect = pygame.Rect(tag_x, tag_y, tag_w, tag_h)
                zones[index] = rect
                chosen = index == selected
                pygame.draw.rect(screen.screen, (60, 60, 60) if not chosen else (90, 80, 30), rect, border_radius=tag_h // 3)
                if chosen:
                    pygame.draw.rect(screen.screen, CHOSEN, rect, 3, border_radius=tag_h // 3)
                # Its value : a swatch (a colour), or its text (shortcuts, alignment)
                swatch = pygame.Rect(rect.x + 4, rect.y + 4, tag_h - 8, tag_h - 8) if side == 'left' else \
                    pygame.Rect(rect.right - tag_h + 4, rect.y + 4, tag_h - 8, tag_h - 8)
                self.draw_value(tag, swatch, font)
                text = font.render(tag + (' *' if tag in self.perso or (tag in self.work and self.work.get(tag) != self.base.get(tag)) else ''),
                                   True, (255, 255, 255))
                room = rect.width - tag_h - 12
                if text.get_width() > room:
                    text = pygame.transform.smoothscale(text, (room, text.get_height()))
                text_x = swatch.right + 6 if side == 'left' else swatch.x - 6 - text.get_width()
                screen.screen.blit(text, (text_x, rect.y + (rect.height - text.get_height()) // 2))
                # The arrow to what it colours
                target = (int(mockup.x + mockup.width * point_x), int(mockup.y + mockup.height * point_y))
                start = (rect.right, rect.centery) if side == 'left' else (rect.x, rect.centery)
                self.arrow(start, target, CHOSEN if chosen else (150, 150, 150), 3 if chosen else 1)
        # Help, at the bottom
        help_rect = pygame.Rect(0, int(height * 13.6 / 16), width, int(height * 0.6 / 16))
        pygame.draw.rect(screen.screen, (0, 0, 0), help_rect)
        screen.blit_text(self.translate('theme-help'), help_rect.x, help_rect.y, help_rect.width, help_rect.height,
                         (255, 255, 255))
        if update:
            screen.update_screen()
        return zones

    def draw_value(self, tag, rect, font):
        value = self.work.get(tag)
        if tag in SHAPE_TAGS:
            pygame.draw.rect(self.screen.screen, (30, 30, 30), rect)
            text = font.render('M' if value == 'max' else str(value), True, (255, 255, 255))
            self.screen.screen.blit(text, text.get_rect(center=rect.center))
            return
        if tag in SHORTCUT_TAGS + ALIGN_TAGS:
            pygame.draw.rect(self.screen.screen, (30, 30, 30), rect)
            label = {'Left': 'G', 'Center': 'C', 'Right': 'D', None: '-', '': 'F'}.get(value, str(value)[:2])
            text = font.render(label, True, (255, 255, 255))
            self.screen.screen.blit(text, text.get_rect(center=rect.center))
            return
        color = self.color(tag)
        if color is None:
            pygame.draw.rect(self.screen.screen, (30, 30, 30), rect)
            pygame.draw.line(self.screen.screen, (200, 0, 0), rect.topleft, rect.bottomright, 2)
        else:
            pygame.draw.rect(self.screen.screen, color, rect)
            pygame.draw.rect(self.screen.screen, (255, 255, 255), rect, 1)

    def arrow(self, start, end, color, width):
        pygame.draw.line(self.screen.screen, color, start, end, width)
        pygame.draw.circle(self.screen.screen, color, end, max(3, width + 2))

    # ------------------------------------------------------------------ mock-ups
    def text(self, text, rect, tag, size=0.6, align='center'):
        color = self.color(tag)
        if color is None:
            return
        font = self.screen.font(self.screen.defaultfontpath, max(8, int(rect.height * size)))
        rendered = font.render(text, True, color)
        if rendered.get_width() > rect.width - 4:
            rendered = pygame.transform.smoothscale(rendered, (rect.width - 4, rendered.get_height()))
        place = rendered.get_rect(center=rect.center)
        if align == 'left':
            place.x = rect.x + 6
        elif align == 'right':
            place.right = rect.right - 6
        self.screen.screen.blit(rendered, place)

    def box(self, rect, tag, radius=6, border=None):
        color = self.color(tag)
        if color is not None:
            pygame.draw.rect(self.screen.screen, color, rect, border_radius=radius)
        if border is not None and self.color(border) is not None:
            pygame.draw.rect(self.screen.screen, self.color(border), rect, 3, border_radius=radius)

    def part(self, mockup, x, y, w, h):
        return pygame.Rect(int(mockup.x + mockup.width * x), int(mockup.y + mockup.height * y),
                           int(mockup.width * w), int(mockup.height * h))

    def draw_background(self, mockup):
        pygame.draw.rect(self.screen.screen, (40, 40, 44), mockup)

    def draw_menus(self, mockup):
        self.draw_background(mockup)
        header = self.part(mockup, 0, 0.02, 1, 0.08)
        self.box(header, 'menu-header', 0)
        self.text('Raspydarts', header, 'menu-text')
        labels = ('Partie simple', 'Partie en réseau', 'Divers', 'Cricket (favori)', 'Revenir sur le bureau')
        for index, label in enumerate(labels):
            row = self.part(mockup, 0.2, 0.17 + index * 0.16, 0.7, 0.12)
            short = pygame.Rect(row.x, row.y, int(row.height * 1.1), row.height)
            if index == 4:
                self.box(row, 'menu-inactive')
                self.text(label, row, 'menu-text-black')
                continue
            selected = index == 0
            self.box(row, 'menu-selected' if selected else 'menu-buttons', border='menu-border' if selected else None)
            self.box(short, 'menu-shortcut')
            self.text(f'F{index + 1}', short, 'menu-text-white')
            text_rect = pygame.Rect(short.right, row.y, row.right - short.right, row.height)
            self.text(label, text_rect, 'menu-favorite' if index == 3 else ('menu-text-white' if selected else 'menu-text-black'))

    def draw_settings(self, mockup):
        self.draw_background(mockup)
        for index, (value, label) in enumerate((('Oui', 'Afficher le segment touché'), ('20', 'Nombre de tours'),
                                                ('Non', 'Mode compétition'))):
            row = self.part(mockup, 0.05, 0.12 + index * 0.14, 0.9, 0.1)
            self.box(row, 'menu-buttons')
            value_rect = pygame.Rect(row.x, row.y, int(row.width * 0.25), row.height)
            self.box(value_rect, 'menu-alternate')
            self.text(value, value_rect, 'menu-text-white')
            self.text(label, pygame.Rect(value_rect.right, row.y, row.right - value_rect.right, row.height), 'menu-text-black')
        panel = self.part(mockup, 0.05, 0.52, 0.55, 0.22)
        self.box(panel, 'menu-item-black')
        self.text('Nouveautés…', panel, 'menu-item-white', 0.3)
        for index, tag in enumerate(('menu-ok', 'menu-warning', 'menu-ko')):
            band = self.part(mockup, 0.62, 0.79 + index * 0.065, 0.36, 0.055)
            self.box(band, tag, 3)
            self.text(('Enregistré', 'Attention', 'Erreur')[index], band, 'menu-text-white', 0.7)

    def draw_description(self, mockup):
        self.draw_background(mockup)
        for index in range(12):
            logo = self.part(mockup, 0.04 + (index % 3) * 0.13, 0.12 + (index // 3) * 0.2, 0.11, 0.17)
            pygame.draw.circle(self.screen.screen, (180, 30, 30), logo.center, logo.width // 2)
            pygame.draw.circle(self.screen.screen, (240, 240, 240), logo.center, logo.width // 4)
        title = self.part(mockup, 0.45, 0.12, 0.52, 0.12)
        self.box(title, 'description-bg', 12)
        self.text('Cricket', title, 'description-game')
        body = self.part(mockup, 0.45, 0.28, 0.52, 0.62)
        self.box(body, 'description-bg', 18)
        for line in range(5):
            self.text('Fermez les chiffres de 15 à 20…', self.part(mockup, 0.47, 0.32 + line * 0.07, 0.48, 0.06),
                      'description-text', 0.7, 'left')

    def draw_messages(self, mockup):
        self.draw_background(mockup)
        band = self.part(mockup, 0, 0.42, 1, 0.16)
        self.box(band, 'message-bg', 0)
        self.text('Retirez les fléchettes et appuyez sur « Joueur suivant »', band, 'message-text', 0.45)

    def draw_game(self, mockup):
        screen = self.screen
        background = self.color('game-bg')
        pygame.draw.rect(screen.screen, background if background is not None else (40, 40, 44), mockup)
        round_header = self.part(mockup, 0.02, 0.03, 0.2, 0.08)
        self.box(round_header, 'bg-round-nb-header', 4)
        self.text('Round', round_header, 'game-headers')
        round_box = self.part(mockup, 0.02, 0.12, 0.2, 0.16)
        self.box(round_box, 'bg-round-nb', 4)
        self.text('1 / 20', round_box, 'game-round')
        darts_header = self.part(mockup, 0.02, 0.32, 0.2, 0.08)
        self.box(darts_header, 'bg-darts-nb-header', 4)
        self.text('Darts', darts_header, 'game-headers')
        darts_box = self.part(mockup, 0.02, 0.41, 0.2, 0.12)
        self.box(darts_box, 'bg-darts-nb', 4)
        self.text('3', darts_box, 'game-darts')
        self.text('Cricket', self.part(mockup, 0.02, 0.62, 0.2, 0.08), 'game-type')
        self.text('Paye ton coup : 200', self.part(mockup, 0.02, 0.71, 0.2, 0.06), 'game-option')
        header = self.part(mockup, 0.3, 0.02, 0.68, 0.08)
        self.box(header, 'game-alt-headers', 0)
        self.text('Joueur          Score', header, 'game-headers')
        for index, (tag, name, score) in enumerate((('game-player', 'Joueur 1', '120'), ('game-inactive', 'Joueur 2', '80'),
                                                    ('game-dead', 'Joueur 3', '0'))):
            line = self.part(mockup, 0.3, 0.13 + index * 0.14, 0.68, 0.12)
            self.box(line, tag, 0)
            self.text(name, pygame.Rect(line.x, line.y, int(line.width * 0.6), line.height),
                      'game-player-name' if index == 0 else 'game-text')
            self.text(score, pygame.Rect(line.x + int(line.width * 0.6), line.y, int(line.width * 0.4), line.height), 'game-score')
        table = self.part(mockup, 0.3, 0.58, 0.68, 0.18)
        color = self.color('game-table')
        if color is not None:
            for row in range(4):
                pygame.draw.line(screen.screen, color, (table.x, table.y + row * table.height // 3),
                                 (table.right, table.y + row * table.height // 3), 2)
        self.text('20   19   18   17', self.part(mockup, 0.3, 0.77, 0.68, 0.06), 'game-text')
        title = self.part(mockup, 0.3, 0.88, 0.68, 0.1)
        self.box(title, 'game-title1', 0)
        self.text('Le gagnant est…', title, 'game-title2')

    def draw_players(self, mockup):
        self.draw_background(mockup)
        for index in range(1, 13):
            swatch = self.part(mockup, 0.02 + 0.17 * ((index - 1) % 6), 0.2 if index <= 6 else 0.6, 0.12, 0.2)
            self.box(swatch, f'player{index}', 8)
            self.text(str(index), swatch, 'menu-text-white' if index > 99 else 'color-black', 0.5)

    def draw_swatches(self, mockup):
        self.draw_background(mockup)
        tags = ('game-red', 'game-green', 'game-blue', 'game-purple', 'game-grey',
                'game-grey2', 'game-gold', 'game-silver', 'game-bronze', 'suggestion-color-allplayer')
        for index, tag in enumerate(tags):
            swatch = self.part(mockup, 0.03 + 0.2 * (index % 5), 0.2 if index < 5 else 0.6, 0.14, 0.2)
            if self.color(tag) is None:
                pygame.draw.rect(self.screen.screen, (90, 90, 90), swatch, 2, border_radius=8)
            self.box(swatch, tag, 8)

    def draw_bob27(self, mockup):
        background = self.color('bob27-bg')
        pygame.draw.rect(self.screen.screen, background or (40, 40, 44), mockup)
        for index, tag in enumerate(('bob27-blue', 'bob27-green', 'bob27-red')):
            bar = self.part(mockup, 0.15, 0.18 + index * 0.25, 0.4, 0.15)
            self.box(bar, tag, 6)
            self.text(('D1   D2   D3', '27 points', 'Touché / Raté')[index], bar, 'bob27-text', 0.5)
        self.text('D1 : OK', self.part(mockup, 0.6, 0.18, 0.25, 0.15), 'bob27-hit')
        self.text('D2 : X', self.part(mockup, 0.6, 0.43, 0.25, 0.15), 'bob27-miss')

    def draw_fighters(self, mockup):
        self.draw_background(mockup)
        for index, (tag, name) in enumerate((('fighters-actual-player', '> Joueur 1'), ('fighters-alive-player', 'Joueur 2'),
                                             ('fighters-dead-player', 'Joueur 3 (KO)'), ('fighters-medic', '+ Soin'))):
            self.text(name, self.part(mockup, 0.05, 0.08 + index * 0.2, 0.45, 0.15), tag, 0.55, 'left')
        for index, (tag, text) in enumerate((('fighters-targets', '20  19  18'), ('fighters-scores', '120'),
                                             ('fighters-darts', 'o  o  o'), ('fighters-round', 'Round 3'))):
            self.text(text, self.part(mockup, 0.55, 0.08 + index * 0.2, 0.4, 0.15), tag, 0.55)

    def radius(self, tag, rect, scale):
        value = self.work.get(tag)
        if value == 'max':
            return rect.height // 2
        try:
            return min(rect.height // 2, int(int(value) * scale))
        except (TypeError, ValueError):
            return 0

    def draw_borders(self, mockup):
        '''
        Buttons of a menu (the first one chosen : its border, its margin), and a button at the
        bottom, drawn with the shapes of the moment (scaled as the mock-up)
        '''
        self.draw_background(mockup)
        scale = mockup.height / self.size[1]
        for index, label in enumerate(('Partie simple', 'Partie en réseau', 'Divers')):
            row = self.part(mockup, 0.15, 0.2 + index * 0.18, 0.7, 0.13)
            radius = self.radius('border-radius', row, scale)
            chosen = index == 0
            if chosen:
                border = max(0, int(int(self.work.get('border-size') or 0) * scale * 2))
                padding = max(0, int(int(self.work.get('padding') or 0) * scale * 2))
                if self.color('menu-border') is not None and border:
                    pygame.draw.rect(self.screen.screen, self.color('menu-border'), row, border, border_radius=radius)
                inner = row.inflate(-2 * (border + padding), -2 * (border + padding))
                if self.color('menu-selected') is not None:
                    pygame.draw.rect(self.screen.screen, self.color('menu-selected'), inner,
                                     border_radius=max(0, radius - border - padding))
                self.text(label, inner, 'menu-text-white')
            else:
                if self.color('menu-buttons') is not None:
                    pygame.draw.rect(self.screen.screen, self.color('menu-buttons'), row, border_radius=radius)
                self.text(label, row, 'menu-text-black')
        button = self.part(mockup, 0.62, 0.8, 0.3, 0.09)
        if self.color('menu-buttons') is not None:
            pygame.draw.rect(self.screen.screen, self.color('menu-buttons'), button,
                             border_radius=self.radius('button-radius', button, scale * 2))
        self.text('Sauvegarder', button, 'menu-text-black')

    def draw_shortcuts(self, mockup):
        self.draw_background(mockup)
        examples = (('main-sub-menu', 'Partie simple'), ('parametrage-menu', 'Paramétrage'),
                    ('players-menu', 'Joueur 1'), ('game-options-menu', 'Nombre de tours'))
        for index, (prefix, label) in enumerate(examples):
            row = self.part(mockup, 0.05, 0.08 + index * 0.24, 0.9, 0.15)
            self.box(row, 'menu-buttons')
            shortcut = self.work.get(f'{prefix}-shortcuts')
            align = str(self.work.get(f'{prefix}-text-align') or 'Center').lower()
            shown = 'F1' if shortcut == '' else ('' if shortcut is None else str(shortcut))
            short = pygame.Rect(row.x, row.y, int(row.height * 1.1), row.height)
            if shown:
                self.box(short, 'menu-shortcut')
                self.text(shown, short, 'menu-text-white')
            text_rect = pygame.Rect(short.right if shown else row.x, row.y, row.right - (short.right if shown else row.x), row.height)
            self.text(label, text_rect, 'menu-text-black', 0.55, align if align in ('left', 'right') else 'center')

    # ------------------------------------------------------------------ choosing
    def choose(self, tag):
        '''
        A tag chosen : its value changed (a colour : palette, then fine, origin, none ; a shortcut,
        an alignment : its list)
        '''
        screen = self.screen
        if tag in SHAPE_TAGS:
            values = [['value', self.translate('theme-value')]]
            if tag in RADIUS_TAGS:
                values.append(['max', self.translate('theme-round-max')])
            values.append(['origin', self.translate('theme-origin-value')])
            chosen = screen.dropdown(screen.res['x'] * 6 / 16, 3 * screen.res_y_16, values,
                                     navigate='max' if self.work.get(tag) == 'max' else 'value')
            if chosen in ('origin', 'max'):
                self.set(tag, chosen)
            elif chosen == 'value':
                current = self.work.get(tag)
                current = int(current) if isinstance(current, (int, float)) else 10
                number = screen.slider(f"{tag} (px)", min(current, SHAPE_LIMITS[tag]), 0, SHAPE_LIMITS[tag], step=1)
                if number != 'escape':
                    self.set(tag, int(number))
            return
        if tag in SHORTCUT_TAGS + ALIGN_TAGS:
            choices = SHORTCUT_CHOICES if tag in SHORTCUT_TAGS else ALIGN_CHOICES
            values = [[str(index), self.translate(text)] for index, (_value, text) in enumerate(choices)]
            values.append(['origin', self.translate('theme-origin-value')])
            current = next((str(index) for index, (value, _text) in enumerate(choices) if value == self.work.get(tag)), None)
            chosen = screen.dropdown(screen.res['x'] * 6 / 16, 3 * screen.res_y_16, values, navigate=current)
            if chosen == 'escape':
                return
            self.set(tag, 'origin' if chosen == 'origin' else choices[int(chosen)][0])
            return
        chosen = self.palette(tag)
        if chosen != 'back':
            self.set(tag, chosen)

    def set(self, tag, value):
        if value == 'origin':
            self.perso.pop(tag, None)
            self.work[tag] = self.base.get(tag)
        else:
            self.perso[tag] = value
            self.work[tag] = value
        self.changed = True

    def palette(self, tag):
        '''
        The palette of a tag : a colour, Réglage fin (red, green, blue), Couleur d'origine du
        thème, Aucune (if it can be None). Returns the colour, None (Aucune), 'origin', or 'back'
        '''
        buttons = ['fine', 'origin'] + (['none'] if tag in NONE_ALLOWED else [])
        chosen = pick_color(self.screen, self.keys, tag, self.color(tag), buttons,
                            lambda name: self.translate(f'theme-{name}'),
                            redraw=lambda: self.redraw() if getattr(self, 'redraw', None) is not None else None)
        return None if chosen == 'none' else chosen

    # ------------------------------------------------------------------ saving
    def save(self):
        '''
        The colours chosen written in other/Colorset_perso.cfg of the theme, shown at once
        '''
        if self.path is None:
            return False
        values = dict(self.perso)
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            write_perso(self.path, values)
        except OSError as error:
            self.screen.logs.error(f"Theme : {self.path} not written ({error})")
            self.screen.message([self.translate('editor-not-saved')], 2500, 'menu-ko', 'middle', 'big')
            return False
        self.screen.logs.info(f"Theme : colours chosen written in {self.path} ({len(values)})")
        self.screen.apply_look()
        self.screen.message([self.translate('editor-saved')], 1500, None, 'middle', 'big')
        return True
