# -*- coding: utf-8 -*-
'''
Game by ... poilou !
'''
# Versions
# 1.01a
# Correction du mode Deuce (permet aux joueurs de terminer leur coups avant de déclarer un vainqueur ou une égalité
# Dans le cas ou les joueurs atteignent le max round en mode Deuce, dans ce cas le meilleur score (le plus bas) sera gagnant
# Affiche en jaune les points réalisable pour renvoyer l'adversaire aux points de début de jeu lors du mode Zap (cumulable avec les verts pour arriver à zéro)
# Affichage sur l'écran de la combinaison zap
# Colorisation des joueurs pour être plus agréable avec le zap

import collections# To use OrderedDict to sort players from the last score they add
import random   # For PNJ
import pygame

from copy import deepcopy

from include import cplayer
from include import cgame
from include import cstats
from include import chandicap
from include import ctrophies  # <-- AJOUT TROPHEES
try: 
    from include import cdebug
    DEBUG = {'debug-record': False, 'debug-replay': False, 'debug-extra_info': True} 
except:
    print('Class cdebug not found in include')

VERSION = '1.01b'
# Background image - relative to images folder
LOGO = 'Ho_One.png'
# Columns headers - Must be a string
HEADERS = [ 'D1', 'D2', 'D3', '', 'Rnd', 'PPD', 'PPR' ]
# Dictionnay of options - will be used at the initial screen
OPTIONS = {'theme': 'default', 'startingat': 301, 'max_round': 20, 'double_in': False, 'double_out': False, \
        'master_in': False, 'master_out': False, 'league': False, 'split_bull': True, 'zap': False, 'equal': False, 'colorised' : True}
# Dictionnary of stats and dislay order (For exemple, avg is displayed in descending order)
GAME_RECORDS = {'Points Per Round':'DESC', 'Points Per Dart':'DESC'}
# How many darts the player is allowed to throw
NB_DARTS = 3 # How many darts the player is allowed to throw


def check_players_allowed(nb_players):
    '''
    Check if number of players is ok according to options
    '''
    return nb_players <= 8, VERSION, 8

############
# Extend the basic player's class
############
class CPlayerExtended(cplayer.Player):
    '''
    Extended Player class
    '''
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        self.pre_play_score = None
        self.unlocked = False
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record] = '0'

############
# Your Game's Class
############
class Game(cgame.Game):
    '''
    Ho One game class
    '''
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        # game_records is the dictionnary of stats (see above)
        self.game_records = GAME_RECORDS
        # Config are the are the options contained in your config file
        self.logo = LOGO
        self.headers = HEADERS
        self.options = options
        self.game_is_ok_for_color = options['colorised']        
        # For rpi
        self.nb_darts = NB_DARTS # To darts the player has to play
        self.rpi = rpi
        # Load handicap and stat classes
        self.handicap = chandicap.Handicap('Ho_One', config, self.logs)
        self.stats = cstats.Stats('Ho_One', self.logs)
        #  Get the maxiumum round number
        self.max_round = int(options['max_round'])
        self.split_bull = options['split_bull']
        self.double_out = options['double_out']
        self.master_out = options['master_out']
        self.double_in = options['double_in']
        self.master_in = options['master_in']
        self.starting_at = int(options['startingat'])
        self.league = options['league']
        self.zap = options['zap']
        self.equal = options['equal']
        self.frozen = False
        self.infos = ""
        self.winner = None
        
        # DEBUG dictionnary special for developer
        self.debug_info = False # par default
        self.debug_record = False
        self.debug_replay = False
        try:
            DEBUG
        except NameError:
            print ('Class cdebug not found in include')
        else :
            self.debuglevel = int(config.get_value('SectionGlobals', 'debuglevel', 0))
            if self.debuglevel == 2: #Ajouter les options du dictionnaire DEBUG
                #on charge les options (le dictionnaire DEBUG est inclus dans OPTIONS lorsque l'on est en debuglevel 2
                self.debug_info = options['debug-extra_info']
                # DEBUG dictionnary special for developer
                self.debug = cdebug.Debug(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
                self.debug.Pos_cible(200,250)
                self.debug_replay = options['debug-replay']
                self.debug_record = options['debug-record']
                #self.actual_round = None
                self.debug.closeFile()
                if self.debug_replay:
                    self.debug_record = False
        
        if nb_players != 4 and self.league:
            self.logs.error("League option can only be used with 4 players! Disabling league play!")
            
        elif self.league:
            self.display.teaming = True
        # Decide on BullEye value
        if not self.split_bull:
            self.score_map.update({'SB': 50})

        self.dart = self.display.file_class.get_full_filename('dart', 'images')
        self.dart_icon = self.display.file_class.get_full_filename('dart_icon', 'images')
        self.online_icon = self.display.file_class.get_full_filename('online', 'images')

        self.margin = self.display.margin
        self.margin_2 = 2 * self.display.margin
        self.margin_4 = 4 * self.display.margin

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        '''
        Actions done before each dart throw - for example, check if the player is allowed to play
        '''
        return_code = 0
        mate_score = 0
        other_team_score = 0
        self.frozen = False
        self.possible_hits = []
        self.possible_zaps = []
        # Set score at startup
        if player_launch == 1:
            players[actual_player].reset_darts()

        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                lst = self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.error(f"Handicap failed : {exception}")
            for player in players:
                # Init score
                if self.league:
                    player.score = int(lst[player.ident])
                else:
                    player.score = self.starting_at
                player.reset_rounds(self.max_round)

        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            self.save_turn(players)
            # Backup current score
            players[actual_player].pre_play_score = players[actual_player].score

            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for i in range(0, 7):
                players[actual_player].columns.append(['', 'str'])
        # Display avg
        if actual_round == 1 and player_launch == 1:
            players[actual_player].unlocked = False
            if not self.master_in and not self.double_in:
                players[actual_player].unlocked = True
            
            players[actual_player].columns[5] = (0.0, 'int')
            players[actual_player].columns[6] = (0.0, 'int')
        else:
            players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
            players[actual_player].columns[6] = (players[actual_player].show_ppr(), 'int')

        # Clean next boxes
        for i in range(player_launch - 1, self.nb_darts):
            players[actual_player].columns[i]=('', 'int')

        # Get Playing Suggestions
        # Double IN or Master IN
            
        leds = self.Sugestions_cible(players,actual_player, player_launch)
        self.rpi.set_target_leds(('|'.join(leds)))

        #Get scores for teammate and opposite team and see if freeze rule is in effect
        if self.league:
            mate = self.mate(actual_player, len(players))
            mate_score = players[mate].score
            if actual_player in (0, 2):
                other_team_score += players[1].score
                other_team_score += players[3].score
            else:
                other_team_score += players[0].score
                other_team_score += players[2].score
            #if teammatescore is not lower than other_team_score, freeze rule is active
            if mate_score >= other_team_score:
                self.logs.debug('FROZEN!!!')
                self.frozen = True
                players[actual_player].columns[3] = ('FRZ', 'str', 'game-red')
            else:
                self.frozen = False
                players[actual_player].columns[3] = ('', 'str', 'game-red')

        if self.debug_info:
            print(f"Leds = {leds}")
            self.debug.leds = [] # efface l'ancienne combinaison
            self.debug.ho_one_cible(leds,True) 
            if player_launch == 1 and actual_round == 1 and actual_player == 0:
                if self.debug_replay or self.debug_record:
                    self.debug_replay = self.debug.open_debug(self.debug_replay,self.debug_record)
                    if self.debug_replay:
                        self.actual_round = self.debug.load_debug(players,self.post_dart_check, self.nb_darts, self.Sugestions_cible)
        # Print debug output
        self.logs.debug(self.infos)
        return return_code

    def Sugestions_cible(self,players,actual_player,player_launch):
        # Get Playing Suggestions
        # Double IN or Master IN
        leds = []
        suggestion_color = players[actual_player].color
        if None != self.display.colorset['suggestion-color-allplayer']:
            suggestion_color = self.display.colorset['suggestion-color-allplayer']
        if players[actual_player].points == 0 and (self.double_in or self.master_in):
            if not players[actual_player].unlocked:
                if self.double_in:
                    leds.extend(f'D{i}#{suggestion_color}' for i in range(1, 21))

                if self.master_in:
                    leds.extend(f'T{i}#{suggestion_color}' for i in range(1, 21))
                    leds.extend(f'D{i}#{suggestion_color}' for i in range(1, 21))
                    leds.extend(f'S{l}#{suggestion_color}' for l in ['B'])
                    leds.extend(f'D{l}#{suggestion_color}' for l in ['B'])
        else :
            # Possible zap ?
            if self.zap:
                for p in players:
                    if actual_player != p.ident and p.score < players[actual_player].score:
                        zapping = self.search_possibilities(players[actual_player].score - p.score, player_launch)
                        if len(zapping) > 0: #ne prend en compte que si existe une solution
                            leds.extend(f'{key}#{players[p.ident].color}' for key in zapping)
                            self.possible_zaps.extend(f'{key}' for key in zapping)
                            self.possible_zaps.append(f'@{p.ident}|')
            # Possible win ?
            self.possible_hits = self.search_possibilities(players[actual_player].score, player_launch)

            # Display if there is a suggestion to display
            if len(self.possible_hits) >= 1:
                players[actual_player].columns[player_launch - 1] = (self.possible_hits[0], 'str', 'green')
            if len(self.possible_hits) >= 2:
                players[actual_player].columns[player_launch] = (self.possible_hits[1], 'str', 'green')
            if len(self.possible_hits) >= 3:
                players[actual_player].columns[player_launch + 1] = (self.possible_hits[2], 'str', 'green')
                
            leds.extend(f'{key}#{suggestion_color}' for key in self.possible_hits)
            
        return leds
        
    def post_pre_dart_check(self, players, actual_round, actual_player, player_launch):
        '''
        Called after player annoucement,...
        '''
        if self.rpi.target_leds != '':
            return ['PRESSURE']
        return ['NOPRESSURE']

    def pnj_score(self, players, actual_player, level, player_launch):
        '''
        Computer Strike
        '''
        # Principe :
        #   Affecter à différentes possibilités un taux de réussite :
        #   - Pneu ou pas (L'expert ne fait jamais de pneu, le noob beaucoup)
        #   - Choix du segment à toucher
        #       . en fonction du niveau
        #       . en fonction des possibilités pour finir
        #
        #   - S'il "touche" :
        #       . Simple, double ou triple en fonction du niveau
        #   - Sinon :
        #       . Définition de la marge (la fléchette sera plutôt proche ou non du segment visé)
        #       . Simple, double ou triple en fonction du niveau


        #               |             Rates                                      |
        #   Level       | Pneu  | Level |Triple|Double| Bull |neighbor1|neighbor2|
        #               |       |       |      |      |      |         |         |
        #  -------------+-------+-------+------+------+------+---------+---------+
        #   1 : noob    |   30  |  10   |  1   |   2  |  10  |   45    |   60    |
        #   2           |   15  |  25   |  5   |   8  |  25  |   58    |   72    |
        #   3           |    3  |  45   |  12  |  12  |  65  |   70    |   80    |
        #   4           |    1  |  70   |  25  |  16  |  80  |   85    |   95    |
        #   5 : Expert  |    0  |  85   |  75  |  32  |  95  |   96    |  100    |

        levels = [
                 [30, 10, 1, 2, 10, 45, 60]
                ,[15, 25, 5, 8, 25, 58, 72]
                ,[3, 45, 12, 12, 65, 70, 80]
                ,[1, 70, 25, 16, 80, 85, 95]
                ,[0, 85, 55, 32, 95, 96, 100]
                ]

        tire_rate      = levels[level - 1][0]
        level_rate     = levels[level - 1][1]
        triple_rate    = levels[level - 1][2]
        double_rate    = levels[level - 1][3]
        bull_rate      = levels[level - 1][4]
        neighbor1_rate = levels[level - 1][5]
        neighbor2_rate = levels[level - 1][6]

        tire_range    = random.randrange(100)
        level_range   = random.randrange(100)
        triple_range  = random.randrange(100)
        double_range  = random.randrange(100)
        bull_range    = random.randrange(100)

        if tire_rate > 0 and tire_range < tire_rate :
            players[actual_player].columns[player_launch - 1] = ('-', 'str')
            return 'MISS'

        possibilities = [f'{number}' for number in range (1, 21)]
        if random.randrange(100) < bull_rate :
            possibilities.append('B')
        random.shuffle(possibilities)

        # possible Win ?
        possible_hits = self.search_possibilities(players[actual_player].score, player_launch)
        target_value = ''
        number = ''
        self.logs.debug(f"possible_hits={possible_hits}")

        # Compute value to strike
        if len(possible_hits) > 0 :
            number = possible_hits[0][1::]
            if level_range <= level_rate :
                target_value = possible_hits[0]

        if target_value == '' and len(possible_hits) == 0:
            min_number = 20 - (5 - level) ** 2
            min_number = max(min_number, 1)
            number = random.randint(min_number, 20)

        # Stroke or not ?
        stroke_range = random.randrange(100)

        if target_value != '':
            score = target_value
        else:
            if number in ('B', 'SB', 'DB'):
                number = random.randint(1, 21)
            elif stroke_range <= neighbor1_rate:
                score = self.neighbors[str(number)][random.randint(0, 1)]
            elif stroke_range <= neighbor2_rate:
                score = self.neighbors[str(number)][2 + random.randint(0, 1)]
            else :
                rnd_number = random.randint(1, 21)
                while rnd_number in self.neighbors[str(number)] :
                    rnd_number = random.randint(1, 21)
                number = rnd_number

            if triple_range <= triple_rate :
                score = 'T' + str(number)
            elif double_range <= double_rate :
                score = 'D' + str(number)
            elif bull_range <= bull_rate :
                if random.randrange(100) <= triple_rate :
                    score = 'DB'
                else :
                    score = 'SB'
            else :
                score = f'S{number}'

        return score

    def update_stats(self, players, actual_player, hit):
        '''
        Updates PPR / PPD ...
        '''
        try:
            score = self.score_map[hit]
        except: # pylint: disable=bare-except
            score = 0
        players[actual_player].round_points += score
        players[actual_player].points += score
        players[actual_player].columns[4] = (players[actual_player].round_points, 'int')
        players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
        players[actual_player].columns[6] = (players[actual_player].show_ppr(), 'int')

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        '''
        Function run after each dart throw - for example, add points to player
        '''

        players[actual_player].add_dart(actual_round, player_launch, hit)
        
        ### TROPHEES
        ctrophies.process_single_dart(players[actual_player], hit)
        
        # On vérifie les trophées de volée uniquement à la 3ème fléchette
        if player_launch == 3:
            round_darts = players[actual_player].darts[-3:]
            ctrophies.check_and_unlock_trophies(players[actual_player], round_darts)
        
        
        #debug Mode
        if self.debug_info:
            if self.debug_record:
                self.debug.record(f"{actual_player}{hit}\n")
            else:
                if player_launch == 1: #se trouve en pre_dart mais en relecture on n'y repasse pas
                    players[actual_player].pre_play_score = players[actual_player].score                    
                print(f"actual_round, actual_player, hit")
                print(f"{actual_round}, {actual_player}, {hit}")
                print(f"subscore = players[actual_player].score - self.score_map[hit]")
                print(f"subscore = {players[actual_player].score} - {self.score_map[hit]}")

        # Define a var for substracted score
        subscore = players[actual_player].score - self.score_map[hit]
        #################################
        # Starting Ho One

        handler = self.init_handler()
        handler['return_code'] = 0
        
        if players[actual_player].score == self.starting_at and not players[actual_player].unlocked:
            # All good opening cases
            if not(self.double_in or self.master_in) or \
                   (  hit[:1] == 'D' or (self.master_in and (hit[:1] == 'T' or hit[1:] == 'B'))):
                handler['show'] = (players[actual_player].darts, hit, True)
                handler['sound'] = hit
                players[actual_player].score = subscore # Substract
                self.update_stats(players, actual_player, hit)
                players[actual_player].unlocked = True #empeche de devoir refaire un double / triple avec le mode Zap

                if self.zap:
                    index = 0
                    for player in players:
                        if index != actual_player and players[actual_player].score == player.score:
                            player.score = self.starting_at
                            handler['sound'] = 'zapdamn'
                            handler['message'] = f'{players[actual_player].name} : Recommence !'
                        index += 1
            else:
                handler['sound'] = 'plouf'
        # Ending Ho One
        elif subscore == 0:
            if self.frozen:
                self.infos += "You were frozen and reached zero!  You lose!"
                handler['message'] = "You were frozen and reached zero!  You lose!"
                handler['sound'] = 'whatamess'
                handler['return_code'] = 3
                if actual_player in (0, 2):
                    self.winner = players[actual_player + 1].ident
                else:
                    self.winner = players[actual_player - 1].ident
            # All closing cases
            elif    not(self.double_out or self.master_out) \
                    or ( \
                        hit[:1] == 'D' \
                        or (self.master_out and (hit[:1] == 'T' or hit[1:] == 'B')) \
                    ):
                winning_player = players[actual_player]
                winning_player.score = 0
                self.update_stats(players, actual_player, hit)

                # ==========================================
                # TROPHEES : Fin de partie en X fléchettes (Atteinte de 0)
                # ==========================================
                total_darts = winning_player.stat_darts
                ctrophies.check_ho_one_finish_trophies(winning_player, self.starting_at, total_darts, winning_dart=hit)
                
                if self.equal and actual_player < len(players)-1:
                    # Next player can equal
                    handler['return_code'] = 1 # pas le dernier joueur
                    winning_player.points -= winning_player.round_points
                else:
                    handler['return_code'] = 3
                    self.winner = winning_player.ident
                    # ==========================================
                    # STATS : Enregistrement des stats de fin de partie
                    # ==========================================
                    ctrophies.check_game_end_stats(players, winning_player, "HO-ONE")

            # else it is a fail
            else:
                # Next player
                handler['return_code'] = 1
                handler['sound'] = 'whatamess'
                players[actual_player].score = players[actual_player].pre_play_score
                players[actual_player].points -= players[actual_player].round_points
        # Case for score = 1 and *_out option enabled
        elif subscore == 1 and (self.double_out or self.master_out):
            players[actual_player].score = players[actual_player].pre_play_score
            players[actual_player].points -= players[actual_player].round_points #for ppd, ppr
            handler['return_code'] = 1
            handler['sound'] = 'whatamess'
        # Classic case (between start and end)
        elif subscore > 0:
            players[actual_player].score = subscore # Substract
            self.update_stats(players, actual_player, hit)

            if self.zap:
                index = 0
                for player in players:
                    if index != actual_player and players[actual_player].score == player.score:
                        player.score = self.starting_at
                        handler['sound'] = 'zapdamn'
                    index += 1
            if handler['sound'] is None:
                handler['sound'] = hit
                handler['show'] = (players[actual_player].darts, hit, True)
        # Any other case it is a fail
        else:
            handler['return_code'] = 1
            handler['sound'] = 'whatamess'
            players[actual_player].score = players[actual_player].pre_play_score
            players[actual_player].points -= players[actual_player].round_points #for ppd, ppr

        # Verifications des trophées de volée (tous les 3 lancers)
        if player_launch == int(self.nb_darts):
            current_darts = players[actual_player].rounds[actual_round - 1]
            ctrophies.check_and_unlock_trophies(players[actual_player], current_darts)

        #check equal mode dans le cas du dernier joueur avec 3 darts lancé ou subscore <= 0 (dépassement ou égaliser)
        if self.equal and actual_player == len(players)-1 and ((player_launch == int(self.nb_darts)) or (subscore <= 0)) and actual_round < self.max_round:
            self.winner = -1
            egalite = -1
            for p in players:
                if p.score == 0 : #score gagnant
                    self.winner = p.ident
                    egalite += 1
                    handler['return_code'] = 3 #gagnant
            if egalite > 0:  
                    handler['return_code'] = 2 #game over car égalité sur un score de 0 avec au moins 2 joueurs
                    
        # Check last round dans le cas ou celui-ci est atteint alors equal mode est ignoré
        elif actual_round == self.max_round and actual_player == self.nb_players - 1 \
                and player_launch == int(self.nb_darts):
            self.infos += f"Last round reached ({actual_round}){self.lf}"
            handler['return_code'] = 2
            self.winner = self.check_winner(players)
            if self.winner is not None:
                handler['return_code'] = 3
                # ==========================================
                # TROPHEES : Fin de partie sur dernier round
                # ==========================================
                winning_player = players[self.winner]
                total_darts = winning_player.stat_darts
                winning_dart = hit if winning_player == players[actual_player] else None
                ctrophies.check_ho_one_finish_trophies(winning_player, self.starting_at, total_darts)

                ctrophies.check_game_end_stats(players, winning_player, "HO-ONE")
                
        # Store what he played in the table
        players[actual_player].columns[player_launch - 1] = (self.score_map[hit], 'int')

        self.refresh_stats(players, actual_round)
        #debug
        if self.debug_info and handler['return_code'] > 1:
            self.debug.closeFile()

        # Time for shot or video ?
        handler['take_shot'] = self.time_to_take_shot_or_video(hit)

        return handler
    
    def check_winner(self, players):
        '''
        Method to check WHO is the winnner
        '''
        deuce = False
        best_score = self.starting_at
        best_player = None
        for player in players:
            if player.score < best_score: # le plus petit score gagne
                best_score = player.score
                deuce = False #necessary to reset deuce if there is a deuce with a higher score !
                best_player = player.ident
            elif player.score == best_score:
                deuce = True
                best_player = None
        if deuce:
            self.infos += f"There is a score deuce ! Two people have {best_score}.{self.lf}"
            self.infos += f"No winner!{self.lf}"
        return best_player # None si égalité, sinon plus petit score

    def miss_button(self, players, actual_player, actual_round, player_launch):
        '''
        Whan missed button pressed
        '''
        return_code = 0
        players[actual_player].add_dart(actual_round, player_launch, 'MISS', hit_value=0)
        self.display.play_sound('miss')
        self.logs.debug(f"MissButtonPressed : {player_launch}")
        players[actual_player].columns[player_launch - 1] = ('tyre', 'image')
        players[actual_player].darts_thrown += 1
        hit = 'MISS'
        print('CONTENU DE HIT  DEF MISS')
        print(hit)
        ### TROPHEES
        ctrophies.process_single_dart(players[actual_player], hit)
        
        # On vérifie les trophées de volée uniquement à la 3ème fléchette
        if player_launch == 3:
            round_darts = players[actual_player].darts[-3:]
            ctrophies.check_and_unlock_trophies(players[actual_player], round_darts)
        
        
        if player_launch == int(self.nb_darts):
            if self.debug_info and self.debug_record:
                self.debug.record(f"{actual_player}EPB\n") #Early player button
            return_code = self.early_player_button(players, actual_player, actual_round)
        # Or just increment dart thrown
        else:
            #players[actual_player].darts_thrown += 1
            if self.debug_info and self.debug_record:
                self.debug.record(f"{actual_player}MB\n") #miss button
        # Refresh stats
        players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
        players[actual_player].columns[6] = (players[actual_player].show_ppr(), 'int')
        self.refresh_stats(players, actual_round)
        return return_code
        
    def early_player_button(self, players, actual_player, actual_round):
        '''
        Pushed Player Early
        '''
        self.winner = -1
        if actual_round == self.max_round and actual_player == len(players) - 1:
            self.winner = self.check_winner(players)
            if self.winner != None:
                self.infos += f"Current winner is Player {self.winner}"
                return 3
            return 2
        elif actual_player == len(players) - 1: #pas au dernier tour mais un gagnant à zero est possible a cause du mode deuce
            egalite = -1
            for p in players:
                if p.score == 0 : #score gagnant
                    self.winner = p.ident
                    egalite += 1
            if egalite > 0:
                return 2 #game over egalité cas possible si il y a plus de 2 joueurs (1 et 2 à 0 , 3 fini son tour)....
            elif egalite == 0:
                return 3 #gagnant
        #rien le jeu continue
        return 1


    def search_possibilities(self, score, player_launch):
        '''
        Used to help drunken player. The same suggestions as always, found in the same order :
        the dart reaching the score is looked up in a table (all the turns of 3 darts were
        tried, 240 000 of them when no finish exists : 0.2 s on a Pi 3 at each new turn)
        '''
        #/!\return value must be iterable and must have at least 3 values
        def allowed(hit):
            return ((not self.double_out and not self.master_out) or (hit[:1] == 'D' and self.double_out)
                    or (hit[:1] in ('D', 'T') and self.master_out))
        first_hit = {}
        for hit, key in self.score_map.items():
            first_hit.setdefault(key, hit)
        # 1 dart possibility
        for hit, key in self.score_map.items():
            if score == key and allowed(hit):
                return [hit.upper()]
        finishes = [(hit, key) for hit, key in self.score_map.items() if score > key and allowed(hit)]
        # 2 darts possibilities - Player must have at least two darts left
        if player_launch in (1, 2):
            for hit, key in finishes:
                if score - key in first_hit:
                    return [first_hit[score - key].upper(), hit.upper()]
        # 3 darts possibilities - Player must have at least 3 darts left
        if player_launch == 1:
            for hit, key in finishes:
                firstrest = score - key
                for hit3, key3 in self.score_map.items():
                    if firstrest > key3 and firstrest - key3 in first_hit:
                        return [hit3.upper(), first_hit[firstrest - key3].upper(), hit.upper()]
        return []

    def refresh_stats(self, players, actual_round):
        '''
        Method to frefresh Each player.stat - Specific to every game
        '''
        for player in players:
            player.stats['Points Per Round'] = player.show_ppr()
            player.stats['Points Per Dart'] = player.show_ppd()

    def next_game_order(self, players):
        '''
        Define the next game players order, depending of previous games' score
        '''
        scores = {}
        # Create a dict with player and his score
        for player in players:
            scores[player.name] = player.score
        # Order this dict depending of the score
        new_order = collections.OrderedDict(sorted(scores.items(), \
                key=lambda t: t[1], reverse=True))
        # Return
        return list(new_order.keys())

    def get_score(self, player):
        '''
        Return score of player
        '''
        return player.score

    def next_set_order(self, players):
        '''
        Sort players for next set
        '''
        players.sort(key=self.get_score, reverse=True)

    def mate(self, actual_player, nb_players):
        '''
        Find your teammate
        '''
        mate = -1
        if actual_player < nb_players / 2:
            mate = actual_player + nb_players / 2
        else:
            mate = actual_player - nb_players / 2
        return int(mate)

    def check_handicap(self, players):
        '''
        Check for handicap and record appropriate marks for player
        '''
        self.logs.debug("Checking for handicaps!")
        # Average PPD of each player in Ho-One (trophies statistics)
        list_ppd = [ctrophies.player_average_ppd(player.name, 'ho-one') for player in players]
        return self.handicap.hoonehandicap(list_ppd, self.starting_at, players)

    def check_players_allowed(self, nb_players):
        '''
        Check if number of players is ok according to options
        '''
        if self.league and nb_players != 4:
            return False

        return nb_players <= 8

    def onscreen_buttons(self):
        '''
        On screen buttons
        '''
        # Init
        click_zones = {}

        # GAME BUTTON
        mid_x = int(self.display.res['x'] / 4) + self.margin
        mid_y = int(self.display.res['y'] * 7 / 8) + self.margin
        mid_width = int(self.display.res['x'] / 8)
        mid_x = int((self.display.res['x'] - self.margin_2 - 3 * mid_width) / 2)
        mid_height = int(self.display.res['y'] / 8) - self.margin_2

        buttons = []
        buttons.append([mid_x, mid_y, mid_width, mid_height, self.display.colorset['menu-alternate'], 'GAMEBUTTON', 'Exit'])
        mid_x += mid_width + self.display.margin
        buttons.append([mid_x, mid_y, mid_width, mid_height, self.display.colorset['menu-shortcut'], 'BACKUPBUTTON', 'Back'])
        mid_x += mid_width + self.display.margin
        buttons.append([mid_x, mid_y, mid_width, mid_height, self.display.colorset['menu-ok'], 'PLAYERBUTTON', 'Next Player'])

        for button in buttons:
            # Blit Background rect
            self.display.blit_rect(button[0], button[1], button[2], button[3], button[4], 2, self.display.colorset['menu-buttons'], self.display.alpha)
            click_zones[button[5]] = (button[0], button[1], button[2], button[3], button[4])

            # Blit button
            self.display.blit_text(button[6], button[0], button[1], button[2], button[3], self.display.colorset['menu-text-white'])
            print(f"bouton : {button[0]}/{button[1]}/{button[2]}/{button[3]}/{button[4]}")

        # Return Dict of tuples representing clickage values
        return click_zones

    def actual_player_score(self, pos_x, pos_y, width, height, heading_height, dart_icon_size, color, name, score):

        self.display.blit_rect(pos_x, pos_y, width, heading_height, color)
        self.display.blit_rect(pos_x, pos_y + heading_height, width, height - heading_height, color)
        if self.display.colorset['game-bg'] is not None:
            pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (pos_x, pos_y + heading_height), (pos_x + width, pos_y + heading_height), 2)
            pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (pos_x, pos_y), (pos_x, pos_y + height), 2)
            pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (pos_x + width, pos_y), (pos_x + width, pos_y + height), 2)
        self.display.display_image(self.dart_icon, pos_x + self.margin, pos_y + heading_height + self.margin, width=dart_icon_size, height=dart_icon_size, UseCache=True)
        self.display.blit_text(name, pos_x, pos_y - self.margin, width, heading_height + self.margin_2, color=self.display.colorset['game-bg'], align='Center')
        self.display.blit_text(score, pos_x, pos_y + heading_height, width, height - heading_height, color=self.display.colorset['game-score'], align='Right')


    def refresh_game_screen(self, players, actual_round, max_round, rem_darts, nb_darts, logo, headers, actual_player, TxtOnLogo=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):

        self.display.reset_background()

        # Scrolling dart
        screenshot1 = None
        # Fading darts (remainings)
        screenshot2 = None
        # Explosion
        screenshot3 = None
        # Darts
        screenshot4 = None
        # Actual player's score
        screenshot5 = None
        # Score
        screenshot6 = None
        rect1 = None
        rect2 = None
        rect3 = None
        rect4 = None
        rect5 = None
        rect6 = None

        game = 'Ho_One'
        hit = ''
        ppd = players[actual_player].show_ppd()
        ppr = players[actual_player].show_ppr()

        scores = players[actual_player].rounds
        score = players[actual_player].score
        darts = None
        for dart in players[actual_player].darts:
            if dart is None:
                dart = '___'
            if darts is None:
                darts = dart
            else:
                darts = f"{darts} / {dart}"

        dart = self.display.file_class.get_full_filename('dart', 'images')
        right_x = int(self.display.res['x'] * 13 / 16)
        right_y = self.margin
        right_width = int(self.display.res['x'] * 3 / 16)
        right_height = int(self.display.res['y'] / 16)

        ppdr_x = right_x + int(self.display.res['x'] * 3 / 32)

        right_mid_x = right_x + (self.display.res['x'] - right_x) / 2
        right_mid_width = (self.display.res['x'] - right_x) / 2

        game_background = f"background_{logo.replace('_', '_').replace('!', '').split('.')[0]}"
        game_background = self.display.file_class.get_full_filename(game_background, 'images')
        # The background under its veil : copied from the cache after the first time
        self.display.display_background(image=game_background, veil=self.display.colorset['game-bg'])

        self.display.blit_text(f"Round", right_x, right_y, int(right_width / 3), right_height, color=self.display.colorset['game-round'], align='Left', valign='top', margin=False)
        self.display.blit_text(f"{actual_round} / {max_round}", right_x + int(right_width / 2), 0, self.display.res['x'] - right_x - int(right_width / 2), right_height * 2, color=self.display.colorset['game-round'], align='Right', valign='top', margin=False)
        right_y += right_height

        heading_height = int(self.display.res['y'] / 24)

        # Game type
        game_width = int(self.display.res['x'] / 16)
        game_x = int(self.display.res['x'] / 2) - game_width
        game_y = self.margin
        game_height = int(self.display.res['y'] / 24)

        heading_color = self.display.colorset['game-headers']
        player_color = self.display.colorset['game-alt-headers']
        if self.display.game_type == 'online':
            self.display.display_image(self.online_icon, game_x - 40, game_y + self.margin, width=32, height=32, UseCache=True)

        self.display.blit_text(f"{self.display.game_type} game", game_x, game_y, game_width, game_height, color=(255, 0, 0), align='Center', valign='top', margin=False)

        hit_x = int(self.display.res['x'] / 4) - self.margin_2
        hit_y = int(self.display.res['y'] / 4) - self.margin_2
        hit_w = self.display.mid_x + 4 * self.margin
        hit_h = self.display.mid_y + 4 * self.margin

        # Score
        rect6 = pygame.Rect(hit_x, hit_y, hit_w, hit_h)
        sub6 = self.display.screen.subsurface(rect6)
        screenshot6 = pygame.Surface((hit_w, hit_h))
        self.display.blit_screen(screenshot6, sub6, (0, 0))

        self.display.blit_text(f'{score}', hit_x, hit_y, hit_w, hit_h, color=self.display.colorset['game-score'], align='Center')

        '''
        Display players and scores
        '''
        if not end_of_game:
            player_y = int(self.display.res['y'] / 16)
        else:
            player_y = int(self.display.res['y'] / 3)
        player_height = int(self.display.res['y'] / 8)
        player_width = int(self.display.res['x'] / max(2 * len(players), 6))
        players_x = int(self.display.res['x'] / 4 + (self.display.res['x'] / 2 - player_width * len(players) - int(player_width / 2)) / 2)

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

                self.display.blit_rect(player_x, player_y, player_width, heading_height, heading_color)
                self.display.blit_rect(player_x, player_y + heading_height, player_width, player_height - heading_height, players[player.ident].color)

                if self.display.colorset['game-bg'] is not None:
                    pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (player_x, player_y + heading_height), (player_x + player_width, player_y + heading_height), 2)
                    pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (player_x, player_y), (player_x, player_y + player_height), 2)
                    pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (player_x + player_width, player_y), (player_x + player_width, player_y + player_height), 2)

                if index < actual_player:
                    align = 'Left'
                else:
                    align = 'Right'
                #pygame.draw.line(self.display.screen, color, (player_x, player_y), (player_x + player_width, player_y), self.margin_2)
                self.display.blit_text(name, player_x, player_y - self.margin, player_width, heading_height + self.margin_2, color=player_color, align=align)
                self.display.blit_text(score, player_x, player_y + heading_height, player_width, player_height - heading_height, color=heading_color, align=align)
            else:
                # For actual player's infos
                actual_color = color
                actual_x = player_x - int(player_width / 2)
                actual_name = name
                actual_score = score
            index += 1

        # Actual player and his score
        player_y -= self.margin
        player_height += self.margin_2
        player_width *= 2
        dart_icon_size = player_height - heading_height - self.margin_2

        ppdr_width = int(self.display.res['x'] / 24)
        # Previous rounds scores
        for index in range(3):
            if end_of_game:
                continue
            if actual_round - index > 0:
                text1 = f'R{actual_round - index}'
                score = 0
                for dartx in scores[actual_round -  1 - index]:
                    if dartx is not None:
                        score += self.score_map[dartx]
                text2 = score
                self.display.blit_text(text1, right_x, right_y, ppdr_width, right_height, color=self.display.colorset['game-score'], align='Left')
                self.display.blit_text(text2, right_x + ppdr_width, right_y, ppdr_width, right_height, color=actual_color, align='Right', margin=False)

            # PPR and PPD
            if index == 1:
                self.display.blit_text(f'PPR', ppdr_x, right_y, ppdr_width, right_height, color=self.display.colorset['game-score'], align='Right')
                self.display.blit_text(f'{ppr}', ppdr_x + ppdr_width, right_y, right_width - ppdr_width, right_height, color=actual_color, align='Left')
            elif index == 2:
                self.display.blit_text(f'PPD', ppdr_x, right_y , ppdr_width, right_height, color=self.display.colorset['game-score'], align='Right')
                self.display.blit_text(f'{ppd}', ppdr_x + ppdr_width, right_y , right_width - ppdr_width, right_height, color=actual_color, align='Left')

            right_y += right_height

        # Display possibilities
        if self.debug_info:
            self.debug.ho_one_cible(affiche=True)

        if len(self.possible_hits) > 0 and not end_of_game:
            text = ' / '.join(self.possible_hits)
            possibilities_color=self.display.colorset['player9'] 
            if self.display.colorset['suggestion-color-allplayer'] is not None:
                possibilities_color=self.display.colorset['suggestion-color-allplayer']
            self.display.blit_text(f'{text}', right_x, right_y + 3 * right_height, right_width, right_height * 2, color=possibilities_color, align='Left', margin=False, Alpha = 255)
            

        # Game's options
        option_height = right_height / 2
        option_y = self.display.res['y'] - option_height

        if self.display.colorset['game-option'] is not None:
            for option, value in self.options.items():
                if option == 'theme' or value is False:
                    continue
                if value is True:
                    self.display.blit_text(f'{game}-{option}', right_x, option_y, right_width, option_height, color=self.display.colorset['menu-ok'], align='Right', margin=False, divider=1, game=game)
                else:
                    self.display.blit_text(f'{self.display.lang.translate(game + "-" + option, game)} : {value}', right_x, option_y, right_width, option_height, color=self.display.colorset['game-option'], align='Right', margin=False, divider=1, game=game)
                option_y -= option_height
        self.display.blit_text(f"{game.replace('_', ' ')}", right_x, option_y - option_height, right_width, option_height * 2, color=(255, 0, 0), align='Right', margin=False, game=game)

        # Darts' scores
        mid_x = int(self.display.res['x'] / 4) + self.margin
        mid_y = int(self.display.res['y'] * 3 / 4) + self.margin
        mid_width = self.display.mid_x - self.margin_2
        mid_height = int(self.display.res['y'] / 4) - self.margin_2

        if not end_of_game:
            min_pos_y = int(self.display.res['y'] / 32)
        else:
            min_pos_y = int(self.display.res['y'] / 3)
        max_pos_y = int(self.display.res['y'] * 31 / 32)

        round_pos_x = int(self.display.res['x'] / 32)
        round_pos_y = int(self.display.res['y'] / 32)
        round_radius = int(round_pos_x / 4)
        line_add = int(self.display.res['x'] / 64)

        '''
        Scores on scale
        '''
        rect3 = pygame.Rect(0, 0, round_pos_x + int(self.display.res['x'] / 12), self.display.res['y'])
        sub3 = self.display.screen.subsurface(rect3)
        screenshot3 = pygame.Surface((mid_width, mid_height))
        self.display.blit_screen(screenshot3, sub3, (0, 0))

        self.display.blit_text('0', 0, min_pos_y - 25, round_pos_x - self.margin, 50, color=self.display.colorset['game-player'], align='Right')
        self.display.blit_text(f'{self.starting_at}', 0, max_pos_y - 25, round_pos_x - self.margin, 50, color=self.display.colorset['game-player'], align='Right')

        pygame.draw.line(self.display.screen, self.display.colorset['game-player'], (round_pos_x, min_pos_y), (round_pos_x, max_pos_y), 3)

        t_players = deepcopy(players)
        t_players.sort(key=self.get_score, reverse=True)

        index = 0
        old_score = -100
        for player in t_players:
            score = player.score
            color = player.color

            round_pos_y = min_pos_y + int((max_pos_y - min_pos_y) * score / self.starting_at)
            text_pos_y = round_pos_y
            
            if abs(score - old_score) < 3:
                add -= int(self.display.res['x'] / 96)
            else:
                add = 0
            pygame.draw.circle(self.display.screen, color, (round_pos_x, round_pos_y), round_radius, 0)
            pygame.draw.line(self.display.screen, color, (round_pos_x, round_pos_y), (round_pos_x + line_add, round_pos_y + line_add), 5)
            pygame.draw.line(self.display.screen, color, (round_pos_x + line_add, round_pos_y + line_add), (round_pos_x + add + int(self.display.res['x'] / 12), round_pos_y + line_add), 5)
            index += 1
            old_score = score
            
        #zap display information    
        if len(self.possible_zaps) > 0 and not end_of_game and self.zap:
            text = ' / '.join(self.possible_zaps)
            lignes = text.count("|") # recherche du pipe pour couper la ligne
            posy = right_y
            while lignes > 0: #forcement superieur à 0 si du text présent (minimum text = 'S1 / |'
                ou = text.find("|") # position du pipe
                aff = text[:text.find("@")-2]
                whois = int(text[text.find("@")+1:ou]) # p.ident
                self.display.blit_text(f'{aff}', 250, (posy - 2 * right_height) + 3 * right_height, right_width, right_height, color=t_players[whois].color, align='Left', margin=False, Alpha = 255)
                text = text[ou+4:] # car suivant sera /  exemple sur 2 lignes:  S12 / | / S15 / | 
                lignes = text.count("|") # mise à jour
                posy += right_height # on saute une ligne à l'écran pour écrire la suite au cas ou

        height = int(self.display.res['y'] / 24)
        pos_y = mid_y - height

        for index in range(3):
        
            if index == rem_darts - 1:

                # scrolling dart
                rect1 = pygame.Rect(0, pos_y, self.display.res['x'], height)
                sub = self.display.screen.subsurface(rect1)
                screenshot1 = pygame.Surface((self.display.res['x'], height))
                self.display.blit_screen(screenshot1, sub, (0, 0))

                # Fading darts
                rect2 = pygame.Rect(right_x, right_y, right_width, right_height)
                sub2 = self.display.screen.subsurface(rect2)
                screenshot2 = pygame.Surface((right_width, right_height))
                self.display.blit_screen(screenshot2, sub2, (0, 0))

                # S12 / ... / ...
                rect4 = pygame.Rect(mid_x, mid_y, mid_width, mid_height)
                sub4 = self.display.screen.subsurface(rect4)
                screenshot4 = pygame.Surface((mid_width, mid_height))
                self.display.blit_screen(screenshot4, sub4, (0, 0))

                # Actual player's score
                rect5 = pygame.Rect(actual_x, player_y, player_width, player_height)
                sub5 = self.display.screen.subsurface(rect5)
                screenshot5 = pygame.Surface((player_width, player_height))
                self.display.blit_screen(screenshot5, sub5, (0, 0))
                rect5 = (actual_x, player_y, player_width, player_height, heading_height, dart_icon_size, actual_color, actual_name, actual_score)

            if index < rem_darts and not end_of_game:
                self.display.display_image(self.dart, right_x, right_y, width=right_width ,height=right_height, UseCache=True)
            right_y += right_height

        self.actual_player_score(actual_x, player_y, player_width, player_height, heading_height, dart_icon_size, actual_color, actual_name, actual_score)
        if not end_of_game:
            if OnScreenButtons:
                mid_y -= int(self.display.res['y'] / 16)

            self.display.blit_text(darts, mid_x, mid_y, mid_width, mid_height, color=self.display.colorset['game-score'], dafont=None, align='Center')

            if OnScreenButtons:
                click = self.onscreen_buttons()

        self.display.update_screen()
        self.display.save_background()

        if end_of_game:
            click = self.display.end_of_game_menu()
            return click
        # Wait if requested
        if OnScreenButtons:
            return [click, [screenshot1, rect1], [screenshot2, rect2], [screenshot3, rect3], [screenshot4, rect4], [screenshot5, rect5], [screenshot6, rect6]]
        else:
            return [[], [screenshot1, rect1], [screenshot2, rect2], [screenshot3, rect3], [screenshot4, rect4], [screenshot5, rect5], [screenshot6, rect6]]

    def draw_rect(self, rect, color):

        col = self.display.colorset[color]
        pygame.draw.line(self.display.screen, col, (rect[0], rect[1]), (rect[0] + rect[2], rect[1]), 2)
        pygame.draw.line(self.display.screen, col, (rect[0], rect[1]), (rect[0], rect[1] + rect[3]), 2)
        pygame.draw.line(self.display.screen, col, (rect[0], rect[1] + rect[3]), (rect[0] + rect[2], rect[1] + rect[3]), 2)
        pygame.draw.line(self.display.screen, col, (rect[0] + rect[2], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]), 2)

    def display_hit(self, rectangles, players, actual_player, player_launch, hit):
        '''
        Nice hit animation
        '''

        if hit == 'MISSDART':
            return
        dart = self.display.file_class.get_full_filename('dart', 'images')

        # Image size
        width = int(self.display.res['x'] / 10)
        height = int(self.display.res['y'] / 10)

        # Image movement step
        nb_steps = 25
        step = int(self.display.res['x'] / nb_steps)

        sens = -1
        min_x = int(self.display.res['x'])
        max_x = -width

        hit_x = int(self.display.res['x'] / 4) - self.margin_2
        hit_y = int(self.display.res['y'] / 4) - self.margin_2
        hit_w = self.display.mid_x + 4 * self.margin
        hit_h = self.display.mid_y + 4 * self.margin

        image = self.display.file_class.get_full_filename('trail', 'images')

        '''
        1 : Scrolling dart
        2 : Fading dart
        3 : libre
        4 : S12 / D15 / ___
        5 : Actual player score
        6 : Score (center of screen)
        '''
        screenshot1 = rectangles[1][0]
        screenshot2 = rectangles[2][0]
        screenshot3 = rectangles[3][0]
        screenshot4 = rectangles[4][0]
        screenshot5 = rectangles[5][0]
        screenshot6 = rectangles[6][0]

        rect1 = rectangles[1][1]
        rect2 = rectangles[2][1]
        rect3 = rectangles[3][1]
        rect4 = rectangles[4][1]
        rect5 = (rectangles[5][1][0], rectangles[5][1][1], rectangles[5][1][2], rectangles[5][1][3])

        heading_height = rectangles[5][1][4]
        dart_icon_size = rectangles[5][1][5]
        color = rectangles[5][1][6]
        name = rectangles[5][1][7]
        score = players[actual_player].score

        self.display.blit(screenshot5, (rect5[0], rect5[1]))
        self.actual_player_score(rect5[0], rect5[1], rect5[2], rect5[3], heading_height, dart_icon_size, color, name, score)

        rect6 = rectangles[6][1]

        self.display.blit(screenshot6, (rect6[0], rect6[1]))
        rect6 = (hit_x, hit_y, hit_w, hit_h)

        mid_x = int(self.display.res['x'] / 4) + self.margin
        mid_y = int(self.display.res['y'] * 3 / 4) + self.margin

        mid_width = self.display.mid_x - self.margin_2
        mid_height = int(self.display.res['y'] / 4) - self.margin_2

        darts = None
        for dart in players[actual_player].darts:
            if dart is None:
                dart = '___'
            if darts is None:
                darts = dart
            else:
                darts = f"{darts} / {dart}"

        # Darts : S12 / D12 / ___
        self.display.blit(screenshot4, (rect4[0], rect4[1]))
        self.display.blit_text(darts, rect4[0], rect4[1], rect4[2], rect4[3], color=self.display.colorset['game-score'], dafont=None, align='Center')

        self.display.blit_text(f'{hit}', hit_x, hit_y, hit_w, hit_h, color=self.display.colorset['game-title1'], align='Center')
        self.display.blit_text(f'{hit}', hit_x + self.margin, hit_y + self.margin, hit_w - self.margin_2, hit_h - self.margin_2, color=self.display.colorset['game-title2'], align='Center')
        self.display.blit_text(f'{hit}', hit_x + self.margin_2, hit_y + self.margin_2, hit_w - self.margin_4, hit_h - self.margin_4, color=self.display.colorset['game-score'], align='Center')
        self.display.update_screen(rect_array=[rect3, rect4, rect5, rect6])

        index = 0
        for dart_x in range(min_x, max_x, step * sens):

            # Fading dart
            dart_width = int(rect2[2] * (nb_steps - index) / nb_steps)
            dart_height = int(rect2[3] * (nb_steps - index) / nb_steps)
            offset_x = int((rect2[2] - dart_width) / 2)
            offset_y = int((rect2[3] - dart_height) / 2)

            if dart_width > 0 and dart_height > 0:
                self.display.blit(screenshot2, (rect2[0], rect2[1]))
                self.display.display_image(self.dart, rect2[0] + offset_x, rect2[1] + offset_y, dart_width, dart_height, UseCache=True)

            # Scrolling dart
            rect = (dart_x, rect1[1] , rect1[2] + 4 * step, rect1[3])
            self.display.blit(screenshot1, (rect1[0], rect1[1]))
            self.display.display_image(image, dart_x, rect1[1], rect1[2], rect1[3], UseCache=True)

            rect_array = [rect, rect2]
            self.display.update_screen(rect_array=rect_array)
            index += 1

        self.display.blit(screenshot1, (rect1[0], rect1[1]))
        self.display.blit(screenshot2, (rect2[0], rect2[1]))

        self.display.update_screen(rect_array=[rect, rect2])
        self.display.save_background()
