import pygame
import os
import json
from include import craspberry

# --- MAPPING DES TOUCHES MATÉRIELLES / CLAVIER ---
ENTER_KEYS = ['enter', 'return', 'space', 'GAMEBUTTON', 'BTN_VALIDATE', 'VALIDATE', 'BTN_GAMEBUTTON', 'SB', 'DB', 'BTN_NEXTPLAYER']
ESCAPE_KEYS = ['escape', 'BTN_BACK', 'BACK', 'CANCEL', 'BTN_CANCEL']
# Right and left go through the lists too (a knob set on them)
UP_KEYS = ['up', 'BTN_UP', 'S20']
DOWN_KEYS = ['down', 'BTN_DOWN', 'S3']
LEFT_KEYS = ['left', 'BTN_LEFT', 'S11']
RIGHT_KEYS = ['right', 'BTN_RIGHT', 'S6']

# Fichiers
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Dans le dossier du joueur (~/.raspydarts), avec ses scores et sa configuration
from include import cfonts
from include import cpaths
from include.ctrophies import average_ppd
DATA_FILE = cpaths.trophies_file()

ALL_TROPHIES = [
    # --- 1. Combinaisons et figures de fléchettes ---
    {"id": "BAIL_OUT", "name": "Bail Out", "desc": "La 3ème fléchette est un gros triple", "img": "bail out", "category": "Combinaisons et figures"},
    {"id": "BLACK_HAT_THREE_IN_THE_BLACK", "name": "Black Hat", "desc": "Toucher 3 Double Bull", "img": "black hat", "category": "Combinaisons et figures"},
    {"id": "BREAKFAST", "name": "Breakfast", "desc": "Toucher S1, S5, S20 (Tous ordre)", "img": "breakfast", "category": "Combinaisons et figures"},
    {"id": "BUCKET_OF_NAILS", "name": "Bucket of Nails", "desc": "Toucher S1, S1, S1", "img": "bucket of nail", "category": "Combinaisons et figures"},
    {"id": "CHAMPAGNE_BREAKFAST", "name": "Champagne Breakfast", "desc": "Toucher T1, T5, T20 (Tous ordres)", "img": "champagne breakfast", "category": "Combinaisons et figures"},
    {"id": "DEVIL", "name": "Devil", "desc": "Toucher S6, S6, S6", "img": "devil", "category": "Combinaisons et figures"},
    {"id": "HAT_TRICK", "name": "Hat Trick", "desc": "Toucher n'importe quel Bull 3x", "img": "hat trick", "category": "Combinaisons et figures"},
    {"id": "LIPSTICK", "name": "Lipstick", "desc": "Toucher un T20 dans la volée", "img": "lipstick", "category": "Combinaisons et figures"},
    {"id": "MAXIMUM_TON_80", "name": "Maximum Ton 80", "desc": "Toucher T20, T20, T20", "img": "maximum ton", "category": "Combinaisons et figures"},
    {"id": "NOT_OLD", "name": "Not Old", "desc": "Toucher S5, S12, S20 (Tous ordres)", "img": "not old", "category": "Combinaisons et figures"},
    {"id": "RED_HAT", "name": "Red Hat", "desc": "Toucher 3 simple bull", "img": "red hat", "category": "Combinaisons et figures"},
    {"id": "ROUND_OF_TERMS", "name": "Round of Terms", "desc": "Toucher n'importe quel Triple 3x", "img": "round of term", "category": "Combinaisons et figures"},
    {"id": "THREE_IN_A_BED", "name": "Three in a Bed", "desc": "3 fois le même chiffre", "img": "three on the bed", "category": "Combinaisons et figures"},
    {"id": "TRIPLE_DEVIL", "name": "Triple Devil", "desc": "Toucher T6, T6, T6", "img": "devil_triple", "category": "Combinaisons et figures"},
    {"id": "WHITE_HORSE", "name": "White Horse", "desc": "Toucher 3 Triples différents au cricket", "img": "white horse", "category": "Combinaisons et figures"},

    # --- 2. Scores spécifiques de volée / Tons ---
    {"id": "2_FAT_LADIES", "name": "2 Fat Ladies", "desc": "Marquer 88 points", "img": "2fat ladies", "category": "Scores spécifiques"},
    {"id": "BABY_TON", "name": "Baby Ton", "desc": "Marquer 95 points", "img": "baby_ton", "category": "Scores spécifiques"},
    {"id": "BAG_O_NUTS", "name": "Bag O Nuts", "desc": "Marquer 45 points", "img": "bag o nuts", "category": "Scores spécifiques"},
    {"id": "FEATHERS", "name": "Feathers", "desc": "Marquer 33 points", "img": "FEATHERS", "category": "Scores spécifiques"},
    {"id": "HAPPY_MEAL", "name": "Happy Meal", "desc": "Marquer 69 points", "img": "happy meal", "category": "Scores spécifiques"},
    {"id": "HIGH_TON", "name": "High Ton", "desc": "Score total entre 151 et 179 points", "img": "high ton", "category": "Scores spécifiques"},
    {"id": "LOW_TON", "name": "Low Ton", "desc": "Score total entre 101 et 149 points", "img": "low ton", "category": "Scores spécifiques"},
    {"id": "ROUTE_66", "name": "Route 66", "desc": "Marquer 66 points", "img": "route 66", "category": "Scores spécifiques"},
    {"id": "SUNSET_STRIP", "name": "Sunset Strip", "desc": "Marquer 77 points", "img": "sunset strip", "category": "Scores spécifiques"},
    {"id": "SWAN_LAKE", "name": "Swan Lake", "desc": "Marquer 22 points", "img": "swan lake", "category": "Scores spécifiques"},
    {"id": "TON", "name": "Ton", "desc": "Marquer 100 points", "img": "TON", "category": "Scores spécifiques"},
    {"id": "TON_10", "name": "Ton 10", "desc": "Marquer 110 points", "img": "TON10", "category": "Scores spécifiques"},
    {"id": "TON_20", "name": "Ton 20", "desc": "Marquer 120 points", "img": "TON20", "category": "Scores spécifiques"},
    {"id": "TON_30", "name": "Ton 30", "desc": "Marquer 130 points", "img": "TON30", "category": "Scores spécifiques"},
    {"id": "TON_40", "name": "Ton 40", "desc": "Marquer 140 points", "img": "ton40", "category": "Scores spécifiques"},
    {"id": "TON_50", "name": "Ton 50", "desc": "Marquer 150 points", "img": "ton50", "category": "Scores spécifiques"},
    {"id": "TON_60", "name": "Ton 60", "desc": "Marquer 160 points", "img": "ton60", "category": "Scores spécifiques"},
    {"id": "TON_70", "name": "Ton 70", "desc": "Marquer 170 points", "img": "ton70", "category": "Scores spécifiques"},
    {"id": "TON_80", "name": "Ton 80", "desc": "Réaliser un 180 aux fléchettes", "img": "ton80", "category": "Scores spécifiques"},

    # --- 3. Doubles ---
    {"id": "DOUBLE_3X_D1", "name": "Double - 3x D1", "desc": "Toucher 3x D1 en une volée", "img": "double - 3xd1", "category": "Doubles"},
    {"id": "DOUBLE_3X_D2", "name": "Double - 3x D2", "desc": "Toucher 3x D2 en une volée", "img": "double - 3xd2", "category": "Doubles"},
    {"id": "DOUBLE_3X_D3", "name": "Double - 3x D3", "desc": "Toucher 3x D3 en une volée", "img": "double - 3xd3", "category": "Doubles"},
    {"id": "DOUBLE_3X_D4", "name": "Double - 3x D4", "desc": "Toucher 3x D4 en une volée", "img": "double - 3xd4", "category": "Doubles"},
    {"id": "DOUBLE_3X_D5", "name": "Double - 3x D5", "desc": "Toucher 3x D5 en une volée", "img": "double - 3xd5", "category": "Doubles"},
    {"id": "DOUBLE_3X_D6", "name": "Double - 3x D6", "desc": "Toucher 3x D6 en une volée", "img": "double - 3xd6", "category": "Doubles"},
    {"id": "DOUBLE_3X_D7", "name": "Double - 3x D7", "desc": "Toucher 3x D7 en une volée", "img": "double - 3xd7", "category": "Doubles"},
    {"id": "DOUBLE_3X_D8", "name": "Double - 3x D8", "desc": "Toucher 3x D8 en une volée", "img": "double - 3xd8", "category": "Doubles"},
    {"id": "DOUBLE_3X_D9", "name": "Double - 3x D9", "desc": "Toucher 3x D9 en une volée", "img": "double - 3xd9", "category": "Doubles"},
    {"id": "DOUBLE_3X_D10", "name": "Double - 3x D10", "desc": "Toucher 3x D10 en une volée", "img": "double - 3xd10", "category": "Doubles"},
    {"id": "DOUBLE_3X_D11", "name": "Double - 3x D11", "desc": "Toucher 3x D11 en une volée", "img": "double - 3xd11", "category": "Doubles"},
    {"id": "DOUBLE_3X_D12", "name": "Double - 3x D12", "desc": "Toucher 3x D12 en une volée", "img": "double - 3xd12", "category": "Doubles"},
    {"id": "DOUBLE_3X_D13", "name": "Double - 3x D13", "desc": "Toucher 3x D13 en une volée", "img": "double - 3xd13", "category": "Doubles"},
    {"id": "DOUBLE_3X_D14", "name": "Double - 3x D14", "desc": "Toucher 3x D14 en une volée", "img": "double - 3xd14", "category": "Doubles"},
    {"id": "DOUBLE_3X_D15", "name": "Double - 3x D15", "desc": "Toucher 3x D15 en une volée", "img": "double - 3xd15", "category": "Doubles"},
    {"id": "DOUBLE_3X_D16", "name": "Double - 3x D16", "desc": "Toucher 3x D16 en une volée", "img": "double - 3xd16", "category": "Doubles"},
    {"id": "DOUBLE_3X_D17", "name": "Double - 3x D17", "desc": "Toucher 3x D17 en une volée", "img": "double - 3xd17", "category": "Doubles"},
    {"id": "DOUBLE_3X_D18", "name": "Double - 3x D18", "desc": "Toucher 3x D18 en une volée", "img": "double - 3xd18", "category": "Doubles"},
    {"id": "DOUBLE_3X_D19", "name": "Double - 3x D19", "desc": "Toucher 3x D19 en une volée", "img": "double - 3xd19", "category": "Doubles"},
    {"id": "DOUBLE_3X_D20", "name": "Double - 3x D20", "desc": "Toucher 3x D20 en une volée", "img": "double - 3xd20", "category": "Doubles"},

    # --- 4. Triples ---
    {"id": "TRIPLE_3X_T1", "name": "Triple - 3x T1", "desc": "Toucher 3x T1 en une volée", "img": "triple - 3xt1", "category": "Triples"},
    {"id": "TRIPLE_3X_T2", "name": "Triple - 3x T2", "desc": "Toucher 3x T2 en une volée", "img": "triple - 3xt2", "category": "Triples"},
    {"id": "TRIPLE_3X_T3", "name": "Triple - 3x T3", "desc": "Toucher 3x T3 en une volée", "img": "triple - 3xt3", "category": "Triples"},
    {"id": "TRIPLE_3X_T4", "name": "Triple - 3x T4", "desc": "Toucher 3x T4 en une volée", "img": "triple - 3xt4", "category": "Triples"},
    {"id": "TRIPLE_3X_T5", "name": "Triple - 3x T5", "desc": "Toucher 3x T5 en une volée", "img": "triple - 3xt5", "category": "Triples"},
    {"id": "TRIPLE_3X_T6", "name": "Triple - 3x T6", "desc": "Toucher 3x T6 en une volée", "img": "triple - 3xt6", "category": "Triples"},
    {"id": "TRIPLE_3X_T7", "name": "Triple - 3x T7", "desc": "Toucher 3x T7 en une volée", "img": "triple - 3xt7", "category": "Triples"},
    {"id": "TRIPLE_3X_T8", "name": "Triple - 3x T8", "desc": "Toucher 3x T8 en une volée", "img": "triple - 3xt8", "category": "Triples"},
    {"id": "TRIPLE_3X_T9", "name": "Triple - 3x T9", "desc": "Toucher 3x T9 en une volée", "img": "triple - 3xt9", "category": "Triples"},
    {"id": "TRIPLE_3X_T10", "name": "Triple - 3x T10", "desc": "Toucher 3x T10 en une volée", "img": "triple - 3xt10", "category": "Triples"},
    {"id": "TRIPLE_3X_T11", "name": "Triple - 3x T11", "desc": "Toucher 3x T11 en une volée", "img": "triple - 3xt11", "category": "Triples"},
    {"id": "TRIPLE_3X_T12", "name": "Triple - 3x T12", "desc": "Toucher 3x T12 en une volée", "img": "triple - 3xt12", "category": "Triples"},
    {"id": "TRIPLE_3X_T13", "name": "Triple - 3x T13", "desc": "Toucher 3x T13 en une volée", "img": "triple - 3xt13", "category": "Triples"},
    {"id": "TRIPLE_3X_T14", "name": "Triple - 3x T14", "desc": "Toucher 3x T14 en une volée", "img": "triple - 3xt14", "category": "Triples"},
    {"id": "TRIPLE_3X_T15", "name": "Triple - 3x T15", "desc": "Toucher 3x T15 en une volée", "img": "triple - 3xt15", "category": "Triples"},
    {"id": "TRIPLE_3X_T16", "name": "Triple - 3x T16", "desc": "Toucher 3x T16 en une volée", "img": "triple - 3xt16", "category": "Triples"},
    {"id": "TRIPLE_3X_T17", "name": "Triple - 3x T17", "desc": "Toucher 3x T17 en une volée", "img": "triple - 3xt17", "category": "Triples"},
    {"id": "TRIPLE_3X_T18", "name": "Triple - 3x T18", "desc": "Toucher 3x T18 en une volée", "img": "triple - 3xt18", "category": "Triples"},
    {"id": "TRIPLE_3X_T19", "name": "Triple - 3x T19", "desc": "Toucher 3x T19 en une volée", "img": "triple - 3xt19", "category": "Triples"},
    {"id": "TRIPLE_3X_T20", "name": "Triple - 3x T20", "desc": "Toucher 3x T20 en une volée", "img": "triple - 3xt20", "category": "Triples"},

    # --- 5. Ho-One ---
    {"id": "HO_ONE_FINIR_PAR_D1", "name": "Ho-One - Finir par D1", "desc": "Terminer en finissant par D1", "img": "ho-one - finish d1", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D2", "name": "Ho-One - Finir par D2", "desc": "Terminer en finissant par D2", "img": "ho-one - finish d2", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D3", "name": "Ho-One - Finir par D3", "desc": "Terminer en finissant par D3", "img": "ho-one - finish d3", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D4", "name": "Ho-One - Finir par D4", "desc": "Terminer en finissant par D4", "img": "ho-one - finish d4", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D5", "name": "Ho-One - Finir par D5", "desc": "Terminer en finissant par D5", "img": "ho-one - finish d5", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D6", "name": "Ho-One - Finir par D6", "desc": "Terminer en finissant par D6", "img": "ho-one - finish d6", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D7", "name": "Ho-One - Finir par D7", "desc": "Terminer en finissant par D7", "img": "ho-one - finish d7", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D8", "name": "Ho-One - Finir par D8", "desc": "Terminer en finissant par D8", "img": "ho-one - finish d8", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D9", "name": "Ho-One - Finir par D9", "desc": "Terminer en finissant par D9", "img": "ho-one - finish d9", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D10", "name": "Ho-One - Finir par D10", "desc": "Terminer en finissant par D10", "img": "ho-one - finish d10", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D11", "name": "Ho-One - Finir par D11", "desc": "Terminer en finissant par D11", "img": "ho-one - finish d11", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D12", "name": "Ho-One - Finir par D12", "desc": "Terminer en finissant par D12", "img": "ho-one - finish d12", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D13", "name": "Ho-One - Finir par D13", "desc": "Terminer en finissant par D13", "img": "ho-one - finish d13", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D14", "name": "Ho-One - Finir par D14", "desc": "Terminer en finissant par D14", "img": "ho-one - finish d14", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D15", "name": "Ho-One - Finir par D15", "desc": "Terminer en finissant par D15", "img": "ho-one - finish d15", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D16", "name": "Ho-One - Finir par D16", "desc": "Terminer en finissant par D16", "img": "ho-one - finish d16", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D17", "name": "Ho-One - Finir par D17", "desc": "Terminer en finissant par D17", "img": "ho-one - finish d17", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D18", "name": "Ho-One - Finir par D18", "desc": "Terminer en finissant par D18", "img": "ho-one - finish d18", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D19", "name": "Ho-One - Finir par D19", "desc": "Terminer en finissant par D19", "img": "ho-one - finish d19", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_D20", "name": "Ho-One - Finir par D20", "desc": "Terminer en finissant par D20", "img": "ho-one - finish d20", "category": "Ho-One"},
    {"id": "HO_ONE_FINIR_PAR_DB", "name": "Ho-One - Finir par DB", "desc": "Terminer en finissant par DB", "img": "ho-one - finish db", "category": "Ho-One"},
    {"id": "HO_ONE_301_6_DARTS", "name": "301 - 6 fléchettes", "desc": "Terminer le 301 en 6 fléchettes", "img": "ho-one - 301 - 6  fleches", "category": "Ho-One"},
    {"id": "HO_ONE_301_7_DARTS", "name": "301 - 7 fléchettes", "desc": "Terminer le 301 en 7 fléchettes", "img": "ho-one - 301 - 7  fleches", "category": "Ho-One"},
    {"id": "HO_ONE_301_8_DARTS", "name": "301 - 8 fléchettes", "desc": "Terminer le 301 en 8 fléchettes", "img": "ho-one - 301 - 8  fleches", "category": "Ho-One"},
    {"id": "HO_ONE_301_9_DARTS", "name": "301 - 9 fléchettes", "desc": "Terminer le 301 en 9 fléchettes", "img": "ho-one - 301 - 9  fleches", "category": "Ho-One"},
    {"id": "HO_ONE_301_12_DARTS", "name": "301 - 12 fléchettes", "desc": "Terminer le 301 en 12 fléchettes", "img": "ho-one - 301 - 12 fleches", "category": "Ho-One"},
    {"id": "HO_ONE_501_9_DARTS", "name": "501 - 9 fléchettes", "desc": "Terminer le 501 en 9 fléchettes (Perfect)", "img": "ho-one - 501 - 9 fleches", "category": "Ho-One"},
    {"id": "HO_ONE_501_10_DARTS", "name": "501 - 10 fléchettes", "desc": "Terminer le 501 en 10 fléchettes", "img": "ho-one - 501 - 10 fleches", "category": "Ho-One"},
    {"id": "HO_ONE_501_11_DARTS", "name": "501 - 11 fléchettes", "desc": "Terminer le 501 en 11 fléchettes", "img": "ho-one - 501 - 11 fleches", "category": "Ho-One"},
    {"id": "HO_ONE_501_12_DARTS", "name": "501 - 12 fléchettes", "desc": "Terminer le 501 en 12 fléchettes", "img": "ho-one - 501 - 12 fleches", "category": "Ho-One"},
    {"id": "HO_ONE_501_15_DARTS", "name": "501 - 15 fléchettes", "desc": "Terminer le 501 en 15 fléchettes", "img": "ho-one - 501 - 15 fleches", "category": "Ho-One"},

    # --- 6. Succès de progression ---
    {"id": "FLECHES_LANCEES_100", "name": "Fléches Lancées (I)", "desc": "Lancer 100 fléchettes", "img": "fleches lancees - 100", "category": "Succès de progression"},
    {"id": "WINNER_10", "name": "Winner (I)", "desc": "Gagner 10 parties", "img": "winner - 10", "category": "Succès de progression"},
    {"id": "BULLS_10", "name": "Simple Bull (I)", "desc": "Toucher le simple bull 10 fois", "img": "bulls 10", "category": "Succès de progression"},
    {"id": "BULLS_50", "name": "Simple Bull (II)", "desc": "Atteindre le bull 50 fois", "img": "bulls 50", "category": "Succès de progression"},
    {"id": "BULLS_100", "name": "Simple Bull (III)", "desc": "Toucher le bull 100 fois", "img": "bulls 100", "category": "Succès de progression"},
    {"id": "FLECHES_LANCEES_500", "name": "Fléches Lancées (II)", "desc": "Lancer 500 fléchettes", "img": "fleches lancees - 500", "category": "Succès de progression"},
    {"id": "WINNER_50", "name": "Winner (II)", "desc": "Gagner 50 parties", "img": "winner - 50", "category": "Succès de progression"},
    {"id": "DBULLS_10", "name": "Double Bull (I)", "desc": "Toucher le double bull 10 fois", "img": "dbulls 10", "category": "Succès de progression"},
    {"id": "DBULLS_50", "name": "Double Bull (II)", "desc": "Toucher le double bull 50 fois", "img": "dbulls 50", "category": "Succès de progression"},
    {"id": "DBULLS_100", "name": "Double Bull (III)", "desc": "Toucher le double bull 100 fois", "img": "dbulls 100", "category": "Succès de progression"},
    {"id": "FLECHES_LANCEES_1000", "name": "Fléches Lancées (III)", "desc": "Lancer 1000 fléchettes", "img": "fleches lancees - 1000", "category": "Succès de progression"},
    {"id": "WINNER_100", "name": "Winner (III)", "desc": "Gagner 100 parties", "img": "winner - 100", "category": "Succès de progression"},
    {"id": "TOUCH_DOUBLE_10", "name": "Double (I)", "desc": "Toucher un double 10 fois", "img": "double - 10", "category": "Succès de progression"},
    {"id": "TOUCH_DOUBLE_50", "name": "Double (II)", "desc": "Toucher un double 50 fois", "img": "double - 50", "category": "Succès de progression"},
    {"id": "TOUCH_DOUBLE_100", "name": "Double (III)", "desc": "Toucher un double 100 fois", "img": "double - 100", "category": "Succès de progression"},
    {"id": "FLECHES_LANCEES_2500", "name": "Fléches Lancées (IV)", "desc": "Lancer 2500 fléchettes", "img": "fleches lancees - 2500", "category": "Succès de progression"},
    {"id": "WINNER_250", "name": "Winner (IV)", "desc": "Gagner 250 parties", "img": "winner - 250", "category": "Succès de progression"},
    {"id": "TOUCH_TRIPLE_10", "name": "Triple (I)", "desc": "Toucher un triple 10 fois", "img": "triple - 10", "category": "Succès de progression"},
    {"id": "TOUCH_TRIPLE_50", "name": "Triple (II)", "desc": "Toucher un triple 50 fois", "img": "triple - 50", "category": "Succès de progression"},
    {"id": "TOUCH_TRIPLE_100", "name": "Triple (III)", "desc": "Toucher un triple 100 fois", "img": "triple - 100", "category": "Succès de progression"},

    # --- 8. CRICKET ---
    {"id": "3_MARK_CRICKET", "name": "3 Mark Cricket", "desc": "Réaliser 3 marques au Cricket", "img": "cricket 3 mark", "category": "Cricket / Mickey"},
    {"id": "4_MARK_CRICKET", "name": "4 Mark Cricket", "desc": "Réaliser 4 marques au Cricket", "img": "cricket 4 mark", "category": "Cricket / Mickey"},
    {"id": "5_MARK_CRICKET", "name": "5 Mark Cricket", "desc": "Réaliser 5 marques au Cricket", "img": "cricket 5 mark", "category": "Cricket / Mickey"},
    {"id": "6_MARK_CRICKET", "name": "6 Mark Cricket", "desc": "Réaliser 6 marques au Cricket", "img": "cricket 6 mark", "category": "Cricket / Mickey"},
    {"id": "7_MARK_CRICKET", "name": "7 Mark Cricket", "desc": "Réaliser 7 marques au Cricket", "img": "cricket 7 mark", "category": "Cricket / Mickey"},
    {"id": "8_MARK_CRICKET", "name": "8 Mark Cricket", "desc": "Réaliser 8 marques au Cricket", "img": "cricket 8 mark", "category": "Cricket / Mickey"},
    {"id": "9_MARK_CRICKET", "name": "9 Mark Cricket", "desc": "Réaliser 9 marques au Cricket", "img": "cricket 9 mark", "category": "Cricket / Mickey"},
    {"id": "3_MARK_MICKEY", "name": "3 Mark Mickey", "desc": "Réaliser 3 marques au Mickey", "img": "mickey 3 mark", "category": "Cricket / Mickey"},
    {"id": "4_MARK_MICKEY", "name": "4 Mark Mickey", "desc": "Réaliser 4 marques au Mickey", "img": "mickey 4 mark", "category": "Cricket / Mickey"},
    {"id": "5_MARK_MICKEY", "name": "5 Mark Mickey", "desc": "Réaliser 5 marques au Mickey", "img": "mickey 5 mark", "category": "Cricket / Mickey"},
    {"id": "6_MARK_MICKEY", "name": "6 Mark Mickey", "desc": "Réaliser 6 marques au Mickey", "img": "mickey 6 mark", "category": "Cricket / Mickey"},
    {"id": "7_MARK_MICKEY", "name": "7 Mark Mickey", "desc": "Réaliser 7 marques au Mickey", "img": "mickey 7 mark", "category": "Cricket / Mickey"},
    {"id": "8_MARK_MICKEY", "name": "8 Mark Mickey", "desc": "Réaliser 8 marques au Mickey", "img": "mickey 8 mark", "category": "Cricket / Mickey"},
    {"id": "9_MARK_MICKEY", "name": "9 Mark Mickey", "desc": "Réaliser 9 marques au Mickey", "img": "mickey 9 mark", "category": "Cricket / Mickey"}
]


NAMES_LEVELS = {
    1: "Novice I",
    2: "Novice II",
    3: "Amateur I",
    4: "Amateur II",
    5: "Amateur III",
    6: "Amateur IV",
    7: "Amateur V",
    8: "Régulier I",
    9: "Régulier II",
    10: "Régulier III",
    11: "Régulier IV",
    12: "Régulier V",
    13: "Confirmé I",
    14: "Confirmé II",
    15: "Confirmé III",
    16: "Vétéran I",
    17: "Vétéran II",
    18: "Vétéran III",
    19: "Expert I",
    20: "Expert II",
    21: "Expert III",
    22: "Maître I",
    23: "Maître II",
    24: "Maître III",
    25: "Grand Maître",
    26: "Élite",
    27: "Légende",
    28: "Champion",
    29: "Grand Champion",
    30: "Ultime Légende"
}


def average_ppd_or_others(stats, game):
    """
    PPD moyen à ce jeu, sinon la moyenne de ceux des autres jeux
    """
    ppd = average_ppd(stats, game)
    if ppd:
        return ppd
    games = {key.split('_', 2)[2] for key in stats if key.startswith(('moyenne_ppd_', 'moyenne_ppr_', 'ppr_moyen_'))}
    values = [value for value in (average_ppd(stats, other) for other in games) if isinstance(value, (int, float)) and value > 0]
    return sum(values) / len(values) if values else 0.0


def get_level_from_ppd(ppd_value):
    """
    Niveau du joueur d'après son PPD (Points Per Dart)
    """
    if ppd_value is None:
        return 1

    if ppd_value <= 10.64: return 1
    elif ppd_value <= 11.89: return 2
    elif ppd_value <= 13.14: return 3
    elif ppd_value <= 14.39: return 4
    elif ppd_value <= 15.64: return 5
    elif ppd_value <= 16.89: return 6
    elif ppd_value <= 18.14: return 7
    elif ppd_value <= 19.44: return 8
    elif ppd_value <= 20.74: return 9
    elif ppd_value <= 22.04: return 10
    elif ppd_value <= 23.34: return 11
    elif ppd_value <= 24.64: return 12
    elif ppd_value <= 25.94: return 13
    elif ppd_value <= 27.29: return 14
    elif ppd_value <= 28.64: return 15
    elif ppd_value <= 29.99: return 16
    elif ppd_value <= 31.34: return 17
    elif ppd_value <= 32.69: return 18
    elif ppd_value <= 34.04: return 19
    elif ppd_value <= 35.39: return 20
    elif ppd_value <= 36.79: return 21
    elif ppd_value <= 38.19: return 22
    elif ppd_value <= 39.59: return 23
    elif ppd_value <= 40.99: return 24
    elif ppd_value <= 42.39: return 25
    elif ppd_value <= 43.79: return 26
    elif ppd_value <= 45.19: return 27
    elif ppd_value <= 46.59: return 28
    elif ppd_value <= 47.99: return 29
    else: return 30

def get_level_from_mpr(mpr_value):
    if mpr_value <= 1.09: return 1
    elif mpr_value <= 1.19: return 2
    elif mpr_value <= 1.30: return 3
    elif mpr_value <= 1.45: return 4
    elif mpr_value <= 1.60: return 5
    elif mpr_value <= 1.75: return 6
    elif mpr_value <= 1.90: return 7
    elif mpr_value <= 2.05: return 8
    elif mpr_value <= 2.20: return 9
    elif mpr_value <= 2.35: return 10
    elif mpr_value <= 2.50: return 11
    elif mpr_value <= 2.65: return 12
    elif mpr_value <= 2.80: return 13
    elif mpr_value <= 2.95: return 14
    elif mpr_value <= 3.10: return 15
    elif mpr_value <= 3.25: return 16
    elif mpr_value <= 3.40: return 17
    elif mpr_value <= 3.56: return 18
    elif mpr_value <= 3.70: return 19
    elif mpr_value <= 3.85: return 20
    elif mpr_value <= 4.06: return 21
    elif mpr_value <= 4.27: return 22
    elif mpr_value <= 4.48: return 23
    elif mpr_value <= 4.69: return 24
    elif mpr_value <= 4.95: return 25
    elif mpr_value <= 5.21: return 26
    elif mpr_value <= 5.47: return 27
    elif mpr_value <= 5.73: return 28
    elif mpr_value <= 5.99: return 29
    else: return 30
    

def delete_player(name):
    data = load_player_data()
    target_key = None
    for k in data.keys():
        if k.lower() == name.lower():
            target_key = k
            break
            
    if target_key and target_key in data:
        del data[target_key]
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print("[ERREUR SUPPRESSION JOUEUR] :", e)
    return False


def load_player_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def load_favorite_names():
    data = load_player_data()
    formatted_names = [name.strip().capitalize() for name in data.keys() if name.strip() and name != "_global_stats"]
    return sorted(formatted_names, key=lambda n: n.lower())


def ensure_player_exists(name):
    data = load_player_data()
    original_key = None
    for k in data.keys():
        if k.lower() == name.lower():
            original_key = k
            break
            
    if original_key is None:
        data[name] = {"trophies": [], "stats": {}}
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception:
            pass


# --- ÉCRAN 1 : SÉLECTION DU JOUEUR (AVEC TABLEAU DÉTAILLÉ) ---
# DEPLACER AU DESSUS DE MAIN

# --- ÉCRAN 1.5 : SÉLECTION DE LA CATÉGORIE ---
class CategorySelectionScreen:
    def __init__(self, screen, current_player, rpi=None):
        self.screen = screen
        self.current_player = current_player
        self.rpi = rpi
        self.selected_index = 0
        self.categories = [
            "Statistiques",
            "Succès de progression",
            "Combinaisons et figures",
            "Scores spécifiques",
            "Cricket / Mickey",
            "Ho-One",
            "Doubles",
            "Triples"
        ]
        all_data = load_player_data()
        player_info = {}
        for k, v in all_data.items():
            if k.strip().lower() == self.current_player.strip().lower():
                player_info = v
                break
        self.unlocked_trophies_list = player_info.get("trophies", [])

    def get_trophy_counts_for_category(self, category_name):
        if category_name == "Statistiques":
            return None, None
            
        total_in_cat = 0
        unlocked_in_cat = 0
        
        for trophy in ALL_TROPHIES:
            if trophy.get("category") == category_name:
                total_in_cat += 1
                if trophy["id"] in self.unlocked_trophies_list:
                    unlocked_in_cat += 1
                    
        return unlocked_in_cat, total_in_cat

    def run(self):
        clock = pygame.time.Clock()
        width, height = self.screen.get_size()
        scale = width / 1280.0

        try:
            title_font = cfonts.font(int(40 * scale), bold=True)
            text_font = cfonts.font(int(22 * scale), bold=True)
            footer_font = cfonts.font(int(16 * scale))
        except Exception:
            title_font = pygame.font.Font(None, 40)
            text_font = pygame.font.Font(None, 22)
            footer_font = pygame.font.Font(None, 16)

        total_cats = len(self.categories)
        running = True

        while running:
            self.screen.fill((20, 24, 33))
            
            title_text = title_font.render(f"{self.current_player} - CHOISIR UNE CATEGORIE", True, (255, 255, 255))
            title_rect = title_text.get_rect(center=(width // 2, int(50 * scale)))
            self.screen.blit(title_text, title_rect)
            
            start_y = int(100 * scale)
            button_width = int(650 * scale)
            button_height = int(55 * scale)
            button_x = (width - button_width) // 2
            
            for idx, cat_name in enumerate(self.categories):
                by = start_y + idx * (button_height + int(12 * scale))
                b_rect = pygame.Rect(button_x, by, button_width, button_height)
                
                is_highlighted = (idx == self.selected_index)
                bg_color = (55, 70, 105) if is_highlighted else (35, 42, 58)
                border_color = (100, 150, 255) if is_highlighted else (60, 72, 98)
                text_color = (255, 255, 255) if is_highlighted else (200, 205, 215)
                border_width = int(3 * scale) if is_highlighted else int(2 * scale)
                
                pygame.draw.rect(self.screen, bg_color, b_rect, border_radius=int(8 * scale))
                pygame.draw.rect(self.screen, border_color, b_rect, border_width, border_radius=int(8 * scale))
                
                unlocked, total = self.get_trophy_counts_for_category(cat_name)
                if cat_name == "Statistiques":
                    display_text = "Statistiques Générales & Par Jeu"
                else:
                    display_text = f"{cat_name}  -  ({unlocked}/{total})"
                
                text_surface = text_font.render(display_text, True, text_color)
                text_rect = text_surface.get_rect(center=b_rect.center)
                self.screen.blit(text_surface, text_rect)

            footer_text = footer_font.render("HAUT / BAS (S20/S3) pour naviguer | ENTRÉE (Bull) pour valider | ÉCHAP pour retour", True, (150, 150, 150))
            footer_rect = footer_text.get_rect(center=(width // 2, height - int(30 * scale)))
            self.screen.blit(footer_text, footer_rect)
            
            pygame.display.flip()
            
            navigation = 0
            action_pressed = None
            back_pressed = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "QUIT", None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        back_pressed = True
                    elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                        navigation = 1
                    elif event.key in (pygame.K_UP, pygame.K_LEFT):
                        navigation = -1
                    elif event.key == pygame.K_RETURN:
                        action_pressed = "SELECT"

            if self.rpi and hasattr(self.rpi, "listen_inputs"):
                try:
                    inp = self.rpi.listen_inputs()
                    if inp:
                        key_str = str(inp).strip()
                        if key_str in UP_KEYS + LEFT_KEYS:
                            navigation = -1
                        elif key_str in DOWN_KEYS + RIGHT_KEYS:
                            navigation = 1
                        elif key_str in ENTER_KEYS:
                            action_pressed = "SELECT"
                        elif key_str in ESCAPE_KEYS:
                            back_pressed = True
                except Exception as e:
                    print("[ERREUR LISTEN_INPUTS] :", e)

            if navigation != 0:
                self.selected_index = (self.selected_index + navigation) % total_cats

            if back_pressed:
                return "BACK", None

            if action_pressed == "SELECT":
                chosen_cat = self.categories[self.selected_index]
                return "SELECT", chosen_cat

            clock.tick(30)
            
        return "QUIT", None


# --- ÉCRAN 1.6 : AFFICHAGE DES TROPHÉES ---
class TrophiesScreen:
    def __init__(self, screen, current_player, category, rpi=None):
        self.screen = screen
        self.current_player = current_player
        self.category = category
        self.rpi = rpi
        
        all_data = load_player_data()
        player_info = {}
        for k, v in all_data.items():
            if k.strip().lower() == self.current_player.strip().lower():
                player_info = v
                break
        self.unlocked_trophies = player_info.get("trophies", [])
        
        self.filtered_trophies = [t for t in ALL_TROPHIES if t["category"] == self.category]
        self.items_per_page = 21
        self.current_page = 0
        self.total_pages = max(1, (len(self.filtered_trophies) + self.items_per_page - 1) // self.items_per_page)

    def run(self):
        clock = pygame.time.Clock()
        width, height = self.screen.get_size()
        scale = width / 1280.0

        try:
            title_font = cfonts.font(int(35 * scale), bold=True)
            text_font = cfonts.font(int(14 * scale), bold=True)
            small_font = cfonts.font(int(11 * scale))
            footer_font = cfonts.font(int(16 * scale))
        except Exception:
            title_font = pygame.font.Font(None, 35)
            text_font = pygame.font.Font(None, 14)
            small_font = pygame.font.Font(None, 11)
            footer_font = pygame.font.Font(None, 16)

        running = True
        while running:
            try:
                self.screen.fill((20, 24, 33))
                
                title_text = title_font.render(f"{self.current_player} - {self.category.upper()}", True, (255, 255, 255))
                title_rect = title_text.get_rect(center=(width // 2, int(45 * scale)))
                self.screen.blit(title_text, title_rect)
                
                start_idx = self.current_page * self.items_per_page
                end_idx = start_idx + self.items_per_page
                current_trophies = self.filtered_trophies[start_idx:end_idx]
                
                left_margin = int(25 * scale)
                column_gap = int(12 * scale)
                col_width = (width - (left_margin * 2) - (column_gap * 4)) // 5  
                start_y = int(90 * scale)
                row_height = int(120 * scale)
                box_height = int(100 * scale)
                
                for i, trophy in enumerate(current_trophies):
                    col = i % 5  
                    row = i // 5  
                    x = left_margin + col * (col_width + column_gap)
                    y = start_y + row * row_height
                    
                    box_rect = pygame.Rect(x, y, col_width, box_height)
                    is_unlocked = trophy["id"] in self.unlocked_trophies
                    
                    box_bg = (35, 42, 58) if is_unlocked else (25, 28, 35)
                    box_border = (60, 72, 98) if is_unlocked else (40, 45, 55)
                    
                    pygame.draw.rect(self.screen, box_bg, box_rect, border_radius=int(6 * scale))
                    pygame.draw.rect(self.screen, box_border, box_rect, int(2 * scale), border_radius=int(6 * scale))
                    
                    self.screen.set_clip(box_rect)
                    
                    img_width = int(36 * scale)
                    img_height = int(51 * scale)
                    img_x = x + int(10 * scale)
                    img_y = y + (box_height - img_height) // 2  

                    img_name = trophy["img"] if "." in trophy["img"] else trophy["img"] + ".png"
                    img_path = os.path.join(BASE_DIR, "images_trophees", img_name)
                    has_image = False
                    if os.path.exists(img_path):
                        try:
                            trophy_img = pygame.image.load(img_path).convert_alpha()
                            trophy_img = pygame.transform.smoothscale(trophy_img, (img_width, img_height))
                            if not is_unlocked:
                                trophy_img.fill((80, 80, 80, 0), special_flags=pygame.BLEND_RGBA_MULT)
                            self.screen.blit(trophy_img, (img_x, img_y))
                            has_image = True
                        except:
                            pass
                    
                    if not has_image:
                        pygame.draw.rect(self.screen, (80, 80, 80), (img_x, img_y, img_width, img_height))
                    
                    text_x = img_x + img_width + int(10 * scale)
                    text_color = (240, 240, 240) if is_unlocked else (100, 110, 120)
                    desc_color = (170, 180, 200) if is_unlocked else (80, 85, 95)
                    
                    name_surface = text_font.render(trophy["name"], True, text_color)
                    desc_surface = small_font.render(trophy["desc"], True, desc_color)
                    
                    self.screen.blit(name_surface, (text_x, y + int(20 * scale)))
                    self.screen.blit(desc_surface, (text_x, y + int(50 * scale)))
                    self.screen.set_clip(None)
                
                if self.total_pages > 1:
                    page_info = f"Page {self.current_page + 1} / {self.total_pages} (GAUCHE / DROITE ou S11 / S6)"
                    page_surf = footer_font.render(page_info, True, (200, 200, 100))
                    page_rect = page_surf.get_rect(center=(width // 2, height - int(60 * scale)))
                    self.screen.blit(page_surf, page_rect)

                footer_text_str = "ÉCHAP (ou bouton retour) pour retourner aux catégories"
                footer_surface = footer_font.render(footer_text_str, True, (150, 150, 150))
                footer_rect = footer_surface.get_rect(center=(width // 2, height - int(25 * scale)))
                self.screen.blit(footer_surface, footer_rect)
                
                pygame.display.flip()
                
            except Exception as e:
                print("[ERREUR DESSIN TROPHÉES] :", e)

            page_change = 0
            back_pressed = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "BACK"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        back_pressed = True
                    elif event.key == pygame.K_RIGHT:
                        page_change = 1
                    elif event.key == pygame.K_LEFT:
                        page_change = -1

            if self.rpi and hasattr(self.rpi, "listen_inputs"):
                try:
                    inp = self.rpi.listen_inputs()
                    if inp:
                        key_str = str(inp).strip()
                        if key_str in RIGHT_KEYS:
                            page_change = 1
                        elif key_str in LEFT_KEYS:
                            page_change = -1
                        elif key_str in ESCAPE_KEYS:
                            back_pressed = True
                except Exception as e:
                    print("[ERREUR LISTEN_INPUTS] :", e)

            if page_change != 0:
                new_page = self.current_page + page_change
                if 0 <= new_page < self.total_pages:
                    self.current_page = new_page

            if back_pressed:
                return "BACK"

            clock.tick(30)
            
        return "BACK"


# --- ÉCRAN 2 : AFFICHAGE DES STATISTIQUES ---
class StatisticsScreen:
    def __init__(self, screen, current_player, rpi=None):
        self.screen = screen
        self.current_player = current_player
        self.rpi = rpi
        
        all_data = load_player_data()
        self.global_data = all_data.get("_global_stats", {})
        player_info = {}
        for k, v in all_data.items():
            if k.strip().lower() == self.current_player.strip().lower():
                player_info = v
                break
        self.stats = player_info.get("stats", {})
        self.scroll_offset = 0
        self.max_scroll = 0

    def run(self):
        clock = pygame.time.Clock()
        width, height = self.screen.get_size()
        scale = width / 1280.0

        all_data_for_trophies = load_player_data()
        player_trophies_list = []
        for k, v in all_data_for_trophies.items():
            if k.strip().lower() == self.current_player.strip().lower():
                player_trophies_list = v.get("trophies", [])
                break
        unlocked_count = len(player_trophies_list)
        total_trophies_count = len(ALL_TROPHIES)

        try:
            title_font = cfonts.font(int(32 * scale), bold=True)
            text_font = cfonts.font(int(13 * scale))     
            bold_font = cfonts.font(int(14 * scale), bold=True)
            hint_font = cfonts.font(int(12 * scale))     
        except Exception:
            title_font = pygame.font.Font(None, 32)
            text_font = pygame.font.Font(None, 13)
            bold_font = pygame.font.Font(None, 14)
            hint_font = pygame.font.Font(None, 12)

        running = True
        while running:
            self.screen.fill((20, 24, 33))  

            main_title_text = f"STATISTIQUES DE : {self.current_player.upper()}"
            sub_title_text = f"  (Trophées : {unlocked_count}/{total_trophies_count})"

            title_surf = title_font.render(main_title_text, True, (255, 255, 255))
            
            try:
                small_title_font = cfonts.font(int(16 * scale), bold=True)
            except Exception:
                small_title_font = pygame.font.Font(None, 20)
                
            sub_surf = small_title_font.render(sub_title_text, True, (180, 190, 210))

            start_x = int(40 * scale)
            title_y = int(15 * scale)
            
            self.screen.blit(title_surf, (start_x, title_y))
            sub_y = title_y + (title_surf.get_height() - sub_surf.get_height()) // 2 + int(2 * scale)
            self.screen.blit(sub_surf, (start_x + title_surf.get_width(), sub_y))

            hint_surf = hint_font.render("Échap pour retour | Flèches Haut/Bas ou S20/S3 pour défiler", True, (150, 150, 170))
            self.screen.blit(hint_surf, (width - hint_surf.get_width() - int(40 * scale), int(20 * scale)))
            
            all_data = load_player_data()
            global_stats_dict = all_data.get("_global_stats", {})
            total_machine_parties = global_stats_dict.get('total_machine_parties', 0)

            total_parties = self.stats.get('total_parties_jouees', 0)
            total_flechettes = self.stats.get('total_darts', self.stats.get('total_flechettes', 0))
            
            wins = self.stats.get('wins', 0)
            losses = self.stats.get('losses', 0)
            
            simple_bulls = self.stats.get('sbulls_count', self.stats.get('simple_bulls_count', 0))
            double_bulls = self.stats.get('dbulls_count', self.stats.get('total_double_bulls', 0))
            total_bulls = simple_bulls + double_bulls
            
            doubles = self.stats.get('doubles_count', self.stats.get('total_doubles', 0))
            triples = self.stats.get('triples_count', self.stats.get('total_triples', 0))
            simples = self.stats.get('singles_count', 0)
            
            #misses = total_flechettes - doubles - triples - simples - double_bulls - simple_bulls
            misses = self.stats.get('misses_count', self.stats.get('total_misses', 0))
            
            p_win = (wins / total_parties * 100) if total_parties > 0 else 0
            p_loss = (losses / total_parties * 100) if total_parties > 0 else 0
            
            p_misses = (misses / total_flechettes * 100) if total_flechettes > 0 else 0
            p_simple_bulls = (simple_bulls / total_flechettes * 100) if total_flechettes > 0 else 0
            p_double_bulls = (double_bulls / total_flechettes * 100) if total_flechettes > 0 else 0
            p_bulls = (total_bulls / total_flechettes * 100) if total_flechettes > 0 else 0
            
            p_simples = (simples / total_flechettes * 100) if total_flechettes > 0 else 0
            p_doubles = (doubles / total_flechettes * 100) if total_flechettes > 0 else 0
            p_triples = (triples / total_flechettes * 100) if total_flechettes > 0 else 0

            def fmt_pct(val):
                return f"{val:.1f}".replace('.', ',')

            global_stats = [
                ("FLÉCHETTES", f"{total_flechettes}", ""),
                ("PARTIES", f"{total_parties}", f"/{total_machine_parties}" if total_machine_parties > 0 else ""),
                ("Victoires", f"{wins}", f"({fmt_pct(p_win)}%)" if total_parties > 0 else ""),
                ("Défaites", f"{losses}", f"({fmt_pct(p_loss)}%)" if total_parties > 0 else ""),
                
                ("Simples", f"{simples}", f"({fmt_pct(p_simples)}%)" if total_flechettes > 0 else ""),
                ("Doubles", f"{doubles}", f"({fmt_pct(p_doubles)}%)" if total_flechettes > 0 else ""),
                ("Triples", f"{triples}", f"({fmt_pct(p_triples)}%)" if total_flechettes > 0 else ""),
                ("MISS", f"{misses}", f"({fmt_pct(p_misses)}%)" if total_flechettes > 0 else ""),
                
                ("Bulls", f"{total_bulls}", f"({fmt_pct(p_bulls)}%)" if total_flechettes > 0 else ""),
                ("Simple Bull", f"{simple_bulls}", f"({fmt_pct(p_simple_bulls)}%)" if total_flechettes > 0 else ""),
                ("Double Bull", f"{double_bulls}", f"({fmt_pct(p_double_bulls)}%)" if total_flechettes > 0 else ""),
                ("", "", "")
            ]

            g_start_y = int(55 * scale)
            g_cols = 4  
            g_start_x = int(40 * scale)
            
            margin_right = int(40 * scale)
            panel_width = int(560 * scale)
            panel_x = width - margin_right - panel_width
            available_width_for_grid = (panel_x - int(20 * scale)) - g_start_x
            g_space_x = int(8 * scale)
            g_box_width = (available_width_for_grid - (g_cols - 1) * g_space_x) // g_cols
            
            g_box_height = int(42 * scale)  
            g_space_y = int(8 * scale)

            for idx, item in enumerate(global_stats):
                label = item[0]
                if not label:
                    continue
                main_val = item[1]
                pct_val = item[2] if len(item) > 2 else ""

                col = idx % g_cols
                row = idx // g_cols
                bx = g_start_x + col * (g_box_width + g_space_x)
                by = g_start_y + row * (g_box_height + g_space_y)

                pygame.draw.rect(self.screen, (30, 35, 45), (bx, by, g_box_width, g_box_height), border_radius=6)
                pygame.draw.rect(self.screen, (60, 70, 90), (bx, by, g_box_width, g_box_height), 1, border_radius=6)

                lbl_surf = text_font.render(f"{label} :", True, (180, 180, 180))
                self.screen.blit(lbl_surf, (bx + int(8 * scale), by + int(12 * scale)))

                val_surf = bold_font.render(str(main_val), True, (0, 220, 120))
                
                if pct_val:
                    pct_surf = hint_font.render(pct_val, True, (140, 180, 160))
                    total_w = val_surf.get_width() + int(3 * scale) + pct_surf.get_width()
                    start_val_x = bx + g_box_width - total_w - int(8 * scale)
                    
                    self.screen.blit(val_surf, (start_val_x, by + int(12 * scale)))
                    self.screen.blit(pct_surf, (start_val_x + val_surf.get_width() + int(3 * scale), by + int(14 * scale)))
                else:
                    self.screen.blit(val_surf, (bx + g_box_width - val_surf.get_width() - int(8 * scale), by + int(12 * scale)))

            game_keys = set()
            for key in self.stats.keys():
                if key.startswith("parties_jouees_"):
                    game_keys.add(key.replace("parties_jouees_", ""))
                elif key.startswith("victoire_"):
                    game_keys.add(key.replace("victoire_", ""))
                elif key.startswith("defaite_"):
                    game_keys.add(key.replace("defaite_", ""))

            all_players_data = load_player_data()
            if self.current_player and self.current_player not in all_players_data:
                all_players_data[self.current_player] = {"stats": self.stats}

            player_summaries = []
            for p_name, p_content in all_players_data.items():
                if p_name == "_global_stats":
                    continue
                p_st = p_content.get("stats", p_content)
                p_games = p_st.get('total_parties_jouees', 0)
                p_w = p_st.get('wins', sum(p_st.get(f"victoire_{g}", 0) for g in game_keys))
                p_l = p_st.get('losses', sum(p_st.get(f"defaite_{g}", 0) for g in game_keys))
                player_summaries.append((p_name, p_games, p_w, p_l))

            top_games = sorted(player_summaries, key=lambda x: x[1], reverse=True)[:3]
            top_wins = sorted(player_summaries, key=lambda x: x[2], reverse=True)[:3]
            top_losses = sorted(player_summaries, key=lambda x: x[3], reverse=True)[:3]

            top_played_games = []
            global_stats_dict = all_players_data.get("_global_stats", {})
            global_game_counts = {}
            
            for k, v in global_stats_dict.items():
                if k.startswith("parties_reelles_"):
                    g_key = k.replace("parties_reelles_", "")
                    global_game_counts[g_key] = v

            if not global_game_counts:
                for p_name, p_content in all_players_data.items():
                    if p_name == "_global_stats":
                        continue
                    p_st = p_content.get("stats", p_content)
                    for k, v in p_st.items():
                        if k.startswith("parties_jouees_"):
                            g_key = k.replace("parties_jouees_", "")
                            global_game_counts[g_key] = global_game_counts.get(g_key, 0) + v

            sorted_global_games = sorted(global_game_counts.items(), key=lambda x: x[1], reverse=True)
            for g_name, g_val in sorted_global_games[:3]:
                formatted_name = g_name.lower().capitalize()
                if len(formatted_name) > 10:
                    formatted_name = formatted_name[:9] + "."
                top_played_games.append((formatted_name, g_val))

            panel_height = (3 * g_box_height) + (2 * g_space_y)  
            
            pygame.draw.rect(self.screen, (25, 30, 40), (panel_x, g_start_y, panel_width, panel_height), border_radius=8)
            pygame.draw.rect(self.screen, (70, 90, 120), (panel_x, g_start_y, panel_width, panel_height), 1, border_radius=8)

            panel_title = bold_font.render("CLASSEMENTS", True, (255, 200, 50))
            self.screen.blit(panel_title, (panel_x + (panel_width - panel_title.get_width()) // 2, g_start_y + int(4 * scale)))

            cols_count = 4
            col_w = panel_width // cols_count
            border_color = (70, 90, 120)

            def draw_mini_top(title, data_list, val_idx, col_index, show_score=True):
                c_start_x = panel_x + (col_index * col_w)
                col_box_rect = (c_start_x, g_start_y + int(24 * scale), col_w, panel_height - int(24 * scale))
                pygame.draw.rect(self.screen, (32, 38, 50), col_box_rect)
                pygame.draw.rect(self.screen, border_color, col_box_rect, 1)

                t_surf = hint_font.render(title, True, (200, 200, 220))
                self.screen.blit(t_surf, (c_start_x + (col_w - t_surf.get_width()) // 2, g_start_y + int(28 * scale)))
                
                line_y = g_start_y + int(48 * scale)
                pygame.draw.line(self.screen, border_color, (c_start_x + int(3 * scale), line_y), (c_start_x + col_w - int(3 * scale), line_y), 1)

                left_padding = int(5 * scale)
                for i, row_data in enumerate(data_list):
                    name = row_data[0]
                    if show_score:
                        score = row_data[val_idx]
                        txt = f"{i+1}. {name} ({score})"
                    else:
                        txt = f"{i+1}. {name}"
                        
                    podium_colors = [
                        (255, 215, 0),
                        (200, 200, 200),
                        (205, 127, 50)
                    ]
                    item_color = podium_colors[i] if i < len(podium_colors) else (150, 220, 255)
                    
                    item_surf = text_font.render(txt, True, item_color)
                    self.screen.blit(item_surf, (c_start_x + left_padding, g_start_y + int(56 * scale) + int(22 * scale) * i))

            draw_mini_top("+ de Parties", top_games, 1, 0, show_score=True)
            draw_mini_top("+ de Victoires", top_wins, 2, 1, show_score=True)
            draw_mini_top("+ de Défaites", top_losses, 3, 2, show_score=True)
            draw_mini_top("Top jeux", top_played_games, 1, 3, show_score=True)

            sorted_games = sorted(list(game_keys))
            j_start_y = g_start_y + (3 * (g_box_height + g_space_y)) + int(15 * scale)
            cols = 4 
            spacing_x = int(12 * scale)
            box_width = (width - int(80 * scale) - (cols - 1) * spacing_x) // cols
            box_height = int(70 * scale)  
            spacing_y = int(10 * scale)

            total_rows = (len(sorted_games) + cols - 1) // cols
            content_height = j_start_y + total_rows * (box_height + spacing_y)
            self.max_scroll = max(0, content_height - height + int(50 * scale))

            for index, game in enumerate(sorted_games):
                col = index % cols
                row = index // cols
                
                box_x = g_start_x + col * (box_width + spacing_x)
                box_y = j_start_y + row * (box_height + spacing_y) - self.scroll_offset
                
                if -box_height < box_y < height:
                    pygame.draw.rect(self.screen, (35, 40, 50), (box_x, box_y, box_width, box_height), border_radius=8)
                    pygame.draw.rect(self.screen, (90, 100, 130), (box_x, box_y, box_width, box_height), 2, border_radius=8)
                    
                    game_title_surf = bold_font.render(game.upper(), True, (255, 200, 50))
                    self.screen.blit(game_title_surf, (box_x + int(8 * scale), box_y + int(5 * scale)))
                    
                    p_jouees = self.stats.get(f"parties_jouees_{game}", 0)
                    victoires = self.stats.get(f"victoire_{game}", 0)
                    defaites = self.stats.get(f"defaite_{game}", 0)
                    
                    if victoires > defaites:
                        vic_num_color = (0, 220, 120)
                    elif victoires < defaites:
                        vic_num_color = (255, 80, 80)
                    else:
                        vic_num_color = (210, 210, 210)

                    lbl_parties = text_font.render(f"Parties : {p_jouees}  •  ", True, (210, 210, 210))
                    lbl_vic_text = text_font.render("Victoires : ", True, (210, 210, 210))
                    lbl_vic_num = text_font.render(str(victoires), True, vic_num_color)
                    lbl_sep = text_font.render("  •  ", True, (210, 210, 210))
                    lbl_def = text_font.render(f"Défaites : {defaites}", True, (210, 210, 210))

                    curr_x = box_x + int(8 * scale)
                    curr_y = box_y + int(26 * scale)
                    
                    self.screen.blit(lbl_parties, (curr_x, curr_y))
                    curr_x += lbl_parties.get_width()
                    self.screen.blit(lbl_vic_text, (curr_x, curr_y))
                    curr_x += lbl_vic_text.get_width()
                    self.screen.blit(lbl_vic_num, (curr_x, curr_y))
                    curr_x += lbl_vic_num.get_width()
                    self.screen.blit(lbl_sep, (curr_x, curr_y))
                    curr_x += lbl_sep.get_width()
                    self.screen.blit(lbl_def, (curr_x, curr_y))

                    best_player_name = "-"
                    max_vic = -1
                    for p_name, p_content in all_players_data.items():
                        if p_name == "_global_stats":
                            continue
                        p_st = p_content.get("stats", p_content)
                        p_vics_game = p_st.get(f"victoire_{game}", 0)
                        if p_vics_game > max_vic:
                            max_vic = p_vics_game
                            best_player_name = p_name

                    line3_y = box_y + int(47 * scale)
                    curr_x_l3 = box_x + int(8 * scale)

                    has_stat = False
                    game_lower = game.lower()
                    
                    if game_lower in ["cricket", "mickey"]:
                        mpr_val = self.stats.get(f"moyenne_mpr_{game}", self.stats.get(f"mpr_moyen_{game}", 0.0))
                        lbl_mpr_label = text_font.render("MPR : ", True, (210, 210, 210))
                        lbl_mpr_val = text_font.render(f"{mpr_val:.2f}", True, (0, 220, 255))
                        
                        self.screen.blit(lbl_mpr_label, (curr_x_l3, line3_y))
                        curr_x_l3 += lbl_mpr_label.get_width()
                        self.screen.blit(lbl_mpr_val, (curr_x_l3, line3_y))
                        curr_x_l3 += lbl_mpr_val.get_width()
                        has_stat = True
                        
                    elif game_lower in ["321_zlip", "batard", "highscore", "shoot-out", "up_and_down", "sabotage", "chaos", "low_score", "ho-one"]:
                        ppd_val = average_ppd(self.stats, game_lower)
                        
                        lbl_ppd_label = text_font.render("PPD : ", True, (210, 210, 210))
                        formatted_ppd = f"{ppd_val:.2f}".replace('.', ',')
                        lbl_ppd_val = text_font.render(f"{formatted_ppd}", True, (0, 220, 255))
                        
                        self.screen.blit(lbl_ppd_label, (curr_x_l3, line3_y))
                        curr_x_l3 += lbl_ppd_label.get_width()
                        self.screen.blit(lbl_ppd_val, (curr_x_l3, line3_y))
                        curr_x_l3 += lbl_ppd_val.get_width()
                        has_stat = True




                    if has_stat:
                        lbl_sep2 = text_font.render("  •  ", True, (210, 210, 210))
                        self.screen.blit(lbl_sep2, (curr_x_l3, line3_y))
                        curr_x_l3 += lbl_sep2.get_width()

                    lbl_best_label = text_font.render("Meilleur Joueur : ", True, (210, 210, 210))
                    lbl_best_val = text_font.render(f"{best_player_name}", True, (0, 220, 255))

                    self.screen.blit(lbl_best_label, (curr_x_l3, line3_y))
                    curr_x_l3 += lbl_best_label.get_width()
                    self.screen.blit(lbl_best_val, (curr_x_l3, line3_y))

            pygame.display.flip()

            back_pressed = False
            navigation = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "BACK"
                elif event.type == pygame.MOUSEWHEEL:
                    self.scroll_offset -= event.y * 30
                    if self.scroll_offset < 0:
                        self.scroll_offset = 0
                    if self.scroll_offset > self.max_scroll:
                        self.scroll_offset = self.max_scroll
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        back_pressed = True
                    elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                        navigation = 1
                    elif event.key in (pygame.K_UP, pygame.K_LEFT):
                        navigation = -1

            if self.rpi and hasattr(self.rpi, "listen_inputs"):
                try:
                    inp = self.rpi.listen_inputs()
                    if inp:
                        key_str = str(inp).strip()
                        if key_str in DOWN_KEYS + RIGHT_KEYS:
                            navigation = 1
                        elif key_str in UP_KEYS + LEFT_KEYS:
                            navigation = -1
                        elif key_str in ESCAPE_KEYS:
                            back_pressed = True
                except Exception as e:
                    print("[ERREUR LISTEN_INPUTS] :", e)

            if navigation != 0:
                self.scroll_offset += navigation * 30
                if self.scroll_offset < 0:
                    self.scroll_offset = 0
                if self.scroll_offset > self.max_scroll:
                    self.scroll_offset = self.max_scroll

            if back_pressed:
                return "BACK"

            clock.tick(30)
            
        return "BACK"

def get_player_logo(player_name, scale, game_type="ho-one", all_players_data=None):
    """
    Récupère et charge le logo du joueur en fonction de son niveau calculé (1 à 30),
    en respectant le format d'origine 136x52.
    """
    try:
        player_stats = {}
        
        # Recherche sécurisée des données et extraction de la sous-clé "stats"
        if all_players_data and isinstance(all_players_data, dict):
            p_content = None
            for k, v in all_players_data.items():
                if k.strip().lower() == player_name.strip().lower():
                    p_content = v
                    break
            
            if p_content:
                if isinstance(p_content, dict) and "stats" in p_content:
                    player_stats = p_content["stats"]
                else:
                    player_stats = p_content

        game_lower = game_type.lower()
        level = 1

        # Calcul du niveau selon le jeu
        if "cricket" in game_lower:
            mpr_value = player_stats.get("moyenne_mpr_cricket", player_stats.get("mpr_moyen_cricket", 0.0))
            level = get_level_from_mpr(mpr_value)
            
        elif "mickey" in game_lower:
            mpr_value = player_stats.get("moyenne_mpr_mickey", player_stats.get("mpr_moyen_mickey", 0.0))
            level = get_level_from_mpr(mpr_value)
            
        elif "highscore" in game_lower:
            level = get_level_from_ppd(average_ppd_or_others(player_stats, "highscore"))
            
           
        else:
            # Ho-One / X01
            level = get_level_from_ppd(average_ppd_or_others(player_stats, "ho-one"))
        
        # Chargement de l'image correspondante
        logo_filename = f"{level}.png"
        logo_path = os.path.join(BASE_DIR, "images_trophees", "logos", logo_filename)
        
        if os.path.exists(logo_path):
            logo_img = pygame.image.load(logo_path).convert_alpha()
            
            # Redimensionnement basé sur le ratio d'origine (136x52)
            orig_w, orig_h = 136, 52
            target_height = int(32 * scale)
            target_width = int(target_height * (orig_w / orig_h))
            
            logo_img = pygame.transform.smoothscale(logo_img, (target_width, target_height))
            return logo_img
        else:
            return None
            
    except Exception as e:
        print(f"[DEBUG LOGO] -> Erreur critique : {e}")
        return None


class PlayerSelectionScreen:
    def __init__(self, screen, rpi=None):
        self.screen = screen
        self.rpi = rpi
        self.selected_index = 0

    def run(self):
        clock = pygame.time.Clock()
        width, height = self.screen.get_size()
        scale = width / 1280.0

        try:
            title_font = cfonts.font(int(35 * scale), bold=True)
            text_font = cfonts.font(int(22 * scale))
            bold_font = cfonts.font(int(22 * scale), bold=True)
            footer_font = cfonts.font(int(16 * scale))
            small_font = cfonts.font(int(14 * scale))
            tiny_font = cfonts.font(int(11 * scale))
            error_font = cfonts.font(int(20 * scale))
        except Exception:
            title_font = pygame.font.Font(None, 35)
            text_font = pygame.font.Font(None, 22)
            bold_font = pygame.font.Font(None, 22)
            footer_font = pygame.font.Font(None, 16)
            tiny_font = pygame.font.Font(None, 11)
            small_font = pygame.font.Font(None, 14)

        max_visible_items = 6
        running = True

        while running:
            players = load_favorite_names()
            total_players = len(players)
            
            if total_players > 0:
                self.selected_index = self.selected_index % total_players
            else:
                self.selected_index = 0
            
            self.screen.fill((20, 24, 33))
            
            title_text = title_font.render("CHOISIR UN JOUEUR", True, (255, 255, 255))
            title_rect = title_text.get_rect(center=(width // 2, int(45 * scale)))
            self.screen.blit(title_text, title_rect)
            
            if total_players == 0:
                err_surf = error_font.render(f"Erreur : Aucun joueur trouvé dans '{DATA_FILE}'.", True, (255, 100, 100))
                err_rect = err_surf.get_rect(center=(width // 2, height // 2))
                self.screen.blit(err_surf, err_rect)
            else:
                start_offset = 0
                if total_players > max_visible_items:
                    start_offset = self.selected_index - (max_visible_items // 2)
                    if start_offset < 0:
                        start_offset = 0
                    elif start_offset > total_players - max_visible_items:
                        start_offset = total_players - max_visible_items

                end_offset = min(start_offset + max_visible_items, total_players)
                visible_players = players[start_offset:end_offset]

                # --- TABLEAU DE SÉLECTION (4 colonnes de scores) ---
                table_width = int(1100 * scale)
                table_x = (width - table_width) // 2
                start_y = int(100 * scale)
                
                # En-tête du tableau
                header_rect = pygame.Rect(table_x, start_y, table_width, int(40 * scale))
                pygame.draw.rect(self.screen, (45, 55, 75), header_rect, border_radius=6)
                pygame.draw.rect(self.screen, (90, 110, 150), header_rect, 1, border_radius=6)
                
                # Positions X réparties pour 4 colonnes de statistiques
                col_name_center = table_x + int(110 * scale)
                col_hoone_center = table_x + int(360 * scale)
                col_highscore_center = table_x + int(590 * scale)
                col_cricket_center = table_x + int(820 * scale)
                col_mickey_center = table_x + int(1010 * scale)

                headers = [
                    ("NOM DU JOUEUR", col_name_center), 
                    ("PPD (Ho-One)", col_hoone_center), 
                    ("PPD (Highscore)", col_highscore_center),
                    ("MPR (Cricket)", col_cricket_center),
                    ("MPR (Mickey)", col_mickey_center)
                ]
                
                for h_text, h_x in headers:
                    h_surf = bold_font.render(h_text, True, (255, 200, 50))
                    self.screen.blit(h_surf, (h_x - h_surf.get_width() // 2, start_y + int(10 * scale)))

                all_data = load_player_data()
                row_y = start_y + int(48 * scale)
                row_height = int(68 * scale)
                
                for idx, player_name in enumerate(visible_players):
                    real_index = start_offset + idx
                    is_highlighted = (real_index == self.selected_index)
                    
                    r_rect = pygame.Rect(table_x, row_y, table_width, row_height)
                    bg_color = (55, 70, 105) if is_highlighted else (30, 36, 48)
                    border_color = (100, 150, 255) if is_highlighted else (50, 60, 80)
                    border_w = int(3 * scale) if is_highlighted else 1
                    
                    pygame.draw.rect(self.screen, bg_color, r_rect, border_radius=6)
                    pygame.draw.rect(self.screen, border_color, r_rect, border_w, border_radius=6)
                    
                    # 1. Nom du joueur
                    name_color = (255, 255, 255) if is_highlighted else (210, 215, 225)
                    name_surf = bold_font.render(player_name.upper(), True, name_color)
                    self.screen.blit(name_surf, (col_name_center - name_surf.get_width() // 2, row_y + (row_height - name_surf.get_height()) // 2))
                    
                    # Récupération des données du joueur
                    p_content = next((v for k, v in all_data.items() if k.strip().lower() == player_name.strip().lower()), {})
                    p_st = p_content.get("stats", {}) if isinstance(p_content, dict) else {}

                    # --- 2. PPD (Ho-One) ---
                    ppd_val = average_ppd(p_st, "ho-one")
                    lvl_num = get_level_from_ppd(ppd_val)
                    rank_name = NAMES_LEVELS.get(lvl_num, "Débutant")
                    
                    score_hoone_surf = small_font.render(f"{ppd_val:.2f}".replace('.', ','), True, (0, 220, 255))
                    level_text_surf = tiny_font.render(rank_name, True, (180, 190, 210))
                    logo_hoone = get_player_logo(player_name, scale, game_type="ho-one", all_players_data=all_data)
                    if ppd_val == 0.0:
                        logo_hoone = None

                    if logo_hoone:
                        spacing = int(6 * scale)
                        combined_w = logo_hoone.get_width() + spacing + score_hoone_surf.get_width()
                        block_left_x = col_hoone_center - combined_w // 2
                        top_h = max(logo_hoone.get_height(), score_hoone_surf.get_height())
                        inner_spacing = int(3 * scale)
                        text_h = level_text_surf.get_height()
                        total_content_h = top_h + inner_spacing + text_h
                        block_y = row_y + (row_height - total_content_h) // 2
                        
                        self.screen.blit(logo_hoone, (block_left_x, block_y))
                        score_y = block_y + (logo_hoone.get_height() - score_hoone_surf.get_height()) // 2 + int(6 * scale)
                        self.screen.blit(score_hoone_surf, (block_left_x + logo_hoone.get_width() + spacing, score_y))
                        text_x = block_left_x + (logo_hoone.get_width() - level_text_surf.get_width()) // 2
                        self.screen.blit(level_text_surf, (text_x, block_y + top_h + inner_spacing))
                    else:
                        no_logo_text = tiny_font.render("Débutant", True, (150, 150, 150))
                        fallback_spacing = int(2 * scale)
                        fallback_total_h = no_logo_text.get_height() + fallback_spacing + score_hoone_surf.get_height()
                        fallback_y = row_y + (row_height - fallback_total_h) // 2
                        self.screen.blit(no_logo_text, (col_hoone_center - no_logo_text.get_width() // 2, fallback_y))
                        self.screen.blit(score_hoone_surf, (col_hoone_center - score_hoone_surf.get_width() // 2, fallback_y + no_logo_text.get_height() + fallback_spacing))

                    # --- 3. HIGHSCORE ---
                    ppd_hs_val = average_ppd(p_st, "highscore")
                    lvl_num_hs = get_level_from_ppd(ppd_hs_val)
                    rank_name_hs = NAMES_LEVELS.get(lvl_num_hs, "Débutant")
                    
                    score_hs_surf = small_font.render(f"{ppd_hs_val:.2f}".replace('.', ','), True, (0, 220, 255))
                    
                    level_text_hs_surf = tiny_font.render(rank_name_hs, True, (180, 190, 210))
                    
                    
                    logo_hs = get_player_logo(player_name, scale, game_type="highscore", all_players_data=all_data)
                    if ppd_hs_val == 0.0:
                        logo_hs = None

                    if logo_hs:
                        spacing = int(6 * scale)
                        combined_w = logo_hs.get_width() + spacing + score_hs_surf.get_width()
                        block_left_x = col_highscore_center - combined_w // 2
                        top_h = max(logo_hs.get_height(), score_hs_surf.get_height())
                        inner_spacing = int(3 * scale)
                        text_h = level_text_hs_surf.get_height()
                        total_content_h = top_h + inner_spacing + text_h
                        block_y = row_y + (row_height - total_content_h) // 2
                        
                        self.screen.blit(logo_hs, (block_left_x, block_y))
                        score_y = block_y + (logo_hs.get_height() - score_hs_surf.get_height()) // 2 + int(6 * scale)
                        self.screen.blit(score_hs_surf, (block_left_x + logo_hs.get_width() + spacing, score_y))
                        text_x = block_left_x + (logo_hs.get_width() - level_text_hs_surf.get_width()) // 2
                        self.screen.blit(level_text_hs_surf, (text_x, block_y + top_h + inner_spacing))
                    else:
                        no_logo_text = tiny_font.render("Débutant", True, (150, 150, 150))
                        fallback_spacing = int(2 * scale)
                        fallback_total_h = no_logo_text.get_height() + fallback_spacing + score_hs_surf.get_height()
                        fallback_y = row_y + (row_height - fallback_total_h) // 2
                        self.screen.blit(no_logo_text, (col_highscore_center - no_logo_text.get_width() // 2, fallback_y))
                        self.screen.blit(score_hs_surf, (col_highscore_center - score_hs_surf.get_width() // 2, fallback_y + no_logo_text.get_height() + fallback_spacing))
                    
                    
                    # --- 4. Cricket ---
                    mpr_val = p_st.get('moyenne_mpr_cricket', p_st.get('mpr_moyen_cricket', 0.0))
                    lvl_num_c = get_level_from_mpr(mpr_val)
                    rank_name_c = NAMES_LEVELS.get(lvl_num_c, "Débutant")
                    
                    score_cricket_surf = small_font.render(f"{mpr_val:.2f}".replace('.', ','), True, (0, 220, 255))
                    level_text_c_surf = tiny_font.render(rank_name_c, True, (180, 190, 210))
                    logo_cricket = get_player_logo(player_name, scale, game_type="cricket", all_players_data=all_data)
                    if mpr_val == 0.0:
                        logo_cricket = None

                    if logo_cricket:
                        spacing = int(6 * scale)
                        total_w = logo_cricket.get_width() + spacing + score_cricket_surf.get_width()
                        start_x = col_cricket_center - total_w // 2
                        logo_y = row_y + (row_height - logo_cricket.get_height()) // 2 - int(5 * scale)
                        score_y = row_y + (row_height - score_cricket_surf.get_height()) // 2 - int(5 * scale) + int(6 * scale)
                        
                        self.screen.blit(logo_cricket, (start_x, logo_y))
                        self.screen.blit(score_cricket_surf, (start_x + logo_cricket.get_width() + spacing, score_y))
                        text_x = start_x + (logo_cricket.get_width() - level_text_c_surf.get_width()) // 2
                        self.screen.blit(level_text_c_surf, (text_x, logo_y + logo_cricket.get_height() + int(3 * scale)))
                    else:
                        self.screen.blit(score_cricket_surf, (col_cricket_center - score_cricket_surf.get_width() // 2, row_y + (row_height - score_cricket_surf.get_height()) // 2))
                    
                    
                    # --- 5. Mickey ---
                    mpr_m_val = p_st.get('moyenne_mpr_mickey', p_st.get('mpr_moyen_mickey', 0.0))
                    lvl_num_m = get_level_from_mpr(mpr_m_val)
                    rank_name_m = NAMES_LEVELS.get(lvl_num_m, "Débutant")
                    
                    score_mickey_surf = small_font.render(f"{mpr_m_val:.2f}".replace('.', ','), True, (0, 220, 255))
                    level_text_m_surf = tiny_font.render(rank_name_m, True, (180, 190, 210))
                    logo_mickey = get_player_logo(player_name, scale, game_type="mickey", all_players_data=all_data)
                    if mpr_m_val == 0.0:
                        logo_mickey = None

                    if logo_mickey:
                        spacing = int(6 * scale)
                        total_w = logo_mickey.get_width() + spacing + score_mickey_surf.get_width()
                        start_x = col_mickey_center - total_w // 2
                        logo_y = row_y + (row_height - logo_mickey.get_height()) // 2 - int(5 * scale)
                        score_y = row_y + (row_height - score_mickey_surf.get_height()) // 2 - int(5 * scale) + int(6 * scale)
                        
                        self.screen.blit(logo_mickey, (start_x, logo_y))
                        self.screen.blit(score_mickey_surf, (start_x + logo_mickey.get_width() + spacing, score_y))
                        text_x = start_x + (logo_mickey.get_width() - level_text_m_surf.get_width()) // 2
                        self.screen.blit(level_text_m_surf, (text_x, logo_y + logo_mickey.get_height() + int(3 * scale)))
                    else:
                        self.screen.blit(score_mickey_surf, (col_mickey_center - score_mickey_surf.get_width() // 2, row_y + (row_height - score_mickey_surf.get_height()) // 2))

                    row_y += row_height + int(8 * scale)

                if total_players > max_visible_items:
                    scroll_info = f"({self.selected_index + 1} / {total_players})"
                    scroll_surf = footer_font.render(scroll_info, True, (120, 130, 150))
                    scroll_rect = scroll_surf.get_rect(center=(width // 2, height - int(75 * scale)))
                    self.screen.blit(scroll_surf, scroll_rect)
            
            footer_text = footer_font.render("HAUT / BAS (ou S20 / S3) pour naviguer | ENTRÉE (ou Bull) pour valider | Échap pour quitter", True, (150, 150, 150))
            footer_rect = footer_text.get_rect(center=(width // 2, height - int(35 * scale)))
            self.screen.blit(footer_text, footer_rect)
            
            pygame.display.flip()
            
            action_pressed = None
            navigation = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "QUIT", None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "QUIT", None
                    elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                        navigation = 1
                    elif event.key in (pygame.K_UP, pygame.K_LEFT):
                        navigation = -1
                    elif event.key == pygame.K_RETURN:
                        action_pressed = "SELECT"

            if self.rpi and hasattr(self.rpi, "listen_inputs"):
                try:
                    inp = self.rpi.listen_inputs()
                    if inp:
                        key_str = str(inp).strip()
                        if key_str in DOWN_KEYS + RIGHT_KEYS:
                            navigation = 1
                        elif key_str in UP_KEYS + LEFT_KEYS:
                            navigation = -1
                        elif key_str in ENTER_KEYS:
                            action_pressed = "SELECT"
                        elif key_str in ESCAPE_KEYS:
                            return "QUIT", None
                except Exception as e:
                    print("[ERREUR LISTEN_INPUTS] :", e)

            if navigation != 0 and total_players > 0:
                self.selected_index = (self.selected_index + navigation) % total_players

            if action_pressed == "SELECT" and total_players > 0:
                chosen_player = players[self.selected_index]
                return "SELECT", chosen_player

            clock.tick(30)
            
        return "QUIT", None
        
# --- FONCTION PRINCIPALE ---
def main(rpi=None):
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
    
    pygame.display.set_caption("Gestionnaire de Trophées Fléchettes")
    
    current_state = "PLAYER_SELECT"
    active_player = None
    active_category = None
    running = True

    while running:
        if current_state == "PLAYER_SELECT":
            selector = PlayerSelectionScreen(screen, rpi=rpi)
            action, active_player = selector.run()
            
            if action == "SELECT" and active_player:
                current_state = "CATEGORY_SELECT"
            else:
                running = False
                
        elif current_state == "CATEGORY_SELECT":
            cat_selector = CategorySelectionScreen(screen, active_player, rpi=rpi)
            action, active_category = cat_selector.run()
            
            if action == "SELECT" and active_category:
                if active_category == "Statistiques":
                    current_state = "STATISTICS"
                else:
                    current_state = "TROPHIES"
            elif action == "BACK":
                current_state = "PLAYER_SELECT"
            else:
                running = False

        elif current_state == "STATISTICS":
            stats_screen = StatisticsScreen(screen, current_player=active_player, rpi=rpi)
            action = stats_screen.run()
            
            if action == "BACK":
                current_state = "CATEGORY_SELECT"
            else:
                running = False

        elif current_state == "TROPHIES":
            trophy_screen = TrophiesScreen(screen, current_player=active_player, category=active_category, rpi=rpi)
            action = trophy_screen.run()
            
            if action == "BACK":
                current_state = "CATEGORY_SELECT"
            else:
                running = False


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    main()
    pygame.quit()
