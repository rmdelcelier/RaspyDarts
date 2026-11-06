#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random

"""
Class used to send informations to dmd
"""

class Cdmd():
    """
    Class used to send messages to DMD
    """

    def __init__(self, logs, event, file_class):
        self.dart = { 0:'', 1:'', 2:''}
        self.event = event
        self.logs = logs
        self.file_class = file_class

        self.init_insults()
        self.insults = False
        # In a game, with « Afficher les textes Raspy2DMD à la couleur du joueur » : the colour
        # of the player whose turn it is (its texts sent by msgcolor) ; None : msg, msgmove
        self.player_color = None

    def init_insults(self):
        """
        Load insults' file
        """

        self.insults_tab = []
        insults_file = self.file_class.get_full_filename('insults', 'text')
        if insults_file is not None:
            try:
                with open(f'{insults_file}', 'r') as insults:
                    text = insults.readlines()
                insults.close()
                self.insults_tab = text
            except:
                pass

    def send_insult(self, firstname=None):
        """
        Send soft insult to DMD
        """
        if len(self.insults_tab) > 0:
            index = random.randint(0, len(self.insults_tab) - 1)
            self.send_text(self.insults_tab[index].replace('\n', '').replace('{}', firstname))

    def send(self, msg):
        """
        Send message using event class
        """
        self.event.publish(msg, limit="DMD")

    def shutdown(self, enabled=True):
        """
        Raspy2DMD powered off with RaspyDarts (option « Éteindre Raspy2DMD avec RaspyDarts ») :
        « shutdwn| » to all the Raspy2DMD listening (their own Raspberry). The one of this machine
        (Pico seul) would power it off at once (forced), while RaspyDarts powers it off cleanly :
        stopped first, it does not receive it (the others, on the network, do : mode double)
        """
        if not enabled:
            self.logs.debug("Raspy2DMD not powered off with RaspyDarts (option)")
            return
        if os.path.isdir('/Raspy2DMD'):
            import subprocess
            import time
            pattern = 'python.*ServerRaspy2DMD[.]py'
            try:
                if os.path.isfile('/etc/systemd/system/raspy2dmd.service'):
                    subprocess.run(['sudo', '-n', 'systemctl', 'stop', 'raspy2dmd'], check=False, timeout=15,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(['sudo', '-n', 'pkill', '-f', pattern], check=False, timeout=10,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                for _ in range(25):
                    if subprocess.run(['pgrep', '-f', pattern], check=False, timeout=5,
                                      stdout=subprocess.DEVNULL).returncode != 0:
                        break
                    time.sleep(0.2)
                else:
                    self.logs.warning("Raspy2DMD of this machine still running : no shutdwn sent")
                    return
            except Exception as error:    # pylint: disable=broad-except
                self.logs.warning(f"Raspy2DMD of this machine not stopped ({error}) : no shutdwn sent")
                return
            self.logs.debug("Raspy2DMD of this machine stopped : shutdwn sent to the others")
        self.send('shutdwn|')
        # Delivered before the Raspberry is powered off
        import time
        time.sleep(1)

    @staticmethod
    def rgb(color):
        """
        A colour of RaspyDarts (r, g, b), a name or #rrggbb) as Raspy2DMD wants it : R;G;B
        """
        try:
            if isinstance(color, (tuple, list)):
                red, green, blue = (int(value) for value in color[:3])
            else:
                import pygame    # pylint: disable=import-outside-toplevel
                found = pygame.Color(str(color).strip())
                red, green, blue = found.r, found.g, found.b
            return f'{red};{green};{blue}'
        except Exception:    # pylint: disable=broad-except
            return None

    def send_text(self, text, tempo=None, sens=None, iteration=None):
        """
        Function used to send text to dmd. In a game, with the option : in the colour of the
        player (msgcolor|text|R;G;B|0;0;0|sens|iterations : all its fields given, the same
        direction and passes as without colour)
        """
        if sens :
            if iteration :
                msg = 'msgmovebcl|{}'
            else :
                msg = 'msgmove|{}'
        else :
            if len(text) > 22 :
                msg = 'msgmove|{}'
                sens = 'left'
            else :
                msg = 'msg|{}'

        color = self.rgb(self.player_color) if self.player_color is not None else None
        if color:
            # The same text, direction and passes as msg / msgmove / msgmovebcl, in the colour
            self.send(f"msgcolor|{text}|{color}|0;0;0|{sens or ''}|{iteration or ''}")
            return

        msg = msg.format(text)
        if sens :
            msg += f'|{sens}'

        if iteration :
            msg += f'|{iteration}'

        if tempo :
            msg += f'|{tempo}'

        self.send(msg)

    def send_score(self, dart, touch):
        """
        Function used to send score to dmd
        """

        if dart == 1:
            self.dart[0] = touch
            text = f'score|{touch} - X - X'
        elif dart == 2:
            self.dart[1] = touch
            text = f'score|{self.dart[0]} - {touch} - X'
        elif dart == 3:
            self.dart[2] = touch
            text = f'score|{self.dart[0]} - {self.dart[1]} - {touch}'
        else:
            return

        # In the colour of the player (option) : score|X - X - X||R;G;B (Raspy2DMD 1.6.1.2 ; an
        # older one shows it in its colour, the field ignored)
        color = self.rgb(self.player_color) if self.player_color is not None else None
        if color:
            text += f'||{color}'
        self.send(text)
