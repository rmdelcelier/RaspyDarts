# -*- coding: utf-8 -*-
# Game by LaDite !
######

from include import cplayer
from include import cgame

import random
import subprocess
import pygame

# Dictionnay of options - Text format only
OPTIONS = {'theme': 'default', 'xgrille': '8x8', 'colorised': False }
# background image - relative to images folder - Name it like the game itself
GAME_LOGO = 'Othello.png' # background image
# Columns headers - Better as a string
HEADERS = [ "#","PTS" ] # Columns headers - Must be a string
# How many darts per player and per round ? Yes ! this is a feature :)
NB_DARTS = 3 # How many darts per player and per round
# Dictionary of stats and display order (For example : Points Per Darts and avg are displayed in ascending order)
GAME_RECORDS = {'Points Per Round':'DESC'}
VERSION = '1.00'

def check_players_allowed(nb_players):
   """
   Return the player number max for a game.
   """
   return nb_players in (2, 4), VERSION, 4


    
#Extend the basic player
class CPlayerExtended(cplayer.Player):
    def __init__(self, ident, nb_columns, interior=False):
      super().__init__(ident, nb_columns, interior)
      self.segments = []
      # Init Player Records to zero
      for record in GAME_RECORDS:
         self.stats[record] = '0'

# Class of the real game
class Game(cgame.Game):
   def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
      super(Game, self).__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
      # For rpi
      self.rpi = rpi
      self.logo = GAME_LOGO
      self.headers = HEADERS
      self.nb_darts = NB_DARTS
      self.nb_players = nb_players
      self.options = options
      self.game_is_ok_for_color = options['colorised']
      # GameRecords is the dictionnary of stats (see above)
      self.GameRecords = GAME_RECORDS

      self.max_round = 100
      self.fleche = 1
      self.touche = 0
      
      self.segmentsLed = []
      self.grid = []

      self.grille = [
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, -1, 0, 0, 0],
            [0, 0, 0, -1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0]
     
      ]

      self.pos = [
            [[513,93], [626,93], [739,93], [851,93], [963,93], [1076,93], [1189,93], [1302,93]],
            [[513,206], [626,206], [739,206], [851,206], [963,206], [1076,206], [1189,206], [1302,206]],
            [[513,318], [626,318], [739,318], [851,318], [963,318], [1076,318], [1189,318], [1302,318]],
            [[513,430], [626,430], [739,430], [850,429], [962,429], [1076,430], [1189,430], [1302,430]],
            [[513,544], [626,544], [739,544], [850,542], [962,542], [1076,544], [1189,544], [1302,544]],
            [[513,655], [626,655], [739,655], [851,655], [963,655], [1076,655], [1189,655], [1302,655]],
            [[513,768], [626,768], [739,768], [851,768], [963,768], [1076,768], [1189,768], [1302,768]],
            [[513,881], [626,881], [739,881], [851,881], [963,881], [1076,881], [1189,881], [1302,881]]
            ]
      ### variable utilisee pour l affichage des nom, tours, ... A LAISSER
      self.bw = self.display.res['y'] * 5 / 6  
      self.y = self.display.res['y'] / 12      
      self.x = self.display.res['x'] / 2 - self.bw / 2  
      case = self.bw / 7    
      self.jw = self.bw / 8   
      pad = (case - self.jw) / 7   
      #
      #calcul le ratio de l ecran
      self.ratioX = self.display.res['x'] / 1920
      self.ratioY = self.display.res['y'] / 1080
      #calcul de la taille de board
      self.x_board = 510 * self.ratioX
      self.y_board = 156 * self.ratioX
      self.x_echelle_board = 900 * self.ratioX
      self.y_echelle_board = 767 * self.ratioX
      #calcul taille pion 
      self.echelle_pion = 108 * self.ratioX   
      self.taille_pion = 108 
      #calcul taille chiffre
      self.echelle_chiffre = 110 / 1.5
      self.decal_chiffre = 110 * 1.6

      self.win = ""
      self.jeton = 0 
      
      self.leds = []
      self.miss = []
      
      self.DIRECTIONS = [(-1,0),(-1,1),(-1,-1),(0,1),(0,-1),(1,0),(1,1),(1,-1)]
      self.scorej1 = 0
      self.scorej2 = 0
      self.joueur_oppose = 1
      self.taille_grille = int(options['xgrille'][:1]) # grille 8x8
      self.update_grid()
      self.nb_jetons = self.taille_grille * self.taille_grille
#      self.Test_grid() #pour debug 4x4

   def Test_grid(self):
       # defini une grille rempli avec la combinaison à tester
       grid_test = [
            [0, 0, 0, 0],
            [0, 1, 1, 1],
            [1, 1, 1, -1],
            [-1,1, 0, 0],
           ]
       grid_test2 = [
            [-1, -1, 1, 1],
            [-1, 1, -1, 1],
            [-1, 1, -1, 1],
            [-1, 0,  0, 1],
           ]
       self.grille = grid_test2
       self.jeton = 14 #jetons joué
       self.logo = None #pour test fin de partie sans logo (plus joli)
      
   def update_grid(self):
       if self.taille_grille == 6:
           delete_me  = [7,0]
       elif self.taille_grille == 4:
           delete_me = [7,6,1,0]
       else:
           return # 8x8 par defaut
        #Suppression des cases en trop par rapport à 8x8
       for action in delete_me:
           self.grille.pop(action)
           self.pos.pop(action)
       for action in delete_me:
           for line in self.grille:
               line.pop(action)
           for line in self.pos:
               line.pop(action)
 
 
   def pnj(self, players, actual_round, actual_player):
      """
      Intelligence Artificielle (PNJ) niveau intermédiaire pour Othello :
      - Stratégie : Priorité aux coins, maximisation des pions retournés.
      - Gestion des ratés (inprécision) : 20% de chance de dévier sur un voisin de la cible.
      - Gestion des miss : Si le voisin touché n'est pas un coup valide, renvoie 'MISS'.
      """
      # =========================================================================
      # GUIDE DE RÉGLAGE DES NIVEAUX DE DIFFICULTÉ :
      # - Légende des probabilités :
      #   * Taux de choix du meilleur coup : 75% (hésitation : 25%)
      #   * Taux de raté / déviation : 20%
      #   * Répartition des multiplicateurs : 75% Simple (S), 25% Double (D)
      # - Plus fort / précis : Augmenter le taux du meilleur coup, réduire la déviation.
      # - Plus humain / brouillon : Augmenter la déviation et favoriser l'hésitation.
      # =========================================================================
      
      if not self.grid:
          return 'MISS'

      max_idx = self.taille_grille - 1
      corners = [(0, 0), (0, max_idx), (max_idx, 0), (max_idx, max_idx)]

      scored_moves = []
      valid_segments = []

      # Évaluation de chaque coup disponible dans self.grid
      for v in self.grid:
          segment = v[0]
          x, y = v[1], v[2]
          valid_segments.append(segment)
          
          flips = 0
          for direction in self.DIRECTIONS:
              new_x, new_y = x + direction[0], y + direction[1]
              temp_flips = 0
              while self.is_inbound(new_x, new_y) and self.grille[new_x][new_y] == self.joueur_oppose:
                  temp_flips += 1
                  new_x += direction[0]
                  new_y += direction[1]
              if self.is_inbound(new_x, new_y) and self.grille[new_x][new_y] == self.current_player:
                  flips += temp_flips

          score = flips
          if (x, y) in corners:
              score += 50
          
          scored_moves.append((score, segment))

      if not scored_moves:
          return 'MISS'

      scored_moves.sort(key=lambda x: x[0], reverse=True)

      # Choix de la cible (75% le meilleur coup, 25% un autre coup valide pour simuler l'hésitation)
      if random.random() < 0.75 and scored_moves:
          target_segment = scored_moves[0][1]
      else:
          target_segment = random.choice(scored_moves)[1]

      # -------------------------------------------------------------------------
      # GESTION DES RATÉS (VOISINS SUR LA CIBLE) ET DES MISS
      # -------------------------------------------------------------------------
      # Ordre classique des secteurs sur une cible de fléchettes traditionnelle
      dartboard_order = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]
      
      # 20% de chance de faire un raté (imprécision humaine)
      if random.random() < 0.20:
          try:
              idx = dartboard_order.index(int(target_segment))
              # Récupère les deux voisins immédiats sur la cible
              neighbor_left = dartboard_order[idx - 1]
              neighbor_right = dartboard_order[(idx + 1) % len(dartboard_order)]
              
              # Le joueur touche l'un des deux voisins au hasard
              potential_hit = random.choice([neighbor_left, neighbor_right])
              
              # Si le chiffre voisin touché par erreur fait partie des coups valides actuels
              if potential_hit in valid_segments:
                  target_segment = potential_hit
              else:
                  # Sinon, le tir tombe sur une case non jouable ou hors jeu -> MISS
                  return 'MISS'
          except (ValueError, TypeError):
              return 'MISS'

      # Choix du multiplicateur : majoritairement Simple (S) pour assurer le placement, parfois Double (D)
      mult = random.choice(['S', 'S', 'S', 'D'])  # 75% Simple, 25% Double

      return f"{mult}{target_segment}"
 
 
               
   # Actions done before each dart throw - for example, check if the player is allowed to play
   def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        return_code = 0
        
        ###choix des jetons
        if players[actual_player].ident == 0 or players[actual_player].ident == 2 :
            self.current_player = 1
            self.joueur_oppose = -1
        if players[actual_player].ident == 1 or players[actual_player].ident == 3 :
            self.current_player = -1
            self.joueur_oppose = 1
          
        ### calcul le score
        self.score()
             # self.display.play_sound(f'othello_falling',wait_finish = True)
             # pygame.time.delay(1500)
             # return_code = 3 
        
        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                LST = self.check_handicap(players)
            except Exception as e:
                self.logs.Log("ERROR","Handicap failed : {}".format(e))
            for Player in players:
                # Init score
                Player.score = 0

        # Each new player
        if player_launch == 1:
            players[actual_player].segments = ['__','__','__']
            players[actual_player].round_points = 0
            self.save_turn(players)
            players[actual_player].pre_play_score = players[actual_player].score # Backup current score
            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for i in range(0,2):
                players[actual_player].columns.append(['','int'])
                
            self.touche = 0
            
            ### remise a 0 des elements > 1 (chiffres a jouer) dans la grille a chaque debut de tour
            testt = True 
            if testt: 
                RAZ = []
                for i in range(self.taille_grille):
                    for j in range(self.taille_grille):
                        if self.grille[i][j] > 1 :
                            RAZ.append((i,j))
   
                    for line, column in RAZ :
                        self.grille[line][column] = 0
                            
                    testt = False

        ### cherche toutes les positions ou jouer et leurs attribues un chiffre
        print("From pre_dart_check")
        if len(self.win) == 0 : #pas d'égalité ou de gagnant après score()
            self.find_all_valid_moves(check_after_dart = False)
#        self.DrawCase(None,True) #ATTENTION K n'est pas utilisé
#        self.display.update_screen()
        ### test en predart pour gagnant si pas ou plus de position
        if self.win == 'J1' :
            self.winner = 0
            print('gagnant j1 - 150')
            self.display.play_sound(f'othello_win',wait_finish = True)
            return 4
        elif self.win == 'J2' :
            self.winner = 1
            print('gagant j2 - 154')
            self.display.play_sound(f'othello_win',wait_finish = True)
            return 4
        elif self.win == 'egalite' :
            self.winner = None
            print('egalite j1=j2')
            self.display.play_sound(f'othello_win',wait_finish = True)
            return 4

        ### GESTION LEDS ET MISS (pour son miss)
        self.miss = self.leds

        if players[actual_player].ident == 0 or players[actual_player].ident == 2:
            color = "#green"
        else :
            color = "#blue"

        self.rpi.set_target_leds('|'.join(f"{mult}{segment}{color}" for mult in ('S', 'D', 'T') for segment in self.leds))         

        return return_code


   def post_dart_check(self,hit,players,actual_round,actual_player,player_launch):
        return_code = 0
        handler = self.init_handler()
        
        self.show_hit = True
        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].segments[player_launch-1] = hit

        if hit == 'SB' or hit == 'DB' :
            for k,v in enumerate(self.grid):  
                  if v[0] == 'B':
                      print('BULL TOUCHE - condition pour eviter bug base int(10) qd bull touche')
                      #self.display.play_sound('othello_miss')
                      handler['sound'] = 'othello_miss'
                      
        else :
        ### verifie le chiffre touche  
            for k,v in enumerate(self.grid): 
                if v[0] == int(hit[1:]):
                  new_move = [v[1], v[2]]
    
                  if self.is_valid_move(new_move[0], new_move[1]): # si mouvement est valide
                      self.take_move(new_move[0], new_move[1])
                      self.touche += 1
                      self.jeton += 1
                      #self.display.play_sound('othello_hit')
                      handler['sound'] = 'othello_hit'
                      break
                    
        ### si ne touche pas le bon chiffre a jouer
        if str(hit[1:]) not in (self.miss) :    
              #self.display.play_sound('othello_miss')
              handler['sound'] = 'othello_miss'

        ### calcul le score
        self.score()
#        print("from Post_dart_check")
        # on verifie que si on a touché et si pas déjà de gagnant
        if self.touche==1 and len(self.win) == 0 :
            self.find_all_valid_moves(check_after_dart=True) 

        ### test gagnant en postdart
        if self.win == 'J1' :
            self.winner = 0
            print('gagnant j1 - 369')
            self.display.play_sound(f'othello_win',wait_finish = True)
            return 3
        elif self.win == 'J2' :
            self.winner = 1
            print('gagant j2 - 313')
            self.display.play_sound(f'othello_win',wait_finish = True)
        elif self.win == 'egalite' :
            self.winner = None
            print('egalite j2 = j1')
            self.display.play_sound(f'othello_win',wait_finish = True)
            return 3
        

        #passe au joueur suivant qd joueur touche une bonne case + test sur victoire 
        if self.touche == 1 and self.win != 'J1' and self.win != 'J2' :
            return_code = 1
        elif self.touche == 1 and self.win == 'J1':
            self.winner = 0
            return 3
        elif self.touche == 1 and self.win == 'J2' :
            self.winner = 1
            return 3

        # Time for shot or video ?
        handler['take_shot'] = self.time_to_take_shot_or_video(hit)
        handler['return_code'] = return_code
        return handler

        #return return_code


##########
   def score(self) :
      self.scorej1 = 0 
      self.scorej2 = 0
      for ligne in range(self.taille_grille):
          for colonne in range(self.taille_grille):
              if self.grille[ligne][colonne] == 1 :
                  self.scorej1 += 1
              elif self.grille[ligne][colonne] == -1 :
                  self.scorej2 += 1
      
      ### si plus de jeton d une couleur, joueur suivant gagne
      print(f"J1 = {self.scorej1}, J2 = {self.scorej2}")
      if self.scorej1 == 0 :
          self.win = 'J2'
      elif self.scorej2 == 0 :
          self.win = 'J1'
      # test si grille pleine (ne pas prendre self.jeton)
      elif self.scorej1 + self.scorej2 == self.nb_jetons :   ### grille pleine 
          if self.scorej1 > self.scorej2 :
              self.win = 'J1'
          elif self.scorej1 < self.scorej2 :
              self.win = 'J2'
          elif self.scorej1 == self.scorej2 :
              self.win = 'egalite'
            
  
##########      
   def is_inbound(self, x, y):
      # decide whether a tuple in inside the board
      return 0 <= x < int(self.taille_grille) and 0 <= y < int(self.taille_grille)

##########
   def is_valid_move(self, x, y,check = False):
      if self.grille[x][y] > 1 or self.grille[x][y] == 0:
          for direction in self.DIRECTIONS:
              new_x = x + direction[0]
              new_y = y + direction[1]
              
              if self.is_inbound(new_x, new_y) and self.grille[new_x][new_y] == self.joueur_oppose and not check:
                  while self.is_inbound(new_x, new_y) and self.grille[new_x][new_y] == self.joueur_oppose : 
                      new_x = new_x + direction[0]
                      new_y = new_y + direction[1]
                  if self.is_inbound(new_x, new_y) and self.grille[new_x][new_y] == self.current_player:
                      return True
              elif self.is_inbound(new_x, new_y) and self.grille[new_x][new_y] == self.current_player and check:
                  while self.is_inbound(new_x, new_y) and self.grille[new_x][new_y] == self.current_player: 
                      new_x = new_x + direction[0]
                      new_y = new_y + direction[1]
                  if self.is_inbound(new_x, new_y) and self.grille[new_x][new_y] == self.joueur_oppose:
                      return True
          return False
      else:
          return False
      
##########          
   def find_all_valid_moves(self,check_after_dart = False):
      # Trouve tous les mouvements possibles
      '''
      print(f"{self.grille[0]}")
      print(f"{self.grille[1]}")
      print(f"{self.grille[2]}")
      print(f"{self.grille[3]}")
      '''
      #
      valid_moves = []
      for i in range(self.taille_grille):
          for j in range(self.taille_grille):
              if self.is_valid_move(i,j,check_after_dart):
                  valid_moves.append((i,j))

      ### modifie la grille pour ajouter les emplacements des chiffres
      test = 10
      for line, column in valid_moves:
          if not check_after_dart:
              self.grille[line][column] = test
          test += 1
      result_test = test - 10 # si 0 pas de combinaison possible
      '''
      print(f"")
      print(f"***resultat***")
      print(f"{self.grille[0]}")
      print(f"{self.grille[1]}")
      print(f"{self.grille[2]}")
      print(f"{self.grille[3]}")
      '''
      if check_after_dart:
          if result_test == 0:
            if self.current_player == -1 :
              self.win = 'J2'
            else :
              self.win = 'J1'
          return 

      self.grid.clear()
      self.leds.clear()
      hits = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]   ### chiffre 1 retirer volontairement car utiliser par le joueur 1

      if result_test > 0 :
        for i in range (0, result_test) :
            h = random.randint(0, len(hits) - 1)
            self.grid.append((hits[h], valid_moves[i][0], valid_moves[i][1])) # segment,pos ligne, pos colonne  
            self.leds.append(str(hits[h]))   ## gestion des leds
            hits.pop(h)
      elif result_test == 0 :
        ### pas de coup possible, determine le gagnant
        if self.current_player == -1:
          self.win = 'J2'
        else :
          self.win = 'J1'

      return valid_moves    
      
 #######     
   def take_move(self, x, y):
      print(self.is_valid_move)
      if self.is_valid_move(x,y):
          self.grille[x][y] = self.current_player
          pieces_to_reverse = []
          for direction in self.DIRECTIONS:
              new_x, new_y = x + direction[0], y + direction[1]
              temp_list = [] # liste pou stocker toutes les directions possibles
              if self.is_inbound(new_x, new_y) and self.grille[new_x][new_y] == self.joueur_oppose : 
                  while self.is_inbound(new_x, new_y) and self.grille[new_x][new_y] == self.joueur_oppose :  
                      temp_list.append((new_x, new_y))
                      new_x, new_y = new_x + direction[0], new_y + direction[1]
                  if self.is_inbound(new_x, new_y) and self.grille[new_x][new_y] == self.current_player: # valide la direction
                      pieces_to_reverse.extend(temp_list) # interverti la couleur des pieces

          for line, column in pieces_to_reverse:
              self.grille[line][column] = self.current_player

   def miss_button(self, players, actual_player, actual_round, player_launch):
      players[actual_player].segments[player_launch-1] = 'MISS'
      self.display.play_sound('miss')
      players[actual_player].darts_thrown += 1
                
   ###############
   # Method to frefresh player.stat - Adapt to the stats you want. They represent mathematical formulas used to calculate stats. Refreshed after every launch
   def refresh_stats(self, players, actual_round):
      for player in players:
         player.stats['Points Per Round'] = player.show_ppr()

   ###############
   # Set if a message is shown to indicate the segment hitted !
   #
   def display_segment(self):
      return False   


   #################
   # Refresh In-game screen
   #
   def refresh_game_screen(self, Players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player,TxtOnLogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
      # do not show the table scores
      ClickZones = {}

      # Clear
      self.display.screen.fill( (0,0,0) )
      # background image
      if self.taille_grille == 6:
          self.display.display_background('othello/background6.jpg')
      elif self.taille_grille == 4:
          self.display.display_background('othello/background4.jpg')
      else:
          self.display.display_background('othello/background.jpg')
          
      #### ancienne variable -- A GARDER
      bw = self.bw
      y = self.y
      x = self.x
      jw= self.jw

      # show values in grid
      self.DrawCase(None,True)

      #### ancienn variable - A GARDER
      pad = bw/20
      pw = x-pad*2
      
      ### Affiche les segments touches
      self.display.display_image(self.display.file_class.get_full_filename('othello/othello_dartbg', 'images'),pad, self.display.res['y']-pw/4, pw, pw/4, True, False, False)
      self.display.blit_text(Players[actual_player].segments[0],pad, self.display.res['y']-pw/4, pw/3, pw/4, color=(255,255,255))
      self.display.blit_text(Players[actual_player].segments[1],pad+pw/3, self.display.res['y']-pw/4, pw/3, pw/4, color=(255,255,255))
      self.display.blit_text(Players[actual_player].segments[2],pad+pw/3*2, self.display.res['y']-pw/4, pw/3, pw/4, color=(255,255,255))
      
      ### Affiche les nb de tours
      self.display.display_image(self.display.file_class.get_full_filename('othello/othello_turnbg', 'images'),x+bw+pad, self.display.res['y']-pw/4, pw, pw/4, True, False, False)
      self.display.blit_text(str(self.display.lang.translate('round')) +' '+str(actual_round) ,x+bw+pad, self.display.res['y']-pw/4, pw, pw/4, color=(255,255,255))
      
      ### Affiche le nom du joueur 1
      self.display.display_image(self.display.file_class.get_full_filename('othello/othello_name0', 'images'),pad, y, pw,pw/4, True, False, False)
      self.display.blit_text(Players[0].name + ' (' + str(self.scorej1) + ')' ,pad, y, pw,pw/4, color=(255,255,255) if actual_player==0 else (0,0,0) )

      ### Affiche le nom du joueur 2
      if len(Players) > 1:
        self.display.display_image(self.display.file_class.get_full_filename('othello/othello_name1', 'images'),x+bw+pad, y, pw,pw/4, True, False, False)
        self.display.blit_text(Players[1].name + ' (' + str(self.scorej2) + ')' ,x+bw+pad, y, pw,pw/4, color=(255,255,255) if actual_player==1 else(0,0,0))
        
       ### Affiche le nom du joueur 3
      if len(Players) > 2:
        self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_name0', 'images'),pad, y+bw/2, pw,pw/4, True, False, False)
        self.display.blit_text(Players[2].name + ' (' + str(self.scorej1) + ')' ,pad, y+bw/2, pw,pw/4, color=(255,255,255) if actual_player==2 else(0,0,0))
        
      ### Affiche le nom du joueur 4
      if len(Players) > 3:
        self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_name1', 'images'),x+bw+pad, y+bw/2, pw,pw/4, True, False, False)
        self.display.blit_text(Players[3].name + ' (' + str(self.scorej2) + ')' ,x+bw+pad, y+bw/2, pw,pw/4, color=(255,255,255) if actual_player==3 else(0,0,0))
       
      if end_of_game :
          ClickZones = self.display.end_of_game_menu(logo, stat_button=False)

      self.display.update_screen()

      return ClickZones

#######################"
   def DrawCase(self, case, redrawgrid = False) :
      
      ### AFFICHE LES PIONS DES JOUEURS ET LES CHIFFRES A JOUER DANS LA GRILLE
      for ligne in range(len(self.grille)):
        for colonne in range(len(self.grille[ligne])):
          position = self.grille[ligne][colonne]
          if position == 1:
            self.display.display_image(self.display.file_class.get_full_filename(f'othello/pion2', 'images'), int((self.display.res['x'] * (self.pos[ligne][colonne][0] - 0)) /1920), int((self.display.res['y'] * (self.pos[ligne][colonne][1] - 0)) /1080) , self.echelle_pion, self.echelle_pion, True, False, False)
          elif position == -1 :
            self.display.display_image(self.display.file_class.get_full_filename(f'othello/pion1', 'images'), int((self.display.res['x'] * (self.pos[ligne][colonne][0] - 0)) /1920), int((self.display.res['y'] * (self.pos[ligne][colonne][1] - 0)) /1080) , self.echelle_pion, self.echelle_pion, True, False, False)
          ### remplacer par une boucle pour gain de lignes -C'est fait ;)
          elif position >= 10 :
              try:
                  self.display.blit_text(str(self.grid[position - 10][0]), int((self.display.res['x'] * (self.pos[ligne][colonne][0] - 0 - 16)) /1920), int((self.display.res['y'] * (self.pos[ligne][colonne][1] - 0)) /1080) , self.echelle_pion, self.echelle_pion, color=(120,255,120), align='center', valign='center', margin=False)
              except:
                  print(f"Error DrawCase")
                  print(f"grille: {self.grille}, ligne = {ligne}")
                  print(f"grille: colonne {colonne}, position = {position} ")

