# -*- coding: utf-8 -*-
'''
Game by LaDite base sur le jeu round the clock de olivierr lu
'''

import random
import pygame
from include import cplayer
from include import cgame

#
LOGO = 'Bob27' # Background image - relative to images folder
HEADERS = ['HIT', '-', '-', '-', '-', '-', '-'] # Columns headers - Must be a string
OPTIONS = {'theme': 'default', 'max_round': 21, 'Bull': True, 'Numbers': True} # Dictionnay of options
NB_DARTS = 3
GAME_RECORDS = {'Score': 'DESC', 'Reached Score': 'DESC', 'Hits': 'DESC'}
VERSION = '1.03'

def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
    """
    return nb_players >= 1 and nb_players <= 12, VERSION, 12
    
class CPlayerExtended(cplayer.Player):
    '''
    Extended Player class
    '''
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        #The score the player has to hit
        self.actual_hit = 1
        self.goals = []
        # Init Player Records to zero
        for game_record in GAME_RECORDS:
            self.stats[game_record] = '0'

class Game(cgame.Game):
    '''
    Round the clock game class
    '''
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.logo = LOGO
        self.headers = HEADERS
        self.game_records = GAME_RECORDS
        self.nb_darts = NB_DARTS
        self.options = options
        self.nb_players = nb_players
        #  Get the maxiumum round number
        # For rpi
        self.rpi = rpi
        self.dmd = dmd

        self.max_round = int(options['max_round'])
        self.bull = options['Bull']
        self.order = not(options['Numbers'])

        self.m_list = []
        ### compteur nb de touche (ratee ou touchee)
        self.nb_touche = 0
        ### compteur nb touche (touche)
        self.nb_touche_ok = 0
        self.current_round_hits = ['', '', '']

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        '''
        After eah row : valid launch ? winner ? ...
        '''
        handler = self.init_handler()
        self.infos = ''

        goal = players[actual_player].goals[actual_round - 1]
        score = self.score_map.get(hit)
        final_check = True
        check = True

        self.current_round_hits[player_launch - 1] = hit

        # Détermination de la cible attendue (Double du chiffre ou DB pour le Bull)
        target_hit = 'DB' if str(goal) == '50' else f'D{goal}'

        self.nb_touche += 1
        if hit == target_hit:
            self.infos += f"Player {actual_player}, your score was {players[actual_player].score}{self.lf}"
            players[actual_player].increment_hits(hit)
            players[actual_player].score += score

            self.display.sound_for_touch(hit)
            self.nb_touche_ok += 1
        else:
            check = False
            if self.nb_touche == 3:
                if self.nb_touche_ok == 0:
                    self.infos += f'le bon chiffre n a pas ete touche{self.lf}'
                    # Pénalité : valeur du double raté
                    if str(goal) == '50':
                        score = -50
                    else:
                        score = -2 * int(goal)
                    final_check = False

                    # Delete from goals
                    players[actual_player].score += score
                else:
                    self.infos += f'le bon chiffre a ete touche au moins 1x{self.lf}'

            handler['sound'] = 'plouf'

        players[actual_player].add_dart(actual_round, player_launch, hit, score=score, check=check, final_check=final_check)

        if players[actual_player].score <= 0:
            players[actual_player].score = 0
            players[actual_player].alive = False

            #Someone is dead, is ther a winner ?
            self.winner = self.check_winner(players, last_round=False)
            if self.winner > -1:
                self.infos += "Here is a winner"
                handler['return_code'] = 3
            if len(players) == 1:
                handler['return_code'] = 2

        # Last round
        if actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and player_launch == int(self.nb_darts) and handler['return_code'] == 0:
            self.infos += rf"\n/!\ Last round reached ({actual_round})\n"
            self.winner = self.check_winner(players, last_round=True)
            if self.winner != -1:
                self.infos += "Here is a winner"
                handler['return_code'] = 3
            else:
                self.infos += "No winner"
                handler['return_code'] = 2

        # Update Score, darts count and Max score possible
        players[actual_player].columns[0] = (f'{players[actual_player].actual_hit}', 'str')

        # You may want to count darts played
        players[actual_player].darts_thrown += 1

        # It is recommanded to update stats every dart thrown
        self.refresh_stats(players, actual_round)

        self.logs.debug(self.infos)

        # Time for shot or video ?
        handler['take_shot'] = self.time_to_take_shot_or_video(hit)

        return handler


    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        '''
        Before each throw - update screen, display score, etc...
        '''
        self.infos = ''
        self.actual_round = actual_round

        ### PASSE LE JOUEUR AYANT UN SCORE A 0 OU INFERIEUR
        if not players[actual_player].alive:
            self.logs.debug(f'Le joueur {actual_player} est éliminé. Il passe son tour')
            return 4

        players[actual_player].columns[3] = (f'{self.nb_touche}', 'str')

        # First round, first player, first dart
        if player_launch == 1 and actual_round == 1 and actual_player == 0:
            for player in players:
                if self.order:
                    player.goals = [target for target in self.target_order]
                else:
                    player.goals = [str(num) for num in range(1, 21)]
                if self.bull:
                    player.goals.append('50')
                player.score = 27
                player.alive = True
                player.columns[0] = (f'{player.goals[0]}', 'str')
                player.reset_rounds(self.max_round)

        if player_launch == 1:
            players[actual_player].reset_darts()
            self.nb_touche = 0
            self.nb_touche_ok = 0
            self.current_round_hits = ['', '', '']

        # Update Score & Actual Hit for AI and screen
        current_goal = players[actual_player].goals[actual_round - 1]
        players[actual_player].columns[0] = (f'{current_goal}', 'str')
        players[actual_player].actual_hit = current_goal

        # Return LED target (DB for bull, D{goal} for others)
        led_target = 'DB' if str(current_goal) == '50' else f'D{current_goal}'
        self.rpi.set_target_leds(f'{led_target}#{self.colors[0]}')

        # For further code cleaning
        return None

    def pnj_score(self, players, actual_player, computer_level, player_launch):
        '''
        Compute PNJ Score according to computer level
        '''
        # =========================================================================
        # GUIDE DE RÉGLAGE DES NIVEAUX DE DIFFICULTÉ :
        # - Légende : [Taux de miss (%), Taux de réussite/précision de la cible (%), Taux Double (%), Taux Triple (%), Taux Voisins/Déviation (%)]
        # - Plus fort / précis : Diminuer le MISS et la déviation, augmenter la précision et les triples/doubles.
        # - Plus humain / brouillon : Augmenter le MISS et la déviation, baisser les taux de triples et doubles.
        # =========================================================================
        levels = [
            [25, 15, 12, 16, 50],  # 1 : Noob
            [15, 25, 12, 16, 50],  # 2 : Débutant
            [ 1, 55, 30, 40, 80],  # 3 : Intermédiaire
            [ 0, 99, 30, 98, 99],  # 4 : Pro
            [ 0, 99, 30, 98, 99]   # 5 : Expert
        ]

        if random.randint(0, 100) < levels[computer_level - 1][0]:
            return 'MISSDART'

        target = players[actual_player].actual_hit
        
        if random.randint(0, 100) < levels[computer_level - 1][1]:
            segment = target
        elif target != '50' and str(target) in self.neighbors and random.randint(0, 100) < levels[computer_level - 1][4]:
            segment = self.neighbors[str(target)][random.randint(0, 1)]
        else:
            segment = random.randint(1, 20) if target != '50' else '50'

        mult = random.randrange(100)
        if segment != '50' and segment != 'B':
            dbl_rate = levels[computer_level - 1][2]
            tpl_rate = levels[computer_level - 1][3]
            
            if mult < dbl_rate:
                score = f'D{segment}'
            elif mult < dbl_rate + tpl_rate:
                score = f'T{segment}'
            else:
                score = f'S{segment}'
        else:
            if mult < levels[computer_level - 1][3]:
                score = 'DB'
            else:
                score = 'SB'

        return score


    def check_winner(self, players, last_round=False):
        '''
        Last round (or not) : who is the winner ?
        Last alive player
        or
        best score at last round
        '''
        nb_alive = 0
        last_alive = -1
        for player in players:
            if player.alive:
                nb_alive += 1
                last_alive = player.ident

        if nb_alive == 1:
            return last_alive
        if not last_round:
            return -1

        deuce = False
        best_score = -1
        best_player = -1
        for player in players:
            if player.score > best_score:
                best_score = player.score
                deuce = False #necessary to reset deuce if there is a deuce with a higher score !
                best_player = player.ident
            elif player.score == best_score:
                deuce = True
                best_player = -1

        return best_player

    def miss_button(self, players, actual_player, actual_round, player_launch):
        '''
        When missed button pressed
        '''
        self.logs.debug(f"MissButtonPressed : {player_launch}")
        players[actual_player].darts_thrown += 1
        self.display.play_sound('miss')

        self.current_round_hits[player_launch - 1] = 'MISSDART'

        # Refresh stats
        if self.nb_touche_ok > 0:
            final_check = True
        else:
            final_check = False

        goal = players[actual_player].goals[actual_round - 1]
        if player_launch == 3 and not final_check:
            if str(goal) == '50':
                score = -50
            else:
                score = -2 * int(goal)
        else:
            score = 0

        players[actual_player].add_dart(actual_round, player_launch, 'MISSDART', score=score, check=False, final_check=final_check)

    def early_player_button(self, players, actual_player, actual_round):
        '''
        Pushed Player Early
        '''

        goal = players[actual_player].goals[actual_round - 1]
        if self.nb_touche_ok == 0:
            if str(goal) == '50':
                score = -50
            else:
                score = -2 * int(goal)
        else:
            score = 0

        players[actual_player].score += score

        if players[actual_player].score <= 0:
            players[actual_player].score = 0
            players[actual_player].alive = False

        return_code = 1

        self.winner = self.check_winner(players, last_round=False)

        if self.winner != -1:
            self.infos += rf"Current winner is Player {self.winner}"
            return_code = 3
        elif actual_round == self.max_round and actual_player == self.nb_players - 1:
            self.winner = self.check_winner(players)
            if self.winner != -1:
                self.infos += rf"Current winner is Player {self.winner}"
                return_code = 3
            else:
                return_code = 2
        return return_code


    def refresh_stats(self, players, actual_round):
        '''
        Method to refresh players' stats
        '''
        for player in players:
            player.stats['Score'] = player.score
            player.stats['Reached Score'] = player.actual_hit
            player.stats['Hits'] = player.get_total_hit()

    def display_score(self, score, score_x, score_y, score_w, score_h):
        '''
        Display players's score
        '''
        font = self.display.defaultfontpath

        # Score
        if score is not None:
            self.display.blit_text(f"{score}", score_x, score_y, score_w, score_h, color=self.display.colorset['bob27-text'], align='Center', valign='Top', margin=False)
        self.display.blit_text("bob27-yourscore", score_x, score_y + score_h, score_w, int(score_h / 3), color=self.display.colorset['bob27-text'], valign='Top')

        return (score_x, score_w, score_h, score_y)

    def compute_states(self, nb_hits, nb_miss):

        if nb_miss == 3:
            return [None, None, None, True]

        if nb_hits > 0:
            stateM = None
        else:
            stateM = False

        if nb_hits == 1:
            state1 = True
        elif nb_hits > 1:
            state1 = None
        else:
            state1 = False

        if nb_hits == 2:
            state2 = True
        elif nb_hits > 2 or nb_miss > 1:
            state2 = None
        elif nb_miss < 2:
            state2 = False

        if nb_hits == 3:
            state3 = True
        elif nb_miss == 0:
            state3 = False
        else:
            state3 = None

        return [state1, state2, state3, stateM]

    def draw_hit(self, hit, state, rectangle, dart_hit=''):
        '''
        Draw one rectangle
        State could be :
            None : no rectangle
            False : inactive
            True : active
        '''

        color = None

        if hit > 1:
            text = f'{hit} hits'
        else:
            text = '1 hit'

        if hit == 4:
            text = self.display.lang.translate('miss')
            # Miss
            if state is False:
                color = self.display.colorset['bob27-red']
            elif state is True:
                 color = self.display.colorset['bob27-miss']
        elif state is False:
            color = self.display.colorset['bob27-green']
        elif state is True:
            color = self.display.colorset['bob27-hit']

        if color is not None:
            self.display.blit_rect(rectangle[0], rectangle[1], rectangle[2], rectangle[3], color)
            self.display.blit_text(text, rectangle[0], rectangle[1], rectangle[2], rectangle[3], color=self.display.colorset['bob27-text'])
        else:
            color = self.display.colorset['bob27-bg']
            self.display.blit_rect(rectangle[0], rectangle[1], rectangle[2], rectangle[3], color)

        # Affichage du segment touché en blanc en dessous du carré
        if dart_hit:
            display_hit_text = 'Miss' if dart_hit == 'MISSDART' else dart_hit
            sub_y = rectangle[1] + rectangle[3] + 4
            sub_h = int(rectangle[3] * 0.6)
            white_color = (255, 255, 255)
            self.display.blit_text(display_hit_text, rectangle[0], sub_y, rectangle[2], sub_h, color=white_color, align='Center', valign='Top')

    def display_hits(self, states, rectangle, marge, round_hits=None):
        '''
        Display actual round hits
        '''

        # Effacer une zone un peu plus haute pour inclure le texte en dessous des carrés
        self.display.blit_rect(0, rectangle[1], self.display.res_x, int(rectangle[3] * 1.7), self.display.colorset['bob27-bg'], Alpha=255)
        rect_x = rectangle[0]

        # Draw hits (Inversion de l'indexation pour afficher le 1er tir sous hit 3 et le dernier sous hit 1)
        dart = 1
        for i, state in enumerate(states):
            rev_index = 2 - i
            hit_val = round_hits[rev_index] if round_hits and 0 <= rev_index < len(round_hits) else ''
            self.draw_hit(dart, state, (rect_x, rectangle[1], rectangle[2], rectangle[3]), hit_val)
            rect_x += rectangle[2] + marge
            dart += 1

        return (0, rectangle[1], self.display.res_x, int(rectangle[3] * 1.7))

    def onscreen_buttons(self):
        '''
        On screen buttons
        '''
        click_zones = {}

        right_x = int(self.display.res['x'] * 12 / 16)
        right_y = self.display.margin
        right_width = int(self.display.res['x'] * 4 / 16)
        right_height = int(self.display.res['y'] * 1.5 / 16)
        right_y = self.display.res['y'] - 4.5 * right_height
        right_y -= 2 * self.display.margin

        buttons = []
        buttons.append([right_x, right_y, right_width, right_height, self.display.colorset['menu-alternate'], 'GAMEBUTTON', 'Exit'])
        right_y += right_height + self.display.margin
        buttons.append([right_x, right_y, right_width, right_height, self.display.colorset['menu-shortcut'], 'BACKUPBUTTON', 'Back'])
        right_y += right_height + self.display.margin
        buttons.append([right_x, right_y, right_width, right_height, self.display.colorset['menu-ok'], 'PLAYERBUTTON', 'Next Player'])

        for button in buttons:
            self.display.blit_rect(button[0], button[1], button[2], button[3], button[4], 2, self.display.colorset['menu-buttons'], self.display.alpha)
            click_zones[button[5]] = (button[0], button[1], button[2], button[3], button[4])
            self.display.blit_text(button[6], button[0], button[1], button[2], button[3], self.display.colorset['menu-text-white'])

        return click_zones


    def refresh_game_screen(self, players, actual_round, max_round, rem_darts, nb_darts, logo, headers, actual_player, TxtOnLogo=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):

        scores = players[actual_player].rounds
        checks = players[actual_player].checks
        score = players[actual_player].score
        launch = nb_darts - rem_darts

        nb_hits = 0
        nb_miss = 0
        for index in range(0, 3):
            if checks[actual_round - 1][index] is True:
                nb_hits += 1
            elif checks[actual_round - 1][index] is False:
                nb_miss += 1
        self.nb_hits = nb_hits
        self.nb_miss = nb_miss
        self.states = self.compute_states(nb_hits, nb_miss)
        self.score = score

        game_background = f"background_{logo}"
        game_background = self.display.file_class.get_full_filename(game_background, 'images')
        if game_background is not None:
            self.display.display_background(image=game_background)
            self.display.save_background()
        else:
            self.display.display_background()

        self.display.blit_rect(0, 0, self.display.res['x'], self.display.res['y'], self.display.colorset['bob27-bg'], Alpha=255)

        round_r = int(self.display.res_x / 12)
        round_m = self.display.margin * 3
        round_x = int(self.display.res_x - round_r - round_m)
        round_y = round_r + round_m

        cercle = pygame.draw.circle(self.display.screen, self.display.colorset['bob27-blue'], (round_x, round_y), round_r)

        title_x = self.display.margin * 2
        title_y = self.display.margin * 2
        title_w = int(self.display.res_x / 8)
        title_h = int(self.display.res_y / 12)
        self.display.blit_text("Bobs 27", title_x, title_y, title_w, title_h, color=self.display.colorset['bob27-text'])

        text_x = int(self.display.res_x / 16)
        text_y = title_y + title_h + self.display.margin * 2
        text_w = int(self.display.res_x / 5)
        text_h = int(self.display.res_y / 36)

        font = self.display.defaultfontpath
        
        current_goal = players[actual_player].goals[actual_round - 1]
        display_goal = 'Bull' if str(current_goal) == '50' else f'Double {current_goal}'

        self.display.blit_text('bob27-nextnumber', text_x, text_y, text_w, text_h, color=self.display.colorset['bob27-text'], align='Left', valign='Bottom', dafont=font)
        self.display.blit_text(display_goal, text_x, text_y + text_h, text_w, text_h * 4, color=self.display.colorset['bob27-text'], align='Left', dafont=font)
        self.display.blit_text('bob27-touchit', text_x, text_y + text_h * 5, text_w, text_h, color=self.display.colorset['bob27-text'], align='Right', valign='Top')

        score_w = int(2 * round_r * 8 / 10)
        score_h = round_r
        score_x = int(round_x - (score_w / 2))
        score_y = round_y - int(score_h / 2)

        rect_score = (score_x, score_y, score_w, score_h)
        sub = self.display.screen.subsurface(rect_score)
        screen_score = pygame.Surface((rect_score[2], rect_score[3]))
        screen_score.blit(sub, (0, 0))

        rect_x = 2 * self.display.margin
        rect_w = int(self.display.res_x / 4) - 4 * self.display.margin
        rect_y = int(self.display.res_y / 3)
        rect_h = int(self.display.res_y / 7)
        rect_m = self.display.margin * 4
        
        rect_hit = (rect_x, rect_y, rect_w, rect_h)
        rect_hits = (0, rect_y, self.display.res_x, int(rect_h * 1.7))
        sub = self.display.screen.subsurface(rect_hits)

        self.display_score(score, score_x, score_y, score_w, score_h)
        self.display_hits(self.states, (rect_x, rect_y, rect_w, rect_h), rect_m, self.current_round_hits)

        self.display.new_display_players(players, actual_player, end_of_game=end_of_game)

        if OnScreenButtons is True or self.display.is_true(self.config.get_value('SectionGlobals', 'onscreenbuttons')):
            click = self.onscreen_buttons()

        self.display.save_background()
        self.display.update_screen()

        if end_of_game:
            click = self.display.end_of_game_menu()
            return click

        if OnScreenButtons is True or self.display.is_true(self.config.get_value('SectionGlobals', 'onscreenbuttons')):
            return [click, [screen_score, rect_score], rect_hits, rect_hit]
        else:
            return [[], [screen_score, rect_score], rect_hits, rect_hit]

    def draw_rect(self, rect, color):
        col = self.display.colorset[color]
        pygame.draw.line(self.display.screen, col, (rect[0], rect[1]), (rect[0] + rect[2], rect[1]), 2)
        pygame.draw.line(self.display.screen, col, (rect[0], rect[1]), (rect[0], rect[1] + rect[3]), 2)
        pygame.draw.line(self.display.screen, col, (rect[0], rect[1] + rect[3]), (rect[0] + rect[2], rect[1] + rect[3]), 2)
        pygame.draw.line(self.display.screen, col, (rect[0] + rect[2], rect[1]), (rect[0] + rect[2], rect[1] + rect[3]), 2)

    def display_hit(self, rectangles, players, actual_player, player_launch, hit):

        self.display.reset_background()

        screen_score = rectangles[1][0]
        rect_score = rectangles[1][1]
        rect_hits = rectangles[2]
        rect_hit = rectangles[3]
        rect_m = self.display.margin * 4

        checks = players[actual_player].checks
        nb_hits = 0
        nb_miss = 0
        for index in range(0, 3):
            if checks[self.actual_round - 1][index] is True:
                nb_hits += 1
            elif checks[self.actual_round - 1][index] is False:
                nb_miss += 1

        score = players[actual_player].score
        states = self.compute_states(nb_hits, nb_miss)

        if self.states[0] != states[0]:
            self.states[0] = None

        if self.states[1] != states[1]:
            self.states[1] = None

        if self.states[2] != states[2]:
            self.states[2] = None

        if self.states[3] != states[3]:
            self.states[3] = None

        if score != self.score:
            self.display.screen.blit(screen_score, (rect_score[0], rect_score[1]))
        self.display_hits(self.states, (rect_hit[0], rect_hit[1], rect_hit[2], rect_hit[3]), rect_m, self.current_round_hits)
        for alpha in [0, 63, 127, 191, 255]:
            self.display.screen.set_alpha(alpha)
            self.display.update_screen(rect_array=[rect_score, rect_hits])

        self.display_score(score, rect_score[0], rect_score[1], rect_score[2], rect_score[3])
        self.display_hits(states, (rect_hit[0], rect_hit[1], rect_hit[2], rect_hit[3]), rect_m, self.current_round_hits)
        for alpha in [0, 63, 127, 191, 255]:
            self.display.screen.set_alpha(alpha)
            self.display.update_screen(rect_array=[rect_score, rect_hits])

        if player_launch >= self.nb_darts:
            self.display.save_background()
