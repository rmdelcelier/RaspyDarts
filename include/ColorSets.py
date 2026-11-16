    #Color Sets - Add your own !
ColorSet = {}

ColorSet['clear'] = {

    # General
    'border-radius': 10,
    'button-radius': 'max',
    'border-size': 3,
    'padding': 2,

    'color-black': (0, 0, 0), # Black RVB color

    # Backgrounds
    'bg-global': False, # True => No background's image
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
    'menu-inactive': (128, 128, 128),
    
    # Game's deczription
    'description-bg': (213, 206, 186),
    'description-text': (0, 0, 0),
    'description-game': (0, 0, 0),

    # For game screen
    'game-bg': (0, 0, 0),
    'game-score': (255, 255, 255),
    'game-headers': (255, 255, 255),
    'game-player': (119, 119, 118),
    'game-player-name': (255, 255, 255),
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
    'game-grey': (213, 206, 186),
    'game-grey2': (74, 74, 74),
    'game-purple':(140, 108, 161),
    'game-red': (255, 0, 0),
    'game-green': (0, 255, 0),
    'game-blue': (0, 0, 255),
    'game-gold': (255, 215, 0),
    'game-silver': (192, 192, 192),
    'game-bronze': (205, 127, 50),

    # Other
    'message-bg': (255, 255, 255),
    'message-text': (0, 0, 0),

    # Target
    'target-sb': (189, 108, 109),
    'target-db': (107, 134, 176),
    'target-double1': (255, 255, 255),
    'target-double2': (255, 0, 0),
    'target-triple1': (255, 255, 255),
    'target-triple2': (255, 0, 0),
    'target-simple1': (0, 0, 255),
    'target-simple2': (255, 255, 255),

    # Bob's 27 colors
    'bob27-bg': (45,78,99),
    'bob27-blue': (46, 64, 76),
    'bob27-green': (45, 108, 85),
    'bob27-red': (124, 84, 87),
    'bob27-hit': (57, 209, 129),
    'bob27-miss': (232, 21, 37),
    'bob27-text': (255, 255, 255),

    # Fighter's colors
    'fighters-medic': (0, 240, 0),
    'fighters-actual-player': (255, 255, 255),
    'fighters-alive-player': (150, 0, 0),
    'fighters-dead-player': (255, 255, 255),
    'fighters-targets': (255, 255, 255),
    'fighters-scores': (255, 255, 255),
    'fighters-round': (255, 255, 255),
    'fighters-darts': (255, 255, 255),
    
    # Color used for suggestion for all players 
    # -> for target leds, this color will be used for all players if not None else player color)
    'suggestion-color-allplayer': None, 

    # Show shortcuts or use a character for Main Menu (and Sub Menu)
    # None : for no shortcut
    # '' : if you want to use 'F1,F2,etc' shortcut
    # '>' : example for '> Partie simple' shortcut
    'main-sub-menu-shortcuts': '',
    # 'Left', 'Center', 'Right'
    'main-sub-menu-text-align': 'Left',
    # Margin of the text in its box (pixels) ; its place in height : 'Top', 'Center', 'Bottom'
    'main-sub-menu-text-margin': 0,
    'main-sub-menu-text-valign': 'Center',

    # Show shortcuts or use a character for Parametrage Menu
    # same options as main-sub-shortcuts
    'parametrage-menu-shortcuts': '',
    # 'Left', 'Center', 'Right'
    'parametrage-menu-text-align': 'Left',
    # Margin of the text in its box (pixels) ; its place in height : 'Top', 'Center', 'Bottom'
    'parametrage-menu-text-margin': 0,
    'parametrage-menu-text-valign': 'Center',

    # Show shortcuts or use a character for Players Menu
    # same options as main-sub-shortcuts
    'players-menu-shortcuts': '',
    # 'Left', 'Center', 'Right'
    'players-menu-text-align': 'Left',
    # Margin of the text in its box (pixels) ; its place in height : 'Top', 'Center', 'Bottom'
    'players-menu-text-margin': 0,
    'players-menu-text-valign': 'Center',

    # Show shortcuts or use a character for Game Options Menu
    # same options as main-sub-shortcuts
    'game-options-menu-shortcuts': '',
    # 'Left', 'Center', 'Right'
    'game-options-menu-text-align': 'Left'
}

