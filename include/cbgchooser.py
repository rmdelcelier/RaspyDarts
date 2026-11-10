"""
Modifier les écrans > Fond animé : the type of animated background first (none, drawn effect,
animated background drawn, both, video or animated GIF), then only its settings, what it gives
played on the right (live, while a list is gone through too) ; Sauvegarder keeps it, Retour
leaves it as it was. The video is chosen in the explorer (include/cexplorer.py), played in its
preview.
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
    A drawn effect over the background of the menus, or over the animated background chosen
    (what it gives on the screen)
    '''

    def __init__(self, screen, box, settings, scene='none'):
        super().__init__(screen, box)
        self.scene_name = scene
        self.scene = ceffects.make_scene(scene, self.box.size, LOGO, theme_color=screen.colorset.get('menu-selected'))
        self.base = self.scene.background() if self.scene is not None else menu_background(screen, self.box.size)
        self.settings = None
        self.effect = None
        self.set(settings)

    def set(self, settings):
        if settings != self.settings:
            self.settings = settings
            self.still = False
            name, color, amount, speed = settings
            # As big as on the screen (the box is smaller : the particles would be barely seen)
            self.effect = ceffects.make(name, self.box.size, color, amount, speed,
                                        theme_color=self.screen.colorset.get('menu-selected'), scale=0.8)

    def caption(self, translate):
        text = translate(f'animated-effect-{self.settings[0]}')
        if self.scene is not None:
            text = f"{translate('animated-scene-' + self.scene_name)} + {text}"
        return text

    def frame(self, elapsed):
        if self.effect is None and self.scene is None and getattr(self, 'still', False):
            return False
        self.still = self.effect is None
        self.surface.blit(self.base, (0, 0))
        if self.scene is not None:
            self.scene.step(elapsed)
            self.scene.draw(self.surface)
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


TYPES = ('none', 'effect', 'scene', 'scene-effect', 'video')
SCENE_CHOICES = tuple(name for name in ceffects.SCENES if name != 'none')
# The lines shown for each type
TYPE_ROWS = {'none': ('type',),
             'effect': ('type', 'effect', 'effect-color', 'effect-amount', 'effect-speed'),
             'scene': ('type', 'scene'),
             'scene-effect': ('type', 'scene', 'effect', 'effect-color', 'effect-amount', 'effect-speed'),
             'video': ('type', 'video', 'rate')}


def load(screen):
    '''
    The settings of the moment, as the screen shows them : the type, and each value
    '''
    globals_ = screen.config.config['SectionGlobals']
    work = {'video': str(globals_.get('animated_background') or ''),
            'scene': str(globals_.get('animated_scene') or 'none'),
            'rate': str(globals_.get('animated_background_rate') or 'auto')}
    for name, key, _choices, _prefix, default in EFFECT_KEYS:
        work[name] = str(globals_.get(key) or default)
    if work['video']:
        work['type'] = 'video'
    elif work['scene'] != 'none':
        work['type'] = 'scene-effect' if work['effect'] != 'none' else 'scene'
    else:
        work['type'] = 'effect' if work['effect'] != 'none' else 'none'
    if work['scene'] == 'none':
        work['scene'] = SCENE_CHOICES[0]
    if work['effect'] == 'none':
        work['effect'] = 'sparks'
    return work


def save_work(screen, work):
    '''
    The settings written as the type says (what it does not use : none)
    '''
    kind = work['type']
    values = {'animated_background': work['video'] if kind == 'video' else '',
              'animated_scene': work['scene'] if kind in ('scene', 'scene-effect') else 'none',
              'animated_effect': work['effect'] if kind in ('effect', 'scene-effect') else 'none',
              'animated_background_rate': work['rate']}
    for name, key, _choices, _prefix, _default in EFFECT_KEYS[1:]:
        values[key] = work[name]
    save(screen, **values)


def preview_of(screen, box, work):
    '''
    What the screen will show for these settings, played in the box
    '''
    kind = work['type']
    effect = tuple(work[name] for name, *_rest in EFFECT_KEYS)
    if kind == 'video':
        if work['video'] and os.path.isfile(work['video']):
            return cexplorer.VideoPreview(screen, work['video'], box)
        return ScenePreview(screen, box, 'none')
    if kind == 'none':
        return EffectPreview(screen, box, ('none',) + effect[1:], 'none')
    if kind == 'effect':
        return EffectPreview(screen, box, effect, 'none')
    if kind == 'scene':
        return EffectPreview(screen, box, ('none',) + effect[1:], work['scene'])
    return EffectPreview(screen, box, effect, work['scene'])


def preview_key(work):
    return tuple(work[name] for name in ('type', 'video', 'scene', 'effect', 'effect-color', 'effect-amount', 'effect-speed'))


def choose(screen, keys):
    '''
    Modifier les écrans > Fond animé : the type first (none, drawn effect, animated background
    drawn, both, video or animated GIF), then only its settings ; each line with a choice opens
    its list (what it gives seen in the preview while going through it) ; Sauvegarder keeps it,
    Retour leaves it as it was. The wheel of a knob goes from a line to the next
    '''
    # pylint: disable=import-outside-toplevel
    from include import cmenueditor
    from include.cscreen import DOWN_KEYS, LEFT_KEYS, RIGHT_KEYS, UP_KEYS
    translate = screen.lang.translate
    work = load(screen)
    unit_x, unit_y = screen.res['x'] / 16, screen.res['y'] / 16
    box = pygame.Rect(int(8.6 * unit_x), int(2.6 * unit_y), int(6.6 * unit_x), int(8.6 * unit_y))
    inner = box.inflate(-int(unit_x / 3), -int(unit_y / 3))
    state = {'preview': None, 'key': None}

    def show(values):
        # The preview of these settings (made again when they change)
        key = preview_key(values)
        if key == state['key']:
            return
        if state['preview'] is not None:
            state['preview'].stop()
        state['preview'] = preview_of(screen, inner, values)
        state['key'] = key
        screen.idle_hook = state['preview'].tick

    selected = 0
    try:
        while True:
            rows = TYPE_ROWS[work['type']]
            count = len(rows) + 2
            selected = min(selected, count - 1)
            show(work)
            zones = draw_screen(screen, work, rows, selected, box)
            key = screen.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'enter', 'space', 'single-click', 'PLAYERBUTTON',
                                                              'BACKUPBUTTON', 'GAMEBUTTON'])
            clicked = screen.is_clicked(zones, key)
            if clicked is not False and clicked is not None:
                selected, key = clicked, 'enter'
            if key in keys['escape']:
                return
            if key in DOWN_KEYS + RIGHT_KEYS:
                selected = (selected + 1) % count
            elif key in UP_KEYS + LEFT_KEYS:
                selected = (selected - 1) % count
            elif key in keys['enter'] + ['space']:
                if selected == len(rows):
                    return
                if selected == len(rows) + 1:
                    save_work(screen, work)
                    screen.message([translate('animated-background-saved')], 1500, None, 'middle', 'big')
                    return
                name = rows[selected]
                if name == 'video':
                    chosen = cexplorer.explore(screen, translate('animated-background-choose-video'), work['video'] or None,
                                               kinds=cexplorer.VIDEOS)
                    if chosen and os.path.isfile(chosen):
                        screen.message([translate('animated-background-copying')], 0, None, 'middle', 'big')
                        kept = cbganim.keep_source(chosen, screen.logs)
                        if kept is None:
                            screen.message([translate('editor-import-failed')], 2500, 'menu-ko', 'middle', 'big')
                        else:
                            work['video'] = kept
                    state['key'] = None
                    continue
                choices, label = row_choices(screen, name)
                trial = dict(work)

                def preview(value, name=name, trial=trial):
                    # The choice shown in the list : seen at once in the preview
                    trial[name] = value
                    show(trial)
                    return box
                picked = screen.dropdown(unit_x, 3 * unit_y, [[choice, label(choice)] for choice in choices],
                                         navigate=work[name], width=7 * unit_x, preview=preview)
                if picked != 'escape':
                    work[name] = picked
                state['key'] = None
    finally:
        if state['preview'] is not None:
            state['preview'].stop()
        screen.idle_hook = None


def row_choices(screen, name):
    '''
    The choices of a line and how each is said
    '''
    from include import cmenueditor    # pylint: disable=import-outside-toplevel
    translate = screen.lang.translate
    if name == 'type':
        return TYPES, lambda value: translate(f'animated-type-{value}')
    if name == 'scene':
        return SCENE_CHOICES, lambda value: translate(f'animated-scene-{value}')
    if name == 'rate':
        choices = ('auto',) + (('30', '20', '10') if screen.bganim.machine['memory'] else ()) + ('still',)
        return choices, lambda value: cmenueditor.rate_text(screen, value)
    _name, _key, choices, prefix, _default = next(row for row in EFFECT_KEYS if row[0] == name)
    if name == 'effect':
        choices = tuple(choice for choice in choices if choice != 'none')
    return choices, lambda value, prefix=prefix: translate(prefix + value)


def value_text(screen, work, name):
    translate = screen.lang.translate
    if name == 'video':
        return os.path.basename(work['video']) if work['video'] else translate('animated-background-video-none')
    choices, label = row_choices(screen, name)
    return label(work[name])


def draw_screen(screen, work, rows, selected, box):
    '''
    The lines of the type chosen (value in its box, name beside it), the preview, the state of the
    video, Retour and Sauvegarder. The zones to click (the index of each line)
    '''
    from include import cmenueditor    # pylint: disable=import-outside-toplevel
    translate = screen.lang.translate
    colorset = screen.colorset
    unit_x, unit_y = screen.res['x'] / 16, screen.res['y'] / 16
    screen.display_background()
    screen.menu_header(translate('animated-background'), translate('animated-background-hint'))
    zones = {}
    bottom = 0
    for index, name in enumerate(rows):
        rect = pygame.Rect(int(unit_x), int(2.8 * unit_y + index * 1.35 * unit_y), int(7 * unit_x), int(1.1 * unit_y))
        cmenueditor.value_item(screen, rect, translate(f'animated-background-{name}'), value_text(screen, work, name),
                               index == selected)
        zones[index] = tuple(rect)
        bottom = rect.bottom
    if work['type'] == 'video':
        # How the preparation of the video goes
        status = pygame.Rect(int(unit_x), bottom + int(unit_y * 0.4), int(7 * unit_x), int(1.6 * unit_y))
        cmenueditor.paragraph(screen, cmenueditor.animated_status(screen), status, colorset['menu-text-white'])
    help_rect = pygame.Rect(int(unit_x), int(11.4 * unit_y), int(14 * unit_x), int(1.2 * unit_y))
    cmenueditor.paragraph(screen, translate(f'animated-type-help-{work["type"]}'), help_rect, colorset['menu-text-white'])
    screen.new_blit_rect2(box, colorset['menu-buttons'], corners='All', border_radius=int(unit_y / 4))
    zones[len(rows)] = screen.display_button(selected == len(rows), 'back', special='escape')
    zones[len(rows) + 1] = screen.display_button(selected == len(rows) + 1, 'save', special='return')
    screen.update_screen()
    return zones
