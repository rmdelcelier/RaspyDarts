"""
Generic game class
"""
from copy import deepcopy  # For backupTurn
import collections
import random
### TROPHEES
from include import ctrophies

# This class is used for common methods and var shared by games - All games have a inherited version of this class

class Game:
    """
    Generic game class
    """

    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player, free_launch=False, game_is_ok_for_color = True):   
        self.logs = logs
        self.options = options
        self.game = game
        self.free_launch = free_launch
        self.game_is_ok_for_color = game_is_ok_for_color  
        self.nb_players = nb_players
        self.config = config
        self.display = display
        self.infos = ""
        self.game_records = []
        self.time = 0
        self.nbcol = int(self.config.get_value('SectionGlobals', 'nbcol'))
        self.random_from_net = False
        # Init and Override default scores if relevant
        self.score_map = deepcopy(self.config.default_score_map)
        # For Raspberry
        self.rpi = rpi
        # For Raspberry DMD
        self.dmd = dmd
        # For Raspberry Video Player
        self.video_player = video_player
        self.play_video = False
        self.max_round = 10
        self.nb_darts = 3
        
        ctrophies.init_trophy_display(self.display)

        self.neighbors = {'1': ['20', '18', '4', '5', 'B'],
                '2': ['17', '15', '3', '10', 'B'],
                '3': ['17', '19', '7', '2', 'B'],
                '4': ['13', '18', '1', '6', 'B'],
                '5': ['20', '12', '1', '9', 'B'],
                '6': ['10', '13', '4', '15', 'B'],
                '7': ['16', '19', '3', '8', 'B'],
                '8': ['11', '16', '7', '14', 'B'],
                '9': ['12', '14', '5', '11', 'B'],
                '10': ['12', '14', '5', '11', 'B'],
                '11': ['14', '8', '9', '16', 'B'],
                '12': ['5', '9', '20', '14', 'B'],
                '13': ['17', '19', '2',  '7', 'B'],
                '14': ['11', '9', '12', '8', 'B'],
                '15': ['2', '10', '6', '17', 'B'],
                '16': ['7', '8', '19', '11', 'B'],
                '17': ['2', '3', '15', '19', 'B'],
                '18': ['1', '4', '13', '20', 'B'],
                '19': ['3', '7', '16', '17', 'B'],
                '20': ['1', '5', '12', '18', 'B']
                }

        self.target_order = [1, 18, 4, 13, 6, 10, 15, 2,
                             17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5, 20]
        self.colors = ['green', 'red', 'blue', 'gold', 'silver']

        # Backups
        self.backups = []

        self.show_segment = True
        self.show_dmd = True
        self.infos = ''
        self.winner = -1
        self.lf = '\n'
        self.intro_done = False

    def init_handler(self, return_code=0):

        # Examples
        #   To play show : handler['show'] = (players[actual_player].darts, hit, True)
        #   To play a video : handler['video'] = 'SB'
        #   To play a sound : handler['sound'] = hit

        return {'return_code': return_code, 'message': None, 'show': None,
                'video': None, 'sound': None, 'light': None, 'strobe': None,
                'dmd': None, 'speech': None, 'speech_speed': None, 'announcement': None, 'event': None, 'take_shot': None}

    def play_intro(self):
        """
        Play intro : video or sound
        """
        self.logs.debug(f"Try to play intros/intro_{self.game}")
        video = self.display.file_class.get_full_filename(
            f"intros/intro_{self.game}", 'videos')

        sound = self.display.file_class.get_full_filename(
                f"{self.game}_intro", 'sounds')

        return self.display.play_sound(sound), self.video_player.play_video(video)

    def play_intro_only_video(self):
        """
        Play intro : video
        """
        self.logs.debug(f"Try to play ONLY intros/intro_{self.game}")
        video = self.display.file_class.get_full_filename(
            f"intros/intro_{self.game}", 'videos')

        return self.video_player.play_video(video)

    def get_score_from_hit(self, hit, sb_value=25, db_value=50):
        """
        Return score from hit
        """
        try:
            if hit == 'SB':
                return sb_value
            if hit == 'DB':
                return db_value

            mult = 1
            if hit[0:1] == 'D':
                mult = 2
            elif hit[0:1] == 'T':
                mult = 3
            return mult * int(hit[1::])
        except:
            return 0

    def split_key(self, hit, multiplier=False):
        """
        Split S1 into S and 1 or 1 and 1 is multiplier is true
        """
        if hit is None:
            return None, None

        if multiplier:
            mult = 1
            if hit[0:1] == 'D':
                mult = 2
            elif hit[0:1] == 'T':
                mult = 3
            return mult, hit[1:]
        return hit[0:1], hit[1:]

    def display_dmd(self):
        """
        Return true if segment should be displayed on DMD
        """
        return self.show_dmd

    def dmd_turn_text(self, players, actual_round, actual_player):
        """
        Text sent to dmd before the first dart of a player
        """
        return players[actual_player].name

    def display_segment(self):
        """
        Return true if segment should be displayed on screen
        """
        return self.show_segment

    def play_show(self, darts, hit, play_special=False):
        """
        Show standard video animation on Raspydarts Video Player
        Return False is show is played else True
        """
        return self.video_player.play_show(darts, hit, play_special)

    def post_pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Special for Simon game
        """
        return 0

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Function ran before each dart throw

        Return codes are:
          0 - Jump to next dart
          1 - Jump to next player immediatly
          2 - Game is over
          3 - There is a winner (self.winner must hold winner id)
          4 - The player is not allowed to play (jump to next player)
         Send debug output to log system. Use DEBUG or WARNING or ERROR or FATAL
        """
        self.infos = ''
        return_code = 0
        # infos Can be used to create a per-player debug output
        self.infos += f"### Player {actual_player + 1}: {players[actual_player].name} ###{self.lf}"
        # You will probably save the turn to be used in case of backup turn (every first dart):
        if player_launch == 1:
            players[actual_player].reset_darts()
            self.save_turn(players)
        #####
        # Write your code here.
        #####
        self.logs.debug(self.infos)
        return return_code

        ###############

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Function run after each dart throw
        for example, add points to player
        Check return codes.
        0 : Next dart
        1 : Next player
        2 : Game over (last round reached)
        3 : Winner
        """
        return_code = 0
        ####
        # Main game code will be here
        ####
        players[actual_player].add_dart(player_launch, actual_round, hit)

        # You may want to keep current score (which is displayed in the last column)
        players[actual_player].add_score(self.score_map.get(hit))

        # You may want to keep the "Total Points" (Global amount of grabbed points,
        # follow the player all game long)
        players[actual_player].points += self.score_map.get(hit)

        # You may want to display score on screen
        players[actual_player].columns[player_launch -
                                       1] = [self.score_map.get(hit), 'txt']

        # You may want to count how many touches
        # Simple = 1 touch, Double = 2 touches, Triple = 3 touches
        players[actual_player].increment_hits(hit)

        # You may want to count darts played
        players[actual_player].darts_thrown += 1

        # You may want to play sound if the hit is valid
        self.display.sound_for_touch(hit)

        # It is recommended to update stats every dart thrown
        self.refresh_stats(players, actual_round)

        # Return codes are:
        #  1 - Jump to next player immediately
        #  2 - Game is over
        #  3 - There is a winner (self.winner must hold winner id)
        #  4 - The player is not allowed to play (jump to next player)
        # Return code to main loop
        return return_code

    def post_round_check(self, players, actual_round, actual_player):
        """
        post round check
        Return id of winner, None if none
        -2 : No winner, one more round (Baseball)
        -1 : No winner
        >= 0 : Id of winner
        """
        if actual_round > self.max_round:
            return -1
        else:
            return -2

    def game_stats(self, players, actual_round, scores=None):
        """
        Common Game Stats Handling - Construct stats stable and return it to be displayed
        """
        # New Score method (Sqlite DB)
        if scores is not None:
            data = {}
            for record in self.game_records:
                for player in players:
                    # Keep game name
                    data['game_name'] = self.game
                    # Construct options data
                    data['game_options'] = ""
                    for opts in self.options:
                        data['game_options'] += f'{opts}={self.options[opts]}|'
                    # Game stats must be initated at top of this file
                    data['score_name'] = record
                    # This stat is calculated like this
                    data['score'] = str(player.stats[record])
                    # Playername is obviously consigned
                    data['player_name'] = player.name
                    # Add data to Sqlite DB
                    try:
                        scores.add_score(data)
                    except:  # pylint: disable=bare-except
                        self.logs.error("Error inserting data into local database")
                        return False
        return True

    def get_player_name(self, players, ident):
        """
        Get players's info by ident
        """
        
        # --- AJOUT POUR ENNEMI GAGNE - code "return -1" dans check_winner du jeu ---
        if ident == -1:
            return "Ennemi"
            
        for player in players:
            if player.ident == ident:
                return player.name
        return ''

    def get_darts_thrown(self, players, ident):
        """
        Get player's darts thrown by ident
        """
        for player in players:
            if player.ident == ident:
                return player.darts_thrown
        return None

    def backup_round(self, players, actual_round):
        """
        Backup /restore: In case of BACK or CANCEL button pushed
                BACK   : Cancel the last dart thrown
                CANCEL : Back to first dart
        """
        if len(self.backups) < actual_round:
            self.backups.append(deepcopy(players))
        else:
            self.backups[actual_round - 1] = deepcopy(players)

    def restore_round(self, roundtorestore):
        """
        Restore
        """
        try:
            return self.backups[roundtorestore - 1]
        except:  # pylint: disable=bare-except
            try:
                return self.backups[roundtorestore]
            except:  # pylint: disable=bare-except
                try:
                    return self.backups[roundtorestore + 1]
                except:  # pylint: disable=bare-except
                    return None

    def save_turn(self, players):
        """
        Backup player properties to use with BackupTurn
        """
        # Create Backup Properies Array
        try:
            self.previous_backup = deepcopy(self.backup)
        except:  # pylint: disable=bare-except
            self.logs.debug("Probably first player of first round. Nothing to backup.")
            self.previous_backup = deepcopy(players)
        self.backup = deepcopy(players)
        self.logs.debug("Backuped score in case of BackUpTurn request.")

    def early_player_button(self, players, actual_player, actual_round):
        """
        Run when player push PLAYERBUTTON before last dart
        return code :
            1. Next player
            2. Last round reach
            3. Winner is
        """
        return_code = 1
        # players[actual_player].darts_thrown += self.nb_darts - actual_round + 1
        self.display.message([self.display.lang.translate(
            'Missed !')], 1000, None, 'middle', 'big')
        self.logs.debug("You pushed player button and default action will occur.")
        if actual_round == int(self.max_round) and actual_player == self.nb_players - 1:
            self.logs.debug("At last round, default action is to return game over.")
            self.logs.debug("If it's not what you expect, raise a bug please.")
            # If its a early_player_button just at the last round - return GameOver
            return 2
        return return_code

    def miss_button(self, players, actual_player, actual_round, player_launch):
        """
        MISSED BUTTON
        """
        return_code = 0
        self.logs.debug("You missed the dart (or pressed the missbutton) and \
                default action will occur.")
        # Return same code than early_player_button and perform the same actions
        if player_launch == int(self.nb_darts):
            self.logs.debug("Running the early_player_button method because it is last dart.")
            return_code = self.early_player_button(
                players, actual_player, actual_round)
            self.logs.debug(f"Which return {return_code}")
        # Or just increment dart thrown
        else:
            players[actual_player].darts_thrown += 1
        # And return value
        return return_code

    def get_random(self, players, actual_round, actual_player, player_launch):
        """
        Returns Random things, to send to clients in case of a network game
        If there is no random values in your game, leave it like this
        """
        return None  # Means that there is no random

    def set_random(self, players, actual_round, actual_player, player_launch, data):
        """
        Set Random things, while received by master in case of a network game
        If there is no random values in your game, leave it like this
        """

    def next_set_order(self, players, new_order=None):
        """
        Define next set order
        """
        if new_order is not None:
            players.sort(key=lambda x: new_order.index(x.name))
        else:
            players.sort(key=self.get_score, reverse=True)

    def next_game_order(self, players):
        """
        Define the next game players order, depending of previous games' scores
        This function reorder players for the next match, based for exemple on final scores
        of previous game
        """
        scores = {}
        # Create a dict with player and his score
        for player in players:
            scores[player.name] = player.score
        # Order this dict depending of the score
        new_order = collections.OrderedDict(
            sorted(scores.items(), key=lambda t: t[1]))

        return list(new_order.keys())

    def check_handicap(self, players):
        """
        Check for handicap and record appropriate marks for player
        """

    def refresh_scores(self, players, actual_player, refresh=True):
        self.refresh_scores(players, actual_player, refresh=True)

    def refresh_stats(self, players, actual_round):
        """
        Method to frefresh player.stat - Adapt to the stats you want.
        They represent mathematical formulas used to calculate stats. Refreshed after every launch
        """
        for player in players:
            try:
                player.stats['Score'] = player.score
            except:  # pylint: disable=bare-except
                self.logs.debug("No Score statistic for player")

    def pnj_score(self, players, actual_player, level, player_launch):
        """
        Compute pnj score
        """

        value = random.randint(1, 20)
        multi = ''.join(random.choice('SDT') for _ in range(1))
        bull = random.randint(0, 100)
        if 85 < bull <= 95:
            return 'SB'
        if bull > 95:
            return 'DB'
        return f'{multi}{value}'

    def check_players_allowed(self, nb_players):
        """
        Check if number of players is ok according to options
        """
        return True

    def refresh_game_screen(self, players, actual_round, max_round, rem_darts, nb_darts, logo, headers, actual_player, TxtOnLogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
        """
        Refresh In-game screen
        """
        # do not show the table scores
        return self.display.refresh_game_screen(players, actual_round, max_round, rem_darts,
                                                nb_darts, logo, headers, actual_player, TxtOnLogo, Wait, OnScreenButtons,
                                                showScores, end_of_game, endOfSet, Set, MaxSet)

    def play_video(self, video):
        """
        Play video
        """
        return self.video_player.play_video(video)

    def SendTextToDmd(self, text, tempo=None, sens=None, iteration=None):
        """
        Send text to dmd
        """
        self.dmd.send_text(text, tempo, sens, iteration)

    def get_hit_unit(self, hit):
        """
        Return hit unit (1 for simple, 2 for double, and 3 for triple)
        """
        if hit[:1] in ('s', 'S'):
            return 1
        if hit[:1] == 'D':
            return 2
        if hit[:1] == 'T':
            return 3
        return 0

    def check_winner(self, players, high=True):
        '''
        Method to check WHO is the winnner
        '''
        deuce = False #égalité
        master = False #utilisé pour les jeux qui disent score = winscore
        print(f"check_winner self.options : {self.options}")
        if 'master' in self.options: # master , true or false , le score doit etre egale pour gagner
            if self.options['master']:
                master = True
            self.logs.debug(f"check_winner master is in self.options with value = {master}")

        if 'winscore' in self.options: # score minimal pour gagner
            best_score = int(self.options['winscore'])
            self.logs.debug(f"check_winner winscore is in self.options with value = {best_score}")
            if not master:
                best_score -= 1
        elif 'startingat' in self.options:
            best_score = int(self.options['startingat'])
            self.logs.debug(f"check_winner startingat is in self.options with value = {best_score}")
        elif high:
            best_score = 0
        else:
            best_score = 999999
        best_player = None
        for player in players:
            if not master :
                if (not high and player.score < best_score) or (high and player.score > best_score): # le plus gros/petit score gagne
                    best_score = player.score
                    deuce = False #necessary to reset deuce if there is a deuce with a higher score !
                    best_player = player.ident
                elif player.score == best_score:
                    deuce = True
                    best_player = None
            else: # master = True
                if player.score == best_score:
                    best_player = player.ident
                    deuce = False
                    break
# best_count not exist                
#        self.logs.debug(\
#                f"Best score : {best_score} / Count={best_count} / Player = {best_player}")
        if deuce:
            self.infos += f"There is a score deuce ! Two people have {best_score}.{self.lf}"
            self.infos += f"No winner!{self.lf}"
            return None
        return best_player
    
    def time_to_take_shot_or_video(self, hit):
        '''
        Method for indicate if you take shot or video
        True : action
        None : Nothing
        '''
        
        if hit in str(self.config.get_value('Camera', 'events')).split(','):
            return True
        else:
            return None
