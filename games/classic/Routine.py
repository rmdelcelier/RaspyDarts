# -*- coding: utf-8 -*-
# Routine Game for PyDarts

import random
import pygame
from include import craspberry
from include import cplayer
from include import cgame

VERSION = '1.14'
#OPTIONS = {'theme': 'default', 'max_round': 15, 'start_drill' : 1, 'max_retries': 3, 'teste' : False, 'nb_repetition' : 5'}
OPTIONS = {'theme': 'default', 'max_round': 35, 'start_drill' : 1, 'max_retries': 3, 'teste': False, 'nb_repetition': 3}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
LOGO = 'Routine.png'
HEADERS = ['Statut', 'Etape', 'Réussites', 'Échecs', 'Score']
ROUTINES_CONFIG = {
    1: {"name": "Check-out de 32 en 1 flèche - toucher D16", "max_darts": 1, "type": "checkout", "target": 32, "finish": "Double"},
    2: {"name": "Check-out de 40 en 3 flèches - finir par un double", "max_darts": 3, "type": "finisher", "target": 40, "finish": "Double"},
    3: {"name": "Check-out de 50 en 3 flèches - Bull interdit", "max_darts": 3, "type": "checkout", "target": 50, "finish": "no_bull"},
    4: {"name": "Check-out de 60 en 2 flèches - finir par un double", "max_darts": 2, "type": "checkout", "target": 60, "finish": "Double"},
    5: {"name": "Check-out de 80 en 2 flèches - finir par un double", "max_darts": 2, "type": "checkout", "target": 80, "finish": "Double"},
    6: {"name": "Check-out de 120 en 3 flèches - finir par un double", "max_darts": 3, "type": "checkout", "target": 120, "finish": "Double"},
    7: {"name": "Check-out de 110 en 6 flèches - finir par un double", "max_darts": 6, "type": "checkout", "target": 110, "finish": "Double"},
    8: {"name": "Check-out de 121 en 6 flèches - finir par un double", "max_darts": 6, "type": "checkout", "target": 121, "finish": "Double"},
    9: {"name": "Check-out de 180 en 9 flèches - finir par un double", "max_darts": 9, "type": "checkout", "target": 180, "finish": "Double"},
    10: {"name": "Check-out de 201 en 12 flèches - finir par un double", "max_darts": 12, "type": "checkout", "target": 201, "finish": "Double"},
    11: {"name": "Check-out de 301 en 12 flèches - finir par un double", "max_darts": 12, "type": "checkout", "target": 301, "finish": "Double"},
    12: {"name": "Check-out de 401 en 10 flèches - finir par un double", "max_darts": 10, "type": "checkout", "target": 401, "finish": "Double"},
    13: {"name": "Check-out de 501 en 15 flèches - finir par un double", "max_darts": 15, "type": "checkout", "target": 501, "finish": "Double"},
    14: {"name": "Toucher 1 Simple, 1 Double, 1 Bull", "max_darts": 3, "type": "bull_mix", "target": 2},
    15: {"name": "Toucher 2 Double Bulls (DB)", "max_darts": 6, "type": "bull_count", "target": 2},
    16: {"name": "Toucher 3 Bulls", "max_darts": 9, "type": "bull_count", "target": 3},
    17: {"name": "Gagner 10 pts en touchant le bull (SB=1, DB=2)", "max_darts": 10, "type": "bull_points", "target": 10},
    18: {"name": "Gagner 15 pts en touchant le bull (SB=1, DB=2)", "max_darts": 15, "type": "bull_points", "target": 15},
    19: {"name": "Toucher 3 chiffres identiques", "max_darts": 3, "type": "identical", "target": 3},
    20: {"name": "Toucher 2 doubles différents", "max_darts": 3, "type": "diff_doubles", "target": 2},
    21: {"name": "Toucher le D20 et le D1", "max_darts": 6, "type": "specific_doubles", "target": 2},
    22: {"name": "Toucher dans l'ordre D20, le D19 et le D18", "max_darts": 9, "type": "descending_doubles", "target": 3},
    23: {"name": "Toucher 3 doubles différents", "max_darts": 9, "type": "diff_doubles", "target": 3},
    24: {"name": "Toucher dans l'ordre le D16, le D8, le D4 et le D2", "max_darts": 12, "type": "halving_doubles", "target": 4},
    25: {"name": "Toucher le D3, le D5, le D7, le D9 et le D11", "max_darts": 15, "type": "odd_doubles", "target": 5},
    26: {"name": "Toucher 2 triples différents", "max_darts": 3, "type": "diff_triples", "target": 2},
    27: {"name": "Toucher le S10, le D10 et le T10", "max_darts": 3, "type": "pyramid_10", "target": 3},
    28: {"name": "Toucher le S20, le T20 et le D20", "max_darts": 3, "type": "fanion_20", "target": 1},
    29: {"name": "Toucher 3 Simples, 2 Doubles et 1 Triple sur le 20", "max_darts": 6, "type": "full_sector_20", "target": 6},
    30: {"name": "Toucher 3x 1 chiffre et 1 bull", "max_darts": 4, "type": "custom_11", "target": 4},
    31: {"name": "Toucher 3x 2 chiffres et 1 bull", "max_darts": 7, "type": "custom_12", "target": 7},
    32: {"name": "Toucher 3 triples différents", "max_darts": 9, "type": "diff_triples", "target": 3},
    33: {"name": "Toucher 3x le Triple 20", "max_darts": 9, "type": "consecutive_t20", "target": 3},
    34: {"name": "Toucher 3x le T20, 3x le T19 et 3x le T18", "max_darts": 9, "type": "triples_sequence", "target": 9},
    35: {"name": "Finisher progressif - finir par un double (+5 par réussite)", "max_darts": 3, "type": "prog_finisher", "target": 40, "finish": "Double"}
}

#FINISHABLE_SCORES = [40, 50, 60, 64, 68, 72, 80, 82, 85, 90, 100, 110, 121, 130, 140, 160]


def check_players_allowed(nb_players):
    return nb_players <= 6, VERSION, 6

class CPlayerExtended(cplayer.Player):
    def __init__(self, ident, config):
        super(CPlayerExtended, self).__init__(ident, config)
        for record in GAME_RECORDS:
            self.stats[record] = '0'
        self.routine_results = {}
        self.current_drill_score = 0
        self.current_drill_hits = []
        self.drill_darts_count = 0
        self.successes = 0
        self.failures = 0
        self.retries_left = 0
        self.current_repetition = 0
        self.finisher_target = 40
        self.prog_finisher_target = 40

class Game(cgame.Game):
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.game_records = GAME_RECORDS
        self.logo = LOGO
        self.headers = HEADERS
        self.options = options
        self.max_round = int(options.get('max_round', 35))
        self.start_drill = int(options.get('start_drill', 1))
        self.max_retries = int(options.get('max_retries', 3))
        self.teste = bool(self.options.get('teste', False))

            
        self.nb_repetition = int(options.get('nb_repetition', 3))
        self.winner = None
        self.video_player = video_player
        self.nb_darts = 99 
        self.possible_hits = ""
        self.margin = self.display.margin
        self.margin_2 = 2 * self.display.margin
        
        self.score_map = {
            'S1': 1, 'D1': 2, 'T1': 3,
            'S2': 2, 'D2': 4, 'T2': 6,
            'S3': 3, 'D3': 6, 'T3': 9,
            'S4': 4, 'D4': 8, 'T4': 12,
            'S5': 5, 'D5': 10, 'T5': 15,
            'S6': 6, 'D6': 12, 'T6': 18,
            'S7': 7, 'D7': 14, 'T7': 21,
            'S8': 8, 'D8': 16, 'T8': 24,
            'S9': 9, 'D9': 18, 'T9': 27,
            'S10': 10, 'D10': 20, 'T10': 30,
            'S11': 11, 'D11': 22, 'T11': 33,
            'S12': 12, 'D12': 24, 'T12': 36,
            'S13': 13, 'D13': 26, 'T13': 39,
            'S14': 14, 'D14': 28, 'T14': 42,
            'S15': 15, 'D15': 30, 'T15': 45,
            'S16': 16, 'D16': 32, 'T16': 48,
            'S17': 17, 'D17': 34, 'T17': 51,
            'S18': 18, 'D18': 36, 'T18': 54,
            'S19': 19, 'D19': 38, 'T19': 57,
            'S20': 20, 'D20': 40, 'T20': 60,
            'SB': 25, 'DB': 50
        }

    def evaluate_drill(self, drill, hits, score, player=None):
        drill_type = drill.get("type", "score")
        finish_rule = drill.get("finish", None)
        
        if drill_type in ["finisher", "checkout"]:
            target = drill.get("target", 0)
        elif drill_type == "prog_finisher":
            target = player.prog_finisher_target if player else drill.get("target", 40)
        else:
            target = drill.get("target", 0)
            
        if not hits:
            return False

        if drill_type == "score":
            score_ok = (score == target) if finish_rule else (score >= target)
            
        elif drill_type in ["checkout", "finisher", "prog_finisher"]:
            if finish_rule == "no_bull":
                has_bull = any(h in ['SB', 'DB'] or (len(h) > 1 and h[1:] == '25') for h in hits)
                score_ok = (score == target and not has_bull)
            else:
                score_ok = (score == target)
                
        elif drill_type == "identical":
            base_nums = [h[1:] for h in hits if len(h) > 1 and h not in ['SB', 'DB']]
            score_ok = len(hits) >= target and len(set(base_nums)) == 1
            
        elif drill_type == "diff_doubles":
            doubles = [h for h in hits if h.startswith('D') and h != 'DB']
            score_ok = len(doubles) >= target and len(set(doubles)) >= target
            
        elif drill_type == "diff_triples":
            triples = [h for h in hits if h.startswith('T')]
            score_ok = len(triples) >= target and len(set(triples)) >= target
            
        elif drill_type == "custom_11":
            bulls = [h for h in hits if h in ['SB', 'DB']]
            non_bulls = [h for h in hits if h not in ['SB', 'DB'] and len(h) > 1]
            base_nums = [h[1:] for h in non_bulls]
            score_ok = len(bulls) >= 1 and len(base_nums) >= 3 and len(set(base_nums)) == 1
            
        elif drill_type == "custom_12":
            bulls = [h for h in hits if h in ['SB', 'DB']]
            non_bulls = [h for h in hits if h not in ['SB', 'DB'] and len(h) > 1]
            base_nums = [h[1:] for h in non_bulls]
            score_ok = len(bulls) >= 1 and len(base_nums) >= 6 and len(set(base_nums)) == 2
            
        elif drill_type == "bull_points":
            bull_pts = sum(1 if h == 'SB' else (2 if h == 'DB' else 0) for h in hits)
            score_ok = (bull_pts >= target)

            
        elif drill_type == "bull_count":
            # Le défi 15 demande explicitement des Double Bulls (DB)
            # Le défi 16 demande des Bulls au sens large (SB ou DB)
            if "Double" in drill.get("name", ""):
                bull_count = sum(1 for h in hits if h == 'DB')
            else:
                bull_count = sum(1 for h in hits if h in ['SB', 'DB'])
            score_ok = (bull_count >= target)

        elif drill_type == "bull_mix":
            has_simple = any(h.startswith('S') or (h.isdigit()) for h in hits)
            has_double = any(h.startswith('D') and h != 'DB' for h in hits)
            has_bull = any(h in ['SB', 'DB'] for h in hits)
            score_ok = has_simple and has_double and has_bull
            
            #has_sb = 'SB' in hits
            #has_db = 'DB' in hits
            #score_ok = has_sb and has_db

        elif drill_type == "descending_doubles":
            expected = ['D20', 'D19', 'D18']
            idx = 0
            for h in hits:
                if idx < len(expected) and h == expected[idx]:
                    idx += 1
            score_ok = (idx >= 3)

        elif drill_type == "odd_doubles":
            odds = ['D3', 'D5', 'D7', 'D9', 'D11']
            matched = sum(1 for h in hits if h in odds)
            score_ok = (matched >= target)

        elif drill_type == "halving_doubles":
            sequence = ['D16', 'D8', 'D4', 'D2']
            idx = 0
            for h in hits:
                if idx < len(sequence) and h == sequence[idx]:
                    idx += 1
            score_ok = (idx >= target)

        elif drill_type == "specific_doubles":
            target_doubs = {'D20', 'D1'}
            hit_doubs = {h for h in hits if h in target_doubs}
            score_ok = len(hit_doubs) >= target

        elif drill_type == "pyramid_10":
            target_set = {'S10', 'D10', 'T10'}
            score_ok = target_set.issubset(set(hits))

        elif drill_type == "full_sector_20":
            # Vérification rigoureuse pour le secteur 20
            sims = sum(1 for h in hits if h == 'S20')
            doubs = sum(1 for h in hits if h == 'D20')
            trips = sum(1 for h in hits if h == 'T20')
            
            # 1. Si on touche un truc qui n'est ni S20, ni D20, ni T20 dans les hits, c'est raté
            other_hits = [h for h in hits if h not in ['S20', 'D20', 'T20']]
            if other_hits:
                score_ok = False
            # 2. Si on dépasse les quotas autorisés, c'est raté
            elif sims > 3 or doubs > 2 or trips > 1:
                score_ok = False
            # 3. Sinon, on valide uniquement si on a exactement le compte requis
            else:
                score_ok = (sims == 3 and doubs == 2 and trips == 1)
 

        elif drill_type == "fanion_20" or drill_type == "custom_s20_d20_t20":
            target_set = {'S20', 'D20', 'T20'}
            score_ok = target_set.issubset(set(hits))

        elif drill_type == "consecutive_t20":
            t20_count = sum(1 for h in hits if h == 'T20')
            score_ok = (t20_count >= target)

        elif drill_type == "triples_sequence":
            t20_count = sum(1 for h in hits if h == 'T20')
            t19_count = sum(1 for h in hits if h == 'T19')
            t18_count = sum(1 for h in hits if h == 'T18')
            score_ok = (t20_count >= 3 and t19_count >= 3 and t18_count >= 3)

        else:
            score_ok = (score >= target)

        if finish_rule and hits and score_ok:
            last_hit = hits[-1]
            if finish_rule.startswith("D") and finish_rule != "Double":
                return last_hit == finish_rule
            elif finish_rule == "Double":
                return last_hit.startswith('D') or last_hit == 'DB'

        return score_ok

    def compute_suggestions(self, remaining_score, darts_left, drill):
        drill_type = drill.get("type", "score")
        finish_rule = drill.get("finish", None)
        
        if drill_type in ["identical", "diff_doubles", "diff_triples", "custom_11", "custom_12", "triples_sequence", "bull_points"]:
            return ""

        if darts_left <= 0 or remaining_score <= 0:
            return ""

        def is_double(hit_name):
            return hit_name.startswith('D') or hit_name == 'DB'
            
        allowed_score_map = self.score_map
        if finish_rule == "no_bull":
            allowed_score_map = {k: v for k, v in self.score_map.items() if k not in ['SB', 'DB']}

        if remaining_score > darts_left * 60:
            return ""

        must_finish_double = (drill.get("finish") == "Double")

        for hit, val in allowed_score_map.items():
            if val == remaining_score:
                if not must_finish_double or is_double(hit):
                    return hit

        if darts_left >= 2:
            for h1, v1 in allowed_score_map.items():
                if v1 < remaining_score:
                    rem = remaining_score - v1
                    for h2, v2 in allowed_score_map.items():
                        if v2 == rem:
                            if not must_finish_double or is_double(h2):
                                return f"{h1}-{h2}"
            
            if must_finish_double:
                for h1, v1 in allowed_score_map.items():
                    if v1 < remaining_score:
                        rem = remaining_score - v1
                        for h2, v2 in allowed_score_map.items():
                            if v2 == rem:
                                return f"{h1}-{h2}"

        return ""

    def compute_suggestions(self, remaining_score, darts_left, drill):
        drill_type = drill.get("type", "score")
        finish_rule = drill.get("finish", None)
        
        if drill_type in ["identical", "diff_doubles", "diff_triples", "custom_11", "custom_12", "triples_sequence", "bull_points"]:
            return ""

        if darts_left <= 0 or remaining_score <= 0:
            return ""

        def is_double(hit_name):
            return hit_name.startswith('D') or hit_name == 'DB'
            
        allowed_score_map = self.score_map
        if finish_rule == "no_bull":
            allowed_score_map = {k: v for k, v in self.score_map.items() if k not in ['SB', 'DB']}

        if remaining_score > darts_left * 60:
            return ""

        must_finish_double = (drill.get("finish") == "Double")

        for hit, val in self.score_map.items():
            if val == remaining_score:
                if not must_finish_double or is_double(hit):
                    return hit

        if darts_left >= 2:
            for h1, v1 in self.score_map.items():
                if v1 < remaining_score:
                    rem = remaining_score - v1
                    for h2, v2 in self.score_map.items():
                        if v2 == rem:
                            if not must_finish_double or is_double(h2):
                                return f"{h1}-{h2}"
            
            if must_finish_double:
                for h1, v1 in self.score_map.items():
                    if v1 < remaining_score:
                        rem = remaining_score - v1
                        for h2, v2 in self.score_map.items():
                            if v2 == rem:
                                return f"{h1}-{h2}"

        return ""

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        return_code = 0
        # Nouvelle volee : les flechettes ratees ajoutees apres un abandon ne concernent plus personne
        if player_launch == 1:
            self.abandoned = False
        raw_drill_id = self.start_drill + (actual_round - 1)
        real_drill_id = min(raw_drill_id, max(ROUTINES_CONFIG.keys()))
        drill_config = ROUTINES_CONFIG.get(real_drill_id, ROUTINES_CONFIG.get(1, {}))
        self.nb_darts = 99
        
        max_drill_darts = drill_config.get("max_darts", 3)
        drill_type = drill_config.get("type", "score")

        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            for player_init in players:
                player_init.score = 0  
                player_init.successes = 0
                player_init.failures = 0
                player_init.routine_results = {}
                player_init.retries_left = self.max_retries
                player_init.reset_rounds(self.max_round)

        current_player = players[actual_player]

        if player_launch == 1 and len(current_player.darts) == 0:
            if current_player.retries_left == 0:
                current_player.retries_left = self.max_retries
                
            current_player.reset_darts()
            current_player.current_drill_score = 0  
            current_player.current_drill_hits = []
            current_player.drill_darts_count = 0
            current_player.round_points = 0
            current_player.darts = []
            
            if drill_type in ["finisher", "checkout"]:
                current_player.finisher_target = drill_config.get("target", 40)
                              
            if drill_type == "prog_finisher" and not hasattr(current_player, 'prog_finisher_initialized'):
                current_player.prog_finisher_target = drill_config.get("target", 40)
                current_player.prog_finisher_initialized = True

            current_player.columns = []
            for _ in range(0, len(self.headers)):
                current_player.columns.append(['', 'str'])

        current_score = current_player.current_drill_score
        if drill_type in ["finisher", "checkout"]:
            target = drill_config.get("target", 0)
        elif drill_type == "prog_finisher":
            target = current_player.prog_finisher_target
        else:
            target = drill_config.get("target", 0)
            
        remaining_target = max(0, target - current_score)
        
        darts_left = max_drill_darts - current_player.drill_darts_count
        self.possible_hits = self.compute_suggestions(remaining_target, darts_left, drill_config)
        
        current_player.columns[0] = ("EN COURS", 'str')
        current_player.columns[1] = (f"E{real_drill_id}", 'str')
        current_player.columns[2] = (current_player.successes, 'int')
        current_player.columns[3] = (current_player.failures, 'int')
        current_player.columns[4] = (current_player.current_drill_score, 'int')
            
        return return_code
        
        
    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        handler = self.init_handler()
        player = players[actual_player]
        raw_drill_id = self.start_drill + (actual_round - 1)
        real_drill_id = min(raw_drill_id, max(ROUTINES_CONFIG.keys()))
        drill = ROUTINES_CONFIG.get(real_drill_id, ROUTINES_CONFIG.get(1, {}))
        max_drill_darts = drill.get("max_darts", 3)
        drill_type = drill.get("type", "score")
        
        if drill_type in ["finisher", "checkout"]:
            target = drill.get("target", 0)
        elif drill_type == "prog_finisher":
            target = player.prog_finisher_target
        else:
            target = drill.get("target", 0)
            
        finish_rule = drill.get("finish", None)

        player.drill_darts_count += 1

        if hit == 'MISS':
            score_val = 0
        elif drill_type == "bull_points":
            score_val = 1 if hit == 'SB' else (2 if hit == 'DB' else 0)
        else:
            score_val = self.score_map.get(hit, 0)

        player.current_drill_score += score_val
        player.current_drill_hits.append(hit)
        player.darts.append(hit)
        
        drill_success = self.evaluate_drill(drill, player.current_drill_hits, player.current_drill_score, player)

        darts_left = max_drill_darts - player.drill_darts_count
        max_possible_remaining = darts_left * 60
        current_total = player.current_drill_score
        remaining = target - current_total

        is_bust = False
        bust_reason = ""
        hits = player.current_drill_hits
        
        if finish_rule == "Double":
            if player.drill_darts_count >= max_drill_darts:
                if remaining != 0 or (remaining == 0 and not (hit.startswith('D') or hit == 'DB')):
                    is_bust = True
                    bust_reason = "RATE"
            elif darts_left == 1:
                if remaining != 0 and (remaining % 2 != 0 or remaining == 1 or remaining > 50):
                    is_bust = True
                    bust_reason = "IMPOSSIBLE"

        if drill_type == "identical":
            base_nums = [h[1:] for h in hits if len(h) > 1 and h not in ['SB', 'DB']]
            if len(set(base_nums)) > 1:
                is_bust = True
                bust_reason = "RATE"
        elif drill_type == "diff_doubles":
            doubles = [h for h in hits if h.startswith('D') and h != 'DB']
            if len(doubles) != len(set(doubles)):
                is_bust = True
                bust_reason = "RATE"
            elif (len(doubles) + darts_left) < target:
                is_bust = True
                bust_reason = "RATE"
        elif drill_type == "diff_triples":
            triples = [h for h in hits if h.startswith('T')]
            if len(triples) != len(set(triples)):
                is_bust = True
                bust_reason = "RATE"
            elif (len(triples) + darts_left) < target:
                is_bust = True
                bust_reason = "RATE"
        elif drill_type == "custom_11":
            if len(hits) >= 4 and hits[3] not in ['SB', 'DB']:
                is_bust = True
                bust_reason = "RATE"
            base_nums = [h[1:] for h in hits[:3] if h in self.score_map and h not in ['SB', 'DB']]
            if len(base_nums) >= 2 and len(set(base_nums)) > 1:
                is_bust = True
                bust_reason = "RATE"
        elif drill_type == "custom_12":
            if len(hits) >= 7 and hits[6] not in ['SB', 'DB']:
                is_bust = True
                bust_reason = "RATE"
            base_nums = [h[1:] for h in hits[:6] if h in self.score_map and h not in ['SB', 'DB']]
            if len(base_nums) >= 2 and len(set(base_nums)) > 2:
                is_bust = True
                bust_reason = "RATE"
        elif drill_type == "bull_points":
            current_bull_pts = sum(1 if h == 'SB' else (2 if h == 'DB' else 0) for h in hits)
            max_possible_pts = current_bull_pts + (darts_left * 2)
            if max_possible_pts < target:
                is_bust = True
                bust_reason = "RATE"
        elif drill_type in ["checkout", "score", "finisher", "prog_finisher"]:
            if remaining < 0:
                is_bust = True
                bust_reason = "SCORE DÉPASSÉ"
            elif finish_rule == "Double" and remaining == 1:
                is_bust = True
                bust_reason = "BLOQUÉ À 1"
            elif finish_rule == "Double" and remaining == 0 and not (hit.startswith('D') or hit == 'DB'):
                is_bust = True
                bust_reason = "MAUVAISE FIN"
            elif finish_rule == "Double" and player.drill_darts_count >= max_drill_darts and remaining != 0:
                is_bust = True
                bust_reason = "RATE"
            elif (current_total + max_possible_remaining) < target:
                is_bust = True
                bust_reason = "IMPOSSIBLE"
            elif player.drill_darts_count >= max_drill_darts and remaining != 0:
                is_bust = True
                bust_reason = "RATE"

        is_drill_finished = False
        if drill_success:
            is_drill_finished = True
        elif player.drill_darts_count >= max_drill_darts:
            is_drill_finished = True
        elif is_bust:
            is_drill_finished = True

        # Gestion des réussites immédiates (ex: prog_finisher)
        if is_drill_finished and drill_success:
            player.score += 1
            player.successes += 1
            
            if drill_type == "prog_finisher":
                player.prog_finisher_target += 5
                player.retries_left = self.max_retries
                player.drill_darts_count = 0
                player.current_drill_score = 0
                player.current_drill_hits = []
                player.darts = []
                player.routine_results[actual_round] = "REUSSI"
                player.columns[0] = (f"VALIDE ! CIBLE : {player.prog_finisher_target}", 'str')
                handler['sound'] = 'dungeon_hit'
                handler['dmd'] = f"0/{max_drill_darts}"
                handler['show'] = (player.darts, hit, True)
                
                self.refresh_game_screen(players, actual_round, self.max_round, 0, self.nb_darts, self.logo, self.headers, actual_player)
                #time.sleep(1.0)
                pygame.time.wait(2000)  
                
                handler['return_code'] = 0
                return handler

            player.routine_results[actual_round] = "REUSSI"
            player.columns[0] = ("VALIDE", 'str')
            handler['sound'] = 'dungeon_hit'
            
            if real_drill_id >= max(ROUTINES_CONFIG.keys()):
                player.retries_left = 0 
                is_drill_finished = True 

        # Si le drill est fini mais raté (on compte un échec pour l'affichage)
        elif is_drill_finished and not drill_success:
            player.failures += 1
            player.columns[3] = (player.failures, 'int')

        player.columns[2] = (player.successes, 'int')
        player.columns[3] = (player.failures, 'int')
        player.columns[4] = (player.current_drill_score, 'int')
        
        player.darts_thrown += 1
        player.increment_hits(hit)
        self.refresh_stats(players, actual_round)

        if drill_type == "prog_finisher":
            target = player.prog_finisher_target
        elif drill_type in ["finisher", "checkout"]:
            target = drill.get("target", 0)
        else:
            target = drill.get("target", 0)

        remaining_target = max(0, target - player.current_drill_score)
        darts_left_after = max_drill_darts - player.drill_darts_count
        self.possible_hits = self.compute_suggestions(remaining_target, darts_left_after, drill)
        
        handler['dmd'] = f"{player.drill_darts_count}/{max_drill_darts}"
        handler['show'] = (player.darts, hit, True)

        # Point unique de gestion de fin de drill (Réussi ou Raté définitif / Essai suivant)
        if is_drill_finished:
            if not drill_success and player.retries_left > 1:
                # Il reste des essais : on redonne une chance sans changer de round
                player.retries_left -= 1
                player.columns[0] = (f"RATE - ESSAI RESTANT ({player.retries_left})", 'str')
                handler['sound'] = 'miss'
                handler['dmd'] = f"0/{max_drill_darts}"
                
                player.drill_darts_count = 0
                player.current_drill_score = 0
                player.current_drill_hits = []
                player.darts = []
                
                self.refresh_game_screen(players, actual_round, self.max_round, 0, self.nb_darts, self.logo, self.headers, actual_player)
                pygame.time.wait(2000)  
                
                handler['show'] = (player.darts, hit, True)
                handler['return_code'] = 0  
                handler['take_shot'] = self.time_to_take_shot_or_video(hit)
                return handler

            # Plus d'essais ou drill réussi : on passe à la suite
            player.retries_left = 0
            player.drill_darts_count = 0
            player.current_drill_score = 0
            player.current_drill_hits = []
            player.darts = []
            self.refresh_game_screen(players, actual_round, self.max_round, 0, self.nb_darts, self.logo, self.headers, actual_player)
            pygame.time.wait(2000)  
            
            player.retries_left = self.max_retries 

            if self.teste:
                player.current_repetition += 1
                if player.current_repetition < self.nb_repetition:
                    handler['return_code'] = 0  
                else:
                    player.current_repetition = 0
                    self.winner = self.best_score(players)
                    handler['return_code'] = 3  
            else:
                if real_drill_id >= max(ROUTINES_CONFIG.keys()) and actual_player == len(players) - 1:
                    # CORRECTION ICI : Si c'est le dernier drill (35)
                    if drill_success:
                        self.winner = self.best_score(players)
                        handler['return_code'] = 3  # Gagnant / Fin normale
                    else:
                        handler['return_code'] = 2  # GAME OVER (échec du dernier défi)
                else:
                    handler['return_code'] = 1  
        else:
            handler['return_code'] = 0  

        return handler

    def best_score(self, players):
        best_player = None
        best_score = None
        best_count = 0
        for player in players:
            if best_score is None or player.score > best_score:
                best_score = player.score
                best_player = player.ident
                best_count = 1
            elif player.score == best_score:
                best_count += 1
        return best_player if best_count == 1 else -1


    def post_round_check(self, players, actual_round, actual_player):
        raw_drill_id = self.start_drill + (actual_round - 1)
        real_drill_id = min(raw_drill_id, max(ROUTINES_CONFIG.keys()))
        max_available_drill = max(ROUTINES_CONFIG.keys())

        if (real_drill_id >= max_available_drill or actual_round >= self.max_round) and actual_player == len(players) - 1:
            return self.best_score(players)
            
        return -2
        
        
    def refresh_stats(self, players, actual_round):
        for player in players:
            player.stats['Points Per Round'] = player.show_ppr()
            player.stats['Points Per Dart'] = player.show_ppd()

    def early_player_button(self, players, actual_player, actual_round):
        """
        Bouton "joueur suivant" avant la fin de l'exercice : l'exercice en cours est abandonne
        (compte comme un echec) et on passe au joueur suivant.
        Le jeu complete ensuite la volee avec des flechettes ratees jusqu'a nb_darts, ici 99 :
        elles sont ignorees (voir miss_button), sinon chacune serait jouee comme une vraie
        flechette, avec ses pauses, pendant plusieurs minutes.
        """
        player = players[actual_player]
        raw_drill_id = self.start_drill + (actual_round - 1)
        real_drill_id = min(raw_drill_id, max(ROUTINES_CONFIG.keys()))
        player.failures += 1
        player.routine_results[actual_round] = "ABANDON"
        player.drill_darts_count = 0
        player.current_drill_score = 0
        player.current_drill_hits = []
        player.darts = []
        player.retries_left = self.max_retries
        player.columns[0] = ("ABANDON", 'str')
        player.columns[1] = (f"E{real_drill_id}", 'str')
        player.columns[2] = (player.successes, 'int')
        player.columns[3] = (player.failures, 'int')
        player.columns[4] = (0, 'int')
        self.abandoned = True
        self.display.play_sound('miss')
        return 1

    def miss_button(self, players, actual_player, actual_round, player_launch):
        if getattr(self, 'abandoned', False):
            # Flechettes ratees ajoutees par le jeu apres un abandon : rien a jouer
            return 0
        self.display.play_sound('miss')
        
        # On traite le MISS comme une fléchette normale qui rapporte 0 et avance le compteur
        return self.post_dart_check('MISS', players, actual_round, actual_player, player_launch)

        
            
    def refresh_game_screen(self, players, actual_round, max_round, rem_darts, nb_darts, logo, headers, actual_player, TxtOnLogo=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
        self.display.reset_background()
        
        raw_drill_id = self.start_drill + (actual_round - 1)
        real_drill_id = min(raw_drill_id, max(ROUTINES_CONFIG.keys()))
        
        cell_bg = (20, 22, 28)        
        header_bg = (35, 38, 48)      
        grid_border_color = (60, 65, 78) 

        game_background = f"background_{logo.replace('_', '_').replace('!', '').split('.')[0]}"
        game_background = self.display.file_class.get_full_filename(game_background, 'images')
        # The background under its veil : copied from the cache after the first time
        self.display.display_background(image=game_background, veil=self.display.colorset['game-bg'])

        title_h = int(self.display.res['y'] * 0.07)
        title_w = int(self.display.res['x'] * 0.4)
        title_x = int((self.display.res['x'] - title_w) / 2)
        title_y = int(self.margin * 2) 
        self.display.blit_text("DAILY ROUTINE", title_x, title_y, title_w, title_h, color=(255, 255, 255), align='Center', valign='center', margin=False)

        drill = ROUTINES_CONFIG.get(real_drill_id, ROUTINES_CONFIG.get(1, {}))
        drill_name = drill.get("name", "Défi")
        drill_type = drill.get("type", "score")
        
        if drill_type in ["finisher", "checkout"]:
            target_score = drill.get("target", 0)
            #drill_name = f"Finisher {target_score}"
        elif drill_type == "prog_finisher":
            target_score = players[actual_player].prog_finisher_target
            drill_name = f"Finisher Progressif ({target_score})"
        else:
            target_score = drill.get("target", 0)

        max_drill_darts = drill.get("max_darts", 3)
        current_score = players[actual_player].current_drill_score
        darts_thrown_current = players[actual_player].drill_darts_count
        
        info_w = int(self.display.res['x'] * 0.90)
        info_h = int(self.display.res['y'] * 0.07)
        info_x = int((self.display.res['x'] - info_w) / 2)
        info_y = title_y + title_h + 15 

        self.display.blit_rect(info_x, info_y, info_w, info_h, header_bg)
        pygame.draw.rect(self.display.screen, grid_border_color, (info_x, info_y, info_w, info_h), 1)
        
        missing = max(0, target_score - current_score)
        text_defi = f"Étape {real_drill_id}: {drill_name} | Cible: {target_score} | Reste: {missing} | Flèches: {darts_thrown_current}/{max_drill_darts}"
        self.display.blit_text(text_defi, info_x, info_y, info_w, info_h, color=(255, 255, 0), align='Center', valign='center', margin=False)

        nb_players = len(players)
        nb_headers = len(headers)
        
        total_parts = 2 + 2 + (nb_headers - 1) + 0.5 
        col_w = int((self.display.res['x'] * 0.92) / total_parts)
        
        name_col_w = col_w * 2
        statut_col_w = col_w * 2  
        score_col_w = int(col_w * 1.5)
        
        table_w = name_col_w + statut_col_w + ((nb_headers - 2) * col_w) + score_col_w
        
        row_h = int(self.display.res['y'] / 22)
        actual_table_h = row_h * (nb_players + 1)
        table_x = int((self.display.res['x'] - table_w) / 2)
        table_y = info_y + info_h + 20 
        
        for col_idx, header in enumerate(headers):
            if col_idx == 0:
                current_col_w = statut_col_w
                cx = table_x + name_col_w
            elif col_idx == nb_headers - 1:
                current_col_w = score_col_w
                cx = table_x + name_col_w + statut_col_w + ((nb_headers - 2) * col_w)
            else:
                current_col_w = col_w
                cx = table_x + name_col_w + statut_col_w + (col_idx - 1) * col_w

            self.display.blit_rect(cx, table_y, current_col_w, row_h, header_bg)
            pygame.draw.rect(self.display.screen, grid_border_color, (cx, table_y, current_col_w, row_h), 1)
            if header:
                self.display.blit_text(header, cx, table_y, current_col_w, row_h, color=(255, 255, 255), align='Center')

        for p_idx, player in enumerate(players):
            ry = table_y + (p_idx + 1) * row_h
            is_active = (p_idx == actual_player)
            name_bg_color = player.color if is_active else cell_bg
            
            self.display.blit_rect(table_x, ry, name_col_w, row_h, name_bg_color)
            pygame.draw.rect(self.display.screen, grid_border_color, (table_x, ry, name_col_w, row_h), 1)
            self.display.blit_text(player.name, table_x + self.margin, ry, name_col_w - self.margin_2, row_h, color=(255, 255, 255), align='Left')
            
            for c_idx in range(nb_headers):
                if c_idx == 0:
                    current_col_w = statut_col_w
                    cx = table_x + name_col_w
                elif c_idx == nb_headers - 1:
                    current_col_w = score_col_w
                    cx = table_x + name_col_w + statut_col_w + ((nb_headers - 2) * col_w)
                else:
                    current_col_w = col_w
                    cx = table_x + name_col_w + statut_col_w + (c_idx - 1) * col_w

                col_bg_color = player.color if (is_active and c_idx == nb_headers - 1) else cell_bg

                self.display.blit_rect(cx, ry, current_col_w, row_h, col_bg_color)
                pygame.draw.rect(self.display.screen, grid_border_color, (cx, ry, current_col_w, row_h), 1)
                
                if c_idx == nb_headers - 1:
                    self.display.blit_text(str(player.score), cx, ry, current_col_w, row_h, color=(255, 255, 255), align='Center')
                elif c_idx < len(player.columns):
                    val = player.columns[c_idx][0] if len(player.columns[c_idx]) > 0 else ''
                    self.display.blit_text(str(val), cx, ry, current_col_w, row_h, color=(255, 255, 255), align='Center')

            if is_active:
                pygame.draw.rect(self.display.screen, player.color, (table_x, ry, table_w, row_h), 3)
        
        player_darts = players[actual_player].darts
        total_darts = len(player_darts)
        max_per_line = 7
        small_box_w = int(col_w * 1.1)
        small_box_h = int(row_h * 1.1)
        start_by = table_y + actual_table_h + 15 

        for i, val_dart in enumerate(player_darts):
            line_idx = i // max_per_line
            col_idx = i % max_per_line
            
            items_in_this_line = min(max_per_line, total_darts - (line_idx * max_per_line))
            line_total_w = items_in_this_line * (small_box_w + 5)
            
            start_bx = int((self.display.res['x'] - line_total_w) / 2)
            bx = start_bx + col_idx * (small_box_w + 5)
            by = start_by + line_idx * (small_box_h + 5)

            self.display.blit_rect(bx, by, small_box_w, small_box_h, cell_bg)
            pygame.draw.rect(self.display.screen, grid_border_color, (bx, by, small_box_w, small_box_h), 1)
            if val_dart != '':
                self.display.blit_text(str(val_dart), bx, by, small_box_w, small_box_h, color=self.display.colorset['game-score'], align='Center')
 
        statut_msg = players[actual_player].columns[0][0]
        
        if statut_msg and statut_msg != "EN COURS":
            display_text = f"DÉFI : {statut_msg}"
            status_w = int(self.display.res['x'] * 0.9) 
            status_h = int(row_h * 3.5)    
            status_y = start_by + ((total_darts // max_per_line) + 1) * (small_box_h + 10) + 30
            status_x = int((self.display.res['x'] - status_w) / 2)
            
            if not statut_msg.startswith("VALIDE"):
                couleur = (255, 0, 0)    
            else:
                couleur = (0, 255, 0)    
            
            self.display.blit_text(
                display_text, 
                status_x, status_y, status_w, status_h, 
                color=couleur,      
                align='Center', 
                valign='center', 
                margin=False
            )

        if self.possible_hits:
            pred_w = int(self.display.res['x'] * 0.22)
            pred_h = int(row_h * 1.2)
            pred_x = int(self.display.res['x'] * 0.03)
            pred_y = int(self.display.res['y'] - pred_h - 20)

            self.display.blit_rect(pred_x, pred_y, pred_w, pred_h, header_bg)
            pygame.draw.rect(self.display.screen, (0, 255, 0), (pred_x, pred_y, pred_w, pred_h), 2)
            self.display.blit_text(f"Cible: {self.possible_hits}", pred_x, pred_y, pred_w, pred_h, color=(0, 255, 0), align='Center', valign='center', margin=False)


        if self.teste or self.max_retries > 0:
            font = self.display.font(self.display.defaultfontpath, 32)
            text_parts = []
            
            if self.teste:
                text_parts.append(f"Nb Rep: {player.current_repetition + 1}/{self.nb_repetition}")
            if self.max_retries > 0:
                text_parts.append(f"Nb Essais: {player.retries_left}")
            
            info_str = " | ".join(text_parts)
            text_surface = font.render(info_str, True, (255, 255, 255))
            
            if hasattr(self.display, 'screen') and self.display.screen:
                screen_width = self.display.screen.get_width()
                screen_height = self.display.screen.get_height()
                
                offset_x = 310 if self.teste else 180
                
                # Shown with the rest by update_screen below (the screen was sent twice, 18 ms)
                self.display.screen.blit(text_surface, (screen_width - offset_x, screen_height - 40))
 
        click = None
        if not end_of_game:
            if OnScreenButtons:
                click = self.onscreen_buttons()

        self.display.update_screen()
        self.display.save_background()

        if end_of_game:
            click = self.display.end_of_game_menu()
            return click
        if OnScreenButtons:
            return [click, [None, None], [None, None], [None, None], [None, None], [None, None], [None, None]]
        else:
            return [[], [None, None], [None, None], [None, None], [None, None], [None, None], [None, None]]
