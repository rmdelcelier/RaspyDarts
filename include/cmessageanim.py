"""
Animated messages (Screen.message) : the strip of a message and its text arrive with an effect
(Personnalisation du jeu > Jeu : Animation des messages).

- The time of an effect is on the clock : the same on a Pi 3 and on a PC. It is taken from the
  time the message stays, the message staying at least HOLD once arrived.
- The screen of a Pi 3 (X11 and its compositor, without acceleration, in 1920 x 1080) shows 30
  frames a second at most, 4 to 7 of an effect of 0.3 s in a game (measured on /dev/fb0) : the
  effects last 0.5 to 0.75 s, and no more frames are drawn than the screen shows (FPS).
- A frame costs little : the strip once opened is drawn once (the background with the strip
  kept), only the place of the text that moves is sent to the screen, a big text that grows or
  turns is scaled from a copy of half its size while it moves (the message once arrived is drawn
  by Screen.message, sharp).
- The strip and the colours are those of the theme (message-bg, message-text, its size and its
  place) : the message once arrived is exactly the one of before.

The first animated messages were written by Dimitri (his cscreen.py of 21/11/2026) : his effects
taken again here, with the strip and the colours of the theme kept.
"""

import math
import random
import time

import pygame

PYGAME2 = pygame.version.vernum[0] >= 2

NONE, RANDOM = 'none', 'random'
# Effect : its time (ms)
EFFECTS = {
    'fade': 500,      # the strip and the text appear
    'slide': 600,     # the strip unrolls from the left, the text comes from the right
    'pop': 600,       # the strip opens, the text grows past its size and comes back
    'drop': 750,      # the strip opens, the text falls and bounces on it
    'stamp': 550,     # the text hits the strip like a stamp : flash and shake
    'wipe': 600,      # the strip and the text revealed from left to right, a light at the edge
    'twist': 700,     # the strip opens from its middle, the text turns and grows
    'shatter': 750,   # the pieces of the text come from everywhere
    'spin': 1000,     # each letter spins on itself (vertical axis), they stop from left to right
}
CHOICES = (NONE, RANDOM) + tuple(EFFECTS)
# The message stays at least this time once arrived (ms)
HOLD = 250
# The strip of an animated message : 3 times as high as the one of before, half the screen at most
SCALE, SCALE_MAX = 3, 0.5
# Room drawn again above and below the strip (part of its height) : what the text of the effect
# may cover
ROOM = {'fade': (0, 0), 'slide': (0, 0), 'wipe': (0, 0), 'pop': (0.15, 0.15), 'stamp': (0.4, 0.4),
        'twist': (0.3, 0.3), 'drop': (1.0, 0.1), 'shatter': (0.35, 0.35), 'spin': (0, 0)}
# A text bigger than this (pixels) scaled from its half while it moves
BIG_TEXT = 150000


# Frames drawn a second at most (the game drawing straight on the screen : picom
# --unredir-if-possible ; with the compositor, 30 at most are shown on a Pi 3)
FPS = 60


def out_cubic(p):
    return 1 - (1 - p) ** 3


def out_back(p, overshoot=1.7):
    q = p - 1
    return 1 + (overshoot + 1) * q ** 3 + overshoot * q ** 2


def out_bounce(p):
    if p < 1 / 2.75:
        return 7.5625 * p * p
    if p < 2 / 2.75:
        p -= 1.5 / 2.75
        return 7.5625 * p * p + 0.75
    if p < 2.5 / 2.75:
        p -= 2.25 / 2.75
        return 7.5625 * p * p + 0.9375
    p -= 2.625 / 2.75
    return 7.5625 * p * p + 0.984375


def clamp(value):
    return max(0.0, min(1.0, value))


LAST = [None]


def choose(value):
    '''
    The effect of a message for the setting (none, random, an effect) ; None : no effect.
    Random : never twice the same in a row
    '''
    value = str(value or NONE)
    if not PYGAME2 or value == NONE:
        return None
    if value == RANDOM:
        value = random.choice([effect for effect in EFFECTS if effect != LAST[0]])
    if value not in EFFECTS:
        return None
    LAST[0] = value
    return value


class Message:
    '''
    The arrival of a message. owner : the Screen ; rect : its strip ; band : the strip drawn
    (None : no strip in the theme) ; text, place : the text rendered and where it goes
    '''
    def __init__(self, owner, effect, rect, band, text, place, text_color, letters=None):
        self.owner = owner
        self.effect = effect
        self.rect = pygame.Rect(rect)
        self.band = band.copy() if band is not None else None
        self.text = text.copy() if text is not None else None
        self.place = place
        self.text_color = tuple(text_color[:3])
        screen = owner.screen
        above, below = ROOM[effect]
        self.area = pygame.Rect(self.rect.x, self.rect.y - int(self.rect.height * above), self.rect.width,
                                int(self.rect.height * (1 + above + below))).clip(screen.get_rect())
        self.under = screen.subsurface(self.area).copy()
        # The background with the strip open : drawn once
        self.with_band = self.under.copy()
        if self.band is not None:
            self.with_band.blit(self.band, (self.rect.x - self.area.x, self.rect.y - self.area.y))
        # A big text : its half, scaled while it moves
        self.small = None
        if self.text is not None and self.text.get_width() * self.text.get_height() > BIG_TEXT:
            width, height = self.text.get_size()
            self.small = pygame.transform.smoothscale(self.text, (max(1, width // 2), max(1, height // 2)))
        self.frames = 0
        self.sent = 0.0    # time to send the frames to the screen (s)
        self.full = True   # the whole place changed in this frame (else : the rectangles drawn)
        self.drawn = []
        self.before = []
        self.opened = None    # the part of the strip open at the frame before (strip coordinates)
        self.front = None     # where the wipe was at the frame before
        self.kept = False     # the frame before : the background with the strip kept
        # The letters of spin : each one rendered, its place, when it stops
        self.letters = []
        if effect == 'spin' and letters is not None:
            font_path, size, shown, outline = letters
            font = owner.font(font_path, size)
            chars = [(index, char) for index, char in enumerate(shown) if not char.isspace()]
            for order, (index, char) in enumerate(chars):
                surface = owner.letter_surface(font_path, size, char, self.text_color, outline)
                back = pygame.transform.flip(surface, True, False)
                back.fill((90, 90, 90), special_flags=pygame.BLEND_RGB_SUB)
                left = font.size(shown[:index])[0]
                stop = 0.45 + 0.5 * order / max(1, len(chars) - 1)
                turns = 2 + order % 2
                self.letters.append((surface, back, left, stop, turns))
        # The pieces of shatter : where each one comes from, when it leaves
        rnd = random.Random(self.rect.y + len(str(place)))
        self.pieces = []
        if self.text is not None and effect == 'shatter':
            width, height = self.text.get_size()
            cols, rows = 12, 2
            for row in range(rows):
                for col in range(cols):
                    x0, x1 = width * col // cols, width * (col + 1) // cols
                    y0, y1 = height * row // rows, height * (row + 1) // rows
                    if x1 > x0 and y1 > y0:
                        part = pygame.Rect(x0, y0, x1 - x0, y1 - y0)
                        self.pieces.append((part, self.text.subsurface(part).copy(),
                                            rnd.uniform(-0.6, 0.6) * owner.res['x'],
                                            rnd.uniform(-0.8, 0.8) * self.rect.height,
                                            rnd.uniform(0, 0.35)))

    def restore(self, band=False):
        '''
        The background under the message, with the strip open (band) or without it
        '''
        if band and self.band is None:
            band = False
        if band and not self.kept:
            # The strip just open (or no more fading) : sent whole once
            self.full = True
        self.kept = band
        self.owner.screen.blit(self.with_band if band else self.under, self.area.topleft)
        return band

    def put(self, surface, pos, alpha=1.0, area=None):
        if surface is None or alpha <= 0:
            return
        surface.set_alpha(int(255 * clamp(alpha)))
        pos = (int(pos[0]), int(pos[1]))
        self.owner.blit(surface, pos, area)
        size = area.size if area is not None else surface.get_size()
        self.drawn.append(pygame.Rect(pos, size))

    def put_scaled(self, scale, alpha=1.0, angle=0.0, offset=(0, 0)):
        '''
        The text at this scale (around its middle), turned, moved
        '''
        if self.text is None or scale <= 0.01:
            return
        width, height = self.text.get_size()
        source = self.small if self.small is not None else self.text
        center_x = self.place[0] + width / 2 + offset[0]
        center_y = self.place[1] + height / 2 + offset[1]
        size = (max(1, int(width * scale)), max(1, int(height * scale)))
        if angle:
            # Scaled then turned, not smoothed : 3 times faster than rotozoom on a Pi 3
            surface = pygame.transform.rotate(pygame.transform.scale(source, size), angle)
        elif abs(scale - 1) < 0.01:
            surface = self.text
        else:
            dest = pygame.Rect(int(center_x - size[0] / 2), int(center_y - size[1] / 2), size[0], size[1])
            shown = dest.clip(self.area)
            if shown.width <= 0 or shown.height <= 0:
                return
            if shown != dest:
                # Bigger than the place (stamp) : only what is seen is scaled
                ratio = source.get_width() / dest.width
                part = pygame.Rect(int((shown.x - dest.x) * ratio), int((shown.y - dest.y) * ratio),
                                   max(1, int(shown.width * ratio)), max(1, int(shown.height * ratio))).clip(source.get_rect())
                self.put(pygame.transform.scale(source.subsurface(part), shown.size), shown.topleft, alpha)
                return
            if self.small is not None or scale > 1.25:
                surface = pygame.transform.scale(source, size)
            else:
                surface = pygame.transform.smoothscale(source, size)
        self.put(surface, (center_x - surface.get_width() / 2, center_y - surface.get_height() / 2), alpha)

    def band_open(self, opened, vertical=True, alpha=1.0, offset=(0, 0)):
        '''
        The strip opened from its middle (vertical : in height, else in width). Sent to the
        screen : what opened since the frame before (all of it if it fades or moves)
        '''
        if self.band is None:
            # No strip (Fond des messages : Aucun, Contour) : only the text
            return
        if opened <= 0:
            self.full = True
            return
        width, height = self.band.get_size()
        if vertical:
            shown = max(1, int(height * opened))
            area = pygame.Rect(0, (height - shown) // 2, width, shown)
        else:
            shown = max(1, int(width * opened))
            area = pygame.Rect((width - shown) // 2, 0, shown, height)
        self.put(self.band, (self.rect.x + area.x + offset[0], self.rect.y + area.y + offset[1]), alpha, area)
        self.drawn.pop()
        if alpha < 1 or offset != (0, 0) or self.opened is None:
            self.full = True
        else:
            self.strips(self.opened, area)
        self.opened = area

    def strips(self, before, now):
        '''
        The strip shown grew from before to now (strip coordinates) : the parts that appeared,
        to send to the screen
        '''
        for part in (pygame.Rect(now.x, now.y, now.width, before.y - now.y),
                     pygame.Rect(now.x, before.bottom, now.width, now.bottom - before.bottom),
                     pygame.Rect(now.x, now.y, before.x - now.x, now.height),
                     pygame.Rect(before.right, now.y, now.right - before.right, now.height)):
            if part.width > 0 and part.height > 0:
                self.drawn.append(part.move(self.rect.x, self.rect.y))

    def opening(self, opened, vertical=True):
        '''
        The background, then the strip opening ; once open : the background with the strip kept
        (only the text changes)
        '''
        if opened >= 1:
            self.restore(band=True)
        else:
            self.restore()
            self.band_open(opened, vertical)

    def message_whole(self):
        '''
        The message arrived over its background (opaque, the place of the message) : made once
        '''
        if getattr(self, 'whole', None) is None:
            self.whole = self.with_band.copy()
            if self.text is not None:
                self.whole.blit(self.text, (self.place[0] - self.area.x, self.place[1] - self.area.y))
        return self.whole

    def step(self, p):
        '''
        The message at p (0 : nothing yet, 1 : arrived)
        '''
        effect, rect = self.effect, self.rect
        tx, ty = self.place
        if effect == 'fade':
            # The message whole (background, strip, text : opaque) faded in, in one blit
            self.restore()
            self.full = True
            whole = self.message_whole()
            whole.set_alpha(int(255 * out_cubic(p)))
            self.owner.blit(whole, self.area.topleft)
        elif effect == 'slide':
            unrolled = out_cubic(clamp(p * 1.5))
            if unrolled >= 1:
                self.restore(band=True)
            else:
                self.restore()
                if self.band is None:
                    self.full = True
                else:
                    shown = pygame.Rect(0, 0, max(1, int(rect.width * unrolled)), rect.height)
                    self.put(self.band, rect.topleft, 1, shown)
                    self.drawn.pop()
                    if self.opened is None:
                        self.full = True
                    else:
                        self.strips(self.opened, shown)
                    self.opened = shown
            start = self.owner.res['x'] - tx
            self.put(self.text, (tx + (1 - out_back(p, 1.2)) * start, ty), clamp(p * 3))
        elif effect == 'pop':
            self.opening(out_cubic(clamp(p * 1.8)))
            self.put_scaled(0.15 + 0.85 * out_back(clamp((p - 0.1) / 0.9), 2.2), clamp(p * 3))
        elif effect == 'drop':
            self.opening(out_cubic(clamp(p * 2)))
            height = self.text.get_height() if self.text is not None else 0
            fall = ty + height - self.area.y
            self.put(self.text, (tx, ty - (1 - out_bounce(p)) * fall), 1)
        elif effect == 'stamp':
            impact = 0.45
            if p < impact:
                q = p / impact
                self.restore()
                self.put_scaled(2.6 - 1.6 * q * q, clamp(q * 2.5))
            else:
                q = (p - impact) / (1 - impact)
                shake = int(math.sin(q * math.pi * 4) * (1 - q) * rect.height * 0.07)
                # The strip and its text shaken in one piece (the message whole, opaque)
                self.restore()
                self.full = True
                whole = self.message_whole()
                whole.set_alpha(None)
                strip = pygame.Rect(rect.x - self.area.x, rect.y - self.area.y, rect.width, rect.height)
                self.owner.screen.blit(whole, (rect.x, rect.y + shake), strip)
                flash = int(150 * (1 - q / 0.4)) if q < 0.4 else 0
                if flash > 0:
                    self.owner.screen.fill((flash, flash, flash), rect.move(0, shake), special_flags=pygame.BLEND_RGB_ADD)
        elif effect == 'wipe':
            front = int(rect.width * out_cubic(p))
            screen = self.owner.screen
            self.restore()
            screen.set_clip(pygame.Rect(rect.x, self.area.y, front, self.area.height).clip(self.area))
            if self.band is not None:
                self.owner.blit(self.band, rect.topleft)
            self.put(self.text, (tx, ty), 1)
            self.drawn.pop()
            screen.set_clip(self.area)
            light = max(3, rect.height // 25)
            # Sent : from where the light was to where it is (the light and its glow)
            before = front if self.front is None else self.front
            self.drawn.append(pygame.Rect(rect.x + before - light * 4, self.area.y, front - before + light * 8, self.area.height))
            if self.front is None:
                self.full = True
            self.front = front
            glow = pygame.Rect(rect.x + front - light, rect.y, light * 2, rect.height)
            screen.fill(self.text_color, glow)
            screen.fill((60, 60, 60), glow.inflate(light * 4, 0), special_flags=pygame.BLEND_RGB_ADD)
        elif effect == 'twist':
            self.opening(out_cubic(clamp(p * 1.6)), False)
            eased = out_cubic(p)
            self.put_scaled(0.2 + 0.8 * out_back(p, 1.4), clamp(p * 2.5), angle=(1 - eased) * 25)
        elif effect == 'spin':
            self.opening(out_cubic(clamp(p * 3)))
            if not self.letters:
                self.put(self.text, (tx, ty), clamp(p * 2))
            for surface, back, left, stop, turns in self.letters:
                q = clamp(p / stop)
                # The turns left, slowing down to stop facing (out_cubic)
                angle = (1 - out_cubic(q)) * turns * 2 * math.pi
                width, height = surface.get_size()
                shown = abs(math.cos(angle))
                face = back if math.cos(angle) < 0 else surface
                if shown > 0.98:
                    letter = face
                else:
                    letter = pygame.transform.scale(face, (max(1, int(width * shown)), height))
                self.put(letter, (tx + left + (width - letter.get_width()) / 2, ty), 1)
        elif effect == 'shatter':
            shown = out_cubic(clamp(p * 1.5))
            if shown >= 1:
                self.restore(band=True)
            else:
                self.restore()
                self.band_open(1, alpha=shown)
            for part, piece, from_x, from_y, delay in self.pieces:
                q = out_cubic(clamp((p - delay) / (1 - delay)))
                if q <= 0:
                    continue
                self.put(piece, (tx + part.x + (1 - q) * from_x, ty + part.y + (1 - q) * from_y), q)

    def changed(self):
        '''
        What to send to the screen for this frame : the whole place, or where the text was and is
        '''
        drawn, before = self.drawn, self.before
        self.before, self.drawn = drawn, []
        full, self.full = self.full, False
        if full or not drawn and not before:
            return self.area
        changed = drawn[0].unionall(drawn[1:] + before)
        return changed.clip(self.area) if changed.colliderect(self.area) else self.area

    def play(self):
        '''
        The arrival, on the clock ; the screen left with the message not drawn (drawn by
        Screen.message as before)
        '''
        screen = self.owner.screen
        duration = EFFECTS[self.effect] / 1000
        clip = screen.get_clip()
        begun = time.perf_counter()
        # The screen under the message (its background drawn again) shown first, out of the
        # time of the effect (the whole screen sent : a long frame on a Pi 3)
        self.restore()
        self.owner.update_screen()
        started = time.perf_counter()
        try:
            while True:
                p = (time.perf_counter() - started) / duration
                if p >= 1:
                    break
                screen.set_clip(self.area)
                self.step(max(p, 0.02))
                screen.set_clip(clip)
                sending = time.perf_counter()
                self.owner.update_screen(rect_array=[self.changed()])
                self.sent += time.perf_counter() - sending
                self.frames += 1
                # No more frames than the screen shows
                wait = started + self.frames / FPS - time.perf_counter()
                if wait > 0:
                    time.sleep(wait)
        finally:
            screen.set_clip(clip)
            self.restore()
        return time.perf_counter() - begun
