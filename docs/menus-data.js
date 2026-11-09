// Genere par docs/generer_menus.py : ne pas modifier a la main
const MENUS_DATA = {
 "defaults": {
  "version": 1,
  "resolution": "auto",
  "defaults": {
   "style": "classic",
   "layout": "list"
  },
  "styles": {
   "classic": {
    "background": {
     "color": "menu-buttons*1.5"
    },
    "text": {
     "size": "auto",
     "color": "menu-text-black",
     "align": "theme"
    }
   },
   "classic-tiles": {
    "background": {
     "color": "menu-inactive",
     "opacity": 0.08
    },
    "radius": 0.17,
    "icon": {
     "size": 1.0
    },
    "text": {
     "size": "auto",
     "color": "menu-text-black",
     "align": "theme"
    },
    "selected": {
     "background": {
      "color": "menu-selected",
      "opacity": 1.0
     }
    }
   }
  },
  "navigation": {
   "up": [
    "up",
    "btn:up",
    "dart:S20"
   ],
   "down": [
    "down",
    "btn:down",
    "dart:S3"
   ],
   "left": [
    "left",
    "btn:left",
    "dart:S11"
   ],
   "right": [
    "right",
    "btn:right",
    "dart:S6"
   ],
   "next": [],
   "previous": [],
   "validate": [
    "enter",
    "btn:game",
    "btn:validate",
    "btn:nextplayer",
    "dart:SB",
    "dart:DB"
   ],
   "back": [
    "escape",
    "btn:back",
    "btn:cancel"
   ]
  },
  "menus": {
   "main": {
    "title": "game-type-menu",
    "show_version": true,
    "buttons": [
     {
      "id": "local",
      "action": "local_game",
      "text": "game-type-local",
      "shortcut": "F1",
      "exhibition": true
     },
     {
      "id": "network",
      "action": "network",
      "text": "online-title",
      "shortcut": "F2"
     },
     {
      "id": "miscellaneous",
      "action": "menu:miscellaneous",
      "text": "miscellaneous",
      "shortcut": "F4"
     },
     {
      "id": "trophees",
      "action": "trophies",
      "text": "trophees",
      "shortcut": "F5",
      "exhibition": true
     },
     {
      "id": "gallery",
      "action": "gallery",
      "text": "gallery",
      "shortcut": "F6",
      "exhibition": true
     },
     {
      "id": "mp3",
      "action": "mp3",
      "text": "music-player",
      "exhibition": true
     },
     {
      "id": "infos",
      "action": "infos",
      "shortcut": "F9",
      "visible": false
     },
     {
      "id": "restart",
      "action": "restart",
      "shortcut": "F11",
      "visible": false
     },
     {
      "id": "quit",
      "action": "desktop",
      "text": "back-to-desktop",
      "shortcut": "F12",
      "space_before": 1.5
     },
     {
      "id": "shutdown",
      "action": "shutdown",
      "text": "exit",
      "shortcut": "escape",
      "space_before": 0.5,
      "confirm": "realy-stop"
     }
    ]
   },
   "miscellaneous": {
    "title": "parameters",
    "info": [
     "ips",
     "rpi_version",
     "version"
    ],
    "remember": true,
    "buttons": [
     {
      "id": "firstnames",
      "action": "favorite_players",
      "text": "favorites-players",
      "shortcut": "F1"
     },
     {
      "id": "games",
      "action": "favorite_games",
      "text": "favorites-games",
      "shortcut": "F2"
     },
     {
      "id": "servers",
      "action": "favorite_servers",
      "text": "favorites-servers",
      "shortcut": "F3"
     },
     {
      "id": "customization",
      "action": "customization",
      "text": "customization",
      "shortcut": "F4"
     },
     {
      "id": "animations",
      "action": "animations",
      "text": "animations",
      "shortcut": "F5"
     },
     {
      "id": "firstname-bank",
      "action": "players_bank",
      "text": "players-bank",
      "shortcut": "F6"
     },
     {
      "id": "setup",
      "action": "menu:settings",
      "text": "setup",
      "shortcut": "F7"
     },
     {
      "id": "backups",
      "action": "backups",
      "text": "backups",
      "shortcut": "F8"
     },
     {
      "id": "exhibition",
      "action": "exhibition",
      "text": "exhibition",
      "shortcut": "F9"
     },
     {
      "id": "raspy2dmd",
      "action": "raspy2dmd",
      "text": "raspy2dmd",
      "shortcut": "F10"
     },
     {
      "id": "edit-screens",
      "action": "edit_screens",
      "text": "edit-screens",
      "shortcut": "F11"
     },
     {
      "id": "back",
      "action": "back",
      "text": "back",
      "shortcut": "escape",
      "footer": "left"
     },
     {
      "id": "update",
      "action": "update",
      "text": "btn_update",
      "footer": "right"
     }
    ]
   },
   "settings": {
    "title": "setup",
    "remember": true,
    "layout": "tiles",
    "columns": 4,
    "buttons": [
     {
      "id": "setup-buttons",
      "action": "setup_buttons",
      "text": "setup-buttons",
      "shortcut": "F1"
     },
     {
      "id": "setup-pinleds",
      "action": "setup_pins_leds",
      "text": "setup-pinsleds",
      "shortcut": "F2"
     },
     {
      "id": "setup-leds",
      "action": "setup_leds",
      "text": "setup-leds",
      "shortcut": "F3"
     },
     {
      "id": "setup-couleurs-segments",
      "action": "setup_segment_colors",
      "text": "setup-couleurs-segments",
      "shortcut": "F4"
     },
     {
      "id": "setup-cam",
      "action": "setup_camera",
      "text": "setup-cam",
      "shortcut": "F5"
     },
     {
      "id": "usb-pads",
      "action": "usb_pads",
      "text": "usb-pads",
      "shortcut": "F6"
     },
     {
      "id": "coins",
      "action": "coins",
      "text": "coins",
      "shortcut": "F7"
     },
     {
      "id": "button-leds",
      "action": "button_leds",
      "text": "button-leds",
      "shortcut": "F8"
     },
     {
      "id": "test-buttons",
      "action": "test_buttons",
      "text": "test-buttons",
      "shortcut": "F9"
     },
     {
      "id": "test-target",
      "action": "test_target",
      "text": "test-target",
      "shortcut": "F10"
     },
     {
      "id": "test-toys",
      "action": "test_toys",
      "text": "test-toys",
      "shortcut": "F11"
     },
     {
      "id": "reset",
      "action": "reset",
      "text": "reset",
      "shortcut": "F12"
     },
     {
      "id": "back",
      "action": "back",
      "text": "back",
      "shortcut": "escape",
      "footer": "left"
     }
    ]
   },
   "categories": {
    "title": "game-cat",
    "layout": "tiles",
    "buttons": [
     {
      "id": "classic",
      "action": "category:classic",
      "logo": "menu_classic",
      "shortcut": "F1",
      "dmd": "dmd-game-classic"
     },
     {
      "id": "fun",
      "action": "category:fun",
      "logo": "menu_fun",
      "shortcut": "F2",
      "dmd": "dmd-game-fun"
     },
     {
      "id": "sport",
      "action": "category:sport",
      "logo": "menu_sport",
      "shortcut": "F3",
      "dmd": "dmd-game-sport"
     },
     {
      "id": "favorites",
      "action": "category:favorites",
      "logo": "menu_favoris",
      "shortcut": "F4",
      "dmd": "dmd-game-favorites",
      "requires": "favorite_games"
     },
     {
      "id": "back",
      "action": "back",
      "text": "back",
      "shortcut": "escape",
      "footer": "left"
     }
    ]
   },
   "favorite_game": {},
   "question": {},
   "music_source": {
    "title": "music-source"
   },
   "favorite_save": {
    "title": "favorite-save",
    "subtitle": "favorite-save-sub"
   },
   "favorite_players": {
    "title": "favorite-players",
    "subtitle": "favorite-players-sub"
   },
   "editor_games": {
    "layout": "grid",
    "columns": 4
   },
   "online_lobby": {
    "buttons": [
     {
      "id": "ready",
      "text": "online-ready",
      "shortcut": "F1"
     },
     {
      "id": "chat",
      "text": "online-chat",
      "shortcut": "F2"
     },
     {
      "id": "create",
      "text": "online-create",
      "shortcut": "F3"
     },
     {
      "id": "server",
      "text": "online-change-server",
      "shortcut": "F4"
     },
     {
      "id": "account",
      "text": "online-change-account",
      "shortcut": "F5"
     },
     {
      "id": "back",
      "text": "back",
      "shortcut": "escape"
     }
    ]
   },
   "online_chat": {
    "buttons": [
     {
      "id": "write",
      "text": "online-write",
      "shortcut": "F1"
     },
     {
      "id": "invite",
      "text": "online-invite",
      "shortcut": "F2"
     },
     {
      "id": "accept",
      "text": "online-accept",
      "shortcut": "F3"
     },
     {
      "id": "refuse",
      "text": "online-refuse",
      "shortcut": "F4"
     },
     {
      "id": "quick",
      "text": "online-quick",
      "shortcut": "F5"
     },
     {
      "id": "logout",
      "text": "online-logout",
      "shortcut": "F6"
     },
     {
      "id": "back",
      "text": "back",
      "shortcut": "escape"
     }
    ]
   }
  }
 },
 "actions": [
  "animations",
  "back",
  "backups",
  "button_leds",
  "coins",
  "customization",
  "desktop",
  "edit_screens",
  "exhibition",
  "favorite_games",
  "favorite_players",
  "favorite_servers",
  "gallery",
  "infos",
  "local_game",
  "mp3",
  "network",
  "network_create",
  "network_join",
  "online_players",
  "players_bank",
  "raspy2dmd",
  "reset",
  "restart",
  "setup_buttons",
  "setup_camera",
  "setup_leds",
  "setup_pins_leds",
  "setup_segment_colors",
  "shutdown",
  "test_buttons",
  "test_target",
  "test_toys",
  "trophies",
  "update",
  "usb_pads"
 ],
 "prefixes": [
  "menu:",
  "category:",
  "game:",
  "favorite:"
 ],
 "games": {
  "classic": [
   "321_Zlip",
   "Batard",
   "Bermuda_Triangle",
   "Big6",
   "Bob27",
   "By_Fives",
   "Chti_501",
   "Color",
   "Cricket",
   "Duel",
   "High_Score",
   "Ho_One",
   "Kapital",
   "Killer",
   "Kinito",
   "Low_Score",
   "Mickey",
   "Practice",
   "Round_the_clock",
   "Routine",
   "Scram_Cricket",
   "Shanghai",
   "Shoot-out",
   "Slider",
   "Up_Down_Count_Up"
  ],
  "fun": [
   "Bingo",
   "Bulls",
   "Castle",
   "Challenge",
   "Chaos",
   "Conquer",
   "Dragon",
   "Dungeon",
   "GameOfGoose",
   "Hangman",
   "Incendie",
   "Morpion",
   "Othello",
   "Puissance4",
   "Pursuit",
   "Risk",
   "Robin_Drink",
   "Robin_Strip",
   "Sabotage",
   "Simon",
   "Switch",
   "Target",
   "Tower",
   "Treasure",
   "Voleur",
   "Yahtzydarts"
  ],
  "sport": [
   "Balltrap",
   "Baseball",
   "Bowling",
   "Fighters",
   "Football",
   "Golf",
   "Horse",
   "Pingpong",
   "Punch-Out",
   "Snooker",
   "Tennis"
  ]
 },
 "themes": {
  "clear": {
   "colors": {
    "border-radius": 10,
    "button-radius": "max",
    "border-size": 3,
    "padding": 2,
    "color-black": [
     0,
     0,
     0
    ],
    "bg-global": false,
    "bg-round-nb": [
     255,
     255,
     255
    ],
    "bg-round-nb-header": [
     107,
     134,
     176
    ],
    "bg-LOGO": [
     0,
     0,
     0
    ],
    "bg-darts-nb": [
     255,
     255,
     255
    ],
    "bg-darts-nb-header": [
     107,
     134,
     176
    ],
    "bg-optionslist-header": [
     107,
     134,
     176
    ],
    "bg-optionslist": [
     255,
     255,
     255
    ],
    "player1": [
     0,
     255,
     0
    ],
    "player2": [
     0,
     0,
     255
    ],
    "player3": [
     255,
     0,
     0
    ],
    "player4": [
     255,
     255,
     0
    ],
    "player5": [
     255,
     0,
     255
    ],
    "player6": [
     0,
     255,
     255
    ],
    "player7": [
     255,
     0,
     128
    ],
    "player8": [
     0,
     255,
     128
    ],
    "player9": [
     0,
     128,
     255
    ],
    "player10": [
     255,
     128,
     0
    ],
    "player11": [
     128,
     255,
     0
    ],
    "player12": [
     128,
     0,
     255
    ],
    "menu-header": [
     255,
     255,
     255
    ],
    "menu-text": [
     0,
     0,
     0
    ],
    "menu-selected": [
     112,
     156,
     118
    ],
    "menu-shortcut": [
     224,
     196,
     119
    ],
    "menu-alternate": [
     107,
     134,
     176
    ],
    "menu-ok": [
     112,
     156,
     118
    ],
    "menu-warning": [
     205,
     144,
     110
    ],
    "menu-ko": [
     189,
     108,
     109
    ],
    "menu-item-white": [
     255,
     255,
     255
    ],
    "menu-item-black": [
     0,
     0,
     0
    ],
    "menu-text-black": [
     0,
     0,
     0
    ],
    "menu-text-white": [
     255,
     255,
     255
    ],
    "menu-buttons": [
     232,
     232,
     232
    ],
    "menu-favorite": [
     255,
     215,
     0
    ],
    "menu-border": [
     0,
     0,
     0
    ],
    "menu-inactive": [
     128,
     128,
     128
    ],
    "description-bg": [
     213,
     206,
     186
    ],
    "description-text": [
     0,
     0,
     0
    ],
    "description-game": [
     0,
     0,
     0
    ],
    "game-bg": [
     0,
     0,
     0
    ],
    "game-score": [
     255,
     255,
     255
    ],
    "game-headers": [
     255,
     255,
     255
    ],
    "game-player": [
     119,
     119,
     118
    ],
    "game-player-name": [
     255,
     255,
     255
    ],
    "game-alt-headers": [
     48,
     48,
     48
    ],
    "game-round": [
     107,
     134,
     176
    ],
    "game-title1": [
     48,
     48,
     48
    ],
    "game-title2": [
     255,
     255,
     255
    ],
    "game-type": [
     255,
     0,
     0
    ],
    "game-table": [
     160,
     160,
     160
    ],
    "game-text": [
     255,
     255,
     255
    ],
    "game-option": [
     255,
     215,
     0
    ],
    "game-darts": [
     160,
     160,
     160
    ],
    "game-inactive": [
     119,
     119,
     118
    ],
    "game-dead": [
     48,
     48,
     48
    ],
    "game-grey": [
     213,
     206,
     186
    ],
    "game-grey2": [
     74,
     74,
     74
    ],
    "game-purple": [
     140,
     108,
     161
    ],
    "game-red": [
     255,
     0,
     0
    ],
    "game-green": [
     0,
     255,
     0
    ],
    "game-blue": [
     0,
     0,
     255
    ],
    "game-gold": [
     255,
     215,
     0
    ],
    "game-silver": [
     192,
     192,
     192
    ],
    "game-bronze": [
     205,
     127,
     50
    ],
    "message-bg": [
     255,
     255,
     255
    ],
    "message-text": [
     0,
     0,
     0
    ],
    "target-sb": [
     189,
     108,
     109
    ],
    "target-db": [
     107,
     134,
     176
    ],
    "target-double1": [
     255,
     255,
     255
    ],
    "target-double2": [
     255,
     0,
     0
    ],
    "target-triple1": [
     255,
     255,
     255
    ],
    "target-triple2": [
     255,
     0,
     0
    ],
    "target-simple1": [
     0,
     0,
     255
    ],
    "target-simple2": [
     255,
     255,
     255
    ],
    "bob27-bg": [
     45,
     78,
     99
    ],
    "bob27-blue": [
     46,
     64,
     76
    ],
    "bob27-green": [
     45,
     108,
     85
    ],
    "bob27-red": [
     124,
     84,
     87
    ],
    "bob27-hit": [
     57,
     209,
     129
    ],
    "bob27-miss": [
     232,
     21,
     37
    ],
    "bob27-text": [
     255,
     255,
     255
    ],
    "fighters-medic": [
     0,
     240,
     0
    ],
    "fighters-actual-player": [
     255,
     255,
     255
    ],
    "fighters-alive-player": [
     150,
     0,
     0
    ],
    "fighters-dead-player": [
     255,
     255,
     255
    ],
    "fighters-targets": [
     255,
     255,
     255
    ],
    "fighters-scores": [
     255,
     255,
     255
    ],
    "fighters-round": [
     255,
     255,
     255
    ],
    "fighters-darts": [
     255,
     255,
     255
    ],
    "suggestion-color-allplayer": null,
    "main-sub-menu-shortcuts": "",
    "main-sub-menu-text-align": "Left",
    "parametrage-menu-shortcuts": "",
    "parametrage-menu-text-align": "Left",
    "players-menu-shortcuts": "",
    "players-menu-text-align": "Left",
    "game-options-menu-shortcuts": "",
    "game-options-menu-text-align": "Left"
   },
   "font": "MaPolice.ttf",
   "background": "images/background.png",
   "menus": {}
  },
  "sombre": {
   "colors": {
    "border-radius": 10,
    "button-radius": "max",
    "border-size": 0,
    "padding": 2,
    "color-black": [
     0,
     0,
     0
    ],
    "bg-global": false,
    "bg-round-nb": [
     0,
     0,
     0
    ],
    "bg-round-nb-header": [
     51,
     81,
     127
    ],
    "bg-LOGO": [
     0,
     0,
     0
    ],
    "bg-darts-nb": [
     0,
     0,
     0
    ],
    "bg-darts-nb-header": [
     51,
     81,
     127
    ],
    "bg-optionslist-header": [
     51,
     81,
     127
    ],
    "bg-optionslist": [
     0,
     0,
     0
    ],
    "player1": [
     255,
     0,
     0
    ],
    "player2": [
     0,
     255,
     0
    ],
    "player3": [
     0,
     0,
     255
    ],
    "player4": [
     255,
     255,
     0
    ],
    "player5": [
     255,
     0,
     255
    ],
    "player6": [
     0,
     255,
     255
    ],
    "player7": [
     128,
     255,
     0
    ],
    "player8": [
     128,
     0,
     255
    ],
    "player9": [
     0,
     128,
     255
    ],
    "player10": [
     255,
     128,
     0
    ],
    "player11": [
     255,
     0,
     128
    ],
    "player12": [
     0,
     255,
     128
    ],
    "menu-header": [
     255,
     255,
     255
    ],
    "menu-text": [
     0,
     0,
     0
    ],
    "menu-selected": [
     193,
     193,
     193
    ],
    "menu-shortcut": [
     194,
     1,
     1
    ],
    "menu-alternate": [
     194,
     1,
     1
    ],
    "menu-ok": [
     112,
     156,
     118
    ],
    "menu-warning": [
     205,
     144,
     110
    ],
    "menu-ko": [
     189,
     108,
     109
    ],
    "menu-item-white": [
     0,
     0,
     0
    ],
    "menu-item-black": [
     0,
     0,
     0
    ],
    "menu-text-black": [
     255,
     255,
     255
    ],
    "menu-text-white": [
     255,
     255,
     255
    ],
    "menu-buttons": [
     100,
     100,
     100
    ],
    "menu-favorite": [
     255,
     215,
     0
    ],
    "menu-border": [
     255,
     255,
     255
    ],
    "menu-inactive": [
     128,
     128,
     128
    ],
    "description-bg": [
     213,
     206,
     186
    ],
    "description-text": [
     0,
     0,
     0
    ],
    "description-game": [
     0,
     0,
     0
    ],
    "game-bg": [
     0,
     0,
     0
    ],
    "game-score": [
     255,
     255,
     255
    ],
    "game-headers": [
     255,
     255,
     255
    ],
    "game-player": [
     119,
     119,
     118
    ],
    "game-player-name": [
     255,
     255,
     255
    ],
    "game-alt-headers": [
     48,
     48,
     48
    ],
    "game-round": [
     107,
     134,
     176
    ],
    "game-title1": [
     48,
     48,
     48
    ],
    "game-title2": [
     255,
     255,
     255
    ],
    "game-type": [
     255,
     0,
     0
    ],
    "game-table": [
     160,
     160,
     160
    ],
    "game-text": [
     255,
     255,
     255
    ],
    "game-option": [
     255,
     215,
     0
    ],
    "game-darts": [
     160,
     160,
     160
    ],
    "game-inactive": [
     119,
     119,
     118
    ],
    "game-dead": [
     48,
     48,
     48
    ],
    "game-grey": [
     213,
     206,
     186
    ],
    "game-grey2": [
     74,
     74,
     74
    ],
    "game-purple": [
     140,
     108,
     161
    ],
    "game-red": [
     255,
     0,
     0
    ],
    "game-green": [
     0,
     255,
     0
    ],
    "game-blue": [
     0,
     0,
     255
    ],
    "game-gold": [
     255,
     215,
     0
    ],
    "game-silver": [
     192,
     192,
     192
    ],
    "game-bronze": [
     205,
     127,
     50
    ],
    "message-bg": [
     255,
     255,
     255
    ],
    "message-text": [
     0,
     0,
     0
    ],
    "target-sb": [
     255,
     0,
     0
    ],
    "target-db": [
     255,
     0,
     0
    ],
    "target-double1": [
     0,
     0,
     255
    ],
    "target-double2": [
     255,
     0,
     0
    ],
    "target-triple1": [
     0,
     0,
     255
    ],
    "target-triple2": [
     255,
     0,
     0
    ],
    "target-simple1": [
     255,
     255,
     255
    ],
    "target-simple2": [
     255,
     255,
     255
    ],
    "bob27-bg": [
     45,
     78,
     99
    ],
    "bob27-blue": [
     46,
     64,
     76
    ],
    "bob27-green": [
     45,
     108,
     85
    ],
    "bob27-red": [
     124,
     84,
     87
    ],
    "bob27-hit": [
     57,
     209,
     129
    ],
    "bob27-miss": [
     232,
     21,
     37
    ],
    "bob27-text": [
     255,
     255,
     255
    ],
    "fighters-medic": [
     0,
     240,
     0
    ],
    "fighters-actual-player": [
     255,
     255,
     255
    ],
    "fighters-alive-player": [
     150,
     0,
     0
    ],
    "fighters-dead-player": [
     255,
     255,
     255
    ],
    "fighters-targets": [
     255,
     255,
     255
    ],
    "fighters-scores": [
     255,
     255,
     255
    ],
    "fighters-round": [
     255,
     255,
     255
    ],
    "fighters-darts": [
     255,
     255,
     255
    ],
    "suggestion-color-allplayer": null,
    "main-sub-menu-shortcuts": null,
    "main-sub-menu-text-align": "Center",
    "parametrage-menu-shortcuts": null,
    "parametrage-menu-text-align": "Center",
    "players-menu-shortcuts": null,
    "players-menu-text-align": "Center",
    "game-options-menu-shortcuts": null,
    "game-options-menu-text-align": "Center",
    "target-bgcolor1": [
     0,
     255,
     0
    ],
    "target-bgcolor2": [
     255,
     0,
     0
    ],
    "target-bgcolor3": [
     255,
     255,
     255
    ]
   },
   "font": "CompactaBT.ttf",
   "background": "images/background/background.png",
   "menus": {
    "version": 1,
    "menus": {
     "main": {
      "area": {
       "x": 0.0885,
       "y": 0.1704,
       "width": 0.8224,
       "height": 0.6611
      },
      "button_size": {
       "height": 0.0206
      },
      "gap": {
       "y": 0.005,
       "x": 0.005
      },
      "align": "top",
      "buttons": [
       {
        "id": "local",
        "action": "local_game",
        "text": {
         "size": "auto",
         "text": "game-type-local"
        },
        "shortcut": "F1",
        "exhibition": true,
        "place": {
         "x": 0.274,
         "y": 0.1519,
         "width": 0.4547,
         "height": 0.1407
        }
       },
       {
        "id": "gallery",
        "action": "gallery",
        "text": "gallery",
        "shortcut": "F6",
        "exhibition": true,
        "place": {
         "x": 0.5021,
         "y": 0.5824,
         "width": 0.4089,
         "height": 0.1231
        }
       },
       {
        "id": "miscellaneous",
        "action": "menu:miscellaneous",
        "text": "miscellaneous",
        "shortcut": "F4",
        "place": {
         "x": 0.2266,
         "y": 0.7111,
         "width": 0.2708,
         "height": 0.1231
        }
       },
       {
        "id": "trophees",
        "action": "trophies",
        "text": "trophees",
        "shortcut": "F5",
        "exhibition": true,
        "place": {
         "x": 0.0885,
         "y": 0.5824,
         "width": 0.4089,
         "height": 0.1231
        }
       },
       {
        "id": "infos",
        "action": "infos",
        "shortcut": "F9",
        "visible": false
       },
       {
        "id": "restart",
        "action": "restart",
        "shortcut": "F11",
        "visible": false
       },
       {
        "id": "quit",
        "action": "desktop",
        "text": "back-to-desktop",
        "shortcut": "F12",
        "shape": "rectangle",
        "place": {
         "x": 0.5021,
         "y": 0.7111,
         "width": 0.2708,
         "height": 0.1231
        }
       },
       {
        "id": "shutdown",
        "action": "shutdown",
        "text": "exit",
        "shortcut": "escape",
        "confirm": "realy-stop",
        "pressed": {
         "scale": 0.5
        },
        "place": {
         "x": 0.9172,
         "y": 0.912,
         "width": 0.0729,
         "height": 0.062
        }
       },
       {
        "id": "button1",
        "action": "game:Ho_One",
        "text": "'01",
        "place": {
         "x": 0.0885,
         "y": 0.2981,
         "width": 0.2021,
         "height": 0.1481
        }
       },
       {
        "id": "button2",
        "action": "game:Cricket",
        "text": "Cricket",
        "place": {
         "x": 0.5021,
         "y": 0.2981,
         "width": 0.2021,
         "height": 0.1481
        }
       },
       {
        "id": "button3",
        "action": "game:321_Zlip",
        "text": "321 Zlip",
        "place": {
         "x": 0.7089,
         "y": 0.2981,
         "width": 0.2021,
         "height": 0.1481
        }
       },
       {
        "id": "button4",
        "action": "game:High_Score",
        "text": "High Score",
        "place": {
         "x": 0.2953,
         "y": 0.2981,
         "width": 0.2021,
         "height": 0.1481
        }
       },
       {
        "id": "network",
        "action": "network",
        "text": "online-title",
        "shortcut": "F2",
        "place": {
         "x": 0.0885,
         "y": 0.4528,
         "width": 0.8224,
         "height": 0.1231
        }
       }
      ],
      "layout": "tiles",
      "columns": 1,
      "style": "main",
      "show_version": {
       "x": 0.0047,
       "y": 0.8472,
       "width": 0.1073,
       "height": 0.1102
      },
      "removed": [
       "game-Ho_One",
       "netcreate",
       "netjoin"
      ]
     },
     "miscellaneous": {
      "area": {
       "x": 0.1443,
       "y": 0.1556,
       "width": 0.7083,
       "height": 0.688
      },
      "button_size": {
       "height": 0.1344
      },
      "gap": {
       "y": 0.004,
       "x": 0.004
      },
      "align": "top",
      "buttons": [
       {
        "id": "firstnames",
        "action": "favorite_players",
        "text": "favorites-players",
        "shortcut": "F1",
        "cell": {
         "row": 0,
         "column": 0
        }
       },
       {
        "id": "games",
        "action": "favorite_games",
        "text": "favorites-games",
        "shortcut": "F2"
       },
       {
        "id": "servers",
        "action": "favorite_servers",
        "text": "favorites-servers",
        "shortcut": "F3"
       },
       {
        "id": "customization",
        "action": "customization",
        "text": "customization",
        "shortcut": "F4"
       },
       {
        "id": "animations",
        "action": "animations",
        "text": "animations",
        "shortcut": "F5"
       },
       {
        "id": "firstname-bank",
        "action": "players_bank",
        "text": "players-bank",
        "shortcut": "F6"
       },
       {
        "id": "setup",
        "action": "menu:settings",
        "text": "setup",
        "shortcut": "F7"
       },
       {
        "id": "backups",
        "action": "backups",
        "text": "backups",
        "shortcut": "F8"
       },
       {
        "id": "exhibition",
        "action": "exhibition",
        "text": "exhibition",
        "shortcut": "F9"
       },
       {
        "id": "back",
        "action": "back",
        "text": "back",
        "shortcut": "escape",
        "footer": "left"
       },
       {
        "id": "update",
        "action": "update",
        "text": "btn_update",
        "footer": "right"
       }
      ],
      "layout": "tiles",
      "style": "miscellaneous",
      "columns": 2
     },
     "games": {
      "style": "classic",
      "area": {
       "x": 0.0172,
       "y": 0.1509,
       "width": 0.4141,
       "height": 0.7019
      }
     },
     "settings": {
      "area": {
       "x": 0.1427,
       "y": 0.1546,
       "width": 0.7104,
       "height": 0.6824
      },
      "button_size": {
       "height": 0.2241
      },
      "gap": {
       "y": 0.004,
       "x": 0.004
      },
      "align": "top",
      "layout": "tiles",
      "style": "settings",
      "buttons": [
       {
        "id": "setup-buttons",
        "action": "setup_buttons",
        "text": "setup-buttons",
        "shortcut": "F1",
        "place": {
         "x": 0.1427,
         "y": 0.1546,
         "width": 0.2302,
         "height": 0.1741
        }
       },
       {
        "id": "setup-pinleds",
        "action": "setup_pins_leds",
        "text": "setup-pinsleds",
        "shortcut": "F2",
        "place": {
         "x": 0.3828,
         "y": 0.1546,
         "width": 0.2302,
         "height": 0.1741
        }
       },
       {
        "id": "setup-leds",
        "action": "setup_leds",
        "text": "setup-leds",
        "shortcut": "F3",
        "place": {
         "x": 0.6229,
         "y": 0.1546,
         "width": 0.2302,
         "height": 0.1741
        }
       },
       {
        "id": "setup-couleurs-segments",
        "action": "setup_segment_colors",
        "text": "setup-couleurs-segments",
        "shortcut": "F4",
        "place": {
         "x": 0.1427,
         "y": 0.338,
         "width": 0.2302,
         "height": 0.1741
        }
       },
       {
        "id": "setup-cam",
        "action": "setup_camera",
        "text": "setup-cam",
        "shortcut": "F5",
        "place": {
         "x": 0.3828,
         "y": 0.338,
         "width": 0.2302,
         "height": 0.1741
        }
       },
       {
        "id": "usb-pads",
        "action": "usb_pads",
        "text": "usb-pads",
        "place": {
         "x": 0.6229,
         "y": 0.338,
         "width": 0.2302,
         "height": 0.1741
        }
       },
       {
        "id": "test-buttons",
        "action": "test_buttons",
        "text": "test-buttons",
        "shortcut": "F6",
        "place": {
         "x": 0.6229,
         "y": 0.5213,
         "width": 0.2302,
         "height": 0.1741
        }
       },
       {
        "id": "test-target",
        "action": "test_target",
        "text": "test-target",
        "shortcut": "F7",
        "place": {
         "x": 0.1427,
         "y": 0.5213,
         "width": 0.2302,
         "height": 0.1741
        }
       },
       {
        "id": "test-toys",
        "action": "test_toys",
        "text": "test-toys",
        "shortcut": "F8",
        "place": {
         "x": 0.3828,
         "y": 0.5213,
         "width": 0.2302,
         "height": 0.1741
        }
       },
       {
        "id": "reset",
        "action": "reset",
        "text": "reset",
        "shortcut": "F9",
        "place": {
         "x": 0.8531,
         "y": 0.8787,
         "width": 0.0984,
         "height": 0.0583
        },
        "shape": "pill",
        "background": {
         "color": "#919191"
        }
       },
       {
        "id": "coins",
        "action": "coins",
        "text": "coins",
        "place": {
         "x": 0.3828,
         "y": 0.7046,
         "width": 0.2302,
         "height": 0.1741
        }
       },
       {
        "id": "back",
        "action": "back",
        "text": "back",
        "shortcut": "escape",
        "footer": "left"
       }
      ]
     }
    },
    "styles": {
     "main": {
      "background": {
       "color": "menu-buttons*1.5"
      },
      "text": {
       "size": "auto",
       "color": "menu-text-black",
       "align": "theme"
      },
      "shape": "rectangle"
     },
     "miscellaneous": {
      "background": {
       "color": "menu-buttons*1.5"
      },
      "text": {
       "size": "auto",
       "color": "menu-text-black",
       "align": "theme"
      },
      "shape": "rectangle"
     },
     "settings": {
      "background": {
       "color": "menu-buttons*1.5"
      },
      "text": {
       "size": "auto",
       "color": "menu-text-black",
       "align": "theme"
      },
      "shape": "rectangle"
     }
    }
   }
  }
 },
 "images": {
  "official": {
   "images/logos_menu/321_Zlip.png": "assets/img/official/images/logos_menu/321_Zlip.webp",
   "images/logos_menu/Balltrap.png": "assets/img/official/images/logos_menu/Balltrap.webp",
   "images/logos_menu/Baseball.png": "assets/img/official/images/logos_menu/Baseball.webp",
   "images/logos_menu/Batard.png": "assets/img/official/images/logos_menu/Batard.webp",
   "images/logos_menu/Bermuda_Triangle.png": "assets/img/official/images/logos_menu/Bermuda_Triangle.webp",
   "images/logos_menu/Big6.png": "assets/img/official/images/logos_menu/Big6.webp",
   "images/logos_menu/Bingo.png": "assets/img/official/images/logos_menu/Bingo.webp",
   "images/logos_menu/Bob27.png": "assets/img/official/images/logos_menu/Bob27.webp",
   "images/logos_menu/Bowling.png": "assets/img/official/images/logos_menu/Bowling.webp",
   "images/logos_menu/Bulls.png": "assets/img/official/images/logos_menu/Bulls.webp",
   "images/logos_menu/By_Fives.png": "assets/img/official/images/logos_menu/By_Fives.webp",
   "images/logos_menu/Castle.png": "assets/img/official/images/logos_menu/Castle.webp",
   "images/logos_menu/Challenge.png": "assets/img/official/images/logos_menu/Challenge.webp",
   "images/logos_menu/Chaos.png": "assets/img/official/images/logos_menu/Chaos.webp",
   "images/logos_menu/Chti_501.png": "assets/img/official/images/logos_menu/Chti_501.webp",
   "images/logos_menu/Color.png": "assets/img/official/images/logos_menu/Color.webp",
   "images/logos_menu/Conquer.png": "assets/img/official/images/logos_menu/Conquer.webp",
   "images/logos_menu/Cricket.png": "assets/img/official/images/logos_menu/Cricket.webp",
   "images/logos_menu/Cul_de_chouette.png": "assets/img/official/images/logos_menu/Cul_de_chouette.webp",
   "images/logos_menu/Dragon.png": "assets/img/official/images/logos_menu/Dragon.webp",
   "images/logos_menu/Duel.png": "assets/img/official/images/logos_menu/Duel.webp",
   "images/logos_menu/Dungeon.png": "assets/img/official/images/logos_menu/Dungeon.webp",
   "images/logos_menu/Fighters.png": "assets/img/official/images/logos_menu/Fighters.webp",
   "images/logos_menu/Football.png": "assets/img/official/images/logos_menu/Football.webp",
   "images/logos_menu/GameOfGoose.png": "assets/img/official/images/logos_menu/GameOfGoose.webp",
   "images/logos_menu/GameOfGoose_0.png": "assets/img/official/images/logos_menu/GameOfGoose_0.webp",
   "images/logos_menu/Golf.png": "assets/img/official/images/logos_menu/Golf.webp",
   "images/logos_menu/Hangman.png": "assets/img/official/images/logos_menu/Hangman.webp",
   "images/logos_menu/High_Score.png": "assets/img/official/images/logos_menu/High_Score.webp",
   "images/logos_menu/Ho_One.png": "assets/img/official/images/logos_menu/Ho_One.webp",
   "images/logos_menu/Horse.png": "assets/img/official/images/logos_menu/Horse.webp",
   "images/logos_menu/Incendie.png": "assets/img/official/images/logos_menu/Incendie.webp",
   "images/logos_menu/Kapital.png": "assets/img/official/images/logos_menu/Kapital.webp",
   "images/logos_menu/Killer.png": "assets/img/official/images/logos_menu/Killer.webp",
   "images/logos_menu/Kinito.png": "assets/img/official/images/logos_menu/Kinito.webp",
   "images/logos_menu/Low_Score.png": "assets/img/official/images/logos_menu/Low_Score.webp",
   "images/logos_menu/Mickey.png": "assets/img/official/images/logos_menu/Mickey.webp",
   "images/logos_menu/Morpion.png": "assets/img/official/images/logos_menu/Morpion.webp",
   "images/logos_menu/Othello.png": "assets/img/official/images/logos_menu/Othello.webp",
   "images/logos_menu/Pingpong.png": "assets/img/official/images/logos_menu/Pingpong.webp",
   "images/logos_menu/Practice.png": "assets/img/official/images/logos_menu/Practice.webp",
   "images/logos_menu/Puissance4.png": "assets/img/official/images/logos_menu/Puissance4.webp",
   "images/logos_menu/Punch-Out.png": "assets/img/official/images/logos_menu/Punch-Out.webp",
   "images/logos_menu/Pursuit.png": "assets/img/official/images/logos_menu/Pursuit.webp",
   "images/logos_menu/Risk.png": "assets/img/official/images/logos_menu/Risk.webp",
   "images/logos_menu/Robin_Drink.png": "assets/img/official/images/logos_menu/Robin_Drink.webp",
   "images/logos_menu/Robin_Strip.png": "assets/img/official/images/logos_menu/Robin_Strip.webp",
   "images/logos_menu/Round_the_clock.png": "assets/img/official/images/logos_menu/Round_the_clock.webp",
   "images/logos_menu/Routine.png": "assets/img/official/images/logos_menu/Routine.webp",
   "images/logos_menu/Sabotage.png": "assets/img/official/images/logos_menu/Sabotage.webp",
   "images/logos_menu/Scram_Cricket.png": "assets/img/official/images/logos_menu/Scram_Cricket.webp",
   "images/logos_menu/Shanghai.png": "assets/img/official/images/logos_menu/Shanghai.webp",
   "images/logos_menu/Shoot-out.png": "assets/img/official/images/logos_menu/Shoot-out.webp",
   "images/logos_menu/Simon.png": "assets/img/official/images/logos_menu/Simon.webp",
   "images/logos_menu/Slider.png": "assets/img/official/images/logos_menu/Slider.webp",
   "images/logos_menu/Snooker.png": "assets/img/official/images/logos_menu/Snooker.webp",
   "images/logos_menu/Switch.png": "assets/img/official/images/logos_menu/Switch.webp",
   "images/logos_menu/Target.png": "assets/img/official/images/logos_menu/Target.webp",
   "images/logos_menu/Tennis.png": "assets/img/official/images/logos_menu/Tennis.webp",
   "images/logos_menu/Tower.png": "assets/img/official/images/logos_menu/Tower.webp",
   "images/logos_menu/Treasure.png": "assets/img/official/images/logos_menu/Treasure.webp",
   "images/logos_menu/Up_Down_Count_Up.png": "assets/img/official/images/logos_menu/Up_Down_Count_Up.webp",
   "images/logos_menu/Voleur.png": "assets/img/official/images/logos_menu/Voleur.webp",
   "images/logos_menu/Yahtzydarts.png": "assets/img/official/images/logos_menu/Yahtzydarts.webp",
   "images/logos_menu/menu_classic/classic_1.png": "assets/img/official/images/logos_menu/menu_classic/classic_1.webp",
   "images/logos_menu/menu_classic/classic_2.png": "assets/img/official/images/logos_menu/menu_classic/classic_2.webp",
   "images/logos_menu/menu_classic/classics.png": "assets/img/official/images/logos_menu/menu_classic/classics.webp",
   "images/logos_menu/menu_classic/classics_2.png": "assets/img/official/images/logos_menu/menu_classic/classics_2.webp",
   "images/logos_menu/menu_favoris/favoris.png": "assets/img/official/images/logos_menu/menu_favoris/favoris.webp",
   "images/logos_menu/menu_favoris/favoris_2.png": "assets/img/official/images/logos_menu/menu_favoris/favoris_2.webp",
   "images/logos_menu/menu_fun/fun.png": "assets/img/official/images/logos_menu/menu_fun/fun.webp",
   "images/logos_menu/menu_fun/fun_1.png": "assets/img/official/images/logos_menu/menu_fun/fun_1.webp",
   "images/logos_menu/menu_fun/fun_2.png": "assets/img/official/images/logos_menu/menu_fun/fun_2.webp",
   "images/logos_menu/menu_sport/sport_1.png": "assets/img/official/images/logos_menu/menu_sport/sport_1.webp",
   "images/logos_menu/menu_sport/sport_2.png": "assets/img/official/images/logos_menu/menu_sport/sport_2.webp",
   "images/logos_menu/menu_sport/sports.png": "assets/img/official/images/logos_menu/menu_sport/sports.webp",
   "images/logos_menu/menu_sport/sports_2.png": "assets/img/official/images/logos_menu/menu_sport/sports_2.webp",
   "images/background.png": "assets/img/official/images/background.jpg",
   "images/background_clear.png": "assets/img/official/images/background_clear.jpg"
  },
  "clear": {},
  "sombre": {
   "images/background/background.png": "assets/img/sombre/images/background/background.jpg",
   "images/logos_menu/321_Zlip.png": "assets/img/sombre/images/logos_menu/321_Zlip.webp",
   "images/logos_menu/Balltrap.png": "assets/img/sombre/images/logos_menu/Balltrap.webp",
   "images/logos_menu/Baseball.png": "assets/img/sombre/images/logos_menu/Baseball.webp",
   "images/logos_menu/Batard.png": "assets/img/sombre/images/logos_menu/Batard.webp",
   "images/logos_menu/Bermuda_Triangle.png": "assets/img/sombre/images/logos_menu/Bermuda_Triangle.webp",
   "images/logos_menu/Big6.png": "assets/img/sombre/images/logos_menu/Big6.webp",
   "images/logos_menu/Bingo.png": "assets/img/sombre/images/logos_menu/Bingo.webp",
   "images/logos_menu/Bob27.png": "assets/img/sombre/images/logos_menu/Bob27.webp",
   "images/logos_menu/Bowling.png": "assets/img/sombre/images/logos_menu/Bowling.webp",
   "images/logos_menu/Bulls.png": "assets/img/sombre/images/logos_menu/Bulls.webp",
   "images/logos_menu/By_Fives.png": "assets/img/sombre/images/logos_menu/By_Fives.webp",
   "images/logos_menu/Castle.png": "assets/img/sombre/images/logos_menu/Castle.webp",
   "images/logos_menu/Challenge.png": "assets/img/sombre/images/logos_menu/Challenge.webp",
   "images/logos_menu/Chaos.png": "assets/img/sombre/images/logos_menu/Chaos.webp",
   "images/logos_menu/Chti_501.png": "assets/img/sombre/images/logos_menu/Chti_501.webp",
   "images/logos_menu/Color.png": "assets/img/sombre/images/logos_menu/Color.webp",
   "images/logos_menu/Conquer.png": "assets/img/sombre/images/logos_menu/Conquer.webp",
   "images/logos_menu/Cricket.png": "assets/img/sombre/images/logos_menu/Cricket.webp",
   "images/logos_menu/Cul_de_chouette.png": "assets/img/sombre/images/logos_menu/Cul_de_chouette.webp",
   "images/logos_menu/Dragon.png": "assets/img/sombre/images/logos_menu/Dragon.webp",
   "images/logos_menu/Duel.png": "assets/img/sombre/images/logos_menu/Duel.webp",
   "images/logos_menu/Dungeon.png": "assets/img/sombre/images/logos_menu/Dungeon.webp",
   "images/logos_menu/Fighters.png": "assets/img/sombre/images/logos_menu/Fighters.webp",
   "images/logos_menu/Football.png": "assets/img/sombre/images/logos_menu/Football.webp",
   "images/logos_menu/GameOfGoose.png": "assets/img/sombre/images/logos_menu/GameOfGoose.webp",
   "images/logos_menu/Golf.png": "assets/img/sombre/images/logos_menu/Golf.webp",
   "images/logos_menu/Hangman.png": "assets/img/sombre/images/logos_menu/Hangman.webp",
   "images/logos_menu/High_Score.png": "assets/img/sombre/images/logos_menu/High_Score.webp",
   "images/logos_menu/Ho_One.png": "assets/img/sombre/images/logos_menu/Ho_One.webp",
   "images/logos_menu/Horse.png": "assets/img/sombre/images/logos_menu/Horse.webp",
   "images/logos_menu/Incendie.png": "assets/img/sombre/images/logos_menu/Incendie.webp",
   "images/logos_menu/Kapital.png": "assets/img/sombre/images/logos_menu/Kapital.webp",
   "images/logos_menu/Killer.png": "assets/img/sombre/images/logos_menu/Killer.webp",
   "images/logos_menu/Kinito.png": "assets/img/sombre/images/logos_menu/Kinito.webp",
   "images/logos_menu/Low_Score.png": "assets/img/sombre/images/logos_menu/Low_Score.webp",
   "images/logos_menu/Mickey.png": "assets/img/sombre/images/logos_menu/Mickey.webp",
   "images/logos_menu/Morpion.png": "assets/img/sombre/images/logos_menu/Morpion.webp",
   "images/logos_menu/Othello.png": "assets/img/sombre/images/logos_menu/Othello.webp",
   "images/logos_menu/Pingpong.png": "assets/img/sombre/images/logos_menu/Pingpong.webp",
   "images/logos_menu/Practice.png": "assets/img/sombre/images/logos_menu/Practice.webp",
   "images/logos_menu/Puissance4.png": "assets/img/sombre/images/logos_menu/Puissance4.webp",
   "images/logos_menu/Punch-Out.png": "assets/img/sombre/images/logos_menu/Punch-Out.webp",
   "images/logos_menu/Pursuit.png": "assets/img/sombre/images/logos_menu/Pursuit.webp",
   "images/logos_menu/Risk.png": "assets/img/sombre/images/logos_menu/Risk.webp",
   "images/logos_menu/Robin_Drink.png": "assets/img/sombre/images/logos_menu/Robin_Drink.webp",
   "images/logos_menu/Robin_Strip.png": "assets/img/sombre/images/logos_menu/Robin_Strip.webp",
   "images/logos_menu/Round_the_clock.png": "assets/img/sombre/images/logos_menu/Round_the_clock.webp",
   "images/logos_menu/Routine.png": "assets/img/sombre/images/logos_menu/Routine.webp",
   "images/logos_menu/Sabotage.png": "assets/img/sombre/images/logos_menu/Sabotage.webp",
   "images/logos_menu/Scram_Cricket.png": "assets/img/sombre/images/logos_menu/Scram_Cricket.webp",
   "images/logos_menu/Shanghai.png": "assets/img/sombre/images/logos_menu/Shanghai.webp",
   "images/logos_menu/Shoot-out.png": "assets/img/sombre/images/logos_menu/Shoot-out.webp",
   "images/logos_menu/Simon.png": "assets/img/sombre/images/logos_menu/Simon.webp",
   "images/logos_menu/Slider.png": "assets/img/sombre/images/logos_menu/Slider.webp",
   "images/logos_menu/Snooker.png": "assets/img/sombre/images/logos_menu/Snooker.webp",
   "images/logos_menu/Switch.png": "assets/img/sombre/images/logos_menu/Switch.webp",
   "images/logos_menu/Target.png": "assets/img/sombre/images/logos_menu/Target.webp",
   "images/logos_menu/Tennis.png": "assets/img/sombre/images/logos_menu/Tennis.webp",
   "images/logos_menu/Tower.png": "assets/img/sombre/images/logos_menu/Tower.webp",
   "images/logos_menu/Treasure.png": "assets/img/sombre/images/logos_menu/Treasure.webp",
   "images/logos_menu/Up_Down_Count_Up.png": "assets/img/sombre/images/logos_menu/Up_Down_Count_Up.webp",
   "images/logos_menu/Voleur.png": "assets/img/sombre/images/logos_menu/Voleur.webp",
   "images/logos_menu/Yahtzydarts.png": "assets/img/sombre/images/logos_menu/Yahtzydarts.webp",
   "images/logos_menu/menu_classic/classic_1.png": "assets/img/sombre/images/logos_menu/menu_classic/classic_1.webp",
   "images/logos_menu/menu_classic/classic_2.png": "assets/img/sombre/images/logos_menu/menu_classic/classic_2.webp",
   "images/logos_menu/menu_favoris/favoris_1.png": "assets/img/sombre/images/logos_menu/menu_favoris/favoris_1.webp",
   "images/logos_menu/menu_favoris/favoris_2.png": "assets/img/sombre/images/logos_menu/menu_favoris/favoris_2.webp",
   "images/logos_menu/menu_fun/fun_1.png": "assets/img/sombre/images/logos_menu/menu_fun/fun_1.webp",
   "images/logos_menu/menu_fun/fun_2.png": "assets/img/sombre/images/logos_menu/menu_fun/fun_2.webp",
   "images/logos_menu/menu_sport/sport_1.png": "assets/img/sombre/images/logos_menu/menu_sport/sport_1.webp",
   "images/logos_menu/menu_sport/sport_2.png": "assets/img/sombre/images/logos_menu/menu_sport/sport_2.webp"
  }
 },
 "fonts": {
  "Baldur.ttf": "assets/fonts/Baldur.ttf",
  "Becker.ttf": "assets/fonts/Becker.ttf",
  "Blackwood.ttf": "assets/fonts/Blackwood.ttf",
  "Campfire.ttf": "assets/fonts/Campfire.ttf",
  "CarbonBlock.ttf": "assets/fonts/CarbonBlock.ttf",
  "Chizz.ttf": "assets/fonts/Chizz.ttf",
  "Digital.ttf": "assets/fonts/Digital.ttf",
  "Erika.ttf": "assets/fonts/Erika.ttf",
  "Fabrik.ttf": "assets/fonts/Fabrik.ttf",
  "FreeSansBold.ttf": "assets/fonts/FreeSansBold.ttf",
  "Impact.ttf": "assets/fonts/Impact.ttf",
  "Kamikzon.ttf": "assets/fonts/Kamikzon.ttf",
  "MaPolice.ttf": "assets/fonts/MaPolice.ttf",
  "MagicSchool.ttf": "assets/fonts/MagicSchool.ttf",
  "Magnetob.ttf": "assets/fonts/Magnetob.ttf",
  "Moderna.ttf": "assets/fonts/Moderna.ttf",
  "Monoglyceride.ttf": "assets/fonts/Monoglyceride.ttf",
  "MorrisRoman.ttf": "assets/fonts/MorrisRoman.ttf",
  "PirataOne.ttf": "assets/fonts/PirataOne.ttf",
  "Purisa.ttf": "assets/fonts/Purisa.ttf",
  "SonOfTmU.ttf": "assets/fonts/SonOfTmU.ttf",
  "Unispace.ttf": "assets/fonts/Unispace.ttf",
  "comic-sans-ms.ttf": "assets/fonts/comic-sans-ms.ttf",
  "unicode.compacta.ttf": "assets/fonts/unicode.compacta.ttf",
  "CompactaBT.ttf": "assets/fonts/CompactaBT.ttf"
 },
 "texts": {
  "fr": {
   "animations": "Animations Leds",
   "back": "Retour",
   "back-to-desktop": "Revenir sur le bureau",
   "backups": "Gestion des sauvegardes",
   "btn_update": "Vérifier les mises à jour",
   "button-leds": "LED des boutons",
   "coins": "Monnayeur",
   "continue": "Continuer",
   "customization": "Personnalisation du jeu",
   "dmd-backup-menu": "Sauvegardes",
   "dmd-bestwin": "Que le meilleur gagne !",
   "dmd-game-choice": "Choix du jeu",
   "dmd-game-classic": "Jeux classiques",
   "dmd-game-favorites": "Jeux favoris",
   "dmd-game-fun": "Jeux fun",
   "dmd-game-sport": "Jeux de sport",
   "dmd-player-bank": "Banque de joueurs",
   "dmd-player-choice": "Choix des joueurs",
   "dmd-player-favorites": "Joueurs favoris",
   "dmd-server-favorites": "Serveurs favoris",
   "down": "Bas",
   "edit-screens": "Modifier les écrans",
   "exhibition": "Mode exposition",
   "exit": "Quitter",
   "favorite": "Favori",
   "favorite-add-game": "Ajouter aux favoris",
   "favorite-add-options": "Nouveau favori avec ses options",
   "favorite-add-plain": "Nouveau favori sans options",
   "favorite-ask": "Les choisir au lancement",
   "favorite-choose": "Choisir dans la liste des joueurs",
   "favorite-count": "Nombre de joueurs du favori",
   "favorite-define-options": "définir ses options ?",
   "favorite-edit-options": "Modifier les options",
   "favorite-edit-players": "Modifier les joueurs",
   "favorite-empty": "vide",
   "favorite-exists": "Ce favori existe déjà",
   "favorite-generic": "Joueur 1, Joueur 2…",
   "favorite-last": "Les derniers joueurs choisis",
   "favorite-no-options": "Sans options : elles sont choisies à chaque lancement",
   "favorite-not-saved": "Le favori n'a pas pu être enregistré",
   "favorite-numbered": "L'enregistrer aussi comme favori numéroté ?",
   "favorite-numbered-remove": "Retirer ce favori",
   "favorite-numbered-sub": "Favori 1 à 9 : il ne sera dans le menu principal que si le fichier de menus lui donne un bouton (favorite:fav1…)",
   "favorite-options-legend": "Opt. : options définies, sans écran d'options",
   "favorite-options-mark": "Opt.",
   "favorite-options-title": "Options du favori",
   "favorite-pick-sub": "Joueurs favoris et banque de prénoms",
   "favorite-place-button": "Le placer aussi sur un bouton du menu principal ?",
   "favorite-player": "Joueur",
   "favorite-players": "Joueurs du favori",
   "favorite-players-sub": "Avec quels joueurs le lancer ?",
   "favorite-remove": "Retirer des favoris",
   "favorite-removed": "Favori {number} retiré",
   "favorite-replace": "Remplacer le favori",
   "favorite-save": "Enregistrer comme favori",
   "favorite-save-sub": "Choisissez son numéro (un favori déjà enregistré n'est remplacé qu'après confirmation)",
   "favorite-saved": "Favori {number} enregistré",
   "favorite-to-button": "Le placer sur un bouton du menu principal",
   "favorite-too-few": "Il manquera des joueurs. Continuer ?",
   "favorite-too-many": "Les joueurs en trop seront retirés. Continuer ?",
   "favorite-with-options": "avec options",
   "favorite-without-options": "sans options",
   "favorites-games": "Jeux favoris",
   "favorites-players": "Joueurs favoris",
   "favorites-servers": "Serveurs favoris",
   "gallery": "Galerie",
   "game-cat": "Catégorie du jeu",
   "game-list": "Choix du jeu",
   "game-options": "Options du jeu",
   "game-type": "Jeu",
   "game-type-local": "Partie simple",
   "game-type-manual": "Créer une partie en réseau",
   "game-type-master": "Rejoindre une partie en réseau",
   "game-type-menu": "Raspydarts",
   "left": "Reste",
   "miscellaneous": "Divers (Favoris, paramétrage,...)",
   "music-player": "Lecteur MP3",
   "music-source": "Source des morceaux",
   "no": "Non",
   "online-accept": "Accepter",
   "online-change-account": "Changer de compte",
   "online-change-server": "Changer de serveur",
   "online-chat": "Joueurs et chat",
   "online-create": "Créer une partie",
   "online-invite": "Inviter",
   "online-logout": "Déconnexion",
   "online-quick": "Réponses rapides",
   "online-ready": "Prêt à jouer",
   "online-refuse": "Refuser",
   "online-title": "Partie en réseau",
   "online-write": "Écrire",
   "parameters": "Paramètres",
   "players-bank": "Banque de prénoms",
   "players-names": "Nom des joueurs",
   "players-names-subtitle": "Appuyez sur + pour ajouter, - pour supprimer, / pour joueur ordinateur, * pour la couleur du joueur, <Tab> pour mélanger",
   "raspy2dmd": "Afficheur DMD (Raspy2DMD)",
   "realy-stop": "Voulez-vous vraiment quitter ?",
   "reset": "Réinitialiser",
   "restart": "Rejouer",
   "right": "Droite",
   "save": "Sauvegarder",
   "setup": "Paramétrage",
   "setup-buttons": "Paramétrage des boutons et toys",
   "setup-cam": "Paramétrage de la caméra",
   "setup-couleurs-segments": "Paramétrage couleur segment d'origine",
   "setup-leds": "Affectation des leds",
   "setup-pinsleds": "Paramétrage des leds",
   "test-buttons": "Test des boutons",
   "test-target": "Test de la cible",
   "test-toys": "Test des toys",
   "trophees": "Trophées et progression",
   "up": "Haut",
   "usb-pads": "Paramétrage boutons, molettes et manettes USB",
   "yes": "Oui"
  },
  "en": {
   "animations": "LED Animations",
   "back": "Back",
   "back-to-desktop": "Back to desktop",
   "backups": "Backup management",
   "btn_update": "Check for updates",
   "button-leds": "Button LEDs",
   "coins": "Coin mechanism",
   "continue": "Continue",
   "customization": "Game customization",
   "dmd-backup-menu": "Backups",
   "dmd-bestwin": "May the best player win!",
   "dmd-game-choice": "Game choice",
   "dmd-game-classic": "Classic games",
   "dmd-game-favorites": "Favorite games",
   "dmd-game-fun": "Fun games",
   "dmd-game-sport": "Sports games",
   "dmd-player-bank": "Player bank",
   "dmd-player-choice": "Player choice",
   "dmd-player-favorites": "Favorite players",
   "dmd-server-favorites": "Favorite servers",
   "down": "Down",
   "edit-screens": "Edit screens",
   "exhibition": "Exhibition Mode",
   "exit": "Exit",
   "favorite": "Favorite",
   "favorite-add-game": "Add to favorites",
   "favorite-add-options": "New favorite with options",
   "favorite-add-plain": "New favorite without options",
   "favorite-ask": "Select on launch",
   "favorite-choose": "Choose from player list",
   "favorite-count": "Player count for favorite",
   "favorite-define-options": "define options?",
   "favorite-edit-options": "Edit options",
   "favorite-edit-players": "Edit players",
   "favorite-empty": "empty",
   "favorite-exists": "Favorite already exists",
   "favorite-generic": "Player 1, Player 2…",
   "favorite-last": "Last selected players",
   "favorite-no-options": "Without options: selected on every launch",
   "favorite-not-saved": "Favorite could not be saved",
   "favorite-numbered": "Save as numbered favorite?",
   "favorite-numbered-remove": "Remove this favorite",
   "favorite-numbered-sub": "Favorite 1 to 9: appears in main menu only if configured in menu file (favorite:fav1…)",
   "favorite-options-legend": "Opt. : predefined options without options screen",
   "favorite-options-mark": "Opt.",
   "favorite-options-title": "Favorite options",
   "favorite-pick-sub": "Favorite players and name bank",
   "favorite-place-button": "Add shortcut button to main menu?",
   "favorite-player": "Player",
   "favorite-players": "Favorite players",
   "favorite-players-sub": "Which players to launch with?",
   "favorite-remove": "Remove from favorites",
   "favorite-removed": "Favorite {number} removed",
   "favorite-replace": "Replace favorite",
   "favorite-save": "Save as favorite",
   "favorite-save-sub": "Choose favorite number (existing favorite requires confirmation to overwrite)",
   "favorite-saved": "Favorite {number} saved",
   "favorite-to-button": "Add to main menu button",
   "favorite-too-few": "Players missing. Continue?",
   "favorite-too-many": "Extra players will be removed. Continue?",
   "favorite-with-options": "with options",
   "favorite-without-options": "without options",
   "favorites-games": "Favorite games",
   "favorites-players": "Favorite players",
   "favorites-servers": "Favorite servers",
   "gallery": "Gallery",
   "game-cat": "Game category",
   "game-list": "Game choice",
   "game-options": "Game options",
   "game-type": "Game",
   "game-type-local": "Single game",
   "game-type-manual": "Create network game",
   "game-type-master": "Join network game",
   "game-type-menu": "Raspydarts",
   "left": "Left",
   "miscellaneous": "Miscellaneous (Favorites, settings...)",
   "music-player": "MP3 player",
   "music-source": "Source of the tracks",
   "no": "No",
   "online-accept": "Accept",
   "online-change-account": "Change account",
   "online-change-server": "Change server",
   "online-chat": "Players & chat",
   "online-create": "Create game",
   "online-invite": "Invite",
   "online-logout": "Log out",
   "online-quick": "Quick replies",
   "online-ready": "Ready to play",
   "online-refuse": "Decline",
   "online-title": "Network match",
   "online-write": "Write",
   "parameters": "Settings",
   "players-bank": "Name bank",
   "players-names": "Players names",
   "players-names-subtitle": "Press + to add, - to remove, / for computer player, * for player color, <Tab> to shuffle",
   "raspy2dmd": "DMD Display (Raspy2DMD)",
   "realy-stop": "Do you really want to quit?",
   "reset": "Reset",
   "restart": "Play again",
   "right": "Right",
   "save": "Save",
   "setup": "Setup",
   "setup-buttons": "Buttons and toys setup",
   "setup-cam": "Camera setup",
   "setup-couleurs-segments": "Original segment colors setup",
   "setup-leds": "LED assignment",
   "setup-pinsleds": "LEDs setup",
   "test-buttons": "Buttons test",
   "test-target": "Target test",
   "test-toys": "Toys test",
   "trophees": "Trophies and progress",
   "up": "Up",
   "usb-pads": "USB buttons, knobs and gamepads setup",
   "yes": "Yes"
  },
  "de": {
   "animations": "LED-Animationen",
   "back": "Zurück",
   "back-to-desktop": "Zurück zum Desktop",
   "backups": "Sicherungsverwaltung",
   "btn_update": "Nach Updates suchen",
   "button-leds": "Tasten-LEDs",
   "coins": "Münzprüfer",
   "continue": "Weiter",
   "customization": "Spielanpassung",
   "dmd-backup-menu": "Sicherungen",
   "dmd-bestwin": "Möge der Bessere gewinnen!",
   "dmd-game-choice": "Spieleauswahl",
   "dmd-game-classic": "Klassische Spiele",
   "dmd-game-favorites": "Favorisierte Spiele",
   "dmd-game-fun": "Fun-Spiele",
   "dmd-game-sport": "Sportspiele",
   "dmd-player-bank": "Spielerbank",
   "dmd-player-choice": "Spielerauswahl",
   "dmd-player-favorites": "Favorisierte Spieler",
   "dmd-server-favorites": "Favorisierte Server",
   "down": "Unten",
   "edit-screens": "Bildschirme bearbeiten",
   "exhibition": "Ausstellungsmodus",
   "exit": "Beenden",
   "favorite": "Favorit",
   "favorite-add-game": "Zu Favoriten hinzufügen",
   "favorite-add-options": "Neuer Favorit mit Optionen",
   "favorite-add-plain": "Neuer Favorit ohne Optionen",
   "favorite-ask": "Beim Start auswählen",
   "favorite-choose": "Aus Spielerliste wählen",
   "favorite-count": "Spieleranzahl für Favorit",
   "favorite-define-options": "Optionen festlegen?",
   "favorite-edit-options": "Optionen bearbeiten",
   "favorite-edit-players": "Spieler bearbeiten",
   "favorite-empty": "leer",
   "favorite-exists": "Favorit existiert bereits",
   "favorite-generic": "Spieler 1, Spieler 2...",
   "favorite-last": "Zuletzt gewählte Spieler",
   "favorite-no-options": "Keine Optionen: Werden bei jedem Start gewählt",
   "favorite-not-saved": "Favorit konnte nicht gespeichert werden",
   "favorite-numbered": "Als nummerierten Favoriten speichern?",
   "favorite-numbered-remove": "Diesen Favoriten löschen",
   "favorite-numbered-sub": "Favorit 1 bis 9: erscheint nur im Hauptmenü, wenn in Menüdatei konfiguriert (favorite:fav1…)",
   "favorite-options-legend": "Opt.: vordefinierte Optionen ohne Optionsbildschirm",
   "favorite-options-mark": "Opt.",
   "favorite-options-title": "Favoriten-Optionen",
   "favorite-pick-sub": "Favorisierte Spieler und Namenbank",
   "favorite-place-button": "Verknüpfungstaste im Hauptmenü hinzufügen?",
   "favorite-player": "Spieler",
   "favorite-players": "Favorisierte Spieler",
   "favorite-players-sub": "Mit welchen Spielern starten?",
   "favorite-remove": "Aus Favoriten entfernen",
   "favorite-removed": "Favorit {number} gelöscht",
   "favorite-replace": "Favorit ersetzen",
   "favorite-save": "Als Favorit speichern",
   "favorite-save-sub": "Favoritennummer wählen (bestehender erfordert Bestätigung zum Überschreiben)",
   "favorite-saved": "Favorit {number} gespeichert",
   "favorite-to-button": "Zum Hauptmenü-Button hinzufügen",
   "favorite-too-few": "Es fehlen Spieler. Fortfahren?",
   "favorite-too-many": "Überschüssige Spieler werden entfernt. Fortfahren?",
   "favorite-with-options": "mit Optionen",
   "favorite-without-options": "ohne Optionen",
   "favorites-games": "Favorisierte Spiele",
   "favorites-players": "Favorisierte Spieler",
   "favorites-servers": "Favorisierte Server",
   "gallery": "Galerie",
   "game-cat": "Spielkategorie",
   "game-list": "Spieleauswahl",
   "game-options": "Spieloptionen",
   "game-type": "Spiel",
   "game-type-local": "Einzelspiel",
   "game-type-manual": "Netzwerkspiel erstellen",
   "game-type-master": "Netzwerkspiel beitreten",
   "game-type-menu": "Raspydarts",
   "left": "Verbleibend",
   "miscellaneous": "Verschiedenes (Favoriten, Einstellungen...)",
   "music-player": "MP3-Player",
   "music-source": "Quelle der Titel",
   "no": "Nein",
   "online-accept": "Annehmen",
   "online-change-account": "Konto wechseln",
   "online-change-server": "Server wechseln",
   "online-chat": "Spieler und Chat",
   "online-create": "Spiel erstellen",
   "online-invite": "Einladen",
   "online-logout": "Abmelden",
   "online-quick": "Schnellantworten",
   "online-ready": "Bereit zum Spielen",
   "online-refuse": "Ablehnen",
   "online-title": "Netzwerkspiel",
   "online-write": "Schreiben",
   "parameters": "Parameter",
   "players-bank": "Namenbank",
   "players-names": "Spielernamen",
   "players-names-subtitle": "Drücken Sie + zum Hinzufügen, - zum Entfernen, / für KI-Spieler, * für Spielerfarbe, <Tab> zum Mischen",
   "raspy2dmd": "DMD-Bildschirm (Raspy2DMD)",
   "realy-stop": "Möchten Sie wirklich beenden?",
   "reset": "Zurücksetzen",
   "restart": "Nochmal spielen",
   "right": "Rechts",
   "save": "Speichern",
   "setup": "Einrichtung",
   "setup-buttons": "Tasten- und Toy-Konfiguration",
   "setup-cam": "Kamerakonfiguration",
   "setup-couleurs-segments": "Konfiguration der Original-Segmentfarben",
   "setup-leds": "LED-Zuweisung",
   "setup-pinsleds": "LED-Konfiguration",
   "test-buttons": "Tastentest",
   "test-target": "Board-Test",
   "test-toys": "Toy-Test",
   "trophees": "Trophäen und Fortschritt",
   "up": "Oben",
   "usb-pads": "USB-Tasten-, Drehregler- und Gamepad-Konfiguration",
   "yes": "Ja"
  },
  "es": {
   "animations": "Animaciones LED",
   "back": "Atrás",
   "back-to-desktop": "Volver al escritorio",
   "backups": "Gestión de copias de seguridad",
   "btn_update": "Comprobar actualizaciones",
   "button-leds": "LED de los botones",
   "coins": "Monedero",
   "continue": "Continuar",
   "customization": "Personalización del juego",
   "dmd-backup-menu": "Copias de seguridad",
   "dmd-bestwin": "¡Que gane el mejor!",
   "dmd-game-choice": "Selección de juego",
   "dmd-game-classic": "Juegos clásicos",
   "dmd-game-favorites": "Juegos favoritos",
   "dmd-game-fun": "Juegos divertidos",
   "dmd-game-sport": "Juegos de deportes",
   "dmd-player-bank": "Banco de jugadores",
   "dmd-player-choice": "Selección de jugadores",
   "dmd-player-favorites": "Jugadores favoritos",
   "dmd-server-favorites": "Servidores favoritos",
   "down": "Abajo",
   "edit-screens": "Editar pantallas",
   "exhibition": "Modo exposición",
   "exit": "Salir",
   "favorite": "Favorito",
   "favorite-add-game": "Añadir a favoritos",
   "favorite-add-options": "Nuevo favorito con opciones",
   "favorite-add-plain": "Nuevo favorito sin opciones",
   "favorite-ask": "Seleccionar al iniciar",
   "favorite-choose": "Elegir de la lista de jugadores",
   "favorite-count": "Número de jugadores para favorito",
   "favorite-define-options": "¿definir opciones?",
   "favorite-edit-options": "Editar opciones",
   "favorite-edit-players": "Editar jugadores",
   "favorite-empty": "vacío",
   "favorite-exists": "El favorito ya existe",
   "favorite-generic": "Jugador 1, Jugador 2...",
   "favorite-last": "Últimos jugadores seleccionados",
   "favorite-no-options": "Sin opciones: se seleccionan en cada inicio",
   "favorite-not-saved": "El favorito no pudo guardarse",
   "favorite-numbered": "¿Guardar como favorito numerado?",
   "favorite-numbered-remove": "Eliminar este favorito",
   "favorite-numbered-sub": "Favorito 1 a 9: aparece en el menú principal solo si se configura en el archivo de menú (favorite:fav1…)",
   "favorite-options-legend": "Opt. : opciones predefinidas sin pantalla de opciones",
   "favorite-options-mark": "Opt.",
   "favorite-options-title": "Opciones de favorito",
   "favorite-pick-sub": "Jugadores favoritos y banco de nombres",
   "favorite-place-button": "¿Añadir botón de acceso directo al menú principal?",
   "favorite-player": "Jugador",
   "favorite-players": "Jugadores favoritos",
   "favorite-players-sub": "¿Con qué jugadores iniciar?",
   "favorite-remove": "Eliminar de favoritos",
   "favorite-removed": "Favorito {number} eliminado",
   "favorite-replace": "Reemplazar favorito",
   "favorite-save": "Guardar como favorito",
   "favorite-save-sub": "Elija el número de favorito (el favorito existente requiere confirmación para sobrescribir)",
   "favorite-saved": "Favorito {number} guardado",
   "favorite-to-button": "Añadir al botón del menú principal",
   "favorite-too-few": "Faltan jugadores. ¿Continuar?",
   "favorite-too-many": "Se eliminarán los jugadores sobrantes. ¿Continuar?",
   "favorite-with-options": "con opciones",
   "favorite-without-options": "sin opciones",
   "favorites-games": "Juegos favoritos",
   "favorites-players": "Jugadores favoritos",
   "favorites-servers": "Servidores favoritos",
   "gallery": "Galería",
   "game-cat": "Categoría de juego",
   "game-list": "Selección de juego",
   "game-options": "Opciones de juego",
   "game-type": "Juego",
   "game-type-local": "Partida individual",
   "game-type-manual": "Crear partida en red",
   "game-type-master": "Unirse a partida en red",
   "game-type-menu": "Raspydarts",
   "left": "Quedan",
   "miscellaneous": "Varios (Favoritos, ajustes...)",
   "music-player": "Reproductor MP3",
   "music-source": "Fuente de las canciones",
   "no": "No",
   "online-accept": "Aceptar",
   "online-change-account": "Cambiar cuenta",
   "online-change-server": "Cambiar servidor",
   "online-chat": "Jugadores y chat",
   "online-create": "Crear partida",
   "online-invite": "Invitar",
   "online-logout": "Cerrar sesión",
   "online-quick": "Respuestas rápidas",
   "online-ready": "Listo para jugar",
   "online-refuse": "Rechazar",
   "online-title": "Partida en red",
   "online-write": "Escribir",
   "parameters": "Parámetros",
   "players-bank": "Banco de nombres",
   "players-names": "Nombres de los jugadores",
   "players-names-subtitle": "Pulse + para añadir, - para eliminar, / para jugador IA, * para el color del jugador, <Tab> para mezclar",
   "raspy2dmd": "Pantalla DMD (Raspy2DMD)",
   "realy-stop": "¿Realmente desea salir?",
   "reset": "Restablecer",
   "restart": "Jugar de nuevo",
   "right": "Derecha",
   "save": "Guardar",
   "setup": "Configuración",
   "setup-buttons": "Configuración de botones y toys",
   "setup-cam": "Configuración de cámara",
   "setup-couleurs-segments": "Configuración de colores originales de segmentos",
   "setup-leds": "Asignación de LEDs",
   "setup-pinsleds": "Configuración de LEDs",
   "test-buttons": "Prueba de botones",
   "test-target": "Prueba de diana",
   "test-toys": "Prueba de toys",
   "trophees": "Trofeos y progreso",
   "up": "Arriba",
   "usb-pads": "Configuración de botones, mandos y gamepads USB",
   "yes": "Sí"
  },
  "it": {
   "animations": "Animazioni LED",
   "back": "Indietro",
   "back-to-desktop": "Torna al desktop",
   "backups": "Gestione backup",
   "btn_update": "Cerca aggiornamenti",
   "button-leds": "LED dei pulsanti",
   "coins": "Gettoniera",
   "continue": "Continua",
   "customization": "Personalizzazione del gioco",
   "dmd-backup-menu": "Salvataggi",
   "dmd-bestwin": "Che vinca il migliore!",
   "dmd-game-choice": "Scelta del gioco",
   "dmd-game-classic": "Giochi classici",
   "dmd-game-favorites": "Giochi preferiti",
   "dmd-game-fun": "Giochi divertenti",
   "dmd-game-sport": "Giochi sportivi",
   "dmd-player-bank": "Banca dei giocatori",
   "dmd-player-choice": "Scelta dei giocatori",
   "dmd-player-favorites": "Giocatori preferiti",
   "dmd-server-favorites": "Server preferiti",
   "down": "Giù",
   "edit-screens": "Modifica schermi",
   "exhibition": "Modalità esposizione",
   "exit": "Esci",
   "favorite": "Preferito",
   "favorite-add-game": "Aggiungi ai preferiti",
   "favorite-add-options": "Nuovo preferito con opzioni",
   "favorite-add-plain": "Nuovo preferito senza opzioni",
   "favorite-ask": "Scegli all'avvio",
   "favorite-choose": "Scegli dalla lista giocatori",
   "favorite-count": "Numero di giocatori per il preferito",
   "favorite-define-options": "Definire le opzioni?",
   "favorite-edit-options": "Modifica opzioni",
   "favorite-edit-players": "Modifica giocatori",
   "favorite-empty": "vuoto",
   "favorite-exists": "Il preferito esiste già",
   "favorite-generic": "Giocatore 1, Giocatore 2...",
   "favorite-last": "Ultimi giocatori scelti",
   "favorite-no-options": "Nessuna opzione: scelte a ogni avvio",
   "favorite-not-saved": "Impossibile salvare il preferito",
   "favorite-numbered": "Salva come preferito numerato?",
   "favorite-numbered-remove": "Elimina questo preferito",
   "favorite-numbered-sub": "Preferito da 1 a 9: appare nel menu principale solo se configurato nel file di menu (favorite:fav1…)",
   "favorite-options-legend": "Opt.: opzioni predefinite senza schermata opzioni",
   "favorite-options-mark": "Opt.",
   "favorite-options-title": "Opzioni preferito",
   "favorite-pick-sub": "Giocatori preferiti e banca dei nomi",
   "favorite-place-button": "Aggiungere un collegamento nel menu principale?",
   "favorite-player": "Giocatore",
   "favorite-players": "Giocatori preferiti",
   "favorite-players-sub": "Con quali giocatori iniziare?",
   "favorite-remove": "Rimuovi dai preferiti",
   "favorite-removed": "Preferito {number} eliminato",
   "favorite-replace": "Sostituisci preferito",
   "favorite-save": "Salva come preferito",
   "favorite-save-sub": "Scegli il numero del preferito (quelli esistenti richiedono conferma per essere sovrascritti)",
   "favorite-saved": "Preferito {number} salvato",
   "favorite-to-button": "Aggiungi al pulsante del menu principale",
   "favorite-too-few": "Mancano dei giocatori. Continuare?",
   "favorite-too-many": "I giocatori in eccesso verranno rimossi. Continuare?",
   "favorite-with-options": "con opzioni",
   "favorite-without-options": "senza opzioni",
   "favorites-games": "Giochi preferiti",
   "favorites-players": "Giocatori preferiti",
   "favorites-servers": "Server preferiti",
   "gallery": "Galleria",
   "game-cat": "Categoria di gioco",
   "game-list": "Elenco giochi",
   "game-options": "Opzioni di gioco",
   "game-type": "Gioco",
   "game-type-local": "Partita singola",
   "game-type-manual": "Crea una partita di rete",
   "game-type-master": "Unisciti a una partita di rete",
   "game-type-menu": "Raspydarts",
   "left": "Rimasti",
   "miscellaneous": "Varie (Preferiti, impostazioni...)",
   "music-player": "Lettore MP3",
   "music-source": "Sorgente dei brani",
   "no": "No",
   "online-accept": "Accetta",
   "online-change-account": "Cambia account",
   "online-change-server": "Cambia server",
   "online-chat": "Giocatori e chat",
   "online-create": "Crea partita",
   "online-invite": "Invita",
   "online-logout": "Disconnetti",
   "online-quick": "Risposte rapide",
   "online-ready": "Pronto per giocare",
   "online-refuse": "Rifiuta",
   "online-title": "Partita di rete",
   "online-write": "Scrivi",
   "parameters": "Parametri",
   "players-bank": "Banca dei nomi",
   "players-names": "Nomi dei giocatori",
   "players-names-subtitle": "Premi + per aggiungere, - per rimuovere, / per IA, * per il colore del giocatore, <Tab> per mescolare",
   "raspy2dmd": "Schermo DMD (Raspy2DMD)",
   "realy-stop": "Vuoi davvero uscire?",
   "reset": "Ripristina",
   "restart": "Rigica",
   "right": "Destra",
   "save": "Salva",
   "setup": "Impostazioni",
   "setup-buttons": "Configurazione pulsanti e toys",
   "setup-cam": "Configurazione telecamera",
   "setup-couleurs-segments": "Configurazione colori originali dei segmenti",
   "setup-leds": "Assegnazione LED",
   "setup-pinsleds": "Configurazione LED",
   "test-buttons": "Test dei pulsanti",
   "test-target": "Test del bersaglio",
   "test-toys": "Test dei toys",
   "trophees": "Trofei e progressi",
   "up": "Su",
   "usb-pads": "Configurazione pulsanti, manopole e gamepad USB",
   "yes": "Sì"
  }
 },
 "styleDefaults": {
  "shape": "rounded",
  "radius": 0.25,
  "background": {
   "color": "menu-buttons",
   "image": null,
   "fit": "stretch",
   "position": "center",
   "offset": [
    0,
    0
   ],
   "size": [
    1.0,
    1.0
   ],
   "opacity": 1.0,
   "slice": 12
  },
  "border": {
   "width": 0,
   "color": "menu-border"
  },
  "shadow": false,
  "text": {
   "font": null,
   "size": "4.5%",
   "color": "menu-text",
   "align": "center",
   "position": "center",
   "offset": [
    0,
    0
   ],
   "shadow": false,
   "bold": false
  },
  "icon": {
   "position": "left",
   "size": 0.7,
   "fit": "contain"
  },
  "selected": {
   "background": {
    "color": "menu-selected"
   },
   "text": {
    "color": "menu-text-white"
   }
  },
  "disabled": {
   "background": {
    "color": "#808080"
   },
   "text": {
    "color": "#C0C0C0"
   }
  },
  "pressed": {
   "scale": 0.96
  }
 },
 "layoutDefaults": {
  "list": {
   "area": {
    "x": "25%",
    "y": "18%",
    "width": "50%",
    "height": "72%"
   },
   "columns": 1,
   "button_size": {
    "width": 1.0,
    "height": "9%"
   }
  },
  "grid": {
   "area": {
    "x": "10%",
    "y": "18%",
    "width": "80%",
    "height": "72%"
   },
   "columns": 3,
   "button_size": {
    "width": 1.0,
    "height": "9%"
   }
  },
  "tiles": {
   "area": {
    "x": "10%",
    "y": "18%",
    "width": "80%",
    "height": "72%"
   },
   "columns": 3,
   "button_size": {
    "width": 1.0,
    "height": null
   }
  }
 },
 "gapDefault": {
  "x": "2%",
  "y": "1.5%"
 }
};
