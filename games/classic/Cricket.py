# -*- coding: utf-8 -*-
"""
Game by poilou
"""

import random
import collections
import pygame
from copy import deepcopy
from include import cgame
from include import cplayer
from include import chandicap
from math import sqrt

from include import ctrophies

LOGO = 'Cricket'
HEADERS = ['20', '19', '18', '17', '16', '15', 'B']
OPTIONS = {'theme': 'default', 'max_round': 20, 'optioncrazy': False, 'optioncutthroat': False, 'drinkscore': 200,
        'Teaming': False, 'optionteamscore': False, 'optionhandicap': False, 'mpr': False, 'colorised': False}
NB_DARTS = 3
GAME_RECORDS = {'MPR': 'DESC', 'Hits per round': 'DESC', 'GiveOut': 'ASC'}

VERSION = '1.00'

def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
    """
    return nb_players >= 1 and nb_players <= 8, VERSION, 8

class CPlayerExtended(cplayer.Player):
    """
    Extend the basic player
    """
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        self.pay_drink = False  # Flag used to know if player has reached the drink score
        self.distrib_points = 0  # COunt how many points the player gave to the others (cut throat)
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record] = '0'

class Game(cgame.Game):
    """
    Cricket game class
    """
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.handicap = chandicap.Handicap('Cricket', config, logs)
        self.game_records = GAME_RECORDS
        self.nb_darts = NB_DARTS  # Total darts the player has to play
        self.logo = LOGO
        self.headers = HEADERS[:]
        self.nb_players = nb_players
        # For rpi
        self.raspberry = rpi
        self.logs = logs
        self.options = options

        #Options
        self.cutthroat = options['optioncutthroat']
        if nb_players % 2 == 1:
            self.teaming = False
        else:
            self.teaming = options['Teaming']
        self.teamscore = options['optionteamscore']
        self.crazy = options['optioncrazy']
        self.handicap = options['optionhandicap']
        self.show_mpr = options['mpr']
        self.drink_score = int(options['drinkscore'])
        self.game_is_ok_for_color = options['colorised']

        #  Get the maxiumum round number
        self.max_round = int(options['max_round'])
        # TEMP - place it somwhere else - prevent option to be activated in case of
        # odd number of players
        if not self.teaming:
            self.teamscore = False
        else:
            self.display.teaming = True

        self.winner = None
        self.infos = ''
        self.to_randomize = []

        self.trail = self.display.file_class.get_full_filename('trail', 'images')
        self.dart = self.display.file_class.get_full_filename('dart3', 'images')
        self.dart_icon = self.display.file_class.get_full_filename('dart_icon', 'images')
        self.online_icon = self.display.file_class.get_full_filename('online', 'images')

        self.margin = self.display.margin
        self.margin_2 = 2 * self.display.margin
        self.margin_4 = 4 * self.display.margin

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Post dart check
        """

        handler = self.init_handler()
        # Find teamMate (only for teaming)
        mate = self.mate(actual_player, len(players))
        # Init
        play_closed = False  # Should we play the closed sound ?
        play_open = False  # Should we play the open sound ?
        play_hit = True  # Should we play the Double & triple sound ?
        play_scored = False  # Should we play the Scored sound ?
        
        ### TROPHEE
        ctrophies.process_single_dart(players[actual_player], hit)
        
        # On vérifie les trophées de volée uniquement à la 3ème fléchette
        if player_launch == 3:
            round_darts = players[actual_player].darts[-3:]
            ctrophies.check_and_unlock_trophies(players[actual_player], round_darts)

        touchcount4total = False
        self.infos = f"Player {players[actual_player].ident} -\
                Score before playing: {players[actual_player].score}\n"

        to_add, value = self.split_key(hit, multiplier=True)
        hit_value = 0
        
        ####TROPHEE pas utiliser handler car envoie diffrent
        if player_launch == self.nb_darts:
            ctrophies.check_cricket_mickey_mark(players[actual_player], players[actual_player].darts, self)
        


        ### TROPHEE pas utiliser handler car envoie diffrent
        if player_launch == self.nb_darts:
            ctrophies.check_cricket_mickey_mark(players[actual_player], players[actual_player].darts, self)
        
        


        #If this column is currently displayed - Valid key
        if value in self.headers and self.get_column_state(actual_player, players, self.headers.index(value)) < 4:
            # Launch animation
            self.ok = True
            # column touched
            column_hit = self.headers.index(value)
            # Add points ?
            overtouched = max(players[actual_player].get_col_value(column_hit) + to_add - 3, 0)

            hit_value = min(to_add, 3 - players[actual_player].get_col_value(column_hit))

            if players[actual_player].get_col_value(column_hit) + to_add >= 3 \
                    and players[actual_player].get_col_value(column_hit) < 3:
                # column is closed
                play_open = True
            else:
                # open and not closed : increment
                play_hit = True

            if self.crazy and value != 'B' and not play_closed:
                self.to_randomize.append(value)

            if self.teaming:
                mate = self.mate(players[actual_player].ident, len(players))
                mate_closed = players[mate].get_col_value(column_hit) >= 3

            # Increase column
            if players[actual_player].get_col_value(column_hit) < 3:
                players[actual_player].increment_column_touch(column_hit, \
                        min(to_add, 3 - players[actual_player].get_col_value(column_hit)))

                if self.teaming and self.teamscore:
                    # Do the same for mate's column
                    players[mate].increment_column_touch(column_hit, \
                        min(to_add, 3 - players[mate].get_col_value(column_hit)))

            if self.get_column_state(actual_player, players, self.headers.index(value)) > 3:
                overtouched = 0
                play_closed = True
            else:
                hit_value += overtouched

            # Add points ? Only if column is already open
            if overtouched > 0:
                # Score to add
                score_to_add = overtouched * self.score_map[f'S{value}']

                play_scored = True
                if not self.teaming:
                    if self.cutthroat:
                        index = 0
                        for player in players:
                            if index != actual_player and players[index].get_col_value(column_hit) < 3:
                                players[index].add_score(score_to_add)
                            index += 1
                    else:
                        players[actual_player].add_score(score_to_add)

                elif mate_closed or self.teamscore:
                    if self.teamscore and not self.cutthroat:
                        players[actual_player].add_score(score_to_add)
                        players[mate].add_score(score_to_add)

                    elif self.cutthroat:
                        index = 0
                        for player in players:
                            if index != actual_player and index != mate and players[index].get_col_value(column_hit) < 3:
                                players[index].add_score(score_to_add)
                            index += 1
                    else:
                        players[actual_player].add_score(score_to_add)
                else:
                    play_scored = False

            # Add hit
            players[actual_player].roundhits += 1

            # Actual player is up to date
            ###################################################################

            # For fun, if the player reached the required drink score (usually 500),
            # tell him to pay a drink !
            if not players[actual_player].pay_drink and \
                    players[actual_player].score >= self.drink_score and self.cutthroat:
                players[actual_player].pay_drink = True
                handler['sound'] = 'diegoaimaboir'

            # Added buttons if the player had a surplus (common to Cut Throat and Normal Mode)
            if overtouched > 0 and touchcount4total:
                # We add his extra hits to his total since they counted (players took points)
                play_hit = True  # Its a valid hit, play sound

            # Sound handling to avoid multiple sounds playing at a time
            if play_closed:
                handler['sound'] = 'closed'
            elif play_scored:
                handler['sound'] = 'very_deep'
            elif play_open:
                handler['sound'] = 'open'
            elif play_hit:
                handler['show'] = (players[actual_player].darts, hit, True)
                handler['sound'] = hit
            else:
                handler['sound'] = 'plouf'
        else:
            handler['sound'] = 'plouf'

        # Count darts played
        players[actual_player].add_dart(actual_round, player_launch, hit, hit_value=hit_value)

        # It is recommanded to update stats evry dart thrown
        self.refresh_stats(players, actual_round)

        self.infos += f"Hit: {hit} - Active Columns: \
                {self.headers}{self.lf}"
        self.infos += f"Total number of hits for this player: \
                {players[actual_player].get_total_hit()}{self.lf}"
        self.infos += f"Number of darts thrown from this player: {player_launch}{self.lf}"
        self.infos += f"Number of total darts thrown from this player: \
                {players[actual_player].darts_thrown}{self.lf}"

        # If it was last throw and no touch : play sound for "round missed"
        if player_launch == self.nb_darts and players[actual_player].roundhits == 0:
            handler['sound'] = 'chaussette'

        # Check if there is a winner
        winner = self.check_winner(players, actual_round, actual_player, player_launch)
        if winner is not None:
            self.infos += f"Player {winner} wins !{self.lf}"
            self.winner = winner
            
            ### TROPHEES DE VICTOIRE ---
            if not self.teaming:
                if self.winner < len(players):
                    winning_player = players[self.winner]
                    ctrophies.check_game_end_stats(players, winning_player, "CRICKET")
            else:
                mate_idx = self.mate(self.winner, len(players))
                winning_names = [players[self.winner].name, players[mate_idx].name]
                ctrophies.check_team_game_end_stats(players, winning_names, "CRICKET")
                

            handler['return_code'] = 3

        # Last throw of the last round
        elif actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and player_launch == self.nb_darts:
            self.infos += f"Last Round Reached ({actual_round}{self.lf}"
            handler['return_code'] = 2

        # Display Recap text
        self.logs.debug(self.infos)

        # Time for shot or video ?
        handler['take_shot'] = self.time_to_take_shot_or_video(hit)

        # And return code
        return handler

    def nb_touch(self, player):
        """
        Count number of valid touch
        """
        nb_hit = 0
        closed = True
        for column in range(0, int(self.nbcol) + 1):
            nb_hit += int(player.columns[column][0])
            if int(player.columns[column][0]) < 3:
                closed = False

        return (nb_hit, closed)

    def check_winner(self, players, actual_round, actual_player, player_launch):
        """
        Method to check if there is a winnner
        Round  player 1   player 2     resultat
        1-20    f 700       150        p1 gagne, le jeu stop car fermé et score p1 > p2
        1-20    f 30        150        le jeu continu jusqu'au round 20, ou p1 > p2, ou p2 ferme. Puis meilleur score gagne
        20      f 30        150        p2 gagne car meilleur score
        20        150       180        p2 gagne car meilleur score
        """
        # doit retourner None en cas d'égalité
        winner_id = None
        index = 0
        if self.teaming:
            max_player = int(len(players) / 2)
            teams = []
            for team_id in range(0, max_player):
                mate = self.mate(team_id, len(players))
                closed = self.nb_touch(players[team_id])[1] and self.nb_touch(players[mate])[1]
                score = players[team_id].score + players[mate].score
                teams.append((team_id, closed, score))

            for team_id in range(0, max_player):
                if winner_id is not None and score == teams[winner_id][2]:
                    best.append(teams[team_id])
                elif winner_id is None \
                    or (teams[team_id][2] < teams[winner_id][2] and self.cutthroat) \
                    or (teams[team_id][2] > teams[winner_id][2] and not self.cutthroat):
                        best = []
                        best.append(teams[team_id])
                        winner_id = team_id

            winners = []
            for team in best:
                if team[1]:   # All closed
                    winners.append(team[0])
        else:
            # Find the best score
            for player in players:
                if winner_id is not None and player.score == players[winner_id].score:
                    # Same score
                    best.append((player.ident, self.nb_touch(player)))
                elif winner_id is None \
                    or (player.score < players[winner_id].score and self.cutthroat) \
                    or (player.score > players[winner_id].score and not self.cutthroat):
                    best = []
                    best.append((player.ident, self.nb_touch(player)))
                    winner_id = index
                index += 1

            winners = []
            for player in best:
                if player[1][1]:   # All closed
                    winners.append(player[0])

        # If the player who have the best score has closed all the gates
        if len(winners) == 1: # and winners[0] == actual_player:
            return winners[0]
        else:
            # Ajout score si fin (not All closed)
            if actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                   and player_launch == self.nb_darts:
                if self.cutthroat:
                    best_score = 99999
                else:
                    best_score = -1
                #
                if self.teaming:
                    for team_id in range(0, max_player):
                        if (teams[team_id][2] >= best_score and not self.cutthroat) \
                               or(teams[team_id][2] <= best_score and self.cutthroat):
                            if teams[team_id][2] != best_score:
                                best_score = teams[team_id][2]
                                winner_id = team_id
                            else:
                                winner_id = None #egalité
                else:
                    for player in players:
                        if (player.score >= best_score and not self.cutthroat) \
                               or (player.score <= best_score and self.cutthroat):
                            if player.score != best_score:
                                best_score = player.score
                                winner_id = player.ident
                            else:
                                #egalité must return None
                                winner_id = None
                return winner_id
        return None

    def random_header(self, actual_player, players, force=False, columns=None):
        """
        New RandomHeader Method that use the get_column_state internal method to check column.
        More reliable.
        """
        for column in range(0, int(self.nbcol)):
            if columns is None or self.headers[column] in self.to_randomize:
                self.infos += f"Working on column {column}{self.lf}"
                # Check state of column (none, open or closed)
                randomize = self.get_column_state(actual_player, players, column) == 2

                # Randomizing column...
                if randomize or force:
                    self.infos += f"Column {column} will randomize.{self.lf}"
                    while True:
                        random_number = random.randint(1, 20)
                        if str(random_number) not in self.headers:
                            self.headers[column] = str(random_number)
                            break
                else:
                    self.infos += f"Column {column} will not be randomized.{self.lf}"

    def get_column_state(self, actual_player, players, col):
        """
        Get state of column. It can be :
        1 : Not open
        2 : Open,
        3 : Closed by a player or a team
        4 : Closed by everybody
        """
        # Init
        state = 1
        nb_closed = 0
        index = 0
        # Loop on players
        for player in players:
            # Get Mate if Teaming enabled
            if self.teaming:
                if index >= int(len(players) / 2):
                    break
                mate = self.mate(index, len(players))
                self.infos += f"Analyse players {index} and {mate}{self.lf}"
                self.infos += f"Columns are {player.get_col_value(col)} and {players[mate].get_col_value(col)}{self.lf}"
                # TEAMING CASE 1 - state can only go upper
                if player.get_col_value(col) in [1, 2]:
                    self.infos += f"[TEAMING] This column {col} is OPEN for at least player \
                            {player.name}!{self.lf}"
                    state = max(state, 2)
                # NOTEAMING CASE 2
                if player.get_col_value(col) == 3 and players[mate].get_col_value(col) == 3:
                    state = max(state, 3)
                    nb_closed += 2
                    self.infos += f"[TEAMING] This column {col} is CLOSED by both players \
                            {player.name} and {players[mate].name} !{self.lf}"
                elif player.get_col_value(col) == 3 and players[mate].get_col_value(col) < 3:
                    state = max(state, 2)
                    self.infos += f"[TEAMING] This column {col} is CLOSED by one player only{self.lf}"
            else:
                # NOTEAMING CASE 1
                if player.get_col_value(col) in [1, 2]:
                    self.infos += f"[NOTEAMING] This column {col} is still OPEN (marked) by \
                            at least player {player.name}!{self.lf}"
                    state = max(state, 2)
                # NOTEAMING CASE 2
                elif player.get_col_value(col) == 3:
                    state = max(state, 3)
                    nb_closed += 1
                    self.infos += f"[NOTEAMING] This column {col} is CLOSED by at least \
                            player {player.name} !{self.lf}"
            index += 1

        if nb_closed == len(players):
            state = 4
            self.infos += f"ALL PLAYERS (OR TEAM) has closed this column {col} !{self.lf}"

        return state

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Action launched before each dart throw
        """
        self.infos = ""
        self.ok = False
        # If first round - set display as leds
        if player_launch == 1 and actual_round == 1 and actual_player == 0:
            for player in players:
                for column, value in enumerate(player.columns):
                    player.columns[column] = [0, 'leds', 'game-grey2']
                player.reset_rounds(self.max_round)
            if self.handicap and self.teaming:
                self.check_handicap(players)

        if player_launch == 1:
            if (self.crazy and actual_player > 0 or actual_round > 1) and not self.random_from_net:
                self.random_header(actual_player, players, columns=self.to_randomize)
            elif self.crazy and not self.random_from_net:
                self.random_header(actual_player, players, True)
            else:
                self.headers = HEADERS[:]

            self.to_randomize = []
            # Reset number of hits in this round for this player
            players[actual_player].roundhits = 0
            players[actual_player].reset_darts()

            self.infos += f"Active columns : {self.headers}"
            self.logs.debug(self.infos)
            self.save_turn(players)

        leds = []
        ind = 0
        for header in self.headers:
            already_closed = 0
            test_player = 0
            column_state = self.get_column_state(actual_player, players, ind)
            for player in players:
                if test_player != actual_player:
                    if isinstance(player.get_col_value(ind), int) and \
                            player.get_col_value(ind) >= 3:
                        already_closed += 1
                test_player += 1

            if column_state == 4:
                # Closed by everyone
                pass
            elif int(players[actual_player].get_col_value(ind)) < 3 and self.teaming:
                mate = self.mate(actual_player, len(players))
                if column_state == 3:
                    leds.extend([f'{mult}{header}#{self.colors[2]}' for mult in ['E', 'S', 'D', 'T']])
                elif int(players[mate].get_col_value(ind)) == 3:
                    #Closed by mate
                    leds.extend([f'{mult}{header}#{self.colors[3]}' for mult in ['E', 'S', 'D', 'T']])
                else:
                    leds.extend([f'{mult}{header}#{self.colors[0]}' for mult in ['E', 'S', 'D', 'T']])

            elif int(players[actual_player].get_col_value(ind)) < 3 and not self.teaming:
                # Open for player
                if column_state == 3:
                    # And closed by one other
                    # Blue
                    leds.extend([f'{mult}{header}#{self.colors[2]}' for mult in ['E', 'S', 'D', 'T']])
                else:
                    # Green
                    leds.extend([f'{mult}{header}#{self.colors[0]}' for mult in ['E', 'S', 'D', 'T']])

            elif column_state == 2:
                pass
            elif self.teaming:
                mate = self.mate(actual_player, len(players))
                if int(players[actual_player].get_col_value(ind)) == 3 and int(players[mate].get_col_value(ind)) < 3:
                    pass
                elif column_state == 3 and int(players[actual_player].get_col_value(ind)) < 3:
                    leds.extend([f'{mult}{header}#{self.colors[2]}' for mult in ['E', 'S', 'D', 'T']])
                elif column_state == 3:
                    leds.extend([f'{mult}{header}#{self.colors[1]}' for mult in ['E', 'S', 'D', 'T']])
            else:
                leds.extend([f'{mult}{header}#{self.colors[1]}' for mult in ['E', 'S', 'D', 'T']])

            ind += 1
            self.raspberry.set_target_leds(('|'.join(leds)))

    def post_pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Called after player annoucement,...
        """
        if self.can_win(players[actual_player], self.nb_darts - player_launch + 1):
            return ['PRESSURE']
        return ['NOPRESSURE']

    def pnj_score(self, players, actual_player, level, player_launch):
        # =========================================================================
        # GUIDE DE RÉGLAGE DES NIVEAUX DE DIFFICULTÉ :
        # - Légende : [Taux de pneu/raté complet (tyre), Taux d'échec/déviation (failure), 
        #              Taux d'ouverture (open), Taux de fermeture (close), Taux max (max), 
        #              Taux de points (points), Taux Triple (triple), Taux Double (double), Taux Bull (bull)]
        # - Plus fort / précis : Diminuer tyre et failure, augmenter les taux de réussite, triples et doubles.
        # - Plus humain / brouillon : Augmenter tyre et failure, baisser les taux tactiques.
        # =========================================================================
        # Niveaux progressifs : [tyre, failure, open, close, max, points, triple, double, bull]
        levels = [
                    [35, 70,  2, 0, 1, 0,  1,  2, 30],  # 1 : Noob (70% échec)
                    [20, 45, 10, 1, 15, 3,  3,  5, 45],  # 2 : Débutant (45% échec)
                    [8,  25, 30, 4, 35, 7,  8, 10, 60],  # 3 : Intermédiaire (25% échec)
                    [2,  10, 60, 8, 65, 15, 18, 20, 80],  # 4 : Pro (10% échec)
                    [0,   2, 90, 15, 95, 25, 32, 30, 95]   # 5 : Expert (2% échec)
                ]

        tyre_rate = levels[level - 1][0]
        failure_rate = levels[level - 1][1]
        open_rate = levels[level - 1][2]
        close_rate = levels[level - 1][3]
        max_rate = levels[level - 1][4]
        points_rate = levels[level - 1][5]
        triple_rate = levels[level - 1][6]
        double_rate = levels[level - 1][7]
        bull_rate = levels[level - 1][8]
        tyre_range = random.randrange(100)

        if tyre_rate > 0 and tyre_range < tyre_rate:
            return 'MISS'

        scores = {}
        my_score = players[actual_player].get_score()
        opponent_scores = [p.get_score() for p in players if p.ident != actual_player]
        
        if not opponent_scores:
            opponent_scores = [0]

        # Calcul de l'écart et de la position (seuil à 50 points)
        if self.cutthroat:
            best_opp_score = min(opponent_scores)
            diff = my_score - best_opp_score
            is_behind = diff > 0  
            is_far_ahead = diff < -50  
        else:
            best_opp_score = max(opponent_scores)
            diff = my_score - best_opp_score
            is_behind = diff < 0  
            is_far_ahead = diff > 50   

        # --- FILTRE DES COLONNES TOTALEMENT FERMÉES ---
        valid_headers = []
        for index, header in enumerate(self.headers):
            # En Cricket, pas de colonnes T et D, on traite tous les headers standards (nombres + B)
            is_completely_closed = True
            for player in players:
                if player.get_col_value(index) < 3:
                    is_completely_closed = False
                    break
            
            if not is_completely_closed:
                valid_headers.append(header)

        # --- CONSTITUTION DES POSSIBILITÉS DE TIR ---
        possibilities = list(valid_headers)
        if random.randrange(100) < bull_rate and 'B' in self.headers:
            bull_idx = self.headers.index('B') if 'B' in self.headers else -1
            if bull_idx != -1:
                if not all(p.get_col_value(bull_idx) >= 3 for p in players):
                    possibilities.append('B')

        # --- ÉVALUATION DES SCORES DE CHAQUE CIBLE ---
        for poss in possibilities:
            numeric_val = int(poss) if poss.isdigit() else (25 if poss == 'B' else 0)
            score = numeric_val * 5  
            
            col_idx = self.headers.index(poss) if poss in self.headers else -1
            if col_idx != -1:
                my_col_val = players[actual_player].get_col_value(col_idx)
                
                # 1. Colonne non fermée par l'IA (Objectif : Ouvrir / Fermer)
                if my_col_val < 3:
                    if is_far_ahead:
                        score += 500 + (numeric_val * 10)  # Priorité absolue à la fin de partie
                    elif is_behind and player_launch >= 2: 
                        score += 400 + (numeric_val * 10)  # 3e fléchette en retard : on cherche à ouvrir/fermer
                    elif random.randrange(100) < open_rate:
                        score += 150

                # 2. Colonne déjà fermée par l'IA (Objectif : Faire des points)
                else:
                    if is_far_ahead:
                        score -= 1000  # Stop le gavage de points si large avance
                    elif is_behind:
                        if player_launch < 2: 
                            # ATTAQUE MASSIVE : 1ère et 2ème fléchette, focus absolu sur les gros chiffres fermés (20, 19, 18...)
                            score += 1500 + (numeric_val * 50)  
                        else:
                            score += 100
                    elif random.randrange(100) < points_rate:
                        score += 200

            scores[poss] = score

        if not scores:
            best = self.headers[0] if self.headers else '20'
        else:
            best = sorted(scores.items(), key=lambda item: item[1], reverse=True)[0][0]

        # --- GESTION DE LA PRÉCISION (Taux d'échec du niveau) ---
        if random.randrange(100) < failure_rate:
            other_possibilities = [p for p in possibilities if p != best]
            if other_possibilities:
                best = random.choice(other_possibilities)

        # --- CHOIX DU MULTIPLICATEUR ---
        mult_roll = random.randrange(100)
        
        if best != 'B':
            if mult_roll < triple_rate:
                score = f'T{best}'
            elif mult_roll < (triple_rate + double_rate):
                score = f'D{best}'
            else:
                score = f'S{best}'
        else:
            if mult_roll < triple_rate:
                score = 'DB'
            else:
                score = 'SB'

        # --- PRÉDICTION DU COUP VISÉ ---
        self.infos += f"Bot aims for: {score}\n"
        players[actual_player].last_aim = score

        return score

    def early_player_button(self, players, actual_player, actual_round):
        """
        If player Hit the Player button before having threw all his darts
        """
        # Jump to next player by default
        return_code = 1
        self.infos += "You hit Player button before throwing all your darts \
                ! Did you hit the PNEU ?"
        self.infos += f"actual_round {actual_round} Max Round {self.max_round} \
                actual_player {actual_player} nb_players {self.nb_players - 1}"
        # If no touch for this player at this round : play sound for "round missed"
        if players[actual_player].roundhits == 0:
            self.display.play_sound('chaussette')

        # If last round reached
        if actual_round == self.max_round and actual_player == self.nb_players - 1:
            winner = self.check_winner(players, actual_round, actual_player, self.nb_darts)
            if winner is not None:
                self.winner = winner
                self.infos += f"Player {winner} wins !{self.lf}"
                return 3
            return 2
        return return_code

    def refresh_stats(self, players, actual_round):
        """
        Method to frefresh player.stat - Adapt to the stats you want.
        They represent mathematical formulas used to calculate stats.
        Refreshed after every launch
        """
        for player in players:
            player.stats['MPR'] = player.show_mpr()
            player.stats['Hits per round'] = player.hits_per_round(actual_round)
            player.stats['GiveOut'] = player.distrib_points

    def get_random(self, players, actual_round, actual_player, player_launch):
        """
        Returns and Random things, to send to clients in case of a network game
        """
        if self.crazy:
            return self.headers
        return False

    def set_random(self, players, actual_round, actual_player, player_launch, data):
        """
        Set Random things, while received by master in case of a network game
        """
        if data is not False:
            self.headers = data
            self.random_from_net = True

    def next_game_order(self, players):
        """
        Define the next game players order, depending of previous games' scores
        """
        scores = {}
        # Create a dict with player and his score
        for player in players:
            scores[player.name] = player.score
        # Order this dict depending of the score
        new_order = collections.OrderedDict(sorted(scores.items(), key=lambda t: t[1],
                                                      reverse=self.cutthroat))
        # Return
        return list(new_order.keys())

    def can_win(self, player, darts):
        """
        Return "player can win with x darts"
        """
        total_hit = 0
        for target in player.columns:
            total_hit += target[0]
        return 21 - total_hit <= darts

    def get_score(self, player):
        """
        Return score of player
        """
        total_hit = 0
        for target in player.columns:
            total_hit += target[0]
        return float(f'{player.score}.{total_hit}')

    def next_set_order(self, players):
        """
        Sort players for next set
        """
        players.sort(key=self.get_score)

    def mate(self, actual_player, nb_players):
        """
        Find TeamMate in case of Teaming
        """
        mate = -1
        if self.teaming:
            if actual_player < (nb_players / 2):
                mate = actual_player + int(nb_players / 2)
            else:
                mate = actual_player - int(nb_players / 2)
        return mate

    def check_handicap(self, players):
        """
        Check for handicap and record appropriate marks for player
        """
        if len(players) != 4:
            self.logs.warning("Handicap is available in Cricket only for 4 players.")
        else:
            self.logs.debug("Looking for handicaps")
            handimarks = []
            mpr = []
            maxid = 0
            for player in players:
                name = player.name
                if name.lower() not in self.stats.PlayerStatDict:
                    mpr.append(0.0)
                else:
                    mpr.append(self.stats.PlayerStatDict[name.lower()][2])
                # Load Handicaps from CHandicap
            handimarks = self.handicap.FindCricketHandicap(mpr)
            maxid = self.handicap.ReturnMaxid()
            # load handicaps into players
            for column in range(0, int(self.nbcol + 1)):
                for handmark in range(handimarks[column] + 1):
                    self.logs.debug(f"Handicap : Column = {column}, handmark = {handmark}")
                    if maxid == 0:
                        if handmark == 0:
                            pass
                        else:
                            players[1].increment_column_touch(column)
                            players[3].increment_column_touch(column)
                    elif maxid == 1:
                        if handmark == 0:
                            pass
                    else:
                        players[0].increment_column_touch(column)
                        players[2].increment_column_touch(column)

    def miss_button(self, players, actual_player, actual_round, player_launch):
        """
        Miss button pressed
        """
        self.logs.debug("MissButtonPressed")
        players[actual_player].darts_thrown += 1
        players[actual_player].add_dart(actual_round, player_launch, 'MISS', hit_value=0)
        self.display.play_sound('miss')
        
        hit = 'MISS'
        print('CONTENU DE HIT  DEF MISS')
        print(hit)
        ### TROPHEES
        ctrophies.process_single_dart(players[actual_player], hit)
        
        # On vérifie les trophées de volée uniquement à la 3ème fléchette
        if player_launch == 3:
            round_darts = players[actual_player].darts[-3:]
            ctrophies.check_and_unlock_trophies(players[actual_player], round_darts)

    def check_players_allowed(self, nb_players):
        """
        Check if numbers of players is ok according to options
        """
        if self.teaming and (nb_players % 2 != 0 or nb_players < 4):
            return False
        return nb_players <= 8

    def draw_symbol(self, color, center_x, center_y, size, thickness, score, ratio=None):
        """
        Remplit la case du Cricket en se basant sur la taille des colonnes et des lignes de Mickey.
        """
        box_w = int(self.target_col_w * 0.7)
        box_h = int(self.row_h * 0.6)
        
        pos_x = int(center_x - box_w / 2)
        pos_y = int(center_y - box_h / 2)

        effective_score = max(0, min(int(score), 3))

        if effective_score > 0:
            fill_height = int(box_h * (effective_score / 3.0))
            fill_y = pos_y + box_h - fill_height

            # Marge de 2 pixels sur les côtés comme sur Mickey
            margin_x = 2
            draw_x = pos_x + margin_x
            draw_w = max(2, box_w - (margin_x * 2))
            
            # Pas de marge artificielle sur la hauteur pour que le palier monte net
            draw_y = fill_y
            draw_h = fill_height

            if draw_h > 0:
                self.display.blit_rect(draw_x, draw_y, draw_w, draw_h, color)

    # code pour afficher symboles classiques
    '''
    def draw_symbol(self, color, center_x, center_y, size, thickness, score, ratio=None):
        pos_x = int(center_x - size / 2)
        pos_y = int(center_y - size / 2)
        if ratio is None:
            for index in range(0, size + 1):
                if score > 0:
                    pygame.draw.circle(self.display.screen, color, (pos_x + index, pos_y + index), thickness, 0)
                if score > 1:
                    pygame.draw.circle(self.display.screen, color, (pos_x + index, pos_y + size - index), thickness, 0)
                if score < 0:
                    pygame.draw.circle(self.display.screen, color, (pos_x + index, center_y), thickness, 0)
            if score > 2:
                 pygame.draw.circle(self.display.screen, color, (center_x, center_y), int(size / sqrt(2)), int(thickness * sqrt(2)))
        else:
            index = int(size * ratio)
            width = int(ratio * thickness * sqrt(2))
            if score > 0:
                pygame.draw.circle(self.display.screen, color, (pos_x + index, pos_y + index), thickness, 0)
            if score > 1:
                pygame.draw.circle(self.display.screen, color, (pos_x + index, pos_y + size - index), thickness, 0)
            if score > 2 and width > 0:
                pygame.draw.circle(self.display.screen, color, (center_x, center_y), int(size / sqrt(2)), width)
            if score < 0:
                pygame.draw.circle(self.display.screen, color, (pos_x + index, center_y), thickness, 0)

    def draw_rect(self, rect, thickness, color):
        pos_x = rect[0]
        pos_y = rect[1]
        width = rect[2]
        height = rect[3]

        pygame.draw.line(self.display.screen, color, (pos_x, pos_y), (pos_x, pos_y + height), thickness)
        pygame.draw.line(self.display.screen, color, (pos_x + width, pos_y), (pos_x + width, pos_y + height), thickness)
        pygame.draw.line(self.display.screen, color, (pos_x, pos_y), (pos_x + width, pos_y), thickness)
        pygame.draw.line(self.display.screen, color, (pos_x, pos_y + height), (pos_x + width, pos_y + height), thickness)

    '''
    def draw_dart_score(self, dart_position, dart_value):
        mid_x = int(self.display.res_x / 4)
        mid_y = self.margin
        mid_w = self.display.mid_x
        mid_h = int(self.display.res_y * 2 / 3) - mid_y

        target_x = self.display.mid_x - int(self.display.res_x / 32)
        # target_y = mid_y + int(mid_h / 16)
        target_y = mid_y + self.margin_2
        target_w = int(self.display.res_x / 16)
        # target_h = int(mid_h / 8)
        target_h = int((mid_h - self.margin_4)/ 7)

        scores_y = mid_y + self.margin
        scores_w = int(self.display.res_x * 3 / 32)
        scores_h = mid_h - self.margin_2

        dart_x = int(self.display.res_x / 4 + self.margin / 2)
        dart_x_increment = int(self.display.mid_x / 3)
        dart_y = scores_y + scores_h + int(self.display.res_y / 32)
        dart_h = target_h
        dart_w = int(self.display.mid_x / 3 - 2 * self.margin)

        # For scrolling dart
        pos_y = dart_y + dart_h + self.margin
        height = int(self.display.res_y / 24)

        if dart_value[:1] == 'T' or dart_value == 'DB':
            dart_color = self.display.colorset['game-gold']
        elif dart_value[:1] == 'D' or dart_value == 'SB':
            dart_color = self.display.colorset['game-silver']
        else:
            dart_color = self.display.colorset['game-bronze']
        self.display.blit_rect(dart_x + dart_position * dart_x_increment, dart_y, dart_w, dart_h, self.display.colorset['game-bg'])
        self.display.blit_text(f"{dart_value}", dart_x + dart_position * dart_x_increment, dart_y, dart_w, dart_h, color=dart_color, align='Center')


    def onscreen_buttons(self):
        '''
        On screen buttons
        '''
        # Init
        click_zones = {}

        # GAME BUTTON
        right_x = int(self.display.res['x'] * 12 / 16)
        right_y = self.display.margin
        right_width = int(self.display.res['x'] * 4 / 16)
        right_height = int(self.display.res['y'] * 1.5 / 16)

        buttons = []
        buttons.append([right_x, right_y, right_width, right_height, self.display.colorset['menu-alternate'], 'GAMEBUTTON', 'Exit'])
        right_y += right_height + self.display.margin
        buttons.append([right_x, right_y, right_width, right_height, self.display.colorset['menu-shortcut'], 'BACKUPBUTTON', 'Back'])
        right_y += right_height + self.display.margin
        buttons.append([right_x, right_y, right_width, right_height, self.display.colorset['menu-ok'], 'PLAYERBUTTON', 'Next Player'])

        for button in buttons:
            # Blit Background rect
            self.display.blit_rect(button[0], button[1], button[2], button[3], button[4], 2, self.display.colorset['menu-buttons'], self.display.alpha)
            click_zones[button[5]] = (button[0], button[1], button[2], button[3], button[4])

            # Blit button
            self.display.blit_text(button[6], button[0], button[1], button[2], button[3], self.display.colorset['menu-text-white'])

        # Return Dict of tuples representing clickage values
        return click_zones

    def refresh_game_screen(self, players, actual_round, max_round, rem_darts, nb_darts, logo, headers, actual_player, TxtOnLogo=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
            self.display.reset_background()

            mpr = players[actual_player].show_mpr()
            self.mpr = mpr

            cell_bg = (20, 22, 28)        
            header_bg = (35, 38, 48)      
            grid_border_color = (60, 65, 78) 

            game_background = f"background_{logo}"
            game_background = self.display.file_class.get_full_filename(game_background, 'images')
            # The background under its veil : copied from the cache after the first time
            self.display.display_background(image=game_background, veil=self.display.colorset['game-bg'])

            # --- AFFICHAGE DU TITRE DU JEU EN HAUT ---
            title_h = int(self.display.res_y * 0.08)
            title_w = int(self.display.res_x * 0.4)
            title_x = int((self.display.res_x - title_w) / 2)
            title_y = int(self.margin)
            self.display.blit_text("Cricket", title_x, title_y, title_w, title_h, color=(255, 255, 255), align='Center', valign='center', margin=False)

            left_x = self.margin
            left_y = self.margin + title_h  # On décale le reste pour ne pas chevaucher le titre
            left_w = int(self.display.res_x * 0.22)
            
            round_h = int(self.display.res_y * 0.05)
            self.display.blit_rect(left_x, left_y, left_w, round_h, self.display.colorset['game-bg'])
            self.display.blit_text(f"Tour : {actual_round}/{max_round}", left_x, left_y, left_w, round_h, color=self.display.colorset['game-round'], align='Left', valign='center', margin=False)

            mpr_y = left_y + round_h + self.margin
            mpr_h = int(self.display.res_y * 0.05)
            mpr_rectangle = (left_x, mpr_y, left_w, mpr_h)
            
            self.display.blit_text(f'MPR : {mpr}', left_x, mpr_y, left_w, mpr_h, color=players[actual_player].color, align='Left', valign='center')
            
            sub = self.display.screen.subsurface(mpr_rectangle)
            screenshot2 = pygame.Surface((mpr_rectangle[2], mpr_rectangle[3]))
            self.display.blit_screen(screenshot2, sub, (0, 0))

            rect_dart = None

            right_w = int(self.display.res_x * 0.35)
            right_x = self.display.res_x - right_w - self.margin
            dart_y = self.margin + title_h # On décale également le bloc darts vers le bas
            dart_h = int(self.display.res_y * 0.08)
            dart_w = int(right_w / 3)

            index_d = 0
            if not end_of_game:
                for dart in players[actual_player].darts:
                    box_x = right_x + index_d * dart_w
                    margin_box_x = int(dart_w * 0.1)
                    margin_box_y = int(dart_h * 0.15)
                    
                    b_x = box_x + margin_box_x
                    b_y = dart_y + margin_box_y
                    b_w = dart_w - (2 * margin_box_x)
                    b_h = dart_h - (2 * margin_box_y)

                    self.display.blit_rect(b_x, b_y, b_w, b_h, cell_bg)
                    pygame.draw.rect(self.display.screen, grid_border_color, (b_x, b_y, b_w, b_h), 1)

                    if dart is None:
                        if index_d == 0:
                            dart_color = self.display.colorset['game-gold']
                        elif index_d == 1:
                            dart_color = self.display.colorset['game-silver']
                        else:
                            dart_color = self.display.colorset['game-bronze']
                        self.display.display_image(self.dart, b_x, b_y, b_w, b_h, center_x=True, change_colors=[[(0, 0, 0), dart_color]])
                    else:
                        self.display.blit_text(str(dart), b_x, b_y, b_w, b_h, color=(255, 255, 255), align='Center', valign='center')

                    index_d += 1

            start_grid_y = mpr_y + mpr_h + (self.margin * 2)
            available_h = self.display.res_y - start_grid_y - self.margin

            nb_headers = len(self.headers)
            
            fixed_total_units = nb_headers + 3 
            unit_w = int(self.display.res_x / (fixed_total_units + 1))

            name_col_w = unit_w * 2  
            target_col_w = unit_w     
            score_col_w = unit_w

            grid_w = name_col_w + (nb_headers * target_col_w) + score_col_w
            grid_x = int((self.display.res_x - grid_w) / 2)

            max_row_h = int((self.display.res_y - (mpr_y + mpr_h + self.margin * 2)) / 9)
            calculated_row_h = int(available_h / 9)
            row_h = min(calculated_row_h, max_row_h)

            self.target_col_w = target_col_w     
            self.row_h = row_h

            total_table_h = row_h * (len(players) + 1)
            
            grid_y = start_grid_y + int((available_h - total_table_h) / 2)

            header_x = grid_x + name_col_w
            for target in self.headers:
                self.display.blit_rect(header_x, grid_y, target_col_w, row_h, header_bg)
                pygame.draw.rect(self.display.screen, grid_border_color, (header_x, grid_y, target_col_w, row_h), 1)
                self.display.blit_text(f'{target}', header_x, grid_y, target_col_w, row_h, color=(255, 255, 255), align='Center')
                header_x += target_col_w

            self.symbol_size = int(row_h * 0.38)
            self.symbol_thickness = 3

            player_row_idx = 0
            for index, player in enumerate(players):
                p_y = grid_y + row_h + (player_row_idx * row_h)
                is_active = (index == actual_player)
                p_color = players[actual_player].color if is_active else self.display.colorset['game-player']

                self.display.blit_rect(grid_x, p_y, name_col_w, row_h, p_color)
                pygame.draw.rect(self.display.screen, (0, 0, 0), (grid_x, p_y, name_col_w, row_h), 1)
                self.display.blit_text(player.name, grid_x + 4, p_y, name_col_w - 4, row_h, color=(255, 255, 255), align='Left')

                c_x = grid_x + name_col_w
                index_c = 0
                for column in player.columns:
                    self.display.blit_rect(c_x, p_y, target_col_w, row_h, cell_bg)
                    pygame.draw.rect(self.display.screen, grid_border_color, (c_x, p_y, target_col_w, row_h), 1)
                    
                    center_x = c_x + int(target_col_w / 2)
                    center_y = p_y + int(row_h / 2)
                    
                    if self.get_column_state(player.ident, players, index_c) == 4:
                        self.draw_symbol((80, 85, 95), center_x, center_y, self.symbol_size, self.symbol_thickness, column[0])
                    else:
                        self.draw_symbol(player.color, center_x, center_y, self.symbol_size, self.symbol_thickness, column[0])
                    
                    c_x += target_col_w
                    index_c += 1

                score_x = grid_x + name_col_w + (nb_headers * target_col_w)
                self.display.blit_rect(score_x, p_y, score_col_w, row_h, header_bg)
                pygame.draw.rect(self.display.screen, grid_border_color, (score_x, p_y, score_col_w, row_h), 1)
                self.display.blit_text(str(player.score), score_x, p_y, score_col_w - 2, row_h, color=(255, 255, 255), align='Right')

                if is_active:
                    pygame.draw.rect(self.display.screen, p_color, (grid_x, p_y, grid_w, row_h), 3)

                player_row_idx += 1

            click = None
            if OnScreenButtons is True or self.display.is_true(self.config.get_value('SectionGlobals', 'onscreenbuttons')):
                click = self.onscreen_buttons()

            self.display.save_background()
            self.display.update_screen()

            rect1 = pygame.Rect(right_x, dart_y, right_w, dart_h)
            sub = self.display.screen.subsurface(rect1)
            screenshot1 = pygame.Surface((right_w, dart_h))
            self.display.blit_screen(screenshot1, sub, (0, 0))

            screenshot3 = None

            if end_of_game:
                click = self.display.end_of_game_menu()
                return click

            if OnScreenButtons is True or self.display.is_true(self.config.get_value('SectionGlobals', 'onscreenbuttons')):
                return [click, [screenshot1, rect1], [screenshot2, mpr_rectangle], [screenshot3, rect_dart]]
            else:
                return [[], [screenshot1, rect1], [screenshot2, mpr_rectangle], [screenshot3, rect_dart]]
