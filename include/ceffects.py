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

EFFECTS = ('none', 'sparks', 'snow', 'bubbles', 'fireflies', 'confetti', 'rain', 'leaves', 'twinkles', 'darts')
COLORS = {'auto': None, 'white': (255, 255, 255), 'red': (235, 50, 40), 'orange': (255, 150, 40),
          'yellow': (255, 225, 70), 'green': (70, 220, 90), 'blue': (70, 150, 255), 'purple': (190, 90, 255),
          'theme': 'theme'}
AMOUNTS = {'few': 40, 'normal': 80, 'many': 150}
SPEEDS = {'slow': 0.5, 'normal': 1.0, 'fast': 1.8}


def color_of(value, theme_color=None):
    '''
    A colour setting : a name of COLORS (the first ones), or r,g,b (chosen in the palette, see
    cthemeeditor.pick_color). None : the own colours of the effect
    '''
    value = str(value).strip()
    if value in COLORS:
        chosen = COLORS[value]
    else:
        try:
            parts = [max(0, min(255, int(float(part)))) for part in value.strip('()').split(',')]
            chosen = tuple(parts) if len(parts) == 3 else None
        except ValueError:
            chosen = None
    if chosen == 'theme':
        chosen = tuple(theme_color[:3]) if theme_color else None
    return chosen


def color_text(color):
    '''
    A colour of the palette as it is written in the settings (r,g,b)
    '''
    return ','.join(str(int(part)) for part in color[:3]) if isinstance(color, (tuple, list)) else str(color)


def mix(back, color, light):
    '''
    A colour between the background (0) and the colour (1) : no alpha drawn
    '''
    return tuple(int(a + (b - a) * light) for a, b in zip(back, color))


def make(name, size, color='auto', amount='normal', speed='normal', theme_color=None, scale=None):
    '''
    The effect of this name for a screen of this size, None : none
    '''
    kinds = {'sparks': Sparks, 'snow': Snow, 'bubbles': Bubbles, 'fireflies': Fireflies, 'confetti': Confetti,
             'rain': Rain, 'leaves': Leaves, 'twinkles': Twinkles, 'darts': Darts}
    kind = kinds.get(str(name))
    if kind is None:
        return None
    chosen = color_of(color, theme_color)
    effect = kind(size, chosen, AMOUNTS.get(str(amount), 80), SPEEDS.get(str(speed), 1.0), scale)
    return effect


class Effect:
    '''
    Particles : [x, y, vx, vy, radius, colour, phase] ; speeds in parts of the height a second
    '''
    PALETTE = ((255, 255, 255),)
    # How many of them for the amount chosen (big ones : fewer)
    DENSITY = 1.0

    def __init__(self, size, color, amount, speed, scale=None):
        self.width, self.height = size
        self.color = color
        self.speed = speed
        # Size of the particles : that of the screen, or given (a small preview)
        self.scale = max(self.height / 1080, scale or 0)
        self.particles = [self.new(first=True) for _ in range(max(3, int(amount * self.DENSITY)))]

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
                math.sin(angle) * 0.03, random.uniform(3, 6) * self.scale + 1.5, self.tint(), random.uniform(0, 6)]

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
        light = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(particle[6] * 2.2))
        return tuple(int(value * light) for value in particle[5])


class Confetti(Effect):
    '''
    Paper squares of all colours falling and turning over
    '''
    PALETTE = ((255, 70, 70), (255, 200, 40), (70, 200, 255), (120, 230, 90), (230, 100, 255), (255, 140, 40))

    def new(self, first=False):
        y = random.uniform(0, self.height) if first else -10
        return [random.uniform(0, self.width), y, random.uniform(-0.02, 0.02), random.uniform(0.08, 0.16),
                random.uniform(4, 7) * self.scale + 1, self.tint(), random.uniform(0, 6)]

    def move(self, particle, elapsed):
        super().move(particle, elapsed)
        particle[0] += math.sin(particle[6] * 1.7) * 25 * elapsed * self.scale

    def draw_one(self, surface, particle):
        # Seen from the side as it turns : narrower, darker
        turn = math.cos(particle[6] * 4)
        radius = particle[4]
        light = 0.55 + 0.45 * abs(turn)
        rect = pygame.Rect(0, 0, max(1, int(abs(turn) * radius * 2)), max(1, int(radius * 1.2)))
        rect.center = (int(particle[0]), int(particle[1]))
        surface.fill(tuple(int(value * light) for value in particle[5]), rect)


class Rain(Effect):
    '''
    Streaks of rain falling fast, a little slanted
    '''
    PALETTE = ((150, 175, 220), (190, 205, 235))
    DENSITY = 1.5

    def new(self, first=False):
        length = random.uniform(14, 30) * self.scale + 4
        y = random.uniform(0, self.height) if first else -length
        return [random.uniform(0, self.width * 1.1), y, -0.12, random.uniform(0.9, 1.3), length / 2, self.tint(),
                random.uniform(0, 6)]

    def draw_one(self, surface, particle):
        half = particle[4]
        x, y = particle[0], particle[1]
        pygame.draw.line(surface, particle[5], (int(x + half * 0.12), int(y - half)), (int(x - half * 0.12), int(y + half)),
                         max(1, int(1.6 * self.scale)))


class Leaves(Effect):
    '''
    Autumn leaves falling, swaying and turning
    '''
    PALETTE = ((220, 120, 30), (200, 70, 30), (230, 170, 50), (150, 90, 40))
    DENSITY = 0.4

    def new(self, first=False):
        y = random.uniform(0, self.height) if first else -20
        return [random.uniform(0, self.width), y, random.uniform(-0.02, 0.03), random.uniform(0.05, 0.10),
                random.uniform(7, 13) * self.scale + 2, self.tint(), random.uniform(0, 6)]

    def move(self, particle, elapsed):
        super().move(particle, elapsed)
        particle[0] += math.sin(particle[6] * 1.1) * 45 * elapsed * self.scale

    def draw_one(self, surface, particle):
        radius = particle[4]
        turn = math.cos(particle[6] * 1.6)
        rect = pygame.Rect(0, 0, max(2, int(abs(turn) * radius * 2)), max(2, int(radius * 1.1)))
        rect.center = (int(particle[0]), int(particle[1]))
        pygame.draw.ellipse(surface, tuple(int(value * (0.6 + 0.4 * abs(turn))) for value in particle[5]), rect)


class Twinkles(Effect):
    '''
    Little stars shining a moment here and there, then gone
    '''
    PALETTE = ((255, 255, 255), (255, 240, 180), (200, 225, 255))
    DENSITY = 0.4

    def new(self, first=False):
        life = random.uniform(0.8, 1.8)
        return [random.uniform(0, self.width), random.uniform(0, self.height), 0, 0,
                random.uniform(6, 14) * self.scale + 2, self.tint(), random.uniform(0, life) if first else 0, life]

    def move(self, particle, elapsed):
        # In place : only the time goes (the speed : how fast they come and go)
        particle[6] += elapsed * (self.speed - 1)

    def gone(self, particle):
        return particle[6] >= particle[7]

    def draw_one(self, surface, particle):
        light = math.sin(math.pi * max(0.0, min(1.0, particle[6] / particle[7])))
        size = particle[4] * light
        if size < 1:
            return
        x, y = int(particle[0]), int(particle[1])
        color = tuple(int(value * (0.4 + 0.6 * light)) for value in particle[5])
        width = max(1, int(1.5 * self.scale))
        pygame.draw.line(surface, color, (x - int(size), y), (x + int(size), y), width)
        pygame.draw.line(surface, color, (x, y - int(size)), (x, y + int(size)), width)
        pygame.draw.circle(surface, color, (x, y), max(1, int(size / 4)))


class Darts(Effect):
    '''
    Darts flying across the screen, from the left to the right
    '''
    PALETTE = ((230, 40, 40), (40, 110, 230), (40, 190, 80), (240, 200, 30))
    DENSITY = 0.12
    BARREL = (200, 200, 205)

    def new(self, first=False):
        length = random.uniform(40, 70) * self.scale + 6
        x = random.uniform(0, self.width) if first else -length
        return [x, random.uniform(self.height * 0.05, self.height * 0.95), random.uniform(0.25, 0.45),
                random.uniform(-0.03, 0.03), length / 2, self.tint(), random.uniform(0, 6)]

    def draw_one(self, surface, particle):
        half = particle[4]
        angle = math.atan2(particle[3], particle[2])
        dx, dy = math.cos(angle), math.sin(angle)
        x, y = particle[0], particle[1]

        def at(part):
            # A point along the dart : 1 the tip, -1 the back
            return (x + dx * half * part, y + dy * half * part)
        width = max(1, int(2 * self.scale))
        # The point, the barrel (thicker), the shaft
        pygame.draw.line(surface, (230, 230, 235), at(0.55), at(1.0), max(1, width // 2))
        pygame.draw.line(surface, self.BARREL, at(-0.1), at(0.55), width * 2)
        pygame.draw.line(surface, (120, 120, 125), at(-0.95), at(-0.1), width)
        # The flights : wider at the back
        wing = half * 0.32
        back = at(-1.0)
        pygame.draw.polygon(surface, particle[5], [at(-0.4), (back[0] - dy * wing, back[1] + dx * wing),
                                                   at(-0.85), (back[0] + dy * wing, back[1] - dx * wing)])


# ---------------------------------------------------------------------- animated backgrounds
# Scenes : a background of their own (not the one of the menu), drawn as the effects (only the
# places changed). Over a plain colour, the logo is blended once : no alpha at each frame (a
# picture with transparency costs 0.22 µs a pixel on a Pi 3)
SCENES = ('none', 'night-sky', 'starfield', 'logo-spin', 'logo-bounce', 'shapes', 'dartboard', 'fireworks',
          'soft-lights')
SCENE_COLOR = (8, 10, 26)


def make_scene(name, size, logo=None, theme_color=None, color='auto'):
    '''
    The animated background of this name for a screen of this size, None : none. color : one of
    COLORS (auto : its own colours) : the stars, the shapes, the shade behind the logo
    '''
    kinds = {'night-sky': NightSky, 'starfield': Starfield, 'logo-spin': LogoSpin, 'logo-bounce': LogoBounce,
             'shapes': Shapes, 'dartboard': Dartboard, 'fireworks': Fireworks, 'soft-lights': SoftLights}
    kind = kinds.get(str(name))
    if kind is None:
        return None
    accent = tuple(theme_color[:3]) if theme_color else (255, 200, 0)
    chosen = color_of(color, accent)
    return kind(size, logo, accent, chosen)


class Scene:
    '''
    An animated background : background() its still part, step() / draw() as the effects
    '''

    def __init__(self, size, logo, accent, color=None):
        self.width, self.height = size
        self.scale = self.height / 1080
        self.accent = accent
        self.color = color
        self.logo_file = logo
        self.time = 0.0
        # The plain colour behind : a dark shade of the colour chosen
        self.back = tuple(int(value * 0.18) for value in color) if color else SCENE_COLOR

    def background(self):
        surface = pygame.Surface((self.width, self.height))
        surface.fill(self.back)
        return surface

    def tinted(self, light):
        '''
        A light (0 to 1) in the colour chosen, else white
        '''
        base = self.color or (255, 255, 255)
        return tuple(int(value * light) for value in base)

    def step(self, elapsed):
        self.time += min(elapsed, 0.2)
        return []

    def draw(self, surface, clip=None):
        pass

    def logo(self, width):
        '''
        The logo of the game blended once over the colour of the scene (opaque)
        '''
        try:
            picture = pygame.image.load(self.logo_file).convert_alpha()
        except Exception:    # pylint: disable=broad-except
            picture = pygame.Surface((400, 225), pygame.SRCALPHA)
            pygame.draw.circle(picture, self.accent, (112, 112), 100, 12)
        height = int(picture.get_height() * width / picture.get_width())
        picture = pygame.transform.smoothscale(picture, (width, height))
        flat = pygame.Surface((width, height))
        flat.fill(self.back)
        flat.blit(picture, (0, 0))
        return flat.convert()


class NightSky(Scene):
    '''
    Stars twinkling, now and then a shooting star
    '''

    def __init__(self, size, logo, accent, color=None):
        super().__init__(size, logo, accent, color)
        self.stars = [[random.uniform(0, self.width), random.uniform(0, self.height),
                       random.uniform(0.8, 2.6) * self.scale + 0.6, random.uniform(0, 6), random.uniform(0.6, 2.0)]
                      for _ in range(140)]
        self.meteor = None
        self.last = []

    def background(self):
        surface = pygame.Surface((self.width, self.height))
        # Darker at the top
        top = (4, 6, 20) if self.color is None else tuple(int(value * 0.04) for value in self.color)
        low = (18, 18, 50) if self.color is None else tuple(int(value * 0.2) for value in self.color)
        for row in range(0, self.height, 4):
            light = row / self.height
            surface.fill(tuple(int(a + (b - a) * light) for a, b in zip(top, low)), (0, row, self.width, 4))
        return surface

    def step(self, elapsed):
        super().step(elapsed)
        # A third of the stars drawn again at each frame (they twinkle slowly)
        changed = [pygame.Rect(int(star[0] - star[2] - 1), int(star[1] - star[2] - 1), int(star[2] * 2 + 3),
                               int(star[2] * 2 + 3))
                   for star in self.stars if int(self.time * 20 + star[3] * 10) % 3 == 0]
        if self.meteor is None and random.random() < elapsed * 0.25:
            self.meteor = [random.uniform(0, self.width * 0.7), random.uniform(0, self.height * 0.4), 0.0]
        changed += self.last
        self.last = []
        if self.meteor is not None:
            self.meteor[2] += elapsed
            if self.meteor[2] > 1.2:
                self.meteor = None
            else:
                rect = self.meteor_rect()
                changed.append(rect)
                self.last = [rect]
        return changed

    def meteor_ends(self):
        x, y, age = self.meteor
        head = (x + age * self.width * 0.45, y + age * self.height * 0.25)
        tail = (head[0] - self.width * 0.08, head[1] - self.height * 0.045)
        return head, tail

    def meteor_rect(self):
        head, tail = self.meteor_ends()
        return pygame.Rect(int(min(head[0], tail[0])) - 3, int(min(head[1], tail[1])) - 3,
                           int(abs(head[0] - tail[0])) + 7, int(abs(head[1] - tail[1])) + 7)

    def draw(self, surface, clip=None):
        for x, y, radius, phase, speed in self.stars:
            light = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(self.time * speed + phase))
            if self.color is None:
                value = int(255 * light)
                shade = (value, value, min(255, value + 20))
            else:
                shade = self.tinted(light)
            pygame.draw.circle(surface, shade, (int(x), int(y)), max(1, int(radius)))
        if self.meteor is not None:
            head, tail = self.meteor_ends()
            pygame.draw.line(surface, self.color or (255, 255, 230), tail, head, max(2, int(3 * self.scale)))


class Starfield(Scene):
    '''
    Travel among the stars : they come from the middle, faster and bigger as they come near
    '''

    def __init__(self, size, logo, accent, color=None):
        super().__init__(size, logo, accent, color)
        self.stars = [self.new(first=True) for _ in range(160)]

    @staticmethod
    def new(first=False):
        return [random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(0.1, 1.0) if first else 1.0]

    def screen_of(self, star):
        x, y, depth = star
        depth = max(depth, 0.02)
        sx = self.width / 2 + x / depth * self.width / 2
        sy = self.height / 2 + y / depth * self.height / 2
        return sx, sy, max(1, int((1.2 - depth) * 3.5 * self.scale + 0.5))

    def place(self, star):
        sx, sy, radius = self.screen_of(star)
        return pygame.Rect(int(sx) - radius - 1, int(sy) - radius - 1, radius * 2 + 3, radius * 2 + 3)

    def step(self, elapsed):
        super().step(elapsed)
        changed = []
        for index, star in enumerate(self.stars):
            before = self.place(star)
            star[2] -= min(elapsed, 0.2) * 0.35
            sx, sy, _radius = self.screen_of(star)
            if star[2] <= 0.02 or not (0 <= sx < self.width and 0 <= sy < self.height):
                # Back to the middle : its last place and its new one, apart
                self.stars[index] = star = self.new()
                changed += [before, self.place(star)]
            else:
                changed.append(before.union(self.place(star)))
        return changed

    def draw(self, surface, clip=None):
        for star in self.stars:
            sx, sy, radius = self.screen_of(star)
            pygame.draw.circle(surface, self.tinted(max(0.0, min(1.0, (1.1 - star[2])))), (int(sx), int(sy)), radius)


class LogoSpin(Scene):
    '''
    The logo of the game turning on itself (as a coin), in the middle
    '''

    def __init__(self, size, logo, accent, color=None):
        super().__init__(size, logo, accent, color)
        self.picture = self.logo(int(self.width * 0.42))
        self.box = self.picture.get_rect(center=(self.width // 2, self.height // 2))

    def step(self, elapsed):
        super().step(elapsed)
        return [self.box]

    def draw(self, surface, clip=None):
        if clip is not None and not clip.colliderect(self.box):
            return
        surface.fill(self.back, self.box)
        turn = math.cos(self.time * 1.2)
        width = max(2, int(abs(turn) * self.box.width))
        picture = pygame.transform.scale(self.picture, (width, self.box.height))
        if turn < 0:
            picture = pygame.transform.flip(picture, True, False)
        surface.blit(picture, picture.get_rect(center=self.box.center))


class LogoBounce(Scene):
    '''
    The logo of the game moving and bouncing on the edges of the screen
    '''

    def __init__(self, size, logo, accent, color=None):
        super().__init__(size, logo, accent, color)
        self.picture = self.logo(int(self.width * 0.26))
        self.rect = self.picture.get_rect(topleft=(int(self.width * 0.2), int(self.height * 0.3)))
        self.position = [float(self.rect.x), float(self.rect.y)]
        self.speed = [self.height * 0.16, self.height * 0.12]

    def step(self, elapsed):
        super().step(elapsed)
        before = self.rect.copy()
        elapsed = min(elapsed, 0.2)
        for axis, limit in ((0, self.width - self.rect.width), (1, self.height - self.rect.height)):
            self.position[axis] += self.speed[axis] * elapsed
            if self.position[axis] < 0 or self.position[axis] > limit:
                self.speed[axis] = -self.speed[axis]
                self.position[axis] = max(0, min(limit, self.position[axis]))
        self.rect.topleft = (int(self.position[0]), int(self.position[1]))
        return [before.union(self.rect)]

    def draw(self, surface, clip=None):
        if clip is None or clip.colliderect(self.rect):
            surface.blit(self.picture, self.rect)


class Shapes(Scene):
    '''
    Outlines of triangles, squares and hexagons drifting and turning slowly
    '''

    def __init__(self, size, logo, accent, color=None):
        super().__init__(size, logo, accent, color)
        palette = (color,) if color else (accent, (90, 160, 255), (255, 255, 255), (255, 120, 60))
        self.shapes = [[random.uniform(0, self.width), random.uniform(0, self.height), random.uniform(-0.04, 0.04),
                        random.uniform(-0.04, 0.04), random.uniform(25, 90) * self.scale, random.choice((3, 4, 6)),
                        random.uniform(0, 6), random.uniform(-0.6, 0.6), random.choice(palette)] for _ in range(18)]

    @staticmethod
    def points(shape):
        x, y, _vx, _vy, radius, sides, angle = shape[:7]
        return [(x + radius * math.cos(angle + index * math.tau / sides),
                 y + radius * math.sin(angle + index * math.tau / sides)) for index in range(sides)]

    @staticmethod
    def place(shape):
        radius = int(shape[4]) + 4
        return pygame.Rect(int(shape[0]) - radius, int(shape[1]) - radius, radius * 2, radius * 2)

    def step(self, elapsed):
        super().step(elapsed)
        elapsed = min(elapsed, 0.2)
        changed = []
        for shape in self.shapes:
            before = self.place(shape)
            shape[0] = (shape[0] + shape[2] * self.height * elapsed + 100) % (self.width + 200) - 100
            shape[1] = (shape[1] + shape[3] * self.height * elapsed + 100) % (self.height + 200) - 100
            shape[6] += shape[7] * elapsed
            after = self.place(shape)
            # Gone at one edge, back at the other : two places
            changed += [before, after] if abs(after.x - before.x) > self.width / 2 or abs(after.y - before.y) > self.height / 2 \
                else [before.union(after)]
        return changed

    def draw(self, surface, clip=None):
        for shape in self.shapes:
            pygame.draw.polygon(surface, shape[8], self.points(shape), max(2, int(3 * self.scale)))


class Dartboard(Scene):
    '''
    A dartboard in the middle, a light going round it (as the lights of a cabinet), with a trail.
    Only the sectors of the light are drawn again, when it goes to the next one
    '''
    TRAIL = (1.0, 0.6, 0.35, 0.15)
    SINGLES = ((22, 22, 22), (232, 222, 190))
    DOUBLES = ((200, 32, 32), (30, 140, 60))

    def __init__(self, size, logo, accent, color=None):
        super().__init__(size, logo, accent, color)
        self.center = (self.width / 2, self.height / 2)
        self.radius = self.height * 0.4
        self.light = color or accent
        self.rings = ((0.16, 0.58, self.SINGLES), (0.58, 0.64, self.DOUBLES), (0.64, 0.94, self.SINGLES),
                      (0.94, 1.0, self.DOUBLES))
        self.lit = -1
        self.board = None

    def wedge(self, index, inner, outer):
        start = math.radians(-99 + index * 18)
        angles = [start + math.radians(18) * step / 6 for step in range(7)]
        cx, cy = self.center
        return [(cx + math.cos(angle) * self.radius * outer, cy + math.sin(angle) * self.radius * outer) for angle in angles] + \
            [(cx + math.cos(angle) * self.radius * inner, cy + math.sin(angle) * self.radius * inner)
             for angle in reversed(angles)]

    def sector_rect(self, index):
        points = self.wedge(index, 0.16, 1.0)
        xs, ys = [point[0] for point in points], [point[1] for point in points]
        return pygame.Rect(int(min(xs)) - 3, int(min(ys)) - 3, int(max(xs) - min(xs)) + 7, int(max(ys) - min(ys)) + 7)

    def background(self):
        if self.board is None:
            surface = super().background()
            center = (int(self.center[0]), int(self.center[1]))
            pygame.draw.circle(surface, (12, 12, 12), center, int(self.radius * 1.12))
            pygame.draw.circle(surface, mix((12, 12, 12), self.light, 0.5), center, int(self.radius * 1.12),
                               max(2, int(3 * self.scale)))
            for index in range(20):
                for inner, outer, colors in self.rings:
                    pygame.draw.polygon(surface, colors[index % 2], self.wedge(index, inner, outer))
            pygame.draw.circle(surface, self.DOUBLES[1], center, int(self.radius * 0.16))
            pygame.draw.circle(surface, self.DOUBLES[0], center, int(self.radius * 0.07))
            self.board = surface
        return self.board

    def step(self, elapsed):
        super().step(elapsed)
        lit = int(self.time * 6) % 20
        if lit == self.lit:
            return []
        self.lit = lit
        # The sectors of the trail, and the one it leaves
        return [self.sector_rect((lit - back) % 20) for back in range(len(self.TRAIL) + 1)]

    def draw(self, surface, clip=None):
        if self.lit < 0:
            return
        for back, light in enumerate(self.TRAIL):
            index = (self.lit - back) % 20
            for inner, outer, colors in self.rings:
                pygame.draw.polygon(surface, mix(colors[index % 2], self.light, light * 0.85), self.wedge(index, inner, outer))


class Fireworks(Scene):
    '''
    Rockets going up and bursting into sparks which fall and fade
    '''
    PALETTE = ((255, 90, 70), (255, 200, 60), (90, 200, 255), (160, 110, 255), (110, 255, 140), (255, 120, 220))

    def __init__(self, size, logo, accent, color=None):
        super().__init__(size, logo, accent, color)
        self.rockets = []
        self.sparks = []
        self.wait = 0.2
        self.size = max(2, int(3.5 * max(self.scale, 0.75)))

    def spark_rect(self, spark):
        size = self.size + 2
        return pygame.Rect(int(spark[0]) - size, int(spark[1]) - size, size * 2 + 1, size * 2 + 1)

    def rocket_rect(self, rocket):
        size = self.size + 3
        return pygame.Rect(int(rocket[0]) - size, int(rocket[1]) - size, size * 2 + 1, int(self.height * 0.035) + size * 2)

    def step(self, elapsed):
        super().step(elapsed)
        elapsed = min(elapsed, 0.2)
        changed = []
        self.wait -= elapsed
        if self.wait <= 0 and len(self.rockets) + len(self.sparks) // 40 < 4:
            color = self.color or random.choice(self.PALETTE)
            self.rockets.append([random.uniform(self.width * 0.15, self.width * 0.85), float(self.height),
                                 -random.uniform(0.55, 0.75) * self.height, random.uniform(0.15, 0.45) * self.height, color])
            self.wait = random.uniform(0.5, 1.4)
        for rocket in list(self.rockets):
            before = self.rocket_rect(rocket)
            rocket[1] += rocket[2] * elapsed
            if rocket[1] <= rocket[3]:
                self.rockets.remove(rocket)
                changed.append(before)
                for _ in range(50):
                    angle, speed = random.uniform(0, math.tau), random.uniform(0.08, 0.3) * self.height
                    self.sparks.append([rocket[0], rocket[1], math.cos(angle) * speed, math.sin(angle) * speed,
                                        random.uniform(1.0, 1.7), 0.0, rocket[4]])
            else:
                changed.append(before.union(self.rocket_rect(rocket)))
        for spark in list(self.sparks):
            before = self.spark_rect(spark)
            spark[5] += elapsed
            spark[3] += 0.22 * self.height * elapsed
            spark[2] *= 1 - 0.9 * elapsed
            spark[0] += spark[2] * elapsed
            spark[1] += spark[3] * elapsed
            if spark[5] >= spark[4]:
                self.sparks.remove(spark)
                changed.append(before)
            else:
                changed.append(before.union(self.spark_rect(spark)))
        return changed

    def draw(self, surface, clip=None):
        for x, y, _speed, _top, _color in self.rockets:
            pygame.draw.line(surface, (120, 90, 60), (int(x), int(y)), (int(x), int(y + self.height * 0.03)),
                             max(1, self.size - 1))
            pygame.draw.circle(surface, (255, 235, 190), (int(x), int(y)), self.size + 1)
        for x, y, _vx, _vy, life, age, color in self.sparks:
            pygame.draw.circle(surface, mix(self.back, color, (1 - age / life) ** 0.6), (int(x), int(y)), self.size)


class SoftLights(Scene):
    '''
    Big soft lights drifting slowly and glowing (a few of them moved at each frame : cheap)
    '''

    def __init__(self, size, logo, accent, color=None):
        super().__init__(size, logo, accent, color)
        palette = tuple(mix((0, 0, 0), color, light) for light in (0.7, 0.85, 1.0)) if color else \
            (accent, (90, 140, 255), (180, 90, 255), (255, 110, 170), (80, 220, 220))
        self.lights = [[random.uniform(0, self.width), random.uniform(0, self.height), random.uniform(-0.03, 0.03),
                        random.uniform(-0.03, 0.03), random.uniform(45, 115) * self.scale + 4, random.choice(palette),
                        random.uniform(0, 6), 0.0] for _ in range(12)]
        self.turn = 0

    @staticmethod
    def place(light):
        radius = int(light[4]) + 2
        return pygame.Rect(int(light[0]) - radius, int(light[1]) - radius, radius * 2 + 1, radius * 2 + 1)

    def step(self, elapsed):
        super().step(elapsed)
        elapsed = min(elapsed, 0.2)
        for light in self.lights:
            light[7] += elapsed
        changed = []
        for _ in range(3):
            light = self.lights[self.turn % len(self.lights)]
            self.turn += 1
            before = self.place(light)
            spent, light[7] = light[7], 0.0
            margin = light[4] * 2
            light[0] = (light[0] + light[2] * self.height * spent + margin) % (self.width + margin * 2) - margin
            light[1] = (light[1] + light[3] * self.height * spent + margin) % (self.height + margin * 2) - margin
            light[6] += spent
            after = self.place(light)
            changed += [before, after] if abs(after.x - before.x) > self.width / 2 or abs(after.y - before.y) > self.height / 2 \
                else [before.union(after)]
        return changed

    def draw(self, surface, clip=None):
        for x, y, _vx, _vy, radius, color, phase, _spent in self.lights:
            if clip is not None and not clip.colliderect(pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)):
                continue
            glow = 0.2 + 0.15 * (0.5 + 0.5 * math.sin(phase * 0.7))
            pygame.draw.circle(surface, mix(self.back, color, glow), (int(x), int(y)), int(radius))
            pygame.draw.circle(surface, mix(self.back, color, glow * 1.5), (int(x), int(y)), int(radius * 0.7))
