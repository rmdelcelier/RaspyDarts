# -*- coding: utf-8 -*-
# Game by ... LaDite
########
import random
import pygame
from include import cplayer
from include import cgame

#

############
# Game Variables
############
OPTIONS = {'max_round': '10', 'simple50' : False}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3  # Total darts the player has to play
LOGO = 'Voleur.png'
HEADERS = ["D1", "D2", "D3", "", "Rnd", "PPD", "PPR"] # Columns headers - Must be a string
VERSION = '1.00'

def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
    """
    return nb_players >= 2 and nb_players <= 12, VERSION, 12
    
class CPlayerExtended(cplayer.Player):
    """
    Exetended player class
    """
    def __init__(self, ident, config):
        super(CPlayerExtended, self).__init__(ident, config)
        # Extend the basic players property with your own here
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record] = '0'
        

class Game(cgame.Game):
    """
    >Voleur game class
    """
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.game_records = GAME_RECORDS
        self.nb_darts = NB_DARTS
        self.logo = LOGO
        self.headers = HEADERS
        self.options = options
        #  Get the maximum round number
        self.max_round = int(options['max_round'])
        self.simple = options['simple50']


        if self.simple:
            self.score_map.update({'SB': 50})
        else:
            self.score_map.update({'SB': 25})

        self.winner = None

        self.video_player = video_player
        
        self.scale = self.display.res['x'] / 1920
        
###"
      # tailles des elements
        self.space = self.display.res['y'] / 20
        self.bh = self.display.res['y'] / 10
        self.targetH = self.display.res['y'] - self.bh * 3 - self.space * 3
###
        
### declaration variable 
        self.chiffre_joue = [0, 0, 0]
        self.leds = True
        self.next_player = 0
        self.p_ident = 0
        self.p_name = ''
        
        self.options = OPTIONS
        
        self.listeS = []
        self.listeD = []
        self.listeT = []
        
        self.margin = self.display.margin
        self.margin_2 = 2 * self.display.margin
        self.margin_4 = 4 * self.display.margin
        
        self.dart = self.display.file_class.get_full_filename('dart', 'images')
        self.dart_icon = self.display.file_class.get_full_filename('dart_icon', 'images')
        self.online_icon = self.display.file_class.get_full_filename('online', 'images')

            
    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        return_code = 0
###
        ### ajout pour refresh_games
        self.player_launch = player_launch
        self.actual_round = actual_round
        self.actual_player = actual_player
        
###

### INITIALISE LES LEDS DE TOUTES LES LEDS POUR CHAQUE JOUEUR -- player.targets
        if self.leds :
                for player in players :
                        hitsS = [f'S{number}#{self.colors[0]}' for number in range(1,21)]
                        hitsD = [f'D{number}#{self.colors[0]}' for number in range(1,21)]
                        hitsT = [f'T{number}#{self.colors[0]}' for number in range(1,21)]
                        Sbull = [f'SB#{self.colors[0]}']
                        Dbull = [f'DB#{self.colors[0]}']
                        
                        self.rpi.set_target_leds('|'.join(hitsS + hitsD + hitsT + Sbull + Dbull))
                        
                        player.targets = hitsS + hitsD + hitsT + Sbull + Dbull
                                   
                        self.leds = False
                        
                #### choisi 3 chiffres au hasard pour j1 a enlever lors du premier tour
                SDT = ['S' , 'D', 'T']
                lettre1 = random.choice(SDT)
                lettre2 = random.choice(SDT)
                lettre3 = random.choice(SDT)
                self.chiffre_joue[0] = lettre1 + str(random.randint(1, 19))
                self.chiffre_joue[1] = lettre2 + str(random.randint(1, 19))
                self.chiffre_joue[2] = lettre3 + str(random.randint(1, 19))
                
        if player_launch == 1: 
            players[actual_player].reset_darts()

        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.error(f"Handicap failed : {exception}")

            for player in players:
                # Init score
                player.score = 0
            
            ### RETIRE LES SEGMENT ALEATOIRE DE J1 AU DEBUT DU PREMIER TOUR
            try :
                    while True :
                            players[actual_player].targets.remove(self.chiffre_joue[0]+'#green') 
                            players[actual_player].targets.remove(self.chiffre_joue[1]+'#green') 
                            players[actual_player].targets.remove(self.chiffre_joue[2]+'#green') 
            except :
                    pass 

        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            players[actual_player].pre_play_score = players[actual_player].score
            
            ### SUPPRIME les chiffres joue par le joueur precedent (NORMALEMENT DEJA RETIRE QD JOUEUR PRECEDENT A JOUER - verifier et effacer)
            try :
                while True :
                    players[actual_player].targets.remove(self.chiffre_joue[0]+'#green') 
            except :
                print('condition except [0]')
                    
            try :
                while True :
                    players[actual_player].targets.remove(self.chiffre_joue[1]+'#green') 
            except :
                print('condition except [1]')
                    
            try :
                while True :
                    players[actual_player].targets.remove(self.chiffre_joue[2]+'#green') 
            except :
                print('condition except [2]')       

            ### REINITIALISE LES CHIFFRES JOUES
            self.chiffre_joue[0] = 0    
            self.chiffre_joue[1] = 0    
            self.chiffre_joue[2] = 0  
            
            ### MAJ DES TARGETS DU JOUEUR
            self.rpi.set_target_leds ('')
            self.rpi.set_target_leds('|'.join(players[actual_player].targets))
                           

            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for i in range(0,7):
                players[actual_player].columns.append(['', 'int'])
            if actual_round == 1 and actual_player == 0:
                for player in players:
                    player.reset_rounds(self.max_round)

        # Display avg
        if actual_round == 1 and player_launch == 1:
                
                players[actual_player].columns[5] = (0.0, 'int')
                players[actual_player].columns[6] = (0.0, 'int')

        # Clean next boxes
        for i in range(player_launch - 1,self.nb_darts):
            players[actual_player].columns[i] = ('', 'int')
            

        if players[actual_player].ident == 0 :
                self.p_ident = 0
                self.next_player = 1
        elif players[actual_player].ident == self.nb_players -1 :
                self.p_ident = players[actual_player].ident
                self.next_player = 0
        else :
                self.p_ident = players[actual_player].ident  
                self.next_player = self.p_ident + 1 

        if actual_player == self.p_ident : ###0 : 
                listeS = []
                listeD = []
                listeT = []
                for player in players :
                        if player.ident == self.next_player :  ### self.next_player = joueur suivant du joueur actif
                                self.p_name = player.name
                                for liste in player.targets:
                                        if liste[:1] == 'S':
                                                listeS.append(liste)
                                        if liste[:1] == 'D' :
                                                listeD.append(liste)
                                        if liste[:1] == 'T' :
                                                listeT.append(liste)
                
                                #modifie les listes "s20#green" en "20"
                                nvellListeS = []
                                for val in listeS:
                                        indexDiese = val.find('#')
                                        nvellListeS.append(val[1:indexDiese])
                                
                                nvellListeD = []
                                for val in listeD:
                                        indexDiese = val.find('#')
                                        nvellListeD.append(val[1:indexDiese])
                                        
                                nvellListeT = []
                                for val in listeT:
                                        indexDiese = val.find('#')
                                        nvellListeT.append(val[1:indexDiese])        
                                
                                #modifie les listes pour n afficher que les segments a afficher
                                listeall = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', 'B']
                                new_listS = []
                                new_listD = []
                                new_listT = []

                                for element in listeall:
                                        if element not in nvellListeS:
                                                new_listS.append(element)
                                        
                                for element in listeall:
                                        if element not in nvellListeD:
                                                new_listD.append(element)  
                                        
                                for element in listeall:
                                        if element not in nvellListeT:
                                                new_listT.append(element)       
                                        
                                print('liste pour afficher les segments')
                                print(new_listS)
                                print(new_listD)
                                print(new_listT)
                                
                                self.listeS = new_listS   
                                self.listeD = new_listD   
                                self.listeT = new_listT   

       
        # Print debug output
        self.logs.debug(self.infos)
        return return_code

###############
    # PNJ SCORE METHOD FOR VOLEUR
    ###############
    def pnj_score(self, players, actual_player, level, player_launch):
        """
        Intelligence Artificielle (PNJ) pour le jeu Voleur :
        - Stratégie humaine : vise en priorité les gros scores (20, 19, 18) en T/D et le Bull (non volable).
        - Gère les 5 niveaux de difficulté avec taux de réussite, voisins physiques et ratés (MISS).
        """
        # =========================================================================
        # GUIDE DE RÉGLAGE DES NIVEAUX DE DIFFICULTÉ :
        # - Légende des niveaux : [p_exact, p_neighbor, p_miss]
        #   * p_exact    : Probabilité de toucher exactement la cible visée (%)
        #   * p_neighbor : Probabilité de dévier vers un secteur voisin physique (%)
        #   * p_miss     : Probabilité de rater complètement (retourne 'MISS') (%)
        # - Ajustement : Pour renforcer l'IA, augmente p_exact et réduis p_miss.
        # =========================================================================

        # Table de précision par niveau : [ % Exact, % Voisin, % Miss ]
        levels = [
            [15, 45, 40],  # Niveau 1 (Noob) : 15% exact, 45% voisin, 40% miss
            [30, 50, 20],  # Niveau 2 (Débutant) : 30% exact, 50% voisin, 20% miss
            [45, 35, 15],  # Niveau 3 (Intermédiaire) : 45% exact, 35% voisin, 15% miss
            [72, 23,  5],  # Niveau 4 (Pro) : 72% exact, 23% voisin, 5% miss
            [90, 10,  0]   # Niveau 5 (Expert) : 90% exact, 10% voisin, 0% miss
        ]

        try:
            comp_lvl = int(level)
        except (ValueError, TypeError):
            comp_lvl = 3

        lvl_idx = max(0, min(comp_lvl - 1, len(levels) - 1))
        p_exact = levels[lvl_idx][0]
        p_neighbor = levels[lvl_idx][1]

        # 1. Choix stratégique de la cible (maximiser les points et viser le Bull sécurisé)
        if comp_lvl >= 4:
            high_values = [20, 19, 18, 17]
            mult_options = ['T', 'T', 'D', 'S']
        elif comp_lvl == 3:
            high_values = [20, 19, 18, 20, 19]
            mult_options = ['T', 'D', 'S', 'S']
        else:
            high_values = [20, 19, 18, 16, 15, 14]
            mult_options = ['S', 'S', 'S', 'D']

        # Occasionnellement viser le Bull (car il rapporte des points et ne peut pas être volé)
        bull_chance = 15 if comp_lvl >= 3 else 5
        if random.randint(1, 100) <= bull_chance:
            intended_hit = 'DB' if (comp_lvl >= 4 and random.randint(1, 100) <= 50) else 'SB'
        else:
            val = random.choice(high_values)
            mult = random.choice(mult_options)
            
            # Comportement humain : les niveaux bas évitent ou ratent les triples trop ambitieux
            if comp_lvl <= 2 and mult == 'T':
                mult = 'S'
            elif comp_lvl == 3 and mult == 'T' and random.randint(1, 100) <= 40:
                mult = 'S'
                
            intended_hit = f"{mult}{val}"

        # 2. Extraction du multiplicateur et de la valeur
        mult = intended_hit[0] if intended_hit[:1] in ['S', 'D', 'T'] else 'S'
        try:
            val_str = intended_hit[1:] if mult in ['S', 'D', 'T'] else intended_hit
            if val_str in ['SB', 'DB', 'B']:
                base_val = val_str
            else:
                base_val = int(val_str)
        except ValueError:
            base_val = 20
            mult = 'S'

        # 3. Gestion si la cible est un Bull (SB / DB)
        if base_val in ['SB', 'DB', 'B']:
            roll = random.randint(1, 100)
            if roll <= p_exact:
                return 'DB' if (comp_lvl >= 4 and base_val == 'DB') else 'SB'
            elif roll <= p_exact + p_neighbor:
                return 'SB' if base_val == 'DB' else 'MISS'
            else:
                return 'MISS'

        # 4. Matrice de voisinage physique de la cible de fléchettes (1-20)
        dartboard_neighbors = {
            20: [1, 5],   1: [20, 18], 18: [1, 4],   4: [18, 13], 13: [4, 6],
            6: [13, 10], 10: [6, 15],  15: [10, 2],  2: [15, 17], 17: [2, 3],
            3: [17, 19], 19: [3, 7],   7: [19, 16], 16: [7, 8],   8: [16, 11],
            11: [8, 14], 14: [11, 9],  9: [14, 12], 12: [9, 5],   5: [12, 20]
        }

        # 5. Évaluation physique du tir (Exact, Voisin, Miss)
        roll = random.randint(1, 100)

        if roll <= p_exact:
            # Succès exact
            return f"{mult}{base_val}"
        elif roll <= p_exact + p_neighbor:
            # Raté de précision : déviation sur un segment voisin physique
            neighbors = dartboard_neighbors.get(base_val, [1, 5])
            hit_val = random.choice(neighbors)
            
            # Si on visait un Double ou Triple et qu'on rate, la fléchette glisse en Simple
            if mult in ['D', 'T']:
                mult = 'S'
                
            return f"{mult}{hit_val}"
        else:
            # Raté total (Miss)
            return 'MISS'
   
    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Function run after each dart throw - for example, add points to player
        """
        
        handler = self.init_handler()
        
        #self.display.sound_for_touch(hit) # Touched !
        
        # Play DMD animation
        if super().play_show(players[actual_player].darts, hit, play_special=True):
            self.display.sound_for_touch(hit)
    
### QD ON TOUCHE UN SEGMENT ETEINT, ON NE PREND PAS DE POINTS MAIS ON LE SUPPRIME POUR LE JOUEUR SUIVANT             
        if not (hit+'#green') in players[actual_player].targets:
                
                if player_launch == 1 :
                        self.chiffre_joue[0] = hit
                        for player in players :
                                if player.ident == self.next_player :
                                        try:
                                                while True :
                                                        player.targets.remove(self.chiffre_joue[0]+'#green') 
                
                                        except :
                                                pass
                                        
                elif player_launch == 2 :
                        self.chiffre_joue[1] = hit
                        for player in players :
                                if player.ident == self.next_player :
                                        try:
                                                while True :
                                                        player.targets.remove(self.chiffre_joue[1]+'#green') 
                
                                        except :
                                                pass
                elif player_launch == 3 :
                        self.chiffre_joue[2] = hit
                        for player in players :
                                if player.ident == self.next_player :
                                        try:
                                                while True :
                                                        player.targets.remove(self.chiffre_joue[2]+'#green') 
                
                                        except :
                                                pass
                #message = 'segment volé'
                #self.display.speech(message, speed=100)
                #self.display.play_sound('plouf')
                handler['sound'] = 'plouf'
                #players[actual_player].darts_thrown += 1
                score = 0
                
        if (hit[1:]) == 'B' :
                score = self.score_map[hit] 
                
                
        ### QD ON TOUCHE UN SEGMENT ALLUME, ON LE SUPPRIME POUR LE JOUEUR SUIVANT SAUF BULL            
        if (hit+'#green') in players[actual_player].targets and (hit[1:]) != 'B':
                if player_launch == 1 :
                        self.chiffre_joue[0] = hit
                        for player in players :
                                if player.ident == self.next_player :
                                        try:
                                                while True :
                                                        player.targets.remove(self.chiffre_joue[0]+'#green') 
                
                                        except :
                                                pass
                                        
                elif player_launch == 2 :
                        self.chiffre_joue[1] = hit
                        for player in players :
                                if player.ident == self.next_player :
                                        try:
                                                while True :
                                                        player.targets.remove(self.chiffre_joue[1]+'#green') 
                
                                        except :
                                                pass
                elif player_launch == 3 :
                        self.chiffre_joue[2] = hit
                        for player in players :
                                if player.ident == self.next_player :
                                        try:
                                                while True :
                                                        player.targets.remove(self.chiffre_joue[2]+'#green') 
                
                                        except :
                                                pass
                            
                
                score = self.score_map[hit] 
                
                ### MAJ DES TARGETS DU JOUEUR
                self.rpi.set_target_leds ('')
                self.rpi.set_target_leds('|'.join(players[actual_player].targets))
        
                #message = 'segment volé a ladversaire'
                #self.display.speech(message, speed=100)
                #self.display.play_sound('plouf')
                self.display.sound_for_touch(hit) # Touched !
                
        return_code = 0

               
        players[actual_player].add_dart(actual_round, player_launch, hit, score=score)

        players[actual_player].score += score
        players[actual_player].round_points += score
        players[actual_player].points += score


        # Store what he played in the table
        players[actual_player].columns[player_launch - 1] = (score, 'int')
        # Store total for the round in column 6 (start from 0)
        players[actual_player].columns[4] = (players[actual_player].round_points, 'int')
        # Calculate average and display in column 7
        players[actual_player].columns[5] = (players[actual_player].show_ppd(), 'int')
        players[actual_player].columns[6] = (players[actual_player].show_ppr(), 'int')

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].increment_hits(hit)
        self.refresh_stats(players, actual_round)

        # Check for end of game (no more rounds to play)
        if player_launch == self.nb_darts and actual_round >= int(self.max_round) \
                and actual_player == len(players) - 1:
            winner = self.best_score(players)
            if winner >= 0:
                self.winner = winner
                return_code = 3
            else:
                # No winner : last round reached
                return_code = 2
       
        # Time for shot or video ?
        handler['take_shot'] = self.time_to_take_shot_or_video(hit)
        handler['return_code'] = return_code
        return handler
        
        #return return_code       

    def best_score(self, players):
        """
        Find the winner
        Only one player with best score
        """
        best_player = None
        best_score = None
        best_count = 0
        for player in players:
            if best_score is None or player.score > best_score:
                best_score = player.score
                best_player = player.ident
                best_count = 1
                self.logs.debug(\
                        f"Best found : {best_score} / Count={best_count} / player = {best_player}")
            elif player.score == best_score:
                best_count += 1

        self.logs.debug(\
                f"Best score : {best_score} / Count={best_count} / Player = {best_player}")

        if best_count == 1:
            return best_player
        return -1


    def display_segment(self):
        """
        Set if a message is shown to indicate the segment hitted !
        """
        return False

    def post_round_check(self, players, actual_round, actual_player):
        """
        Post round checks
        When PLAYER BUTTON is pressed on last round of last player
        """
        if actual_round >= int(self.max_round) and actual_player == len(players) - 1:
            # Last round, last player
            return self.best_score(players)
        return -2


    def get_winner(self, players):
        """
        Sudden death option :
        After each round, the winner is the last alive player
        """
        nb_winner = 0
        for i in range(0, len(players)):
            if players[i].alive:
                winner = i
                nb_winner += 1

        if nb_winner == 1:
            return winner
        return None

    def get_score(self, player):
        """
        Return score of player
        """
        return player.score

    def next_set_order(self, players):
        """
        Sort players for next set
        """
        players.sort(key=self.get_score)

    def refresh_stats(self, players, actual_round):
        """
        refresh players' stats
        """
        for player in players:
            player.stats['Points Per Round'] = player.show_ppr()
            player.stats['Points Per Dart'] = player.show_ppd()
    
    
    def actual_player_score(self, pos_x, pos_y, width, height, heading_height, dart_icon_size, color, name, score):

        self.display.blit_rect(pos_x, pos_y, width, heading_height, color)
        self.display.blit_rect(pos_x, pos_y + heading_height, width, height - heading_height, color)
        pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (pos_x, pos_y + heading_height), (pos_x + width, pos_y + heading_height), 2)
        pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (pos_x, pos_y), (pos_x, pos_y + height), 2)
        pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (pos_x + width, pos_y), (pos_x + width, pos_y + height), 2)
        self.display.display_image(self.dart_icon, pos_x + self.margin, pos_y + heading_height + self.margin, width=dart_icon_size, height=dart_icon_size, UseCache=True)
        self.display.blit_text(name, pos_x, pos_y - self.margin, width, heading_height + self.margin_2, color=self.display.colorset['game-bg'], align='Center')
        self.display.blit_text(score, pos_x, pos_y + heading_height, width, height - heading_height, color=self.display.colorset['game-score'], align='Right')


        
    ###############
    # Refresh In-game screen
    ###############
   
    def refresh_game_screen(self, players, actual_round, max_round, rem_darts, nb_darts, logo, headers, actual_player, TxtOnLogo=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
        
        # Clear
        self.display.screen.fill((0, 0, 0))
        
        game_background = f"background_{logo.replace('_', '_').replace('!', '').split('.')[0]}"
        game_background = self.display.file_class.get_full_filename(game_background, 'images')
        if game_background is not None:
            self.display.display_background(image=game_background)
            self.display.save_background()
        else:
            self.display.display_background()
           
        
        game = 'Voleur'
        hit = ''
        ppd = players[actual_player].show_ppd()
        ppr = players[actual_player].show_ppr()

        scores = players[actual_player].rounds
        score = players[actual_player].score
        darts = None
        #reprendre score via un self par fleche
        ####self.score_map[dartx]
        
        for dart in players[actual_player].darts:
            if dart is None:
                dart = 'MISS'
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
     
     
        self.display.blit_rect(0, 0, self.display.res['x'], self.display.res['y'], self.display.colorset['game-bg'])

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
        hit_w = self.display.res['x'] - (2 * hit_x)   ###self.display.mid_x + 4 * self.margin
        hit_h = self.display.mid_y + 4 * self.margin


        
        # Display players ans scores 
        if not end_of_game:
            player_y = int(self.display.res['y'] / 16)
        else:
            player_y = int(self.display.res['y'] / 3)
        player_height = int(self.display.res['y'] / 8)
        player_width = int(self.display.res['x'] / max(2 * len(players), 6))
        players_x = int(self.display.res['x'] / 4 + (self.display.res['x'] / 2 - player_width * len(players) - int(player_width / 2)) / 2)

        index = 0

        ### AFFICHE LES JOUEURS
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
                self.display.blit_rect(player_x, player_y + heading_height, player_width, player_height - heading_height, player_color)

                pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (player_x, player_y + heading_height), (player_x + player_width, player_y + heading_height), 2)
                pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (player_x, player_y), (player_x, player_y + player_height), 2)
                pygame.draw.line(self.display.screen, self.display.colorset['game-bg'], (player_x + player_width, player_y), (player_x + player_width, player_y + player_height), 2)

                if index < actual_player:
                    align = 'Left'
                else:
                    align = 'Right'
                pygame.draw.line(self.display.screen, color, (player_x, player_y), (player_x + player_width, player_y), self.margin_2)
                self.display.blit_text(name, player_x, player_y - self.margin_2, player_width, heading_height + self.margin_2, color=player_color, align=align)
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

        #self.actual_player_score(actual_x, player_y, player_width, player_height, heading_height, dart_icon_size, actual_color, actual_name, actual_score)
        
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

            # PPR and PPD
            if index == 1:
                self.display.blit_text(f'PPR', ppdr_x, right_y, ppdr_width, right_height, color=self.display.colorset['game-score'], align='Right')
                self.display.blit_text(f'{ppr}', ppdr_x + ppdr_width, right_y, right_width - ppdr_width, right_height, color=actual_color, align='Left')
            elif index == 2:
                self.display.blit_text(f'PPD', ppdr_x, right_y , ppdr_width, right_height, color=self.display.colorset['game-score'], align='Right')
                self.display.blit_text(f'{ppd}', ppdr_x + ppdr_width, right_y , right_width - ppdr_width, right_height, color=actual_color, align='Left')

            right_y += right_height
            
            
        # Dartts' scores
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

       
        
        for index in range(3):
            if index == rem_darts - 1:

                # Actual player's score
                rect5 = pygame.Rect(actual_x, player_y, player_width, player_height)
                sub5 = self.display.screen.subsurface(rect5)
                screenshot5 = pygame.Surface((mid_width, mid_height))
                screenshot5.blit(sub5, (0, 0))
                rect5 = (actual_x, player_y, player_width, player_height, heading_height, dart_icon_size, actual_color, actual_name, actual_score)

            if index < rem_darts and not end_of_game:
                self.display.display_image(self.dart, right_x, right_y, width=right_width ,height=right_height, UseCache=True)
            right_y += right_height

        self.actual_player_score(actual_x, player_y, player_width, player_height, heading_height, dart_icon_size, actual_color, actual_name, actual_score)
        if not end_of_game:
            if OnScreenButtons:
                mid_y -= int(self.display.res['y'] / 16)

            self.display.blit_text(darts, mid_x, mid_y, mid_width, mid_height, color=self.display.colorset['game-score'], dafont=None, align='Center')


        
        image_voleur = self.display.file_class.get_full_filename('voleur/voleur', 'images')
        self.display.display_image(image_voleur, 15, int(self.display.res['y'] * 2 / 4) + self.margin , width=320, height=320, UseCache=True)

 
####
        
        if not end_of_game:
            rect = (self.display.res['x'] / 2 - self.targetH /2 ,self.display.res['y'] / 2 - self.targetH / 2, self.targetH, self.targetH)
            self.display.display_image(self.display.file_class.get_full_filename('voleur/voleur_target', 'images'),rect[0], rect[1], rect[2], rect[3], True, False, False)

            #if self.player_launch == 1 and actual_player == 1 and round == 1:
            self.display.blit_text(f"VOLEZ LES SEGMENTS DE " + str(self.p_name.upper()) , 25, 200 , 300, 60 , color=(255, 255, 0)) 
               
            if self.actual_round == 1 and self.player_launch == 1 and self.actual_player == 0:        
                #for s in range (1,21):
                #  self.display.display_image(self.display.file_class.get_full_filename(f'voleur/ALL{s}', 'images'), rect[0], rect[1], rect[2], rect[3], True, False, False)
                #self.display.display_image(self.display.file_class.get_full_filename('voleur/voleur_target', 'images'),rect[0], rect[1], rect[2], rect[3], True, False, False)
                print('ligne 752 - suppression de la condition car n affiche plus tous les segments mais juste les segments manquants')        
            else:
                for player in players:
                  for s in self.listeS :
                     self.display.display_image(self.display.file_class.get_full_filename(f'voleur/S{s}', 'images'),rect[0], rect[1], rect[2], rect[3], True, False, False)
                  for s in self.listeD :
                     self.display.display_image(self.display.file_class.get_full_filename(f'voleur/D{s}', 'images'),rect[0], rect[1], rect[2], rect[3], True, False, False)
                  for s in self.listeT :
                     self.display.display_image(self.display.file_class.get_full_filename(f'voleur/T{s}', 'images'),rect[0], rect[1], rect[2], rect[3], True, False, False)
            
            
            self.display.blit_text(f'{players[actual_player].round_points}', right_x + self.margin, right_y  - self.margin ,  150, 150, color=(255,255,255), align='Center')
                    
            self.display.update_screen()
        else :
            ClickZones = self.display.end_of_game_menu(logo, stat_button=False)
            return ClickZones

###       
        if end_of_game:
            ClickZones = self.display.end_of_game_menu(logo, stat_button=True)
            return ClickZones
