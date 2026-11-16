"""
Captures of the screen for a theme sent to RaspyHub (include/cthemehub.py).

- grab(screen) : the screen as it is shown, without what is drawn over it (the activity
  indicator, the frame of the mode capture), the animated background included.
- The pages of the menus drawn by the game itself (generate) : each page shown by its own code,
  the inputs given by the game (Craspberry.scripted) : a capture, then the page left.
- The mode capture (CaptureMode) : the player goes everywhere (menus, games) ; F1 or Print Screen
  takes the screen, Escape or Valider held ends it (Craspberry, Gpio_Extender). A frame
  yellow-orange, a camera and a band recall it : drawn over the screen sent, never captured.
"""

import array
import math
import os
import time

import pygame

# Captures : JPEG of this size at most (the pages of RaspyHub, the screens of the bornes)
SIZE = (1280, 720)
QUALITY = 85
# The mode capture : captures a session, its colours
MOST = 6
FRAME = (255, 160, 0)
BAND = (20, 20, 20, 215)


def grab(screen):
    '''
    The screen shown, as a surface : with the animated background, without the indicator of
    activity nor the frame of the mode capture
    '''
    animated = getattr(screen, 'bganim', None)
    if animated is not None and animated.mode == 'layer' and screen.screen is animated.layer:
        # The screen made again from the video, the effect and the menu : nothing over it
        animated.compose()
        picture = animated.real.copy()
        screen.update_screen()
        return picture
    # The screen keeps no trace of what is drawn over it (see Screen.update_screen)
    return screen.screen.copy()


def save(surface, path):
    '''
    A capture written in JPEG (SIZE at most, its proportions kept) : True if written
    '''
    from PIL import Image    # pylint: disable=import-outside-toplevel
    width, height = surface.get_size()
    picture = Image.frombytes('RGB', (width, height), pygame.image.tostring(surface, 'RGB'))
    scale = min(1.0, SIZE[0] / width, SIZE[1] / height)
    if scale < 1.0:
        picture = picture.resize((max(1, int(width * scale)), max(1, int(height * scale))), Image.LANCZOS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    partial = path + '.part'
    picture.save(partial, 'JPEG', quality=QUALITY, optimize=True)
    os.replace(partial, path)
    return True


# ---------------------------------------------------------------------- pages of the menus
# The pages captured by the game : (name, how it is drawn) ; the first three are asked by RaspyHub
PAGES = (('main', 'menu'), ('miscellaneous', 'menu'), ('games-classic', 'games'),
         ('settings', 'menu'), ('categories', 'menu'), ('games-fun', 'games'), ('games-sport', 'games'))
MANDATORY = ('main', 'miscellaneous', 'games-classic')


def page_items(screen, name):
    '''
    The buttons of a page of the menus, as the game shows them : (shown, everything)
    '''
    menus = screen.menus()
    if name == 'main':
        return screen.main_menu_items(), [screen.favorite_button(button) for button in menus.buttons('main')]
    everything = menus.buttons(name)
    if name == 'categories':
        everything = [button for button in everything if button.get('requires') != 'favorite_games']
    return [button for button in everything if button.get('visible', True) is not False], everything


def generate(screen, folder, logs, progress=None):
    '''
    Each page of PAGES drawn by its own code, captured in folder (auto-<name>.jpg) : the names
    of the pages written
    '''
    rpi = screen.rpi
    written = []
    # Not the addresses of the borne on the pages (Screen.menu_of_files)
    screen.capturing = True
    try:
        for index, (name, kind) in enumerate(PAGES):
            if progress is not None:
                progress(index, len(PAGES))
            written += page(screen, rpi, name, kind, folder, logs)
    finally:
        screen.capturing = False
    logs.info(f"Captures of the pages : {', '.join(written) or 'none'}")
    return written


def page(screen, rpi, name, kind, folder, logs):
    '''
    A page drawn by its own code (its first button selected) and captured : [name], [] : not
    captured
    '''
    path = os.path.join(folder, f'auto-{name}.jpg')
    done = []

    def take(path=path, done=done):
        try:
            save(grab(screen), path)
            done.append(True)
        except Exception as error:    # pylint: disable=broad-except
            logs.error(f"Capture {path} not written ({error})")
            done.append(False)

    try:
        if kind == 'games':
            category = name.split('-', 1)[1]
            # Drawn, captured, then left (Retour)
            rpi.scripted = [take, 'escape']
            screen.game_menu(category, screen.get_games_list(category), [], 2)
        else:
            items, everything = page_items(screen, name)
            menus = screen.menus()
            first = menus.button_id(items[0]) if items else None
            # Drawn, captured, then an input it does not know : at its next turn, the page left
            rpi.scripted = [take, '__capture__']
            screen.run_menu(name, items, everything, initial=first,
                            hook=lambda done=done: {'action': '__capture__'} if done else None)
    except Exception as error:    # pylint: disable=broad-except
        logs.error(f"Capture of the page {name} : {error}")
    finally:
        rpi.scripted = []
    return [name] if done and done[0] else []


# ---------------------------------------------------------------------- mode capture
def shutter_sound():
    '''
    The click of a camera, made here (no file) : a short noise, twice
    '''
    try:
        if not pygame.mixer.get_init():
            return None
        rate, _size, channels = pygame.mixer.get_init()
        samples = array.array('h')
        seed = 12345
        for part, (start, length) in enumerate(((0.0, 0.025), (0.06, 0.035))):
            for index in range(int(rate * length)):
                seed = (seed * 1103515245 + 12345) & 0x7fffffff
                fade = math.exp(-index / (rate * 0.008))
                value = int(((seed >> 8) % 20000 - 10000) * fade * (1.0 if part else 0.7))
                for _channel in range(channels):
                    samples.append(value)
            if part == 0:
                for _index in range(int(rate * 0.035) * channels):
                    samples.append(0)
        return pygame.mixer.Sound(buffer=samples.tobytes())
    except Exception:    # pylint: disable=broad-except
        return None


class CaptureMode:
    '''
    The mode capture : the screen captured with F1 / Print Screen (MOST at most), ended with
    Escape or Valider held ; its frame drawn over the screen sent (over / restore). on_end :
    called when it ends, with the captures taken
    '''

    def __init__(self, screen, folder, on_end=None, most=MOST):
        self.screen = screen
        self.folder = folder
        self.on_end = on_end
        self.most = most
        self.taken = []
        self.active = True
        self.under = []
        self.sound = shutter_sound()
        rpi = screen.rpi
        rpi.capture = self
        gpio = getattr(rpi, 'gpio', None)
        if gpio is not None and hasattr(gpio, 'hold_validate'):
            gpio.hold_validate = True
        screen.logs.info(f"Mode capture started ({folder})")
        screen.update_screen()

    # ------------------------------------------------------------------ drawn over the screen
    def parts(self, size):
        '''
        Its parts on a screen of this size : the frame (4 bands), the camera, the band of help
        '''
        width, height = size
        thick = max(6, height // 110)
        frame = [pygame.Rect(0, 0, width, thick), pygame.Rect(0, height - thick, width, thick),
                 pygame.Rect(0, 0, thick, height), pygame.Rect(width - thick, 0, thick, height)]
        badge = pygame.Rect(thick * 2, thick * 2, int(height * 0.16), int(height * 0.075))
        band_height = int(height * 0.055)
        # As wide as its text (the buttons at the bottom of the screens stay visible)
        from include import cfonts    # pylint: disable=import-outside-toplevel
        text_width = cfonts.font(max(8, int(band_height * 0.75 * 0.8))).size(self.screen.lang.translate('hub-capture-help'))[0]
        band_width = min(width - 2 * thick, text_width + 2 * band_height)
        band = pygame.Rect((width - band_width) // 2, height - thick - band_height, band_width, band_height)
        return frame, badge, band

    def draw_camera(self, surface, rect):
        '''
        A camera on the left of rect
        '''
        side = rect.height
        body = pygame.Rect(rect.x + side * 0.12, rect.y + side * 0.3, side * 0.9, side * 0.58)
        pygame.draw.rect(surface, FRAME, (body.x + body.w * 0.18, body.y - side * 0.14, body.w * 0.32, side * 0.16),
                         border_radius=max(1, int(side * 0.04)))
        pygame.draw.rect(surface, FRAME, body, border_radius=max(2, int(side * 0.1)))
        pygame.draw.circle(surface, (20, 20, 20), body.center, int(body.h * 0.36))
        pygame.draw.circle(surface, FRAME, body.center, int(body.h * 0.24))

    def draw(self, surface):
        '''
        Its frame, its camera and its band over surface : the places drawn
        '''
        frame, badge, band = self.parts(surface.get_size())
        for rect in frame:
            surface.fill(FRAME, rect)
        back = pygame.Surface(badge.size, pygame.SRCALPHA)
        pygame.draw.rect(back, BAND, back.get_rect(), border_radius=badge.height // 4)
        surface.blit(back, badge)
        pygame.draw.rect(surface, FRAME, badge, 2, border_radius=badge.height // 4)
        self.draw_camera(surface, badge.inflate(-badge.height * 0.15, -badge.height * 0.15))
        back = pygame.Surface(band.size, pygame.SRCALPHA)
        back.fill(BAND)
        surface.blit(back, band)
        help_text = self.screen.lang.translate('hub-capture-help')
        self.text(surface, help_text, band.inflate(-band.height, -band.height * 0.25), (255, 255, 255))
        self.text(surface, f"{len(self.taken)} / {self.most}",
                  pygame.Rect(badge.x + badge.height * 1.05, badge.y, badge.width - badge.height * 1.15, badge.height), FRAME)
        return frame + [badge, band]

    def text(self, surface, text, rect, color):
        '''
        A line in rect, as big as it can be (the font of the game)
        '''
        from include import cfonts    # pylint: disable=import-outside-toplevel
        font = cfonts.font(max(8, int(rect.height * 0.8)))
        picture = font.render(str(text), True, color)
        if picture.get_width() > rect.width:
            picture = pygame.transform.smoothscale(picture, (rect.width, max(1, int(picture.get_height() * rect.width
                                                                                     / picture.get_width()))))
        surface.blit(picture, picture.get_rect(center=rect.center))

    def over(self, surface):
        '''
        Drawn over a screen about to be sent, what was under kept (restore) : its places
        '''
        if not self.active:
            return []
        frame, badge, band = self.parts(surface.get_size())
        self.under = [(rect, surface.subsurface(rect.clip(surface.get_rect())).copy()) for rect in frame + [badge, band]]
        return self.draw(surface)

    def restore(self, surface):
        '''
        What was under it back in the screen (the screen keeps no trace of it)
        '''
        for rect, picture in reversed(self.under):
            surface.blit(picture, rect.topleft)
        self.under = []

    # ------------------------------------------------------------------ keys
    def shot(self):
        '''
        F1 / Print Screen : the screen captured (without the frame), a flash and a click
        '''
        if not self.active:
            return
        screen = self.screen
        try:
            path = os.path.join(self.folder, f"free-{time.strftime('%Y%m%d-%H%M%S')}-{len(self.taken) + 1}.jpg")
            save(grab(screen), path)
            self.taken.append(os.path.basename(path))
            screen.logs.info(f"Mode capture : {path}")
        except Exception as error:    # pylint: disable=broad-except
            screen.logs.error(f"Mode capture : not written ({error})")
            screen.message([screen.lang.translate('hub-capture-failed')], 2000, 'menu-ko', 'middle', 'big')
            screen.update_screen()
            return
        if self.sound is not None:
            try:
                self.sound.set_volume(min(1.0, int(screen.sound_volume) / 100))
                self.sound.play()
            except Exception:    # pylint: disable=broad-except
                pass
        self.flash()
        if len(self.taken) >= self.most:
            self.finish()

    def flash(self):
        '''
        A short white flash over the screen, then the screen as it was
        '''
        screen = self.screen
        animated = getattr(screen, 'bganim', None)
        target = animated.real if animated is not None and animated.mode == 'layer' and screen.screen is animated.layer \
            else pygame.display.get_surface()
        if target is None:
            return
        saved = target.copy()
        white = pygame.Surface(target.get_size())
        white.fill((255, 255, 255))
        white.set_alpha(170)
        target.blit(white, (0, 0))
        pygame.display.update()
        pygame.time.wait(90)
        target.blit(saved, (0, 0))
        screen.update_screen()

    def finish(self):
        '''
        Escape, Valider held, the last capture : the mode ended, the screen without its frame
        '''
        if not self.active:
            return
        self.active = False
        screen = self.screen
        rpi = screen.rpi
        if rpi.capture is self:
            rpi.capture = None
        gpio = getattr(rpi, 'gpio', None)
        if gpio is not None and hasattr(gpio, 'hold_validate'):
            gpio.hold_validate = False
        screen.logs.info(f"Mode capture ended : {len(self.taken)} capture(s)")
        screen.update_screen()
        if self.on_end is not None:
            self.on_end(self.taken)
