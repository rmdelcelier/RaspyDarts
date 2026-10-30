# -*- coding: utf-8 -*-
import json
import os
import pygame

from include import cemoji
from include import cfonts
from include import cpaths

# Dans le dossier du joueur (~/.raspydarts), avec ses scores et sa configuration
DATA_FILE = cpaths.trophies_file()


def average_ppd(stats, game):
    """
    PPD moyen du joueur à ce jeu (0.0 s'il n'y a jamais joué).
    Les parties jouées depuis que chaque fléchette est comptée une seule fois (10/2026) sont dans
    moyenne_ppd_<jeu> ; avant, moyenne_ppr_<jeu> : un vrai PPR en Ho-One, à peu près le PPD
    ailleurs (fléchettes comptées 1 à 3 fois selon le jeu). Il reste affiché tant que le joueur
    n'a pas rejoué à ce jeu.
    """
    if f"moyenne_ppd_{game}" in stats:
        return stats[f"moyenne_ppd_{game}"]
    legacy = stats.get(f"moyenne_ppr_{game}", stats.get(f"ppr_moyen_{game}", 0.0))
    return legacy / 3.0 if game == "ho-one" else legacy


def player_average_ppd(name, game):
    """
    PPD moyen d'un joueur (nom sans tenir compte de la casse) à ce jeu, 0.0 si inconnu
    """
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return 0.0
    for p_name, content in data.items():
        if p_name.strip().lower() == name.strip().lower() and isinstance(content, dict):
            return average_ppd(content.get("stats", {}), game)
    return 0.0

# Variable globale pour stocker l'instance d'affichage Pygame
_DISPLAY_INSTANCE = None

def init_trophy_display(display_instance):
    """Permet de lier l'affichage de Pygame au module des trophées pour les pop-ups."""
    global _DISPLAY_INSTANCE
    _DISPLAY_INSTANCE = display_instance

def play_trophy_sound():
    """Joue l'effet sonore du trophée sans superposition si un son est déjà en cours."""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(44100, -16, 2, 4096)
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sound_path = os.path.normpath(os.path.join(script_dir, "..", "sounds", "trophees.ogg"))
        
        if os.path.exists(sound_path):
            channel = pygame.mixer.Channel(7)
            if channel.get_busy():
                return

            sound = pygame.mixer.Sound(sound_path)
            channel.play(sound)
        else:
            print(f"[AVERTISSEMENT] Fichier audio introuvable : {sound_path}")
            
    except Exception as e:
        print(f"[AVERTISSEMENT] Impossible de lire le son du trophée : {e}")

def show_trophy_popup(trophy_id):
    """Affiche un pop-up visuel temporaire du trophée débloqué au centre de l'écran."""
    if not _DISPLAY_INSTANCE or not hasattr(_DISPLAY_INSTANCE, 'screen'):
        return

    try:
        screen = _DISPLAY_INSTANCE.screen
        screen_w = screen.get_width()
        screen_h = screen.get_height()

        # Dimensions et position du pop-up (centré sur l'écran)
        popup_w = int(screen_w * 0.65)
        popup_h = int(screen_h * 0.22)
        popup_x = (screen_w - popup_w) // 2
        popup_y = (screen_h - popup_h) // 2  # Centrage vertical exact

        # Surface du pop-up avec fond sombre et semi-transparent
        popup_surface = pygame.Surface((popup_w, popup_h))
        popup_surface.set_alpha(240)
        popup_surface.fill((25, 28, 36))

        screen.blit(popup_surface, (popup_x, popup_y))
        # Cadre doré élégant
        pygame.draw.rect(screen, (255, 215, 0), (popup_x, popup_y, popup_w, popup_h), 4)

        # Polices de texte ajustées à la taille du pop-up
        font_title = cfonts.font(popup_h * 0.30)
        font_desc = cfonts.font(popup_h * 0.25, bold=True)

        # Les coupes en emoji (police Noto Color Emoji ; sans elle, le titre seul, sans carre)
        title_surf = cemoji.render(font_title, "🏆 NOUVEAU TROPHÉE ! 🏆", (255, 215, 0))
        
        # Nettoyage de l'ID du trophée pour un affichage plus propre
        clean_name = str(trophy_id).replace("_", " ")
        desc_surf = font_desc.render(clean_name, True, (255, 255, 255))

        # Centrage des textes à l'intérieur du pop-up
        screen.blit(title_surf, (popup_x + (popup_w - title_surf.get_width()) // 2, popup_y + int(popup_h * 0.20)))
        screen.blit(desc_surf, (popup_x + (popup_w - desc_surf.get_width()) // 2, popup_y + int(popup_h * 0.58)))

        pygame.display.update()
        
        # Petite pause pour laisser le temps au joueur de lire (1,5 seconde)
        pygame.time.wait(1500)

    except Exception as e:
        print(f"[ERREUR] Affichage du pop-up trophée : {e}")

def save_unlocked_trophy(player_name, trophy_id):
    """Enregistre un trophée pour un joueur dans players_data.json s'il ne l'a pas déjà."""
    if not os.path.exists(DATA_FILE):
        data = {}
    else:
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    if player_name not in data:
        data[player_name] = {"trophies": [], "stats": {}}
    if "stats" not in data[player_name]:
        data[player_name]["stats"] = {}
    if "trophies" not in data[player_name]:
        data[player_name]["trophies"] = []

    if trophy_id not in data[player_name]["trophies"]:
        data[player_name]["trophies"].append(trophy_id)
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
            play_trophy_sound()
            show_trophy_popup(trophy_id) # Affichage visuel du pop-up
            print(f"[TROPHÉE] Nouveau trophée débloqué pour {player_name} : {trophy_id}")
        except Exception as e:
            print(f"[ERREUR] Impossible d'enregistrer le trophée : {e}")

def update_player_stat_and_check(player_name, stat_name, increment=1, thresholds=None):
    """Met à jour une statistique globale et ne débloque que le trophée le plus élevé atteint."""
    if not os.path.exists(DATA_FILE):
        data = {}
    else:
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    if player_name not in data:
        data[player_name] = {"trophies": [], "stats": {}}
    if "stats" not in data[player_name]:
        data[player_name]["stats"] = {}
    if "trophies" not in data[player_name]:
        data[player_name]["trophies"] = []

    old_val = data[player_name]["stats"].get(stat_name, 0)
    current_val = old_val + increment
    data[player_name]["stats"][stat_name] = current_val

    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[ERREUR] Impossible de sauvegarder les stats : {e}")

    newly_unlocked = []

    if thresholds:
        triggered_thresholds = []
        for limit, trophy_id in thresholds.items():
            if old_val < limit <= current_val:
                if trophy_id not in data[player_name]["trophies"]:
                    triggered_thresholds.append((limit, trophy_id))
        
        if triggered_thresholds:
            max_limit, max_trophy_id = max(triggered_thresholds, key=lambda x: x[0])
            save_unlocked_trophy(player_name, max_trophy_id)
            newly_unlocked.append(max_trophy_id)

    return newly_unlocked

def check_cricket_mickey_mark(player, darts, game):
    """Vérifie les marques au Cricket/Mickey pour toute la volée."""
    if not darts or not game:
        return []

    clean_darts = [str(d).upper() for d in darts if d is not None]
    if not clean_darts:
        return []

    game_headers = getattr(game, "headers", [])
    valid_targets = {str(h).upper() for h in game_headers}
    game_logo = getattr(game, "logo", "Cricket").upper()
    
    volley_marks = {}

    for dart in clean_darts:
        marks = 0
        target_name = ""

        if dart in ('SB', 'DB', 'B', '25', '50'):
            if 'B' in valid_targets or '25' in valid_targets or '50' in valid_targets:
                target_name = "BULL"
                marks = 2 if dart in ('DB', '50') else 1
        else:
            for prefix, multiplier in [('T', 3), ('D', 2), ('S', 1)]:
                if dart.startswith(prefix):
                    num_str = dart.replace(prefix, '')
                    if num_str in valid_targets:
                        target_name = num_str
                        marks = multiplier
                    break

        if marks > 0 and target_name:
            volley_marks[target_name] = volley_marks.get(target_name, 0) + marks

    unlocked_trophies = []
    prefix_stat = "cricket" if "CRICKET" in game_logo else "mickey"
    
    thresholds = {
        3: f"3_MARK_{game_logo}",
        4: f"4_MARK_{game_logo}",
        5: f"5_MARK_{game_logo}",
        6: f"6_MARK_{game_logo}",
        7: f"7_MARK_{game_logo}",
        8: f"8_MARK_{game_logo}",
        9: f"9_MARK_{game_logo}"
    }

    for target_name, total_marks in volley_marks.items():
        stat_key = f"{prefix_stat}_marks_{target_name}"
        new_trophies = update_player_stat_and_check(
            player.name, 
            stat_name=stat_key, 
            increment=total_marks, 
            thresholds=thresholds
        )
        if new_trophies:
            if isinstance(new_trophies, list):
                unlocked_trophies.extend(new_trophies)
            else:
                unlocked_trophies.append(new_trophies)

    return unlocked_trophies

def check_ho_one_finish_trophies(player, game_type, total_darts_used, winning_dart=None):
    """Vérifie les trophées spécifiques de fin de partie Ho-One."""
    if winning_dart and winning_dart.startswith('D'):
        try:
            num = winning_dart.replace('D', '')
            trophy_id = f"HO_ONE_FINIR_PAR_D{num}"
            save_unlocked_trophy(player.name, trophy_id)
        except Exception as e:
            print(f"[ERREUR] Finition Ho-One double : {e}")

    if game_type == 301:
        thresholds_301 = {6: "HO_ONE_301_6_DARTS", 7: "HO_ONE_301_7_DARTS", 8: "HO_ONE_301_8_DARTS", 9: "HO_ONE_301_9_DARTS", 12: "HO_ONE_301_12_DARTS"}
        if total_darts_used in thresholds_301:
            save_unlocked_trophy(player.name, thresholds_301[total_darts_used])
    elif game_type == 501:
        thresholds_501 = {9: "HO_ONE_501_9_DARTS", 10: "HO_ONE_501_10_DARTS", 11: "HO_ONE_501_11_DARTS", 12: "HO_ONE_501_12_DARTS", 15: "HO_ONE_501_15_DARTS"}
        if total_darts_used in thresholds_501:
            save_unlocked_trophy(player.name, thresholds_501[total_darts_used])

def check_and_unlock_trophies(player, darts):
    """Vérifie et met à jour les stats et trophées basés sur une volée de fléchettes."""
    p_name = getattr(player, "name", getattr(player, "ident", str(player)))

    if not darts or len(darts) < 3:
        return

    def clean_dart_format(d):
        if d is None:
            return 'MISS'
        s = str(d).upper().strip()
        if s in ['SB', '25']:
            return 'SB'
        if s in ['DB', '50']:
            return 'DB'
        if s in ['MISS', '0', '-1', '']:
            return 'MISS'
        if s.startswith(('S', 'D', 'T', 'MISS')):
            return s
        if s.isdigit():
            return f"S{s}"
        return s

    clean_darts = [clean_dart_format(d) for d in darts[:3]]
    dart1, dart2, dart3 = clean_darts[0], clean_darts[1], clean_darts[2]

    def parse_dart(d):
        if d == 'MISS': return 0
        s = str(d).upper()
        if s == 'SB': return 25
        if s == 'DB': return 50
        try:
            mult = 1
            if s.startswith('T'):
                mult = 3
                num_str = s[1:]
            elif s.startswith('D'):
                mult = 2
                num_str = s[1:]
            elif s.startswith('S'):
                mult = 1
                num_str = s[1:]
            else:
                num_str = s
            return int(num_str) * mult
        except:
            return 0

    sorted_darts = sorted(clean_darts, key=parse_dart)
    somme = sum(parse_dart(d) for d in clean_darts)

    if all(x == 'T20' for x in clean_darts):
        save_unlocked_trophy(p_name, "MAXIMUM_TON_80")
    elif all(x == 'S6' for x in clean_darts):
        save_unlocked_trophy(p_name, "DEVIL")
    elif all(x == 'T6' for x in clean_darts):
        save_unlocked_trophy(p_name, "TRIPLE_DEVIL")
    elif sorted_darts == ['S1', 'S5', 'S20']:
        save_unlocked_trophy(p_name, "BREAKFAST")
    elif sorted_darts == ['T1', 'T5', 'T20']:
        save_unlocked_trophy(p_name, "CHAMPAGNE_BREAKFAST")
    elif dart1 and dart1.startswith('T') and dart2 and dart2.startswith('T') and dart3 and dart3.startswith('T'):
        save_unlocked_trophy(p_name, "ROUND_OF_TERMS")
    elif all(x == 'S1' for x in clean_darts):
        save_unlocked_trophy(p_name, "BUCKET_OF_NAILS")
    elif sorted_darts == ['S5', 'S12', 'S20']:
        save_unlocked_trophy(p_name, "NOT_OLD")
    elif all(x == 'MISS' for x in clean_darts):
        save_unlocked_trophy(p_name, "WHITE_HORSE")
    elif all(x == 'DB' for x in clean_darts):
        save_unlocked_trophy(p_name, "BLACK_HAT_THREE_IN_THE_BLACK")
    elif all(x == 'SB' for x in clean_darts):
        save_unlocked_trophy(p_name, "RED_HAT")
    elif all(x in ['SB', 'DB'] for x in clean_darts):
        save_unlocked_trophy(p_name, "HAT_TRICK")
    elif all(x == dart1 for x in clean_darts) and dart1 not in ['MISS', '']:
        save_unlocked_trophy(p_name, "THREE_IN_A_BED")
        
    if dart3 and dart3 in ['T20', 'T19', 'T18', 'T17']:
        save_unlocked_trophy(p_name, "BAIL_OUT")

    if 'T20' in clean_darts:
        save_unlocked_trophy(p_name, "LIPSTICK")

    for i in range(1, 21):
        if all(x == f"D{i}" for x in clean_darts):
            save_unlocked_trophy(p_name, f"DOUBLE_3X_D{i}")
        if all(x == f"T{i}" for x in clean_darts):
            save_unlocked_trophy(p_name, f"TRIPLE_3X_T{i}")

    score_trophies = {
        22: "SWAN_LAKE", 33: "FEATHERS", 45: "BAG_O_NUTS", 66: "ROUTE_66",
        69: "HAPPY_MEAL", 77: "SUNSET_STRIP", 88: "2_FAT_LADIES", 95: "BABY_TON",
        100: "TON", 110: "TON_10", 120: "TON_20", 130: "TON_30", 140: "TON_40",
        150: "TON_50", 160: "TON_60", 170: "TON_70", 180: "TON_80"
    }
    
    if somme in score_trophies:
        save_unlocked_trophy(p_name, score_trophies[somme])
    
    if 100 < somme < 150:
        save_unlocked_trophy(p_name, "LOW_TON")
    elif 150 < somme < 180:
        save_unlocked_trophy(p_name, "HIGH_TON")

def check_game_end_stats(players, winner, game_name):
    """Enregistre proprement les statistiques de fin de partie individuelle et déclenche les trophées de victoires."""
    if not players:
        return

    game_key = str(game_name).strip().lower().replace(" ", "_")
    is_cricket_like = game_key in ["cricket", "mickey"]

    if not os.path.exists(DATA_FILE):
        data = {}
    else:
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = {}

    if "_global_stats" not in data:
        data["_global_stats"] = {}
    
    data["_global_stats"]["total_machine_parties"] = data["_global_stats"].get("total_machine_parties", 0) + 1
    game_real_count_key = f"parties_reelles_{game_key}"
    data["_global_stats"][game_real_count_key] = data["_global_stats"].get(game_real_count_key, 0) + 1

    winner_name = getattr(winner, "name", winner) if winner else None
    victory_thresholds = {10: "WINNER_10", 50: "WINNER_50", 100: "WINNER_100", 250: "WINNER_250"}

    for player in players:
        p_name = getattr(player, "name", player)

        if p_name not in data:
            data[p_name] = {"trophies": [], "stats": {}}
        if "stats" not in data[p_name]:
            data[p_name]["stats"] = {}
        if "trophies" not in data[p_name]:
            data[p_name]["trophies"] = []

        p_stats = data[p_name]["stats"]

        p_stats["total_parties_jouees"] = p_stats.get("total_parties_jouees", 0) + 1
        parties_ce_jeu_key = f"parties_jouees_{game_key}"
        p_stats[parties_ce_jeu_key] = p_stats.get(parties_ce_jeu_key, 0) + 1
        parties_ce_jeu = p_stats[parties_ce_jeu_key]

        ppd_actuel = float(player.show_ppd()) if hasattr(player, "show_ppd") else 0.0

        mpr_actuel = 0.0
        if is_cricket_like and hasattr(player, "show_mpr"):
            try: mpr_actuel = float(player.show_mpr())
            except: pass

        if is_cricket_like:
            cumul_mpr = p_stats.get(f"cumul_mpr_{game_key}", 0.0) + mpr_actuel
            p_stats[f"cumul_mpr_{game_key}"] = cumul_mpr
            p_stats[f"moyenne_mpr_{game_key}"] = round(cumul_mpr / parties_ce_jeu, 2)
        else:
            # PPD of the darts counted once (10/2026) : own count of games, the PPR before were
            # computed on darts counted 1 to 3 times depending on the game
            parties_ppd = p_stats.get(f"parties_ppd_{game_key}", 0) + 1
            cumul_ppd = p_stats.get(f"cumul_ppd_{game_key}", 0.0) + ppd_actuel
            p_stats[f"parties_ppd_{game_key}"] = parties_ppd
            p_stats[f"cumul_ppd_{game_key}"] = cumul_ppd
            p_stats[f"moyenne_ppd_{game_key}"] = round(cumul_ppd / parties_ppd, 2)

        is_winner = (winner_name and p_name == winner_name)
        if is_winner:
            old_wins = p_stats.get('wins', 0)
            new_wins = old_wins + 1
            p_stats['wins'] = new_wins
            p_stats[f"victoire_{game_key}"] = p_stats.get(f"victoire_{game_key}", 0) + 1

            for limit, trophy_id in victory_thresholds.items():
                if new_wins >= limit:
                    if trophy_id not in data[p_name]["trophies"]:
                        data[p_name]["trophies"].append(trophy_id)
                        play_trophy_sound()
                        show_trophy_popup(trophy_id)
                        print(f"[TROPHÉE] Nouveau trophée débloqué pour {p_name} : {trophy_id}")
        else:
            p_stats['losses'] = p_stats.get('losses', 0) + 1
            p_stats[f"defaite_{game_key}"] = p_stats.get(f"defaite_{game_key}", 0) + 1

    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[STATS FIN DE PARTIE] Jeu : {game_name} | Enregistrées avec succès.")
    except Exception as e:
        print(f"[ERREUR] Sauvegarde globale fin de partie : {e}")

def check_team_game_end_stats(players, winning_players, game_name):
    """Enregistre proprement les statistiques de fin de partie en équipe et déclenche les trophées."""
    if not players:
        return

    game_key = str(game_name).strip().lower().replace(" ", "_")
    is_cricket_like = game_key in ["cricket", "mickey"]
    winning_names_set = {getattr(w, "name", w) for w in winning_players} if winning_players else set()

    if not os.path.exists(DATA_FILE):
        data = {}
    else:
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = {}

    if "_global_stats" not in data:
        data["_global_stats"] = {}
    
    data["_global_stats"]["total_machine_parties"] = data["_global_stats"].get("total_machine_parties", 0) + 1
    game_real_count_key = f"parties_reelles_{game_key}"
    data["_global_stats"][game_real_count_key] = data["_global_stats"].get(game_real_count_key, 0) + 1

    victory_thresholds = {10: "WINNER_10", 50: "WINNER_50", 100: "WINNER_100", 250: "WINNER_250"}

    for player in players:
        p_name = getattr(player, "name", player)

        if p_name not in data:
            data[p_name] = {"trophies": [], "stats": {}}
        if "stats" not in data[p_name]:
            data[p_name]["stats"] = {}
        if "trophies" not in data[p_name]:
            data[p_name]["trophies"] = []

        p_stats = data[p_name]["stats"]

        p_stats["total_parties_jouees"] = p_stats.get("total_parties_jouees", 0) + 1
        parties_ce_jeu_key = f"parties_jouees_{game_key}"
        p_stats[parties_ce_jeu_key] = p_stats.get(parties_ce_jeu_key, 0) + 1
        parties_ce_jeu = p_stats[parties_ce_jeu_key]

        ppd_actuel = float(player.show_ppd()) if hasattr(player, "show_ppd") else 0.0

        mpr_actuel = 0.0
        if is_cricket_like and hasattr(player, "show_mpr"):
            try: mpr_actuel = float(player.show_mpr())
            except: pass

        if is_cricket_like:
            cumul_mpr = p_stats.get(f"cumul_mpr_{game_key}", 0.0) + mpr_actuel
            p_stats[f"cumul_mpr_{game_key}"] = cumul_mpr
            p_stats[f"moyenne_mpr_{game_key}"] = round(cumul_mpr / parties_ce_jeu, 2)
        else:
            # PPD of the darts counted once (10/2026) : own count of games, the PPR before were
            # computed on darts counted 1 to 3 times depending on the game
            parties_ppd = p_stats.get(f"parties_ppd_{game_key}", 0) + 1
            cumul_ppd = p_stats.get(f"cumul_ppd_{game_key}", 0.0) + ppd_actuel
            p_stats[f"parties_ppd_{game_key}"] = parties_ppd
            p_stats[f"cumul_ppd_{game_key}"] = cumul_ppd
            p_stats[f"moyenne_ppd_{game_key}"] = round(cumul_ppd / parties_ppd, 2)

        is_winner = (p_name in winning_names_set)
        if is_winner:
            old_wins = p_stats.get('wins', 0)
            new_wins = old_wins + 1
            p_stats['wins'] = new_wins
            p_stats[f"victoire_{game_key}"] = p_stats.get(f"victoire_{game_key}", 0) + 1

            for limit, trophy_id in victory_thresholds.items():
                if new_wins >= limit:
                    if trophy_id not in data[p_name]["trophies"]:
                        data[p_name]["trophies"].append(trophy_id)
                        play_trophy_sound()
                        show_trophy_popup(trophy_id)
                        print(f"[TROPHÉE] Nouveau trophée débloqué pour {p_name} : {trophy_id}")
        else:
            p_stats['losses'] = p_stats.get('losses', 0) + 1
            p_stats[f"defaite_{game_key}"] = p_stats.get(f"defaite_{game_key}", 0) + 1

    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"[STATS FIN DE PARTIE ÉQUIPE] Jeu : {game_name} | Enregistrées avec succès.")
    except Exception as e:
        print(f"[ERREUR] Sauvegarde globale fin de partie équipe : {e}")

def process_single_dart(player, dart):
    """Traite une fléchette unique dès son impact."""
    if dart is None:
        return
    
    clean_dart = str(dart).upper()
    
    update_player_stat_and_check(
        player.name, 
        "total_darts", 
        increment=1, 
        thresholds={100: "FLECHES_LANCEES_100", 500: "FLECHES_LANCEES_500", 1000: "FLECHES_LANCEES_1000", 2500: "FLECHES_LANCEES_2500"}
    )
    
    if clean_dart in ('0', 'MISS', '-1'):
        update_player_stat_and_check(player.name, "misses_count", 1)
    elif clean_dart == 'SB':
        update_player_stat_and_check(player.name, "sbulls_count", 1, {10: "BULLS_10", 50: "BULLS_50", 100: "BULLS_100"})
    elif clean_dart == 'DB':
        update_player_stat_and_check(player.name, "dbulls_count", 1, {10: "DBULLS_10", 50: "DBULLS_50", 100: "DBULLS_100"})
    elif clean_dart.startswith('D'):
        update_player_stat_and_check(player.name, "doubles_count", 1, {10: "TOUCH_DOUBLE_10", 50: "TOUCH_DOUBLE_50", 100: "TOUCH_DOUBLE_100"})
    elif clean_dart.startswith('T'):
        update_player_stat_and_check(player.name, "triples_count", 1, {10: "TOUCH_TRIPLE_10", 50: "TOUCH_TRIPLE_50", 100: "TOUCH_TRIPLE_100"})
    elif clean_dart.startswith('S'):
        update_player_stat_and_check(player.name, "singles_count", 1)
