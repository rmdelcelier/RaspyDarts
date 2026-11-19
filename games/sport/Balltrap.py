# -*- coding: utf-8 -*-
"""
Game by LaDite
"""

import random
import pygame
from include import cplayer
from include import cgame

#
VERSION = '1.01'
LOGO = 'Balltrap.png' # Background image - relative to images folder
HEADERS = ['PL1', 'PL2', '-', '-', '-', 'BULL', '-'] # Columns headers - Must be a string
OPTIONS = {'theme': 'default', 'Time': 500} # Dictionnay of options
NB_DARTS = 3
GAME_RECORDS = {'Score': 'DESC', 'Reached Score': 'DESC', 'Hits': 'DESC'}

def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
    """
    return nb_players <= 12, VERSION, 12

class CPlayerExtended(cplayer.Player):
    """
    Extended Player class
    """
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        #The score the player has to hit
        self.actual_hit = 1
        self.next = 0
        self.targets_list = []
        # Init Player Records to zero
        for game_record in GAME_RECORDS:
            self.stats[game_record] = '0'

class Game(cgame.Game):
    """
    balltrap game class
    """
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.logo = LOGO
        self.headers = HEADERS
        self.game_records = GAME_RECORDS
        self.nb_darts = NB_DARTS
        self.options = options
        self.nb_players = nb_players
        # For rpi
        self.rpi = rpi
        self.dmd = dmd

        self.max_round = 12
        self.time = int(options['Time'])
        self.tirsrestant = 3
        self.repetition = 10

        self.bull = False
        self.first = True

        # --- INITIALISATIONS  ---
        self.target_order = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]
        self.colors = ['green', 'red', 'blue']

        # --- ÉTATS DU JEU & ANIMATIONS DUCK HUNT ---
        self.duck_positions = [
            {'x': 100, 'y': 150, 'speed': 30}
        ]
        self.dog_state = None      # 'success', 'miss' ou None
        self.show_pan = False      # Indicateur de tir réussi
        self.pan_timer = 0         # Chrono pour le pop-up PAN
        self.dog_timer = 0         # Chrono pour l'affichage temporaire du chien (2s)
        self.duck_falling = False  # État de chute du canard
        self.duck_hit_state = False # État d'affichage de l'impact (duck_hit)
        self.hit_timer = 0         # Chrono pour l'affichage de duck_hit (1s)
        self.fall_timer = 0        # Chrono pour la chute du canard
        
        # AFFICHE Le DEBUG A L ECRAN
        self.debug_balltrap = False
        

    def play_intro(self):
        """
        Retourne un tuple vide pour satisfaire l'appel de raspydarts.py et éviter le TypeError.
        """
        return None, None

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        After each row : valid launch ? winner ? ...
        """
        handler = self.init_handler()
        play_hit = False
        # The dart landed before the last move of the target (it waited while the game moved the
        # duck, include/craspberry.py) : judged on the target lit when it landed
        dart_before = getattr(self.rpi, 'dart_before_targets_changed', None)
        if (dart_before is not None and dart_before() and getattr(self, 'previous_next', None) is not None
                and hit not in self.targets_list and hit in getattr(self, 'previous_targets', [])):
            print(f"[DEBUG POST-DART] {hit} lancee avant le deplacement : jugee sur la cible precedente")
            players[actual_player].next = self.previous_next
            self.targets_list = self.previous_targets
        players[actual_player].add_dart(actual_round, player_launch, hit)
        
        # --- AFFICHAGE DU "PAN !" A CHAQUE TIR (TOUCHÉ OU RATÉ) ---
        self.show_pan = True
        self.pan_timer = pygame.time.get_ticks()
        
        return_code = 0
        self.infos = ''
        self.first = True

        current_time = pygame.time.get_ticks()

        # --- DEBUG PRINCIPAL ---
        print(f"\n[DEBUG POST-DART] --- NOUVEAU TIR ---")
        print(f"[DEBUG POST-DART] Round: {actual_round} | Joueur: {actual_player} | Lancer: {player_launch} | Hit reçu: {hit}")
        print(f"[DEBUG POST-DART] self.bull: {self.bull} | self.targets_list: {self.targets_list}")

        if self.bull and hit == 'SB':
            print("[DEBUG POST-DART] -> Touché SB en mode BULL")
            players[actual_player].score += 2
            self.display.play_sound('balltrap_pan-bulls')
            self.show_pan = True
            self.pan_timer = current_time
            for duck in self.duck_positions:
                duck['hit'] = True
                duck['falling'] = True
                duck['hit_timer'] = current_time
       
        elif self.bull and hit == 'DB':
            print("[DEBUG POST-DART - BALLTRAP] -> Touché DB en mode BULL")
            players[actual_player].score += 3
            self.display.play_sound('balltrap_pan-bulls')
            self.show_pan = True
            self.pan_timer = current_time
            for duck in self.duck_positions:
                duck['hit'] = True
                duck['falling'] = True
                duck['hit_timer'] = current_time
        
        # --- GESTION DES CIBLES NORMALES (UNIQUEMENT SI PAS EN MODE BULL) ---
        elif not self.bull and hit in self.targets_list:
            print("[DEBUG POST-DART] -> Hit présent dans targets_list, vérification de la cible...")
            self.display.play_sound('balltrap_pan-touche')
            self.pan_timer = current_time
            
            # --- GESTION DE LA CHUTE INDIVIDUELLE OU DOUBLE DES CANARDS ---
            if actual_round in (3, 6, 9, 12) and len(self.duck_positions) >= 2:
                next_index = players[actual_player].next
                next_target = str(players[actual_player].goals[next_index])
                opposite = str(players[actual_player].goals[(20 + 2 * getattr(self, 'offset', 0) - next_index) % 20])
                
                hit_value = hit[1:] if len(hit) > 1 and hit[0] in ('S', 's', 'D', 'T') else hit
                
                print(f"[DEBUG POST-DART] Rond 3/6/9/12 -> Canard 0 attend: {next_target} | Canard 1 attend: {opposite}")
                print(f"[DEBUG POST-DART] Valeur brute du hit analysée (hit_value): {hit_value}")
                
                # Identifier clairement qui est touché de manière exclusive
                hit_is_master = (hit_value == next_target and not self.duck_positions[0].get('dead', False) and not self.duck_positions[0].get('falling', False))
                hit_is_opposite = (hit_value == opposite and not self.duck_positions[1].get('dead', False) and not self.duck_positions[1].get('falling', False))

                # touche le canard 0 (master)
                if hit_is_master:
                    print(f"[DEBUG POST-DART] ===> MATCH Canard 0 ! (Il va tomber)")
                    self.duck_positions[0]['hit'] = True
                    self.duck_positions[0]['falling'] = True
                    self.duck_positions[0]['hit_timer'] = current_time
                
                # touche le canard 1 (opposite)
                elif hit_is_opposite:
                    print(f"[DEBUG POST-DART] ===> MATCH Canard 1 ! (Il va tomber)")
                    self.duck_positions[1]['hit'] = True
                    self.duck_positions[1]['falling'] = True
                    self.duck_positions[1]['hit_timer'] = current_time
                else:
                    print(f"[DEBUG POST-DART] Pas de match valide ou canard déjà touché/mort")
            else:
                hit_is_master = True
                hit_is_opposite = False
                print("[DEBUG POST-DART] -> Round classique, on fait tomber le canard 0")
                self.duck_positions[0]['hit'] = True
                self.duck_positions[0]['falling'] = True
                self.duck_positions[0]['hit_timer'] = current_time

            self.infos += f"Player {players[actual_player].name}, your score was {players[actual_player].score}{self.lf}"
            self.infos += f"at round {actual_round}{self.lf} You add to touch {self.targets_list}{self.lf}"
            self.infos += f"and you hit {hit}{self.lf}"

            # ROUND BONUS POINTS
            if actual_round in (3, 6, 9, 12):
                # les 2 canards ont le meme chiffre (Double Kill)
                if self.left == 2 and len(self.targets_list) >= 8 and (
                        (hit == self.targets_list[0] and hit == self.targets_list[1]) or 
                        (hit == self.targets_list[2] and hit == self.targets_list[3]) or 
                        (hit == self.targets_list[4] and hit == self.targets_list[5]) or 
                        (hit == self.targets_list[6] and hit == self.targets_list[7])
                ):
                    # calcul le bonus pour le double kill et active self.bull
                    players[actual_player].score += (3 - player_launch) * 4
                    self.bull = True
                    self.left = 0
                    players[actual_player].columns[0] = ('B', 'str')
                    self.display.play_sound('balltrap_pan-touche-2x')
                    
                    # Animation dck_Falling et hit
                    for d in self.duck_positions:
                        d['hit'] = True
                        d['falling'] = True
                        d['hit_timer'] = current_time
                        d['dead'] = False
                else:
                    # les 2 canards ont des chiffres differents
                    players[actual_player].score += 2
                    
                    # supprime un canard
                    self.left -= 1
                    print(f"[DEBUG POST-DART] self.left décrémenté à : {self.left}")
                    
                    # --- ON LANCE LA CHUTE MAIS ON LAISSE L'ANIMATION GÉRER LA MORT AU SOL ---
                    if hit_is_master:
                        self.targets_list = self.targets_list[4:]
                        self.drop = 'master'
                        print("[DEBUG POST-DART] Il reste 1 canard -> Canard 0 en train de tomber, drop = 'master'")
                    
                    elif hit_is_opposite:
                        self.drop = 'opposite'
                        self.targets_list = self.targets_list[:4]
                        print("[DEBUG POST-DART] Il reste 1 canard -> Canard 1 en train de tomber, drop = 'opposite'")

                    if self.left <= 0:
                        # Si les 2 sont touchés à la volée, on active le bull
                        self.bull = True
            else:
                # --- CORRECTION TOUR 1 : PASSAGE EN MODE BULL SUR ROUND CLASSIQUE ---
                players[actual_player].score += 2
                self.bull = True
                players[actual_player].columns[0] = ('B', 'str')
                print("[DEBUG POST-DART] Round classique -> Canard touché, passage en mode BULL")

        # canard MISS
        elif player_launch in (1, 2, 3):
            print("[DEBUG POST-DART] -> TIR RATÉ (Miss)")
            self.display.play_sound('balltrap_missed')
            
            for duck in self.duck_positions:
                duck['falling'] = False
                duck['hit'] = False
                
            #animation du chien ==> RATE 
            self.dog_state = 'miss'
            self.dog_timer = pygame.time.get_ticks()
            
            #Si canard non touche avec les 2 premieres fleches, ==> JOUEUR SUIVANT
            if player_launch == 2 and not self.bull:
                self.bull = False
                self.first = True
                return_code = -1

        players[actual_player].increment_hits(hit)
        self.tirsrestant -= 1

        # Affichage dans colonne - ANCIEN ECRAN
        if self.bull:
            players[actual_player].columns[5] = (self.tirsrestant, 'int')
        else:
            players[actual_player].columns[5] = ('0', 'int')

        if play_hit:
            if super().play_show(players[actual_player].darts, hit, play_special=True):
                self.display.sound_for_touch(hit)

        #pour determiner victoire
        if actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and ((player_launch == self.nb_darts and return_code <= 1) or return_code == -1):
            self.infos += rf"\n/!\ Last round reached ({actual_round})\n"
            self.winner = self.check_winner(players)
            if self.winner != -1:
                self.infos += "Here is a winner"
                return_code = 3
            else:
                self.infos += "No winner"
                return_code = 2
        
        players[actual_player].columns[0] = (players[actual_player].actual_hit, 'int')
        players[actual_player].darts_thrown += 1
        self.refresh_stats(players, actual_round)
        self.logs.debug(self.infos)

        handler['take_shot'] = self.time_to_take_shot_or_video(hit)
        
        #variable pour passer joueur suivant en cas ou on a pas toucher les canards
        if return_code == -1:
            return_code = 1

        # --- SUR LA 3ÈME FLÉCHETTE : ATTENTE DE LA FIN DU TOUR (CORRECTION ANIMATION TOUR 6) ---
        if player_launch == self.nb_darts:
            dog_started = False
            wait_start_time = pygame.time.get_ticks()
            
            # Correction : Retrait de 'and not self.bull' pour laisser l'animation aller jusqu'au bout
            while (any(duck.get('falling', False) for duck in self.duck_positions) or self.dog_state is not None) and (pygame.time.get_ticks() - wait_start_time < 2500):    
                pygame.event.pump()
                
                # Gestion du timer du chien (2 secondes)
                if self.dog_state is not None:
                    if not dog_started:
                        dog_start_time = pygame.time.get_ticks()
                        dog_started = True
                    elif pygame.time.get_ticks() - dog_start_time >= 2000:
                        self.dog_state = None
                
                self.refresh_game_screen(players, actual_round, self.max_round, self.tirsrestant, self.nb_darts, self.logo, self.headers, actual_player)
                pygame.time.delay(120)
            
            #joueur suivant apres l animation de la derniere fleches    
            return 1

        return handler
        
    def pnj_score(self, players, actual_player, computer_level, player_launch):
        try:
            comp_lvl = int(computer_level)
        except (ValueError, TypeError):
            comp_lvl = 3

        if self.bull:
            if random.randrange(100) < (comp_lvl * 15):
                return 'DB'
            return 'SB'

        if not self.targets_list:
            return f"S{random.randint(1, 20)}"

        chosen_target_str = random.choice(self.targets_list)
        levels_miss = [40, 25, 10, 2, 0]
        lvl_idx = max(0, min(comp_lvl - 1, len(levels_miss) - 1))
        
        if random.randrange(100) < levels_miss[lvl_idx]:
            players[actual_player].darts_thrown += 1
            return 'MISSDART'

        return chosen_target_str

    def post_round_check(self, players, actual_round, actual_player):
        if actual_round >= self.max_round and actual_player == self.nb_players - 1:
            self.infos += rf"\n/!\ Last round reached ({actual_round})\n"
            self.winner = self.check_winner(players)
            return self.winner
        else:
            return -2

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Before each throw - update screen, display score, etc...
        """
        return_code = None
        self.infos = ''
        
        res_y = self.display.res['y'] if hasattr(self.display, 'res') else 1080

        if self.bull:
            players[actual_player].columns[5] = (self.tirsrestant, 'int')
        else:
            players[actual_player].columns[5] = ('0', 'str')

        if player_launch == 1 and actual_round == 1 and actual_player == 0 and self.first:
            for player in players:
                start = random.choice(self.target_order)
                player.goals = self.target_order[::]
                player.next = random.randint(0, 19)
                player.columns[0] = (f'{player.goals[player.next]}', 'str')
                player.reset_darts()
                player.reset_rounds(self.max_round)

        if player_launch == 1 and self.first:
            self.left = 2
            self.offset = random.randint(-5, 5)

        
        # The target before this move : a dart which landed before it is judged on it (see
        # post_dart_check)
        self.previous_next = players[actual_player].next if hasattr(players[actual_player], 'next') else None
        self.previous_targets = list(getattr(self, 'targets_list', []))

        if not self.first:
            players[actual_player].next += 1
            if players[actual_player].next >= len(self.target_order):
                players[actual_player].next = 0

        # ajuste les tir et anim chien et pan
        if player_launch == 1:
            self.tirsrestant = 3
            self.bull = False
            self.dog_state = None
            self.show_pan = False
            
            # --- Réinitialise l'état "mort/chute" des canards ---
            if hasattr(self, 'duck_positions') and self.duck_positions:
                for duck in self.duck_positions:
                    duck['dead'] = False
                    duck['falling'] = False
                    duck['hit'] = False
                    
                # Remise à jour de Y selon le format d'origine
                if actual_round in (3, 6, 9, 12) and len(self.duck_positions) >= 2:
                    self.duck_positions[0]['y'] = int(res_y * 0.15)
                    self.duck_positions[1]['y'] = int(res_y * 0.35)
                elif len(self.duck_positions) > 0:
                    self.duck_positions[0]['y'] = int(res_y * 0.20)

        # --- INITIALISATION DES CANARDS UNE SEULE FOIS PAR ROUND ---
        if not hasattr(self, 'initialized_round') or self.initialized_round != actual_round:
            self.initialized_round = actual_round
            self.bull = False  # Sécurité anti-bull au démarrage d'un round

            if actual_round in (3, 6, 9, 12):
                self.duck_positions = [
                    {'x': 100, 'y': int(res_y * 0.15), 'speed': 30, 'falling': False, 'hit': False, 'hit_timer': 0, 'dead': False},
                    {'x': 100, 'y': int(res_y * 0.35), 'speed': 30, 'falling': False, 'hit': False, 'hit_timer': 0, 'dead': False}
                ]
            else:
                self.duck_positions = [
                    {'x': 100, 'y': int(res_y * 0.20), 'speed': 30, 'falling': False, 'hit': False, 'hit_timer': 0, 'dead': False}
                ]

        ## Affichage des chiffres dans les colonnes (ANCIEN ECRAN)
        if self.bull:
            players[actual_player].columns[0] = ('B' , 'str')
            players[actual_player].columns[1] = ('', 'str')
            self.targets_list = ['SB', 'DB', 'sb', 'db']
        
        elif actual_round in (3, 6, 9, 12):
            next_index = players[actual_player].next
            next_target = players[actual_player].goals[next_index]
            opposite = players[actual_player].goals[(20 + 2 * self.offset - next_index) % 20]

            if self.left == 2:
                # Les 2 canards sont vivants au début
                self.targets_list = [f'{mult}{value}' for mult in ['S', 's', 'D', 'T'] for value in [next_target, opposite]]
                players[actual_player].columns[0] = (f'{next_target}', 'str')
                players[actual_player].columns[1] = (f'{opposite}', 'str')
            
            elif getattr(self, 'drop', '') == 'master':
                # Le canard 0 (master) est mort, il ne reste que le canard 1 (opposite)
                self.targets_list = [f'{mult}{opposite}' for mult in ['S', 's', 'D', 'T']]
                players[actual_player].columns[0] = ('', 'str')
                players[actual_player].columns[1] = (f'{opposite}', 'str')
            
            elif getattr(self, 'drop', '') == 'opposite':
                # Le canard 1 (opposite) est mort, il ne reste que le canard 0 (master)
                self.targets_list = [f'{mult}{next_target}' for mult in ['S', 's', 'D', 'T']]
                players[actual_player].columns[0] = (f'{next_target}', 'str')
                players[actual_player].columns[1] = ('', 'str')
            
            else:
                # Sécurité par défaut
                self.targets_list = [f'{mult}{next_target}' for mult in ['S', 's', 'D', 'T']]
                players[actual_player].columns[0] = (f'{next_target}', 'str')
                players[actual_player].columns[1] = ('', 'str')
        
        else:
            players[actual_player].columns[1] = ('', 'str')
            players[actual_player].columns[0] = (f'{players[actual_player].goals[players[actual_player].next]}', 'str')
            players[actual_player].actual_hit = players[actual_player].goals[players[actual_player].next]
            self.targets_list = [f'{mult}{players[actual_player].goals[players[actual_player].next]}' for mult in ['S', 's', 'D', 'T']]
        
        # gestion leds
        if not self.bull:
            targets_str = '|'.join([f'{value}#{self.colors[0]}' for value in self.targets_list])
        else:
            targets_str = f'SB#{self.colors[0]}|DB#{self.colors[0]}'

        # Utilisation directe du nouveau gestionnaire de LED indépendant 
        self.rpi.set_target_leds(targets_str)

        if self.first:
            self.first = False

        return return_code

    def check_winner(self, players):
        """
        Last round : who is the winner ?
        """
        deuce = False
        best_score = -1
        best_player = -1
        for player in players:
            if player.score > best_score:
                best_score = player.score
                deuce = False
                best_player = player.ident
            elif player.score == best_score:
                deuce = True
                best_player = -1
        return best_player

    def early_player_button(self, players, actual_player, actual_round):
        """
        Pushed Player Early
        """

        return_code = 1
        self.first = True
        if actual_round == self.max_round and actual_player == self.nb_players - 1:
            self.winner = self.check_winner(players)
            if self.winner != -1:
                self.infos += rf"Current winner is Player {self.winner}"
                return_code = 3
            else:
                return_code = 2
        return return_code

    def refresh_stats(self, players, actual_round):
        """
        Method to refresh players' stats
        """

        for player in players:
            player.stats['Score'] = player.score
            player.stats['Reached Score'] = player.actual_hit
            player.stats['Hits'] = player.get_total_hit()

    def miss_button(self, players, actual_player, actual_round, player_launch):
        """
        Miss button
        """
        players[actual_player].columns[player_launch + 1] = ('MISS', 'str')
        players[actual_player].add_dart(actual_round, player_launch, 'MISS')
        players[actual_player].darts_thrown += 1

        if self.tirsrestant > 0:
            self.tirsrestant -= 1

        if self.bull:
            players[actual_player].columns[5] = (self.tirsrestant, 'int')
        else:
            players[actual_player].columns[5] = ('0', 'str')

        self.display.play_sound('balltrap_missed')
        self.show_pan = False
        self.duck_falling = False
        self.duck_hit_state = False
        self.dog_state = 'miss'
        self.dog_timer = pygame.time.get_ticks()

        self.refresh_stats(players, actual_round)

    def display_segment(self):
        False
    
    def refresh_game_screen(self, players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player, TxtOnlogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
        """
        Refresh In-game screen - Style Duck Hunt
        """
        ClickZones = {}

        # 1. Fond d'écran officiel du jeu via le chemin 'balltrap/Balltrap'
        self.display.screen.fill((0, 0, 0))
        bg_img = self.display.file_class.get_full_filename('balltrap/Balltrap', 'images')
        if bg_img:
            self.display.display_background(bg_img)
        else:
            self.display.display_background(self.logo)

        res_x = self.display.res['x']
        res_y = self.display.res['y']

        if not hasattr(self, 'duck_positions') or not self.duck_positions:
            self.duck_positions = [
                {'x': 100, 'y': int(res_y * 0.15), 'speed': 30}
            ]

        # 3. Affichage dynamique du chasseur (hunter_back_left / hunter_back_right) selon la position des canards
        hunter_w = 420 * res_x / 1920
        hunter_h = 520 * res_y / 1080
        hunter_x = (res_x - hunter_w) / 2  # Centré horizontalement
        hunter_y = res_y - hunter_h - 40   # Tout en bas de l'écran

        # --- ORIENTATION DU CHASSEUR ---
        duck_center_x = res_x / 2  # Valeur par défaut au centre
        
        if self.duck_positions:
            # cherche un canard qui vole
            active_duck = next((d for d in self.duck_positions if not d.get('falling', False) and not d.get('dead', False)), None)
            
            # S'ils sont mort, on prend le canard 0
            if not active_duck:
                active_duck = self.duck_positions[0]
                
            duck_center_x = active_duck['x'] + (120 * res_x / 1920) / 2

        # Si canard à gauche, chasseur regarde à gauche
        if duck_center_x < (res_x / 2):
            hunter_img_name = 'balltrap/hunter_back_left.png'
        else:
            hunter_img_name = 'balltrap/hunter_back_right.png'

        hunter_img = self.display.file_class.get_full_filename(hunter_img_name, 'images')
        if hunter_img:
            self.display.display_image(hunter_img, hunter_x, hunter_y, hunter_w, hunter_h, True, False, False)
            
        # --- AFFICHAGE DU POPUP "PAN !" LORS D'UN TIR ---
        if getattr(self, 'show_pan', False):
            if pygame.time.get_ticks() - getattr(self, 'pan_timer', 0) > 750:
                self.show_pan = False
            else:
                pan_w = 180 * res_x / 1920
                pan_h = 90 * res_y / 1080
                pan_x = hunter_x + (hunter_w / 2) - (pan_w / 2)
                pan_y = hunter_y - pan_h - 20
                
                self.display.blit_text("PAN !", pan_x, pan_y, pan_w, pan_h, color=(255, 255, 0))

        # 4. Affichage du Chiffre à toucher en HAUT au CENTRE (dans un cadre)
        if players and actual_player < len(players):
            if self.bull and self.tirsrestant > 0:
                current_target_text = "BULL"
            elif actual_round in (3, 6, 9, 12) and hasattr(self, 'targets_list') and self.targets_list:
                next_index = players[actual_player].next
                next_target = str(players[actual_player].goals[next_index])
                opposite = str(players[actual_player].goals[(20 + 2 * getattr(self, 'offset', 0) - next_index) % 20])
                
                # --- Vérifie si un canard est mort ---
                duck0_dead = len(self.duck_positions) > 0 and (self.duck_positions[0].get('falling', False) or self.duck_positions[0].get('dead', False))
                duck1_dead = len(self.duck_positions) > 1 and (self.duck_positions[1].get('falling', False) or self.duck_positions[1].get('dead', False))
                
                # S'il ne reste qu'un seul canard en vie (ou left == 1)
                left_count = getattr(self, 'left', 2)
                
                if left_count == 1 or (duck0_dead != duck1_dead):
                    # Si le canard 0 est mort, il ne reste que le canard 1 (opposite)
                    if duck0_dead and not duck1_dead:
                        current_target_text = f"{opposite}"
                    # Si le canard 1 est mort, il ne reste que le canard 0 (next_target)
                    elif duck1_dead and not duck0_dead:
                        current_target_text = f"{next_target}"
                    else:
                        # Fallback basé sur 'drop' si l'état des booléens est ambigu
                        if getattr(self, 'drop', '') == 'opposite':
                            current_target_text = f"{opposite}"
                        else:
                            current_target_text = f"{next_target}"
                elif len(self.duck_positions) == 2 and not duck0_dead and not duck1_dead:
                    current_target_text = f"{next_target} / {opposite}"
                else:
                    current_target_text = f"{next_target}"        

                # --- PRINT DE DEBUG : AFFICHAGE & CIBLES ---
                print(f"[DEBUG SCREEN] Round {actual_round} | left={getattr(self, 'left', 2)} | drop={getattr(self, 'drop', '')}")
                print(f"[DEBUG SCREEN] Duck0 dead={duck0_dead} | Duck1 dead={duck1_dead}")
                print(f"[DEBUG SCREEN] next_target={next_target} | opposite={opposite} ==> affiché VISE : {current_target_text}")
            else:
                current_target_text = str(players[actual_player].columns[0][0])
            
            box_w = 320 * res_x / 1920
            box_h = 70 * res_y / 1080
            box_x = (res_x - box_w) / 2
            box_y = int(res_y * 0.02)
            
            if hasattr(self.display, 'screen') and self.display.screen:
                pygame.draw.rect(self.display.screen, (20, 20, 40), (box_x, box_y, box_w, box_h), border_radius=10)
                pygame.draw.rect(self.display.screen, (200, 200, 200), (box_x, box_y, box_w, box_h), 2, border_radius=10)

            self.display.blit_text(f"VISE : {current_target_text}", box_x + 10, box_y + 10, box_w - 20, box_h - 20, color=self.display.colorset.get('fighters-actual-player', (255, 255, 255)))
            
        # 5. Affichage du Round en haut à droite - nom + score en bas a gauche
        if players:
            round_w = 260 * res_x / 1920
            round_h = 70 * res_y / 1080
            round_x = res_x - round_w - 30
            round_y = int(res_y * 0.02)

            if hasattr(self.display, 'screen') and self.display.screen:
                pygame.draw.rect(self.display.screen, (20, 20, 40), (round_x, round_y, round_w, round_h), border_radius=10)
                pygame.draw.rect(self.display.screen, (200, 200, 200), (round_x, round_y, round_w, round_h), 2, border_radius=10)

            self.display.blit_text(f"ROUND : {actual_round} / {max_round}", round_x + 10, round_y + 10, round_w - 20, round_h - 20, color=(255, 255, 255))
            
            # 5.2 : Affichage des Joueurs et des Scores EN BAS À GAUCHE
            box_score_w = 320 * res_x / 1920
            box_score_h = (len(players) * 45) + 35 
            box_score_x = 40
            box_score_y = res_y - box_score_h - 120

            if hasattr(self.display, 'screen') and self.display.screen:
                pygame.draw.rect(self.display.screen, (20, 20, 40), (box_score_x, box_score_y, box_score_w, box_score_h), border_radius=10)
                pygame.draw.rect(self.display.screen, (200, 200, 200), (box_score_x, box_score_y, box_score_w, box_score_h), 2, border_radius=10)

            self.display.blit_text("SCORES", box_score_x + 10, box_score_y + 5, box_score_w - 20, 30, color=(255, 255, 0))

            for idx, player in enumerate(players):
                if idx == actual_player:
                    p_color = self.display.colorset.get('fighters-actual-player', (255, 255, 0))
                else:
                    p_color = (200, 200, 200)
                
                player_text = f"{player.name} : {player.score} pts"
                self.display.blit_text(player_text, box_score_x + 15, box_score_y + 35 + (idx * 40), box_score_w - 30, 35, color=p_color)

        # 2. GESTION DU MOUVEMENT, ANIMATION ET AFFICHAGE DES CANARDS (DEVANT LE SCORE)
        duck_w = 120 * res_x / 1920
        duck_h = 100 * res_y / 1080
        sol_y = res_y - duck_h - 40  
        
        for idx, duck in enumerate(self.duck_positions):
            # --- SI LE CANARD EST MORT DÉFINITIVEMENT, ON L'IGNORE ---
            if duck.get('dead', False):
                continue

            if duck.get('falling', False):
                if duck.get('hit', False):
                    if pygame.time.get_ticks() - duck['hit_timer'] < 1000:
                        duck_img_name = 'balltrap/duck_hit.png'
                    else:
                        duck['hit'] = False  
                        duck_img_name = 'balltrap/duck_falling.png'
                else:
                    duck['y'] += 65  
                    if duck['y'] >= sol_y:
                        duck['falling'] = False
                        
                        # --- CE CANARD PRÉCIS (idx) MEURT DÉFINITIVEMENT ---
                        if actual_round in (3, 6, 9, 12) and not self.bull:
                            duck['dead'] = True  # Seul CE canard reste au sol
                            print(f"[DEBUG DUCK] Canard {idx} touché et mort définitivement au round {actual_round}")
                        else:
                            duck['dead'] = False 
                            duck['x'] = -duck_w
                            if actual_round in (3, 6, 9, 12):
                                duck['y'] = int(res_y * 0.15) if idx == 0 else int(res_y * 0.35)
                            else:
                                duck['y'] = int(res_y * 0.20)
                            print(f"[DEBUG DUCK] Canard {idx} respawn (revient par la gauche)")
                        
                        if actual_round in (3, 6, 9, 12) and len(self.duck_positions) >= 2:
                            other_duck = self.duck_positions[1] if idx == 0 else self.duck_positions[0]
                            if other_duck.get('falling', False) or other_duck.get('dead', False) or other_duck['x'] < 0:
                                self.dog_state = 'success_double'
                            else:
                                self.dog_state = 'success'
                        else:
                            self.dog_state = 'success'
                            
                        self.dog_timer = pygame.time.get_ticks()
                        
                        self.display.play_sound('balltrap_success')
                        
                    duck_img_name = 'balltrap/duck_falling.png'
            else:
                speed = duck.get('speed', 30)
                duck['x'] += speed  
                
                if duck['x'] > res_x:
                    duck['x'] = -duck_w  

                anim_frame = (pygame.time.get_ticks() // 200) % 2
                duck_img_name = 'balltrap/duck_fly1.png' if anim_frame == 0 else 'balltrap/duck_fly2.png'
                
                
                # --- JOUE COINCOIN en mm temps que l animation duck_fly1 et 2 ---
                if idx == 0 and anim_frame == 0:
                    current_time = pygame.time.get_ticks()
                    if not hasattr(self, 'last_coin_time'):
                        self.last_coin_time = 0
                    
                    # attendre 5 secondes (5000 ms) entre chaque coincoin
                    if current_time - self.last_coin_time > 7500:
                        self.last_coin_time = current_time
                        self.display.play_sound('balltrap_duckquack')

            duck_img = self.display.file_class.get_full_filename(duck_img_name, 'images')
            if duck_img:
                self.display.display_image(duck_img, duck['x'], duck['y'], duck_w, duck_h, True, False, False)

        # 6. Chien (dog_wait en permanence OU dog_caught / dog_caught2 / dog_laugh animé en bas à droite)
        dog_w = 250 * res_x / 1920
        dog_h = 250 * res_y / 1080
        dog_x = res_x - dog_w - 60  
        dog_y = res_y - dog_h - 60

        if self.dog_state is not None:
            elapsed = pygame.time.get_ticks() - self.dog_timer
            if -1000 < elapsed < 2000:
                if self.dog_state == 'success_double':
                    dog_img_name = 'balltrap/dog_caught2.png'
                elif self.dog_state == 'success':
                    dog_img_name = 'balltrap/dog_caught.png'
                else:
                    # Alternance 4x entre dog_laugh et dog_laugh2 sur les 2000ms (toutes les 500ms)
                    frame = (elapsed // 500) % 2
                    dog_img_name = 'balltrap/dog_laugh2.png' if frame == 1 else 'balltrap/dog_laugh.png'
            else:
                self.dog_state = None
                dog_img_name = 'balltrap/dog_wait.png'
        else:
            dog_img_name = 'balltrap/dog_wait.png'

        dog_img = self.display.file_class.get_full_filename(f'balltrap/{dog_img_name.split("/")[-1]}', 'images')
        if dog_img:
            self.display.display_image(dog_img, dog_x, dog_y, dog_w, dog_h, True, False, False)

        # 7. Munitions 
        cart_w = 35 * res_x / 1920
        cart_h = 70 * res_y / 1080
        cart_x = 50
        cart_y = res_y - cart_h - 30
        
        cart_img = self.display.file_class.get_full_filename('balltrap/cartridge', 'images')
        if cart_img:
            for i in range(self.tirsrestant):
                self.display.display_image(cart_img, cart_x, cart_y, cart_w, cart_h, True, False, False)
                cart_x += cart_w + 10
                
        if self.debug_balltrap :        
            # ==========================================
            # --- RÉCUPÉRATION DES ÉTATS ET ANIMATIONS ---
            # ==========================================
            next_index = players[actual_player].next
            next_target = str(players[actual_player].goals[next_index]) if players and actual_player < len(players) else ""
            opposite = str(players[actual_player].goals[(20 + 2 * getattr(self, 'offset', 0) - next_index) % 20]) if players and actual_player < len(players) else ""
    
            # Canard 0 (master)
            duck0 = self.duck_positions[0] if len(self.duck_positions) > 0 else {}
            d0_x = int(duck0.get('x', 0))
            d0_y = int(duck0.get('y', 0))
            d0_alive = "DEAD" if duck0.get('dead', False) or duck0.get('falling', False) else "VIVANT"
    
            # Canard 1 (opposite)
            duck1 = self.duck_positions[1] if len(self.duck_positions) > 1 else {}
            d1_x = int(duck1.get('x', 0))
            d1_y = int(duck1.get('y', 0))
            d1_alive = "DEAD" if duck1.get('dead', False) or duck1.get('falling', False) else "VIVANT"
    
            # --- NOM DE L'ANIMATION DU CHIEN ---
            # Si self.dog_state est None ou vide, le chien est par défaut en mode 'wait' (attente)
            if self.dog_state is not None and str(self.dog_state).strip() != "":
                dog_anim = str(self.dog_state)
            else:
                dog_anim = "wait"
    
            # Textes à afficher dans les 3 rectangles
            texts_box1 = [
                f"canard 0 (master) = {next_target}",
                f"position X = {d0_x} | position Y = {d0_y}",
                f"canard vivant ou dead = {d0_alive}"
            ]
    
            texts_box2 = [
                f"canard 1 (opposite) = {opposite}",
                f"position X = {d1_x} | position Y = {d1_y}",
                f"canard vivant ou dead = {d1_alive}"
            ]
    
            texts_box3 = [
                f"chien animation en cours = {dog_anim}",
                "-----",
                f"vise = {current_target_text if 'current_target_text' in locals() else ''}"
            ]
    
            boxes_data = [texts_box1, texts_box2, texts_box3]
    
            # ==========================================
            # --- AFFICHAGE GRAPHIQUE DES RECTANGLES ---
            # ==========================================
            dbg_w = 600 * res_x / 1920
            dbg_h = 130 * res_y / 1080
            dbg_x = (res_x - dbg_w) / 2
            
            total_dbg_h = (dbg_h * 3) + 40
            dbg_start_y = (res_y - total_dbg_h) / 2
    
            for i, lines in enumerate(boxes_data):
                cur_y = dbg_start_y + i * (dbg_h + 20)
                
                if hasattr(self.display, 'screen') and self.display.screen:
                    pygame.draw.rect(self.display.screen, (0, 0, 0), (dbg_x, cur_y, dbg_w, dbg_h), border_radius=12)
                    pygame.draw.rect(self.display.screen, (255, 255, 255), (dbg_x, cur_y, dbg_w, dbg_h), 3, border_radius=12)
    
                line_h = dbg_h / len(lines)
                for j, line_text in enumerate(lines):
                    self.display.blit_text(
                        line_text, 
                        dbg_x + 15, 
                        cur_y + 8 + (j * line_h), 
                        dbg_w - 30, 
                        line_h - 4, 
                        color=(255, 255, 255)
                    )

        if end_of_game:
            ClickZones = self.display.end_of_game_menu(logo, stat_button=False)

        self.display.update_screen()
        return ClickZones
