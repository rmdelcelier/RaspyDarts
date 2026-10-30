# -*- coding: utf-8 -*-
import os
import os.path

import threading
from datetime import datetime

import sys
# Randomize player names / and create a random game name / ...
import random
# Run external commands (shell)
import subprocess
# Make hard calculation
import math
# For file list
import glob
# String to dict
import ast
# Reg exp
import re
# For personnalisation
import importlib
# For debug
import time

import shutil
import json
# For IP addresses
from netifaces import interfaces
from netifaces import ifaddresses
from netifaces import AF_INET
#from PIL import Image
from threading import Thread
from functools import lru_cache
from collections import OrderedDict
from itertools import chain

import pygame
from pygame.locals import *
from include.ColorSets import *

from include import cpaths
from include import ccamera
from include import ccoins
from include import cmenus
from include import cfonts
from include import cmenustyle
from include import cfavorites

try:
    from include import cqrcode
    QRCODE = True
except:
    QRCODE = False

from PIL import Image, ImageOps 

ENTER_KEYS = ['enter', 'BTN_GAMEBUTTON', 'BTN_VALIDATE', 'SB', 'DB', 'BTN_NEXTPLAYER']
ESCAPE_KEYS = ['escape', 'BTN_BACK', 'BTN_CANCEL']
MINUS_KEYS = ['-', 'BTN_MINUS', 'minus', 'S13']
PLUS_KEYS = ['+', 'BTN_PLUS', 'add', 'plus', 'S10']
UP_KEYS = ['up', 'BTN_UP', 'S20']
DOWN_KEYS = ['down', 'BTN_DOWN', 'S3']
LEFT_KEYS = ['left', 'BTN_LEFT', 'S11']
RIGHT_KEYS = ['right', 'BTN_RIGHT', 'S6']
DIRECTION_KEYS = UP_KEYS + DOWN_KEYS + LEFT_KEYS + RIGHT_KEYS
BACK_KEYS = ['backspace', 'BTN_BACK', 'S16']
SAVE_KEYS = ['save', 'S2']    #BTN_NEXTPLAYER
EXTRA_KEYS = ['BTN_CPTPLAYER', '/', 'S15']
CONTINUE_KEYS = ['continue', 'BTN_NEXTPLAYER', 'S2']
BACKUP_KEYS = ['backup', 'BTN_GAME_BUTTON', 'S2']
CLEAN_KEYS = ['clean', 'BTN_GAMEBUTTON']
TAB_KEYS = ['tab', 'shake']
VOLUME_UP_KEYS = ['+', 'BTN_PLUS', 'BTN_VOLUME_UP', 'VOLUME-UP', 'S14']
VOLUME_DOWN_KEYS = ['-', 'BTN_MINUS', 'BTN_VOLUME_DOWN', 'VOLUME-DOWN', 'S8']
VOLUME_MUTE = ['BTN_VOLUME_MUTE', 'VOLUME-MUTE', 'S7']

# The game behind a question : its colours multiplied by this
QUESTION_VEIL = (70, 70, 70)
BTN_CHECK = 1
BTN_CHOICE = 2
# Menus whose background and title are kept (a screen : 4 to 8 MB)
MENU_BACKGROUNDS = 4
BTN_VALUE = 3
BTN_LOGO = 4
BTN_DROPDOWN = 5

def debug(func):
    def wrapper(*args, **kargs):
        print(f"[DEBUG] {datetime.now()} - Calling {func.__name__} with args:{args}, kargs={kargs}", flush=True)
        start = time.perf_counter()
        result = func(*args, **kargs)
        duration = time.perf_counter() - start
        print(f"[DEBUG] {datetime.now()} - Result of {func.__name__} is {result}")
        print(f"[DEBUG] {datetime.now()} - {func.__name__} took {int(duration * 1000)} ms")
        return result
    return wrapper
     
# Rounded corners and accurate transparency need pygame 2. The test was written for the
# version 2.0.0 only : with a more recent one, buttons lost their rounded corners
PYGAME2 = pygame.version.vernum[0] >= 2

# Size of the audio buffer, in samples (about 0.1 second)
MIXER_BUFFER = 4096

def intro_is_playing():
    '''
    True while the intro video launched when the session opens (scripts/Intro.sh) is playing
    '''
    try:
        return subprocess.call(['pgrep', '-f', 'scripts/Intro.sh'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
    except OSError:
        return False

def intro_over_screen():
    '''
    True if the intro video is played by omxplayer : on a layer of the firmware, above the
    whole screen (as on Buster). The game is displayed normally behind it.
    '''
    return shutil.which('omxplayer') is not None

def with_look(name):
    '''
    A screen whose buttons come from the game (games, options, players, wizard) : its look
    is the one the files of menus give to the menu of this name (docs/menu/menus.md, 7.6)
    '''
    def decorate(method):
        def run(self, *args, **kwargs):
            return self.run_with_look(name, method, *args, **kwargs)
        run.__name__ = method.__name__
        run.__doc__ = method.__doc__
        return run
    return decorate

# Sent by the background task watching the intro video when it is finished : the main loop
# then shows the window of the game (see craspberry.keyboard_mouse)
INTRO_END_EVENT = pygame.event.custom_type() if hasattr(pygame.event, 'custom_type') else pygame.USEREVENT + 30

class Screen(pygame.Surface):
    '''
    Class for display
    '''
    def __init__(self, config, logs, File, lang, rpi, dmd, video_player, image_player, Font=None, random_speed=False, wait_event_time=None, t_event=None):
        # Init
        self.gamepath = os.getcwd()
        self.backupscript = f"{self.gamepath}/scripts/Backup.sh"
        self.background = None
        self.theme_font = None
        self.file_class = File

        self.ips = self.get_ips()

        #
        self.netgamename = None
        self.netgamecreator = None
        # Store config in local value
        self.logs = logs
        self.lang = lang    # Import language values
        self.line_height = None    # Depends of player number - calculated later
        self.config = config
        self.colorsets = {}
        # Image cache (speed up pygame image load process
        self.games = {}
        self.imagecache = {}
        self.tinted_backgrounds = {}
        self.pristine_background = None
        # For drawing a dart board
        self.targets = {20: 1, 1: 2, 18: 3, 4: 4, 13: 5, 6: 6, 10: 7, 15: 8, 2: 9, 17: 10, 3: 11, 19: 12, 7: 13,
                         16: 14, 8: 15, 11: 16, 14: 17, 9: 18, 12: 19, 5: 20}
        # Set default Sound Volume (percent)
        try:
            self.sound_volume = int(self.config.get_value('SectionGlobals', 'soundvolume'))
        except:
            self.sound_volume = 50
        self.random_speed = random_speed
        self.old_volume = self.sound_volume
        self.sound_multiplier = 100

        # Audio buffer : with the default one (a few milliseconds), sounds are chopped and
        # cut as soon as the game is busy
        pygame.mixer.pre_init(44100, -16, 2, MIXER_BUFFER)

        # While the intro video is playing, the audio output is not opened : this chops
        # the sound of the video. It is opened as soon as the video is finished.
        self.hidden = False
        self.intro = intro_is_playing()
        self.audio_deferred = self.intro and not intro_over_screen()
        if self.audio_deferred:
            pygame.display.init()
            pygame.font.init()
        else:
            pygame.init()
        # Used resolution
        self.res = {}
        # Minimal resolution
        self.resmin = {}

        # Create resolution prameters
        self.fullscreen = self.config.get_value('SectionGlobals', 'fullscreen')

        # create_screen Init or toggle screen
        self.create_screen()
        # Choose color set
        self.init_colorset()
        # Define constants - first without the required nb of players
        self.define_constants(Font = Font)
        # Define a boolean value to know if teaming is active (default is inactive)
        self.teaming = False
        self.selectedgame = ''
        #
        self.session_players = {}

        # Init Clickable zone
        self.click_zones = {}

        # Init menu item types
        self.selected = None
        # Margin
        self.margin = int(self.res['y'] / 200)
        self.rpi = rpi
        if rpi is not None:
            # Coin acceptor : a coin shows the credits at once
            rpi.on_coins = self.coins_redraw
        if self.intro:
            # The target is read once the intro video is finished and the menu shown
            rpi.target_enabled = False
            rpi.set_intro_end(INTRO_END_EVENT, self.show)
            Thread(target=self.watch_intro, daemon=True).start()
        self.dmd = dmd
        self.video_player = video_player
        self.image_player = image_player
        self.game_options = []

        self.game_background = None
        # The surface game_background is copied in (see save_background)
        self.background_buffer = None

        self.wait_event_time = wait_event_time
        self.t_event = t_event
        self.thread = None
        self.rects = []
        self.blinktime = int(self.config.get_value('SectionGlobals', 'blinktime'))
        self.selected_menu = {}
        # Sounds chosen and decoded before they are played (see prepare_sound)
        self.prepared_sounds = {}
        # Sounds decoded once (see decoded_sound)
        self.kept_sounds = OrderedDict()
        self.kept_sounds_lock = threading.Lock()
        # Background and title of the menus of the files (see run_menu)
        self.menu_backgrounds = {}
        # Buttons of the styles over their piece of background (see run_styled_menu)
        self.menu_composites = {}
        # Screens skipped by a button of the main menu or by start : ('game', 'classic.Cricket'),
        # ('category', 'favoris') or None (see cmenus.Menus.target)
        self.menu_target = None
        # Screen whose look comes from the files (see with_look)
        self.current_look = None
        self.end_of_game_winner = ''
        if QRCODE:
            self.qrcode = cqrcode.Qrcoder()
        else:
            self.qrcode = None
        self.qrlogo = ''
        # QR codes generated (see draw_qrcode)
        self.qrcodes = {}
        self.camera = ccamera.Camera(self.config, self.display, logs, show_in_parametrage=True)

    def set_end_of_game_winner(self, value):
        self.end_of_game_winner = value

    def set_soundmultiplier(self, multiplier):
        self.sound_multiplier = int(multiplier) / 100
        self.logs.debug(f"sound_multiplier is set to {self.sound_multiplier}")

    def set_blinktime(self, value):
        self.blinktime = int(value)

    def reset_mode(self):
        self.blinktime = int(self.config.get_value('SectionGlobals', 'blinktime'))
        self.video_player.level = int(self.config.get_value('SectionGlobals', 'videos'))
        self.image_player.level = int(self.config.get_value('SectionGlobals', 'videos'))

    def blit(self, source, destination, area=None):
        # Something drawn : the background is not intact any more (see blit_rect)
        self.pristine_background = None
        self.blit_screen(self.screen, source, destination, area)

    def blit_screen(self, screen, source, destination, area=None):
        '''
        Blit with alpha blending, except the opaque sources : copied as they are, same
        result, several times faster (pygame is built without NEON on the Pi)
        '''
        opaque = not source.get_flags() & pygame.SRCALPHA and source.get_alpha() is None
        if PYGAME2 and not opaque:
            screen.blit(source, destination, area=area, special_flags=pygame.BLEND_ALPHA_SDL2)
        else:
            screen.blit(source, destination, area=area)

    def save_background(self):
        '''
        To use the game's screen instead of classic background
        '''
        # Grab screen (a copy : blending it took 18 ms on a Pi 3 at each dart). Copied in the
        # same surface each time : creating a new one (screen.copy()) took 22 ms, 9 ms like this
        if self.background_buffer is None or self.background_buffer.get_size() != self.screen.get_size():
            self.background_buffer = pygame.Surface(self.screen.get_size(), 0, self.screen)
        self.background_buffer.blit(self.screen, (0, 0))
        self.game_background = self.background_buffer

    def restore_background(self, refresh=True):
        '''
        To use the game's screen instead of classic background
        '''
        if self.game_background is not None:
            self.blit(self.game_background, (0, 0))
            if refresh:
                self.update_screen()

    def reset_background(self):
        '''
        Go back to original background
        '''
        self.game_background = None

    def init_background(self, background):
        '''
        Init background
        '''
        self.logs.debug(f"Cleaning image cache")
        if self.background is None or self.background != background:
            self.imagecache = {}
            self.tinted_backgrounds = {}
        self.background = background
        self.logs.debug(f"Background is now {self.background}")
        self.set_intro_background(background)

    def mcp_error(self, error):
        '''
        To avoid a violent back to desktop
        '''
        margin = self.res_y / 24
        color = (255,0 ,0)

        self.display_background()
        self.update_screen()

        rect = pygame.Rect(self.res_x / 64, self.res_y / 64, self.res_x  * 62 / 64, self.res_y * 62 / 64)
        self.new_blit_rect2(rect, self.colorset['bg-global'])

        rect = pygame.Rect(self.res_x / 32, self.res_y / 32, self.res_x * 28 / 32, self.res_y / 8)
        self.blit_text2("ATTENTION", rect, color)

        
        rect.y += rect.height * 2 + margin
        rect.height /= 2
        self.blit_text2("Une carte d'extension est déclarée mais n'a pas été détectée", rect, color)

        rect.y += margin * 2
        self.blit_text2("Le jeu va se lancer mais les boutons seront inutilisables.", rect, color)

        rect.y += margin
        self.blit_text2("La cible peut également ne pas fonctionner.", rect, color)

        rect.y += margin
        self.blit_text2("Utilisez la cible pour vous déplacer et arrêter le jeu proprement,", rect, color)

        rect.y += margin
        self.blit_text2("puis corrigez le problème (vérifiez que la carte est bien enfichée)", rect, color)

        rect.y += margin
        self.blit_text2("Et enfin redémarrez le jeu", rect, color)

        rect.y += margin * 2
        self.blit_text2(f"L'erreur est la suivante :", rect, color)

        rect.y += margin
        self.blit_text2(f"{error}", rect, (152, 176, 2))

        rect.y += rect.height * 2 + margin
        self.blit_text2("Appuyez sur la cible pour continuer.", rect, color)

        self.update_screen()
        self.wait_touch()

    def send_cheer(self):
        '''
        Send Cheer to dmd : usefull ??
        '''
        self.dmd.send_text(self.lang.translate('dmd-bestwin'), tempo=2)

    def get_ips(self):
        '''
        Get IP of the rpi
        '''
        ips = []
        for iface in interfaces():
            if iface != 'lo':
                ip = ifaddresses(iface).setdefault(AF_INET, [{'addr': 'None'}])[0]['addr']
                if ip != 'None':
                    ips.append((iface, ip))
        return ips

    def create_screen(self, Toggle=False, newresolution=False, Font=None):
        '''
        Create screen and optionnaly toggle Fullscreen/windowed
        '''

        if newresolution:
            self.imagecache = {}
            self.tinted_backgrounds = {}
        # Toggle if requested
        if self.fullscreen and Toggle:
            self.fullscreen = False
        elif Toggle:
            self.fullscreen = True
        # If toggle screen or resize
        if Toggle:
            # grab information before quitting actual screen
            self.screen = pygame.display.get_surface()    # Get a reference to the currently set display surface
            tmp = self.screen.convert() # change the pixel format of an image ? Can't remember why I do that ;)
            #cursor = pygame.mouse.get_cursor()    # Get the image for the system mouse cursor
            # Bye bye old screen !
            pygame.display.quit()

        if not pygame.display or Toggle:
            # Welcome new screen !
            pygame.display.init()
        # Define resolution
        self.init_resolution(newresolution)
        # Define screen constants (depends on resolution)
        self.define_constants(Font = Font)
        # While the intro video is playing, the game loads behind it, goes up to its menu
        # and plays no sound (it would chop the sound of the video) : like omxplayer on
        # Buster, the menu is there as soon as the video ends. Its window stays hidden until
        # then, else it would cover the video. See show()
        self.hidden = not Toggle and hasattr(pygame, 'HIDDEN') and intro_is_playing() and not intro_over_screen()
        hidden_flag = pygame.HIDDEN if self.hidden else 0
        # Tell pygame it is fullscreen if it is
        if self.fullscreen:
            self.flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
            self.screen = pygame.display.set_mode((0, 0), self.flags | hidden_flag)    # Set fullscreen with actual resolution and depth (X : 32 bits, a depth asked is not followed)
        else:
            self.screen = pygame.display.set_mode((self.res['x'], self.res['y']), pygame.RESIZABLE | hidden_flag) # Start windowed with settings

        # If Toggling, blit the new screen
        if Toggle:
            self.blit(tmp, (0, 0))

        # Get caption back
        pygame.display.set_caption(f'RaspyDarts v.{self.config.pyDartsVersion}')
        # Set pyDarts icon images
        imagefile = self.file_class.get_full_filename('icon', 'images')
        if imagefile is not None:
            iconimage = pygame.image.load(imagefile).convert_alpha()
            pygame.display.set_icon(iconimage)
        else:
            self.logs.warning(f"Unable to load icon image.")
        pygame.key.set_mods(0)    # HACK: work-a-round for a SDL bug??
        #if Toggle:
        #    pygame.mouse.set_cursor(*cursor)    # Duoas 16-04-2007
        self.display = pygame.display

    def init_colorset(self):
        '''
        Init the choosen ColorSet
        '''

        self.choosen_colorset = self.config.get_value('SectionGlobals', 'colorset')
        # The font the theme asks for itself (not the one it gets from the clear theme)
        theme_has_font = False

        try:
            self.colorset = ColorSet[self.choosen_colorset]
        except:
            colorset_file = self.file_class.get_full_filename('Colorset', 'text')
            try:
                colorset_file = self.file_class.get_full_filename('Colorset', 'text')
                if colorset_file is None:
                    raise Exception(f"No Colorset.cfg in {self.file_class.theme_dir}/other")
                self.logs.info(f"Use {colorset_file} for color's customization")
                ColorSet['Colorset'] = self.config.read_colorset(colorset_file)
                self.colorset = ColorSet['Colorset']
                theme_has_font = bool(self.colorset.get('font'))
                for key, value in ColorSet['clear'].items():
                    if key not in self.colorset:
                        self.colorset[key] = value
                    else:
                        self.logs.info(f"Customization : {key} is customized to {value}")
            except Exception as e:
                self.logs.warning("Error during load of custom colorset")
                self.logs.warning(f"Error was {e}")
                self.colorset = ColorSet['clear']

        if self.choosen_colorset != 'clear':
            background = self.file_class.get_full_filename(f'background_{self.choosen_colorset}', 'images')
        else:
            background = None

        if background is None:
            background = self.file_class.get_full_filename('background', 'images')
        self.init_background(background)

        for colorset in ColorSet:
            self.colorsets[colorset] = ColorSet[colorset]

        self.online_icon = self.file_class.get_full_filename('online', 'images')

        try:
            # A theme made on another installation keeps the path it had there
            font = cpaths.relocate(self.colorset['font'])
            if not os.path.isfile(font):
                # Saved there under another name of theme (the sombre theme of the example :
                # /home/pi/.pydarts/themes/remi/font/CompactaBT.ttf) : the font of this name in
                # the theme, else in the game
                name = os.path.basename(str(self.colorset['font']))
                for candidate in (os.path.join(str(getattr(self.file_class, 'theme_dir', '')), 'font', name),
                                  os.path.join(self.config.fontsDir, name)):
                    if os.path.isfile(candidate):
                        font = candidate
                        break
            if os.path.isfile(font):
                self.defaultfontpath = font
                self.colorset['font'] = font
            else:
                self.defaultfontpath = f"{self.config.fontsDir}/{self.colorset['font']}"
            self.logs.info(f"Font defined in your colorset : {self.colorset['font']}")
            if not os.path.isfile(self.defaultfontpath):
                self.logs.warning(f"Font {self.defaultfontpath} not found : default font is used")
                self.defaultfontpath = f"{self.config.fontsDir}/FreeSansBold.ttf"
                # The descriptions of the games open this one too (the path not found stopped the game)
                self.colorset['font'] = self.defaultfontpath
        except Exception as e:
            self.logs.info("No font defined in your colorset")
        self.theme_font = self.defaultfontpath if theme_has_font and os.path.isfile(str(self.defaultfontpath)) else None
        self.use_chosen_font()

    def font_file(self, font):
        '''
        File of a font of the settings : the one of the theme, or in the fonts of the game and of
        ~/.raspydarts
        '''
        if not font:
            return None
        if self.theme_font and os.path.basename(self.theme_font) == str(font):
            return self.theme_font
        return self.file_class.get_full_filename(str(font), 'fonts')

    def use_chosen_font(self):
        '''
        The font of the settings, over the one of the theme : each init_colorset (at the start,
        after a game) put back the font of the theme on the menus, the games using this one
        '''
        font = self.font_file(self.config.get_value('SectionGlobals', 'font', False))
        if font:
            self.defaultfontpath = font
            self.colorset['font'] = font
        cfonts.path = self.defaultfontpath

    def init_resolution(self, newresolution=False):
        '''
        Get best parametered display resolution or best resolution if fullscreen
        Init a dictionnary named "res" which contains x and y display resolutions
        '''
        self.resmin['x'] = 200
        self.resmin['y'] = 100
        if newresolution:
            self.res['x'] = int(newresolution[0])
            self.res['y'] = int(newresolution[1])
            self.logs.debug(f"Using display mode : {self.res['x']}x{self.res['y']}")
        elif self.fullscreen is False:
            self.res['x'] = int(self.config.get_value('SectionGlobals', 'resx'))
            self.res['y'] = int(self.config.get_value('SectionGlobals', 'resy'))
            self.logs.debug(f"Using display mode : {self.res['x']}x{self.res['y']}")
        else:
            infoObject = pygame.display.Info()
            self.res['x'] = infoObject.current_w
            self.res['y'] = infoObject.current_h
            self.logs.debug(f"Ho yeah, going fullscreen : {self.res['x']}x{self.res['y']}")

        # Exit if resolution smaller than minimal size
        if self.res['x'] < self.resmin['x'] or self.res['y'] < self.resmin['y']:
            self.logs.warning(f"Cannot reduce resolution to something smaller than {self.resmin['x']}x{self.resmin['y']}, sorry.")
            self.res['x'] = self.resmin['x']
            self.res['y'] = self.resmin['y']

        self.res_x = self.res['x']
        self.res_y = self.res['y']
        self.mid_x = int(self.res['x'] / 2)
        self.mid_y = int(self.res['y'] / 2)
        self.quart_x = int(self.res['x'] / 4)
        self.quart_y = int(self.res['y'] / 4)
        self.res_x_16 = int(self.res['x'] / 16)
        self.res_y_15 = int(self.res['y'] / 15)
        self.res_y_8 = int(self.res['y'] / 8)
        self.res_y_16 = int(self.res['y'] / 16)

    def blit_rect(self, pos_x, pos_y, width, height, color, border=False, border_color=False, Alpha=None):
        '''
        Display a rect with transparency, with optionnal border
        '''
        if not color:    # If color is not set, put alpha to 100%
            color = self.colorset['message-bg']    # Arbitrary
            Alpha = 0
        if not color:
            return
        if Alpha is None:
            Alpha = self.alpha
        if not border_color:
            border_color = self.colorset['menu-border']

        # Nothing to blend : invisible, or the color as it is (filled, same pixels : a full
        # screen took 19 ms through a surface created, 5 ms filled)
        if Alpha <= 0 or Alpha >= 255:
            rect = (int(pos_x), int(pos_y), int(width), int(height))
            if Alpha >= 255:
                self.pristine_background = None
                self.screen.fill(color, rect)
            if border:
                self.pristine_background = None
                pygame.draw.rect(self.screen, border_color, rect, border)
            return

        # A veil on the whole background just displayed (game screens, at each dart) :
        # blending 1920x1080 pixels took 35 ms on a Pi 3. The result is kept, then copied
        key = None
        if not border and self.pristine_background is not None \
                and (int(pos_x), int(pos_y), int(width), int(height)) == (0, 0) + self.screen.get_size():
            key = (self.pristine_background, tuple(color), Alpha)
            if key in self.tinted_backgrounds:
                self.screen.blit(self.tinted_backgrounds[key], (0, 0))
                self.pristine_background = None
                return

        surface = self.filled_rect(int(width), int(height), tuple(color), Alpha)
        self.blit(surface, (int(pos_x), int(pos_y)))    # (0, 0) are the top-left coordinates
        if border:
            pygame.draw.rect(self.screen, border_color, (int(pos_x), int(pos_y), int(width), int(height)), border)
        if key is not None:
            if len(self.tinted_backgrounds) >= 8:
                self.tinted_backgrounds = {}
            self.tinted_backgrounds[key] = self.screen.copy()

    @lru_cache(maxsize=128)
    def font(self, path, size):
        '''
        Return the font of this file and size. Kept once loaded : creating a font reads and
        parses its file, and texts are drawn with the same fonts over and over
        '''
        return pygame.font.Font(path, size)

    def get_font(self, size):
        '''
        Return the font with size given
        '''
        return self.font(self.defaultfontpath, size)

    @lru_cache(maxsize=2048)
    def scale_text(self, text, width, height, dafont=None, divider=1.5, step=0.1):
        '''
        Return best text size to scale text in a given box size (usefull for responsive design)
        '''
        if dafont is None:
            dafont = self.defaultfontpath
        else:
            dafont = self.file_class.get_full_filename(f'{dafont}', 'fonts')

        while True:
            text_size = int(height / divider)
            font = self.font(f'{dafont}', text_size)
            font_size = font.size(str(text))

            if text_size <= 0:
                self.logs.error(f"Unable to find suitable text size for a box of size {width}x{height} and for text {text}")
                return None

            if font_size[0] < width and font_size[1] < height:
                # Returns Best text size, horizontal space needed to center text, vertical space to center text
                return [text_size, int((width - font_size[0]) / 2), int((height - font_size[1]) / 2), font_size[0], font_size[1]]

            divider += step

    #@debug
    def blit_text2(self, text, rect, color=None, font=None, align='Center', valign='center', margin=True, divider=1.5, alpha=255):
        self.blit_text(text, rect[0], rect[1], rect[2], rect[3], color=color, dafont=font, align=align, valign=valign, margin=margin, divider=divider, Alpha=alpha)
        return rect

    #@debug
    def blit_text(self, text, pos_x, pos_y, width, height, color=None, dafont=None, image=None, align='Center', valign='center', margin=True, divider=1.5, Alpha=255, game=None):
        '''
        Render text in a box, directly at best size
        '''
        if text is None or text == '':
            return
        if divider is None:
            divider = 1.5

        text = str(text)

        if dafont is None:
            dafont = self.defaultfontpath
            
        if color is None:
            color = self.colorset['menu-text-white']

        try:
            text = self.lang.translate(text, game)
        except Exception as e:
            self.logs.warning("Issue in Screen.lit_text method.")
            self.logs.debug(f"Issue is {e}")

        if margin:
            text_margin = self.margin
        else:
            text_margin = 0

        # Display Text
        scaled_text = self.scale_text(text, width - 2 * text_margin, height - 2 * text_margin, divider=divider, dafont=dafont)
        font_path = dafont if dafont == self.defaultfontpath else self.file_class.get_full_filename(dafont, 'fonts')
        if image is None:
            # Render text (the same texts at each dart : rendered once)
            text = self.rendered_text(font_path, scaled_text[0], text, tuple(color), Alpha)
        # Calculate place of text
        if align == 'Center':
            text_x = int(pos_x + (width - scaled_text[3] + text_margin) / 2)
        elif align == 'Left':
            text_x = int(pos_x + text_margin)
        else : # Right
            text_x = int(pos_x + width - scaled_text[3] - 2 * text_margin)

        if valign == 'top':
            text_y = int(pos_y + text_margin)
        else:
            text_y = int(pos_y + scaled_text[2] + text_margin)

        if image != None:
            img = pygame.image.load(image).convert_alpha()
            img.set_alpha(Alpha)
            self.blit(img, [text_x, text_y])
        else:
            # Display text
            self.blit(text, [text_x, text_y])

    @lru_cache(maxsize=128)
    def rendered_text(self, font_path, size, text, color, alpha):
        '''
        Text rendered (never drawn on : shared)
        '''
        surface = self.font(font_path, size).render(text, True, color)
        surface.set_alpha(alpha)
        return surface

    def menu_header(self, text, subtxt=None, centertxt=None):
        '''
        All menus use the same header
        '''
        if self.current_look is not None and centertxt is None:
            # Screen whose look comes from the files : their title and subtitle (text and look)
            name = self.current_look
            title, title_look = self.menu_text_look(name, 'title')
            subtitle, subtitle_look = self.menu_text_look(name, 'subtitle')
            text = title or text
            subtxt = subtitle or subtxt
            if title_look or subtitle_look:
                self.styled_title(name, text, subtxt)
                return
        self.classic_header(text, subtxt, centertxt)

    def classic_header(self, text, subtxt=None, centertxt=None):
        '''
        The header of always : bands of the colours of the theme
        '''
        rect = pygame.Rect(0, int(self.res['y'] / 30), self.res['x'], int(self.res['y'] / 15))

        if self.colorset['menu-header'] is not None:
            self.new_blit_rect2(rect, self.colorset['menu-header'])
        self.blit_text2(text, rect, self.colorset['menu-text'])

        if subtxt:
            rect.y += rect.height
            if self.colorset['menu-header'] is not None:
                self.new_blit_rect2(rect, self.colorset['menu-header'], alpha=255)
            self.blit_text2(subtxt, rect, self.colorset['menu-text'])

        if centertxt is not None:
            rect.y = int(self.res['y'] * 6 / 14)

            if self.colorset['menu-header'] is not None:
                self.new_blit_rect2(rect, self.colorset['menu-header'], alpha=255)
            self.blit_text2(centertxt, rect, self.colorset['menu-text'])

    def watch_intro(self):
        '''
        Background task : as soon as the intro video is finished, asks the main loop to show
        the window of the game (show() cannot be called from here)
        '''
        while intro_is_playing():
            time.sleep(0.1)
        self.logs.debug("End of the intro video")
        if self.hidden or self.audio_deferred:
            pygame.event.post(pygame.event.Event(INTRO_END_EVENT))
        else:
            # Intro played over the game (omxplayer) : the menu is already displayed
            self.rpi.target_enabled = True
            self.logs.debug("Target read")

    def set_intro_background(self, background):
        '''
        While the intro video is playing, the background of the menu replaces the startup
        image on the screen : it is what is seen during the short time between the end of
        the video and the window of the game
        '''
        if self.hidden and background and os.path.isfile(background) and shutil.which('feh'):
            subprocess.Popen(['feh', '--no-fehbg', '--bg-fill', background],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def show(self):
        '''
        Once the intro video is finished : show the window of the game (hidden during the
        video, with what is already drawn on it), open the audio output and start reading
        the target. Does nothing while the video is playing.
        '''
        if not self.hidden and not self.audio_deferred:
            return
        if intro_is_playing():
            return

        if self.hidden:
            # Same mode without the hidden flag : pygame shows the window, but what is
            # already drawn on it is lost
            drawn = self.screen.copy()
            if self.fullscreen:
                self.screen = pygame.display.set_mode((0, 0), self.flags)
            else:
                self.screen = pygame.display.set_mode((self.res['x'], self.res['y']), pygame.RESIZABLE)
            self.hidden = False
            # The window appears first with its normal size, then goes full screen : it is
            # drawn again until the window manager is done (longer while starting up)
            for _ in range(12):
                pygame.event.pump()
                self.screen.blit(drawn, (0, 0))
                self.display.flip()
                pygame.time.wait(100)

        if self.audio_deferred:
            # Modules left aside at startup, audio output included. After the window is
            # shown : their initialization takes time, the desktop would be seen meanwhile
            pygame.init()
            self.audio_deferred = False
            self.rpi.target_enabled = True
            self.logs.debug("Window of the game shown, audio output opened, target read")

    def loading(self, percent):
        '''
        Startup screen : only the progress of the loading is displayed
        '''
        self.message([f"{self.lang.translate('Loading')} {percent} %"], 0, None, 'middle')
        pygame.event.pump()
        # Intro video finished before the end of the loading : its progress is shown
        self.show()

    def wait_touch(self):
        '''
        Wait for touch
        '''
        self.show()

        press = self.rpi.listen_inputs(
                    ['alpha', 'num', 'fx', 'math', 'arrows'],
                    ['PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON', 'EXTRABUTTON',
                    'escape', 'enter', 'backspace', 'tab', 'TOGGLEFULLSCREEN',
                    'space', 'single-click'])
        return press

    def wait_validation(self, text):
        '''
        Wait for validation
        '''
        rect = pygame.Rect(0, int(self.res['y'] * 9 / 20), self.res['x'], self.res['y'] / 5)

        if self.colorset['border-radius'] == 'max':
            border_radius = int(rect.h / 2)
        else:
            border_radius = int(self.colorset['border-radius']) * 4

        self.save_background()
        self.display_background(image=True)

        minus = 10

        self.new_blit_rect2(rect, self.colorset['message-bg'], alpha=255, corners='All', border_radius=border_radius)
        self.blit_border(rect, (0, 0, 0), minus, alpha=255, corners='All', border_radius=border_radius)
        rect2 = rect.copy()
        rect2.height /= 2
        self.blit_text2(text, rect2, self.colorset['message-text'])
        rect2.y = rect2.bottom
        self.blit_text2("press-enter", rect2, self.colorset['message-text'])

        self.update_screen()
        if self.wait_touch() in ENTER_KEYS:
            self.restore_background()
            self.reset_background()
            return True

        self.restore_background()
        self.reset_background()
        return False

    def message(self, texts, wait=3000, color=None, pos_y=None, size=None, logo=None, refresh=True, bg_color=None):
        '''
        Main UI messaging method - can display multiple phrases, mutiple sizes, multiple places
        '''

        if logo is not None:
            size = self.res['y'] / 4
        else:
            if size == 'small':
                size = self.res['y'] / 40
            if size is None or size == 'normal':
                size = self.res['y'] / 20
            if size == 'big':
                size = self.res['y'] / 7
            if size == 'huge':
                size = self.res['y'] / 4

        # set the color of the Text
        text_color = self.colorset['message-text']
        if type(color) is tuple:
            text_color = color
        elif type(color) == str and color in self.colorset:
            text_color = self.colorset[color]

        # Constants
        width = self.res['x']
        rect_x = 0
        # Display background
        if refresh and self.game_background is None:
            self.display_background()
        elif refresh:
            self.blit(self.game_background, (0, 0))

        if bg_color is None:
            bg_color = self.colorset['message-bg']
        else:
            bg_color = self.colorset[bg_color]

        # For each sentence in list
        for text in texts:
            # Calculate Y
            if pos_y is None or pos_y == 'bottom':
                pos_y = self.res['y'] / 3 * 2
            if pos_y == 'fullbottom':
                pos_y = self.res['y'] - (size / 2)
            if pos_y == 'top':
                pos_y = self.res['y'] / 3
            if pos_y == 'middle':
                pos_y = self.res['y'] / 2
            # Calculate rect size and place
            rect_y = int(pos_y - (size / 2))
            # Display rect
            rect = pygame.Rect(rect_x, rect_y, width, size)
            self.new_blit_rect2(rect, bg_color)

            if logo is None:
                self.blit_text2(text, rect, text_color)
            else:
                self.blit_text2('' , rect, text_color)

                # Display LOGO
                width = int(self.res['x'] / 3)
                height = int(self.res['y'] / 4)
                pos_x = 0 + width
                pos_y = int(self.res['y'] / 2.7)
                # Display LOGO
                self.display_image(self.file_class.get_full_filename(logo, 'images'), pos_x, pos_y, width, height, False, True, True)

            if refresh:
                # Update screen
                self.update_screen()
                # Optionnaly wait a few sec between each message
                if wait is None:
                    pygame.time.wait(self.blinktime)
                elif wait > 0:
                    pygame.time.wait(wait)    # Wait X millisecond

    def is_clicked(self, zones=None, click=False):
        '''
        Define if the click is inside the given zone
        '''
        # Eventually get Zones for current object if not provided
        if zones is None:
            zones = self.click_zones
        # Exit if we did not receive a click (maybe another input) or if Zones is not set
        if type(click) is not tuple or zones is None:
            return False
        # Try to expand all zones and compare them to click

        try:
            for key in zones.keys():
                if type(zones[key]) is pygame.Rect and zones[key].collidepoint(click[0], click[1]):
                    return key
                # Avoid getting an exception for integers
                if type(zones[key]) is not tuple:
                    continue
                # Compare
                if click[0] >= zones[key][0] and click[0] <= zones[key][0] + zones[key][2] and click[1] >= zones[key][1] and click[1] <= zones[key][1] + zones[key][3]:
                    return key
        except Exception as e:
            self.logs.warning("Issue in cscreen.is_clicked method.")
            self.logs.debug(f"Issue is {e}")
            return False

    def on_desktop(self, function):
        '''
        The wizard and the calibration : on the background of the desktop whatever the theme
        '''
        background, bg_global = self.background, self.colorset.get('bg-global')
        self.background = os.path.join(cpaths.ROOT_DIR, 'images', 'background_clear.png')
        self.colorset['bg-global'] = None
        self.reset_background()
        try:
            return function()
        finally:
            self.background = background
            self.colorset['bg-global'] = bg_global

    def get_rpi_config(self):
        '''
        1st execution : the wizard
        '''
        return self.on_desktop(self.wizard)

    # Names of the sections of the configuration, for the deposited file
    DEPOSIT_SECTIONS = ('SectionGlobals', 'SectionAdvanced', 'SectionKeys', 'Raspberry', 'Raspberry_Leds',
                        'Raspberry_BoardPinsIns', 'Raspberry_BoardPinsOuts', 'LEDTarget', 'Camera', 'Gallery',
                        'Events', 'Favorites', 'Server')

    def deposit_menu(self, changes):
        '''
        A configuration was put on the SD card : its new values listed by category, taken
        or the file removed. Returns True (taken), False (removed), None (escape : asked
        again at the next start)
        '''
        lines = []
        for section, values in changes.items():
            name = self.lang.translate(f'deposit-{section}') if section in self.DEPOSIT_SECTIONS else section
            lines.append(f"{name} : {len(values)}")
        choices = [('yes', self.lang.translate('deposit-apply')), ('no', self.lang.translate('deposit-drop'))]
        self.display_background()
        self.menu_header(self.lang.translate('deposit-title'), self.lang.translate('deposit-sub'))
        height = int(self.res['y'] / 18)
        top = int(self.res['y'] * 9 / 16)
        shown = lines[:8]
        box = pygame.Rect(int(self.res['x'] / 5), top - height // 2, int(self.res['x'] * 3 / 5), (len(shown) + 1) * height)
        self.new_blit_rect2(box, self.colorset['message-bg'], alpha=255, corners='All', border_radius=int(height / 2))
        for index, line in enumerate(shown):
            self.blit_text2(line, pygame.Rect(box.x, top + index * height, box.w, height), self.colorset['message-text'])
        self.update_screen()
        answer = self.dropdown(6 * self.res_x_16, 3 * self.res_y_16, choices)
        if answer == 'escape':
            return None
        return answer == 'yes'

    def calibration_needed(self):
        '''
        The target is wired on the GPIO but none of its segments is known : configuration
        made without it (page of the web site, target of no known model)
        '''
        if not (self.rpi.inputs and self.rpi.outputs):
            return False
        keys = self.config.config.get('SectionKeys', {})
        return not any(keys.get(segment) for segment in list(self.config.keys)[:62])

    def calibration_only(self):
        '''
        Only the calibration of the target, the rest of the configuration being there.
        Escape on the first segment : not now (asked again at the next start)
        '''
        calibrated = self.on_desktop(self.calibrate_target)
        if calibrated is None:
            return False
        keys = dict(self.config.config.get('SectionKeys', {}))
        keys.update(calibrated)
        self.rpi.set_keys_conf(keys)
        self.config.write_file()
        self.message([f"{self.lang.translate('config-restart')}"], 2500, None, 'middle', 'big')
        return True

    def calibrate_target(self):
        '''
        Calibration of the target : the whole target is drawn, the segment to press blinks,
        a segment done turns green (with a sound). Escape : the one before ; on the first
        one, None. Space : the segment left unset (not told on the screen)
        Returns {segment: code of its contact ("2410")}
        '''
        new_keys = {}
        segments = list(self.config.keys)[:62]
        lit = True
        j = 0
        while j < 62:
            key = segments[j]
            self.draw_calibration(segments, j, lit, new_keys)
            # Code of the contact as it is ("2410") : the segment is not known yet
            key_pressed = self.rpi.listen_inputs([], ['escape', 'enter', 'space', 'TOGGLEFULLSCREEN'], context='wizard', timeout=400)
            if key_pressed is False:
                # Blinking
                lit = not lit
                continue
            lit = True
            if key_pressed == 'escape':
                if j == 0:
                    return None
                j -= 1
                new_keys.pop(segments[j], None)
            elif key_pressed == 'space':
                # Not wired, broken
                new_keys[key] = ''
                j += 1
            elif key_pressed not in new_keys.values() and key_pressed not in ('enter', '', None):
                new_keys[key] = key_pressed
                self.play_sound('Blaster')
                j += 1
        return new_keys

    @with_look('wizard')
    def wizard(self):
        '''
        1st execution : get configuration
        '''
        self.logs.info(f"Lauch target's setup wizard")


        self.display_background()    # display basic screen
        self.display_ips(big=True)            # display IPs addresses
        self.menu_header("config-interface")
        self.update_screen()
        cards_dd = [['Ji', 'Cartes de Jimmy'], ['Jo', 'Carte de Joffrey'], ['Ch', 'La Chti Raspycard'], ['Jt', 'Carte de Julien V1'],
                    ['Jt2', 'Carte de Julien V2'],['Mm', 'MM-Workshop DartCab'], ['MMWVdarts', 'MM-Workshop VDarts'], ['Re', 'DartBoard'], ['Au', 'card-other']]
        card = self.dropdown(6 * self.res_x_16, 3 * self.res_y_16, cards_dd)
        if card == 'escape':
            return False

        if card in ('Ji', 'Jo'):
            # Menu extendarts pour choix des matrices

            self.display_background()    # display basic screen
            self.menu_header("config-interface")
            self.update_screen()
            if card == 'Ji':
                cards_dd = [['Ji', 'RaspyCard'], ['Jiz', 'RaspyZcard'], ['Ji3', 'RaspYDartsCard'], ['Ji2', 'RaspyCard V4'], ['GB', 'RaspyBoard'], ['ED', 'ED900']]
            else:
                cards_dd = [['Jo', 'Cible ED110 7*10'], ['Jo416', 'Cible Pro 4*16'], ['Au', 'card-other'], ]
            card = self.dropdown(6 * self.res_x_16, 3 * self.res_y_16, cards_dd)
            if card == 'escape':
                return False

        if card in ('Jo', 'Re'):
            self.config.set_jo_card_config()
        elif card == 'Jo416':
            self.config.set_jo_416_card_config()
        elif card in ('Ji', 'Mm'):
            self.config.set_ji_card_config()
        elif card in ('Ji2', 'Ji3'):
            self.config.set_ji2_card_config()
        elif card == 'MMWVdarts':
            self.set_mmworks_vdartscard_config()
        elif card == 'GB':
            self.config.set_gb_card_config()
        elif card == 'ED':
            self.config.set_ed900_card_config()
        elif card == 'Jt':
            self.config.set_jt_card_config()
        elif card == 'Jt2':
            self.config.set_jt2_card_config()
        elif card == 'Jiz':
            self.config.set_jiz_card_config()
        elif card == 'Ch':
            self.config.set_clk_card_config()

        self.display_background()    # display basic screen
        self.menu_header("config-leds_choice", "config-leds_question")
        self.update_screen()
        leds_dd = [['yes', 'yes'], ['no', 'no']]
        leds_ji = self.dropdown(6 * self.res_x_16, 3 * self.res_y_16, leds_dd)

        used_pins = []
        if card == 'Au':
            i = 0
            total = 66

            # Out pins
            new_outputs = {}
            totalOuts = len(self.config.outputs)

            # In pins
            new_inputs = {}
            totalIns = len(self.config.inputs)

            # Buttons conf (extended card)
            new_buttons = {}
            totalButtons = len(self.config.buttons)

            # Target configuration
            new_keys = {}

            j = 0
            # Parametrage des pins de sortie
            while j < totalOuts:
                self.display_background()    # display basic screen
                key = list(self.config.outputs)[j]
                txt = f"{self.lang.translate('conf-fillin')} {key}"
                self.message([txt], 0, None, 'fullbottom', 'big', refresh=False)
                if j == 0:
                    esc_text = self.lang.translate('conf-esc1')
                else:
                    esc_text = self.lang.translate('conf-esc2')

                subtxt = self.lang.translate('conf-pin1').format(txt, esc_text)
                self.menu_header("config-pin_out", subtxt)
                self.update_screen()

                tmp = self.input_value_item('pins', '', 1, 27, align='Center')

                if tmp in ('', 'space'):
                    j = totalOuts
                elif tmp == 'escape':
                    j-=1
                    if len(used_pins)>0:
                        used_pins.pop()
                    if j < 0:
                        return False
                elif tmp in used_pins:
                    self.message(["config-already"], 2000, None, 'fullbottom', 'big')
                else:
                    new_outputs[key] = tmp
                    self.rpi.set_outputs(tmp)
                    used_pins.append(tmp)
                    j+=1
                    
            self.rpi.init_gpio(new_outputs, 'OUT')

            # Parametrage des pins d'entrée
            j = 0
            while j < totalIns:
                self.display_background()    # display basic screen
                key = list(self.config.inputs)[j]
                txt = f"{self.lang.translate('conf-fillin')} {key}"
                self.message([txt], 0, None, 'fullbottom', 'big', refresh=False)
                if j == 0:
                    esc_text = self.lang.translate('conf-esc1')
                else:
                    esc_text = self.lang.translate('conf-esc2')

                subtxt = self.lang.translate('conf-pin2').format(txt, esc_text)

                self.menu_header("Configuration des pins d'entrée de la cible", subtxt)
                self.update_screen()

                tmp = self.input_value_item('pins', '', 1, 27, align='Center')
                if tmp in ('', 'space'):
                    j = totalIns
                elif tmp == 'escape':
                    j-=1
                    used_pins.pop()
                    if j < 1:
                        return False
                elif tmp in used_pins:
                    self.message(["config-already"], 2000, None, 'fullbottom', 'big')
                else:
                    new_inputs[key] = tmp
                    self.rpi.set_inputs(tmp)
                    used_pins.append(tmp)
                    j+=1

            self.rpi.init_gpio(new_inputs, 'IN')

            # Parametrage des boutons

            self.display_background()    # display basic screen
            self.menu_header("Configuration des boutons")
            self.message(["Avez-vous une carte d'extension ?"], 0, None, 'fullbottom', 'big', refresh=False)
            self.update_screen()

            new_buttons['EXTENDED_GPIO'] = self.dropdown(self.res['x'] / 8 * 3, self.res['y'] / 8 * 3, [('1', 'yes'), ('0', 'no')])

            if new_buttons['EXTENDED_GPIO'] == '0':
                j = 0
                while j < totalButtons:
                    if list(self.config.buttons)[j] == 'EXTENDED_GPIO':
                        j+=1
                        continue

                    key = list(self.config.buttons)[j]
                    txt = f"{self.lang.translate('conf-fillin')} {key}"
                    self.message([txt], 0, None, 'fullbottom', 'big')
                    if j == 0:
                        subtxt = "Merci d'indiquer si vous avez une carte d'extension. Echap pour quitter, Entrée pour valider."
                    else:
                        subtxt = f"Merci d'indiquer sur quel pin est connecté le bouton {key.replace('PIN_', '')}.Echap pour revenir en arrière, Entrée pour valider ou passer."

                    self.menu_header("Configuration du Raspberry", key)
                    self.update_screen()

                    tmp = self.input_value_item('pins', '', 1, 27, align='Center')
                    if tmp in ('', 'space'):
                        j = totalButtons
                    elif tmp == 'escape':
                        j-=1
                        used_pins.pop()
                        if j < 1:
                            return False
                    elif tmp in used_pins:
                        self.message([self.lang.translate('config-already')], 2000, None, 'fullbottom', 'big')
                    else:
                        new_buttons[key] = tmp
                        used_pins.append(tmp)
                        j+=1

            #self.rpi.init_gpio(new_inputs, 'IN')
            #self.rpi.init_gpio(new_outputs, 'OUT')

        # Leds conf
        new_leds = {}
        totalLeds = len(self.config.leds)

        j = 0
        while j < totalLeds:
            self.display_background()    # display basic screen

            key = list(self.config.leds)[j]
            if j == 0:
                esc_text = self.lang.translate('conf-esc1')
            else:
                esc_text = self.lang.translate('conf-esc2')

            if key.startswith('PIN_'):
                subtxt = self.lang.translate('conf-pin1').format(self.lang.translate(key), esc_text)
            else:
                subtxt = self.lang.translate('conf-pin2').format(self.lang.translate(key), esc_text)

            self.menu_header(self.lang.translate('conf-leds'))
            self.message([f"{self.lang.translate('conf-fillin')} {self.lang.translate(key)}"], 0, None, 'fullbottom', 'big', refresh=False)
            self.update_screen()
            
            if key in ('PIN_STRIPLED', 'PIN_TARGETLED'):
                tmp = self.input_value_item('pins', '', 1, 27, align='Center')
            elif key in ('BRI_STRIPLED', 'BRI_TARGETLED'):
                tmp = self.input_value_item('number', '', 1, 100, align='Center')
            elif key in ('TYP_STRIPLED', 'TYP_TARGETLED'):
                tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, [['rgb','RGB'], ['grb','GRB']])
            elif key == 'NBR_STRIPLED':
                tmp = self.input_value_item('number', '', 1, 1000, align='Center')
            
            if tmp in ('', 'space'):
                new_leds[key] = '0'
                if key == 'PIN_STRIPLED':
                    j += 3
                    new_leds['NBR_STRIPLED'] = 0
                    new_leds['BRI_STRIPLED'] = 0
                elif key == 'PIN_TARGETLED':
                    j += 2
                    new_leds['BRI_TARGETLED'] = 0
                elif key.startswith('BRI') or key == 'NBR_STRIPLED':
                    if key in ('NBR_STRIPLED', 'BRI_TARGETLED'):
                        used_pins.pop()
                    j-=1
                else:
                    tmp = 'escape'
            elif key in ('TYP_STRIPLED', 'TYP_TARGETLED'):
                new_leds[key] = tmp
                j+=1
            elif tmp == 'escape':
                j-=1
                if j < 0:
                    return False
            elif key in ('PIN_STRIPLED', 'PIN_TARGETLED') and tmp in used_pins:
                self.message([self.lang.translate('config-already')], 2000, None, 'fullbottom', 'big')
            else:
                new_leds[key] = tmp
                if key.startswith('PIN'):
                    used_pins.append(tmp)
                j+=1

        self.rpi.set_leds_conf(new_leds)

        if card == 'Au':
            calibrated = self.calibrate_target()
            if calibrated is None:
                self.rpi.gpio_flush()
                sys.exit(0)
            new_keys.update(calibrated)
            j = 62

            for l in [1, 2, 3, 4]:
                new_keys[self.config.keys[j]] = ''
                j+=1

            if new_buttons['EXTENDED_GPIO'] == '1':
                from include import cgpio_extender

                for k in self.config.buttons:
                    if k != 'EXTENDED_GPIO':
                        new_buttons[k] = cgpio_extender.DEFAULTS[k]

            self.rpi.set_inputs_conf(new_inputs)
            self.rpi.set_outputs_conf(new_outputs)
            self.rpi.set_buttons_conf(new_buttons)
            self.rpi.set_keys_conf(new_keys)
        else:
            used_pins = []
            for p in self.rpi.inputs:
                pin = self.raspberry.inputs[p]
                if pin != '':
                    used_pins.append(int(pin))

            for p in self.rpi.outputs:
                pin = self.rpi.outputs[p]
                if pin != '':
                    used_pins.append(int(pin))

        if leds_ji == 'yes':
            if card == 'MMWVdarts':
                self.config.set_mmworks_leds_config()
            else:
                self.config.set_ji_leds_config()

        self.display_background()    # display basic screen
        self.menu_header("config-buttons_choice", "config-buttons_question")
        self.update_screen()
        yesno_dd = [['yes', 'yes'], ['no', 'no']]
        go_conf = self.dropdown(6 * self.res_x_16, 3 * self.res_y_16, yesno_dd)

        if go_conf == 'yes':
            extended_io = self.setup_io_extender()
            if extended_io is not None:
                self.config.set_config('Raspberry', extended_io)

        # Write config file
        self.config.write_file()

        self.message([f"{self.lang.translate('config-restart')}"], 2500, None, 'middle', 'big')
        return True

    def setup_io_extender(self):

        try:
            # The extension card opened by the game : created again here with an old way
            # (Gpio_extender(''), gpio.mcp), it failed and the card was "not found"
            from digitalio import Direction, Pull
            gpio = self.rpi.gpio
            if gpio is None or gpio.mcp1 is None:
                raise RuntimeError("no MCP23017")

            # Every card : a pin read low with its pull-up is an output (toy, light)
            outputs = []
            for index, chip in enumerate(gpio.chips):
                names = gpio.pins_of(index)
                for pin in range(0, 16):
                    io = chip.get_pin(pin)
                    io.direction = Direction.INPUT
                    io.pull = Pull.UP
                value = chip.gpio
                outputs += [names[pin] for pin in range(0, 16) if not value & 2**pin]

            if len(outputs) > 0:
                self.message([f"{self.lang.translate('config-toysfound')} {'/'.join(outputs)}"], 2500, None, 'middle', 'big')

            buttons_list = []
            toys_list = []
            done = []
            buttons_conf = {}
            toys_conf = {}

            for key in gpio.get_defaults():
                if key.startswith('PIN_'):
                    buttons_list.append(key)
                # Lights of the buttons and toys (TOY1...) : both on the outputs
                if key.startswith(('LIGHT_', 'TOY')):
                    toys_list.append(key)

            # One step per pin : the button wired on each input, then the toy on each
            # output. Escape : the step before (its choice proposed again) ; on the first
            # one, the card is left as it is. "Skip" : nothing on this pin. A light or a
            # toy is not always read low : they are proposed on the inputs too, after the
            # buttons
            steps = [('pin', pin) for pin in gpio.all_io if pin not in outputs] + [('toy', pin) for pin in outputs]
            chosen = {}
            index = 0
            while index < len(steps):
                kind, pin = steps[index]
                if kind == 'pin':
                    title, sub, names = 'config-pin', 'config-pin-sub', buttons_list + toys_list
                else:
                    title, sub, names = 'config-toy', 'config-toy-sub', toys_list
                taken = [value for step, value in chosen.items() if step != index]
                choices = [(name, self.lang.translate(name)) for name in names if name not in taken]
                choices.append(('None', self.lang.translate('config-skip')))
                self.display_background()
                self.menu_header(f"{self.lang.translate(title)} {pin}", self.lang.translate(sub))
                self.update_screen()
                answer = self.dropdown(6 * self.res_x_16, 3 * self.res_y_16, choices, navigate=chosen.get(index))
                if answer == 'escape':
                    if index == 0:
                        return None
                    chosen.pop(index, None)
                    index -= 1
                    continue
                if answer == 'None':
                    chosen.pop(index, None)
                else:
                    chosen[index] = answer
                index += 1

            for step, value in chosen.items():
                _kind, pin = steps[step]
                if value.startswith('PIN_'):
                    buttons_conf[value] = pin
                else:
                    toys_conf[value] = pin

            config = {}
            for key in gpio.get_defaults():
                if key == 'EXTENDED_GPIO':
                    if buttons_conf is not None:
                        value = 1
                    else:
                        value = 0
                elif key.startswith('PIN_'):
                    if buttons_conf is not None:
                        value = buttons_conf.get(key, '')
                    else:
                        value = ''
                elif key.startswith(('LIGHT_', 'TOY')):
                    if buttons_conf is not None:
                        value = toys_conf.get(key, '')
                    else:
                        value = ''
                config[key] = value

            return config
        except Exception as error:
            self.logs.warning(f"Extension card not configured : {error}")
            self.message([self.lang.translate('config-noMCP')], 3000, None, 'middle', 'big', bg_color='menu-ko')
            return None

    def starting(self, NetClient, NetStatus, local_players, netgamename, game):
        '''
        Display Players engaged in a network game menu
        '''
        self.display_background()    # display basic screen
        # Init empty values
        Rdy = {'REQUEST': None, 'PLAYERSNAMES': None}
        players = []
        # This loop will ends when the game will be launched
        click_zones = {}
        selected = 1
        nb_boutons = 1
        nb_players = len(local_players)
        nb_local_players = nb_players
        old_nb_players = nb_players
        Rdy = NetClient.send_local_players(local_players)    # Send name of local players, and wait for game to be launched
        while True:
            # Listen for keyboard
            key_pressed = self.rpi.listen_inputs(['arrows', 'fx'],
                            ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON',
                            'single-click', 'double-click', 'resize', 'VOLUME-UP', 'VOLUME-DOWN', 'enter', 'space'],
                            timeout=1000)

            # Analyse mouse
            clicked = self.is_clicked(click_zones, key_pressed)
            if clicked:
                key_pressed = clicked

            selected = self.navigate(selected, key_pressed, 0, nb_boutons, nb_boutons)

            # Analyse key
            # If the Master player pressed tab
            if nb_players > nb_local_players and NetStatus == 'YOUAREMASTER' and ((key_pressed in ENTER_KEYS and selected == 2) or key_pressed in TAB_KEYS):
                self.play_sound('shakeitbaby')
                # Request the server to shuffle player names
                data = {'REQUEST': 'SHUFFLE', 'GAMENAME': NetClient.gamename}
                NetClient.send(data)    # Send message
                # Display refreshing from server
                #self.message([self.lang.translate('net-client-randomizing')], 500)

            elif (key_pressed in ENTER_KEYS and selected == 1) or key_pressed in ESCAPE_KEYS:
                if NetStatus == 'YOUARESLAVE':
                    return -1    # Return -1 means yourself, as a slave client left the game
                return []    # Return -1 means yourself, as a slave client left the game

            # If the Master pressed enter
            if nb_players > nb_local_players and NetStatus == 'YOUAREMASTER' and ((key_pressed in ENTER_KEYS and selected == 3) or key_pressed in CONTINUE_KEYS):
                self.message([self.lang.translate('Ready to kick ass ?')], 0, None, 'middle', 'big')
                # He is ok to launch the game. Tell it to server
                data = {'REQUEST': 'LAUNCH', 'GAMENAME': NetClient.gamename}
                NetClient.send(data)    # Send message

            Rdy = NetClient.send_local_players(local_players)    # Send name of local players, and wait for game to be launched
            # refresh player list if provided by server
            if 'PLAYERSNAMES' in Rdy:
                players = Rdy['PLAYERSNAMES']
            # Display page title
            if NetStatus == 'YOUAREMASTER':
                txt = self.lang.translate('players-ready-masterplayer')
            else:
                txt = self.lang.translate('players-ready-slaveplayer')

            # Display screen
            self.display_background()
            txt2 = f"{self.lang.translate('game-type')} : {game.replace('_', ' ')} - {self.lang.translate('game-name')} : {netgamename}"
            self.menu_header(txt, txt2)

            nb_players = 0
            for player in players:
                nb_players += 1
                self.menu_item((nb_players, len(players), 0), ('', player, BTN_CHOICE, None), collapsed=True)

            if NetStatus == 'YOUAREMASTER' and nb_players > nb_local_players:
                if key_pressed is False and old_nb_players != nb_players:
                    selected = 3
                click_zones['shake'] = self.display_button(2 == selected, 'shake', special='refresh')
                click_zones['continue'] = self.display_button(3 == selected, 'continue', special='return')
                nb_boutons = 3
            else:
                nb_boutons = 1
                selected = 1

            click_zones['escape'] = self.display_button(1 == selected, 'back', special='escape')

            self.update_screen()
            # If we received the order to LAUNCH or to ABORT game
            if Rdy['REQUEST'] in ('LAUNCH', 'ABORT'):
                # Return Player list to main game
                return players
            old_nb_players = nb_players

    def pnj_name(self, playerName):
        '''
        Compute PNJ name
        '''

        if '[' not in playerName:
            return '[NoOb]' + playerName
            # Noob

        if '[NoOb]' in playerName:
            return playerName.replace('[NoOb]', '[BegiN]')
             # Beginner

        if '[BegiN]' in playerName:
            return playerName.replace('[BegiN]', '[InTeR]')
            # Interdemdiate

        if '[InTeR]' in playerName:
            return playerName.replace('[InTeR]', '[PrO]')
            # Pro

        if '[PrO]' in playerName:
            return playerName.replace('[PrO]', '[ExperT]')
            # Expert

        return playerName.replace('[ExperT]', '')

    def next_key(self, character, context=None):
        '''
        In case of using buttons instead of keyboard
        return the next character
        '''

        if context == 'number':
            next_key = {'9':'0'}
        elif context == 'leds':
            next_key = {
                '9':', ',
                ', ':'0'
                }
        elif context == 'server':
            next_key = {
                'z':'0',
                '9':'.',
                '.':':',
                ':':'_',
                '_':'-',
                '-':'a'
                }
        else:
            next_key = {
                    'e': 'é',
                    'é': 'è',
                    'è': 'ë',
                    'ë': 'f',
                    'o': 'ô',
                    'ô': 'p',
                    'z': 'a'
                }

        return next_key.get(character, chr(ord(character) + 1))

    def previous_key(self, character, context=None):
        '''
        In case of using buttons instead of keyboard
        return the previous character
        '''

        if context == 'number':
            previous_key = {'0':'9'}
        elif context == 'leds':
            previous_key = {
                ', ':'9',
                '0':', '
                }
        elif context == 'server':
            previous_key = {
                 'a':'_',
                 '_':'-',
                 '-':':',
                 ':':'.',
                 '.':'9',
                 '0':'z'
                 }
        else:
            previous_key = {
                    'a': 'z',
                    'p': 'ô',
                    'ô': 'o',
                    'f': 'ë',
                    'ë': 'è',
                    'è': 'é',
                    'é': 'e',
                    }

        return previous_key.get(character, chr(ord(character)-1))

    def no_doubles(self, edit, players, selected):
        '''
        Check if player name is already in list of players
        '''
        index = 1
        for player in players:
            if edit.upper() == player.upper() and index != selected:
                return False
            index += 1
        return True

    def navigate(self, selected, key, nb_elements, add, defaultTopBottom, sound=True, item_per_line=1, left_right=False, zero=1, tab=0):
        '''
        Common navigation menu
        '''
        grid_max = math.ceil(nb_elements/item_per_line) * item_per_line
        v_min = zero

        if key in DOWN_KEYS:
            if zero < 0 and selected == nb_elements + add:
                selected = tab
            elif zero < 0 and selected <= 0:
                selected = 1
            elif item_per_line > 1:
                if selected > nb_elements:
                    selected = 1
                elif selected < 0:
                    selected = 1
                else:
                    selected += item_per_line
                    if selected > nb_elements and add > 0:
                        selected = nb_elements + add
                    elif selected > nb_elements:
                        selected = selected - grid_max
                    if selected < v_min:
                        selected += item_per_line
            elif selected < nb_elements:
                selected += 1
            elif selected == nb_elements and defaultTopBottom > 0:
                selected = nb_elements + defaultTopBottom
            else:
                selected = v_min

        elif key in UP_KEYS:
            if zero < 0 and selected <= 0:
                selected = nb_elements + add
            elif zero < 0 and selected == nb_elements + add:
                selected = nb_elements
            elif zero < 0 and selected <= item_per_line:
                selected = tab
            elif item_per_line > 1:
                if selected > nb_elements:
                    selected -= 1
                else:
                    selected -= item_per_line
                    if selected < v_min and add > 0:
                        selected = nb_elements + 1
                    elif selected < v_min:
                        selected = grid_max + selected
                        if selected > nb_elements:
                            selected -= item_per_line
            elif selected == v_min:
                selected = nb_elements + defaultTopBottom
            elif selected <= nb_elements:
                selected -= 1
            elif nb_elements == 0:
                selected = defaultTopBottom
            else:
                selected = nb_elements

        elif key in LEFT_KEYS + RIGHT_KEYS and left_right:
            # Reading order over all : the tabs (zero < 0), the list, the buttons at the bottom,
            # then the start again (with tabs, they went round between them or stayed on the
            # last button)
            first = min(zero, 1)
            total = nb_elements + add - first + 1
            selected = first + (selected - first + (1 if key in RIGHT_KEYS else -1)) % total

        elif key in LEFT_KEYS:
            if zero < 0 and selected == zero:
                selected = 0
            elif zero < 0 and selected <= 0:
                selected -= 1
            elif zero < 0 and selected == nb_elements + 1:
                selected = nb_elements + add
            elif selected > nb_elements or left_right:
                selected -= 1
            if selected < v_min:
                selected = nb_elements + add

        elif key in RIGHT_KEYS:
            if zero < 0 and selected == 0:
                selected = zero
            elif zero < 0 and selected <= 0:
                selected += 1
            elif zero < 0 and selected == nb_elements + add:
                selected = nb_elements + 1
            elif selected > nb_elements or left_right:
                selected += 1
            if selected > nb_elements + add:
                selected = v_min

        elif key == 'resize':    # Resize screen
            self.create_screen(False, self.rpi.newresolution)
        elif key == 'TOGGLEFULLSCREEN':    # Toggle fullscreen
            self.create_screen(True, False)
        elif sound and key in VOLUME_UP_KEYS + VOLUME_DOWN_KEYS:
            self.adjust_volume(key, False)
        elif sound and key in VOLUME_MUTE:
            self.adjust_volume(key, False)

        return selected

    @staticmethod
    def grid_step(cursor, selected, nb_elements, footers, key):
        '''
        Right and left on a screen of boxes in lines (cursor : 'line-column' of each box) : the
        next box in reading order, the buttons at the bottom after the last line (lines
        nb_elements + 1...), then the first box. A knob set on right and left goes through the
        whole screen (they stayed in a line)
        '''
        cells = sorted({tuple(int(number) for number in str(name).split('-')) for name in cursor})
        cells = [cell for cell in cells if cell[0] <= nb_elements] + \
                [(line, 0) for line in range(nb_elements + 1, nb_elements + footers + 1)]
        current = (selected[0], 0) if selected[0] > nb_elements else tuple(selected)
        position = cells.index(current) if current in cells else 0
        return list(cells[(position + (1 if key in RIGHT_KEYS else -1)) % len(cells)])

    @with_look('players')
    def players_menu(self, favorites, context='game', bank=None, sets=None, competition_mode=False, colors_available = None, players_color = None):
        '''
        Player Names menu
        '''
        players = []
        player_color = []
        nb_players = 0

        if context == 'pref':
            self.dmd.send_text(self.lang.translate('dmd-player-favorites'), tempo = 1)
        elif context == 'bank':
            self.dmd.send_text(self.lang.translate('dmd-player-bank'), tempo = 1)
        else:
            self.dmd.send_text(self.lang.translate('dmd-player-choice'), tempo = 1)

        for player in favorites:
            if len(player) > 0:
                players.append(player)
        if context in ('game', 'netcreate', 'netjoin'):
            random.shuffle(players)

        if len(players) == 0:
            players.append(f"{self.lang.translate('Player')} 1")
        
        if context in ('netcreate', 'netjoin'):
            btn_random = False
            selected = 1
        elif len(players) > 1:
            btn_random = True
            selected = len(players) + 3
        else:
            btn_random = False
            selected = len(players) + 2
        
        # For players color dropdown
        # For operation via Colorset with player1, player2, etc : first (last, it was hidden by the
        # scrolling of a hundred colours)
        colors_list = [('AUTO COLORSET', 'Auto')]
        if colors_available is not None:
            for val in colors_available:
                if val in pygame.color.THECOLORS:
                    colors_list.append((val, (pygame.Color(val).r, pygame.Color(val).g, pygame.Color(val).b)))
        
        # Init enabled F keys
        key_pressed = ''
        # Box of the selected player reached by right and left, None : its name
        part = None

        while True:
            nb_elements = len(players)
            shortcuts = []
            click_zones = {}
            clic = ''
            # Draw background
            self.display_background()
            # Draw Text
            self.menu_header(self.lang.translate('players-names'), self.lang.translate('players-names-subtitle'))

            i = 1
            if len(players) == 1:
                special = 'first'
            elif len(players) == 16:
                special = 'last'
            else:
                special = None

            for player in players:
                shortcut = f'F{i}'
                # Display player name
                tmp = self.player_item((i, nb_elements, selected), shortcut, player, special=special, specific_color=players_color,
                                       part=part)

                # Add clickable zones
                for (e, f) in tmp:
                    click_zones[e] = f

                # Construct available F keys list
                shortcuts.append(shortcut)

                i += 1

            if nb_players != len(players):
                # Show message on Raspydarts DMD
                self.dmd.send_text(f"{len(players)} joueur" + ('', 's')[bool(len(players) > 1)])
                nb_players = len(players)

            # go back and next
            if bool(self.config.get_value('SectionGlobals', 'fast_games_mode', False)) and context in ('game', 'netcreate', 'netjoin'):
                click_zones['escape'] = self.display_button(i == selected, 'main-menu', special='escape')
            else:
                click_zones['escape'] = self.display_button(i == selected, 'back', special='escape')
            if context in ('game', 'netcreate', 'netjoin'):
                if btn_random:
                    click_zones['shake'] = self.display_button(i + 1 == selected, 'shake', special='refresh')
                    click_zones['continue'] = self.display_button(i + 2 == selected, 'continue', special='return')
                else:
                    click_zones['continue'] = self.display_button(i + 1 == selected, 'continue', special='return')
            else:
                if btn_random:
                    click_zones['shake'] = self.display_button(i + 1 == selected, 'shake', special='refresh')
                    click_zones['save'] = self.display_button(i + 2 == selected, 'save', special='return')
                else:
                    click_zones['save'] = self.display_button(i + 1 == selected, 'save', special='return')

            zero = False
            if sets is not None:
                rect = pygame.Rect(self.res_x_16, 3 * self.res_y_16, 2 * self.res_x_16, self.res_x_16)
                self.new_blit_rect2(rect, self.colorset['menu-alternate'], corners='Top')
                self.blit_text2("sets", rect, color=self.colorset['menu-text'])

                rect2 = pygame.Rect(self.res_x_16, 3 * self.res_y_16 + self.res_x_16, 2 * self.res_x_16, self.res_x_16)
                if (selected == 0 and context != 'game') or selected == -1:
                    self.new_blit_rect2(rect2, self.colorset['menu-selected'], padding=self.colorset['padding'] \
                            , border_size=self.colorset['border-size'], border_color=self.colorset['menu-border'], corners='Bottom')
                else:
                    self.new_blit_rect2(rect2, self.colorset['menu-header'], alpha=166, corners='Bottom')
                self.blit_text2(sets, rect2, color=self.colorset['menu-text'])


                if context == 'game':
                    click_zones['F-1'] = rect2
                    shortcuts.append('F-1')

                    zero = True
                    rect = pygame.Rect(self.res_x_16, 7 * self.res_y_16, 2 * self.res_x_16, self.res_x_16)
                    self.new_blit_rect2(rect, self.colorset['menu-alternate'], corners='Top')
                    self.blit_text2("mode", rect, color=self.colorset['menu-text'])

                    rect2 = pygame.Rect(self.res_x_16, 7 * self.res_y_16 + self.res_x_16, 2 * self.res_x_16, self.res_x_16)
                    if selected == 0:
                        self.new_blit_rect2(rect2, self.colorset['menu-selected'], padding=self.colorset['padding'] \
                                , border_size=self.colorset['border-size'], border_color=self.colorset['menu-border'], corners='Bottom')
                    else:
                        self.new_blit_rect2(rect2, self.colorset['menu-header'], alpha=166, corners='Bottom')
                    if competition_mode:
                        mode = "competition"
                    else:
                        mode = "leisure"
                    self.blit_text2(mode, rect2, color=self.colorset['menu-text'])

                click_zones['F0'] = rect2
                shortcuts.append('F0')

            self.update_screen()

            # Read input
            key_pressed = self.rpi.listen_inputs(
                    ['alpha', 'num', 'fx', 'math', 'arrows'],
                    ['PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON', 'EXTRABUTTON',
                    'escape', 'enter', 'backspace', 'tab', 'TOGGLEFULLSCREEN',
                    'space', 'single-click'],
                    events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Compare all Players names zone to clicked zone
            clicked = self.is_clicked(click_zones, key_pressed)

            # Return:
            #   +|F1    Add player
            #   -|F1    Del 1st player
            #   /|F1    Player 1 PNJ
            #   1|F1    Select player 1
            #   *|F1    Player 1 Color
            
            if clicked:
                if "|" in clicked:
                    splitted = clicked.split("|")
                    clic = splitted[0]
                    selected = int(splitted[1][1::])    # 1 from +|F1

                    if clic in PLUS_KEYS + MINUS_KEYS + ['/']:
                        key_pressed = clic
                    else:
                        key_pressed = "enter"
                else:
                    key_pressed = clicked

            # Navigation in menu
            if sets is not None:
                zero = -1
            else:
                zero = 1
            if clicked or key_pressed in UP_KEYS + DOWN_KEYS:
                part = None
            if key_pressed in LEFT_KEYS + RIGHT_KEYS:
                # Right and left go through the whole screen in reading order, as in the menus :
                # sets and mode, each player then its boxes (colour, PNJ, +, -), the buttons at
                # the bottom (they stayed on these)
                boxes = ['*', '/'] + (['+'] if special != 'last' else []) + (['-'] if special != 'first' else [])
                order = [(number, None) for number in ([-1, 0] if sets is not None and context == 'game' else
                                                       [0] if sets is not None else [])]
                for number in range(1, nb_elements + 1):
                    order += [(number, None)] + [(number, box) for box in boxes]
                order += [(number, None) for number in range(nb_elements + 1, nb_elements + (3 if btn_random else 2) + 1)]
                position = order.index((selected, part)) if (selected, part) in order else 0
                selected, part = order[(position + (1 if key_pressed in RIGHT_KEYS else -1)) % len(order)]
            elif part is not None and key_pressed in ENTER_KEYS:
                # A box of the player : as clicked
                clic = part
                if part != '*':
                    key_pressed = part
                part = None if part in ('+', '-') else part
            elif btn_random:
                selected = self.navigate(selected, key_pressed, nb_elements, 3, 3, sound=False, zero=zero)
            else:
                selected = self.navigate(selected, key_pressed, nb_elements, 2, 2, sound=False, zero=zero)
            
            if key_pressed in shortcuts:
                selected = int(key_pressed.replace('F', ''))
                key_pressed = 'enter'

            # Key analysis
            if key_pressed in ESCAPE_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 1):
                if context in ('pref', 'bank'):
                    return sets, 'escape', players_color
                return sets, 'escape', competition_mode, players_color

            if key_pressed in TAB_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 2 and btn_random):
                # Randomize players
                self.play_sound('shakeitbaby')
                random.shuffle(players)

            elif key_pressed in EXTRA_KEYS and selected <= nb_elements:
                # Set player as computer
                players[selected - 1] = self.pnj_name(players[selected - 1])

            elif key_pressed in PLUS_KEYS and (context == 'pref' or nb_elements < 16):
                # Add a player
                i = nb_elements + 1
                while True:
                    new_player = f"{self.lang.translate('Player')} {i}"
                    if new_player not in players:
                        break
                    i += 1

                if bank is None or len(bank) == 0 or len(bank[0]) == 0:
                    players.append(f'{new_player}')
                else:
                    missing_players = [(f'{player}', f'{player}') for player in bank
                                       if player.casefold() not in [name.casefold() for name in players]] + [(new_player, new_player)]

                    if len(missing_players) > 1:
                        new_player = self.dropdown(int(6.5 * self.res_x_16 ), int(2.5 * self.res_y_16), missing_players)

                    if new_player != 'escape':
                        players.append(f'{new_player}')

                selected = i
                btn_random = True

            elif key_pressed in MINUS_KEYS and nb_elements > 1 and selected <= nb_elements:
                # Remove player color
                if players[selected-1] in players_color:
                    players_color.pop(players[selected-1])
                # Remove player
                players.pop(selected - 1)
                selected -= 1
                selected = max(selected, 1)
                if len(players) < 2:
                    btn_random = False

            elif key_pressed in ENTER_KEYS and ((selected == 0 and context != 'game') or selected == -1):
                sets_bank = [(x, x) for x in (1, 2, 3, 5, 10)]
                tmp = self.dropdown(self.res_x_16, 3 * self.res_y_16 + self.res_x_16, sets_bank, width=2 * self.res_x_16)
                if tmp != 'escape':
                    sets = int(tmp)

            elif key_pressed in ENTER_KEYS and selected == -1 and context == 'game':
                if competition_mode:
                    competition_mode = False
                else:
                    competition_mode = True

            elif key_pressed in ENTER_KEYS and selected == 0 and context == 'game':
                if competition_mode:
                    competition_mode = False
                else:
                    competition_mode = True

            elif key_pressed in SAVE_KEYS or (key_pressed in CONTINUE_KEYS and ( key_pressed != 'BTN_NEXTPLAYER' or selected > nb_elements))\
                    or (key_pressed in ENTER_KEYS and selected == nb_elements + 2 and not btn_random) \
                    or (key_pressed in ENTER_KEYS and selected == nb_elements + 3 and btn_random):
                new_players = []
                nb_elements = 0
                for player in players:
                    if len(player) > 0:
                        nb_elements += 1
                        new_players.append(player)
                # Next Screen !
                self.define_constants(nb_elements)
                if context in ('pref', 'bank'):
                    return sets, sorted(new_players), players_color
                elif context in ('netcreate', 'netjoin'):
                    return sets, new_players, True, players_color
                return sets, new_players, competition_mode, players_color
            
            elif ((key_pressed in ENTER_KEYS and clic == "*") or (key_pressed == "*")) and players_color is not None \
                    and selected <= nb_elements:
                # Alone too (a single player went to the edition of his name). The list on the
                # colour of the player (Auto : none chosen)
                current = players_color.get(players[selected - 1])
                current = next((name for name, value in colors_list if current is not None and tuple(value) == tuple(current)),
                               'AUTO COLORSET')
                tmp = self.dropdown(self.res['x'] * 6 / 16,
                                    3 * self.res_y_16,
                                    colors_list,
                                    special='colors',
                                    navigate=current)
                if tmp != 'escape':
                    if tmp == 'AUTO COLORSET':
                        players_color.pop(players[selected - 1], None)
                    else:
                        players_color[str(players[selected - 1])] = tuple([color[1] for color in colors_list if color[0] == str(tmp)][0])

            elif key_pressed in ENTER_KEYS + CONTINUE_KEYS:
                # Edit player name
                if players[selected - 1].startswith(self.lang.translate('Player')):
                    tmp = self.input_value_item('string', '', 1, 12, text='player-name')
                else:
                    tmp = self.input_value_item('string', players[selected - 1], 1, 12, text='player-name')

                if tmp != '' and tmp != 'escape':
                    name = tmp.strip()
                    name = name[:1].upper() + name[1:]
                    others = [player.casefold() for index, player in enumerate(players) if index != selected - 1]
                    if not name:
                        pass
                    elif name.casefold() in others:
                        # The same name twice (Rémi, rémi) : refused
                        self.message([self.lang.translate('player-exists')], 2000, 'menu-ko', 'middle', 'big')
                    else:
                        players[selected - 1] = name


    def blit_border(self, rect, border_color, border_size, corners, border_radius=None, alpha=None):

        if border_color is not None:
            if border_radius is None:
                if self.colorset['border-radius'] == 'max':
                    border_radius = int(rect.height / 2)
                else:
                    border_radius = int(self.colorset['border-radius'])

            if alpha is None:
                alpha = self.alpha
            border_color = (border_color[0], border_color[1], border_color[2], alpha)

            top_left = 0
            top_right = 0
            bottom_left = 0
            bottom_right = 0

            if corners in ('Top', 'TopLeft', 'Left', 'All', 'NotTopRight', 'NotBottomLeft', 'NotBottomRight'):
                top_left = border_radius

            if corners in ('Top', 'TopRight', 'Right', 'All', 'NotTopLeft', 'NotBottomLeft', 'NotBottomRight'):
                top_right = border_radius

            if corners in ('Bottom', 'BottomLeft', 'Left', 'All', 'NotTopLeft', 'NotTopRight', 'NotBottomRight'):
                bottom_left = border_radius

            if corners in ('Bottom', 'BottomRight', 'Right', 'All', 'NotTopLeft', 'NotTopRight', 'NotBottomLeft'):
                bottom_right = border_radius

            surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            self.rect(surface, border_color, surface.get_rect(), border_size, top_left=top_left, top_right=top_right, bottom_left=bottom_left, bottom_right=bottom_right)
            self.blit(surface, rect)

    #@debug
    def new_blit_rect2(self, rectangle, background_color, padding=0, border_color=None, border_size=0, alpha=None, corners=None, border_radius=None, selected=False):
        '''
        Blit rect using rectangle
        '''

        if background_color is None or background_color is False:
            return
        else:
            if selected:
                border_color = self.colorset['menu-border']
                border_size = self.colorset['border-size']
                padding = self.colorset['padding']
                background_color = self.colorset['menu-selected']
            if alpha is None:
                alpha = self.alpha
            color = (background_color[0], background_color[1], background_color[2], alpha)

        top_left = 0
        top_right = 0
        bottom_left = 0
        bottom_right = 0

        if border_radius is None:
            if self.colorset['border-radius'] == 'max':
                border_radius = int(rectangle.height / 2)
            else:
                border_radius = int(self.colorset['border-radius'])

        if corners in ('Top', 'TopLeft', 'Left', 'All', 'NotTopRight', 'NotBottomLeft', 'NotBottomRight'):
            top_left = border_radius

        if corners in ('Top', 'TopRight', 'Right', 'All', 'NotTopLeft', 'NotBottomLeft', 'NotBottomRight'):
            top_right = border_radius

        if corners in ('Bottom', 'BottomLeft', 'Left', 'All', 'NotTopLeft', 'NotTopRight', 'NotBottomRight'):
            bottom_left = border_radius

        if corners in ('Bottom', 'BottomRight', 'Right', 'All', 'NotTopLeft', 'NotTopRight', 'NotBottomLeft'):
            bottom_right = border_radius

        corners = (top_left, top_right, bottom_left, bottom_right)
        if padding == 'max' and border_color is not None:
            self.blit(self.rounded_box(rectangle.width, rectangle.height, tuple(border_color), border_size, corners), rectangle)

        elif padding + border_size > 0:
            if border_color is not None:
                # Draw border
                self.blit(self.rounded_box(rectangle.width, rectangle.height, tuple(border_color), border_size, corners), rectangle)
            # Draw rectangle
            inside_rectangle = rectangle.copy()
            inside_rectangle.x += border_size + padding
            inside_rectangle.y += border_size + padding
            inside_rectangle.width -= 2 * (border_size + padding)
            inside_rectangle.height -= 2 * (border_size + padding)

            self.blit(self.rounded_box(inside_rectangle.width, inside_rectangle.height, color, 0, corners), inside_rectangle)

        else:
            self.blit(self.rounded_box(abs(rectangle.width), abs(rectangle.height), color, border_size, corners), rectangle)

    # Boxes kept : up to 150 000 pixels (600 kB), 64 at most (the cells of the game screens)
    ROUNDED_BOX_KEPT = 150000

    def filled_rect(self, width, height, color, alpha):
        '''
        Rectangle of a color with a transparency (never drawn on : shared). The cells of the
        game screens are the same at each dart : created once
        '''
        if width * height > self.ROUNDED_BOX_KEPT:
            return self.new_filled_rect(width, height, color, alpha)
        return self.kept_filled_rect(width, height, color, alpha)

    @lru_cache(maxsize=64)
    def kept_filled_rect(self, width, height, color, alpha):
        '''
        filled_rect kept
        '''
        return self.new_filled_rect(width, height, color, alpha)

    @staticmethod
    def new_filled_rect(width, height, color, alpha):
        '''
        filled_rect created
        '''
        surface = pygame.Surface((width, height))
        surface.set_alpha(alpha)
        surface.fill(color)
        return surface

    def rounded_box(self, width, height, color, border_size, corners):
        '''
        Rectangle with rounded corners on a transparent surface (never drawn on : shared). The
        same boxes are displayed at each dart : created once
        '''
        if width * height > self.ROUNDED_BOX_KEPT:
            return self.new_rounded_box(width, height, color, border_size, corners)
        return self.kept_rounded_box(width, height, color, border_size, corners)

    @lru_cache(maxsize=64)
    def kept_rounded_box(self, width, height, color, border_size, corners):
        '''
        rounded_box kept
        '''
        return self.new_rounded_box(width, height, color, border_size, corners)

    def new_rounded_box(self, width, height, color, border_size, corners):
        '''
        rounded_box created
        '''
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self.rect(surface, color, surface.get_rect(), border_size, top_left=corners[0], top_right=corners[1], bottom_left=corners[2], bottom_right=corners[3])
        return surface


    def rect(self, surface, color, rect, border_size=0, top_left=None, top_right=None, bottom_left=None, bottom_right=None):
        if PYGAME2:
            pygame.draw.rect(surface
                , color
                , rect
                , width=border_size
                , border_top_left_radius=top_left
                , border_top_right_radius=top_right
                , border_bottom_left_radius=bottom_left
                , border_bottom_right_radius=bottom_right)
        else:
            pygame.draw.rect(surface, color, rect, border_size)

            
    def new_blit_rect(self, pos_x, pos_y, width, height, background_color, border_color=None, Alpha=None, corners=None, border_radius=None, border_size=3):
        '''
        New blit_rect method, usefull for pygame 2.0
        It could display rounded corners (blended by SDL2 through blit : the blending of pygame
        took 180 ms for the frame of a game's description on a Pi 3)
        '''
        if background_color is None:
            return
        if Alpha is None:
            Alpha = 225    # Half transparency
        if border_radius is None:
            if self.colorset['border-radius'] == 'max':
                border_radius = int(height / 2)
            else:
                border_radius = int(self.colorset['border-radius'])

        top_left = 0
        top_right = 0
        bottom_left = 0
        bottom_right = 0

        if corners in ('Top', 'TopLeft', 'Left', 'All'):
            top_left = border_radius

        if corners in ('Top', 'TopRight', 'Right', 'All'):
            top_right = border_radius

        if corners in ('Bottom', 'BottomLeft', 'Left', 'All'):
            bottom_left = border_radius

        if corners in ('Bottom', 'BottomRight', 'Right', 'All'):
            bottom_right = border_radius
        
        if border_color is not None:
            shape_surf = pygame.Surface((width - border_size * 4, height - border_size * 4), pygame.SRCALPHA)

            self.rect(shape_surf
                    , (background_color[0], background_color[1], background_color[2], Alpha)
                    , shape_surf.get_rect()
                    , top_left = top_left - border_size
                    , top_right = top_right - border_size
                    , bottom_left = bottom_left - border_size
                    , bottom_right = bottom_right - border_size
                )
            self.blit(shape_surf, (pos_x + border_size * 2, pos_y + border_size * 2, width + border_size * 2, height + border_size * 2))

            shape_surf = pygame.Surface((width, height), pygame.SRCALPHA)
            self.rect(shape_surf
                , (border_color[0], border_color[1], border_color[2])
                , shape_surf.get_rect()
                , border_size
                , top_left = top_left
                , top_right = top_right
                , bottom_left = bottom_left
                , bottom_right = bottom_right
            )
            self.blit(shape_surf, (pos_x, pos_y, width, height))

        else:
            shape_surf = pygame.Surface((width, height), pygame.SRCALPHA)

            self.rect(shape_surf
                    , (background_color[0], background_color[1], background_color[2], Alpha)
                    , shape_surf.get_rect()
                    , top_left = top_left
                    , top_right = top_right
                    , bottom_left = bottom_left
                    , bottom_right = bottom_right
                )
            self.blit(shape_surf, (pos_x, pos_y, width, height))


    def div_color(self, component, div):
        '''
        Divide component of color
        Maximum is 255
        '''
        return int(min(255, component * div))

    def menu_color(self, color, div=1.5, index=None):
        '''
        Return color
        '''
        if index is None or index % 2 == 1:
            return (self.div_color(color[0], div)
                    , self.div_color(color[1], div)
                    , self.div_color(color[2], div)
                    )
        return color

    def invert_color(self, color):
        '''
        Return inverted color
        '''

        return (255 - int(color[0]), 255 - color[1], 255 - color[2])

    def slider(self, title, value, minimum, maximum, step=1, diviser=1, bar_color=None, dot_color=None, text_color=None):
        '''
        Display a slider
        '''
        if bar_color is None:
            bar_color = self.colorset['menu-buttons']
        if dot_color is None:
            dot_color = self.colorset['menu-shortcut']
        if text_color is None:
            text_color = self.colorset['menu-text-black']
        border_color = self.colorset['menu-border']

        pos_x = int(self.res_x / 4)
        pos_y = int(self.res_y / 16 * 6)
        width = int(self.res_x / 2)
        height = int(self.res_y / 4)
        border_size = 10
        margin = int(self.res_x / 64)

        border_radius = int(height / 8)

        border_rect = pygame.Rect(pos_x, pos_y, width, height)
        title_rect = pygame.Rect(pos_x, pos_y, width, height / 4 + 2 * border_size)
        value_rect = pygame.Rect(pos_x, title_rect.bottom - 2 * border_size, width, height - title_rect.height + 2 * border_size)
        bar = pygame.Rect(value_rect.x + margin, value_rect.y + int(value_rect.height * 4 / 6), value_rect.width - 2 * margin, margin)

        border_radius -= border_size

        self.new_blit_rect2(title_rect, self.colorset['menu-buttons'], corners='Top', border_radius=border_radius, border_size=border_size, alpha=255)
        self.new_blit_rect2(value_rect, self.colorset['menu-selected'], corners='Bottom', border_radius=border_radius, border_size=border_size, alpha=255)

        if border_color is not None:
            # Blit border
            border_radius += border_size
            self.blit_border(border_rect, border_color, border_size, corners='All', border_radius=border_radius, alpha=255)
        self.blit_text2(title, title_rect, color=self.colorset['menu-text-black'])

        pygame.draw.rect(self.screen, bar_color, bar)
        pygame.draw.circle(self.screen, bar_color , (bar.x, bar.y + int(bar.height / 2)), int(bar.height / 2))
        pygame.draw.circle(self.screen, bar_color, (bar.x + bar.width, bar.y + int(bar.height / 2)), int(bar.height / 2))

        if (minimum / diviser) % 1:
            self.blit_text(f'{(minimum / diviser):.1f}', bar.x, bar.y - self.res_y_8, self.res_y_8, self.res_y_8, text_color, align='Left')
        else:
            self.blit_text(f'{int(minimum / diviser)}', bar.x, bar.y - self.res_y_8, self.res_y_8, self.res_y_8, text_color, align='Left')
        self.blit_text(str(int(maximum / diviser)), bar.x + bar.width - self.res_y_8, bar.y - self.res_y_8, self.res_y_8, self.res_y_8, text_color, align='Right')

        rect = pygame.Rect((pos_x - border_size, pos_y - border_size, width + 2 * border_size \
                    , height + 2 * border_size))

        sub = self.screen.subsurface(rect)
        screenshot = pygame.Surface((rect.width, rect.height))
        screenshot.blit(sub, (0, 0))

        click_zones = {}
        width = int(bar.w / (1 + ((maximum - minimum) / step)))
        for segment in range(minimum, maximum + step, step):
            value_offset = 100 * ((segment - minimum) / (maximum - minimum))
            dot_x = bar.x + int(bar.width / 100 * value_offset)
            click_zones[f'S{segment}'] = (dot_x - int(width / 2), bar.y, width, bar.height)

        while True:
            self.blit(screenshot, (rect.x, rect.y))
            value_offset = 100 * ((value - minimum) / (maximum - minimum))
            dot_x = bar.x + int(bar.width / 100 * value_offset)
            dot_y = bar.y + int(bar.height / 2)

            pygame.draw.circle(self.screen, dot_color, (dot_x, dot_y), margin)

            self.blit_text(f"{(value / diviser):.1f}".replace('.0', ''), bar.centerx - self.res_y_16, bar.top - self.res_y_8, self.res_y_8, self.res_y_8, text_color)

            self.update_screen((rect))
            # Read input
            key_pressed = self.rpi.listen_inputs(['arrows'], ['PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON', 'EXTRABUTTON', 'VOLUME-UP', 'VOLUME-DOWN', 'escape', 'enter', 'space', 'single-click'], context='editing')

            clicked = self.is_clicked(click_zones, key_pressed)

            if key_pressed in LEFT_KEYS:
                value = max(minimum, int(value - step))
            elif key_pressed in RIGHT_KEYS:
                value = min(maximum, int(value + step))
            elif key_pressed in ENTER_KEYS:
                return value
            elif key_pressed in ESCAPE_KEYS:
                return 'escape'
            elif clicked and clicked.startswith('S'):
                value = int(clicked[1::])

    def dropdown(self, pos_x, pos_y, values, special=None, navigate=None, width=None):
        '''
        Display a dropdown
        '''

        selected = 1
        max_items = 9
        moy = int((max_items + 1) / 2)
        border_size = 3
        nb_elements = len(values)
        if width is None:
            width = int(3 * self.res_x_16)
        else:
            width = int(width)
        height = self.res_y_16

        if nb_elements > max_items:
            add_arrows = True
        else:
            add_arrows = False

        index = 0        
        for value in values:
            index += 1
            if navigate == value[0]:
                selected = index
                break

        border_radius = self.get_radius(int(height / 2))
        while True:
            key_pressed = ''
            click_zones = {}
            if selected > nb_elements:
                selected = 1
            elif selected < 1:
                selected = nb_elements

            offset = 0
            if add_arrows:
                offset = 1

            rect = pygame.Rect(pos_x - border_size, pos_y - border_size, width + 2 * border_size, height * ( 2 * offset + min(nb_elements, max_items)) + 2 * border_size)
            self.new_blit_rect2(rect, self.colorset['menu-text-black'], alpha=255, corners='All', border_radius=border_radius)

            i_rect = pygame.Rect(rect.x + border_size, rect.y + border_size, rect.w - 2 * border_size, height)
            if add_arrows:
                click_zones['scrollup'] = self.dropdown_item(i_rect, True, "^", special='arrowFirst')
                i_rect.y = i_rect.bottom

            i = 0

            for value in values:
                i += 1
                if nb_elements <= max_items:
                    Go = True
                else:
                    if selected - moy <= 0:
                        if i <= max_items:
                            Go = True
                        else:
                            Go = False
                    elif selected + moy > nb_elements:
                        if i >= nb_elements + 1 - max_items:
                            Go = True
                        else:
                            Go = False
                    elif selected - moy + 1 <= i <= selected + moy - 1:
                        Go = True
                    else:
                        Go = False

                if Go:
                    if offset == 0 and i == 1:
                        FirstLast = 'First'
                    elif offset == 0 and i == nb_elements:
                        FirstLast = 'Last'
                    else:
                        FirstLast = None

                    if special == 'font':
                        # Its file, and its name to show (the font of the theme says it is)
                        click_zones[str(i)] = self.dropdown_item(i_rect, selected == i, value[0], special=special, FirstLast=FirstLast,
                                                                 label=value[1])
                    elif special == 'pattern':
                        click_zones[str(i)] = self.dropdown_item(i_rect, selected == i, value[1], special=special, FirstLast=FirstLast)
                    elif special == 'colors':
                        click_zones[str(i)] = self.dropdown_item(i_rect, selected == i, value[0], special=special, FirstLast=FirstLast,
                                                                 label=value[1])
                    else:
                        click_zones[str(i)] = self.dropdown_item(i_rect, selected == i, value[1], FirstLast=FirstLast)
                    i_rect.y = i_rect.bottom


            if add_arrows:
                click_zones['scrolldown'] = self.dropdown_item(i_rect, True, "v", special='arrowLast')

            #self.update_screen(rect=(rect.x, rect.y, rect.w, rect.h))
            self.update_screen()

            # Read input
            key_pressed = self.rpi.listen_inputs(['arrows'], ['PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON', 'EXTRABUTTON', 'VOLUME-UP', 'VOLUME-DOWN', 'escape', 'enter', 'space', 'single-click'], context='editing')

            # Click cases
            clicked = self.is_clicked(click_zones, key_pressed)

            # Navigation
            # Right and left too : a vertical list in reading order (a knob set on them did nothing)
            selected = self.navigate(selected, key_pressed, nb_elements, 0, 0, left_right=True)

            if clicked:
                if clicked == 'scrolldown':
                    selected += 1
                elif clicked == 'scrollup':
                    selected -= 1
                else:
                    selected = int(clicked)
                    return values[selected - 1][0]
            elif key_pressed in ENTER_KEYS:
                return values[selected - 1][0]
            elif key_pressed in ESCAPE_KEYS:
                return 'escape'

    def dropdown_item(self, rect, selected, value, special=False, FirstLast=None, label=None):
        '''
        Display drop down item
        '''
        if special == 'arrowFirst':
            color = self.colorset['menu-alternate']
            FirstLast = 'First'
        elif special == 'arrowLast':
            color = self.colorset['menu-alternate']
            FirstLast = 'Last'
        elif selected:
            color = self.colorset['menu-selected']
        else:
            color = self.colorset['menu-buttons']

        if FirstLast == 'First':
            corners = 'Top'
        elif FirstLast == 'Last':
            corners = 'Bottom'
        else:
            corners = 'None'

        if special == 'colors':
            brdr_size = 0
            if selected:
                brdr_size = 4
            try:
                self.new_blit_rect2(rect, pygame.Color(value), corners=corners, border_size=brdr_size, border_color= self.colorset['menu-border'])
            except:
                # La coleur n'est pas geree par pygame
                self.new_blit_rect2(rect, color, corners=corners, border_size=brdr_size, border_color= self.colorset['menu-border'])
        else:
            self.new_blit_rect2(rect, color, corners=corners)

        if selected:
            text_color = self.colorset['menu-text-white']
        else:
            text_color = self.colorset['menu-text-black']
        if special == 'colors':
            # Its name readable on the colour : black on a light one (white, gold...), else white
            try:
                shown = pygame.Color(value)
                text_color = (0, 0, 0) if 0.299 * shown.r + 0.587 * shown.g + 0.114 * shown.b > 150 else (255, 255, 255)
            except ValueError:
                pass

        if special == 'font':
            minus = int(rect.height * 0.1)
            rect2 = rect.copy()
            rect2.y += minus
            rect2.height -= 2 * minus
            self.blit_text2(label, rect2, text_color, font=self.font_file(value))
        elif special == 'pattern':
            self.blit_text2(value, rect, text_color, image=f'patterns/{value}')
        else:
            # (a list of colours : the name shown of a value which is not a colour, Off... ; not
            # its (r, g, b), given by the colours of the players and of the segments)
            self.blit_text2(label if isinstance(label, str) else value, rect, text_color)
        return (rect.x, rect.y, rect.w, rect.h)

    def display_button(self, selected, text, special):
        '''
        Display buttons at bottom of menus : escape, save, continue, ...
        '''

        width = int(self.res['x'] / 8)

        if special in ('tab1', 'escape'):
            pos_x = int(self.res['x'] / 8)
        elif special in ('tab2', 'refresh'):
            pos_x = int(self.res['x'] / 2 - width / 2)
        #elif special == 'return':
        else:
            pos_x = int(self.res['x'] * 7 / 8 - width)

        if special.startswith('tab'):
            pos_y = int(self.res['y'] / 32 * 3.5)
        else:
            pos_y = int(self.res['y'] / 32 * 29)
        height = self.res_y_16

        rect = pygame.Rect(pos_x, pos_y, width, height)

        if selected:
            background_color = self.colorset['menu-selected']
            text_color = self.colorset['menu-text-white']
            border_color = self.colorset['menu-border']
            border_size = self.colorset['border-size']
            padding = self.colorset['padding']
        else:
            background_color = self.colorset['menu-buttons']
            text_color = self.colorset['menu-text-black']
            border_color = None
            border_size = 0
            padding = 0

        if self.colorset['button-radius'] == 'max':
            border_radius = int(height / 2)
        else:
            border_radius = min(int(height / 2), int(self.colorset['button-radius']))

        self.new_blit_rect2(rect, background_color, padding, border_color, border_size, corners='All', border_radius=border_radius)
        self.blit_text2(text, rect, color=text_color)

        return (rect[0], rect[1], rect[2], rect[3])

    def get_radius(self, value):
        if self.colorset['border-radius'] == 'max':
            return int(value)
        elif int(self.colorset['border-radius']) > int(value):
            return int(value)
        else:
            return int(self.colorset['border-radius'])

    def compute_corners(self, item_id, total, selected, collapsed, alternate=False):
        if alternate:
            offset = 2
        else:
            offset = 1

        if collapsed:
            if item_id == selected - offset:
                corners = 'Bottom'
                if item_id <= offset:
                    corners = 'All'
            elif item_id == selected + offset:
                corners = 'Top'
                if item_id > total - offset:
                    corners = 'All'
            elif item_id <= offset:
                corners = 'Top'
            elif item_id > total - offset:
                corners = 'Bottom'
            else:
                corners = 'None'
            return corners
        else:
            return 'All'


    def adapt_corners(self, corners, operation, operation2=None):
        if operation == 'AddRight':
            if corners == 'All' and operation2 == 'NotLeft':
                return 'Right'
            elif corners == 'All' and operation2 == 'NotRight':
                return 'Left'
            elif corners == 'All':
                return corners
            elif corners == 'Top':
                if operation2 == 'NotLeft':
                    return 'Right'
                else:
                    return 'NotBottomLeft'
            elif corners == 'Bottom':
                if operation2 == 'NotLeft':
                    return 'Right'
                else:
                    return 'NotTopLeft'
            elif corners == 'None':
                return 'Right'
            else:
                return corners
        elif operation == 'NotRight':
            if corners == 'Bottom':
                return 'BottomLeft'
            elif corners == 'Top':
                return 'TopLeft'
            elif corners == 'All':
                return 'Left'
            else:
                return corners
        elif operation == 'NotLeft':
            if corners == 'Bottom':
                return 'BottomRight'
            elif corners == 'Top':
                return 'TopRight'
            elif corners == 'All':
                return 'Right'
            else:
                return corners
        else:
            return corners

    def pouet(self):
        self.update_screen()
        self.wait_touch()

    #@debug
    def st_item(self, shortcut, text, rect, padding=0, border_size=0, border_color=None, alpha=None, divider=None, corners=None):
        '''
        Display one line : Shortcut | Text
        Shortcut and text must be :
            (background_color, text_value, text_color)
        '''

        s_rect = rect.copy()
        s_rect.width = s_rect.height

        t_rect = pygame.Rect(s_rect.right, s_rect.y, rect.w - s_rect.w, s_rect.h)
        
        pict_shortcut = self.colorset['main-sub-menu-shortcuts']
        align_text = self.colorset['main-sub-menu-text-align']
        
        if border_size + padding > 0:
            minus = border_size + padding
            if self.colorset['border-radius'] == 'max':
                border_radius = int(rect.h / 2) - minus
            else:
                border_radius = int(self.colorset['border-radius']) - minus

            border_radius = max(border_radius, 0)

            if border_color is not None:
                # Blit border
                self.blit_border(rect, border_color, border_size, corners=corners)

            inside_rect = pygame.Rect(rect.x + minus, rect.y + minus, rect.w - 2 * minus, rect.h - 2 * minus)
            self.new_blit_rect2(inside_rect, text[0], alpha=alpha, corners=corners, border_radius=border_radius)

            # Compute missing values
            if shortcut[1] is not None and pict_shortcut is not None:
                inside_rect.width = inside_rect.height + minus
                # Display shortcut
                self.new_blit_rect2(inside_rect, shortcut[0], alpha=alpha, corners=self.adapt_corners(corners, 'AddRight'), border_radius=border_radius)
                if pict_shortcut != '':
                    self.blit_text2(pict_shortcut, s_rect, color=shortcut[2])
                else:
                    self.blit_text2(shortcut[1], s_rect, color=shortcut[2])
                self.blit_text2(text[1], t_rect, color=text[2], align=align_text, divider=divider)
                
            else:
                self.blit_text2(text[1], rect, color=text[2], align=align_text, divider=divider)

        elif shortcut[1] is None or pict_shortcut is None:
            # Display text
            self.new_blit_rect2(rect, text[0], alpha=alpha, corners=corners)
            self.blit_text2(text[1], rect, color=text[2], align=align_text, divider=divider)
        else:
            # Display text
            self.new_blit_rect2(rect, text[0], alpha=alpha, corners=self.adapt_corners(corners, 'All'))            
            self.blit_text2(text[1], t_rect, color=text[2], align=align_text, divider=divider)

            ## Display shortcut
            self.new_blit_rect2(s_rect, shortcut[0], alpha=alpha, corners='All')
            if pict_shortcut != '':
                self.blit_text2(pict_shortcut, s_rect, color=shortcut[2], divider=divider)
            else:
                self.blit_text2(shortcut[1], s_rect, color=shortcut[2], divider=divider)


    #@debug
    def svt_item(self, shortcut, value, text, rect, padding=0, border_size=0, border_color=None, alpha=None, ratio=0.2):
        '''
        Display one line : Shortcut | Value | Text
        Shortcut, value and text must be :
            (background_color, text_value, text_color)
        '''

        s_rect = rect.copy()
        s_rect.width = s_rect.height

        v_rect = pygame.Rect(s_rect.right, s_rect.y, int(rect.w * ratio), s_rect.h)
        t_rect = pygame.Rect(v_rect.right, s_rect.y, rect.w - v_rect.w - s_rect.w, s_rect.h)
        
        pict_shortcut = self.colorset['parametrage-menu-shortcuts']
        align_text = self.colorset['parametrage-menu-text-align']

        if border_size + padding > 0:
            minus = border_size + padding
            if border_color is not None:
                # Blit border
                self.blit_border(rect, border_color, border_size, corners='All')
            if self.colorset['border-radius'] == 'max':
                border_radius = int(rect.h / 2) - minus
            else:
                border_radius = int(self.colorset['border-radius']) - minus

            border_radius = max(border_radius, 0)

            inside_rect = pygame.Rect(rect.x + minus, s_rect.y + minus, rect.w - 2 * minus, s_rect.h - 2 * minus)            
            
            if pict_shortcut is not None :
                # Display text
                self.new_blit_rect2(inside_rect, text[0], alpha=alpha, corners='All', border_radius=border_radius)
                self.blit_text2(text[1], t_rect, color=text[2], align=align_text)

                # Display value
                inside_rect = pygame.Rect(s_rect.x + minus, v_rect.y + minus, v_rect.w + s_rect.w - minus, inside_rect.h)
                self.new_blit_rect2(inside_rect, value[0], alpha=alpha, border_radius=border_radius, corners='All')
                self.blit_text2(value[1], v_rect, color=value[2])
            
                # Display shortcut
                inside_rect = pygame.Rect(s_rect.x + minus, s_rect.y + minus, s_rect.w - minus, s_rect.h - 2 * minus)
                self.new_blit_rect2(inside_rect, shortcut[0], alpha=alpha, corners='All', border_radius=border_radius)
                if pict_shortcut != '':
                    self.blit_text2(pict_shortcut, s_rect, color=shortcut[2])
                else:
                    self.blit_text2(shortcut[1], s_rect, color=shortcut[2])
                
            else:
                # Display text
                self.new_blit_rect2(inside_rect, text[0], alpha=alpha, corners='All', border_radius=border_radius)
                t_rect.x -= s_rect.w
                t_rect.w += s_rect.w
                self.blit_text2(text[1], t_rect, color=text[2], align=align_text)

                # Display value
                inside_rect = pygame.Rect(s_rect.x + minus, v_rect.y + minus, v_rect.w - minus, inside_rect.h)                
                self.new_blit_rect2(inside_rect, value[0], alpha=alpha, border_radius=border_radius, corners='All')                
                v_rect.x = s_rect.x
                self.blit_text2(value[1], v_rect, color=value[2])
                
        else:
            if pict_shortcut is not None : 
                # Display text
                self.new_blit_rect2(rect, text[0], alpha=alpha, corners='All')
                self.blit_text2(text[1], t_rect, color=text[2], align=align_text)
                
                # Display value
                v_rect.x -= s_rect.w
                v_rect.w += s_rect.w
                self.new_blit_rect2(v_rect, value[0], alpha=alpha, corners='All')
                v_rect.x += s_rect.w
                v_rect.w -= s_rect.w
                self.blit_text2(value[1], v_rect, color=value[2], align='Center')
                
                # Display shortcut
                self.new_blit_rect2(s_rect, shortcut[0], alpha=alpha, corners='All')                
                if pict_shortcut != '':
                    self.blit_text2(pict_shortcut, s_rect, color=shortcut[2])
                else:
                    self.blit_text2(shortcut[1], s_rect, color=shortcut[2])
            else:
                # Display text
                self.new_blit_rect2(rect, text[0], alpha=alpha, corners='All')
                t_rect.x -= s_rect.w
                t_rect.w += s_rect.w
                self.blit_text2(text[1], t_rect, color=text[2], align=align_text)
                
                # Display value
                v_rect.x = s_rect.x
                self.new_blit_rect2(v_rect, value[0], alpha=alpha, corners='All')
                v_rect.x = s_rect.x
                self.blit_text2(value[1], v_rect, color=value[2], align='Center')
                

    def game_item(self, item, favorite):
        '''
        Special item for favorite games
        2 columns

        item is : (item_id, total, selected)
        favorite is Shortcut / Game name / value=True/False (True : the game has favorites)
        '''
        
        pict_shortcut = self.colorset['parametrage-menu-shortcuts']
        align_text = self.colorset['parametrage-menu-text-align']

        width = 2 * self.res_x_16
        height = int(22 * self.res_y_16 / max(item[1], 20))

        pos_y = 3 * self.res_y_16 + height * ((item[0] - 1) % (item[1] / 2))

        if item[0] % 2 == 1:
            pos_x = self.mid_x - self.res_x_16 - width
        else:
            pos_x = self.mid_x + self.res_x_16

        pos_y = 3 * self.res_y_16 + height * (int((item[0] + 1) / 2) - 1)
    

        if item[0] == item[2]:
            value_bg_color = self.menu_color(self.colorset['menu-selected'])
        else:
            value_bg_color = self.menu_color(self.colorset['menu-buttons'], index=(item[0] + 1) // 2 + 1)

        radius = self.get_radius(height / 2)

        if item[0] == item[2]:
            minus = self.colorset['border-size'] + self.colorset['padding']
            # Selected item
            if favorite[2]:
                shortcut_bg_color = self.colorset['menu-ok']
            else:
                shortcut_bg_color = self.colorset['menu-ko']
            value_bg_color = self.menu_color(self.colorset['menu-selected'])
            shortcut_text_color = self.colorset['menu-text-white']
            value_text_color = self.colorset['menu-text-white']

            if self.colorset['border-radius'] == 'max':
                border_radius = int(height / 2) - minus
            else:
                border_radius = int(self.colorset['border-radius']) - minus

            border_radius = max(border_radius, 0)

            # Display border
            rect = pygame.Rect(pos_x, pos_y, width, height)
            self.blit_border(rect, self.colorset['menu-border'] , self.colorset['border-size'], corners='All')

            # Display value
            rect = pygame.Rect(pos_x + minus
                    , pos_y + minus
                    , width - 2 * minus
                    , height - 2 * minus)
            self.new_blit_rect2(rect, value_bg_color, corners='All', border_radius=border_radius)
            # To keep same text size
            rect2 = pygame.Rect(pos_x + height, pos_y, width - height, height)
            self.blit_text2(favorite[1], rect2, color=value_text_color, align=align_text)
            
            # Display shortcut
            rect = pygame.Rect(pos_x + minus
                    , pos_y + minus
                    , height - minus
                    , height - 2 * minus)
            self.new_blit_rect2(rect, shortcut_bg_color, corners='All', border_radius=border_radius)
            # To keep same text size
            rect2 = pygame.Rect(pos_x, pos_y, height, height)
            shortcut = ''            
            if pict_shortcut is not None:
                if pict_shortcut != '':
                    self.blit_text2(pict_shortcut, rect2, color=shortcut_text_color)
                else:
                    self.blit_text2(favorite[0], rect2, color=shortcut_text_color)
            else:
                self.blit_text2(shortcut, rect2, color=shortcut_text_color)

        else:
            corners = self.compute_corners(item[0], item[1], item[2], True, alternate=True)
            # Change color according to index
            if favorite[2]:
                shortcut_bg_color = self.colorset['menu-ok']
            else:
                shortcut_bg_color = self.colorset['menu-ko']
            shortcut_text_color = self.colorset['menu-text-black']
            value_text_color = self.colorset['menu-text-black']

            # Display value
            rect = pygame.Rect(pos_x, pos_y, width, height)
            self.new_blit_rect2(rect, value_bg_color, corners=corners, border_radius=radius)

            # Display shortcut
            rect.width = rect.h
            self.new_blit_rect2(rect, shortcut_bg_color, corners=self.adapt_corners(corners, 'AddRight'), border_radius=radius)
            #self.blit_text2(favorite[0], rect, color=shortcut_text_color)
            shortcut = ''            
            if pict_shortcut is not None:
                if pict_shortcut != '':
                    self.blit_text2(pict_shortcut, rect, color=shortcut_text_color)
                else:
                    self.blit_text2(favorite[0], rect, color=shortcut_text_color)
            else:
                self.blit_text2(shortcut, rect, color=shortcut_text_color)
            rect = pygame.Rect(pos_x + height, pos_y, width - height, height)
            self.blit_text2(favorite[1], rect, color=value_text_color)

        return (pos_x, pos_y, width, height)

    def button_item(self, item, value, text, alpha):
        '''
        Special item for buttons
        Text and value have same width
        2 columns

        item is : (item_id, total, selected)
        '''

        if alpha is None:
            alpha = self.alpha

        width = self.mid_x - 2 * self.res_x_16
        height = int(22 * self.res_y_16 / item[1])

        if item[0] > int(item[1] / 2):
            pos_x = self.res_x_16 + self.mid_x
        else:
            pos_x = self.res_x_16

        pos_y = 3 * self.res_y_16 + height * ((item[0] - 1) % (item[1] / 2))

        if item[0] % 2 == 1:
            pos_x = self.res_x_16
        else:
            pos_x = self.res_x_16 + self.mid_x

        pos_y = 3 * self.res_y_16 + height * (int((item[0] + 1) / 2) - 1)
    

        if item[0] == item[2]:
            minus = self.colorset['border-size'] + self.colorset['padding']
            # Selected item
            item_bg_color = self.menu_color(self.colorset['menu-selected'])
            value_bg_color = self.menu_color(self.colorset['menu-selected'])
            item_text_color = self.colorset['menu-text-white']
            value_text_color = self.colorset['menu-text-white']

            # Display border
            rect = pygame.Rect(pos_x, pos_y, width, height)
            self.blit_border(rect, self.colorset['menu-border'] , self.colorset['border-size'], corners='All')

            # Display text
            rect = pygame.Rect(pos_x + minus
                    , pos_y + minus
                    , int(width / 2) - minus
                    , height - 2 * minus)
            self.new_blit_rect2(rect, item_bg_color, alpha=alpha, corners='Left')
            # To keep same text size
            rect2 = pygame.Rect(pos_x, pos_y, int(width / 2), height)
            self.blit_text2(text, rect2, color=value_text_color)

            # Display value
            rect = pygame.Rect(pos_x + int(width / 2)
                    , pos_y + minus
                    , int(width / 2) - minus
                    , height - 2 * minus)
            self.new_blit_rect2(rect, value_bg_color, alpha=alpha, corners='Right')
            # To keep same text size
            rect2 = pygame.Rect(pos_x + int(width / 2), pos_y, int(width / 2), height)
            self.blit_text2(value, rect2, color=item_text_color)
        else:
            corners = self.compute_corners(item[0], item[1], item[2], collapsed=True, alternate=True)

            # Change color according to index
            item_bg_color = self.menu_color(self.colorset['menu-buttons'], index=item[0] + 1)
            value_bg_color = self.menu_color(self.colorset['menu-shortcut'], index=item[0] + 1)
            item_text_color = self.colorset['menu-text-black']
            value_text_color = self.colorset['menu-text-black']

            # Display text
            rect = pygame.Rect(pos_x, pos_y, int(width / 2), height)
            self.new_blit_rect2(rect, item_bg_color, alpha=alpha, corners=self.adapt_corners(corners, 'NotRight'))
            self.blit_text2(text, rect, color=value_text_color)

            # Display value
            rect = pygame.Rect(pos_x + int(width / 2), pos_y, int(width / 2), height)
            self.new_blit_rect2(rect, value_bg_color, alpha=alpha, corners=self.adapt_corners(corners, 'NotLeft'))
            self.blit_text2(value, rect, color=item_text_color)

        return (pos_x, pos_y, width, height)

    # Border of the box of a player reached by right and left (colour, PNJ, +, -)
    PLAYER_PART_COLOR = (255, 215, 0)

    def player_item(self, item, shortcut, name, special, alpha=None, specific_color=None, part=None):
        '''
        Display Players' menu items
        item is : (item_id, total, selected)
        part : box of the selected player reached by right and left ('*' colour, '/' PNJ,
        '+', '-'), a golden border around it
        '''
        
        pict_shortcut = self.colorset['players-menu-shortcuts']
        align_text = self.colorset['players-menu-text-align']
        
        if alpha is None:
            alpha = self.alpha

        click_zones = []

        min_y = 3 * self.res_y_16
        max_y = 13 * self.res_y_16
        
        pos_x = 4 * self.res_x_16
        width = self.res_x - 2 * pos_x

        height = min(int(self.res['y'] / 14), int((max_y - min_y) / item[1]))
        pos_y = min_y + height * (item[0] - 1)

        minus = self.colorset['border-size'] + self.colorset['padding']

        shortcut_bg_color = self.colorset['menu-shortcut']
        
        #if specific_color:
        if specific_color is not None and name in specific_color:
            specific_backcolor = specific_color[name]
            specific_lbl_color = ""
        else:
            specific_backcolor = self.colorset['menu-inactive']
            specific_lbl_color = "AUTO"
        
        if special == 'first':
            minus_bg_color = self.colorset['menu-inactive']
        else:
            minus_bg_color = self.colorset['menu-ko']
        
        if special == 'last':
            plus_bg_color = self.colorset['menu-inactive']
        else:
            plus_bg_color = self.colorset['menu-ok']

        radius = self.get_radius(height / 2)
        
        # Highlight menu
        if item[0] == item[2]:
            shortcut_text_color = self.colorset['menu-text-black']
            text_color = self.colorset['menu-text-white']

            inside_y = pos_y + minus
            inside_h = height - 2 * minus
            
            rect = pygame.Rect(pos_x, pos_y, width + height + minus, height)
            self.blit_border(rect, self.colorset['menu-border'], self.colorset['border-size'], corners='All')

            # Display Firstname
            firstname_x = pos_x + minus
            rect = pygame.Rect(firstname_x, inside_y, width - 3 * height - minus, inside_h)
            self.new_blit_rect2(rect, self.colorset['menu-selected'], alpha=alpha, corners='Left')
            
            if pict_shortcut is None:
                rect.x -= inside_h
                rect.w += inside_h
            else:
                rect.x += height
                rect.width -= height
                
            self.blit_text2(name, rect, color=text_color, align=align_text)

            if pict_shortcut is not None :
                # Display Shortcut
                shortcut_x = pos_x + minus
                rect = pygame.Rect(shortcut_x, inside_y, height - minus, inside_h)
                self.new_blit_rect2(rect, shortcut_bg_color, alpha=alpha, corners='All')
                if pict_shortcut != '':
                    self.blit_text2(pict_shortcut, rect, color=shortcut_text_color)
                else:
                    self.blit_text2(shortcut, rect, color=shortcut_text_color)
                    
            specific_x = firstname_x + width - 3 * height 
            rect.x += height
            rect.width -= height
            
            # Color box
            rect = pygame.Rect(specific_x, inside_y, height, inside_h)
            self.new_blit_rect2(rect, specific_backcolor, alpha=alpha)
            self.blit_text2(specific_lbl_color, rect, color=text_color)
            
            # Pnj box
            pnj_x = specific_x + height
            rect = pygame.Rect(pnj_x, inside_y, height, inside_h)
            self.new_blit_rect2(rect, shortcut_bg_color, alpha=alpha)
            self.blit_text2('PNJ', rect, color=text_color)

            # Plus box
            plus_x = pnj_x + height
            rect = pygame.Rect(plus_x, inside_y, height, inside_h)
            self.new_blit_rect2(rect, plus_bg_color, alpha=alpha)
            self.blit_text2('+', rect, color=text_color)

            # Minus box
            minus_x = plus_x + height
            rect = pygame.Rect(minus_x, inside_y, height - minus, inside_h)
            self.new_blit_rect2(rect, minus_bg_color, alpha=alpha, corners='Right')
            self.blit_text2('-', rect, color=text_color)

            boxes = {'*': specific_x, '/': pnj_x, '+': plus_x, '-': minus_x}
            if part in boxes:
                box_width = height - minus if part == '-' else height
                pygame.draw.rect(self.screen, self.PLAYER_PART_COLOR, (boxes[part], inside_y, box_width, inside_h),
                                 max(2, int(self.colorset['border-size'])))

        else:
            corners = self.compute_corners(item[0], item[1], item[2], collapsed=True)
            shortcut_text_color = self.colorset['menu-text-white']
            text_color = self.colorset['menu-text-black']
            shortcut_color = self.menu_color(shortcut_bg_color, index=item[0] + 1)
            plus_color = self.menu_color(plus_bg_color, index=item[0] + 1)
            minus_color = self.menu_color(minus_bg_color, index=item[0] + 1)
            player_color = self.menu_color(self.colorset['menu-buttons'], index=item[0] + 1)

            # Display Firstname
            firstname_x = pos_x + height
            rect = pygame.Rect(firstname_x - height, pos_y, width - 3 * height, height)
            self.new_blit_rect2(rect, player_color, alpha=alpha, corners='Left', border_radius=radius)
            
            if pict_shortcut is not None :
                rect = pygame.Rect(firstname_x, pos_y, width - 4 * height, height)
            
            if pict_shortcut is None :
                rect.x -= height - 2 * minus
                rect.w += height - 2
            self.blit_text2(name, rect, color=text_color, align=align_text)

            if pict_shortcut is not None :
                # Display Shortcut
                rect = pygame.Rect(pos_x, pos_y, height, height)
                self.new_blit_rect2(rect, shortcut_color, alpha=alpha, corners='All', border_radius=radius)
                if pict_shortcut != '':
                    self.blit_text2(pict_shortcut, rect, color=shortcut_text_color)
                else:
                    self.blit_text2(shortcut, rect, color=shortcut_text_color)
                                  
            # Color box
            specific_x = firstname_x + width - 4 * height  
            rect = pygame.Rect(specific_x, pos_y, height, height)
            self.new_blit_rect2(rect, specific_backcolor, alpha=alpha)
            self.blit_text2(specific_lbl_color, rect, color=text_color)            
                
            # Pnj box
            pnj_x = specific_x + height
            rect = pygame.Rect(pnj_x, pos_y, height, height)
            self.new_blit_rect2(rect, shortcut_color, alpha=alpha)
            self.blit_text2('PNJ', rect, color=text_color)

            # Plus box
            plus_x = pnj_x + height
            rect = pygame.Rect(plus_x, pos_y, height, height)
            self.new_blit_rect2(rect, plus_color, alpha=alpha)
            self.blit_text2('+', rect, color=text_color)

            # Minus box
            minus_x = plus_x + height
            rect = pygame.Rect(minus_x, pos_y, height, height)
            self.new_blit_rect2(rect, minus_color, alpha=alpha, corners='Right', border_radius=radius)
            self.blit_text2('-', rect, color=text_color)

        click_zones.append(('*|' + shortcut, (specific_x, pos_y, height, height)))
            
        if special != 'first':
            click_zones.append(('-|' + shortcut, (minus_x, pos_y, height, height)))
        if special != 'last':
            click_zones.append(('+|' + shortcut, (plus_x, pos_y, height, height)))

        click_zones.append(('/|' + shortcut, (pnj_x, pos_y, height, height)))
        click_zones.append((shortcut, (firstname_x, pos_y, width - 4 * height, height)))

        return click_zones

    def logo_item(self, item, logo, item_per_line, align, limit_height=None, Alpha=None, menu=False, border_radius=50, available=True):
        '''
        Print games' logo
        '''

        if align == 'Left':
            pos_x = int(self.res_x_16 / 2)
            max_x = 8 * self.res_x_16 - pos_x
        else:
            pos_x = 3 * self.res_x_16
            max_x = 13 * self.res_x_16
        max_w = max_x - pos_x

        pos_y = 3 * self.res_y_16
        max_y = 13 * self.res_y_16
        max_h = max_y - pos_y

        item_per_col = (item[1] // item_per_line) + 1

        # Max size of logo
        height = (max_w // (item_per_line+1))

        # To center logo on available surface
        pos_x += (max_w - item_per_line * height) / 2
        if menu:
            pos_y = (self.res_y - height) / 2
        else:
            pos_y += (max_h - item_per_col * height) / 2

        # Position of the logo
        pos_y += ((item[0] - 1) // item_per_line) * height
        pos_x += ((item[0] - 1) % item_per_line) * height

        selected_color = self.colorset['menu-selected']
        inactive_color = self.colorset['menu-inactive']
        border_color = self.colorset['menu-border']
        
        if not available:
            selected_color = self.colorset['menu-warning']
            border_color = self.colorset['menu-warning']

        rect = pygame.Rect(pos_x, pos_y, height, height)
        if item[0] == item[2]:
            # Selected logo
            if self.colorset['border-size'] + self.colorset['padding'] > 0:
                minus = self.colorset['border-size'] + self.colorset['padding']
                if border_color is not None:
                    # Blit border
                    self.blit_border(rect, border_color, int(self.colorset['border-size']), border_radius=border_radius, corners='All')
                rect2 = pygame.Rect(pos_x + minus, pos_y + minus, height - 2 * minus, height - 2 * minus)
                border_radius -= self.colorset['padding']
                border_radius -= self.colorset['border-size']

            else:
                rect2 = rect
            self.new_blit_rect2(rect2, selected_color, alpha=Alpha, border_radius=border_radius, corners='All')
        else:
            # Not selected
            self.new_blit_rect2(rect, inactive_color, alpha=20, border_radius=border_radius, corners='All')

        self.display_image(self.file_class.get_full_filename(f'logos_menu/{logo}', 'images'), pos_x, pos_y, height, height, True, False, False, enabledImage=available)

        return (pos_x, pos_y, height, height)

    # Zone of the tiles of the list of games when the files do not give one : the left of the
    # screen, the description of the game on the right (from 7/16 of the width)
    GAME_TILES_AREA = {'x': '3.125%', 'y': '18.75%', 'width': '40%', 'height': '62.5%'}

    def game_tiles(self, games, columns, own):
        '''
        Tiles of the list of games drawn with the style of the menu games (section 7.6) : None
        if its style is classic (the logos as always). All on the screen : square, the logo
        of the game above its name ; when the rows are too many for squares, as wide as the
        columns, the logo on the left of the name
        '''
        menus = self.menus()
        menu = menus.menu('games')
        if str(menu.get('style') or 'classic') == 'classic' or not games:
            return None
        width, height = self.screen.get_size()
        units = cmenustyle.Units((width, height), menus.data.get('resolution'))
        area = cmenustyle.merge(self.GAME_TILES_AREA, own.get('area') or {})
        gap = cmenustyle.merge(cmenustyle.GAP_DEFAULT, own.get('gap') or {})
        rows = math.ceil(len(games) / columns)
        area_w, area_h = units.length(area['width'], 'x'), units.length(area['height'], 'y')
        gap_x, gap_y = units.length(gap['x'], 'x'), units.length(gap['y'], 'y')
        column_w = (area_w - (columns - 1) * gap_x) / columns
        tile_h = max(1.0, min(column_w, (area_h - (rows - 1) * gap_y) / rows))
        square = tile_h >= column_w * 0.8
        tile_w = tile_h if square else column_w
        # Sizes in pixels of this screen : no reference resolution for this layout
        description = {'layout': 'grid', 'columns': columns, 'align': own.get('align') or 'center',
                       'area': {key: units.length(area[key], 'x' if key in ('x', 'width') else 'y') / (width if key in ('x', 'width') else height)
                                for key in ('x', 'y', 'width', 'height')},
                       'gap': {'x': gap_x / width, 'y': gap_y / height},
                       'button_size': {'width': tile_w / column_w, 'height': tile_h / height}}
        rects = cmenustyle.layout(description, [{}] * len(games), (width, height))[0]
        # Text sizes in percent : parts of the screen, whatever the unit of the file
        look = {'icon': {'position': 'top', 'size': 0.72}, 'text': {'size': f'{tile_h * 13 / height:.3f}%'}} if square else \
            {'icon': {'position': 'left', 'size': 0.86}, 'text': {'size': f'{tile_h * 30 / height:.3f}%'}}
        style = cmenustyle.merge(look, self.button_style(menu, {}))
        logos = [self.file_class.get_full_filename(f"logos_menu/{self.favorite_entry(game)[0].replace(' ', '_')}", 'images')
                 for game in games]
        return {'rects': rects, 'style': style, 'logos': logos,
                'names': [self.favorite_entry_label(game).replace('_', ' ') for game in games],
                'units': units, 'composites': {}}

    def game_tile(self, tiles, pristine, index, look):
        '''
        A tile of the list of games in a state, drawn on its piece of background once (an
        opaque image, copied at each move) : returns its rectangle
        '''
        painter = self.menu_painter()
        rect = pygame.Rect(tiles['rects'][index])
        target = painter.placed(rect, tiles['style'], look)[1].clip(self.screen.get_rect())
        key = (index, look, tuple(target))
        composite = tiles['composites'].get(key)
        if composite is None:
            composite = pristine.subsurface(target).copy()
            painter.draw_button(composite, rect.move(-target.x, -target.y), tiles['style'], tiles['names'][index - 1],
                                tiles['logos'][index - 1], look, tiles['units'])
            tiles['composites'][key] = composite
        self.screen.blit(composite, target)
        return (rect.x, rect.y, rect.width, rect.height)

    def menu_item(self, item, value, space=0, align=None, collapsed=False, exit=True, special=None, border_color=None, valid=None, item_per_line=None, limit_height=None, divider=None, tabs=False, column=None):
        '''
        Display menu's item (new version)

        item is : (item_id, total, selected)
        value is : (shortcut, text, button_type, value)
        column : (column 0 or 1, rows of a column, row in it) : the items in two columns
        '''
        is_selected = item[0] == item[2]
        if column is not None:
            # Its place in its column : the rows of a column instead of all the items
            column_index, rows, row = column
            start = item[0] - row
            # The selected one, in this column (else none : the rounded corners of the others)
            item = (row, rows, item[2] - start if start < item[2] <= start + rows else 0)

        padding = self.margin
        vertical_margin = 0 # Margin between 2 lines

        # ItemType:
        #   BTN_CHECK    (1) : Check Box
        #   BTN_CHOICE   (2) : Text (not editable)
        #   BTN_VALUE    (3) : Text (editable)
        #   BTN_LOGO     (4) : img
        #   BTN_DROPDOWN (5) : Drop down

        # Base display
        min_x = self.res_x_16
        if item[1] > 8:
            min_y = 2 * self.res_y_16
        else:
            min_y = 3 * self.res_y_16

        if tabs:
            min_y += self.res_y_16

        max_x = 14 * self.res_x_16

        if exit:
            max_y = self.res_y - 4 * self.res_y_16 - min_y  # 3 / 16 reserved for title and 3 / 16 for other buttons
        else:
            max_y = self.res_y - 3 * self.res_y_16 - min_y  #Only 3 / 16 reserved for title

        if align == 'Full' and item[1] >= 15:
            collapsed = True
        elif align == 'Full':
            vertical_margin = int(max_y / 72)
        elif item[1] >= 10:                   # No blank between items if > 9 items
            collapsed = True
        else:
            vertical_margin = int(max_y / 72)

        height = min(self.res_y_15, int(max_y / item[1]))

        if column is not None:
            # Two columns side by side, from 1/16 to 15/16 of the screen
            gap = int(self.res_x_16 / 2)
            width = int((14 * self.res_x_16 - gap) / 2)
            pos_x = int(self.res_x_16 + column_index * (width + gap))
        elif align in ('Full', 'Values'):
            pos_x = int(3 * self.res_x_16)
            width = int(self.res['x'] - pos_x - height - pos_x)
        elif align == 'Left':
            pos_x = int(self.res['x'] * 1 / 16)
            width = int(self.res['x'] * 7 / 16 - min_x - height)
        elif align == 'Half':
            pos_x = int(self.res['x'] * 6 / 16)
            width = int(self.res['x'] * 4 / 16 - height)
        elif align == 'Right':
            pos_x = int(self.res['x'] * 9 / 16)
            width = int(self.res['x'] * 8 / 16 - min_x - height)
        else:
            pos_x = int(self.res['x'] * 5 / 16)
            width = int(self.res['x'] / 2 - min_x - height)

        pos_y = min_y + (vertical_margin + height) * (item[0] + space - 1)

        if is_selected:
            shortcut_bg_color = self.colorset['menu-selected']
            shortcut_text_color = self.colorset['menu-text-black']
            value_bg_color = self.colorset['menu-selected']
            value_text_color = self.colorset['menu-text-white']
            text_bg_color = self.colorset['menu-selected']
            text_text_color = self.colorset['menu-text-black']
            border_color = self.colorset['menu-border']
            border_size = int(self.colorset['border-size'])
            padding = int(self.colorset['padding'])
            corners = 'All'
        else:
            shortcut_bg_color = self.colorset['menu-shortcut']
            shortcut_text_color = self.colorset['menu-text-black']
            text_bg_color = self.menu_color(self.colorset['menu-buttons'])
            text_text_color = self.colorset['menu-text-black']
            if collapsed:
                text_bg_color = self.menu_color(self.colorset['menu-buttons'], index=item[0] + 1, div=0.5)
                value_bg_color = self.menu_color(self.colorset['menu-shortcut'], index=item[0] + 1)
                value_text_color = self.menu_color(self.colorset['menu-text-black'], index=item[0] + 1)
            else:
                value_bg_color = self.colorset['menu-shortcut']
                value_text_color = self.colorset['menu-text-black']

            border_color = None
            border_size = 0
            padding = 0
            corners = self.compute_corners(item[0], item[1], item[2], collapsed)

        if valid is False and not is_selected:
            # Button which does nothing (empty favorite) : greyed
            text_bg_color = self.colorset['menu-inactive']
            text_text_color = value_text_color = (150, 150, 150)

        if value[2] == BTN_CHECK and value[3]:
            shortcut_bg_color = self.colorset['menu-ok']
        elif value[2] == BTN_CHECK:
            shortcut_bg_color = self.colorset['menu-ko']
        elif value[2] in (BTN_VALUE, BTN_DROPDOWN):
            shortcut_bg_color = self.colorset['menu-alternate']

        shortcut = (shortcut_bg_color, value[0], shortcut_text_color)
        text = (text_bg_color, value[1], value_text_color)
        rect = pygame.Rect(pos_x, pos_y, width, height)
        if value[2] == BTN_CHOICE:
            # Background_value, text_value, text_color
            self.st_item(shortcut, text, rect, padding, border_size, border_color, divider=divider, corners=corners)
        else:
            text = (text_bg_color, value[1], text_text_color)
            value = (value_bg_color, value[3], value_text_color)
            # In a column : a wider place for the value (half the width of a line)
            self.svt_item(shortcut, value, text, rect, padding, border_size, border_color, ratio=0.3 if column is not None else 0.2)

        return (pos_x, pos_y, width, height)

    def favorites_servers_menu(self, favorites):
        '''
        Favorites servers
        '''
        selected = 1
        servers = []
        self.dmd.send_text(self.lang.translate('dmd-server-favorites'), tempo = 1)

        for f in favorites.split(', '):
            servers.append(f)

        while True:
            nb_elements = len(servers)
            index = 0

            shortcuts = []
            click_zones = {}

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('favorites-servers', 'enter-valid-url')

            for server in servers:
                index += 1
                click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), ('', f"Serveur {index}", BTN_VALUE, server), align='Values')
                shortcuts.append(f'F{index}')

            # go back and next
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')
            click_zones['add'] = self.display_button(nb_elements + 2 == selected, 'add', special='refresh')
            click_zones['save'] = self.display_button(nb_elements + 3 == selected, 'save', special='return')

            self.update_screen()

            # Read input
            key_pressed = self.rpi.listen_inputs(
                    ['alpha', 'num', 'fx', 'math', 'arrows'],
                    ['PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON', 'EXTRABUTTON',
                    'escape', 'enter', 'backspace', 'tab', 'TOGGLEFULLSCREEN',
                    'space', 'single-click'],
                    events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Click cases
            clicked = self.is_clicked(click_zones, key_pressed)
            if clicked:
                key_pressed = clicked

            # Navigation
            selected = self.navigate(selected, key_pressed, nb_elements, 3, 3, left_right=True)

            #Shortcuts
            if key_pressed in shortcuts:
                selected = int(key_pressed.replace('F', ''))
                key_pressed = 'enter'

            if key_pressed in ESCAPE_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            if key_pressed in SAVE_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 3):
                return ', '.join(servers)

            if key_pressed in PLUS_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 2):
                if len(servers) < 8:
                    servers.append('')
                    selected = len(servers)

            elif key_pressed in MINUS_KEYS:
                if len(servers) > 0:
                    servers.pop(selected - 1)

            elif key_pressed in ENTER_KEYS:    # Edition mode
                tmp = self.input_value_item('string', '', 1, 64)
                if tmp != 'escape':
                    servers[selected - 1] = tmp

    def favorites_games_menu(self, favorites):
        '''
        Favorite games : the favorites of each game (its options, or without options : chosen
        at its launch ; a number if wanted : a button of the main menu too), saved at once.
        favorites : the favorite games of raspydarts.cfg (before the favorites without number).
        Returns the games which have a favorite without number (raspydarts.cfg)
        '''
        selected = 1

        self.dmd.send_text(self.lang.translate('dmd-game-favorites'), tempo = 1)

        unnumbered = self.favorites().unnumbered(favorites)
        having = self.games_with_favorites(unnumbered)
        game_list = self.get_games_list()
        nb_elements = len(game_list)

        game_list.sort()
        tab = -2

        old_selection = None
        refresh = True
        while True:
            index = 0

            shortcuts = []
            games = []
            click_zones = {}

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('favorites-games')

            #Tabs
            click_zones['F-2'] = self.display_button(-2 == selected, 'category-classic', special='tab1')
            shortcuts.append(f'F-2')
            click_zones['F-1'] = self.display_button(-1 == selected, 'category-fun', special='tab2')
            shortcuts.append(f'F-1')
            click_zones['F0'] = self.display_button(0 == selected, 'category-sport', special='tab3')
            shortcuts.append(f'F0')

            for game in game_list:
                index += 1
                games.append(game)
                # Green : the game has favorites
                click_zones[f'F{index}'] = self.game_item((index, nb_elements, selected) \
                        , (f'F{index}', game, game.replace(' ', '_') in having))
                shortcuts.append(f'F{index}')

            # go back (the favorites are saved at once)
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')

            if selected <= nb_elements:
                selection = [click_zones[f'F{selected}']]
                if selected > 1:
                    selection.append(click_zones[f'F{selected - 1}'])
                if selected > 2:
                    selection.append(click_zones[f'F{selected - 2}'])
                if selected < nb_elements:
                    selection.append(click_zones[f'F{selected + 1}'])
                if selected < nb_elements - 1:
                    selection.append(click_zones[f'F{selected + 2}'])
            elif nb_elements + 1 == selected:
                selection = [click_zones['escape']]
            else:
                selection = None

            if refresh:
                self.update_screen()
                refresh = False
            elif old_selection is None or selection is None:
                self.update_screen(rect_array=[click_zones[cz] for cz in click_zones])
            else:
                self.update_screen(rect_array=old_selection)
                self.update_screen(rect_array=selection)

            key_pressed = self.rpi.listen_inputs(['arrows', 'fx'],
                                                 ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'],
                                                 events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Click cases
            clicked = self.is_clicked(click_zones, key_pressed)
            if clicked:
                key_pressed = clicked

            # Navigation
            selected = self.navigate(selected, key_pressed, nb_elements, 1, 1, item_per_line=2 , left_right=True, zero=-2, tab=tab)

            if key_pressed in shortcuts:
                selected = int(key_pressed.replace('F', ''))
                key_pressed = 'enter'

            if key_pressed in ESCAPE_KEYS + SAVE_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 1):
                return ', '.join(sorted({entry['game'].replace('_', ' ') for entry in unnumbered}))

            if selected < 1:
                if selected == - 2:
                    game_list = self.get_games_list()
                if selected == - 1:
                    game_list = self.get_games_list(category='fun')
                if selected == 0:
                    game_list = self.get_games_list(category='sport')

                nb_elements = len(game_list)

                game_list.sort()
                refresh = True
                tab = selected

            # Keyboard cases : the favorites of the game chosen
            if key_pressed in ENTER_KEYS and selected <= nb_elements and selected > 0:
                unnumbered = self.favorite_game_menu(games[selected - 1], unnumbered)
                having = self.games_with_favorites(unnumbered)
                refresh = True

            old_selection = selection

    def games_with_favorites(self, unnumbered):
        '''
        The games (Ho_One...) which have favorites, numbered or not
        '''
        having = {entry['game'] for entry in unnumbered}
        try:
            having.update(favorite['game'] for _, favorite in self.favorites().numbered())
        except Exception as error:    # pylint: disable=broad-except
            self.logs.error(f"Favorites : numbered favorites not read ({error})")
        return having

    def favorite_text(self, number, options):
        '''
        Name of a favorite in the screens of the favorites : Favori [1] avec options / sans options
        '''
        kind = self.lang.translate('favorite-with-options' if options else 'favorite-without-options')
        return f"{self.lang.translate('favorite')}{f' {number}' if number else ''} {kind}"

    def favorite_game_menu(self, game, unnumbered):
        '''
        Screen Jeux favoris, a game chosen : a favorite of it added (with its options, or
        without options : chosen at its launch ; on a button of the main menu if wanted), or one
        of its favorites changed or removed (the others are kept). Returns the favorites without
        number
        '''
        name = game.replace(' ', '_')
        back = {'id': 'back', 'action': 'back', 'text': 'back', 'footer': 'left', 'shortcut': 'escape'}
        while True:
            # Its favorites : without number, then numbered (their options under the list when
            # selected)
            numbered = dict((slot, favorite) for slot, favorite in self.favorites().numbered() if favorite['game'] == name)
            favorites = [(f'list{position}', None, entry['options']) for position, entry in enumerate(unnumbered) if entry['game'] == name]
            favorites += [(slot, slot[3:], favorite['options']) for slot, favorite in numbered.items()]
            items = [{'id': 'new', 'action': 'new', 'text': 'favorite-add-options'}]
            # Without options : one for a game (they would be the same)
            if all(options for _, _, options in favorites):
                items.append({'id': 'plain', 'action': 'plain', 'text': 'favorite-add-plain'})
            for ident, number, options in favorites:
                # A numbered favorite : its players first
                players = [self.favorite_players_text(numbered[ident])] if number else []
                items.append({'id': ident, 'action': 'favorite', 'text': self.favorite_text(number, options),
                              'details': players + self.favorite_options_lines(game, options)})
            for number, item in enumerate(items, 1):
                item['shortcut'] = f'F{number}'
            choice = self.run_menu('favorite_game', items + [back], items + [back], title=game).get('id')
            if choice == 'back':
                return unnumbered
            if choice in ('new', 'plain'):
                options = {}
                if choice == 'new':
                    options = self.favorite_options_screen(game, None)
                    if options is None:
                        continue
                # On a button of the main menu too ? Back : nothing saved
                button = self.ask_yes_no(self.lang.translate('favorite-place-button'),
                                         self.lang.translate('favorite-numbered-sub'), cancel=True)
                if button is None:
                    continue
                if button and self.new_numbered_favorite(game, options):
                    continue
                unnumbered = self.save_unnumbered(unnumbered + [{'game': name, 'options': options}])
            elif choice.startswith('list'):
                unnumbered = self.unnumbered_favorite_menu(game, int(choice[4:]), unnumbered)
            elif choice in numbered:
                self.numbered_favorite_menu(choice, numbered[choice])

    def save_unnumbered(self, unnumbered):
        '''
        The favorites without number saved : those saved (the previous ones if they cannot be)
        '''
        try:
            self.favorites().set_unnumbered(unnumbered)
            return unnumbered
        except Exception as error:    # pylint: disable=broad-except
            self.logs.error(f"Favorites : not saved ({error})")
            self.message([self.lang.translate('favorite-not-saved')], 2500, 'menu-ko', 'middle', 'big')
            return self.favorites().unnumbered()

    def unnumbered_favorite_menu(self, game, position, unnumbered):
        '''
        Screen Jeux favoris : a favorite without number, its options changed, placed on a button
        of the main menu or removed. Returns the favorites without number
        '''
        entry = unnumbered[position]
        edit = {'id': 'edit', 'action': 'edit', 'text': 'favorite-edit-options', 'shortcut': 'F1'}
        button = {'id': 'button', 'action': 'button', 'text': 'favorite-to-button', 'shortcut': 'F2'}
        remove = {'id': 'remove', 'action': 'remove', 'text': 'favorite-numbered-remove', 'shortcut': 'F3'}
        back = {'id': 'back', 'action': 'back', 'text': 'back', 'footer': 'left', 'shortcut': 'escape'}
        others = unnumbered[:position] + unnumbered[position + 1:]
        while True:
            choice = self.run_menu('favorite_game', [edit, button, remove, back], [edit, button, remove, back],
                                   title=f"{game} · {self.favorite_text(None, entry['options'])}").get('id')
            if choice == 'back':
                return unnumbered
            if choice == 'remove':
                return self.save_unnumbered(others)
            if choice == 'button':
                # Numbered : no more in the favorites without number
                if self.new_numbered_favorite(game, entry['options']):
                    return self.save_unnumbered(others)
                continue
            options = self.favorite_options_screen(game, entry['options'] or None)
            if options is not None:
                changed = dict(entry, options=options)
                return self.save_unnumbered(unnumbered[:position] + [changed] + unnumbered[position + 1:])

    def numbered_favorite_menu(self, slot, favorite):
        '''
        Screen Jeux favoris : a numbered favorite of the game chosen, its options or its players
        changed, or removed (the others are kept)
        '''
        game = favorite['game'].replace('_', ' ')
        edit = {'id': 'edit', 'action': 'edit', 'text': 'favorite-edit-options', 'shortcut': 'F1'}
        players = {'id': 'players', 'action': 'players', 'text': 'favorite-edit-players', 'shortcut': 'F2',
                   'details': [self.favorite_players_text(favorite)]}
        remove = {'id': 'remove', 'action': 'remove', 'text': 'favorite-numbered-remove', 'shortcut': 'F3'}
        back = {'id': 'back', 'action': 'back', 'text': 'back', 'footer': 'left', 'shortcut': 'escape'}
        buttons = [edit, players, remove, back]
        title = f"{game} · {self.favorite_text(slot[3:], favorite['options'])}"
        while True:
            choice = self.run_menu('favorite_game', buttons, buttons, title=title).get('id')
            if choice == 'back':
                return
            try:
                if choice == 'remove':
                    self.favorites().remove(slot)
                    self.message([self.lang.translate('favorite-removed').replace('{number}', slot[3:])], 1500, None, 'middle', 'big')
                    return
                if choice == 'players':
                    chosen = self.favorite_players_choice(game, favorite)
                    if chosen is None:
                        continue
                    mode, count, names = chosen
                    self.favorites().save(slot, game, favorite['options'], count, mode, names)
                    self.message([self.lang.translate('favorite-saved').replace('{number}', slot[3:])], 1500, None, 'middle', 'big')
                    return
                options = self.favorite_options_screen(game, favorite['options'] or None)
                if options is None:
                    continue
                self.favorites().save(slot, game, options, favorite['players'], favorite['mode'], favorite['names'])
                self.message([self.lang.translate('favorite-saved').replace('{number}', slot[3:])], 1500, None, 'middle', 'big')
            except Exception as error:    # pylint: disable=broad-except
                self.logs.error(f"Favorites : {slot} not changed ({error})")
                self.message([self.lang.translate('favorite-not-saved')], 2500, 'menu-ko', 'middle', 'big')
            return

    def favorite_options_screen(self, game, preset):
        '''
        The screen of the options of a favorite : its options, None if given up or not shown
        '''
        try:
            return self.favorite_game_options(game, preset)
        except Exception as error:    # pylint: disable=broad-except
            self.logs.error(f"Favorites : options of {game} not shown ({error})")
            return None

    def new_numbered_favorite(self, game, options):
        '''
        A numbered favorite of a game saved (options {} : chosen at its launch). False : not
        saved
        '''
        return self.favorite_save(game, options)

    def favorite_players_text(self, favorite):
        '''
        The players of a numbered favorite, as the screens of the favorites write them
        '''
        if favorite['mode'] == 'choose' and favorite['names']:
            players = ', '.join(favorite['names'])
        elif favorite['mode'] == 'generic':
            players = self.generic_players_text(favorite['players'])
        elif favorite['mode'] == 'last':
            players = f"{self.lang.translate('favorite-last')} ({favorite['players']})"
        else:
            players = self.lang.translate('favorite-ask')
        return f"{self.lang.translate('favorite-players')} : {players}"

    def generic_players_text(self, count):
        '''
        Joueur 1, Joueur 2... (Joueur 1 ... Joueur 5 beyond 4)
        '''
        player = self.lang.translate('favorite-player')
        names = [f"{player} {index}" for index in range(1, count + 1)]
        return ', '.join(names) if count <= 4 else f"{names[0]} … {names[-1]}"

    def known_players(self):
        '''
        The players the borne knows : the favorite players, then those of the bank of
        firstnames (Divers > Banque de prénoms)
        '''
        bank = self.config.get_value('SectionAdvanced', 'localplayers', False, None, split=',') or []
        names = []
        # The same name once (Rémi, rémi, ' Rémi')
        for name in [str(name).strip() for name in list(self.favorite_players()) + list(bank)]:
            if name and name.casefold() not in [known.casefold() for known in names]:
                names.append(name)
        return names

    def pick_favorite_players(self, names, current=None):
        '''
        The players of a favorite chosen among those the borne knows (taken at first : those
        of the favorite changed, else the favorite players) : green taken, pink left, as the
        favorite games. None : back
        '''
        taken = current if current else self.favorite_players()
        chosen = [name for name in names if name in taken]
        nb_elements = len(names)
        selected = 1
        old_selection = None
        refresh = True
        while True:
            click_zones = {}
            shortcuts = []
            self.display_background()
            self.menu_header('favorite-players', 'favorite-pick-sub')
            for index, name in enumerate(names, 1):
                click_zones[f'F{index}'] = self.game_item((index, nb_elements, selected), (f'F{index}', name, name in chosen))
                shortcuts.append(f'F{index}')
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')
            # Validate : at least one player
            click_zones['save'] = self.display_button(nb_elements + 2 == selected, 'validate', special='return')

            if 1 <= selected <= nb_elements:
                selection = [click_zones[f'F{index}'] for index in range(max(1, selected - 2), min(nb_elements, selected + 2) + 1)]
            elif selected == nb_elements + 1:
                selection = [click_zones['escape']]
            elif selected == nb_elements + 2:
                selection = [click_zones['save']]
            else:
                selection = None
            if refresh:
                self.update_screen()
                refresh = False
            elif old_selection is None or selection is None:
                self.update_screen(rect_array=[click_zones[zone] for zone in click_zones])
            else:
                self.update_screen(rect_array=old_selection)
                self.update_screen(rect_array=selection)

            key_pressed = self.rpi.listen_inputs(['arrows', 'fx'],
                                                 ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'],
                                                 events=[(self.wait_event_time, 'EVENT', 'wait')])
            clicked = self.is_clicked(click_zones, key_pressed)
            if clicked:
                key_pressed = clicked
            selected = self.navigate(selected, key_pressed, nb_elements, 2, 2, item_per_line=2, left_right=True)
            if key_pressed in shortcuts:
                selected = int(key_pressed.replace('F', ''))
                key_pressed = 'enter'

            if key_pressed in ESCAPE_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 1):
                return None
            if (key_pressed in SAVE_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 2)) and chosen:
                # In the order of the list
                return [name for name in names if name in chosen]
            if key_pressed in ENTER_KEYS and 1 <= selected <= nb_elements:
                name = names[selected - 1]
                if name in chosen:
                    chosen.remove(name)
                else:
                    chosen.append(name)
                refresh = True
            old_selection = selection

    def favorite_count(self, game, generic=False):
        '''
        Number of players of a favorite (generic : Joueur 1, Joueur 2... written on its
        buttons, else the last players), among those its game allows. None : back
        '''
        try:
            limits = self.config.get_value('NbOfPlayersPerGame', game.replace(' ', '_'))
            low, high = max(1, int(limits[0])), max(1, int(limits[1]))
        except Exception:    # pylint: disable=broad-except
            low, high = 1, 8
        if low == high:
            return low
        back = {'id': 'back', 'action': 'back', 'text': 'back', 'footer': 'left', 'shortcut': 'escape'}
        items = []
        for count in range(low, min(high, 12) + 1):
            text = str(count)
            if generic:
                text = self.generic_players_text(count)
            item = {'id': f'count{count}', 'action': 'count', 'text': text}
            if count <= 9:
                item['shortcut'] = f'F{count}'
            items.append(item)
        choice = self.run_menu('favorite_players', items + [back], items + [back],
                               title=self.lang.translate('favorite-count')).get('id')
        return None if choice == 'back' else int(choice[5:])

    def display_changelog(self, version):
        '''
        Display Changelog
        '''
        if os.path.isfile(f'{self.config.changelogFile}.{version}') or os.path.isfile(f'{self.config.changelogFile}.{version}.1'):
            self.show()

        try:
            with open(f'{self.config.changelogFile}.{version}', 'r') as changelog:
                text = changelog.readlines()
            action = "move"
            changelog.close()

        except:
            try:
                with open(f'{self.config.changelogFile}.{version}.1', 'r') as changelog:
                    text = changelog.readlines()
                action = "delete"
                changelog.close()

            except:
                return

        self.dmd.send_text(self.lang.translate('news'))

        # Draw bg
        self.display_background()

        # Titles
        self.menu_header('news')
        self.update_screen()

        width = 14 * self.res_x_16
        height = 12 * self.res_y_16
        pos_x = self.res_x_16
        pos_y = 2 * self.res_y_16
        marge_x = int(self.res['x'] / 64)
        marge_y = int(self.res['y'] / 64)

        # New surface
        Surface = pygame.Surface((width, height))
        Surface.set_alpha(192)
        Surface.fill(self.colorset['menu-item-black'])
        self.new_blit_rect(pos_x, pos_y, width, height, self.colorset['menu-buttons'], corners='All', border_radius=50, Alpha=228)

        font_file = self.defaultfontpath
        # Add description
        nb_lines = len(text)
        font = self.font(font_file, 50)

        index = 0
        maxsize = 0
        # Find correct font size
        for line in text:
            font_size = font.size(line)
            if font_size[0] > maxsize:
                maxsize = font_size[0]
                longest = index
            index += 1

        scaled_text = self.scale_text(text[longest], width - 2 * marge_x, (height - 2 * marge_y) / nb_lines, divider=1.5, step=0.05, dafont=font_file )
        font_size = scaled_text[0]
        font = self.font(font_file, font_size + self.margin)

        if nb_lines > 1:
            interline = (height - nb_lines * font_size - 2 * marge_y) / (nb_lines - 1)
        else:
            interline = 0

        index = 0
        for line in text:
            text = font.render(line.replace('\n', ''), True, self.colorset['menu-text-black'])
            #self.blit(text, [pos_x + marge_x, pos_y + I * (i-1) + marge_y])
            self.blit(text, [pos_x + marge_x, pos_y + marge_y])
            index += 1
            pos_y += font_size + interline

        ################
        # Update screen
        self.update_screen()
        self.wait_touch()

        if action == 'move':
            os.system(f"mv {self.config.changelogFile}.{version} {self.config.changelogFile}.{version}.1")
        elif action == 'delete':
            os.system(f"mv {self.config.changelogFile}.{version}.1 {self.config.changelogFile}.{version}.read")

    def backup_menu(self):
        '''
        Backups menu
        '''
        selected = 1
        self.dmd.send_text(self.lang.translate('dmd-backup-menu'), tempo = 1)

        while True:
            files_list = self.get_backups_list()
            if files_list is None:
                files_list = []

            nb_elements = len(files_list)

            index = 0

            click_zones = {}
            shortcuts = []
            backups = []

            if nb_elements > 3:
                addClean = True
                add = 3
            else:
                addClean = False
                add = 2

            click_zones = {}

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('backups')

            for backup in files_list:
                index += 1
                if index <= 12:
                    if backup[0].startswith('backup/raspydarts'):
                        file_type = 'Full'
                    elif backup[0].startswith('backup/update'):
                        file_type = 'Update'
                    else:
                        index -= 1
                        continue

                    backup_text = f"Version {backup[1]} du {backup[2][6::]}/{backup[2][4:6]}/{backup[2][0:4]} ({backup[3][0:2]}h{backup[3][2::].split('.')[0]} - {file_type})"
                    backups.append((backup[0], backup_text))
                    click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), (f'F{index}', backup_text, BTN_CHOICE, None))
                    shortcuts.append(f'F{index}')

            # go back and next
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')
            if addClean:
                click_zones['clean'] = self.display_button(nb_elements + 2 == selected, 'clean', special='refresh')
            click_zones['backup'] = self.display_button(nb_elements + add == selected, 'backup', special='return')

            ################
            # Update screen
            self.update_screen()

            key_pressed = self.rpi.listen_inputs(['arrows', 'fx'], 
                                                 ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'], 
                                                 events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Click cases
            clicked = self.is_clicked(click_zones, key_pressed)
            if clicked:
                key_pressed = clicked

            # Navigation
            selected = self.navigate(selected, key_pressed, nb_elements, add, add, left_right=True)

            # Shotcuts
            if key_pressed in shortcuts:
                selected = int(key_pressed[1::])
                key_pressed = 'enter'

            # Key analysis
            if key_pressed in ESCAPE_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 1) :    # Previous menu
                return 'escape'

            if key_pressed in BACKUP_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + add) : # Make a backup
                self.message(['backing-up'], wait = 100)
                os.system(f"{self.backupscript} b")
                self.message(['backup-done'], wait = 2000)

            elif nb_elements > 3 and (key_pressed in CLEAN_KEYS or (key_pressed in ENTER_KEYS and selected == nb_elements + 2)): # Clean backups
                response = self.wait_validation('backup-clean')
                if response:
                    self.message(['cleaning'])
                    pygame.time.wait(1000)
                    os.system(f"{self.backupscript} c")
                    self.message(['clean-done'], wait = 2000)

            elif key_pressed in ENTER_KEYS and 0 < selected <= nb_elements:
                restore = backups[selected - 1][0]
                msg= f"{self.lang.translate('backup-choice')} {backups[selected - 1][1]}"
                response = self.wait_validation(msg)
                if response:
                    response = self.wait_validation("are-you-sure")
                    if response:
                        # Ici
                        self.message(['restoring'])
                        os.system(f"{self.backupscript} r {restore}")
                        self.message(['restore-done'], wait = 2000)
                        response = self.wait_validation(self.lang.translate('need-restart'))
                        if response:
                            return 'restart'

    # Keyboards on the screen : rows of keys. Special keys : (name, width in keys)
    KEYPAD_NUMBERS = [['1', '2', '3', ('backspace', 1.5)], ['4', '5', '6', ','], ['7', '8', '9', '.'],
                      [('escape', 1.5), '0', ('enter', 1.5)]]
    KEYBOARDS = {
        'azerty': [list('1234567890'), list('azertyuiop'), list('qsdfghjklm'),
                   [('shift', 1.5)] + list('wxcvbn') + ['.', '-', ('backspace', 1.5)],
                   [('escape', 2)] + ['_', ':', '@', ('space', 4), ('enter', 2)]],
        'qwerty': [list('1234567890'), list('qwertyuiop'), list('asdfghjkl') + ['-'],
                   [('shift', 1.5)] + list('zxcvbnm') + ['.', ('backspace', 1.5)],
                   [('escape', 2)] + ['_', ':', '@', ('space', 4), ('enter', 2)]],
    }
    KEY_TEXTS = {'backspace': 'vk-delete', 'enter': 'vk-ok', 'escape': 'vk-cancel', 'shift': 'vk-shift', 'space': 'vk-space'}

    def keyboard_wanted(self):
        '''
        Keyboard on the screen for a field : virtual_keyboard.mode of the files of menus.
        touch (default) : the field was reached by a finger ; always ; never
        '''
        mode = str((self.menus().data.get('virtual_keyboard') or {}).get('mode') or 'touch')
        if mode == 'always':
            return True
        if mode == 'never':
            return False
        return bool(getattr(self.rpi, 'last_input_touch', False))

    def draw_keyboard(self, v_type, shift):
        '''
        Keyboard on the screen, under the field : returns {rect: key}. Numbers : a keypad
        (with , and . for the leds) ; text : letters of the language of the game
        '''
        if v_type == 'string':
            language = str(self.config.get_value('SectionGlobals', 'locale', False) or 'en')[:2]
            rows = self.KEYBOARDS['azerty' if language == 'fr' else 'qwerty']
            width = int(self.res_x_16 * 14)
        else:
            rows = [[key for key in row if v_type == 'leds' or key not in (',', '.')] for row in self.KEYPAD_NUMBERS]
            width = int(self.res_x_16 * 6)
        top = int(self.res_y_16 * 10.25)
        height = int(self.res_y_16 * 5.5)
        panel = pygame.Rect(int((self.res['x'] - width) / 2), top, width, height)
        self.new_blit_rect2(panel, self.colorset['menu-header'], corners='All', border_radius=int(self.res_y_16 / 3), alpha=255)
        margin = max(2, int(self.res_y_16 / 12))
        row_height = (height - margin) / len(rows)
        keys = {}
        for index, row in enumerate(rows):
            units = sum(key[1] if isinstance(key, tuple) else 1 for key in row)
            unit = (width - margin) / units
            pos_x = panel.x + margin
            for key in row:
                name, size = key if isinstance(key, tuple) else (key, 1)
                rect = pygame.Rect(int(pos_x), int(top + margin + index * row_height), int(unit * size) - margin, int(row_height) - margin)
                pos_x += unit * size
                color = self.colorset['menu-selected'] if name in ('enter', 'shift') and (name != 'shift' or shift) \
                    else self.colorset['menu-buttons']
                self.new_blit_rect2(rect, color, corners='All', border_radius=int(rect.h / 4), alpha=255)
                if name in self.KEY_TEXTS:
                    label = self.lang.translate(self.KEY_TEXTS[name])
                else:
                    label = name.upper() if shift else name
                self.blit_text2(label, rect, self.colorset['menu-text-black'])
                keys[(rect.x, rect.y, rect.w, rect.h)] = name
        return panel, keys

    # Choices of the wheel of characters of a knob, besides the characters : delete the last one,
    # end the typing
    KNOB_DELETE = '<'
    KNOB_OK = 'OK'

    def input_value_item(self, *args, **kwargs):
        '''
        Input value item (see typed_value) : a knob of a USB pad changes the value while it is
        typed (a number : its value, faster when turned fast ; a text : a wheel of characters),
        its press validates (a text : keeps the character), held : validates
        '''
        pads = getattr(self.rpi, 'usb_pads', None)
        if pads is not None:
            pads.set_value_input(True)
        try:
            return self.typed_value(*args, **kwargs)
        finally:
            if pads is not None:
                pads.set_value_input(False)

    def knob_wheel(self, v_type):
        '''
        Characters of the wheel of a knob for a text (the order of up and down), then delete
        and end
        '''
        first = '0' if v_type == 'leds' else 'a'
        wheel = [first]
        while len(wheel) < 200:
            character = self.next_key(wheel[-1], context=v_type)
            if character in wheel:
                break
            wheel.append(character)
        return wheel + [self.KNOB_DELETE, self.KNOB_OK]

    def typed_value(self, v_type, value, v_min, v_max, character=None, align='Center', text=None, zero=False, knob_start=None, hidden=False):
        '''
        Input value item
        hidden : a password, shown as stars
        knob_start : a number typed from nothing (a new value by the keyboard) : the knob
        starts from it (the value of the option)

        v_type : string, number , numeric(=number + . + , )
        v_min : Min length or min value
        v_max : Maw length or max value
        special : Authorized keys (if string)
        '''
        authorized = ['alpha', 'num', 'arrows']
        limited = None

        if v_type == 'number':
            authorized = ['num', 'arrows', 'math']
            limited = None
        elif v_type == 'pins':
            authorized = ['num', 'arrows']
            limited = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'backspace', 'enter', 'escape']
        elif v_type == 'leds':
            authorized = ['num', 'alpha', 'math', 'arrows']
            limited = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ',', '.', 'backspace', 'enter', 'escape']
        elif v_type == 'string':
            authorized = ['num', 'alpha', 'fx', 'math', 'arrows']
            limited = None
        else:
            self.logs.error(f"Line 2786 : Unauthorized type: {v_type}")
            return False

        self.save_background()

        value = str(value)
        if character is None:
            if value == '':
                character = ''
            else:
                character = value[-1]

        border_size = 5 * self.colorset['border-size']
        minus = self.colorset['padding'] + border_size
        minus = border_size

        if text is not None:
            rect = pygame.Rect(self.res_x_16 * 6, self.res_y_16 * 6, self.res_x_16 * 4, self.res_y_16 * 4)
            t_rect = pygame.Rect(rect.x + minus, rect.y + minus, rect.w - 2 * minus, self.res_y_16 * 2 - minus)
            v_rect = pygame.Rect(rect.x + minus, t_rect.bottom, rect.w - 2 * minus, self.res_y_16 * 2 - minus)
        else:
            rect = pygame.Rect(self.res_x_16 * 6, self.res_y_16 * 6.5, self.res_x_16 * 4, self.res_y_16 * 3)
            v_rect = pygame.Rect(rect.x + minus, rect.y + minus, rect.w - 2 * minus, self.res_y_16 * 3 - 2 * minus)


        if self.colorset['border-radius'] == 'max':
            border_radius = int(v_rect.h / 2)
        else:
            border_radius = int(self.colorset['border-radius'])

        key = ''
        # Keyboard on the screen (field reached by a finger) : drawn under the field
        keyboard = self.keyboard_wanted()
        shift = False
        panel = None
        keyboard_keys = {}
        # Wheel of characters of a knob (a text) : its choices, the one shown (None : not turned)
        wheel = self.knob_wheel(v_type) if v_type in ('string', 'leds') else []
        wheel_at = None
        while True:
            if keyboard:
                panel, keyboard_keys = self.draw_keyboard(v_type, shift)
            self.blit_border(rect, self.colorset['menu-border'], border_size, corners='All', border_radius=border_radius, alpha=255)
            inside_border_radius = border_radius - border_size
            if text is not None:
                self.new_blit_rect2(t_rect, self.colorset['menu-buttons'], corners='Top', border_radius=inside_border_radius, alpha=255)
                self.blit_text2(self.lang.translate(text), t_rect, self.colorset['menu-text-black'])
                self.new_blit_rect2(v_rect, self.colorset['menu-selected'], corners='Bottom', border_radius=inside_border_radius, alpha=255)
            else:
                self.new_blit_rect2(v_rect, self.colorset['menu-selected'], corners='All', border_radius=inside_border_radius, alpha=255)

            # The choice of the wheel after the text, between brackets : not written yet
            shown = '*' * len(value) if hidden else value
            shown = shown if wheel_at is None else f"{shown}[{wheel[wheel_at]}]"
            self.blit_text2(shown, v_rect, self.colorset['menu-text-black'], align=align)

            self.update_screen(rect_array=[rect] + ([panel] if keyboard else []))

            # Read input
            key = self.rpi.listen_inputs(authorized,
                    ['PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON', 'EXTRABUTTON',
                    'escape', 'enter', 'backspace', 'tab', 'TOGGLEFULLSCREEN',
                    'space', 'single-click'], wait_for=limited, context='editing')

            if isinstance(key, tuple):
                # A touch : a key of the keyboard on the screen, or the field (opens it)
                pressed = next((name for zone, name in keyboard_keys.items() if pygame.Rect(zone).collidepoint(key)), None)
                if pressed is None and not keyboard and rect.collidepoint(key):
                    keyboard = True
                    continue
                if pressed == 'shift':
                    shift = not shift
                    continue
                if pressed is None:
                    continue
                key = pressed.upper() if shift and len(pressed) == 1 else pressed
            elif keyboard and key not in (None, False) and not getattr(self.rpi, 'last_input_touch', False):
                # A real keyboard is used : the one on the screen goes away
                keyboard = False
                if panel is not None and self.game_background is not None:
                    self.screen.blit(self.game_background, panel, panel)
                    self.update_screen(panel)

            if isinstance(key, str) and key.startswith('KNOB_'):
                # Knob of a USB pad (include/cusbpads.py) : turned (KNOB_RIGHT:step), pressed,
                # held (KNOB_LONG : validates)
                turned = key.startswith(('KNOB_RIGHT', 'KNOB_LEFT'))
                if turned and wheel:
                    # A text : the next choice of the wheel
                    move = 1 if key.startswith('KNOB_RIGHT') else -1
                    wheel_at = 0 if wheel_at is None else (wheel_at + move) % len(wheel)
                    continue
                if turned:
                    # A number : its value, between its limits
                    step = int(key.split(':')[1]) * (1 if key.startswith('KNOB_RIGHT') else -1)
                    if not value.isdigit() and str(knob_start).isdigit():
                        value = str(knob_start)
                    if value.isdigit():
                        value = str(min(max(int(value) + step, v_min), v_max))
                    else:
                        value = str(v_min if step > 0 else v_max)
                    character = value[-1]
                    continue
                if key == 'KNOB_PRESS' and wheel_at is not None:
                    choice = wheel[wheel_at]
                    if choice == self.KNOB_DELETE:
                        value = value[:-1]
                    elif choice != self.KNOB_OK:
                        if len(value) < v_max:
                            value = f"{value}{choice}"
                        continue
                    if choice != self.KNOB_OK:
                        continue
                # Press of a number, OK of the wheel, held : validated
                key = 'enter'

            if key in ENTER_KEYS :    # Valid and quit
                if v_type == 'leds' and len(value) > 0:
                    self.restore_background()
                    self.reset_background()
                    return value
                if v_type == 'pins':
                    self.restore_background()
                    self.reset_background()
                    return value
                if v_type == 'string' and len(value) >= v_min and len(value) <= v_max:
                    self.restore_background()
                    self.reset_background()
                    return value
                if v_type == 'number' and value == str(v_min):
                    # For solo option which accept -1
                    self.restore_background()
                    self.reset_background()
                    return value
                if v_type == 'number' and value != '' and value.isnumeric() and int(value) >= v_min and int(value) <= v_max:
                    self.restore_background()
                    self.reset_background()
                    return value
                if v_type == 'number' and value != '' and value.isnumeric() and int(value) == 0 and zero:
                    self.restore_background()
                    self.reset_background()
                    return value
                if v_type == 'number':
                    # Refused : the limits are shown (Enter seemed not to work)
                    self.message([f"{v_min} - {v_max}"], 1500, self.colorset['menu-ko'], 'middle', 'big')
                    self.restore_background()
            elif key in ESCAPE_KEYS:
                self.restore_background()
                self.reset_background()
                return 'escape'
            elif key in RIGHT_KEYS : # Add char
                if v_type == 'string' and len(value) < v_max:
                    character = 'a'
                elif (v_type in ('number', 'pins') and int(f"{value}0") <= v_max) or (v_type == 'leds' and len(value) < v_max):
                    if len(value)== 0:
                        character = '1'
                    else:
                        character = '0'
                else:
                    character = ''
                value = f"{value}{character}"

            elif key in BACK_KEYS + LEFT_KEYS :     # Del char
                if len(value) > 0:
                    character = value[-1]
                    value = value[:-1]

            elif key in UP_KEYS + DOWN_KEYS :    # Change char
                if character == '':
                    if v_type in ('leds', 'number', 'pins'):
                        new_char = '0'
                    else:
                        new_char = 'a'
                elif key in UP_KEYS:
                    new_char = self.next_key(character, context=v_type)
                else:
                    new_char = self.previous_key(character, context=v_type)

                if len(value) > 0:
                    value = (f"{value[:-1]}{new_char}")
                else:
                    value = new_char
                character = new_char
            elif len(str(key)) == 1:
                if (v_type == 'string' and len(value) < v_max) \
                or (v_type == 'leds' and len(value) < v_max) \
                or (v_type == 'pins' and int(f"{value}0") <= v_max) \
                or (v_type == 'number' and int(f"{value}0") <= v_max):
                    if v_type != 'string' and value == '0' and str(key) != '0':
                        value = key
                    elif not(v_type == 'number' and value == '' and str(key) == '0') or zero:
                        if str(key).isspace():
                            key = ' '
                        value = f"{value}{key}"
                    character = str(key)
            elif "space" in key:
                value = f"{value} "
                character = ' '

    def reverse_leds(self, leds):
        '''
        Reverse led's values
        '''
        return ",".join(leds.split(',')[::-1])

    def clean_led(self, leds):
        '''
        Clean leds
        '''
        prev = True
        new = ''
        leds = leds.replace('.', ',')
        for led in leds:
            if led != ',':
                new = f'{new}{led}'
                prev = False
            if led == ',' and not prev :
                prev = True
                new = f'{new}{led}'
        if len(leds)> 0 and leds[-1] == ',':
            return new[0:-1:1]
        return new

    def valid_led(self, leds):
        '''
        Check if there is no doubles
        '''
        tab = []
        for led in leds.split(','):
            if led in tab:
                return False
            else:
                tab.append(led)
        return True

    def valid_leds(self, mult, led, leds):
        '''
        Check if there is no doubles
        '''
        tab = []

        # leds = {'S': '128, 129', 'D': '129', 'T': '130'}
        # mult = S
        # led = '128, 129'

        for multiplier in leds:
            if multiplier != mult:
                for led in leds[multiplier].split(','):
                    tab.append(led)

        for led in led.split(','):
            if led in tab:
                return False
        return True

    def valid_all_leds(self, leds, key):
        '''
        Check is data are correct
        '''

        if key not in ('TB', 'EB'):
            for led in leds[key].split(','):
                for o in leds:
                    if o != key and leds[o] != '' and led in leds[o].split(','):
                        return False
        return True

    def setup_pinsleds_menu(self, config, used_pins):
        '''
        Setup pins and brightness of leds
        '''
        selected = 1
        nb_elements = 7
        new = {}

        links = {}
        for key in config:
            new[key] = config[key]

        while True:
            click_zones = {}
            shortcuts = {}

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('setup-pinsleds')

            index = 1
            for key in new:
                shortcut = f'F{index}'
                if key not in ('TYP_STRIPLED', 'TYP_TARGETLED'):
                    click_zones[shortcut] = self.menu_item((index, nb_elements, selected), (shortcut, self.lang.translate(f"menu-{key}"), BTN_VALUE, new[key]), exit=False)
                else:
                    click_zones[shortcut] = self.menu_item((index, nb_elements, selected), (shortcut, self.lang.translate(f"menu-{key}"), BTN_DROPDOWN, new[key]), exit=False)
                links[shortcut] = key
                shortcuts[shortcut] = index

                index += 1

            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')
            click_zones['save'] = self.display_button(nb_elements + 2 == selected, 'save', special='return')

            self.update_screen()

            key = self.rpi.listen_inputs(['arrows'], 
                                         ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'],
                                         events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            # Navigation
            selected = self.navigate(selected, key, nb_elements, 2, 2, left_right=True)

            # Shortcuts
            if key in shortcuts:
                selected = shortcuts[key]
                key = 'enter'

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            #if key in EXTRA_KEYS or (key in ENTER_KEYS and selected == nb_elements + 2):
            #    return Defaults

            if key in SAVE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 2):
                if int(new['PIN_STRIPLED']) != int(new['PIN_TARGETLED']) \
                        or new['PIN_STRIPLED'] == '' or new['PIN_TARGETLED'] == '':
                    return new
                else:
                    self.message(['menu-leds-conflict'], 1000, self.colorset['menu-text-black'], 'middle', 'big')

            if key in ('F1', 'F4') or (selected in (1, 4) and key in ENTER_KEYS):
                key = f'F{selected}'
                tmp = self.input_value_item('pins', new[links[key]], 10, 21)
                if tmp == 'escape' :
                    pass
                elif int(tmp) in used_pins:
                    self.message(['menu-config-already'], 1000, self.colorset['menu-text-black'], 'middle', 'big', bg_color='menu-ko')
                elif tmp != 'escape':
                    new[links[key]] = tmp

            if key in ('F2', 'F6') or (selected in (2, 6) and key in ENTER_KEYS):
                key = f'F{selected}'
                tmp = self.input_value_item('number', new[links[key]], 1, 100)
                if tmp != 'escape':
                    new[links[key]] = tmp

            if key == 'F5' or (selected == 5 and key in ENTER_KEYS):
                key = f'F{selected}'
                tmp = self.input_value_item('number', new[links[key]], 1, 1000)
                if tmp != 'escape':
                    new[links[key]] = tmp

            if key in ('F3', 'F7') or (selected in (3,7) and key in ENTER_KEYS):
                key = f'F{selected}'
                tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, [['grb', 'GRB (ws2812b)'], ['rgb','RGB (ws2815b)']])
                if tmp != 'escape':
                    new[links[key]] = tmp


    def setup_couleurs_segments_menu(self, color_available, dispatcher):
        '''
        Setup couleurs segments d'origine
        '''
        refresh = True
        selected = 1
        nb_elements = 1
        conf_colorset_segments = []
        values_conf_segment = []
        conf_colorset = ['target-simple1','target-simple2',
                         'target-double1','target-double2',
                         'target-triple1','target-triple2',
                         'target-sb','target-db']
        
        conf_values = []
        for val in color_available:
            if val in pygame.color.THECOLORS:
                conf_values.append((val, (pygame.Color(val).r, pygame.Color(val).g, pygame.Color(val).b)))
                
        for conf in conf_colorset:
            conf_colorset_segments.append([conf, self.colorset[conf], 'dropdown_colors', 1, conf_values, 0, False])
                                    
        while True:
            nb_elements = len(conf_colorset)
            click_zones = {}
            shortcuts = []
            cursor = []

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('setup-couleurs-segments')
            
            incr = 0
            paire_impaire = "1"
            for hit in [f'{mult}{num}' for mult in ['S', 'D', 'T'] for num in [20,1,18,4,13,6,10,15,2,17,3,19,7,16,8,11,14,9,12,5]] + ['SB', 'DB']:                
                # Draw the right thing
                if hit in ['SB', 'DB']:
                    score = 'Bull'
                else:        
                    if (int(incr) % 2) == 0:
                        paire_impaire = "2"
                    else:
                        paire_impaire = "1" 
                    incr += 1               
                    multiplier = hit[:1]
                    score = int(hit[1:])                    
                
                if score == 'Bull' :
                    if hit == 'SB':
                        self.draw_bull(True, False, self.colorset[f"target-sb"], center=False)
                    else:
                        self.draw_bull(False, True, self.colorset[f"target-db"], center=False)
                elif multiplier == 'S':
                    self.draw_exterior_simple(self.targets[score], self.colorset[f"target-simple{paire_impaire}"], center=False)
                    self.draw_interior_simple(self.targets[score], self.colorset[f"target-simple{paire_impaire}"], center=False)
                elif multiplier == 'D':
                    self.draw_double(self.targets[score], self.colorset[f"target-double{paire_impaire}"], center=False)
                else:
                    self.draw_triple(self.targets[score], self.colorset[f"target-triple{paire_impaire}"], center=False)

            index = 1
            for confs in conf_colorset_segments:
                if confs[2] == 'dropdown_colors':
                    value = ''
                    for element in confs[4]:
                        if element[0] == confs[1] or element[1] == confs[1]:
                            value = element[0]
                            break
                            
                click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), (f'F{index}', confs[0], BTN_DROPDOWN, value), align='Right')
                shortcuts.append(f'F{index}')
                cursor.append(click_zones[f'F{index}'])                
                index += 1
                
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')
            click_zones['save'] = self.display_button(nb_elements + 2 == selected, 'save', special='return')

            if refresh:
                dispatcher.publish('Background', limit=['TARGET','STRIP','OTHER'])
                self.update_screen()
                refresh = False

            key_press = self.rpi.listen_inputs(['arrows', 'fx'], 
                                         ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'])
                                           #,timeout=int(self.wait_event_time) + 100)
            
            # Click cases
            clicked = self.is_clicked(click_zones, key_press)
            if clicked:
                key_press = clicked

            # Navigation
            selected = self.navigate(selected, key_press, nb_elements, 2, 1, left_right=True)

            # Keyboard cases
            if key_press in shortcuts:
                selected = int(key_press.replace('F', ''))
                key_press = 'enter'
                        
            if key_press in SAVE_KEYS or (key_press in ENTER_KEYS and selected == nb_elements + 2):     
                for key_conf in conf_colorset:
                    values_conf_segment.append((key_conf, self.colorset[key_conf])) 
                dispatcher.publish('off', limit=['TARGET','STRIP','OTHER'])
                return values_conf_segment

            # Key analysis
            if key_press in ESCAPE_KEYS or (key_press in ENTER_KEYS and selected == nb_elements + 1):
                dispatcher.publish('off', limit=['TARGET','STRIP','OTHER'])
                return 'escape'
                                                          
            
            if key_press in ENTER_KEYS:
                if conf_colorset_segments[selected - 1][2] == 'dropdown_colors':
                    value_selected = ''
                    for element in conf_values:
                        if element[0] == conf_colorset_segments[selected - 1][1] or element[1] == conf_colorset_segments[selected - 1][1]:
                            value_selected = element[0]
                            break
                    tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16,
                            conf_colorset_segments[selected - 1][4],
                            special='colors',
                            navigate=value_selected) 
                    if tmp != 'escape':
                        value_selected = ''
                        for element in conf_values:
                            if element[0] == tmp or element[1] == tmp:
                                value_selected = element[1]
                                break
                        conf_colorset_segments[selected - 1][1] = str(tmp)
                        self.colorset[conf_colorset_segments[selected - 1][0]] = value_selected
                        color_values = []
                        for seg in conf_colorset:
                            color_values.append(str(self.colorset[seg]).replace('(','').replace(')','').replace(' ',''))
                        dispatcher.publish('reload', "|".join(color_values), limit=['TARGET','STRIP','OTHER'])
                            
            # Force refresh off screen
            #selection = None
            refresh = True
            
    def setup_cam_menu(self, config_camera):
        '''
        Setup cam menu
        '''        
        menu_configuration = []
        refresh = True
        resw_picts = None
        resh_picts = None
        resw_vids = None
        resh_vids = None
        res_values = []
        menu_config_camera = {x:config_camera[x] for x in config_camera}
       
        for conf in menu_config_camera: 
            zero = False           
            min_value = 0
            max_value = 100
            conf_values = [] 
            if ('camera_id' in conf):
                conf_type = 'check'
                if config_camera[conf] == '-1':
                    menu_config_camera[conf] = False
                else:
                    menu_config_camera[conf] = True
            elif (conf in ('flip_horizontal', 'flip_vertical', 'upload_cloud', 'fullscreen_pop')):
                conf_type = 'check'
                if config_camera[conf] == '0':
                    menu_config_camera[conf] = False
                else:
                    menu_config_camera[conf] = True
            elif ('directory_order' in conf):
                conf_type = 'dropdown'
                conf_values = [('0', 'Date/Jeux'), ('1', 'Jeux/Date')]
            elif ('choice_of_memories' in conf):
                conf_type = 'dropdown'
                conf_values = [('0', 'Rien'), ('1', 'QUE Photos'), ('2', 'QUE Videos'), ('3', 'ALEATOIREMENT Photos ou Videos')]
            elif (conf in ('picture_path', 'video_path', 'events', 'path_google_drive')):
                conf_type = 'string'
                # Google Drive : empty is allowed (the root of the drive)
                min_value = 0 if conf == 'path_google_drive' else 1
                max_value = 128
            elif ('nb_picture' in conf):
                conf_type = 'dropdown'
                for a in range(1,6):
                    conf_values.append((str(a), str(a)))
            elif ('video_duration' in conf):
                conf_type = 'dropdown'
                for a in [ 5, 10, 15 ]:
                    conf_values.append((str(a), str(a)))
            elif ('fps' in conf):
                conf_type = 'dropdown'
                for a in [ 15, 30, 60 ]:
                    conf_values.append((str(a), str(a)))
            elif ('resolutions_available' in conf):
                if menu_config_camera[conf] != '':
                    for res in menu_config_camera[conf].split(','):
                        res_values.append((res, res))
            elif ('picture_res_width' in conf):
                resw_picts = menu_config_camera[conf]
            elif ('picture_res_height' in conf):
                resh_picts = menu_config_camera[conf]
            elif ('video_res_width' in conf):
                resw_vids = menu_config_camera[conf]
            elif ('video_res_height' in conf):
                resh_vids = menu_config_camera[conf]
                
            if conf not in ('picture_path', 'video_path', 'picture_res_width', 'picture_res_height',
                            'video_res_width', 'video_res_height', 'resolutions_available', 'fps', 'duree_ms'): 
                menu_configuration.append([conf, menu_config_camera[conf], conf_type, max_value, conf_values, min_value, zero])
            
        if None != resw_picts and None != resh_picts:
            if res_values == []:
                res_values.append((f"{resw_picts}x{resh_picts}", f"{resw_picts}x{resh_picts}"))
            # On prend par defaut la plus haute resolution pas d'impacte sur le Rpi
            #menu_configuration.append(['picture_res_width*picture_res_height', f'{resw_picts}x{resh_picts}', 'dropdown', 1, res_values, 0, False])
            
        if None != resw_vids and None != resh_vids:
            if res_values == []:
                res_values.append((f"{resw_vids}x{resh_vids}", f"{resw_vids}x{resh_vids}"))
            # On prend par defaut la plus haute resolution, mais diminuer la résolution peut ameliorer la qualite video Rpi
            menu_configuration.append(['video_res_width*video_res_height', f'{resw_vids}x{resh_vids}', 'dropdown', 1, res_values, 0, False])
        
        menu_configuration.append(['take_a_shot', '0', 'check', 1, [], 0, False])
        menu_configuration.append(['take_a_video', '0', 'check', 1, [], 0, False])
        
        nb_elements = len(menu_configuration)
        old_selection = None        
        selected = 1
        self.camera.camera_start()
        
        while True:
            click_zones = {}
            shortcuts = []
            cursor = []

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('setup-cam')
            
            index = 1
            for confs in menu_configuration:
                if confs[2] == 'check' and not confs[1] and confs[0] not in 'camera_id':
                    value = False
                    Cbtn = BTN_CHECK
                elif confs[2] == 'check' and confs[1] and confs[0] not in 'camera_id':
                    value = True
                    Cbtn = BTN_CHECK
                elif confs[2] == 'dropdown':
                    value = ''
                    for element in confs[4]:
                        if element[0] == confs[1] or element[1] == confs[1]:
                            value = element[1]
                    Cbtn = BTN_DROPDOWN
                else:
                    value = confs[1]
                    Cbtn = BTN_VALUE
                if confs[0] in ('camera_id', 'take_a_shot', 'take_a_video'):
                    click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), (f'F{index}', confs[0], BTN_CHOICE, None), align='Left')
                else:
                    click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), (f'F{index}', confs[0], Cbtn, value), align='Left')
                shortcuts.append(f'F{index}')
                cursor.append(click_zones[f'F{index}'])                
                index += 1
            
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')
            click_zones['save'] = self.display_button(nb_elements + 2 == selected, 'save', special='return')

            posX_camera = int(click_zones['F1'][0] + click_zones['F1'][2] + 100)
            posY_camera = int(click_zones['F1'][1] + (click_zones['F1'][3]/2))
            # The preview in the same picture as the menu : drawn after it, it disappeared
            # at each move in the menu, then came back
            self.camera.show_camera(self.screen, posX=posX_camera, posY=posY_camera, load=False)

            ################
            # Update screen
            if refresh:
                self.update_screen()
                refresh = False
            elif old_selection is None:
                self.update_screen(rect_array=[click_zones[cz] for cz in click_zones])

            key = self.rpi.listen_inputs(['arrows', 'fx'],
                                         ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space',\
                                          'backspace']
                                         , events=[(self.wait_event_time, 'EVENT', 'wait')]
                                         , camera=(self.camera, self.screen, posX_camera, posY_camera))
            
            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            # Navigation
            selected = self.navigate(selected, key, nb_elements, 1, 2, left_right=True)
                
            # Key analysis
            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):           
                self.camera.camera_stop()
                return 'escape'
                        
            if key in SAVE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 2):           
                self.camera.camera_stop()
                return config_camera
            
            if key in shortcuts:
                selected = int(key.replace('F', ''))
                key = 'enter'
            elif isinstance(key, str) and len(key) == 1 and selected <= nb_elements and menu_configuration[selected - 1][2] == 'Alpha':
                key = 'enter'
                
            if key in ENTER_KEYS :
                key_press = menu_configuration[selected - 1][0]
                if key_press == 'camera_id':
                    self.camera.camera_stop()
                    camera = self.camera.find_camera()
                    if None is camera:
                        self.update_screen(self.message(['Camera non trouvée!'], wait=3000, color=self.colorset['menu-ko'], size='big', refresh=True))
                    elif not camera:
                        self.update_screen(self.message(['Camera non trouvée!'], wait=3000, color=self.colorset['menu-ko'], size='big', refresh=True))
                    else:
                        self.update_screen(self.message(['Camera trouvée!'], wait=3000, color=self.colorset['menu-ok'], size='big', refresh=True))
                        # Attention : on utilise toujours que la premiere donc '0', mais en cas de branchement/débranchement
                        #             il se peut que l'indice de la premiere change (passe de 0 a 1) et au redemarrage du Rpi on sera de nouveau a 0
                        config_camera['camera_id'] = list(camera.keys())[0]
                        #
                        menu_configuration[selected - 1][1] = config_camera['camera_id']
                        for conf in menu_configuration:
                            if conf[2] == 'dropdown' and (conf[0] == "picture_res_width*picture_res_height" or conf[0] == "video_res_width*video_res_height"):
                                conf[1] = camera[config_camera['camera_id']][0][0]
                                conf[4] = camera[config_camera['camera_id']]
                        resolution_find = []
                        for resol in camera[config_camera['camera_id']]:
                            resolution_find.append(resol[0])
                        config_camera['resolutions_available'] = ','.join(resolution_find)
                        config_camera['picture_res_width'] = camera[config_camera['camera_id']][0][0].split('x')[0]
                        config_camera['picture_res_height'] = camera[config_camera['camera_id']][0][0].split('x')[1]
                        config_camera['video_res_width'] = camera[config_camera['camera_id']][0][0].split('x')[0]
                        config_camera['video_res_height'] = camera[config_camera['camera_id']][0][0].split('x')[1]
                        self.camera.init_var(config_camera, show_in_parametrage=True)
                        self.camera.camera_start()
                                            
                elif key_press in ('flip_horizontal', 'flip_vertical', 'upload_cloud', 'fullscreen_pop'):
                    self.camera.camera_stop()
                    if key_press in ('flip_horizontal', 'flip_vertical', 'upload_cloud', 'fullscreen_pop'):
                        if menu_configuration[selected - 1][1]:
                            menu_configuration[selected - 1][1] = False
                            config_camera[key_press] = '0'
                        else:
                            menu_configuration[selected - 1][1] = True
                            config_camera[key_press] = '1'
                    self.camera.init_var(config_camera, show_in_parametrage=True)
                    self.camera.camera_start()
                        
                elif menu_configuration[selected - 1][2] == 'dropdown':
                    self.camera.camera_stop()
                    tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, 
                                menu_configuration[selected - 1][4], navigate=menu_configuration[selected - 1][1])
                    if tmp != 'escape':
                        menu_configuration[selected - 1][1] = tmp
                        if key_press == 'picture_res_width*picture_res_height':
                            config_camera['picture_res_width'] = tmp.split('x')[0]
                            config_camera['picture_res_height'] = tmp.split('x')[1]
                        elif key_press == 'video_res_width*video_res_height':
                            config_camera['video_res_width'] = tmp.split('x')[0]
                            config_camera['video_res_height'] = tmp.split('x')[1]
                        elif key_press in ('nb_picture', 'video_duration', 'fps', 'directory_order', 'choice_of_memories'):
                            config_camera[key_press] = tmp
                    self.camera.init_var(config_camera, show_in_parametrage=True)
                    self.camera.camera_start()
                        
                elif key_press in ('picture_path', 'video_path', 'events', 'path_google_drive'):
                    click_zone = cursor[selected - 1]
                    tmp = self.input_value_item(menu_configuration[selected - 1][2], menu_configuration[selected - 1][1], 
                            menu_configuration[selected - 1][5], menu_configuration[selected - 1][3], 
                            text = menu_configuration[selected - 1][0], zero = menu_configuration[selected - 1][6])
                    if tmp != 'escape':
                        menu_configuration[selected - 1][1] = tmp
                        if key_press in ('events', 'path_google_drive'):
                            config_camera[key_press] = tmp
                        else:
                            if not os.path.exists(tmp):
                                response = self.wait_validation('dir-dont-exist-create')
                                if response:
                                    os.mkdir(tmp)
                                    self.update_screen(self.message(['abstracted'], wait=3000, color=self.colorset['menu-ok'], size='big', refresh=True))
                            if key_press in ('picture_path', 'video_path'):
                                config_camera['picture_path'] = tmp.split('*')[0]
                
                elif key_press in ('take_a_shot', 'take_a_video'):
                    if key_press in 'take_a_shot':
                        self.camera.take_a_shot(start_stop=False)
                    elif key_press in 'take_a_video':
                        self.camera.take_a_video((self.screen, self.defaultfontpath, posX_camera, posY_camera))
                            
            # Force refresh off screen
            refresh = True

    def setup_led_menu(self, number, s_value, d_value, t_value, e_value, bull=False):
        '''
        Setup leds menu
        '''

        pos_x = 3 * self.res_x_16
        pos_y = int(self.res['y'] / 8)
        W = 10 * self.res_x_16
        H = int(self.res['y'] * 3 / 4)

        w = int(W / 10)
        h = int(H / 8)

        texts = {'S': 'simple', 'D': 'double', 'T': 'triple', 'E': 'tire'}
        values = {'S': s_value, 'D': d_value, 'T': t_value, 'E': e_value}
        selected = [1, 2]
        while True:
            click_zones = {}
            shortcuts = {}
            cursor = {}

            self.new_blit_rect(pos_x, pos_y, W, H, self.colorset['menu-buttons'], border_color=self.colorset['menu-border'], border_size=10, border_radius=30, Alpha=255, corners='All', )
            self.blit_text(f"{self.lang.translate('paramled_text1')} {number}", pos_x + int(W / 4), pos_y, int(W / 2), h, self.colorset['menu-text'], align='Center')
            self.blit_text(f"{self.lang.translate('paramled_text2')}", pos_x + int(W / 4), pos_y + int(h * 3 / 4), int(W / 2), int(h / 2), self.colorset['menu-text'], align='Center')
            self.blit_text(f"{self.lang.translate('paramled_text3')}", pos_x + int(W / 4), pos_y + int(h * 9 / 8), int(W / 2), int(h / 2), self.colorset['menu-text'], align='Center')
            self.blit_text(f"{self.lang.translate('paramled_text4')}", pos_x + int(W / 4), pos_y + int(h * 3 / 2), int(W / 2), int(h / 2), self.colorset['menu-text'], align='Center')

            index = 0
            if bull:
                keys = ['S', 'D']
                nb_elements = 2
            else:
                keys = ['S', 'D', 'T', 'E']
                nb_elements = 4

            for key in keys:
                index += 1
                if index % 2 == 0:
                    Alpha = self.alpha2
                else:
                    Alpha = self.alpha
                x_ = pos_x + w
                for column in range(1, 5):
                    y_ = pos_y + (1 + index) * h
                    w_ = w
                    align='Left'

                    if column == 1:
                        text = texts[key]
                        background_color = 'menu-item-black'
                        textColor = 'menu-text-white'
                        index_click_zone = None
                    elif column == 2:
                        text = values[key]
                        if values[key] == '':
                            background_color = 'menu-buttons'
                        elif self.valid_leds(key, values[key], values) is False:
                            background_color = 'menu-ko'
                        elif self.valid_led(values[key]) is False:
                            background_color = 'menu-warning'
                        else:
                            background_color = 'menu-ok'
                        textColor = 'menu-text-black'
                        index_click_zone = key
                        w_ = 5 * w
                    elif column == 3:
                        text = 'reverse'
                        background_color = 'menu-alternate'
                        textColor = 'menu-text-white'
                        index_click_zone = f'I-{key}'
                    else:
                        text = 'test'
                        background_color = 'menu-shortcut'
                        textColor = 'menu-text-black'
                        index_click_zone = f'T-{key}'
                        align='Center'


                    self.new_blit_rect(x_, y_, w_, h, self.colorset[background_color], Alpha=Alpha, border_color=self.border_color(selected, column, index))
                    self.blit_text(text, x_, y_, w_, h, self.colorset[textColor], align=align)
                    if index_click_zone != None:
                        click_zones[index_click_zone] = (x_, y_, w_, h)
                        shortcuts[index_click_zone] = [index, column]
                        cursor[f"{index}-{column}"] = index_click_zone

                    x_ += w_

            if selected[0] == nb_elements + 1:
                self.new_blit_rect(pos_x + w, pos_y + 7 * h, 2 * w, int(h / 2),
                        self.colorset['menu-ok'], corners = 'All', border_radius = 10,
                        border_color = self.colorset['menu-text-white'])
            else:
                self.new_blit_rect(pos_x + w, pos_y + 7 * h, 2 * w, int(h / 2),
                        self.colorset['menu-item-black'], corners = 'All', border_radius = 10)
            click_zones['escape'] = (pos_x + w, pos_y + 7 * h, 2 * w, int(h / 2))
            self.blit_text('back', pos_x + w, pos_y + 7 * h, 2 * w, int(h / 2),
                   self.colorset['menu-text-white'])

            if selected[0] == nb_elements + 2:
                self.new_blit_rect(pos_x + 7*w, pos_y + 7 * h, 2 * w, int(h / 2),
                        self.colorset['menu-ok'], corners = 'All', border_radius = 10,
                        border_color = self.colorset['menu-text-white'])
            else:
                self.new_blit_rect(pos_x + 7*w, pos_y + 7 * h, 2 * w, int(h / 2),
                        self.colorset['menu-item-black'], corners = 'All', border_radius = 10)
            self.blit_text('save', pos_x + 7*w, pos_y + 7 * h, 2 * w, int(h / 2),
                    self.colorset['menu-text-white'])
            click_zones['save'] = (pos_x + 7*w, pos_y + 7 * h, 2 * w, int(h / 2))

            self.update_screen(rect=(pos_x, pos_y, W, H))

            key = self.rpi.listen_inputs(['arrows', 'fx'], 
                                         ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'],
                                         events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            if key in shortcuts:
                selected =[shortcuts[key][0], shortcuts[key][1]]
                key = 'enter'

            # Navigation (right and left : see grid_step)
            if key not in LEFT_KEYS + RIGHT_KEYS:
                selected = [self.navigate(selected[0], key, nb_elements, 2, 2), selected[1]]

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected[0] == nb_elements + 1):
                return 'escape'

            if key in SAVE_KEYS or (key in ENTER_KEYS and selected[0] == nb_elements + 2):
                return values['S'], values['D'], values['T'], values['E']

            if key == 'space':
                if selected == 1:
                    values['S'] = ''
                elif selected == 2:
                    values['D'] = ''
                elif selected == 3:
                    values['T'] = ''
                else:
                    values['E'] = ''
            elif key in ENTER_KEYS :
                C = cursor[f"{selected[0]}-{selected[1]}"]
                if len(C) == 1:
                    tmp = self.clean_led(self.input_value_item('leds', values[C], 0, 43))
                    if tmp != 'escape':
                        values[C] = tmp
                elif C[0:2:1] == 'I-':
                    # Reverse
                    values[C[2]] = self.reverse_leds(values[C[2]])
                elif C[0:2:1] == 'T-':
                    # Try this
                    C = cursor[f"{selected[0]}-{selected[1]}"]
                    ret = 'try|'
                    if selected[0] == 1:
                        ret += f"-S:{values['S']}"
                    elif selected[0] == 2:
                        ret += f"-D:{values['D']}"
                    elif selected[0] == 3:
                        ret += f"-T:{values['T']}"
                    elif selected[0] == 4:
                        ret += f"-E:{values['E']}"
                    return ret

            elif key in LEFT_KEYS + RIGHT_KEYS:
                selected = self.grid_step(cursor, selected, nb_elements, 2, key)

    def setup_leds_menu(self, leds, sel_y, sel_x, Nmoy):
        '''
        Leds setup menu
        '''
        selected = [sel_y, sel_x]

        if '|' in leds :    # Submenu
            if sel_x == 5:
                sub = ''
            else:
                sub = leds.split('|')[0]
            leds = leds.split('|')[1]
        else:
            sub = ''

        if leds != '':
            leds = ast.literal_eval(leds)
        else:
            leds = {}

        List = {}
        for number in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', 'B']:
            for multiplier in ['S', 'D', 'T', 'E']:
                if number == 'B' and multiplier in ('T', 'E'):
                    continue
                index = f"{multiplier}{number}"
                try:
                    List[index] = leds[index]
                except:
                    List[index] = ''

        numbers = ['20', '1', '18', '4', '13', '6', '10', '15', '2', '17', '3', '19', '7', '16', '8', '11', '14', '9', '12', '5', 'B']

        H = self.res_y_16
        N = 1
        S = 6
        D = 2
        T = 2
        E = 2

        nb_elements = 1
        key = ''
        while True:
            if selected[0] <= 5:
                Nmoy = 6
            elif selected[0] > 4 and selected[0] < 18:
                if key in UP_KEYS:
                    Nmoy -= 1
                elif key in DOWN_KEYS:
                    Nmoy += 1
            else:
                Nmoy = 18

            click_zones = {}
            shortcuts = {}
            cursor = {}

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('setup-leds')

            pos_x = min_x = self.res_x_16
            W = self.res_x_16

            pos_y = 3*H
            self.new_blit_rect(pos_x, pos_y, N*W, H, self.colorset['menu-item-black'])
            self.new_blit_rect(pos_x + N*W, pos_y, S*W, H, self.colorset['menu-item-black'])
            self.blit_text("simple", pos_x + N*W, pos_y, S*W, H, self.colorset['menu-text-white'], align='Left')
            self.new_blit_rect(pos_x + W*(N + S), pos_y, D*W, H, self.colorset['menu-item-black'])
            self.blit_text("double", pos_x + W+S*W, pos_y, D*W, H, self.colorset['menu-text-white'], align='Left')
            self.new_blit_rect(pos_x + W*(N + S+D), pos_y, T*W, H, self.colorset['menu-item-black'])
            self.blit_text("triple", pos_x + W+S*W + D*W, pos_y, T*W, H, self.colorset['menu-text-white'], align='Left')
            self.new_blit_rect(pos_x + W*(N + S+D + T), pos_y, E*W, H, self.colorset['menu-item-black'])
            self.blit_text("tire", pos_x + W*(N + S+D + T), pos_y, E*W, H, self.colorset['menu-text-white'])
            self.new_blit_rect(pos_x + W*(N + S+D + T+E), pos_y, W, H, self.colorset['menu-item-black'])
            self.blit_text("test", pos_x + W*(N + S+D + T+E), pos_y, W, H, self.colorset['menu-text-white'])
            pos_y += H
            nb_elements = 0

            index = 0
            for n in numbers:
                pos_x = min_x
                index += 1
                if Nmoy - 5 <= index < Nmoy + 4:
                    if index % 2 == 0:
                        Alpha = self.alpha2
                    else:
                        Alpha = self.alpha
                    if selected[0] == index:
                        background_color = self.colorset['menu-ok']
                    else:
                        background_color = self.colorset['menu-buttons']

                    self.new_blit_rect(pos_x, pos_y, N*W, H, background_color, Alpha=Alpha)
                    self.blit_text(n, pos_x, pos_y, N*W, H, self.colorset['menu-text-black'])
                    pos_x += N * W

                    j = 0
                    for (k, w) in [('S', S), ('D', D), ('T', T), ('E', E), ('A', 1)]:
                        j+=1
                        key = f"{k}{n}"
                        if k == 'A':
                            background_color = self.colorset['menu-shortcut']
                        else:
                            valid = self.valid_all_leds(List, key)
                            if selected[0] == index:
                                if valid:
                                    background_color = self.colorset['menu-ok']
                                else:
                                    background_color = self.colorset['menu-shortcut']
                            elif valid:
                                background_color = self.colorset['menu-buttons']
                            else:
                                background_color = self.colorset['menu-ko']

                        if k == 'A' and selected[1] == 5 and selected[0] == index:
                            borderColor = self.colorset['menu-text-white']
                        elif k != 'A' and selected[1] != 5 and selected[0] == index:
                            borderColor = self.colorset['menu-text-white']
                        else:
                            borderColor = None
                        self.new_blit_rect(pos_x, pos_y, w * W, H, background_color, border_color=borderColor, Alpha=Alpha)
                        if k != 'A' and key not in ('TB', 'EB'):
                            self.blit_text(List[key], pos_x, pos_y, w * W, H, self.colorset['menu-text-black'], align='Left')
                        elif k == 'A':
                            self.blit_text('X', pos_x, pos_y, w * W, H, self.colorset['menu-text-black'], align='Center')
                        click_zones[key] = (pos_x, pos_y, w * W, H)
                        cursor[f'{index}-{j}'] = key
                        shortcuts[key] = [index, j]
                        pos_x += w*W

                    pos_y += H
                nb_elements += 1

            click_zones['escape'] = self.display_button(nb_elements + 1 == selected[0], 'back', special='escape')
            click_zones['save'] = self.display_button(nb_elements + 2 == selected[0], 'save', special='return')

            if sub == '':
                self.update_screen()
                key = self.rpi.listen_inputs(['arrows', 'fx'], 
                                             ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'],
                                            events=[(self.wait_event_time, 'EVENT', 'wait')])
            else:
                selected = shortcuts[f'S{sub}']
                key = 'enter'

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            if key in shortcuts:
                selected = [shortcuts[key][0], shortcuts[key][1]]
                key = 'enter'

            # Navigation (right and left : see grid_step)
            if key in LEFT_KEYS + RIGHT_KEYS:
                selected = self.grid_step(cursor, selected, nb_elements, 2, key)
            else:
                selected = [self.navigate(selected[0], key, nb_elements, 2, 2), selected[1]]

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected[0] == nb_elements + 1) :    # Previous menu
                return 'escape'

            if key in SAVE_KEYS or (key in ENTER_KEYS and selected[0] == nb_elements + 2):
                return List

            if key in ENTER_KEYS :
                n = cursor[f'{selected[0]}-{selected[1]}'][1::]
                if selected[1] == 5:
                    # Try
                    C = cursor[f"{selected[0]}-{selected[1]}"][1:3:1]
                    ret = 'try|'
                    if List[f'S{C}'] != '':
                        ret += '-S:{}'.format(List[f'S{C}'])
                    if List['D{}'.format(C)] != '':
                        ret += '-D:{}'.format(List[f'D{C}'])
                    if C != 'B' and List['T{}'.format(C)] != '':
                        ret += '-T:{}'.format(List[f'T{C}'])
                    if C != 'B' and List['E{}'.format(C)] != '':
                        ret += '-E:{}'.format(List[f'E{C}'])
                    ret += f'|{List}|{n}|{selected[0]}|{selected[1]}|{Nmoy}'
                    return ret

                if n != 'B':
                    tmp = self.setup_led_menu(str(n), List[f'S{n}'], List[f'D{n}'], List[f'T{n}'], List[f'E{n}'])
                else:
                    tmp = self.setup_led_menu(str(n), List[f'S{n}'], List[f'D{n}'], '', '', bull=True)

                if tmp[0:3:1] == 'try':
                    if tmp[5:6] == 'S':
                        List[f'S{n}'] = tmp.split(':')[1]
                    if tmp[5:6] == 'D':
                        List[f'D{n}'] = tmp.split(':')[1]
                    if tmp[5:6] == 'T':
                        List[f'T{n}'] = tmp.split(':')[1]
                    if tmp[5:6] == 'E':
                        List[f'E{n}'] = tmp.split(':')[1]

                    return f"{tmp}|{List}|{n}|{selected[0]}|{1}|{Nmoy}"

                if tmp != 'escape':
                    List[f'S{n}'] = tmp[0]
                    List[f'D{n}'] = tmp[1]
                    List[f'T{n}'] = tmp[2]
                    List[f'E{n}'] = tmp[3]
                    sub = ''
                else:
                    sub = ''

    def test_target_menu(self):
        '''
        Test target menu
        '''
        self.display_background()
        self.menu_header('test-target', subtxt = 'test-target-msg')
        self.update_screen()

        while True:
            stroke = self.rpi.listen_inputs([],
                 ['PLAYERBUTTON', 'GAMEBUTTON', 'BACKUPBUTTON', 'EXTRABUTTON',
                  'TOGGLEFULLSCREEN', 'resize', 'JOKER', 'CHEAT', 'double-click', 'MISSDART',
                  'VOLUME-UP', 'VOLUME-DOWN', 'enter', 'single-click', 'escape', 'space', 'special'],
                  context='test', timeout=10000)

            if stroke is False:
                self.message(['timeout'], 1000, self.colorset['menu-item-black'], 'middle', 'big')
                return

            if stroke == 'escape':
                return

            if stroke and not isinstance(stroke, tuple):
                code = stroke[0]
                message = stroke[1]

                if code == 0:
                    self.play_sound(stroke[1])
                    self.message([message], 200, self.colorset['menu-ok'], 'middle', 'big')
                else:
                    self.message([message], 5000, self.colorset['menu-ko'], 'middle', 'big')

                self.display_background()
                self.menu_header('test-target', subtxt = 'test-target-msg')
                self.update_screen()

    def test_buttons_menu(self):
        '''
        Test buttons menu
        '''
        self.display_background()
        self.menu_header('test-buttons', subtxt = 'test-button-msg')
        self.update_screen()

        while True:

            key_pressed = self.rpi.test_buttons()

            if key_pressed == 'nogpio':
                self.message([self.lang.translate('nogpio')], 2000, self.colorset['menu-item-black'], 'middle', 'big')
                return

            if key_pressed is False:
                self.message(['timeout'], 1000, self.colorset['menu-item-black'], 'middle', 'big')
                return

            if key_pressed == 'escape':
                return

            if isinstance(key_pressed, list) and len(key_pressed) > 0:
                self.message([' / '.join(key_pressed)], 100, self.colorset['menu-item-black'], 'middle', 'big')
                if len(key_pressed) >= 3:
                    return

                self.display_background()
                self.menu_header('test-buttons', subtxt = 'Appuyer sur escape, sur 3 boutons en même temps ou attendez 10 secondes pour quitter.')
                self.update_screen()

    def setup_buttons_menu(self, buttons, Defaults):
        '''
        Buttons setup menu
        '''

        if self.rpi.gpio.mcp1 is None:
            self.message([self.lang.translate('nogpio')], 3000, None, 'middle', 'big', bg_color='menu-ko')
            return 'escape'

        selected = 1
        ext1_buttons = []
        ext1_buttons_list = []
        ext2_buttons = []
        ext2_buttons_list = []

        selected_buttons_list = [('', 'notattributed')]

        for letter in ('A', 'B'):
            for number in (0, 1, 2, 3, 4, 5, 6, 7):
                ext1_buttons_list.append((f'{letter}{number}', f'{letter}{number}'))

        for letter in ('C', 'D'):
            for number in (0, 1, 2, 3, 4, 5, 6, 7):
                ext2_buttons_list.append((f'{letter}{number}', f'{letter}{number}'))

        index = 0
        for button in buttons:
            if buttons[button] != '0' and buttons[button] != '':
                index = 1

        for button in self.rpi.gpio.get_defaults():
            if button.startswith('TOY'):
                ext2_buttons.append(button)
            else:
                ext1_buttons.append(button)

        if index == 0 :    # Tous les boutons à 0
            buttons = Defaults.copy()

        selected_buttons = ext1_buttons
        selected_buttons_list += ext1_buttons_list
        refresh = True
        while True:
            click_zones = {}
            shortcuts = []
            cursor = []
            index = 0

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('setup-buttons')

            #Tabs
            click_zones['F-1'] = self.display_button(-1 == selected, 'extension1', special='tab1')
            shortcuts.append(f'F-1')
            click_zones['F0'] = self.display_button(0 == selected, 'extension2', special='tab3')
            shortcuts.append(f'F0')


            nb_elements = len(selected_buttons)

            index = 0
            for button in selected_buttons:
                index += 1
                if (index // 2) % 2 == 0:
                    Alpha = self.alpha
                else:
                    Alpha = self.alpha2
                if buttons[button] == '':
                    val = 'notattributed'
                else:
                    val = buttons[button]
                click_zones[f'F{index}'] = self.button_item((index, nb_elements, selected), val, button.replace('pin_', ''), Alpha)

                shortcuts.append(f'F{index}')
                cursor.append(click_zones[f'F{index}'])

            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')
            click_zones['reset'] = self.display_button(nb_elements + 2 == selected, 'reset', special='refresh')
            click_zones['save'] = self.display_button(nb_elements + 3 == selected, 'save', special='return')

            # Update screen
            #if refresh:
            if True:
                self.update_screen()
                refresh = False
            else:
                self.update_screen(rect_array=[click_zones[cz] for cz in click_zones])


            key = self.rpi.listen_inputs(['arrows'], ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            # Navigation
            selected = self.navigate(selected, key, nb_elements, 3, 3, zero=-1, item_per_line=2 , left_right=True)

            # Shortcuts
            if key in shortcuts:
                selected = int(key.replace('F', ''))
                key = 'enter'

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            if key in EXTRA_KEYS or (key in ENTER_KEYS and selected == nb_elements + 2):
                return Defaults

            if key in SAVE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 3):
                return buttons

            # Key analysis
            # Change tab
            if selected == -1:
                selected_buttons = ext1_buttons
                selected_buttons_list += ext1_buttons_list
                tab = -1
                refresh = True
                continue
            
            if selected == 0:
                selected_buttons = ext2_buttons
                selected_buttons_list += ext2_buttons_list
                tab = 0
                refresh = True
                continue
            
            if key in ENTER_KEYS :
                key = cursor[selected-1]

                old = buttons[selected_buttons[selected-1]]
                t = self.dropdown(self.res['x'] / 8*3, self.res['y'] / 4, selected_buttons_list, navigate = selected_buttons[selected-1])
                if t != 'escape':
                    for button in buttons:
                        if buttons[button] == t and t != '':
                            buttons[button] = old
                            break
                    buttons[selected_buttons[selected-1]] = t

    '''
    Test toys menu
    '''
    def test_toys_menu(self):
        selected = 1
        nb_elements = 0
        toys = []

        for toy in self.rpi.buttons:
            if (toy.startswith('LIGHT_') or toy.startswith('TOY')) and self.rpi.buttons[toy] != '':
                toys.append((self.rpi.buttons[toy], toy))
                nb_elements += 1

        self.rpi.light_toys(toys, state=False)

        while True:
            click_zones = {}
            shortcuts = []

            # Draw bg
            self.display_background()
            self.menu_header('test-toys')

            index = 1
            for toy in toys:
                if toy[0] != '0':
                    Fx = f'F{index}'
                    click_zones[Fx] = self.menu_item((index, nb_elements, selected)
                            , (Fx, f'{toy[0]}  --  {self.lang.translate(toy[1])}', BTN_CHOICE, None)
                            , exit=False)
                    shortcuts.append(Fx)
                    index += 1

            if index == 1:
                self.message([self.lang.translate('notoyset')], 2000, None, 'middle', 'big', bg_color='menu-ko')
                return

            # go back and next
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')

            ################
            # Update screen
            self.update_screen()

            key = self.rpi.listen_inputs(['arrows', 'fx'], 
                                         ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'],
                                         events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            # Navigation
            selected = self.navigate(selected, key, nb_elements, 1, 1, left_right=True)

            # Keyboard cases
            if key in shortcuts:
                selected = int(key.replace('F', ''))
                key = 'enter'

            # Key analysis
            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            if key in ENTER_KEYS :
                toy = toys[selected - 1][1]
                self.rpi.gpio.strobe_toys([toy], delay_on=1200, delay_off=400)


    def setup_menu(self):
        '''
        Main setup menu : described by the files of menus (menus/defaults.yaml...)
        '''
        menus = self.menus()
        buttons = [button for button in menus.buttons('settings') if button.get('visible', True) is not False]
        return menus.result(self.run_menu('settings', buttons, menus.buttons('settings')))

    def miscellaneous(self, update):
        '''
        Miscellaneous : described by the files of menus (menus/defaults.yaml...). The check
        of the updates stays here : the menu gives the hand back for its button
        '''
        self.dmd.send_text(f"{self.lang.translate('parameters')}")
        menus = self.menus()
        while True:
            buttons = [button for button in menus.buttons('miscellaneous') if button.get('visible', True) is not False]
            button = self.run_menu('miscellaneous', buttons, menus.buttons('miscellaneous'))
            if button.get('action') != 'update':
                return menus.result(button)

            version = update[0].get_version(self.logs)
            try:
                self.update_screen(self.message(['update-check'], 0, None, 'middle'))
                last = update[0].get_last(self.logs, version)

                if last is None:
                    self.update_screen(self.message(['no-update-available'], 1500, None, 'middle'))
                else:
                    response = self.wait_validation("update-available")
                    if response:
                        self.update_screen(self.message(['update-download'], 0, None, 'middle'))
                        new_version = None
                        if update[0].download_update(self.logs, last):
                            self.update_screen(self.message(['updating'], 0, None, 'middle'))
                            new_version = update[0].apply_update(self.logs, last)

                        if new_version is None:
                            self.update_screen(self.message(['update-failed'], 1500, None, 'middle'))
                        else:
                            self.update_screen(self.message([f'Version {new_version} installée', 'restarting'], \
                                    1000,  'middle', bg_color='menu-ok'))
                            version = new_version

                            response = self.wait_validation("Voulez-vous redémarrer?")
                            if response:
                                return 'restart'
            except Exception as exception:
                self.logs.debug("[WARNING] Unable to check/get updates.")
                self.logs.debug(f"[WARNING] Error was {exception}")
                self.logs.debug(f"version is {version}")

    def border_color(self, selected, pos_x, pos_y):
        '''
        Return border's color according selected item or not
        '''
        if selected[0] == pos_y and selected[1] == pos_x:
            return self.colorset['menu-border']

        return None

    def event_menu(self, event_name, S_Animations, T_Animations, Colors, Event):
        '''
        Event <> animation link menu
        '''
        empty_animation = ',1,random,10'
        empty_element = ['', 1, 'random', 10]
        if Event is None:
            #if event_name not in ('touch', 'SB', 'DB'):
            if event_name not in ('touch'):
                Event = {'TARGET':[empty_animation], 'STRIP':[empty_animation], 'DMD':[empty_animation], 'MATRIX':[empty_animation], 'OTHER':[',,,']}
            else:
                Event = {'STRIP':[empty_animation], 'DMD':[empty_animation], 'MATRIX':[empty_animation], 'OTHER':[',,,']}
        # Adding missing devices
        for device in ['STRIP', 'TARGET', 'DMD', 'MATRIX', 'OTHER']:
            if device not in Event:
                Event[device] = [empty_animation]
            elif len(Event[device]) == 0 and device in ['STRIP', 'TARGET'] and event_name not in ('touch'):
                Event[device] = ['']

        if self.selected is None:
            self.selected = [1, 1]

        S_Animations_DD = []
        for a in S_Animations:
            S_Animations_DD.append([a, a])

        T_Animations_DD = []
        for a in T_Animations:
            T_Animations_DD.append([a, a])

        count_dropdown = []
        for index in [1, 2, 3, 4, 5, 10, 15, 20, 50, 100]:
            count_dropdown.append([str(index), str(index)])

        colors_dropdown = []
        for color in Colors:
            colors_dropdown.append([color, color])

        delay_dropdown = []
        for delay in [1, 2, 5, 10, 20, 50, 100, 200, 500]:
            delay_dropdown.append([str(delay), str(delay)])

        #if event_name not in ('touch', 'SB', 'DB'):
        if event_name not in ('touch'):
            deviceList = ['TARGET', 'STRIP']
        else:
            deviceList = ['STRIP']

        title = self.lang.translate('menu-event') + ' "' + self.lang.translate(f"event-{event_name}") + '"'
        key = ''
        act = ''
        refresh = True
        selection = None

        while True:
            nb_elements = 0
            for element in Event:
                if element in deviceList:
                    nb_elements += len(Event[element])
            i = 0
            k = 0
            if self.selected[0] > nb_elements + 3:
                self.selected = [1, 1]
            elif self.selected[0] < 1:
                self.selected = [nb_elements + 3, 1]

            click_zones = {}
            shortcuts = {}
            cursor = {}
            left = []

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header(title, subtxt = '5 animations maxi par évènement')

            # + STRIP  | Ring   | blue   | 2
            # +        | Strobe | red    | 2
            # +-------- + -------- + -------- + ---
            # + TARGET | Ring   | yellow | 3
            # +-------- + -------- + -------- + ---
            # + DMD    | yes/no
            # +-------- + -------- + -------- + ---
            # + MATRIX | yes/no

            nb_animations = 0
            for element in Event:
                if element not in deviceList:
                    continue
                nb_animations += len(Event[element])
            pos_y = 3 * self.res_y_16
            for element in Event:
                if element not in deviceList:
                    continue
                i += 1

                if i % 2 == 0:
                    background_color = self.colorset['menu-text-white']
                else:
                    background_color = self.colorset['menu-shortcut']
                device = Event[element]

                pos_x = int(self.res['x'] * 2.5 / 16)
                nb = len(Event[element])
                if nb_animations <= 9:
                    H = self.res_y_16
                else:
                    H = int(10 * self.res_y_16 / nb_animations)

                # 1st : Animation device
                w = int(self.res['x'] * 2 / 16)
                rect = pygame.Rect(pos_x, pos_y, w, H)
                if nb == 1:
                    self.new_blit_rect2(rect, background_color, corners='Left')
                else:
                    self.new_blit_rect2(rect, background_color, corners='TopLeft')

                self.blit_text2(element, rect, self.colorset['menu-text-black'])

                j = 0
                for e in Event[element]:
                    if j % 2 == 0:
                        Alpha = self.alpha
                    else:
                        Alpha = self.alpha2
                    if j > 0:
                        i += 1
                    j+=1
                    if j == 2:
                        pos_x = int(self.res['x'] * 2.5 / 16)
                        rect = pygame.Rect(pos_x, pos_y, w, H)
                        border_color = self.border_color(self.selected, 0, i)
                        self.new_blit_rect2(rect, self.colorset['menu-shortcut'], corners='BottomLeft', alpha=Alpha, border_color=border_color)
                        self.blit_text2('try', rect, self.colorset['menu-text-black'])
                        click_zones[f'{element}-0-try'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-0-try'] = (element, 10, 'try', i, 0)
                        cursor[f'{k + 1}-0'] = f'{element}-0-try'
                        left.append(i)

                    pos_x = int(self.res['x'] * 2.5 / 16 + w)
                    W = self.res_x_16

                    if element in deviceList:
                        selected = False
                        k += 1
                        if e.count(',') < 3:
                            elts = empty_element
                            Event[element] = [empty_animation]
                        else:
                            elts = e.split(',')

                        rect = pygame.Rect(pos_x, pos_y, 3 * W, H)
                        border_color = self.border_color(self.selected, 1, k)
                        selected = [k, 1] == self.selected

                        if j <= 2 or j != nb:
                            self.new_blit_rect2(rect, self.colorset['menu-buttons'], alpha=Alpha, border_color=border_color, selected=selected)
                        else:
                            self.new_blit_rect2(rect, self.colorset['menu-buttons'], alpha=Alpha, corners='BottomLeft', border_color=border_color, selected=selected)

                        self.blit_text2(elts[0], rect, self.colorset['menu-text-white'])
                        click_zones[f'{element}-{j}-anim'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-anim'] = (element, j, 'anim', i, 1)
                        cursor[f'{k}-1'] = f'{element}-{j}-anim'

                        rect.x = rect.right
                        rect.width = W

                        border_color = self.border_color(self.selected, 2, k)
                        selected = [k, 2] == self.selected

                        self.new_blit_rect2(rect, self.menu_color(self.colorset['menu-ok']), alpha=Alpha, border_color=border_color, selected=selected)
                        self.blit_text2(elts[1], rect, self.colorset['menu-text-white'])
                        click_zones[f'{element}-{j}-count'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-count'] = (element, j, 'count', i, 2)
                        cursor[f'{k}-2'] = f'{element}-{j}-count'

                        rect.x = rect.right
                        rect.width = 2 * W

                        border_color = self.border_color(self.selected, 3, k)
                        selected = [k, 3] == self.selected

                        self.new_blit_rect2(rect, self.colorset['menu-ok'], alpha=Alpha, border_color=border_color, selected=selected)
                        self.blit_text2(elts[2], rect, self.colorset['menu-text-black'])
                        click_zones[f'{element}-{j}-color'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-color'] = (element, j, 'color', i, 3)
                        cursor[f'{k}-3'] = f'{element}-{j}-color'

                        # Color
                        rect.x = rect.right
                        rect.width = rect.height

                        border_color = self.border_color(self.selected, 4, k)
                        selected = [k, 4] == self.selected

                        self.new_blit_rect2(rect, self.colorset['menu-shortcut'], alpha=Alpha, border_color=border_color, selected=selected)
                        self.blit_text2(elts[3], rect, self.colorset['menu-text-black'])
                        click_zones[f'{element}-{j}-delay'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-delay'] = (element, j, 'delay', i, 4)
                        cursor[f'{k}-4'] = f'{element}-{j}-delay'

                        # Up
                        rect.x = rect.right
                        border_color = self.border_color(self.selected, 4, k)
                        selected = [k, 5] == self.selected

                        if nb > 1:
                            updown_color = self.colorset['menu-alternate']
                        else:
                            updown_color = self.menu_color(self.colorset['menu-inactive'])

                        self.new_blit_rect2(rect, self.menu_color(updown_color), alpha=Alpha, border_color=border_color, selected=selected)
                        if j > 1:
                            self.blit_text2('^', rect, self.colorset['menu-text-black'])
                        click_zones[f'{element}-{j}-moveup'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-moveup'] = (element, j, 'moveup', i, 5)
                        cursor[f'{k}-5'] = f'{element}-{j}-moveup'

                        # Down
                        rect.x = rect.right
                        border_color = self.border_color(self.selected, 4, k)
                        selected = [k, 6] == self.selected

                        self.new_blit_rect2(rect, updown_color, alpha=Alpha, border_color=border_color, selected=selected)
                        if j < nb:
                            self.blit_text2('v', rect, self.colorset['menu-text-black'])
                        click_zones[f'{element}-{j}-movedown'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-movedown'] = (element, j, 'movedown', i, 6)
                        cursor[f'{k}-6'] = f'{element}-{j}-movedown'

                        if nb < 5:
                            plus_color = self.menu_color(self.colorset['menu-ok'])
                        else:
                            plus_color = self.menu_color(self.colorset['menu-inactive'])

                        # Plus
                        rect.x = rect.right
                        border_color = self.border_color(self.selected, 7, k)
                        selected = [k, 7] == self.selected

                        self.new_blit_rect2(rect, plus_color, alpha=Alpha, border_color=border_color, selected=selected)

                        click_zones[f'{element}-{j}-plus'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-plus'] = (element, j, 'plus', i, 7)
                        cursor[f'{k}-7'] = f'{element}-{j}-plus'
                        if nb < 5:
                            self.blit_text2('+', rect, self.colorset['menu-text-black'])

                        # Minus
                        rect.x = rect.right
                        border_color = self.border_color(self.selected, 8, k)
                        selected = [k, 8] == self.selected

                        minus_color = self.colorset['menu-ok']
                        self.new_blit_rect2(rect, minus_color, alpha=Alpha, border_color=border_color, selected=selected)
                        self.blit_text2('-', rect, self.colorset['menu-text-black'])
                        click_zones[f'{element}-{j}-minus'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-minus'] = (element, j, 'minus', i, 8)
                        cursor[f'{k}-8'] = f'{element}-{j}-minus'

                        # Try
                        rect.x = rect.right
                        rect.width *= 2
                        border_color = self.border_color(self.selected, 9, k)
                        selected = [k, 9] == self.selected

                        if nb == 1:
                            self.new_blit_rect2(rect, self.colorset['menu-shortcut'], corners='Right', alpha=Alpha, border_color=border_color, selected=selected)
                        elif j == 1:
                            self.new_blit_rect2(rect, self.colorset['menu-shortcut'], corners='TopRight', alpha=Alpha, border_color=border_color, selected=selected)
                        elif j == nb:
                            self.new_blit_rect2(rect, self.colorset['menu-shortcut'], corners='BottomRight', alpha=Alpha, border_color=border_color, selected=selected)
                        else:
                            self.new_blit_rect2(rect, self.colorset['menu-shortcut'], alpha=Alpha, border_color=border_color, selected=selected)

                        self.blit_text2('try', rect, self.colorset['menu-text-black'])
                        click_zones[f'{element}-{j}-try'] = (rect.x, rect.y, rect.w, rect.h)
                        shortcuts[f'{element}-{j}-try'] = (element, j, 'try', i, 9)
                        cursor[f'{k}-9'] = f'{element}-{j}-try'

                    pos_y += H
                pos_y += H

            # go back and next
            click_zones['escape'] = self.display_button(nb_elements + 1 == self.selected[0], 'back', special='escape')
            click_zones['try'] = self.display_button(nb_elements + 2 == self.selected[0], 'try', special='refresh')
            click_zones['save'] = self.display_button(nb_elements + 3 == self.selected[0], 'save', special='return')
            shortcuts['try'] = ('event', 0, 'try', nb_elements + 2, 0)

            if self.selected[0] <= nb_elements:
                selection = click_zones[cursor[f"{self.selected[0]}-{self.selected[1]}"]]
            elif nb_elements + 1 == self.selected[0]:
                selection = click_zones['escape']
            elif nb_elements + 2 == self.selected[0]:
                selection = click_zones['try']
            elif nb_elements + 3 == self.selected[0]:
                selection = click_zones['save']
            else:
                selection = None

            ################
            # Update screen
            if refresh:
                self.update_screen()
                refresh = False
            elif old_selection is not None and selection is not None:
                self.update_screen(rect_array=[old_selection, selection])
            else:
                self.update_screen(rect_array=[click_zones[click_zone] for click_zone in click_zones])

            key = self.rpi.listen_inputs(['math', 'arrows', 'fx'], ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space', 'backspace'])

            act = ''
            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked
            if key in PLUS_KEYS:
                key = cursor[f"{self.selected[0]}-7"]
            elif key in MINUS_KEYS:
                key = cursor[f"{self.selected[0]}-8"]

            if key not in ['escape', 'BACKUPBUTTON', 'BTN_GAMEBUTTON', 'enter', 'save'] + DIRECTION_KEYS:
                try:
                    T = shortcuts[key]
                    dev = T[0]
                    index = int(T[1])-1
                    act = T[2]
                    y = int(T[3])
                    x = T[4]
                    self.selected = [y, x]

                    if act == 'try':
                        if index == -1:
                            act = 'tryE'            # try whole event
                        elif index == 9:
                            act = 'tryD'            # try device animation
                        else:
                            act = 'tryA'            # try only this animation
                except:
                    act = key
            else:
                act = key

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and self.selected[0] == nb_elements + 1):
                return 'escape'

            if key in EXTRA_KEYS or (key in ENTER_KEYS and self.selected[0] == nb_elements + 2):
                act = 'tryE'
            elif key in SAVE_KEYS or (key in ENTER_KEYS and self.selected[0] == nb_elements + 3):
                # Clean empty animations
                for device in Event:
                    devices = []
                    for anim in Event[device]:
                        if anim == empty_animation:
                            anim = ''
                        else:
                            devices.append(anim)
                    Event[device] = devices
                return str(Event)

            elif key in ENTER_KEYS:
                try:
                    T = shortcuts[cursor[f"{self.selected[0]}-{self.selected[1]}"]]
                    dev = T[0]
                    index = int(T[1])-1
                    act = T[2]
                    if act == 'try':
                        if index == -1:
                            act = 'tryE'            # try whole event
                        elif index == 9:
                            act = 'tryD'             # try device animation
                        else:
                            act = 'tryA'            # try only this animation
                except:
                    act = act
                refresh = True
            elif key in LEFT_KEYS + RIGHT_KEYS:
                self.selected = self.grid_step(cursor, self.selected, nb_elements, 3, key)
            elif key in UP_KEYS:
                if self.selected[0] == 1:
                    self.selected = [nb_elements + 2, 1]
                elif self.selected[0] in left and self.selected[1] == 0:
                    self.selected = [self.selected[0] - 1, 1]
                elif self.selected[0] > nb_elements:
                    self.selected = [nb_elements, 1]
                else:
                    self.selected = [self.selected[0] - 1, self.selected[1]]
            elif key in DOWN_KEYS:
                if self.selected[0] == nb_elements:
                    self.selected = [nb_elements + 2, 1]
                elif self.selected[0] > nb_elements:
                    self.selected = [1, 1]
                elif self.selected[0] in left and self.selected[1] == 0:
                    self.selected = [self.selected[0] + 1, 1]
                else:
                    self.selected = [self.selected[0] + 1, self.selected[1]]
            elif key == 'resize':    # Resize screen
                self.create_screen(False, self.rpi.newresolution)
                refresh = True
            elif key == 'TOGGLEFULLSCREEN':    # Toggle fullscreen
                self.create_screen(True, False)
                refresh = True

            if act == 'anim':
                if dev == 'STRIP':
                    tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, S_Animations_DD, navigate=Event[dev][index].split(',')[0])
                else:
                    tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, T_Animations_DD, navigate=Event[dev][index].split(',')[0])
                if tmp != 'escape':
                    anim = Event[dev][index].split(',')
                    an = anim[0]
                    it = anim[1]
                    co = anim[2]
                    de = anim[3]
                    Event[dev][index] = f"{tmp},{it},{co},{de}"
                refresh = True
            elif act == 'count':
                tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, count_dropdown, navigate=Event[dev][index].split(',')[1])
                if tmp != 'escape':
                    anim = Event[dev][index].split(',')
                    an = anim[0]
                    it = anim[1]
                    co = anim[2]
                    de = anim[3]
                    Event[dev][index] = f"{an},{tmp},{co},{de}"
                refresh = True
            elif act == 'color':
                tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, colors_dropdown, special='colors', navigate=Event[dev][index].split(',')[2])
                if tmp != 'escape':
                    anim = Event[dev][index].split(',')
                    an = anim[0]
                    it = anim[1]
                    co = anim[2]
                    de = anim[3]
                    Event[dev][index] = f"{an},{it},{tmp},{de}"
                refresh = True
            elif act == 'delay':
                tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, delay_dropdown, navigate=Event[dev][index].split(',')[3])
                if tmp != 'escape':
                    anim = Event[dev][index].split(',')
                    an = anim[0]
                    it = anim[1]
                    co = anim[2]
                    de = anim[3]
                    Event[dev][index] = f"{an},{it},{co},{tmp}"
                refresh = True
            elif act in PLUS_KEYS:
                if len(Event[dev]) < 5:
                    Event[dev].append(empty_animation)
                    refresh = True
            elif act in MINUS_KEYS:
                del Event[dev][index]
                if len(Event[dev]) == 0:
                    Event[dev].append(empty_animation)
                refresh = True

            elif act == 'movedown' and index + 1 < len(Event[dev]):
                tmp = Event[dev][index + 1]
                Event[dev][index + 1] = Event[dev][index]
                Event[dev][index] = tmp
                refresh = True
            elif act == 'moveup' and index > 0:
                tmp = Event[dev][index]
                Event[dev][index] = Event[dev][index - 1]
                Event[dev][index - 1] = tmp
                refresh = True

            elif act == 'tryE':
                # Try event (all animations, on all devices)
                ret = 'tryE'
                ret += f'|{Event}|'
                for d in Event:
                    ret += f"-{d}:{';'.join(Event[d])}"
                return ret.replace('|+', '|')
            elif act == 'tryD':
                # Try animation of specific device (ex TARGET)
                ret = f"tryD|{Event}|{dev}:{';'.join(Event[dev])}"
                return ret

            elif act == 'tryA':
                # Try specific animation on specific device
                ret = f"tryA|{Event}|{dev}:{Event[dev][index]}"
                return ret
            old_selection = selection

    def animations_menu(self, events, selected_event=None):
        '''
        Leds animations menu
        '''
        selected = 1
        index = 0
        for event in events:
            index += 1
            if selected_event == event:
                selected = index

        nb_elements = len(events)
        self.dmd.send_text(f"{self.lang.translate('animations')}", tempo=2)

        refresh = True

        while True:
            click_zones = {}
            shortcuts = []
            cursor = {}

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('animations-menu')

            index = 0
            for event in events:
                index += 1
                click_zones[event] = self.menu_item((index, nb_elements, selected), (None, f"event-{event}", BTN_CHOICE, None), align='Half')
                shortcuts.append(event)
                cursor[event] = index

            # go back and next
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')

            ################
            # Update screen
            if refresh:
                self.update_screen()
                refresh = False
            else:
                self.update_screen(rect_array=[click_zones[cz] for cz in click_zones])

            key = self.rpi.listen_inputs(['arrows', 'fx'], 
                                         ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space', 'backspace'],
                                         events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            # Navigation
            selected = self.navigate(selected, key, nb_elements, 1, 1, left_right=True)
            if selected <= nb_elements:
                text = f"event-{shortcuts[selected - 1]}"
            else:
                text = 'back'
            self.dmd.send_text(f"{self.lang.translate(text)}")

            # Shortcuts
            if key in shortcuts:
                selected = int(cursor[key])
                key = 'enter'

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            # (Right goes to the next one, as everywhere : a knob set on right and left goes
            # through the list ; it opened the selected one)
            if key in ENTER_KEYS:
                return shortcuts[selected - 1]

    def customization_menu(self, customization, colors_available):
        '''
        Customization menu
        '''
        selected = 1
        all_customization = []
        game_customization = []
        general_customization = []
        avoid = []
        refresh = True

        nb_elements = 0
        for option in customization:
            min_value = 1
            max_value = 10000
            zero = False

            if option in ('startpercent', 'nbcol', 'resx', 'resy', 
                    'masterserver', 'endgamestats', 'videosound_multiplier', 'pnj_time',
                    'exhibition_mode', 'exhibition_items', 'illumination_mode', 'illumination_color',
                    'idle_light_color', 'colorset', 'font'):
                avoid.append([option, customization[option], '', 0, []])
                continue

            if option in ('endgamestats', 'bypass-stats', 'onscreenbuttons', 'fullscreen',
                    'keeporder', 'play_firstname', 'nextplayer_music', 'print_dartstroke', 'light_target', 'light_strip', 'idle_light',
                    'competition_mode', 'exhibition_mode', 'illumination_mode', 'fast_games_mode', 'only_favorites_games_mode', 'check_for_updates'):  
                option_type = 'check'
                option_values = []
                if customization[option] == 'False' or customization[option] is False:
                    customization[option] = False
                else:
                    customization[option] = True
            elif option in ('sound_multiplier'):
                option_type = 'slider'
                min_value = 0
                max_value = 100
                option_values = 5
                zero = 1
            elif option in ('soundvolume'):
                option_type = 'slider'
                min_value = 0
                max_value = 100
                option_values = 10
                zero = 1
            elif option in ('pnj_time', 'blinktime', 'releasedartstime', 'waitevent_time', 'nextplayer_sound_duration'):
                option_type = 'slider'
                min_value = 500
                max_value = 5000
                zero = 1000         # Divisé par
                option_values = 500 # Pas
                if option == 'waitevent_time':
                    min_value = 15000
                    max_value = 180000
                    option_values = 3000
                if option == 'nextplayer_sound_duration':
                    min_value = 3000
                    max_value = 30000
                if option == 'releasedartstime':
                    min_value = 0
                    max_value = 30000
            elif option in ('solo', 'resx', 'resy', 'nbcol'):
                option_type = 'number'
                option_values = []
                if option == 'solo':
                    min_value = -1
                    zero = True
                elif option in ('resx', 'resy'):
                    min_value = 200
                    if option == 'resx':
                        max_value = 1920
                    else:
                        max_value = 1080
                elif option == 'nbcol':
                    min_value = 6
                    max_value = 6
            elif option == 'locale':
                option_type = 'dropdown'
                option_values = []
                for l in [name for name in os.listdir('locales') if os.path.isdir(os.path.join('locales', name)) ]:
                    option_values.append((l, self.lang.translate(l)))
            elif option == 'debuglevel':
                option_type = 'dropdown'
                option_values = [('0', 'Debug'), ('1', 'Warnings'), ('2', 'Errors'), ('3', 'Fatal errors'), ('4', 'Infos'), ('5', 'No logs')]
            elif option == 'videos':
                option_type = 'dropdown'
                option_values = [('0', 'videos-none'), ('1', 'videos-special'), ('2', 'videos-all')]
            elif option == 'preferedcategory':
                option_type = 'dropdown'
                option_values = [('classic', 'classic'), ('fun', 'fun'), ('sport', 'sport')]
            elif option == 'sound_output':
                # HDMI, jack of the Raspberry, USB sound card (include/caudio.py)
                option_type = 'dropdown'
                option_values = [(output, f'sound-output-{output}') for output in ('auto', 'hdmi', 'jack', 'usb')]
            elif option == 'illumination_color':
                option_type = 'dropdown_colors'
                option_values = [(val, val) for val in colors_available]
            elif option in ('idle_strip_color', 'idle_target_color'):
                # The light out of games : off, the colours of the segments (target), or a colour
                option_type = 'dropdown_colors'
                option_values = [('off', self.lang.translate('idle-off-target' if option == 'idle_target_color' else 'idle-off'))]
                if option == 'idle_target_color':
                    option_values.append(('origin', self.lang.translate('idle-origin')))
                option_values += [(val, val) for val in colors_available if val != 'random']
            else:
                option_type = 'string'
                option_values = []
                min_value = 1
                if option == 'netgamecreator':
                    max_value = 12
                else:
                    max_value = 64
                    
            all_customization.append([option, customization[option], option_type, max_value, option_values, min_value, zero])
            
            if option in ('pnj_time', 'nextplayer_sound_duration', 'nextplayer_music', 'releasedartstime', 'onscreenbuttons', 'keeporder', 'videos', \
                'play_firstname', 'print_dartstroke', 'light_target', 'light_strip', 'waitevent_time', 'competition_mode', \
                'illumination_mode', 'illumination_color', 'idle_light', 'idle_strip_color', 'idle_target_color'):
                game_customization.append([option, customization[option], option_type, max_value, option_values, min_value, zero])
            else:
                general_customization.append([option, customization[option], option_type, max_value, option_values, min_value, zero])

        selected_customization = game_customization
        tab = -1

        old_selection = None
        while True:
            nb_elements = len(selected_customization)
            click_zones = {}
            shortcuts = []
            cursor = []

            # Draw bg
            self.display_background()

            # Titles
            self.menu_header('customization')

            # Tabs
            click_zones['F-1'] = self.display_button(-1 == selected, 'game', special='tab1')
            shortcuts.append(f'F-1')
            click_zones['F0'] = self.display_button(0 == selected, 'general', special='tab3')
            shortcuts.append(f'F0')

            index = 0
            rows = (nb_elements + 1) // 2
            for option in selected_customization:
                index += 1
                # Two columns : the first half on the left, the other on the right ; down goes
                # on from the bottom of the left one to the top of the right one
                column = (0, rows, index) if index <= rows else (1, rows, index - rows)

                if option[2] == 'check' and not option[1]:
                    value = False
                    Cbtn = BTN_CHECK
                elif option[2] == 'check' and option[1]:
                    value = True
                    Cbtn = BTN_CHECK
                elif 'dropdown' in option[2]:
                    value = ''
                    for element in option[4]:
                        if element[0] == option[1] or element[1] == option[1]:
                            value = element[1]
                    Cbtn = BTN_DROPDOWN
                else:
                    value = option[1]
                    Cbtn = BTN_VALUE

                if option[2] == 'slider':
                    number = float(value)

                    if (number / option[6]) % 1 == 0:
                        value = int(int(value) / option[6])
                    else:
                        value = int(value) / option[6]
                    click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), (f'F{index}', option[0], Cbtn, value), align='Full', tabs=True, column=column)
                else:
                    click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), (f'F{index}', option[0], Cbtn, value), align='Full', tabs=True, column=column)

                shortcuts.append(f'F{index}')
                cursor.append(click_zones[f'F{index}'])

            if selected <= nb_elements:
                if selected_customization[selected - 1][2] == 'numeric':
                    allowed = ['arrows', 'fx', 'num', 'math']
                elif selected_customization[selected - 1][2] == 'Alpha':
                    allowed = ['arrows', 'fx', 'num', 'math', 'alpha']
                else:
                    allowed = ['arrows', 'fx']
            else:
                allowed = ['arrows', 'fx']

            # go back and next
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')
            click_zones['save'] = self.display_button(nb_elements + 2 == selected, 'save', special='return')

            if selected <= nb_elements:
                selection = click_zones[f'F{selected}']
            elif nb_elements + 1 == selected:
                selection = click_zones['escape']
            elif nb_elements + 2 == selected:
                selection = click_zones['save']
            else:
                selection = None

            ################
            # Update screen
            if refresh:
                self.update_screen()
                refresh = False
            elif old_selection is None:
                self.update_screen(rect_array=[click_zones[cz] for cz in click_zones])
            else:
                self.update_screen(rect_array=[old_selection, selection])

            key = self.rpi.listen_inputs(allowed, ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space', 'backspace'],
                                         events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked

            # Navigation in menu. Right and left in reading order : the two tabs, the options, the
            # buttons at the bottom (they went between the tabs, and opened an option)
            if key in LEFT_KEYS + RIGHT_KEYS:
                order = list(range(-1, nb_elements + 3))
                position = order.index(selected) if selected in order else 0
                selected = order[(position + (1 if key in RIGHT_KEYS else -1)) % len(order)]
            else:
                selected = self.navigate(selected, key, nb_elements, 2, 2, zero=-1, tab=tab)

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            if key in SAVE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 2):
                customization = {}
                for option in game_customization + general_customization:
                    customization[option[0]] = option[1]
                for option in avoid:
                    customization[option[0]] = option[1]

                return customization

            if key in shortcuts:
                selected = int(key.replace('F', ''))
                key = 'enter'
            elif isinstance(key, str) and len(key) == 1 and selected <= nb_elements and selected_customization[selected - 1][2] == 'Alpha':
                key = 'enter'

            if selected == -1:
                # Game options
                selected_customization = game_customization
                tab = -1
                refresh = True
                continue

            if selected == 0:
                # General options
                selected_customization = general_customization
                tab = 0
                refresh = True
                continue

            if key in ENTER_KEYS:
                if selected_customization[selected - 1][2] == 'check':
                    if selected_customization[selected - 1][1]:
                        selected_customization[selected - 1][1] = False
                    else:
                        selected_customization[selected - 1][1] = True
                elif selected_customization[selected - 1][2] == 'slider':
                    act_value = float(selected_customization[selected - 1][1])
                    min_value = selected_customization[selected - 1][5]
                    max_value = selected_customization[selected - 1][3]
                    step = selected_customization[selected - 1][4]
                    title = selected_customization[selected - 1][0]
                    diviser = selected_customization[selected - 1][6]

                    tmp = self.slider(title, act_value, min_value, max_value, step=step, diviser=diviser)
                    if tmp != 'escape':
                        selected_customization[selected - 1][1] = str(tmp)
                    # Force refresh off screen
                    selection = None
                    
                elif selected_customization[selected - 1][2] == 'dropdown_colors':
                    tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16,
                            selected_customization[selected - 1][4],
                            special='colors',
                            navigate=selected_customization[selected - 1][1]) 
                    if tmp != 'escape':
                        selected_customization[selected - 1][1] = str(tmp)
                    # Force refresh off screen
                    selection = None
                    refresh = True
                    
                elif selected_customization[selected - 1][2] == 'dropdown':
                    tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16,
                            selected_customization[selected - 1][4],
                            navigate=selected_customization[selected - 1][1])
                    if tmp != 'escape':
                        selected_customization[selected - 1][1] = tmp
                    # Force refresh off screen
                    selection = None
                    refresh = True
                else:
                    click_zone = cursor[selected - 1]
                    tmp = self.input_value_item(selected_customization[selected - 1][2],
                            selected_customization[selected - 1][1],
                            selected_customization[selected - 1][5],
                            selected_customization[selected - 1][3],
                            text = selected_customization[selected - 1][0],
                            zero = selected_customization[selected - 1][6])
                    if tmp != 'escape':
                        if selected_customization[selected - 1][2] == 'number':
                            selected_customization[selected - 1][1] = int(tmp)
                        else:
                            selected_customization[selected - 1][1] = tmp
            old_selection = selection

    def server_menu(self, NetClient, ServerList):
        '''
        Server Menu : Choice server before create/join network games
        '''
        nb_elements = len(ServerList)
        if nb_elements == 0 :    # No prefered servers
            return 'noserver'

        if nb_elements == 1 : #Only one, no choice, skip the screen
            return ServerList[0]

        # Draw bg
        self.display_background()

        # Titles
        self.menu_header('server-menu')

        self.message(['check-server'], wait = 0)

        self.update_screen()
        List = []

        for server in ServerList:
            txt = server.split('.')[0]
            if NetClient.test_host(server) == True:
                Valid = True
            else:
                Valid = False
                txt += " ({self.lang.translate('server-unreachable')})"
            List.append((server, Valid, txt))

        else :    # You have to make a choice
            selected =1

            while True:
                # Round the selected clock ;)
                if selected > nb_elements + 2:
                    selected = 1
                if selected == 0:
                    selected = nb_elements + 2

                click_zones = {}

                # Draw bg
                self.display_background()

                # Titles
                self.menu_header('server-menu')

                shortcuts = []
                index = 0
                for s in List:
                    index += 1
                    click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), (f"F{index}", s[2], BTN_CHOICE, None), valid=s[1])
                    shortcuts.append(f'F{index}')

                # go back and next
                click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')

                ################
                # Update screen
                self.update_screen()

                key = self.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON', 'single-click', 'enter', 'space'])

                # Click cases
                clicked = self.is_clicked(click_zones, key)
                if clicked:
                    key = clicked

                # Navigation menu
                selected = self.navigate(selected, key, nb_elements, 1, 1, left_right=True)

                #Shortcuts
                if key in shortcuts:
                    key = 'enter'
                    selected = int(clicked.replace('F', ''))

                # Keyboard cases (right goes to the next one, as everywhere : it validated)
                if key in ENTER_KEYS:
                    if selected == nb_elements + 1:
                        key = 'escape'
                    elif selected == nb_elements + 2:
                        key = 'enter'
                    elif List[selected - 1][1]:
                        return List[selected - 1][0]

                elif key in ESCAPE_KEYS :    # Previous menu
                    return 'escape'

    def infos_menu(self, Conf):
        '''
        Infos menu
        '''
        import shutil
        import psutil

        ratio = 1 / 3

        while True:
            total, used, free = shutil.disk_usage("/")

            # Draw bg
            self.display_background()

            # Rpi version:
            # cat /proc/device-tree/model

            # Titles
            self.menu_header(self.lang.translate('technical-informations'))

            self.display_row(1, 2, 1, [("Hardware", 1 / 2), ('Version', 1 / 2)], ratio, offset=-2)
            self.display_row(2, 2, 0, [("Raspberry", 1 / 2), (Conf.rpi_version, 1 / 2)], ratio, offset=-2)

            self.display_row(1, 4, 1, [("Software", 1 / 2), ('Version', 1 / 2)], ratio, 1)
            self.display_row(2, 4, 0, [("Raspydarts", 1 / 2), (Conf.pyDartsFullVersion, 1 / 2)], ratio, 1)

            self.display_row(3, 4, 0, [("Python", 1 / 2), (sys.version.split(' ')[0], 1 / 2)], ratio, 1)
            self.display_row(4, 4, 0, [("Pygame", 1 / 2), (str(pygame.version.ver), 1 / 2)], ratio, 1)

            if len(self.ips) > 0:
                self.display_row(1, 1 + len(self.ips), 1, [("Interface", 1 / 2), ("Adresse IP", 1 / 2)], ratio, 6)

            index = 1
            for ip in self.ips:
                index += 1
                self.display_row(index, 1 + len(self.ips), 0, [(ip[0], 1 / 2), (ip[1], 1 / 2)], ratio, 6)

            cpu_freq = f"{psutil.cpu_freq().current:.0f} ({psutil.cpu_freq().min:.0f} - {psutil.cpu_freq().max:.0f})"

            self.display_row(1, 6, 1, [("Information", 1 / 2), ("Value", 1 / 2)], ratio, 8 + len(self.ips))
            self.display_row(2, 6, 0, [("Résolution", 1 / 2), (f"{self.res_x} x {self.res_y}", 1 / 2)], ratio, 8 + len(self.ips))
            self.display_row(3, 6, 0, [("Disk occupation", 1 / 2), ("{} %".format(round(100 * used / total, 1)), 1 / 2)], ratio, 8 + len(self.ips))
            self.display_row(4, 6, 0, [("RAM occupation", 1 / 2), ("{} %".format(psutil.virtual_memory()[2]), 1 / 2)], ratio, 8 + len(self.ips))
            self.display_row(5, 6, 0, [("CPU usage", 1 / 2), ("{} %".format(psutil.cpu_percent()), 1 / 2)], ratio, 8 + len(self.ips))
            self.display_row(6, 6, 0, [("CPU frequency", 1 / 2), (cpu_freq, 1 / 2)], ratio, 8 + len(self.ips))

            self.update_screen()

            key = self.rpi.listen_inputs(['arrows', 'fx', 'alpha', 'math'],
                         ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON',
                        'single-click', 'double-click', 'resize', 'VOLUME-UP', 'VOLUME-DOWN', 'enter', 'space'], \
                        timeout = 2000)
            if key is not False:
                break

    def menus(self):
        '''
        Menus described by the files (see cmenus), read again when the theme changes
        '''
        theme_dir = getattr(self.file_class, 'theme_dir', None)
        if getattr(self, 'menus_read', None) is None or self.menus_theme != theme_dir:
            self.menus_read = cmenus.Menus(self.logs, theme_dir, cpaths.user_dir())
            self.menus_theme = theme_dir
        return self.menus_read

    def main_menu_items(self, everything=False):
        '''
        Buttons shown in the main menu : all of them, or those of the exhibition mode. Those
        chosen in its screen (exhibition_items), else those of the file (exhibition: true).
        everything : all the buttons which can be shown (screen of the exhibition mode)
        '''
        menus = self.menus()
        buttons = [self.favorite_button(button) for button in menus.buttons('main') if button.get('visible', True) is not False]
        if everything or not bool(self.config.get_value('SectionGlobals', 'exhibition_mode')):
            return buttons
        chosen = [name for name in str(self.config.get_value('SectionGlobals', 'exhibition_items', False) or '').split(',') if name]
        if chosen:
            shown = [button for button in buttons if menus.button_id(button) in chosen]
        else:
            shown = [button for button in buttons if button.get('exhibition')]
        # Nothing chosen : a game can be played all the same
        return shown or buttons[:1]

    def favorites(self):
        '''
        The favorites fav1, fav2... (section 13)
        '''
        if getattr(self, 'favorites_saved', None) is None:
            self.favorites_saved = cfavorites.Favorites(self.logs)
        return self.favorites_saved

    def favorite_button(self, button):
        '''
        A button of the files : for a favorite (favorite:fav1), the text and the logo of its
        game by default, unavailable (state disabled : greyed, does nothing) when it is empty
        '''
        action = str(button.get('action') or '')
        if not action.startswith('favorite:'):
            return button
        name = action[9:]
        favorite = self.favorites().get(name)
        button = dict(button)
        if favorite is None:
            # Not 'disabled' : in a file, that is the look of the state disabled (section 7.2)
            button['unavailable'] = True
            number = name[3:] if name.startswith('fav') else name
            button.setdefault('text', f"{self.lang.translate('favorite')} {number} : {self.lang.translate('favorite-empty')}")
        else:
            button.setdefault('text', favorite['game'].replace('_', ' '))
            button.setdefault('logo', favorite['game'])
            button['game_logo'] = self.file_class.get_full_filename(f"logos_menu/{favorite['game']}", 'images')
        return button

    def ask_quit_game(self):
        '''
        Leave the game ? A dart on the key Escape left it at once : No selected first. The screen
        kept for this question was the one of another game : drawn again
        '''
        for key in [key for key in self.menu_backgrounds if key[0] == 'question']:
            self.menu_backgrounds.pop(key)
        # The game darkened behind the question : its texts mixed with those of the question
        game_background = self.game_background
        if game_background is not None:
            self.game_background = game_background.copy()
            self.game_background.fill(QUESTION_VEIL, special_flags=pygame.BLEND_RGB_MULT)
        try:
            return self.ask_yes_no(self.lang.translate('quit-game-question'), initial='no')
        finally:
            self.game_background = game_background

    def ask_yes_no(self, question, explanation=None, cancel=False, initial=None):
        '''
        A question answered by Yes or No (menu question of the files : its look), back : No
        (cancel : None, nothing is done). explanation : under the question (subtitle) ;
        initial : the answer selected first
        '''
        items = [{'id': 'yes', 'action': 'yes', 'text': 'yes', 'shortcut': 'F1'},
                 {'id': 'no', 'action': 'no', 'text': 'no', 'shortcut': 'F2'}]
        escape = {'id': 'cancel' if cancel else 'no', 'action': 'no', 'text': 'no', 'shortcut': 'escape'}
        previous = self.current_look
        self.current_look = None
        try:
            answer = self.run_menu('question', items, items + [escape], title=question,
                                   subtitle=explanation, initial=initial).get('id')
            return None if answer == 'cancel' else answer == 'yes'
        finally:
            self.current_look = previous

    def favorite_game_options(self, game, preset=None):
        '''
        Screen of the options of a favorite game (its options : those saved for the game, and
        those already defined for the favorite over them). None : given up
        '''
        name = game.replace(' ', '_')
        module = importlib.import_module(f'games.{cmenus.game_category(name)}.{name}')
        options = dict(module.OPTIONS)
        saved = self.config.read_file(f"game-{name}") or {}
        options.update({option: value for option, value in saved.items() if option in options})
        options.update({option: value for option, value in (preset or {}).items() if option in options})
        try:
            limits = self.config.get_value('NbOfPlayersPerGame', name)
            count = max(1, int(limits[0])) + (1 if bool(limits[2]) and int(limits[0]) % 2 else 0)
        except Exception:    # pylint: disable=broad-except
            count = 1
        result = self.options_menu(options, name, count, favorite=True)
        return None if result == 'escape' else result

    def favorite_players(self):
        '''
        The favorite players (Divers > Joueurs favoris) : the players of a favorite button
        made in the screen Jeux favoris
        '''
        names = self.config.get_value('Favorites', 'firstnames', False, None, split=',') or []
        return [str(name).strip() for name in names if str(name).strip()]

    def favorite_save(self, game, options):
        '''
        A favorite game and its options placed on a button fav1... of the main menu, with
        the number of players and how they are chosen (section 13). False : not saved
        '''
        favorites = self.favorites()
        back = {'id': 'back', 'action': 'back', 'text': 'back', 'footer': 'left', 'shortcut': 'escape'}
        slots = []
        taken = {}
        for number in range(1, cfavorites.SLOTS + 1):
            name = f'fav{number}'
            current = favorites.get(name)
            what = current['game'].replace('_', ' ') if current else self.lang.translate('favorite-empty')
            if current:
                taken[name] = what
            slots.append({'id': name, 'action': f'favorite:{name}', 'text': f"{number} : {what}", 'shortcut': f'F{number}'})
        free = next((slot['id'] for slot in slots if slot['id'] not in taken), None)
        # Menus of their own (files of menus : favorite_save, favorite_players), not the look
        # of the screen of the options
        previous = self.current_look
        self.current_look = None
        try:
            while True:
                slot = self.run_menu('favorite_save', slots + [back], slots + [back], initial=free)
                if slot.get('id') == 'back':
                    return False
                # The others are kept : a favorite saved is replaced only if wanted
                if slot['id'] not in taken or self.ask_yes_no(
                        f"{self.lang.translate('favorite-replace')} {slot['id'][3:]} ({taken[slot['id']]}) ?"):
                    break
            chosen = self.favorite_players_choice(game)
            if chosen is None:
                return False
            mode, count, players = chosen
            favorites.save(slot['id'], game, options, count, mode, players)
            self.message([self.lang.translate('favorite-saved').replace('{number}', slot['id'][3:])], 1500, None, 'middle', 'big')
            return True
        except Exception as error:    # pylint: disable=broad-except
            self.logs.error(f"Favorites : not saved ({error})")
            self.message([self.lang.translate('favorite-not-saved')], 2500, 'menu-ko', 'middle', 'big')
            return False
        finally:
            self.current_look = previous

    def favorite_players_choice(self, game, current=None):
        '''
        How the players of a numbered favorite are chosen : (mode, count, players), None : back.
        current : the favorite changed (its choice selected first)
        '''
        names = self.known_players()
        back = {'id': 'back', 'action': 'back', 'text': 'back', 'footer': 'left', 'shortcut': 'escape'}
        modes = []
        if names:
            # Chosen among the favorite players and the bank of firstnames
            modes.append({'id': 'choose', 'action': 'favorite:choose', 'shortcut': 'F1',
                          'text': self.lang.translate('favorite-choose')})
        modes.append({'id': 'generic', 'action': 'favorite:generic', 'shortcut': f'F{len(modes) + 1}',
                      'text': self.lang.translate('favorite-generic')})
        modes.append({'id': 'last', 'action': 'favorite:last', 'shortcut': f'F{len(modes) + 1}',
                      'text': self.lang.translate('favorite-last')})
        modes.append({'id': 'ask', 'action': 'favorite:ask', 'shortcut': f'F{len(modes) + 1}',
                      'text': self.lang.translate('favorite-ask')})
        previous = self.current_look
        self.current_look = None
        try:
            # Back in the choice of the players or of their number : back to this question
            while True:
                mode = self.run_menu('favorite_players', modes + [back], modes + [back],
                                     initial=current['mode'] if current else None)
                if mode.get('id') == 'back':
                    return None
                players = []
                count = 1
                if mode['id'] == 'choose':
                    players = self.pick_favorite_players(names, current['names'] if current else None)
                    count = len(players or [])
                elif mode['id'] in ('generic', 'last'):
                    count = self.favorite_count(game, generic=mode['id'] == 'generic')
                if players is not None and count is not None:
                    return mode['id'], count, players
        finally:
            self.current_look = previous

    def favorite_launch(self, name, last_players):
        '''
        A favorite chosen in a menu : (favorite, players) to start its game at once (players
        None : chosen first in the screen of the players), None if it cannot (empty) or if the
        player gives up (the last players do not match)
        '''
        favorite = self.favorites().get(name)
        if favorite is None:
            self.message([self.lang.translate('favorite-empty')], 2000, 'menu-ko', 'middle', 'big')
            return None
        players, warning = cfavorites.Favorites.players_for(favorite, last_players, self.lang.translate('favorite-player'))
        if warning and not self.wait_validation(self.lang.translate(f'favorite-{warning}')):
            return None
        return favorite, players

    def button_text(self, button):
        '''
        Text of a button : a key of translation, a text, or a text per language
        '''
        text = button.get('text', self.menus().button_id(button))
        if isinstance(text, dict) and not set(text) <= self.LANGUAGES:
            # Look of the text (size, font...), not its translations : its text in 'text' (as
            # the titles), otherwise the name of the button
            text = text.get('text', self.menus().button_id(button))
        if isinstance(text, dict):
            language = str(self.config.get_value('SectionGlobals', 'locale', False) or 'en')[:2]
            text = text.get(language) or text.get('en') or next(iter(text.values()), '')
        return str(text)

    def styled_text(self, button):
        '''
        Text of a button drawn by the files : a setting has only one part there, its value with it
        '''
        text = self.lang.translate(self.button_text(button))
        if 'value' not in button:
            return text
        value = button['value']
        value = 'yes' if value is True else 'no' if value is False else str(value)
        return f"{text} : {self.lang.translate(value)}"

    @staticmethod
    def button_label(button, menu=None):
        '''
        Shortcut written on a button : its first key (F1, ESC...) in the format of the menu
        (shortcuts: format, '{key}' by default), None if it has none or if they are hidden
        (shortcuts: show: false : they still work)
        '''
        settings = (menu or {}).get('shortcuts') or {}
        if settings.get('show') is False and not Screen.revealed:
            return None
        keys = cmenus.as_list(button.get('shortcut'))
        if not keys or str(keys[0]).lower() == 'none':
            return None
        key = str(keys[0])
        key = 'ESC' if key == 'escape' else key
        return str(settings.get('format') or '{key}').replace('{key}', key)

    # Look of the titles when the files say nothing (section 7.1)
    TITLE_LOOK = {'size': '5%', 'color': 'menu-text'}
    SUBTITLE_LOOK = {'size': '3.5%', 'color': 'menu-text', 'position': 'below_title'}

    def menu_text_look(self, name, key):
        '''
        Title or subtitle of a menu (section 7.1) : its text, and its look (font, size, colour,
        background, place) from the defaults then from the menu ; {} : the look of always.
        Written as a text, or as a block with its text : {text: ..., size: ...}
        '''
        data = self.menus().data
        default = (data.get('defaults') or {}).get(key)
        own = ((data.get('menus') or {}).get(name) or {}).get(key)
        # A text per language ({fr: ..., en: ...}) is a text, not a look
        default, own = [{'text': value} if isinstance(value, dict) and value and set(value) <= self.LANGUAGES else value
                        for value in (default, own)]
        look = {}
        for value in (default, own):
            if isinstance(value, dict):
                look = cmenustyle.merge(look, {k: v for k, v in value.items() if k != 'text'})
        if isinstance(own, dict):
            text = own.get('text')
        elif own is not None:
            text = own
        else:
            text = default if not isinstance(default, dict) else default.get('text')
        if isinstance(text, dict):
            # A text per language
            language = str(self.config.get_value('SectionGlobals', 'locale', False) or 'en')[:2]
            text = text.get(language) or text.get('en') or next(iter(text.values()), '')
        return (str(text) if text else None), look

    @staticmethod
    def move_selection(rects, selected, direction):
        '''
        Arrows : the closest button in the direction (docs/menu/menus.md, 9), by the edges of the
        buttons (not their centres : a button as wide as the screen has the buttons of the row
        under it below it, even far from its centre). In the direction : the buttons beyond its
        edge ; those facing it (sharing part of its width, or of its height) first : the closest
        row, the one facing it the most, the first in reading order ; then, up and down only, the
        others : gap + 2 x distance across between the edges. None : right and left go on in reading order (the end of a row : the
        first button of the next row ; left : the one before) ; up and down go around, to the
        farthest one facing it on the other side
        '''
        horizontal = direction in ('left', 'right')
        sign = 1 if direction in ('right', 'down') else -1

        def spans(rect):
            # (start, end) along the direction, then across it
            x, y, width, height = rect[:4]
            return ((x, x + width), (y, y + height)) if horizontal else ((y, y + height), (x, x + width))

        (start, end), (across_start, across_end) = spans(rects[selected])

        def beyond(rect, way):
            # Beyond the edge of the selected button on this side (a little overlap allowed : the
            # selected button is drawn larger), and how far
            (low, high), _ = spans(rect)
            gap = low - end if way > 0 else start - high
            return gap >= -0.3 * (high - low), max(0, gap)

        def facing(rect):
            # A few pixels shared are not facing : the selected button, drawn larger, reached
            # the row under it
            _, (low, high) = spans(rect)
            shared = min(high, across_end) - max(low, across_start)
            return shared if shared > 0.1 * min(high - low, across_end - across_start) else min(shared, 0)

        def apart(rect):
            # Distance across between its edges and those of the selected one (it does not
            # face it) : by the centres, a far button in line with it won over a near one
            _, (low, high) = spans(rect)
            return max(low - across_end, across_start - high, 0)

        # Rows of reading by the tops of the buttons : a button whose top is above the middle of
        # the first one of the row is in it (the same when a button is drawn larger, a few pixels
        # higher). By their middles, a tall element (the panel of the players online, beside all
        # the rows) came after the first rows : right went round them, the others never reached
        rows = []
        for index in sorted(rects, key=lambda index: (rects[index][1], index)):
            if rows and rects[index][1] < rows[-1][0]:
                rows[-1][1].append(index)
            else:
                rows.append((rects[index][1] + rects[index][3] / 2, [index]))
        order = [index for _middle, row in rows for index in sorted(row, key=lambda index: (rects[index][0], index))]
        row_of = {index: number for number, (_middle, row) in enumerate(rows) for index in row}

        best, wrap = None, None
        for index, rect in rects.items():
            if index == selected:
                continue
            if horizontal and row_of[index] != row_of[selected]:
                # Right and left stay on the row of reading (a tall element facing several rows
                # was reached from all of them, the others never)
                continue
            shared = facing(rect)
            ahead, gap = beyond(rect, sign)
            if ahead:
                if shared > 0:
                    # The part of it facing the selected one (in tenths : one pixel apart is equal)
                    part = round(shared / max(1, spans(rect)[1][1] - spans(rect)[1][0]), 1)
                    score = (0, round(gap), -part, spans(rect)[1][0], index)
                elif not horizontal:
                    score = (1, gap + 2 * apart(rect), 0, 0, index)
                else:
                    # Right and left stay on the row : a button above or below it is reached
                    # in reading order (in diagonal, a free placement went round in circles
                    # on three buttons, the others never reached)
                    continue
                if best is None or score < best[0]:
                    best = (score, index)
            elif not horizontal and shared > 0 and beyond(rect, -sign)[0]:
                part = round(shared / max(1, spans(rect)[1][1] - spans(rect)[1][0]), 1)
                score = (-beyond(rect, -sign)[1], -part, spans(rect)[1][0], index)
                if wrap is None or score < wrap[0]:
                    wrap = (score, index)
        if best is not None:
            return best[1]
        if wrap is not None:
            return wrap[1]
        # Right at the end of a row (left at its start) : the next button in reading order (the
        # one before), as a text is read ; all the menu is gone through with right alone
        if len(order) < 2:
            return selected
        return order[(order.index(selected) + sign) % len(order)]

    # Places of the buttons at the bottom of the menus (footer : see display_button)
    FOOTERS = {'left': 'escape', 'center': 'refresh', 'right': 'return'}
    # Secret key of the menus : the shortcut of each button shown, or hidden again (until the
    # game is left ; in a game, c is the cheat dart)
    REVEAL_KEY = 'c'
    # Room chosen in the online games (network_lobby)
    lobby_game = None
    revealed = False
    # The entries of the colours which hid them, given a value while they are shown
    hidden_shortcuts = []

    # Keys of a button which change its look (section 7.2 : style properties on the button)
    STYLE_KEYS = ('shape', 'radius', 'background', 'border', 'shadow', 'selected', 'disabled', 'pressed')
    LANGUAGES = {'fr', 'en', 'de', 'es', 'it'}

    def button_style(self, menu, button):
        '''
        Style of a button : the style named by the button or its menu, then the properties
        written on the button (text: {size...}, color, background...)
        '''
        styles = self.menus().data.get('styles') or {}
        style = dict(styles.get(str(button.get('style') or menu.get('style') or 'classic')) or {})
        inline = {key: button[key] for key in self.STYLE_KEYS if key in button}
        if 'color' in button:
            inline['background'] = cmenustyle.merge(inline.get('background') or {}, {'color': button['color']})
        if isinstance(button.get('text'), dict) and not set(button['text']) <= self.LANGUAGES:
            inline['text'] = {key: value for key, value in button['text'].items() if key != 'text'}
        if isinstance(button.get('icon'), dict):
            inline['icon'] = {key: value for key, value in button['icon'].items() if key != 'image'}
        return cmenustyle.merge(style, inline)

    def button_icon(self, button):
        '''
        Image of the icon of a button : its path, or the image of its look (icon: {image:
        ..., size: ...}), otherwise the logo of its game (favorites), otherwise its logo
        (logos_menu of the theme, as the classic tiles : the same image all along the menu)
        '''
        icon = button.get('icon')
        icon = icon.get('image') if isinstance(icon, dict) else icon
        if isinstance(icon, str):
            return icon
        if button.get('game_logo') or not button.get('logo'):
            return button.get('game_logo')
        if 'logo_image' not in button:
            button['logo_image'] = self.file_class.get_full_filename(f"logos_menu/{button['logo']}", 'images')
        return button['logo_image']

    def menu_styled(self, name, menu, items):
        '''
        A menu drawn by cmenustyle : a style other than classic, a layout or places of its
        own, a background, a title or shortcuts of their own look. Otherwise the classic
        drawing (as always)
        '''
        if str(menu.get('style') or 'classic') != 'classic' or menu.get('area') or menu.get('layout') == 'grid' or \
                menu.get('zones') or isinstance(menu.get('show_version'), dict):
            return True
        if menu.get('background') is not None or self.menu_text_look(name, 'title')[1] or \
                self.menu_text_look(name, 'subtitle')[1]:
            return True
        if any(key in (menu.get('shortcuts') or {}) for key in ('color', 'position', 'size', 'font', 'background')):
            return True
        for button in items:
            if button.get('footer') in self.FOOTERS:
                continue
            if button.get('place') or str(button.get('style') or 'classic') != 'classic' or \
                    any(key in button for key in self.STYLE_KEYS + ('color',)) or isinstance(button.get('icon'), dict) or \
                    (isinstance(button.get('text'), dict) and not set(button['text']) <= self.LANGUAGES) or button.get('icon'):
                return True
        return False

    def reveal_shortcuts(self):
        '''
        The secret key of the menus : the shortcuts shown on all the buttons (those the theme
        hides too), or hidden again as the theme wants
        '''
        Screen.revealed = not Screen.revealed
        if Screen.revealed:
            # The menus drawn the classic way hide them when their entry of the colours is None
            Screen.hidden_shortcuts = [key for key, value in self.colorset.items() if key.endswith('-shortcuts') and value is None]
            for key in Screen.hidden_shortcuts:
                self.colorset[key] = ''
        else:
            for key in Screen.hidden_shortcuts:
                self.colorset[key] = None
            Screen.hidden_shortcuts = []
        self.logs.info(f"Menus : shortcuts {'shown' if Screen.revealed else 'as the theme wants'} (secret key)")

    def run_menu(self, name, items, everything, hook=None, initial=None, title=None, subtitle=None):
        '''
        A menu of the files, drawn as a list of classic buttons (menu_item) and the buttons
        at its bottom (display_button) : returns the button chosen. items : buttons shown ;
        everything : all those which have a shortcut (hidden ones too) ; initial : id of the
        button selected first. The background, the title and the informations are drawn
        once : moving only draws again the buttons whose look changes
        '''
        menus = self.menus()
        menu = menus.menu(name)
        if self.menu_styled(name, menu, items):
            return self.run_styled_menu(name, menu, items, everything, hook, initial, title, subtitle)
        # Title and subtitle : those given (a question...), else those of the files
        title = title or self.menu_text_look(name, 'title')[0]
        subtitle = subtitle or self.menu_text_look(name, 'subtitle')[0]
        show_version = menu.get('show_version') or False
        info = [str(value) for value in cmenus.as_list(menu.get('info'))]
        remember = bool(menu.get('remember'))
        layout = str(menu.get('layout') or 'list')
        keys = {direction: set(menus.keys(direction)) for direction in
                ('up', 'down', 'left', 'right', 'next', 'previous', 'validate', 'back')}
        listed = [button for button in items if button.get('footer') not in self.FOOTERS]
        footers = [button for button in items if button.get('footer') in self.FOOTERS]
        shown = listed + footers
        nb_listed = len(listed)
        nb_shown = len(shown)
        selected = self.selected_menu.get(name, 1) if remember else 1
        if initial is not None:
            selected = next((index for index, button in enumerate(shown, 1) if menus.button_id(button) == initial), selected)
        if not 1 <= selected <= nb_shown:
            selected = 1
        dmd_sent = None
        full = True
        pristine = None
        rects = {}
        drawn = {}
        spaces = []
        space = 0
        for button in listed:
            space += float(button.get('space_before', 0) or 0)
            spaces.append(space)
        # Details of the buttons (the options of a favorite) : under the list, those of the
        # button selected
        with_details = any(button.get('details') for button in listed)
        details_area = None
        details_shown = None
        # A setting (a button with a value) : the line in two parts, as in the pages of settings,
        # all the lines of the menu as wide
        with_values = any('value' in button for button in listed)

        def look(index):
            # Selected or not (with 10 buttons or more, the corners of the neighbours change)
            if index > nb_listed or nb_listed < 10 or layout != 'list':
                return index == selected
            return (index, selected)

        def draw(index):
            button = shown[index - 1]
            if index > nb_listed:
                rects[index] = self.display_button(index == selected, self.button_text(button), self.FOOTERS[button['footer']])
            elif layout == 'tiles':
                # The tiles of always : the logo of each button, in a row (logo_item)
                rects[index] = self.logo_item((index, nb_listed, selected), str(button.get('logo') or ''), nb_listed, 'Center',
                                              limit_height=self.res['y'] / 3, menu=True)
            else:
                # More than 8 buttons go up : under a subtitle, one line lower (tabs)
                kind, value = BTN_CHOICE, None
                if 'value' in button:
                    kind = BTN_CHECK if isinstance(button['value'], bool) else BTN_DROPDOWN
                    value = button['value'] if kind == BTN_CHECK else self.lang.translate(str(button['value']))
                rects[index] = self.menu_item((index, nb_listed, selected), (self.button_label(button, menu), self.button_text(button),
                                              kind, value), space=spaces[index - 1], exit=False,
                                              valid=not button.get('unavailable'), tabs=bool(subtitle) and nb_listed > 8,
                                              align='Full' if with_values else None)
            drawn[index] = look(index)

        while True:
            if hook is not None and hook():
                full = True
            # Text of the selected button on the DMD
            dmd = shown[selected - 1].get('dmd') if 1 <= selected <= nb_shown else None
            if dmd and dmd != dmd_sent:
                self.dmd.send_text(self.lang.translate(str(dmd)))
                dmd_sent = dmd
            if full:
                # Background, title and informations : drawn once, then kept from one display
                # to the next (copying the whole screen each time made the return slower)
                cache_key = (name, title, subtitle, repr(show_version), tuple(info), tuple(self.screen.get_size()),
                             getattr(self.file_class, 'theme_dir', None), self.background)
                pristine = self.menu_backgrounds.get(cache_key)
                if pristine is None:
                    self.display_background()
                    self.menu_version(show_version)
                    if title:
                        self.menu_header(title, subtitle)
                    if 'ips' in info:
                        self.display_ips()
                    if 'rpi_version' in info:
                        self.display_rpi_version()
                    if 'version' in info:
                        self.display_version()
                    pristine = self.screen.copy()
                    # A few menus only : one screen is several MB
                    while len(self.menu_backgrounds) >= MENU_BACKGROUNDS:
                        self.menu_backgrounds.pop(next(iter(self.menu_backgrounds)))
                    self.menu_backgrounds[cache_key] = pristine
                else:
                    self.screen.blit(pristine, (0, 0))
                    self.pristine_background = None
                for index in range(1, nb_shown + 1):
                    draw(index)
                if with_details:
                    details_area = self.menu_details_area([rects[index] for index in range(1, nb_listed + 1)],
                                                          [rects[index] for index in range(nb_listed + 1, nb_shown + 1)])
                    details_shown = shown[selected - 1].get('details')
                    self.menu_details(details_area, details_shown, pristine)
                self.update_screen()
                full = False
            else:
                changed = [index for index in range(1, nb_shown + 1) if drawn.get(index) != look(index)]
                for index in changed:
                    rect = pygame.Rect(rects[index])
                    self.screen.blit(pristine, rect, rect)
                    draw(index)
                if changed:
                    self.update_screen(rect_array=[pygame.Rect(rects[index]) for index in changed])
                if details_area is not None and shown[selected - 1].get('details') != details_shown:
                    details_shown = shown[selected - 1].get('details')
                    self.update_screen(rect_array=[self.menu_details(details_area, details_shown, pristine)])

            key = self.rpi.listen_inputs(['arrows', 'fx', 'alpha', 'math'],
               ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON',
                'single-click', 'double-click', 'resize', 'VOLUME-UP', 'VOLUME-DOWN', 'enter', 'space'],
                 events=[(self.wait_event_time, 'EVENT', 'wait')])

            if key == 'resize':
                full = True
                continue
            if key == self.REVEAL_KEY:
                self.reveal_shortcuts()
                full = True
                continue
            clicked = self.is_clicked({index: pygame.Rect(rect) for index, rect in rects.items()}, key)
            if clicked:
                selected = clicked
                key = 'enter'

            for direction in ('up', 'down', 'left', 'right'):
                if key in keys[direction] and selected in rects:
                    selected = self.move_selection(rects, selected, direction)
            if key in keys['next']:
                selected = selected % nb_shown + 1
            elif key in keys['previous']:
                selected = (selected - 2) % nb_shown + 1

            if key in keys['validate'] and 1 <= selected <= nb_shown:
                button = shown[selected - 1]
            else:
                # Shortcuts : all the buttons, hidden ones too. 'escape' : every key back
                pressed = 'escape' if key in keys['back'] else key
                button = next((button for button in everything
                               if pressed in [cmenus.key_name(k) for k in cmenus.as_list(button.get('shortcut'))]), None)
            if button is None or button.get('unavailable'):
                continue
            # The selection kept is the one of a button of the list (not Back at the bottom)
            if remember and button in listed:
                self.selected_menu[name] = listed.index(button) + 1
            if button.get('confirm'):
                full = True
                if not self.wait_validation(self.lang.translate(str(button['confirm']))):
                    continue
            return button

    def menu_details_area(self, listed, footers):
        '''
        Place of the details of the selected button : between the list and the buttons at the
        bottom, nearly the whole width. None : no room
        '''
        margin = int(self.res_y_16 / 4)
        top = max(pygame.Rect(rect).bottom for rect in listed) + margin
        bottom = min([pygame.Rect(rect).top for rect in footers] or [self.res['y']]) - margin
        if bottom - top < 2 * self.res_y_16:
            return None
        return pygame.Rect(int(self.res['x'] / 8), top, int(self.res['x'] * 3 / 4), bottom - top)

    def menu_details(self, area, lines, pristine):
        '''
        Details of the selected button (lines : the options of a favorite...) drawn in their
        place over the background (nothing : the background only). Returns the place drawn
        '''
        if area is None:
            return pygame.Rect(0, 0, 0, 0)
        self.screen.blit(pristine, area, area)
        if not lines:
            return area
        margin = int(self.res_y_16 / 4)
        self.new_blit_rect2(area, self.menu_color(self.colorset['menu-buttons']), corners='All',
                            border_radius=self.get_radius(margin * 2))
        columns = 2 if len(lines) > 6 else 1
        rows = math.ceil(len(lines) / columns)
        step = min(int((area.height - 2 * margin) / rows), int(self.res['y'] / 22))
        font = self.font(self.defaultfontpath, max(10, int(step * 0.8)))
        width = int((area.width - 2 * margin) / columns)
        for index, line in enumerate(lines):
            column, row = divmod(index, rows)
            text = font.render(str(line), True, self.colorset['menu-text-white'])
            if text.get_width() > width - margin:
                text = pygame.transform.smoothscale(text, (width - margin, text.get_height()))
            self.screen.blit(text, (area.x + margin + column * width, area.y + margin + row * step))
        return area

    def styled_title(self, name, title, subtitle):
        '''
        Title and subtitle of a menu drawn by cmenustyle (section 7.1) : their band and text
        as the files say, the classic header if they say nothing
        '''
        title_look = self.menu_text_look(name, 'title')[1]
        subtitle_look = self.menu_text_look(name, 'subtitle')[1]
        if not title_look and not subtitle_look:
            if title:
                self.classic_header(title, subtitle)
            return
        painter = self.menu_painter()
        units = cmenustyle.Units(self.screen.get_size(), self.menus().data.get('resolution'))

        def place_of(settings, default):
            place = settings.get('place')
            if not isinstance(place, dict):
                return default
            return pygame.Rect(int(units.length(place.get('x', 0), 'x')), int(units.length(place.get('y', 0), 'y')),
                               int(units.length(place.get('width', '100%'), 'x')), int(units.length(place.get('height', '7%'), 'y')))

        def band(text, settings, rect):
            if settings.get('background') is not None:
                self.blit(painter.background(settings['background'], rect.size), rect.topleft)
            painter.text(self.screen, self.lang.translate(str(text)), rect, settings, units)

        rect = place_of(title_look, pygame.Rect(0, int(self.res['y'] / 30), self.res['x'], int(self.res['y'] / 15)))
        if title and title_look:
            band(title, cmenustyle.merge(self.TITLE_LOOK, title_look), rect)
        elif title:
            # Only the subtitle has a look of its own : the title of always
            self.classic_header(title)
        if subtitle:
            settings = cmenustyle.merge(self.SUBTITLE_LOOK, subtitle_look)
            band(subtitle, settings, place_of(settings, pygame.Rect(rect.x, rect.bottom, rect.width, int(self.res['y'] / 20))))

    def screen_skin(self, name):
        '''
        Colours of the theme (Colorset.cfg) given by the style of the menu of this name, for the
        screens drawn with them (games, options, players, wizard : section 7.6), and the font
        of their texts (None : the font of the theme)
        '''
        menus = self.menus()
        menu = menus.menu(name)
        if str(menu.get('style') or 'classic') == 'classic':
            # The classic style is the look of the theme itself
            return {}, None
        style = (menus.data.get('styles') or {}).get(str(menu.get('style') or 'classic')) or {}
        painter = self.menu_painter()
        skin = {}

        def color(block, key):
            value = block.get('color') if isinstance(block, dict) else block
            found = painter.color(value, None)
            if found is not None:
                skin[key] = tuple(found[:3])

        selected = style.get('selected') or {}
        disabled = style.get('disabled') or {}
        if 'color' in style:
            color(style['color'], 'menu-buttons')
        color(style.get('background') or {}, 'menu-buttons')
        color(selected.get('background') or {}, 'menu-selected')
        color(disabled.get('background') or {}, 'menu-warning')
        color(style.get('text') or {}, 'menu-text-black')
        color(selected.get('text') or {}, 'menu-text-white')
        border = cmenustyle.merge(style.get('border') or {}, selected.get('border') or {})
        color(border, 'menu-border')
        if 'width' in border:
            skin['border-size'] = int(border.get('width') or 0)
        color(menu.get('shortcuts') or {}, 'menu-shortcut')
        shape = style.get('shape')
        if shape == 'pill':
            skin['border-radius'] = skin['button-radius'] = 'max'
        elif shape == 'rectangle':
            skin['border-radius'] = skin['button-radius'] = 0
        elif style.get('radius') is not None:
            radius = float(style['radius'])
            # A part of the height of a button (the rows of these screens : 1/15 of the screen)
            pixels = int(radius * self.res['y'] / 15) if radius <= 1 else \
                int(cmenustyle.Units(self.screen.get_size(), menus.data.get('resolution')).length(radius, 'y'))
            skin['border-radius'] = skin['button-radius'] = pixels
        font = (style.get('text') or {}).get('font')
        return skin, (painter.font_path(font) if font else None)

    def run_with_look(self, name, method, *args, **kwargs):
        '''
        A screen drawn with the look of the menu of this name (see with_look) : its colours
        and font while it is shown, those of the theme again after
        '''
        colorset = self.colorset
        skin, font = self.screen_skin(name)
        saved = {key: colorset[key] for key in skin if key in colorset}
        added = [key for key in skin if key not in colorset]
        saved_font = getattr(self, 'defaultfontpath', None)
        previous = self.current_look
        colorset.update(skin)
        if font:
            self.defaultfontpath = font
            # Sizes of texts computed for the font of the theme
            self.scale_text.cache_clear()
        self.current_look = name
        try:
            return method(self, *args, **kwargs)
        finally:
            self.current_look = previous
            colorset.update(saved)
            for key in added:
                colorset.pop(key, None)
            if font:
                self.defaultfontpath = saved_font
                self.scale_text.cache_clear()

    def menu_painter(self):
        '''
        Drawer of the buttons of the styles (kept : it keeps the buttons drawn)
        '''
        if getattr(self, 'painter', None) is None:
            self.painter = cmenustyle.Painter(self)
        return self.painter

    def run_styled_menu(self, name, menu, items, everything, hook=None, initial=None, title=None, subtitle=None):
        '''
        A menu whose look is described by the files (styles, layouts, places, backgrounds) :
        same behaviour as run_menu (keys, shortcuts, confirmation, remembered button), drawn
        by cmenustyle. The buttons at the bottom (footer) stay the classic ones
        '''
        menus = self.menus()
        painter = self.menu_painter()
        resolution = menus.data.get('resolution')
        units = cmenustyle.Units(self.screen.get_size(), resolution)
        title = title or self.menu_text_look(name, 'title')[0]
        subtitle = subtitle or self.menu_text_look(name, 'subtitle')[0]
        # Shortcuts shown as on the classic buttons of the theme, unless the menu says
        shortcuts = cmenustyle.merge({'show': self.colorset.get('main-sub-menu-shortcuts') is not None, 'format': '{key}',
                                      'position': 'top_left' if menu.get('layout') == 'tiles' else 'left'},
                                     menu.get('shortcuts') or {})
        # As the theme wants : its entry of the colours is changed while they are shown
        if Screen.revealed and 'main-sub-menu-shortcuts' in Screen.hidden_shortcuts and                 'show' not in (menu.get('shortcuts') or {}):
            shortcuts['show'] = False
        theme_show = shortcuts.get('show')
        shortcuts['show'] = theme_show or Screen.revealed
        show_version = menu.get('show_version') or False
        info = [str(value) for value in cmenus.as_list(menu.get('info'))]
        remember = bool(menu.get('remember'))
        keys = {direction: set(menus.keys(direction)) for direction in
                ('up', 'down', 'left', 'right', 'next', 'previous', 'validate', 'back')}
        listed = [button for button in items if button.get('footer') not in self.FOOTERS]
        footers = [button for button in items if button.get('footer') in self.FOOTERS]
        shown = listed + footers
        nb_listed, nb_shown = len(listed), len(shown)
        styles = [self.button_style(menu, button) for button in listed]
        # Panels of the players online placed as buttons : drawn again every second
        widgets = {index for index, button in enumerate(listed, 1) if button.get('action') == 'online_players'}
        selected = self.selected_menu.get(name, 1) if remember else 1
        if initial is not None:
            selected = next((index for index, button in enumerate(shown, 1) if menus.button_id(button) == initial), selected)
        if not 1 <= selected <= nb_shown:
            selected = 1
        page_of = {}
        for index in range(1, nb_listed + 1):
            page_of[index] = cmenustyle.layout(menu, listed, self.screen.get_size(), resolution, selected=index)[1]
        full, pristine, page = True, None, None
        rects, drawn, looks = {}, {}, {}
        dmd_sent = None

        def state(index):
            if index == selected:
                return 'selected'
            return 'disabled' if listed[index - 1].get('unavailable') else 'normal'

        def draw(index):
            if index > nb_listed:
                button = shown[index - 1]
                rects[index] = drawn[index] = pygame.Rect(self.display_button(index == selected, self.button_text(button),
                                                                              self.FOOTERS[button['footer']]))
                looks[index] = index == selected
                return
            if index in widgets:
                # Panel of the players online : drawn each time (it changes), on its background
                rect = pygame.Rect(rects[index]).clip(self.screen.get_rect())
                self.screen.blit(pristine, rect, rect)
                drawn[index] = self.online_players_panel(rect, index == selected)
                looks[index] = state(index)
                return
            look = state(index)
            rect = pygame.Rect(rects[index])
            target, composite = composed(index, look)
            self.screen.blit(composite, target)
            drawn[index] = target.union(rect)
            looks[index] = look

        def composed(index, look):
            # The button drawn on its piece of background, once : an opaque image in the
            # format of the screen. Blending a button with transparency at each move took 80 to
            # 130 ms on a Pi 3
            rect = pygame.Rect(rects[index])
            target = painter.placed(rect, styles[index - 1], look)[1].clip(self.screen.get_rect())
            composite_key = (id(pristine), index, look, tuple(target), Screen.revealed)
            composite = self.menu_composites.get(composite_key)
            if composite is None:
                composite = paint(index, look, rect, target)
                if len(self.menu_composites) >= 256:
                    self.menu_composites.pop(next(iter(self.menu_composites)))
                self.menu_composites[composite_key] = composite
            return target, composite

        def paint(index, look, rect, target):
            # The button of this index in this state on the piece target of the background
            button = listed[index - 1]
            patch = pristine.subsurface(target).copy()
            painter.draw_button(patch, rect.move(-target.x, -target.y), styles[index - 1],
                                '' if button.get('text', True) is None or ('text' not in button and button.get('logo')) else
                                self.styled_text(button),
                                self.button_icon(button), look, units,
                                shortcut=self.button_label(button, menu) if shortcuts.get('show') else None, shortcuts=shortcuts)
            return patch

        while True:
            if hook is not None and hook():
                full = True
            dmd = shown[selected - 1].get('dmd') if 1 <= selected <= nb_shown else None
            if dmd and dmd != dmd_sent:
                self.dmd.send_text(self.lang.translate(str(dmd)))
                dmd_sent = dmd
            new_page = page_of.get(selected, page)
            if new_page != page:
                full = True
            if full:
                page = new_page if new_page is not None else 0
                layout, page, pages = cmenustyle.layout(menu, listed, self.screen.get_size(), resolution,
                                                        selected=selected if selected <= nb_listed else
                                                        next((i for i, p in page_of.items() if p == page), 1))
                rects = {index: pygame.Rect(rect) for index, rect in layout.items()}
                cache_key = (name, 'styled', title, subtitle, repr(menu.get('background')), repr(self.menu_text_look(name, 'title')),
                             repr(self.menu_text_look(name, 'subtitle')), repr(show_version),
                             tuple(info), tuple(self.screen.get_size()), getattr(self.file_class, 'theme_dir', None), self.background)
                pristine = self.menu_backgrounds.get(cache_key)
                if pristine is None:
                    if menu.get('background') is not None:
                        block = menu.get('background')
                        block = cmenustyle.merge({'fit': 'cover'}, block) if isinstance(block, dict) else block
                        self.screen.fill((0, 0, 0))
                        self.screen.blit(painter.background(block, self.screen.get_size()), (0, 0))
                    else:
                        self.display_background()
                    self.menu_version(show_version)
                    if title or subtitle:
                        self.styled_title(name, title, subtitle)
                    if 'ips' in info:
                        self.display_ips()
                    if 'rpi_version' in info:
                        self.display_rpi_version()
                    if 'version' in info:
                        self.display_version()
                    pristine = self.screen.copy()
                    while len(self.menu_backgrounds) >= MENU_BACKGROUNDS:
                        self.menu_backgrounds.pop(next(iter(self.menu_backgrounds)))
                    self.menu_backgrounds[cache_key] = pristine
                else:
                    self.screen.blit(pristine, (0, 0))
                self.pristine_background = None
                drawn, looks = {}, {}
                # The selected button last : enlarged (scale), it stays over its neighbours
                for index in sorted(list(rects) + list(range(nb_listed + 1, nb_shown + 1)), key=lambda i: i == selected):
                    draw(index)
                if pages > 1:
                    # Arrows of the pages (pages before, after), and the page shown
                    area = pygame.Rect(int(self.res['x'] * 0.9), int(self.res['y'] * 0.9), int(self.res['x'] * 0.08), int(self.res_y_16))
                    self.blit_text2(f"{page + 1} / {pages}", area, self.colorset['menu-text-white'])
                    side = int(area.height * 0.5)
                    middle = area.centery
                    for shown_arrow, tip_x, base_x in ((page > 0, area.x - side, area.x),
                                                       (page < pages - 1, area.right + side, area.right)):
                        if shown_arrow:
                            pygame.draw.polygon(self.screen, self.colorset['menu-text-white'],
                                                [(tip_x, middle), (base_x, middle - side // 2), (base_x, middle + side // 2)])
                self.update_screen()
                full = False
                if self.intro and not intro_is_playing():
                    self.intro = False
                if self.intro:
                    # The intro video still plays (the menu is ready first) : the other looks
                    # of the buttons drawn now, unseen (the first move took up to 240 ms)
                    for index in rects:
                        for look in ('selected', 'normal'):
                            if not listed[index - 1].get('unavailable') and index not in widgets:
                                composed(index, look)
            else:
                changed = [index for index in drawn if looks.get(index) != (state(index) if index <= nb_listed else index == selected)]
                if changed:
                    # Places of the changed buttons back to the background, then the buttons
                    # touching them drawn again too (an enlarged button covers its
                    # neighbours a little), the selected one last
                    olds = [pygame.Rect(drawn[index]) for index in changed]
                    for old in olds:
                        self.screen.blit(pristine, old, old)
                    again = {index for index in drawn if any(pygame.Rect(drawn[index]).colliderect(old) for old in olds)}
                    for index in sorted(again | set(changed), key=lambda i: i == selected):
                        draw(index)
                    self.update_screen(rect_array=olds + [pygame.Rect(drawn[index]) for index in again | set(changed)])

            key = self.rpi.listen_inputs(['arrows', 'fx', 'alpha', 'math'],
               ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON',
                'single-click', 'double-click', 'resize', 'VOLUME-UP', 'VOLUME-DOWN', 'enter', 'space'],
                 events=[(self.wait_event_time, 'EVENT', 'wait')], timeout=1000 if widgets else 0)

            if key in (None, False) and widgets:
                # A second without a key : the panels of the players online drawn again
                again = [index for index in widgets if index in rects]
                for index in again:
                    draw(index)
                if again:
                    self.update_screen(rect_array=[pygame.Rect(drawn[index]) for index in again])
                continue
            if key == 'resize':
                full = True
                continue
            if key == self.REVEAL_KEY:
                self.reveal_shortcuts()
                shortcuts['show'] = theme_show or Screen.revealed
                full = True
                continue
            clicked = self.is_clicked({index: pygame.Rect(rect) for index, rect in drawn.items()}, key)
            if clicked:
                selected = clicked
                key = 'enter'

            for direction in ('up', 'down', 'left', 'right'):
                if key in keys[direction] and selected in drawn:
                    moved = self.move_selection({index: tuple(rect) for index, rect in drawn.items()}, selected, direction)
                    # Several pages : at the edge of one, the next one (or the one before)
                    if selected <= nb_listed and page_of:
                        last_page = max(page_of.values())
                        forward = direction in ('down', 'right')
                        on_page = sorted(index for index, number in page_of.items() if number == page)
                        at_edge = (forward and selected == on_page[-1]) or (not forward and selected == on_page[0])
                        if at_edge and ((forward and page < last_page) or (not forward and page > 0)):
                            moved = on_page[-1] + 1 if forward else on_page[0] - 1
                    selected = moved
            if key in keys['next']:
                selected = selected % nb_shown + 1
            elif key in keys['previous']:
                selected = (selected - 2) % nb_shown + 1

            if key in keys['validate'] and 1 <= selected <= nb_shown:
                button = shown[selected - 1]
            else:
                pressed = 'escape' if key in keys['back'] else key
                button = next((button for button in everything
                               if pressed in [cmenus.key_name(k) for k in cmenus.as_list(button.get('shortcut'))]), None)
            if button is None:
                continue
            if button.get('unavailable'):
                continue
            if button.get('action') == 'online_players' and not self.online_known_session():
                # No account : S'identifier (a QR code to create one first), then the menu again
                self.online_session()
                full = True
                continue
            if button in listed and listed.index(button) + 1 in drawn and listed.index(button) + 1 not in widgets:
                # Pressed : seen for a moment
                index = listed.index(button) + 1
                old = pygame.Rect(drawn[index])
                self.screen.blit(pristine, old, old)
                look = 'pressed'
                target = painter.placed(rects[index], styles[index - 1], look)[1].clip(self.screen.get_rect())
                self.screen.blit(paint(index, look, pygame.Rect(rects[index]), target), target)
                self.update_screen(rect_array=[old.union(target)])
                pygame.time.wait(80)
                looks[index] = 'pressed'
            if remember and button in listed:
                self.selected_menu[name] = listed.index(button) + 1
            if button.get('confirm'):
                full = True
                if not self.wait_validation(self.lang.translate(str(button['confirm']))):
                    continue
            return button

    def chat_menu(self):
        '''
        Chat between the players online (include/cchat.py)
        '''
        from include.cchat import show
        return show(self)

    def online_account_screen(self, url):
        '''
        Account of the online games required : a QR code to create one with a phone, then log
        in. True : log in, False : back
        '''
        import qrcode
        picture = qrcode.make(url)
        picture = (picture.get_image() if hasattr(picture, 'get_image') else picture).convert('RGB')
        side = int(self.res['y'] * 0.45)
        code = pygame.transform.scale(pygame.image.fromstring(picture.tobytes(), picture.size, 'RGB'), (side, side))
        selected = 2
        while True:
            self.display_background()
            self.menu_header(self.lang.translate('online-account'), self.lang.translate('online-account-scan'))
            pos_y = int(self.res['y'] / 5)
            self.blit(code, (int((self.res['x'] - side) / 2), pos_y))
            line = int(self.res['y'] / 20)
            self.blit_text(url, 0, pos_y + side + self.margin * 2, self.res['x'], line, self.colorset['menu-text-white'])
            click_zones = {'escape': self.display_button(selected == 1, 'back', special='escape'),
                           'login': self.display_button(selected == 2, 'online-login', special='return')}
            self.update_screen()
            key = self.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'enter', 'space', 'single-click'])
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked
            if key in LEFT_KEYS:
                selected = 1
            elif key in RIGHT_KEYS:
                selected = 2
            elif key == 'login' or (key in ENTER_KEYS and selected == 2):
                return True
            elif key in ESCAPE_KEYS or key == 'escape' or key in ENTER_KEYS:
                return False

    def online_servers(self):
        '''
        Favorite servers (Divers > Favoris > Serveurs) : the first one is the server of the
        online games
        '''
        servers = str(self.config.get_value('Favorites', 'servers', False) or '')
        return [server.strip() for server in servers.split(',') if server.strip() and server.strip() not in ('False', 'None')]

    def online_server_choice(self):
        '''
        Another favorite server for the online games : put first of the favorites (kept for the
        next times). True : changed
        '''
        servers = self.online_servers()
        if len(servers) < 2:
            self.message([self.lang.translate('online-one-server')], 3000)
            return False
        items = [{'id': f'server{index}', 'action': 'server', 'text': server, 'shortcut': f'F{index + 1}' if index < 12 else None}
                 for index, server in enumerate(servers)]
        back = {'id': 'back', 'action': 'back', 'text': 'back', 'footer': 'left', 'shortcut': 'escape'}
        choice = self.run_menu('online_servers', items + [back], items + [back],
                               title=self.lang.translate('online-server-choice')).get('id')
        if choice in (None, 'back') or choice == 'server0':
            return False
        chosen = servers.pop(int(choice[6:]))
        self.config.config.setdefault('Favorites', {})['servers'] = ','.join([chosen] + servers)
        self.config.write_file()
        return True

    def online_session(self):
        '''
        Account of the borne on the server of the online games : the one of this session, the
        one kept on the borne, else asked (QR code to create one). None : given up
        '''
        from include import caccount
        session = getattr(self, '_lobby_account_session', None)
        if not session or session.get('server') != caccount.SERVER or session.get('expires', 0) <= time.time():
            session = caccount.load_session()
        if not session:
            client = getattr(self, '_lobby_chat_client', None)
            if client is not None:
                client.stop()
                self._lobby_chat_client = None
            self._lobby_ready_online = False
            self._lobby_auth_open = True
            try:
                session = caccount.login_dialog(self)
            finally:
                self._lobby_auth_open = False
        self._lobby_account_session = session
        return session

    def network_lobby(self):
        '''
        Online games screen (see online_lobby). Left : the borne is not ready any more (not seen
        online by the others until it comes back and says it is)
        '''
        from include.cchat import set_ready
        try:
            return self.online_lobby()
        finally:
            set_ready(self, False)

    def online_lobby(self):
        '''
        Online games : the account of the borne first (asked once, kept), then the rooms waiting
        for a player and the games being played, the chat. Returns netjoin (self.lobby_game :
        the room chosen), netcreate, or None. The keys and texts of its buttons : menu
        online_lobby of the files of menus
        '''
        import socket
        from include import caccount
        from include.cchat import draw_line, draw_button, shortcuts, toggle_ready
        from include.crooms import active_rooms, merge_rooms, joinable, label, color

        translate = self.lang.translate
        buttons = shortcuts(self, 'online_lobby')
        order = [name for name in ('ready', 'chat', 'create', 'server', 'account', 'back') if name in buttons]
        keys = {buttons[name][0]: name for name in buttons if buttons[name][0]}
        self.lobby_game = None
        port = 25006
        colors = self.colorset
        w, h = self.res['x'], self.res['y']
        radius = int(h * .012)

        while True:
            # Server : the first of the favorites ; the account of the borne on it
            caccount.set_server((self.online_servers() or [''])[0])
            host = caccount.SERVER
            session = self.online_session()
            if not session:
                return None
            # Line of the list chosen (None : the buttons on the right), button chosen
            line = None
            selected = 0
            # status : key of the translations
            state = {'status': 'online-connecting', 'rooms': [], 'busy': False, 'last': 0, 'host': host}

            def refresh(state=state):
                try:
                    with socket.create_connection((state['host'], port), timeout=3) as sock:
                        sock.settimeout(3)
                        sock.sendall(b'{"REQUEST":"LIST"}')
                        data = b''
                        while b'|' not in data:
                            part = sock.recv(4096)
                            if not part:
                                break
                            data += part
                            if len(data) > 262144:
                                raise ValueError('Reponse trop volumineuse')
                        answer = json.loads(data.split(b'|', 1)[0].decode('utf-8'))
                    if isinstance(answer, list):
                        waiting = [room for room in answer if isinstance(room, dict)]
                    elif isinstance(answer, dict) and answer.get('RESPONSE') == 'EMPTY':
                        waiting = []
                    else:
                        raise ValueError('Reponse inconnue')
                    try:
                        playing = active_rooms(state['host'])
                        state['status'] = 'online-connected'
                    except Exception:
                        playing = []
                        state['status'] = 'online-connected-no-live'
                    state['rooms'] = merge_rooms(waiting, playing, state['host'], state['rooms'])
                except Exception as error:
                    state['status'] = 'online-offline'
                    state['rooms'] = []
                    self.logs.warning(f"Online games : rooms of {state['host']} unavailable ({error})")
                finally:
                    state['busy'] = False

            again = False
            while not again:
                now = time.monotonic()
                if not state['busy'] and (state['last'] == 0 or now - state['last'] >= 3):
                    state['busy'] = True
                    state['last'] = now
                    threading.Thread(target=refresh, daemon=True).start()
                ready = bool(getattr(self, '_lobby_ready_online', False))
                rooms = list(state['rooms'])[:12]
                if line is not None and line >= len(rooms):
                    line = len(rooms) - 1 if rooms else None

                # Background of the theme, title, list of the rooms on the left, buttons on the right
                self.display_background()
                self.blit_text2('online-title', pygame.Rect(int(w*.045), int(h*.04), int(w*.9), int(h*.1)),
                                colors['menu-text-white'], align='Left')
                panel = pygame.Rect(int(w*.04), int(h*.19), int(w*.72), int(h*.70))
                self.new_blit_rect2(panel, colors['menu-header'], corners='All', border_radius=radius, alpha=255)
                # Server, account and state on one line
                user = session.get('user') or {}
                draw_line(self, translate('online-server').format(server=host), pygame.Rect(int(w*.06), int(h*.21), int(w*.27), int(h*.045)),
                          colors['menu-text'])
                draw_line(self, translate('online-account-name').format(name='{:03d} · {}'.format(user.get('id', 0), user.get('username', '?'))),
                          pygame.Rect(int(w*.34), int(h*.21), int(w*.24), int(h*.045)), colors['menu-text'])
                status_color = colors['menu-ok'] if state['status'].startswith('online-connected') \
                    else colors['menu-ko'] if state['status'] == 'online-offline' else colors['menu-inactive']
                self.new_blit_rect2(pygame.Rect(int(w*.59), int(h*.216), int(w*.015), int(h*.033)), status_color,
                                    corners='All', border_radius=radius, alpha=255)
                draw_line(self, translate(state['status']), pygame.Rect(int(w*.612), int(h*.21), int(w*.14), int(h*.045)),
                          colors['menu-text'])
                zones = {}
                for index in range(12):
                    zone = pygame.Rect(int(w*.059), int(h*(.275 + index * .05)), int(w*.69), int(h*.044))
                    if index >= len(rooms):
                        self.new_blit_rect2(zone, colors['menu-inactive'], corners='All', border_radius=radius, alpha=255)
                        draw_line(self, '{:02d}   ---'.format(index + 1), zone.inflate(-18, -8), colors['menu-text-black'])
                        continue
                    zones['room|{}'.format(index)] = zone
                    self.new_blit_rect2(zone, colors[color(rooms[index], line == index)], corners='All',
                                        border_radius=radius, alpha=255)
                    draw_line(self, label(rooms[index], index, translate), zone.inflate(-18, -8), colors['menu-text-black'])
                if state['status'] == 'online-connected' and not rooms:
                    draw_line(self, translate('online-no-room'), pygame.Rect(int(w*.07), int(h*.28), int(w*.66), int(h*.035)),
                              colors['menu-text'])

                for index, name in enumerate(order):
                    rect = pygame.Rect(int(w*.79), int(h*(.19 + index * .118)), int(w*.18), int(h*.10))
                    zones[name] = rect
                    if name == 'ready':
                        # A switch : green when the borne is seen online by the others, red otherwise
                        background = colors['menu-ok'] if ready else colors['menu-ko']
                        text = '{} : {}'.format(translate(buttons[name][1]), translate('yes' if ready else 'no'))
                    else:
                        background = colors['menu-buttons']
                        text = None
                    chosen = line is None and selected == index
                    if chosen and name != 'ready':
                        background = colors['menu-selected']
                    draw_button(self, rect, buttons[name], 'online_lobby', background, text)
                    if chosen and name == 'ready':
                        # The switch keeps its colour : chosen, a frame around it
                        self.blit_border(rect, colors['menu-selected'], max(3, int(h * .005)), corners='All',
                                         border_radius=int(rect.height * .15), alpha=255)
                draw_line(self, translate('online-legend'), pygame.Rect(int(w*.045), int(h*.91), int(w*.9), int(h*.045)),
                          colors['menu-text-white'])
                self.update_screen()

                key = self.rpi.listen_inputs(['arrows', 'fx', 'alpha'], ['enter', 'escape', 'space', 'single-click'],
                                             timeout=200)
                clicked = self.is_clicked(zones, key)
                if clicked:
                    key = clicked
                elif key in keys:
                    key = keys[key]
                if key == self.REVEAL_KEY:
                    # As in the menus : the shortcuts shown, even when the theme hides them
                    self.reveal_shortcuts()
                    continue
                if key in ESCAPE_KEYS or key == 'back':
                    return None
                if key in ENTER_KEYS:
                    key = 'room|{}'.format(line) if line is not None else order[selected]
                if key == 'back':
                    # Retour chosen, then validated
                    return None
                if key == 'ready':
                    toggle_ready(self)
                elif key == 'chat':
                    self.chat_menu()
                    # Logged out in the chat : an account asked again
                    again = getattr(self, '_lobby_account_session', None) is None
                elif key == 'create':
                    return 'netcreate'
                elif key == 'server':
                    # Another server : its rooms, and the account of the borne on it
                    again = self.online_server_choice()
                    if again:
                        # The chat of the server before stopped
                        client = getattr(self, '_lobby_chat_client', None)
                        if client is not None:
                            client.stop()
                            self._lobby_chat_client = None
                        self._lobby_ready_online = False
                elif key == 'account':
                    # Another account : the one of the borne forgotten, another one asked
                    caccount.logout(self)
                    again = True
                elif isinstance(key, str) and key.startswith('room|'):
                    # A click on a room waiting for a player joins it
                    index = int(key.split('|', 1)[1])
                    if 0 <= index < len(rooms) and joinable(rooms[index]):
                        self.lobby_game = dict(rooms[index])
                        return 'netjoin'
                elif key in LEFT_KEYS and rooms:
                    line = 0 if line is None else line
                elif key in RIGHT_KEYS:
                    line = None
                elif key in UP_KEYS + DOWN_KEYS:
                    move = -1 if key in UP_KEYS else 1
                    if line is not None:
                        line = (line + move) % len(rooms)
                    else:
                        selected = (selected + move) % len(order)

    def online_qrcode(self, url, side):
        '''
        QR code of an address, at this size (made once : about 200 ms on a Pi 3)
        '''
        key = (url, side)
        codes = getattr(self, '_online_qrcodes', {})
        if key not in codes:
            import qrcode
            picture = qrcode.make(url)
            picture = (picture.get_image() if hasattr(picture, 'get_image') else picture).convert('RGB')
            codes[key] = pygame.transform.scale(pygame.image.fromstring(picture.tobytes(), picture.size, 'RGB'), (side, side))
            self._online_qrcodes = codes
        return codes[key]

    def online_known_session(self):
        '''
        Account of the borne on the server of the online games, without asking it : the one of
        this session, or the one kept on the borne. None : none
        '''
        from include import caccount
        caccount.set_server((self.online_servers() or [''])[0])
        session = getattr(self, '_lobby_account_session', None)
        if not session or session.get('server') != caccount.SERVER or session.get('expires', 0) <= time.time():
            session = caccount.load_session()
            self._lobby_account_session = session
        return session

    def online_players_panel(self, rect, chosen=False):
        '''
        Panel of the players online, placed as a button in a menu (action online_players of
        the files of menus). Without an account : a QR code to create one, and S'identifier.
        Drawn again every second by the menu
        '''
        from include import caccount
        from include.cchat import ensure_session, pump_presence, draw_line
        translate = self.lang.translate
        colors = self.colorset
        rect = pygame.Rect(rect)
        radius = max(4, int(rect.height * .06))
        margin = max(6, int(rect.height * .05))
        session = self.online_known_session()
        unread = getattr(self, '_lobby_chat_unread', 0) if session else 0
        # Messages not read : the colour of the theme for a success ; chosen (arrows) : the colour
        # of a button chosen, as the others (a frame alone was hardly seen on a light panel)
        background = colors['menu-ok'] if unread else colors['menu-selected'] if chosen else colors['menu-header']
        self.new_blit_rect2(rect, background, corners='All', border_radius=radius, alpha=255)
        # Text of a panel : menu-text ; of a button (and of the panel when coloured) : menu-text-black
        text_color = colors['menu-text-black'] if unread else colors['menu-text']
        line = max(12, int(rect.height * .13))
        if not session:
            # No account : a QR code to create one with a phone, and the button to log in
            side = min(rect.height - 2 * margin, int(rect.width * .4))
            self.blit(self.online_qrcode(caccount.BASE + '/joueurs', side), (rect.x + margin, rect.y + margin))
            left = rect.x + 2 * margin + side
            width = rect.right - margin - left
            draw_line(self, translate('online-account-required'), pygame.Rect(left, rect.y + margin, width, line), text_color)
            draw_line(self, translate('online-account-create'), pygame.Rect(left, rect.y + margin + line, width, line),
                      text_color, size=line * .55)
            button = pygame.Rect(left, rect.bottom - margin - int(line * 1.6), width, int(line * 1.6))
            self.new_blit_rect2(button, colors['menu-buttons'], corners='All', border_radius=radius, alpha=255)
            draw_line(self, translate('online-identify'), button.inflate(-margin, -int(line * .6)), colors['menu-text-black'],
                      align='Center')
        else:
            client = ensure_session(self)
            pump_presence(self)
            if client is None:
                status = getattr(self, '_lobby_chat_status', 'online-chat-unavailable')
                ident, players = None, []
            else:
                status, ident, players, _ = client.snapshot()
            players = [player for player in players if isinstance(player, dict)]
            title = translate('online-new-messages').format(count=unread) if unread \
                else translate('online-players-online').format(count=len(players))
            draw_line(self, title, pygame.Rect(rect.x + margin, rect.y + margin, rect.width - 2 * margin, line), text_color)
            top = rect.y + margin + int(line * 1.2)
            rows = max(1, int((rect.bottom - margin - line - top) / line))
            if status != 'online-connected':
                draw_line(self, translate(status), pygame.Rect(rect.x + margin, top, rect.width - 2 * margin, line),
                          colors['menu-inactive'])
            elif not players:
                draw_line(self, translate('online-no-player'), pygame.Rect(rect.x + margin, top, rect.width - 2 * margin, line),
                          colors['menu-inactive'])
            for row, player in enumerate(players[:rows]):
                name = str(player.get('name', '?'))
                if player.get('id') == ident:
                    name += ' ' + translate('online-you')
                if row == rows - 1 and len(players) > rows:
                    name = '+ {}'.format(len(players) - rows + 1)
                draw_line(self, name, pygame.Rect(rect.x + margin, top + row * line, rect.width - 2 * margin, line),
                          text_color, size=line * .7)
            footer = translate('online-unread-open') if unread else translate('online-open-lobby')
            draw_line(self, footer, pygame.Rect(rect.x + margin, rect.bottom - margin - line, rect.width - 2 * margin, line),
                      text_color, size=line * .6)
        if chosen and unread:
            # Coloured by its messages : chosen, a frame of the colour of a button chosen
            self.blit_border(rect, colors['menu-selected'], max(4, int(rect.height * .02)), corners='All',
                             border_radius=radius, alpha=255)
        return rect

    def main_menu(self):
        '''
        Choose Game Type : Local - Network. The menu is described by the files of menus
        (menus/defaults.yaml...). The shortcuts work even for the buttons hidden in
        exhibition mode (F4 : the settings, to leave this mode)
        '''
        #self.dmd.send_text(self.lang.translate('Welcome') + "!")
        self.dmd.send_text('Raspydarts')
        menus = self.menus()
        first = [True]

        def banned():
            if first[0]:
                # Measure of the start : the main menu is ready
                self.logs.debug("Main menu shown")
                first[0] = False
            shown = False
            if self.rpi.banned_gpio is not None:
                self.message([f'Button {self.rpi.banned_gpio} (GPIO) is banned.'], color=(189, 108, 109), size='big')
                shown = True
            if self.rpi.gpio is not None and self.rpi.gpio.banned_button is not None:
                self.message([f'Button {self.rpi.gpio.banned_button} (MCP) is banned.'], color=(189, 108, 109), size='big')
                shown = True
            return shown

        button = self.run_menu('main', self.main_menu_items(), [self.favorite_button(button) for button in menus.buttons('main')],
                               hook=banned)
        # A button going straight to a game or to the games of a category : a local game,
        # whose players are chosen first
        self.menu_target = menus.target(button.get('action'))
        if self.menu_target is not None:
            return 'local'
        return menus.result(button)

    def edit_screens(self):
        '''
        Paramètres > Modifier les écrans : the buttons of the main screens placed, resized,
        added or deleted on the borne (include/cmenueditor.py)
        '''
        from include import cmenueditor    # pylint: disable=import-outside-toplevel
        cmenueditor.screens_menu(self, {'plus': PLUS_KEYS, 'minus': MINUS_KEYS, 'enter': ENTER_KEYS,
                                        'escape': ESCAPE_KEYS})

    # Columns of elements on a line of the screen of the USB pads (beyond : a second line)
    USB_PADS_COLUMNS = 11

    def usb_pads_menu(self):
        '''
        Paramètres > Pavés USB : the pad chosen (several can be plugged), its numbers of keys
        and knobs, written in it (« Programmer le pavé »), then the button of each key in the
        menus and in a game. A key pressed on a pad is lit on the screen (include/cusbpads.py)
        '''
        from include import cusbpads    # pylint: disable=import-outside-toplevel
        pads = self.rpi.usb_pads
        # Changed here, kept by « Enregistrer » (or by programming a pad)
        settings = json.loads(json.dumps(pads.settings))
        pads.set_capture(True)
        try:
            self.usb_pads_loop(cusbpads, pads, settings)
        finally:
            pads.set_capture(False)

    def usb_pads_loop(self, cusbpads, pads, settings):
        '''
        Screen of the USB pads, until back (see usb_pads_menu)
        '''
        port = None
        row, column = 0, 0
        lit = {}
        status = None
        while True:
            plugged = pads.plugged()
            if port not in plugged:
                port = plugged[0] if plugged else None
            if port is not None and port not in settings:
                settings[port] = json.loads(json.dumps(pads.settings_of(port)))
            pad = settings.get(port)
            names = cusbpads.elements(pad['keys'], pad['knobs']) if pad else []
            # Lines : 0 the pad, 1 menus, 2 game, 3 back and save
            lengths = [4, len(names), len(names), 2] if pad else [0, 0, 0, 1]
            if lengths[row] == 0:
                row = 3
            column = min(column, lengths[row] - 1)
            now = time.monotonic()
            lit = {name: moment for name, moment in lit.items() if now - moment < 0.25}

            click_zones = self.usb_pads_draw(cusbpads, plugged, port, pad, names, (row, column), lit, status)
            self.update_screen()

            key = self.rpi.listen_inputs(['arrows'], ['escape', 'enter', 'space', 'single-click',
                                                      'PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON'],
                                         timeout=250 if lit else 1000)
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked
            if key is False or key is None:
                continue
            if isinstance(key, str) and key.startswith('USBPAD:'):
                _usbpad, pressed_port, element = key.split(':')
                if element == 'unknown':
                    status = ('usb-pads-not-programmed', self.colorset['menu-ko'])
                    port = pressed_port
                    continue
                if pressed_port != port:
                    port = pressed_port
                    continue
                status = None
                lit[element] = time.monotonic()
                continue
            if isinstance(key, str) and key.startswith('cell:'):
                row, column = (int(number) for number in key.split(':')[1:])
                key = 'enter'
            elif key == 'save':
                row, column, key = 3, 1, 'enter'

            if key == 'escape' or key in ESCAPE_KEYS:
                return
            if key in UP_KEYS:
                row = max(0, row - 1)
                while row > 0 and lengths[row] == 0:
                    row -= 1
            elif key in DOWN_KEYS:
                row = min(3, row + 1)
                while row < 3 and lengths[row] == 0:
                    row += 1
            elif key in LEFT_KEYS + RIGHT_KEYS:
                # Reading order, from a line to the next one (a knob set on right and left goes
                # through the whole screen)
                cells = [(line, place) for line in range(4) for place in range(lengths[line])]
                position = cells.index((row, column)) if (row, column) in cells else 0
                row, column = cells[(position + (1 if key in RIGHT_KEYS else -1)) % len(cells)]
            elif key in ENTER_KEYS + PLUS_KEYS + MINUS_KEYS + ['space']:
                if row == 3:
                    if column == 0:
                        return
                    pads.save(settings)
                    self.message([self.lang.translate('usb-pads-saved')], 1000, self.colorset['menu-ok'], 'middle', 'big')
                    return
                if row == 0 and column == 3:
                    status = self.usb_pads_program(pads, settings, port)
                    continue
                # The values of the cell : its list (as the pins of the MCP), + and - go one by one
                if row == 0 and column == 0:
                    values = [[number, f"{self.lang.translate('usb-pads-pad')} {number + 1} (USB {name})"]
                              for number, name in enumerate(plugged)]
                    current = plugged.index(port)
                elif row == 0:
                    name = 'keys' if column == 1 else 'knobs'
                    most = cusbpads.MAX_KEYS if column == 1 else cusbpads.MAX_KNOBS
                    other = pad['knobs'] if column == 1 else pad['keys']
                    # At least one element on the pad
                    values = [[number, str(number)] for number in range(0 if other else 1, most + 1)]
                    current = pad[name]
                else:
                    context = 'menus' if row == 1 else 'game'
                    values = [[action[0], self.lang.translate(action[1])] for action in cusbpads.actions(context)]
                    current = pad[context].get(names[column], '')
                if key in PLUS_KEYS + MINUS_KEYS:
                    index = next((number for number, value in enumerate(values) if value[0] == current), 0)
                    chosen = values[(index + (-1 if key in MINUS_KEYS else 1)) % len(values)][0]
                else:
                    chosen = self.usb_pads_choose(values, current)
                    if chosen is None:
                        continue
                if row == 0 and column == 0:
                    port = plugged[chosen]
                elif row == 0:
                    if chosen != pad[name]:
                        self.usb_pads_count(cusbpads, pad, name, chosen)
                        status = ('usb-pads-to-program', self.colorset['menu-warning'])
                else:
                    pad[context][names[column]] = chosen

    def usb_pads_choose(self, values, current):
        '''
        List of the values of a cell of the screen of the USB pads, in the middle of the
        screen as everywhere. Returns the value chosen, None if none
        '''
        chosen = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, values, navigate=current)
        return None if chosen == 'escape' else chosen

    @staticmethod
    def usb_pads_count(cusbpads, pad, name, value):
        '''
        Number of keys or knobs of a pad changed : the buttons of its elements kept, the
        defaults for the new ones
        '''
        pad[name] = value
        defaults = cusbpads.default_settings(pad['keys'], pad['knobs'])
        for context in ('menus', 'game'):
            pad[context] = {element: pad[context].get(element, defaults[context][element])
                            for element in cusbpads.elements(pad['keys'], pad['knobs'])}

    def usb_pads_program(self, pads, settings, port):
        '''
        « Programmer le pavé » : its codes written in it, then its settings kept (they go
        together). Returns the line of state shown under the line of the pad
        '''
        pad = settings[port]
        error = pads.program(port, pad['keys'], pad['knobs'])
        if error is None:
            pads.save(settings)
            return ('usb-pads-programmed', self.colorset['menu-ok'])
        if 'Access denied' in error or 'Errno 13' in error:
            return ('usb-pads-program-denied', self.colorset['menu-ko'])
        return ('usb-pads-program-error', self.colorset['menu-ko'])

    def usb_pads_draw(self, cusbpads, plugged, port, pad, names, selected, lit, status):
        '''
        Screen of the USB pads drawn : the line of the pad, then the elements in columns with
        the button of each in the menus and in a game. Returns the zones to click
        '''
        self.display_background()
        self.menu_header(self.lang.translate('usb-pads'), self.lang.translate('usb-pads-sub'))
        click_zones = {}
        unit_x, unit_y = self.res_x_16, self.res_y_16
        gap = max(2, int(unit_x / 10))
        if pad is None:
            # As the messages of error : red on the band of the messages (white)
            band = pygame.Rect(0, 6 * unit_y, self.res['x'], unit_y)
            self.new_blit_rect2(band, self.colorset['message-bg'])
            self.blit_text(self.lang.translate('usb-pads-none'), band.x, band.y, band.width, band.height, self.colorset['menu-ko'])
            click_zones['escape'] = self.display_button(selected == (3, 0), 'back', special='escape')
            return click_zones

        def cell(rect, text, color, text_color, zone, value=None):
            self.new_blit_rect2(pygame.Rect(rect), color, corners='All', border_radius=int(rect[3] / 4))
            if value is None:
                self.blit_text(text, rect[0], rect[1], rect[2], rect[3], text_color)
            else:
                # A setting : in two parts, its value first, as in the pages of settings
                part = rect[2] * 0.25
                self.new_blit_rect2(pygame.Rect(rect[0], rect[1], part, rect[3]), self.colorset['menu-alternate'],
                                    corners='All', border_radius=int(rect[3] / 4))
                self.blit_text(value, rect[0], rect[1], part, rect[3], text_color)
                self.blit_text(text, rect[0] + part, rect[1], rect[2] - part, rect[3], text_color)
            if zone:
                click_zones[zone] = tuple(int(value) for value in rect)

        def colors(is_selected):
            if is_selected:
                return self.colorset['menu-selected'], self.colorset['menu-text-white']
            return self.colorset['menu-buttons'], self.colorset['menu-text-black']

        # Line of the pad
        translate = self.lang.translate
        texts = [(f"{translate('usb-pads-pad')} {plugged.index(port) + 1}/{len(plugged)} (USB {port})", None),
                 (translate('usb-pads-keys'), str(pad['keys'])),
                 (translate('usb-pads-knobs'), str(pad['knobs'])),
                 (translate('usb-pads-program'), None)]
        width = (14 * unit_x - 3 * gap) / 4
        for index, (text, value) in enumerate(texts):
            cell((unit_x + index * (width + gap), 3 * unit_y, width, unit_y), text, *colors(selected == (0, index)),
                 f'cell:0:{index}', value)
        if status is not None:
            self.blit_text(translate(status[0]), unit_x, 4.1 * unit_y, 14 * unit_x, 0.8 * unit_y, status[1])

        # Elements in columns, a second line beyond USB_PADS_COLUMNS
        labels = {'menus': translate('usb-pads-menus'), 'game': translate('usb-pads-game')}
        texts = {action[0]: translate(action[1]) for action in cusbpads.ACTIONS}
        columns = min(self.USB_PADS_COLUMNS, len(names))
        label_width = 2 * unit_x
        width = (12 * unit_x - (columns - 1) * gap) / columns
        heights = (unit_y, 1.2 * unit_y, 1.2 * unit_y)
        block = sum(heights) + 3 * gap
        top = 5 * unit_y
        for index, name in enumerate(names):
            line, place = divmod(index, self.USB_PADS_COLUMNS)
            pos_x = unit_x + label_width + gap + place * (width + gap)
            pos_y = top + line * (block + gap)
            if place == 0:
                for number, context in enumerate(('menus', 'game')):
                    label_y = pos_y + heights[0] + gap + number * (heights[1] + gap)
                    self.blit_text(labels[context], unit_x, label_y, label_width, heights[1], self.colorset['menu-text-white'], align='Left')
            header = self.colorset['menu-ok'] if name in lit else self.colorset['menu-shortcut']
            cell((pos_x, pos_y, width, heights[0]), self.usb_pads_element(name), header, self.colorset['menu-text-black'], None)
            for number, context in enumerate(('menus', 'game')):
                cell((pos_x, pos_y + heights[0] + gap + number * (heights[1] + gap), width, heights[1]),
                     texts.get(pad[context].get(name, ''), ''), *colors(selected == (number + 1, index)),
                     f'cell:{number + 1}:{index}')

        click_zones['escape'] = self.display_button(selected == (3, 0), 'back', special='escape')
        click_zones['save'] = self.display_button(selected == (3, 1), 'save', special='return')
        return click_zones

    def usb_pads_element(self, name):
        '''
        Name of an element of a pad shown : Touche 1, Molette gauche (Molette gauche 2 with
        several knobs)
        '''
        if name.startswith('k'):
            return f"{self.lang.translate('usb-pads-key')} {name[1:]}"
        knob, action = name[1:].split('-')
        text = self.lang.translate(f'usb-pads-knob-{action}')
        return text if knob == '1' else f"{text} {knob}"

    # Values offered by the screen of the coin acceptor
    COINS_PRICES = (0, 1, 2, 3, 4, 5)
    COINS_MINUTES = (1, 2, 3, 5, 10, 15, 20, 30, 45, 60)

    def coins_password(self, coins):
        '''
        Its password asked (set the first time). True : the screen of the coin acceptor opened
        '''
        translate = self.lang.translate
        if not coins.settings.get('password'):
            first = self.input_value_item('string', '', 4, 32, text='coins-password-new')
            if first in ('', 'escape'):
                return False
            if self.input_value_item('string', '', 4, 32, text='coins-password-again') != first:
                self.message([translate('coins-password-different')], 2500, self.colorset['menu-ko'], 'middle', 'big')
                return False
            settings = dict(coins.settings)
            settings['password'] = coins.hash_password(first)
            coins.save_settings(settings)
            return True
        typed = self.input_value_item('string', '', 1, 32, text='coins-password')
        if typed in ('', 'escape'):
            return False
        if not coins.check_password(typed):
            self.logs.warning("Coin acceptor : wrong password")
            self.message([translate('coins-password-wrong')], 2500, self.colorset['menu-ko'], 'middle', 'big')
            return False
        return True

    def coins_inputs(self, coins, current):
        '''
        Inputs offered to the coin acceptor : the pins of the MCP not used by the buttons and
        the toys (the GPIO of the Raspberry : all taken by the biggest wirings of a target)
        '''
        taken = {str(value).upper() for value in (self.config.config.get('Raspberry') or {}).values()}
        return [(name, f'MCP {name}') for name in (getattr(coins.extender, 'all_io', None) or [])
                if name not in taken or name == current]

    def coins_menu(self):
        '''
        Paramétrage > Monnayeur : behind its password ; its mode (free, credits by game, time),
        its input, the credits or the minutes of a coin, the players of a game, the prices by
        type and by game, credits given by hand, the coins counted (live : the test)
        '''
        coins = self.rpi.coins
        if not self.coins_password(coins):
            return
        translate = self.lang.translate
        settings = json.loads(json.dumps(coins.settings))
        selected = 1
        while True:
            source = str(settings.get('mcp') or '')
            types = settings.setdefault('types', {})
            price_text = lambda price: translate('coins-free') if int(price) == 0 else str(price)
            rows = [('mode', 'coins-mode', translate(f"coins-mode-{settings.get('mode')}")),
                    ('input', 'coins-input', f'MCP {source}' if source else translate('coins-input-none')),
                    ('credits', 'coins-credits-per-coin', str(settings.get('credits_per_coin'))),
                    ('players', 'coins-players-per-credit',
                     translate('coins-players-any') if int(settings.get('players_per_credit', 0)) == 0
                     else str(settings.get('players_per_credit'))),
                    ('minutes', 'coins-minutes-per-coin', str(settings.get('minutes_per_coin'))),
                    ('local', 'coins-price-local', price_text(types.get('local', 1))),
                    ('network', 'coins-price-network', price_text(types.get('network', 1))),
                    ('games', 'coins-price-games', str(len(settings.get('games') or {}))),
                    ('add', 'coins-add', ''),
                    ('count', 'coins-count', str(coins.state.get('coins', 0))),
                    ('position', 'coins-badge-position', translate(f"coins-badge-{settings.get('badge_position', 'top-right')}")),
                    ('size', 'coins-badge-size', translate(f"coins-badge-{settings.get('badge_size', 'medium')}")),
                    ('password', 'coins-password-change', '')]
            nb_elements = len(rows)
            self.display_background()
            last = coins.last_coin
            subtitle = translate('coins-sub') if last is None else \
                translate('coins-last').replace('{seconds}', str(int(time.monotonic() - last)))
            self.menu_header(translate('coins'), subtitle)
            click_zones = {}
            half = (nb_elements + 1) // 2
            for index, (_name, label, value) in enumerate(rows, 1):
                column = (0, half, index) if index <= half else (1, half, index - half)
                click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), (f'F{index}', label, BTN_DROPDOWN, value),
                                                          align='Full', tabs=True, column=column)
            click_zones['escape'] = self.display_button(selected == nb_elements + 1, 'back', special='escape')
            click_zones['save'] = self.display_button(selected == nb_elements + 2, 'save', special='return')
            self.update_screen()
            key = self.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'enter', 'space', 'single-click', 'PLAYERBUTTON',
                                                            'BACKUPBUTTON', 'GAMEBUTTON'], timeout=1000)
            if key is False:
                continue
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked
            if key in [f'F{index}' for index in range(1, nb_elements + 1)]:
                selected = int(key[1:])
                key = 'enter'
            selected = self.navigate(selected, key, nb_elements, 2, 2, left_right=True)
            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                # The strip of the credits shown as it was (not saved)
                coins.settings = coins.read(ccoins.SETTINGS, ccoins.DEFAULTS)
                return
            if key == 'save' or key in SAVE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 2):
                coins.save_settings(settings)
                self.message([translate('coins-saved')], 1500, self.colorset['menu-ok'], 'middle', 'big')
                return
            if key not in ENTER_KEYS or not 1 <= selected <= nb_elements:
                continue
            self.coins_change(coins, settings, rows[selected - 1][0], source)

    def coins_change(self, coins, settings, name, source):
        '''
        A row of the screen of the coin acceptor changed (its list, a question...)
        '''
        translate = self.lang.translate
        choose = lambda values, current: self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, values, navigate=current)
        prices = [(str(price), 'coins-free' if price == 0 else str(price)) for price in self.COINS_PRICES]
        if name == 'mode':
            chosen = choose([(mode, f'coins-mode-{mode}') for mode in ('off', 'games', 'time')], settings.get('mode'))
            if chosen != 'escape':
                settings['mode'] = chosen
        elif name == 'input':
            inputs = self.coins_inputs(coins, source)
            if not inputs:
                self.message([translate('coins-no-mcp')], 3000, self.colorset['menu-ko'], 'middle', 'big')
                return
            chosen = choose(inputs, source)
            if chosen != 'escape':
                settings['mcp'] = chosen
        elif name == 'credits':
            chosen = choose([(str(number), str(number)) for number in range(1, 11)], str(settings.get('credits_per_coin')))
            if chosen != 'escape':
                settings['credits_per_coin'] = int(chosen)
        elif name == 'players':
            chosen = choose([('0', 'coins-players-any')] + [(str(number), str(number)) for number in range(1, 9)],
                            str(settings.get('players_per_credit', 0)))
            if chosen != 'escape':
                settings['players_per_credit'] = int(chosen)
        elif name == 'minutes':
            chosen = choose([(str(number), str(number)) for number in self.COINS_MINUTES], str(settings.get('minutes_per_coin')))
            if chosen != 'escape':
                settings['minutes_per_coin'] = int(chosen)
        elif name in ('local', 'network'):
            chosen = choose(prices, str(settings['types'].get(name, 1)))
            if chosen != 'escape':
                settings['types'][name] = int(chosen)
        elif name == 'games':
            self.coins_games(settings, prices)
        elif name == 'add':
            timed = settings.get('mode') == 'time'
            values = [(str(number), f"{number} min" if timed else str(number))
                      for number in (self.COINS_MINUTES if timed else range(1, 11))]
            chosen = choose(values, values[0][0])
            if chosen != 'escape':
                coins.add(seconds=60 * int(chosen)) if timed else coins.add(credits=int(chosen))
                self.logs.info(f"Coin acceptor : {chosen} {'minutes' if timed else 'credits'} given by hand")
        elif name == 'count':
            if self.ask_yes_no(translate('coins-count-reset')):
                coins.reset_count()
        elif name in ('position', 'size'):
            # The strip of the credits : shown at once (saved with the others)
            key = 'badge_position' if name == 'position' else 'badge_size'
            choices = ccoins.BADGE_POSITIONS if name == 'position' else tuple(ccoins.BADGE_SIZES)
            chosen = choose([(choice, f'coins-badge-{choice}') for choice in choices], settings.get(key))
            if chosen != 'escape':
                settings[key] = chosen
                coins.settings[key] = chosen
        elif name == 'password':
            new = self.input_value_item('string', '', 4, 32, text='coins-password-new')
            if new not in ('', 'escape'):
                if self.input_value_item('string', '', 4, 32, text='coins-password-again') == new:
                    settings['password'] = coins.hash_password(new)
                    self.message([translate('coins-password-changed')], 1500, self.colorset['menu-ok'], 'middle', 'big')
                else:
                    self.message([translate('coins-password-different')], 2500, self.colorset['menu-ko'], 'middle', 'big')

    def coins_wait(self, title, text, enough):
        '''
        Coins asked : the screen until enough() (a coin, credits given) or Back. True : enough
        '''
        while not enough():
            # The background of the theme : in a game, the default one is the board of the game
            self.display_background(image=True)
            self.menu_header(self.lang.translate(title), text)
            self.blit_text(self.lang.translate('coins-insert-coin'), 0, int(self.res['y'] * 0.4), self.res['x'],
                           int(self.res['y'] / 8), (230, 30, 30))
            self.display_button(True, 'back', special='escape')
            self.update_screen()
            key = self.rpi.listen_inputs(['arrows'], ['escape', 'enter', 'space', 'single-click', 'PLAYERBUTTON',
                                                      'BACKUPBUTTON', 'GAMEBUTTON'], timeout=1000)
            if key in ESCAPE_KEYS or key in ('escape', 'single-click') or key in ENTER_KEYS:
                return enough()
        return True

    def coins_pay(self, game, game_type, players):
        '''
        A game about to start (include/ccoins.py) : free, paid (its credits taken), or coins
        asked until enough. False : given up (back to the menus)
        '''
        coins = getattr(self.rpi, 'coins', None)
        if coins is None or not coins.active():
            return True
        cost = coins.cost(game, game_type, len(players))
        if not coins.can_pay(cost):
            if coins.settings.get('mode') == 'time':
                text = self.lang.translate('coins-need-time')
            else:
                text = self.lang.translate('coins-need-credits').replace('{credits}', str(cost))
            if not self.coins_wait('coins', text, lambda: coins.can_pay(cost)):
                return False
        coins.pay(cost)
        self.logs.info(f"Coin acceptor : {game} ({game_type}, {len(players)} players) paid {cost}")
        return True

    def coins_time_up(self):
        '''
        Mode time, at the end of a turn : no time left, a coin asked to go on. False : the
        game stops
        '''
        coins = getattr(self.rpi, 'coins', None)
        if coins is None or not coins.time_up():
            return True
        self.logs.info("Coin acceptor : time up")
        return self.coins_wait('coins-time-up', self.lang.translate('coins-time-up-sub'), lambda: not coins.time_up())

    def coins_games(self, settings, prices):
        '''
        Prices by game : the price of its type, or one of its own (free, 1, 2...). The games of a
        type in a tab (as Classics / Fun / Sports of the favorites), in two columns of the same
        height
        '''
        translate = self.lang.translate
        games_dir = os.path.join(cpaths.ROOT_DIR, 'games')
        categories = []
        for category in ('classic', 'fun', 'sport'):
            folder = os.path.join(games_dir, category)
            categories.append(sorted(name[:-3] for name in (os.listdir(folder) if os.path.isdir(folder) else [])
                                     if name.endswith('.py') and not name.startswith('_')))
        tabs = (('category-classic', 'tab1'), ('category-fun', 'tab2'), ('category-sport', 'tab3'))
        own = settings.setdefault('games', {})
        # The tabs are -2, -1 and 0 (the type shown : the tab where the selection went last)
        tab = -2
        selected = 1
        values = [('type', 'coins-price-type')] + prices
        while True:
            names = categories[tab + 2]
            nb_elements = len(names)
            self.display_background()
            # No subtitle : the tabs are under the title (Prix du type says where a price comes from)
            self.menu_header(translate('coins-price-games'))
            click_zones = {}
            for number, (text, special) in enumerate(tabs, -2):
                click_zones[f'F{number}'] = self.display_button(number == selected, text, special=special)
            half = (nb_elements + 1) // 2
            for index, name in enumerate(names, 1):
                column = (0, half, index) if index <= half else (1, half, index - half)
                value = translate('coins-price-type') if name not in own else                     (translate('coins-free') if int(own[name]) == 0 else str(own[name]))
                click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), ('', name.replace('_', ' '), BTN_DROPDOWN, value),
                                                          align='Full', tabs=True, column=column)
            click_zones['escape'] = self.display_button(selected == nb_elements + 1, 'back', special='escape')
            self.update_screen()
            key = self.rpi.listen_inputs(['arrows'], ['escape', 'enter', 'space', 'single-click', 'PLAYERBUTTON',
                                                      'BACKUPBUTTON', 'GAMEBUTTON'])
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked
            if key in [f'F{index}' for index in range(-2, nb_elements + 1)]:
                selected = int(key[1:])
                key = 'enter' if selected > 0 else None
            else:
                selected = self.navigate(selected, key, nb_elements, 1, 1, left_right=True, zero=-2, tab=tab)
            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return
            if selected <= 0:
                # On a tab : its games shown at once (as the tabs of the customization)
                tab = selected
                continue
            if key in ENTER_KEYS and 1 <= selected <= nb_elements:
                name = names[selected - 1]
                chosen = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, values,
                                       navigate=str(own[name]) if name in own else 'type')
                if chosen == 'type':
                    own.pop(name, None)
                elif chosen != 'escape':
                    own[name] = int(chosen)

    def exhibition_menu(self):
        '''
        Exhibition mode : on or off, and the buttons of the main menu it shows
        '''
        globals_ = self.config.config['SectionGlobals']
        active = bool(self.config.get_value('SectionGlobals', 'exhibition_mode'))
        chosen = set(str(globals_.get('exhibition_items', '') or '').split(','))
        buttons = self.main_menu_items(everything=True)
        if not [name for name in chosen if name]:
            # Never chosen in this screen : those of the files of menus
            chosen = {self.menus().button_id(button) for button in buttons if button.get('exhibition')}
        rows = [('exhibition_mode', 'exhibition_mode')] + [(self.menus().button_id(button), self.button_text(button)) for button in buttons]
        nb_elements = len(rows)
        selected = 1
        while True:
            click_zones = {}
            self.display_background()
            self.menu_header(self.lang.translate('exhibition'), self.lang.translate('exhibition-sub'))
            for index, (name, text) in enumerate(rows, 1):
                value = active if name == 'exhibition_mode' else name in chosen
                # Same layout as the other screens of settings (Personnalisation...)
                click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), (f'F{index}', text, BTN_CHECK, value),
                                                          align='Full', tabs=True)
            click_zones['escape'] = self.display_button(nb_elements + 1 == selected, 'back', special='escape')
            click_zones['save'] = self.display_button(nb_elements + 2 == selected, 'save', special='return')
            self.update_screen()

            key = self.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'enter', 'space', 'single-click',
                                                            'PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON'])
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked
            selected = self.navigate(selected, key, nb_elements, 1, 2, left_right=True)

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return
            if key in SAVE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 2):
                globals_['exhibition_mode'] = active
                globals_['exhibition_items'] = ','.join(name for name, _t in rows[1:] if name in chosen)
                self.config.write_file()
                return
            if isinstance(key, str) and key.startswith('F') and key[1:].isdigit() and 1 <= int(key[1:]) <= nb_elements:
                selected = int(key[1:])
                key = 'enter'
            if (key in ENTER_KEYS or key == 'space') and 1 <= selected <= nb_elements:
                name = rows[selected - 1][0]
                if name == 'exhibition_mode':
                    active = not active
                elif name in chosen:
                    chosen.discard(name)
                else:
                    chosen.add(name)

    # The DMD display Raspy2DMD (its own project) installed on this machine, panels driven by a
    # Raspberry Pico by USB : it shows what RaspyDarts publishes on raspydarts/dmd, and takes its
    # commands on the topic raspy2dmd
    RASPY2DMD_DIR = '/Raspy2DMD'
    RASPY2DMD_TOPIC = 'raspy2dmd'
    # Its installation from the game : the public script, mode « Pico seul » (nothing changed in
    # the system of the cabinet), without question (the game answers : install, no reboot)
    RASPY2DMD_INSTALLER = 'https://raw.githubusercontent.com/rmdelcelier/Raspy2DMD/main/scripts/install_raspy2dmd.sh'
    RASPY2DMD_INSTALL_OPTIONS = '--pico-seul --sans-question'
    RASPY2DMD_INSTALL_UNIT = 'raspy2dmd-install'
    RASPY2DMD_INSTALL_LOG = 'logs/raspy2dmd_install.log'
    # Its updates : its releases vX.Y.Z.W (Raspy2DMD_PiZeroWH_v... on a Pi Zero W), the first one
    # not a draft, as its engine chooses them (DMDRenderer.searchUpdate) ; installed by its engine
    # when it starts (saved first, progress on the DMD, back to the old one if it fails)
    RASPY2DMD_RELEASES = 'https://api.github.com/repos/rmdelcelier/Raspy2DMD/releases'
    RASPY2DMD_VERSION = '/Raspy2DMD/web/VERSION'
    RASPY2DMD_CONFIG = '/Medias/Raspy2DMD.cfg'
    RASPY2DMD_UPDATE = 'update'
    # Its update followed this long at most (download of about 40 MB, copy, its scripts)
    RASPY2DMD_UPDATE_TIME = 600

    @classmethod
    def raspy2dmd_installed(cls):
        '''
        Raspy2DMD installed on this machine
        '''
        return os.path.isdir(cls.RASPY2DMD_DIR)

    @classmethod
    def raspy2dmd_installing(cls):
        '''
        Its installation running (launched from this screen, in the background)
        '''
        try:
            return subprocess.run(['systemctl', 'is-active', '--quiet', cls.RASPY2DMD_INSTALL_UNIT],
                                  check=False, timeout=5).returncode == 0
        except Exception:    # pylint: disable=broad-except
            return False

    @staticmethod
    def raspy2dmd_running():
        '''
        Its engine running (its watchdog, every minute, starts it within its operating hours ;
        it can also be started from its screen)
        '''
        try:
            return subprocess.run(['pgrep', '-f', 'python.*ServerRaspy2DMD[.]py'], stdout=subprocess.DEVNULL,
                                  check=False, timeout=5).returncode == 0
        except Exception:    # pylint: disable=broad-except
            return False

    def raspy2dmd_install(self):
        '''
        Raspy2DMD not installed : asked, then installed in the background (internet needed,
        15 to 45 minutes) ; the game stays usable meanwhile. Its log : logs/raspy2dmd_install.log.
        Followed at once (see raspy2dmd_install_progress) : True when installed
        '''
        if not self.wait_validation('raspy2dmd-install-question'):
            return
        import socket
        try:
            socket.create_connection(('raw.githubusercontent.com', 443), timeout=5).close()
        except OSError:
            self.message([self.lang.translate('raspy2dmd-no-internet')], 3000, self.colorset['menu-ko'], 'middle', 'big')
            return
        log = os.path.abspath(self.RASPY2DMD_INSTALL_LOG)
        command = f"curl -fsSL {self.RASPY2DMD_INSTALLER} | bash -s -- {self.RASPY2DMD_INSTALL_OPTIONS} > {log} 2>&1"
        try:
            # A unit of its own : it goes on even if the game is restarted
            subprocess.run(['sudo', 'systemd-run', f'--unit={self.RASPY2DMD_INSTALL_UNIT}', '--collect',
                            '/bin/bash', '-c', command], check=True, timeout=30,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.logs.info(f"Raspy2DMD : installation launched ({command})")
        except Exception as error:    # pylint: disable=broad-except
            self.logs.error(f"Raspy2DMD : installation not launched : {error}")
            self.message([self.lang.translate('raspy2dmd-install-failed')], 3000, self.colorset['menu-ko'], 'middle', 'big')
            return False
        # Followed at once (the screen of the settings came back : nothing showed it)
        return self.raspy2dmd_install_progress()

    def raspy2dmd_start(self):
        '''
        Start it at once, as at the start of the machine (rc.local) : its engine and its web
        page (each script once : the engine has its lock, the page is checked), in a unit of
        their own ; then up to 30 s for the engine
        '''
        command = ("(pgrep -f 'python.*ServerRaspy2DMD[.]py' > /dev/null || bash /Raspy2DMD/ServerRaspy2DMD.sh) & "
                   "(pgrep -f 'node.*app[.]js' > /dev/null || bash /Raspy2DMD/ServerRaspy2DMDWeb.sh) & wait")
        try:
            subprocess.run(['sudo', 'systemd-run', '--unit=raspy2dmd-start', '--collect', '/bin/bash', '-c', command],
                           check=True, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as error:    # pylint: disable=broad-except
            self.logs.error(f"Raspy2DMD : not started : {error}")
        self.message([self.lang.translate('raspy2dmd-starting')], 0, None, 'middle', 'big')
        for _ in range(30):
            if self.raspy2dmd_running():
                self.message([self.lang.translate('raspy2dmd-started')], 1500, self.colorset['menu-ok'], 'middle', 'big')
                return
            pygame.time.wait(1000)
        self.message([self.lang.translate('raspy2dmd-start-failed')], 3000, self.colorset['menu-ko'], 'middle', 'big')

    @staticmethod
    def raspy2dmd_version_key(version):
        '''
        A version X.Y.Z.W to compare
        '''
        return tuple(int(number) for number in re.findall(r'\d+', str(version)))

    def raspy2dmd_versions(self):
        '''
        Its version installed, and the last one published (None : none ; False : not read,
        no internet...)
        '''
        installed = self.raspy2dmd_installed_version()
        import platform    # pylint: disable=import-outside-toplevel
        prefix = 'Raspy2DMD_PiZeroWH_v' if platform.machine() == 'armv6l' else 'v?'
        pattern = re.compile(rf'^{prefix}(\d+\.\d+\.\d+\.\d+)$')
        try:
            import requests    # pylint: disable=import-outside-toplevel
            response = requests.get(self.RASPY2DMD_RELEASES, headers={'Accept': 'application/vnd.github.v3+json'}, timeout=10)
            response.raise_for_status()
            for release in response.json():
                match = pattern.match(str(release.get('tag_name', '')))
                if match and not release.get('draft'):
                    return installed, match.group(1)
            return installed, None
        except Exception as error:    # pylint: disable=broad-except
            self.logs.warning(f"Raspy2DMD : its releases not read : {error}")
            return installed, False

    def raspy2dmd_auto_update(self):
        '''
        Its updates installed by its engine when it starts ([Running] checkforupdate = 1, the
        default ; its configuration is readable by root only)
        '''
        import configparser    # pylint: disable=import-outside-toplevel
        try:
            text = subprocess.run(['sudo', '-n', 'cat', self.RASPY2DMD_CONFIG], capture_output=True, text=True,
                                  check=True, timeout=10).stdout
            config = configparser.ConfigParser(interpolation=None, strict=False)
            config.read_string(text)
            return config.get('Running', 'checkforupdate', fallback='1').strip() == '1'
        except Exception as error:    # pylint: disable=broad-except
            self.logs.warning(f"Raspy2DMD : its configuration not read : {error}")
            return True

    def raspy2dmd_restart(self):
        '''
        Its engine stopped, then started again by its service (installed by its versions from
        1.5.5.98), else as raspy2dmd_start does
        '''
        subprocess.run(['sudo', 'pkill', '-f', 'python.*ServerRaspy2DMD[.]py'], check=False, timeout=10)
        for _ in range(20):
            if not self.raspy2dmd_running():
                break
            pygame.time.wait(500)
        if os.path.isfile('/etc/systemd/system/raspy2dmd.service'):
            subprocess.run(['sudo', 'systemctl', 'restart', 'raspy2dmd'], check=False, timeout=30,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(['sudo', 'systemd-run', '--unit=raspy2dmd-start', '--collect', '/bin/bash',
                            '/Raspy2DMD/ServerRaspy2DMD.sh'], check=False, timeout=30,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def raspy2dmd_update(self):
        '''
        « Vérifier les mises à jour » : its last version published compared with the one
        installed ; a newer one, accepted : installed by its engine, started again for it (the
        progress on the DMD), followed here until its version changes
        '''
        translate = self.lang.translate
        self.message([translate('raspy2dmd-checking')], 0, None, 'middle', 'big')
        installed, latest = self.raspy2dmd_versions()
        if latest is False:
            self.message([translate('raspy2dmd-check-failed')], 3000, self.colorset['menu-ko'], 'middle', 'big')
            return
        if not latest or (installed and self.raspy2dmd_version_key(latest) <= self.raspy2dmd_version_key(installed)):
            self.message([translate('raspy2dmd-up-to-date').replace('{version}', installed or '?')], 3000,
                         self.colorset['menu-ok'], 'middle', 'big')
            return
        if not self.raspy2dmd_auto_update():
            self.message([translate('raspy2dmd-update-disabled')], 5000, self.colorset['menu-ko'], 'middle', 'big')
            return
        if not self.ask_yes_no(translate('raspy2dmd-update-question').replace('{version}', latest),
                               translate('raspy2dmd-update-explain').replace('{version}', installed or '?')):
            return
        self.logs.info(f"Raspy2DMD : update {installed} -> {latest} by its engine")
        self.raspy2dmd_restart()
        started = time.monotonic()
        while time.monotonic() - started < self.RASPY2DMD_UPDATE_TIME:
            seconds = int(time.monotonic() - started)
            # The time in the same text (two texts were drawn one over the other)
            self.message([f"{translate('raspy2dmd-updating').replace('{version}', latest)} ({seconds // 60}:{seconds % 60:02d})"],
                         0, None, 'middle', 'big')
            # Its version written at the end of the copy ; then its engine starts again
            if self.raspy2dmd_installed_version() == latest and self.raspy2dmd_running():
                self.logs.info(f"Raspy2DMD : {latest} installed in {seconds} s")
                self.message([translate('raspy2dmd-updated').replace('{version}', latest)], 3000,
                             self.colorset['menu-ok'], 'middle', 'big')
                return
            pygame.time.wait(1000)
        self.logs.error(f"Raspy2DMD : {latest} not installed after {self.RASPY2DMD_UPDATE_TIME} s")
        self.message([translate('raspy2dmd-update-failed')], 5000, self.colorset['menu-ko'], 'middle', 'big')

    def raspy2dmd_installed_version(self):
        '''
        Its version installed ('' : none)
        '''
        try:
            with open(self.RASPY2DMD_VERSION, encoding='utf-8') as file:
                return file.read().strip()
        except OSError:
            return ''

    def raspy2dmd_install_log(self):
        '''
        Its log of installation : its lines, without the colours of the terminal nor the lines
        drawn
        '''
        try:
            with open(self.RASPY2DMD_INSTALL_LOG, encoding='utf-8', errors='ignore') as file:
                lines = [re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line).strip()
                         for line in file.read().replace('\r', '\n').split('\n')]
        except OSError:
            return []
        return [line for line in lines if line and not set(line) <= set('─━═-=')]

    def raspy2dmd_install_started(self):
        '''
        Seconds since its installation started (None : unknown)
        '''
        try:
            value = subprocess.run(['systemctl', 'show', '--value', '-p', 'ActiveEnterTimestampMonotonic',
                                    self.RASPY2DMD_INSTALL_UNIT], capture_output=True, text=True, check=False,
                                   timeout=5).stdout.strip()
            return time.monotonic() - int(value) / 1e6 if value and int(value) > 0 else None
        except (OSError, ValueError, subprocess.TimeoutExpired):
            return None

    def raspy2dmd_install_progress(self):
        '''
        Its installation running : a bar by its steps ([ETAPE 4/14] ...), its step, the last line
        of its log and the time gone by. Its end : said, and installed, Raspy2DMD started at once
        (its watchdog would take up to a minute). True : installed ; False : left (it goes on)
        or failed
        '''
        translate = self.lang.translate
        while self.raspy2dmd_installing():
            self.display_background()
            self.menu_header(translate('raspy2dmd'), translate('raspy2dmd-installing'))
            lines = self.raspy2dmd_install_log()
            step = next((line for line in reversed(lines) if line.startswith('[ETAPE')), '')
            last = lines[-1] if lines and lines[-1] != step else ''
            # Its progress bars : blocks the font of the game does not have, their percentage kept
            last = re.sub(r'\[[^\]%]*\]\s*', '', last) if '%' in last else last
            last = re.sub('[─-▟]', '', last).strip()
            numbers = re.match(r'\[ETAPE (\d+)/(\d+)\]', step)
            done = (int(numbers.group(1)) - 1) / int(numbers.group(2)) if numbers else 0
            line = int(self.res['y'] / 18)
            pos_x, width, pos_y = self.res_x_16 * 3, self.res_x_16 * 10, int(self.res['y'] * 0.35)
            self.blit_rect(pos_x, pos_y, width, line, self.colorset['menu-buttons'], Alpha=255)
            self.blit_rect(pos_x, pos_y, max(1, int(width * done)), line, self.colorset['menu-ok'], Alpha=255)
            self.blit_text(step[:90], 0, pos_y + line * 1.5, self.res['x'], line, self.colorset['menu-text-white'])
            self.blit_text(last[:90], 0, pos_y + line * 3, self.res['x'], int(line * 0.8), self.colorset['menu-text-white'])
            started = self.raspy2dmd_install_started()
            if started is not None:
                self.blit_text(translate('raspy2dmd-install-elapsed').replace('{time}', f"{int(started) // 60}:{int(started) % 60:02d}"),
                               0, pos_y + line * 4.5, self.res['x'], int(line * 0.8), self.colorset['menu-text-white'])
            self.display_button(True, 'back', special='escape')
            self.update_screen()
            key = self.rpi.listen_inputs(['arrows', 'fx'], ['escape', 'enter', 'space', 'PLAYERBUTTON', 'BACKUPBUTTON',
                                                            'GAMEBUTTON', 'single-click'], timeout=2000)
            if key in ESCAPE_KEYS or key in ENTER_KEYS or key in ('escape', 'single-click'):
                self.message([translate('raspy2dmd-install-continues')], 3000, None, 'middle', 'big')
                return False
        if any('Installation terminee avec succes' in line for line in self.raspy2dmd_install_log()[-30:])                 and self.raspy2dmd_installed():
            self.logs.info("Raspy2DMD : installed from the game")
            self.message([translate('raspy2dmd-install-done')], 3000, self.colorset['menu-ok'], 'middle', 'big')
            if not self.raspy2dmd_running():
                self.raspy2dmd_start()
            return True
        self.logs.error(f"Raspy2DMD : installation failed (see {self.RASPY2DMD_INSTALL_LOG})")
        self.message([translate('raspy2dmd-install-error')], 5000, self.colorset['menu-ko'], 'middle', 'big')
        return False

    def raspy2dmd_menu(self, dispatcher):
        '''
        The DMD display Raspy2DMD : the QR code of its web page (all its settings, from a
        phone), and a few commands sent to it (a message to check the link, the test pattern
        of the Pico, the clock, the demo)
        '''
        # Its installation followed until its end : then its screen
        if self.raspy2dmd_installing() and not self.raspy2dmd_install_progress():
            return
        if not self.raspy2dmd_installed() and not self.raspy2dmd_install():
            return
        from include import cgallery
        import qrcode
        import socket
        # Its address by the name of the Raspberry (raspydarts.local) : it stays when the IP
        # changes ; the IP written under it, if a device does not know the .local names
        url = f"http://{socket.gethostname()}.local/"
        address = f"http://{cgallery.local_ip()}/"
        picture = qrcode.make(url)
        picture = (picture.get_image() if hasattr(picture, 'get_image') else picture).convert('RGB')
        side = int(self.res['y'] * 0.5)
        code = pygame.transform.scale(pygame.image.fromstring(picture.tobytes(), picture.size, 'RGB'), (side, side))
        selected = 1
        while True:
            # Stopped : start it (its commands go through it) ; running : its commands
            running = self.raspy2dmd_running()
            commands = [('raspy2dmd-test-message', f"msg|{self.lang.translate('raspy2dmd-hello')}"),
                        ('raspy2dmd-test-pattern', 'pico|test_rgb'),
                        ('raspy2dmd-clock', 'time|start'),
                        ('raspy2dmd-demo', 'demo|gif')] if running else [('raspy2dmd-start', None)]
            commands.append(('raspy2dmd-check-update', self.RASPY2DMD_UPDATE))
            nb_elements = len(commands)
            selected = min(selected, nb_elements + 1)
            self.display_background()
            self.menu_header(self.lang.translate('raspy2dmd'), self.lang.translate('raspy2dmd-scan'))
            pos_x = int(self.res_x_16 * 2)
            pos_y = int(self.res['y'] / 5)
            self.blit(code, (pos_x, pos_y))
            line = int(self.res['y'] / 20)
            self.blit_text(url, pos_x, pos_y + side + self.margin, side, line, self.colorset['menu-text-white'])
            self.blit_text(address, pos_x, pos_y + side + self.margin + line, side, int(line * 0.8), self.colorset['menu-text-white'])
            if not running:
                # Installed, not started (just installed, out of its operating hours...)
                self.blit_text(self.lang.translate('raspy2dmd-not-running'), 0, pos_y + side + self.margin + line,
                               self.res['x'], line, self.colorset['menu-ko'])
            click_zones = {}
            for index, (text, _) in enumerate(commands, 1):
                click_zones[f'F{index}'] = self.menu_item((index, nb_elements, selected), (f'F{index}', text, BTN_CHOICE, None),
                                                          align='Right')
            click_zones['escape'] = self.display_button(selected == nb_elements + 1, 'back', special='escape')
            self.update_screen()

            key = self.rpi.listen_inputs(['arrows', 'fx'],
                                         ['escape', 'enter', 'space', 'PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON', 'single-click'])
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked
            if key in [f'F{index}' for index in range(1, nb_elements + 1)]:
                selected = int(key[1:])
                key = 'enter'
            selected = self.navigate(selected, key, nb_elements, 1, 1, left_right=True)
            if key in ESCAPE_KEYS or key == 'escape' or (key in ENTER_KEYS and selected == nb_elements + 1):
                return
            if key in ENTER_KEYS and 1 <= selected <= nb_elements:
                if commands[selected - 1][1] is None:
                    self.raspy2dmd_start()
                    selected = 1
                    continue
                if commands[selected - 1][1] == self.RASPY2DMD_UPDATE:
                    self.raspy2dmd_update()
                    continue
                dispatcher.mqtt_publish(self.RASPY2DMD_TOPIC, commands[selected - 1][1])
                self.message([self.lang.translate('raspy2dmd-sent')], 1000, self.colorset['menu-ok'], 'middle', 'big')

    def gallery_menu(self):
        '''
        QR code of the gallery of the memories (see cgallery), and its password : only its
        hash is kept in the configuration. A QR code shown here logs in at once
        '''
        from include import cgallery
        import qrcode
        selected = 2
        while True:
            gallery = self.config.config.setdefault('Gallery', {'password': ''})
            stored = str(gallery.get('password', '')).strip()
            url = cgallery.address(cgallery.local_ip(), stored=stored)
            picture = qrcode.make(url)
            picture = (picture.get_image() if hasattr(picture, 'get_image') else picture).convert('RGB')
            side = int(self.res['y'] * 0.55)
            code = pygame.transform.scale(pygame.image.fromstring(picture.tobytes(), picture.size, 'RGB'), (side, side))

            self.display_background()
            self.menu_header(self.lang.translate('gallery'), self.lang.translate('gallery-scan'))
            pos_y = int(self.res['y'] / 5)
            self.blit(code, (int((self.res['x'] - side) / 2), pos_y))
            pos_y += side + self.margin * 2
            line = int(self.res['y'] / 20)
            self.blit_text(url.split('?')[0], 0, pos_y, self.res['x'], line, self.colorset['menu-text-white'])
            if not stored:
                self.blit_text(self.lang.translate('gallery-no-password'), 0, pos_y + line, self.res['x'], line, self.colorset['menu-ko'])
            click_zones = {'escape': self.display_button(selected == 1, 'back', special='escape'),
                           'password': self.display_button(selected == 2, 'gallery-password', special='return')}
            self.update_screen()

            key = self.rpi.listen_inputs(['arrows', 'fx'],
                                         ['escape', 'enter', 'space', 'PLAYERBUTTON', 'BACKUPBUTTON', 'GAMEBUTTON', 'single-click'])
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                key = clicked
            if key in LEFT_KEYS:
                selected = 1
            elif key in RIGHT_KEYS:
                selected = 2
            elif key == 'password' or (key in ENTER_KEYS and selected == 2):
                # Empty : no password any more
                typed = self.input_value_item('string', '', 0, 32, text='gallery_password')
                if typed != 'escape':
                    gallery['password'] = cgallery.hash_password(typed) if typed else ''
                    self.config.write_file()
                    text = 'gallery-password-set' if typed else 'gallery-password-removed'
                    self.message([self.lang.translate(text)], 1500, self.colorset['menu-ok'], 'middle', 'big')
            elif key in ESCAPE_KEYS or key in ENTER_KEYS or key == 'escape':
                return

    def extract_version(self, file_name):
        '''
        Return version of file, included in his name
        '''
        version = re.search(r'^.*V([0-9._]*)\..*$', file_name)

        return version.group(1)

    def get_backups_list(self):
        '''
        Get list and infos from availables backup files
        '''
        file_list = []
        tmp_list = []

        if len(glob.glob('backup')) > 0:
            for backup in glob.glob('backup/raspydarts*tgz') + glob.glob('backup/update*tgz'):
                tmp_list.append(backup)

            tmp_list.sort(key = self.extract_version, reverse=True)

            for backup in tmp_list:
                data = backup.split('_')
                file_list.append((backup, data[1], data[2], data[3]))

            return file_list
        return None

    # An entry of the list Favoris : a favorite game ('Ho One'), or a numbered favorite of
    # its game ('Ho One|fav1') : the same game can be there several times, each one with its options
    FAVORITE_SEPARATOR = '|'

    def favorite_entries(self, favorite_games):
        '''
        The list Favoris : the favorites without number (Ho One|list0...), by game, then the
        numbered ones (Ho One|fav1...). favorite_games : those of raspydarts.cfg (before the
        favorites without number)
        '''
        entries = []
        try:
            unnumbered = sorted(enumerate(self.favorites().unnumbered(favorite_games)), key=lambda item: item[1]['game'])
            for position, entry in unnumbered:
                entries.append(f"{entry['game'].replace('_', ' ')}{self.FAVORITE_SEPARATOR}list{position}")
            for slot, favorite in self.favorites().numbered():
                entries.append(f"{favorite['game'].replace('_', ' ')}{self.FAVORITE_SEPARATOR}{slot}")
        except Exception as error:    # pylint: disable=broad-except
            self.logs.error(f"Favorites : not read ({error})")
        return entries

    def favorite_entry(self, entry):
        '''
        An entry of the lists of games : (its game, the slot of its numbered favorite or None)
        '''
        game, _, slot = str(entry).partition(self.FAVORITE_SEPARATOR)
        return game, slot or None

    def favorite_entry_options(self, entry, favorite_games):
        '''
        Options of an entry of the list Favoris : those of its favorite ({} : without options,
        chosen at its launch), None if it is not a favorite
        '''
        _, slot = self.favorite_entry(entry)
        return self.favorite_slot_options(slot, favorite_games) if slot else None

    def favorite_slot_options(self, slot, favorite_games):
        '''
        Options of a favorite : list0... (without number) or fav1... ({} : chosen at its
        launch), None if it does not exist any more
        '''
        try:
            if slot.startswith('list'):
                unnumbered = self.favorites().unnumbered(favorite_games)
                position = int(slot[4:])
                return dict(unnumbered[position]['options']) if position < len(unnumbered) else None
            favorite = self.favorites().get(slot)
            return dict(favorite['options']) if favorite else None
        except Exception as error:    # pylint: disable=broad-except
            self.logs.error(f"Favorites : options of {slot} not read ({error})")
        return None

    def favorite_entry_label(self, entry):
        '''
        Name of an entry : the game, and the number of its numbered favorite
        '''
        game, slot = self.favorite_entry(entry)
        return f"{game} · {self.lang.translate('favorite')} {slot[3:]}" if slot and slot.startswith('fav') else game

    def get_games_list(self, category='classic', favorites=None):
        '''
        Get Game List from local game folder
        '''
        if self.games.get(category) is None or category == 'favoris':
            if category == 'favoris':
                fileiter = (os.path.join(root, f)
                        for root, _, files in chain(os.walk(f'games/classic'), os.walk(f'games/fun'), os.walk(f'games/sport'))
                        for f in files if f.replace('.py', '').replace('_', ' ') in favorites)
            else:
                fileiter = (os.path.join(root, f)
                        for root, _, files in os.walk(f'games/{category}')
                        for f in files)
            fileiter = sorted(fileiter)
            menu_data = [self.lang.translate('game-list')]
            games = []
            for foundfiles in fileiter:
                name, extension = os.path.splitext(foundfiles)
                if extension == '.py' and os.path.basename(name) != '__init__':
                    games.append(os.path.basename(name).replace('_', ' '))
                    menu_data.append(os.path.basename(name).replace('_', ' '))

            # Display all games names
            self.logs.debug(f"Found these games : {'/'.join(menu_data[1:])}")
            self.games[category] = games
            return games
        else:
            return self.games.get(category)

    def get_description(self, game):
        '''
        Get Game description (from language file)
        '''
        description = []
        try:
            description = self.lang.translate(f"Description-{game.replace(' ', '_')}")
        except:
            description.append(self.lang.translate('game-no-desc'))
            self.logs.warning(f"Unable to get a description for game {game}")
        return description

    def game_category_menu(self, favorites, category=None, load=False):
        '''
        Menu which display a table to choose the category of the game : described by the
        files of menus (menus/defaults.yaml...). Favorites : only if there are favorite games
        '''
        if load:
            return None
        menus = self.menus()
        everything = [button for button in menus.buttons('categories')
                      if favorites or button.get('requires') != 'favorite_games']
        buttons = [button for button in everything if button.get('visible', True) is not False]
        initial = None if category is None else next((menus.button_id(button) for button in buttons
                                                      if menus.result(button) == category), None)
        return menus.result(self.run_menu('categories', buttons, everything, initial=initial))

    @with_look('games')
    def game_menu(self, category, games_list, favorites, nb_player, selected_game=None, load=False):
        '''
        Menu which display a table to choose the game
        '''
        selected = 1

        if not load:
            self.dmd.send_text(self.lang.translate('dmd-game-choice'), tempo=1)

        games = []
        index = 1
        # Favorites first
        for game in games_list:
            if game in favorites:
                games.append(game)
                if selected_game is not None and selected_game == game:
                    selected = index
                index += 1

        # and others
        if category != 'favoris':
            for game in games_list:
                if game not in favorites:
                    games.append(game)
                    if selected_game is not None and selected_game == game:
                        selected = index
                    index += 1
        else:
            # Favoris : its entries (favorite games, then numbered favorites : a game may be there
            # several times)
            games = list(games_list)
            selected = next((position for position, entry in enumerate(games, 1) if entry == selected_game), 1)

        nb_elements = len(games)
        if nb_elements > 16:
            nb_column = 5
        else:
            nb_column = 4

        # Look given by the files of menus (menu games : columns, area, style of the tiles)
        own = (self.menus().data.get('menus') or {}).get('games') or {}
        if own.get('columns'):
            nb_column = max(1, int(own['columns']))
        tiles = None if load else self.game_tiles(games, nb_column, own)
        pristine = None

        refresh = True
        old_selection = None
        #self.imagecache = {}

        while True:
            click_zones = {}
            shortcuts = []
            validate = []
            states = []
            if not load and tiles is not None and pristine is not None:
                # Background and title drawn once
                self.screen.blit(pristine, (0, 0))
            elif not load:
                # Draw background
                self.display_background()

                # Screen Titles
                self.menu_header(self.lang.translate('game-list'))
                if tiles is not None:
                    pristine = self.screen.copy()

            index = 1
            for entry in games:     # Display Game menu
                game, slot = self.favorite_entry(entry)
                shortcut = f'F{index}'
                try:
                    min_max_players_per_game = self.config.get_value('NbOfPlayersPerGame', game.replace(" ", "_"))
                except:
                    self.logs.error("[] No game with name '{0}' find in DefaultConfig['NbOfPlayersPerGame'] dict".format(game.replace(" ", "_")))
                    min_max_players_per_game = [0, 0, False]
                    
                good_nb_players = int(min_max_players_per_game[0]) <= nb_player and nb_player <= int(min_max_players_per_game[1])
                player_in_pairs = bool(min_max_players_per_game[2])

                if player_in_pairs:
                    if nb_player % 2 != 0:
                        good_nb_players = False
                
                if index == selected:
                    # A favorite with options : its options instead of the description
                    options = self.favorite_entry_options(entry, favorites) if category == 'favoris' else None
                    game_desc_rect = self.game_description(game, False, min_max_players=min_max_players_per_game, goodNbPlayers=good_nb_players,
                                                           favorite_options=options, title=self.favorite_entry_label(entry))
                    game_desc_rect = [(game_desc_rect[0], game_desc_rect[1], game_desc_rect[2], game_desc_rect[3])]
                
                if tiles is None:
                    click_zones[shortcut] = self.logo_item((index, len(games), selected), game.replace(' ', '_'), nb_column, 'Left', border_radius=25, available=good_nb_players)
                    if slot and slot.startswith('fav'):
                        # Its number on its logo : the same game may be there several times
                        self.favorite_badge(click_zones[shortcut], slot[3:])
                else:
                    states.append((index, 'selected' if index == selected else 'normal' if good_nb_players else 'disabled'))

                validate.append(good_nb_players)
                if good_nb_players:
                    shortcuts.append(shortcut)
                index += 1

            if load:
                return
            if tiles is not None:
                # The selected tile last : enlarged (scale), it stays over its neighbours
                for tile_index, look in sorted(states, key=lambda state: state[1] == 'selected'):
                    click_zones[f'F{tile_index}'] = self.game_tile(tiles, pristine, tile_index, look)
                refresh = True
            # Arrow to go back and next
            click_zones['escape'] = self.display_button(index == selected, 'back', special='escape')

            if selected <= nb_elements:
                selection = click_zones[f'F{selected}']
            elif nb_elements == selected:
                selection = click_zones['escape']
            else:
                selection = None

            # Update screen
            if refresh:
                self.update_screen()
                refresh = False
            elif old_selection is None or selection is None:
                self.update_screen(rect_array=[click_zones[click_zone] for click_zone in click_zones] + game_desc_rect)
            else:
                self.update_screen(rect_array=[old_selection, selection] + game_desc_rect)

            key = self.rpi.listen_inputs(
                    ['arrows', 'fx', 'alpha', 'math'],
                    ['escape', 'PLAYERBUTTON', 'BACKUPBUTTON', 'TOGGLEFULLSCREEN', 'GAMEBUTTON',
                    'single-click', 'double-click', 'resize', 'VOLUME-UP', 'VOLUME-DOWN',
                    'enter', 'space'],
                    events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Click cases
            clicked = self.is_clicked(click_zones, key)
            if clicked:
                if clicked in shortcuts:
                    selected = int(clicked[1::])
                    key = 'enter'
                else:
                    key = clicked

            # Navigation menu
            selected = self.navigate(selected, key, nb_elements, 1, 1, \
                    item_per_line=nb_column, left_right=True)
            
            if selected <= nb_elements:
                self.dmd.send_text(self.favorite_entry_label(games[selected - 1]).replace('_', ' '))
            else:
                self.dmd.send_text(self.lang.translate('back'))
            # Keyboard cases
            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                return 'escape'

            if (key in ENTER_KEYS + SAVE_KEYS + CONTINUE_KEYS) and validate[selected-1] == True:
                # A numbered favorite : its game (the entry tells it to raspydarts.py)
                self.selectedgame = self.favorite_entry(games[selected - 1])[0]
                if category == 'favoris':
                    tmp = f"{self.selectedgame.replace(' ', '_')}.py"
                    if os.path.isfile(f"{self.config.gamesDir}/classic/{tmp}"):
                        category = 'classic'
                    elif os.path.isfile(f"{self.config.gamesDir}/fun/{tmp}"):
                        category = 'fun'
                    elif os.path.isfile(f"{self.config.gamesDir}/sport/{tmp}"):
                        category = 'sport'
                    else:
                        return None

                return f'{category}.{games[selected - 1]}'

            old_selection = selection

    def display_row(self, item_id, total, selected, columns, ratio=1, offset=0, center=True, align=None):
        '''
        Menu to display a row (to display an array)
        '''

        # Columns = [("Title1", pct1), ("Title2", pct2), ... ]

        # 1st cell position
        if center:
            min_x = self.res_x_16
        elif align == 'right':
            min_x = int(self.res['x'] * 3 / 4)
        else:
            min_x = int(self.res['x'] / 2)
        min_y = 4 * self.res_y_16

        # Line size
        if center:
            row_width = int(self.res['x'] * 14 / 16)
        elif align == 'right':
            row_width = int(self.res['x'] * 7 / 32)
        else:
            row_width = int(self.res['x'] * 7 / 16)
        row_height = int((self.res['y'] * 10 / 16) / (max(15, total)))

        # Apply ratio
        if ratio < 1:
            row_width = int(row_width * ratio)
            if center:
                min_x = int((self.res['x'] - row_width) / 2)

        cell_x = min_x
        cell_y = min_y + row_height * (item_id - 1 + offset)

        index = 0
        for column in columns:
            index += 1
            # Cell size
            cell_width = int(row_width * column[1])

            # Cell value
            value = column[0]

            # Cell color
            if item_id == selected:
                cell_color = self.colorset['menu-selected']
                cell_text_color = self.colorset['menu-text-black']
            elif item_id == 1:
                cell_color = self.colorset['menu-item-white']
                cell_text_color = self.colorset['menu-text-black']
            elif item_id % 2 == 0:
                cell_color = self.colorset['menu-item-black']
                cell_text_color = self.colorset['menu-text-white']
            else:
                cell_color = self.menu_color(self.colorset['menu-buttons'])
                cell_text_color = self.colorset['menu-text-black']

            if item_id == 1 and index == 1:
                corners = 'TopLeft'
            elif item_id == 1 and index == len(columns):
                corners = 'TopRight'
            elif item_id == total and index == 1:
                corners = 'BottomLeft'
            elif item_id == total and index == len(columns):
                corners = 'BottomRight'
            else:
                corners = 'None'

            self.new_blit_rect(cell_x, cell_y, cell_width, row_height, cell_color, corners=corners)
            self.blit_text(value, cell_x, cell_y, cell_width, row_height, cell_text_color, \
                    align='Center')

            cell_x += cell_width

        return (min_x, cell_y, row_width, row_height)

    def display_big_row(self, item_id, total, selected, columns, offset=0):
        '''
        Menu to display a big row (to display an array)
        '''
        # Columns = [("Title1", pct1), ("Title2", pct2), ... ]

        row_width = int(self.res['x'] * 14 / 16)
        row_height = int((self.res['y'] * 10 / 16) / (max(5, total)))

        cell_x = self.res_x_16
        cell_y = 3 * self.res_y_16 + row_height * (item_id - 1 + offset)

        for column in columns:
            # Cell size
            cell_width = int(row_width * column[1])

            # Cell value
            text = column[0]

            # Cell color
            if item_id == 1:
                cell_color = self.colorset['menu-item-black']
                cell_text_color = self.colorset['menu-text-white']
            elif item_id == selected:
                cell_color = self.colorset['menu-selected']
                cell_text_color = self.colorset['menu-text-white']
            elif item_id % 2 == 1:
                cell_color = self.colorset['menu-buttons']
                cell_text_color = self.colorset['menu-text-black']
            else:
                cell_color = self.menu_color(self.colorset['menu-buttons'])
                cell_text_color = self.colorset['menu-text-black']

            self.new_blit_rect(cell_x, cell_y, cell_width, row_height, cell_color)
            self.blit_text(text, cell_x, cell_y, cell_width, row_height, cell_text_color, \
                    align='Center')

            cell_x += cell_width

        return (self.res_x_16, cell_y, row_width, row_height)

    def net_game_list(self, master_client, number_of_players, host, port):
        '''
        Menu which display a table to choose net game (MasterServer Client)
        '''
        self.rpi.shift = False    # Reinit Kbd Shift status
        # Display "Pending connexion..."
        self.display_background()
        self.message([self.lang.translate('master-client-connecting')], wait = 0)
        masterclientpolltime = int(self.config.get_value('SectionAdvanced', 'masterclientpolltime'))
        selected = 1

        while True:
            try:
                self.logs.debug(f"Try to connect to {host}:{port}")
                master_client.connect_master(host, port)
                self.logs.debug(f"Connected")
            except:
                self.logs.error(f"Unable to reach Master Server : {host}:{port}")
                self.display_background()
                self.message([self.lang.translate('master-client-no-connection')])
                return 'escape'    # Tels master loop to turn back to previous menu

            game_list = master_client.wait_list(number_of_players)    # get and clean server list
            self.logs.debug(f"game_list={game_list}")
            master_client.close_connection()
            self.logs.debug(f"Disconnected")

            # In case of network issue
            if game_list is False:
                # Tell the user there is a network error
                msg = self.lang.translate('network-error')
                # Display error msg
                self.message([msg], 1000)
                # Simulate an escape key (back to menu)
                return 'escape'

            if game_list == 0:
                game_list = {}
            # In case of a list containing something (or not)
            self.logs.debug(f"Received a list with {len(game_list)} games")
            nb_elements = len(game_list) + 1    # Add first line

            while True:
                # Display basis
                self.display_background()
                self.menu_header(self.lang.translate('master-client-title'), \
                        self.lang.translate('master-client-refresh'))

                click_zones = {}
                self.display_row(0, nb_elements, False, [('game-name', 4 / 16), \
                        ('game-type', 4 / 16), ('creator', 6 / 16), \
                        ('players', 2 / 16)], 3 / 4)

                index = 0
                for game in game_list:
                    click_zones[f'select|{index}'] = self.display_row(1 + index, nb_elements, \
                            selected, [(game['GAMENAME'], 4 / 16), \
                            (game['GAMETYPE'].replace('_', ' '), 4 / 16), \
                            (game['GAMECREATOR'], 6 / 16), (str(game['PLAYERS']), 2 / 16)], 3 / 4)
                    index += 1

                click_zones['escape'] = self.display_button(index + 2 == selected, 'back', special='escape')
                #click_zones['escape'] = self.display_button(index + 3 == selected, 'refresh', special='refresh')

                self.update_screen()    # refresh screen

                # Listen for any input
                key = self.rpi.listen_inputs(['arrows', 'alpha'], ['enter', 'escape', 'space', \
                        'TOGGLEFULLSCREEN', 'single-click'], \
                        timeout=max(1000, masterclientpolltime))

                if not key:
                    # Refresh screen
                    break

                # Mouse
                clicked = self.is_clicked(click_zones, key)
                if clicked:
                    if "select|" in clicked:
                        selected = int(clicked.split('|')[1]) + 1
                        key = 'enter'
                    else:
                        key = clicked

                # Navigation menu
                # Avoid 1st line => titles
                # Right and left too, in reading order ; left on the first one : the last button
                moved = self.navigate(selected, key, nb_elements, 2, 2, left_right=True)
                selected = moved if moved >= 2 else (nb_elements + 2 if key in LEFT_KEYS else 2)

                # Keyboard
                if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                    return 'escape'

                if key in ENTER_KEYS and selected <= nb_elements:
                    return game_list[selected-2]['GAMENAME']    # Header not counted

    def favorite_badge(self, rect, number):
        '''
        The number of a numbered favorite, in a corner of its logo
        '''
        side = max(12, int(rect[3] / 4))
        badge = pygame.Rect(rect[0] + rect[2] - side - 4, rect[1] + 4, side, side)
        pygame.draw.circle(self.screen, self.colorset.get('menu-favorite') or (255, 215, 0), badge.center, side // 2)
        font = self.font(self.defaultfontpath, int(side * 0.8))
        text = font.render(str(number), True, (0, 0, 0))
        self.screen.blit(text, text.get_rect(center=badge.center))

    def favorite_options_text(self, game, options):
        '''
        The options of a favorite, one per line (as the screen of the options names them)
        '''
        lines = [f"{self.lang.translate('favorite-options-title')} :", '']
        return '\n'.join(lines + self.favorite_options_lines(game, options))

    def favorite_options_lines(self, game, options):
        '''
        The options of a favorite : 'label : value' (as the screen of the options names them)
        '''
        if not options:
            return [self.lang.translate('favorite-no-options')]
        lines = []
        for name, value in options.items():
            if isinstance(value, bool):
                value = self.lang.translate('yes' if value else 'no')
            label = self.lang.translate('colorset') if name == 'theme' else self.translate_option(game.replace(' ', '_'), name)
            lines.append(f"{label} : {value}")
        return lines

    def game_description(self, game, full=False, versionGame = '', min_max_players = None, goodNbPlayers=True, favorite_options=None, title=None):
        '''
        Display game's description (a favorite with options : its options instead, and its name
        with its number)
        '''

        # Game description
        description = self.get_description(game)
        if favorite_options is not None:
            description = self.favorite_options_text(game, favorite_options)
        
        # Marges
        marge_x = int(self.res['x'] / 64)
        marge_y = int(self.res['y'] / 64)
    
        # Main box
        box_pos_x = int(self.res['x'] * 7 / 16)
        box_width = int(self.res['x'] * 9 / 16 - marge_x)
        box_pos_y = 2.5 * self.res_y_16
        box_height = 10.5 * self.res_y_16

        if not full:
            # Title box
            title_pos_x = box_pos_x
            title_pos_y = box_pos_y
            title_width = box_width
            title_height = self.res_y_16

            # Players' box
            players_pos_x = box_pos_x
            players_width = box_width
            players_height = self.res_y_16
            box_height = box_height + players_height
            players_pos_y = box_pos_y + box_height - players_height
#            players_pos_y = box_pos_y + box_height 

            # Description box
            text_pos_x = box_pos_x
            text_pos_y = box_pos_y + title_height + marge_y
            text_width = box_width
            text_height = players_pos_y - title_pos_y - title_height - 2 * marge_y
            text_margin = int(marge_y / 2)
            
        else:
            try: 
                nb_lines = len(description.split("-----\n")[1].splitlines())
            except:
                nb_lines = 1
            # Description box
            text_pos_x = box_pos_x
            text_pos_y = box_pos_y
            text_width = box_width
            text_height = box_height +  self.res_y_16  - 2 * marge_y
            text_margin = int(marge_y / 2)

        # cut description for not full mode
        if not full:
            description = description.split("-----\n")[0]
        else:
            if "-----\n" in description:
                description = description.split("-----\n")[1]

        text_player = "{0} - {1} {2} {3}".format(min_max_players[0],
                                    min_max_players[1],
                                    self.lang.translate(f"players"),
                                    "par paire" if bool(min_max_players[2]) == True else "")
         
        if goodNbPlayers :
            color = self.colorset['description-bg']
        else:
            color = self.colorset['menu-warning']
            text_player = "==> {0} <==".format(text_player)            
           
        if color is not None:
            # New surface
            self.new_blit_rect(text_pos_x, text_pos_y, text_width, text_height, color, corners='All', \
                    border_radius=50, Alpha=192)
            if not full:
                self.new_blit_rect(title_pos_x, title_pos_y, title_width, title_height, color, corners='All', \
                        border_radius=50, Alpha=192)
                self.new_blit_rect(players_pos_x, players_pos_y, players_width, players_height, color, corners='All', \
                        border_radius=50, Alpha=192)

        if not full:
            # Print game's name
            height = int((int(self.res['x']) / 1920) * 50)
            font = self.font(self.defaultfontpath, height)
            game_name = self.lang.translate(f"{game.replace(' ', '_')}-name")
            if game_name == f"{game.replace(' ', '_')}-name":
                game_name = game
            if title and title != game:
                # A numbered favorite : its number with the name of its game
                game_name = f"{game_name}{title[len(game):]}"

            text = font.render(game_name, True, self.colorset['description-text'])
            self.blit(text, [title_pos_x + (title_width - font.size(game_name)[0]) / 2, \
                    title_pos_y + (title_height - font.size(game_name)[1]) / 2, title_width, title_height])

            # Display max player
            text = font.render(text_player, True, self.colorset['description-text'])
            self.blit(text, [players_pos_x + (players_width - font.size(text_player)[0]) / 2, \
                    players_pos_y + (players_height - font.size(text_player)[1]) / 2, players_width, players_height])

        if versionGame != '':
            self.blit_text(f'{self.lang.translate(f"Version")} {versionGame}', self.margin, \
                self.res['y'] * 1.05 / 30, self.res['x'] * 1.9 / 16, \
                self.res['y'] * 0.9 / 30, self.colorset['menu-text-black'], align='Left', margin=False)
                
        # Add description
        description = description.splitlines()
        height = int((int(self.res['x']) / 1920) * 25)
        indice = 85
        if(self.colorset.get('font') is None):
            font = self.font(f'{self.config.fontsDir}/FreeSansBold.ttf', height)
        else:
            font = self.font(self.colorset['font'], height)

        index = 0
        text_pos_y += 20 # Border radiue
        for line in description:
            if len(line)>indice :
                s = line[:indice].rfind(' ')
                k = line[:s].strip()
                nl = line[s:].strip()
                text = font.render(k, True, self.colorset['description-text'])
                self.blit(text, [text_pos_x + marge_x / 4, text_pos_y + text_margin / 2])
                text_pos_y += height + text_margin
                text = font.render(nl, True, self.colorset['description-text'])
            else:
                text = font.render(line, True, self.colorset['description-text'])
            self.blit(text, [text_pos_x + marge_x / 4, text_pos_y + text_margin / 2])
            text_pos_y += height + text_margin

        return pygame.Rect(box_pos_x, box_pos_y, box_width, box_height + 1)

    @with_look('options')
    def options_menu(self, game_options, game, number_of_players, versionGame = '', max_players = 12, favorite=False):
        '''
        Game options menu. favorite : options of a favorite game (screen Jeux favoris) : the
        buttons Back and Save only, Save returns the options
        '''
        # Buttons at the bottom : (zone, text, place)
        if favorite:
            footers = [('escape', 'back', 'escape'), ('continue', 'save', 'return')]
        else:
            footers = [('escape', 'back', 'escape'), ('save', 'save', 'refresh'), ('continue', 'continue', 'return')]
        self.logs.debug("Waiting for game options")

        # Show message on Raspydarts DMD
        self.dmd.send_text(self.lang.translate('game-options'), tempo=1)
        self.dmd.send_text(game.upper().replace('_', ' '))

        # List avaiables themes
        try:
            themes = [os.path.basename(f.path) for f in os.scandir(self.config.themes_dir) if f.is_dir() ]
        except:
            themes = []
        themes.append('default')

        teaming = False
        if number_of_players % 2 == 0:
            teaming = True

        nb_elements = 0
        # The last button at the bottom selected first (Continue)
        selected = len(footers)
        for option_name, option_value in game_options.items():
            if (option_name.endswith('Teaming') or option_name.endswith('optionteamscore')) \
                    and not teaming:
                continue
            if option_name == 'theme' and len(themes) == 0:
                continue
            nb_elements += 1

        selected += nb_elements

        refresh = True
        old_selection = None
        while True:
            # Display Background
            self.display_background()            
            
            try:
                min_max_players_per_game = self.config.get_value('NbOfPlayersPerGame', game.replace(" ", "_"))
            except:
                self.logs.error("[] No game with name '{0}' find in DefaultConfig['NbOfPlayersPerGame'] dict".format(game.replace(" ", "_")))
                min_max_players_per_game = [ 0, 0, False ]
                
            good_nb_players = (int(min_max_players_per_game[0]) <= number_of_players) and (number_of_players <= int(min_max_players_per_game[1]))
            player_in_pairs = bool(min_max_players_per_game[2])
            if player_in_pairs == True :
                if (number_of_players % 2) != 0 :
                    good_nb_players = False
    
            text_player = "{0} - {1} {2} {3}".format(min_max_players_per_game[0],
                                                     min_max_players_per_game[1],
                                                     self.lang.translate(f"players"),
                                                     "par paire" if bool(min_max_players_per_game[2]) == True else "")


            self.menu_header(f"{self.lang.translate('game-options')} {game.replace('_', ' ')} ({text_player})")
            

            #Display game description and game options
            game_desc_rect = self.game_description(game, True, min_max_players=min_max_players_per_game, goodNbPlayers=good_nb_players)

            click_zones = {}
            shortcuts = []
            cursor = {}
            options = {}
            values = []
            if QRCODE:
                self.qrcode.set_qrsize() # remet la taille par defaut au cas ou elle aurait changé dans un jeu
                self.qrcode.set_color('black','white')
                image_qrcode = self.draw_qrcode(game)
                self.display_qrcode(image_qrcode)
                del image_qrcode #libère la mémoire après l'affichage

            index = 1
            for option_name, option_value in game_options.items():
                text = self.translate_option(game,option_name)

                if (option_name.endswith('Teaming') or \
                        option_name.endswith('optionteamscore')) and not teaming:
                    continue
                if option_name == 'theme' and len(themes) == 0:
                    continue

                if isinstance(option_value, bool):
                    option_type = BTN_CHECK    # Boolean
                    value = False
                    if option_value is True:
                        value = True
                elif option_name == 'theme':
                    text = 'colorset'
                    option_type = BTN_DROPDOWN
                    values = [(theme, theme) for theme in themes]
                    value = option_value
                else:
                    option_type = BTN_VALUE    # free entry (Alphanum)
                    value = option_value

                shortcut = f'F{index}'
                options[index] = [value, option_type, option_name]

                click_zones[shortcut] = self.menu_item((index, nb_elements, selected)
                        , (shortcut, f'{text}', option_type, value), align='Left')
                shortcuts.append(shortcut)
                cursor[index] = shortcut
                index += 1

            # Arrow to go back and next
            for position, (zone, text, place) in enumerate(footers):
                click_zones[zone] = self.display_button(index + position == selected, text, special=place)

            if selected < nb_elements:
                selection = click_zones[f'F{selected}']
            elif index <= selected < index + len(footers):
                selection = click_zones[footers[selected - index][0]]
            else:
                selection = None

            if refresh:
                self.update_screen()
                refresh = False
            elif old_selection is None or selection is None or True:
                self.update_screen(rect_array=[click_zones[cz] for cz in click_zones])
            else:
                self.update_screen(rect_array=[old_selection, selection])

            key = self.rpi.listen_inputs(['num', 'fx', 'arrows'], \
                 ['BACKUPBUTTON', 'EXTRABUTTON', 'BTN_NEXTPLAYER', 'PLAYERBUTTON', 'GAMEBUTTON', 'return', \
                 'enter', 'escape', 'TOGGLEFULLSCREEN', 'single-click', 'space', 'backspace'],
                 events=[(self.wait_event_time, 'EVENT', 'wait')])

            # Input - mouse
            clicked = self.is_clicked(click_zones, key)

            if clicked:
                key = clicked
            else:
                key = str(key)

            # Navigation in menu (right and left too, in reading order : they ticked a box, as
            # validate does)
            selected = self.navigate(selected, key, nb_elements, len(footers), len(footers), left_right=True)

            if key in ESCAPE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 1):
                self.qrlogo = ''
                return 'escape'

            if not favorite and (key in SAVE_KEYS or (key in ENTER_KEYS and selected == nb_elements + 2)):
                self.config.set_game_config(game, game_options)
                self.config.write_file()
                self.message(['options-saved'], None, self.colorset['menu-text-black'], 'middle', 'big')
                refresh = True
                continue

            #if key in SAVE_KEYS + CONTINUE_KEYS or key == 'BTN_NEXTPLAYER' \
            if key in CONTINUE_KEYS and key != 'BTN_NEXTPLAYER' or (favorite and key in SAVE_KEYS) \
                    or (key in ENTER_KEYS and selected == nb_elements + len(footers)):
                self.game_options = game_options
                self.qrlogo = ''
                return game_options

            if key in shortcuts:
                selected = int(key.replace('F', ''))
                key = 'enter'

            if key in ENTER_KEYS or key == 'BTN_NEXTPLAYER':
                # Toggle on edit mode with Fx keys
                if options[selected][1] == BTN_CHECK:
                    if options[selected][0]:
                        game_options[options[selected][2]] = False
                    else:
                        game_options[options[selected][2]] = True
                elif options[selected][1] == BTN_DROPDOWN:
                    tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, values)
                    if tmp != 'escape':
                        game_options[options[selected][2]] = tmp
                    refresh = True
                elif options[selected][2] == 'xgrille':
                    values = [['4x4','4x4'],['6x6','6x6'],['8x8','8x8']]
                    tmp = self.dropdown(self.res['x'] * 6 / 16, 3 * self.res_y_16, values,navigate = game_options[options[selected][2]])
                    if tmp != 'escape':
                        game_options[options[selected][2]] = tmp
                    refresh = True

                else:
                    click_zone = click_zones[f'F{selected}']
                    if options[selected][2] == 'max_round':
                        min_value = 1
                        max_value = 99
                    elif options[selected][2] == 'Time':
                        min_value = 500
                        max_value = 10000
                    elif options[selected][2] == 'startingat':
                        min_value = 181
                        max_value = 10000
                    elif options[selected][2] == 'nb_segment':  
                        min_value = 1
                        max_value = 5
                    elif options[selected][2] == 'rouge':  
                        min_value = 6
                        max_value = 14
                    else:
                        min_value = 0
                        max_value = 500
                    translate = self.translate_option(game,options[selected][2])
                    tmp = self.input_value_item('number', '', min_value, max_value, text=translate,
                                                knob_start=game_options.get(options[selected][2]))

                    if tmp != 'escape':
                        game_options[options[selected][2]] = tmp

        old_selection = selection
        self.qrlogo = ''


    def menu_version(self, show):
        '''
        The version (V4.6) on the background of a menu : show_version: true (at the right, as
        always), or a block of its place and look ({x, y, width, height, color, font} : the
        text fills its box ; positions as the menus files measure them, section 4)
        '''
        if not show:
            return
        self.draw_version(self.menu_version_rect(show), show)

    def menu_version_rect(self, show):
        '''
        Box of the version of a menu (see menu_version) : the editor of the screens places it
        '''
        look = show if isinstance(show, dict) else {}
        units = cmenustyle.Units(self.screen.get_size(), self.menus().data.get('resolution'))
        width = int(units.length(look['width'], 'x')) if 'width' in look else self.res_x_16
        height = int(units.length(look['height'], 'y')) if 'height' in look else self.res_y_16
        pos_x = int(units.length(look['x'], 'x')) if 'x' in look else self.res['x'] - width
        pos_y = int(units.length(look['y'], 'y')) if 'y' in look else int(self.res['y'] * 3 / 4) - height
        return pygame.Rect(pos_x, pos_y, width, height)

    def draw_version(self, rect, show):
        '''
        The version (V4.6) filling this box, in the colour and font of the menu
        '''
        look = show if isinstance(show, dict) else {}
        color = self.menu_painter().color(look.get('color'), None) or self.colorset['menu-text-white']
        font = self.menu_painter().font_path(look.get('font'))
        self.blit_text(f"V{self.config.pyDartsVersion[0:3]}", rect.x, rect.y, rect.width, rect.height, tuple(color[:3]), dafont=font)

    def display_version(self):
        self.blit_text(self.config.pyDartsFullVersion, self.margin, \
            self.res['y'] * 1.05 / 30, self.res['x'] * 1.9 / 16, \
            self.res['y'] * 0.9 / 30, self.colorset['menu-text-black'], align='Left', margin=False)

    def display_rpi_version(self):
        '''
        Display version of raspydarts on top
        '''
        self.blit_text(self.config.rpi_version, self.res['x'] * 3 / 4, \
                self.res['y'] * 1.05 / 30, self.res['x'] / 4 - self.margin, \
                self.res['y'] * 0.9 / 30, self.colorset['menu-text-black'], align='Right', margin=False)

    def display_ips(self, big=False):
        '''
        Display ip address on top
        '''
        index = 0
        if big:
            for ip in self.ips:
                self.blit_text(ip[1], self.res['x'] * 12 / 16, self.res['y'] * (13 + index) / 16, \
                        self.res['x'] / 8, self.res_y_16, self.colorset['menu-text-white'], margin=False)
                index += 1
        else:
            ips = [ip[1] for ip in self.ips]
            self.blit_text(' / '.join(ips), self.res['x'] * 3 / 4, self.res['y'] * 2.05 / 30, \
                    self.res['x'] / 4 - self.margin, self.res['y'] * 0.9 / 30, self.colorset['menu-text-black'], \
                    align='Right', margin=False)
            self.blit_text(' / '.join(ips), 0, self.res['y'] * 2.05 / 30, \
                    self.res['x'] / 4 - self.margin, self.res['y'] * 0.9 / 30, self.colorset['menu-text-black'], \
                    align='Left', margin=False)

    def display_volume(self, backup):
        self.save_background()

        if self.sound_volume > 90:
            color = self.colorset['menu-ko']
        elif self.sound_volume > 70:
            color = self.colorset['menu-warning']
        else:
            color = self.colorset['menu-ok']

        rect = pygame.Rect(self.res_x / 4, self.res_y / 4, self.res_x / 2, self.res_y / 2)
        self.new_blit_rect2(rect, self.colorset['message-bg'])
        if self.sound_volume == 0:
            self.blit_text2('Mute', rect, color=color)
        else:
            self.blit_text2(self.sound_volume, rect, color=color)
        self.update_screen(rect=rect)

        pygame.time.wait(200)

        self.restore_background()
        self.reset_background()

    def display_records(self, data, record, game, options, current=False):
        '''
        Dsiplay records
        '''
        self.logs.debug(f"Displaying Hi score table for {game}, options : {options}")

        ratio = 1 / 2

        # Store number of columns to display
        rows = len(data)

        selected = 2

        while True:

            # Init
            click_zones = {}
            self.display_background()

            # Array title
            if current:
                txt = self.lang.translate('this-game-stats')
            else:
                txt = self.lang.translate('local-db-stats')

            self.display_row(1, 2 + rows, False, [(txt, 1)], ratio)
            self.display_row(2, 2 + rows, False, [(self.lang.translate('ranking'), 1 / 4), \
                    (self.lang.translate('Date'), 1 / 4), \
                    (self.lang.translate('Player'), 1 / 4), \
                    (self.lang.translate(record), 1 / 4)], ratio)

            index = 0
            for row in data:
                index += 1
                self.display_row(2 + index, 2 + rows, False, [(str(index), 1 / 4), \
                        (row[1], 1 / 4), (row[2], 1 / 4), ('%.2f' % (row[3]), 1 / 4)], ratio)

            # back to desktop and next
            click_zones['escape'] = self.display_button(1 == selected, 'back-to-menu', special='escape')
            click_zones['continue'] = self.display_button(2 == selected, 'continue', special='refresh')
            #click_zones['restart'] = self.display_button(3 == selected, 'restart', special='return')

            self.update_screen()
            # Wait for an input
            key_pressed = self.rpi.listen_inputs(['fx', 'arrows'], ['escape', 'enter', \
                    'TOGGLEFULLSCREEN', 'BACKUPBUTTON', 'GAMEBUTTON', 'single-click'])

            selected = self.navigate(selected, key_pressed, 0, 2, 2)
            # Analyse input (Mouse, keyboard and buttons)
            clicked = self.is_clicked(click_zones, key_pressed)
            if clicked:
                key_pressed = clicked

            if key_pressed in ESCAPE_KEYS or (key_pressed in ENTER_KEYS and selected == 1):
                return 'menu'

            #if key_pressed == 'restart' or (key_pressed in ENTER_KEYS and selected == 3):
            #    return 'startagain'

            if key_pressed in ENTER_KEYS + CONTINUE_KEYS and selected == 2:
                return 'continue'

    def new_player_line(self, pos_y, player_id, actual_player, nb_players, p_color=None, b_color=None, alive=True):
        '''
        This method fill background squares
        '''
        # Please comment to explain
        teaming_size = self.pn_size / 5
        score_size = self.box_width * 2
        # Player names' box
        if b_color is None:
            if player_id == actual_player:
                background_color = self.colorset['menu-alternate']
            else:
                background_color = self.colorset['menu-item-white']
        else:
            background_color = b_color

        if p_color is None:
            p_color = b_color

        if not alive:
            background_color = self.colorset['game-dead']
            box_background_color = self.colorset['game-dead']
        else:
            box_background_color = self.colorset['game-dead']

        # If teaming is enabled, display a colored square beside the player name
        if nb_players >= 10:
            color_line_height = self.margin
        else:
            color_line_height = int(self.margin * (1 + (10 - nb_players) * 0.5))
        firstname_height = self.line_height - color_line_height - self.margin - 2

        rect = pygame.Rect(self.margin, pos_y, self.pn_size - self.margin, color_line_height)
        self.new_blit_rect2(rect, p_color)

        rect.y += color_line_height + 2
        rect.height = firstname_height
        self.new_blit_rect2(rect, background_color)

        # All other boxes
        rect = pygame.Rect(self.margin + self.pn_size, pos_y, self.box_width - self.margin, self.line_height - self.margin)

        for index in range(0, int(self.config.get_value('SectionGlobals', 'nbcol')) + 1):
            rect.x = self.margin + self.pn_size + self.box_width * index
            self.new_blit_rect2(rect, box_background_color)

        # Score box
        rect = pygame.Rect(self.margin + self.pn_size + self.box_width * (int(self.config.get_value('SectionGlobals', 'nbcol')) + 1), pos_y, score_size - self.margin, self.line_height - self.margin)
        self.new_blit_rect2(rect, box_background_color)

    def new_headers(self, headers):
        '''
        This method display column headers
        '''
        y = self.position[0] - self.line_height - self.margin

        for index in range(0, int(self.config.get_value('SectionGlobals', 'nbcol')) + 1):
            rect = pygame.Rect(self.margin + self.pn_size + self.box_width * index, y, self.box_width - self.margin, self.line_height)

            self.new_blit_rect2(rect, self.colorset['game-table'], alpha=self.alpha + 10)
            self.blit_text2(str(headers[index][:5]), rect, self.colorset['game-headers'])


    def headers(self, headers):
        '''
        This method display column headers
        '''
        y = self.position[0] - self.line_height - self.margin

        for index in range(0, int(self.config.get_value('SectionGlobals', 'nbcol')) + 1):
            # Limit header to 3 char
            txt = str(headers[index][:3])
            scaled_text = self.scale_text(txt, self.box_width, self.line_height)
            font = self.font(self.defaultfontpath, scaled_text[0])
            # Render text
            text = font.render(txt, True, self.colorset['menu-text-black'])
            # Calculate place of text
            pos_x = int(self.margin + self.pn_size + self.box_width * index + scaled_text[1])
            pos_y = int(y + scaled_text[2])
            # Create BG rect
            self.blit_rect(self.margin + self.pn_size + self.box_width * index, y, self.box_width - self.margin, self.line_height, self.colorset['game-table'], False, False, self.alpha + 10)
            # Display text
            self.blit(text, [pos_x, pos_y])

    def end_of_set(self, data):
        '''
        End of set's screen
        '''
        pos_y = self.top_space
        height = (self.box_height - self.line_height - self.top_space - self.margin) / 2
        pos_y += height - self.margin

        # Display text container - if a color is set in colorset
        self.blit_rect(0, pos_y, self.res['x'], height, self.colorset['menu-ko'])
        self.blit_text(f"{self.lang.translate('end-of-set')} {data[0]}", 0, pos_y, self.res['x'], height, self.colorset['menu-text-black'])

    def end_of_game_text(self, display_logo=False):
        '''
        Display "End of game"
        '''
        height = (self.box_height - self.line_height - self.top_space - self.margin) / 2
        if display_logo:
            pos_y = self.res_y_16
            height = 2 * pos_y
        else:
            pos_y = self.res_y_16
            height = 2 * pos_y

        # Display text container - if a color is set in colorset
        self.blit_rect(0, pos_y, self.res['x'], height, self.colorset['menu-ko'])
        self.blit_text('end-of-game', 0, pos_y, self.res['x'], height, self.colorset['menu-text-black'])

        if len(self.end_of_game_winner) > 0:
            pos_y = self.res['y'] / 2 # middle
            if self.lang.translate('nowinner') == self.end_of_game_winner:
                self.blit_rect(0, pos_y , self.res['x'], height, self.colorset['menu-warning'])
            else:
                self.blit_rect(0, pos_y , self.res['x'], height, self.colorset['menu-ok'])
            self.blit_text(self.end_of_game_winner, 0, pos_y, self.res['x'], height, self.colorset['message-text'])
            self.end_ofgame_winner =''

    def is_true(self, var):
        '''
        Return true or false
        '''
        if var is True or var == 'True' or var == 1 or var == '1':
            return True
        return False

    
    def refresh_game_screen(self, players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player, text_on_logo=False, wait=False, onscreen_buttons=None, showScores=True, end_of_game=False, end_of_set=None, set_number=None, max_set=None):

        return self.new_refresh_game_screen(players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player, text_on_logo, wait, onscreen_buttons, showScores, end_of_game, end_of_set, set_number, max_set)

    def on_event(self, display, t_event, rect_array):
        count = 0
        online = []
        for index in range(1,6):
            online.append(self.file_class.get_full_filename(f'online{index}', 'images'))

        self.display = display
        index = 0
        while True:
            if t_event.is_set():
                for rect in rect_array:
                    self.blit(rect[0], (rect[1][0], rect[1][1]))
                    if index != 3:
                        self.display_image(online[index], rect[1][0], rect[1][1], width=rect[1][2], height=rect[1][3])
                    self.update_screen(rect[1])

                if index >= 3:
                    index = 0
                else:
                    index += 1
                t_event.clear()
            else:
                pygame.time.wait(25)

    def create_thread(self, rect_array=None):
        if self.thread is None and rect_array is not None and len(rect_array) > 0:
            index = 0
            for rect in rect_array:
                sub = self.screen.subsurface(rect)
                screenshot = pygame.Surface((rect[2], rect[3]))
                screenshot.blit(sub, (0, 0))

                self.rects.append((screenshot, rect))  # (x, y, w, h, data)
            self.thread = Thread(target=self.on_event, args=(self.display, self.t_event, self.rects))
            self.thread.setDaemon(True)
            self.thread.start()

    def refresh_scores(self, players, actual_player, refresh=True):
        # Get number of players
        nb_players = len(players)

        # Display headers

        if refresh:
            self.display_background()
        index = 0
        for player in players:
            if player.position is None:
                # Classical display
                position = self.position[index]
            else:
                # 1st dead at last position (Sudden death of High Score)
                position = self.position[player.position - 1]

            # Display all other info on the player line
            if index == actual_player:
                self.new_player_line(position, index, actual_player, nb_players, p_color=player.color, b_color=player.color, alive=player.alive)
                self.new_display_score(position, player.score, player.color)
            else:
                self.new_player_line(position, index, actual_player, nb_players, p_color=player.color, b_color=self.colorset['game-inactive'], alive=player.alive)
                self.new_display_score(position, player.score, self.colorset['menu-text-white'])

            # Display player's score
            # Displayer player name box
            self.display_player_name(position, index, actual_player, player.name)
            index += 1

        # Display Table Content
        rect = self.new_display_table_content(players, actual_player)
        if refresh:
            self.update_screen(rect)
            self.save_background()

    def new_refresh_game_screen(self, players, actual_round, max_round, remaining, nb_darts, logo, headers, actual_player, text_on_logo=False, wait=False, onscreen_buttons=None, showScores=True, end_of_game=False, end_of_set=None, set_number=None, max_set=None):

        '''
        Refresh in game screen
        '''
        # Get number of players
        nb_players = len(players)

        # Recalculate line height
        self.define_constants(nb_players)

        # Init click_zones
        click = None

        self.reset_background()

        game_background = f"background_{logo.replace(' ', '_').split('.')[0]}"
        game_background = self.file_class.get_full_filename(game_background, 'images')
        self.display_background(image=game_background, veil=self.colorset['game-bg'])
        if self.game_type == 'online' and self.t_event is not None:
            self.create_thread(rect_array=[(int(self.res_x / 2 - 110), self.margin + int(self.res_y / 5), int(self.res_y / 36), int(self.res_y / 36))])

        if not end_of_game and end_of_set is None:
            # Game options
            #
            # If some options are displayed, use compact mode for remaining darts
            OptDisplayed = self.new_display_game_options()
            #if OptDisplayed:
            # Rem Darts compact display
            self.display_darts(remaining, nb_darts, players[actual_player].color)

            game_h = int(self.res_y / 12)
            game_w = game_h
            game_x = int(self.res_x - 3 * (game_w + self.margin))
            game_y = self.margin + game_h

            # Display on-screen clickable buttons if requested
            if onscreen_buttons is True or self.is_true(self.config.get_value('SectionGlobals', 'onscreenbuttons')):
                click = self.onscreen_buttons()
        #
        # All players line by line
        #
        if showScores:
            self.new_headers(headers)
            self.refresh_scores(players, actual_player, refresh=False)

        self.new_display_round(players[actual_player], actual_round, max_round, set_number, max_set)
        self.new_display_logo(logo)

        self.save_background()
        self.update_screen()

        # manage end game menu
        if end_of_game:
            click = self.end_of_game_menu(logo)
        # Wait if requested
        elif wait:
            pygame.time.wait(wait)

        # Return Click
        return click


    def old_refresh_game_screen(self, players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player, text_on_logo=False, wait=False, onscreen_buttons=None, showScores=True, end_of_game=False, end_of_set=None, set_number=None, max_set=None):
        '''
        refresh In-game screen
        '''
        # Get number of players
        nb_players = len(players)

        # Recalculate line height
        self.define_constants(nb_players)

        # Init click_zones
        click = None

        # Clear
        #self.screen.fill(self.colorset['menu-item-white']

        # Background image
        self.display_background()

        if not end_of_game and end_of_set is None:
            # Game Logo (or optionnaly "Text On Logo")
            if not text_on_logo:
                self.display_logo(logo)
            else:
                self.text_on_logo(str(text_on_logo))
            #
            # Game options
            #
            # If some options are displayed, use compact mode for remaining darts
            OptDisplayed = self.display_game_options()
            #if OptDisplayed:
                # Rem Darts compact display
            self.display_rem_darts_compact(RemDarts, nb_darts)
            #else:
                # Rem Darts normal :)
            #    self.display_rem_darts(RemDarts, nb_darts)

            # Display on-screen clickable buttons if requested
            if onscreen_buttons is True or self.is_true(self.config.get_value('SectionGlobals', 'onscreenbuttons')):
                click = self.onscreen_buttons()
        #
        # Rounds
        #
        self.display_round(actual_round, max_round, set_number, max_set)

        #
        # All players line by line
        #
        if showScores:
            save = self.config.get_value('SectionGlobals', 'onscreenbuttons')
            if end_of_game:
                # Force onscreenbuttons for available space to print buttons
                self.config.set_value('SectionGlobals', 'onscreenbuttons', True)
                self.define_constants(nb_players)

            index = 0
            for player in players:
                # Displayer player name box
                self.display_player_name(self.position[index], index, actual_player, player.name)
                # Display all other info on the player line
                if index == actual_player:
                    self.player_line(self.position[index], index, actual_player, nb_players, color=player.color, alive=player.alive)
                else:
                    self.player_line(self.position[index], index, actual_player, nb_players, color=self.colorset['game-inactive'], alive=player.alive)
                # Display player's score
                self.display_score(self.position[index], player.score)
                index += 1
            # Display headers
            self.headers(headers)
            # Display Table Content
            self.display_table_content(players)

            # Restore onscreenbuttons
            self.config.set_value('SectionGlobals', 'onscreenbuttons', save)

        # refresh !
        self.update_screen()

        # manage end game menu
        if end_of_game:
            click = self.end_of_game_menu(logo)
        # Wait if requested
        elif wait:
            pygame.time.wait(wait)
        # Return Click
        return [click]

    def end_of_game_menu(self, logo=None, stat_button=True):
        '''
        Manage End game menu
        '''
        if logo is not None:
            self.display_logo(logo)
        self.end_of_game_text(logo is not None)
        self.rpi.light_toys(['LIGHT_NEXTPLAYER', 'LIGHT_BACK', 'LIGHT_VALIDATE', 'LIGHT_NAVIGATE'], True)

        selected = 2
        while True:
            click_zones = {}
            if stat_button:
                stats = 1
                click_zones['stats'] = self.display_button(selected == 1, 'statistics', special='escape')
            else:
                stats = 0

            click_zones['continue'] = self.display_button(selected == 1 + stats, 'back-to-menu', special='refresh')
            if self.game_type != 'online':
                online = 1
                click_zones['restart'] = self.display_button(selected == 2 + stats, 'restart', special='return')
            else:
                online = 0


            self.update_screen()

            key_pressed = self.rpi.listen_inputs(['arrows'], ['escape', 'enter', 'TOGGLEFULLSCREEN', 'BACKUPBUTTON', 'GAMEBUTTON', 'single-click'])

            selected = self.navigate(selected, key_pressed, 0, 1 + online + stats, 2)

            # Analyse input (Mouse, keyboard and buttons)
            clicked = self.is_clicked(click_zones, key_pressed)

            if clicked:
                key_pressed = clicked

            if key_pressed == 'stats' or (key_pressed in ENTER_KEYS and selected == 1 and stat_button):
                return 'stats'

            if key_pressed == 'restart' or (key_pressed in ENTER_KEYS and selected == 2 + stats):
                return 'startagain'

            if key_pressed in CONTINUE_KEYS + ESCAPE_KEYS + BACK_KEYS or (key_pressed in ENTER_KEYS and selected == 1 + stats):
                return 'continue'

            if key_pressed in DIRECTION_KEYS:
                self.update_screen(rect_array = click_zones.values())
        # Return Clickable zones
        return click_zones

    def new_display_logo(self, logo=False):
        '''
        Display an image on the middle top of the screen
        '''
        pos_x = int(self.res_x / 2 - self.res_x / 6)
        pos_y = self.margin
        height = int(self.res_y / 5)
        width = int(self.res_x / 3)

        #self.display_image(self.file_class.get_full_filename(f'logos_menu/{logo}', 'images'), pos_x, pos_y, width, height, Scale=False, center_x=True)
        name = logo.replace('_', ' ').split('.')[0]
        self.blit_text(name, pos_x, pos_y, width, height, self.colorset['game-title1'], margin=False)
        self.blit_text(name, pos_x, pos_y, width, height, self.colorset['game-title2'])
        
        gt_height = int(self.res_y / 36)

        if self.colorset['game-type'] is not None:
            if self.game_type == 'online':
                self.display_image(self.online_icon, self.res_x / 2 - 110, pos_y + height, width=gt_height, height=gt_height)
            self.blit_text(f"{self.game_type} game", pos_x, pos_y + height, width, gt_height, color=self.colorset['game-type'], align='Center', valign='top', margin=False)

    def new_display_players(self, players, actual_player, end_of_game=False):
        
        player_height = int(self.res_y / 8)
        player_width = int(self.res_x / max(2 * len(players), 6))
        players_x = int(self.res_x / 4 + (self.res_x / 2 - player_width * len(players)) / 2)
        if end_of_game:
            player_y = self.res_y - 2 * player_height - self.margin
        else:
            player_y = self.res_y - player_height - self.margin
        heading_height = int(self.res_y / 24)

        heading_color = self.colorset['game-headers']
        player_color = self.colorset['game-alt-headers']

        index = 0
        for player in players:
            color = player.color
            name = player.name
            score = player.score
            player_x = players_x + index * player_width

            if index != actual_player:
                if index < actual_player:
                    player_x -= int(player_width / 2)
                else:
                    player_x += int(player_width / 2)

                self.blit_rect(player_x, player_y, player_width, heading_height, heading_color)
                self.blit_rect(player_x, player_y + heading_height, player_width, player_height - heading_height, player_color)

                if self.colorset['game-bg'] is not None:
                    pygame.draw.line(self.screen, self.colorset['game-bg'], (player_x, player_y + heading_height), (player_x + player_width, player_y + heading_height), 2)
                    pygame.draw.line(self.screen, self.colorset['game-bg'], (player_x, player_y), (player_x, player_y + player_height - 1), 2)
                    pygame.draw.line(self.screen, self.colorset['game-bg'], (player_x + player_width, player_y), (player_x + player_width, player_y + player_height), 2)

                if index < actual_player:
                    align='Left'
                    icon_align='Right'
                else:
                    icon_align='Left'
                    align='Right'
                skull_icon = self.file_class.get_full_filename('killer_skull', 'images')
                pygame.draw.line(self.screen, color, (player_x, player_y), (player_x + player_width, player_y), self.margin * 2)
                self.blit_text(name, player_x, player_y - self.margin * 2, player_width, heading_height + self.margin * 2, color=player_color, align=align, valign='Bottom')
                self.blit_text(score, player_x, player_y + heading_height, player_width, player_height - heading_height, color=heading_color, align=align)
                if not player.alive:
                    if index < actual_player:
                        self.display_image(skull_icon, player_x + player_width - (player_height - heading_height), player_y + heading_height, player_width, player_height - heading_height)
                    else:
                        self.display_image(skull_icon, player_x, player_y + heading_height, player_width, player_height - heading_height)
            else:
                # For actual player's infos
                actual_color = color
                actual_x = player_x - int(player_width / 2)
                actual_name = name
                actual_score = score
            index += 1

        # Actual player and his score
        player_x = int(self.res_x / 4 + (self.res_x / 2 - player_width * len(players)) / 2) + actual_player * player_width - (player_width / 2)
        player_y -= self.margin
        player_height += self.margin * 2
        player_width *= 2
        dart_icon_size = player_height - heading_height - self.margin * 2
        dart_icon = self.file_class.get_full_filename('dart_icon', 'images')
        self.blit_rect(player_x, player_y, player_width, heading_height, actual_color)
        self.blit_rect(player_x, player_y + heading_height, player_width, player_height - heading_height, actual_color)
        if self.colorset['game-bg'] is not None:
            pygame.draw.line(self.screen, self.colorset['game-bg'], (player_x, player_y + heading_height), (player_x + player_width, player_y + heading_height), 2)
            pygame.draw.line(self.screen, self.colorset['game-bg'], (player_x, player_y), (player_x, player_y + player_height), 2)
            pygame.draw.line(self.screen, self.colorset['game-bg'], (player_x + player_width, player_y), (player_x + player_width, player_y + player_height), 2)
        self.display_image(dart_icon, player_x + self.margin, player_y + heading_height + self.margin, width=dart_icon_size, height=dart_icon_size)
        if self.colorset['game-bg'] is not None:
            self.blit_text(actual_name, player_x, player_y - self.margin, player_width, heading_height + self.margin * 2, color=self.colorset['game-bg'], align='Center')
        else:
            self.blit_text(actual_name, player_x, player_y - self.margin, player_width, heading_height + self.margin * 2, color=(0, 0, 0), align='Center')

        self.blit_text(actual_score, player_x, player_y + heading_height, player_width, player_height - heading_height, color=self.colorset['game-score'], align='Right')

    def display_logo(self, logoimage=False):
        '''
        Display an image on the middle top of the screen
        '''
        # Local Constants
        pos_x = self.pn_size + self.margin
        pos_y = self.top_space
        width = self.box_width * (int(self.config.get_value('SectionGlobals', 'nbcol')) + 1) - self.margin
        height = self.box_height - self.line_height - self.top_space - self.margin
        # Display rect container - if a color is set in colorset
        self.blit_rect(pos_x, pos_y, width, height, self.colorset['bg-LOGO'])
        # Display LOGO
        self.display_image(self.file_class.get_full_filename(f'logos_menu/{logoimage}', 'images'), pos_x, pos_y, width, height, Scale=False, center_x=True)

    def text_on_logo(self, txt, wait=False, update=False):
        '''
        Display text instead of game LOGO
        '''
        # Local Constants
        pos_x = self.pn_size + self.margin
        pos_y = self.top_space
        width = self.box_width * (int(self.config.get_value('SectionGlobals', 'nbcol')) + 1) - self.margin
        height = self.box_height - self.line_height - self.top_space - self.margin
        border_color = self.colorset['menu-border']
        border_size = int(self.box_width / 20)
        text_color = self.colorset['menu-text-black']
        scaled_text = self.scale_text(txt, width, height)
        font = self.font(self.defaultfontpath, scaled_text[0])
        # Display rect container
        self.blit_rect(pos_x, pos_y, width, height, self.colorset['bg-LOGO'], border_size, border_color)
        # Render text
        text = font.render(txt, True, text_color)
        # Text location
        text_x = pos_x + scaled_text[1]
        text_y = pos_y + scaled_text[2]
        # Blit text
        self.blit(text, [text_x, text_y])
        if update:
            self.update_screen()    # refresh screen if requested
        if wait:
            pygame.time.wait(wait)    # Wait if requested

    def display_background(self, image=None, rect=None, display_version=False, veil=None):
        '''
        Display background, under a veil of this color if given (game screens)
        '''
        if self.current_look is not None and image is None and rect is None and veil is None \
                and self.game_background is None:
            # Screen whose look comes from the files : their background, if they give one
            block = self.menus().menu(self.current_look).get('background')
            if block is not None:
                block = cmenustyle.merge({'fit': 'cover'}, block) if isinstance(block, dict) else block
                self.screen.fill((0, 0, 0))
                self.blit(self.menu_painter().background(block, self.screen.get_size()), (0, 0))
                self.pristine_background = None
                return
        if image is True:
            image = self.background
        elif image is not None:
            image = self.file_class.get_full_filename(image, 'images')

        # Background already displayed under this veil : copied as it was, without drawing the
        # background first (a full screen blit, 9 to 16 ms on a Pi 3, covered right after)
        if veil and rect is None and not display_version:
            if self.game_background is not None and image is None:
                shown = None
            elif self.colorset['bg-global']:
                shown = ('fill', tuple(self.colorset['bg-global']))
            elif image is not None or self.background is not None:
                shown = ('image', image if image is not None else self.background)
            else:
                shown = None
            tinted = self.tinted_backgrounds.get((shown, tuple(veil), self.alpha))
            if shown is not None and tinted is not None:
                self.screen.blit(tinted, (0, 0))
                self.pristine_background = None
                return

        # The background alone is on the screen (see blit_rect) : said at the end
        pristine = None
        if self.colorset['bg-global']:
            self.screen.fill(self.colorset['bg-global'])
            pristine = ('fill', tuple(self.colorset['bg-global']))
        # If there is no background color in used colorset, try to use image
        if self.game_background is not None and image is None:
            self.restore_background()
            pristine = None

        elif not self.colorset['bg-global'] and (self.background is not None or image is not None):
            if image is None:
                image = self.background

            if rect is None:
                self.display_image(image, 0, 0, self.res['x'], self.res['y'], Scale=True, Opaque=True)
                pristine = None if display_version else ('image', image)
            else:
                self.display_image(image, 0, 0, self.res['x'], self.res['y'], Scale=True, rect=rect, Opaque=True)

            if display_version :
                width = self.res_x_16
                height = self.res_y_16
                pos_x = self.res['x'] - width
                pos_y = int(self.res['y'] * 3 / 4) - height
                version = f"V{self.config.pyDartsVersion[0:3]}"

                self.blit_text(version, pos_x , pos_y, width, height, self.colorset['menu-text-white'])

        self.pristine_background = pristine
        if veil:
            self.blit_rect(0, 0, self.res_x, self.res_y, veil)

    def scale_image(self, image, scale=True, width=0, height=0):
        '''
        Method to scale an image to fit on given size
        '''
        image_size = image.get_rect().size
        image_prop = float(image_size[0]) / float(image_size[1])

        if width > 0 and height > 0 and scale:
            # Force to given size
            image_width = width
            image_height = height

        elif not scale and int(width / image_prop) <= height:
            # Else, try first to fit into width
            image_width = width
            image_height = int(width / image_prop)

        elif not scale:
            # If it doesnt fit, fit to height
            image_width = int(height * image_prop)
            image_height = height

        # Scale to correct size
        return (pygame.transform.scale(image, (image_width, image_height)), (image_width, image_height))

    def opaque_to_screen_format(self, image):
        '''
        An image without any transparent pixel (backgrounds, photos...) is blitted much
        faster in the format of the screen than with an alpha channel
        '''
        # Bits set for the pixels whose alpha is above 254 (pygame.mask, not surfarray :
        # numpy is not loaded, see raspydarts.py)
        mask = pygame.mask.from_surface(image, 254)
        if mask.count() == image.get_width() * image.get_height():
            return image.convert()
        return image

    #@debug
    def display_image(self, imagepath, pos_x, pos_y, width=0, height=0, Scale=False, center_x=False, center_y=False, rect=None, Screen=None, change_colors=None, enabledImage=True, UseCache=True, Opaque=False):
        '''
        Scale and display an image (Opaque : its transparent pixels on black, for the backgrounds)
        '''
        if imagepath is None:
            return

        # Cache is cleaned when resolution changed
        # Store in cache for Scate True/False and width/height (surface size to blit
        image_cache = f'{imagepath}-{Scale}-{width}-{height}-{enabledImage}-{change_colors}-{Opaque}'

        if image_cache not in self.imagecache or UseCache is False:
            try:
                self.logs.debug(f"Inserting image into cache {imagepath} ({image_cache})")
                opaque = False
                if enabledImage:
                    # Load. Without alpha channel nor transparent color (JPEG...), the image is
                    # opaque : nothing to check (checking every pixel took 210 ms for a background)
                    loaded_image = pygame.image.load(imagepath)
                    opaque = not loaded_image.get_flags() & pygame.SRCALPHA and loaded_image.get_colorkey() is None
                    loaded_image = loaded_image.convert() if opaque else loaded_image.convert_alpha()
                else:
                    loaded_image_PIL = Image.open(imagepath).convert('LA').convert('RGBA')
                    loaded_image = pygame.image.fromstring(
                                        loaded_image_PIL.tobytes(),
                                        loaded_image_PIL.size,
                                        loaded_image_PIL.mode).convert_alpha()

                if change_colors is not None:
                    image_pixel_array = pygame.PixelArray(loaded_image)
                    for change in change_colors:
                        image_pixel_array.replace(change[0], change[1])
                    # Unlocks the image
                    del image_pixel_array
        
                # Scale
                scaled = self.scale_image(loaded_image, scale=Scale, width=int(width), height=int(height))
                if opaque:
                    pass
                elif Opaque:
                    # Nothing to see under a background : a few transparent pixels (2 in a
                    # theme's background) made it blended at each display, 16 ms instead of 9
                    flat = pygame.Surface(scaled[0].get_size(), 0, self.screen)
                    flat.fill((0, 0, 0))
                    flat.blit(scaled[0], (0, 0))
                    scaled = (flat, scaled[1])
                else:
                    scaled = (self.opaque_to_screen_format(scaled[0]), scaled[1])
                # then store image + size
                if UseCache:
                    self.imagecache[image_cache] = scaled

            except Exception as e:
                self.logs.warning(f"Unable to load image {imagepath}. Error was {e}.")
                return False

            self.logs.debug(f"{len(self.imagecache)} elements in cache")
        scaled_image = self.imagecache[image_cache][0]
        scaled_width = self.imagecache[image_cache][1][0]
        scaled_height = self.imagecache[image_cache][1][1]

        # Compute posiion
        if center_x:
            pos_x = int(pos_x + (width - scaled_width) / 2)
        else:
            pos_x = pos_x
        if center_y:
            pos_y = int(pos_y + (height - scaled_height) / 2)
        else:
            pos_y = pos_y

        if Screen is None:
            self.blit(scaled_image, (pos_x, pos_y), area=rect)
        else:
            self.blit_screen(scaled_image, (pos_x, pos_y), area=rect)

        return (scaled_width, scaled_height)

    def theme_choices(self):
        '''
        The themes : clear, and the folders of ~/.raspydarts/themes
        '''
        try:
            themes = sorted(entry.name for entry in os.scandir(self.config.themes_dir) if entry.is_dir())
        except OSError:
            themes = []
        return [('clear', 'clear')] + [(theme, theme) for theme in themes if theme != 'clear']

    def font_choices(self):
        '''
        The fonts : the one the theme asks for, if it does, then those of the game and of
        ~/.raspydarts/fonts
        '''
        choices = []
        for folder in ('fonts', f'{self.config.user_dir}/fonts'):
            if os.path.isdir(folder):
                choices += [(name, name[:-4]) for name in os.listdir(folder) if name.endswith('.ttf')]
        choices = sorted(set(choices))
        if self.theme_font:
            name = os.path.basename(self.theme_font)
            label = f"{os.path.splitext(name)[0]} ({self.lang.translate('colorset').lower()})"
            choices = [(name, label)] + [choice for choice in choices if choice[0] != name]
        return choices

    def apply_look(self, theme=None, font=None):
        '''
        A theme or a font chosen (Modifier les écrans) : written, and shown at once on every
        screen (the menus of the theme read again)
        '''
        globals_ = self.config.config['SectionGlobals']
        if theme is not None:
            globals_['colorset'] = theme
        if font is not None:
            globals_['font'] = font
        self.config.write_file()
        self.file_class.reset_theme(globals_['colorset'])
        self.init_colorset()
        self.menus_read = None
        self.apply_font()

    def apply_font(self):
        '''
        The font of the game (Personnalisation du jeu > Général > Police) used at once on every
        screen : after the font of the theme (init_colorset), as at the start ; the menus drawn
        with the former one forgotten (kept drawn, they kept it until a game)
        '''
        self.define_constants()
        self.use_chosen_font()
        self.menu_backgrounds.clear()
        self.menu_composites.clear()
        # The drawer of the styled menus keeps its buttons drawn too
        self.painter = None
        self.logs.info(f"Font of the game : {self.defaultfontpath}")

    def define_constants(self, nb_players=None, Font=None):
        '''
        Define and eventually refresh some constants (most of them depends of user resolution)
        '''
        # Basic space
        self.margin = int(self.res['y'] / 200)
        # space at the top side of the screen
        self.top_space = self.margin
        # Define bottom space
        if self.is_true(self.config.get_value('SectionGlobals', 'onscreenbuttons')):
            self.bottomspace = self.margin*32
        else:
            self.bottomspace = self.margin
        # Space on left side of the screen
        self.leftspace = int(self.res['x'] / 8)
        # Header for in-game screen boxes
        self.box_headers = int(self.res['y'] / 25)
        self.box_height = int(self.res['y'] / 2.5)
        # Nb col + 1 bull + 4 unit for player name and score
        self.box_width = int(self.res['x'] / (int(self.config.get_value('SectionGlobals', 'nbcol')) + 5))
        # Transparency
        self.alpha = 210
        self.alpha2 = 168
        # Default font path
        if Font is None:
            try :    # Already define
                self.defaultfontpath = self.defaultfontpath
            except :    # 1st define
                self.defaultfontpath = self.file_class.get_full_filename('MaPolice', 'fonts')
        else:
            self.defaultfontpath = self.font_file(Font) or self.defaultfontpath

        # Animation time (in ms)
        self.animation = 5
        ###### HEIGHT
        # All this sh** depends of the nb of players
        if nb_players:
            # The size of the top and bottom part of the screen
            self.screen_top = self.box_height - self.box_headers - self.top_space
            self.screen_bottom = self.res['y'] - self.screen_top - self.bottomspace
            # Max line_height is restrained to the space when 3 players plays (+ 1 header)
            max_line_height = int(self.screen_bottom / 4)
            # Calculate line_height
            # Screen size minus the header size, divided by number of players + 1 header
            self.line_height = min(int(self.screen_bottom / (nb_players + 1)), max_line_height)
            # Define Y position of each line for each player
            self.position = []
            for p in range(0, nb_players):
                positemp = int(self.res['y'] - self.bottomspace - ((nb_players - p) * (self.line_height)))
                self.position.append(positemp)

        ###### WIDTH (X Axis)
        # Player name box width
        self.pn_size = self.box_width * 2
        # Width of an in-game column
        self.colwidth = self.box_width

        ###### SCREEN PROPORTIONS
        # Proportion between screen Height and Width
        self.screen_proportions = float(float(self.res['x']) / float(self.res['y']))
        # Limit of proportion before considering the screen as vertical display
        self.prop_limit = 1

    def display_player_name(self, pos_y, ident, actual_player, playername=None):
        '''
        Display name of the player if given, Player X otherwise
        '''
        if playername is None:
            playername = 'Player ' + str(ident)
        if actual_player == ident:
            txtcolor = self.colorset['menu-text-white']
        else:
            txtcolor = self.colorset['menu-text-black']
        #  Player name size depends of player name number of char (dynamic size)
        scaled_text = self.scale_text(playername, self.pn_size - 2 * self.margin, self.line_height)
        font = self.font(self.defaultfontpath, scaled_text[0])
        # Render the text. "True" means anti-aliased text.
        pos_x = self.margin * 2 + scaled_text[1]
        pos_y = pos_y + scaled_text[2]
        text = font.render(playername, True, txtcolor)
        self.blit(text, [pos_x, pos_y])

    def new_display_table_content(self, players, actual_player):
        '''
        Fill-in table With DISPLAY-LEDS func
        '''
        index = 0
        min_x = self.res['x']
        min_y = self.res['y']
        max_x = 0
        max_y = 0

        for player in players:
            if player.position is None:
                # Classical display
                position = self.position[index]
            else:
                # 1st dead at last position (Sudden death of High Score)
                position = self.position[player.position - 1]

            if index == actual_player:
                color = player.color
            elif player.alive:
                color = self.colorset['game-table']
            else:
                color = self.colorset['game-dead']

            for column, value in enumerate(player.columns):
                pos_x = min_x
                pos_y = min_y
                width = max_x
                height = max_y
                if len(value) == 3 and value[2] is not None:
                    color = self.colorset[value[2]]

                if value[1] == 'image' and value[0] is not None:    # Maybe you want to put images in the table?
                    pos_x, pos_y, width, height = self.display_leds_image(position, value[0], column)
                elif value[1] == 'leds':    # Or you want to display leds style?
                    pos_x, pos_y, width, height = self.led_box2(position, int(value[0]), column, player.color)
                elif value[1] == 'int' and value[0] != '':
                    if value[0] != '' and int(value[0]) > 100:
                        pos_x, pos_y, width, height = self.new_text_box(position, str(int(value[0])), column, color)
                    else:
                        pos_x, pos_y, width, height = self.new_text_box(position, str(value[0]).replace('.0', ''), column, color)
                elif value[1] == 'str' and value[0] != '':
                    pos_x, pos_y, width, height = self.new_text_box(position, value[0], column, color)
                elif value[0] is not None and value[0] != '':    # Or fallback to default, it displays a string or int
                    pos_x, pos_y, width, height = self.new_text_box(position, value[0], column, color)

                if pos_x < min_x:
                    min_x = pos_x
                    max_x = pos_x + width
                if pos_y < min_y :
                    min_y = pos_y
                    max_y = pos_y + height
            index += 1

        return (min_x, min_y, max_x, max_y)

    def display_table_content(self, players, wait=False):
        '''
        Fill-in table With DISPLAY-LEDS func
        '''
        index = 0
        for player in players:
            for column, value in enumerate(player.columns):
                if len(value) == 3:
                    color = value[2]
                else:
                    color = None
                if value[1] == 'image':    # Maybe you want to put images in the table?
                    self.display_leds_image(self.position[index], value[0], column)
                elif value[1] == 'leds':    # Or you want to display leds style?
                    self.led_box2(self.position[index], int(value[0]), column, list(self.colorset)[player.ident])
                elif value[1] == 'int' and value[0] != '':
                    if value[0] != '' and int(value[0]) > 100:
                        self.text_box(self.position[index], str(int(value[0])), column, color)
                    else:
                        self.text_box(self.position[index], str(value[0]).replace('.0', ''), column, color)
                elif value[1] == 'str' and value[0] != '':
                    self.text_box(self.position[index], value[0], column, color)
                elif value[0] != '' :    # Or fallback to default, it displays a string or int
                    self.text_box(self.position[index], value[0], column, color)
                if wait:
                    pygame.time.wait(self.animation)
            index += 1

    def led_box(self, pos_y, nb_leds, column, color=None):
        '''
        Graphical representation of a number in the box, from 0 to 3
        '''
        # 3 leds max
        #
        pos_x = int(column * self.box_width + self.pn_size + self.margin)
        end_x = int(column * self.box_width + self.box_width + self.pn_size - self.margin / 4)
        end_y = int(pos_y + self.line_height - self.margin * 2)
        if color is None:
            color = self.colorset['menu-text-black']
        else:
            color = self.colorset[color]
        BB = int(self.res['y'] / 130)
        if nb_leds == 1:
            pygame.draw.line(self.screen, color, [pos_x, pos_y + self.margin], [end_x, end_y], BB)
        elif nb_leds == 2:
            pygame.draw.line(self.screen, color, [pos_x, pos_y + self.margin], [end_x, end_y], BB)
            pygame.draw.line(self.screen, color, [pos_x, end_y], [end_x, pos_y + self.margin], BB)
        elif nb_leds == 3:
            self.blit_rect(self.margin + self.pn_size + self.box_width * column, pos_y, self.box_width - self.margin,
                          self.line_height - self.margin, color)

    def led_box2(self, pos_y, nb_leds, column, color=None):
        '''
        graphical representation of a number in the box, from 0 to 3
        '''
        # 3 leds max
        #
        if color is None:
            color = self.colorset['menu-ok']
        elif type(color) is not tuple:
            color = self.colorset[color]

        height = int((self.line_height - self.margin) * nb_leds / 3) + 1
        if nb_leds > 0:
            self.blit_rect(self.margin + self.pn_size + self.box_width * column
                , pos_y + self.line_height - self.margin - height
                , self.box_width - self.margin, height
                , color)

        return self.margin + self.pn_size + self.box_width * column \
            , pos_y + self.line_height - self.margin - height \
            , self.box_width - self.margin, height

    def led_box3(self, pos_y, nb_leds, column, color=None):
        '''
        graphical representation of a number in the box, from 0 to 3
        '''
        color = self.colorset['menu-item-black']
        height = int((self.line_height - self.margin) * nb_leds / 3) + 1
        if nb_leds > 0:
            self.blit_rect(self.margin + self.pn_size + self.box_width * column
                , pos_y + self.line_height - self.margin - height
                , self.box_width - self.margin, height
                , color, Alpha=255)

    def new_text_box(self, pos_y, text, column, color=None):
        '''
        Display text or integer in the given column
        '''
        # keep max 4 char
        # text = str(text[:4])
        if text.endswith('.'):
            text = str(text[:-1])

        # Asign default color if required
        if color is None: color = self.colorset['game-text']

        pos_x = column * self.box_width + self.pn_size
        # Write text in box
        self.blit_text(text, pos_x, pos_y, self.box_width, self.line_height, color)

        return pos_x, pos_y, self.box_width, self.line_height

    def text_box(self, pos_y, text, column, color=None):
        '''
        Display text or integer in the given column
        '''
        # keep max 4 char
        text = str(text[:4])
        if text.endswith('.'):
            text = str(text[:3])

        # Asign default color if required
        if color is None: color = 'menu-text-black'

        # Write text in box
        scaled_text = self.scale_text(text, self.box_width - self.margin * 2, self.line_height - self.margin * 2)
        font = self.font(self.defaultfontpath, scaled_text[0])
        text = font.render(text, True, self.colorset[color])
        pos_x = column * self.box_width + self.pn_size + self.margin * 2 + scaled_text[1]

        self.blit(text, [pos_x, pos_y + scaled_text[2]])

    def display_leds_image(self, pos_y, image, column):
        '''
        Display an image in a specified column of a given player
        '''
        #
        height = int(self.line_height - self.margin * 3)
        width = int(min(self.box_width - self.margin * 3, height))
        #
        pos_x = int(column * self.box_width + self.pn_size + self.margin + (self.box_width - width) / 2)
        pos_y = int(pos_y + self.margin)
        #
        imagefile = self.file_class.get_full_filename(f'{image}', 'images')
        self.display_image(imagefile, pos_x, pos_y, width, height, False, True, True)

        return pos_x, pos_y, width, height

    def new_display_score(self, pos_y, txt, color):
        '''
        Display score for given player
        '''
        txt = str(txt).replace('.0', '')
        pos_x = int(self.pn_size + (int(self.config.get_value('SectionGlobals', 'nbcol')) + 1) * self.box_width)
        score_size = int(self.res['x'] / 5)

        self.blit_text(txt, pos_x, pos_y, score_size, self.line_height, color)


    def display_score(self, pos_y, txt):
        '''
        Display score for given player
        '''
        txt = str(txt).replace('.0','')
        score_size = int(self.res['x'] / 5)
        # self.box_width = int(self.res['x'] / 11.7)
        #
        pos_x = int(self.pn_size + (int(self.config.get_value('SectionGlobals', 'nbcol')) + 1) * self.box_width)
        scaled_text = self.scale_text(txt, score_size - self.margin * 2, self.line_height - self.margin * 2)
        font = self.font(self.defaultfontpath, scaled_text[0])
        text = font.render(txt, True, self.colorset['menu-text-black'])
        self.blit(text, [pos_x + self.margin * 2 + scaled_text[1], pos_y + scaled_text[2]])

    def display_darts(self, remaining, nb_darts, color, image='dart_icon'):
        '''
        Display remaining darts
        '''
        pos_y = self.margin + int(self.res_y / 96)
        height = int(self.res_y / 12)
        width = height
        pos_x = int(self.res_x - nb_darts * (width + 2 * self.margin))  

        for dart in range(1, nb_darts + 1):
            if dart <= remaining:
                self.display_image(self.file_class.get_full_filename(image, 'images'), pos_x, pos_y, width, height, Scale=False, center_x=True, change_colors=[((0, 0, 0), color)])
            elif self.colorset['game-darts'] is not None:
                self.display_image(self.file_class.get_full_filename(image, 'images'), pos_x, pos_y, width, height, Scale=False, center_x=True, change_colors=[((0, 0, 0), self.colorset['game-darts'])])
            pos_x += width + 2 * self.margin

    def new_display_game_options(self):
        '''
        Display game's options
        '''
        pos_y = self.margin + int(self.res_y / 48) + int(self.res_y / 12)
        height = int(self.res_y / 36)
        width = int(self.res_y / 6)
        width = int(self.res_y / 2)

        pos_x = self.res_x - width - self.margin
        game = self.selectedgame.replace(' ', '_')

        if self.colorset['game-option'] is not None:
            # Display options one by one
            for option, value in self.game_options.items():
                if option == 'theme':
                    continue
                if option == 'Time':
                    continue
                if value == '0' or value is False:
                    continue 
                txt_option = self.translate_option(game, option)

                if value is True:
                    self.blit_text(f'{txt_option}', pos_x, pos_y, width, height, color=self.colorset['game-option'], align='Right', margin=False)
                else:
                    self.blit_text(f'{txt_option} : {value}', pos_x, pos_y, width, height, color=self.colorset['game-option'], align='Right', margin=False)
                # One option under the other (they were all written at the same place)
                pos_y += height + self.margin

    def display_rem_darts(self, remaining, nb_darts, dartimage='target'):
        '''
        Display how many darts remain (only if game has no option so more room space available)
        '''
        #
        pos_x = int(self.margin + self.pn_size + (self.box_width * 7))
        pos_y = self.top_space
        #
        width = int(self.res['x'] - pos_x - self.margin)
        height = self.box_height
        #
        title_height = self.box_headers    # Basic title height
        #
        height = min(int((height - title_height) / nb_darts), width)
        width = height
        #
        image_x = pos_x + ((width - width) / 2)
        image_y = pos_y + title_height
        #
        imagefile = self.file_class.get_full_filename(dartimage, 'images')
        #
        scaled_text= self.scale_text(self.lang.translate('remaining-darts'), width, title_height)
        font_size = scaled_text[0]
        font = self.font(self.defaultfontpath, font_size)
        text_x = int(pos_x + scaled_text[1])
        text_y = int(pos_y + scaled_text[2])
        text = font.render(self.lang.translate('remaining-darts'), True, self.colorset['menu-text-black'])
        # Display
        self.blit_rect(pos_x, pos_y, width, height, self.colorset['bg-darts-nb'])
        self.blit_rect(pos_x, pos_y, width, title_height, self.colorset['bg-darts-nb-header'])
        self.blit(text, [text_x, text_y])
        for dart in range(0, remaining):
            self.display_image(imagefile, image_x, image_y + (dart * width), width, height)

    def display_rem_darts_compact(self, nb_remaining, nb_darts, dartimage='target'):
        '''
        Compact version (when options are set in game)
        '''
        #
        pos_x = int(self.margin + self.pn_size + (self.box_width * 7))
        pos_y = self.top_space
        #
        width = int(self.res['x'] - pos_x - self.margin)
        height = int(self.res['y'] / 12)
        # Title height
        title_height = self.box_headers    # Basic title height
        #
        image_height = min(int(width / nb_darts), height)
        image_width = image_height
        #
        image_x = int(pos_x + ((width - image_width * nb_darts) / 2))
        image_y = int(pos_y + title_height + ((height - image_height) / 2))
        #
        imagefile = self.file_class.get_full_filename(dartimage, 'images')
        #
        scaled_text= self.scale_text(self.lang.translate('remaining-darts'), width, title_height)
        font_size = scaled_text[0]
        font = self.font(self.defaultfontpath, font_size)
        text_x = int(pos_x + scaled_text[1])
        text_y = int(pos_y + scaled_text[2])
        text = font.render(self.lang.translate('remaining-darts'), True, self.colorset['menu-text-black'])
        # Display
        self.blit_rect(pos_x, pos_y + title_height, width, height, self.colorset['bg-darts-nb'])
        self.blit_rect(pos_x, pos_y, width, title_height, self.colorset['bg-darts-nb-header'])
        self.blit(text, [text_x, text_y])

        for x in range(0, nb_remaining):
            self.display_image(imagefile, image_x + (x * image_width), image_y, \
                    image_width, image_height)

    def display_game_options(self):
        '''
        Display game options during gameplay
        '''
        # Define options to be hidden on game screen
        hide_options = {'totalround': False, 'max_round': False}
        # Remove them from dict
        display_game_options = {key: value for key, value in self.game_options.items() \
                if key not in hide_options}    # Hide arbitrary options
        # Remove options when value is False
        display_game_options = {key: value for key, value in display_game_options.items()
                if value not in ('False', '0')}    # Remove false options
        # Get number of options
        nb_options = len(display_game_options)
        # Stop here if there is no otion to display
        if nb_options == 0: return False
        #
        pos_x = int(self.margin + self.pn_size + (self.box_width * 7))
        pos_y = self.top_space + int(self.res['y'] / 12) + int(self.res['y'] / 25) + self.margin
        #
        width = int(self.res['x'] - pos_x - self.margin)
        title_height = self.box_headers    # Basic title height
        max_y = int(self.screen_top - int(self.res['y'] / 12) - title_height - self.top_space - self.margin)
        height = min(title_height, int(max_y / nb_options))
        # Display header
        self.blit_rect(pos_x, pos_y, width, title_height, self.colorset['bg-optionslist-header'])
        scaled_text= self.scale_text(self.lang.translate('game-options'), width, height)
        font = self.font(self.defaultfontpath, scaled_text[0])
        text_x = int(pos_x + scaled_text[1])
        text_y = int(pos_y + scaled_text[2])
        text = font.render(self.lang.translate('game-options'), True, self.colorset['menu-text-black'])
        self.blit(text, [text_x, text_y])
        pos_y += height
        # Display options one by one
        for option, value in display_game_options.items():
            if value != 'True':
                txt = self.lang.translate(f"{self.selectedgame.replace(' ', '_')}-{option}") + ' : ' + str(value)
            else:
                txt = self.lang.translate(f"{self.selectedgame.replace(' ', '_')}-{option}")
            scaled_text= self.scale_text(txt, width, height)
            font_size = scaled_text[0]
            font = self.font(self.defaultfontpath, font_size)
            self.blit_rect(pos_x, pos_y, width, height, self.colorset['bg-optionslist'])
            text = font.render(txt, True, self.colorset['menu-text-black'])
            self.blit(text, [pos_x + scaled_text[1], pos_y + scaled_text[2]])
            pos_y += height
        # Return True if some options are displayed
        return True

    def display_sets(self, sets, end_of_game=False, wait=True):
        '''
        Sets winner's screen
        '''

        nb_sets = len(sets)
        self.reset_background()
        self.display_background()
        if end_of_game:
            self.end_of_game_text()

        self.display_big_row(1, nb_sets, 0, [(self.lang.translate("set"), 3 / 32), \
                (self.lang.translate('winner'), 3 / 8), \
                (self.lang.translate('duration'), 2 / 8), \
                (self.lang.translate('rounds'), 1 / 8), \
                (self.lang.translate('darts'), 5 / 32)] )

        index = 2
        for se_t in sets:
            data = str(se_t[2] - se_t[1]).split('.')[0]
            if data.startswith('0:0'):
                data = data[3::]
            elif data.startswith('0:'):
                data = data[2::]

            if isinstance(se_t[3], int) and se_t[3] == -1:
                w = self.lang.translate('none')
            else:
                w = se_t[3]

            self.display_big_row(index, nb_sets, 0, [(str(se_t[0]), 3 / 32), (w, 3 / 8), \
                    (data, 2 / 8), (str(se_t[4]), 1 / 8), (str(se_t[5]), 5 / 32)])
            index += 1

        # manage end game menu
        if end_of_game:
            click_zones = self.end_of_game_menu()
        elif wait:
            self.display_button(True, 'continue', special='return')

        self.update_screen()

        if end_of_game:
            return click_zones
        elif wait:
            self.wait_touch()

        return None

    def new_display_round(self, player, actual_round, max_round, set_number=None, max_set=None, history='scores', end_of_game=False):
        '''
        Display round
        '''

        left_x = self.margin
        left_y = self.margin
        left_w = int(self.res_x / 6 - 2 * self.margin)
        left_h = int(self.res_y / 4 - 2 * self.margin)
        text_h = int(left_h / 5)

        if set_number is not None and max_set is not None and max_set > 1:
            self.blit_text(f"Set", left_x, left_y, int(left_w / 3), text_h, color=self.colorset['game-round'], align='Left', valign='top', margin=False)
            self.blit_text(f"{set_number} / {max_set}", left_x + int(left_w / 2), 0, left_x + left_w - int(left_w / 2), text_h * 2, color=self.colorset['game-round'], align='Right', valign='top', margin=False)
            left_y += text_h * 2

        self.blit_text(f"Round", left_x, left_y, int(left_w / 3), text_h, color=self.colorset['game-round'], align='Left', valign='top', margin=False)
        self.blit_text(f"{actual_round} / {max_round}", left_x + int(left_w / 2), left_y - self.margin, left_x + left_w - int(left_w / 2), text_h * 2, color=self.colorset['game-round'], align='Right', valign='top', margin=False)
        left_y += text_h * 2

        if history == 'scores':
            try:
                for index in range(3):
                    if end_of_game:
                        continue
                    if actual_round - index > 0:
                        text1 = f'R{actual_round - index}'
                        score = player.scores[actual_round - 1 - index][3]
                        #text2 = f'{sum(scores[actual_round - index - 1] if scores[actual_round - index - 1] is not None else 0)}'
                        text2 = score
                        self.blit_text(text1, left_x, left_y, int(left_w / 2), text_h, color=self.colorset['menu-text-white'], align='Left')
                        self.blit_text(text2, left_x, left_y, int(left_w / 2), text_h, color=player.color, align='Right', margin=False)
                    left_y += text_h
            except:
                self.logs.error(f"No score historized for this game")

    def display_round(self, actual_round, max_round, set_number=None, max_set=None):
        '''
        Display Round
        '''
        #
        pos_x = self.margin
        pos_y = self.top_space
        # Title Y size
        height = 2 * self.box_headers    # Basic title height
        #
        title_width = int(self.pn_size - self.margin)
        title_height = int(min(self.position[0], self.res['y'] / 2) / 2 - height - self.margin) / 2

        if set_number is None or max_set is None or max_set < 2:
            title1 = 'round'
            title2 = 'over'
            text1 = f'{round}'
            text2 = f'{max_round}'
        else:
            title1 = 'set'
            title2 = 'round'
            text1 = f'{set_number+1}'
            text2 = f'{round} / {max_round}'

        self.blit_rect(pos_x, pos_y, title_width, title_height, self.colorset['bg-round-nb-header'])
        self.blit_text(title1, pos_x, pos_y, title_width, title_height, self.colorset['menu-text-black'])

        self.blit_rect(pos_x, pos_y + title_height, title_width, height, \
                self.colorset['bg-round-nb'])
        self.blit_text(text1, pos_x, pos_y + title_height, title_width, height, \
                self.colorset['menu-text-black'])

        self.blit_rect(pos_x, pos_y + title_height + height, title_width, height, \
                self.colorset['bg-round-nb-header'])
        self.blit_text(title2, pos_x, pos_y + title_height + height, title_width, height, \
                self.colorset['menu-text-black'])

        self.blit_rect(pos_x, pos_y + title_height  + 2 * height, title_width, height, \
                self.colorset['bg-round-nb'])
        self.blit_text(text2, pos_x, pos_y + title_height + 2 * height, title_width, height, \
                self.colorset['menu-text-black'])

    def onscreen_buttons(self):
        '''
        On screen buttons
        '''
        # Init
        click_zones = {}

        # GAME BUTTON
        width = (self.res['x'] - self.margin * 6) / 4
        height = self.margin * 30
        pos_x = self.margin
        pos_y = self.res['y'] - height - self.margin * 2

        # Blit Background rect
        self.blit_rect(pos_x, pos_y, width, height, self.colorset['menu-alternate'], 2, self.colorset['menu-buttons'], self.alpha)
        click_zones['GAMEBUTTON'] = (pos_x, pos_y, width, height)

        # Blit button
        self.blit_text('Exit', pos_x, pos_y, width, height, self.colorset['menu-text-white'])

        # BACKUP BUTTON
        pos_x = pos_x + self.margin + width + width / 2

        # Blit Background rect
        self.blit_rect(pos_x, pos_y, width, height, self.colorset['menu-shortcut'], 2, self.colorset['menu-buttons'], self.alpha)
        click_zones['BACKUPBUTTON'] = (pos_x, pos_y, width, height)

        # Blit button
        self.blit_text('Backup', pos_x, pos_y, width, height, self.colorset['menu-text-white'])

        # MISS BUTTON
        pos_x = pos_x + self.margin + width + width / 2

        # Blit Background rect
        self.blit_rect(pos_x, pos_y, width, height, self.colorset['menu-ok'], 2, self.colorset['menu-buttons'], self.alpha)
        click_zones['PLAYERBUTTON'] = (pos_x, pos_y, width, height)

        # Blit button
        self.blit_text('Next Player', pos_x, pos_y, width, height, self.colorset['menu-text-white'])

        # Return Dict of tuples representing clickage values
        return [click_zones]


    def press_player(self, txt='Press Player button', color='menu-ko'):
        '''
        Show the player icon on the top right of the screen
        '''
        height = int(self.res['y'] / 10)
        width = int(self.res['x'])
        pos_x = 0
        pos_y = int((self.res['y'] / 2) - (height / 2))
        pygame.draw.rect(self.screen, self.colorset[color], (pos_x, pos_y, width, height), 0)

        self.blit_text(txt, pos_x, pos_y, width, height)

        self.update_screen()

    def update_screen(self, rect=None, rect_array=None):
        '''
        Simply update the screen (after multiple updates for example)
        '''
        # Delay from an input to the screen showing its result : the measure of the
        # menus (it must not get worse)
        rpi = getattr(self, 'rpi', None)
        started = getattr(rpi, 'input_time', None)
        if started is not None:
            self.rpi.input_time = None
            self.logs.debug(f"Input to screen : {(time.perf_counter() - started) * 1000:.0f} ms")
        # The credits of the coin acceptor over every screen
        badge = self.coins_badge()
        if rect_array is not None:
            #self.display.update(rect_array)
            for rect in rect_array:
                self.display.update(rect)
            if badge is not None:
                self.display.update(badge)
        elif rect is not None:
            self.display.update(rect)
            if badge is not None:
                self.display.update(badge)
        else:
            self.display.flip()

    def coins_badge(self):
        '''
        Credits or time left of the coin acceptor (include/ccoins.py), in red at the top right
        of every screen. Its place, None when the games are free
        '''
        coins = getattr(getattr(self, 'rpi', None), 'coins', None)
        left = coins.left() if coins is not None else None
        if left is None:
            return None
        kind, value = left
        if kind == 'games':
            text = self.lang.translate('coins-credits').replace('{credits}', str(value))
        else:
            text = self.lang.translate('coins-time').replace('{time}', f"{value // 60}:{value % 60:02d}")
        # Its size and its place, set in the screen of the coin acceptor
        part_x, part_y = ccoins.BADGE_SIZES.get(coins.settings.get('badge_size'), ccoins.BADGE_SIZES['medium'])
        width, height = int(self.res['x'] * part_x), int(self.res['y'] * part_y)
        position = str(coins.settings.get('badge_position') or 'top-right')
        pos_x = {'left': self.margin, 'center': (self.res['x'] - width) // 2}.get(position.split('-')[-1],
                                                                                  self.res['x'] - width - self.margin)
        pos_y = self.res['y'] - height - self.margin if position.startswith('bottom') else self.margin
        badge = pygame.Rect(pos_x, pos_y, width, height)
        self.screen.fill((0, 0, 0), badge)
        self.blit_text(text, badge.x, badge.y, badge.w, badge.h, (230, 30, 30), margin=False)
        return badge

    def coins_redraw(self):
        '''
        A coin arrived : the credits drawn again, alone (the screen waits for an input)
        '''
        badge = self.coins_badge()
        if badge is not None:
            self.display.update(badge)

    def speech(self, text, speed=None):
        '''
        Espeak vocal synthetiser (untested on windows)
        '''
        try:
            volume = self.sound_volume
            if speed is not None:
                pass
            elif self.random_speed:
                speed = random.randint(80, 180)
            else:
                speed = 150

            # Non-blocking : if the audio output stalls, aplay may hang for ~30s and freeze the game loop
            subprocess.Popen(f'espeak -a {volume} -s {speed} -v mb-fr1 "{text}" --stdout |aplay 2> /dev/null', shell=True)
            return True
        except Exception as e:
            self.logs.warning(f"Problem trying to use espeak : {e}")
            return False

    def fade_out(self, sound, duration, fade_time, channel=None):
        '''
        Crop and fadeout the sound (on its channel if given : the same sound, kept, can be
        played again meanwhile)
        '''
        if duration > fade_time:
            pygame.time.wait(duration - fade_time)
        else:
            fade_time = duration
        if channel is None:
            sound.fadeout(fade_time)
        elif channel.get_sound() is sound:
            channel.fadeout(fade_time)

    # Sounds of a folder played at each turn : the next one is chosen and decoded while the
    # player throws (decoding the sound of the next player took 0.3 s, the game waited)
    PREPARED_SOUNDS = ('next_player',)

    # Sounds kept once decoded (a sound alone, not one chosen at random in a folder) : 3 minutes
    # in all at most (16 MB). Decoding miss.ogg took 0.1 s at each dart missed
    KEPT_SOUNDS_SECONDS = 180

    @staticmethod
    def chosen_in_folder(filename, sound_file):
        '''
        Sound chosen at random in the folder of this name (another one next time)
        '''
        return os.path.basename(os.path.dirname(sound_file)) == filename

    def decoded_sound(self, filename, sound_file):
        '''
        The sound of this file : decoded once if it is a sound alone
        '''
        with self.kept_sounds_lock:
            sound = self.kept_sounds.get(sound_file)
            if sound is not None:
                self.kept_sounds.move_to_end(sound_file)
                return sound
        sound = pygame.mixer.Sound(sound_file)
        if not self.chosen_in_folder(filename, sound_file):
            with self.kept_sounds_lock:
                self.kept_sounds[sound_file] = sound
                while len(self.kept_sounds) > 1                         and sum(kept.get_length() for kept in self.kept_sounds.values()) > self.KEPT_SOUNDS_SECONDS:
                    self.kept_sounds.popitem(last=False)
        return sound

    def prepare_sound(self, *filenames):
        '''
        Decode these sounds in the background (for a folder : its next sound, chosen now)
        '''
        if self.hidden or self.audio_deferred or not pygame.mixer.get_init():
            return

        def decode():
            for filename in filenames:
                sound_file = self.file_class.get_full_filename(filename, 'sounds')
                if sound_file is None:
                    continue
                try:
                    if self.chosen_in_folder(filename, sound_file):
                        self.prepared_sounds[filename] = (sound_file, pygame.mixer.Sound(sound_file))
                    else:
                        self.decoded_sound(filename, sound_file)
                except Exception as error:    # pylint: disable=broad-except
                    self.logs.warning(f"Sound {sound_file} not prepared : {error}")

        threading.Thread(target=decode, daemon=True).start()

    def play_sound(self, filename='beep1', wait_finish=False, duration=0):
        '''
        Play given sound. Search first in the home folder, then play default sound, or beep1 if not found.
        '''
        if self.audio_deferred:
            # Audio output opened at the first sound after the intro video
            self.show()
        if self.hidden or self.audio_deferred:
            # The intro video is playing : opening the audio output would chop its sound
            return
        prepared = self.prepared_sounds.pop(filename, None)
        sound_file = prepared[0] if prepared else self.file_class.get_full_filename(filename, 'sounds')
        if sound_file is not None:
            try:
                pygame.mixer.init(22050, -16, 2, MIXER_BUFFER)
                sound = prepared[1] if prepared else self.decoded_sound(filename, sound_file)
                if filename in self.PREPARED_SOUNDS:
                    self.prepare_sound(filename)
                # Play only if sound is set
                if sound:
                    # Set volume to defined setting and play
                    volume = round((int(self.sound_volume) * self.sound_multiplier / 100), 1)
                    sound.set_volume(volume)
                    self.logs.info(f"Play {sound_file} at volume {volume}")
                    play_sound = sound.play()

                    # if crop duration is requested, new thread to fadeout the sound (its
                    # 100 ms of delay in the thread : the game waited them)
                    if duration > 0:
                        x = threading.Thread(target = self.fade_out, args = (sound, duration + 100, 2000, play_sound))
                        x.start()

                    # if requested, we block the process until the sound is running
                    if wait_finish:
                        self.wait_end_sound(play_sound)
                    else:
                        return play_sound
            except Exception as e:
                self.logs.warning(f"Unable to load audio while trying to play file : {sound_file}\n{e}")
        else:
            self.logs.warning(f"Unable to load this audio file : {filename}")

    def wait_end_sound(self, played_sound):
        '''
        '''
        while played_sound.get_busy():
             pygame.time.wait(100)
            
    def adjust_volume(self, key, backup=True):
        '''
        Set sound volume
        '''
        if key in VOLUME_DOWN_KEYS:
            diff = -10
            if self.sound_volume == 0:
                diff = 0
        elif key in VOLUME_UP_KEYS:
            diff = 10
            if self.sound_volume == 100:
                diff = 0
        elif key in VOLUME_MUTE:
            if self.sound_volume == 0:
                self.sound_volume = self.old_volume
            else:
                self.old_volume = self.sound_volume
                self.sound_volume = 0
            diff = 0
        else:
            diff = 0

        if diff != 0:
            self.sound_volume += diff
            self.sound_volume = max(0, self.sound_volume)
            self.sound_volume = min(100, self.sound_volume)

            self.logs.debug(f"Volume level is now {self.sound_volume}")
            if diff > 0:
                self.play_sound('vol+', wait_finish=False)
            else:
                self.play_sound('vol-', wait_finish=False)
            self.video_player.set_volume(self.sound_volume)
        self.display_volume(backup)

    def sound_start_round(self, player, play_firstname=True):
        '''
        Play player name at the begining of a round (priority : personnal sound / speech / beep)
        '''
        # Try to play User Sound (user.ogg in the .pydarts directory)
        user_sound = self.play_sound(player, False)
        # If it fail, try to generate sound with text-to-speech
        if not user_sound and play_firstname:
            user_speech = self.speech(str(player))
            if not user_speech:
                self.play_sound()

    def sound_end_game(self, player, delay=None, duration=0):
        '''
        Play Winner at the end of the Game (priority : personnal sound / speech / "you")
        '''
        play_sound_end_game = "winneris"
        if player.find(',') > 0:
            play_sound_end_game = "winnerare"

        if self.file_class.is_dir(play_sound_end_game, 'sounds'):
            self.play_sound(play_sound_end_game, wait_finish=False, duration=duration)
            self.play_sound(f'{self.config.root_dir}/sounds/{play_sound_end_game}.ogg', wait_finish=True, duration=duration)
        else:
            self.play_sound(play_sound_end_game, wait_finish=True, duration=duration)        

        if delay is not None:
            pygame.time.wait(delay)
        user_sound = self.play_sound(player, False)
        if not user_sound:
            user_speech = self.speech(player)
            if not user_speech:
                self.play_sound('you', False)
        if duration > 0:
            self.play_sound('set_victory', wait_finish=True, duration=duration)
        else:
            self.play_sound('victory', wait_finish=True, duration=duration)
            
    def sound_for_touch(self, touch):
        '''
        Method to play sound for double, triple and bullseye
        '''
        if touch == "DB":
            self.play_sound('doublebullseye')
        elif touch == "SB":
            self.play_sound('bullseye')
        else:
            self.play_sound(touch)

    def nice_shot(self, msg='Nice Shot !', wait_time=3000, sens='DG'):
        '''
        Nice hit animation
        '''

        # Image size
        width = int(self.res['x'] / 3)
        height = int(self.res['y'] / 8)

        # Image movement step
        if self.config.rpi_model in ('0', '3A+', '3B+'):
            nb_steps = 20
        else:
            nb_steps = 45
        step = int(self.res['x'] / nb_steps)

        # Placement
        pos_y = int(self.res['y'] / 2.4)
        self.play_sound('niceshot')

        self.display_background()
        self.update_screen()

        if sens == 'GD' :    # Gauche à Droite
            sens = 1
            min_x = -width
            max_x = int(self.res['x'])
        else:
            sens = -1
            min_x = int(self.res['x'])
            max_x = -width

        image1 = self.file_class.get_full_filename('dart1', 'images')
        image2 = self.file_class.get_full_filename('dart2', 'images')

        alternate = 0
        for pos_x in range(min_x, max_x, step * sens):
            rect = (pos_x - step, pos_y , width + 4 * step, height)

            if alternate % 10 < 5:
                image = image1
            else:
                image = image2

            self.display_background(rect=rect)
            self.display_image(image, pos_x, pos_y, width, height)
            self.update_screen(rect=rect)
            alternate += 1

        self.message([msg], wait_time, self.colorset['menu-text-black'], 'middle', 'big')

    def version_check(self, serverversion):
        '''
        Display message for network version mismatch (only for major versions : exemple 1.0.1
        and 1.0.9 are supposed to be compatibles)
        '''
        if serverversion[:3] != self.config.pyDartsVersion[:3]:
            self.logs.error(f'Version of client ({self.config.pyDartsVersion}) and server \
                                ({serverversion}) do not match. This is strongly \
                                discouraged ! Please upgrade !')
            self.message([self.lang.translate('version-mismatch')], 200, None, 'middle', 'big', bg_color='menu-ko')
        else:
            self.logs.debug(f'Version of client ({self.config.pyDartsVersion}) \
                    and server ({serverversion}) are supposed to be compatible. Continuing...')

    def calibration_color(self, segment):
        '''
        Colors of a dartboard, dimmed : the segments not done yet
        '''
        if segment == 'SB':
            return (30, 70, 30)
        if segment == 'DB':
            return (90, 30, 30)
        dark = self.targets[int(segment[1:])] % 2 == 1
        if segment[0] == 'S':
            return (55, 55, 55) if dark else (105, 100, 85)
        return (90, 30, 30) if dark else (30, 80, 30)

    def draw_segment(self, segment, color):
        '''
        One segment of the target : S20, D5, T19, SB, DB
        '''
        if segment == 'SB':
            self.draw_bull(True, False, color)
        elif segment == 'DB':
            self.draw_bull(False, True, color)
        else:
            index = self.targets[int(segment[1:])]
            if segment[0] == 'S':
                self.draw_exterior_simple(index, color)
                self.draw_interior_simple(index, color)
            elif segment[0] == 'D':
                self.draw_double(index, color)
            else:
                self.draw_triple(index, color)

    def draw_calibration(self, segments, current, lit, codes):
        '''
        Wizard of the target : the whole target, segments done in green (skipped ones
        dimmed : no code in codes), the one to press blinking (lit or not), the others in
        the colors of a dartboard, dimmed
        '''
        self.display_background()
        self.message([self.lang.translate('press-on').format(segments[current])], 0, None, 'fullbottom', 'big', refresh=False)
        self.draw_background()
        for index, segment in enumerate(segments):
            if index < current and codes.get(segment):
                color = self.colorset['menu-ok']
            elif index == current:
                color = self.colorset['menu-shortcut'] if lit else (20, 20, 20)
            else:
                color = self.calibration_color(segment)
            self.draw_segment(segment, color)
        self.menu_header(self.lang.translate('board-calibration'),
                         f"{self.lang.translate('press-on-parts')} - {self.lang.translate('left')} : {len(segments) - current}")
        self.update_screen()

    def draw_sector(self, angle_index, radius_out, width, color, center=True):
        '''
        A ring sector of the target, filled : pygame.draw.arc with a thick width left holes.
        From radius_out inward on width, as the arcs it replaces
        '''
        center_x = self.res['x'] / (2 if center else 4)
        center_y = self.res['y'] / 2
        start = math.radians(18 * 6.5 - 18 * (angle_index + 1))
        end = math.radians(18 * 6.5 - 18 * angle_index)
        steps = 12
        angles = [start + (end - start) * step / steps for step in range(steps + 1)]
        points = [(center_x + radius_out * math.cos(a), center_y - radius_out * math.sin(a)) for a in angles]
        radius_in = radius_out - width
        points += [(center_x + radius_in * math.cos(a), center_y - radius_in * math.sin(a)) for a in reversed(angles)]
        pygame.draw.polygon(self.screen, color, points)

    def draw_triple(self, angle_index, color=None, center=True):
        '''
        Draw triples
        '''
        color = self.colorset['menu-ok'] if color is None else color
        radius_triple_out = int(min(self.res['y'], self.res['x']) / 5.3)
        width_triple = min(int(self.res['y'] / 38), int(self.res['x'] / 38))

        self.draw_sector(angle_index, radius_triple_out, width_triple, color, center)

    def draw_missed(self, color=None, center=True):
        '''
        Draw missed
        '''
        color = self.colorset['menu-item-black'] if color is None else color
        radius_missed_out = int(min(self.res['y'], self.res['x']) / 3)
        width_missed = int(min(self.res['y'], self.res['x'] / 60))
        if center:
            div = 2
        else:
            div = 4

        arc_rect = (self.res['x'] / div - radius_missed_out, self.res['y'] / 2 - radius_missed_out,
                radius_missed_out * 2, radius_missed_out * 2)

        pygame.draw.arc(self.screen, color, arc_rect, math.radians(0), math.radians(361), width_missed)

    def draw_double(self, angle_index, color=None, center=True):
        '''
        draw_double
        '''
        if color is None:
            color = self.colorset['menu-alternate']

        radius_double_out = int(min(self.res['y'], self.res['x']) / 3.3)
        width_double = min(int(self.res['y'] / 35), int(self.res['x'] / 35))
        self.draw_sector(angle_index, radius_double_out, width_double, color, center)

    def draw_exterior_simple(self, angle_index, color=None, center=True):
        '''
        Draw external simple
        '''
        if color is None:
            color = self.colorset['menu-item-white']

        radius_double_in = int(min(self.res['y'], self.res['x']) / 3.65)
        width_simple1 = min(int(self.res['y'] / 12), int(self.res['x'] / 12))

        self.draw_sector(angle_index, radius_double_in, width_simple1, color, center)

    def draw_interior_simple(self, angle_index, color=None, center=True):
        '''
        Draw internal simple
        '''
        if color is None:
            color = self.colorset['menu-item-white']

        radius_triple_in = int(min(self.res['y'], self.res['x']) / 6.2)
        width_simple2 = min(int(self.res['y'] / 8.7), int(self.res['x'] / 8.7))

        self.draw_sector(angle_index, radius_triple_in, width_simple2, color, center)

    def draw_bull(self, simple=False, double=False, color=None, center=True):
        '''
        Draw bullseye and double bullseye
        '''
        if color is None:
            if double:
                color = self.colorset['target-db']
            elif simple:
                color = self.colorset['target-sb']

        width_simple = min(int(self.res['y'] / 32), int(self.res['x'] / 32))
        width_double = min(int(self.res['y'] / 64), int(self.res['x'] / 64))

        radius_center_out = int(min(self.res['y'], self.res['x']) / 22)
        radius_center_in = int(min(self.res['y'], self.res['x']) / 52)

        if center:
            center_x = int(self.res['x'] / 2)
        else:
            center_x = int(self.res['x'] / 4)

        if simple:
            pygame.draw.circle(self.screen, color, (center_x, int(self.res['y'] / 2)), \
                    radius_center_out, width_simple)
        if double:
            pygame.draw.circle(self.screen, color, (center_x, int(self.res['y'] / 2)), radius_center_in)

    def draw_background(self, center=True):
        '''
        Draw background. Call it before anything else
        '''

        width = min(int(self.res['y'] / 3), int(self.res['x'] / 3))
        radius_center = int(min(self.res['y'], self.res['x']) / 3)
        if center:
            center_x = int(self.res['x'] / 2)
        else:
            center_x = int(self.res['x'] / 4)
        pygame.draw.circle(self.screen, self.colorset['color-black'], \
                (center_x, int(self.res['y'] / 2)), radius_center, width)

    def heat_map(self, name, stats, color=None):
        '''
        Display heat map
        '''

        self.display_background()
        self.menu_header(name)
        self.draw_background(center=False)

        item_id = 2
        total = stats[1]
        max_darts = min(total, 15)

        self.display_row(1, 5, 1, [(self.lang.translate("stats-multiplier"), 1 / 3), (self.lang.translate('stats-touch'), 1 / 3), (self.lang.translate('stats-percent'), 1/3)], center=False, align='right')
        self.display_row(2, 5, 1, [(self.lang.translate("Simple"), 1 / 3), (str(stats[2][0]), 1 / 3), (str(stats[2][1]), 1/3)], center=False, align='right')
        self.display_row(3, 5, 0, [(self.lang.translate("Double"), 1 / 3), (str(stats[3][0]), 1 / 3), (str(stats[3][1]), 1/3)], center=False, align='right')
        self.display_row(4, 5, 1, [(self.lang.translate("Triple"), 1 / 3), (str(stats[4][0]), 1 / 3), (str(stats[4][1]), 1/3)], center=False, align='right')
        self.display_row(5, 5, 0, [(self.lang.translate("Missed"), 1 / 3), (str(stats[5][0]), 1 / 3), (str(stats[5][1]), 1/3)], center=False, align='right')

        self.display_row(1, max_darts + 1, 1, [("Segment", 1 / 3), ('Touches', 1 / 3), ('Pourcentage', 1/3)], 1/2, center=False)

        # Print 10 first more occurences
        for stat in stats[0]:
            if item_id > max_darts or stats[0][stat][0] == 0:
                break
            self.display_row(item_id, max_darts, item_id % 2 == 0, [(stat, 1/3), (str(stats[0][stat][0]), 1/3), (str(stats[0][stat][1]), 1/3)], 1/2, 0, False)
            item_id += 1

        ref = 30

        interior = self.config.get_value('SectionAdvanced', 'interior')
        if interior:
            multipliers = ['s', 'S', 'D', 'T']
        else:
            multipliers = ['S', 'D', 'T']
        for hit in [f'{mult}{num}' for mult in multipliers for num in range(1, 21)] + ['SB', 'DB', 'MISS']:
            # Get type
            multiplier = hit[:1]
            pos = stats[0][hit][3]

            # Define colors
            if stats[0][hit][0] == 0:
                green = ref
                red = ref
                blue = ref
                part_color = (ref, ref, ref)
            elif color == 'green':
                green = 255 - ( pos / total ) * 192
                part_color = (0, green, 0)
            else:
                red = 255 - ( pos / total ) * 255
                blue = 255 - red
                green = 0
                part_color = (max(ref, int(red)), max(ref, int(green)), max(ref, int(blue)))
                part_color = (red, green, blue)

            # Draw the right thing
            if hit[1:] == 'B':
                score = 'B'
            elif hit == 'MISS':
                score = None
            else:
                score = int(hit[1:])

            if score == 'B' :
                if multiplier == 'S':
                    self.draw_bull(True, False, part_color, center=False)
                else:
                    self.draw_bull(False, True, part_color, center=False)
            elif multiplier == 'S':
                self.draw_exterior_simple(self.targets[score], part_color, center=False)
                if not interior:
                    self.draw_interior_simple(self.targets[score], part_color, center=False)
            elif multiplier == 's':
                self.draw_interior_simple(self.targets[score], part_color, center=False)
            elif multiplier == 'D':
                self.draw_double(self.targets[score], part_color, center=False)
            elif multiplier == 'M':
                self.draw_missed(part_color, center=False)
            else:
                self.draw_triple(self.targets[score], part_color, center=False)

        self.update_screen()
        self.display_button(True, 'continue', special='return')

        self.wait_touch()

    def sort_players(self, player):
        return player[1]
        
    def translate_option(self, game, option_name):
        if option_name[0:6].upper() == 'DEBUG-': # Dictionnaire DEBUG pour aide au debugage des jeux (voir Othello)
            text = option_name[6:] #On ne traduit pas c'est pour un debug
            #DEBUG-Nb_de_tour  affichera Nb_de_tour
            return text
        text = self.lang.translate(f'{game}-{option_name}')
        self.logs.debug(f"Cherche {game}-{option_name}")
        if text == f'{game}-{option_name}': # pas de traduction trouvée
            text = self.lang.translate(f'AllGame-{option_name}')
        return text
    
    def draw_qrcode(self, game, size=3, bordure=4):
        if self.qrlogo != f'logos_menu/{game}':
            self.qrlogo = f'logos_menu/{game}'
            logo = self.file_class.get_full_filename(self.qrlogo, 'images')
            # Generated once for the same code (210 ms on a Pi 3 at each opening of the options)
            maker = self.qrcode
            key = (game, logo, size, bordure, maker.transparent, maker.qrsize, maker.color, maker.bgcolor, maker.tcolor)
            img = self.qrcodes.get(key)
            if img is None:
                img = maker.generate(game, logo, size, bordure)
                if len(self.qrcodes) >= 16:
                    self.qrcodes = {}
                self.qrcodes[key] = img
            else:
                # As generate does : transparency asked for one code only
                maker.transparent = False
        else:
            img = None #n'affiche pas l'image à nouveau
        return img

    def display_qrcode(self, img = None, pos_x = -160 ,pos_y = 10 ):
        '''
        Affiche qrcode
        '''
#        print (f" image = {img}")
        if img is None:
            return
        if pos_x < 0:
            pos_x = self.res_x - abs(pos_x)
        if pos_y < 0:
            pos_y = self.res_y - abs(pos_y)
            
        self.blit(img, (pos_x, pos_y))
        self.update_screen()
        
      
        
