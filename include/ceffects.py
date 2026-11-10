"""
Drawn effects of the animated background (include/cbganim.py) : particles drawn over the
background of the menus (an image, the still picture of the video, or the video itself).

Over an image, only the places of the particles are drawn again and sent to the screen (their
place before and after) : measured on a Pi 3 B+, 80 particles at 30 frames a second, 47 % of the
processor with the game (the video : 57 % at 20 frames a second).

step(elapsed) moves them and returns the places changed ; draw(surface) draws them.
"""

import math
import random

import pygame

EFFECTS = ('none', 'sparks', 'snow', 'bubbles', 'fireflies')
COLORS = {'auto': None, 'white': (255, 255, 255), 'red': (235, 50, 40), 'orange': (255, 150, 40),
          'yellow': (255, 225, 70), 'green': (70, 220, 90), 'blue': (70, 150, 255), 'purple': (190, 90, 255),
          'theme': 'theme'}
AMOUNTS = {'few': 40, 'normal': 80, 'many': 150}
SPEEDS = {'slow': 0.5, 'normal': 1.0, 'fast': 1.8}


def make(name, size, color='auto', amount='normal', speed='normal', theme_color=None):
    '''
    The effect of this name for a screen of this size, None : none
    '''
    kinds = {'sparks': Sparks, 'snow': Snow, 'bubbles': Bubbles, 'fireflies': Fireflies}
    kind = kinds.get(str(name))
    if kind is None:
        return None
    chosen = COLORS.get(str(color), None)
    if chosen == 'theme':
        chosen = tuple(theme_color[:3]) if theme_color else None
    return kind(size, chosen, AMOUNTS.get(str(amount), 80), SPEEDS.get(str(speed), 1.0))


class Effect:
    '''
    Particles : [x, y, vx, vy, radius, colour, phase] ; speeds in parts of the height a second
    '''
    PALETTE = ((255, 255, 255),)

    def __init__(self, size, color, amount, speed):
        self.width, self.height = size
        self.color = color
        self.speed = speed
        self.scale = self.height / 1080
        self.particles = [self.new(first=True) for _ in range(amount)]

    def tint(self):
        return self.color if self.color is not None else random.choice(self.PALETTE)

    def new(self, first=False):
        raise NotImplementedError

    def move(self, particle, elapsed):
        particle[0] += particle[2] * elapsed * self.height * self.speed
        particle[1] += particle[3] * elapsed * self.height * self.speed

    def gone(self, particle):
        radius = particle[4]
        return particle[1] < -radius * 2 or particle[1] > self.height + radius * 2 \
            or particle[0] < -radius * 2 or particle[0] > self.width + radius * 2

    @staticmethod
    def place(particle):
        radius = int(particle[4]) + 2
        return pygame.Rect(int(particle[0]) - radius, int(particle[1]) - radius, radius * 2 + 1, radius * 2 + 1)

    def step(self, elapsed):
        '''
        The particles moved (elapsed : seconds) : the places changed (before and after)
        '''
        changed = []
        elapsed = min(elapsed, 0.2)
        for index, particle in enumerate(self.particles):
            before = self.place(particle)
            self.move(particle, elapsed)
            particle[6] += elapsed
            if self.gone(particle):
                self.particles[index] = particle = self.new()
            changed.append(before.union(self.place(particle)))
        return changed

    def shade(self, particle):
        return particle[5]

    def draw(self, surface, clip=None):
        for particle in self.particles:
            if clip is not None and not clip.colliderect(self.place(particle)):
                continue
            self.draw_one(surface, particle)

    def draw_one(self, surface, particle):
        pygame.draw.circle(surface, self.shade(particle), (int(particle[0]), int(particle[1])), max(1, int(particle[4])))


class Sparks(Effect):
    '''
    Sparks rising from the bottom, swaying, dimmer as they rise
    '''
    PALETTE = ((255, 170, 60), (255, 220, 120), (255, 120, 40))

    def new(self, first=False):
        y = random.uniform(0, self.height) if first else self.height + 5
        return [random.uniform(0, self.width), y, random.uniform(-0.03, 0.03), -random.uniform(0.12, 0.35),
                random.uniform(1.5, 4.0) * self.scale + 1, self.tint(), random.uniform(0, 6)]

    def move(self, particle, elapsed):
        super().move(particle, elapsed)
        particle[0] += math.sin(particle[6] * 3) * 20 * elapsed * self.scale

    def shade(self, particle):
        light = 0.35 + 0.65 * max(0.0, min(1.0, particle[1] / self.height))
        return tuple(int(value * light) for value in particle[5])


class Snow(Effect):
    '''
    Flakes falling, drifting from side to side
    '''
    PALETTE = ((255, 255, 255), (220, 235, 255))

    def new(self, first=False):
        y = random.uniform(0, self.height) if first else -5
        return [random.uniform(0, self.width), y, 0, random.uniform(0.05, 0.14),
                random.uniform(1.5, 4.5) * self.scale + 1, self.tint(), random.uniform(0, 6)]

    def move(self, particle, elapsed):
        super().move(particle, elapsed)
        particle[0] += math.sin(particle[6] * 1.3) * 30 * elapsed * self.scale


class Bubbles(Effect):
    '''
    Rings rising slowly
    '''
    PALETTE = ((120, 200, 255), (180, 230, 255), (255, 255, 255))

    def new(self, first=False):
        y = random.uniform(0, self.height) if first else self.height + 30
        return [random.uniform(0, self.width), y, 0, -random.uniform(0.04, 0.10),
                random.uniform(6, 22) * self.scale + 2, self.tint(), random.uniform(0, 6)]

    def move(self, particle, elapsed):
        super().move(particle, elapsed)
        particle[0] += math.sin(particle[6] * 2) * 15 * elapsed * self.scale

    def draw_one(self, surface, particle):
        pygame.draw.circle(surface, particle[5], (int(particle[0]), int(particle[1])), max(2, int(particle[4])),
                           max(1, int(2 * self.scale)))


class Fireflies(Effect):
    '''
    Small lights wandering, glowing and fading
    '''
    PALETTE = ((210, 255, 120), (255, 240, 140))

    def new(self, first=False):
        angle = random.uniform(0, math.tau)
        return [random.uniform(0, self.width), random.uniform(0, self.height), math.cos(angle) * 0.03,
                math.sin(angle) * 0.03, random.uniform(2, 4.5) * self.scale + 1, self.tint(), random.uniform(0, 6)]

    def move(self, particle, elapsed):
        # Turning a little now and then ; back inside at the edges
        if random.random() < elapsed * 0.8:
            angle = math.atan2(particle[3], particle[2]) + random.uniform(-1.2, 1.2)
            particle[2], particle[3] = math.cos(angle) * 0.03, math.sin(angle) * 0.03
        super().move(particle, elapsed)
        if not 0 <= particle[0] <= self.width:
            particle[2] = -particle[2]
        if not 0 <= particle[1] <= self.height:
            particle[3] = -particle[3]

    def gone(self, particle):
        return False

    def shade(self, particle):
        light = 0.25 + 0.75 * (0.5 + 0.5 * math.sin(particle[6] * 2.2))
        return tuple(int(value * light) for value in particle[5])
