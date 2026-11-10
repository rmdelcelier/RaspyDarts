"""
Modifier les écrans > Fond animé : an explorer (include/cexplorer.py) opened at once, its first
lines : no animated background, the drawn effect (its settings and what it gives, live), the
animated backgrounds drawn (logo, stars, shapes : each played in the preview), the rate and how
the preparation goes ; then the folders, the videos and animated GIF played in the preview.
Nothing is changed before a choice is validated.
"""

import os
import time

import pygame

from include import cbganim
from include import ceffects
from include import cexplorer
from include import cpaths

LOGO = os.path.join(cpaths.ROOT_DIR, 'images', 'boot_logo.png')
EFFECT_KEYS = (('effect', 'animated_effect', ceffects.EFFECTS, 'animated-effect-', 'none'),
               ('effect-color', 'animated_effect_color', tuple(ceffects.COLORS), 'animated-effect-color-', 'auto'),
               ('effect-amount', 'animated_effect_amount', tuple(ceffects.AMOUNTS), 'animated-effect-amount-', 'normal'),
               ('effect-speed', 'animated_effect_speed', tuple(ceffects.SPEEDS), 'animated-effect-speed-', 'normal'))
RATE = 25


def menu_background(screen, size):
    '''
    The background of the menus as they are shown (the still picture of the video chosen, or
    the background of the theme), at this size : what an effect is seen over
    '''
    animated = screen.bganim
    picture = None
    if animated.still and animated.still_surface() is not None:
        picture = animated.still_surface()
    else:
        picture = pygame.Surface(screen.screen.get_size(), 0, screen.screen)
        saved = screen.screen
        screen.screen = picture
        try:
            screen.display_background()
        finally:
            screen.screen = saved
    return pygame.transform.smoothscale(picture, size)


class Preview:
    '''
    Something played in the box of the preview of the explorer, or of the screen of the effect :
    drawn at each turn of the reading of the inputs (tick), RATE times a second at most
    '''

    def __init__(self, screen, box):
        self.screen = screen
        self.box = pygame.Rect(box)
        self.surface = pygame.Surface(self.box.size, 0, screen.screen)
        self.last = time.time()
        self.next = 0
        self.path = None

    def caption(self, translate):
        return ''

    def frame(self, elapsed):
        raise NotImplementedError

    def tick(self):
        now = time.time()
        if now < self.next:
            return
        # Someone looking with VNC : slower (see cbganim.remote_viewer)
        self.next = now + 1 / (cbganim.REMOTE_RATE if cbganim.remote_viewer() else RATE)
        elapsed, self.last = now - self.last, now
        if self.frame(elapsed) is False:
            # Nothing changed : nothing sent
            return
        self.screen.screen.blit(self.surface, self.box)
        self.screen.update_screen(rect=self.box)

    def stop(self):
        pass


class EffectPreview(Preview):
    '''
    A drawn effect over the background of the menus
    '''

    def __init__(self, screen, box, settings):
        super().__init__(screen, box)
        self.base = menu_background(screen, self.box.size)
        self.settings = None
        self.effect = None
        self.set(settings)

    def set(self, settings):
        if settings != self.settings:
            self.settings = settings
            self.still = False
            name, color, amount, speed = settings
            self.effect = ceffects.make(name, self.box.size, color, amount, speed,
                                        theme_color=self.screen.colorset.get('menu-selected'))

    def caption(self, translate):
        return translate(f'animated-effect-{self.settings[0]}')

    def frame(self, elapsed):
        if self.effect is None and getattr(self, 'still', False):
            return False
        self.still = self.effect is None
        self.surface.blit(self.base, (0, 0))
        if self.effect is not None:
            self.effect.step(elapsed)
            self.effect.draw(self.surface)
        return True


class ScenePreview(Preview):
    '''
    An animated background drawn (its background kept once)
    '''

    def __init__(self, screen, box, name):
        super().__init__(screen, box)
        self.name = name
        self.scene = ceffects.make_scene(name, self.box.size, LOGO, theme_color=screen.colorset.get('menu-selected'))
        self.base = self.scene.background() if self.scene is not None else None

    def caption(self, translate):
        return translate(f'animated-scene-{self.name}')

    def frame(self, elapsed):
        if self.scene is None:
            # No animated background : drawn once
            if getattr(self, 'blank', False):
                return False
            self.blank = True
            self.surface.fill((0, 0, 0))
            return True
        self.surface.blit(self.base, (0, 0))
        self.scene.step(elapsed)
        self.scene.draw(self.surface)


class StatusPreview(Preview):
    '''
    The rate, how the preparation of the video goes, what the animated background does
    '''

    def __init__(self, screen, box):
        super().__init__(screen, box)
        self.text = None

    def frame(self, elapsed):
        from include import cmenueditor    # pylint: disable=import-outside-toplevel
        translate = self.screen.lang.translate
        status = cmenueditor.animated_status(self.screen)
        text = (status, translate('animated-background-help'))
        if text == self.text:
            return False
        self.text = text
        self.surface.fill((40, 40, 40))
        inner = self.surface.get_rect().inflate(-int(self.box.width * 0.08), -int(self.box.height * 0.08))
        saved = self.screen.screen
        self.screen.screen = self.surface
        try:
            cmenueditor.paragraph(self.screen, status, pygame.Rect(inner.x, inner.y, inner.width, int(inner.height * 0.3)),
                                  (255, 220, 0))
            cmenueditor.paragraph(self.screen, text[1], pygame.Rect(inner.x, inner.y + int(inner.height * 0.35), inner.width,
                                                                    int(inner.height * 0.65)), (255, 255, 255))
        finally:
            self.screen.screen = saved

    def tick(self):
        # Once a second is enough
        now = time.time()
        if now < self.next:
            return
        super().tick()
        self.next = now + 1


def settings_of(screen):
    globals_ = screen.config.config['SectionGlobals']
    return tuple(str(globals_.get(key) or default) for _name, key, _choices, _prefix, default in EFFECT_KEYS)


def save(screen, **values):
    globals_ = screen.config.config['SectionGlobals']
    for key, value in values.items():
        globals_[key] = value
    screen.config.write_file()
    screen.bganim.apply_settings()


def choose(screen, keys):
    '''
    The explorer of the animated background, until Back or a background chosen
    '''
    from include import cmenueditor    # pylint: disable=import-outside-toplevel
    translate = screen.lang.translate
    while True:
        globals_ = screen.config.config['SectionGlobals']
        video = str(globals_.get('animated_background') or '')
        scene = str(globals_.get('animated_scene') or 'none')
        settings = settings_of(screen)
        rate = str(globals_.get('animated_background_rate') or 'auto')
        extras = [
            ('none', translate('animated-background-none-all'), None,
             lambda screen_, box: ScenePreview(screen_, box, 'none')),
            ('effect', f"{translate('animated-background-effect')} : {translate('animated-effect-' + settings[0])}", None,
             lambda screen_, box: EffectPreview(screen_, box, settings)),
            ('scenes', f"{translate('animated-background-scenes')} : {translate('animated-scene-' + scene)}", None,
             lambda screen_, box: ScenePreview(screen_, box, scene if scene != 'none' else 'night-sky')),
            ('rate', f"{translate('animated-background-rate')} : {cmenueditor.rate_text(screen, rate, short=True)}", None,
             lambda screen_, box: StatusPreview(screen_, box)),
        ]
        chosen = cexplorer.explore(screen, translate('animated-background-choose'), video or None, extras,
                                   kinds=cexplorer.VIDEOS)
        if chosen is None:
            return
        if chosen == 'none':
            save(screen, animated_background='', animated_scene='none', animated_effect='none')
            return
        if chosen == 'effect':
            effect_screen(screen, keys)
        elif chosen == 'scenes':
            picked = cexplorer.explore(screen, translate('animated-background-scenes'), None,
                                       [(name, translate(f'animated-scene-{name}'), None,
                                         (lambda name_: lambda screen_, box: ScenePreview(screen_, box, name_))(name))
                                        for name in ceffects.SCENES if name != 'none'], places_shown=False,
                                       subtitle=translate('animated-background-scenes-hint'))
            if picked:
                save(screen, animated_scene=picked, animated_background='')
                return
        elif chosen == 'rate':
            choices = ['auto'] + (['30', '20', '10'] if screen.bganim.machine['memory'] else []) + ['still']
            picked = screen.dropdown(screen.res['x'] * 6 / 16, 3 * screen.res_y_16,
                                     [[choice, cmenueditor.rate_text(screen, choice)] for choice in choices], navigate=rate)
            if picked != 'escape':
                save(screen, animated_background_rate=picked)
        else:
            screen.message([translate('animated-background-copying')], 0, None, 'middle', 'big')
            kept = cbganim.keep_source(chosen, screen.logs)
            if kept is None:
                screen.message([translate('editor-import-failed')], 2500, 'menu-ko', 'middle', 'big')
                continue
            save(screen, animated_background=kept, animated_scene='none')
            return


def effect_screen(screen, keys):
    '''
    The drawn effect : its kind (none included), colour, amount, speed on the left, what it gives
    on the right, live ; left / right (the knob, the buttons) change the value of the line,
    Valider opens its list ; Enregistrer keeps it, Retour leaves it as it was
    '''
    # pylint: disable=import-outside-toplevel
    from include.cscreen import DOWN_KEYS, LEFT_KEYS, RIGHT_KEYS, UP_KEYS
    translate = screen.lang.translate
    work = list(settings_of(screen))
    rows = len(EFFECT_KEYS)
    selected = 0
    unit_x, unit_y = screen.res['x'] / 16, screen.res['y'] / 16
    box = pygame.Rect(int(8.6 * unit_x), int(2.6 * unit_y), int(6.6 * unit_x), int(8.6 * unit_y))
    preview = EffectPreview(screen, box.inflate(-int(unit_x / 3), -int(unit_y / 3)), tuple(work))
    screen.idle_hook = preview.tick
    try:
        while True:
            zones = draw_effect_screen(screen, work, selected, box)
            preview.set(tuple(work))
            key = screen.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'enter', 'space', 'single-click', 'PLAYERBUTTON',
                                                              'BACKUPBUTTON', 'GAMEBUTTON'])
            clicked = screen.is_clicked(zones, key)
            if clicked is not False and clicked is not None:
                selected, key = clicked, 'enter'
            if key in keys['escape']:
                return
            if key in DOWN_KEYS:
                selected = (selected + 1) % (rows + 2)
            elif key in UP_KEYS:
                selected = (selected - 1) % (rows + 2)
            elif (key in LEFT_KEYS or key in RIGHT_KEYS) and selected < rows:
                _name, _key, choices, _prefix, _default = EFFECT_KEYS[selected]
                position = choices.index(work[selected]) if work[selected] in choices else 0
                work[selected] = choices[(position + (1 if key in RIGHT_KEYS else -1)) % len(choices)]
            elif (key in LEFT_KEYS or key in RIGHT_KEYS) and selected >= rows:
                selected = rows + 1 if selected == rows else rows
            elif key in keys['enter'] + ['space']:
                if selected == rows:
                    return
                if selected == rows + 1:
                    save(screen, **{key_: work[index] for index, (_n, key_, _c, _p, _d) in enumerate(EFFECT_KEYS)})
                    return
                _name, _key, choices, prefix, _default = EFFECT_KEYS[selected]
                picked = screen.dropdown(unit_x, 3 * screen.res_y_16, [[choice, translate(prefix + choice)] for choice in choices],
                                         navigate=work[selected])
                if picked != 'escape':
                    work[selected] = picked
    finally:
        screen.idle_hook = None


def draw_effect_screen(screen, work, selected, box):
    translate = screen.lang.translate
    colorset = screen.colorset
    unit_x, unit_y = screen.res['x'] / 16, screen.res['y'] / 16
    screen.display_background()
    screen.menu_header(translate('animated-background-effect'))
    zones = {}
    for index, (name, _key, _choices, prefix, _default) in enumerate(EFFECT_KEYS):
        rect = pygame.Rect(int(unit_x), int(2.8 * unit_y + index * 1.5 * unit_y), int(7 * unit_x), int(1.2 * unit_y))
        chosen = index == selected
        screen.new_blit_rect2(rect, colorset['menu-selected'] if chosen else colorset['menu-buttons'], corners='All',
                              border_radius=int(rect.height / 4))
        color = colorset['menu-text-white'] if chosen else colorset['menu-text-black']
        label = pygame.Rect(rect.x, rect.y, int(rect.width * 0.5), rect.height)
        screen.blit_text(translate(f'animated-background-{name}'), label.x, label.y, label.width, label.height, color)
        value = pygame.Rect(label.right, rect.y, rect.width - label.width, rect.height)
        arrows = '< ' if chosen else ''
        screen.blit_text(f"{arrows}{translate(prefix + work[index])}{' >' if chosen else ''}", value.x, value.y,
                         value.width - int(unit_x / 4), value.height, color)
        zones[index] = tuple(rect)
    hint = pygame.Rect(int(unit_x), int(2.8 * unit_y + len(EFFECT_KEYS) * 1.5 * unit_y), int(7 * unit_x), int(1.6 * unit_y))
    from include import cmenueditor    # pylint: disable=import-outside-toplevel
    cmenueditor.paragraph(screen, translate('animated-effect-hint'), hint, colorset['menu-text-white'])
    screen.new_blit_rect2(box, colorset['menu-buttons'], corners='All', border_radius=int(unit_y / 4))
    rows = len(EFFECT_KEYS)
    zones[rows] = screen.display_button(selected == rows, 'back', special='escape')
    zones[rows + 1] = screen.display_button(selected == rows + 1, 'save', special='return')
    screen.update_screen()
    return zones
