# -*- coding: utf-8 -*-
"""
Game by ... @fragarch!
"""

from include import cplayer
from include import cgame
import random

GAME_LOGO = 'GameOfGoose.png'
HEADERS = "D1","D2","","","","","CASE" 
OPTIONS = {'theme': 'default' , 'max_round': 20, 'level': 1 , 'master': False, 'tour': False, 'alea': False} 
NB_DARTS = 2
GAME_RECORDS = {'Score Per Round': 'DESC', 'Dribbles': 'DESC'}
VERSION = '1.00'

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
        
        self.token = 'tbd'
        self.color = 'tbd'

        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record]='0'

class Game(cgame.Game):
    """
    Goose game class
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
        
        self.tour = options['tour']
        
        # Generic but copied as reminder
        self.colors = ['green', 'red', 'blue', 'gold', 'silver']
        
        # Game of Goose specific
        self.positions = {}                                     # to store positions of players
        self.totalTurn = 0                                      # to store total of dice
        self.firstDart = 0                                      # to store score of first dart
        self.secondDart = 0                                     # to store score of second dart
        
        if self.tour:
            self.hotel = {'Resident' : '', 'RemainingTurns' : 0}    # to manage players stuck in hotel
            self.well = {'Resident' : '', 'RemainingTurns' : 0}     # to manage players fallen in the well
            self.prison = {'Resident' : '', 'RemainingTurns' : 0}   # to manage players stuck in prison
        else:
            self.hotel = {'Resident' : '', 'RemainingTurns' : 0}    # to manage players stuck in hotel
            self.well = {'Victim' : ''}                             # to manage players fallen in the well
            self.prison = {'Prisoner' : 'Nobody'}                   # to manage players stuck in prison
            
        self.tokens = ['goose_greenCircle', 'goose_redCircle', 'goose_blueCircle', 'goose_yellowCircle'] # Player Tokens
        self.onlyOneDart = False
        self.twoDartsThrown = False
        self.dartScore = 0

        
        self.scale = self.display.res['x'] * 95 / 1920          # Adapt token to screen
        self.scale = self.scale / 1.6                           # Change size
        
        # Coordinates of spaces on board
        self.coords = [[165, 813], [510, 813], [620, 813], [740, 813], [870, 813], [990, 813], [0,0], [1230, 813], [1340, 810], [1455, 805], [1590, 750],
        [1661, 694], [1696, 626], [1777, 570], [1767, 488], [1750, 414], [1707, 342], [1602, 287], [1469, 222], [1349, 197], [1226, 197],
        [1102, 197], [977, 197], [ 860, 197], [740, 197], [609, 197], [482, 197], [370, 216], [281, 249], [225, 297], [133, 353],
        [98, 432], [93, 507], [125, 592], [189, 659], [289, 700], [401, 719], [501, 719], [619, 719], [738, 719], [863, 719],
        [981, 719], [1112, 719], [1233, 719], [1349, 713], [1453, 611], [1569, 609], [1611, 542], [1615, 472], [1563, 410], [1455, 331],
        [1316, 301], [1190, 280], [1103, 301], [970, 301], [846, 301], [732, 301], [607, 301], [0, 0], [349, 360], [289, 457],
        [314, 557], [426, 603], [597, 613]]
        
        # Note : all positions are for 1920/1080. We will have to resize
        self.ratioX = self.display.res['x'] / 1920
        self.ratioY = self.display.res['y'] / 1080
        
        #  Get the options
        self.max_round = int(options['max_round'])
        self.master = options['master']
        self.difficulty = int(options['level'])
        
        # More fun, more videos
        self.videos = {'6' : 'gooseBridge', '19' : 'gooseHotel', '31' : 'gooseWell', '42' : 'gooseMaze', '52' : 'goosePrison', '58' : 'gooseDeath', 'square' : 'gooseSquare', 'boost' : 'gooseBoost', 'victory' : 'gooseFinishLine', 'advance' : 'gooseAdv'}

        # For rpi
        self.rpi = rpi

        self.winner = None
        self.infos = ''
        self.translate = self.display.lang.translate
        self.show_hit = True
        
        self.alea = options['alea']
   
   
    def pnj_score(self, players, actual_player, computerLevel, player_launch):
        '''
        IA pour le Jeu de l'Oie : cherche à atteindre les segments cibles autorisés (1 à 6 selon la difficulté) 
        tout en gérant le taux de raté (miss) et le glissement de la matrice physique.
        '''
        # =========================================================================
        # GUIDE DE RÉGLAGE DES NIVEAUX DE DIFFICULTÉ :
        # - Légende des niveaux : [miss_rate, slip_rate]
        #   * miss_rate : Probabilité d'un raté pur (MISSDART, score à 0) (%)
        #   * slip_rate : Probabilité de déviation/glissement vers un voisin géographique si non raté (%)
        # - Plus fort / précis : Diminuer miss_rate et slip_rate.
        # - Plus humain / brouillon : Augmenter miss_rate et slip_rate.
        # =========================================================================
        
        geo_neighbors = {
            1: [20, 18, 4], 2: [17, 15, 10], 3: [19, 17, 2], 4: [18, 13, 1], 
            5: [20, 12, 9], 6: [10, 13, 15], 7: [19, 16, 8], 8: [16, 11, 7], 
            9: [14, 12, 5], 10: [15, 6, 2], 11: [14, 8, 16], 12: [9, 5, 20], 
            13: [6, 4, 11], 14: [9, 11, 16], 15: [10, 2, 6], 16: [7, 8, 11], 
            17: [2, 3, 15], 18: [4, 1, 20], 19: [7, 3, 2], 20: [1, 5, 12]
        }

        # Niveaux de difficulté [Taux de raté (miss), Taux de glissement (slip)]
        levels = [
                 [45, 80],  # Niveau 1 : Noob
                 [30, 70],  # Niveau 2 : Débutant
                 [15, 40],  # Niveau 3 : Intermédiaire
                 [6, 25],   # Niveau 4 : Pro
                 [2, 8]     # Niveau 5 : Expert
                ]

        lvl_idx = max(0, min(computerLevel - 1, len(levels) - 1))
        miss_rate = levels[lvl_idx][0]
        slip_rate = levels[lvl_idx][1]

        # 1. Test du MISS pur : On retourne 'MISSDART' pour indiquer le raté
        if random.randrange(100) < miss_rate:
            if player_launch == 1:
                self.onlyOneDart = True
            else:
                self.twoDartsThrown = True
            self.dartScore = 0
            players[actual_player].darts_thrown += 1
            self.display.play_sound('miss')
            return 'MISSDART'

        # Stratégie Jeu de l'Oie : viser en priorité les segments de 1 à 6 autorisés par les règles
        allowed_targets = [1, 2, 3, 4, 5, 6]
        target_num = random.choice(allowed_targets)
        mult = 'S'

        # 2. Simulation de la déviation / glissement de la matrice physique
        if random.randrange(100) < slip_rate:
            if target_num in geo_neighbors:
                target_num = random.choice(geo_neighbors[target_num])
            mult = 'S'

        return f'{mult}{target_num}'
   
   
    
    def advance(self, player, spaces): # player can move
        self.video_player.play_video(self.display.file_class.get_full_filename('gameofgoose/' + self.videos['advance'], 'videos'))
        initPos = self.positions[player]
        self.positions[player] += spaces
        self.checkPos(player, initPos, self.positions[player])
        
    def specialFirstTurn(self, player, dart1, dart2):
		
        handler = self.init_handler()
        initPos = self.positions[player]
        #self.dmd.send_text("BOOST !")
        handler['dmd'] = ("BOOST !")
        
        self.video_player.play_video(self.display.file_class.get_full_filename('gameofgoose/' + self.videos['boost'], 'videos'))
        #handler['video'] = 'gameofgoose/' + self.videos['boost']
        
        if (dart1 == 6 and dart2 == 3) or (dart1 == 3 and dart2 == 6):
            self.positions[player] = 26
        if (dart1 == 5 and dart2 == 4) or (dart1 == 4 and dart2 == 5):
            self.positions[player] = 53
        self.checkPos(player, initPos, self.positions[player])
        
    def checkPos(self, player, startPosition, newPosition): # define events based on new position
        # Square 63+ : We go back
        handler = self.init_handler()
                
        if newPosition > 63:
            backwards = newPosition - 63
            newPosition = 63 - backwards
            self.positions[player] = newPosition
            self.checkPos(player, startPosition, newPosition) # to avoid special cases
        # Square 6 : The bridge - Shortcut to 12
        if newPosition == 6:
            self.video_player.play_video(self.display.file_class.get_full_filename('gameofgoose/' + self.videos['6'], 'videos'))
            #handler['video'] = 'gameofgoose/' + self.videos['6']
            newPosition = 12
            self.positions[player] = newPosition
        # Square 42 : The maze - Lost, go back to 30
        if newPosition == 42:
            self.video_player.play_video(self.display.file_class.get_full_filename('gameofgoose/' + self.videos['42'], 'videos'))
            #handler['video'] = 'gameofgoose/' + self.videos['42']
            newPosition = 30
            self.positions[player] = newPosition
        # Goose square : advance again of same amount of spaces
        if newPosition in [9, 18, 27, 36, 45, 54] and startPosition % 9 != 0 : # avoid scenario Death > Start > Goose > Loop
            self.video_player.play_video(self.display.file_class.get_full_filename('gameofgoose/' + self.videos['square'], 'videos'))
            #handler['video'] = 'gameofgoose/' + self.videos['square']
            spaces = newPosition - startPosition
            newPosition += spaces
            self.positions[player] = newPosition
            self.checkPos(player, startPosition, newPosition) # to avoid special cases
        if self.tour:
            # Square 19 : The hotel - wait 2 turns there
            if newPosition == 19:
                #self.dmd.send_text("A L'HOTEL !")
                handler['dmd'] = ("A L'HOTEL !")
                
                self.video_player.play_video(self.display.file_class.get_full_filename('gameofgoose/' + self.videos['19'], 'videos'))
                #handler['video'] = 'gameofgoose/' + self.videos['19']
                self.hotel['Resident'] = player
                self.hotel['RemainingTurns'] = 2
            # Square 31 : The well : wait until someone takes you out
            if newPosition == 31:
                #self.dmd.send_text("LE PUITS !")
                handler['dmd'] = ("LE PUITS !")
                
                self.video_player.play_video(self.display.file_class.get_full_filename('gameofgoose/' + self.videos['31'], 'videos'))
                #handler['video'] = 'gameofgoose/' + self.videos['31']
                self.well['Resident'] = player
                self.well['RemainingTurns'] = 2
            # Check if a player was already present on the new position. If yes, switch positions
            for pl, pos in self.positions.items():
                if pl != player and pos == newPosition and newPosition != 52:
                    self.positions[pl] = startPosition
            # Square 52 : The prison - wait someone visits you
            if newPosition == 52:
                #if self.prison['Prisoner'] == 'Nobody':
                self.video_player.play_video(self.display.file_class.get_full_filename('gameofgoose/' + self.videos['52'], 'videos'))
                #handler['video'] = 'gameofgoose/' + self.videos['52']
                #self.dmd.send_text("EN PRISON !")
                handler['dmd'] = ("EN PRISON !")
                
                self.prison['Resident'] = player
                self.prison['RemainingTurns'] = 2
               # else:
               #     self.prison['Prisoner'] = 'Nobody'
        else:
            # Square 19 : The hotel - wait 2 turns there
            if newPosition == 19:
                #self.dmd.send_text("A L'HOTEL !")
                handler['dmd'] = ("A L'HOTEL !")
                
                self.video_player.play_video(self.display.file_class.get_full_filename('gameofgoose/' + self.videos['19'], 'videos'))
                #handler['video'] = 'gameofgoose/' + self.videos['19']
                self.hotel['Resident'] = player
                self.hotel['RemainingTurns'] = 2
            # Square 31 : The well : wait until someone takes you out
            if newPosition == 31:
                #self.dmd.send_text("LE PUITS !")
                handler['dmd'] = ("LE PUITS !")
                
                self.video_player.play_video(self.display.file_class.get_full_filename('gameofgoose/' + self.videos['31'], 'videos'))
                #handler['video'] = 'gameofgoose/' + self.videos['31']
                self.well['Victim'] = player
            # Check if a player was already present on the new position. If yes, switch positions
            for pl, pos in self.positions.items():
                if pl != player and pos == newPosition and newPosition != 52:
                    self.positions[pl] = startPosition
            # Square 52 : The prison - wait someone visits you
            if newPosition == 52:
                if self.prison['Prisoner'] == 'Nobody':
                    self.video_player.play_video(self.display.file_class.get_full_filename('gameofgoose/' + self.videos['52'], 'videos'))
                    #handler['video'] = 'gameofgoose/' + self.videos['52']
                    
                    
                    #self.dmd.send_text("EN PRISON !")
                    handler['dmd'] = ("EN PRISON !")
                    
                    self.prison['Prisoner'] = player
                else:
                    self.prison['Prisoner'] = 'Nobody'
            
            
        return handler            
            
            
        # Square 58 : Death - Go back to start
        if newPosition == 58:
            self.video_player.play_video(self.display.file_class.get_full_filename('gameofgoose/' + self.videos['58'], 'videos'))
            #handler['video'] = 'gameofgoose/' + self.videos['58']
            #self.dmd.send_text("MORT !")
            handler['dmd'] = ("A L'HOTEL !")
            
            newPosition = 0
            self.positions[player] = newPosition

    def pre_dart_check(self,  players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """

        handler = self.init_handler()

        self.show_hit = False # Don't show hit segment
        return_code = 0
        # infos Can be used to create a per-player debug output
        self.infos += f"###### Player {actual_player} ######{self.lf}"
        
        
        # Extra before the very first dart : initiate positions on board and assign colors to players
        if player_launch == 1 and actual_round == 1 and actual_player == 0:
            self.display.display_background('gooseBoard')
            i = 0
            for p in players:
                self.positions.update({p.name : 0})
                p.token = self.tokens[i]
                p.color = self.colors[i]
                i += 1
        
        if self.tour:
            # We check the hotel to skip turn
            if player_launch == 1 and self.hotel['Resident'] == players[actual_player].name and self.hotel['RemainingTurns'] > 0  and len(players) > 1:
                self.hotel['RemainingTurns'] -=1 # One turn less to wait
                tour2 = str(self.hotel['RemainingTurns']+1)
                tour = ' '.join(tour2)
                joueur = players[actual_player].name 
    
                #tour -= 1 
                # Video
                ###self.display.message([
                handler['message'] = ([f"{joueur} : {self.translate('GameofGoose-hotel')} {tour} {self.translate('GameofGoose-hotel2')}"], 2000, None, 'middle', 'big')
                return_code = 4 # Go to next player
                
            # We check the well to skip turn
            if player_launch == 1 and self.well['Resident'] == players[actual_player].name and self.well['RemainingTurns'] > 0  and len(players) > 1:
                self.well['RemainingTurns'] -=1
                tour2 = str(self.well['RemainingTurns']+1)
                tour = ' '.join(tour2)
                joueur = players[actual_player].name 
                
                # Video
                #self.display.message
                handler['message'] =([f"{joueur} : {self.translate('GameofGoose-well')} {tour} {self.translate('GameofGoose-well2')}"], 2000, None, 'middle', 'big')
                return_code = 4 # Go to next player
                
             # We check the prison to skip turn
            if player_launch == 1 and self.prison['Resident'] == players[actual_player].name and self.prison['RemainingTurns'] > 0  and len(players) > 1 :
                self.prison['RemainingTurns'] -= 1
                tour2 = str(self.prison['RemainingTurns']+1)
                tour = ' '.join(tour2)
                joueur = players[actual_player].name 
                # Video
                ##self.display.message
                handler['message'] =([f"{joueur} : {self.translate('GameofGoose-prison')} {tour} {self.translate('GameofGoose-prison2')}"], 2000, None, 'middle', 'big')
                return_code = 4 # Go to next player           
        else:
            # We check the hotel to skip turn
            if player_launch == 1 and self.hotel['Resident'] == players[actual_player].name and self.hotel['RemainingTurns'] > 0  and len(players) > 1:
                self.hotel['RemainingTurns'] -=1 # One turn less to wait
                # Video
                return_code = 4 # Go to next player
                
            # We check the well to skip turn
            if player_launch == 1 and self.well['Victim'] == players[actual_player].name and len(players) > 1:
                # Video
                return_code = 4 # Go to next player
                
             # We check the prison to skip turn
            if player_launch == 1 and self.prison['Prisoner'] == players[actual_player].name and len(players) > 1:
                # Video
                return_code = 4 # Go to next player            
        # Set total to 0 beginning of turn    
        if player_launch == 1:
            self.totalTurn = 0
            self.dartScore = 0
            self.onlyOneDart = False
            self.twoDartsThrown = False
        
        # You will probably save the turn to be used in case of backup turn (each first launch):
        if player_launch == 1:
            self.save_turn(players)
            # Clean actual_players' columns
            i = 0
            for column in players[actual_player].columns:
                players[actual_player].columns[i] = ['', 'txt']
                i += 1
        
        # Level 1
        targ = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6']
        
        # Other levels
        if self.difficulty == 2:
            targ = targ[:6]
        elif self.difficulty == 3:
            targ = targ[6:12]
        elif self.difficulty == 4:
            targ = targ[12:] 
        else:
            self.difficulty = 1
        
        if not self.alea:
            # Turn leds on
            self.rpi.set_target_leds('|'.join([f'{key}#{self.colors[0]}' for key in targ]))
        elif self.alea:
            leds = '|'.join(f'S{number}#{self.colors[0]}|D{number}#{self.colors[0]}|T{number}#{self.colors[0]}' for number in range(1, 21))
            self.rpi.set_target_leds(leds)
        
        # Backuping scores
        self.save_turn(players)
        # Send debug output to log system. Use DEBUG or WARNING or ERROR or FATAL
        self.logs.debug(self.infos)
         
        handler['return_code'] = return_code 
        return handler
        
        #return return_code

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Function run after each dart throw - for example, add points to player
        """
        
        handler = self.init_handler()

        return_code = 0
        
        if player_launch == self.nb_darts and actual_round >= self.max_round and actual_player == len(players)-1:
            return_code = 2

        # Level 1
        targ = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6']
        
        # Other levels
        if self.difficulty == 2:
            targ = targ[:6]
        elif self.difficulty == 3:
            targ = targ[6:12]
        elif self.difficulty == 4:
            targ = targ[12:] 
            
        if not self.alea:
            if hit in targ: # check if valid throw (one dart is one die)
                self.dartScore = int(hit[1:])
                self.display.play_sound('DiceRoll')
                handler['sound'] = 'DiceRoll'
                
            else:
                self.dartScore = 0
        if self.alea:
        ####### aleatoire
            if hit : # check if valid throw (one dart is one die)
                self.dartScore = random.randint(1, 6)
                #self.display.play_sound('DiceRoll') 
                handler['sound'] = 'DiceRoll'
        
        # increment total
        self.totalTurn += self.dartScore
        
        if player_launch == 1:
            self.firstDart = self.dartScore
            self.onlyOneDart = True
            self.twoDartsThrown = False
        else:
            self.secondDart = self.dartScore
            self.onlyOneDart = False
            self.twoDartsThrown = True
                
        if self.totalTurn == 9 and actual_round == 1:
            if not self.master:
                self.specialFirstTurn(players[actual_player].name, self.firstDart, self.secondDart)
            else:
                self.advance(players[actual_player].name, self.totalTurn + 1) # Master Mode false, no mega boost on turn, just a +1
        else:
            if self.twoDartsThrown:
                self.advance(players[actual_player].name, self.totalTurn)
                    
        # Victory for current player
        if self.positions[players[actual_player].name] == 63:
            self.video_player.play_video(self.display.file_class.get_full_filename('gameofgoose/' + self.videos['victory'], 'videos'))
            #handler['video'] = 'gameofgoose/' + self.videos['victory']
            self.winner = players[actual_player].ident
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

        # Return code to main
        #return return_code
        
    def refresh_game_screen(self, Players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player,TxtOnLogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
       
        ClickZones={}
        # Clear screen
        # self.display.screen.fill((0,0,0))
        
        # Background image
        self.display.display_background('gooseBoard')
        
        # Place player tokens on board    
        a = 0
        for p in Players:
            if self.positions[p.name] != 0 and self.positions[p.name] != 52: # Normal squares
                self.display.display_image(self.display.file_class.get_full_filename(p.token, 'images'), (self.coords[self.positions[p.name]][0]) * self.ratioX, (self.coords[self.positions[p.name]][1]) * self.ratioY, self.scale, self.scale, True)
            elif self.positions[p.name] == 52 : # The prison - only one that can take 2 tokens
                
                self.display.display_image(self.display.file_class.get_full_filename(p.token, 'images'), (self.coords[self.positions[p.name]][0] + (7 * a)) * self.ratioX, (self.coords[self.positions[p.name]][1] + (7 * a)) * self.ratioY, self.scale, self.scale, True)
            else : # Startpositions
                if p.color == 'green':
                    self.display.display_image(self.display.file_class.get_full_filename('goose_greenCircle', 'images'), 165 * self.ratioX, 813 * self.ratioY, self.scale, self.scale, True)
                elif p.color == 'red':
                    self.display.display_image(self.display.file_class.get_full_filename('goose_redCircle', 'images'), (165 + self.scale + 5) * self.ratioX, 813 * self.ratioY, self.scale, self.scale, True)
                elif p.color == 'blue':
                    self.display.display_image(self.display.file_class.get_full_filename('goose_blueCircle', 'images'), (165 + (self.scale + 5)*2) * self.ratioX , 813 * self.ratioY, self.scale, self.scale, True)
                else:
                    self.display.display_image(self.display.file_class.get_full_filename('goose_yellowCircle', 'images'), (165 + (self.scale + 5)*3) * self.ratioX , 813 * self.ratioY, self.scale, self.scale, True)
            a += 2
            
        # Place dice to inform Players
        if not(self.onlyOneDart) and not(self.twoDartsThrown):
            self.display.display_image(self.display.file_class.get_full_filename('gooseDiceWaiting', 'images'), 740 * self.ratioX , 400 * self.ratioY, 180 * self.ratioX, 180 * self.ratioY, True)
            self.display.display_image(self.display.file_class.get_full_filename('gooseDiceWaiting', 'images'), 980 * self.ratioX , 400 * self.ratioY, 180 * self.ratioX, 180 * self.ratioY, True)
        
        if self.onlyOneDart:
            self.display.display_image(self.display.file_class.get_full_filename('gooseDice' + str(self.firstDart), 'images'), 740 * self.ratioX , 400 * self.ratioY, 180 * self.ratioX, 180 * self.ratioY, True)
            self.display.display_image(self.display.file_class.get_full_filename('gooseDiceWaiting', 'images'), 980 * self.ratioX , 400 * self.ratioY, 180 * self.ratioX, 180 * self.ratioY, True)
            
        if self.twoDartsThrown:
            self.display.display_image(self.display.file_class.get_full_filename('gooseDice' + str(self.firstDart), 'images'), 740 * self.ratioX , 400 * self.ratioY, 180 * self.ratioX, 180 * self.ratioY, True)
            self.display.display_image(self.display.file_class.get_full_filename('gooseDice' + str(self.secondDart), 'images'), 980 * self.ratioX , 400 * self.ratioY, 180 * self.ratioX, 180 * self.ratioY, True)
       
        # Show players names
        self.display_player_name(self.display,30, 0, actual_player, Players[0])
        if len(Players)>1:
            self.display_player_name(self.display,30 + self.display.pn_size + self.display.margin, 0, actual_player, Players[1])
        if len(Players)>2:
            self.display_player_name(self.display,30 + 2*(self.display.pn_size + self.display.margin), 0, actual_player, Players[2])
        if len(Players)>3:
            self.display_player_name(self.display,30 + 3*(self.display.pn_size + self.display.margin), 0, actual_player, Players[3])
            
        # Show round number   
        right_x = int(self.display.res['x'] * 13 / 16)
        right_y = 20
        right_width = int(self.display.res['x'] * 3 / 16)
        right_height = int(self.display.res['y'] / 16)

        self.display.blit_text(f"Round", right_x, right_y, int(right_width / 3), right_height, color=(246, 85, 41), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{actual_round} / {max_round}", right_x + int(right_width / 2), 0, self.display.res['x'] - right_x - int(right_width / 2), right_height * 2, color=(246, 85, 41), align='Right', valign='top', margin=False)
        
        # Show difficulty level
        self.display.display_image(self.display.file_class.get_full_filename('gooseLvl' + str(self.difficulty), 'images'), 1764 * self.ratioX, right_y + right_height - 20, 160 * self.ratioX, 380 * self.ratioY, True)
       
        # Refresh screen
        if end_of_game:
            ClickZones = self.display.end_of_game_menu(logo, stat_button=False)

        self.display.update_screen()

        return [ClickZones]

    def refresh_stats(self, players, actual_round):
        """
        Method to frefresh player.stat - Adapt to the stats you want.
        They represent mathematical formulas used to calculate stats. Refreshed after every launch
        """
        for player in players:
            player.stats['Score Per Round'] = player.score_per_round(actual_round)
            
   # Display name of the player if given, Player X otherwise
    def display_player_name(self, display, pos_x, pos_y, actual_player, player):
        playername = player.name
        if playername is None:
            playername = f'Oie {player.ident}'
            
        playername += ' (' + str(self.positions[player.name]) +')'

        if player.color == 'green':
            txtcolor = (0, 255, 0)  # green
        elif player.color == 'blue':
            txtcolor = (0, 0, 255)  # red
        elif player.color == 'red':
            txtcolor = (255, 0, 0) # blue
        else:
            txtcolor = (255, 255, 0) # gold
        #  Player name size depends of player name number of char (dynamic size)
        scaled = self.display.scale_text(playername, self.display.pn_size - 2 * self.display.margin, self.display.line_height)
        font = self.display.get_font(scaled[0])

        # display rect
        background_color = (150,150,150,100)
        if player.ident == actual_player:
            background_color = (245, 245, 245)
        self.display.blit_rect(pos_x, pos_y, self.display.pn_size - self.display.margin, self.display.line_height - self.display.margin, background_color)

        # Render the text. "True" means anti-aliased text.
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
        return code:
            1. Next player
            2. Last round reach
            3. Winner is
        """
        return_code = 1
        
        
        # Advance even if only one die
        self.advance(players[actual_player].name, self.totalTurn)
        
        # Victory for current player
        if self.positions[players[actual_player].name] == 63:
            self.video_player.play_video(self.display.file_class.get_full_filename('gameofgoose/' + self.videos['victory'], 'videos'))
            #handler['video'] = 'gameofgoose/' + self.videos['victory']
            self.winner = players[actual_player].ident
            return_code = 3
        
        if actual_round == int(self.max_round) and actual_player == self.nb_players - 1:
            self.logs.debug("At last round, default action is to return game over.")
            self.logs.debug("If it's not what you expect, raise a bug please.")
            # If its a early_player_button just at the last round - return GameOver
            return_code = 2
        return return_code
        
    def miss_button(self, players, actual_player, actual_round, player_launch):
        '''
        Miss button
        '''
        print('miss')
        if player_launch == 1 : 
            self.onlyOneDart = True
        elif player_launch == 2 :
            self.secondDart  = True
        self.dartScore = 0
        players[actual_player].darts_thrown += 1   
        self.display.play_sound('miss')     
        
 


