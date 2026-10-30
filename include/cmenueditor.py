"""
Editor of the screens of menus on the borne (Paramètres > Modifier les écrans) : the buttons
of a menu moved, resized by their handles, added or deleted, their shortcut changed, with the
keyboard (a key held down repeats), the buttons of the borne, the darts (keys of the
navigation, docs/menu/menus.md section 9), the mouse or a finger (a button or its handles
dragged).

The screen is frozen when it opens : each button keeps the place it has on the screen (free
placement, section 7.5), so moving one never moves the others. Saved in the menus of the
theme (themes/<theme>/menu/menus.yaml), the previous file kept as menus.yaml.bak
"""

import copy
import os
import re
import shutil
import time

import pygame

from include import cmenus
from include import cpaths
from include import cmenustyle

try:
    import yaml
except ImportError:
    yaml = None

# Menus the editor changes (name of the menu, text of the list of the screens)
SCREENS = (('main', 'editor-screen-main'), ('miscellaneous', 'editor-screen-miscellaneous'),
           ('settings', 'editor-screen-settings'))
# Steps of a move or a resize, in parts of the screen (0 : one pixel ; + and - change it)
STEPS = (0, 0.0025, 0.005, 0.01, 0.02, 0.05)
FIRST_STEP = 3
# Handles of a button : (part of the width, part of the height) of the handle on its rect
HANDLES = ((0, 0), (0.5, 0), (1, 0), (1, 0.5), (1, 1), (0.5, 1), (0, 1), (0, 0.5))
# Frame of the button moved or resized, and its handle moved
MOVING = (255, 200, 0)
# Smallest button, in parts of the screen
SMALLEST = 0.02
# Keys added by the game to the buttons it shows (not written in the file)
RUNTIME_KEYS = ('logo_image', 'game_logo', 'unavailable')
# Keys of the automatic layouts : a button placed freely does not use them
LAYOUT_KEYS = ('span', 'cell', 'zone', 'space_before', 'space_left')
# A key held down : repeated after this delay, at this interval (ms)
REPEAT = (350, 60)
# Keys which can be a shortcut of a button (not c : the secret key showing them)
SHORTCUT_KEYS = re.compile(r'^(F([1-9]|1[0-2])|[abd-z0-9])$')
# A drag drawn again at most every (s) : a drawing takes 50 to 90 ms on a Pi 3
DRAG_FRAME = 0.04
# Snapping : an edge or a centre caught by those of the other buttons, the edges and the middle
# of the screen, this near (part of the screen) ; the lines it is caught by drawn in this colour
SNAP = 0.01
GUIDE = (0, 200, 255)
# Shapes a button can be given (over the one of its style)
SHAPES = ('rectangle', 'rounded', 'pill')
# The version (V4.6) of the menus which show it : an element placed as the buttons, kept in
# show_version of the menu (not in its buttons)
VERSION_ID = '__version__'
# Images a menu can have as background : in these folders of the theme and of ~/.raspydarts,
# and those of the game named background...
BACKGROUND_FOLDERS = (os.path.join('images', 'background'), os.path.join('images', 'menus'))
IMAGES = ('.png', '.jpg', '.jpeg')
# Buttons arranged in a zone : the spaces between them (parts of the screen), the zone drawn
GAPS = (0, 0.005, 0.01, 0.02, 0.03, 0.05)
FIRST_GAP = 2
MOST_CELLS = 12
ZONE = (255, 200, 0, 50)


class Editor:
    '''
    The editor of one menu, drawn and driven by the Screen of the game
    '''

    def __init__(self, screen, name, keys):
        self.screen = screen
        self.name = name
        self.keys = keys
        self.menus = screen.menus()
        self.menu = self.menus.menu(name)
        self.resolution = self.menus.data.get('resolution')
        self.size = screen.screen.get_size()
        self.units = cmenustyle.Units(self.size, self.resolution)
        self.removed = []
        self.changed = False
        self.step = FIRST_STEP
        self.mode = 'select'
        self.handle = 4
        self.menu_rect = pygame.Rect(0, 0, 0, 0)
        self.snap = True
        self.dragging = False
        # The zone where buttons are arranged (mode zone), and the last choices of the arrangement
        self.zone = None
        self.arrangement = {'columns': None, 'rows': None, 'gap': GAPS[FIRST_GAP], 'inside': False}
        # The buttons shown in the menu (not those at the bottom), with their place on the screen
        shown = [button for button in self.menus.buttons(name)
                 if button.get('visible', True) is not False and not button.get('footer')]
        rects = cmenustyle.layout(self.menu, shown, self.size, self.resolution)[0]
        self.items = []
        for index, button in enumerate(shown, 1):
            if index in rects:
                self.items.append({'button': self.clean(button), 'rect': pygame.Rect(rects[index])})
        self.version_shown = self.menu.get('show_version') or False
        if self.version_shown:
            self.items.append({'button': {'id': VERSION_ID, 'version': True},
                               'rect': screen.menu_version_rect(self.version_shown)})
        self.selected = 1
        # Its background : the one of the files (None : the one of the theme), and the one
        # given back by Back while they are browsed
        self.backdrop = self.menu.get('background')
        self.backdrop_before = None
        self.backdrops = []

    @staticmethod
    def clean(button):
        '''
        A copy of a button without what the game added to it while showing it
        '''
        button = copy.deepcopy(button)
        for key in RUNTIME_KEYS:
            button.pop(key, None)
        return button

    def translate(self, key):
        return self.screen.lang.translate(key)

    def button_name(self, button):
        if button.get('version'):
            return self.translate('editor-version')
        return self.screen.lang.translate(self.screen.button_text(button))

    # ------------------------------------------------------------------ drawing
    def background(self):
        '''
        The background of the menu (its own image, or the one of the theme) and its title
        '''
        screen = self.screen
        block = self.backdrop
        # On black : a background with transparency let the screen before show through
        screen.screen.fill((0, 0, 0))
        if block is not None:
            block = cmenustyle.merge({'fit': 'cover'}, block) if isinstance(block, dict) else block
            screen.screen.blit(screen.menu_painter().background(block, self.size), (0, 0))
        else:
            screen.display_background()
        # Its own title : the screen stays recognisable
        title = screen.menu_text_look(self.name, 'title')[0]
        subtitle = screen.menu_text_look(self.name, 'subtitle')[0]
        if title or subtitle:
            screen.styled_title(self.name, title, subtitle)

    def step_text(self):
        step = STEPS[self.step]
        return '1 px' if step == 0 else f"{step * 100:g} %"

    def step_pixels(self, axis):
        step = STEPS[self.step]
        return 1 if step == 0 else max(1, int(round(step * self.size[0 if axis == 'x' else 1])))

    def help_text(self):
        if self.mode == 'backdrop':
            number = self.backdrops.index(self.backdrop) + 1 if self.backdrop in self.backdrops else 1
            return f"{self.translate(dict(SCREENS)[self.name])} · {self.backdrop_name(self.backdrop)} "                 f"({number}/{len(self.backdrops)}) · {self.translate('editor-help-background')}"
        key = {'move': 'editor-help-move', 'resize': 'editor-help-resize', 'zone': 'editor-help-zone'}.get(
            self.mode, 'editor-help-select')
        return f"{self.translate(dict(SCREENS)[self.name])} · {self.translate(key).replace('{step}', self.step_text())}"

    def help_bar(self):
        '''
        The keys of the moment, in a thin band at the bottom (the title of the menu stays
        visible at the top), and the button Menu (adding, saving, leaving : also Back)
        '''
        screen = self.screen
        height = max(24, int(self.size[1] / 28))
        band = pygame.Surface((self.size[0], height), pygame.SRCALPHA)
        band.fill((0, 0, 0, 190))
        screen.screen.blit(band, (0, self.size[1] - height))
        font = screen.font(screen.defaultfontpath, int(height * 0.7))
        self.menu_rect = pygame.Rect(self.size[0] - int(self.size[0] / 9), self.size[1] - height + 2,
                                     int(self.size[0] / 9) - 4, height - 4)
        text = font.render(self.help_text(), True, (255, 255, 255))
        room = self.menu_rect.x - 16
        if text.get_width() > room:
            text = pygame.transform.smoothscale(text, (room, text.get_height()))
        screen.screen.blit(text, (8, self.size[1] - height + (height - text.get_height()) // 2))
        pygame.draw.rect(screen.screen, MOVING, self.menu_rect, border_radius=height // 3)
        label = font.render(self.translate('editor-menu-button'), True, (0, 0, 0))
        screen.screen.blit(label, label.get_rect(center=self.menu_rect.center))

    def handle_rects(self, rect):
        '''
        The squares of the handles of a rect (the one moved bigger while it is resized)
        '''
        side = max(12, int(self.size[1] / 50))
        squares = []
        for number, (part_x, part_y) in enumerate(HANDLES):
            bigger = self.mode in ('resize', 'zone') and number == self.handle
            square = pygame.Rect(0, 0, side * 2 if bigger else side, side * 2 if bigger else side)
            square.center = (rect.x + int(rect.width * part_x), rect.y + int(rect.height * part_y))
            squares.append(square)
        return squares

    def draw(self):
        '''
        The whole screen of the editor : the menu, its buttons at their place (the one chosen
        last, over the others, framed, with its handles), the bar of the keys
        '''
        screen = self.screen
        started = time.perf_counter()
        painter = screen.menu_painter()
        self.background()
        shortcuts = cmenustyle.merge({'show': screen.colorset.get('main-sub-menu-shortcuts') is not None, 'format': '{key}',
                                      'position': 'top_left' if self.menu.get('layout') == 'tiles' else 'left'},
                                     self.menu.get('shortcuts') or {})
        for index in sorted(range(1, len(self.items) + 1), key=lambda number: number == self.selected):
            item = self.items[index - 1]
            button = item['button']
            if button.get('version'):
                # The version, as the menu shows it, filling its box
                screen.draw_version(item['rect'], self.version_shown or True)
                continue
            if button.get('action') == 'online_players':
                # The panel of the players online as it will be shown, at its size
                screen.online_players_panel(item['rect'], index == self.selected)
                continue
            shown = screen.favorite_button(button) if self.name == 'main' else button
            style = screen.button_style(self.menu, shown)
            state = 'selected' if index == self.selected else ('disabled' if shown.get('unavailable') else 'normal')
            text = '' if shown.get('text', True) is None or ('text' not in shown and shown.get('logo')) else \
                screen.lang.translate(screen.button_text(shown))
            painter.draw_button(screen.screen, item['rect'], style, text, screen.button_icon(shown), state, self.units,
                                shortcut=screen.button_label(shown, self.menu) if shortcuts.get('show') else None,
                                shortcuts=shortcuts)
        if self.mode == 'zone':
            # The zone where the buttons will be arranged, over them, with its handles
            veil = pygame.Surface(self.zone.size, pygame.SRCALPHA)
            veil.fill(ZONE)
            screen.screen.blit(veil, self.zone.topleft)
            pygame.draw.rect(screen.screen, MOVING, self.zone, 4)
            self.draw_handles(self.zone)
        elif 1 <= self.selected <= len(self.items) and self.mode != 'backdrop':
            rect = self.items[self.selected - 1]['rect']
            # The button chosen framed : green, gold while it is moved or resized
            color = screen.colorset['menu-ok'] if self.mode == 'select' else MOVING
            pygame.draw.rect(screen.screen, color, rect.inflate(8, 8), 3 if self.mode == 'select' else 5)
            if self.mode != 'move':
                self.draw_handles(rect)
        self.draw_guides()
        self.help_bar()
        screen.update_screen()
        screen.logs.debug(f"Menu editor : drawn in {(time.perf_counter() - started) * 1000:.0f} ms")

    def draw_handles(self, rect):
        '''
        The handles of a rect (dragged with the mouse or a finger) ; the one moved by the
        arrows : bigger, gold
        '''
        for number, square in enumerate(self.handle_rects(rect)):
            current = self.mode in ('resize', 'zone') and number == self.handle
            pygame.draw.rect(self.screen.screen, MOVING if current else (255, 255, 255), square)
            pygame.draw.rect(self.screen.screen, (0, 0, 0), square, 2)

    def draw_guides(self):
        '''
        While a button or the zone is moved or resized : the lines its edges and its centre
        are on (those of the other buttons, of the screen), across the screen
        '''
        rect = self.active_rect()
        if not self.snap or rect is None:
            return
        for axis in ('x', 'y'):
            lines = self.lines(axis)
            for value in self.edges(rect, axis):
                if value in lines:
                    start, end = ((value, 0), (value, self.size[1])) if axis == 'x' else ((0, value), (self.size[0], value))
                    pygame.draw.line(self.screen.screen, GUIDE, start, end, 2)

    # ------------------------------------------------------------------ snapping
    def active_rect(self):
        '''
        The rect moved or resized : the zone, or the button chosen ; None if none is
        '''
        if self.mode == 'zone':
            return self.zone
        if (self.mode in ('move', 'resize') or self.dragging) and 1 <= self.selected <= len(self.items):
            return self.items[self.selected - 1]['rect']
        return None

    @staticmethod
    def edges(rect, axis):
        return (rect.left, rect.centerx, rect.right) if axis == 'x' else (rect.top, rect.centery, rect.bottom)

    def lines(self, axis):
        '''
        Lines a button or the zone is caught by along an axis : the edges and the centres of
        the other buttons (all of them for the zone), the edges and the middle of the screen
        '''
        size = self.size[0 if axis == 'x' else 1]
        lines = {0, size // 2, size}
        for index, item in enumerate(self.items, 1):
            if self.mode == 'zone' or index != self.selected:
                lines.update(self.edges(item['rect'], axis))
        return lines

    def caught(self, values, axis):
        '''
        The shift which brings the nearest of these positions on a line, if one is near enough
        (0 : none)
        '''
        if not self.snap:
            return 0
        reach = SNAP * self.size[0 if axis == 'x' else 1]
        shifts = [line - value for line in self.lines(axis) for value in values if abs(line - value) <= reach]
        return min(shifts, key=abs) if shifts else 0

    def on_the_way(self, values, delta, axis):
        '''
        A move by the arrows : stopped on the first line one of these positions meets (the
        next press goes past it : the step of one pixel stays possible)
        '''
        if not self.snap or delta == 0:
            return delta
        shifts = [line - value for line in self.lines(axis) for value in values
                  if 0 < (line - value) * (1 if delta > 0 else -1) < abs(delta)]
        return min(shifts, key=abs) if shifts else delta

    def snapped(self, rect, handle=None):
        '''
        A rect dragged with the mouse or a finger, caught by the lines near it : moved
        (handle None) or the edges of its handle moved
        '''
        if handle is None:
            return self.clamp(rect.move(self.caught(self.edges(rect, 'x'), 'x'), self.caught(self.edges(rect, 'y'), 'y')))
        part_x, part_y = HANDLES[handle]
        delta_x = self.caught([rect.left if part_x == 0 else rect.right], 'x') if part_x in (0, 1) else 0
        delta_y = self.caught([rect.top if part_y == 0 else rect.bottom], 'y') if part_y in (0, 1) else 0
        return self.stretched(rect, handle, delta_x, delta_y)

    def rects(self):
        '''
        Places of the buttons, which can be chosen
        '''
        return {index: tuple(item['rect']) for index, item in enumerate(self.items, 1)}

    # ------------------------------------------------------------------ keys
    def key_in(self, key, direction):
        return key in set(self.menus.keys(direction)) or (direction == 'validate' and key in self.keys['enter']) or \
            (direction == 'back' and key in self.keys['escape'])

    def direction_of(self, key):
        for direction in ('up', 'down', 'left', 'right'):
            if self.key_in(key, direction):
                return direction
        return None

    def listen(self):
        return self.screen.rpi.listen_inputs(['arrows', 'fx', 'alpha', 'math', 'num'],
                                             ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON', 'single-click',
                                              'enter', 'space'],
                                             events=[(self.screen.wait_event_time, 'EVENT', 'wait')])

    def run(self):
        '''
        The editor until it is saved or given up : True if the menu was saved. A key held down
        repeats while it runs
        '''
        pygame.key.set_repeat(*REPEAT)
        try:
            return self.loop()
        finally:
            pygame.key.set_repeat()
            # Keys repeated while the screen was saved (the keyboard not read : the key seemed
            # held) : 8 Enter in 0.7 s opened again Modifier les écrans and an editor
            pygame.event.clear((pygame.KEYDOWN, pygame.KEYUP))

    def loop(self):
        while True:
            self.draw()
            key = self.listen()
            if self.mode == 'backdrop':
                self.backdrop_key(key)
                continue
            if isinstance(key, tuple):
                choice = self.clicked(key)
                if choice is not None:
                    key = choice
                else:
                    continue
            if self.mode == 'move':
                self.moving(key)
                continue
            if self.mode == 'resize':
                self.resizing(key)
                continue
            if self.mode == 'zone':
                if self.zoning(key):
                    self.arrange_menu()
                continue
            direction = self.direction_of(key)
            if direction is not None:
                self.selected = self.screen.move_selection(self.rects(), self.selected, direction)
                continue
            if self.key_in(key, 'back') or key == 'menu':
                # The screen is all the menu's : adding, saving and leaving are behind Back
                choice = self.editor_menu()
                if choice == 'save' and self.save():
                    return True
                if choice == 'quit' and self.give_up():
                    return False
                if choice == 'add':
                    self.add()
                if choice == 'background':
                    self.backdrops = self.backdrop_choices()
                    self.backdrop_before = self.backdrop
                    self.mode = 'backdrop'
                if choice == 'arrange' and self.items:
                    # The zone : first the one of all the buttons, then changed by the user
                    self.zone = self.items[0]['rect'].unionall([item['rect'] for item in self.items[1:]])
                    self.mode, self.handle = 'zone', 0
                continue
            if self.key_in(key, 'validate') and 1 <= self.selected <= len(self.items):
                self.button_actions()

    # ------------------------------------------------------------------ mouse and finger
    def clicked(self, position):
        '''
        A click (or a touch) : the button Menu ('menu') ; a handle of the button chosen or a
        button dragged ; a button chosen ; the button already chosen clicked without moving it :
        its actions ('enter'). None : done here
        '''
        if self.menu_rect.collidepoint(position):
            if self.mode != 'zone':
                self.mode = 'select'
            return 'menu'
        if self.mode == 'zone':
            # The zone : by a handle, or dragged whole
            for number, square in enumerate(self.handle_rects(self.zone)):
                if square.inflate(10, 10).collidepoint(position):
                    self.handle = number
                    self.drag(position, number)
                    return None
            if self.zone.collidepoint(position):
                self.drag(position, None)
            return None
        if 1 <= self.selected <= len(self.items) and self.mode != 'move':
            for number, square in enumerate(self.handle_rects(self.items[self.selected - 1]['rect'])):
                if square.inflate(10, 10).collidepoint(position):
                    self.drag(position, number)
                    return None
        # The button on top first : the chosen one is drawn over the others, then the last ones
        # over those before them
        order = sorted(range(1, len(self.items) + 1), key=lambda number: (number == self.selected, number), reverse=True)
        index = next((number for number in order if self.items[number - 1]['rect'].collidepoint(position)), None)
        self.screen.logs.debug(f"Menu editor : click at {position}, button {index}")
        if index is None:
            return None
        already = index == self.selected
        self.selected = index
        self.mode = 'select'
        if not self.drag(position, None) and already:
            return 'enter'
        return None

    def pointer_events(self):
        '''
        Positions of the pointer since the last call, and whether it was released : the mouse,
        or a finger (the clicks SDL makes from the touches are left aside)
        '''
        width, height = self.size
        positions, released = [], False
        for event in pygame.event.get((pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP, pygame.FINGERMOTION, pygame.FINGERUP)):
            if event.type in (pygame.FINGERMOTION, pygame.FINGERUP):
                positions.append((int(event.x * width), int(event.y * height)))
                released = released or event.type == pygame.FINGERUP
            elif not getattr(event, 'touch', False):
                positions.append(event.pos)
                released = released or event.type == pygame.MOUSEBUTTONUP
        return positions, released

    def drag(self, start, handle):
        '''
        The button chosen (or the zone) dragged (handle None) or resized by a handle, until the
        mouse button or the finger is released, caught by the lines near it : True if it moved
        '''
        zone = self.mode == 'zone'
        item = None if zone else self.items[self.selected - 1]
        before = pygame.Rect(self.zone if zone else item['rect'])
        touch = getattr(self.screen.rpi, 'last_input_touch', False)
        moved, drawn = False, 0
        self.dragging = True
        try:
            while True:
                positions, released = self.pointer_events()
                if positions:
                    delta_x, delta_y = positions[-1][0] - start[0], positions[-1][1] - start[1]
                    if moved or abs(delta_x) > 3 or abs(delta_y) > 3:
                        moved = True
                        if handle is None:
                            rect = self.snapped(self.clamp(before.move(delta_x, delta_y)))
                        else:
                            rect = self.snapped(self.stretched(before, handle, delta_x, delta_y), handle)
                        if zone:
                            self.zone = rect
                        else:
                            item['rect'] = rect
                            self.changed = True
                if released or (not touch and not pygame.mouse.get_pressed()[0]):
                    break
                if moved and time.perf_counter() - drawn > DRAG_FRAME:
                    self.draw()
                    drawn = time.perf_counter()
                pygame.time.wait(10)
        finally:
            self.dragging = False
        return moved

    # ------------------------------------------------------------------ actions
    def editor_menu(self):
        '''
        Back in the editor : a button added, the screen saved, or left without saving, the
        buttons arranged in a zone, the snapping on or off (back : the editor again)
        '''
        # The likely choice selected : save after changes, else leave (Add first : two times down
        # left without saving)
        initial = 'save' if self.changed else 'quit'
        while True:
            snap = f"{self.translate('editor-snap')} : {self.translate('yes' if self.snap else 'no')}"
            items = [{'id': 'add', 'action': 'add', 'text': 'editor-add-title', 'shortcut': 'F1'},
                     {'id': 'save', 'action': 'save', 'text': 'editor-save-quit', 'shortcut': 'F2'},
                     {'id': 'quit', 'action': 'quit', 'text': 'editor-quit', 'shortcut': 'F3'},
                     {'id': 'arrange', 'action': 'arrange', 'text': 'editor-arrange', 'shortcut': 'F4'},
                     {'id': 'snap', 'action': 'snap', 'text': snap, 'shortcut': 'F5'},
                     {'id': 'background', 'action': 'background', 'shortcut': 'F6',
                      'text': f"{self.translate('editor-background')} : {self.backdrop_name(self.backdrop)}"}]
            back = {'id': 'back', 'action': 'back', 'text': 'editor-continue', 'footer': 'left', 'shortcut': 'escape'}
            title = f"{self.translate('editor-title')} : {self.translate(dict(SCREENS)[self.name])}"
            choice = self.screen.run_menu('editor_menu', items + [back], items + [back], title=title,
                                          initial=initial).get('id')
            if choice != 'snap':
                return choice
            self.snap = not self.snap
            initial = 'snap'

    # ------------------------------------------------------------------ background
    def backdrop_name(self, block):
        if block is None:
            return self.translate('editor-background-theme')
        # Its folder kept (background.png of the theme and of the game) : images/ left out
        name = str(block.get('image') or block.get('color') or '') if isinstance(block, dict) else str(block)
        return name[7:] if name.startswith('images/') else name

    def backdrop_choices(self):
        '''
        The backgrounds offered : the one of the theme, then the images of the folders of the
        theme, of ~/.raspydarts and of the game (written as the menus find them : from the
        folder of the theme, of ~/.raspydarts or of the game) ; the one of the menu kept first
        if it is none of them
        '''
        theme_dir = getattr(self.screen.file_class, 'theme_dir', None)
        places = []
        if theme_dir:
            places += [(theme_dir, folder, '') for folder in BACKGROUND_FOLDERS]
        places += [(cpaths.user_dir(), folder, '') for folder in BACKGROUND_FOLDERS]
        places.append((cpaths.ROOT_DIR, 'images', 'background'))
        choices = [None]
        for base, folder, start in places:
            path = os.path.join(base, folder)
            if not os.path.isdir(path):
                continue
            for name in sorted(os.listdir(path), key=str.lower):
                if name.lower().endswith(IMAGES) and name.lower().startswith(start):
                    block = {'image': f'{folder}/{name}'.replace(os.sep, '/'), 'fit': 'cover'}
                    if block not in choices:
                        choices.append(block)
        if self.backdrop not in choices:
            choices.insert(1, self.backdrop)
        return choices

    def forget_backdrop(self, block):
        '''
        The drawings of a background left while they are browsed forgotten : a full screen
        image is 8 MB in 1920 x 1080, the painter keeps 128 of them (a Pi 3 has 1 GB)
        '''
        if not isinstance(block, dict) or not block.get('image') or block == self.backdrop_before:
            return
        painter = self.screen.menu_painter()
        image = block['image']
        for cache in (painter.backgrounds, painter.fills):
            for key in [key for key in cache if image in str(key[0])]:
                cache.pop(key, None)
        painter.images.pop(painter.image_path(image), None)

    def backdrop_key(self, key):
        '''
        The backgrounds browsed under the buttons : right and left (or a touch on the right
        or the left of the screen) the next one or the one before, Enter (or Menu) kept, Back
        the one before given back
        '''
        step = 0
        if isinstance(key, tuple):
            if self.menu_rect.collidepoint(key):
                key = 'menu'
            else:
                step = 1 if key[0] >= self.size[0] / 2 else -1
        direction = self.direction_of(key)
        if direction is not None:
            step = 1 if direction in ('right', 'down') else -1
        if step:
            index = self.backdrops.index(self.backdrop) if self.backdrop in self.backdrops else 0
            self.forget_backdrop(self.backdrop)
            self.backdrop = self.backdrops[(index + step) % len(self.backdrops)]
        elif self.key_in(key, 'validate') or key == 'menu':
            self.changed = self.changed or self.backdrop != self.backdrop_before
            self.mode = 'select'
        elif self.key_in(key, 'back'):
            self.forget_backdrop(self.backdrop)
            self.backdrop = self.backdrop_before
            self.mode = 'select'

    def give_up(self):
        '''
        Leaving without saving : asked if something changed
        '''
        return not self.changed or self.screen.ask_yes_no(self.translate('editor-discard'))

    def shortcut_text(self, button):
        keys = cmenus.as_list(button.get('shortcut'))
        if not keys or str(keys[0]).lower() == 'none':
            return self.translate('editor-shortcut-none')
        # The keys which are words : their name (Échap, Entrée, Espace)
        key = str(keys[0])
        return self.translate(f'editor-key-{key}') if key in ('escape', 'enter', 'space') else key

    def button_actions(self):
        '''
        The button chosen : moved, resized, its shortcut or its shape changed, or deleted
        '''
        item = self.items[self.selected - 1]
        name = self.button_name(item['button'])
        choice = None
        while True:
            items = [{'id': 'move', 'action': 'move', 'text': 'editor-move', 'shortcut': 'F1'},
                     {'id': 'resize', 'action': 'resize', 'text': 'editor-resize', 'shortcut': 'F2'},
                     {'id': 'shortcut', 'action': 'shortcut', 'shortcut': 'F3',
                      'text': f"{self.translate('editor-shortcut')} : {self.shortcut_text(item['button'])}"},
                     {'id': 'shape', 'action': 'shape', 'shortcut': 'F4',
                      'text': f"{self.translate('editor-shape')} : {self.translate(self.shape_text(item['button']))}"},
                     {'id': 'delete', 'action': 'delete', 'text': 'editor-delete', 'shortcut': 'F5'}]
            if item['button'].get('version'):
                # The version : no shortcut nor shape, it is only a text
                items = [entry for entry in items if entry['id'] not in ('shortcut', 'shape')]
            back = {'id': 'back', 'action': 'back', 'text': 'back', 'footer': 'left', 'shortcut': 'escape'}
            choice = self.screen.run_menu('editor_button', items + [back], items + [back], title=name,
                                          initial=choice if choice in ('shortcut', 'shape') else None).get('id')
            if choice == 'shortcut':
                self.shortcut(item)
                continue
            if choice == 'shape':
                self.shape(item)
                continue
            if choice in ('move', 'resize'):
                self.mode = choice
                self.handle = 4
            elif choice == 'delete' and self.screen.ask_yes_no(f"{self.translate('editor-delete-confirm')} ({name})"):
                ident = self.menus.button_id(item['button'])
                if not item.get('new') and not item['button'].get('version'):
                    self.removed.append(ident)
                del self.items[self.selected - 1]
                self.selected = max(1, min(self.selected, len(self.items)))
                self.changed = True
            return

    @staticmethod
    def shape_text(button):
        '''
        The shape of a button : its own, or the one of its style
        '''
        return f"editor-shape-{button['shape']}" if button.get('shape') in SHAPES else 'editor-shape-style'

    def shape(self, item):
        '''
        The shape of a button : rectangle, rounded corners, round ends (a square button : a
        circle), or the one of its style (the others of the screen)
        '''
        button = item['button']
        values = [('style', 'editor-shape-style')] + [(shape, f'editor-shape-{shape}') for shape in SHAPES]
        current = button.get('shape') if button.get('shape') in SHAPES else 'style'
        chosen = self.screen.dropdown(self.screen.res['x'] * 6 / 16, 3 * self.screen.res_y_16, values, navigate=current)
        if chosen in ('escape', current):
            return
        if chosen == 'style':
            button.pop('shape', None)
        else:
            button['shape'] = chosen
        self.changed = True

    def shortcut(self, item):
        '''
        The shortcut of a button : changed (the key pressed ; taken from another button of
        the screen if wanted) or removed
        '''
        button = item['button']
        has = self.shortcut_text(button) != self.translate('editor-shortcut-none')
        items = [{'id': 'change', 'action': 'change', 'text': 'editor-shortcut-change', 'shortcut': 'F1'}]
        if has:
            items.append({'id': 'remove', 'action': 'remove', 'text': 'editor-shortcut-remove', 'shortcut': 'F2'})
        back = {'id': 'back', 'action': 'back', 'text': 'back', 'footer': 'left', 'shortcut': 'escape'}
        title = f"{self.button_name(button)} · {self.translate('editor-shortcut')} : {self.shortcut_text(button)}"
        choice = self.screen.run_menu('editor_button', items + [back], items + [back], title=title).get('id')
        if choice == 'remove':
            button.pop('shortcut', None)
            self.changed = True
            return
        if choice != 'change':
            return
        self.screen.display_background()
        self.screen.menu_header(self.button_name(button), self.translate('editor-shortcut-press'))
        self.screen.update_screen()
        while True:
            key = self.listen()
            if self.key_in(key, 'back'):
                return
            key = str(key)
            if SHORTCUT_KEYS.match(key):
                break
        # Another button of the screen with this key : it loses it if wanted
        for other in self.items:
            if other is not item and key in [str(value) for value in cmenus.as_list(other['button'].get('shortcut'))]:
                question = self.translate('editor-shortcut-taken').replace('{key}', key).replace(
                    '{button}', self.button_name(other['button']))
                if not self.screen.ask_yes_no(question):
                    return
                other['button'].pop('shortcut', None)
        button['shortcut'] = key
        self.changed = True

    def clamp(self, rect):
        '''
        A rect kept on the screen
        '''
        rect = pygame.Rect(rect)
        rect.width = min(rect.width, self.size[0])
        rect.height = min(rect.height, self.size[1])
        rect.x = max(0, min(rect.x, self.size[0] - rect.width))
        rect.y = max(0, min(rect.y, self.size[1] - rect.height))
        return rect

    def stretched(self, rect, handle, delta_x, delta_y):
        '''
        A rect whose handle moved : the edges it is on, kept on the screen and not too small
        '''
        part_x, part_y = HANDLES[handle]
        smallest_x, smallest_y = int(SMALLEST * self.size[0]), int(SMALLEST * self.size[1])
        left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
        if part_x == 0:
            left = max(0, min(left + delta_x, right - smallest_x))
        elif part_x == 1:
            right = min(self.size[0], max(right + delta_x, left + smallest_x))
        if part_y == 0:
            top = max(0, min(top + delta_y, bottom - smallest_y))
        elif part_y == 1:
            bottom = min(self.size[1], max(bottom + delta_y, top + smallest_y))
        return pygame.Rect(left, top, right - left, bottom - top)

    def stepped(self, key):
        '''
        + and - : the step (one pixel to 5 % of the screen). True if the key was one of them
        '''
        if key in self.keys['plus']:
            self.step = min(len(STEPS) - 1, self.step + 1)
        elif key in self.keys['minus']:
            self.step = max(0, self.step - 1)
        else:
            return False
        return True

    def moving(self, key):
        '''
        Move of the button chosen : arrows (by the step), + and - (the step), validate or
        back (done)
        '''
        item = self.items[self.selected - 1]
        direction = self.direction_of(key)
        if direction is not None:
            step_x, step_y = self.step_pixels('x'), self.step_pixels('y')
            move_x, move_y = {'up': (0, -step_y), 'down': (0, step_y), 'left': (-step_x, 0), 'right': (step_x, 0)}[direction]
            rect = item['rect']
            item['rect'] = self.clamp(rect.move(self.on_the_way(self.edges(rect, 'x'), move_x, 'x'),
                                                self.on_the_way(self.edges(rect, 'y'), move_y, 'y')))
            self.changed = True
        elif self.stepped(key):
            pass
        elif self.key_in(key, 'validate') or self.key_in(key, 'back'):
            self.mode = 'select'

    def resizing(self, key):
        '''
        Resize of the button chosen by one of its handles : arrows (the handle, by the step),
        + and - (the step), validate (the next handle), back (done)
        '''
        item = self.items[self.selected - 1]
        direction = self.direction_of(key)
        if direction is not None:
            item['rect'] = self.handle_moved(item['rect'], direction)
            self.changed = True
        elif self.stepped(key):
            pass
        elif self.key_in(key, 'validate'):
            self.handle = (self.handle + 1) % len(HANDLES)
        elif self.key_in(key, 'back'):
            self.mode = 'select'

    def handle_moved(self, rect, direction):
        '''
        A rect whose handle is moved by an arrow (by the step, stopped on the lines met)
        '''
        part_x, part_y = HANDLES[self.handle]
        delta_x = {'left': -1, 'right': 1}.get(direction, 0) * self.step_pixels('x')
        delta_y = {'up': -1, 'down': 1}.get(direction, 0) * self.step_pixels('y')
        if part_x in (0, 1):
            delta_x = self.on_the_way([rect.left if part_x == 0 else rect.right], delta_x, 'x')
        if part_y in (0, 1):
            delta_y = self.on_the_way([rect.top if part_y == 0 else rect.bottom], delta_y, 'y')
        return self.stretched(rect, self.handle, delta_x, delta_y)

    # ------------------------------------------------------------------ arranging
    def zoning(self, key):
        '''
        The zone of the buttons to arrange : arrows (its handle, by the step), + and - (the
        step), validate (the next handle). True : done (back, or the button Menu)
        '''
        direction = self.direction_of(key)
        if direction is not None:
            self.zone = self.handle_moved(self.zone, direction)
        elif self.stepped(key):
            pass
        elif self.key_in(key, 'validate'):
            self.handle = (self.handle + 1) % len(HANDLES)
        elif self.key_in(key, 'back') or key == 'menu':
            return True
        return False

    @staticmethod
    def reading_order(items):
        '''
        Buttons in the order they are read (rows from the top, each from the left), and the
        most buttons in a row
        '''
        rows = []
        for item in sorted(items, key=lambda item: item['rect'].centery):
            first = rows[-1][0]['rect'] if rows else None
            if first is not None and item['rect'].centery - first.centery < first.height / 2:
                rows[-1].append(item)
            else:
                rows.append([item])
        ordered = [item for row in rows for item in sorted(row, key=lambda item: item['rect'].centerx)]
        return ordered, max((len(row) for row in rows), default=1)

    def arranged_items(self):
        '''
        The buttons to arrange : all of them, or those whose centre is in the zone
        '''
        # The version stays where it is
        items = [item for item in self.items if not item['button'].get('version')]
        if not self.arrangement['inside']:
            return items
        return [item for item in items if self.zone.collidepoint(item['rect'].center)]

    def arrange_menu(self):
        '''
        The buttons arranged in the zone : columns, rows, the space between them, which
        buttons ; the zone changed again ; back : the editor, nothing arranged
        '''
        translate = self.translate
        settings = self.arrangement
        initial = 'apply'
        choose = lambda values, current: self.screen.dropdown(self.screen.res['x'] * 6 / 16, 3 * self.screen.res_y_16,
                                                              values, navigate=current)
        while True:
            chosen, widest = self.reading_order(self.arranged_items())
            count = max(1, len(chosen))
            if not settings['columns']:
                settings['columns'] = min(MOST_CELLS, widest)
            if not settings['rows']:
                settings['rows'] = min(MOST_CELLS, -(-count // settings['columns']))
            values = [('columns', 'editor-arrange-columns', str(settings['columns'])),
                      ('rows', 'editor-arrange-rows', str(settings['rows'])),
                      ('gap', 'editor-arrange-gap', f"{settings['gap'] * 100:g} %"),
                      ('inside', 'editor-arrange-buttons',
                       f"{translate('editor-arrange-inside' if settings['inside'] else 'editor-arrange-all')} ({len(chosen)})")]
            items = [{'id': ident, 'action': ident, 'text': f"{translate(text)} : {value}", 'shortcut': f'F{number}'}
                     for number, (ident, text, value) in enumerate(values, 1)]
            items += [{'id': 'apply', 'action': 'apply', 'text': 'editor-arrange-apply', 'shortcut': 'F5'},
                      {'id': 'zone', 'action': 'zone', 'text': 'editor-arrange-zone', 'shortcut': 'F6'}]
            back = {'id': 'back', 'action': 'back', 'text': 'back', 'footer': 'left', 'shortcut': 'escape'}
            choice = self.screen.run_menu('editor_arrange', items + [back], items + [back],
                                          title=translate('editor-arrange'), initial=initial).get('id')
            initial = choice
            numbers = [(str(number), str(number)) for number in range(1, MOST_CELLS + 1)]
            if choice in ('columns', 'rows'):
                value = choose(numbers, str(settings[choice]))
                if value != 'escape':
                    settings[choice] = int(value)
                    if choice == 'columns':
                        settings['rows'] = None
            elif choice == 'gap':
                value = choose([(str(gap), f'{gap * 100:g} %') for gap in GAPS], str(settings['gap']))
                if value != 'escape':
                    settings['gap'] = float(value)
            elif choice == 'inside':
                settings['inside'] = not settings['inside']
                settings['columns'] = settings['rows'] = None
            elif choice == 'zone':
                return
            elif choice == 'apply':
                if self.arrange(chosen):
                    self.mode, self.zone = 'select', None
                    return
            else:
                self.mode, self.zone = 'select', None
                return

    def arrange(self, chosen):
        '''
        The buttons put in the cells of the zone, in the order they are read, all of the
        same size : False (said) if they do not fit
        '''
        columns, rows = self.arrangement['columns'], self.arrangement['rows']
        if not chosen:
            self.screen.message([self.translate('editor-arrange-none')], 2500, 'menu-ko', 'middle', 'big')
            return False
        if columns * rows < len(chosen):
            text = self.translate('editor-arrange-too-few').replace('{buttons}', str(len(chosen))).replace(
                '{cells}', str(columns * rows))
            self.screen.message([text], 3000, 'menu-ko', 'middle', 'big')
            return False
        gap_x, gap_y = int(self.arrangement['gap'] * self.size[0]), int(self.arrangement['gap'] * self.size[1])
        width = (self.zone.width - gap_x * (columns - 1)) // columns
        height = (self.zone.height - gap_y * (rows - 1)) // rows
        if width < SMALLEST * self.size[0] or height < SMALLEST * self.size[1]:
            self.screen.message([self.translate('editor-arrange-too-small')], 3000, 'menu-ko', 'middle', 'big')
            return False
        for number, item in enumerate(chosen):
            row, column = divmod(number, columns)
            item['rect'] = pygame.Rect(self.zone.x + column * (width + gap_x), self.zone.y + row * (height + gap_y),
                                       width, height)
        self.changed = True
        return True

    # ------------------------------------------------------------------ adding
    def addable(self):
        '''
        Buttons which can be added : those of the game for this menu which are not shown,
        and for the main menu the favorites, the categories and the games
        '''
        present = {self.menus.button_id(item['button']) for item in self.items}
        choices = []
        defaults = cmenus.Menus(self.screen.logs, None, None).menu(self.name).get('buttons') or []
        for button in defaults:
            ident = self.menus.button_id(button)
            if ident not in present and not button.get('footer') and button.get('visible', True) is not False:
                choices.append((self.button_name(button), self.clean(button)))
        if self.name == 'main':
            actions = {str(item['button'].get('action')) for item in self.items}
            for slot, favorite in self.screen.favorites().numbered():
                if f'favorite:{slot}' not in actions:
                    text = f"{self.translate('favorite')} {slot[3:]} : {favorite['game'].replace('_', ' ')}"
                    choices.append((text, {'id': slot, 'action': f'favorite:{slot}'}))
            # As in the screen of the categories : their logo, their name
            for category, logo in (('classic', 'menu_classic'), ('fun', 'menu_fun'), ('sport', 'menu_sport'),
                                   ('favorites', 'menu_favoris')):
                if f'category:{category}' not in actions:
                    text = f'dmd-game-{category}'
                    choices.append((f"{self.translate('editor-category')} : {self.translate(text)}",
                                    {'id': f'category-{category}', 'action': f'category:{category}',
                                     'text': text, 'logo': logo}))
            choices.append((self.translate('editor-add-game'), 'game'))
            # The version, deleted before
            if not any(item['button'].get('version') for item in self.items):
                choices.append((self.translate('editor-version'), {'id': VERSION_ID, 'version': True}))
            # The panel of the players online (include/cscreen.py online_players_panel)
            if 'online_players' not in actions:
                choices.append((self.translate('online-players-panel'),
                                {'id': 'online-players', 'action': 'online_players', 'text': 'online-players-panel'}))
        return choices

    def choose_game(self):
        '''
        A game chosen by its category then its name (in columns), None : back
        '''
        back = {'id': 'back', 'action': 'back', 'text': 'back', 'footer': 'left', 'shortcut': 'escape'}
        categories = [{'id': category, 'action': category, 'text': text, 'shortcut': f'F{number}'}
                      for number, (category, text) in enumerate((('classic', 'Classics'), ('fun', 'Fun'), ('sport', 'Sports')), 1)]
        while True:
            category = self.screen.run_menu('editor_add', categories + [back], categories + [back],
                                            title=self.translate('editor-add-game')).get('id')
            if category == 'back':
                return None
            games = sorted(self.screen.get_games_list(category))
            items = [{'id': f'game{number}', 'action': 'game', 'text': game} for number, game in enumerate(games)]
            choice = self.screen.run_menu('editor_games', items + [back], items + [back],
                                          title=self.translate('editor-add-game')).get('id')
            if choice != 'back':
                return games[int(choice[4:])]

    def add(self):
        '''
        A button added in the middle of the screen, as big as the others (then to be placed)
        '''
        choices = self.addable()
        back = {'id': 'back', 'action': 'back', 'text': 'back', 'footer': 'left', 'shortcut': 'escape'}
        items = [{'id': f'add{number}', 'action': 'add', 'text': text} for number, (text, _) in enumerate(choices)]
        for number, item in enumerate(items[:9], 1):
            item['shortcut'] = f'F{number}'
        choice = self.screen.run_menu('editor_add', items + [back], items + [back],
                                      title=self.translate('editor-add-title')).get('id')
        if choice == 'back':
            return
        button = choices[int(choice[3:])][1]
        if button == 'game':
            game = self.choose_game()
            if game is None:
                return
            name = game.replace(' ', '_')
            button = {'id': f'game-{name}', 'action': f'game:{name}', 'text': game}
        # An id not used in this menu
        ident, number = self.menus.button_id(button), 2
        used = {self.menus.button_id(item['button']) for item in self.items}
        while self.menus.button_id(button) in used:
            button['id'] = f"{ident}-{number}"
            number += 1
        # Its shortcut already taken by a button of the screen (the theme moved them : the coin
        # acceptor came with F7, the one of Test de la cible) : none, one can be given after
        # (one without shortcut : nothing to compare, other buttons may have none either)
        if button.get('shortcut') and button.get('shortcut') in {item['button'].get('shortcut') for item in self.items}:
            button = dict(button)
            button.pop('shortcut')
        widths = sorted(item['rect'].width for item in self.items) or [int(self.size[0] / 4)]
        heights = sorted(item['rect'].height for item in self.items) or [int(self.size[1] / 10)]
        rect = pygame.Rect(0, 0, widths[len(widths) // 2], heights[len(heights) // 2])
        if button.get('version'):
            # The version : the size it has by default
            rect = self.screen.menu_version_rect(True)
        rect.center = (self.size[0] // 2, self.size[1] // 2)
        self.items.append({'button': button, 'rect': rect, 'new': True})
        if ident in self.removed:
            self.removed.remove(ident)
        self.selected = len(self.items)
        self.changed = True

    # ------------------------------------------------------------------ saving
    def place_of(self, rect):
        '''
        Free placement of a rect, in the units of the file (section 4)
        '''
        reference = self.units.reference
        values = {}
        for key, value, axis in (('x', rect.x, 'x'), ('y', rect.y, 'y'), ('width', rect.width, 'x'), ('height', rect.height, 'y')):
            size = self.size[0] if axis == 'x' else self.size[1]
            if reference is None:
                values[key] = round(value / size, 4)
            else:
                values[key] = int(round(value * (reference[0] if axis == 'x' else reference[1]) / size))
        return values

    def file_path(self):
        theme_dir = getattr(self.screen.file_class, 'theme_dir', None)
        return os.path.join(theme_dir, cmenus.THEME_FILE) if theme_dir else None

    def save(self):
        '''
        The menu written in the menus of the theme : its whole list of buttons (the hidden
        ones and those at the bottom kept), each button shown placed where it is
        '''
        path = self.file_path()
        try:
            if yaml is None or path is None:
                raise RuntimeError('no PyYAML or no theme')
            content = {}
            if os.path.isfile(path):
                with open(path, encoding='utf-8') as file:
                    content = yaml.safe_load(file) or {}
            menus = content.setdefault('menus', {})
            menu = menus.get(self.name) if isinstance(menus.get(self.name), dict) else {}
            menus[self.name] = menu
            placed = {self.menus.button_id(item['button']): item for item in self.items}
            # The version : in show_version (its colour and font kept), not in the buttons
            version = placed.pop(VERSION_ID, None)
            if version is not None:
                look = dict(self.version_shown) if isinstance(self.version_shown, dict) else {}
                look.update(self.place_of(version['rect']))
                menu['show_version'] = look
            elif self.version_shown:
                menu['show_version'] = False
            buttons = []
            for button in self.menu.get('buttons') or []:
                if not isinstance(button, dict):
                    continue
                ident = self.menus.button_id(button)
                if ident in self.removed:
                    continue
                button = self.clean(button)
                if ident in placed:
                    item = placed.pop(ident)
                    button = dict(item['button'])
                    for key in LAYOUT_KEYS:
                        button.pop(key, None)
                    button['place'] = self.place_of(item['rect'])
                buttons.append(button)
            # The buttons added : after the others, before those at the bottom
            at = next((index for index, button in enumerate(buttons) if button.get('footer')), len(buttons))
            for item in placed.values():
                button = dict(item['button'])
                button['place'] = self.place_of(item['rect'])
                buttons.insert(at, button)
                at += 1
            menu['buttons'] = buttons
            menu.pop('button_changes', None)
            if self.backdrop != self.menu.get('background'):
                # Its background : its own image, or none (the one of the theme)
                if self.backdrop is None:
                    menu.pop('background', None)
                else:
                    menu['background'] = self.backdrop
            removed = [str(ident) for ident in cmenus.as_list(menu.get('removed'))]
            menu['removed'] = sorted(set(removed + self.removed)) if set(removed + self.removed) else None
            if menu['removed'] is None:
                menu.pop('removed')
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if os.path.isfile(path):
                shutil.copyfile(path, f'{path}.bak')
            temporary = f'{path}.tmp'
            with open(temporary, 'w', encoding='utf-8') as file:
                yaml.safe_dump(content, file, allow_unicode=True, sort_keys=False, default_flow_style=False)
            os.replace(temporary, path)
            self.screen.logs.info(f"Menus : {self.name} saved by the editor in {path}")
        except Exception as error:    # pylint: disable=broad-except
            self.screen.logs.error(f"Menus : {self.name} not saved ({error})")
            self.screen.message([self.translate('editor-not-saved')], 2500, 'menu-ko', 'middle', 'big')
            return False
        # The menus read again, their drawings forgotten
        self.screen.menus_read = None
        self.screen.menu_backgrounds.clear()
        self.screen.menu_composites.clear()
        self.screen.message([self.translate('editor-saved')], 1500, None, 'middle', 'big')
        return True


def screens_menu(screen, keys):
    '''
    Paramètres > Modifier les écrans : the screen chosen, then its editor ; saved or left :
    the list again, this screen selected (the keys repeated while saving are cleared by the
    editor : they no longer open it again), until Back
    '''
    back = {'id': 'back', 'action': 'back', 'text': 'back', 'footer': 'left', 'shortcut': 'escape'}
    items = [{'id': name, 'action': name, 'text': text, 'shortcut': f'F{number}'}
             for number, (name, text) in enumerate(SCREENS, 1)]
    choice = None
    while True:
        choice = screen.run_menu('edit_screens', items + [back], items + [back],
                                 title=screen.lang.translate('edit-screens'), initial=choice).get('id')
        if choice not in dict(SCREENS):
            return
        Editor(screen, choice, keys).run()
