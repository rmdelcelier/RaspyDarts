# -*- coding: utf-8 -*-
"""
Game by ... LaDite
"""
### coder le BACK (save_player)
### early ==> impossible de selectionner la combinaison car passe au joueur suivant automatiquement
### nettoyer code


from include import cplayer
from include import cgame
import random

GAME_LOGO = 'Yahtzydarts.png'
HEADERS = "D1","D2","","","","","CASE" 
OPTIONS = {'theme': 'default', 'video' : True} 
NB_DARTS = 9
GAME_RECORDS = {'Score Per Round': 'DESC', 'Dribbles': 'DESC'}
VERSION = '1.00'

def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
    """
    return nb_players >= 1 and nb_players <= 4, VERSION, 4
    
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
    Yahtzydarts game class
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
        self.video = options['video']
                
        #  Get the options
        self.max_round = 15 
        self.wrong = False
        # Generic but copied as reminder
        self.colors = ['green', 'blue', 'red', 'gold']

        self.score_j1 = 0
        self.score_j2 = 0
        self.score_j3 = 0
        self.score_j4 = 0
        
        self.leds1 = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]       
        self.leds2 = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
        self.leds3 = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
        self.leds4 = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
        self.leds_blink = self.leds1
        
        #target_suite = [(1, 2, 3, 4, 5, 6),(2, 3, 4, 5, 6, 7), (3, 4, 5, 6, 7, 8), (4, 5, 6, 7, 8, 9), (5, 6, 7, 8, 9, 10), (6, 7, 8, 9, 10, 11), (7, 8, 9, 10, 11, 12), (8, 9, 10, 11, 12, 13), (9, 10, 11, 12, 13, 14), (10, 11, 12, 13, 14, 15), (11, 12, 13, 14, 15, 16), (12, 13, 14, 15, 16, 17), (13, 14, 15, 16, 17, 18), (14, 15, 16, 17, 18, 19), (15, 16, 17, 18, 19, 20)]
        target_suite = [(8, 9, 10, 11, 12, 13), (9, 10, 11, 12, 13, 14), (10, 11, 12, 13, 14, 15), (11, 12, 13, 14, 15, 16), (12, 13, 14, 15, 16, 17), (13, 14, 15, 16, 17, 18), (14, 15, 16, 17, 18, 19), (15, 16, 17, 18, 19, 20)]
        random.shuffle(target_suite)
        self.target = random.choice(target_suite)

        self.points_bonus = 0
        self.points_full = 0
        self.points_yahtzydarts = 0
        self.points_suite = 30
        self.bonus = 35
        self.nb_bull = 0
        
        self.des = ['', '', '', '', '']
        self.des_int = ['', '', '', '', '']
        self.check = False

        # liste preview des scores
        self.score_preview = [
        [0, 'nb1', ' ', 'False', (0, 128, 0)] , [0, 'nb2', ' ', 'False', (0, 128, 0)] , [0, 'nb3', ' ', 'False', (0, 128, 0)] , [0, 'nb4', ' ', 'False', (0, 128, 0)] , [0, 'nb5', ' ', 'False', (0, 128, 0)] , [0, 'nb6', ' ', 'False', (0, 128, 0)] ,
        [0, 'une_paire', ' ', 'False', (0, 128, 0)] , [0, 'deux_paires', ' ', 'False', (0, 128, 0)] , [0, 'brelan', ' ', 'False', (0, 128, 0)] , [0, 'full', ' ', 'False', (0, 128, 0)] , [0, 'carre', ' ', 'False', (0, 128, 0)] , [0, 'bull', ' ', 'False', (0, 128, 0)] , [0, 'suite', ' ', 'False', (0, 128, 0)] , [0, 'yahtzydarts', ' ', 'False', (0, 128, 0)] , [0, 'chance', ' ', 'False', (0, 128, 0)],
        [1, 'nb1', ' ', 'False', (0, 128, 0)] , [1, 'nb2', ' ', 'False', (0, 128, 0)] , [1, 'nb3', ' ', 'False', (0, 128, 0)] , [1, 'nb4', ' ', 'False', (0, 128, 0)] , [1, 'nb5', ' ', 'False', (0, 128, 0)] , [1, 'nb6', ' ', 'False', (0, 128, 0)] ,
        [1, 'une_paire', ' ', 'False', (0, 128, 0)] , [1, 'deux_paires', ' ', 'False', (0, 128, 0)] , [1, 'brelan', ' ', 'False', (0, 128, 0)] , [1, 'full', ' ', 'False', (0, 128, 0)] , [1, 'carre', ' ', 'False', (0, 128, 0)] , [1, 'bull', ' ', 'False', (0, 128, 0)] , [1, 'suite', ' ', 'False', (0, 128, 0)] , [1, 'yahtzydarts', ' ', 'False', (0, 128, 0)] , [1, 'chance', ' ', 'False', (0, 128, 0)],
        [2, 'nb1', ' ', 'False', (0, 128, 0)] , [2, 'nb2', ' ', 'False', (0, 128, 0)] , [2, 'nb3', ' ', 'False', (0, 128, 0)] , [2, 'nb4', ' ', 'False', (0, 128, 0)] , [2, 'nb5', ' ', 'False', (0, 128, 0)] , [2, 'nb6', ' ', 'False', (0, 128, 0)] ,
        [2, 'une_paire', ' ', 'False', (0, 128, 0)] , [2, 'deux_paires', ' ', 'False', (0, 128, 0)] , [2, 'brelan', ' ', 'False', (0, 128, 0)] , [2, 'full', ' ', 'False', (0, 128, 0)] , [2, 'carre', ' ', 'False', (0, 128, 0)] , [2, 'bull', ' ', 'False', (0, 128, 0)] , [2, 'suite', ' ', 'False', (0, 128, 0)] , [2, 'yahtzydarts', ' ', 'False', (0, 128, 0)] , [2, 'chance', ' ', 'False', (0, 128, 0)],
        [3, 'nb1', ' ', 'False', (0, 128, 0)] , [3, 'nb2', ' ', 'False', (0, 128, 0)] , [3, 'nb3', ' ', 'False', (0, 128, 0)] , [3, 'nb4', ' ', 'False', (0, 128, 0)] , [3, 'nb5', ' ', 'False', (0, 128, 0)] , [3, 'nb6', ' ', 'False', (0, 128, 0)] ,
        [3, 'une_paire', ' ', 'False', (0, 128, 0)] , [3, 'deux_paires', ' ', 'False', (0, 128, 0)] , [3, 'brelan', ' ', 'False', (0, 128, 0)] , [3, 'full', ' ', 'False', (0, 128, 0)] , [3, 'carre', ' ', 'False', (0, 128, 0)] , [3, 'bull', ' ', 'False', (0, 128, 0)] , [3, 'suite', ' ', 'False', (0, 128, 0)] , [3, 'yahtzydarts', ' ', 'False', (0, 128, 0)] , [3, 'chance', ' ', 'False', (0, 128, 0)]
        ]
        
        # liste score reel des joueurs
        self.score_joueur = [
        [0, 'nb1', ' ', 'False', (0, 0, 0)] , [0, 'nb2', ' ', 'False', (0, 0, 0)] , [0, 'nb3', ' ', 'False', (0, 0, 0)] , [0, 'nb4', ' ', 'False', (0, 0, 0)] , [0, 'nb5', ' ', 'False', (0, 0, 0)] , [0, 'nb6', ' ', 'False', (0, 0, 0)] ,
        [0, 'une_paire', ' ', 'False', (0, 0, 0)] , [0, 'deux_paires', ' ', 'False', (0, 0, 0)] , [0, 'brelan', ' ', 'False', (0, 0, 0)] , [0, 'full', ' ', 'False', (0, 0, 0)] , [0, 'carre', ' ', 'False', (0, 0, 0)] , [0, 'bull', ' ', 'False', (0, 0, 0)] , [0, 'suite', ' ', 'False', (0, 0, 0)] , [0, 'yahtzydarts', ' ', 'False', (0, 0, 0)] , [0, 'chance', ' ', 'False', (0, 0, 0)],
        [1, 'nb1', ' ', 'False', (0, 0, 0)] , [1, 'nb2', ' ', 'False', (0, 0, 0)] , [1, 'nb3', ' ', 'False', (0, 0, 0)] , [1, 'nb4', ' ', 'False', (0, 0, 0)] , [1, 'nb5', ' ', 'False', (0, 0, 0)] , [1, 'nb6', ' ', 'False', (0, 0, 0)] ,
        [1, 'une_paire', ' ', 'False', (0, 0, 0)] , [1, 'deux_paires', ' ', 'False', (0, 0, 0)] , [1, 'brelan', ' ', 'False', (0, 0, 0)] , [1, 'full', ' ', 'False', (0, 0, 0)] , [1, 'carre', ' ', 'False', (0, 0, 0)] , [1, 'bull', ' ', 'False', (0, 0, 0)] , [1, 'suite', ' ', 'False', (0, 0, 0)] , [1, 'yahtzydarts', ' ', 'False', (0, 0, 0)] , [1, 'chance', ' ', 'False', (0, 0, 0)],
        [2, 'nb1', ' ', 'False', (0, 0, 0)] , [2, 'nb2', ' ', 'False', (0, 0, 0)] , [2, 'nb3', ' ', 'False', (0, 0, 0)] , [2, 'nb4', ' ', 'False', (0, 0, 0)] , [2, 'nb5', ' ', 'False', (0, 0, 0)] , [2, 'nb6', ' ', 'False', (0, 0, 0)] ,
        [2, 'une_paire', ' ', 'False', (0, 0, 0)] , [2, 'deux_paires', ' ', 'False', (0, 0, 0)] , [2, 'brelan', ' ', 'False', (0, 0, 0)] , [2, 'full', ' ', 'False', (0, 0, 0)] , [2, 'carre', ' ', 'False', (0, 0, 0)] , [2, 'bull', ' ', 'False', (0, 0, 0)] , [2, 'suite', ' ', 'False', (0, 0, 0)] , [2, 'yahtzydarts', ' ', 'False', (0, 0, 0)] , [2, 'chance', ' ', 'False', (0, 0, 0)],
        [3, 'nb1', ' ', 'False', (0, 0, 0)] , [3, 'nb2', ' ', 'False', (0, 0, 0)] , [3, 'nb3', ' ', 'False', (0, 0, 0)] , [3, 'nb4', ' ', 'False', (0, 0, 0)] , [3, 'nb5', ' ', 'False', (0, 0, 0)] , [3, 'nb6', ' ', 'False', (0, 0, 0)] ,
        [3, 'une_paire', ' ', 'False', (0, 0, 0)] , [3, 'deux_paires', ' ', 'False', (0, 0, 0)] , [3, 'brelan', ' ', 'False', (0, 0, 0)] , [3, 'full', ' ', 'False', (0, 0, 0)] , [3, 'carre', ' ', 'False', (0, 0, 0)] , [3, 'bull', ' ', 'False', (0, 0, 0)] , [3, 'suite', ' ', 'False', (0, 0, 0)] , [3, 'yahtzydarts', ' ', 'False', (0, 0, 0)] , [3, 'chance', ' ', 'False', (0, 0, 0)]
        ]

        #liste score pour realiser les calculs
        self.score_calcul = [
        [0, 'nb1', '0', 'False', (0, 0, 0)] , [0, 'nb2', '0', 'False', (0, 0, 0)] , [0, 'nb3', '0', 'False', (0, 0, 0)] , [0, 'nb4', '0', 'False', (0, 0, 0)] , [0, 'nb5', '0', 'False', (0, 0, 0)] , [0, 'nb6', '0', 'False', (0, 0, 0)] ,
        [0, 'une_paire', '0', 'False', (0, 0, 0)] , [0, 'deux_paires', '0', 'False', (0, 0, 0)] , [0, 'brelan', '0', 'False', (0, 0, 0)] , [0, 'full', '0', 'False', (0, 0, 0)] , [0, 'carre', '0', 'False', (0, 0, 0)] , [0, 'bull', '0', 'False', (0, 0, 0)] , [0, 'suite', '0', 'False', (0, 0, 0)] , [0, 'yahtzydarts', '0', 'False', (0, 0, 0)] , [0, 'chance', '0', 'False', (0, 0, 0)],
        [1, 'nb1', '0', 'False', (0, 0, 0)] , [1, 'nb2', '0', 'False', (0, 0, 0)] , [1, 'nb3', '0', 'False', (0, 0, 0)] , [1, 'nb4', '0', 'False', (0, 0, 0)] , [1, 'nb5', '0', 'False', (0, 0, 0)] , [1, 'nb6', '0', 'False', (0, 0, 0)] ,
        [1, 'une_paire', '0', 'False', (0, 0, 0)] , [1, 'deux_paires', '0', 'False', (0, 0, 0)] , [1, 'brelan', '0', 'False', (0, 0, 0)] , [1, 'full', '0', 'False', (0, 0, 0)] , [1, 'carre', '0', 'False', (0, 0, 0)] , [1, 'bull', '0', 'False', (0, 0, 0)] , [1, 'suite', '0', 'False', (0, 0, 0)] , [1, 'yahtzydarts', '0', 'False', (0, 0, 0)] , [1, 'chance', '0', 'False', (0, 0, 0)],
        [2, 'nb1', '0', 'False', (0, 0, 0)] , [2, 'nb2', '0', 'False', (0, 0, 0)] , [2, 'nb3', '0', 'False', (0, 0, 0)] , [2, 'nb4', '0', 'False', (0, 0, 0)] , [2, 'nb5', '0', 'False', (0, 0, 0)] , [2, 'nb6', '0', 'False', (0, 0, 0)] ,
        [2, 'une_paire', '0', 'False', (0, 0, 0)] , [2, 'deux_paires', '0', 'False', (0, 0, 0)] , [2, 'brelan', '0', 'False', (0, 0, 0)] , [2, 'full', '0', 'False', (0, 0, 0)] , [2, 'carre', '0', 'False', (0, 0, 0)] , [2, 'bull', '0', 'False', (0, 0, 0)] , [2, 'suite', '0', 'False', (0, 0, 0)] , [2, 'yahtzydarts', '0', 'False', (0, 0, 0)] , [2, 'chance', '0', 'False', (0, 0, 0)],
        [3, 'nb1', '0', 'False', (0, 0, 0)] , [3, 'nb2', '0', 'False', (0, 0, 0)] , [3, 'nb3', '0', 'False', (0, 0, 0)] , [3, 'nb4', '0', 'False', (0, 0, 0)] , [3, 'nb5', '0', 'False', (0, 0, 0)] , [3, 'nb6', '0', 'False', (0, 0, 0)] ,
        [3, 'une_paire', '0', 'False', (0, 0, 0)] , [3, 'deux_paires', '0', 'False', (0, 0, 0)] , [3, 'brelan', '0', 'False', (0, 0, 0)] , [3, 'full', '0', 'False', (0, 0, 0)] , [3, 'carre', '0', 'False', (0, 0, 0)] , [3, 'bull', '0', 'False', (0, 0, 0)] , [3, 'suite', '0', 'False', (0, 0, 0)] , [3, 'yahtzydarts', '0', 'False', (0, 0, 0)] , [3, 'chance', '0', 'False', (0, 0, 0)]
     ]        
        
        # Note : all positions are for 1920/1080. We will have to resize
        self.ratioX = self.display.res['x'] / 1920
        self.ratioY = self.display.res['y'] / 1080

        # For rpi
        self.rpi = rpi

        self.winner = None
        self.infos = ''
        self.translate = self.display.lang.translate
        self.show_hit = True


    def best_score(self, players):
        '''
        Find the winner
        Only one player with best score
        '''
        best_player = None
        best_score = None
        best_count = 0
        for player in players:
            if best_score is None or player.score > best_score:
                best_score = player.score
                best_player = player.ident
                best_count = 1
                self.logs.debug(\
                        f'Best found : {best_score} / Count={best_count} / player = {best_player}')
            elif player.score == best_score:
                best_count += 1

        self.logs.debug(\
                f'Best score : {best_score} / Count={best_count} / Player = {best_player}')

        if best_count == 1:
            return best_player
        return -1

     
    # pour tester les combinaisons
    def check_combinaison(self, actual_player) :
        print('dans CHECK_COMBINAISON')    
        nb1 = 0
        nb2 = 0
        nb3 = 0
        nb4 = 0
        nb5 = 0
        nb6 = 0
        chx = 0
        ### faire boucle pour gain de lignes
        if int(self.target[0]) == int(self.des[0]) :
            nb1 += 1
        if int(self.target[0]) == int(self.des[1]) :
            nb1 += 1
        if int(self.target[0]) == int(self.des[2]) :
            nb1 += 1
        if int(self.target[0]) == int(self.des[3]) :
            nb1 += 1
        if int(self.target[0]) == int(self.des[4]) :
            nb1 += 1
                
        if int(self.target[1]) == int(self.des[0]) :
            nb2 += 1
        if int(self.target[1]) == int(self.des[1]) :
            nb2 += 1
        if int(self.target[1]) == int(self.des[2]) :
            nb2 += 1
        if int(self.target[1]) == int(self.des[3]) :
            nb2 += 1
        if int(self.target[1]) == int(self.des[4]) :
            nb2 += 1
        
        if int(self.target[2]) == int(self.des[0]) :
            nb3 += 1
        if int(self.target[2]) == int(self.des[1]) :
            nb3 += 1
        if int(self.target[2]) == int(self.des[2]) :
            nb3 += 1
        if int(self.target[2]) == int(self.des[3]) :
            nb3 += 1
        if int(self.target[2]) == int(self.des[4]) :
            nb3 += 1
                
        if int(self.target[3]) == int(self.des[0]) :
            nb4 += 1
        if int(self.target[3]) == int(self.des[1]) :
            nb4 += 1
        if int(self.target[3]) == int(self.des[2]) :
            nb4 += 1
        if int(self.target[3]) == int(self.des[3]) :
            nb4 += 1
        if int(self.target[3]) == int(self.des[4]) :
            nb4 += 1
        
        if int(self.target[4]) == int(self.des[0]) :
            nb5 += 1
        if int(self.target[4]) == int(self.des[1]) :
            nb5 += 1
        if int(self.target[4]) == int(self.des[2]) :
            nb5 += 1
        if int(self.target[4]) == int(self.des[3]) :
            nb5 += 1
        if int(self.target[4]) == int(self.des[4]) :
            nb5 += 1
        
        if int(self.target[5]) == int(self.des[0]) :
            nb6 += 1
        if int(self.target[5]) == int(self.des[1]) :
            nb6 += 1
        if int(self.target[5]) == int(self.des[2]) :
            nb6 += 1
        if int(self.target[5]) == int(self.des[3]) :
            nb6 += 1
        if int(self.target[5]) == int(self.des[4]) :
            nb6 += 1
        
        ### Initialise la liste preview avec les resultat 
        for k, v in enumerate(self.score_preview):  
                    if v[0] == actual_player and v[3] == 'False' and v[1] == 'nb1'  :
                        joueur = actual_player
                        combinaison = 'nb1'
                        score = nb1 * int(self.target[0])  
                        drapeau = 'False' 
                        couleur = (0, 128, 0)
                        self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur)
           
                    if v[0] == actual_player and v[3] == 'False' and v[1] == 'nb2'  :
                        joueur = actual_player
                        score = nb2 * int(self.target[1])
                        combinaison = 'nb2'
                        drapeau = 'True' 
                        couleur = (0, 128, 0)
                        self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur)

                    if v[0] == actual_player and v[3] == 'False' and v[1] == 'nb3'  :
                        joueur = actual_player
                        score = nb3 * int(self.target[2])
                        combinaison = 'nb3'
                        drapeau = 'True' 
                        couleur = (0, 128, 0)
                        self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur)

                    if v[0] == actual_player and v[3] == 'False' and v[1] == 'nb4'  :
                        joueur = actual_player
                        score = nb4 * int(self.target[3])
                        combinaison = 'nb4'
                        drapeau = 'True' 
                        couleur = (0, 128, 0)
                        self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 

                    if v[0] == actual_player and v[3] == 'False' and v[1] == 'nb5'  :
                        joueur = actual_player
                        score = nb5 * int(self.target[4])
                        combinaison = 'nb5'
                        drapeau = 'True' 
                        couleur = (0, 128, 0)
                        self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur)
   
                    if v[0] == actual_player and v[3] == 'False' and v[1] == 'nb6'  :
                        joueur = actual_player
                        score = nb6 * int(self.target[5])
                        combinaison = 'nb6'
                        drapeau = 'True' 
                        couleur = (0, 128, 0)
                        self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur)   
        
        #### PARTIE INFERIEURE
        compte_chiffres = []
        for x in self.des:
            compte_chiffres.append(self.des.count(x))

        #si compte_chiffre contient 5        
        for k, v in enumerate(self.score_preview):  
                if 5 in compte_chiffres and self.des_int[0] != 0 :
                        if v[0] == actual_player and v[3] == 'False' and v[1] == 'yahtzydarts'  :
                                print('dans yahtzydarts - trouve')
                                joueur = actual_player
                                score = self.points_yahtzydarts
                                combinaison = 'yahtzydarts'
                                drapeau = 'True'
                                couleur = (0, 128, 0) 
                                self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 
                else :
                        if v[0] == actual_player and v[3] == 'False' and v[1] == 'yahtzydarts'  :
                                print('dans yahtzydarts - non trouve')
                                joueur = actual_player
                                score = '0'
                                combinaison = 'yahtzydarts'
                                drapeau = 'True'
                                couleur = (0, 128, 0) 
                                self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 

        #si compte_chiffre contient 3 et 2 
                if compte_chiffres == [2,2,3,3,3] and self.des_int[0] != 0 \
                        or compte_chiffres == [3,3,3,2,2] and self.des_int[0] != 0 :
                        if v[0] == actual_player and v[3] == 'False' and v[1] == 'full'  :         
                                print('dans full - trouve')
                                joueur = actual_player
                                score = self.points_full
                                combinaison = 'full'
                                drapeau = 'True'
                                couleur = (0, 128, 0) 
                                self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 
                else :
                        if v[0] == actual_player and v[3] == 'False' and v[1] == 'full'  :         
                                print('dans full - non trouve')
                                joueur = actual_player
                                score = 0
                                combinaison = 'full'
                                drapeau = 'True'
                                couleur = (0, 128, 0) 
                                self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 
           
        #si compte_chiffre contient 3 et pas de 2 (possibilite de mettre le carre et le yahzydarts et le full dedans)
                if 3 in compte_chiffres and 2 not in compte_chiffres or 4 in compte_chiffres \
                        or 5 in compte_chiffres and self.des_int[0] != 0 or 3 in compte_chiffres and 2 in compte_chiffres:
                        if v[0] == actual_player and v[3] == 'False' and v[1] == 'brelan'  :        
                                print('dans brelan - trouve')
                                joueur = actual_player
                                score = int(self.des[0]) + int(self.des[1]) + int(self.des[2]) + int(self.des[3]) + int(self.des[4])
                                combinaison = 'brelan'
                                drapeau = 'True'
                                couleur = (0, 128, 0) 
                                self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 
                else :
                        if v[0] == actual_player and v[3] == 'False' and v[1] == 'brelan'  :        
                                print('dans brelan - non trouve')
                                joueur = actual_player
                                score = '0'
                                combinaison = 'brelan'
                                drapeau = 'True'
                                couleur = (0, 128, 0) 
                                self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 

        #si compte_chiffre contient 4 (possibilite de mettre le yahtzydarts dedans)
                if 4 in compte_chiffres or 5 in compte_chiffres :
                        if v[0] == actual_player and v[3] == 'False' and v[1] == 'carre'  :
                                print('dans carre - trouve')
                                joueur = actual_player
                                score = int(self.des[0]) + int(self.des[1]) + int(self.des[2]) + int(self.des[3]) + int(self.des[4])
                                combinaison = 'carre'
                                drapeau = 'True'
                                couleur = (0, 128, 0) 
                                self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 
                else :
                        if v[0] == actual_player and v[3] == 'False' and v[1] == 'carre'  :
                                print('dans carre - non trouve')
                                joueur = actual_player
                                score = '0'
                                combinaison = 'carre'
                                drapeau = 'True'
                                couleur = (0, 128, 0) 
                                self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 

        #si compte_chiffre contient 4*2 et 1*1 
                if compte_chiffres == [2,2,2,2,1] or compte_chiffres == [1,2,2,2,2] or compte_chiffres == [2,2,1,2,2] \
                        or 3 in compte_chiffres and 2 in compte_chiffres or 5 in compte_chiffres or 4 in compte_chiffres:
                        if v[0] == actual_player and v[3] == 'False' and v[1] == 'deux_paires'  :
                                print('dans deux paires - trouve')
                                joueur = actual_player
                                
                                if int(self.des[0]) == int(self.des[1]) and int(self.des[2]) == int(self.des[3]) :
                                        score = int(self.des[0]) + int(self.des[1]) + int(self.des[2]) + int(self.des[3])   
                                elif int(self.des[1]) == int(self.des[2]) and int(self.des[3]) == int(self.des[4]) :
                                        score = int(self.des[1]) + int(self.des[2]) + int(self.des[3]) + int(self.des[4])
                                elif int(self.des[0]) == int(self.des[1]) and int(self.des[3]) == int(self.des[4]) :
                                        score = int(self.des[0]) + int(self.des[1]) + int(self.des[3]) + int(self.des[4]) 
                                
                                combinaison = 'deux_paires'
                                drapeau = 'True'
                                couleur = (0, 128, 0) 
                                self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 
                else :
                        if v[0] == actual_player and v[3] == 'False' and v[1] == 'deux_paires'  :
                                print('dans deux paires - non trouve')
                                joueur = actual_player
                                score = '0'
                                combinaison = 'deux_paires'
                                drapeau = 'True'
                                couleur = (0, 128, 0) 
                                self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 
                                
  
        #si compte_chiffre contient 2*2 
                if compte_chiffres == [2,2,1,1,1] or compte_chiffres == [1,2,2,1,1] or compte_chiffres == [1,1,2,2,1]  \
                        or compte_chiffres == [1,1,1,2,2] or compte_chiffres == [2,2,2,2,1] or compte_chiffres == [1,2,2,2,2] \
                        or compte_chiffres == [2,2,1,2,2] or compte_chiffres == [2,2,3,3,3] or compte_chiffres == [3,3,3,2,2] \
                        or 5 in compte_chiffres or 4 in compte_chiffres or 3 in compte_chiffres : 
                        if v[0] == actual_player and v[3] == 'False' and v[1] == 'une_paire'  :
                                print('dans une paire - trouve') 
                                joueur = actual_player
                                
                                if int(self.des[0]) == int(self.des[1]) :
                                        score = int(self.des[0]) + int(self.des[1])  
                                elif int(self.des[1]) == int(self.des[2]) :
                                        score = int(self.des[1]) + int(self.des[2])  
                                elif int(self.des[2]) == int(self.des[3]) :
                                        score = int(self.des[2]) + int(self.des[3])  
                                elif int(self.des[3]) == int(self.des[4]) :
                                        score = int(self.des[3]) + int(self.des[4])  
                                elif int(self.des[4]) == int(self.des[5]) :
                                        score = int(self.des[4]) + int(self.des[5])  
                                
                                combinaison = 'une_paire'
                                drapeau = 'True'
                                couleur = (0, 128, 0) 
                                self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 
                else :
                        if v[0] == actual_player and v[3] == 'False' and v[1] == 'une_paire'  :
                                print('dans une paire - nonn trouve') 
                                joueur = actual_player
                                score = '0' 
                                combinaison = 'une_paire'
                                drapeau = 'True'
                                couleur = (0, 128, 0) 
                                self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 
        
        ### CHANCE
        for k, v in enumerate(self.score_preview): 
                if v[0] == actual_player and v[3] == 'False' and v[1] == 'chance'  :
                        print('dans chance - trouve')
                        joueur = actual_player
                        score = int(self.des[0]) + int(self.des[1]) + int(self.des[2]) + int(self.des[3]) + int(self.des[4])
                        combinaison = 'chance'
                        drapeau = 'True'
                        couleur = (0, 128, 0) 
                        self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 
        
        ### SUITE - utilisation de self.des_int   
        if (int(self.des_int[-2]) == int(self.des_int[-1]) -1) and (int(self.des_int[-3]) == int(self.des_int[-2]) - 1) \
                or (int(self.des_int[-5]) == int(self.des_int[-4]) -1) and (int(self.des_int[-4]) == int(self.des_int[-3]) - 1) \
                or (int(self.des_int[-4]) == int(self.des_int[-3]) -1) and (int(self.des_int[-3]) == int(self.des_int[-2]) - 1) \
                or (int(self.des_int[-5]) == int(self.des_int[-4]) -1) and (int(self.des_int[-4]) == int(self.des_int[-1]) - 1) \
                or (int(self.des_int[-5]) == int(self.des_int[-4]) -1) and (int(self.des_int[-4]) == int(self.des_int[-2]) - 1) \
                or (int(self.des_int[-4]) == int(self.des_int[-3]) -1) and (int(self.des_int[-3]) == int(self.des_int[-1]) - 1) : 
                
                for k, v in enumerate(self.score_preview):  
                        if v[0] == actual_player and v[3] == 'False' and v[1] == 'suite'  :
                                print('dans suite - trouve')
                                joueur = actual_player
                                
                                if (int(self.des_int[-5]) == int(self.des_int[-4]) -1) and (int(self.des_int[-4]) == int(self.des_int[-3]) - 1) and (int(self.des_int[-3]) == int(self.des_int[-2]) -1) and (int(self.des_int[-2]) == int(self.des_int[-1]) -1):
                                        
                                        score = 50
                                        print(' BIG suite - trouve')
                                elif (int(self.des_int[-2]) == int(self.des_int[-1]) -1) and (int(self.des_int[-3]) == int(self.des_int[-2]) - 1) and (int(self.des_int[-4]) == int(self.des_int[-3]) -1) \
                                        or (int(self.des_int[-5]) == int(self.des_int[-4]) -1) and (int(self.des_int[-4]) == int(self.des_int[-3]) - 1) and (int(self.des_int[-3]) == int(self.des_int[-2]) -1) \
                                        or (int(self.des_int[-5]) == int(self.des_int[-4]) -1) and (int(self.des_int[-4]) == int(self.des_int[-3]) - 1) and (int(self.des_int[-4]) == int(self.des_int[-1]) -1) \
                                        or (int(self.des_int[-4]) == int(self.des_int[-3]) -1) and (int(self.des_int[-3]) == int(self.des_int[-2]) - 1) and (int(self.des_int[-2]) == int(self.des_int[-1]) -1) \
                                        or (int(self.des_int[-5]) == int(self.des_int[-4]) -1) and (int(self.des_int[-4]) == int(self.des_int[-2]) - 1) and (int(self.des_int[-2]) == int(self.des_int[-1]) -1) :
                                        score = 40
                                        print('GRANDE suite - trouve')

                                else :
                                        score = 30
                                        print('PETITE suite - trouve')
                                        
                                #score = 30
                                combinaison = 'suite'
                                drapeau = 'True'
                                couleur = (0, 128, 0) 
                                self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 
        else :
                for k, v in enumerate(self.score_preview):  
                        if v[0] == actual_player and v[3] == 'False' and v[1] == 'suite'  :
                                print('dans suite - non trouve')
                                joueur = actual_player
                                score = '0'
                                combinaison = 'suite'
                                drapeau = 'True'
                                couleur = (0, 128, 0) 
                                self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 
             
        ### BULL - faire boucle
        if int(self.des[0]) == 25 :
            self.nb_bull += 1
        if int(self.des[1]) == 25 :
            self.nb_bull += 1
        if int(self.des[2]) == 25 :
            self.nb_bull += 1
        if int(self.des[3]) == 25 :
            self.nb_bull += 1
        if int(self.des[4]) == 25 :
            self.nb_bull += 1

        if self.nb_bull > 0 :
                for k, v in enumerate(self.score_preview):  
                        if v[0] == actual_player and v[3] == 'False' and v[1] == 'bull'  :
                                print('dans bull - trouve') 
                                joueur = actual_player
                                score = self.nb_bull * 25
                                combinaison = 'bull'
                                drapeau = 'True'
                                couleur = (0, 128, 0) 
                                self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 
        else : 
                for k, v in enumerate(self.score_preview):  
                        if v[0] == actual_player and v[3] == 'False' and v[1] == 'bull'  :
                                print('dans bull - non trouve') 
                                joueur = actual_player
                                score = '0'
                                combinaison = 'bull'
                                drapeau = 'True'
                                couleur = (0, 128, 0) 
                                self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur) 
 
          
    def valide_combinaison(self, players, actual_player, hit) :
		
		
            #handler = self.init_handler()
            if hit == 'SB' or hit == 'DB' and self.check :
                    print('mauvais choix lors de la validation')
                    self.nb_darts = self.nb_darts + 1
                    self.display.message([self.display.lang.translate('Yahtzydarts-wrong')], 1000, None, 'middle', 'big')
                    ok = False
                    self.check = False
                    self.wrong = True    

            elif hit[:1] != 'B' and int(hit[1:]) in self.leds_blink and self.check : 
                    print('choix de la COMBINAISON A VALIDER')
                    self.wrong = False
                    if int(hit[1:]) == 1 :
                        combinaison = 'nb1'
                        for k, v in enumerate(self.score_joueur):  
                            if v[0] == actual_player and v[3] == 'False' and v[1] == 'nb1'  :
                                joueur = actual_player
                                score = self.score_preview[k][2]
                                drapeau = 'True' 
                                couleur = (0, 0, 0)
                                self.score_joueur[k] = (joueur, combinaison, score, drapeau, couleur)
                        ###  supprime la leds dans le choix des combinaisons
                        led_a_retirer = 1
                        video = 'nb1'
                        ok = True 
                        
                    elif int(hit[1:]) == 2 :
                        combinaison = 'nb2'  
                        for k, v in enumerate(self.score_joueur):
                            if v[0] == actual_player and v[3] == 'False' and v[1] == 'nb2'  :
                                joueur = actual_player
                                score = self.score_preview[k][2]
                                drapeau = 'True' 
                                couleur = (0, 0, 0)
                                self.score_joueur[k] = (joueur, combinaison, score, drapeau, couleur)
                        ###  supprime la leds dans le choix des combinaisons
                        led_a_retirer = 2   
                        video = 'nb2' 
                        ok = True   
                        
                    elif int(hit[1:]) == 3 :
                        combinaison = 'nb3'
                        for k, v in enumerate(self.score_joueur):
                            if v[0] == actual_player and v[3] == 'False' and v[1] == 'nb3'  :
                                joueur = actual_player
                                score = self.score_preview[k][2]
                                drapeau = 'True' 
                                couleur = (0, 0, 0)
                                self.score_joueur[k] = (joueur, combinaison, score, drapeau, couleur)    
                        ###  supprime la leds dans le choix des combinaisons
                        led_a_retirer = 3
                        video = 'nb3'
                        ok = True 
                        
                    elif int(hit[1:]) == 4 :
                        combinaison = 'nb4'
                        for k, v in enumerate(self.score_joueur):
                            if v[0] == actual_player and v[3] == 'False' and v[1] == 'nb4'  :
                                joueur = actual_player
                                score = self.score_preview[k][2]
                                drapeau = 'True' 
                                couleur = (0, 0, 0)
                                self.score_joueur[k] = (joueur, combinaison, score, drapeau, couleur)
                        ###  supprime la leds dans le choix des combinaisons
                        led_a_retirer = 4
                        video = 'nb4'
                        ok = True
                                    
                    elif int(hit[1:]) == 5 :
                        combinaison = 'nb5'
                        for k, v in enumerate(self.score_joueur):
                            if v[0] == actual_player and v[3] == 'False' and v[1] == 'nb5'  :
                                joueur = actual_player
                                score = self.score_preview[k][2]
                                drapeau = 'True' 
                                couleur = (0, 0, 0)
                                self.score_joueur[k] = (joueur, combinaison, score, drapeau, couleur)  
                        ###  supprime la leds dans le choix des combinaisons
                        led_a_retirer = 5
                        video = 'nb5'
                        ok = True 
                                 
                    elif int(hit[1:]) == 6 :
                        combinaison = 'nb6'
                        for k, v in enumerate(self.score_joueur):
                            if v[0] == actual_player and v[3] == 'False' and v[1] == 'nb6'  :
                                joueur = actual_player
                                score = self.score_preview[k][2]
                                drapeau = 'True' 
                                couleur = (0, 0, 0)
                                self.score_joueur[k] = (joueur, combinaison, score, drapeau, couleur)  
                        ###  supprime la leds dans le choix des combinaisons
                        led_a_retirer = 6
                        video = 'nb1'
                        ok = True    
                                
                    elif int(hit[1:]) == 7 :
                        combinaison = 'une_paire'
                        for k, v in enumerate(self.score_joueur):
                            if v[0] == actual_player and v[3] == 'False' and v[1] == 'une_paire'  :
                                joueur = actual_player
                                score = self.score_preview[k][2]
                                drapeau = 'True' 
                                couleur = (0, 0, 0)
                                self.score_joueur[k] = (joueur, combinaison, score, drapeau, couleur) 
                        ###  supprime la leds dans le choix des combinaisons
                        led_a_retirer = 7
                        video = 'une_paire'
                        ok = True
                       
                    elif int(hit[1:]) == 8 :
                        combinaison = 'deux_paires'
                        for k, v in enumerate(self.score_joueur):
                            if v[0] == actual_player and v[3] == 'False' and v[1] == 'deux_paires'  :
                                joueur = actual_player
                                score = self.score_preview[k][2]
                                drapeau = 'True' 
                                couleur = (0, 0, 0)
                                self.score_joueur[k] = (joueur, combinaison, score, drapeau, couleur)   
                        ###  supprime la leds dans le choix des combinaisons
                        led_a_retirer = 8
                        video = 'deux_paires'
                        ok = True
                        
                    elif int(hit[1:]) == 9 :
                        combinaison = 'brelan'
                        for k, v in enumerate(self.score_joueur):
                            if v[0] == actual_player and v[3] == 'False' and v[1] == 'brelan'  :
                                joueur = actual_player
                                score = self.score_preview[k][2]
                                drapeau = 'True' 
                                couleur = (0, 0, 0)
                                self.score_joueur[k] = (joueur, combinaison, score, drapeau, couleur)   
                        ###  supprime la leds dans le choix des combinaisons
                        led_a_retirer = 9
                        video = 'brelan'
                        ok = True
                        
                    elif int(hit[1:]) == 10 :
                        combinaison = 'full'
                        for k, v in enumerate(self.score_joueur):
                            if v[0] == actual_player and v[3] == 'False' and v[1] == 'full'  :
                                joueur = actual_player
                                score = self.score_preview[k][2]
                                drapeau = 'True' 
                                couleur = (0, 0, 0)
                                self.score_joueur[k] = (joueur, combinaison, score, drapeau, couleur)  
                        ###  supprime la leds dans le choix des combinaisons
                        led_a_retirer = 10
                        video = 'full'
                        ok = True
                        
                    elif int(hit[1:]) == 11 :
                        combinaison = 'carre' 
                        for k, v in enumerate(self.score_joueur):
                            if v[0] == actual_player and v[3] == 'False' and v[1] == 'carre'  :
                                joueur = actual_player
                                score = self.score_preview[k][2]
                                drapeau = 'True' 
                                couleur = (0, 0, 0)
                                self.score_joueur[k] = (joueur, combinaison, score, drapeau, couleur)   
                        ###  supprime la leds dans le choix des combinaisons
                        led_a_retirer = 11
                        video = 'carre'
                        ok = True
                          
                    elif int(hit[1:]) == 12 :
                        combinaison = 'bull' 
                        for k, v in enumerate(self.score_joueur):  
                            if v[0] == actual_player and v[3] == 'False' and v[1] == 'bull'  :
                                joueur = actual_player
                                score = self.score_preview[k][2]
                                drapeau = 'True' 
                                couleur = (0, 0, 0)
                                self.score_joueur[k] = (joueur, combinaison, score, drapeau, couleur) 
                        ###  supprime la leds dans le choix des combinaisons
                        led_a_retirer = 12
                        video = 'bull'
                        ok = True
                        
                    elif int(hit[1:]) == 13 :
                        combinaison = 'suite'
                        for k, v in enumerate(self.score_joueur):
                            if v[0] == actual_player and v[3] == 'False' and v[1] == 'suite'  :
                                joueur = actual_player
                                score = self.score_preview[k][2]                    
                                drapeau = 'True'
                                couleur = (0, 0, 0) 
                                self.score_joueur[k] = (joueur, combinaison, score, drapeau, couleur)   
                        ###  supprime la leds dans le choix des combinaisons
                        led_a_retirer = 13
                        
                        if int(score) == 30 :
                                video = 'P_suite'
                        elif int(score) == 40 :
                                video = 'G_suite'
                        elif int(score) == 50 :
                                video = 'B_suite'
                        elif int(score) == 0 :
                                video = 'suite'
                        ok = True
                        
                    elif int(hit[1:]) == 14 :
                        combinaison = 'yahtzydarts'
                        for k, v in enumerate(self.score_joueur):
                            if v[0] == actual_player and v[3] == 'False' and v[1] == 'yahtzydarts'  :
                                joueur = actual_player
                                score = self.score_preview[k][2]
                                drapeau = 'True' 
                                couleur = (0, 0, 0)
                                self.score_joueur[k] = (joueur, combinaison, score, drapeau, couleur)  
                        ###  supprime la leds dans le choix des combinaisons
                        led_a_retirer = 14
                        video = 'yahtzydarts'
                        ok = True
           
                    elif int(hit[1:]) == 15 :
                        combinaison = 'chance'
                        for k, v in enumerate(self.score_joueur):
                            if v[0] == actual_player and v[3] == 'False' and v[1] == 'chance'  :
                                joueur = actual_player
                                score = self.score_preview[k][2]
                                drapeau = 'True' 
                                couleur = (0, 0, 0)
                                self.score_joueur[k] = (joueur, combinaison, score, drapeau, couleur)   
                        ###  supprime la leds dans le choix des combinaisons
                        led_a_retirer = 15
                        video = 'chance'
                        ok = True
                        
                    ### supprime la led sellectionnee suivant le joueur    
                    if actual_player == 0 :
                            self.leds1.remove(led_a_retirer)
                    elif actual_player == 1 :
                            self.leds2.remove(led_a_retirer)
                    elif actual_player == 2 :
                            self.leds3.remove(led_a_retirer)
                    elif actual_player == 3 :
                            self.leds4.remove(led_a_retirer)   
                                
                    ### lecture video de la combinaison - voir si possible de mettre WAIT
                    if self.video :
                            self.video_player.play_video(self.display.file_class.get_full_filename(f'yahtzydarts/'+video, 'videos')) 
                            
                            #handler['video'] = 'yahtzydarts/'+video
                            #return handler
                    
                        
                    if ok :
                            print('dans ok - COMBINAISON VALIDEE - reinitialise les variables (check, ok, liste dés')
                            self.des_int = ['', '', '', '', '']
                            self.check = False
                            self.ok = False
                            ok = False
                           
                            self.score_preview = [
                [0, 'nb1', ' ', 'False', (0, 128, 0)] , [0, 'nb2', ' ', 'False', (0, 128, 0)] , [0, 'nb3', ' ', 'False', (0, 128, 0)] , [0, 'nb4', ' ', 'False', (0, 128, 0)] , [0, 'nb5', ' ', 'False', (0, 128, 0)] , [0, 'nb6', ' ', 'False', (0, 128, 0)] ,
                [0, 'une_paire', ' ', 'False', (0, 128, 0)] , [0, 'deux_paires', ' ', 'False', (0, 128, 0)] , [0, 'brelan', ' ', 'False', (0, 128, 0)] , [0, 'full', ' ', 'False', (0, 128, 0)] , [0, 'carre', ' ', 'False', (0, 128, 0)] , [0, 'bull', ' ', 'False', (0, 128, 0)] , [0, 'suite', ' ', 'False', (0, 128, 0)] , [0, 'yahtzydarts', ' ', 'False', (0, 128, 0)] , [0, 'chance', ' ', 'False', (0, 128, 0)],
                [1, 'nb1', ' ', 'False', (0, 128, 0)] , [1, 'nb2', ' ', 'False', (0, 128, 0)] , [1, 'nb3', ' ', 'False', (0, 128, 0)] , [1, 'nb4', ' ', 'False', (0, 128, 0)] , [1, 'nb5', ' ', 'False', (0, 128, 0)] , [1, 'nb6', ' ', 'False', (0, 128, 0)] ,
                [1, 'une_paire', ' ', 'False', (0, 128, 0)] , [1, 'deux_paires', ' ', 'False', (0, 128, 0)] , [1, 'brelan', ' ', 'False', (0, 128, 0)] , [1, 'full', ' ', 'False', (0, 128, 0)] , [1, 'carre', ' ', 'False', (0, 128, 0)] , [1, 'bull', ' ', 'False', (0, 128, 0)] , [1, 'suite', ' ', 'False', (0, 128, 0)] , [1, 'yahtzydarts', ' ', 'False', (0, 128, 0)] , [1, 'chance', ' ', 'False', (0, 128, 0)],
                [2, 'nb1', ' ', 'False', (0, 128, 0)] , [2, 'nb2', ' ', 'False', (0, 128, 0)] , [2, 'nb3', ' ', 'False', (0, 128, 0)] , [2, 'nb4', ' ', 'False', (0, 128, 0)] , [2, 'nb5', ' ', 'False', (0, 128, 0)] , [2, 'nb6', ' ', 'False', (0, 128, 0)] ,
                [2, 'une_paire', ' ', 'False', (0, 128, 0)] , [2, 'deux_paires', ' ', 'False', (0, 128, 0)] , [2, 'brelan', ' ', 'False', (0, 128, 0)] , [2, 'full', ' ', 'False', (0, 128, 0)] , [2, 'carre', ' ', 'False', (0, 128, 0)] , [2, 'bull', ' ', 'False', (0, 128, 0)] , [2, 'suite', ' ', 'False', (0, 128, 0)] , [2, 'yahtzydarts', ' ', 'False', (0, 128, 0)] , [2, 'chance', ' ', 'False', (0, 128, 0)],
                [3, 'nb1', ' ', 'False', (0, 128, 0)] , [3, 'nb2', ' ', 'False', (0, 128, 0)] , [3, 'nb3', ' ', 'False', (0, 128, 0)] , [3, 'nb4', ' ', 'False', (0, 128, 0)] , [3, 'nb5', ' ', 'False', (0, 128, 0)] , [3, 'nb6', ' ', 'False', (0, 128, 0)] ,
                [3, 'une_paire', ' ', 'False', (0, 128, 0)] , [3, 'deux_paires', ' ', 'False', (0, 128, 0)] , [3, 'brelan', ' ', 'False', (0, 128, 0)] , [3, 'full', ' ', 'False', (0, 128, 0)] , [3, 'carre', ' ', 'False', (0, 128, 0)] , [3, 'bull', ' ', 'False', (0, 128, 0)] , [3, 'suite', ' ', 'False', (0, 128, 0)] , [3, 'yahtzydarts', ' ', 'False', (0, 128, 0)] , [3, 'chance', ' ', 'False', (0, 128, 0)]
                ]
        
                            ### intialise 'true-false' de score_preview pour ne pas pouvoir entrer de nouvelles valeurs dans ces combinaisons
                            for k, v in enumerate(self.score_joueur) :
                                    if v[3] == 'True' :
                                        joueur = v[0]
                                        combinaison = v[1]
                                        score = v[2]
                                        drapeau = 'True' 
                                        couleur = (0, 0, 0)
                                        self.score_preview[k] = (joueur, combinaison, score, drapeau, couleur)          
                            
                            ### nouveau - pour calcul score --- pour ne pas afficher '0' sur le tableau car ' ' est utilise
                            for k, v in enumerate(self.score_joueur) :
                                    if v[3] == 'True' : 
                                        joueur = v[0] 
                                        combinaison = v[1]   
                                        score = v[2]
                                        drapeau = 'True'
                                        couleur = (0, 0, 0)
                                        self.score_calcul[k] = (joueur, combinaison, score, drapeau, couleur)

            else :
                    print('mauvais choix lors de la validation')
                    self.nb_darts = self.nb_darts + 1
                    self.display.message([self.display.lang.translate('Yahtzydarts-wrong')], 1000, None, 'middle', 'big')
                    ok = False
                    self.check = False
                    self.wrong = True   
           
            #return handler

    def calcul_score(self):    
        print('dans def calcul')
        soustotal_j1 = int(self.score_calcul[0][2]) +  int(self.score_calcul[1][2]) + int(self.score_calcul[2][2]) + int(self.score_calcul[3][2]) + int(self.score_calcul[4][2]) + int(self.score_calcul[5][2])
        soustotal_j2 = int(self.score_calcul[15][2]) +  int(self.score_calcul[16][2]) + int(self.score_calcul[17][2]) + int(self.score_calcul[18][2]) + int(self.score_calcul[19][2]) + int(self.score_calcul[20][2])
        soustotal_j3 = int(self.score_calcul[30][2]) +  int(self.score_calcul[31][2]) + int(self.score_calcul[32][2]) + int(self.score_calcul[33][2]) + int(self.score_calcul[34][2]) + int(self.score_calcul[35][2])
        soustotal_j4 = int(self.score_calcul[45][2]) +  int(self.score_calcul[46][2]) + int(self.score_calcul[47][2]) + int(self.score_calcul[48][2]) + int(self.score_calcul[49][2]) + int(self.score_calcul[50][2])

        #colonne7 (bonus)
        if soustotal_j1 >= self.points_bonus :
                bonus_j1 = self.bonus
        if soustotal_j2 >= self.points_bonus  :
                bonus_j2 = self.bonus
        if soustotal_j3 >= self.points_bonus :
                bonus_j3 = self.bonus   
        if soustotal_j4 >= self.points_bonus :
                bonus_j4 = self.bonus
        # n ajoute pas le bonus
        if soustotal_j1 < self.points_bonus :
                bonus_j1 = 0
        if soustotal_j2 < self.points_bonus  :
                bonus_j2 = 0
        if soustotal_j3 < self.points_bonus :
                bonus_j3 = 0   
        if soustotal_j4 < self.points_bonus :
                bonus_j4 = 0

        total_sup_j1 = int(bonus_j1) + int(soustotal_j1)
        total_sup_j2 = int(bonus_j2) + int(soustotal_j2) 
        total_sup_j3 = int(bonus_j3) + int(soustotal_j3)
        total_sup_j4 = int(bonus_j4) + int(soustotal_j4)
 
        total_inf_j1 = int(self.score_calcul[6][2]) +  int(self.score_calcul[7][2]) + int(self.score_calcul[8][2]) + int(self.score_calcul[9][2]) + int(self.score_calcul[10][2]) + int(self.score_calcul[11][2]) + int(self.score_calcul[12][2]) + int(self.score_calcul[13][2]) + int(self.score_calcul[14][2])
        total_inf_j2 = int(self.score_calcul[21][2]) +  int(self.score_calcul[22][2]) + int(self.score_calcul[23][2]) + int(self.score_calcul[24][2]) + int(self.score_calcul[25][2]) + int(self.score_calcul[26][2]) + int(self.score_calcul[27][2]) + int(self.score_calcul[28][2]) + int(self.score_calcul[29][2])
        total_inf_j3 = int(self.score_calcul[36][2]) +  int(self.score_calcul[37][2]) + int(self.score_calcul[38][2]) + int(self.score_calcul[39][2]) + int(self.score_calcul[40][2]) + int(self.score_calcul[41][2]) + int(self.score_calcul[42][2]) + int(self.score_calcul[43][2]) + int(self.score_calcul[44][2])
        total_inf_j4 = int(self.score_calcul[51][2]) +  int(self.score_calcul[52][2]) + int(self.score_calcul[53][2]) + int(self.score_calcul[54][2]) + int(self.score_calcul[55][2]) + int(self.score_calcul[56][2]) + int(self.score_calcul[57][2]) + int(self.score_calcul[58][2]) + int(self.score_calcul[59][2])

        self.score_j1 = int(total_inf_j1) + int(total_sup_j1)
        self.score_j2 = int(total_inf_j2) + int(total_sup_j2)
        self.score_j3 = int(total_inf_j3) + int(total_sup_j3)
        self.score_j4 = int(total_inf_j4) + int(total_sup_j4)
            
 
    def pre_dart_check(self,  players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """

        self.show_hit = False # Don't show hit segment
        return_code = 0
        # infos Can be used to create a per-player debug output
        self.infos += f"###### Player {actual_player} ######{self.lf}"

        
        #initialisation des leds + points des 
        if actual_round == 1 and player_launch == 1 and actual_player == 0:    
            ### calcul bonus - yahtzydarts - full suivant la valeur des chiffres a jouer
            self.points_bonus = (self.target[0] + self.target[1] + self.target[2] + self.target[3] + self.target[4] + self.target[5]) * 3
            self.points_yahtzydarts = (5 * int(self.target[5])) + 20  ### 50 d origine pour 66666 (30 points max - ajouter 20points)  
            self.points_full = (3 * int(self.target[5])) + (2 * self.target[4]) - 3    ### 25 d origine pour 66655 (28 points max - retirer 3points)
            self.bonus = (self.target[0] + self.target[1] + self.target[2] + self.target[3] + self.target[4] + self.target[5]) + 14 ### 35 d origine pour 1-2-3-4-5-6 (21 points max) - ajouter 14 points
            
            '''
            for player in players :
                    player.leds = self.leds_valide
                    print('player.leds - attribution des leds (1-15) a tous les joueurs')
                    print(player.leds)
            '''
                    
            ### changer bk
            self.display.display_background('bk_yahtzydarts.jpg')
            
            ### choix de la couleur des joueurs 
            i = 0
            for p in players:
                p.color = self.colors[i]
                i += 1
 
        # Set total to 0 beginning of turn    
        if player_launch == 1:
            ### reinitialise le compteur bulls et liste dés
            self.des = ['', '', '', '', '']
            self.nb_bull = 0
                
        # You will probably save the turn to be used in case of backup turn (each first launch):
        if player_launch == 1:
            self.save_turn(players)
            # Clean actual_players' columns
            i = 0
            for column in players[actual_player].columns:
                players[actual_player].columns[i] = ['', 'txt']
                i += 1
        
        if not self.check :
            ### leds des chiffres a viser    
            leds = (f'S{self.target[0]}#{self.colors[0]}|D{self.target[0]}#{self.colors[0]}|T{self.target[0]}#{self.colors[0]}|S{self.target[1]}#{self.colors[0]}|D{self.target[1]}#{self.colors[0]}|T{self.target[1]}#{self.colors[0]}|S{self.target[2]}#{self.colors[0]}|D{self.target[2]}#{self.colors[0]}|T{self.target[2]}#{self.colors[0]}|S{self.target[3]}#{self.colors[0]}|D{self.target[3]}#{self.colors[0]}|T{self.target[3]}#{self.colors[0]}|S{self.target[4]}#{self.colors[0]}|D{self.target[4]}#{self.colors[0]}|T{self.target[4]}#{self.colors[0]}|S{self.target[5]}#{self.colors[0]}|D{self.target[5]}#{self.colors[0]}|T{self.target[5]}#{self.colors[0]}')
            self.rpi.set_target_leds(leds)
            self.rpi.set_target_leds_blink('') 
        
        else : 
            if actual_player == 0 :
                    self.leds_blink = self.leds1
            elif actual_player == 1 :
                    self.leds_blink = self.leds2
            elif actual_player == 2 :
                    self.leds_blink = self.leds3
            elif actual_player == 3 :
                    self.leds_blink = self.leds4
            
            ### leds pour choisir ou mettre le score
            ledss = '|'.join(f'S{number}#{self.colors[0]}|D{number}#{self.colors[0]}|T{number}#{self.colors[0]}' for number in self.leds_blink)  
            self.rpi.set_target_leds('')
            self.rpi.set_target_leds_blink(ledss)      
        
        self.des.sort(reverse = True)
        
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

        ## valide la combinaison choisie au prealable
        if self.check :  
                self.valide_combinaison(players, actual_player,  hit)
                                
                self.calcul_score()
                
                # Victory for current player
                if actual_player == len(players) - 1 and actual_round >= self.max_round  :

                    self.calcul_score()    
                        
                    for player in players :
                        if player.ident == 0 :
                                player.score = self.score_j1 
                        if player.ident == 1 :
                                player.score = self.score_j2 
                        if player.ident == 2 :
                                player.score = self.score_j3
                        if player.ident == 3 :
                                player.score = self.score_j4
                                
                    winner = self.best_score(players)
                    if winner > 0:
                        self.winner = winner
                        return_code = 3
                    else:
                        # No winner : last round reached
                        return_code = 2        
        
                else :
                    if not self.wrong :
                            return 1 
         
        
        
        multi = self.get_hit_unit(hit)
        if hit == 'SB' or hit == 'DB' and not self.check :
            for i in range((multi)) : 
                ### passe l emplacement si il contient un chiffre  
                if self.des[-i] != '' :
                    i=i+1
                ### inscrit le chiffre touche    
                if self.des[-i] == ''  :
                    self.des[-i] = '25'

            ### inverse l ordre de self.des
            self.des.sort(reverse=True)
            #self.display.play_sound('DiceRoll')
            handler['sound'] = 'DiceRoll'
        
        elif int(hit[1:]) in self.target and not self.check : # check si Joueur touche un chiffre target 
            for i in range((multi)) :
                ### passe l emplacement si il contient un chiffre  
                if self.des[-i] != '' :
                    i=i+1
                ### inscrit le chiffre touche    
                if self.des[-i] == ''  :
                    self.des[-i] = str((hit[1:]))

            ### inverse l ordre de self.des
            self.des.sort(reverse=True)
            #self.display.play_sound('DiceRoll')
            handler['sound'] = 'DiceRoll'

        else:
            ### si pas touche un bon chiffre, note 0    
            multi = 1
            for i in range((multi)) :
                if self.des[i] != '' :
                    i=i+1
                if self.des[-i] == ''  :
                    self.des[-i] = '0'
            self.des.sort(reverse=True)
            if not self.check :
                #self.display.play_sound('miss') 
                handler['sound'] = 'miss'

        #### transforme la liste self.des en "integer" por checker les combinaisons        
        for k, v in enumerate(self.des):
           if v != '':
              self.des_int[k] = int(self.des[k])
           else : 
              pass  

        #### SI les 5 des sont joues - active self.check (True)
        if self.des.count('') == 0 :  
            self.display.play_sound('yathzydarts_choix_combinaison')
            #handler['sound'] = 'yahtzydarts_choix_combinaison'
            self.check = True
          
        if self.check :
                ### classe self.des_int dans l ordre pour faciliter la detection des combinaisons
                self.des_int.sort(reverse = False)
                
                #verifie les combinaisons
                self.check_combinaison(actual_player)

        #initialise les scores   --- DOUBLONS - A TESTER SANS   
        '''
        for player in players :
                if player.ident == 0 :
                        player.score = self.score_j1 
                if player.ident == 1 :
                        player.score = self.score_j2 
                if player.ident == 2 :
                        player.score = self.score_j3
                if player.ident == 3 :
                        player.score = self.score_j4
        '''
     
        # You may want to count how many touches
        # Simple = 1 touch, Double = 2 touches, Triple = 3 touches
        players[actual_player].increment_hits(hit)

        # You may want to count darts played
        players[actual_player].darts_thrown += 1

        # It is recommanded to update stats every dart thrown
        self.refresh_stats(players, actual_round)

        ### NORMALEMENT NON UTILISE - A TESTER SANS
        # Check for end of game (no more rounds to play)
        '''
        if player_launch == self.nb_darts and actual_round >= self.max_round \
                and actual_player == len(players) - 1:
            winner = self.best_score(players)
            if winner > 0:
                self.winner = winner
                return_code = 3
            else:
                # No winner : last round reached
               return_code = 2
        '''
        
        # Time for shot or video ?
        handler['take_shot'] = self.time_to_take_shot_or_video(hit)
        handler['return_code'] = return_code
        return handler
        
        # Return code to main
        #return return_code
        
    def refresh_game_screen(self, Players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player,TxtOnLogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
       
        ClickZones={}
        
        # Background image
        if self.check :
            self.display.display_background('bk_yahtzydarts1.jpg')
            liste_a_afficher = self.score_preview
        else : 
            self.display.display_background('bk_yahtzydarts.jpg')
            liste_a_afficher = self.score_joueur
       
        
        # Show players names
        self.display_player_name(self.display, 110 * self.ratioX, 70 * self.ratioY, actual_player, Players[0])
        self.display_player_name(self.display, 110 * self.ratioX, 580 * self.ratioY, actual_player, Players[0])
        if len(Players)>1:
            self.display_player_name(self.display, 110 * self.ratioX, 141 * self.ratioY, actual_player, Players[1])
            self.display_player_name(self.display, 110 * self.ratioX, 651 * self.ratioY, actual_player, Players[1])
        if len(Players)>2:
            self.display_player_name(self.display, 110 * self.ratioX, 216 * self.ratioY, actual_player, Players[2])
            self.display_player_name(self.display, 110 * self.ratioX, 723 * self.ratioY, actual_player, Players[2])
        if len(Players)>3:
            self.display_player_name(self.display, 110 * self.ratioX, 291 * self.ratioY, actual_player, Players[3])
            self.display_player_name(self.display, 110 * self.ratioX, 801 * self.ratioY, actual_player, Players[3])
            

        #chiffres a jouer  1-6
        self.display.blit_text(f"{self.target[0]}", 390 * self.ratioX, 20 * self.ratioY, 60 * self.ratioX, 60 * self.ratioY, color=(255, 255, 255), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{self.target[1]}", 525 * self.ratioX, 20 * self.ratioY, 60 * self.ratioX, 60 * self.ratioY, color=(255, 255, 255), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{self.target[2]}", 640 * self.ratioX, 20 * self.ratioY, 60 * self.ratioX, 60 * self.ratioY, color=(255, 255, 255), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{self.target[3]}", 770 * self.ratioX, 20 * self.ratioY, 60 * self.ratioX, 60 * self.ratioY, color=(255, 255, 255), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{self.target[4]}", 895 * self.ratioX, 20 * self.ratioY, 60 * self.ratioX, 60 * self.ratioY, color=(255, 255, 255), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{self.target[5]}", 1015 * self.ratioX, 20 * self.ratioY, 60 * self.ratioX, 60 * self.ratioY, color=(255, 255, 255), align='Left', valign='top', margin=False)
        
        ### affichage des infos sur les points BONUS, FULL, YAHTZEE, SUITE
        self.display.blit_text("(Si "+f"{self.points_bonus}"+")", 1260 * self.ratioX, 44 * self.ratioY, 50 * self.ratioX, 50 * self.ratioX, color=(255, 255, 255), align='Left', valign='top', margin=False)
        self.display.blit_text("("+f"{self.points_full}"+")", 768 * self.ratioX, 559 * self.ratioY, 40 * self.ratioX, 40 * self.ratioX, color=(255, 255, 0), align='Left', valign='top', margin=False)
        self.display.blit_text("(30-40-50)", 1110 * self.ratioX, 559 * self.ratioY, 100 * self.ratioX, 100 * self.ratioX, color=(255, 255, 0), align='Left', valign='top', margin=False)
        self.display.blit_text("("+f"{self.points_yahtzydarts}"+")", 1265 * self.ratioX, 559 * self.ratioY, 40 * self.ratioX, 40 * self.ratioX, color=(255, 255, 0), align='Left', valign='top', margin=False)
        self.display.blit_text("("+f"{self.bonus}"+")", 1265 * self.ratioX, 60 * self.ratioY, 40 * self.ratioX, 35 * self.ratioX, color=(255, 255, 0), align='Left', valign='top', margin=False)
        
        
        #colonne0 (chiffre1)  
        self.display.blit_text(f"{liste_a_afficher[0][2]}", 380 * self.ratioX, 90 * self.ratioY, 75 * self.ratioX, 75 * self.ratioY, color=(liste_a_afficher[0][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[15][2]}", 380 * self.ratioX, 170 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[15][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[30][2]}", 380 * self.ratioX, 242 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[30][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[45][2]}", 380 * self.ratioX, 312 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[45][4]), align='Left', valign='top', margin=False)
        
        #colonne1 (chiffre2)
        self.display.blit_text(f"{liste_a_afficher[1][2]}", 510 * self.ratioX, 90 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[1][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[16][2]}", 510 * self.ratioX, 170 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[16][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[31][2]}", 510 * self.ratioX, 242 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[31][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[46][2]}", 510 * self.ratioX, 312 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[46][4]), align='Left', valign='top', margin=False)
        
        #colonne2 (chiffre3)
        self.display.blit_text(f"{liste_a_afficher[2][2]}", 635 * self.ratioX, 90 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[2][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[17][2]}", 635 * self.ratioX, 170 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[17][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[32][2]}", 635 * self.ratioX, 242 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[32][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[47][2]}", 635 * self.ratioX, 312 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[47][4]), align='Left', valign='top', margin=False)
        
        #colonne3 (chiffre4)
        self.display.blit_text(f"{liste_a_afficher[3][2]}", 760 * self.ratioX, 90 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[3][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[18][2]}", 760 * self.ratioX, 170 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[18][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[33][2]}", 760 * self.ratioX, 242 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[33][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[48][2]}", 760 * self.ratioX, 312 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[48][4]), align='Left', valign='top', margin=False)
        
        #colonne4 (chiffre5)
        self.display.blit_text(f"{liste_a_afficher[4][2]}", 885 * self.ratioX, 90 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[4][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[19][2]}", 885 * self.ratioX, 170 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[19][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[34][2]}", 885 * self.ratioX, 242 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[34][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[49][2]}", 885 * self.ratioX, 312 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[49][4]), align='Left', valign='top', margin=False)
        
        #colonne5 (chiffre6)
        self.display.blit_text(f"{liste_a_afficher[5][2]}", 1005 * self.ratioX, 90 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[5][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[20][2]}", 1005 * self.ratioX, 170 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[20][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[35][2]}", 1005 * self.ratioX, 242 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[35][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[50][2]}", 1005 * self.ratioX, 312 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[50][4]), align='Left', valign='top', margin=False)
        

        #partie inferieur
        #colonne0 - 1 paire
        self.display.blit_text(f"{liste_a_afficher[6][2]}", 380 * self.ratioX, 600 * self.ratioY, 75 * self.ratioX, 75 * self.ratioY, color=(liste_a_afficher[6][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[21][2]}", 380 * self.ratioX, 675 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[21][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[36][2]}", 380 * self.ratioX, 747 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[36][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[51][2]}", 380 * self.ratioX, 817 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[51][4]), align='Left', valign='top', margin=False)
        
        #colonne2 - 2 paires
        self.display.blit_text(f"{liste_a_afficher[7][2]}", 510 * self.ratioX, 600 * self.ratioY, 75 * self.ratioX, 75 * self.ratioY, color=(liste_a_afficher[7][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[22][2]}", 510 * self.ratioX, 675 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[22][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[37][2]}", 510 * self.ratioX, 747 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[37][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[52][2]}", 510 * self.ratioX, 817 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[52][4]), align='Left', valign='top', margin=False)
        
        #colonne3 - brelan
        self.display.blit_text(f"{liste_a_afficher[8][2]}", 635 * self.ratioX, 600 * self.ratioY, 75 * self.ratioX, 75 * self.ratioY, color=(liste_a_afficher[8][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[23][2]}", 635 * self.ratioX, 675 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[23][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[38][2]}", 635 * self.ratioX, 747 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[38][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[53][2]}", 635 * self.ratioX, 817 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[53][4]), align='Left', valign='top', margin=False)
        
        #colonne4 - full
        self.display.blit_text(f"{liste_a_afficher[9][2]}", 760 * self.ratioX, 600 * self.ratioY, 75 * self.ratioX, 75 * self.ratioY, color=(liste_a_afficher[9][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[24][2]}", 760 * self.ratioX, 675 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[24][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[39][2]}", 760 * self.ratioX, 747 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[39][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[54][2]}", 760 * self.ratioX, 817 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[54][4]), align='Left', valign='top', margin=False)
        
        #colonne5 - carre
        self.display.blit_text(f"{liste_a_afficher[10][2]}", 885 * self.ratioX, 600 * self.ratioY, 75 * self.ratioX, 75 * self.ratioY, color=(liste_a_afficher[10][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[25][2]}", 885 * self.ratioX, 675 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[25][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[40][2]}", 885 * self.ratioX, 747 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[40][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[55][2]}", 885 * self.ratioX, 817 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[55][4]), align='Left', valign='top', margin=False)
        
        #colonne6 - bull
        self.display.blit_text(f"{liste_a_afficher[11][2]}", 1005 * self.ratioX, 600 * self.ratioY, 75 * self.ratioX, 75 * self.ratioY, color=(liste_a_afficher[11][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[26][2]}", 1005 * self.ratioX, 675 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[26][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[41][2]}", 1005 * self.ratioX, 747 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[41][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[56][2]}", 1005 * self.ratioX, 817 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[56][4]), align='Left', valign='top', margin=False)
        
        #colonne7 - suite
        self.display.blit_text(f"{liste_a_afficher[12][2]}", 1135 * self.ratioX, 600 * self.ratioY, 75 * self.ratioX, 75 * self.ratioY, color=(liste_a_afficher[12][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[27][2]}", 1135 * self.ratioX, 675 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[27][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[42][2]}", 1135 * self.ratioX, 747 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[42][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[57][2]}", 1135 * self.ratioX, 817 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[57][4]), align='Left', valign='top', margin=False)
        
        #colonne8 - yahtzee
        self.display.blit_text(f"{liste_a_afficher[13][2]}", 1255 * self.ratioX, 600 * self.ratioY, 75 * self.ratioX, 75 * self.ratioY, color=(liste_a_afficher[13][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[28][2]}", 1255 * self.ratioX, 675 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[28][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[43][2]}", 1255 * self.ratioX, 747 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[43][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[58][2]}", 1255 * self.ratioX, 817 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[58][4]), align='Left', valign='top', margin=False)
        
        #colonne9 - chance
        self.display.blit_text(f"{liste_a_afficher[14][2]}", 1380 * self.ratioX, 600 * self.ratioY, 75 * self.ratioX, 75 * self.ratioY, color=(liste_a_afficher[14][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[29][2]}", 1380 * self.ratioX, 675 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[29][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[44][2]}", 1380 * self.ratioX, 747 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[44][4]), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{liste_a_afficher[59][2]}", 1385 * self.ratioX, 817 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(liste_a_afficher[59][4]), align='Left', valign='top', margin=False)
        
        #affichage des des
        self.display.blit_text(f"{self.des_int[0]}", 500 * self.ratioX, 940 * self.ratioY, 125 * self.ratioX, 125 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{self.des_int[1]}", 710 * self.ratioX, 940 * self.ratioY, 125 * self.ratioX, 125 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{self.des_int[2]}", 920 * self.ratioX, 940 * self.ratioY, 125 * self.ratioX, 125 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{self.des_int[3]}", 1130 * self.ratioX, 940 * self.ratioY, 125 * self.ratioX, 125 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{self.des_int[4]}", 1340 * self.ratioX, 940 * self.ratioY, 125 * self.ratioX, 125 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
      

        ### affichage des scores
        #colonne6 (soustotal)
        soustotal_j1 = int(self.score_calcul[0][2]) +  int(self.score_calcul[1][2]) + int(self.score_calcul[2][2]) + int(self.score_calcul[3][2]) + int(self.score_calcul[4][2]) + int(self.score_calcul[5][2])
        soustotal_j2 = int(self.score_calcul[15][2]) +  int(self.score_calcul[16][2]) + int(self.score_calcul[17][2]) + int(self.score_calcul[18][2]) + int(self.score_calcul[19][2]) + int(self.score_calcul[20][2])
        soustotal_j3 = int(self.score_calcul[30][2]) +  int(self.score_calcul[31][2]) + int(self.score_calcul[32][2]) + int(self.score_calcul[33][2]) + int(self.score_calcul[34][2]) + int(self.score_calcul[35][2])
        soustotal_j4 = int(self.score_calcul[45][2]) +  int(self.score_calcul[46][2]) + int(self.score_calcul[47][2]) + int(self.score_calcul[48][2]) + int(self.score_calcul[49][2]) + int(self.score_calcul[50][2])
        
        self.display.blit_text(f"{soustotal_j1}", 1135 * self.ratioX, 90 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{soustotal_j2}", 1135 * self.ratioX, 170 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{soustotal_j3}", 1135 * self.ratioX, 242 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{soustotal_j4}", 1135 * self.ratioX, 312 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        
        #colonne7 (bonus)
        if soustotal_j1 >= self.points_bonus :
                bonus_j1 = self.bonus
        if soustotal_j2 >= self.points_bonus  :
                bonus_j2 = self.bonus
        if soustotal_j3 >= self.points_bonus :
                bonus_j3 = self.bonus   
        if soustotal_j4 >= self.points_bonus :
                bonus_j4 = self.bonus
        # n ajoute pas le bonus
        if soustotal_j1 < self.points_bonus :
                bonus_j1 = 0
        if soustotal_j2 < self.points_bonus  :
                bonus_j2 = 0
        if soustotal_j3 < self.points_bonus :
                bonus_j3 = 0   
        if soustotal_j4 < self.points_bonus :
                bonus_j4 = 0

        self.display.blit_text(f"{bonus_j1}", 1255 * self.ratioX, 90 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{bonus_j2}", 1255 * self.ratioX, 170 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{bonus_j3}", 1255 * self.ratioX, 242 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{bonus_j4}", 1255 * self.ratioX, 312 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        
        #colonne8 (total-sup)
        total_sup_j1 = int(bonus_j1) + int(soustotal_j1)
        total_sup_j2 = int(bonus_j2) + int(soustotal_j2) 
        total_sup_j3 = int(bonus_j3) + int(soustotal_j3)
        total_sup_j4 = int(bonus_j4) + int(soustotal_j4)
        
        self.display.blit_text(f"{total_sup_j1}", 1510 * self.ratioX, 90 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{total_sup_j2}", 1510 * self.ratioX, 170 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{total_sup_j3}", 1510 * self.ratioX, 242 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{total_sup_j4}", 1510 * self.ratioX, 312 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        
        #colonne9 (total-inf)
        total_inf_j1 = int(self.score_calcul[6][2]) +  int(self.score_calcul[7][2]) + int(self.score_calcul[8][2]) + int(self.score_calcul[9][2]) + int(self.score_calcul[10][2]) + int(self.score_calcul[11][2]) + int(self.score_calcul[12][2]) + int(self.score_calcul[13][2]) + int(self.score_calcul[14][2])
        total_inf_j2 = int(self.score_calcul[21][2]) +  int(self.score_calcul[22][2]) + int(self.score_calcul[23][2]) + int(self.score_calcul[24][2]) + int(self.score_calcul[25][2]) + int(self.score_calcul[26][2]) + int(self.score_calcul[27][2]) + int(self.score_calcul[28][2]) + int(self.score_calcul[29][2])
        total_inf_j3 = int(self.score_calcul[36][2]) +  int(self.score_calcul[37][2]) + int(self.score_calcul[38][2]) + int(self.score_calcul[39][2]) + int(self.score_calcul[40][2]) + int(self.score_calcul[41][2]) + int(self.score_calcul[42][2]) + int(self.score_calcul[43][2]) + int(self.score_calcul[44][2])
        total_inf_j4 = int(self.score_calcul[51][2]) +  int(self.score_calcul[52][2]) + int(self.score_calcul[53][2]) + int(self.score_calcul[54][2]) + int(self.score_calcul[55][2]) + int(self.score_calcul[56][2]) + int(self.score_calcul[57][2]) + int(self.score_calcul[58][2]) + int(self.score_calcul[59][2])

        self.display.blit_text(f"{total_inf_j1}", 1635 * self.ratioX, 90 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{total_inf_j2}", 1635 * self.ratioX, 170 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{total_inf_j3}", 1635 * self.ratioX, 242 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{total_inf_j4}", 1635 * self.ratioX, 312 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 0), align='Left', valign='top', margin=False)
        
        #colonne10 (score)
        self.score_j1 = int(total_inf_j1) + int(total_sup_j1)
        self.score_j2 = int(total_inf_j2) + int(total_sup_j2)
        self.score_j3 = int(total_inf_j3) + int(total_sup_j3)
        self.score_j4 = int(total_inf_j4) + int(total_sup_j4)
        
        self.display.blit_text(f"{self.score_j1}", 1755 * self.ratioX, 90 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 128, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{self.score_j2}", 1755 * self.ratioX, 170 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(0, 0, 255), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{self.score_j3}", 1755 * self.ratioX, 242 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(255, 0, 0), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{self.score_j4}", 1755 * self.ratioX, 312 * self.ratioY, 75 * self.ratioX, 75 * self.ratioX, color=(225,225, 0), align='Left', valign='top', margin=False)

        # Show round number 
        self.display.blit_text(f"Round", 100 * self.ratioX, 925 * self.ratioY, 150, 150, color=(246, 85, 41), align='Left', valign='top', margin=False)
        self.display.blit_text(f"{actual_round} / {max_round}", 100 * self.ratioX, 1000 * self.ratioY, 100, 100, color=(246, 85, 41), align='Right', valign='top', margin=False)
                 
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

        txtcolor = (255,255,0)
        
        if player.color == 'green':
            if actual_player == 0 :
                txtcolor = (0, 255, 0)  # green
            else :
                txtcolor = (192, 192, 192)       
        elif player.color == 'blue':
            if actual_player == 1 :
                txtcolor = (0, 0, 255)  # blue
            else :
                txtcolor = (192, 192, 192)    
        elif player.color == 'red':
            if actual_player == 2 :
                txtcolor = (255, 0, 0) # red
            else :
                txtcolor = (192, 192, 192)
        elif player.color == 'gold':
            if actual_player == 3 :
                txtcolor = (255, 255, 0) # yellow
            else :
                txtcolor = (192, 192, 192)    

        #  Player name size depends of player name number of char (dynamic size)
        scaled = self.display.scale_text(playername, (120  * self.ratioX), 100 * self.ratioX)
        font = self.display.get_font(scaled[0])

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
        print('early')
        pass
        """
        self.check = False
        for k, v in enumerate(self.score_joueur):
            if v[0] == actual_player and v[3] == 'False' and v[2] == '0'  :
                joueur = actual_player
                score = 0
                drapeau = 'True' 
                couleur = (0, 0, 0)
                combinaison = v[1]
                self.score_joueur[k] = (joueur, combinaison, score, drapeau, couleur)
                print('k')
                print(k)
                asupp = k + 1
                video = v[1]
        
        ###  supprime la leds dans le choix des combinaisons
        led_a_retirer = asupp
        
        ### supprime la led sellectionnee suivant le joueur    
        if actual_player == 0 :
                self.leds1.remove(led_a_retirer)
        elif actual_player == 1 :
                self.leds2.remove(led_a_retirer)
        elif actual_player == 2 :
                self.leds3.remove(led_a_retirer)
        elif actual_player == 3 :
                self.leds4.remove(led_a_retirer)   
        
                       
        ### lecture video de la combinaison - voir si possible de mettre WAIT
        if self.video :
                self.video_player.play_video(self.display.file_class.get_full_filename(f'yahtzydarts/'+video, 'videos')) 
            
        """

        #return_code = 1
      
        
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
        players[actual_player].darts_thrown += 1
        ### si pas touche un bon chiffre, note 0    
        multi = 1
        for i in range((multi)) :
            if self.des[i] != '' :
                i=i+1
            if self.des[-i] == ''  :
                self.des[-i] = '0'
        self.des.sort(reverse=True)
        if not self.check :
            self.display.play_sound('miss') 

#### transforme la liste self.des en "integer" por checker les combinaisons        
        for k, v in enumerate(self.des):
           if v != '':
              self.des_int[k] = int(self.des[k])
           else : 
              pass     
        
#### SI les 5 des sont joues - active self.check (True)
        if self.des.count('') == 0 :  
            self.display.play_sound('yathzydarts_choix_combinaison')
            self.check = True
          
        if self.check :
                ### classe self.des_int dans l ordre pour faciliter la detection des combinaisons
                self.des_int.sort(reverse = False)
                
                #verifie les combinaisons
                self.check_combinaison(actual_player)



