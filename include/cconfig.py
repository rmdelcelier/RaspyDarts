
import os
import sys
import ast      # Convert string to dict
import json     #for debug

from include import cpaths

# Import library depending of python version
if sys.version[:1] == '2':
    import ConfigParser as configparser
elif sys.version[:1] == '3':
    import configparser
# pyDarts running Version
pyDartsVersion = "4.5.1"
# pyDarts official running wiki
wiki="https://www.facebook.com/groups/124845401274184"
# Official website
officialwebsite = "https://raspydarts.wordpress.com/"

rpi_versions = {'Pi 4 Model B': '4',
    'Pi Zero 2 W': '0',
    'Pi 3 Model A Plus': '3A+',
    'Pi 3 Model B Plus': '3B+'
    }

#
# Default values and default config file structure
#
DefaultConfig = {}
AlternateConfig = {}
#
#    'solo': 2000,
DefaultConfig['SectionGlobals'] = {
    'locale': 'fr_FR',
    # Theme of the example configuration (~/.raspydarts/themes/sombre) ; clear if missing
    'colorset': 'sombre',
    'font': 'Fabrik.ttf',
    'soundvolume': 100,
    'videos': 2,
    'blinktime': 3000,
    'pnj_time': 2000,
    'releasedartstime': 1800,
    'nextplayer_sound_duration': 7000,
    # The music played at the start of each turn (next_player) : False, none
    'nextplayer_music': True,
    'waitevent_time': 30000,
    'resx': 1000,
    'resy': 700,
    'fullscreen': True,
    'nbcol': 6,
    'onscreenbuttons': False,
    'startpercent': 0.4,
    'endgamestats': 1,
    'keeporder': False,
    'play_firstname': True,
    'print_dartstroke': True,
    'light_target': False,
    'light_strip': False,
    # Strip and target lit all the time out of games, without the animations of the events
    # (menu, wait...) : the colour of the strip (off : off) and of the target (off, origin : the
    # colours of the segments, as light_target)
    'idle_light': False,
    'idle_strip_color': 'white',
    'idle_target_color': 'origin',
    'netgamecreator': 'Raspydarts',
    'debuglevel': 0,
    'exhibition_mode': False,
    # Buttons of the main menu shown in exhibition mode, chosen in its screen (ids of the
    # buttons, see menus/defaults.yaml). Empty : those of the files of menus (exhibition: true)
    'exhibition_items': '',
    'competition_mode': False,
    'videosound_multiplier': 1,
    'sound_multiplier': 100, 
    'illumination_mode': False, 
    'illumination_color': 'white',    
    'fast_games_mode': False,
    'only_favorites_games_mode': False,
    'check_for_updates': True,
    # Output of the sound : auto (a USB card when plugged, else HDMI), hdmi, jack, usb
    # (include/caudio.py)
    'sound_output': 'auto'
    }
#
DefaultConfig['SectionAdvanced'] = {
    'bypass-stats': 1,
    'directplay': False,
    'selectedgame': False,
    'gametype': False,
    'netgamename': False,
    'servername': 'video.chtiraspycard.fr',
    'serverport': 5005,
    'masterserver': 'video.chtiraspycard.fr',
    'masterport': '5006',
    'serveralias': False,
    'listen': 'eth0',
    'clientpolltime': 5,
    'masterclientpolltime': 32,
    'animationduration': 5,
    'clear-local-db': False,
    'localplayers': '',
    'stats-format': 'old',
    'use-matrix': False,
    'use-dmd': True,
    'use-other': False,
    'use-hue': False,
    'mqtt-broker': 'localhost',
    'interior': False,
    'target-bgcolor1': 'blue',
    'target-bgcolor2': 'red',
    'target-bgcolor3': 'white',
    'target-bgbrightness': 10,
    'prefered_game': '',
    'preferedclassicgame': '',
    'preferedfungame': '',
    'preferedsportgame': '',
    'preferedcategory': 'classic',
    'nb_sets': 1,
    'db-celebration-delay': 2000,
    'set-celebration-delay': 3000,
    'victory-celebration-delay': 5000,
    'launch-game-celebration': False,
    'game-options-list':'',
    'richard-mode': False
    }
#
# Former server of the network games, which answers no more (removed from the favorites)
OLD_SERVER = 'raspydarts.synology.me'

DefaultConfig['Favorites'] = {
    # The first one : server of the online games (include/caccount.py), chosen again in their
    # screen
    'servers': 'video.chtiraspycard.fr',
    'firstnames': 'Joueur 1',
    'games': '',
    'players_color': ''
    }

#
DefaultConfig['Events'] = {
    'launch':{'TARGET': ['FadeRGB,1,random,10', 'Snake,100,random,50', 'Sparkle,10,gold,20'], 'STRIP': ['Strobe,5,red,20', 'Strobe,3,blue,50']},
    'off':{'TARGET': ['off,,,'], 'STRIP': ['off,,,'], 'DMD': ['off,,,'], 'MATRIX': ['off,,,']},
    'menu':{'TARGET': ['Strobe,3,gold,50'], 'STRIP': ['Strobe,3,gold,50']},
    'wait':{'TARGET': ['Alain2,10,red,20'], 'STRIP': ['Fireworks,1,random,1']},
    'quit':{'TARGET': ['Rainbow2,50,random,50'], 'STRIP': ['Rainbow,50,random,50']},
    'newgame':{},
    'ready':{},
    'release':{},
    'nextplayer':{'TARGET': ['Ring,20,random,50'], 'STRIP': ['Cylon,2,red,1']},
    'SB':{},
    'DB':{},
    '180':{'LIGHT': ['LIGHT_CELEBRATION, 2500'], 'STROBE': ['LIGHT_FLASH, 10']},
    'winner':{},
    'miss':{},
    'gameover':{},
    'interrupt':{},
    'simple':{'STROBE': ['TOY1, 1']},
    'double':{'STROBE': ['TOY1, 2']},
    'triple':{'STROBE': ['TOY1, 3']},
    'setwinner':{'STRIP':  ['Fireworks,1,gold,10'], 'TARGET': ['Wait,15,gold,100', 'Sparkle,10,gold,5']},
    'pressure': {'TARGET': ['TheaterChase,10,blue,10'], 'STRIP': ['RunningLights,100,blue,10']},
    'nopressure': {'TARGET': ['off,,,']}
    }

for letter in ['S', 'D', 'T']:
    for number in range(1, 21):
        DefaultConfig['Events'][f"{letter}{number}"] = {}

#
DefaultConfig['Raspberry_Leds'] = {
    'PIN_TARGETLED':0,
    'BRI_TARGETLED':0.5,
    'TYP_TARGETLED':'grb',
    'PIN_STRIPLED':0,
    'NBR_STRIPLED':0,
    'BRI_STRIPLED':0.5,
    'TYP_STRIPLED':'grb'
    }
#
DefaultConfig['Raspberry'] = {
    'PIN_UP': '0',
    'PIN_DOWN': '0',
    'PIN_LEFT': '0',
    'PIN_RIGHT': '0',
    'PIN_MINUS': '0',
    'PIN_PLUS': '0',
    'PIN_VALIDATE': '0',
    'PIN_CANCEL': '0',
    'PIN_NEXTPLAYER': '0',
    'PIN_BACK': '0',
    'PIN_GAMEBUTTON': '0',
    'PIN_VOLUME_UP': '0',
    'PIN_VOLUME_DOWN': '0',
    'PIN_VOLUME_MUTE': '0',
    'PIN_CPTPLAYER': '0',
    'PIN_MISSDART': '0',
    'LIGHT_NEXTPLAYER':'',
    'LIGHT_NAVIGATE':'',
    'LIGHT_VALIDATE':'',
    'LIGHT_BACK':'',
    'LIGHT_PLAYERS':'',
    'LIGHT_LASER':'',
    'LIGHT_FLASH':'',
    'LIGHT_CELEBRATION':'',
    'LIGHT_CELEBRATION2':'',
    'LIGHT_LIGHT':'',
    'TOY1': '',
    'TOY2': '',
    'TOY3': '',
    'TOY4': '',
    'TOY5': '',
    'TOY6': '',
    'TOY7': '',
    'TOY8': '',
    'TOY9': '',
    'TOY10': '',
    'TOY11': '',
    'TOY12': '',
    'TOY13': '',
    'TOY14': '',
    'TOY15': '',
    'TOY16': ''
    }
#
DefaultConfig['Camera'] = {
    'camera_id': '-1',
    'picture_path': os.path.expanduser('~/Pictures'),
    'video_path': os.path.expanduser('~/Videos'),
    'directory_order': '0',
    'choice_of_memories':'1',
    'video_res_width': '1280',
    'video_res_height': '720',
    'picture_res_width': '1280',
    'picture_res_height': '720',
    'flip_horizontal': '0',
    'flip_vertical': '0',
    'resolutions_available': '',
    'nb_picture': '1',
    'video_duration': '5',
    'fps': '30',
    'events': 'DB,SB,T20',
    'upload_cloud': '0',
    'path_google_drive': '',
    'fullscreen_pop': '0',
    'duree_ms': '5000'
    }
# Gallery of the memories on the local network (see cgallery). Its own section : the
# setup menu of the webcam writes back the [Camera] it read, and erased the password
DefaultConfig['Gallery'] = {
    # Hash of the password (see cgallery.hash_password) : empty, no password
    'password': ''
    }
# A deplacer dans un fichier yaml
#
######### CONFIG NB JOUEURS - 2 choix
#
#   nomdujeu : [ min , max , en equipe ]
DefaultConfig['NbOfPlayersPerGame'] = {
    'Routine' : [1, 4, False],
    'Duel' : [1, 2, False],
    'Shoot-out' : [1, 12, False],
    '321_Zlip': [2, 12, False], 
    'Batard': [1, 12, False],
    'Bermuda_Triangle': [1, 12, False],
    'Big6': [2, 12, False],
    'Bob27': [1, 12, False],
    'By_Fives': [1, 12, False],
    'Color': [1, 12, False],
    'Cricket': [1, 8, False], 
    'High_Score': [1, 12, False],
    'Ho_One': [1, 8, False],
    'Kapital': [1, 12, False],
    'Killer': [2, 12, False],
    'Kinito': [1, 12, False],
    'Low_Score': [1, 12, False],
    'Mickey': [1, 8, False],
    'Practice': [1, 12, False],
    'Round_the_clock': [1, 12, False],
    'Scram_Cricket': [2, 4, True],         #### NOTE : ce jeu se joue a 2 ou a 4, on ne peux pas jouer a 3 joueurs (d ailleurs pour moi, ce jeu ne se joue qu a 2, c est tres long commme jeu)
    'Shanghai': [1, 12, False],
    'Slider': [1, 12, False],
    'Up_Down_Count_Up': [1, 12, False],
    
    'Bingo': [ 1 , 4 , False ],
    'Bulls': [1, 12, False],
    'Castle': [2, 4, False],
    'Challenge': [2, 12, False],
    'Chaos': [1, 12, False],                    #### NOTE : nouveau jeu pas encore sorti, supprime si il faut
    'Conquer': [2, 4, False],
    'Dragon': [1, 12, False],                   #### NOTE : nouveau jeu pas encore fait, supprime si il faut
    'GameOfGoose': [1, 4, False], 
    'Dungeon': [2, 4, False],
    'Hangman': [1, 1, False], 
    'Incendie': [2, 4, False],    
    'Morpion': [2, 4, False],
    'Othello': [2, 4, True],                   #### NOTE : ce jeu se joue a 2 ou a 4, on ne peux pas jouer a 3 joueurs    
    'Puissance4': [2, 4, True],                #### NOTE : ce jeu se joue a 2 ou a 4, on ne peux pas jouer a 3 joueurs
    'Pursuit': [2, 4, False],   
    'Risk': [2, 5, False],
    'Robin_Drink': [2, 10, False],
    'Robin_Strip': [2, 10, False],
    'Sabotage': [2, 12, False],   
    'Simon': [2, 12, False],
    'Switch': [1, 12, False],
    'Target': [1, 12, False],
    'Tower': [1, 6, False],
    'Treasure': [2, 12, False],
    'Voleur': [1, 12, False],
    'Yahtzydarts': [1, 4, False],  
    
    'Balltrap': [1, 12, False],
    'Baseball': [2, 4, False],
    'Bowling': [1, 12, False],   
    'Fighters': [2, 5, False],
    'Football': [2, 2, False],                #### NOTE : ce jeu se joue a 2 uniquement
    'Golf': [1, 12, False],
    'Horse': [1, 4, False],
    'Pingpong': [2, 12, False],    
    'Punch-Out': [2, 7, False],       
    'Snooker': [1, 6, False],
    'Tennis': [2, 4, True]                   #### NOTE : ce jeu se joue a 2 ou a 4, on ne peux pas jouer a 3 joueurs    
    
    }

#   nom du jeu : categorie
DefaultConfig['GamePerCategory'] = {
    '321_Zlip': 'classic', 
    'Batard': 'classic',
    'Bermuda_Triangle': 'classic',
    'Big6': 'classic',
    'Bob27': 'classic',
    'By_Fives': 'classic',
    'Color': 'classic',
    'Cricket': 'classic', 
    'High_Score': 'classic',
    'Ho_One': 'classic',
    'Kapital': 'classic',
    'Killer': 'classic',
    'Kinito': 'classic',
    'Low_Score': 'classic',
    'Mickey': 'classic',
    'Practice': 'classic',
    'Round_the_clock': 'classic',
    'Routine' : 'classic',
    'Scram_Cricket': 'classic',         #### NOTE : ce jeu se joue a 2 ou a 4 , on ne peux pas jouer a 3 joueurs (d ailleurs pour moi, ce jeu ne se joue qu a 2, c est tres long commme jeu)
    'Shanghai': 'classic',
    'Slider': 'classic',
    'Up_Down_Count_Up': 'classic',
    
    'Bingo': 'fun',
    'Castle': 'fun',
    'Challenge': 'fun',
    'Chaos': 'fun',                    #### NOTE : nouveau jeu pas encore sorti, supprime si il faut
    'Conquer': 'fun',
    'Dungeon' : 'fun',
    'Dragon': 'fun',                   #### NOTE : nouveau jeu pas encore fait, supprime si il faut
    'GameOfGoose': 'fun', 
    'Incendie' : 'fun',
    'Morpion': 'fun',
    'Othello': 'fun',                   #### NOTE : ce jeu se joue a 2 ou a 4 , on ne peux pas jouer a 3 joueurs    
    'Puissance4': 'fun',                #### NOTE : ce jeu se joue a 2 ou a 4 , on ne peux pas jouer a 3 joueurs
    'Pursuit': 'fun',   
    'Risk': 'fun',
    'Robin_Drink': 'fun',
    'Robin_Strip': 'fun',
    'Sabotage': 'fun',   
    'Simon': 'fun',
    'Target': 'fun',
    'Tower': 'fun',
    'Treasure': 'fun',
    'Voleur': 'fun',
    'Yahtzydarts': 'fun', 
    
    'Balltrap': 'sport',
    'Baseball': 'sport',
    'Bowling': 'sport',   
    'Fighters': 'sport',
    'Football': 'sport',                #### NOTE : ce jeu se joue a 2 uniquement
    'Golf': 'sport',
    'Horse': 'sport',
    'Pingpong': 'sport',    
    'Punch-Out': 'sport',       
    'Snooker': 'sport',
    'Tennis': 'sport'                   #### NOTE : ce jeu se joue a 2 ou a 4 , on ne peux pas jouer a 3 joueurs    
    
    }

AlternateConfig['Raspberry'] = {
    'PIN_UP': 'A0',
    'PIN_DOWN': 'A1',
    'PIN_LEFT': 'A2',
    'PIN_RIGHT': 'A3',
    'PIN_PLUS': 'A4',
    'PIN_MINUS': 'A5',
    'PIN_VALIDATE': 'A6',
    'PIN_CANCEL':'A7',
    'PIN_NEXTPLAYER':'B0',
    'PIN_BACK':'B1',
    'PIN_GAMEBUTTON':'',
    'PIN_VOLUME_UP':'',
    'PIN_VOLUME_DOWN':'',
    'PIN_VOLUME_MUTE':'',
    'PIN_CPTPLAYER':'',
    'PIN_MISSDART':'',
    'LIGHT_NEXTPLAYER':'',
    'LIGHT_NAVIGATE':'',
    'LIGHT_VALIDATE':'',
    'LIGHT_BACK':'',
    'LIGHT_PLAYERS':'',
    'LIGHT_LASER':'',
    'LIGHT_FLASH':'',
    'LIGHT_CELEBRATION':'',
    'LIGHT_CELEBRATION2':'',
    'LIGHT_LIGHT':''
    }

#
DefaultConfig['Raspberry_BoardPinsIns'] = {}
for pin in range(1, 17):
    DefaultConfig['Raspberry_BoardPinsIns'][f'PIN_{pin}']= ''

#
DefaultConfig['Raspberry_BoardPinsOuts'] = {}
for pin in range(1, 11):
    DefaultConfig['Raspberry_BoardPinsOuts'][f'PIN_{pin}'] = ''

# Buttons connected to gpio
GPIO_BUTTONS_CONFIG = {
        'PLAYERBUTTON': '', 'GAMEBUTTON': '', 'BACKUPBUTTON': '', 'EXTRABUTTON': '',
        'MISSDART': '', 'SHOCKSENSOR': ''}

#
DefaultConfig['SectionKeys'] = {}

for key in [f'{mult}{num}' for mult in ['s', 'S', 'D', 'T'] for num in range(1, 21)] + ['SB', 'DB']:
    DefaultConfig['SectionKeys'][key] = ''
for button in GPIO_BUTTONS_CONFIG:
    DefaultConfig['SectionKeys'][button] = ''

#
DefaultConfig['LEDTarget'] = {}
for key in [f'{mult}{num}' for mult in ['S', 'D', 'T', 'E'] for num in range(1, 21)] + ['SB', 'DB']:
    DefaultConfig['LEDTarget'][key] = ''

#
DefaultConfig['Server'] = {
    'mastertest':False,
    'masterclosegames':False,
    'notifications':False,
    'notifications-smtp-server':None,
    'notifications-sender':None,
    'notifications-reply':None,
    'notifications-username':None,
    'notifications-password':None,
    'clear-db':False,
    'server2':False
    }

DefaultConfig['Colorset'] = {
    'border-radius' : 5,
    'border-size': 5,
    'padding': 2,

    'black': (0, 0, 0), # Black RVB color

    # Backgrounds
    'bg-global': False,
    'bg-round-nb': (255, 255, 255), #Black
    'bg-round-nb-header': (107, 134, 176), #Blue
    'bg-LOGO': (0, 0, 0), #Black
    'bg-darts-nb': (255, 255, 255), #Black
    'bg-darts-nb-header': (107, 134, 176), #Blue
    'bg-optionslist-header': (107, 134, 176), #Blue
    'bg-optionslist': (255, 255, 255), #Black

    # Players's colors (for leds and screen)
    'player1': (0, 255, 0),
    'player2': (0, 0, 255),
    'player3': (255, 0, 0),
    'player4': (255, 255, 0),
    'player5': (255, 0, 255),
    'player6': (0, 255, 255),
    'player7': (255, 0, 128),
    'player8': (0, 255, 128),
    'player9': (0, 128, 255),
    'player10': (255, 128, 0),
    'player11': (128, 255, 0),
    'player12': (128, 0, 255),

    # For menu screens
    'menu-header': (255, 255, 255),
    'menu-text': (0, 0, 0),
    'menu-selected': (112, 156, 118),
    'menu-shortcut': (224, 196, 119),
    'menu-alternate': (107, 134, 176),
    'menu-ok': (112, 156, 118),
    'menu-warning': (205, 144, 110),
    'menu-ko': (189, 108, 109),
    'menu-item-white': (255, 255, 255),
    'menu-item-black': (0, 0, 0),
    'menu-text-black': (0, 0, 0),
    'menu-text-white': (255, 255, 255),
    'menu-buttons': (232, 232, 232),
    'menu-favorite': (255, 215, 0),
    'menu-border': (0, 0, 0),

    # Game's deczription
    'description-bg': (213, 206, 186),
    'description-text': (0, 0, 0),
    'description-game': (0, 0, 0),
    # For game screen
    'game-bg': (0, 0, 0),
    'game-score': (255, 255, 255),
    'game-headers': (255, 255, 255),
    'game-player': (119, 119, 118),
    'game-alt-headers': (48, 48, 48),
    'game-round': (107, 134, 176),
    'game-title1': (48, 48, 48),
    'game-title2': (255, 255, 255),
    'game-type': (255, 0, 0),
    'game-table': (160, 160, 160),
    'game-text': (255, 255, 255),
    'game-option': (255, 215, 0),
    'game-darts': (160, 160, 160),
    'game-inactive': (119, 119, 118),
    'game-dead': (48, 48, 48),
    'game-green': (0, 255, 0),
    'game-gold': (255, 215, 0),
    'game-silver': (192, 192, 192),
    'game-bronze': (205, 127, 50),

    # Other
    'message-bg': (255, 255, 255),
    'message-text': (0, 0, 0),

    # Target LED option "Allumer tous les segments avec les couleurs d'origine":
    'target-sb': (189, 108, 109),
    'target-db': (107, 134, 176),
    'target-double1': (255, 255, 255),
    'target-double2': (255, 0, 0),
    'target-triple1': (255, 255, 255),
    'target-triple2': (255, 0, 0),
    'target-simple1': (0, 0, 255),
    'target-simple2': (255, 255, 255),

    # Bob's 27 colors
    'bob27-bg': (45, 78, 99),
    'bob27-blue': (46, 64, 76),
    'bob27-green': (45, 108, 85),
    'bob27-red': (124, 84, 87),
    'bob27-hit': (57, 209, 129),
    'bob27-miss': (232, 21, 37),
    'bob27-text': (255, 255, 255),

    # Color used for suggestion for all players (for target leds, this color will be used for all players if not None)
    'suggestion-color-allplayer': None, #(255, 0, 0) - Red

    # Show shortcuts or use a character
    'shortcuts': None, # None if you want to use 'F1,F2,etc' shortcut; empty -> '' <- for no shortcut; '>' for '> Partie simple' shortcut
    'center-shortcuts-text': False
}

EXTENDED_CONFIG = {
        'PIN_UP': 'A0', 'PIN_DOWN': 'A1', 'PIN_LEFT': 'A2', 'PIN_RIGHT': 'A3',
        'PIN_MINUS': 'A5', 'PIN_PLUS': 'A4', 'PIN_VALIDATE': 'A6', 'PIN_CANCEL': 'B1', 'PIN_NEXTPLAYER': 'B0',
        'PIN_BACK': 'A7', 'PIN_GAMEBUTTON': '', 'PIN_VOLUME_UP': '', 'PIN_VOLUME_DOWN': '',
        'PIN_VOLUME_MUTE': '', 'PIN_CPTPLAYER': '', 'PIN_MISSDART': '', 'LIGHT_NAVIGATE': '',
        'LIGHT_NEXTPLAYER': '', 'LIGHT_BACK': '', 'LIGHT_PLAYERS': '', 'LIGHT_LASER': '', 'LIGHT_FLASH': '',
        'LIGHT_VALIDATE': '', 'LIGHT_CELEBRATION' :'', 'LIGHT_CELEBRATION2' :'', 'LIGHT_LIGHT': '',
        'TOY1': 0, 'TOY2': 0, 'TOY3': 0, 'TOY4': 0
    }

GBCardConfig = {
    'CARD_NAME': 'RaspyCard',
    'INPUT': {
        'PIN_1': '6', 'PIN_2': '7', 'PIN_3': '8', 'PIN_4': '13', 'PIN_5': '16',
        'PIN_6': '18', 'PIN_7': '19', 'PIN_8': '20', 'PIN_9': '23', 'PIN_10': '24',
        'PIN_11': '25', 'PIN_12': '26', 'PIN_13': '', 'PIN_14': '', 'PIN_15': '', 'PIN_16': ''
        },
    'OUTPUT': {
        'PIN_1': '9', 'PIN_2': '10', 'PIN_3': '14', 'PIN_4': '15', 'PIN_5': '17',
        'PIN_6': '22', 'PIN_7': '27', 'PIN_8': '', 'PIN_9': '', 'PIN_10': ''
        },
    'KEYS': {
        'S1': '610', 'S2': '1617', 'S3': '817', 'S4': '1810', 'S5': '2622', 'S6': '2327',
        'S7': '2422', 'S8': '2510', 'S9': '1610', 'S10': '617', 'S11': '810', 'S12': '2610',
        'S13': '1822', 'S14': '710', 'S15': '1317', 'S16': '2410', 'S17': '717', 'S18': '2310',
        'S19': '2527', 'S20': '1310', 'D1': '69', 'D2': '2017', 'D3': '2022', 'D4': '189',
        'D5': '199', 'D6': '1922', 'D7': '209', 'D8': '259', 'D9': '169', 'D10': '1927', 'D11': '89',
        'D12': '269', 'D13': '1910', 'D14': '79', 'D15': '1917', 'D16': '249', 'D17': '2027',
        'D18': '239', 'D19': '2010', 'D20': '139', 'T1': '622', 'T2': '1614', 'T3': '814',
        'T4': '1827', 'T5': '2617', 'T6': '2315', 'T7': '2417', 'T8': '2522', 'T9': '1622',
        'T10': '615', 'T11': '822', 'T12': '2627', 'T13': '1817', 'T14': '722', 'T15': '1315',
        'T16': '2427', 'T17': '714', 'T18': '2322', 'T19': '2514', 'T20': '1322', 'SB': '2014',
        'DB': '1914', 's1': '627', 's2': '1615', 's3': '815', 's4': '1815', 's5': '2615',
        's6': '2314', 's7': '2415', 's8': '2517', 's9': '1627', 's10': '614', 's11': '827',
        's12': '2614', 's13': '1814', 's14': '727', 's15': '1314', 's16': '2414', 's17': '715',
        's18': '2317', 's19': '2515', 's20': '1327'
        },
    'EXTENDED': EXTENDED_CONFIG
    }

ClkCardConfig = {
    'CARD_NAME': 'La Chti Raspycard',
    'INPUT': {
        'PIN_1': '24', 'PIN_2': '25', 'PIN_3': '8', 'PIN_4': '7', 'PIN_5': '16',
        'PIN_6': '20', 'PIN_7': '26', 'PIN_8': '19', 'PIN_9': '13', 'PIN_10': '6',
        'PIN_11': '', 'PIN_12': '', 'PIN_13': '', 'PIN_14': '', 'PIN_15': '', 'PIN_16': ''
        },
    'OUTPUT': {
        'PIN_1': '15', 'PIN_2': '17', 'PIN_3': '27', 'PIN_4': '22', 'PIN_5': '5',
        'PIN_6': '9', 'PIN_7': '11', 'PIN_8': '', 'PIN_9': '', 'PIN_10': ''
        },
    'KEYS': {
        'S1': '245', 'S2': '1627', 'S3': '827', 'S4': '85', 'S5': '195', 'S6': '165',
        'S7': '2427', 'S8': '1927', 'S9': '65', 'S10': '205', 'S11': '1327', 'S12': '135',
        'S13': '75', 'S14': '627', 'S15': '2027', 'S16': '2627', 'S17': '727', 'S18': '255',
        'S19': '2527', 'S20': '265', 'D1': '249', 'D2': '1617', 'D3': '817', 'D4': '89',
        'D5': '199', 'D6': '169', 'D7': '2417', 'D8': '1917', 'D9': '69', 'D10': '209',
        'D11': '1317', 'D12': '139', 'D13': '79', 'D14': '617', 'D15': '2017', 'D16': '2617',
        'D17': '717', 'D18': '259', 'D19': '2517', 'D20': '269', 'T1': '2411', 'T2': '1615',
        'T3': '815', 'T4': '811', 'T5': '1911', 'T6': '1611', 'T7': '2415', 'T8': '1915',
        'T9': '611', 'T10': '2011', 'T11': '1315', 'T12': '1311', 'T13': '711', 'T14': '615',
        'T15': '2015', 'T16': '2615', 'T17': '715', 'T18': '2511', 'T19': '2515', 'T20': '2611',
        'SB': '1322', 'DB': '622'
        },
    'EXTENDED': EXTENDED_CONFIG
    }

JtCardConfig = {
    'CARD_NAME': 'Carte de Julien V1',
    'INPUT': {
        'PIN_1': '17', 'PIN_2': '27', 'PIN_3': '22', 'PIN_4': '10', 'PIN_5': '9',
        'PIN_6': '11', 'PIN_7': '24', 'PIN_8': '25', 'PIN_9': '8', 'PIN_10': '7',
        'PIN_11': '', 'PIN_12': '', 'PIN_13': '', 'PIN_14': '', 'PIN_15': '', 'PIN_16': ''
        },
    'OUTPUT': {
        'PIN_1': '5', 'PIN_2': '6', 'PIN_3': '13', 'PIN_4': '19', 'PIN_5': '26',
        'PIN_6': '16', 'PIN_7': '20', 'PIN_8': '', 'PIN_9': '', 'PIN_10': ''
        },
    'KEYS': {
        'S1': '1013', 'S2': '2416', 'S3': '916', 'S4': '913', 'S5': '2213', 'S6': '2413',
        'S7': '1016', 'S8': '2216', 'S9': '1713', 'S10': '713', 'S11': '2716', 'S12': '2713',
        'S13': '813', 'S14': '1716', 'S15': '716', 'S16': '2516', 'S17': '816', 'S18': '1113',
        'S19': '1116', 'S20': '2513', 'D1': '106', 'D2': '2426', 'D3': '926', 'D4': '96',
        'D5': '226', 'D6': '246', 'D7': '1026', 'D8': '2226', 'D9': '176', 'D10': '76', 'D11': '2726',
        'D12': '276', 'D13': '86', 'D14': '1726', 'D15': '726', 'D16': '2526', 'D17': '826',
        'D18': '116', 'D19': '1126', 'D20': '256', 'T1': '105', 'T2': '2420', 'T3': '920',
        'T4': '95', 'T5': '225', 'T6': '245', 'T7': '1020', 'T8': '2220', 'T9': '175',
        'T10': '75', 'T11': '2720', 'T12': '275', 'T13': '85', 'T14': '1720', 'T15': '720',
        'T16': '2520', 'T17': '820', 'T18': '115', 'T19': '1120', 'T20': '255', 'SB': '2719',
        'DB': '1719',
        'PLAYERBUTTON': '', 'GAMEBUTTON': '', 'BACKUPBUTTON': '', 'EXTRABUTTON': '', 'MISSDART': ''
        },
    'EXTENDED': EXTENDED_CONFIG
    }

Jt2CardConfig = {
    'CARD_NAME': 'Carte de Julien V2',
    'INPUT': {
        'PIN_1': '17', 'PIN_2': '27', 'PIN_3': '22', 'PIN_4': '23', 'PIN_5': '24',
        'PIN_6': '9', 'PIN_7': '25', 'PIN_8': '11', 'PIN_9': '8', 'PIN_10': '7',
        'PIN_11': '', 'PIN_12': '', 'PIN_13': '', 'PIN_14': '', 'PIN_15': '', 'PIN_16': ''
        },
    'OUTPUT': {
        'PIN_1': '20', 'PIN_2': '26', 'PIN_3': '19', 'PIN_4': '16', 'PIN_5': '13',
        'PIN_6': '6', 'PIN_7': '5', 'PIN_8': '', 'PIN_9': '', 'PIN_10': ''
        },
    'KEYS': {
        'S1':'2417','S2':'1622','S3':'822','S4':'817','S5':'1917','S6':'1617',
        'S7':'2422','S8':'1922','S9':'617','S10':'2017','S11':'1322','S12':'1317',
        'S13':'717','S14':'622','S15':'2022','S16':'2622','S17':'722','S18':'2517',
        'S19':'2522','S20':'2617','D1':'2415','D2':'1610','D3':'810','D4':'815',
        'D5':'1915','D6':'1615','D7':'2410','D8':'1910','D9':'615','D10':'2015','D11':'1310',
        'D12':'1315','D13':'715','D14':'610','D15':'2010','D16':'2610','D17':'710',
        'D18':'2515','D19':'2510','D20':'2615','T1':'2411','T2':'169','T3':'89',
        'T4':'811','T5':'1911','T6':'1611','T7':'249','T8':'199','T9':'611',
        'T10':'2011','T11':'139','T12':'1311','T13':'711','T14':'69','T15':'209',
        'T16':'269','T17':'79','T18':'2511','T19':'259','T20':'2611','SB':'1327',
        'DB':'627',
        'PLAYERBUTTON': '', 'GAMEBUTTON': '', 'BACKUPBUTTON': '', 'EXTRABUTTON': '', 'MISSDART': ''
        },
    'EXTENDED': EXTENDED_CONFIG
    }

ED900Config = {
    'CARD_NAME': 'RaspyCard',
    'INPUT': {
        'PIN_1': '6', 'PIN_2': '7', 'PIN_3': '8', 'PIN_4': '13', 'PIN_5': '16',
        'PIN_6': '18', 'PIN_7': '19', 'PIN_8': '20', 'PIN_9': '23', 'PIN_10': '24',
        'PIN_11': '25', 'PIN_12': '26', 'PIN_13': '', 'PIN_14': '', 'PIN_15': '', 'PIN_16': ''
        },
    'OUTPUT': {
        'PIN_1': '9', 'PIN_2': '10', 'PIN_3': '17', 'PIN_4': '15', 'PIN_5': '14',
        'PIN_6': '22', 'PIN_7': '27', 'PIN_8': '', 'PIN_9': '', 'PIN_10': ''
        },
    'KEYS': {
        'S1': '610', 'S2': '1617', 'S3': '817', 'S4': '1810', 'S5': '2622', 'S6': '2327',
        'S7': '2422', 'S8': '2517', 'S9': '1610', 'S10': '617', 'S11': '810', 'S12': '2610',
        'S13': '1817', 'S14': '710', 'S15': '1317', 'S16': '2410', 'S17': '717', 'S18': '2310',
        'S19': '2510', 'S20': '1310', 'D1': '69', 'D2': '2017', 'D3': '2022', 'D4': '189',
        'D5': '199', 'D6': '1922', 'D7': '209', 'D8': '259', 'D9': '169', 'D10': '1927', 'D11': '89',
        'D12': '269', 'D13': '1910', 'D14': '79', 'D15': '1914', 'D16': '249', 'D17': '2027',
        'D18': '239', 'D19': '2010', 'D20': '139', 'T1': '622', 'T2': '1614', 'T3': '814',
        'T4': '1815', 'T5': '2617', 'T6': '2315', 'T7': '2417', 'T8': '2514', 'T9': '1622',
        'T10': '615', 'T11': '822', 'T12': '2627', 'T13': '1822', 'T14': '722', 'T15': '1315',
        'T16': '2427', 'T17': '714', 'T18': '2322', 'T19': '2522', 'T20': '1322', 'SB': '2014',
        'DB': '1917', 's1': '627', 's2': '1615', 's3': '815', 's4': '1827', 's5': '2615',
        's6': '2314', 's7': '2415', 's8': '2515', 's9': '1627', 's10': '614', 's11': '827',
        's12': '2614', 's13': '1814', 's14': '727', 's15': '1314', 's16': '2414', 's17': '715',
        's18': '2317', 's19': '2527', 's20': '1327',
        'PLAYERBUTTON': '', 'GAMEBUTTON': '', 'BACKUPBUTTON': '', 'EXTRABUTTON': ''},
        'EXTENDED': EXTENDED_CONFIG
    }

JiCardConfig = {
    'CARD_NAME': 'RaspyCard - MM WS',
    'INPUT': {
        'PIN_1': '24', 'PIN_2': '25', 'PIN_3': '8', 'PIN_4': '7', 'PIN_5': '16',
        'PIN_6': '20', 'PIN_7': '26', 'PIN_8': '19', 'PIN_9': '13', 'PIN_10': '6',
        'PIN_11': '', 'PIN_12': '', 'PIN_13': '', 'PIN_14': '', 'PIN_15': '', 'PIN_16': ''
        },
    'OUTPUT': {
        'PIN_1': '15', 'PIN_2': '17', 'PIN_3': '27', 'PIN_4': '22', 'PIN_5': '10',
        'PIN_6': '9', 'PIN_7': '11', 'PIN_8': '', 'PIN_9': '', 'PIN_10': ''
        },
    'KEYS': {
        'S1': '2410', 'S2': '1627', 'S3': '827', 'S4': '810', 'S5': '1910', 'S6': '1610',
        'S7': '2427', 'S8': '1927', 'S9': '610', 'S10': '2010', 'S11': '1327', 'S12': '1310',
        'S13': '710', 'S14': '627', 'S15': '2027', 'S16': '2627', 'S17': '727', 'S18': '2510',
        'S19': '2527', 'S20': '2610', 'D1': '249', 'D2': '1617', 'D3': '817', 'D4': '89',
        'D5': '199', 'D6': '169', 'D7': '2417', 'D8': '1917', 'D9': '69', 'D10': '209',
        'D11': '1317', 'D12': '139', 'D13': '79', 'D14': '617', 'D15': '2017', 'D16': '2617',
        'D17': '717', 'D18': '259', 'D19': '2517', 'D20': '269', 'T1': '2411', 'T2': '1615',
        'T3': '815', 'T4': '811', 'T5': '1911', 'T6': '1611', 'T7': '2415', 'T8': '1915',
        'T9': '611', 'T10': '2011', 'T11': '1315', 'T12': '1311', 'T13': '711', 'T14': '615',
        'T15': '2015', 'T16': '2615', 'T17': '715', 'T18': '2511', 'T19': '2515', 'T20': '2611',
        'SB': '1322', 'DB': '622',
        'PLAYERBUTTON': '', 'GAMEBUTTON': '', 'BACKUPBUTTON': '', 'EXTRABUTTON': ''
        },
    'EXTENDED': EXTENDED_CONFIG
    }

Ji2CardConfig = {
    'CARD_NAME': 'RaspyCard v4',
    'INPUT': {
        'PIN_1': '24', 'PIN_2': '25', 'PIN_3': '8', 'PIN_4': '7', 'PIN_5': '16',
        'PIN_6': '20', 'PIN_7': '26', 'PIN_8': '19', 'PIN_9': '13', 'PIN_10': '6',
        'PIN_11': '', 'PIN_12': '', 'PIN_13': '', 'PIN_14': '', 'PIN_15': '', 'PIN_16': ''},
    'OUTPUT': {
        'PIN_1': '15', 'PIN_2': '17', 'PIN_3': '27', 'PIN_4': '22', 'PIN_5': '10',
        'PIN_6': '9', 'PIN_7': '11', 'PIN_8': '', 'PIN_9': '', 'PIN_10': ''},
    'KEYS': {
        'S1': '2417', 'S2': '1622', 'S3': '822', 'S4': '817', 'S5': '1917', 'S6': '1617',
        'S7': '2422', 'S8': '1922', 'S9': '617', 'S10': '2017', 'S11': '1322', 'S12': '1317',
        'S13': '717', 'S14': '622', 'S15': '2022', 'S16': '2622', 'S17': '722', 'S18': '2517',
        'S19': '2522', 'S20': '2617', 'D1': '2415', 'D2': '1610', 'D3': '810', 'D4': '815',
        'D5': '1915', 'D6': '1615', 'D7': '2410', 'D8': '1910', 'D9': '615', 'D10': '2015',
        'D11': '1310', 'D12': '1315', 'D13': '715', 'D14': '610', 'D15': '2010', 'D16': '2610',
        'D17': '710', 'D18': '2515', 'D19': '2510', 'D20': '2615', 'T1': '2411', 'T2': '169',
        'T3': '89', 'T4': '811', 'T5': '1911', 'T6': '1611', 'T7': '249', 'T8': '199',
        'T9': '611', 'T10': '2011', 'T11': '139', 'T12': '1311', 'T13': '711', 'T14': '69',
        'T15': '209', 'T16': '269', 'T17': '79', 'T18': '2511', 'T19': '259', 'T20': '2611',
        'SB': '1327', 'DB': '627',
        'PLAYERBUTTON': '', 'GAMEBUTTON': '', 'BACKUPBUTTON': '', 'EXTRABUTTON': ''
        },
    'EXTENDED': EXTENDED_CONFIG
    }

JizCardConfig = {
    'CARD_NAME': 'RaspyZcard',
    'INPUT': {
        'PIN_1': '24', 'PIN_2': '25', 'PIN_3': '8', 'PIN_4': '7', 'PIN_5': '16',
        'PIN_6': '20', 'PIN_7': '26', 'PIN_8': '19', 'PIN_9': '13', 'PIN_10': '6',
        'PIN_11': '', 'PIN_12': '', 'PIN_13': '', 'PIN_14': '', 'PIN_15': '', 'PIN_16': ''
        },
    'OUTPUT': {
        'PIN_1': '14', 'PIN_2': '15', 'PIN_3': '17', 'PIN_4': '27', 'PIN_5': '22',
        'PIN_6': '10', 'PIN_7': '9', 'PIN_8': '', 'PIN_9': '', 'PIN_10': ''
        },
    'KEYS': {
        'S1': '617', 'S2': '2022', 'S3': '1922', 'S4': '1917', 'S5': '817', 'S6': '2017',
        'S7': '622', 'S8': '822', 'S9': '2417', 'S10': '1617', 'S11': '2522', 'S12': '2517',
        'S13': '2617', 'S14': '2422', 'S15': '1622', 'S16': '722', 'S17': '2622', 'S18': '1317',
        'S19': '1322', 'S20': '717', 'D1': '615', 'D2': '2010', 'D3': '1910', 'D4': '1915',
        'D5': '815', 'D6': '2015', 'D7': '610', 'D8': '810', 'D9': '2415', 'D10': '1615',
        'D11': '2510', 'D12': '2515', 'D13': '2615', 'D14': '2410', 'D15': '1610', 'D16': '710',
        'D17': '2610', 'D18': '1315', 'D19': '1310', 'D20': '715', 'T1': '614', 'T2': '209',
        'T3': '199', 'T4': '1914', 'T5': '814', 'T6': '2014', 'T7': '69', 'T8': '89',
        'T9': '2414', 'T10': '1614', 'T11': '259', 'T12': '2514', 'T13': '2614', 'T14': '249',
        'T15': '169', 'T16': '79', 'T17': '269', 'T18': '1314', 'T19': '139', 'T20': '714',
        'SB': '2527', 'DB': '2427',
        'PLAYERBUTTON': '', 'GAMEBUTTON': '', 'BACKUPBUTTON': '', 'EXTRABUTTON': ''
        },
    'EXTENDED': EXTENDED_CONFIG
    }

JoCardConfig = {
    'CARD_NAME': 'Extendart ED110 7*10',
    'INPUT': {
        'PIN_1': '4', 'PIN_2': '5', 'PIN_3': '6', 'PIN_4': '9', 'PIN_5': '11',
        'PIN_6': '13', 'PIN_7': '17', 'PIN_8': '19', 'PIN_9': '22', 'PIN_10': '27',
        'PIN_11': '', 'PIN_12': '', 'PIN_13': '', 'PIN_14': '', 'PIN_15': '', 'PIN_16': ''},
    'OUTPUT': {
        'PIN_1': '7', 'PIN_2': '8', 'PIN_3': '16', 'PIN_4': '20', 'PIN_5': '23',
        'PIN_6': '24', 'PIN_7': '25', 'PIN_8': '', 'PIN_9': '', 'PIN_10': ''
        },
    'KEYS': {
        'S1': '425', 'S2': '97', 'S3': '277', 'S4': '2725', 'S5': '625', 'S6': '925',
        'S7': '47', 'S8': '67', 'S9': '1925', 'S10': '1125', 'S11': '137',
        'S12': '1325', 'S13': '2225', 'S14': '197', 'S15': '117', 'S16': '57',
        'S17': '227', 'S18': '1725', 'S19': '177', 'S20': '525', 'D1': '424',
        'D2': '916', 'D3': '2716', 'D4': '2724', 'D5': '624', 'D6': '924',
        'D7': '416', 'D8': '616', 'D9': '1924', 'D10': '1124', 'D11': '1316',
        'D12': '1324', 'D13': '2224', 'D14': '1916', 'D15': '1116', 'D16': '516',
        'D17': '2216', 'D18': '1724', 'D19': '1716', 'D20': '524', 'T1': '423',
        'T2': '920', 'T3': '2720', 'T4': '2723', 'T5': '623', 'T6': '923',
        'T7': '420', 'T8': '620', 'T9': '1923', 'T10': '1123', 'T11': '1320',
        'T12': '1323', 'T13': '2223', 'T14': '1920', 'T15': '1120', 'T16': '520',
        'T17': '2220', 'T18': '1723', 'T19': '1720', 'T20': '523', 'SB': '138', 'DB': '198',
        'PLAYERBUTTON': '', 'GAMEBUTTON': '', 'BACKUPBUTTON': '', 'EXTRABUTTON': ''
        },
    'EXTENDED': EXTENDED_CONFIG
    }

Jo416CardConfig = {
    'CARD_NAME': 'Extendart 4*16',
    'INPUT': {
        'PIN_1': '6', 'PIN_2': '5', 'PIN_3': '11', 'PIN_4': '9', 'PIN_5': '22',
        'PIN_6': '27', 'PIN_7': '17', 'PIN_8': '4', 'PIN_9': '23', 'PIN_10': '24',
        'PIN_11': '25', 'PIN_12': '8', 'PIN_13': '7', 'PIN_14': '16', 'PIN_15': '20', 'PIN_16': '26'},
    'OUTPUT': {
        'PIN_1': '14', 'PIN_2': '15', 'PIN_3': '19', 'PIN_4': '13', 'PIN_5': '',
        'PIN_6': '', 'PIN_7': '', 'PIN_8': '', 'PIN_9': '', 'PIN_10': ''},
    'KEYS': {
        'S1': '2714', 'S2': '515', 'S3': '413', 'S4': '514', 'S5': '2414', 'S6': '415',
        'S7': '913', 'S8': '2419', 'S9': '919', 'S10': '2715', 'S11': '419',
        'S12': '519', 'S13': '2415', 'S14': '2719', 'S15': '915', 'S16': '513',
        'S17': '2413', 'S18': '914', 'S19': '2713', 'S20': '414', 'D1': '2214',
        'D2': '615', 'D3': '1713', 'D4': '614', 'D5': '2314', 'D6': '1715',
        'D7': '1113', 'D8': '2319', 'D9': '1119', 'D10': '2215', 'D11': '1719',
        'D12': '619', 'D13': '2315', 'D14': '2219', 'D15': '1115', 'D16': '613',
        'D17': '2313', 'D18': '1114', 'D19': '2213', 'D20': '1714', 'T1': '1614',
        'T2': '815', 'T3': '2013', 'T4': '814', 'T5': '2614', 'T6': '2015',
        'T7': '713', 'T8': '2619', 'T9': '719', 'T10': '1615', 'T11': '2019',
        'T12': '819', 'T13': '2615', 'T14': '1619', 'T15': '715', 'T16': '813',
        'T17': '2613', 'T18': '714', 'T19': '1613', 'T20': '2014', 'SB': '2515', 'DB': '2513',
        'PLAYERBUTTON': '', 'GAMEBUTTON': '', 'BACKUPBUTTON': '', 'EXTRABUTTON': ''
        },
    'EXTENDED': EXTENDED_CONFIG
    }

JiLedsConfig = {'S1': '99,98,97,95,94,93,92', 'S2': '29,28,27,25,24,23,22', 'S3': '9,8,7,5,4,3,2',
    'S4': '79,78,77,75,74,73,72', 'S5': '110,111,112,114,116,115,117', 'S6': '59,58,57,55,54,53,52',
    'S7': '180,181,182,184,186,185,187', 'S8': '160,161,162,164,166,165,167', 'S9': '130,131,132,134,136,135,137',
    'S10':'49,48,47,45,44,43,42', 'S11': '159,158,157,155,154,153,152', 'S12': '129,128,127,125,124,123,122',
    'S13': '60,61,62,64,66,65,67', 'S14': '149,148,147,145,144,143,142', 'S15': '30,31,32,34,36,35,37',
    'S16': '179,178,177,175,174,173,172', 'S17': '10,11,12,14,16,15,17', 'S18': '80,81,82,84,86,85,87',
    'S19': '199,198,197,195,194,193,192', 'S20': '109,108,107,105,104,103,102', 'D1': '91,90', 'D2': '21,20',
    'D3': '1,0', 'D4': '71,70', 'D5': '119,118', 'D6': '51,50', 'D7': '189,188', 'D8': '169,168', 'D9': '139,138',
    'D10': '41,40', 'D11': '151,150', 'D12': '121,120', 'D13': '69,68', 'D14': '141,140', 'D15': '39,38',
    'D16': '171,170', 'D17': '19,18', 'D18': '89,88', 'D19': '191,190', 'D20': '101,100', 'T1': '96', 'T2': '26',
    'T3': '6', 'T4': '76', 'T5': '113', 'T6': '56', 'T7': '183', 'T8': '163', 'T9': '133', 'T10': '46', 'T11': '156',
    'T12': '126', 'T13': '63', 'T14': '146', 'T15': '33', 'T16': '176', 'T17': '13', 'T18': '83', 'T19': '196',
    'T20': '106', 'E1': '223,222', 'E2': '209,208', 'E3': '205,204', 'E4': '219,218', 'E5': '227,226', 'E6': '215,214', 
    'E7': '241,240', 'E8': '237,236', 'E9': '231,230', 'E10': '213,212', 'E11': '235,234', 'E12': '229,228', 'E13': '217,216', 
    'E14': '233,232', 'E15': '211,210', 'E16': '239,238', 'E17': '207,206', 'E18': '221,220', 'E19': '243,242', 'E20': '225,224',
    'SB': '200,201,202', 'DB': '203'}

MMWorkshopVdartsLedsConfig = {'S1':'79,78,76,75,74','S2':'23,22,20,19,18','S3':'7,6,4,3,2',
    'S4':'63,62,60,59,58','S5':' 88,89,91,92,93','S6':'47,46,44,43,42',
    'S7':'144,145,147,148,149','S8':'128,129,131,132,133','S9':'104,105,107,108,109',
    'S10':'39,38,36,35,34','S11':'127,126,124,123,122','S12':'103,102,100,99,98',
    'S13':'48,49,51,52,53','S14':'119,118,116,115,114','S15':'24,25,27,28,29',
    'S16':'143,142,140,139,138','S17':'8,9,11,12,13','S18':'64,65,67,68,69',
    'S19':'159,158,156,155,154','S20':'87,86,84,83,82','D1':'73,72','D2':'17,16',
    'D3':'1,0','D4':'57,56','D5':'95,94','D6':'41,40','D7':'151,150','D8':'135,134','D9':'111,110',
    'D10':'33,32','D11':'121,120','D12':'97,96','D13':'55,54','D14':'113,112','D15':'31,30',
    'D16':'137,136','D17':'15,14','D18':'71,70','D19':'153,152','D20':'81,80 ','T1':'77','T2':'21',
    'T3':'5','T4':'61','T5':'90','T6':'45','T7':'146','T8':'130','T9':'106','T10':'37','T11':'125',
    'T12':'101','T13':'50','T14':'117','T15':'26','T16':'141','T17':'10','T18':'66','T19':'157',
    'T20':'85','E1':'','E2':'','E3':'','E4':'','E5':'','E6':'','E7':'','E8':'','E9':'','E10':'',
    'E11':'','E12':'','E13':'','E14':'','E15':'','E16':'','E17':'','E18':'','E19':'','E20':'',
    'SB':'160,161,162','DB':'163'}

MMWorksVDartsCardConfig = {
    'CARD_NAME': 'MMWorkshop VDarts Card',
    'INPUT': {
        'PIN_1': '6', 'PIN_2': '13', 'PIN_3': '19', 'PIN_4': '26', 'PIN_5': '20',
        'PIN_6': '16', 'PIN_7': '7', 'PIN_8': '8', 'PIN_9': '25', 'PIN_10': '24',
        'PIN_11': '14', 'PIN_12': '4', 'PIN_13': '', 'PIN_14': '', 'PIN_15': '', 'PIN_16': ''
        },
    'OUTPUT': {
        'PIN_1': '11', 'PIN_2': '9', 'PIN_3': '10', 'PIN_4': '22', 'PIN_5': '27',
        'PIN_6': '17', 'PIN_7': '15', 'PIN_8': '', 'PIN_9': '', 'PIN_10': ''
        },
    'KEYS': {
        's1':'1922', 's2':'89', 's3':'249', 's4':'69', 's5':'169', 's6':'1311',
        's7':'49', 's8':'1410', 's9':'822', 's10':'1911', 's11':'2422', 's12':'1611',
        's13':'611', 's14':'2522', 's15':'2611', 's16':'411', 's17':'259', 's18':'1310',
        's19':'149', 's20':'2622', 'S1':'1917', 'S2':'810', 'S3':'2410', 'S4':'617', 'S5':'1627',
        'S6':'1322', 'S7':'427', 'S8':'1417', 'S9':'817', 'S10':'1910', 'S11':'2417', 'S12':'1617',
        'S13':'627', 'S14':'2517', 'S15':'2610', 'S16':'417', 'S17':'2510', 'S18':'1317', 'S19':'1422',
        'S20':'2617', 'D1':'1915', 'D2':'710', 'D3':'727', 'D4':'615', 'D5':'2015', 'D6':'2027', 'D7':'715',
        'D8':'1415', 'D9':'815', 'D10':'2022', 'D11':'2415', 'D12':'1615', 'D13':'2017', 'D14':'2515', 'D15':'2010',
        'D16':'415', 'D17':'722', 'D18':'1315', 'D19':'717', 'D20':'2615', 'T1':'1927', 'T2':'811', 'T3':'2411',
        'T4':'622', 'T5':'1610', 'T6':'139', 'T7':'410', 'T8':'1427', 'T9':'827', 'T10':'199', 'T11':'2427',
        'T12':'1622', 'T13':'610', 'T14':'2527', 'T15':'269', 'T16':'422', 'T17':'2511', 'T18':'1327',
        'T19':'1411', 'T20':'2627', 'SB':'711', 'DB':'2011'
        },
    'EXTENDED': EXTENDED_CONFIG
    }


#
# Start of Config Class
#
class Config:
    def __init__(self, logs):
        # Define paths
        self.GPIO_BUTTONS_CONFIG = GPIO_BUTTONS_CONFIG
        self.default_SectionKeys = DefaultConfig['SectionKeys']

        self.userpath = os.path.expanduser('~')
        self.user_dir = cpaths.user_dir()
        self.other_dir = f'{self.user_dir}/other'
        self.configFile = cpaths.config_file()
        self.themes_dir = f'{self.user_dir}/themes'
        self.root_dir = cpaths.ROOT_DIR
        self.fontsDir = f'{self.root_dir}/fonts'
        self.gamesDir = f'{self.root_dir}/games'
        self.dirs = {'images': ['images', ['png', 'jpg', 'gif']],
                'sounds': ['sounds', ['ogg']],
                'videos': ['videos', ['mkv', 'mp4']],
                'fonts': ['fonts', ['ttf']],
                'text': ['other', ['cfg', 'txt']]}
        self.dartsStrokeDir = f"{self.root_dir}/{self.dirs['images']}/valeurs"
        self.versionFile = f'{self.root_dir}/VERSION'
        self.changelogFile = f'{self.root_dir}/CHANGELOG'

        # Local logs object
        self.logs = logs
        # Copy into object the value of default config
        self.config = DefaultConfig
        # Default score map (can be overrided in games)
        self.default_score_map = {'SB': 25, 'DB': 50,
              's20': 20, 'S20': 20, 'D20': 40, 'T20': 60,
              's19': 19, 'S19': 19, 'D19': 38, 'T19': 57,
              's18': 18, 'S18': 18, 'D18': 36, 'T18': 54,
              's17': 17, 'S17': 17, 'D17': 34, 'T17': 51,
              's16': 16, 'S16': 16, 'D16': 32, 'T16': 48,
              's15': 15, 'S15': 15, 'D15': 30, 'T15': 45,
              's14': 14, 'S14': 14, 'D14': 28, 'T14': 42,
              's13': 13, 'S13': 13, 'D13': 26, 'T13': 39,
              's12': 12, 'S12': 12, 'D12': 24, 'T12': 36,
              's11': 11, 'S11': 11, 'D11': 22, 'T11': 33,
              's10': 10, 'S10': 10, 'D10': 20, 'T10': 30,
              's9': 9, 'S9': 9, 'D9': 18, 'T9': 27,
              's8': 8, 'S8': 8, 'D8': 16, 'T8': 24,
              's7': 7, 'S7': 7, 'D7': 14, 'T7': 21,
              's6': 6, 'S6': 6, 'D6': 12, 'T6': 18,
              's5': 5, 'S5': 5, 'D5': 10, 'T5': 15,
              's4': 4, 'S4': 4, 'D4': 8, 'T4': 12,
              's3': 3, 'S3': 3, 'D3': 6, 'T3': 9,
              's2': 2, 'S2': 2, 'D2': 4, 'T2': 6,
              's1': 1, 'S1': 1, 'D1': 2, 'T1': 3,
              'MISS': 0
              }
        # pyDarts running Version
        self.pyDartsVersion = self.get_version()
        self.pyDartsFullVersion = self.get_version()
        self.pyDartsVersion = self.pyDartsVersion[1:6]
        # pyDarts running wiki
        self.wiki = wiki
        # Official website
        self.officialwebsite = officialwebsite
        # Supported games (games availables in compiled version)
        self.officialgames = ['321_Zlip', 'Cricket', 'Football', 'Ho_One', 'Kapital', 'Kinito', 'Practice', 'Sample_game', 'Shanghai']
        # List of compatibles versions of python
        # 3.7 : Raspbian Buster - 3.13 : Raspberry Pi OS Trixie
        self.supported_python_versions = ('3.2', '3.3', '3.4', '3.5', '3.6', '3.7', '3.8', '3.13')

        # Order of your dart board parts
        self.keys = ['S20', 'S1', 'S18', 'S4', 'S13', 'S6', 'S10', 'S15', 'S2', 'S17', 'S3',
                         'S19', 'S7', 'S16', 'S8', 'S11', 'S14', 'S9', 'S12', 'S5', 'D20', 'D1',
                         'D18', 'D4', 'D13', 'D6', 'D10', 'D15', 'D2', 'D17', 'D3', 'D19', 'D7',
                         'D16', 'D8', 'D11', 'D14', 'D9', 'D12', 'D5', 'T20', 'T1', 'T18', 'T4',
                         'T13', 'T6', 'T10', 'T15', 'T2', 'T17', 'T3', 'T19', 'T7', 'T16', 'T8',
                         'T11', 'T14', 'T9', 'T12', 'T5', 'SB', 'DB', 'PLAYERBUTTON', 'GAMEBUTTON',
                         'BACKUPBUTTON', 'EXTRABUTTON']

        self.interior_keys = ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11'
                's12', 's13', 's14', 's15', 's16', 's17', 's18', 's19', 's20']

        self.outputs = DefaultConfig['Raspberry_BoardPinsOuts']
        self.inputs = DefaultConfig['Raspberry_BoardPinsIns']
        self.leds = DefaultConfig['Raspberry_Leds']
        self.buttons = DefaultConfig['Raspberry']

        self.camera = DefaultConfig['Camera']

        # Print version if requested
        with open('/proc/device-tree/model') as f:
            self.rpi_version = f.readlines()
        f.close()

        # Print version if requested
        with open('/sys/firmware/devicetree/base/serial-number') as f:
            self.rpi_serial = f.readlines()
        f.close()

        self.rpi_serial = self.rpi_serial[0].rstrip('\x00')
        self.rpi_version = self.rpi_version[0].replace('Raspberry ', '').rstrip('\x00')
        self.rpi_model = rpi_versions.get(self.rpi_version.split(' Rev')[0], '0')
        self.file_exists = False

        if self.rpi_model in ('0', '3A+', '3B+'):
            self.delay = 0.1
        else:
            self.delay = 0.1

    def print(self):
        value = f"{self.config}"
        value = value.replace("'", '"').replace('True', '"True"').replace('False', '"False"').replace('None', '"None"')
        value = value.replace('(', '"(').replace(')', ')"').replace('|"(', '|(').replace(')""', ')"')
        parsed = json.loads(value)

        pretty = json.dumps(parsed, indent=4)

        print(pretty)

    def get_version(self):
        """
        Return actual version of pydarts stored in VERSION file
        """

        with open (self.versionFile, "r") as version_file:
            data = version_file.readlines()

        return data[0].strip()

    def deposit_file(self):
        """
        Configuration put on the SD card while there was one already : put aside by the
        service raspydarts-boot (see the installation), proposed at the start
        """
        return os.path.join(self.user_dir, 'raspydarts.cfg.depose')

    @staticmethod
    def file_value(section, value):
        """
        A value as read_file gives it
        """
        if len(value) == 0 or value == "''":
            return ''
        if value.startswith("'") and value.endswith("'"):
            return value[1:-1]
        if section == 'Events' or section.startswith('Colorset-'):
            return ast.literal_eval(value)
        if value in ('False', 'True'):
            return value == 'True'
        return value

    def deposit_changes(self):
        """
        The values of the deposited file different from the current ones : {section: {key: value}},
        None without file. An empty segment does not erase a calibration (file made without
        the target). Sections and keys unknown to the game are left aside
        """
        path = self.deposit_file()
        if not os.path.isfile(path):
            return None
        deposited = configparser.ConfigParser(inline_comment_prefixes="#", interpolation=None)
        deposited.optionxform = str
        try:
            deposited.read(path, encoding='utf-8-sig')
        except (configparser.Error, UnicodeDecodeError) as error:
            self.logs.error(f"Deposited configuration unreadable, removed : {error}")
            self.drop_deposit()
            return None

        changes = {}
        for section in deposited.sections():
            if section not in DefaultConfig and not section.startswith('game-'):
                self.logs.warning(f"Deposited configuration : section {section} unknown")
                continue
            if section not in self.config:
                self.read_file(section)
            current = self.config.get(section) or {}
            for key, raw in deposited.items(section):
                if not section.startswith('game-') and key not in DefaultConfig[section]:
                    self.logs.warning(f"Deposited configuration : {key} unknown in {section}")
                    continue
                try:
                    value = self.file_value(section, raw)
                except (ValueError, SyntaxError):
                    self.logs.warning(f"Deposited configuration : {section}/{key} unreadable")
                    continue
                if section == 'SectionKeys' and value == '':
                    continue
                if str(current.get(key, '')) != str(value):
                    changes.setdefault(section, {})[key] = value
        return changes

    def apply_deposit(self, changes):
        """
        The new values taken : the current configuration kept aside first (one file)
        """
        import shutil
        shutil.copy2(self.configFile, f"{self.configFile}.avant-depot")
        for section, values in changes.items():
            if section not in self.config or not self.config[section]:
                self.config[section] = self.init_section(section) if section in DefaultConfig else {}
            self.config[section].update(values)
        self.write_file()
        self.drop_deposit()
        self.logs.info(f"Deposited configuration taken : {', '.join(changes)}")

    def drop_deposit(self):
        """
        Deposited file removed
        """
        try:
            os.remove(self.deposit_file())
        except OSError:
            pass

    def check_config_file(self):
        """
        Check if the config file exists and if not, create it
        """
        self.file_exists = True
        # Create config folder in profile if necessary
        if not os.path.isfile(self.configFile):
            self.logs.warning(f"Creating folder {self.user_dir}")
            if not os.path.exists(self.user_dir):
                os.makedirs(self.user_dir)
            self.file_exists = False
            return False

        self.logs.debug(f"Config file {self.configFile} exists. We use it so...")
        return True

    def config_section(self, section, text=None):
        """
        conf for writing
        """

        self.conf += f"\n\n[{section}]\n"
        if text is not None:
            self.conf += f"### {text}\n"

        keys = self.config[section]
        for key in keys:
            self.conf += f"{key}:{keys[key]}\n"

    def config_colorset(self, name, colorset, default):
        self.conf += f"\n\n[{name}]\n"

        self.conf += f"# basic colors\n"
        for key, value in colorset.items():
            if key.startswith('color-'):
                if value != default[key]:
                    self.conf += f"{key}:{value}\n"
                else:
                    self.conf += f"#{key}:{value}\n"

        self.conf += f"\n# Backgrounds\n"
        for key, value in colorset.items():
            if key.startswith('bg-'):
                if value != default[key]:
                    self.conf += f"{key}:{value}\n"
                else:
                    self.conf += f"#{key}:{value}\n"

        self.conf += f"\n# For menus\n"
        for key, value in colorset.items():
            if key.startswith('menu-'):
                if value != default[key]:
                    self.conf += f"{key}:{value}\n"
                else:
                    self.conf += f"#{key}:{value}\n"

        self.conf += f"\n# For game's description\n"
        for key, value in colorset.items():
            if key.startswith('description-'):
                if value != default[key]:
                    self.conf += f"{key}:{value}\n"
                else:
                    self.conf += f"#{key}:{value}\n"

        self.conf += f"\n# For messages\n"
        for key, value in colorset.items():
            if key.startswith('message-'):
                if value != default[key]:
                    self.conf += f"{key}:{value}\n"
                else:
                    self.conf += f"#{key}:{value}\n"

        self.conf += f"\n# For game screen\n"
        for key, value in colorset.items():
            if key.startswith('game-'):
                if value != default[key]:
                    self.conf += f"{key}:{value}\n"
                else:
                    self.conf += f"#{key}:{value}\n"

        self.conf += f"\n# For target\n"
        for key, value in colorset.items():
            if key.startswith('target-'):
                if value != default[key]:
                    self.conf += f"{key}:{value}\n"
                else:
                    self.conf += f"#{key}:{value}\n"

        self.conf += f"\n# Players colors\n"
        for key, value in colorset.items():
            if key.startswith('player'):
                if value != default[key]:
                    self.conf += f"{key}:{value}\n"
                else:
                    self.conf += f"#{key}:{value}\n"

        self.conf += f"\n# Games specific colors\n"
        for key, value in colorset.items():
            if key.startswith('bob27'):
                if value != default[key]:
                    self.conf += f"{key}:{value}\n"
                else:
                    self.conf += f"#{key}:{value}\n"

    def write_file(self):
        """
        Create and fill config file
        """
        self.conf = "[SectionGlobals]\n"

        Global = self.config["SectionGlobals"]

        self.conf += "### Blink time of main information (ms) (good is 3000)\n"
        self.conf += f"blinktime:{Global['blinktime']}\n"
        #self.conf += "### Wait between player in ms - (Solo Option - put to 0 disable it, -1 to disable release darts message - default 2000)\n"
        #self.conf += f"solo:{Global['solo']}\n"
        self.conf += "### Pnj time\n"
        self.conf += f"pnj_time:{Global['pnj_time']}\n"
        self.conf += "### Max time of the next_player sound/music (max 10000)\n"
        self.conf += f"nextplayer_sound_duration:{Global['nextplayer_sound_duration']}\n"
        self.conf += "### Music at the start of each turn (False : none)\n"
        self.conf += f"nextplayer_music:{Global['nextplayer_music']}\n"
        self.conf += "### Time to release darts safely after a hit on player button (good is 1000-3000)\n"
        self.conf += f"releasedartstime:{Global['releasedartstime']}\n"
        self.conf += "### Screen resolution - if fullscreen is set to 1, resolution is bypassed\n"
        self.conf += f"resx:{Global['resx']}\n"
        self.conf += f"resy:{Global['resy']}\n"
        self.conf += f"fullscreen:{Global['fullscreen']}\n"
        self.conf += "### Screen resolution - if fullscreen is set to 1, resolution is bypassed\n"
        self.conf += f"nbcol:{Global['nbcol']}\n"
        self.conf += "### Default sound volume (percent)\n"
        self.conf += f"soundvolume:{Global['soundvolume']}\n"
        self.conf += "### Debug level:  0=Debug|1=Warnings|2=Errors|3=Fatal Errors (Default 2)|4=Informations|5=None\n"
        self.conf += f"debuglevel:{Global['debuglevel']}\n"
        self.conf += "### Localization (en_GB, fr_FR, de_DE, es_ES, ...)\n"
        self.conf += f"locale:{Global['locale']}\n"
        self.conf += "### Display clickable buttons at the bottom of the screen (for touchscreen)\n"
        self.conf += f"onscreenbuttons:{Global['onscreenbuttons']}\n"
        self.conf += "### Handicap option\n"
        self.conf += f"startpercent:{Global['startpercent']}\n"
        self.conf += "### Print stats of the game after winner\n"
        self.conf += f"endgamestats:{Global['endgamestats']}\n"
        self.conf += "### Keep players order when restart (instead of sort on score\n"
        self.conf += f"keeporder:{Global['keeporder']}\n"
        self.conf += "### Videos to play:  None / Specials moves / all\n"
        self.conf += f"videos:{Global['videos']}\n"
        self.conf += "### Colorset\n"
        self.conf += f"colorset:{Global['colorset']}\n"
        self.conf += "### Name of online game creator\n"
        self.conf += f"netgamecreator:{Global['netgamecreator']}\n"
        self.conf += "### Font\n"
        self.conf += f"font:{Global['font']}\n"
        self.conf += "### Play firstname\n"
        self.conf += f"play_firstname:{Global['play_firstname']}\n"
        self.conf += "### Print touched target, depend on game\n"
        self.conf += f"print_dartstroke:{Global['print_dartstroke']}\n"
        self.conf += "### Light target (for white targets)\n"
        self.conf += f"light_target:{Global['light_target']}\n"
        self.conf += "### Light strip according to players's color\n"
        self.conf += f"light_strip:{Global['light_strip']}\n"
        self.conf += "### Strip and target lit out of games, without the animations of the events\n"
        self.conf += f"idle_light:{Global['idle_light']}\n"
        self.conf += "### Colour of the strip out of games (off : off)\n"
        self.conf += f"idle_strip_color:{Global['idle_strip_color']}\n"
        self.conf += "### Colour of the target out of games (off : off, origin : colours of the segments)\n"
        self.conf += f"idle_target_color:{Global['idle_target_color']}\n"
        self.conf += "### Wait event delay (in seconds)\n"
        self.conf += f"waitevent_time:{Global['waitevent_time']}\n"
        self.conf += "### Exhibition mode\n"
        self.conf += f"exhibition_mode:{Global['exhibition_mode']}\n"
        self.conf += "### Buttons of the main menu shown in exhibition mode\n"
        self.conf += f"exhibition_items:{Global.get('exhibition_items', DefaultConfig['SectionGlobals']['exhibition_items'])}\n"
        self.conf += "### Competition mode\n"
        self.conf += f"competition_mode:{Global['competition_mode']}\n"
        self.conf += "### To adjust the volume of videos\n"
        self.conf += f"videosound_multiplier:{Global['videosound_multiplier']}\n"
        self.conf += "### To adjust the volume of sounds (10 - 100)\n"
        self.conf += f"sound_multiplier:{Global['sound_multiplier']}\n" 
        self.conf += "### light strip according to illumination mode\n" 
        self.conf += f"illumination_mode:{Global['illumination_mode']}\n" 
        self.conf += "### light strip illumination color\n" 
        self.conf += f"illumination_color:{Global['illumination_color']}\n\n" 
        self.conf += "### Fast games mode\n"
        self.conf += f"fast_games_mode:{Global['fast_games_mode']}\n"
        self.conf += "### Only favorites games mode\n"
        self.conf += f"only_favorites_games_mode:{Global['only_favorites_games_mode']}\n"
        self.conf += "### Check for update available\n"
        self.conf += f"check_for_updates:{Global['check_for_updates']}\n"
        self.conf += "### Output of the sound : auto (USB sound card when plugged, else HDMI), hdmi, jack, usb\n"
        self.conf += f"sound_output:{Global.get('sound_output', 'auto')}\n"

        Advanced = self.config["SectionAdvanced"]

        self.conf += "\n[SectionAdvanced]\n"
        self.conf += "### If you do not want the stats to be updated, please use this option:\n"
        self.conf += f"bypass-stats:{Advanced['bypass-stats']}\n"
        self.conf += "### Frequency in second for the client to poll the server for players names\n"
        self.conf += f"clientpolltime:{Advanced['clientpolltime']}\n"
        self.conf += "### Stats format ('old','csv', or coming soon:  'sqlite'\n"
        self.conf += f"stats-format:{Advanced['stats-format']}\n"
        self.conf += "### Clear score DB (for Sqlite fomat)\n"
        self.conf += f"clear-local-db:{Advanced['clear-local-db']}\n"
        self.conf += "### Bank of players\n"
        self.conf += f"localplayers:{Advanced['localplayers']}\n"
        self.conf += "### Use DMD\n"
        self.conf += f"use-dmd:{Advanced['use-dmd']}\n"
        self.conf += "### Use MatrixLeds\n"
        self.conf += f"use-matrix:{Advanced['use-matrix']}\n"
        self.conf += "### Use Other (Typically for home automation\n"
        self.conf += f"use-other:{Advanced['use-other']}\n"
        self.conf += "### Use Philips Hue controler\n"
        self.conf += f"use-hue:{Advanced['use-hue']}\n"
        self.conf += "### Alternative mqtt broker\n"
        self.conf += f"mqtt-broker:{Advanced['mqtt-broker']}\n"
        self.conf += "### separated interior and exterioir simples\n"
        self.conf += f"interior:{Advanced['interior']}\n"
        self.conf += "### Target's leds specifics\n"
        self.conf += "### Color1 : Simple 20, ...\n"
        self.conf += "### Color2 : Double 1, double 5\n"
        self.conf += "### Color3 : Simple 1, simple 5...\n"
        self.conf += f"target-bgcolor1:{Advanced['target-bgcolor1']}\n"
        self.conf += f"target-bgcolor2:{Advanced['target-bgcolor2']}\n"
        self.conf += f"target-bgcolor3:{Advanced['target-bgcolor3']}\n"
        self.conf += f"target-bgbrightness:{Advanced['target-bgbrightness']}\n"
        self.conf += "### Direct play : both prefered_game and firstnames must be filled\n"
        self.conf += f"directplay:{Advanced['directplay']}\n"
        self.conf += f"prefered_game:{Advanced['prefered_game']}\n"
        self.conf += "### Prefered Games\n"
        self.conf += f"preferedclassicgame:{Advanced['preferedclassicgame']}\n"
        self.conf += f"preferedfungame:{Advanced['preferedfungame']}\n"
        self.conf += f"preferedsportgame:{Advanced['preferedsportgame']}\n"
        self.conf += f"preferedcategory:{Advanced['preferedcategory']}\n"
        self.conf += "### Sets default number\n"
        self.conf += f"nb_sets:{Advanced['nb_sets']}\n"
        self.conf += "### Delay to light Celebration in case of DB\n"
        self.conf += f"db-celebration-delay:{Advanced['db-celebration-delay']}\n"
        self.conf += "### Delay to light Celebration when set is won \n"
        self.conf += f"set-celebration-delay:{Advanced['set-celebration-delay']}\n"
        self.conf += "### Delay to light Celebration in case of victory\n"
        self.conf += f"victory-celebration-delay:{Advanced['victory-celebration-delay']}\n"
        self.conf += "### Light or not celebration when game is launched\n"
        self.conf += f"launch-game-celebration:{Advanced['launch-game-celebration']}\n"
        self.conf += "### List of games for which options are saved\n"
        self.conf += f"game-options-list:{Advanced['game-options-list']}\n"
        self.conf += "### For Richard's case\n"
        self.conf += f"richard-mode:{Advanced['richard-mode']}\n\n"

        Server = self.config["Server"]

        self.conf += "\n\n[Server]\n"
        self.conf += "### Clear Server (Game Server or Master Server) Database at startup:\n"
        self.conf += f"clear-db:{Server['clear-db']}\n"
        self.conf += "### Enable or not notifications (Master Server):\n"
        self.conf += f"notifications:{Server['notifications']}\n"
        self.conf += "### SMTP server that will send notifications (Master Server):\n"
        self.conf += f"notifications-smtp-server:{Server['notifications-smtp-server']}\n"
        self.conf += "### The email address used as the sender address (Master Server):\n"
        self.conf += f"notifications-sender:{Server['notifications-sender']}\n"
        self.conf += "### The email address used as the reply-to address (Master Server):\n"
        self.conf += f"notifications-reply:{Server['notifications-reply']}\n"
        self.conf += "### Username used to authenticate on smtp server (Master Server):\n"
        self.conf += f"notifications-username:{Server['notifications-username']}\n"
        self.conf += "### Password used to authenticate on smtp server (Master Server):\n"
        self.conf += f"notifications-password:{Server['notifications-password']}\n"
        self.conf += "### Use the Master server in Test mode (0 or 1) - (Create fake games):\n"
        self.conf += f"mastertest:{Server['mastertest']}\n"
        self.conf += "### Close all open games in MasterServer (0 or 1):\n"
        self.conf += f"masterclosegames:{Server['masterclosegames']}\n"

        self.config_section("Camera", "Camera USB settings")

        if 'Gallery' not in self.config:
            self.config['Gallery'] = self.init_section('Gallery')
        self.config_section("Gallery", "Gallery of the memories : hash of its password")

        self.config_section("Favorites", "High level customization")
        self.config_section("Raspberry_BoardPinsIns", "Input GPIO section")
        self.config_section("Raspberry_BoardPinsOuts", "Output GPIO section")
        self.config_section("Raspberry_Leds", "Basic setup of leds")
        self.config_section("LEDTarget", "For beautiful illuminations of your target")
        self.config_section("SectionKeys", "Target settings")
        self.config_section("Raspberry", "In case of MCP23017 extend card")
        self.config_section("Events", "Launch Led or DMD animation on event")

        game_list = [section for section in self.config if section.startswith('game-')]

        for game in game_list:
            self.config_section(game, f"{game.replace('game-', '')}'s options")

        self.logs.debug(f"Writing config file: {self.configFile}")
        try:
            file = open(self.configFile, 'w')
            file.write(self.conf)
            file.close()
        except:
            self.logs.fatal(f"Unable to write config file {self.configFile}. Please check permissions. Exiting.")
            exit(1)

    def init_section(self, section):
        """
        Init section options
        """
        options = {}
        for o in DefaultConfig[section]:
            options[o] = DefaultConfig[section][o]
        return options

    def set_config(self, section, values):
        """
        Set Leds Config
        """
        for o in self.config[section]:
            try:
                self.config[section][o] = values[o]
            except:
                self.logs.warning(f"No config for {o}")

    def set_game_config(self, game, values):
        """
        Set Leds Config
        """
        game_name = game.replace(' ', '_')
        if game_name not in self.config['SectionAdvanced']['game-options-list']:
            if self.config['SectionAdvanced']['game-options-list'] != '':
                games_list = self.config['SectionAdvanced']['game-options-list'].split(',')
                games_list.append(game_name)
            else:
                games_list = [game_name]
            self.config['SectionAdvanced']['game-options-list'] = ','.join(games_list)

        section = f"game-{game.replace(' ', '_')}"
        if section not in self.config:
            self.config[section] = {}
        for o in values:
            try:
                self.config[section][o] = values[o]
            except:
                self.logs.warning(f"No config for {o}")
    
    def set_clk_card_config(self):
        """
        Set Julien's card config
        """
        self.set_config('Raspberry_BoardPinsIns', ClkCardConfig['INPUT'])
        self.set_config('Raspberry_BoardPinsOuts', ClkCardConfig['OUTPUT'])
        self.set_config('SectionKeys', ClkCardConfig['KEYS'])
        self.set_config('Raspberry', ClkCardConfig['EXTENDED'])

    def set_jt_card_config(self):
        """
        Set Julien's card config
        """
        self.set_config('Raspberry_BoardPinsIns', JtCardConfig['INPUT'])
        self.set_config('Raspberry_BoardPinsOuts', JtCardConfig['OUTPUT'])
        self.set_config('SectionKeys', JtCardConfig['KEYS'])
        self.set_config('Raspberry', JtCardConfig['EXTENDED'])

    def set_jt2_card_config(self):
        """
        Set Julien's card config
        """
        self.set_config('Raspberry_BoardPinsIns', Jt2CardConfig['INPUT'])
        self.set_config('Raspberry_BoardPinsOuts', Jt2CardConfig['OUTPUT'])
        self.set_config('SectionKeys', Jt2CardConfig['KEYS'])
        self.set_config('Raspberry', Jt2CardConfig['EXTENDED'])

    def set_ji_card_config(self):
        """
        Set Jimmy or Remi's card config
        """
        self.set_config('Raspberry_BoardPinsIns', JiCardConfig['INPUT'])
        self.set_config('Raspberry_BoardPinsOuts', JiCardConfig['OUTPUT'])
        self.set_config('SectionKeys', JiCardConfig['KEYS'])
        self.set_config('Raspberry', JiCardConfig['EXTENDED'])

    def set_ji2_card_config(self):
        """
        Set Jimmy or Remi's card config
        """
        self.set_config('Raspberry_BoardPinsIns', Ji2CardConfig['INPUT'])
        self.set_config('Raspberry_BoardPinsOuts', Ji2CardConfig['OUTPUT'])
        self.set_config('SectionKeys', Ji2CardConfig['KEYS'])
        self.set_config('Raspberry', Ji2CardConfig['EXTENDED'])

    def set_jiz_card_config(self):
        """
        Set Jimmy or Remi's card config
        """
        self.set_config('Raspberry_BoardPinsIns', JizCardConfig['INPUT'])
        self.set_config('Raspberry_BoardPinsOuts', JizCardConfig['OUTPUT'])
        self.set_config('SectionKeys', JizCardConfig['KEYS'])
        self.set_config('Raspberry', JizCardConfig['EXTENDED'])

    def set_gb_card_config(self):
        """
        Set Jimmy or Remi's card config
        """
        self.set_config('Raspberry_BoardPinsIns', GBCardConfig['INPUT'])
        self.set_config('Raspberry_BoardPinsOuts', GBCardConfig['OUTPUT'])
        self.set_config('SectionKeys', GBCardConfig['KEYS'])
        self.set_config('Raspberry', GBCardConfig['EXTENDED'])
        self.config['SectionAdvanced']['interior'] = True

    def set_ed900_card_config(self):
        """
        Set Jimmy or Remi's card config
        """
        self.set_config('Raspberry_BoardPinsIns', ED900Config['INPUT'])
        self.set_config('Raspberry_BoardPinsOuts', ED900Config['OUTPUT'])
        self.set_config('SectionKeys', ED900Config['KEYS'])
        self.set_config('Raspberry', ED900Config['EXTENDED'])
        self.config['SectionAdvanced']['interior'] = True

    def set_jo_416_card_config(self):
        """
        Set Joffrey pour matrice 4*16
        """
        self.set_config('Raspberry_BoardPinsIns', Jo416CardConfig['INPUT'])
        self.set_config('Raspberry_BoardPinsOuts', Jo416CardConfig['OUTPUT'])
        self.set_config('SectionKeys', Jo416CardConfig['KEYS'])
        self.set_config('Raspberry', Jo416CardConfig['EXTENDED'])

    def set_jo_card_config(self):
        """
        Set Joffrey or Remi's card config
        """
        self.set_config('Raspberry_BoardPinsIns', JoCardConfig['INPUT'])
        self.set_config('Raspberry_BoardPinsOuts', JoCardConfig['OUTPUT'])
        self.set_config('SectionKeys', JoCardConfig['KEYS'])
        self.set_config('Raspberry', JoCardConfig['EXTENDED'])

    def set_ji_leds_config(self):
        """
        Set Jimmy's leds config
        """
        self.set_config('LEDTarget', JiLedsConfig)
        
    def set_mmworks_vdartscard_config(self):
        """
        Set MMWorkshop VDarts card config
        """
        self.set_config('Raspberry_BoardPinsIns', MMWorksVDartsCardConfig['INPUT'])
        self.set_config('Raspberry_BoardPinsOuts', MMWorksVDartsCardConfig['OUTPUT'])
        self.set_config('SectionKeys', MMWorksVDartsCardConfig['KEYS'])
        self.set_config('Raspberry', MMWorksVDartsCardConfig['EXTENDED'])

    def set_mmworks_leds_config(self):
        """
        Set MMWorkshop's leds config
        """
        self.set_config('LEDTarget', MMWorkshopVdartsLedsConfig)
        

    def read_colorset(self, colorset_file):
        """
        Read specific colorset file
        """
        section = 'Colorset'
        Config = configparser.ConfigParser(inline_comment_prefixes="#")
        Config.optionxform = str
        self.logs.debug(f"Working on Colorset's section of {colorset_file}")
        try:
             Config.read(colorset_file)
        except:
            self.logs.error("No {colorset_file} file")
            return None

        try:
            #options = self.init_section(section)
            options = {}
        except:
            self.logs.warning(f"No {section} section in {colorset_file}")
            return None

        try:
            file_options = Config.options(section)
        except Exception as e:
            self.logs.debug(f"Don't forget that you may create section named {section} in {colorset_file}")
            return None

        for option in file_options:
            try:
                value = Config.get(section, option)
                options[option] = ast.literal_eval(value)
            except Exception as e:
                self.logs.error(f"Configuration issue with this option : {option}")
                self.logs.debug(f"Error was:  {e}".format(e))
                self.logs.debug(f"Use default:  {DefaultConfig[section][option]}")
                options[option] = DefaultConfig[section][option]

        # Store in local object
        self.config['Colorset']['Colorset'] = options
        return options

    def read_file(self, section, none=None):
        """
        Read a section of the config file
        """
        Config = configparser.ConfigParser(inline_comment_prefixes="#")

        # If somedays you like to preserve case in options, just uncomment the following
        Config.optionxform = str
        self.logs.debug(f"Working on section {section} of your config file.")
        try:
            Config.read(self.configFile)
        except:
            self.logs.fatal(f"Your config file {self.configFile} contains errors. Correct them or rename this file (it will be regenerated).")
            exit (1)

        # Init with defaults values
        try:
            options = self.init_section(section)
        except:
            self.logs.warning(f"No default {section} section. Use config only")
            options = {}

        try:
            file_options = Config.options(section)  # Try to loads options from config file
        except Exception as e:
            if section in DefaultConfig:       # Warn only if the requested section is part of the config
                self.logs.warning(f"Your config file does not contain a section named {section}.")
                self.logs.warning("Will use default section values")
                file_options = DefaultConfig[section]
            else:
                self.logs.debug(f"Don't forget that you may create section named {section} to customize pyDarts")
                self.config[section] = {} # Create empty config values even if the section does not exists
                if none != None:
                    return ''
                else:
                    return False

        for option in file_options:
            if not section.startswith('game-') and not option in DefaultConfig[section]:
                self.logs.warning(f"Unexpected {option} in {section}")
            else:
                try:
                    value = Config.get(section, option)
                    if option == 'font' and value == 'Casino.ttf':
                        options[option] = 'MaPolice.ttf'
                    elif len(value) == 0 or value == "''":
                        options[option] = ''
                    elif value.startswith("'") and value.endswith("'"):
                        options[option] = value[:-1][1::]
                    elif section == 'Events' or section.startswith('Colorset-'):
                        options[option] = ast.literal_eval(value)
                    elif value == 'False':
                        options[option] = False
                    elif value == 'True':
                        options[option] = True
                    else:
                        options[option] = value
                except Exception as e:
                    self.logs.error(f"Configuration issue with this option : {option}")
                    self.logs.debug(f"Error was:  {e}".format(e))
                    self.logs.debug(f"Use default:  {DefaultConfig[section][option]}")
                    options[option] = DefaultConfig[section][option]

        if section == 'Raspberry':
            """
            Special case:  use V2 config file in V3+
            """
            config_v2 = True
            for option in options:
                if options[option] != '0':
                    config_v2 = False

            if config_v2:
                for option in options:
                    options[option] = AlternateConfig[section][option]

        if section == 'Favorites':
            # The former server of the network games answers no more : left out of the favorite
            # servers, the one of the online games instead if it was the only one
            servers = [server.strip() for server in str(options.get('servers') or '').split(',') if server.strip()]
            kept = [server for server in servers if server.split(':')[0] not in (OLD_SERVER, '51.210.43.252')]
            if kept != servers:
                options['servers'] = ','.join(kept or [DefaultConfig['Favorites']['servers']])
                self.logs.info(f"Favorite servers : {OLD_SERVER} removed ({options['servers']})")

        # Store in local object
        self.config[section] = options

        self.logs.debug(f"Config[{section}]={self.config[section]}")

        # Return options
        return options

    def set_value(self, section, item, value):
        """
        Set value, specific for booleans
        """
        if value == 'True':
            value = True
        elif value == 'False':
            value = False
        self.config[section][item] = value


    def get_value(self, section, key, required=True, default_value=False, split=None):
        """
        Return value for an option (first search CLI args, then config file, then search default value)
        Break if option is required, return false otherwise
        """
        if key is None or section is None:
            return False

        if section == 'SectionGlobals' and key == 'colorset' and key in self.config[section]:
            return self.theme_name(self.config[section][key])

        if key in self.config[section]:
            if self.config[section][key] in ('True', 'False'):
                # A text True / False : bool('False') was True (an option said off was on)
                return self.config[section][key] == 'True'
            else:
                if self.config[section][key] is False and default_value is not None and default_value != 'None':
                    return default_value
                if self.config[section][key] is False and default_value == 'None':
                    return None
                if split is not None:
                    return self.config[section][key].split(split)
                else:
                    return self.config[section][key]

        if required:
            self.logs.fatal(f"Error getting required config value {key}. No command line, no config found, no default. Abort")
            sys.exit(1)

        return default_value

    # Themes renamed : remi is now sombre. A configuration naming one of them uses the folder
    # which exists (an installation of before keeps its theme, a new one finds sombre)
    RENAMED_THEMES = {'remi': 'sombre', 'sombre': 'remi'}

    def theme_name(self, name):
        '''
        Name of the theme to use for this value of colorset
        '''
        other = self.RENAMED_THEMES.get(str(name))
        themes = os.path.join(str(getattr(self, 'user_dir', '') or ''), 'themes')
        if other and not os.path.isdir(os.path.join(themes, str(name))) and os.path.isdir(os.path.join(themes, other)):
            return other
        return name

    def get_players_names(self):
        """
        Specific config (comma separated values)
        """
        players_names = self.get_value('Favorites', 'firstnames')
        if players_names:
            return players_names.split(',')
        return False

    def get_players_color(self):
        """
        Specific config (comma separated values)
        """
        players_color = self.get_value('Favorites', 'players_color')
        if players_color:
            try:
                return ast.literal_eval(players_color)
            except (ValueError, SyntaxError):
                return {}
        return {}
    
    def get_colorset(self, personnal_dir, colorset):
        '''
        Init and get the ColorSet
        '''
        try:         
            colorset = self.read_colorset(f"{personnal_dir}/themes/{colorset}/other/Colorset.cfg")
        except:
            try:
                colorset = self.read_colorset(f"{personnal_dir}/themes/{colorset}/Colorset.cfg")
            except:
                try:                
                    colorset = self.read_colorset(f"{personnal_dir}/themes/clear/other/Colorset.cfg")
                except:
                    try:                
                        colorset = self.read_colorset(f"{personnal_dir}/themes/clear/Colorset.cfg")                
                    except Exception as e:
                        self.logs.warning("Error during load of custom colorset")
                        self.logs.warning(f"Error was {e}")
        return colorset
    
    def set_value_colorset(self, colorset_path, list_of_key_and_value):
        '''
        Write in the ColorSet
        '''
        try:
            path = colorset_path + "/other/Colorset.cfg"
            all_line_in_colorset_file = []

            self.logs.debug(f"Reading colorset file: {path}")
            
            with open(path, 'r') as colorset:
                colorset_lines = colorset.read()
            colorset.close()
                
            for line in colorset_lines.split("\n"):
                if (any(line.split(':')[0] in value for value in list_of_key_and_value)):
                    all_line_in_colorset_file.append((f"{line.split(':')[0]}:{dict(list_of_key_and_value)[line.split(':')[0]]}"))
                else:
                    all_line_in_colorset_file.append(line)
                    
            colorset_lines = "\n".join(all_line_in_colorset_file)
                
            self.logs.debug(f"Writing colorset file: {path}")
            
            try:
                with open(path, 'w', encoding = "utf-8") as colorset:
                    colorset.write(colorset_lines)
                colorset.close()
            except:
                self.logs.fatal(f"Unable to write colorset file {path} with cconfig.set_value_colorset(). Please check permissions. Exiting.")
                exit(1)
                
        except Exception as ex:
            self.logs.error(f"Error in cconfig set_value_colorset() : {ex}")
    
    def get_values_segment_colors(self, all_colorset_values):
        '''
        Get values only for segments colors
        '''
        try:
            # 2 - list2 TLS - 20,18,13,10,2,3,7,8,14,12
            # 1 - list1 TLS - 1,4,6,15,17,19,16,11,9,5
            # format r,g,b sans parenthese pour convenir a 'TargetLeds_Server'
            return [str(all_colorset_values['target-simple1']).replace('(','').replace(')','').replace(' ',''),
                    str(all_colorset_values['target-simple2']).replace('(','').replace(')','').replace(' ',''),
                    str(all_colorset_values['target-double1']).replace('(','').replace(')','').replace(' ',''),
                    str(all_colorset_values['target-double2']).replace('(','').replace(')','').replace(' ',''),
                    str(all_colorset_values['target-triple1']).replace('(','').replace(')','').replace(' ',''),
                    str(all_colorset_values['target-triple2']).replace('(','').replace(')','').replace(' ',''),
                    str(all_colorset_values['target-sb']).replace('(','').replace(')','').replace(' ',''),
                    str(all_colorset_values['target-db']).replace('(','').replace(')','').replace(' ','')]
        except Exception as ex:
            self.logs.error(f"Error in cconfig get_values_segment_colors() : {ex}")
