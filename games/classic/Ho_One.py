# -*- coding: utf-8 -*-
'''
Game by ... poilou !
'''
# Versions
# 1.01h - Version intégrale restaurée (Modes Classic et Horizontal complets + Z, A, P + Trophées)

import collections  # To use OrderedDict to sort players from the last score they add
import random       # For PNJ
import pygame

from copy import deepcopy

from include import cplayer
from include import cgame
from include import cstats
from include import chandicap
from include import ctrophies  # Trophées
try: 
    from include import cdebug
    DEBUG = {'debug-record': False, 'debug-replay': False, 'debug-extra_info': True} 
except:
    print('Class cdebug not found in include')

VERSION = '1.01h'
# Background image - relative to images folder
LOGO = 'Ho_One.png'
# Columns headers - 9 colonnes au total (SCORE séparé des colonnes Z, A, P)
HEADERS = ['D1', 'D2', 'D3', '', 'Rnd', 'Z', 'A', 'P', 'SCORE']
# Dictionnay of options - will be used at the initial screen
OPTIONS = {'theme': 'default', 'startingat': 301, 'display': 'classic', 'max_round': 20, 'double_in': False, 'double_out': False, \
        'master_in': False, 'master_out': False, 'league': False, 'split_bull': True, 'zap': False, 'equal': False, 'colorised' : True}

OPTION_CHOICES = {'display': [('horizontal', 'ho_one-display-horizontal'), ('classic', 'ho_one-display-classic')]}

# Dictionnary of stats and dislay order
GAME_RECORDS = {'Points Per Round':'DESC', 'Points Per Dart':'DESC'}
# How many darts the player is allowed to throw
NB_DARTS = 3


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
        self.has_been_zapped = False  # Suivi de l'état du zap
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
        self.game_records = GAME_RECORDS
        self.logo = LOGO
        self.headers = HEADERS
        self.options = options
        self.game_is_ok_for_color = options['colorised']        
        self.nb_darts = NB_DARTS
        self.rpi = rpi
        self.handicap = chandicap.Handicap('Ho_One', config, self.logs)
        self.stats = cstats.Stats('Ho_One', self.logs)
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
        
        self.display_mode = options.get('display', 'classic')
        
        self.debug_info = False
        self.debug_record = False
        self.debug_replay = False
        try:
            DEBUG
        except NameError:
            print ('Class cdebug not found in include')
        else :
            self.debuglevel = int(config.get_value('SectionGlobals', 'debuglevel', 0))
            if self.debuglevel == 2:
                self.debug_info = options['debug-extra_info']
                self.debug = cdebug.Debug(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
                self.debug.Pos_cible(200,250)
                self.debug_replay = options['debug-replay']
                self.debug_record = options['debug-record']
                self.debug.closeFile()
                if self.debug_replay:
                    self.debug_record = False
        
        if nb_players != 4 and self.league:
            self.logs.error("League option can only be used with 4 players! Disabling league play!")
        elif self.league:
            self.display.teaming = True

        if not self.split_bull:
            self.score_map.update({'SB': 50})

        self.dart = self.display.file_class.get_full_filename('dart', 'images')
        self.dart_icon = self.display.file_class.get_full_filename('dart_icon', 'images')
        self.online_icon = self.display.file_class.get_full_filename('online', 'images')

        self.margin = self.display.margin
        self.margin_2 = 2 * self.display.margin
        self.margin_4 = 4 * self.display.margin

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        return_code = 0
        mate_score = 0
        other_team_score = 0
        self.frozen = False
        self.possible_hits = []
        self.possible_zaps = []

        if len(players[actual_player].columns) < len(self.headers):
            players[actual_player].columns = []
            for i in range(0, len(self.headers)):
                players[actual_player].columns.append(['', 'str'])

        if player_launch == 1:
            players[actual_player].reset_darts()
            players[actual_player].has_been_zapped = False

        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                lst = self.check_handicap(players)
            except Exception as exception:
                self.logs.error(f"Handicap failed : {exception}")
            for player in players:
                if self.league:
                    player.score = int(lst[player.ident])
                else:
                    player.score = self.starting_at
                player.reset_rounds(self.max_round)

        if player_launch == 1:
            players[actual_player].round_points = 0
            self.save_turn(players)
            players[actual_player].pre_play_score = players[actual_player].score

            players[actual_player].columns = []
            for i in range(0, len(self.headers)):
                players[actual_player].columns.append(['', 'str'])

        if actual_round == 1 and player_launch == 1:
            players[actual_player].unlocked = False
            if not self.master_in and not self.double_in:
                players[actual_player].unlocked = True

        for i in range(player_launch - 1, self.nb_darts):
            players[actual_player].columns[i]=('', 'int')

        leds = self.Sugestions_cible(players, actual_player, player_launch)
        self.rpi.set_target_leds(('|'.join(leds)))

        if self.league:
            mate = self.mate(actual_player, len(players))
            mate_score = players[mate].score
            if actual_player in (0, 2):
                other_team_score += players[1].score + players[3].score
            else:
                other_team_score += players[0].score + players[2].score
            if mate_score >= other_team_score:
                self.frozen = True
                players[actual_player].columns[3] = ('FRZ', 'str', 'game-red')
            else:
                self.frozen = False
                players[actual_player].columns[3] = ('', 'str', 'game-red')

        if self.debug_info:
            print(f"Leds = {leds}")
            self.debug.leds = [] 
            self.debug.ho_one_cible(leds, True) 
            if player_launch == 1 and actual_round == 1 and actual_player == 0:
                if self.debug_replay or self.debug_record:
                    self.debug_replay = self.debug.open_debug(self.debug_replay, self.debug_record)
                    if self.debug_replay:
                        self.actual_round = self.debug.load_debug(players, self.post_dart_check, self.nb_darts, self.Sugestions_cible)
        
        self.logs.debug(self.infos)
        return return_code

    def Sugestions_cible(self, players, actual_player, player_launch):
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
            if self.zap:
                for p in players:
                    while len(p.columns) < len(self.headers):
                        p.columns.append(['', 'str'])

                for p in players:
                    if actual_player != p.ident:
                        while len(p.columns) <= 8:
                            p.columns.append(['', 'str'])
                        for col_idx in range(5, 8):
                            p.columns[col_idx] = ('', 'str')

                for p in players:
                    if actual_player != p.ident and p.score < players[actual_player].score:
                        diff_points = players[actual_player].score - p.score
                        zapping = self.search_possibilities(diff_points, player_launch)
                        
                        if len(zapping) > 0: 
                            leds.extend(f'{key}#{players[p.ident].color}' for key in zapping)
                            self.possible_zaps.extend(f'{key}' for key in zapping)
                            self.possible_zaps.append(f'@{p.ident}|')
                            
                            for i, zap_hit in enumerate(zapping):
                                target_col = 5 + i
                                while len(p.columns) <= target_col:
                                    p.columns.append(['', 'str'])
                                if target_col <= 7:
                                    p.columns[target_col] = (zap_hit, 'suggestion', players[p.ident].color)
            
            self.possible_hits = self.search_possibilities(players[actual_player].score, player_launch)

            while len(players[actual_player].columns) < player_launch + 2:
                players[actual_player].columns.append(['', 'str'])

            if len(self.possible_hits) >= 1:
                players[actual_player].columns[player_launch - 1] = (self.possible_hits[0], 'str', 'green')
            if len(self.possible_hits) >= 2:
                players[actual_player].columns[player_launch] = (self.possible_hits[1], 'str', 'green')
            if len(self.possible_hits) >= 3:
                players[actual_player].columns[player_launch + 1] = (self.possible_hits[2], 'str', 'green')
                
            leds.extend(f'{key}#{suggestion_color}' for key in self.possible_hits)
            
        return leds

    def post_pre_dart_check(self, players, actual_round, actual_player, player_launch):
        if self.rpi.target_leds != '':
            return ['PRESSURE']
        return ['NOPRESSURE']

    def pnj_score(self, players, actual_player, level, player_launch):
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

        possible_hits = self.search_possibilities(players[actual_player].score, player_launch)
        target_value = ''
        number = ''

        if len(possible_hits) > 0 :
            number = possible_hits[0][1::]
            if level_range <= level_rate :
                target_value = possible_hits[0]

        if target_value == '' and len(possible_hits) == 0:
            min_number = 20 - (5 - level) ** 2
            min_number = max(min_number, 1)
            number = random.randint(min_number, 20)

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
        try:
            score = self.score_map[hit]
        except: 
            score = 0
        players[actual_player].round_points += score
        players[actual_player].points += score
        players[actual_player].columns[4] = (players[actual_player].round_points, 'int')

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        players[actual_player].add_dart(actual_round, player_launch, hit)
        
        ctrophies.process_single_dart(players[actual_player], hit)
        
        if player_launch == 3:
            round_darts = players[actual_player].darts[-3:]
            ctrophies.check_and_unlock_trophies(players[actual_player], round_darts)
        
        if self.debug_info:
            if self.debug_record:
                self.debug.record(f"{actual_player}{hit}\n")
            else:
                if player_launch == 1: 
                    players[actual_player].pre_play_score = players[actual_player].score                    

        subscore = players[actual_player].score - self.score_map[hit]

        handler = self.init_handler()
        handler['return_code'] = 0
        
        if players[actual_player].score == self.starting_at and not players[actual_player].unlocked:
            if not(self.double_in or self.master_in) or \
                   (  hit[:1] == 'D' or (self.master_in and (hit[:1] == 'T' or hit[1:] == 'B'))):
                handler['show'] = (players[actual_player].darts, hit, True)
                handler['sound'] = hit
                players[actual_player].score = subscore 
                self.update_stats(players, actual_player, hit)
                players[actual_player].unlocked = True 

                if self.zap:
                    index = 0
                    for player in players:
                        if index != actual_player and players[actual_player].score == player.score:
                            player.score = self.starting_at
                            player.has_been_zapped = True
                            handler['sound'] = 'zapdamn'
                            handler['message'] = f'{players[actual_player].name} : Recommence !'
                        index += 1
            else:
                handler['sound'] = 'plouf'
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
            elif not(self.double_out or self.master_out) \
                    or (hit[:1] == 'D' or (self.master_out and (hit[:1] == 'T' or hit[1:] == 'B'))):
                winning_player = players[actual_player]
                winning_player.score = 0
                self.update_stats(players, actual_player, hit)

                total_darts = winning_player.stat_darts
                ctrophies.check_ho_one_finish_trophies(winning_player, self.starting_at, total_darts, winning_dart=hit)
                
                if self.equal and actual_player < len(players)-1:
                    handler['return_code'] = 1 
                    winning_player.points -= winning_player.round_points
                else:
                    handler['return_code'] = 3
                    self.winner = winning_player.ident
                    ctrophies.check_game_end_stats(players, winning_player, "HO-ONE")
            else:
                handler['return_code'] = 1
                handler['sound'] = 'whatamess'
                players[actual_player].score = players[actual_player].pre_play_score
                players[actual_player].points -= players[actual_player].round_points
        elif subscore == 1 and (self.double_out or self.master_out):
            players[actual_player].score = players[actual_player].pre_play_score
            players[actual_player].points -= players[actual_player].round_points 
            handler['return_code'] = 1
            handler['sound'] = 'whatamess'
        elif subscore > 0:
            players[actual_player].score = subscore 
            self.update_stats(players, actual_player, hit)

            if self.zap:
                index = 0
                for player in players:
                    if index != actual_player and players[actual_player].score == player.score:
                        player.score = self.starting_at
                        player.has_been_zapped = True
                        handler['sound'] = 'zapdamn'
                    index += 1
            if handler['sound'] is None:
                handler['sound'] = hit
                handler['show'] = (players[actual_player].darts, hit, True)
        else:
            handler['return_code'] = 1
            handler['sound'] = 'whatamess'
            players[actual_player].score = players[actual_player].pre_play_score
            players[actual_player].points -= players[actual_player].round_points 

        if player_launch == int(self.nb_darts):
            current_darts = players[actual_player].rounds[actual_round - 1]
            ctrophies.check_and_unlock_trophies(players[actual_player], current_darts)

        if self.equal and actual_player == len(players)-1 and ((player_launch == int(self.nb_darts)) or (subscore <= 0)) and actual_round < self.max_round:
            self.winner = -1
            egalite = -1
            for p in players:
                if p.score == 0 : 
                    self.winner = p.ident
                    egalite += 1
                    handler['return_code'] = 3 
            if egalite > 0:  
                    handler['return_code'] = 2 
                    
        elif actual_round == self.max_round and actual_player == self.nb_players - 1 \
                and player_launch == int(self.nb_darts):
            self.infos += f"Last round reached ({actual_round}){self.lf}"
            handler['return_code'] = 2
            self.winner = self.check_winner(players)
            if self.winner is not None:
                handler['return_code'] = 3
                winning_player = players[self.winner]
                total_darts = winning_player.stat_darts
                ctrophies.check_ho_one_finish_trophies(winning_player, self.starting_at, total_darts)
                ctrophies.check_game_end_stats(players, winning_player, "HO-ONE")
                
        players[actual_player].columns[player_launch - 1] = (self.score_map[hit], 'int')

        self.refresh_stats(players, actual_round)
        if self.debug_info and handler['return_code'] > 1:
            self.debug.closeFile()

        handler['take_shot'] = self.time_to_take_shot_or_video(hit)

        return handler
    
    def check_winner(self, players):
        deuce = False
        best_score = self.starting_at
        best_player = None
        for player in players:
            if player.score < best_score: 
                best_score = player.score
                deuce = False 
                best_player = player.ident
            elif player.score == best_score:
                deuce = True
                best_player = None
        if deuce:
            self.infos += f"There is a score deuce ! Two people have {best_score}.{self.lf}"
            self.infos += f"No winner!{self.lf}"
        return best_player 

    def miss_button(self, players, actual_player, actual_round, player_launch):
        return_code = 0
        players[actual_player].add_dart(actual_round, player_launch, 'MISS', hit_value=0)
        self.display.play_sound('miss')
        self.logs.debug(f"MissButtonPressed : {player_launch}")
        players[actual_player].columns[player_launch - 1] = ('tyre', 'image')
        players[actual_player].darts_thrown += 1
        hit = 'MISS'
        
        ctrophies.process_single_dart(players[actual_player], hit)
        
        if player_launch == 3:
            round_darts = players[actual_player].darts[-3:]
            ctrophies.check_and_unlock_trophies(players[actual_player], round_darts)
        
        if player_launch == int(self.nb_darts):
            if self.debug_info and self.debug_record:
                self.debug.record(f"{actual_player}EPB\n") 
            return_code = self.early_player_button(players, actual_player, actual_round)
        else:
            if self.debug_info and self.debug_record:
                self.debug.record(f"{actual_player}MB\n") 

        self.refresh_stats(players, actual_round)
        return return_code
        
    def early_player_button(self, players, actual_player, actual_round):
        self.winner = -1
        if actual_round == self.max_round and actual_player == len(players) - 1:
            self.winner = self.check_winner(players)
            if self.winner != None:
                self.infos += f"Current winner is Player {self.winner}"
                return 3
            return 2
        elif actual_player == len(players) - 1: 
            egalite = -1
            for p in players:
                if p.score == 0 : 
                    self.winner = p.ident
                    egalite += 1
            if egalite > 0:
                return 2 
            elif egalite == 0:
                return 3 
        return 1

    def search_possibilities(self, score, player_launch):
        def allowed(hit):
            return ((not self.double_out and not self.master_out) or (hit[:1] == 'D' and self.double_out)
                    or (hit[:1] in ('D', 'T') and self.master_out))
        first_hit = {}
        for hit, key in self.score_map.items():
            first_hit.setdefault(key, hit)
        for hit, key in self.score_map.items():
            if score == key and allowed(hit):
                return [hit.upper()]
        finishes = [(hit, key) for hit, key in self.score_map.items() if score > key and allowed(hit)]
        if player_launch in (1, 2):
            for hit, key in finishes:
                if score - key in first_hit:
                    return [first_hit[score - key].upper(), hit.upper()]
        if player_launch == 1:
            for hit, key in finishes:
                firstrest = score - key
                for hit3, key3 in self.score_map.items():
                    if firstrest > key3 and firstrest - key3 in first_hit:
                        return [hit3.upper(), first_hit[firstrest - key3].upper(), hit.upper()]
        return []

    def refresh_stats(self, players, actual_round):
        for player in players:
            player.stats['Points Per Round'] = player.show_ppr()
            player.stats['Points Per Dart'] = player.show_ppd()

    def next_game_order(self, players):
        scores = {}
        for player in players:
            scores[player.name] = player.score
        new_order = collections.OrderedDict(sorted(scores.items(), \
                key=lambda t: t[1], reverse=True))
        return list(new_order.keys())

    def get_score(self, player):
        return player.score

    def next_set_order(self, players):
        players.sort(key=self.get_score, reverse=True)

    def mate(self, actual_player, nb_players):
        mate = -1
        if actual_player < nb_players / 2:
            mate = actual_player + nb_players / 2
        else:
            mate = actual_player - nb_players / 2
        return int(mate)

    def check_handicap(self, players):
        self.logs.debug("Checking for handicaps!")
        list_ppd = [ctrophies.player_average_ppd(player.name, 'ho-one') for player in players]
        return self.handicap.hoonehandicap(list_ppd, self.starting_at, players)

    def check_players_allowed(self, nb_players):
        if self.league and nb_players != 4:
            return False
        return nb_players <= 8

    def onscreen_buttons(self):
        click_zones = {}
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
            self.display.blit_rect(button[0], button[1], button[2], button[3], button[4], 2, self.display.colorset['menu-buttons'], self.display.alpha)
            click_zones[button[5]] = (button[0], button[1], button[2], button[3], button[4])
            self.display.blit_text(button[6], button[0], button[1], button[2], button[3], self.display.colorset['menu-text-white'])

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
        if self.display_mode == 'horizontal':
            return self.refresh_game_screen_horizontal(players, actual_round, max_round, rem_darts, nb_darts, logo, headers, actual_player, TxtOnLogo, OnScreenButtons, showScores, end_of_game, endOfSet, Set, MaxSet)
        else:
            self.display.reset_background()
            
            screenshot1 = None
            screenshot2 = None
            screenshot3 = None
            screenshot4 = None
            screenshot5 = None
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
    
            game_background = f"background_{logo.replace('_', '_').replace('!', '').split('.')[0]}"
            game_background = self.display.file_class.get_full_filename(game_background, 'images')
            self.display.display_background(image=game_background, veil=self.display.colorset['game-bg'])
    
            self.display.blit_text(f"Round", right_x, right_y, int(right_width / 3), right_height, color=self.display.colorset['game-round'], align='Left', valign='top', margin=False)
            self.display.blit_text(f"{actual_round} / {max_round}", right_x + int(right_width / 2), 0, self.display.res['x'] - right_x - int(right_width / 2), right_height * 2, color=self.display.colorset['game-round'], align='Right', valign='top', margin=False)
            right_y += right_height
    
            heading_height = int(self.display.res['y'] / 24)
    
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
    
            rect6 = pygame.Rect(hit_x, hit_y, hit_w, hit_h)
            sub6 = self.display.screen.subsurface(rect6)
            screenshot6 = pygame.Surface((hit_w, hit_h))
            self.display.blit_screen(screenshot6, sub6, (0, 0))
    
            self.display.blit_text(f'{score}', hit_x, hit_y, hit_w, hit_h, color=self.display.colorset['game-score'], align='Center')
    
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
                    self.display.blit_text(name, player_x, player_y - self.margin, player_width, heading_height + self.margin_2, color=player_color, align=align)
                    self.display.blit_text(score, player_x, player_y + heading_height, player_width, player_height - heading_height, color=heading_color, align=align)
                else:
                    actual_color = color
                    actual_x = player_x - int(player_width / 2)
                    actual_name = name
                    actual_score = score
                index += 1
    
            player_y -= self.margin
            player_height += self.margin_2
            player_width *= 2
            dart_icon_size = player_height - heading_height - self.margin_2
    
            ppdr_width = int(self.display.res['x'] / 24)
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
    
                if index == 1:
                    self.display.blit_text(f'PPR', ppdr_x, right_y, ppdr_width, right_height, color=self.display.colorset['game-score'], align='Right')
                    self.display.blit_text(f'{ppr}', ppdr_x + ppdr_width, right_y, right_width - ppdr_width, right_height, color=actual_color, align='Left')
                elif index == 2:
                    self.display.blit_text(f'PPD', ppdr_x, right_y , ppdr_width, right_height, color=self.display.colorset['game-score'], align='Right')
                    self.display.blit_text(f'{ppd}', ppdr_x + ppdr_width, right_y , right_width - ppdr_width, right_height, color=actual_color, align='Left')
    
                right_y += right_height
    
            if self.debug_info:
                self.debug.ho_one_cible(affiche=True)
    
            if len(self.possible_hits) > 0 and not end_of_game:
                text = ' / '.join(self.possible_hits)
                possibilities_color=self.display.colorset['player9'] 
                if self.display.colorset['suggestion-color-allplayer'] is not None:
                    possibilities_color=self.display.colorset['suggestion-color-allplayer']
                self.display.blit_text(f'{text}', right_x, right_y + 3 * right_height, right_width, right_height * 2, color=possibilities_color, align='Left', margin=False, Alpha = 255)
                
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
                
                if abs(score - old_score) < 3:
                    add -= int(self.display.res['x'] / 96)
                else:
                    add = 0
                pygame.draw.circle(self.display.screen, color, (round_pos_x, round_pos_y), round_radius, 0)
                pygame.draw.line(self.display.screen, color, (round_pos_x, round_pos_y), (round_pos_x + line_add, round_pos_y + line_add), 5)
                pygame.draw.line(self.display.screen, color, (round_pos_x + line_add, round_pos_y + line_add), (round_pos_x + add + int(self.display.res['x'] / 12), round_pos_y + line_add), 5)
                index += 1
                old_score = score
                
            # zap display information en mode classic    
            if len(self.possible_zaps) > 0 and not end_of_game and self.zap:
                text = ' / '.join(self.possible_zaps)
                lignes = text.count("|") # recherche du pipe pour couper la ligne
                posy = right_y
                while lignes > 0: # forces supérieur à 0 si du texte est présent
                    ou = text.find("|") 
                    aff = text[:text.find("@")-2]
                    whois = int(text[text.find("@")+1:ou]) # p.ident d'origine
                    
                    # Correction : Trouver le bon joueur par son identifiant fixe et non par sa position dans la liste triée
                    player_color = self.display.colorset['game-score'] # couleur par défaut de secours
                    for p_item in players:
                        if p_item.ident == whois:
                            player_color = p_item.color
                            break
                            
                    self.display.blit_text(f'{aff}', 250, (posy - 2 * right_height) + 3 * right_height, right_width, right_height, color=player_color, align='Left', margin=False, Alpha = 255)
                    text = text[ou+4:] 
                    lignes = text.count("|")
                    posy += right_height # on saute une ligne à l'écran
    
            height = int(self.display.res['y'] / 24)
            pos_y = mid_y - height
    
            for index in range(3):
                if index == rem_darts - 1:
                    rect1 = pygame.Rect(0, pos_y, self.display.res['x'], height)
                    sub = self.display.screen.subsurface(rect1)
                    screenshot1 = pygame.Surface((self.display.res['x'], height))
                    self.display.blit_screen(screenshot1, sub, (0, 0))
    
                    rect2 = pygame.Rect(right_x, right_y, right_width, right_height)
                    sub2 = self.display.screen.subsurface(rect2)
                    screenshot2 = pygame.Surface((right_width, right_height))
                    self.display.blit_screen(screenshot2, sub2, (0, 0))
    
                    rect4 = pygame.Rect(mid_x, mid_y, mid_width, mid_height)
                    sub4 = self.display.screen.subsurface(rect4)
                    screenshot4 = pygame.Surface((mid_width, mid_height))
                    self.display.blit_screen(screenshot4, sub4, (0, 0))
    
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

        if self.display_mode == 'horizontal' or len(rectangles) <= 5 or rectangles[5][1] is None:
            return
            
        width = int(self.display.res['x'] / 10)
        height = int(self.display.res['y'] / 10)

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

        self.display.blit(screenshot4, (rect4[0], rect4[1]))
        self.display.blit_text(darts, rect4[0], rect4[1], rect4[2], rect4[3], color=self.display.colorset['game-score'], dafont=None, align='Center')

        self.display.blit_text(f'{hit}', hit_x, hit_y, hit_w, hit_h, color=self.display.colorset['game-title1'], align='Center')
        self.display.blit_text(f'{hit}', hit_x + self.margin, hit_y + self.margin, hit_w - self.margin_2, hit_h - self.margin_2, color=self.display.colorset['game-title2'], align='Center')
        self.display.blit_text(f'{hit}', hit_x + self.margin_2, hit_y + self.margin_2, hit_w - self.margin_4, hit_h - self.margin_4, color=self.display.colorset['game-score'], align='Center')
        self.display.update_screen(rect_array=[rect3, rect4, rect5, rect6])

        index = 0
        for dart_x in range(min_x, max_x, step * sens):
            dart_width = int(rect2[2] * (nb_steps - index) / nb_steps)
            dart_height = int(rect2[3] * (nb_steps - index) / nb_steps)
            offset_x = int((rect2[2] - dart_width) / 2)
            offset_y = int((rect2[3] - dart_height) / 2)

            if dart_width > 0 and dart_height > 0:
                self.display.blit(screenshot2, (rect2[0], rect2[1]))
                self.display.display_image(self.dart, rect2[0] + offset_x, rect2[1] + offset_y, dart_width, dart_height, UseCache=True)

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

    def refresh_game_screen_horizontal(self, players, actual_round, max_round, rem_darts, nb_darts, logo, headers, actual_player, TxtOnLogo=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
        self.display.reset_background()

        screenshot1 = None
        screenshot2 = None
        screenshot3 = None
        screenshot4 = None
        screenshot5 = None
        screenshot6 = None
        rect1 = None
        rect2 = None
        rect3 = None
        rect4 = None
        rect5 = None
        rect6 = None

        game = 'Ho_One'
        hit = ''
        player_darts = players[actual_player].darts

        cell_bg = (20, 22, 28)        
        header_bg = (35, 38, 48)      
        grid_border_color = (60, 65, 78) 

        game_background = f"background_{logo.replace('_', '_').replace('!', '').split('.')[0]}"
        game_background = self.display.file_class.get_full_filename(game_background, 'images')
        if game_background is not None:
            self.display.display_background(image=game_background)
            self.display.save_background()
        else:
            self.display.display_background()

        self.display.blit_rect(0, 0, self.display.res['x'], self.display.res['y'], self.display.colorset['game-bg'])

        title_h = int(self.display.res['y'] * 0.08)
        title_w = int(self.display.res['x'] * 0.4)
        title_x = int((self.display.res['x'] - title_w) / 2)
        title_y = int(self.margin)
        self.display.blit_text("Ho One", title_x, title_y, title_w, title_h, color=(255, 255, 255), dafont='Impact', align='Center', valign='center', margin=False)

        left_x = self.margin
        left_y = self.margin + title_h  
        left_width = int(self.display.res['x'] * 3 / 16)
        right_height = int(self.display.res['y'] / 16)

        self.display.blit_text(f"Round : {actual_round} / {max_round}", left_x, left_y, left_width, right_height, color=self.display.colorset['game-round'], dafont='Impact', align='Left', valign='top', margin=False)
        ppd_val = players[actual_player].show_ppd()
        ppr_val = players[actual_player].show_ppr()
        stats_text = f"PPD: {ppd_val} | PPR: {ppr_val}"
        self.display.blit_text(stats_text, left_x, left_y + right_height, left_width, right_height, color=(255, 255, 255), dafont='Impact', align='Left', valign='top', margin=False)
        
        game_width = int(self.display.res['x'] / 16)
        game_x = int(self.display.res['x'] / 2) - game_width
        game_y = self.margin
        game_height = int(self.display.res['y'] / 24)

        if self.display.game_type == 'online':
            self.display.display_image(self.online_icon, game_x - 40, game_y + self.margin, width=32, height=32, UseCache=True)

        self.display.blit_text(f"{self.display.game_type} game", game_x, game_y, game_width, game_height, color=(255, 0, 0), dafont='Impact', align='Center', valign='top', margin=False)

        nb_players = len(players)
        nb_headers = len(headers)
        
        fixed_total_units = (nb_headers - 1) + 3 + 2.4  
        col_w = int((self.display.res['x'] * 15 / 16) / fixed_total_units)
        score_col_w = int(col_w * 2.4) 
        table_w = int(3 * col_w + (nb_headers - 1) * col_w + score_col_w)
        
        max_slots_for_height = 9  
        table_h = int(self.display.res['y'] * 7 / 8)
        row_h = int(table_h / max_slots_for_height)
        
        actual_table_h = row_h * (nb_players + 1)
        table_x = int((self.display.res['x'] - table_w) / 2)
        table_y = int((self.display.res['y'] - actual_table_h) / 2) + int(self.display.res['y'] / 16)
        
        for col_idx, header in enumerate(headers):
            if col_idx == nb_headers - 1:
                current_col_w = score_col_w
                cx = table_x + 3 * col_w + (nb_headers - 1) * col_w
            else:
                current_col_w = col_w
                cx = table_x + (col_idx + 3) * col_w

            cy = table_y
            
            self.display.blit_rect(cx, cy, current_col_w, row_h, header_bg)
            pygame.draw.rect(self.display.screen, grid_border_color, (cx, cy, current_col_w, row_h), 1)
            if header:
                self.display.blit_text(header, cx, cy, current_col_w, row_h, color=(255, 255, 255), dafont='Impact', align='Center')

        for p_idx, player in enumerate(players):
            ry = table_y + (p_idx + 1) * row_h
            is_active = (p_idx == actual_player)
            
            name_bg_color = player.color if is_active else cell_bg
            self.display.blit_rect(table_x, ry, col_w * 3, row_h, name_bg_color)
            pygame.draw.rect(self.display.screen, grid_border_color, (table_x, ry, col_w * 3, row_h), 1)
            self.display.blit_text(player.name, table_x + self.margin, ry, col_w * 3 - self.margin_2, row_h, color=(255, 255, 255), dafont='Impact', align='Left')
            
            for c_idx in range(nb_headers):
                if c_idx == nb_headers - 1:
                    current_col_w = score_col_w
                    cx = table_x + 3 * col_w + (nb_headers - 1) * col_w
                else:
                    current_col_w = col_w
                    cx = table_x + (c_idx + 3) * col_w

                if c_idx == nb_headers - 1:
                    col_bg_color = player.color if is_active else header_bg
                else:
                    col_bg_color = cell_bg

                self.display.blit_rect(cx, ry, current_col_w, row_h, col_bg_color)
                pygame.draw.rect(self.display.screen, grid_border_color, (cx, ry, current_col_w, row_h), 1)
                
                if c_idx == nb_headers - 1:
                    self.display.blit_text(str(player.score), cx, ry, current_col_w, row_h, color=(255, 255, 255), dafont='Impact', align='Center')
                elif c_idx < len(player.columns):
                    val = player.columns[c_idx][0] if len(player.columns[c_idx]) > 0 else ''
                    col_type = player.columns[c_idx][1] if len(player.columns[c_idx]) > 1 else 'text'
                    current_header = headers[c_idx] if c_idx < len(headers) else ''

                    if current_header in ['Z', 'A', 'P']:
                        display_val = ""
                        if is_active:
                            display_val = "-"
                            c_color = self.display.colorset['game-score']
                        else:
                            if col_type == 'suggestion' and val != '':
                                display_val = val
                                c_color = player.columns[c_idx][2] if len(player.columns[c_idx]) > 2 else self.display.colorset['game-score']
                            elif getattr(player, 'has_been_zapped', False):
                                zap_image = self.display.file_class.get_full_filename('zap', 'images')
                                icon_size = int(row_h * 0.8)
                                self.display.display_image(zap_image, cx + int((current_col_w - icon_size) / 2), ry + int((row_h - icon_size) / 2), width=icon_size, height=icon_size, UseCache=True)
                            else:
                                display_val = "-"
                                c_color = self.display.colorset['game-score']

                        if isinstance(c_color, str):
                            c_color = self.display.colorset.get(c_color, self.display.colorset['game-score'])
                        
                        self.display.blit_text(str(display_val), cx, ry, current_col_w, row_h, color=c_color, dafont='Impact', align='Center')
                    else:
                        if col_type == 'image':
                            self.display.blit_text("MISS", cx, ry, current_col_w, row_h, color=(255, 0, 0), dafont='Impact', align='Center')
                        else:
                            c_color = player.columns[c_idx][2] if len(player.columns[c_idx]) > 2 else self.display.colorset['game-score']
                            if isinstance(c_color, str):
                                c_color = self.display.colorset.get(c_color, self.display.colorset['game-score'])
                            self.display.blit_text(str(val), cx, ry, current_col_w, row_h, color=c_color, dafont='Impact', align='Center')

            if is_active:
                pygame.draw.rect(self.display.screen, player.color, (table_x, ry, table_w, row_h), 3)

        if self.debug_info:
            self.debug.ho_one_cible(affiche=True)

        right_width_opt = int(self.display.res['x'] * 3 / 16)

        if len(self.possible_hits) > 0 and not end_of_game:
            text = ' / '.join(self.possible_hits)
            pred_width = int(table_w * 0.8)  
            pred_x = table_x + int((table_w - pred_width) / 2)
            pred_y = table_y - right_height - self.margin  
            full_text = f"Finish : {text}"
            self.display.blit_text(full_text, pred_x, pred_y, pred_width, right_height, color=(255, 255, 255), dafont='Impact', align='Center', margin=False, Alpha=255)

        right_x_opt = int(self.display.res['x'] * 13 / 16)
        small_box_w = int(right_width_opt / 2.7)
        small_box_h = int(right_height * 1.1)
        
        for i in range(3):
            bx = right_x_opt + i * (small_box_w - 5) - 25
            by = self.margin + 5
            self.display.blit_rect(bx, by, small_box_w - 4, small_box_h, cell_bg)
            pygame.draw.rect(self.display.screen, grid_border_color, (bx, by, small_box_w - 4, small_box_h), 1)
            
            val_dart = player_darts[i] if i < len(player_darts) and player_darts[i] is not None else ''
            if val_dart != '':
                self.display.blit_text(str(val_dart), bx, by, small_box_w - 4, small_box_h, color=self.display.colorset['game-score'], dafont='Impact', align='Center')

        if not end_of_game:
            if OnScreenButtons:
                click = self.onscreen_buttons()

        self.display.update_screen()
        self.display.save_background()

        if end_of_game:
            click = self.display.end_of_game_menu()
            return click
        if OnScreenButtons:
            return [click, [screenshot1, rect1], [screenshot2, rect2], [screenshot3, rect3], [screenshot4, rect4], [screenshot5, rect5], [screenshot6, rect6]]
        else:
            return [[], [screenshot1, rect1], [screenshot2, rect2], [screenshot3, rect3], [screenshot4, rect4], [screenshot5, rect5], [screenshot6, rect6]]
