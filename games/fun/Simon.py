# -*- coding: utf-8 -*-
# Game by ... you ! - Version corrigée (Correction du bug d'affichage des colonnes PNJ)
########
from include import cplayer
from include import cgame
import time
import random

############
# Game Variables
############
OPTIONS = {
    'theme': 'default', 
    'nb_segment': 5, 
    'max_round': 7, 
    'nb_bonus_darts': 1,
    'color_palette': 'classic', # classic, neon, pastel
    'start_sequence_length': 1  # Taille de la séquence au départ
}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
LOGO = 'Simon.png'
HEADERS = ['Seq 1', 'Seq 2', 'Seq 3', 'Seq 4', 'Seq 5', 'Seq 6', 'Seq 7']
VERSION = '1.41'

def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
    """
    return nb_players >= 1 and nb_players <= 12, VERSION, 12

class CPlayerExtended(cplayer.Player):
    """
    Extend the basic player
    """
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        for record in GAME_RECORDS:
            self.stats[record] = '0'

class Game(cgame.Game):
    """
    Extend the common Game class
    """
    # Its sequence shown on the target after the name of the player (post_pre_dart_check) : the
    # target lit after it, not with the name (raspydarts.py)
    lights_after_announce = True

    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        
        self.options = options
        self.GameRecords = GAME_RECORDS
        self.logo = LOGO
        self.game_is_ok_for_color = False  
        self.headers = HEADERS
        self.max_round = int(options['max_round'])
        self.nb_bonus_darts = int(self.options['nb_bonus_darts'])
        self.nb_segment = int(self.options['nb_segment'])  
        
        try:
            self.start_seq_len = int(self.options.get('start_sequence_length', 1))
        except ValueError:
            self.start_seq_len = 1

        self.rpi = rpi

        palette = self.options.get('color_palette', 'classic')
        if palette == 'neon':
            self.Colors = ('magenta', 'cyan', 'lime', 'yellow')
        elif palette == 'pastel':
            self.Colors = ('pink', 'lightblue', 'lightgreen', 'peach')
        else:
            self.Colors = ('red', 'green', 'blue', 'yellow')

        self.segments = (
            (20, 1, 18, 4, 13),
            (6, 10, 15, 2, 17),
            (3, 19, 7, 16, 8),
            (11, 14, 9, 12, 5)
        )

        if self.nb_segment == 1:
            self.segments = ((20,), (6,), (3,), (11,))
        elif self.nb_segment == 2:
            self.segments = ((20, 1), (6, 10), (3, 19), (11, 14))
        elif self.nb_segment == 3:
            self.segments = ((20, 1, 18), (6, 10, 15), (3, 19, 7), (11, 14, 9))
        elif self.nb_segment == 4:
            self.segments = ((20, 1, 18, 4), (6, 10, 15, 2), (3, 19, 7, 16), (11, 14, 9, 12))

        self.scores = {}
        self.sequence_index = 0
        self.sequence = []
        
        while len(self.sequence) < self.start_seq_len:
            self.Incsequence()

        self.light_segment = False

    def refresh_stats(self, players, actual_round):
        for player in players:
            player.stats['Points Per Round'] = player.show_ppr()
            player.stats['Points Per Dart'] = player.show_ppd()

    def display_segment(self):
        return False

    def reset_leds(self):
        for index in range(len(self.segments)):
            self.set_leds(index, 'black')

    def set_leds(self, pos, color, blink=False):
        strings = []
        for segment in self.segments[pos]:
            for mult in ('S', 'D', 'T'):
                strings.append(f"{mult}{segment}#{color}")
        s = '|'.join(strings)
        self.rpi.set_target_leds(s)
        if blink:
            self.rpi.event.publish('simon', s)
        else:
            self.rpi.event.publish('goal', s)

    def Incsequence(self):
        last = self.sequence[-1] if len(self.sequence) > 0 else None
        while True:
            i = random.randint(0, len(self.segments) - 1)
            if last is None or i != last:
                break
        self.sequence.append(i)

    def post_pre_dart_check(self, players, actual_round, actual_player, player_launch):
        seq_len = (self.scores.get(actual_player, 0) + self.start_seq_len) - 1
        if player_launch == 1:
            time.sleep(0.8)
            for i in self.sequence[0:seq_len]:
                self.set_leds(i, self.Colors[i])
                time.sleep(0.4)
                self.reset_leds()
                time.sleep(0.1)

        return None

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            self.logs.debug('RESET')
            self.reset_leds()
            self.display.display_background('bg_simon')

        if actual_player not in self.scores:
            self.scores[actual_player] = 0

        if player_launch == 1:
            self.sequence_index = 0

        seq_len = self.scores[actual_player] + self.start_seq_len

        while len(self.sequence) < seq_len:
            self.Incsequence()

        try:
            n = self.nb_bonus_darts
        except ValueError:
            n = 0
        self.nb_darts = seq_len + n

        return 0
	
    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        ret = 0
        handler = self.init_handler()
        
        pts = int(hit[1:]) if hit[1:] != 'B' else None
        seq_len = self.scores[actual_player] + self.start_seq_len
        targets = self.segments[self.sequence[self.sequence_index]]
        finished = False

        if pts in targets:
            self.sequence_index += 1

            for index in range(len(self.segments)):
                if pts in self.segments[index]:
                    self.set_leds(index, self.Colors[index], True)
                    self.reset_leds()
                    break

            if self.sequence_index == seq_len:
                self.scores[actual_player] += 1
                players[actual_player].add_score(1)
                
                # ---> REMPLACEMENT ICI : Utilisation de l'image de réussite (check-mark)[cite: 2]
                players[actual_player].columns[self.scores[actual_player] - 1] = ('check-mark', 'image')
                
                if player_launch != self.nb_darts:
                    self.nb_darts = player_launch
                ret = 4
                finished = True
        elif self.nb_darts - player_launch < seq_len - self.sequence_index:
            self.scores[actual_player] += 1
            
            # ---> REMPLACEMENT ICI : Utilisation de l'image d'échec (cross-mark)[cite: 2]
            players[actual_player].columns[self.scores[actual_player] - 1] = ('cross-mark', 'image')
            
            ret = 1
            finished = True
        else:
            return -1

        if finished and actual_round >= self.max_round and actual_player == len(players) - 1:
            winner = -1
            best_score = -1
            for player in players:
                if player.score > best_score:
                    best_score = player.score
                    winner = player.ident
            self.winner = winner
            ret = 3

        handler['take_shot'] = self.time_to_take_shot_or_video(hit)
        handler['return_code'] = ret
        return handler


    def pnj_score(self, players, actual_player, level, player_launch):
        """
        PNJ humain pour le jeu Simon :
        - Gère les niveaux de difficulté (taux de raté / miss et taux de glissement / slip).
        - Utilise la matrice des voisins pour faire dévier la fléchette de manière réaliste.
        - Ne perturbe plus l'affichage des colonnes du tableau des scores.
        """
        # =========================================================================
        # GUIDE DE RÉGLAGE DES NIVEAUX DE DIFFICULTÉ :
        # - Légende des niveaux : [miss_rate, slip_rate]
        #   * miss_rate : Probabilité de rater complètement la cible (MISSDART) (%)
        #   * slip_rate : Probabilité que la fléchette glisse/dévie vers un secteur voisin (%)
        # - Ajustement : Pour renforcer l'IA, réduis miss_rate et slip_rate.
        # =========================================================================

        geo_neighbors = {
            1: [20, 18, 4], 2: [17, 15, 10], 3: [19, 17, 2], 4: [18, 13, 1], 
            5: [20, 12, 9], 6: [10, 13, 15], 7: [19, 16, 8], 8: [16, 11, 7], 
            9: [14, 12, 5], 10: [15, 6, 2], 11: [14, 8, 16], 12: [9, 5, 20], 
            13: [6, 4, 11], 14: [9, 11, 16], 15: [10, 2, 6], 16: [7, 8, 11], 
            17: [2, 3, 15], 18: [4, 1, 20], 19: [7, 3, 2], 20: [1, 5, 12]
        }

        levels = [
                 [40, 70],  # 1 : Noob 
                 [25, 60],  # 2 : Débutant
                 [15, 50],  # 3 : Intermédiaire 
                 [8, 30],   # 4 : Pro 
                 [2, 10]    # 5 : Expert 
                ]

        lvl_idx = max(0, min(level - 1, len(levels) - 1))
        miss_rate = levels[lvl_idx][0]
        slip_rate = levels[lvl_idx][1]

        # 1. Gestion du raté pur (Miss) - Ne touche plus aux colonnes pour éviter les superpositions
        if random.randrange(100) < miss_rate:
            self.display.play_sound('miss')
            players[actual_player].darts_thrown += 1
            return 'MISSDART'

        # 2. Détermination de la cible idéale selon la séquence
        seq_len = self.scores.get(actual_player, 0) + self.start_seq_len
        target_seq_index = player_launch - 1
        
        if target_seq_index >= len(self.sequence) or target_seq_index >= seq_len:
            group_idx = random.randint(0, len(self.segments) - 1)
        else:
            group_idx = self.sequence[target_seq_index]
            
        target_numbers = self.segments[group_idx]
        if isinstance(target_numbers, int):
            target_numbers = (target_numbers,)
            
        chosen_number = random.choice(target_numbers)

        # 3. Gestion de la déviation / glissement (slip) via la matrice physique des voisins
        if random.randrange(100) < slip_rate:
            if chosen_number in geo_neighbors:
                chosen_number = random.choice(geo_neighbors[chosen_number])

        # 4. Choix réaliste du multiplicateur (favorise grandement les Singles)
        if level <= 2:
            mult = 'S'
        elif level == 3:
            mult = random.choice(['S', 'S', 'S', 'D'])
        else:
            mult = random.choice(['S', 'S', 'D', 'T'])

        return f'{mult}{chosen_number}'


    def miss_button(self, players, actual_player, actual_round, player_launch):
        self.display.play_sound('miss')
        players[actual_player].darts_thrown += 1
