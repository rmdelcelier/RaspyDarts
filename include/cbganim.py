"""
Animated background of the menus (the screens before the games) : a video (MP4, GIF, WebM...)
chosen by the user, shown behind the buttons.

Measured on a Pi 3 B+ (1920x1080, pygame without NEON) :
- decoding the video while it is shown costs about a core (MP4 960x540 20 i/s : 86 % of the
  whole processor with the menu) ; its frames prepared once, in 256 colours (one palette for
  the whole video, ffmpeg palettegen / paletteuse), kept in memory (0.5 MB a frame in
  960x540) : 20 i/s, 57 % of the processor ;
- a layer with an alpha channel over the video costs 460 ms a frame : the menu is drawn as
  always, on a surface of its own (the layer) whose background is filled with a key colour,
  and blitted over the video with that colour transparent (2 to 12 ms). The key colour is
  the average colour of the video : the soft edges of the texts drawn on the background
  blend with a colour close to the video, the translucent buttons become opaque ;
- the hardware decoder of the Pi 3 is slower than the processor : not used.

The frames prepared (preparation : once per video and per rate, in the background, in a
temporary file checked then renamed ; paused during the games) are kept in
~/.raspydarts/cache/fond_anime. Until they are ready, and on the Pi too small for it, the
background is a still picture of the video.

Settings (raspydarts.cfg, SectionGlobals) : animated_background (the video, empty : none),
animated_background_rate (auto, 30, 20, 10, still), animated_effect (a drawn effect, see
include/ceffects.py : over the video, or alone over the background of the menu, its own image
included) and its colour, amount and speed.
"""

import hashlib
import json
import os
import shutil
import signal
import subprocess
import threading
import time

import pygame

from include import ceffects
from include import cpaths

# Size of the frames kept (made bigger on the screen) ; 256 colours : a byte a pixel and the
# palette after each frame (rawvideo pal8 of ffmpeg)
WIDTH, HEIGHT = 960, 540
FRAME_BYTES = WIDTH * HEIGHT + 1024
RATES = ('auto', '30', '20', '10', 'still')
# Longest video kept (seconds) : a background loops
LONGEST = 30


def cache_dir():
    return os.path.join(cpaths.user_dir(), 'cache', 'fond_anime')


def memory_mb():
    try:
        with open('/proc/meminfo', encoding='utf-8') as meminfo:
            for line in meminfo:
                if line.startswith('MemTotal:'):
                    return int(line.split()[1]) // 1024
    except OSError:
        pass
    return 0


def pi_model():
    try:
        with open('/proc/device-tree/model', encoding='utf-8') as model:
            return model.read().rstrip('\x00').strip()
    except OSError:
        return ''


def profile(model=None, memory=None):
    '''
    What this machine can show, from the data of the maker (only the Pi 3 B+ was measured) :
    rate (frames a second, 0 : a still picture) and the memory given to the frames (MB).
    Pi Zero 2 W (4 x A53 1 GHz, 512 MB) : still ; Pi 3 A+ (4 x A53 1.4 GHz, 512 MB) : 10 ;
    Pi 3 B (4 x A53 1.2 GHz, 1 GB) : 15 ; Pi 3 B+ (4 x A53 1.4 GHz, 1 GB, measured) : 20 ;
    Pi 4 / 400 / 5 (A72 1.5-1.8 GHz, A76 2.4 GHz) : 30 ; the older ones : still
    '''
    model = pi_model() if model is None else model
    memory = memory_mb() if memory is None else memory
    if 'Raspberry' not in model:
        return {'rate': 30, 'memory': 300, 'name': model or '?'}
    if 'Zero 2' in model:
        rate, budget = 0, 0
    elif 'Pi 3 Model A' in model:
        rate, budget = 10, 45
    elif 'Pi 3 Model B Plus' in model:
        rate, budget = 20, 110
    elif 'Pi 3' in model or 'Compute Module 3' in model:
        rate, budget = 15, 100
    elif any(name in model for name in ('Pi 4', 'Pi 400', 'Compute Module 4', 'Pi 5', 'Pi 500', 'Compute Module 5')):
        rate, budget = 30, 300 if memory >= 2000 else 110
    else:
        rate, budget = 0, 0
    if memory and memory < 700:
        budget = min(budget, 45)
    return {'rate': rate, 'memory': budget, 'name': model}


def wanted_rate(setting, machine):
    '''
    Rate of the frames prepared and shown : the setting (auto : the one of this Pi). 0 : a
    still picture
    '''
    setting = str(setting or 'auto')
    if setting == 'still':
        return 0
    if setting.isdigit():
        return int(setting) if machine['memory'] else 0
    return machine['rate']


def source_key(path):
    '''
    Name of the files prepared from a video : changes with the video (its place, size, date)
    '''
    try:
        stat = os.stat(path)
        text = f"{os.path.realpath(path)}|{stat.st_size}|{int(stat.st_mtime)}"
    except OSError:
        text = os.path.realpath(path)
    return hashlib.sha1(text.encode('utf-8')).hexdigest()[:12]


def keep_source(path, logs=None):
    '''
    The video chosen kept where it stays : from a USB key (/media, /mnt), copied in
    ~/.raspydarts/images/fond_anime (it is prepared again when the rate changes). Its path, None :
    not copied
    '''
    full = os.path.realpath(path)
    if not full.startswith(('/media/', '/mnt/')):
        return full
    target_dir = os.path.join(cpaths.user_dir(), 'images', 'fond_anime')
    try:
        os.makedirs(target_dir, exist_ok=True)
        target = os.path.join(target_dir, os.path.basename(full))
        if not os.path.exists(target) or os.path.getsize(target) != os.path.getsize(full):
            shutil.copyfile(full, target + '.tmp')
            os.replace(target + '.tmp', target)
        return target
    except OSError as error:
        if logs is not None:
            logs.error(f"Animated background : {path} not copied ({error})")
        return None


def clean_cache(path=None, rate=0):
    '''
    The frames prepared from other videos or at another rate removed (about 100 MB each) ;
    path, rate : the video chosen and its rate (its still picture kept), None : all removed
    '''
    try:
        names = os.listdir(cache_dir())
    except OSError:
        return
    kept = ()
    if path:
        kept = (os.path.basename(still_path(path)),) + tuple(os.path.basename(name) for name in frames_paths(path, rate))
    for name in names:
        if name not in kept:
            try:
                os.remove(os.path.join(cache_dir(), name))
            except OSError:
                pass


def still_path(path):
    return os.path.join(cache_dir(), f"{source_key(path)}.png")


def frames_paths(path, rate):
    base = os.path.join(cache_dir(), f"{source_key(path)}_{WIDTH}x{HEIGHT}_{rate}")
    return base + '.pal8', base + '.json'


def duration(path):
    try:
        out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                             capture_output=True, text=True, timeout=20, check=False).stdout.strip()
        return float(out)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def make_still(path, size=(1920, 1080)):
    '''
    A still picture of the video (its first second), the size of the screen : the background
    until its frames are ready, or on a Pi too small. Its file, None : not made
    '''
    target = still_path(path)
    if os.path.exists(target):
        return target
    os.makedirs(cache_dir(), exist_ok=True)
    temporary = target + '.tmp.png'
    for start in ('1', '0'):
        try:
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', start, '-i', path, '-frames:v', '1',
                            '-vf', f"scale={size[0]}:{size[1]}:force_original_aspect_ratio=increase,crop={size[0]}:{size[1]}",
                            temporary], timeout=60, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.replace(temporary, target)
            return target
        except (OSError, subprocess.SubprocessError):
            continue
    return None


class Preparation:
    '''
    The frames of a video prepared in the background (ffmpeg, lowest priority) : its palette
    from a part of its frames (a few seconds), then all the frames in 256 colours, written in
    a temporary file renamed once checked. Paused during the games (the processor reads the
    darts). progress() : (done, total) ; state : running, paused, done, failed
    '''

    def __init__(self, logs, path, rate, budget_mb):
        self.logs = logs
        self.path = path
        self.rate = rate
        self.frames_file, self.meta_file = frames_paths(path, rate)
        self.temporary = self.frames_file + '.tmp'
        longest = min(LONGEST, int(budget_mb * 1048576 / FRAME_BYTES / rate))
        found = duration(path)
        self.length = found
        self.seconds = min(longest, found) if found else longest
        self.total = max(1, int(self.seconds * rate))
        self.done = 0
        # palette (its length unknown), then frames
        self.phase = 'palette'
        self.state = 'running'
        self.process = None
        self.paused = False
        self.lock = threading.Lock()
        threading.Thread(target=self.run, daemon=True).start()

    def progress(self):
        return self.done, self.total

    def start(self, command):
        def lowest():
            os.nice(19)
        with self.lock:
            if self.state == 'cancelled':
                return None
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,  # pylint: disable=consider-using-with
                                            stdin=subprocess.DEVNULL, preexec_fn=lowest)
            if self.paused:
                self.process.send_signal(signal.SIGSTOP)
            return self.process

    def run(self):
        os.makedirs(cache_dir(), exist_ok=True)
        palette = self.frames_file + '.palette.png'
        crop = f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase:flags=bicubic,crop={WIDTH}:{HEIGHT}"
        started = time.time()
        try:
            # The palette : from a frame every half second (all of them took minutes on a Pi 3)
            process = self.start(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-t', str(self.seconds), '-i', self.path,
                                  '-vf', f"fps=2,{crop},palettegen=stats_mode=full", palette])
            if process is None or process.wait() != 0 or not os.path.exists(palette):
                raise RuntimeError(f"palette : {process.stderr.read().decode(errors='replace')[-300:] if process else 'cancelled'}")
            # The frames, counted as they come (-progress)
            self.phase = 'frames'
            process = self.start(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-progress', 'pipe:2', '-stats_period', '1',
                                  '-t', str(self.seconds), '-i', self.path, '-i', palette, '-an', '-filter_complex',
                                  f"[0:v]fps={self.rate},{crop}[v];[v][1:v]paletteuse=dither=bayer:bayer_scale=3",
                                  '-pix_fmt', 'pal8', '-f', 'rawvideo', self.temporary])
            if process is None:
                raise RuntimeError('cancelled')
            errors = []
            for line in process.stderr:
                line = line.decode(errors='replace').strip()
                if line.startswith('frame='):
                    try:
                        self.done = min(self.total, int(line[6:]))
                    except ValueError:
                        pass
                elif '=' not in line and line:
                    errors.append(line)
            code = process.wait()
            size = os.path.getsize(self.temporary) if os.path.exists(self.temporary) else 0
            frames = size // FRAME_BYTES
            if code != 0 or frames < 1 or size % FRAME_BYTES:
                raise RuntimeError(f"ffmpeg {code}, {size} octets : {' '.join(errors)[-300:]}")
            key = average_color(self.temporary, frames)
            with open(self.meta_file, 'w', encoding='utf-8') as meta:
                json.dump({'frames': frames, 'rate': self.rate, 'width': WIDTH, 'height': HEIGHT, 'key': key,
                           'source': self.path, 'length': self.length}, meta)
            os.replace(self.temporary, self.frames_file)
            self.done = self.total = frames
            self.state = 'done'
            self.logs.info(f"Animated background : {frames} frames of {self.path} prepared in {time.time() - started:.0f} s")
        except Exception as error:    # pylint: disable=broad-except
            if self.state != 'cancelled':
                self.state = 'failed'
                self.logs.error(f"Animated background : {self.path} not prepared ({error})")
            for name in (self.temporary,):
                try:
                    os.remove(name)
                except OSError:
                    pass
        finally:
            try:
                os.remove(palette)
            except OSError:
                pass

    def pause(self, paused):
        '''
        Paused during the games : the process stopped as it is, then going on (nothing lost)
        '''
        with self.lock:
            self.paused = paused
            if self.process is not None and self.process.poll() is None:
                self.process.send_signal(signal.SIGSTOP if paused else signal.SIGCONT)
        if self.state in ('running', 'paused'):
            self.state = 'paused' if paused else 'running'

    def cancel(self):
        with self.lock:
            self.state = 'cancelled'
            if self.process is not None and self.process.poll() is None:
                self.process.send_signal(signal.SIGCONT)
                self.process.kill()


def average_color(frames_file, frames):
    '''
    The key colour of the menus over this video : its average colour (a few frames), slightly
    changed so that no pixel of a button is exactly it
    '''
    totals, count = [0, 0, 0], 0
    try:
        with open(frames_file, 'rb') as data:
            for index in range(0, frames, max(1, frames // 8)):
                data.seek(index * FRAME_BYTES)
                chunk = data.read(FRAME_BYTES)
                if len(chunk) < FRAME_BYTES:
                    break
                palette = chunk[WIDTH * HEIGHT:]
                for pixel in chunk[0:WIDTH * HEIGHT:997]:
                    totals[0] += palette[pixel * 4 + 2]
                    totals[1] += palette[pixel * 4 + 1]
                    totals[2] += palette[pixel * 4]
                    count += 1
    except OSError:
        pass
    if not count:
        return [17, 3, 29]
    red, green, blue = (int(total / count) for total in totals)
    # Odd / even mixed : a plain grey or a colour of the theme is never it exactly
    return [red | 1, green & 254, blue | 1]


class AnimatedBackground:
    '''
    The animated background of a Screen (cscreen) : the frames in memory, the layer the menus
    are drawn on (screen.screen while a menu is shown), the frame shown at each turn of the
    reading of the inputs (tick)
    '''

    def __init__(self, screen):
        self.owner = screen
        self.logs = screen.logs
        self.machine = profile()
        self.source = None
        self.rate = 0
        self.frames = []
        self.palette = None
        self.key = (17, 2, 29)
        self.still = None
        self.still_picture = None
        self.loading = None
        self.preparation = None
        # The screens of the menus being shown (see scope) ; the layer mode
        self.depth = 0
        self.layer = None
        self.keyed = None
        self.scaled = None
        self.real = None
        self.mode = None
        self.started = time.time()
        self.next_frame = 0
        self.shown = -1
        self.cost = 0.0
        self.effective = 0
        self.redraw = False
        self.in_game = False
        # The drawn effect (include/ceffects.py) : its settings, the effect, the background it is
        # drawn over when there is no video (the one of the menu, made at its first drawing)
        self.effect_settings = ('none', 'auto', 'normal', 'normal')
        self.effect = None
        # An animated background drawn (include/ceffects.py SCENES : starry sky, logo...) : its own
        # background, the effect over it ; a video chosen comes first
        self.scene_name = 'none'
        self.scene = None
        self.base = None
        self.bases = {}
        self.base_key = None
        self.use_frames = False
        self.last_step = time.time()
        self.logs.info(f"Animated background : {self.machine['name']}, rate {self.machine['rate']} i/s, "
                       f"{self.machine['memory']} MB")

    # ------------------------------------------------------------------ settings
    def settings(self):
        config = self.owner.config
        path = str(config.get_value('SectionGlobals', 'animated_background', False) or '').strip()
        rate = str(config.get_value('SectionGlobals', 'animated_background_rate', False) or 'auto').strip()
        return path, rate

    def effect_wanted(self):
        config = self.owner.config
        values = []
        for key, default in (('animated_effect', 'none'), ('animated_effect_color', 'auto'),
                             ('animated_effect_amount', 'normal'), ('animated_effect_speed', 'normal')):
            values.append(str(config.get_value('SectionGlobals', key, False) or default).strip())
        if values[0] not in ceffects.EFFECTS:
            values[0] = 'none'
        return tuple(values)

    def apply_settings(self):
        '''
        The video and the rate of the settings : its still picture at once, its frames read
        (prepared first if needed, in the background)
        '''
        path, setting = self.settings()
        rate = wanted_rate(setting, self.machine)
        effect = self.effect_wanted()
        if effect != self.effect_settings:
            # Made again at the size of the screen (see make_layer)
            self.effect_settings = effect
            self.effect = None
            self.redraw = True
        scene = str(self.owner.config.get_value('SectionGlobals', 'animated_scene', False) or 'none').strip()
        scene = scene if scene in ceffects.SCENES else 'none'
        if scene != self.scene_name:
            self.scene_name = scene
            self.scene = None
            self.bases.clear()
            self.redraw = True
        if path and not os.path.exists(path):
            self.logs.warning(f"Animated background : {path} not found")
            path = ''
        if (path, rate) == (self.source, self.rate):
            return
        if self.preparation is not None:
            self.preparation.cancel()
            self.preparation = None
        self.source, self.rate = path or None, rate
        clean_cache(path or None, rate)
        self.length = None
        self.frames = []
        self.palette = None
        self.still = None
        self.still_picture = None
        self.redraw = True
        if not path:
            return
        threading.Thread(target=self.load, args=(path, rate), daemon=True).start()

    def load(self, path, rate):
        self.still = make_still(path, self.owner.screen.get_size())
        self.redraw = True
        if rate <= 0:
            return
        frames_file, meta_file = frames_paths(path, rate)
        if not os.path.exists(frames_file):
            if self.preparation is None or self.preparation.state in ('failed', 'cancelled'):
                self.preparation = Preparation(self.logs, path, rate, self.machine['memory'] or 45)
                self.preparation.pause(self.in_game)
                # Followed in the activity indicator (include/cactivity.py)
                activities = getattr(self.owner, 'activities', None)
                if activities is not None:
                    activities.add('bganim', self.activity)
            while self.preparation is not None and self.preparation.state in ('running', 'paused'):
                time.sleep(1)
            if (path, rate) != (self.source, self.rate) or not os.path.exists(frames_file):
                return
        try:
            with open(meta_file, encoding='utf-8') as meta:
                info = json.load(meta)
            frames = []
            palette = None
            with open(frames_file, 'rb') as data:
                while True:
                    chunk = data.read(FRAME_BYTES)
                    if len(chunk) < FRAME_BYTES:
                        break
                    if palette is None:
                        raw = chunk[WIDTH * HEIGHT:]
                        palette = [(raw[index * 4 + 2], raw[index * 4 + 1], raw[index * 4]) for index in range(256)]
                    surface = pygame.Surface((WIDTH, HEIGHT), 0, 8)
                    surface.set_palette(palette)
                    surface.get_buffer().write(chunk[:WIDTH * HEIGHT], 0)
                    frames.append(surface)
            if (path, rate) != (self.source, self.rate):
                return
            self.key = tuple(info.get('key') or self.key)
            self.length = info.get('length')
            self.palette = palette
            self.frames = frames
            self.started = time.time()
            self.effective = rate
            self.redraw = True
            self.logs.info(f"Animated background : {len(frames)} frames of {path} read")
        except Exception as error:    # pylint: disable=broad-except
            self.logs.error(f"Animated background : frames of {path} not read ({error})")

    def status(self):
        '''
        For the screen of the settings : ('none'|'still'|'preparing'|'ready'|'failed', done, total)
        '''
        if not self.source:
            return 'none', 0, 0
        if self.preparation is not None and self.preparation.state in ('running', 'paused'):
            done, total = self.preparation.progress()
            return 'preparing', done, total
        if self.preparation is not None and self.preparation.state == 'failed' and not self.frames:
            return 'failed', 0, 0
        if self.frames:
            return 'ready', len(self.frames), self.rate
        return ('still' if self.rate <= 0 else 'preparing'), 0, 0

    def activity(self):
        '''
        The preparation in the activity indicator : its percentage, then its end
        '''
        preparation = self.preparation
        translate = self.owner.lang.translate
        if preparation is None or preparation.state == 'cancelled':
            return None
        if preparation.state in ('running', 'paused'):
            done, total = preparation.progress()
            fraction = done / total if total and preparation.phase == 'frames' else None
            text = translate('activity-bganim')
            if fraction is not None:
                text += f" {int(fraction * 100)} %"
            if preparation.state == 'paused':
                text += ' ' + translate('activity-paused')
            return {'text': text, 'fraction': fraction}
        return {'text': translate('activity-bganim-done' if preparation.state == 'done' else 'activity-bganim-failed'),
                'final': True}

    def game(self, playing):
        '''
        A game starts (True) or ends : the preparation paused meanwhile
        '''
        self.in_game = playing
        if self.preparation is not None:
            self.preparation.pause(playing)

    # ------------------------------------------------------------------ the screens of the menus
    def wanted(self, name):
        '''
        This menu shows the video : one is chosen, the menu has no background of its own in the
        files of menus (the drawn effect is shown over its own background)
        '''
        if not self.source:
            return False
        try:
            return self.owner.menus().menu(name).get('background') is None
        except Exception:    # pylint: disable=broad-except
            return True

    def scope(self, name):
        return _Scope(self, name)

    def enter(self, name):
        self.depth += 1
        if self.depth > 1:
            return
        self.scope_ok = self.wanted(name)
        try:
            self.menu_own = self.owner.menus().menu(name).get('background') is not None
        except Exception:    # pylint: disable=broad-except
            self.menu_own = False
        # The background under the effect : the one of this menu, made at its first drawing and
        # kept (the menus keep theirs : drawn again from their copy, the background not asked)
        self.base_key = (name, tuple(self.owner.screen.get_size()), getattr(self.owner.file_class, 'theme_dir', None),
                         self.owner.background, bool(self.source and self.scope_ok and self.still))
        self.base = self.bases.get(self.base_key)
        self.set_mode(self.wanted_mode())

    def scene_shown(self):
        '''
        The animated background drawn on this menu (not on one with a background of its own)
        '''
        return self.scene is not None and not getattr(self, 'menu_own', False)

    def with_effect(self):
        '''
        Something drawn without a video : the effect, an animated background
        '''
        return self.effect_settings[0] != 'none' or self.scene_name != 'none'

    def wanted_mode(self):
        '''
        layer : the video, or the drawn effect over the background of the menu ; still : the
        still picture of the video ; None : the background of the menu as always
        '''
        video = getattr(self, 'scope_ok', False) and bool(self.frames)
        if video or self.with_effect():
            return 'layer'
        if self.source and getattr(self, 'scope_ok', False) and self.still:
            return 'still'
        return None

    def leave(self):
        self.depth -= 1
        if self.depth <= 0:
            self.depth = 0
            self.set_mode(None)

    def set_mode(self, mode):
        owner = self.owner
        if mode != self.mode or (mode == 'layer' and self.use_frames != (getattr(self, 'scope_ok', False) and bool(self.frames))):
            # Backgrounds and buttons kept by the menus : drawn on another background
            owner.menu_backgrounds.clear()
            owner.menu_composites.clear()
        if mode == 'layer':
            if self.mode != 'layer':
                self.real = owner.screen
            self.use_frames = getattr(self, 'scope_ok', False) and bool(self.frames)
            self.make_layer()
            owner.screen = self.layer
            self.redraw = False
            self.effective = self.rate if self.use_frames else self.effect_rate()
        elif self.mode == 'layer':
            owner.screen = self.real
            self.report()
        if mode == 'layer' and self.mode != 'layer':
            self.counted = [time.time(), 0, 0.0]
        self.mode = mode
        if mode != 'layer':
            self.redraw = False

    def effect_rate(self):
        '''
        Frames a second of an effect alone (only its places drawn : light, even on a small Pi)
        '''
        return 30 if self.machine['rate'] >= 15 else 20

    def report(self):
        '''
        How it went, in the log, when a screen of the menus is left (a few seconds at least)
        '''
        counted = getattr(self, 'counted', None)
        if counted is None:
            return
        elapsed = time.time() - counted[0]
        if elapsed >= 5 and counted[1]:
            what = 'video' if self.use_frames else f"{self.scene_name} + {self.effect_settings[0]}"
            self.logs.info(f"Animated background : {counted[1] / elapsed:.1f} i/s for {elapsed:.0f} s, {what} "
                           f"({counted[2] / counted[1] * 1000:.0f} ms a frame, rate {self.effective})")
        self.counted = None

    def make_layer(self):
        size = self.real.get_size()
        if self.layer is None or self.layer.get_size() != size:
            self.layer = pygame.Surface(size, 0, self.real)
            self.keyed = pygame.Surface(size, 0, self.real)
        self.layer.fill(self.key)
        self.keyed.fill(self.key)
        # Blitted whole (the video) : compressed (2 ms instead of 12) ; in small pieces (an effect
        # alone : 80 places a frame), not : each piece of a compressed surface reads it from its top
        self.keyed.set_colorkey(self.key, pygame.RLEACCEL if self.use_frames else 0)
        if self.scene_name != 'none' and (self.scene is None or (self.scene.width, self.scene.height) != size):
            self.scene = ceffects.make_scene(self.scene_name, size, os.path.join(cpaths.ROOT_DIR, 'images', 'boot_logo.png'),
                                             theme_color=self.owner.colorset.get('menu-selected'))
        elif self.scene_name == 'none':
            self.scene = None
        if self.effect_settings[0] != 'none' and (self.effect is None or (self.effect.width, self.effect.height) != size):
            name, color, amount, speed = self.effect_settings
            self.effect = ceffects.make(name, size, color, amount, speed,
                                        theme_color=self.owner.colorset.get('menu-selected'))
        self.last_step = time.time()
        if self.use_frames:
            if self.scaled is None or self.scaled.get_size() != size:
                self.scaled = pygame.Surface(size, 0, 8)
            self.scaled.set_palette(self.palette)
            self.draw_frame(force=True)

    def display_changed(self):
        '''
        The window made again (full screen, size) : the layer the size of the new one
        '''
        if self.mode == 'layer':
            self.real = self.owner.screen
            self.base = None
            self.bases.clear()
            self.make_layer()
            self.owner.screen = self.layer
        self.still_picture = None

    def background(self, rect=None):
        '''
        The background of a menu shown with the animated one (Screen.display_background) : the
        key colour on the layer (its background under the effect kept first), else the still
        picture. False : not this background
        '''
        if self.mode == 'layer':
            if not self.use_frames and self.base is None:
                self.base = self.make_base()
            self.owner.screen.fill(self.key, rect)
            return True
        if self.mode == 'still':
            picture = self.still_surface()
            if picture is None:
                return False
            if rect is None:
                self.owner.screen.blit(picture, (0, 0))
            else:
                self.owner.screen.blit(picture, rect, rect)
            return True
        return False

    def make_base(self):
        '''
        The background the effect is drawn over : the still picture of the video (a Pi too
        small for it), else the background of the menu as always (its own image, the theme).
        Kept for this menu
        '''
        owner = self.owner
        surface = pygame.Surface(self.real.get_size(), 0, self.real)
        while len(self.bases) >= 6:
            self.bases.pop(next(iter(self.bases)))
        self.bases[self.base_key] = surface
        if self.scene_shown():
            surface.blit(self.scene.background(), (0, 0))
            return surface
        if self.source and getattr(self, 'scope_ok', False) and self.still and self.still_surface() is not None:
            surface.blit(self.still_surface(), (0, 0))
            return surface
        screen, mode = owner.screen, self.mode
        owner.screen, self.mode = surface, None
        try:
            owner.display_background()
        finally:
            owner.screen, self.mode = screen, mode
        return surface

    def still_surface(self):
        size = self.owner.screen.get_size()
        if self.still_picture is None or self.still_picture.get_size() != size:
            try:
                picture = pygame.image.load(self.still).convert()
                if picture.get_size() != size:
                    picture = pygame.transform.smoothscale(picture, size)
                self.still_picture = picture
            except Exception:    # pylint: disable=broad-except
                return None
        return self.still_picture

    # ------------------------------------------------------------------ showing
    def under(self):
        '''
        What is under the menu : the frame of the video, else the background of the menu
        '''
        if self.use_frames:
            return self.scaled
        if self.base is None and self.mode == 'layer':
            self.base = self.make_base()
        return self.base

    def compose(self, rect=None):
        '''
        The screen made again from what is under the menu, the effect and the menu (a part)
        '''
        under = self.under()
        if under is not None:
            if rect is None:
                self.real.blit(under, (0, 0))
            else:
                self.real.blit(under, rect, rect)
        if self.scene_shown() and not self.use_frames:
            self.scene.draw(self.real, rect)
        if self.effect is not None:
            self.effect.draw(self.real, rect)
        if rect is None:
            self.real.blit(self.keyed, (0, 0))
        else:
            self.real.blit(self.keyed, rect, rect)

    def present(self, rects=None):
        '''
        What the menu drew (rects, None : everything) sent to the screen over the video
        '''
        if rects is None:
            self.keyed.blit(self.layer, (0, 0))
            self.compose()
            self.activity_over()
            pygame.display.update()
            return
        rects = [pygame.Rect(rect) for rect in rects if rect is not None]
        for rect in rects:
            self.keyed.blit(self.layer, rect, rect)
        for rect in rects:
            self.compose(rect)
        drawn = self.activity_over()
        pygame.display.update(rects + ([drawn] if drawn is not None else []))

    def activity_over(self):
        '''
        The activity indicator over the frame sent (made again from the video, the effect and
        the layer : nothing to restore) ; gone : its place made again. The place to send
        '''
        activities = getattr(self.owner, 'activities', None)
        if activities is None:
            return None
        drawn = activities.draw(self.real)
        if drawn is not None:
            return drawn
        gone = activities.erase_rect()
        if gone is not None:
            self.compose(gone)
        return gone

    def draw_frame(self, force=False):
        '''
        The frame of the moment made the size of the screen (scaled) : True if it changed
        '''
        if not self.frames:
            return False
        index = int((time.time() - self.started) * self.rate) % len(self.frames)
        if index == self.shown and not force:
            return False
        self.shown = index
        pygame.transform.scale(self.frames[index], self.scaled.get_size(), self.scaled)
        return True

    def tick(self, can_redraw=False):
        '''
        At each turn of the reading of the inputs : the next frame when it is time. True : the
        screen shown must be drawn again (the frames are ready, the background changed) ; only
        for a screen which can (can_redraw : it takes 'resize'), the others keep their
        background until the next screen
        '''
        if self.depth == 0:
            return False
        if self.redraw:
            wanted = self.wanted_mode()
            changed = wanted != self.mode or (wanted == 'layer' and (
                self.use_frames != (getattr(self, 'scope_ok', False) and bool(self.frames))
                or (self.effect_settings[0] != 'none') != (self.effect is not None)
                or (self.scene_name != 'none') != (self.scene is not None)))
            if not changed:
                self.redraw = False
            elif can_redraw:
                if self.effect_settings[0] == 'none':
                    self.effect = None
                if self.scene_name == 'none':
                    self.scene = None
                self.base = None
                self.bases.clear()
                self.set_mode(None)
                self.set_mode(wanted)
                return True
        if self.mode != 'layer':
            return False
        now = time.time()
        if now < self.next_frame:
            return False
        started = time.perf_counter()
        elapsed, self.last_step = now - self.last_step, now
        if self.use_frames:
            new_frame = self.draw_frame()
            if not new_frame and self.effect is None:
                return False
            if self.effect is not None:
                self.effect.step(elapsed)
            self.compose()
            self.activity_over()
            pygame.display.update()
        elif (self.effect is not None or self.scene_shown()) and self.under() is not None:
            # Over the background of the menu (or of the scene) : the places changed only
            rects = (self.scene.step(elapsed) if self.scene_shown() else []) + \
                (self.effect.step(elapsed) if self.effect is not None else [])
            for rect in rects:
                self.real.blit(self.base, rect, rect)
            if self.scene_shown():
                self.scene.draw(self.real)
            if self.effect is not None:
                self.effect.draw(self.real)
            for rect in rects:
                self.real.blit(self.keyed, rect, rect)
            drawn = self.activity_over()
            pygame.display.update(rects + ([drawn] if drawn is not None else []))
        else:
            return False
        cost = time.perf_counter() - started
        counted = getattr(self, 'counted', None)
        if counted is not None:
            counted[1] += 1
            counted[2] += cost
        # Slower than its rate (the processor busy elsewhere, a small Pi) : fewer frames shown,
        # the video keeping its speed ; the rate back when it is fast enough again
        top = self.rate if self.use_frames else self.effect_rate()
        self.cost = self.cost * 0.9 + cost * 0.1
        if self.cost > 0.8 / max(1, self.effective) and self.effective > 5:
            self.effective -= 1
        elif self.cost < 0.5 / max(1, self.effective) and self.effective < top:
            self.effective += 1
        self.next_frame = now + 1 / max(1, self.effective)
        return False


class _Scope:
    '''
    with animated.scope(name) : a screen of the menus (before the games)
    '''

    def __init__(self, animated, name):
        self.animated = animated
        self.name = name

    def __enter__(self):
        self.animated.enter(self.name)
        return self.animated

    def __exit__(self, *args):
        self.animated.leave()
        return False
