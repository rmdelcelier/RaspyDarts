"""
A network game waiting for its players, followed in the background : the screen of the wait
(Screen.starting) left, the borne asks the server every second as that screen did (the
players connected, the game launched or given up) while the menus are used. Shown by the
activity indicator (include/cactivity.py), reachable as a button of the menus (wheel of a USB
knob, buttons, arrows, touch) : resume the screen of the wait, or give up the wait.

Everything goes back through the screen of the wait (the main loop resumes it) : the game
launched, given up, or the connection lost are done there as always.
"""

import threading
import time


class NetWait:
    '''
    The wait of a network game in the background. state : waiting, launch (the game starts),
    abort, lost (the server does not answer) ; intent : None, resume, abandon ; resume_wanted :
    the menus go back to the main menu, which gives the hand back to the main loop
    '''
    PERIOD = 1.0

    def __init__(self, logs, client, status, local_players, gamename, game, game_type, players):
        self.logs = logs
        self.client = client
        self.status = status
        self.local_players = list(local_players)
        self.gamename = gamename
        self.game = game
        self.game_type = game_type
        self.players = list(players or [])
        self.reply = {'REQUEST': None}
        self.state = 'waiting'
        self.intent = None
        self.resume_wanted = False
        self.woken = False
        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def run(self):
        while self.running:
            started = time.monotonic()
            try:
                reply = self.client.send_local_players(self.local_players)
            except Exception as error:    # pylint: disable=broad-except
                self.logs.warning(f"Network game {self.gamename} : server lost while waiting ({error})")
                self.state = 'lost'
                self.want_resume()
                return
            if not isinstance(reply, dict):
                continue
            self.reply = reply
            if 'PLAYERSNAMES' in reply and reply['PLAYERSNAMES'] is not None:
                self.players = list(reply['PLAYERSNAMES'])
            if reply.get('REQUEST') in ('LAUNCH', 'ABORT'):
                # The game starts (or is given up) : back to its screen at once
                self.state = 'launch' if reply.get('REQUEST') == 'LAUNCH' else 'abort'
                self.logs.info(f"Network game {self.gamename} : {self.state} while waiting in the background")
                self.want_resume()
                return
            time.sleep(max(0.0, self.PERIOD - (time.monotonic() - started)))

    def want_resume(self, intent=None):
        if intent is not None:
            self.intent = intent
        self.resume_wanted = True
        self.woken = False

    def stop(self):
        '''
        The asking stopped before the screen of the wait uses the connection again
        '''
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=15)

    def others(self):
        return max(0, len(self.players) - len(self.local_players))
