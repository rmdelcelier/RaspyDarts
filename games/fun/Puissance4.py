# -*- coding: utf-8 -*-
# Game by LaDite !
######

from include import cplayer
from include import cgame
import random
import subprocess
import pygame
#### TROPHEES
from include import ctrophies


# Dictionnay of options - Text format only
OPTIONS = {'theme': 'default', 'win_points':'2', 'fleche':'2', 'regenere': True}
# background image - relative to images folder - Name it like the game itself
GAME_LOGO = 'Puissance4.png' # background image
# Columns headers - Better as a string
HEADERS = [ "#","PTS" ] # Columns headers - Must be a string
# How many darts per player and per round ? Yes ! this is a feature :)
NB_DARTS = 3 # How many darts per player and per round
# Dictionary of stats and display order (For example : Points Per Darts and avg are displayed in ascending order)
GAME_RECORDS = {'Points Per Round':'DESC'}
VERSION = '1.00'

def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
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
      # GameRecords is the dictionnary of stats (see above)
      self.GameRecords = GAME_RECORDS

      self.max_round = 100
      self.winpoints = int(self.options['win_points'])
      self.fleche = int(self.options['fleche'])
      if self.fleche == 0 :
        self.fleche = 1
      elif self.fleche >= 3 :
        self.fleche = 3
      
      self.touche = 0
      self.regenere = self.options['regenere']
      
      self.segmentsLed = []
      self.grid = []

      self.grille = [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0]
        ]
 
      self.pos = [
            [[639,278], [763,278], [890,278], [1016,278], [1141,278], [1267,278], [1392,278]],
            [[639,404], [763,404], [890,404], [1016,404], [1141,404], [1267,404], [1392,404]],
            [[639,530], [763,530], [890,530], [1016,530], [1141,530], [1267,530], [1392,530]],
            [[639,658], [763,658], [890,658], [1016,658], [1141,658], [1267,658], [1392,658]],
            [[639,785], [763,785], [890,785], [1016,785], [1141,785], [1267,785], [1392,785]],
            [[639,911], [763,911], [890,911], [1016,911], [1141,911], [1267,911], [1392,911]]
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
      self.y_board = 156 * self.ratioY
      self.x_echelle_board = 900 * self.ratioX
      self.y_echelle_board = 767 * self.ratioY
      #calcul taille pion
      self.echelle_pion = 110 * self.ratioX 
      self.taille_pion = 110
      #calcul taille chiffre
      self.echelle_chiffre = 110 / 1.5
      self.decal_chiffre = 110 * 1.6

      self.win = ""
      self.jeton = 0 
      
      self.leds = []
      self.miss = []

   def check_win_condition(self, players):
        """
        Vérifie si la condition de victoire est atteinte.
        - En 2 joueurs : le joueur qui atteint winpoints gagne.
        - En 4 joueurs : l'équipe (0 et 2) ou (1 et 3) gagne.
        Renvoie la liste des indices des joueurs gagnants, ou [] si pas de gagnant.
        """
        if self.nb_players == 2:
            for idx, player in enumerate(players):
                if player.score >= self.winpoints:
                    return [idx]
        elif self.nb_players == 4:
            scoreJ1 = sum(p.score for p in players if p.ident in (0, 2))
            scoreJ2 = sum(p.score for p in players if p.ident in (1, 3))
            
            if scoreJ1 >= self.winpoints:
                return [idx for idx, p in enumerate(players) if p.ident in (0, 2)]
            elif scoreJ2 >= self.winpoints:
                return [idx for idx, p in enumerate(players) if p.ident in (1, 3)]
        return []

   # Actions done before each dart throw - for example, check if the player is allowed to play
   def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        
        handler = self.init_handler()
        return_code = 0

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                LST = self.check_handicap(players)
            except Exception as e:
                self.logs.Log("ERROR","Handicap failed : {}".format(e))
            for Player in players:
                # Init score
                Player.score = 0

            # define the first grid
            self.creategrid()

        if self.jeton == 42 :   ### grille pleine - pas de gagnant
              self.win = ""
              self.jeton = 0
              self.grille = [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0]
        ]
              self.creategrid()
              self.display.play_sound(f'p4_falling',wait_finish = True)
        ### mettre message grille pleine
              pygame.time.delay(1500)
              return_code = 1 
                
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
                
            if self.regenere and (players[actual_player].ident == 0 or players[actual_player].ident == 2):
                self.creategrid()
                 
            self.touche = 0
        
        ### GESTION LEDS ET MISS (pour son miss)
        self.leds = []
        self.miss = []
        if players[actual_player].ident == 0 or players[actual_player].ident == 2:
            color = "#green"
        else :
            color = "#blue"
        
        ### ajoute les chiffres a la liste des leds si ligne 0 de self.grille est egale a 0 + creation liste 'miss' pour son     
        if self.grille[0][0] == 0 :  #col 1
            self.leds.append(str(self.grid[0][0])+color)
            self.miss.append(str(self.grid[0][0]))
        if self.grille[0][1] == 0 :  #col 2
            self.leds.append(str(self.grid[1][0])+color)
            self.miss.append(str(self.grid[1][0]))
        if self.grille[0][2] == 0 :  #col 3
            self.leds.append(str(self.grid[2][0])+color)
            self.miss.append(str(self.grid[2][0]))
        if self.grille[0][4] == 0 :  #col 5
            self.leds.append(str(self.grid[4][0])+color)
            self.miss.append(str(self.grid[4][0]))
        if self.grille[0][5] == 0 :  #col 6
            self.leds.append(str(self.grid[5][0])+color)
            self.miss.append(str(self.grid[5][0]))
        if self.grille[0][6] == 0 :  #col 7
            self.leds.append(str(self.grid[6][0])+color)   
            self.miss.append(str(self.grid[6][0]))
        if self.grille[0][3] == 0 : ### col bull
            self.leds.append(str(self.grid[3][0])+color) 
            self.miss.append(str(self.grid[3][0])) 
 
        self.rpi.set_target_leds('|'.join(f"{mult}{segment}" for mult in ('S', 'D', 'T') for segment in self.leds))         
        
     
        # test for a winner
        winners_indices = self.check_win_condition(players)
        if winners_indices:
            self.winner = winners_indices[0]
            if self.nb_players == 2:
                ctrophies.check_game_end_stats(players, players[winners_indices[0]].name, "PUISSANCE4")
            else:
                winning_names = [players[idx].name for idx in winners_indices]
                ctrophies.check_team_game_end_stats(players, winning_names, "PUISSANCE4")
            return_code = 3
                
        handler['return_code'] = return_code
        return handler

   def pnj_score(self, players, actual_player, level, player_launch):
      """
      Intelligence Artificielle (PNJ) pour le Puissance 4 :
      - Analyse globale (Horizontal, Vertical, Diagonales).
      - Table standardisée des 5 niveaux [Précis, Voisin, Raté/Miss].
      - Utilisation de la vraie matrice physique de la cible de fléchettes pour les voisins (ex: 20 -> 1 ou 5).
      """
      # =========================================================================
      # GUIDE DE RÉGLAGE DES NIVEAUX DE DIFFICULTÉ :
      # - Légende des niveaux : [p_exact, p_neighbor, p_miss]
      #   * p_exact    : Probabilité de toucher exactement la cible calculée (%)
      #   * p_neighbor : Probabilité de dévier vers un secteur voisin via la matrice (%)
      #   * p_miss     : Probabilité de rater complètement (retourne 'MISS') (%)
      # - Plus fort / précis : Augmenter p_exact, réduire p_neighbor et p_miss.
      # - Plus humain / brouillon : Augmenter p_miss et p_neighbor, réduire p_exact.
      # =========================================================================

      levels = [
          [20, 40, 40],  # Niveau 1 (Noob)
          [35, 45, 20],  # Niveau 2 (Débutant)
          [55, 35, 10],  # Niveau 3 (Intermédiaire)
          [75, 20,  5],  # Niveau 4 (Pro)
          [90, 10,  0]   # Niveau 5 (Expert)
      ]
      
      try:
          comp_lvl = int(level)
      except (ValueError, TypeError):
          comp_lvl = 3

      lvl_idx = max(0, min(comp_lvl - 1, len(levels) - 1))
      p_exact = levels[lvl_idx][0]
      p_neighbor = levels[lvl_idx][1]

      player_ident = players[actual_player].ident
      if player_ident in (0, 2):
          my_val = 1
          opp_val = -1
      else:
          my_val = -1
          opp_val = 1

      playable_cols = []
      for col in range(7):
          if self.grille[0][col] == 0:
              playable_cols.append(col)

      if not playable_cols:
          return 'MISS'

      col_to_segment = {}
      segment_to_col = {}
      for item in self.grid:
          seg, col = item[0], item[1]
          col_to_segment[col] = seg
          segment_to_col[seg] = col

      def simulate(grille_state, col, val):
          for r in range(5, -1, -1):
              if grille_state[r][col] == 0:
                  new_g = [row[:] for row in grille_state]
                  new_g[r][col] = val
                  return new_g, r
          return None, None

      def check_win(grille_state, val):
          for r in range(6):
              for c in range(4):
                  if grille_state[r][c] == val and grille_state[r][c+1] == val and grille_state[r][c+2] == val and grille_state[r][c+3] == val:
                      return True
          for r in range(3):
              for c in range(7):
                  if grille_state[r][c] == val and grille_state[r+1][c] == val and grille_state[r+2][c] == val and grille_state[r+3][c] == val:
                      return True
          for r in range(3):
              for c in range(4):
                  if grille_state[r][c] == val and grille_state[r+1][c+1] == val and grille_state[r+2][c+2] == val and grille_state[r+3][c+3] == val:
                      return True
          for r in range(3):
              for c in range(3, 7):
                  if grille_state[r][c] == val and grille_state[r+1][c-1] == val and grille_state[r+2][c-2] == val and grille_state[r+3][c-3] == val:
                      return True
          return False

      def evaluate_grid(grille_state, me, opp):
          score = 0
          def score_window(window):
              s = 0
              m = window.count(me)
              o = window.count(opp)
              e = window.count(0)
              if m > 0 and o > 0:
                  return 0
              if m == 3 and e == 1:
                  s += 200
              elif m == 2 and e == 2:
                  s += 20
              elif m == 1 and e == 3:
                  s += 2
              if o == 3 and e == 1:
                  s -= 150
              elif o == 2 and e == 2:
                  s -= 15
              return s

          for r in range(6):
              for c in range(4):
                  score += score_window([grille_state[r][c+i] for i in range(4)])
          for r in range(3):
              for c in range(7):
                  score += score_window([grille_state[r+i][c] for i in range(4)])
          for r in range(3):
              for c in range(4):
                  score += score_window([grille_state[r+i][c+i] for i in range(4)])
          for r in range(3):
              for c in range(3, 7):
                  score += score_window([grille_state[r+i][c-i] for i in range(4)])
          return score

      scored_moves = []
      for col in playable_cols:
          if col not in col_to_segment:
              continue
          seg = col_to_segment[col]
          score = 0

          new_g_self, _ = simulate(self.grille, col, my_val)
          if new_g_self and check_win(new_g_self, my_val):
              score += 100000

          new_g_opp, _ = simulate(self.grille, col, opp_val)
          if new_g_opp and check_win(new_g_opp, opp_val):
              score += 50000

          if new_g_self:
              score += evaluate_grid(new_g_self, my_val, opp_val)

          distance_center = abs(col - 3)
          if seg == "B":
              score -= 70
          else:
              score += (3 - distance_center) * 15

          scored_moves.append((score, col, seg))

      if not scored_moves:
          return 'MISS'

      scored_moves.sort(key=lambda x: x[0], reverse=True)
      best_target = scored_moves[0][2]

      dartboard_neighbors = {
          20: [1, 5],   1: [20, 18], 18: [1, 4],   4: [18, 13], 13: [4, 6],
          6: [13, 10], 10: [6, 15],  15: [10, 2],  2: [15, 17], 17: [2, 3],
          3: [17, 19], 19: [3, 7],   7: [19, 16], 16: [7, 8],   8: [16, 11],
          11: [8, 14], 14: [11, 9],  9: [14, 12], 12: [9, 5],   5: [12, 20]
      }
      valid_segments = list(segment_to_col.keys())
      roll = random.randint(1, 100)

      if roll <= p_exact:
          target_segment = best_target
      elif roll <= p_exact + p_neighbor:
          try:
              target_int = int(best_target)
          except (ValueError, TypeError):
              target_int = None

          if target_int in dartboard_neighbors:
              neighbors = dartboard_neighbors[target_int]
              valid_neighbors = [
                  n for n in neighbors 
                  if n in valid_segments and self.grille[0][segment_to_col[n]] == 0
              ]
              if valid_neighbors:
                  target_segment = random.choice(valid_neighbors)
              else:
                  return 'MISS'
          else:
              return 'MISS'
      else:
          return 'MISS'

      if target_segment == "B":
          mult = random.choice(['SB', 'DB'])
          return f"{mult}"
      else:
          mult = random.choice(['S', 'S', 'S', 'D'])
          return f"{mult}{target_segment}"


   def post_dart_check(self,hit,players,actual_round,actual_player,player_launch):
        return_code = 0
        handler = self.init_handler()
        self.show_hit = True

        players[actual_player].darts_thrown += 1
        players[actual_player].segments[player_launch-1] = hit
        
        # On vérifie les trophées de volée uniquement à la 3ème fléchette
        if player_launch == 3:
            round_darts = players[actual_player].darts[-3:]
            ctrophies.check_and_unlock_trophies(players[actual_player], round_darts)
        
        ### TROPHEES
        ctrophies.process_single_dart(players[actual_player], hit)

        if hit == 'SB' or hit == 'DB' :
              for k,v in enumerate(self.grid):  
                  if v[0] == 'B':
                    self.touche += 1
                    colonne = 3     
                    ligne = 5  
                    stop = False
                    while ligne >= 0 and stop == False:
                      if self.grille[ligne][colonne] == 0:
                        if players[actual_player].ident in (0, 2):
                          self.grille[ligne][colonne] = 1
                          self.jeton += 1
                          handler['sound'] = 'p4_hit'
                          stop = True
                        elif players[actual_player].ident in (1, 3):
                          self.grille[ligne][colonne] = -1
                          self.jeton += 1
                          handler['sound'] = 'p4_hit'
                          stop = True
                      ligne = ligne - 1 

        else :            
              for k,v in enumerate(self.grid): 
                  if v[0] == int(hit[1:]):
                    self.touche += 1
                    colonne = v[1]    
                    ligne = 5  
                    stop = False
                    while ligne >= 0 and stop == False:
                      if self.grille[ligne][colonne] == 0:
                        if players[actual_player].ident in (0, 2):
                          self.grille[ligne][colonne] = 1
                          self.jeton += 1
                          handler['sound'] = 'p4_hit'
                          stop = True
                        elif players[actual_player].ident in (1, 3) :
                          self.grille[ligne][colonne] = -1
                          self.jeton += 1
                          handler['sound'] = 'p4_hit'
                          stop = True
                      ligne = ligne - 1 
        
        if str(hit[1:]) not in (self.miss) :    
              handler['sound'] = 'p4_miss'
              
        self.verif_horiz()
        self.verif_vert()
        self.verif_diag()
        self.DrawCase(k, True)
        self.display.update_screen()


        # si ligne gagnante - ajoute point et nouvelle grille
        if self.win != "" :
              players[actual_player].score += 1
              self.win = ""
              self.jeton = 0
              self.display.play_sound(f'p4_win',wait_finish = True)
              
              winners_indices = self.check_win_condition(players)
              if winners_indices:
                  self.winner = winners_indices[0]
                  if self.nb_players == 2:
                      ctrophies.check_game_end_stats(players, players[winners_indices[0]].name, "PUISSANCE4")
                  else:
                      winning_names = [players[idx].name for idx in winners_indices]
                      ctrophies.check_team_game_end_stats(players, winning_names, "PUISSANCE4")
                  return_code = 3
              else:
                  self.grille = [[0]*7 for _ in range(6)]
                  self.creategrid()
                  self.display.play_sound(f'p4_falling', wait_finish = True)
                  return_code = 1 
 
        # test for a winner standard
        if return_code != 3:
            winners_indices = self.check_win_condition(players)
            if winners_indices:
                self.winner = winners_indices[0]
                if self.nb_players == 2:
                    ctrophies.check_game_end_stats(players, players[winners_indices[0]].name, "PUISSANCE4")
                else:
                    winning_names = [players[idx].name for idx in winners_indices]
                    ctrophies.check_team_game_end_stats(players, winning_names, "PUISSANCE4")
                return_code = 3

        if return_code != 3:
            if self.fleche == 1 and self.touche == 1 :
                return_code = 1
            elif self.fleche == 2 and self.touche == 2 :
                return_code = 1

        handler['take_shot'] = self.time_to_take_shot_or_video(hit)
        handler['return_code'] = return_code
        return handler

   def creategrid(self):
      self.grid.clear()
      hits = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
      for i in range (0, 6) :
         h = random.randint(0, len(hits) - 1)
         if i < 3 :
           self.grid.append((hits[h], i))  
           hits.pop(h)
         if i >= 3 :
           self.grid.append((hits[h], i+1))   
           hits.pop(h)
      self.grid.insert(3, ("B", 3))

   def refresh_stats(self, players, actual_round):
      for player in players:
         player.stats['Points Per Round'] = player.show_ppr()

   def display_segment(self):
      return False   

   def verif_horiz(self):
      ligne = 5
      stop = False
      while ligne >= 0 and stop == False:
          for colonne in range(4):  
              if self.grille[ligne][colonne] + self.grille[ligne][colonne + 1] + self.grille[ligne][colonne + 2] + self.grille[ligne][colonne + 3] == 4:  
                  self.win = "jaune"
                  stop = True
              if self.grille[ligne][colonne] + self.grille[ligne][colonne + 1] + self.grille[ligne][colonne + 2] + self.grille[ligne][colonne + 3] == -4: 
                  self.win = "rouge"
                  stop = True
          ligne = ligne - 1

   def verif_vert(self):
      for colonne in range(7) :
          for ligne in range(5, 2, -1):
              if self.grille[ligne][colonne] + self.grille[ligne - 1][colonne] + self.grille[ligne - 2][colonne] + self.grille[ligne - 3][colonne] == 4:
                  self.win = "jaune"
              if self.grille[ligne][colonne] + self.grille[ligne - 1][colonne] + self.grille[ligne - 2][colonne] + self.grille[ligne - 3][colonne] == -4:
                  self.win = "rouge"

   def verif_diag(self) :
      for ligne in range(3):
          for colonne in range(4):
              if self.grille[ligne][colonne] + self.grille[ligne + 1][colonne + 1] + self.grille[ligne + 2][colonne + 2] + self.grille[ligne + 3][colonne + 3] == 4:
                  self.win = "jaune"
              if self.grille[ligne][colonne] + self.grille[ligne + 1][colonne + 1] + self.grille[ligne + 2][colonne + 2] + self.grille[ligne + 3][colonne + 3] == -4:
                  self.win = "rouge"
      
      for ligne in range(3): 
          for colonne in range(3, 7): 
              if self.grille[ligne][colonne] + self.grille[ligne + 1][colonne - 1] + self.grille[ligne + 2][colonne - 2] + self.grille[ligne + 3][colonne - 3] == 4:
                  self.win = "jaune"
              if self.grille[ligne][colonne] + self.grille[ligne + 1][colonne - 1] + self.grille[ligne + 2][colonne - 2] + self.grille[ligne + 3][colonne - 3] == -4:
                  self.win = "rouge"

   def miss_button(self, players, actual_player, actual_round, player_launch):
      players[actual_player].segments[player_launch-1] = 'MISS'
      self.display.play_sound('miss')

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
        
   def refresh_game_screen(self, Players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player,TxtOnLogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
      ClickZones = {}

      self.display.screen.fill( (0,0,0) )
      self.display.display_background('puissance4/background.jpg')

      bw = self.bw
      y = self.y
      x = self.x
      jw= self.jw

      self.display.display_image(self.display.file_class.get_full_filename('puissance4/p4_board_back', 'images'), self.x_board, self.y_board, self.x_echelle_board, self.y_echelle_board, True, False, False)

      for k,v in enumerate(self.grid ):
         self.DrawCase(k)

      self.display.display_image(self.display.file_class.get_full_filename('puissance4/p4_board', 'images'), self.x_board, self.y_board, self.x_echelle_board, self.y_echelle_board, True, False, False)

      pad = bw/20
      pw = x-pad*2
      
      self.display.display_image(self.display.file_class.get_full_filename('puissance4/p4_dartbg', 'images'),pad, self.display.res['y']-pw/4, pw, pw/4, True, False, False)
      self.display.blit_text(Players[actual_player].segments[0],pad, self.display.res['y']-pw/4, pw/3, pw/4, color=(255,255,255))
      self.display.blit_text(Players[actual_player].segments[1],pad+pw/3, self.display.res['y']-pw/4, pw/3, pw/4, color=(255,255,255))
      self.display.blit_text(Players[actual_player].segments[2],pad+pw/3*2, self.display.res['y']-pw/4, pw/3, pw/4, color=(255,255,255))
      
      self.display.display_image(self.display.file_class.get_full_filename('puissance4/p4_turnbg', 'images'),x+bw+pad, self.display.res['y']-pw/4, pw, pw/4, True, False, False)
      self.display.blit_text(str(self.display.lang.translate('round')) +' '+str(actual_round) ,x+bw+pad, self.display.res['y']-pw/4, pw, pw/4, color=(255,255,255))
      
      self.display.display_image(self.display.file_class.get_full_filename('puissance4/p4_name0', 'images'),pad, y, pw,pw/4, True, False, False)
      self.display.blit_text(Players[0].name,pad, y, pw,pw/4, color=(255,255,255) if actual_player==0 else (0,0,0) )
      self.display.blit_text(str(Players[0].score),pad+pw*3/4, y+pw/4, pw/4,pw/4, color=(255,255,255) if actual_player==0 else (0,255,255) )
      
      if len(Players) > 1:
        self.display.display_image(self.display.file_class.get_full_filename('puissance4/p4_name1', 'images'),x+bw+pad, y, pw,pw/4, True, False, False)
        self.display.blit_text(Players[1].name,x+bw+pad, y, pw,pw/4, color=(255,255,255) if actual_player==1 else(0,0,0))
        self.display.blit_text(str(Players[1].score),x+bw+pad+pw*3/4,y+pw/4, pw/4,pw/4, color=(255,255,255) if actual_player==1 else(0,255,255))
      
      if len(Players) > 2:
        self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_name0', 'images'),pad, y+bw/2, pw,pw/4, True, False, False)
        self.display.blit_text(Players[2].name,pad, y+bw/2, pw,pw/4, color=(255,255,255) if actual_player==2 else(0,0,0))
        self.display.blit_text(str(Players[2].score),pad+pw*3/4, y+bw/2+pw/4 , pw/4,pw/4, color=(255,255,255) if actual_player==2 else (0,255,255) )
      
      if len(Players) > 3:
        self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_name1', 'images'),x+bw+pad, y+bw/2, pw,pw/4, True, False, False)
        self.display.blit_text(Players[3].name,x+bw+pad, y+bw/2, pw,pw/4, color=(255,255,255) if actual_player==3 else(0,0,0))
        self.display.blit_text(str(Players[3].score),x+bw+pad+pw*3/4, y+bw/2+pw/4, pw/4,pw/4, color=(255,255,255) if actual_player==3 else(0,255,255))
 
      if end_of_game :
          ClickZones = self.display.end_of_game_menu(logo, stat_button=False)
          return ClickZones

      self.display.update_screen()
      return ClickZones

   def DrawCase(self, case, redrawgrid = False) :
      for ligne in range(len(self.grille)):
        for colonne in range(len(self.grille[ligne])):
          if self.grille[ligne][colonne] == 1:
            self.display.display_image(self.display.file_class.get_full_filename(f'puissance4/pion_1', 'images'), int((self.display.res['x'] * (self.pos[ligne][colonne][0] - self.taille_pion)) /1920), int((self.display.res['y'] * (self.pos[ligne][colonne][1] - self.taille_pion)) /1080) , self.echelle_pion, self.echelle_pion, True, False, False)
          elif self.grille[ligne][colonne] == -1 :
            self.display.display_image(self.display.file_class.get_full_filename(f'puissance4/pion_2', 'images'), int((self.display.res['x'] * (self.pos[ligne][colonne][0] - self.taille_pion)) /1920), int((self.display.res['y'] * (self.pos[ligne][colonne][1] - self.taille_pion)) /1080) , self.echelle_pion, self.echelle_pion, True, False, False)
            
      self.display.blit_text(str(self.grid[0][0]), int((self.display.res['x']*(679-self.decal_chiffre) /1920)), self.y_board - self.echelle_chiffre , self.echelle_pion, self.echelle_pion, color=(255,255,255), align='center', valign='center', margin=False)
      self.display.blit_text(str(self.grid[1][0]), int((self.display.res['x']*(803-self.decal_chiffre) /1920)), self.y_board - self.echelle_chiffre  , self.echelle_pion, self.echelle_pion, color=(255,255,255), align='center', valign='center', margin=False)
      self.display.blit_text(str(self.grid[2][0]), int((self.display.res['x']*(930-self.decal_chiffre) /1920)), self.y_board - self.echelle_chiffre  , self.echelle_pion, self.echelle_pion, color=(255,255,255), align='center', valign='center', margin=False)
      self.display.blit_text(str(self.grid[3][0]), int((self.display.res['x']*(1046-self.decal_chiffre) /1920)), self.y_board - self.echelle_chiffre  , self.echelle_pion, self.echelle_pion, color=(255,255,255), align='center', valign='center', margin=False)
      self.display.blit_text(str(self.grid[4][0]), int((self.display.res['x']*(1181-self.decal_chiffre) /1920)), self.y_board - self.echelle_chiffre  , self.echelle_pion, self.echelle_pion, color=(255,255,255), align='center', valign='center', margin=False)
      self.display.blit_text(str(self.grid[5][0]), int((self.display.res['x']*(1307-self.decal_chiffre) /1920)), self.y_board - self.echelle_chiffre  , self.echelle_pion, self.echelle_pion, color=(255,255,255), align='center', valign='center', margin=False)
      self.display.blit_text(str(self.grid[6][0]), int((self.display.res['x']*(1432-self.decal_chiffre) /1920)), self.y_board - self.echelle_chiffre  , self.echelle_pion, self.echelle_pion, color=(255,255,255), align='center', valign='center', margin=False)

      if redrawgrid :
        self.display.display_image(self.display.file_class.get_full_filename('puissance4/p4_board', 'images'), self.x_board, self.y_board, self.x_echelle_board, self.y_echelle_board, True, False, False)
