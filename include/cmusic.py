"""
Music player (Lecteur MP3, PR n° 9 of Pascal62110) : the MP3 of a source played in the menus and
during the games (pygame.mixer.music, the channel the sounds of the game do not use), with a
spectrum of 18 bands : ffmpeg decodes the file apart from the sound, a frame every 64 ms, never
more than 2 seconds ahead of the music.

The source (music_source of raspydarts.cfg) :
- empty : the USB keys (/media)
- /a/folder : a folder of the cabinet
- //server/share[/folder] : a share of Windows or of a NAS (SMB) ; its user and password (none :
  guest) in a file of their own, readable by the cabinet only (CREDENTIALS), never in
  raspydarts.cfg nor in the logs
- server:/path : a share NFS
A share is mounted by the cabinet itself (sudo mount, read only) in MOUNT_POINT. The tracks are
searched in a thread : a share or a big key does not stop the screen.
"""

import json
import math
import os
import re
import subprocess
import sys
import threading
import time

import pygame

from include import cpaths

USB_ROOT = '/media'
MOUNT_POINT = '/mnt/raspydarts-musique'
CREDENTIALS = os.path.join(cpaths.user_dir(), 'musique_partage.cred')
MOUNT_TIMEOUT = 20
# A key or a share of several thousands of files : the first ones only
MAX_TRACKS = 5000
DEFAULT_VOLUME = 35
BANDS = 18
# FFT of 1024 samples at 16 kHz : a frame every 64 ms
RATE, SIZE, FRAME_MS = 16000, 1024, 64
# Messages to the DMD : 10 a second at most
DMD_DELAY = 0.1


def normalized(source):
    '''
    The source as kept : smb://server/share and \\\\server\\share written //server/share
    '''
    source = str(source or '').strip()
    if source.startswith('\\\\'):
        source = source.replace('\\', '/')
    if source.lower().startswith('smb://'):
        source = '//' + source[6:]
    return source.rstrip('/') if len(source) > 1 else source


def kind_of(source):
    '''
    usb (nothing), smb (//server/share), nfs (server:/path) or folder (/a/folder)
    '''
    source = normalized(source)
    if not source:
        return 'usb'
    if source.startswith('//'):
        return 'smb'
    if re.match(r'^[^/\s]+:/', source):
        return 'nfs'
    return 'folder'


def level(value):
    '''
    Amplitude of a band -> 0..1 (from -70 dB to -10 dB)
    '''
    return max(0.0, min(1.0, (20.0 * math.log10(max(1e-8, value)) + 70.0) / 60.0))


class MusicPlayer:
    '''
    The tracks of the source, their playing and their spectrum. Made once (Screen.music_player) :
    the music goes on when its screen is left
    '''

    def __init__(self, config, logs, dmd):
        self.config = config
        self.logs = logs
        self.dmd = dmd
        self.lock = threading.RLock()
        self.tracks = []
        self.index = -1
        self.paused = False
        self.playing = False
        self.volume = self.saved_volume()
        # Translation keys : status of the search of the tracks, error of the playing
        self.status = 'music-searching'
        self.error = ''
        self.artist = ''
        self.title = ''
        self.scan_generation = 0
        self.generation = 0
        self.process = None
        self.frames = {}
        self.peaks = [0.0] * BANDS
        self.draw_time = time.monotonic()
        self.dmd_time = 0.0
        self.dmd_sent = None
        self.dmd_error_time = 0.0
        threading.Thread(target=self.worker, daemon=True).start()

    # ----- Source -----

    def source(self):
        return normalized(self.config.get_value('SectionGlobals', 'music_source', False) or '')

    def kind(self):
        return kind_of(self.source())

    def saved_volume(self):
        try:
            return max(0, min(100, int(self.config.get_value('SectionGlobals', 'music_volume', False))))
        except (TypeError, ValueError):
            return DEFAULT_VOLUME

    def save_volume(self):
        if self.volume != self.saved_volume():
            self.config.set_value('SectionGlobals', 'music_volume', self.volume)
            self.config.write_file()

    def user(self):
        '''
        User of the share SMB ('' : guest)
        '''
        try:
            with open(CREDENTIALS, encoding='utf-8') as file:
                for line in file:
                    if line.startswith('username='):
                        return line[9:].rstrip('\n')
        except OSError:
            pass
        return ''

    def set_source(self, source, user='', password=''):
        '''
        A new source : kept in raspydarts.cfg (its user and password apart), the music of the
        former one stopped, its share unmounted, the tracks searched again
        '''
        source = normalized(source)
        if source != self.source() or kind_of(source) == 'smb':
            # The same folder chosen again : the music goes on (a share : its user may change)
            with self.lock:
                self.action('stop')
                self.tracks = []
                self.index = -1
        try:
            if kind_of(source) == 'smb' and user:
                # Created readable by the cabinet only, before anything is written in it
                descriptor = os.open(CREDENTIALS, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                with os.fdopen(descriptor, 'w', encoding='utf-8') as file:
                    file.write(f"username={user}\npassword={password}\n")
            elif os.path.exists(CREDENTIALS):
                os.remove(CREDENTIALS)
        except OSError as error:
            self.logs.error(f"Music : user of the share not kept ({error})")
        self.config.set_value('SectionGlobals', 'music_source', source)
        self.config.write_file()
        self.logs.info(f"Music : source {kind_of(source)} {source}")
        self.refresh()

    def refresh(self):
        '''
        The tracks searched again (a key plugged since...), in a thread
        '''
        with self.lock:
            self.scan_generation += 1
            self.status = 'music-searching'
            generation = self.scan_generation
        threading.Thread(target=self.scan, args=(generation,), daemon=True).start()

    def scan(self, generation):
        source = self.source()
        kind = kind_of(source)
        if kind in ('smb', 'nfs'):
            root = self.mount(source, kind)
            if root is None:
                self.found(generation, [], 'music-share-failed')
                return
        else:
            if os.path.ismount(MOUNT_POINT):
                self.unmount()
            root = USB_ROOT if kind == 'usb' else source
        if not os.path.isdir(root):
            self.found(generation, [], 'music-folder-missing')
            return
        tracks = []
        for base, folders, names in os.walk(root):
            if generation != self.scan_generation:
                return
            # Hidden folders (.Trash...) left aside, the others in the order of their names
            folders[:] = sorted((folder for folder in folders if not folder.startswith('.')), key=str.casefold)
            tracks.extend(os.path.join(base, name) for name in names
                          if name.lower().endswith('.mp3') and not name.startswith('.'))
            if len(tracks) >= MAX_TRACKS:
                self.logs.warning(f"Music : more than {MAX_TRACKS} tracks in {root}, the first ones kept")
                break
        tracks = sorted(tracks[:MAX_TRACKS], key=str.casefold)
        self.found(generation, tracks, 'music-ready' if tracks else 'music-none')

    def found(self, generation, tracks, status):
        with self.lock:
            if generation != self.scan_generation:
                return
            current = self.tracks[self.index] if 0 <= self.index < len(self.tracks) else None
            self.tracks = tracks
            self.index = tracks.index(current) if current in tracks else -1
            self.status = status
        self.logs.info(f"Music : {len(tracks)} tracks ({self.kind()})")

    def mount(self, source, kind):
        '''
        The share mounted, read only, in MOUNT_POINT : the folder of the tracks, None : failed
        '''
        self.unmount()
        subprocess.run(['sudo', '-n', 'mkdir', '-p', MOUNT_POINT], capture_output=True, timeout=10, check=False)
        folders = []
        if kind == 'smb':
            parts = [part for part in source[2:].split('/') if part]
            if len(parts) < 2:
                self.logs.warning(f"Music : {source} is not //server/share")
                return None
            device = f"//{parts[0]}/{parts[1]}"
            folders = parts[2:]
            options = ['ro', f'uid={os.getuid()}', f'gid={os.getgid()}', 'iocharset=utf8',
                       'file_mode=0444', 'dir_mode=0555',
                       f'credentials={CREDENTIALS}' if os.path.isfile(CREDENTIALS) else 'guest']
            command = ['mount', '-t', 'cifs', device, MOUNT_POINT, '-o', ','.join(options)]
        else:
            device = source
            command = ['mount', '-t', 'nfs', device, MOUNT_POINT, '-o', 'ro,soft,timeo=50,retrans=2,nolock']
        # The command is logged : the password is in the file of the credentials only
        self.logs.info(f"Music : {' '.join(command)}")
        try:
            result = subprocess.run(['sudo', '-n', 'timeout', str(MOUNT_TIMEOUT)] + command,
                                    capture_output=True, text=True, timeout=MOUNT_TIMEOUT + 5, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            self.logs.warning(f"Music : {device} not mounted ({error})")
            return None
        if result.returncode != 0:
            self.logs.warning(f"Music : {device} not mounted ({(result.stderr or result.stdout).strip()})")
            return None
        return os.path.join(MOUNT_POINT, *folders)

    def unmount(self):
        if os.path.ismount(MOUNT_POINT):
            subprocess.run(['sudo', '-n', 'umount', '-l', MOUNT_POINT], capture_output=True, timeout=15, check=False)

    # ----- Playing -----

    def state(self):
        '''
        music-paused, music-playing or music-stopped (translation keys)
        '''
        if self.paused:
            return 'music-paused'
        return 'music-playing' if self.playing else 'music-stopped'

    def play(self, index):
        with self.lock:
            if not self.tracks:
                return
            self.playing = False
            self.spectrum_stop()
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(22050, -16, 2)
                self.index = index % len(self.tracks)
                filename = self.tracks[self.index]
                self.artist, self.title = self.names(filename)
                pygame.mixer.music.load(filename)
                pygame.mixer.music.set_volume(self.volume / 100)
                pygame.mixer.music.play()
                self.paused = False
                self.playing = True
                self.error = ''
                generation = self.generation
                threading.Thread(target=self.tags, args=(filename, generation), daemon=True).start()
                threading.Thread(target=self.spectrum_decode, args=(filename, generation), daemon=True).start()
            except Exception as error:    # pylint: disable=broad-except
                self.error = 'music-unreadable'
                self.logs.warning(f"Music : {error}")

    def action(self, action):
        '''
        pause (play when stopped), next, previous, stop, volup, voldown
        '''
        with self.lock:
            if action == 'pause':
                if not self.playing:
                    self.play(max(0, self.index))
                elif self.paused:
                    pygame.mixer.music.unpause()
                    self.paused = False
                else:
                    pygame.mixer.music.pause()
                    self.paused = True
            elif action in ('next', 'previous'):
                self.play(self.index + (1 if action == 'next' else -1))
            elif action == 'stop':
                self.spectrum_stop()
                self.playing = False
                self.paused = False
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    # The file closed : a share can be unmounted
                    pygame.mixer.music.unload()
            elif action in ('volup', 'voldown'):
                self.volume = max(0, min(100, self.volume + (5 if action == 'volup' else -5)))
                if pygame.mixer.get_init():
                    pygame.mixer.music.set_volume(self.volume / 100)

    def worker(self):
        '''
        The next track when one is over, in the menus and during the games
        '''
        while True:
            time.sleep(0.3)
            with self.lock:
                if self.playing and not self.paused and pygame.mixer.get_init() \
                        and not pygame.mixer.music.get_busy():
                    self.play(self.index + 1)

    @staticmethod
    def names(filename):
        '''
        (artist, title) from the name of the file : « 01 - Artist - Title.mp3 »
        '''
        name = os.path.splitext(os.path.basename(filename))[0]
        name = re.sub(r'^\s*\d+[ ._-]+', '', name).replace('_', ' ').strip()
        parts = re.split(r'\s*[-–—]\s*', name, maxsplit=1)
        return (parts[0].strip(), parts[1].strip()) if len(parts) == 2 else ('', name)

    def tags(self, filename, generation):
        '''
        Artist and title of the tags (ffprobe), else those of the name of the file
        '''
        try:
            result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format_tags=artist,title',
                                     '-of', 'json', filename], capture_output=True, timeout=3, check=False)
            if result.returncode != 0:
                return
            tags = json.loads(result.stdout.decode('utf-8')).get('format', {}).get('tags', {})
            tags = {key.lower(): value for key, value in tags.items()}
            with self.lock:
                if generation == self.generation:
                    self.artist = str(tags.get('artist') or self.artist)
                    self.title = str(tags.get('title') or self.title)
        except Exception:    # pylint: disable=broad-except
            pass

    # ----- Spectrum -----

    def spectrum_stop(self):
        self.generation += 1
        process = self.process
        self.process = None
        self.frames = {}
        self.peaks = [0.0] * BANDS
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass

    def spectrum_decode(self, filename, generation):
        '''
        Analysis of the file (the sound played is neither captured nor changed)
        '''
        process = None
        try:
            # numpy is kept away from the game (raspydarts.py : sys.modules) : its loading is long
            # on a Pi 3, the player only needs it
            if 'numpy' in sys.modules and sys.modules['numpy'] is None:
                del sys.modules['numpy']
            import numpy    # pylint: disable=import-outside-toplevel
            window = numpy.hanning(SIZE)
            frequencies = numpy.fft.rfftfreq(SIZE, 1.0 / RATE)
            edges = numpy.geomspace(45.0, 7500.0, BANDS + 1)
            bands = [(frequencies >= edges[i]) & (frequencies < edges[i + 1]) for i in range(BANDS)]
            process = subprocess.Popen(['ffmpeg', '-nostdin', '-v', 'error', '-threads', '1', '-i', filename,
                                        '-vn', '-ac', '1', '-ar', str(RATE), '-f', 's16le', 'pipe:1'],
                                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            with self.lock:
                if generation != self.generation:
                    return
                self.process = process
            frame_number = 0
            while generation == self.generation:
                # Two seconds ahead at most : memory and CPU kept low, during a long pause or a game
                with self.lock:
                    position = max(0, pygame.mixer.music.get_pos()) if pygame.mixer.get_init() else 0
                    ahead = frame_number * FRAME_MS > position + 2000
                if ahead:
                    time.sleep(0.08)
                    continue
                data = process.stdout.read(SIZE * 2)
                if not data:
                    break
                if len(data) < SIZE * 2:
                    data += b'\x00' * (SIZE * 2 - len(data))
                samples = numpy.frombuffer(data, dtype='<i2').astype(numpy.float32) / 32768.0
                amplitude = numpy.abs(numpy.fft.rfft(samples * window)) * (2.0 / window.sum())
                values = tuple(float(amplitude[band].max()) if band.any() else 0.0 for band in bands)
                with self.lock:
                    if generation != self.generation:
                        break
                    self.frames[frame_number] = values
                    while len(self.frames) > 256:
                        del self.frames[min(self.frames)]
                frame_number += 1
        except Exception as error:    # pylint: disable=broad-except
            self.logs.warning(f"Music : no spectrum ({error})")
        finally:
            if process is not None:
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                if process.stdout is not None:
                    process.stdout.close()
            with self.lock:
                if self.process is process:
                    self.process = None

    def levels(self):
        '''
        The bands now (0..1 each), all 0 when nothing is played
        '''
        with self.lock:
            frame = None
            if self.playing and not self.paused and pygame.mixer.get_init():
                position = pygame.mixer.music.get_pos()
                index = int(max(0, position) / FRAME_MS)
                if position >= 0:
                    frame = self.frames.get(index)
                    if frame is None and self.frames:
                        nearest = min(self.frames, key=lambda number: abs(number - index))
                        if abs(nearest - index) <= 8:
                            frame = self.frames[nearest]
            return [level(value) for value in frame] if frame is not None else [0.0] * BANDS

    def draw_spectrum(self, surface, rect):
        '''
        Bars of LED segments, and a mark of the peak falling slowly
        '''
        now = time.monotonic()
        elapsed = min(0.5, now - self.draw_time)
        self.draw_time = now
        values = self.levels()
        segments = 12
        step_x = rect.width / BANDS
        step_y = rect.height / segments
        for column, value in enumerate(values):
            peak = max(value, self.peaks[column] - elapsed * 1.8)
            self.peaks[column] = peak
            for segment in range(segments):
                color = (55, 220, 90) if segment < 7 else (250, 200, 45) if segment < 10 else (245, 65, 45)
                if segment >= int(round(value * segments)):
                    color = tuple(int(component * .13) for component in color)
                cell = pygame.Rect(rect.x + int(column * step_x), rect.bottom - int((segment + 1) * step_y),
                                   max(1, int(step_x) - 3), max(1, int(step_y) - 2))
                pygame.draw.rect(surface, color, cell)
            if peak > .025:
                pygame.draw.rect(surface, (245, 240, 185),
                                 (rect.x + int(column * step_x), rect.bottom - max(2, int(peak * rect.height)),
                                  max(1, int(step_x) - 3), 2))

    # ----- DMD -----

    def send_dmd(self, active=True):
        '''
        The track, its state and its bands to the DMD (music|{...}) while the screen is shown
        '''
        now = time.monotonic()
        if active and now - self.dmd_time < DMD_DELAY:
            return
        self.dmd_time = now
        try:
            if not active:
                message = 'music|{"active":false}'
            else:
                data = {'active': True, 'artist': self.artist[:120], 'title': self.title[:160],
                        'bands': [int(round(100 * value)) for value in self.levels()],
                        'state': {'music-paused': 'Pause', 'music-playing': 'Lecture'}.get(self.state(), 'Arret')}
                message = 'music|' + json.dumps(data, ensure_ascii=True, separators=(',', ':'))
            # The same message again (stopped, paused) : not sent
            if message != self.dmd_sent:
                self.dmd.send(message)
                self.dmd_sent = message
        except Exception as error:    # pylint: disable=broad-except
            # The player is still used when the DMD is not reached
            if now - self.dmd_error_time > 10:
                self.dmd_error_time = now
                self.logs.warning(f"Music : DMD ({error})")
