"""
Activity indicator : what goes on in the background (the video of the animated background
prepared, Raspy2DMD installed, an update downloaded, players awaited for a game on the
network...) shown in a corner of the screens of the menus (the corner of the settings, at the
top right by default), over the animated background or the background of the theme.

Each task gives a function returning its state : None (finished, the line goes away), or a
dict : text, fraction (0 to 1 ; None : waiting, an animation instead of a bar), final (its
end said : shown a few seconds then gone). A task can be chosen (select : a function) : the
indicator is then a button of the menus (see Screen.run_menu), reached with the wheel of a USB
knob, the buttons, the arrows or a touch, framed when it is selected.
"""

import time

import pygame

CORNERS = ('top-right', 'top-left', 'bottom-right', 'bottom-left')
# A final state (« installed ») shown this long
FINAL_TIME = 6
# Drawn again this often when nothing else draws the screen (its bar, its animation)
REFRESH = 0.3


class Activities:
    '''
    The tasks shown by the indicator of a Screen (cscreen)
    '''

    def __init__(self, screen):
        self.owner = screen
        self.items = {}
        self.selects = {}
        # Selected as a button of a menu
        self.focused = False
        self.states = {}
        self.finals = {}
        self.under = None
        self.last = 0
        self.drawn_rect = None
        self.font = None
        self.font_size = None

    # ------------------------------------------------------------------ tasks
    def add(self, key, state, select=None):
        '''
        A task shown while state() gives something (see the module) ; select : done when the
        indicator is chosen
        '''
        self.items[key] = state
        if select is not None:
            self.selects[key] = select
        self.finals.pop(key, None)

    def remove(self, key):
        self.items.pop(key, None)
        self.selects.pop(key, None)
        self.states.pop(key, None)
        self.finals.pop(key, None)

    def current(self):
        '''
        The states of the tasks of the moment (the finished ones removed, a final one kept a
        few seconds)
        '''
        now = time.time()
        shown = []
        for key, state in list(self.items.items()):
            try:
                value = state()
            except Exception as error:    # pylint: disable=broad-except
                self.owner.logs.error(f"Activity {key} : {error}")
                value = None
            if value is not None and value.get('final'):
                started = self.finals.setdefault(key, now)
                if now - started > FINAL_TIME:
                    value = None
            if value is None:
                self.remove(key)
                continue
            shown.append(value)
        return shown

    def visible(self):
        '''
        Shown on every screen out of the games (the menus, Modifier les écrans, the settings...)
        '''
        animated = getattr(self.owner, 'bganim', None)
        return bool(self.items) and animated is not None and not animated.in_game

    def selectable(self):
        '''
        A task can be chosen : the indicator is a button of the menus
        '''
        return any(key in self.items for key in self.selects)

    def choose(self):
        '''
        The indicator chosen : what its task does (the first one which can be chosen)
        '''
        for key, select in list(self.selects.items()):
            if key in self.items:
                return select()
        return None

    def focus_place(self, selected):
        '''
        As a button of a menu : selected or not, its place (to click, to move to)
        '''
        self.focused = bool(selected)
        return tuple(self.place(max(1, len(self.items)))[0])

    # ------------------------------------------------------------------ drawing
    def corner(self):
        corner = str(self.owner.config.get_value('SectionGlobals', 'activity_corner', False) or 'top-right')
        return corner if corner in CORNERS else 'top-right'

    def sample(self, surface, corner):
        '''
        Where the window will be (Personnalisation, its line selected) : an example in a yellow
        frame, at this corner. Its rectangle
        '''
        rect, line = self.place(1, corner)
        size = max(10, int(line * 0.34))
        font = self.owner.font(self.owner.defaultfontpath, size)
        radius = int(line / 5)
        item = pygame.Rect(rect.x, rect.y, rect.width, line - 4)
        pygame.draw.rect(surface, (25, 25, 25), item, border_radius=radius)
        pygame.draw.rect(surface, (255, 220, 0), item, max(3, int(line * 0.06)), border_radius=radius)
        rendered = font.render(self.owner.lang.translate('activity-sample'), True, (255, 255, 255))
        if rendered.get_width() > item.width - 2 * radius:
            rendered = pygame.transform.smoothscale(rendered, (item.width - 2 * radius, rendered.get_height()))
        surface.blit(rendered, (item.x + radius, item.y + int(line * 0.08)))
        bar = pygame.Rect(item.x + radius, item.bottom - int(line * 0.32), item.width - 2 * radius, int(line * 0.16))
        pygame.draw.rect(surface, (70, 70, 70), bar, border_radius=bar.height // 2)
        pygame.draw.rect(surface, (255, 220, 0), (bar.x, bar.y, int(bar.width * 0.45), bar.height),
                         border_radius=bar.height // 2)
        return item

    def place(self, count, corner=None):
        '''
        The rectangle of the indicator for this number of tasks, in its corner, away from the
        credits of the coin acceptor when they are in the same one
        '''
        res_x, res_y = self.owner.res['x'], self.owner.res['y']
        width, line = int(res_x * 0.24), int(res_y * 0.08)
        height = line * count
        margin = int(res_y / 60)
        corner = corner if corner in CORNERS else self.corner()
        pos_x = res_x - width - margin if corner.endswith('right') else margin
        # At the top : over the band of the title ; at the bottom : over the buttons (Back, Quit...)
        pos_y = margin if corner.startswith('top') else res_y - height - int(res_y * 0.105)
        coins = getattr(getattr(self.owner, 'rpi', None), 'coins', None)
        try:
            if coins is not None and coins.left() is not None \
                    and str(coins.settings.get('badge_position') or 'top-right') == corner:
                from include import ccoins    # pylint: disable=import-outside-toplevel
                part_y = ccoins.BADGE_SIZES.get(coins.settings.get('badge_size'), ccoins.BADGE_SIZES['medium'])[1]
                shift = int(res_y * part_y) + margin
                pos_y += shift if corner.startswith('top') else -shift
        except Exception:    # pylint: disable=broad-except
            pass
        return pygame.Rect(pos_x, pos_y, width, height), line

    def draw(self, surface):
        '''
        The indicator drawn on this surface : its rectangle, None : nothing to show
        '''
        if not self.visible():
            return None
        states = self.current()
        if not states:
            return None
        rect, line = self.place(len(states))
        colorset = self.owner.colorset
        size = max(10, int(line * 0.34))
        if self.font is None or self.font_size != size:
            self.font = self.owner.font(self.owner.defaultfontpath, size)
            self.font_size = size
        background = (25, 25, 25)
        accent = tuple(colorset.get('menu-selected') or (200, 200, 200))[:3]
        good = tuple(colorset.get('menu-ok') or (40, 170, 60))[:3]
        radius = int(line / 5)
        for index, state in enumerate(states):
            item = pygame.Rect(rect.x, rect.y + index * line, rect.width, line - 4)
            pygame.draw.rect(surface, background, item, border_radius=radius)
            framed = self.focused and self.selectable()
            pygame.draw.rect(surface, good if state.get('final') else accent, item, max(2, int(line * 0.08)) if framed else 2,
                             border_radius=radius)
            text = str(state.get('text') or '')
            rendered = self.font.render(text, True, (255, 255, 255))
            room = item.width - 2 * radius
            if rendered.get_width() > room:
                rendered = pygame.transform.smoothscale(rendered, (room, rendered.get_height()))
            surface.blit(rendered, (item.x + radius, item.y + int(line * 0.08)))
            bar = pygame.Rect(item.x + radius, item.bottom - int(line * 0.32), item.width - 2 * radius, int(line * 0.16))
            fraction = state.get('fraction')
            if state.get('final'):
                continue
            pygame.draw.rect(surface, (70, 70, 70), bar, border_radius=bar.height // 2)
            if fraction is not None:
                done = pygame.Rect(bar.x, bar.y, max(bar.height, int(bar.width * max(0.0, min(1.0, fraction)))), bar.height)
                pygame.draw.rect(surface, accent, done, border_radius=bar.height // 2)
            else:
                # Waiting : a part of the bar going back and forth
                phase = (time.time() % 2) / 2
                phase = phase * 2 if phase < 0.5 else (1 - phase) * 2
                part = int(bar.width / 4)
                moving = pygame.Rect(bar.x + int((bar.width - part) * phase), bar.y, part, bar.height)
                pygame.draw.rect(surface, accent, moving, border_radius=bar.height // 2)
        self.drawn_rect = rect
        return rect

    def over(self, surface):
        '''
        Drawn over a screen about to be sent, what was under kept (see restore) : its
        rectangle, None : nothing drawn
        '''
        if not self.visible():
            self.focused = False
            return self.erase_rect()
        states_rect, _line = self.place(max(1, len(self.items)))
        area = states_rect.clip(surface.get_rect())
        self.under = (area, surface.subsurface(area).copy())
        drawn = self.draw(surface)
        if drawn is None:
            self.restore(surface)
            return self.erase_rect()
        previous = self.drawn_rect if self.drawn_rect is not None else drawn
        return drawn.union(previous)

    def erase_rect(self):
        '''
        The place of the indicator gone : sent again once (its last picture removed)
        '''
        rect, self.drawn_rect = self.drawn_rect, None
        return rect

    def restore(self, surface):
        '''
        What was under the indicator back in the surface (the screen keeps no trace of it)
        '''
        if self.under is not None:
            area, picture = self.under
            surface.blit(picture, area)
            self.under = None

    def tick(self):
        '''
        At the turns of the reading of the inputs : the indicator drawn again (its bar, its
        animation) when the animated background does not
        '''
        owner = self.owner
        animated = getattr(owner, 'bganim', None)
        if animated is not None and animated.mode == 'layer' and animated.frames:
            return
        if not self.items and self.drawn_rect is None:
            return
        now = time.time()
        if now - self.last < REFRESH:
            return
        self.last = now
        surface = owner.screen
        rect = self.over(surface)
        if rect is not None:
            pygame.display.update(rect)
        self.restore(surface)
