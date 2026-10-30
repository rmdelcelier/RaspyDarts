# -*- coding: utf-8 -*-
# Game by Pydarts Team - Tactical Match-3 / Fighting Darts Game (Custom Layout)
########
import random
import pygame
from include import cgame, cplayer

### TROPHEES
from include import ctrophies



VERSION = "1.35"
OPTIONS = {
    "theme": "default",
    "max_round": 10,
    "start_hp": 100,
    "penality": 10,
    "speed": 120,            # Vitesse pour la synthèse vocale
}
GAME_RECORDS = {
    "Points Per Round": "DESC",
    "Points Per Dart": "DESC",
    "Max Damage Turn": "DESC",
    "Total Parried": "DESC",
}
NB_DARTS = 3
LOGO = "Duel.png"
HEADERS = ["Joueur", "D1", "D2", "D3", "Pts", "Bonus", "Pwr", "Sante (PV)", "Dégâts en attente"]


def check_players_allowed(nb_players):
    """Vérifie le nombre de joueurs autorisés (2 à 8 joueurs en versus)"""
    return nb_players >= 2 and nb_players <= 8, VERSION, 8


class CPlayerExtended(cplayer.Player):
    """Extension de la classe Joueur avec métriques de combat, combos et IA"""

    def __init__(self, ident, config):
        super(CPlayerExtended, self).__init__(ident, config)
        self.hp = 100
        self.pending_damage = 0
        self.total_damage_dealt = 0
        self.total_damage_blocked = 0
        self.max_damage_turn = 0
        self.turn_darts = []
        self.round_bonus = 0
        self.round_power = 0
        self.alive = True
        self.is_bot = False
        self.columns = [["", "str"] for _ in range(9)]

        for record in GAME_RECORDS:
            self.stats[record] = "0"

    def reset_stats_game(self, start_hp):
        """Réinitialisation complète du joueur en début de partie"""
        self.hp = start_hp
        self.pending_damage = 0
        self.total_damage_dealt = 0
        self.total_damage_blocked = 0
        self.max_damage_turn = 0
        self.turn_darts = []
        self.round_bonus = 0
        self.round_power = 0
        self.alive = True
        self.columns = [["", "str"] for _ in range(9)]


class Game(cgame.Game):

    def __init__(
        self,
        display,
        game,
        nb_players,
        options,
        config,
        logs,
        rpi,
        dmd,
        video_player,
    ):
        super().__init__(
            display,
            game,
            nb_players,
            options,
            config,
            logs,
            rpi,
            dmd,
            video_player,
        )
        self.game_records = GAME_RECORDS
        self.nb_darts = NB_DARTS
        self.logo = LOGO
        self.headers = HEADERS
        self.options = options
        self.max_round = int(options.get("max_round", 10))
        self.start_hp = int(options.get("start_hp", 100))
        self.penality = int(options.get("penality", 10))
        self.speed = int(options.get("speed", 1000))
        self.rpi = rpi
        self.dmd = dmd
        self.video_player = video_player
        self.winner = None
        self.last_action_msg = ""
        self.last_combos_str = "AUCUN COMBO"

        self.margin = int(self.display.res["y"] * 0.01)
        self.margin_2 = self.margin * 2

    def pre_dart_check(
        self, players, actual_round, actual_player, player_launch
    ):
        """Phase d'initialisation en début de tour"""
        curr_player = players[actual_player]

        if player_launch == 1:
            curr_player.reset_darts()
            curr_player.turn_darts = []
            curr_player.round_points = 0
            curr_player.round_bonus = 0
            curr_player.round_power = 0
            curr_player.columns = [["", "str"] for _ in range(9)]

        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            for player in players:
                if hasattr(player, "reset_stats_game"):
                    player.reset_stats_game(self.start_hp)
                    player.reset_rounds(self.max_round)
                else:
                    player.hp = self.start_hp
                    player.pending_damage = 0
                    player.total_damage_dealt = 0
                    player.total_damage_blocked = 0
                    player.alive = True

        self.refresh_game_screen(
            players,
            actual_round,
            self.max_round,
            self.nb_darts,
            self.nb_darts,
            self.logo,
            self.headers,
            actual_player,
        )
        return 0

    def evaluate_combos(self, turn_darts):
        if len(turn_darts) == 0:
            return 0, []

        combo_bonus = 0
        combo_list = []

        sectors = [d["sector"] for d in turn_darts]
        mults = [d["mult"] for d in turn_darts]
        hits = [d["hit"] for d in turn_darts]

        # 1. BONUS INDIVIDUELS (DOUBLES, TRIPLES, SB ET DB)
        doubles_count = mults.count(2)
        triples_count = mults.count(3)
        
        sb_count = sum(1 for h in hits if h in ["25", "SB", "S25"])
        db_count = sum(1 for h in hits if h in ["50", "DB", "BULL"])

        if doubles_count > 0:
            bonus_d = doubles_count * 5
            combo_bonus += bonus_d
            combo_list.append(f"{doubles_count}x DOUBLE (+{bonus_d})")

        if triples_count > 0:
            bonus_t = triples_count * 5
            combo_bonus += bonus_t
            combo_list.append(f"{triples_count}x TRIPLE (+{bonus_t})")

        if sb_count > 0:
            bonus_sb = sb_count * 2
            combo_bonus += bonus_sb
            combo_list.append(f"{sb_count}x SINGLE BULL (+{bonus_sb})")

        if db_count > 0:
            bonus_db = db_count * 5
            combo_bonus += bonus_db
            combo_list.append(f"{db_count}x DOUBLE BULL (+{bonus_db})")

        # 2. COMBO TRICOLORE (Indépendant)
        has_single = 1 in mults
        has_double = 2 in mults
        has_triple = 3 in mults

        if has_single and has_double and has_triple:
            combo_bonus += 30
            combo_list.append("S-D-T (+30)")

        # 3. COMBOS DE VOLÉE GLOBALE & SECTEURS
        if len(turn_darts) == 3:
            if triples_count == 3:
                combo_bonus += 50
                combo_list.append("HAT-TRICK TRIPLE (+50)")

            if doubles_count == 3:
                combo_bonus += 50
                combo_list.append("HAT-TRICK DOUBLE (+50)")

            if db_count == 3:
                combo_bonus += 75
                combo_list.append("HAT-TRICK DOUBLE BULL (+75)")

            if all(str(s).upper() in ["25", "50", "BULL", "SB", "DB", "B"] for s in sectors):
                combo_bonus += 50
                combo_list.append("FULL BULL (+50)")

            try:
                sec_ints = [int(s) for s in sectors]
                if sec_ints[0] == sec_ints[1] == sec_ints[2] and sec_ints[0] != 0:
                    combo_bonus += 30
                    combo_list.append(f"3x SECTEUR {sec_ints[0]} (+30)")
            except ValueError:
                pass

            try:
                sec_nums = sorted([int(s) for s in sectors])
                if sec_nums[0] + 1 == sec_nums[1] and sec_nums[1] + 1 == sec_nums[2]:
                    combo_bonus += 20
                    combo_list.append(f"SUITE {sec_nums[0]}-{sec_nums[1]}-{sec_nums[2]} (+20)")
            except ValueError:
                pass

            # --- BONUS VOISINS (+15) ---
            dartboard_order = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]
            try:
                sec_ints = [int(s) for s in sectors]
                indices = []
                for s in sec_ints:
                    if s in dartboard_order:
                        indices.append(dartboard_order.index(s))
                
                if len(indices) == 3:
                    indices.sort()
                    is_neighbor = (
                        (indices[1] == indices[0] + 1 and indices[2] == indices[1] + 1) or
                        (indices[0] == 0 and indices[1] == 1 and indices[2] == 19) or
                        (indices[0] == 0 and indices[1] == 18 and indices[2] == 19)
                    )
                    if not is_neighbor:
                        diff1 = abs(indices[0] - indices[1])
                        diff2 = abs(indices[1] - indices[2])
                        if (diff1 == 1 or diff1 == 19) and (diff2 == 1 or diff2 == 19):
                            if len(set(sec_ints)) > 1:
                                is_neighbor = True

                    if is_neighbor:
                        combo_bonus += 15
                        combo_list.append("VOISINS (+15)")
            except ValueError:
                pass

            # --- BONUS POINTS (EXCLUSIF : SEUL LE PLUS HAUT S'APPLIQUE) ---
            raw_points_turn = sum(d["points"] for d in turn_darts)
            points_bonus = 0
            points_label = ""
            
            if raw_points_turn > 100:
                points_bonus = 10
                points_label = "> 100 PTS (+10)"
            elif raw_points_turn > 50:
                points_bonus = 5
                points_label = "> 50 PTS (+5)"
            elif raw_points_turn > 30:
                points_bonus = 2
                points_label = "> 30 PTS (+2)"
                
            if points_bonus > 0:
                combo_bonus += points_bonus
                combo_list.append(points_label)

            # --- BONUS EN COMMENTAIRE ---
            # blue_sectors = [dartboard_order[i] for i in range(0, len(dartboard_order), 2)]
            # white_sectors = [dartboard_order[i] for i in range(1, len(dartboard_order), 2)]
            # try:
            #     sec_ints = [int(s) for s in sectors]
            #     blue_hits = sum(1 for s in sec_ints if s in blue_sectors)
            #     white_hits = sum(1 for s in sec_ints if s in white_sectors)
            #
            #     if blue_hits == 3:
            #         combo_bonus += 10
            #         combo_list.append("3x SECTEURS BLEUS (+10)")
            #     elif white_hits == 3:
            #         combo_bonus += 10
            #         combo_list.append("3x SECTEURS BLANCS (+10)")
            # except ValueError:
            #     pass
            #
            # raw_points_turn = sum(d["points"] for d in turn_darts)
            # if raw_points_turn > 0:
            #     if raw_points_turn % 2 != 0:
            #         combo_bonus += 5
            #         combo_list.append("SCORE IMPAIR (+5)")
            #     else:
            #         combo_bonus += 5
            #         combo_list.append("SCORE PAIR (+5)")

        return combo_bonus, combo_list
        
        
    def post_dart_check(
        self, hit, players, actual_round, actual_player, player_launch
    ):
        handler = self.init_handler()
        handler["show"] = (players[actual_player].darts, hit, True)
        handler["sound"] = hit
        
        ### TROPHEES
        #ctrophies.process_single_dart(players[actual_player], hit)
        
        # On vérifie les trophées de volée uniquement à la 3ème fléchette
        if player_launch == 3:
            round_darts = players[actual_player].darts[-3:]
            ctrophies.check_and_unlock_trophies(players[actual_player], round_darts)

        #players[actual_player].darts_thrown += 1


        curr_player = players[actual_player]
        opponent = players[(actual_player + 1) % len(players)]

        score = self.score_map.get(hit, 0)
        
        # --- EXTRACTION ROBUSTE DU MULTIPLICATEUR ET DU SECTEUR ---
        if hit.startswith("D"):
            mult = 2
            sector = hit[1:]
        elif hit.startswith("T"):
            mult = 3
            sector = hit[1:]
        elif hit.startswith("S"):
            mult = 1
            sector = hit[1:]
        else:
            mult = 1
            sector = hit
        # ----------------------------------------------------------

        # 1. On enregistre la fléchette dans le tour du joueur
        curr_player.round_points += score
        curr_player.points += score
        curr_player.turn_darts.append(
            {"hit": hit, "points": score, "sector": sector, "mult": mult}
        )

        curr_player.columns[player_launch - 1] = (hit, "str")
        dmd_msg = ""


        # --- AJOUT POUR LES TROPHÉES ---
        curr_player.add_dart(actual_round, player_launch, hit, score=score)
        # ---------------------------------------------

        ### TROPHEES
        ctrophies.process_single_dart(players[actual_player], hit)
        
        # TROPHEES
        # On vérifie les trophées de volée uniquement à la 3ème fléchette
        if player_launch == 3:
            round_darts = players[actual_player].darts[-3:]
            ctrophies.check_and_unlock_trophies(players[actual_player], round_darts)



        # --- CALCULS MIS À JOUR EN TEMPS RÉEL À CHAQUE FLÉCHETTE ---
        raw_points = curr_player.round_points
        combo_bonus, combo_list = self.evaluate_combos(curr_player.turn_darts)
        
        curr_player.round_bonus = combo_bonus
        total_power = (raw_points + combo_bonus) // 2
        curr_player.round_power = total_power
        
        if combo_list:
            details_str = " | ".join(combo_list)
            self.last_combos_str = f"Bonus: {details_str} | Total Bonus: +{combo_bonus}"
        else:
            self.last_combos_str = "AUCUN COMBO | Total Bonus: +0"

        # 2. APPLICATION DU COMBAT (UNIQUEMENT À LA DERNIÈRE FLÉCHETTE DE LA VOLÉE)
        if player_launch == self.nb_darts:
            if total_power > getattr(curr_player, "max_damage_turn", 0):
                curr_player.max_damage_turn = total_power

            is_defending = curr_player.pending_damage > 0

            if is_defending:
                if total_power >= curr_player.pending_damage:
                    blocked = curr_player.pending_damage
                    riposte = total_power - curr_player.pending_damage

                    curr_player.total_damage_blocked += blocked
                    curr_player.pending_damage = 0

                    if riposte > 0:
                        opponent.pending_damage += riposte
                        curr_player.total_damage_dealt += riposte
                        self.last_action_msg = f"CONTRE-ATTAQUE ! PARADE DE {blocked} PV + RIPOSTE DE {riposte} PV !"
                        dmd_msg = f"CONTRE ATTAQUE! +{riposte} DMG"
                        self.display.speech(f"contre attaque de {riposte} points", speed=self.speed)
                    else:
                        self.last_action_msg = f"PARADE PARFAITE ! {blocked} PV ABSORBÉS !"
                        dmd_msg = "PARADE PARFAITE!"
                        self.display.speech(f"parade parfaite", speed=self.speed)

                    # Son d'origine supprimé pour la défense réussie/contre-attaque
                    handler["sound"] = None
                else:
                    initial_pending = curr_player.pending_damage  # On sauvegarde d'abord la valeur initiale
                    curr_player.total_damage_blocked += total_power
                    curr_player.pending_damage -= total_power
                    unblocked_damage = curr_player.pending_damage
                    
                    curr_player.hp -= unblocked_damage
                    curr_player.pending_damage = 0

                    self.last_action_msg = f"Dégât en attente : {initial_pending} - PARADE PARTIELLE ! {total_power} PV BLOQUÉS - subit {unblocked_damage} points de dégâts"
                    dmd_msg = f"PARADE -{unblocked_damage} PV"
                    
                    # Remplacement du son par la synthèse vocale
                    handler["sound"] = None
                    self.display.speech(f"subit {unblocked_damage} points de dommage", speed=self.speed)

                    if curr_player.hp <= 0:
                        curr_player.hp = 0
                        curr_player.alive = False
                        dmd_msg = f"K.O. SUR {curr_player.name}!"
                        self.display.play_sound("explosion")
            else:
                opponent.pending_damage += total_power
                curr_player.total_damage_dealt += total_power
                self.last_action_msg = f"ATTAQUE ! +{total_power} PWR (DÉGÂTS EN ATTENTE : {opponent.pending_damage} PV)"
                dmd_msg = f"ATTAQUE! +{total_power} DMG"

            if curr_player.pending_damage > 0:
                unblocked_damage = curr_player.pending_damage
                curr_player.hp -= unblocked_damage
                curr_player.pending_damage = 0

                self.last_action_msg += f" | SUBIT -{unblocked_damage} PV !"
                dmd_msg = f"PARADE MANQUÉE! -{unblocked_damage} PV"
                self.display.speech(f"subit {unblocked_damage} points de dommage", speed=self.speed)

                if curr_player.hp <= 0:
                    curr_player.hp = 0
                    curr_player.alive = False
                    dmd_msg = f"K.O. SUR {curr_player.name}!"
                    self.display.play_sound("explosion")
        else:
            self.last_action_msg = f"Fléchette {player_launch} lancée | Pts: {raw_points} | Bonus: +{combo_bonus} | Pwr: {total_power}"

        if self.dmd and dmd_msg:
            if hasattr(self.dmd, "clear_and_print_text"):
                self.dmd.clear_and_print_text(dmd_msg, 2)
            elif hasattr(self.dmd, "print_text"):
                self.dmd.print_text(dmd_msg)

        self.refresh_game_screen(
            players,
            actual_round,
            self.max_round,
            self.nb_darts,
            self.nb_darts,
            self.logo,
            self.headers,
            actual_player,
        )

        alive_players = [p for p in players if getattr(p, "alive", True) and p.hp > 0]
        if len(alive_players) <= 1 or (
            actual_round >= self.max_round and player_launch == self.nb_darts and actual_player == len(players) - 1
        ):
            # S'il reste des dégâts en attente (notamment suite à une contre-attaque au dernier tour),
            # ils sont immédiatement convertis en perte de PV définitive puisque la partie s'arrête.
            
            
            for p in players:
                if getattr(p, "pending_damage", 0) > 0:
                    unblocked = p.pending_damage
                    p.hp -= unblocked
                    p.pending_damage = 0
                    if p.hp <= 0:
                        p.hp = 0
                        p.alive = False

            self.winner = self.best_score(players)

            winning_player = players[self.winner]
            
            
            # --- CALCUL ET MISE À JOUR DES STATS (PPR, PPD, ETC.) ---
            for p in players:
                    p.stats["Points Per Round"] = str(p.show_ppr())
                    p.stats["Points Per Dart"] = str(p.show_ppd())
                    p.stats["Max Damage Turn"] = str(getattr(p, "max_damage_turn", 0))
                    p.stats["Total Parried"] = str(getattr(p, "total_damage_blocked", 0))
                # ---------------------------------------------------------
   
                

            ctrophies.check_game_end_stats(players, winning_player, "DUEL")
            
            handler["return_code"] = 3 if self.winner >= 0 else 2

        return handler
        
        '''
        alive_players = [p for p in players if getattr(p, "alive", True) and p.hp > 0]
        if len(alive_players) <= 1 or (
            actual_round >= self.max_round and player_launch == self.nb_darts and actual_player == len(players) - 1
        ):
            self.winner = self.best_score(players)
            handler["return_code"] = 3 if self.winner >= 0 else 2

        return handler
        '''
        
        
    def miss_button(self, players, actual_player, actual_round, player_launch):
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
        
        handler = self.init_handler()
        curr_player = players[actual_player]
        opponent = players[(actual_player + 1) % len(players)]
        
        # 1. Enregistrement du MISS sur la colonne de la fléchette
        curr_player.columns[player_launch - 1] = ("MISS", "str")
        
        self.display.play_sound("miss")

        # 2. Chaque MISS inflige immédiatement la pénalité fixe de PV
        curr_player.hp -= self.penality
        if curr_player.hp < 0:
            curr_player.hp = 0
            curr_player.alive = False

        self.last_action_msg = f"MISS ! -{self.penality} PV DIRECTS !"
        dmd_msg = f"MISS! -{self.penality} PV"

        # 3. Si c'est la 3ème fléchette (fin de volée)
        if player_launch == self.nb_darts:
            raw_points = curr_player.round_points
            combo_bonus, combo_list = self.evaluate_combos(curr_player.turn_darts)
            
            curr_player.round_bonus = combo_bonus
            total_power = (raw_points + combo_bonus) // 2
            curr_player.round_power = total_power
            
            if combo_list:
                details_str = " | ".join(combo_list)
                self.last_combos_str = f"Bonus: {details_str} | Total Bonus: +{combo_bonus}"
            else:
                self.last_combos_str = "AUCUN COMBO | Total Bonus: +0"

            is_defending = curr_player.pending_damage > 0

            if is_defending:
                if total_power >= curr_player.pending_damage:
                    blocked = curr_player.pending_damage
                    riposte = total_power - curr_player.pending_damage

                    curr_player.total_damage_blocked += blocked
                    curr_player.pending_damage = 0

                    if riposte > 0:
                        opponent.pending_damage += riposte
                        curr_player.total_damage_dealt += riposte
                        self.last_action_msg = f"MISS (3e) + PARADE TOTALE DE {blocked} PV + RIPOSTE DE {riposte} PV !"
                        dmd_msg = f"PARADE + RIPOSTE +{riposte}"
                        self.display.speech(f"contre attaque de {riposte} points", speed=self.speed)
                    else:
                        self.last_action_msg = f"MISS (3e) + PARADE PARFAITE ! {blocked} PV ABSORBÉS !"
                        dmd_msg = "PARADE PARFAITE!"
                        self.display.speech(f"parade parfaite", speed=self.speed)

                    handler["sound"] = None
                else:
                    curr_player.total_damage_blocked += total_power
                    curr_player.pending_damage -= total_power
                    unblocked_damage = curr_player.pending_damage
                    
                    curr_player.hp -= unblocked_damage
                    curr_player.pending_damage = 0

                    self.last_action_msg = f"MISS (3e) + PARADE PARTIELLE : -{unblocked_damage} PV ENCAISSÉS !"
                    dmd_msg = f"MALUS -{unblocked_damage} PV"
                    handler["sound"] = None
                    self.display.speech(f"subit {unblocked_damage} points de dommage", speed=self.speed)
            else:
                opponent.pending_damage += total_power
                curr_player.total_damage_dealt += total_power
                self.last_action_msg = f"MISS (3e) + ATTAQUE : +{total_power} PWR ENVOYÉS !"
                dmd_msg = f"ATTAQUE! +{total_power} DMG"

            if curr_player.hp <= 0:
                curr_player.hp = 0
                curr_player.alive = False
                dmd_msg = f"K.O. SUR {curr_player.name}!"
                self.display.play_sound("duel_winner")
        else:
            curr_player.round_bonus = 0
            curr_player.round_power = 0
            self.last_combos_str = "AUCUN COMBO (MISS) | Total Bonus: +0"

        if self.dmd:
            if hasattr(self.dmd, "clear_and_print_text"):
                self.dmd.clear_and_print_text(dmd_msg, 2)
            elif hasattr(self.dmd, "print_text"):
                self.dmd.print_text(dmd_msg)

        if curr_player.hp == 0 and not hasattr(self, "explosion_played"):
            self.display.play_sound("explosion")

        self.refresh_game_screen(
            players, actual_round, self.max_round, self.nb_darts, self.nb_darts, self.logo, self.headers, actual_player
        )

        if player_launch == self.nb_darts:
            alive_players = [p for p in players if getattr(p, "alive", True) and p.hp > 0]
            if len(alive_players) <= 1 or (
                actual_round >= self.max_round and player_launch == self.nb_darts and actual_player == len(players) - 1
            ):
                # S'il reste des dégâts en attente (notamment suite à une contre-attaque au dernier tour),
                # ils sont immédiatement convertis en perte de PV définitive puisque la partie s'arrête.
                for p in players:
                    if getattr(p, "pending_damage", 0) > 0:
                        unblocked = p.pending_damage
                        p.hp -= unblocked
                        p.pending_damage = 0
                        if p.hp <= 0:
                            p.hp = 0
                            p.alive = False

                self.winner = self.best_score(players)
                
                winning_player = players[self.winner] if self.winner >= 0 else players[0]

                
                # --- CALCUL ET MISE À JOUR DES STATS (PPR, PPD, ETC.) ---
                for p in players:
                    p.stats["Points Per Round"] = str(p.show_ppr())
                    p.stats["Points Per Dart"] = str(p.show_ppd())
                    p.stats["Max Damage Turn"] = str(getattr(p, "max_damage_turn", 0))
                    p.stats["Total Parried"] = str(getattr(p, "total_damage_blocked", 0))
                # ---------------------------------------------------------


                ctrophies.check_game_end_stats(players, winning_player, "DUEL")
                handler["return_code"] = 3 if self.winner >= 0 else 2

        return handler


    def pnj(self, players, actual_player, player_launch):
        curr_player = players[actual_player]
        if not getattr(curr_player, "alive", True):
            return "MISS"

        if curr_player.pending_damage > 0:
            targets = ["T20", "T19", "T18", "D20", "20"]
        else:
            if player_launch > 1 and len(curr_player.turn_darts) > 0:
                last_sector = curr_player.turn_darts[-1]["sector"]
                targets = [f"T{last_sector}", f"D{last_sector}", last_sector, "T20"]
            else:
                targets = ["T20", "T19", "T20", "20", "19"]

        accuracy = {"Easy": 0.35, "Medium": 0.60, "Hard": 0.85}.get(self.bot_level, 0.60)

        if random.random() < accuracy:
            chosen_hit = random.choice(targets[:2])
        else:
            chosen_hit = random.choice(targets[2:] + ["1", "5", "3", "MISS"])

        return chosen_hit

    def refresh_game_screen(
        self,
        players,
        actual_round,
        max_round,
        rem_darts,
        nb_darts,
        logo,
        headers,
        actual_player,
        TxtOnLogo=False,
        OnScreenButtons=None,
        showScores=True,
        end_of_game=False,
        endOfSet=None,
        Set=None,
        MaxSet=None,
    ):
        self.display.reset_background()

        REF_HEIGHT = 1080
        current_w, current_h = self.display.screen.get_size()
        scale_factor = current_h / REF_HEIGHT

        cell_bg = (18, 20, 26)
        header_bg = (30, 34, 45)
        border_col = (55, 62, 78)

        game_background = f"background_{logo.replace('!', '').split('.')[0]}"
        game_background = self.display.file_class.get_full_filename(game_background, 'images')
        if game_background is not None:
            self.display.display_background(image=game_background)
            self.display.save_background()
        else:
            self.display.blit_rect(0, 0, current_w, current_h, (12, 14, 20))

        box_w = int(current_w * 0.96)
        box_x = int((current_w - box_w) / 2)

        red_y = int(10 * scale_factor)
        red_h = int(int(REF_HEIGHT * 0.10) * scale_factor)

        curr_p = players[actual_player]
        is_defending = curr_p.pending_damage > 0
        status_label = " [MODE DÉFENSE / PARADE]" if is_defending else " [MODE ATTAQUE]"

        self.display.blit_rect(box_x, red_y, box_w, red_h, (35, 12, 16))
        pygame.draw.rect(self.display.screen, (255, 40, 40), (box_x, red_y, box_w, red_h), max(1, int(3 * scale_factor)))

        self.display.blit_text(
            f"DUEL  |  ROUND {actual_round}/{max_round}",
            box_x + int(15 * scale_factor), red_y + int(5 * scale_factor), box_w - int(40 * scale_factor), int(45 * scale_factor),
            color=(255, 215, 0), align='Center'
        )

        txt_color = (255, 120, 120) if is_defending else (120, 255, 120)
        self.display.blit_text(
            f"TOUR DE : {curr_p.name.upper()} ({curr_p.hp}/{self.start_hp} PV){status_label}",
            box_x + int(15 * scale_factor), red_y + int(48 * scale_factor), box_w - int(40 * scale_factor), int(45 * scale_factor),
            color=txt_color, align='Center'
        )

        table_y = red_y + red_h + int(current_h * 0.01)
        row_h = int(int(REF_HEIGHT * 0.054) * scale_factor)

        col_widths = [
            int(box_w * 0.18), int(box_w * 0.06), int(box_w * 0.06), int(box_w * 0.06),
            int(box_w * 0.08), int(box_w * 0.08), int(box_w * 0.08), int(box_w * 0.22), int(box_w * 0.18)
        ]

        curr_x = box_x
        for idx, h_name in enumerate(headers):
            w = col_widths[idx]
            self.display.blit_rect(curr_x, table_y, w, row_h, header_bg)
            pygame.draw.rect(self.display.screen, border_col, (curr_x, table_y, w, row_h), 1)
            self.display.blit_text(h_name, curr_x, table_y, w, row_h, color=(220, 220, 220), align="Center")
            curr_x += w

        for p_idx, p in enumerate(players):
            ry = table_y + (p_idx + 1) * row_h
            is_active = p_idx == actual_player
            bg_color = (35, 45, 60) if is_active else cell_bg

            curr_x = box_x
            for c_idx in range(len(headers)):
                w = col_widths[c_idx]
                self.display.blit_rect(curr_x, ry, w, row_h, bg_color)
                pygame.draw.rect(self.display.screen, border_col, (curr_x, ry, w, row_h), 1)

                if c_idx == 0:
                    is_alive = getattr(p, "alive", True)
                    txt_col = (255, 255, 255) if is_alive else (100, 100, 100)
                    self.display.blit_text(f"{p.name}{' (KO)' if not is_alive else ''}", curr_x + int(10 * scale_factor), ry, w - int(20 * scale_factor), row_h, color=txt_col, align="Left")
                elif c_idx in [1, 2, 3]:
                    val = p.columns[c_idx - 1][0] if hasattr(p, "columns") and len(p.columns[c_idx - 1]) > 0 else ""
                    self.display.blit_text(str(val), curr_x, ry, w, row_h, color=(220, 220, 220), align="Center")
                elif c_idx == 4:
                    self.display.blit_text(str(getattr(p, "round_points", 0)), curr_x, ry, w, row_h, color=(255, 255, 100), align="Center")
                elif c_idx == 5:
                    self.display.blit_text(str(getattr(p, "round_bonus", 0)), curr_x, ry, w, row_h, color=(255, 105, 180), align="Center")
                elif c_idx == 6:
                    self.display.blit_text(f"{getattr(p, 'round_power', 0)} PWR", curr_x, ry, w, row_h, color=(0, 200, 255), align="Center")
                elif c_idx == 7:
                    hp = getattr(p, "hp", 0)
                    pct = max(0.0, min(1.0, hp / float(self.start_hp)))
                    bar_w = int((w - int(20 * scale_factor)) * pct)
                    bar_h = int(row_h * 0.48)
                    bar_x = curr_x + int(10 * scale_factor)
                    bar_y = ry + int((row_h - bar_h) / 2)

                    hp_col = (50, 220, 50) if pct > 0.5 else ((230, 180, 30) if pct > 0.2 else (220, 40, 40))
                    self.display.blit_rect(bar_x, bar_y, bar_w, bar_h, hp_col)
                    pygame.draw.rect(self.display.screen, (200, 200, 200), (curr_x + int(10 * scale_factor), bar_y, w - int(20 * scale_factor), bar_h), 1)
                    self.display.blit_text(f"{hp}/{self.start_hp}", curr_x, ry, w, row_h, color=(255, 255, 255), align="Center")
                elif c_idx == 8:
                    dmg = getattr(p, "pending_damage", 0)
                    txt_col = (255, 60, 60) if dmg > 0 else (120, 120, 120)
                    self.display.blit_text(f"-{dmg} PV" if dmg > 0 else "AUCUNE", curr_x, ry, w, row_h, color=txt_col, align="Center")

                curr_x += w

            if is_active:
                pygame.draw.rect(self.display.screen, (255, 215, 0), (box_x, ry, box_w, row_h), max(1, int(2 * scale_factor)))

        table_bottom = table_y + (len(players) + 1) * row_h
        
        cyan_h = int(150 * scale_factor)    
        pink_h = int(160 * scale_factor)   
        info_h = int(270 * scale_factor)   
        
        total_blocks_h = cyan_h + pink_h + info_h
        available_space = current_h - table_bottom - int(10 * scale_factor)
        if available_space > total_blocks_h:
            spacing = (available_space - total_blocks_h) // 4
        else:
            spacing = int(4 * scale_factor)

        cyan_y = table_bottom + spacing
        pink_y = cyan_y + cyan_h + spacing
        info_y = pink_y + pink_h + spacing

        # --- A. BILAN COMBAT (BLEU) ---
        self.display.blit_rect(box_x, cyan_y, box_w, cyan_h, (12, 30, 40))
        pygame.draw.rect(self.display.screen, (0, 240, 255), (box_x, cyan_y, box_w, cyan_h), max(1, int(2 * scale_factor)))

        col_w_bilan = (box_w - int(60 * scale_factor)) // 2
        p1 = players[0]
        p2 = players[1] if len(players) > 1 else players[0]

        p1_dealt = getattr(p1, "total_damage_dealt", 0)
        p1_blocked = getattr(p1, "total_damage_blocked", 0)
        p1_avg = round(p1_dealt / float(actual_round), 1) if actual_round > 0 else 0

        p2_dealt = getattr(p2, "total_damage_dealt", 0)
        p2_blocked = getattr(p2, "total_damage_blocked", 0)
        p2_avg = round(p2_dealt / float(actual_round), 1) if actual_round > 0 else 0

        x_p1 = box_x + int(20 * scale_factor)
        self.display.blit_text(f"BILAN : {p1.name.upper()}", x_p1, cyan_y + int(6 * scale_factor), col_w_bilan, int(40 * scale_factor), color=(0, 220, 255), align="Left")
        self.display.blit_text(f"Dégâts infligés : {p1_dealt} PV ({p1_avg}/tour)", x_p1, cyan_y + int(55 * scale_factor), col_w_bilan, int(40 * scale_factor), color=(240, 240, 240), align="Left")
        self.display.blit_text(f"Dégâts parés : {p1_blocked} PV", x_p1, cyan_y + int(100 * scale_factor), col_w_bilan, int(40 * scale_factor), color=(100, 255, 120), align="Left")

        sep_x = box_x + (box_w // 2)
        pygame.draw.line(self.display.screen, (0, 150, 180), (sep_x, cyan_y + int(8 * scale_factor)), (sep_x, cyan_y + cyan_h - int(8 * scale_factor)), max(1, int(2 * scale_factor)))

        x_p2 = sep_x + int(20 * scale_factor)
        self.display.blit_text(f"BILAN : {p2.name.upper()}", x_p2, cyan_y + int(8 * scale_factor), col_w_bilan, int(40 * scale_factor), color=(0, 220, 255), align="Left")
        self.display.blit_text(f"Dégâts infligés : {p2_dealt} PV ({p2_avg}/tour)", x_p2, cyan_y + int(55 * scale_factor), col_w_bilan, int(40 * scale_factor), color=(240, 240, 240), align="Left")
        self.display.blit_text(f"Dégâts parés : {p2_blocked} PV", x_p2, cyan_y + int(100 * scale_factor), col_w_bilan, int(40 * scale_factor), color=(100, 255, 120), align="Left")

        # --- B. DERNIÈRE ACTION & BONUS COMBOS (ROSE) ---
        self.display.blit_rect(box_x, pink_y, box_w, pink_h, (35, 12, 30))
        pygame.draw.rect(self.display.screen, (255, 20, 147), (box_x, pink_y, box_w, pink_h), max(1, int(2 * scale_factor)))

        self.display.blit_text("DERNIÈRE ACTION & BONUS COMBOS (EN DIRECT)", box_x + int(10 * scale_factor), pink_y + int(8 * scale_factor), box_w - int(40 * scale_factor), int(40 * scale_factor), color=(255, 215, 0), align="Center")

        combos_txt = getattr(self, "last_combos_str", "AUCUN COMBO")
        self.display.blit_text(f"COMBOS : {combos_txt}", box_x + int(10 * scale_factor), pink_y + int(55 * scale_factor), box_w - int(40 * scale_factor), int(40 * scale_factor), color=(120, 255, 120), align="Center")

        action_txt = getattr(self, "last_action_msg", "AUCUNE ACTION")
        self.display.blit_text(action_txt, box_x + int(10 * scale_factor), pink_y + int(105 * scale_factor), box_w - int(40 * scale_factor), int(40 * scale_factor), color=(255, 255, 255), align="Center")

        # --- C. GUIDE DES BONUS (JAUNE) ---
        self.display.blit_rect(box_x, info_y, box_w, info_h, (25, 22, 10))
        pygame.draw.rect(self.display.screen, (230, 180, 30), (box_x, info_y, box_w, info_h), max(1, int(2 * scale_factor)))

        self.display.blit_text(
            "GUIDE DES BONUS",
            box_x + int(10 * scale_factor), info_y + int(6 * scale_factor), box_w - int(20 * scale_factor), int(40 * scale_factor),
            color=(255, 215, 0), align="Center"
        )
        
        col_w = box_w // 5
        start_text_y = info_y + int(42 * scale_factor)
        line_h = int(37 * scale_factor)

        for i in range(1, 5):
            sep_line_x = box_x + (col_w * i)
            pygame.draw.line(self.display.screen, (180, 140, 20), (sep_line_x, info_y + int(6 * scale_factor)), (sep_line_x, info_y + info_h - int(6 * scale_factor)), max(1, int(2 * scale_factor)))

        # 1. INDIVIDUEL
        c1_x = box_x
        self.display.blit_text("INDIVIDUEL", c1_x, start_text_y, col_w, int(40 * scale_factor), color=(255, 200, 0), align="Center")
        self.display.blit_text("1x Double = +5", c1_x, start_text_y + line_h, col_w, int(40 * scale_factor), color=(240, 240, 200), align="Center")
        self.display.blit_text("1x Triple = +5", c1_x, start_text_y + line_h * 2, col_w, int(40 * scale_factor), color=(240, 240, 200), align="Center")
        self.display.blit_text("1x Single Bull = +2", c1_x, start_text_y + line_h * 3, col_w, int(40 * scale_factor), color=(240, 240, 200), align="Center")
        self.display.blit_text("1x Double Bull = +5", c1_x, start_text_y + line_h * 4, col_w, int(40 * scale_factor), color=(240, 240, 200), align="Center")

        # 2. VOLÉE (avec S-D-T, Suite et Voisins)
        c2_x = box_x + col_w
        self.display.blit_text("VOLÉE", c2_x, start_text_y, col_w, int(40 * scale_factor), color=(255, 200, 0), align="Center")
        self.display.blit_text("S + D + T = +30", c2_x, start_text_y + line_h, col_w, int(40 * scale_factor), color=(240, 240, 200), align="Center")
        self.display.blit_text("Suite = +20", c2_x, start_text_y + line_h * 2, col_w, int(40 * scale_factor), color=(240, 240, 200), align="Center")
        self.display.blit_text("Voisins = +15", c2_x, start_text_y + line_h * 3, col_w, int(40 * scale_factor), color=(240, 240, 200), align="Center")

        # 3. POINTS
        c3_x = box_x + (col_w * 2)
        self.display.blit_text("POINTS", c3_x, start_text_y, col_w, int(40 * scale_factor), color=(255, 200, 0), align="Center")
        self.display.blit_text("> 30 pts = +2", c3_x, start_text_y + line_h, col_w, int(40 * scale_factor), color=(240, 240, 200), align="Center")
        self.display.blit_text("> 50 pts = +5", c3_x, start_text_y + line_h * 2, col_w, int(40 * scale_factor), color=(240, 240, 200), align="Center")
        self.display.blit_text("> 100 pts = +10", c3_x, start_text_y + line_h * 3, col_w, int(40 * scale_factor), color=(240, 240, 200), align="Center")

        # 4. MÊME CHIFFRE
        c4_x = box_x + (col_w * 3)
        self.display.blit_text("MÊME CHIFFRE", c4_x, start_text_y, col_w, int(40 * scale_factor), color=(255, 200, 0), align="Center")
        self.display.blit_text("3x Identiques = +30", c4_x, start_text_y + line_h * 2, col_w, int(40 * scale_factor), color=(240, 240, 200), align="Center")

        # 5. HAT-TRICK
        c5_x = box_x + (col_w * 4)
        self.display.blit_text("HAT TRICK", c5_x, start_text_y, col_w, int(40 * scale_factor), color=(255, 200, 0), align="Center")
        self.display.blit_text("3x Double = +50", c5_x, start_text_y + line_h, col_w, int(40 * scale_factor), color=(240, 240, 200), align="Center")
        self.display.blit_text("3x Triples = +50", c5_x, start_text_y + line_h * 2, col_w, int(40 * scale_factor), color=(240, 240, 200), align="Center")
        self.display.blit_text("3x Bull = +50", c5_x, start_text_y + line_h * 3, col_w, int(40 * scale_factor), color=(240, 240, 200), align="Center")
        self.display.blit_text("3x Double Bull = +75", c5_x, start_text_y + line_h * 4, col_w, int(40 * scale_factor), color=(240, 240, 200), align="Center")    
        
        click = None
        if not end_of_game and OnScreenButtons:
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

    def best_score(self, players):
        """Détermine le gagnant (joueur avec le plus de PV restants)"""
        best_player = None
        max_hp = -1
        for p in players:
            if p.hp > max_hp:
                max_hp = p.hp
                best_player = p.ident
        return best_player if best_player is not None else -1
