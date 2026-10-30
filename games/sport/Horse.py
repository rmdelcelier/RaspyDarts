# -*- coding: utf-8 -*-
"""
Game by ... LaDite
jeu base sur GooseOfGame
"""
# Versions
# 1.00

from include import cplayer
from include import cgame
import random
VERSION = '1.00'
GAME_LOGO = 'Horse.png'
HEADERS = "D1","D2","","","","","CASE" 
OPTIONS = {'theme': 'default' , 'max_round': 20, 'inter': False, 'master': False} 
NB_DARTS = 3
GAME_RECORDS = {'Score Per Round': 'DESC', 'Dribbles': 'DESC'}


def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
    """
    return nb_players <= 4, VERSION, 4
    
class CPlayerExtended(cplayer.Player):
    """
    Extend the basic player
    """
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        # Read the CJoueur class parameters, and add here yours if needed
        
        self.color = 'tbd'

        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record]='0'

class Game(cgame.Game):
    """
    Horse game class
    """
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        # GameRecords is the dictionnary of stats (see above)
        self.game_records = GAME_RECORDS
        # Import game settings
        self.logo = GAME_LOGO
        self.headers = HEADERS
        self.nb_darts = NB_DARTS
        self.options = options
        
        # Generic but copied as reminder
        self.colors = ['green', 'blue', 'red', 'yellow', 'silver']
        
        # Game of Goose specific
        self.positions = {}                                     # to store positions of players
        self.totalTurn = 0                                      # to store total of dice
        self.dartScore = 0

        self.scale = self.display.res['x'] * 95 / 1920          # Adapt token to screen
        self.scale = self.scale / 0.7                       # Change size
        self.chiffreY = 490 ####self.scale /0.48    ####190
        
        # Coordinates of spaces on board
        self.coords = [[0,513], [160, 513], [318, 513], [482, 513], [642, 513], [804, 513], [966,513], [1127, 513], [1289, 513], [1451, 513], [1613, 513],[1775, 513]]       
        self.coords1 = [[0,657], [160, 657], [318, 657], [482, 657], [642, 657], [804, 657], [966,657], [1127, 657], [1289, 657], [1451, 657], [1613, 657],[1775, 657]]
        self.coords2 = [[0,803], [160, 803], [318, 803], [482, 803], [642, 803], [804, 803], [966,803], [1127, 803], [1289, 803], [1451, 803], [1613, 803],[1775, 803]]
        self.coords3 = [[0,948], [160, 948], [318, 948], [482, 948], [642, 948], [804, 948], [966,948], [1127, 948], [1289, 948], [1451, 948], [1613, 948],[1775, 948]]
        
        # Note : all positions are for 1920/1080. We will have to resize
        self.ratioX = self.display.res['x'] / 1920
        self.ratioY = self.display.res['y'] / 1080
        
        #  Get the options
        self.max_round = int(options['max_round'])
        self.master = options['master']
        self.inter = options['inter']
        self.grid = []
        
        # For rpi
        self.rpi = rpi

        self.winner = None
        self.infos = ''
        self.translate = self.display.lang.translate
        self.show_hit = True
        
        self.pos_player = 0     #### position joueur
        self.hit_player = 0     #### hit que joueurdoit toucher
        
    def advance(self, player, spaces): # player can move
        initPos = self.positions[player]
        self.positions[player] += spaces

        
    def pre_dart_check(self,  players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """

        self.show_hit = False # Don't show hit segment
        return_code = 0
        # infos Can be used to create a per-player debug output
        self.infos += f"###### Player {actual_player} ######{self.lf}"
        
        
        # Extra before the very first dart : initiate positions on board and assign colors to players
        if player_launch == 1 and actual_round == 1 and actual_player == 0 :
            self.display.display_background('horse/background')
            i = 0
            for p in players:
                self.positions.update({p.name : 0})
                p.color = self.colors[i]
                i += 1
                
            """
            create grid
            """
            self.grid.clear()
            if not self.master :
                hits = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
                random.shuffle(hits)
            else : 
                hits = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'S11', 'S12', 'S13', 'S14', 'S15', 'S16', 'S17', 'S18', 'S19', 'S20', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12', 'T13', 'T14', 'T15', 'T16', 'T17', 'T18', 'T19', 'T20', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12', 'D13', 'D14', 'D15', 'D16', 'D17', 'D18', 'D19', 'D20']            
                random.shuffle(hits)
                
            for i in range (0, 10) :
                h = random.randint(0, len(hits) - 1)    
                if not self.inter and not self.master :
                        if i == 3  :
                            self.grid.append(('D'+str(hits[h]), self.coords[i][0], i)) 
                            hits.pop(h)
                        elif i == 7 :
                            self.grid.append(('T'+str(hits[h]), self.coords[i][0], i))  
                            hits.pop(h)    
                        else :
                            self.grid.append(('S'+str(hits[h]), self.coords[i][0], i))  
                            hits.pop(h)
                                
                elif self.inter :
                        if i == 2 :
                            self.grid.append(('D'+str(hits[h]), self.coords[i][0], i)) 
                            hits.pop(h)
                        elif i == 6  :
                            self.grid.append(('D'+str(hits[h]), self.coords[i][0], i))  
                            hits.pop(h)  
                        elif i == 4 :
                            self.grid.append(('T'+str(hits[h]), self.coords[i][0], i)) 
                            hits.pop(h) 
                        elif i == 8 :
                            self.grid.append(('T'+str(hits[h]), self.coords[i][0], i)) 
                            hits.pop(h)     
                        else :
                            self.grid.append(('S'+str(hits[h]), self.coords[i][0], i))  
                            hits.pop(h)
                
                elif self.master :
                        self.grid.append((hits[h], self.coords[i][0], i)) 
                        hits.pop(h)
    
                
            self.grid.append((25, 0))   ### ajout pour le bull


        # You will probably save the turn to be used in case of backup turn (each first launch) :
        if player_launch == 1:
            self.save_turn(players)
            # Clean actual_players' columns
            i = 0
            for column in players[actual_player].columns:
                players[actual_player].columns[i] = ['', 'txt']
                i += 1

        if players[actual_player].ident == 0 :
            color = 0
        elif players[actual_player].ident == 1 :
            color = 1
        elif players[actual_player].ident == 2 :
            color = 2
        elif players[actual_player].ident == 3 :
            color = 3
        elif players[actual_player].ident == 4 :
            color = 4
                   
        # Turn leds on
        if self.positions[players[actual_player].name] == 0 :
            leds = self.grid[0][0]
        elif self.positions[players[actual_player].name] == 1 :
            leds = self.grid[1][0]
        elif self.positions[players[actual_player].name] == 2 :
            leds = self.grid[2][0]          
        elif self.positions[players[actual_player].name] == 3 :
            leds = self.grid[3][0]      
        elif self.positions[players[actual_player].name] == 4 :
            leds = self.grid[4][0]      
        elif self.positions[players[actual_player].name] == 5 :
            leds = self.grid[5][0]                        
        elif self.positions[players[actual_player].name] == 6 :
            leds = self.grid[6][0]  
        elif self.positions[players[actual_player].name] == 7 :
            leds = self.grid[7][0]             
        elif self.positions[players[actual_player].name] == 8 :
            leds = self.grid[8][0] 
        elif self.positions[players[actual_player].name] == 9 :
            leds = self.grid[9][0]     
        elif self.positions[players[actual_player].name] == 10 :
            leds = f'SB#{self.colors[0]}|DB#{self.colors[0]}'
            #leds = f'SB#{players[actual_player].color}|DB#{players[actual_player].color}'       
        
        self.rpi.set_target_leds(f'{leds}#{self.colors[color]}')  
        #self.rpi.set_target_leds(f'{leds}#{players[actual_player].color}')  
        
        # Backuping scores
        self.save_turn(players)
        # Send debug output to log system. Use DEBUG or WARNING or ERROR or FATAL
        self.logs.debug(self.infos)
         
        return return_code

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Function run after each dart throw - for example, add points to player
        """
        
        handler = self.init_handler()

        return_code = 0
        
        if player_launch == self.nb_darts and actual_round >= self.max_round and actual_player == len(players)-1 :
            return_code = 2

        self.pos_player = int(self.positions[players[actual_player].name])
        self.hit_player = self.grid[self.pos_player][0]

        arrivee = False
        if self.pos_player == 10 :
            arrivee = True
       
        ### touche le segment
        if int(self.positions[players[actual_player].name]) == self.pos_player and (hit == 'SB' or hit == 'DB') and arrivee :
            self.totalTurn = 1  
            self.advance(players[actual_player].name, self.totalTurn)
            #self.display.play_sound('horse_galop')   
            handler['sound'] = 'horse_galop'
            #self.display.play_sound('horse_hennissement')  
            handler['sound'] = 'horse_hennissement'
        elif int(self.positions[players[actual_player].name]) == self.pos_player and hit == self.hit_player and not arrivee :
            self.totalTurn = 1
            self.advance(players[actual_player].name, self.totalTurn)
            #self.display.play_sound('horse_galop')
            handler['sound'] = 'horse_galop'  
        else :
            self.dartScore = 0
            #self.display.play_sound('horse_hennissement')  
            handler['sound'] = 'horse_hennissement'
            print('pas touche')    
                        
        # increment total
        self.totalTurn += self.dartScore
           
        # Victory for current player
        if self.positions[players[actual_player].name] == 11 :
            #self.video_player.play_video(self.display.file_class.get_full_filename('horse/victoire', 'videos'))
            handler['video'] = 'horse/victoire'
            #self.display.play_sound('horse_hennissement')  
            handler['sound'] = 'horse_hennissement'
            self.winner = players[actual_player].ident
            self.totalTurn = 0
            return_code = 3

        # You may want to count how many touches
        # Simple = 1 touch, Double = 2 touches, Triple = 3 touches
        players[actual_player].increment_hits(hit)

        # You may want to count darts played
        players[actual_player].darts_thrown += 1

        # It is recommanded to update stats every dart thrown
        self.refresh_stats(players, actual_round)

        # Time for shot or video ?
        handler['take_shot'] = self.time_to_take_shot_or_video(hit)
        handler['return_code'] = return_code
        return handler
        
    def refresh_game_screen(self, Players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player,TxtOnLogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
       
        ClickZones={}
        # Clear screen
        # self.display.screen.fill((0,0,0))
        
        # Background image
        if not self.master and not self.inter :
            self.display.display_background('horse/background')
        elif self.inter :
            self.display.display_background('horse/background_inter')    
        else :
            self.display.display_background('horse/background_master')  

        self.display.blit_text(str(self.grid[0][0]), int((self.display.res['x']*(160) /1920)), int((self.display.res['y']* self.chiffreY /1920)) , self.scale, self.scale, color=(0,0,0), align='center', valign='center', margin=False)
        self.display.blit_text(str(self.grid[1][0]), int((self.display.res['x']*(318) /1920)), int((self.display.res['y']* self.chiffreY /1920)) , self.scale, self.scale, color=(0,0,0), align='center', valign='center', margin=False)
        self.display.blit_text(str(self.grid[2][0]), int((self.display.res['x']*(482) /1920)), int((self.display.res['y']* self.chiffreY /1920)) , self.scale, self.scale, color=(0,0,0), align='center', valign='center', margin=False)
        self.display.blit_text(str(self.grid[3][0]), int((self.display.res['x']*(642) /1920)), int((self.display.res['y']* self.chiffreY /1920)) , self.scale, self.scale, color=(0,0,0), align='center', valign='center', margin=False)
        self.display.blit_text(str(self.grid[4][0]), int((self.display.res['x']*(804) /1920)), int((self.display.res['y']* self.chiffreY /1920)) , self.scale, self.scale, color=(0,0,0), align='center', valign='center', margin=False)
        self.display.blit_text(str(self.grid[5][0]), int((self.display.res['x']*(966) /1920)), int((self.display.res['y']* self.chiffreY /1920)) , self.scale, self.scale, color=(0,0,0), align='center', valign='center', margin=False)
        self.display.blit_text(str(self.grid[6][0]), int((self.display.res['x']*(1127) /1920)), int((self.display.res['y']* self.chiffreY /1920)) , self.scale, self.scale, color=(0,0,0), align='center', valign='center', margin=False)
        self.display.blit_text(str(self.grid[7][0]), int((self.display.res['x']*(1289) /1920)), int((self.display.res['y']* self.chiffreY /1920)) , self.scale, self.scale, color=(0,0,0), align='center', valign='center', margin=False)
        self.display.blit_text(str(self.grid[8][0]), int((self.display.res['x']*(1451) /1920)), int((self.display.res['y']* self.chiffreY /1920)) , self.scale, self.scale, color=(0,0,0), align='center', valign='center', margin=False)
        self.display.blit_text(str(self.grid[9][0]), int((self.display.res['x']*(1613) /1920)), int((self.display.res['y']* self.chiffreY /1920)) , self.scale, self.scale, color=(0,0,0), align='center', valign='center', margin=False)
      
        ### determine la couleur des chiffres a jouer
        if Players[actual_player].ident == 0 :
                couleur = (0,255,0)
        elif Players[actual_player].ident == 1 :
                couleur = (0,0,255)
        elif Players[actual_player].ident == 2 :
                couleur = (255,0,0)   
        elif Players[actual_player].ident == 3 :
                couleur = (255,255,0)    
        elif Players[actual_player].ident == 4 :
                couleur = (255,0,255) 
         
   
        ### positionne le chiffre a jouer selon la couleur du joueur        
        if self.positions[Players[actual_player].name] <= 9 :
            if self.positions[Players[actual_player].name] == self.grid[self.positions[Players[actual_player].name]][2] :
                self.display.blit_text(str(self.grid[self.positions[Players[actual_player].name]][0]), int((self.display.res['x']*(self.coords[self.positions[Players[actual_player].name]+1][0]) /1920)), int((self.display.res['y']* self.chiffreY /1920)) , self.scale, self.scale, color=(couleur), align='center', valign='center', margin=False)
      
        ### deplacement joueurs
        for p in Players:
            if self.positions[p.name] != 0 : # Deplacement joeuur
                 if p.ident == 0 :
                     self.display.display_image(self.display.file_class.get_full_filename('horse/horse_j1', 'images'), (self.coords[self.positions[p.name]][0]) * self.ratioX, (self.coords[self.positions[p.name]][1]) * self.ratioY , self.scale, self.scale, True)
                 elif p.ident == 1 :
                     self.display.display_image(self.display.file_class.get_full_filename('horse/horse_j2', 'images'), (self.coords1[self.positions[p.name]][0]) * self.ratioX , (self.coords1[self.positions[p.name]][1]) * self.ratioY , self.scale, self.scale, True)
                 elif p.ident == 2 :
                     self.display.display_image(self.display.file_class.get_full_filename('horse/horse_j3', 'images'), (self.coords2[self.positions[p.name]][0]) * self.ratioX , (self.coords2[self.positions[p.name]][1]) * self.ratioY , self.scale, self.scale, True)
                 elif p.ident == 3 :
                     self.display.display_image(self.display.file_class.get_full_filename('horse/horse_j4', 'images'), (self.coords3[self.positions[p.name]][0]) * self.ratioX , (self.coords3[self.positions[p.name]][1]) * self.ratioY , self.scale, self.scale, True)

            else : # Position de depart
                 if p.color == 'green':
                     self.display.display_image(self.display.file_class.get_full_filename('horse/horse_j1', 'images'), 1 * self.ratioX, 504 * self.ratioY, self.scale, self.scale, True)
                 elif p.color == 'blue':
                     self.display.display_image(self.display.file_class.get_full_filename('horse/horse_j2', 'images'), 1 * self.ratioX , 655 * self.ratioY, self.scale, self.scale, True)
                 elif p.color == 'red':
                     self.display.display_image(self.display.file_class.get_full_filename('horse/horse_j3', 'images'), 1 * self.ratioX , 805 * self.ratioY, self.scale, self.scale, True)
                 else :
                     self.display.display_image(self.display.file_class.get_full_filename('horse/horse_j4', 'images'), 1 * self.ratioX , 950 * self.ratioY, self.scale, self.scale, True)

        # Show players names
        self.display_player_name(self.display,30, 0, actual_player, Players[0])
        if len(Players)>1 :
            self.display_player_name(self.display,30 + self.display.pn_size + self.display.margin, 0, actual_player, Players[1])
        if len(Players)>2 :
            self.display_player_name(self.display,30 + 2*(self.display.pn_size + self.display.margin), 0, actual_player, Players[2])
        if len(Players)>3 :
            self.display_player_name(self.display,30 + 3*(self.display.pn_size + self.display.margin), 0, actual_player, Players[3])
            
        # Show round number   
        right_x = int(self.display.res['x'] * 13 / 16)
        right_y = 20
        right_width = int(self.display.res['x'] * 3 / 16)
        right_height = int(self.display.res['y'] / 16)

        self.display.blit_text(f"Round", right_x, right_y, int(right_width / 3), right_height, color=(246, 85, 41), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{actual_round} / {max_round}", right_x + int(right_width / 2), 0, self.display.res['x'] - right_x - int(right_width / 2), right_height * 2, color=(246, 85, 41), align='Right', valign='top', margin=False)
        
        # Refresh screen
        if end_of_game :
            ClickZones = self.display.end_of_game_menu(logo, stat_button=False)

        self.display.update_screen()

        return [ClickZones]

    def refresh_stats(self, players, actual_round):
        """
        Method to refresh player.stat - Adapt to the stats you want.
        They represent mathematical formulas used to calculate stats. Refreshed after every launch
        """
        for player in players:
            player.stats['Score Per Round'] = player.score_per_round(actual_round)
            
    def display_player_name(self, display, pos_x, pos_y, actual_player, player):
        playername = player.name
        if playername is None:
            playername = f'horse {player.ident}'
            
        txtcolor = player.color
        
        scaled = self.display.scale_text(playername, self.display.pn_size - 2 * self.display.margin, self.display.line_height)
        font = self.display.get_font(scaled[0])

        background_color = (150,150,150,100)
        if player.ident == actual_player :
            background_color = (245, 245, 245)
        self.display.blit_rect(pos_x, pos_y, self.display.pn_size - self.display.margin, self.display.line_height - self.display.margin, background_color)

        playername_x = pos_x + self.display.margin * 2 + scaled[1]
        playername_y = pos_y + scaled[2]
        text = font.render(playername, True, txtcolor)
        self.display.screen.blit(text, [playername_x, playername_y])

    def display_segment(self):
        """
        Display or not the hit segment
        """
        return self.show_hit
        
    def early_player_button(self, players, actual_player, actual_round):
        """
        Run when player push PLAYERBUTTON before last dart
        return code :
            1. Next player
            2. Last round reach
            3. Winner is
        """
        return_code = 1

        if self.positions[players[actual_player].name] == 11 :
            self.video_player.play_video(self.display.file_class.get_full_filename('horse/victoire', 'videos'))
            self.winner = players[actual_player].ident
            return_code = 3
        
        if actual_round == int(self.max_round) and actual_player == self.nb_players - 1:
            return_code = 2
        return return_code
        
    def miss_button(self, players, actual_player, actual_round, player_launch):
        """
        EMPTY
        """
        players[actual_player].columns[player_launch+1] = ('MISS', 'str')
        self.display.play_sound('miss')
        players[actual_player].darts_thrown += 1    
        pass

    def pnj_score(self, players, actual_player, computer_level, player_launch):
        """
        Intelligence Artificielle (PNJ) pour le jeu Horse :
        - Vise la cible de la position actuelle sur la piste (Single, Double, Triple ou Bull pour l'arrivée).
        - Gère les probabilités de réussite exacte, de déviation sur les voisins physiques et de raté complet.
        """
        # =========================================================================
        # GUIDE DE RÉGLAGE DES NIVEAUX DE DIFFICULTÉ :
        # - Légende du format par niveau [p_exact, p_neighbor, p_miss] :
        #   * p_exact    : Probabilité de toucher la cible exacte (%)
        #   * p_neighbor : Probabilité de toucher un segment voisin géométrique (%)
        #   * p_miss     : Probabilité de rater complètement (chiffre aléatoire) (%)
        # - Cas particulier : Position 10 (Arrivée / Bull) avec gestion spécifique du Double Bull (DB) et Single Bull (SB).
        # - Ajustement : Pour renforcer l'IA, augmente p_exact et réduis p_miss.
        # =========================================================================

        current_player = players[actual_player]
        pos = getattr(self, 'positions', {}).get(current_player.name, 0)

        if pos >= 11:
            return 'S1'

        # Niveaux de difficulté : [Chance cible exacte, Chance voisin, Chance raté/miss]
        levels = [
            [20, 50, 30],  # Niveau 1 : Noob (20% exact, 50% voisin, 30% miss)
            [35, 45, 20],  # Niveau 2 : Débutant (35% exact, 45% voisin, 20% miss)
            [45, 35, 10],  # Niveau 3 : Intermédiaire (45% exact, 35% voisin, 10% miss)
            [75, 20,  5],  # Niveau 4 : Pro (75% exact, 20% voisin, 5% miss)
            [90, 10,  0]   # Niveau 5 : Expert (90% exact, 10% voisin, 0% miss)
        ]

        try:
            comp_lvl = int(computer_level)
        except (ValueError, TypeError):
            comp_lvl = 3

        lvl_idx = max(0, min(comp_lvl - 1, len(levels) - 1))
        p_exact = levels[lvl_idx][0]
        p_neighbor = levels[lvl_idx][1]

        dartboard_order = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]

        # Cas particulier : Position 10 (Ligne d'arrivée / Bull)
        if pos == 10:
            rand_val = random.randrange(100)
            if rand_val < p_exact:
                return 'DB' if comp_lvl >= 3 and random.randrange(100) < 50 else 'SB'
            elif rand_val < p_exact + p_neighbor:
                return 'SB'
            else:
                return f"S{random.choice([1, 20])}"

        # Position normale (0 à 9)
        grid_data = getattr(self, 'grid', {})
        target_str = str(grid_data[pos][0]) if pos in grid_data and grid_data[pos] else '20'
        
        if target_str.startswith('S') or target_str.startswith('D') or target_str.startswith('T'):
            multi = target_str[0]
            try:
                num = int(target_str[1:])
            except ValueError:
                num = 20
        else:
            try:
                num = int(target_str)
                multi = 'S'
            except ValueError:
                num = 20
                multi = 'S'

        rand_val = random.randrange(100)

        # 1. Touche la cible exacte
        if rand_val < p_exact:
            return f"{multi}{num}"

        # 2. Touche un voisin (raté partiel)
        elif rand_val < p_exact + p_neighbor:
            if num in dartboard_order:
                idx = dartboard_order.index(num)
                left_neighbor = dartboard_order[(idx - 1) % len(dartboard_order)]
                right_neighbor = dartboard_order[(idx + 1) % len(dartboard_order)]
                neighbor_num = random.choice([left_neighbor, right_neighbor])
            else:
                neighbor_num = random.randint(1, 20)
            
            neighbor_multi = multi if random.randrange(100) < 30 else 'S'
            return f"{neighbor_multi}{neighbor_num}"

        # 3. Raté complet (Miss / Chiffre aléatoire)
        else:
            miss_num = random.randint(1, 20)
            return f"S{miss_num}"
