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


# ---------------------------------------------------------------------- animated backgrounds
# Scenes : a background of their own (not the one of the menu), drawn as the effects (only the
# places changed). Over a plain colour, the logo is blended once : no alpha at each frame (a
# picture with transparency costs 0.22 µs a pixel on a Pi 3)
SCENES = ('none', 'night-sky', 'starfield', 'logo-spin', 'logo-bounce', 'shapes')
SCENE_COLOR = (8, 10, 26)


def make_scene(name, size, logo=None, theme_color=None):
    '''
    The animated background of this name for a screen of this size, None : none
    '''
    kinds = {'night-sky': NightSky, 'starfield': Starfield, 'logo-spin': LogoSpin, 'logo-bounce': LogoBounce,
             'shapes': Shapes}
    kind = kinds.get(str(name))
    if kind is None:
        return None
    return kind(size, logo, tuple(theme_color[:3]) if theme_color else (255, 200, 0))


class Scene:
    '''
    An animated background : background() its still part, step() / draw() as the effects
    '''

    def __init__(self, size, logo, accent):
        self.width, self.height = size
        self.scale = self.height / 1080
        self.accent = accent
        self.logo_file = logo
        self.time = 0.0

    def background(self):
        surface = pygame.Surface((self.width, self.height))
        surface.fill(SCENE_COLOR)
        return surface

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
        flat.fill(SCENE_COLOR)
        flat.blit(picture, (0, 0))
        return flat.convert()


class NightSky(Scene):
    '''
    Stars twinkling, now and then a shooting star
    '''

    def __init__(self, size, logo, accent):
        super().__init__(size, logo, accent)
        self.stars = [[random.uniform(0, self.width), random.uniform(0, self.height),
                       random.uniform(0.8, 2.6) * self.scale + 0.6, random.uniform(0, 6), random.uniform(0.6, 2.0)]
                      for _ in range(140)]
        self.meteor = None
        self.last = []

    def background(self):
        surface = pygame.Surface((self.width, self.height))
        # Darker at the top
        for row in range(0, self.height, 4):
            light = row / self.height
            surface.fill((int(4 + 14 * light), int(6 + 12 * light), int(20 + 30 * light)), (0, row, self.width, 4))
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
            value = int(255 * light)
            pygame.draw.circle(surface, (value, value, min(255, value + 20)), (int(x), int(y)), max(1, int(radius)))
        if self.meteor is not None:
            head, tail = self.meteor_ends()
            pygame.draw.line(surface, (255, 255, 230), tail, head, max(2, int(3 * self.scale)))


class Starfield(Scene):
    '''
    Travel among the stars : they come from the middle, faster and bigger as they come near
    '''

    def __init__(self, size, logo, accent):
        super().__init__(size, logo, accent)
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
            light = int(255 * max(0.0, min(1.0, (1.1 - star[2]))))
            pygame.draw.circle(surface, (light, light, light), (int(sx), int(sy)), radius)


class LogoSpin(Scene):
    '''
    The logo of the game turning on itself (as a coin), in the middle
    '''

    def __init__(self, size, logo, accent):
        super().__init__(size, logo, accent)
        self.picture = self.logo(int(self.width * 0.42))
        self.box = self.picture.get_rect(center=(self.width // 2, self.height // 2))

    def step(self, elapsed):
        super().step(elapsed)
        return [self.box]

    def draw(self, surface, clip=None):
        if clip is not None and not clip.colliderect(self.box):
            return
        surface.fill(SCENE_COLOR, self.box)
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

    def __init__(self, size, logo, accent):
        super().__init__(size, logo, accent)
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

    def __init__(self, size, logo, accent):
        super().__init__(size, logo, accent)
        palette = (accent, (90, 160, 255), (255, 255, 255), (255, 120, 60))
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
