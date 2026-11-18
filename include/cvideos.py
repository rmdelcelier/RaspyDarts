#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Class used to play videos
"""

from math import log as math_log
import shutil
import subprocess as subp

# Players by order of preference : omxplayer only exists on Raspbian Buster
PLAYERS = ('omxplayer', 'cvlc')

FOUND_PLAYER = []

def find_player():
    """
    Return the first video player installed, None if there is none
    """
    if len(FOUND_PLAYER) == 0:
        FOUND_PLAYER.append(None)
        for player in PLAYERS:
            if shutil.which(player) is not None:
                FOUND_PLAYER[0] = player
                break
    return FOUND_PLAYER[0]

# Videos launched by the game (animations) : the photos and clips of the webcam are
# shown once they are over (see ccamera.show_in_turn)
PLAYING = []

def playing():
    '''
    Is a video of the game being played ?
    '''
    PLAYING[:] = [process for process in PLAYING if process.poll() is None]
    return bool(PLAYING)

def player_command(player, video, volume=None, window=None):
    """
    Build the command line used to play a video
    volume : in millibels (0 = original volume, -6000 = muted)
    window : (x, y, width, height) to play in a part of the screen, else fullscreen
    """
    if player == 'omxplayer':
        command = ['omxplayer']
        if volume is not None:
            command += ['--vol', f'{volume}']
        if window is not None:
            pos_x, pos_y, width, height = window
            command += ['--win', f'{pos_x},{pos_y},{pos_x + width},{pos_y + height}', '--aspect-mode', 'letterbox']
        return command + ['-o', 'alsa', f'{video}']

    command = ['cvlc', '--play-and-exit', '--no-video-title-show', '--no-osd']
    if volume is not None:
        command += [f'--gain={min(10 ** (volume / 2000), 8):.3f}']
    if window is not None:
        pos_x, pos_y, width, height = window
        command += ['--no-fullscreen', '--no-embedded-video', '--no-video-deco', '--video-on-top',
                    f'--video-x={pos_x}', f'--video-y={pos_y}', f'--width={width}', f'--height={height}']
    else:
        command += ['--fullscreen']
    return command + [f'{video}']

def stop_player(player, process):
    """
    Stop a video launched without waiting for its end
    """
    if process is None or not hasattr(process, 'poll') or process.poll() is not None:
        return
    if player == 'omxplayer':
        # omxplayer is a script which launch omxplayer.bin : only the 'q' key stops both
        process.stdin.write(b'q')
        process.stdin.flush()
        process.stdin.close()
    else:
        # vlc needs more than 2 seconds to close when asked politely
        process.kill()


class Videos():
    """
    Module used to play videos
    """

    def __init__(self, logs, c_file, level=0, volume=70, multiplier=1):
        self.logs = logs
        self.level = int(level)
        self.volume = volume
        self.file = c_file
        self.multiplier = multiplier
        self.set_volume(volume)
        self.played_video = None
        self.player = find_player()
        if self.player is None:
            self.logs.warning(f"No video player found ({' or '.join(PLAYERS)}) : videos are disabled")
        else:
            self.logs.debug(f"Video player is {self.player}")

    def set_level(self, level):
        """
        Set video level
        """
        self.logs.debug(f"Set video level to {level}")
        self.level = int(level)

    def set_volume(self, volume):
        """
        Set volume
        """
        log = int(4000 - math_log(max(int(volume / 3 * self.multiplier), 1), 10) * 2000)
        self.logs.debug(f"Set volume to {-log}")

        self.volume = -log

    def play_video(self, video, wait=False):
        """
        Play video
        """
        if video is None or self.player is None:
            return False

        self.logs.debug(f"Play {video} wait={wait}")
        command = player_command(self.player, video, self.volume)

        self.logs.debug(f"{' '.join(command)}")
        if wait:
            with subp.Popen(command, stdout=subp.DEVNULL, stderr=subp.DEVNULL) as process :
                PLAYING.append(process)
                process.wait()
                return True
        else:
            process = subp.Popen(command, stdin=subp.PIPE, stdout=subp.DEVNULL, stderr=subp.DEVNULL)
            PLAYING.append(process)
            return process

    ################################################################
    ### Methode pour lire un plusieurs videos
    ################################################################
    def play_videos(self, videos):
        """
        Play a list of videos
        """

        self.play_video(videos.join(' '))

    ################################################################
    ### Methode pour lire les videos standard et speciales
    ################################################################
    def play_show(self, darts, hit, play_special=False):
        """
        Identify the special move, find the video and play it
        """
        if self.level < 1:
            return None
        if self.played_video is not None:
            try:
                stop_player(self.player, self.played_video)
                self.played_video = None
            except Exception as error:
                print(f"exception is {error}")            
        video = None
        # Special moves need the three darts of the round (some games give less)
        if len(darts) >= 3 and 'X' not in darts and None not in darts:
            video = self.special_move(darts[0], darts[1], darts[2], play_special)
            if video is not None:
                self.played_video = self.play_video(self.file.get_full_filename(video, 'videos'), wait=False)
                return self.played_video

        if video is None:   # and hit in ('SB', 'DB'):
            video = self.file.get_full_filename(file_name=hit, file_type='videos')

        if video is None and hit in ('SB', 'DB', 'T20', 'T19', 'T18', 'T17'):
            video = self.file.get_full_filename(file_name='big_score', file_type='videos')

        if video is not None:
            self.played_video = self.play_video(video, wait=False)
            return self.played_video

        return None

    def play_event(self, name, wait=False):
        """
        The video of a moment of the game (WINNER : the winner of the game, MISS : a dart missed),
        found as the ones of the darts (DB, SB...) : a folder videos/<name> of the theme, of the
        user or of the game (a video chosen at random in it), or a file videos/<name>.<ext>.
        The one being played stopped first. None : no video (or the videos are off)
        """
        if self.level < 1 or self.player is None:
            return None
        video = self.file.get_full_filename(file_name=name, file_type='videos')
        if video is None:
            return None
        if self.played_video is not None:
            try:
                stop_player(self.player, self.played_video)
            except Exception as error:    # pylint: disable=broad-except
                self.logs.debug(f"Video not stopped : {error}")
            self.played_video = None
        if wait:
            self.play_video(video, wait=True)
            return True
        self.played_video = self.play_video(video, wait=False)
        return self.played_video

    def dart_value(self, dart, mult=False):
        """
        Extract number from dart stroke
        """
        if dart == 'SB':
            return 25

        if dart == 'DB':
            return 50

        multiplier = 1
        if mult:
            if dart[0] == 'D':
                multiplier = 2
            elif dart[0] == 'T':
                multiplier = 3

        return int(dart[1::]) * multiplier

    def special_move(self, dart1, dart2, dart3, play_special):
        """
        Is ther any special video according to special move ?
        """
        special_move = None
        darts = [dart1.upper(), dart2.upper(), dart3.upper()]
        try:
            sorted_darts = darts
            sorted_darts.sort(key=self.dart_value)
        except: # pylint: disable=bare-except
            sorted_darts = []

        somme = 0
        for dart in darts:
            if dart == 'SB':
                somme += 25
            elif dart == 'DB':
                somme += 50
            elif dart is not None and dart[0] in ['S', 'D', 'T']:
                somme += self.dart_value(dart, True)

        self.logs.debug(f"Search for move ({play_special}/{self.level}) : {sorted_darts}")

        if all(x == 'T20' for x in darts):
            special_move = 'MAXIMUM_TON_80'

        elif play_special and self.level == 2:

            # DEVIL = S6 - S6 - S6
            if all(x == 'S6' for x in darts):
                special_move = 'DEVIL'

            # TRIPLE DEVIL = T6 - T6 - T6
            elif all(x == 'T6' for x in darts):
                special_move = 'DEVIL_TRIPLE'

            # BREAKFAST (CHIPS/CLASSIC) = S5 - S20 - S1 (peu importe l'ordre)
            elif sorted_darts == ['S1', 'S5', 'S20']:
                special_move = 'BREAKFAST'

            # CHAMPAGNE BREAKFAST (GRAND SLAM) = T5 - T1 - T20 (peu importe l'ordre)
            elif sorted_darts == ['T1', 'T5', 'T20']:
                special_move = 'CHAMPAGNE_BREAKFAST'

            # ROUND OF TERMS = T1 - T1 - T1
            elif dart1[0:1] == 'T' and dart2[0:1] == 'T' and dart3[0:1] == 'T':
                special_move = 'ROUND_OF_TERMS'

            # BAG (BUCKET) OF NAIL = S1 - S1- S1
            elif all(x == 'S1' for x in darts):
                special_move = 'BUCKET_OF_NAIL'

            # NOT OLD = S5 - S20 - S12 (peu importe l'ordre)
            elif sorted_darts == ['S5', 'S12', 'S20']:
                special_move = 'NOT_OLD'

        if special_move is not None:
            return special_move

        if all(x is None for x in darts):
            special_move = 'WHITE_HORSE'

        # BLACK HAT = DB - DB - DB
        elif all(x == 'DB' for x in darts):
            special_move = 'BLACK_HAT_THREE_IN_THE_BLACK'

        # RED HAT = SB - SB - SB
        elif all(x == 'SB' for x in darts):
            special_move = 'RED_HAT'

        # HAT TRICK = SB - DB - SB (3 bulls peu importe lesquelles)
        elif dart1 in ['SB', 'DB'] and dart2 in ['SB', 'DB'] and dart3 in ['SB', 'DB']:
            special_move = 'HAT_TRICK'

        # THREE IN A BED = 3 fois le meme segment
        elif all(x == dart1 for x in darts):
            special_move = 'THREE_IN_A_BED'

        # LOW TON = tot >= 100 & <= 150
        elif 99 < somme < 151:
            special_move = 'LOW_TON'

        # HIGH TON = tot >= 151 & <= 179
        elif 150 < somme < 180:
            special_move = 'HIGH_TON'

        # BAIL OUT = La 3eme flechette marque un triple eleve
        elif dart3 in ['T20', 'T19', 'T18', 'T17'] and play_special and self.level == 2:
            special_move = 'BAIL_OUT'

        return special_move
