#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
import ctypes
import glob
import shutil
import signal
import tempfile
import pygame
from pygame.locals import *
import pygame.font
import datetime
import time
import subprocess
from PIL import Image
import threading
from operator import itemgetter
import random
from time import sleep

from include import cpaths
from include import cvideos

#resolution_width_ex = [ 320, 320, 640, 720, 854, 768, 800, 1024, 1280, 1280, 1280, 1400, 1680, 1600, 1920, 1920, 2048, 2048, 2560, 2560, 2560, 2560, 3440, 3840, 4096, 7680 ]
#resolution_height_ex= [ 200, 240, 480, 480, 480, 576, 600, 768 , 720 ,  800, 1024, 1050, 1050, 1200, 1080, 1200, 1080, 1536, 1080, 1440, 1600, 2048, 1440, 2160, 2160, 4320 ]
resolution_width_ex = [ 320, 640, 720, 768, 800, 1024, 1280, 1280, 1280, 1400, 1600, 1920, 2048, 2560, 3440, 3840, 7680 ]
resolution_height_ex= [ 240, 480, 480, 576, 600, 768 , 720 ,  800, 1024, 1050, 1200, 1080, 1536, 1440, 1440, 2160, 4320 ]

# The webcam is held by one ffmpeg, in Motion-JPEG : in YUYV (what pygame.camera reads),
# USB 2 delivers truncated pictures above 640x480 (green rectangles on the photos).
# It writes in RAM (no wear of the SD card), the last seconds only :
#   seg_<epoch>.mkv   one second each, pictures of the webcam copied (never decoded) and
#                     sound : the full size clips (archive, Google Drive)
#   last.jpg          the last picture, complete : photos and preview
#   live_<n>.ts       one second each, encoded at once at SHOWN_WIDTH x SHOWN_HEIGHT, with
#                     the flips and a filter : the clips shown are these files put end to
#                     end (MPEG-TS), ready as soon as the last second is recorded. Starting
#                     ffmpeg to encode them afterwards took 0.74 s each time on a Pi 3
# Measured on a Pi 3 (1280x960, 30 i/s, sound) : 22 % of a core without the live clips
RECORD_DIR = '/dev/shm/raspydarts-camera'
# A clip starts this long before the event : the dart is in it, not only what follows
CLIP_BEFORE = 1
# Size of the clips shown
SHOWN_WIDTH = 640
SHOWN_HEIGHT = 480
# The last picture is older than this : ffmpeg does not deliver any more
LAST_PICTURE_MAX_AGE = 1.0
# Messages of ffmpeg
LOG_FILE = os.path.join(cpaths.ROOT_DIR, 'logs', 'camera.log')
# Tried in this order until ffmpeg keeps running : (sound, live clips encoder)
LEVELS = ((True, 'h264_v4l2m2m'), (False, 'h264_v4l2m2m'), (False, 'libx264'), (True, None), (False, None))
# The H.264 encoder of the Pi stopped answering : recording without live clips from
# LEVELS[STALLED_LEVEL], clips encoded by the processor (see encode_clip)
STALLED_LEVEL = 3
# The last picture is older than this while ffmpeg runs : ffmpeg is stuck
STALLED_AFTER = 4
# Its first picture is awaited this long after its start : 1.5 s on a Pi 3 at rest, 2.7 s with
# the sound of the webcam, more while the game runs. With 4 s, ffmpeg was killed just before its
# first picture, then again and again : no picture at all, « stuck » in the log
FIRST_PICTURE_AFTER = 10


def _die_with_parent():
    '''
    In the child, before ffmpeg starts : killed if the game is gone (killed, crashed),
    else it keeps the webcam busy
    '''
    try:
        ctypes.CDLL('libc.so.6').prctl(1, signal.SIGTERM)    # PR_SET_PDEATHSIG
    except OSError:
        pass


class Recorder:
    '''
    The ffmpeg which holds the webcam, shared by all the Camera objects : only one
    process can open the device. Each user (the game, the setup menu) asks for it with
    its settings ; the last asking wins, the one remaining is restored on release.
    '''
    def __init__(self):
        self.process = None
        self.settings = None
        self.users = {}
        self.logs = None
        self.lock = threading.RLock()
        self.cleaner = None
        self.level = 0
        self.started = 0
        self.started_at = 0
        self.confirmed = False
        # Increased at each game : a game which ends does not stop the next one
        self.game = 0
        # The encoder of the Pi stopped answering (its driver crashed) : until a restart
        self.encoder_stalled = False
        # Launch to try again : (level, when), failures at the current level, stuck
        # ffmpeg killed but not gone yet
        self.retry = None
        self.attempts = 0
        self.dying = None

    def need(self, user, settings, logs):
        '''
        settings : (device, width, height, fps, seconds kept, filter of the live clips, flips,
        live clips wanted)
        '''
        with self.lock:
            self.logs = logs
            self.users[user] = settings
            if self.process is None or self.process.poll() is not None or self.settings != settings:
                self.start(settings)

    def release(self, user):
        with self.lock:
            self.users.pop(user, None)
            if not self.users:
                self.stop()
            else:
                remaining = list(self.users.values())[-1]
                if remaining != self.settings:
                    self.start(remaining)

    def command(self, settings, level):
        device, width, height, fps, _kept, live_filter, flips, live = settings
        sound, live_encoder = LEVELS[level]
        if not live:
            live_encoder = None
        command = ['ffmpeg', '-nostdin', '-loglevel', 'error',
                   '-f', 'v4l2', '-input_format', 'mjpeg', '-video_size', f'{width}x{height}',
                   '-framerate', str(fps), '-timestamps', 'mono2abs', '-thread_queue_size', '64',
                   '-i', device]
        if sound:
            command += ['-f', 'alsa', '-thread_queue_size', '1024', '-ac', '1', '-i', 'default']
        if live_encoder is not None:
            # Fast scaling and the filter laid in YUV : 83 % of a core on a Pi 3, 146 % with
            # the default scaling and an RGB overlay (decoding alone takes 63 %)
            graph = (f"[0:v]scale={SHOWN_WIDTH}:{SHOWN_HEIGHT}:flags=fast_bilinear"
                     + ''.join(f',{flip}' for flip in flips) + ",format=yuv420p")
            if live_filter is not None:
                graph += (f"[s];movie={RECORD_DIR}/live_filter.png,scale={SHOWN_WIDTH}:{SHOWN_HEIGHT},"
                          f"format=yuva420p[f];[s][f]overlay=format=yuv420[live]")
            else:
                graph += "[live]"
            command += ['-filter_complex', graph]

        command += ['-map', '0:v', '-c:v', 'copy']
        if sound:
            command += ['-map', '1:a', '-c:a', 'pcm_s16le']
        command += ['-f', 'segment', '-segment_time', '1', '-segment_atclocktime', '1',
                    '-strftime', '1', '-reset_timestamps', '1', f'{RECORD_DIR}/seg_%s.mkv']
        # mjpeg2jpeg : the pictures of webcams lack the tables a JPEG file needs
        command += ['-map', '0:v', '-c:v', 'copy', '-bsf:v', 'mjpeg2jpeg', '-f', 'image2',
                    '-update', '1', '-atomic_writing', '1', f'{RECORD_DIR}/last.jpg']
        if live_encoder is not None:
            command += ['-map', '[live]']
            if sound:
                command += ['-map', '1:a', '-c:a', 'aac', '-b:a', '96k']
            if live_encoder == 'libx264':
                command += ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23']
            else:
                command += ['-c:v', live_encoder, '-b:v', '2M']
            # A keyframe every half second, each with the parameters of the stream (the
            # encoder of the Pi gives them once) : every file can be read alone or after
            # another. Numbered, not named after the clock : with the delay of encoding,
            # two files could get the same second. Their time is their last write (see
            # live_files)
            command += ['-g', str(max(1, fps // 2)), '-bsf:v', 'dump_extra=freq=keyframe',
                        '-f', 'segment', '-segment_time', '1', '-segment_atclocktime', '1',
                        '-segment_format', 'mpegts', f'{RECORD_DIR}/live_%06d.ts']
        return command

    def start(self, settings):
        '''
        Launched without waiting : the supervisor (see clean) launches it again with
        less (no sound : microphone missing or busy ; no live clips : no encoder) if it
        stops at once
        '''
        self.stop()
        os.makedirs(RECORD_DIR, exist_ok=True)
        if settings[5] is not None:
            # Copied under a plain name : the movie filter reads some characters of paths
            shutil.copy(settings[5], f'{RECORD_DIR}/live_filter.png')
        self.settings = settings
        self.retry = None
        self.attempts = 0
        if self.dying is not None and self.dying.poll() is None:
            # A stuck ffmpeg is not gone yet : launched by the supervisor once it is
            self.process = None
        else:
            self.launch(settings, STALLED_LEVEL if self.encoder_stalled else 0)
        if self.cleaner is None:
            # Long lived : ffmpeg dies with the thread which launched it (_die_with_parent)
            self.cleaner = threading.Thread(target=self.clean, daemon=True)
            self.cleaner.start()

    def launch(self, settings, level):
        self.level = level
        self.started = time.monotonic()
        self.started_at = time.time()
        self.confirmed = False
        try:
            # Its messages in a file : a pipe nobody reads would block it once full
            with open(LOG_FILE, 'w') as log:
                self.process = subprocess.Popen(self.command(settings, level), stdin=subprocess.DEVNULL,
                                                stdout=subprocess.DEVNULL, stderr=log,
                                                preexec_fn=_die_with_parent)
        except OSError as ex:
            self.process = None
            self.logs.error(f"Webcam : ffmpeg not started ({ex})")

    def last_error(self):
        try:
            with open(LOG_FILE) as log:
                lines = log.read().strip().splitlines()
            return lines[-1] if lines else ''
        except OSError:
            return ''

    def stop(self):
        process, self.process, self.settings = self.process, None, None
        self.retry = None
        if process is not None:
            # SIGINT : ffmpeg closes its files properly
            process.send_signal(signal.SIGINT)
            try:
                # Time to close the encoder properly : its driver crashed once
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        # The recording only : the clips being made have their own links (clip_*)
        for path in glob.glob(f'{RECORD_DIR}/seg_*.mkv') + glob.glob(f'{RECORD_DIR}/live_*.ts')                 + [f'{RECORD_DIR}/last.jpg']:
            try:
                os.remove(path)
            except OSError:
                pass

    def describe(self):
        sound, live_encoder = LEVELS[self.level]
        return (f"{'with' if sound else 'without'} sound, "
                f"{'live clips by ' + live_encoder if live_encoder else 'no live clips'}")

    def supervise(self):
        '''
        ffmpeg confirmed after 3 seconds ; launched again when it stops at once (twice at
        the same level, 3 seconds apart : a webcam being reset, a microphone busy) then
        with less ; launched again without live clips when it is stuck
        '''
        settings = self.settings
        if settings is None:
            return
        process = self.process
        if process is None:
            if self.dying is not None:
                # The stuck ffmpeg killed holds the webcam until it is really gone (it may
                # take long, stuck in the crashed driver) : launched again 3 seconds after
                if self.dying.poll() is None:
                    return
                self.dying = None
                self.retry = (STALLED_LEVEL, time.monotonic() + 3)
            if self.retry is not None and time.monotonic() >= self.retry[1]:
                level, self.retry = self.retry[0], None
                self.launch(settings, level)
            return
        if self.confirmed:
            if process.poll() is not None:
                # Webcam unplugged... : launched again by the next Camera which needs it
                self.logs.error(f"Webcam : ffmpeg stopped : {self.last_error() or process.returncode}")
                self.process = None
                return
            try:
                picture = os.path.getmtime(f'{RECORD_DIR}/last.jpg')
            except OSError:
                picture = 0
            if picture < self.started_at:
                # No picture of this ffmpeg yet : its first one is awaited longer
                stalled = time.time() - self.started_at > FIRST_PICTURE_AFTER
            else:
                stalled = time.time() - picture > STALLED_AFTER
            if stalled:
                # Stuck : the H.264 encoder of the Pi does not answer any more (its driver
                # crashed after quick restarts). Recorded again without it : photos go on,
                # clips are encoded by the processor
                encoder = LEVELS[self.level][1] is not None
                self.logs.error("Webcam : ffmpeg stuck, recorded again without live clips. "
                                + ("The H.264 encoder of the Pi does not answer : restart the Pi" if encoder
                                   else "No picture from the webcam"))
                self.encoder_stalled = True
                process.kill()
                self.process = None
                self.attempts = 0
                self.dying = process
            return
        if process.poll() is None:
            if time.monotonic() - self.started >= 3:
                self.confirmed = True
                self.attempts = 0
                self.logs.info(f"Webcam recorded by ffmpeg : {settings[1]}x{settings[2]} {settings[3]} i/s, {self.describe()}")
            return
        self.logs.warning(f"Webcam : ffmpeg stopped ({self.describe()}) : {self.last_error() or process.returncode}")
        self.process = None
        if self.attempts < 2:
            self.attempts += 1
            self.retry = (self.level, time.monotonic() + 3)
        elif self.level + 1 < len(LEVELS):
            self.attempts = 0
            self.retry = (self.level + 1, time.monotonic() + 1)
        else:
            # Never given up while needed : after a stuck ffmpeg was killed, the webcam took
            # more than 30 seconds to be usable again (several USB resets)
            self.logs.error("Webcam : not recorded (Motion-JPEG not available at this size ?), "
                            "tried again in 30 seconds")
            self.attempts = 0
            self.retry = (STALLED_LEVEL if self.encoder_stalled else 0, time.monotonic() + 30)

    def clean(self):
        '''
        Thread : supervises ffmpeg, keeps only the last seconds (RAM)
        '''
        while True:
            time.sleep(0.5)
            with self.lock:
                self.supervise()
            settings = self.settings
            if settings is None:
                continue
            limit = time.time() - settings[4]
            old = [path for epoch, path in self.files('seg') if epoch < limit]
            old += [path for _start, end, path in self.live_files() if end < limit]
            for path in old:
                try:
                    os.remove(path)
                except OSError:
                    pass

    def files(self, kind, start=None, end=None):
        '''
        Recorded seconds (epoch, path) covering [start, end], in order
        '''
        found = []
        for path in glob.glob(f'{RECORD_DIR}/{kind}_*.mkv'):
            try:
                epoch = int(os.path.basename(path)[4:-4])
            except ValueError:
                continue
            if start is None or start - 1 < epoch <= end:
                found.append((epoch, path))
        return sorted(found)

    def live_files(self, closed_only=False):
        '''
        Live clips (start, end, path), in order. A file ends at its last write, starts
        at the end of the one before. The last one is being written : left out if closed_only
        '''
        found = []
        for path in sorted(glob.glob(f'{RECORD_DIR}/live_*.ts')):
            try:
                found.append((os.path.getmtime(path), path))
            except OSError:
                pass
        if closed_only:
            found = found[:-1]
        return [(found[i - 1][0] if i > 0 else end - 1.0, end, path) for i, (end, path) in enumerate(found)]

    def running(self):
        return self.process is not None and self.process.poll() is None

    def live(self):
        '''
        Live clips being recorded : not in the setup menu, not once the encoder is stuck
        '''
        return self.running() and LEVELS[self.level][1] is not None and bool(self.settings and self.settings[7])

    def last_picture(self):
        '''
        Path of the last picture, None if it is not fresh
        '''
        path = f'{RECORD_DIR}/last.jpg'
        try:
            if time.time() - os.path.getmtime(path) <= LAST_PICTURE_MAX_AGE:
                return path
        except OSError:
            pass
        return None


RECORDER = Recorder()

# The H.264 encoder of the Pi runs out of memory with several encodings at once : the
# full size clips are made one at a time (the live clips use one encoding all along)
ARCHIVING = threading.Lock()
# Photos and clips are shown one after the other, never on top of each other
SHOWING = threading.Lock()


def show_in_turn(launch, after=None):
    '''
    Thread : waits for what is shown before and for the videos of the game, launches
    (launch returns the process), waits for its end, then calls after (files shown can
    be removed)
    '''
    def run():
        try:
            with SHOWING:
                # Not over an animation of the game (DB, 180...) : after it
                deadline = time.monotonic() + 60
                while cvideos.playing() and time.monotonic() < deadline:
                    sleep(0.1)
                process = launch()
                if process is not None:
                    process.wait()
        finally:
            if after is not None:
                after()
    threading.Thread(target=run, daemon=True).start()


def wait_closed(kind, epoch):
    '''
    The recorded second is complete once the next one exists
    '''
    while not os.path.exists(f"{RECORD_DIR}/{kind}_{epoch + 1}.mkv") and time.time() < epoch + 4:
        sleep(0.05)


def encode_clip(segments, start, duration, size, flips, filter_path, target, logs):
    '''
    Full size clip from the recorded seconds, flipped and with the filter, in H.264 : by
    the encoder of the Pi, by the processor if it has none (Pi 5). One ffmpeg for all :
    starting one takes 0.74 s on a Pi 3
    '''
    folder = os.path.dirname(segments[0])
    list_file = f'{folder}/segments.txt'
    with open(list_file, 'w') as file:
        for path in segments:
            file.write(f"file '{path}'\n")
    width, height = size
    video = flips + ['format=yuv420p']
    inputs = ['-ss', f'{start:.3f}', '-f', 'concat', '-safe', '0', '-i', list_file]
    if filter_path is not None:
        inputs += ['-i', filter_path]
        filters = ['-filter_complex', f"[0:v]{','.join(video)}[v0];[1:v]scale={width}:{height}[png];"
                                      f"[v0][png]overlay,format=yuv420p[v]", '-map', '[v]', '-map', '0:a?']
    else:
        filters = ['-vf', ','.join(video), '-map', '0:v', '-map', '0:a?']
    encoders = [['-c:v', 'h264_v4l2m2m', '-b:v', '4M'], ['-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23']]
    if RECORDER.encoder_stalled:
        encoders = encoders[1:]
    with ARCHIVING:
        for encoder in encoders:
            try:
                # Bounded : a stuck encoder of the Pi would wait for ever
                result = subprocess.run(['nice', '-n', '15', 'ffmpeg', '-nostdin', '-loglevel', 'error', '-y']
                                        + inputs + filters + ['-t', str(duration)] + encoder
                                        + ['-c:a', 'aac', '-b:a', '96k', '-movflags', '+faststart', target],
                                        capture_output=True, text=True, timeout=duration * 12 + 30)
            except subprocess.TimeoutExpired:
                logs.warning(f"Webcam : clip not encoded by {encoder[1]} in time")
                continue
            if result.returncode == 0:
                return True
            logs.warning(f"Webcam : clip not encoded by {encoder[1]} : {result.stderr.strip()[-200:]}")
    return False


#
# Start of Camera Class
#
class Camera:
    def __init__(self, config, display, log, show_in_parametrage=False):
        self.camera = None
        self.update_filter = 0
        self.logs = log
        self.config = config
        self.userDirectory = f"{config.user_dir}"
        self.photo_filter_directory = "images/photo_filter"
        self.theme = str(config.get_value('SectionGlobals', 'colorset'))
        # The game records all along a game ; the setup menu only while it is shown
        self.user = 'setup' if show_in_parametrage else 'game'
        # (date, game) of the last memory taken : QR code of the gallery at the end
        self.last_partie = None
        self.preview = None
        self.preview_time = 0
        self.preview_mtime = 0
        self.display = display
        self.path_of_filter = None
        self.incr_filter = 0
        self.path_of_filters_directory = None
        self.list_of_filter = []
        # Filters already read and scaled, see filter_layer()
        self._filter_layers = {}
        self.init_list_of_filters()
        self.init_var(config.read_file("Camera"), show_in_parametrage)
        self.showing_in_progress = False
        self.qrPopThread = None
        self.qrPopWindow = None
        self.runningQRPop = False
        self.credentialsPath = os.path.join(self.userDirectory, "credentials.json")
        self._uploadToGoogleDrive = None
        try:
            if os.path.exists(self.credentialsPath) and self.upload_cloud:
                from include import ccamera_upload_GoogleDrive
                self._uploadToGoogleDrive = ccamera_upload_GoogleDrive.CameraUploadGoogleDrive(config, self.logs, self.credentialsPath)
            else:
                self.logs.debug(f"No credentials found to upload via Google Drive")
        except Exception as ex:
            self.logs.error(f"Error in ccamera __init__() : {ex}")

    def init_var(self, config_camera, show_in_parametrage=False):
        self.camera_id = str(config_camera['camera_id'])
        self.picture_path = cpaths.usable_dir(config_camera['picture_path'], os.path.join(cpaths.user_home(), 'Pictures'))
        self.video_path = cpaths.usable_dir(config_camera['video_path'], os.path.join(cpaths.user_home(), 'Videos'))
        self.directory_order = int(config_camera['directory_order'])
        self.choice_of_memories = int(config_camera['choice_of_memories'])
        self.pict_res_width = int(config_camera['picture_res_width'])
        self.pict_res_height = int(config_camera['picture_res_height'])
        self.vid_res_width = int(config_camera['video_res_width'])
        self.vid_res_height = int(config_camera['video_res_height'])
        self.flip_horizontal = bool(config_camera['flip_horizontal'] == '1')
        self.flip_vertical = bool(config_camera['flip_vertical'] == '1')
        self.nb_picture = int(config_camera['nb_picture'])
        self.video_duration = int(config_camera['video_duration'])
        self.fps = int(config_camera['fps'])
        self.events = str(config_camera['events'])
        self.upload_cloud = bool(config_camera['upload_cloud'] == '1')
        self.fullscreen = bool(config_camera['fullscreen_pop'] == '1')
        self.duree = int(config_camera['duree_ms'])
        # Photos and clips come from the same recording : the size of the videos (the one
        # the setup menu offers) is used for both
        flips = tuple(f for f, wanted in (('hflip', self.flip_horizontal), ('vflip', self.flip_vertical)) if wanted)
        # Live clips for the game only : the setup menu records again at each change, and
        # quick restarts of the encoder of the Pi crashed its driver
        self.record_settings = (f"/dev/video{self.camera_id}", self.vid_res_width, self.vid_res_height,
                                self.fps, self.video_duration + 3, self.live_filter(), flips, self.user == 'game')
        if RECORDER.users.get(self.user) is not None:
            # Recording (game in progress, setup menu) : new settings applied at once
            if self.user != 'game' or (self.is_connected() and self.choice_of_memories != 0):
                RECORDER.need(self.user, self.record_settings, self.logs)
            else:
                RECORDER.release(self.user)

    def init_list_of_filters(self):
        try:
            files = []
            if self.theme in ('', 'clear', 'dark'):
                self.path_of_filters_directory = f"{self.userDirectory}/{self.photo_filter_directory}"
            else:
                self.path_of_filters_directory = f"{self.userDirectory}/themes/{self.theme}/{self.photo_filter_directory}"
            if os.path.exists(self.path_of_filters_directory):
                files = os.listdir(self.path_of_filters_directory)
                if files:
                    self.list_of_filter = []
                    for f in files:
                        self.list_of_filter.append((f, False))
            else:
                self.list_of_filter = None
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera init_list_of_filters() : {ex}")
        

    def live_filter(self):
        '''
        Filter of the live clips : the first one (photos and archives take them in turn)
        '''
        for name, _shown in sorted(self.list_of_filter or []):
            path = f"{self.path_of_filters_directory}/{name}"
            if os.path.isfile(path):
                return path
        return None

    def is_connected(self):
        try:
            return self.camera_id != '-1' and os.path.exists(f"/dev/video{self.camera_id}")
        except Exception as ex:
            self.logs.error(f"Error in ccamera is_connected() : {ex}")

    def game_start(self):
        '''
        The webcam is recorded during the games only (its light is off in the menus)
        '''
        try:
            RECORDER.game += 1
            self.last_partie = None
            if self.is_connected() and self.choice_of_memories != 0:
                RECORDER.need('game', self.record_settings, self.logs)
        except Exception as ex:
            self.logs.error(f"Error in ccamera game_start() : {ex}")

    def game_end(self):
        '''
        Recording stopped once the clip of the last dart is recorded, unless another
        game started meanwhile
        '''
        game = RECORDER.game

        def later():
            sleep(self.video_duration + 3)
            if RECORDER.game == game:
                RECORDER.release('game')
        threading.Thread(target=later, daemon=True).start()

    def camera_start(self):
        '''
        The setup menu shows the preview : the webcam is recorded while it is shown
        '''
        try:
            if self.is_connected():
                RECORDER.need(self.user, self.record_settings, self.logs)
        except Exception as ex:
            self.logs.error(f"Error in ccamera camera_start() : {ex}")

    def camera_stop(self):
        '''
        Only the setup menu stops : the game records all along
        '''
        try:
            if self.user != 'game':
                RECORDER.release(self.user)
        except Exception as ex:
            self.logs.error(f"Error in ccamera camera_stop() : {ex}")

    def find_camera(self):
        '''
        USB cameras and their sizes available in Motion-JPEG (the only format recorded),
        from v4l2-ctl : pygame.camera.list_cameras() does not tell enough
        Return None if not find
        '''
        try:
            cam_with_resolution = {}
            devices = subprocess.run(['v4l2-ctl', '--list-devices'], capture_output=True, text=True).stdout
            usb = False
            cam_ids = []
            for line in devices.splitlines():
                if not line.startswith(('\t', ' ')):
                    usb = '(usb-' in line
                elif usb and '/dev/video' in line:
                    # The first node of a USB camera is the one which delivers pictures
                    cam_ids.append(line.strip())
                    usb = False

            for device in cam_ids:
                formats = subprocess.run(['v4l2-ctl', '-d', device, '--list-formats-ext'], capture_output=True, text=True).stdout
                resolutions = []
                mjpeg = False
                for line in formats.splitlines():
                    if "]: '" in line:
                        mjpeg = "'MJPG'" in line
                    elif mjpeg and 'Size: Discrete' in line:
                        parts = line.strip().replace("Size: Discrete ", "").split('x')
                        if len(parts) == 2:
                            w, h = int(parts[0]), int(parts[1])
                            if (w, h) not in resolutions:
                                resolutions.append((w, h))
                if resolutions:
                    resolutions = sorted(resolutions, key=itemgetter(0, 1), reverse=True)
                    cam_with_resolution[device.replace('/dev/video', '')] = [(f"{w}x{h}", f"{w}x{h}") for w, h in resolutions]

            return cam_with_resolution

        except Exception as ex:
            self.logs.error(f"Error in ccamera find_camera() : {ex}")

    def resolutions_only_width(self, resolution):
        return int(resolution.split('x')[0])
    

    def resolutions_only_height(self, resolution):
        return int(resolution.split('x')[1])
    

    def resize_camera_image(self, screen, posXecran, posYecran, resWcamera, resHcamera):
        '''
        Resize the image so that it does not overflow the screen
        '''
        try:
            indexWidthRes = -1
            screen_width, screen_height = screen.get_size()
            widthEnd = posXecran + resWcamera
            heightEnd = posYecran + resHcamera
            
            # si on detecte une largeur trop grande alors on reajuste et on modifiera la hauteur
            if widthEnd > screen_width:
                possibleWidth = screen_width - posXecran - 100
                possibleWidth = (possibleWidth - min((possibleWidth - a for a in resolution_width_ex), key = abs))
                indexWidthRes = resolution_width_ex.index(possibleWidth)
            else:
                possibleWidth = resWcamera
                
            # on a deja detecte une largeur trop grande
            if indexWidthRes != -1:
                possibleHeight = resolution_height_ex[indexWidthRes]
            # si on detecte une hauteur trop grande alors on reajuste et on modifiera la largeur
            elif heightEnd > screen_height:
                possibleHeight = screen_height - posYecran - 100
                possibleHeight = (possibleHeight - min((possibleHeight - a for a in resolution_height_ex), key = abs))
                possibleWidth = resolution_height_ex[resolution_height_ex.index(possibleHeight)]
            else:
                possibleHeight = resHcamera
            
            return possibleWidth, possibleHeight
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera resize_camera_image() : {ex}")     
    

    def get_photo_filter(self):
        try:
            path_of_filter = ""
            self.list_of_filters()
            
            if self.list_of_filter:   
                # Find not show
                nb_filter_not_show = list((file[0], file[1]) for file in self.list_of_filter if file[1] == False)
                nb_files = len(nb_filter_not_show)
                rand_file = random.randint(0, nb_files - 1)
                             
                # Test if path or directory always exist (change value dynamically)
                path_of_filter =f"{self.path_of_filters_directory}/{nb_filter_not_show[rand_file][0]}"
                
                # No surprise ?
                if not self.filter_always_exist(path_of_filter):
                    self.list_of_filter.remove(nb_filter_not_show[rand_file])
                    self.get_photo_filter()
                    
                # next(ind for ind, tup in enumerate(self.list_of_filter) if nb_filter_not_show[rand_file][0] in tup)
                self.list_of_filter = self.update_list_of_filter_value(self.list_of_filter, str(nb_filter_not_show[rand_file][0]), True)
                
                # Reinit if all show
                if sum(1 for file in self.list_of_filter if file[1] == False) == 0:
                    newList = []
                    for f, aff in self.list_of_filter:
                        newList.append((f, False))
                    self.list_of_filter = newList
                     
            return path_of_filter if self.list_of_filter else None
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera get_photo_filter() : {ex}")
    

    def list_of_filters(self):
        try:
            filter_finded = []
            if os.path.exists(self.path_of_filters_directory):
                filter_finded = os.listdir(self.path_of_filters_directory)
            #
            if (filter_finded and len(filter_finded) > 0) and not self.list_of_filter:
                self.init_list_of_filters()
            elif (filter_finded and len(filter_finded) > 0) and len(filter_finded) != len(self.list_of_filter):
                self.populate_list_of_filter(filter_finded, self.list_of_filter)
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera list_of_filters() : {ex}")
    

    def filter_always_exist(self, filter_path):
        try:
            return (filter_path != None and os.path.isfile(filter_path))
                
        except Exception as ex:
            self.logs.error(f"Error in ccamera filter_always_exist() : {ex}")
            

    def populate_list_of_filter(self, new_list_of_filter, list_of_filter):
        try:
            for filt in new_list_of_filter:
                list_of_filter.append((filt, False)) if (filt, True) not in list_of_filter and (filt, False) not in list_of_filter else None
                    
        
        except Exception as ex:
            self.logs.error(f"Error in ccamera populate_list_of_filter() : {ex}")
            

    def update_list_of_filter_value(self, list_of_filter, key, value):
        try:
            return [(ke,va) if (ke != key) else (ke, value) for (ke, va) in list_of_filter]
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera update_list_of_filter_value() : {ex}")
            

    def filter_layer(self, path, size):
        '''
        Filter read from its file and scaled only once (the preview used to read it
        again from the SD card for each of its pictures)
        '''
        key = (path, os.path.getmtime(path), int(size[0]), int(size[1]))
        layer = self._filter_layers.get(key)
        if layer is None:
            layer = pygame.transform.scale(pygame.image.load(path).convert_alpha(), (key[2], key[3]))
            if len(self._filter_layers) >= 8:
                self._filter_layers.clear()
            self._filter_layers[key] = layer
        return layer

    def preview_picture(self, width, height, load=True):
        '''
        Last picture recorded, at the size of the preview, flipped and with the filter.
        Made once per new picture, 10 times per second at most (reading a 1280x960 JPEG
        takes 40 ms on a Pi 3, laying the filter as much). Returns (picture, new) ;
        load=False gives the one already made (menu drawn again : no delay)
        '''
        size_changed = self.preview is not None and self.preview.get_size() != (width, height)
        if not load and self.preview is not None and not size_changed:
            return self.preview, False
        path = RECORDER.last_picture()
        if path is None:
            return self.preview, False
        now = time.monotonic()
        try:
            mtime = os.path.getmtime(path)
            if self.preview is not None and not size_changed \
                    and (mtime == self.preview_mtime or now - self.preview_time < 0.1):
                return self.preview, False
            picture = pygame.transform.scale(pygame.image.load(path), (width, height))
            picture = pygame.transform.flip(picture, self.flip_horizontal, self.flip_vertical)

            # The filter changes every 30 pictures (3 seconds)
            if self.incr_filter == 0:
                self.path_of_filter = self.get_photo_filter()
            self.incr_filter = (self.incr_filter + 1) % 30
            # certains aiment supprimer les filtres en cours
            if not self.filter_always_exist(self.path_of_filter):
                self.path_of_filter = self.get_photo_filter()
            if self.path_of_filter is not None:
                picture.blit(self.filter_layer(self.path_of_filter, (width, height)), (0, 0))

            self.preview = picture
            self.preview_mtime = mtime
            self.preview_time = now
            return self.preview, True
        except (OSError, pygame.error):
            return self.preview, False

    def show_camera(self, screen, posX=0, posY=0, resW=0, resH=0, load=True):
        '''
        Display camera. In the waiting loop (load=True) : drawn only when a new picture
        came. Menu drawn again (load=False) : the last one, without sending it to the
        screen (the menu does it)
        '''
        try:
            screen_width, screen_height = screen.get_size()
            if resW == 0:
                resW = self.pict_res_width
            if resH == 0:
                resH = self.pict_res_height
            # centrage automatique si posX = 0 ou posY = 0
            if posX == 0:
                posX = ((screen_width - resW) / 2)
            if posY == 0:
                posY = ((screen_height - resH) / 2)

            # on va eviter tout debordement du preview
            resW, resH = self.resize_camera_image(screen, posX, posY, resW, resH)

            camera_picture = Rect(posX, posY, resW, resH)

            image, new = self.preview_picture(resW, resH, load) if self.is_connected() else (None, False)
            if image is not None:
                if new or not load:
                    # display the preview
                    screen.blit(image, (posX, posY))
                    if load:
                        pygame.display.update(camera_picture)
                return

            pygame.draw.rect(screen, pygame.Color(100, 100, 100), camera_picture)
            pygame.draw.line(screen, (255, 255, 255), (posX, posY), (posX + resW, posY + resH), 10)
            pygame.draw.line(screen, (255, 255, 255), (posX , posY + resH), (posX + resW, posY), 10)
            if load:
                pygame.display.update(camera_picture)

        except Exception as ex:
            self.logs.error(f"Error in ccamera show_camera() : {ex}")

    def folder_tree(self, directory_name, game):
        try:
            if self.directory_order == 0:
                # /home/pi/Pictures_Videos/Date/Jeux/Photos_Videos
                return f"{directory_name}/{game}"
            elif self.directory_order == 1:                
                # /home/pi/Pictures_Videos/Jeux/Date/Photos_Videos
                return f"{game}/{directory_name}"
                
        except Exception as ex:
            self.logs.error(f"Error in ccamera folder_tree() : {ex}")
                

    def action(self, directory_name_of_game, file_name):
        '''
        A photo or a clip of this event. Several events in a row each give theirs :
        the moment is taken at once, the work is done in the background
        '''
        try:
            choice = self.choice_of_memories
            if choice == 0:
                return

            filename = f"{file_name}"
            directory_game_name = f"{directory_name_of_game}"

            if choice == 3:
                choice = random.randint(1, 2)

            if choice == 1:
                # Cheeeeeeze
                self.take_shot(game=directory_game_name, picture_name=filename)
            elif choice == 2:
                # Lights... Camera... ...aaaaannnnnddd Action !
                self.take_video(game=directory_game_name, video_name=filename)

        except Exception as ex:
            self.logs.error(f"Error in ccamera action() : {ex}")

    def take_shot(self, start_stop=True, game="Test", picture_name=None):
        '''
        Here we take a shot in thread mode : the picture of this moment is read now
        '''
        try:
            first = self.read_last_picture()
            threading.Thread(target=self.take_a_shot, args=(start_stop, game, picture_name, first), daemon=True).start()
        except Exception as ex:
            self.logs.error(f"Error in ccamera take_shot() : {ex}")

    def read_last_picture(self):
        '''
        Content of the last picture recorded, None if there is none recent
        '''
        path = RECORDER.last_picture()
        if path is None:
            return None
        with open(path, 'rb') as file:
            return file.read()

    def popup_picture(self, picture, number):
        '''
        The photo at the size it is shown, in PPM : read by the popup (Tk) without being
        decoded, where a PNG of 1280x960 took a second to read
        '''
        screen_width, screen_height = pygame.display.get_surface().get_size()
        if self.fullscreen:
            box = (screen_width, screen_height)
        else:
            # A third of the width, as the clips (640x480 on a 1920x1080 screen)
            box = (screen_width // 3, screen_height // 2)
        width, height = picture.get_size()
        scale = min(box[0] / width, box[1] / height)
        shown = pygame.transform.smoothscale(picture, (int(width * scale), int(height * scale)))
        if self.fullscreen:
            # The popup shows it as it is when it fills the screen
            screen = pygame.Surface(box)
            screen.blit(shown, ((box[0] - shown.get_width()) // 2, (box[1] - shown.get_height()) // 2))
            shown = screen
        path = f"{RECORD_DIR}/popup_{number}.ppm"
        Image.frombytes('RGB', shown.get_size(), pygame.image.tobytes(shown, 'RGB')).save(path)
        return path

    def take_a_shot(self, start_stop=True, game="Test", picture_name=None, first=None):
        '''
        Here we take a shot of the current event : the last picture recorded. Shown
        first, then saved in JPEG (a PNG of 1280x960 took 1.5 s to save on a Pi 3)
        (start_stop : kept for the callers, the webcam is recorded all along)
        '''
        try:
            if self.is_connected():
                # Create folder in Google Drive if it not exists
                if self._uploadToGoogleDrive is not None:
                    if self._uploadToGoogleDrive.get_folder_id() is None:
                        self._uploadToGoogleDrive.create_new_folder_in_google_drive(game)
                nbCapture = 0
                while nbCapture < self.nb_picture:
                    data = first if nbCapture == 0 and first is not None else self.read_last_picture()
                    if data is None:
                        self.logs.error("Webcam : no recent picture, the photo is not taken")
                        return
                    picture_shot = pygame.image.load(io.BytesIO(data), 'last.jpg')
                    nbCapture += 1
                    # flip
                    picture_shot = pygame.transform.flip(picture_shot, self.flip_horizontal, self.flip_vertical)
                    # name and other
                    now = datetime.datetime.now()
                    if picture_name is None:
                        pictureName = now.strftime("%H:%M:%S.%f")
                    else:
                        pictureName = picture_name if nbCapture == 1 else f"{picture_name}_{nbCapture}"
                    directory_name = now.strftime("%d_%m_%Y")
                    directory_default_name = f"{self.picture_path}/{self.folder_tree(directory_name, game)}"
                    if not os.path.exists(directory_default_name):
                        os.makedirs(directory_default_name)

                    path_of_filter = self.get_photo_filter()
                    if path_of_filter is not None:
                        calque = self.filter_layer(path_of_filter, picture_shot.get_size())
                        picture_shot.blit(calque, (0, 0))

                    # Look at me !
                    popup = self.popup_picture(picture_shot, f"{time.monotonic_ns()}")
                    show_in_turn(lambda path=popup: self.show_image_popup(path, fullscreen=self.fullscreen, duree=self.duree),
                                 after=lambda path=popup: os.path.exists(path) and os.remove(path))

                    # save
                    photo = f"{directory_default_name}/{pictureName}.jpg"
                    pygame.image.save(picture_shot, photo)
                    # Its game is shown by the QR code at the end
                    self.last_partie = (directory_name, game)

                    # Load picture in Google Drive
                    if self._uploadToGoogleDrive is not None:
                        if self._uploadToGoogleDrive.get_folder_id() is not None:
                            self._uploadToGoogleDrive.upload_one_picture_video_to_google_drive(photo)

                    if nbCapture < self.nb_picture:
                        # The next photo shows the next moment
                        sleep(0.2)

        except Exception as ex:
            self.logs.error(f"Error in ccamera take_a_shot() : {ex}")

    def take_video(self, game="Test", video_name=None):
        '''
        Here we take a video in thread mode : the moment is the one of the call
        '''
        try:
            self.last_partie = (datetime.datetime.now().strftime("%d_%m_%Y"), game)
            threading.Thread(target=self.take_a_video, args=(None, False, game, video_name, time.time()), daemon=True).start()
        except Exception as ex:
            self.logs.error(f"Error in ccamera take_video() : {ex}")

    def take_a_video(self, screen_with_all_information=None, stop_start=True, game="Test", video_name=None, event=None):
        '''
        Here we take a video of the current event : from CLIP_BEFORE second before it.
        The clip shown is made of the live clips of these seconds put end to end : ready
        as soon as the last second is recorded. The full size one (archive, Google
        Drive) follows in the background.
        (stop_start : kept for the callers, the webcam is recorded all along)
        '''
        # screen_with_all_information : (screen, defaultfontpath, posX_camera, posY_camera, resW, resH)
        clip_dir = None
        try:
            if self.is_connected():
                if event is None:
                    event = time.time()
                before = CLIP_BEFORE
                # 1 second before and 3 after for 5 seconds asked
                after = max(1, self.video_duration - CLIP_BEFORE - 1)
                # warn user (for exemple : parameters screen)
                if screen_with_all_information is not None:
                    resW, resH = self.resize_camera_image(screen_with_all_information[0], screen_with_all_information[2], screen_with_all_information[3],
                                                          self.vid_res_width, self.vid_res_height)
                    camera_picture = Rect(screen_with_all_information[2], screen_with_all_information[3], resW, resH)
                    pygame.draw.rect(screen_with_all_information[0], pygame.Color(100, 100, 100), camera_picture)
                    font = pygame.font.Font(screen_with_all_information[1], 30)
                    text = font.render("Recording in progress..", True, (255, 255, 255))
                    screen_with_all_information[0].blit(text, (screen_with_all_information[2] + 100, screen_with_all_information[3] + 100))
                    pygame.display.update(camera_picture)

                live = RECORDER.live()
                shown_done = threading.Event()
                lives = []
                if live:
                    # The live clip holding the end is complete once a newer one exists
                    while time.time() < event + after + 4 and \
                            not any(end >= event + after for _start, end, _path in RECORDER.live_files(True)):
                        sleep(0.05)
                    lives = [path for start, end, path in RECORDER.live_files(True)
                             if end > event - before and start < event + after]
                # Linked, not read in place : the oldest are removed while the clip is made
                clip_dir = tempfile.mkdtemp(prefix='clip_', dir=RECORD_DIR)
                if lives:
                    # MPEG-TS : files put end to end make one video
                    clip = f"{clip_dir}/shown.ts"
                    with open(clip, 'wb') as output:
                        for path in lives:
                            with open(path, 'rb') as part:
                                shutil.copyfileobj(part, output)
                    # Tadaaaa
                    show_in_turn(lambda: self.show_action_video(clip, SHOWN_WIDTH, SHOWN_HEIGHT), after=shown_done.set)
                else:
                    shown_done.set()

                wait_closed('seg', int(event + after))
                segments = []
                for epoch, path in RECORDER.files('seg', event - before, event + after):
                    segments.append(f"{clip_dir}/{os.path.basename(path)}")
                    os.link(path, segments[-1])
                if not segments:
                    self.logs.error("Webcam : nothing recorded, the video is not made")
                    return

                start = max(0, event - before - int(os.path.basename(segments[0])[4:-4]))
                # The full size one, in the background : the clip directory is its own
                threading.Thread(target=self.archive_video, args=(clip_dir, segments, start, before + after,
                                 game, video_name, shown_done, not lives), daemon=True).start()
                clip_dir = None

        except Exception as ex:
            self.logs.error(f"Error in ccamera take_a_video() : {ex}")
        finally:
            if clip_dir is not None:
                shutil.rmtree(clip_dir, ignore_errors=True)

    def archive_video(self, clip_dir, segments, start, duration, game, video_name, shown_done, show):
        '''
        Thread : the clip at the size of the recording, saved in the videos folder and
        sent to Google Drive (and shown, when there are no live clips)
        '''
        try:
            flips = [f for f, wanted in (('hflip', self.flip_horizontal), ('vflip', self.flip_vertical)) if wanted]
            now = datetime.datetime.now()
            if video_name is None:
                video_name = now.strftime("%H:%M:%S.%f")
            directory_default_name = f"{self.video_path}/{self.folder_tree(now.strftime('%d_%m_%Y'), game)}"
            if not os.path.exists(directory_default_name):
                os.makedirs(directory_default_name)
            output_path = f"{directory_default_name}/{video_name}.mp4"
            if not encode_clip(segments, start, duration, (self.vid_res_width, self.vid_res_height), flips,
                               self.get_photo_filter(), output_path, self.logs):
                return
            if show:
                show_in_turn(lambda: self.show_action_video(output_path))

            # Load video in Google Drive
            if self._uploadToGoogleDrive is not None:
                if self._uploadToGoogleDrive.get_folder_id() is None:
                    self._uploadToGoogleDrive.create_new_folder_in_google_drive(game)
                if self._uploadToGoogleDrive.get_folder_id() is not None:
                    self._uploadToGoogleDrive.upload_one_picture_video_to_google_drive(output_path)
        except Exception as ex:
            self.logs.error(f"Error in ccamera archive_video() : {ex}")
        finally:
            # Once the clip shown has been played
            shown_done.wait(timeout=120)
            shutil.rmtree(clip_dir, ignore_errors=True)

    def show_action_video(self, video_path, width=None, height=None):
        '''
        The clip in the top right corner of the screen. Returns the player (see show_in_turn)
        '''
        try:
            width = width or self.vid_res_width
            height = height or self.vid_res_height
            screen_width, screen_height = pygame.display.get_surface().get_size()
            width, height = min(width, screen_width), min(height, screen_height)
            right_corner_x = screen_width - width

            player = cvideos.find_player()
            if player == 'omxplayer':
                # Over the game, without a window : nothing of the desktop shows up
                command = ['omxplayer', '--win', f'{right_corner_x},0,{screen_width},{height}',
                           '--aspect-mode', 'letterbox', '-o', 'alsa', f'{video_path}']
            elif player is not None:
                command = cvideos.player_command(player, video_path, window=(right_corner_x, 0, width, height))
            else:
                self.logs.warning("No video player found : recorded video is not shown")
                return None

            return subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        except Exception as ex:
            self.logs.error(f"Error in ccamera show_action_video() : {ex}")
            return None

    def show_qr_code(self):   
            try:
                if self._uploadToGoogleDrive is not None:
                    if self._uploadToGoogleDrive.get_folder_id() is not None:
                        qrPop = self._uploadToGoogleDrive.get_qrcode_to_new_google_drive_folder()
                        if qrPop is not None:
                            self.show_qr_popup(qrPop)
                elif self.last_partie is not None:
                    # The page of this game in the gallery of the borne (see cgallery)
                    from include import cgallery
                    import qrcode
                    # Hash of the password, set on the gallery screen (see Screen.gallery_menu)
                    stored = str(self.config.config.get('Gallery', {}).get('password', '')).strip()
                    url = cgallery.address(cgallery.local_ip(), cgallery.partie_id(*self.last_partie), stored)
                    picture = qrcode.make(url)
                    self.show_qr_popup(picture.get_image() if hasattr(picture, 'get_image') else picture)
                        
            except Exception as ex:
                self.logs.error(f"Error in ccamera show_qr_code() : {ex}") 

    def show_qr_code_for_pictures_videos(self):
            try:
                threading.Thread(target=self.show_qr_code, daemon=True).start()

            except Exception as ex:
                self.logs.error(f"Error in ccamera get_qr_code_for_pictures_videos() : {ex}")
       

    def show_image_popup(self, image_path, fullscreen=False, duree=5000):
        """
        Affiche une image en popup via subprocess
        """
        try:
            if not os.path.exists(image_path):
                self.logs.error(f"Image path does not exist: {image_path}")
                return
            
            popup_script = None
            possible_paths = [
                os.path.join(os.path.dirname(__file__), 'cpopup_manager.py'),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cpopup_manager.py'),
                os.path.join(cpaths.ROOT_DIR, 'include', 'cpopup_manager.py')
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    popup_script = path
                    break
            
            if not popup_script:
                self.logs.error("cpopup_manager.py not found")
                return
            
            cmd = [
                'python3',
                popup_script,
                'image',
                image_path,
                'true' if fullscreen else 'false',
                str(duree)
            ]
            
            # Lancer en arrière-plan (non-bloquant) : renvoyé pour show_in_turn
            return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera show_image_popup() : {ex}")

    def close_qr_popup(self):
        """
        Ferme le popup QR code
        """
        try:
            if self._uploadToGoogleDrive is not None:
                self._uploadToGoogleDrive.reinit_folder_id()
        except Exception as ex:
            self.logs.error(f"Error in ccamera close_qr_popup() : {ex}")

    def show_qr_popup(self, qr_img):
        """
        Affiche le QR code en popup via subprocess
        """
        try:
            # Sauvegarder le QR code temporairement
            tmp_path = "/tmp/temp_qr_popup.png"
            qr_display_size = 200
            resized_qr = qr_img.resize((qr_display_size, qr_display_size), resample=Image.BICUBIC)
            resized_qr.save(tmp_path)
            
            popup_script = None
            possible_paths = [
                os.path.join(os.path.dirname(__file__), 'cpopup_manager.py'),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cpopup_manager.py'),
                os.path.join(cpaths.ROOT_DIR, 'include', 'cpopup_manager.py')
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    popup_script = path
                    break
            
            if not popup_script:
                self.logs.error("cpopup_manager.py not found")
                return
            
            cmd = [
                'python3',
                popup_script,
                'qr',
                tmp_path,
                '30000'
            ]
            
            # Lancer en arrière-plan (non-bloquant)
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera show_qr_popup(): {ex}")
