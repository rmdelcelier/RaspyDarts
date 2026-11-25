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
      "id": "autodarts",
      "action": "autodarts",
      "text": "autodarts",
      "shortcut": "F12",
      "place_free": true
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
  "autodarts",
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
  "netresume",
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
   "Fiesta",
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
    "main-sub-menu-text-position": [
     0,
     0,
     0,
     0
    ],
    "main-sub-menu-text-valign": "Center",
    "parametrage-menu-shortcuts": "",
    "parametrage-menu-text-align": "Left",
    "parametrage-menu-text-position": [
     0,
     0,
     0,
     0
    ],
    "parametrage-menu-text-valign": "Center",
    "players-menu-shortcuts": "",
    "players-menu-text-align": "Left",
    "players-menu-text-position": [
     0,
     0,
     0,
     0
    ],
    "players-menu-text-valign": "Center",
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
    "main-sub-menu-text-position": [
     0,
     0,
     0,
     0
    ],
    "main-sub-menu-text-valign": "Center",
    "parametrage-menu-shortcuts": null,
    "parametrage-menu-text-align": "Center",
    "parametrage-menu-text-position": [
     0,
     0,
     0,
     0
    ],
    "parametrage-menu-text-valign": "Center",
    "players-menu-shortcuts": null,
    "players-menu-text-align": "Center",
    "players-menu-text-position": [
     0,
     0,
     0,
     0
    ],
    "players-menu-text-valign": "Center",
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
   "images/logos_menu/Fiesta.png": "assets/img/official/images/logos_menu/Fiesta.webp",
   "images/logos_menu/Fiesta_0.png": "assets/img/official/images/logos_menu/Fiesta_0.webp",
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
   "images/logos_menu/Fiesta.png": "assets/img/sombre/images/logos_menu/Fiesta.webp",
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
   "autodarts": "Autodarts",
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
   "dmd-gif": "GIF des coups",
   "dmd-gif-N": "Non",
   "dmd-gif-O": "Oui",
   "dmd-gif-short-N": "sans GIF",
   "dmd-gif-short-O": "avec GIF",
   "dmd-inherit-general": "Comme pour tous les jeux",
   "dmd-inherit-type": "Comme le type",
   "dmd-player-bank": "Banque de joueurs",
   "dmd-player-choice": "Choix des joueurs",
   "dmd-player-favorites": "Joueurs favoris",
   "dmd-score": "Affichage du score",
   "dmd-score-by-game": "Par type et par jeu",
   "dmd-score-general": "Pour tous les jeux",
   "dmd-score-try": "Essayer l'affichage du score",
   "dmd-score-trying": "Essai envoyé à l'afficheur",
   "dmd-score-whole-classic": "Tous les jeux classiques",
   "dmd-score-whole-fun": "Tous les jeux fun",
   "dmd-score-whole-sport": "Tous les jeux sport",
   "dmd-server-favorites": "Serveurs favoris",
   "dmd-style": "Style du score",
   "dmd-style-camera": "Caméra grand écran",
   "dmd-style-cards": "Les cartes",
   "dmd-style-classic": "Classique",
   "dmd-style-drum": "Le tambour",
   "dmd-style-duck": "Chasse aux canards",
   "dmd-style-ducks": "Tir aux canards",
   "dmd-style-help-camera": "Comme Moderne, avec une grande fenêtre de caméra : elle cherche puis filme en gros plan le segment touché. Le tableau est à droite.",
   "dmd-style-help-cards": "Des cartes à jouer révèlent le segment (une carte par multiplicateur), puis une grande carte ; une carte se retourne sur « MISS ».",
   "dmd-style-help-classic": "L'affichage habituel des trois fléchettes, sans fond pendant la partie.",
   "dmd-style-help-drum": "Une baguette frappe le tambour une fois par multiplicateur, la peau s'illumine ; sur un tir manqué, elle frappe le bord.",
   "dmd-style-help-duck": "Un chien de chasse sort des herbes avec le segment touché, et se moque d'un tir manqué. Pendant la partie, fond : ciel de nuit, arbres et herbes.",
   "dmd-style-help-ducks": "Le même stand, avec des canards jaunes qui basculent quand ils sont touchés ; sur un tir manqué, le rideau se déchire.",
   "dmd-style-help-modern": "Une caméra filme la cible : zoom sur le segment touché, la cible explose sur un tir manqué. Pendant la partie, fond : mur de briques et cible.",
   "dmd-style-help-pipes": "Un stand de fête foraine : les pipes éclatent (une par multiplicateur, une rafale pour le bull) ; sur un tir manqué, le rideau se déchire.",
   "dmd-style-help-random": "Un style animé tiré au hasard au début de chaque partie, pour varier l'affichage. Les jeux qui ont leur propre style (Balltrap) le gardent.",
   "dmd-style-help-ringboy": "Le même ring de boxe, avec un ring boy qui présente le segment ; projecteurs et confettis pour le bull, éponge jetée et huées sur un tir manqué. Un nouveau ring boy à chaque joueur.",
   "dmd-style-help-ringgirl": "Un ring de boxe la nuit : une ring girl entre avec un panneau où est écrit le segment, puis il s'affiche en grand ; projecteurs et confettis pour le bull, éponge jetée et huées sur un tir manqué. Une nouvelle ring girl à chaque joueur.",
   "dmd-style-help-shuriken": "Des shurikens se plantent dans des planches (un par multiplicateur, des kunaïs pour le bull) ; sur un tir manqué, ils rebondissent.",
   "dmd-style-help-skater": "Un skateur bombe le segment sur un mur de briques ; sur un tir manqué, il tombe sur un caillou.",
   "dmd-style-help-wave": "Une vague d'estampe japonaise se retire et découvre le segment ; sur un tir manqué, le soleil explose. Pendant la partie : nuages et pétales de cerisier.",
   "dmd-style-modern": "Moderne",
   "dmd-style-pipes": "Tir aux pipes",
   "dmd-style-random": "Aléatoire à chaque partie",
   "dmd-style-ringboy": "Ring boy",
   "dmd-style-ringgirl": "Ring girl",
   "dmd-style-shuriken": "Le shuriken",
   "dmd-style-skater": "Le skateur",
   "dmd-style-wave": "La vague",
   "dmd-version-needed": "Moderne et Chasse aux canards : Raspy2DMD 1.6.2.3 ou plus",
   "dmd-version-needed-1624": "Ce style : Raspy2DMD 1.6.2.4 ou plus",
   "dmd-version-old": "Moderne et Chasse aux canards : Raspy2DMD 1.6.2.3 ou plus (installé : {}) ; le score reste en Classique",
   "dmd-version-old-1624": "Ce style : Raspy2DMD 1.6.2.4 ou plus (installé : {}) ; il est remplacé par Moderne",
   "dmd-wait": "En attente pendant la partie",
   "dmd-wait-N": "Scène du style",
   "dmd-wait-O": "Animation habituelle",
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
   "theme-align-center": "Au centre",
   "theme-align-left": "À gauche",
   "theme-align-right": "À droite",
   "theme-back": "Retour",
   "theme-blue": "Bleu",
   "theme-cancel": "Annuler",
   "theme-create": "Créer un thème…",
   "theme-create-bad": "Nom de thème : lettres, chiffres, espaces, - et _ ({most} caractères au plus)",
   "theme-create-copying": "Copie du thème…",
   "theme-create-done": "Thème {name} créé à partir de {theme}",
   "theme-create-exists": "Ce nom est déjà pris par un thème de la borne",
   "theme-create-failed": "Le thème n'a pas pu être créé ou supprimé (voir le journal)",
   "theme-create-name": "Nom du nouveau thème (copie de {theme})",
   "theme-create-space": "Pas assez de place sur la carte ({size} Mo à copier)",
   "theme-customize": "Personnaliser le thème",
   "theme-delete": "Supprimer un thème",
   "theme-delete-done": "Thème {name} supprimé",
   "theme-delete-explain": "Ses fichiers (menus, couleurs, images, sons, vidéos) seront effacés de la borne",
   "theme-delete-none": "Aucun thème à supprimer (le thème utilisé reste)",
   "theme-delete-question": "Supprimer le thème {name} ?",
   "theme-export": "Exporter le thème",
   "theme-export-home": "Sur la borne (Dossier personnel > Exports)",
   "theme-export-media": "Inclure les vidéos et les sons du thème ({size} Mo) ?",
   "theme-export-media-explain": "Non : un fichier bien plus léger (couleurs, menus, images et police)",
   "theme-export-none": "Ce thème n'a pas de dossier à exporter",
   "theme-export-readonly": "Impossible d'écrire dans ce dossier",
   "theme-export-running": "Un export est déjà en cours",
   "theme-export-started": "Export du thème en tâche de fond, vers :",
   "theme-export-to-folder": "Vers un dossier ou une clé USB",
   "theme-export-to-raspyhub": "Vers RaspyHub",
   "theme-export-where": "Exporter le thème : où ?",
   "theme-export-where-hint": "Ouvrez le dossier voulu (une clé USB…), puis « Choisir ce dossier »",
   "theme-fine": "Réglage fin",
   "theme-green": "Vert",
   "theme-group-games": "Jeux",
   "theme-group-general": "Général",
   "theme-group-menus": "Menus",
   "theme-help": "Clic ou flèches : une balise · Clic ou Entrée : changer sa couleur · Échap : les panneaux (* : couleur choisie)",
   "theme-import": "Importer un thème",
   "theme-import-copying": "Copie du thème…",
   "theme-import-exists": "Le thème {theme} existe déjà. Le remplacer ?",
   "theme-import-exists-explain": "Oui : l'ancien est gardé à côté · Non : le nouveau prend un autre nom",
   "theme-import-failed": "Import impossible (voir le journal)",
   "theme-import-folder": "Importer un dossier",
   "theme-import-hint": "Un fichier .zip, ou un dossier ouvert puis « Choisir ce dossier »",
   "theme-import-not-theme": "Ce n'est pas un thème : aucun fichier Colorset.cfg",
   "theme-import-raspyhub": "Télécharger depuis RaspyHub",
   "theme-import-reading": "Lecture du thème…",
   "theme-import-use": "Thème {theme} importé. L'utiliser maintenant ?",
   "theme-import-zip": "Importer un dossier zippé (.zip)",
   "theme-keyboard-mouse": "Molette ou flèches : choisir - Valider : ouvrir ou changer - Appui long ou Échap : retour",
   "theme-none": "Aucune",
   "theme-origin": "Couleur d'origine du thème",
   "theme-origin-value": "Valeur d'origine du thème",
   "theme-plate-bob27": "Bob's 27",
   "theme-plate-borders": "Bordures et arrondis",
   "theme-plate-description": "Description d'un jeu",
   "theme-plate-fighters": "Fighters / Punch-Out",
   "theme-plate-game": "Écran de jeu",
   "theme-plate-games": "Couleurs utilisées par certains jeux",
   "theme-plate-menus": "Écran principal",
   "theme-plate-messages": "Messages",
   "theme-plate-players": "Couleurs des joueurs",
   "theme-plate-settings": "Listes de réglages et messages d'état",
   "theme-plate-shortcuts": "Raccourcis et alignement des textes",
   "theme-position-bottom": "Marge en bas",
   "theme-position-left": "Marge à gauche",
   "theme-position-right": "Marge à droite",
   "theme-position-set": "Définir la position…",
   "theme-position-title": "Position du texte dans son emplacement",
   "theme-position-top": "Marge en haut",
   "theme-red": "Rouge",
   "theme-round-max": "Maximum (pilule)",
   "theme-save-question": "Enregistrer le thème ?",
   "theme-shortcut-keys": "Touches F1, F2…",
   "theme-shortcut-none": "Aucun raccourci",
   "theme-transparent": "Transparente",
   "theme-valign-bottom": "En bas",
   "theme-valign-top": "En haut",
   "theme-value": "Valeur…",
   "trophees": "Trophées et progression",
   "up": "Haut",
   "usb-pads": "Paramétrage boutons, molettes et manettes USB",
   "yes": "Oui"
  },
  "en": {
   "animations": "LED Animations",
   "autodarts": "Autodarts",
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
   "dmd-gif": "GIF of the strokes",
   "dmd-gif-N": "No",
   "dmd-gif-O": "Yes",
   "dmd-gif-short-N": "without GIF",
   "dmd-gif-short-O": "with GIF",
   "dmd-inherit-general": "As for every game",
   "dmd-inherit-type": "As the type",
   "dmd-player-bank": "Player bank",
   "dmd-player-choice": "Player choice",
   "dmd-player-favorites": "Favorite players",
   "dmd-score": "Display of the score",
   "dmd-score-by-game": "By type and by game",
   "dmd-score-general": "For every game",
   "dmd-score-try": "Try the display of the score",
   "dmd-score-trying": "Try sent to the display",
   "dmd-score-whole-classic": "All the classic games",
   "dmd-score-whole-fun": "All the fun games",
   "dmd-score-whole-sport": "All the sport games",
   "dmd-server-favorites": "Favorite servers",
   "dmd-style": "Style of the score",
   "dmd-style-camera": "Large camera",
   "dmd-style-cards": "The cards",
   "dmd-style-classic": "Classic",
   "dmd-style-drum": "The drum",
   "dmd-style-duck": "Duck hunting",
   "dmd-style-ducks": "Duck shooting",
   "dmd-style-help-camera": "Like Modern, with a large camera window: it searches, then films the segment hit in close-up. The scoreboard is on the right.",
   "dmd-style-help-cards": "Playing cards reveal the segment (one card per multiplier), then a large card; a card turns over on \"MISS\".",
   "dmd-style-help-classic": "The usual display of the three darts, no background during the game.",
   "dmd-style-help-drum": "A stick hits the drum once per multiplier and the skin lights up; on a miss, it hits the rim.",
   "dmd-style-help-duck": "A hunting dog comes out of the grass with the segment hit, and laughs at a missed dart. During the game, background: night sky, trees and grass.",
   "dmd-style-help-ducks": "The same stall, with yellow ducks that tip over when hit; on a miss, the curtain tears.",
   "dmd-style-help-modern": "A camera films the board: zoom on the segment hit, the board explodes on a missed dart. During the game, background: brick wall and board.",
   "dmd-style-help-pipes": "A fairground stall: pipes burst (one per multiplier, a burst of fire for the bull); on a miss, the curtain tears.",
   "dmd-style-help-random": "An animated style drawn at random at the start of each game, for variety. Games with their own style (Balltrap) keep it.",
   "dmd-style-help-ringboy": "The same boxing ring, with a ring boy showing the segment; spotlights and confetti for the bull, the towel is thrown and the crowd boos on a miss. A new ring boy for each player.",
   "dmd-style-help-ringgirl": "A boxing ring at night: a ring girl walks in holding a card with the segment, then it is shown in large; spotlights and confetti for the bull, the towel is thrown and the crowd boos on a miss. A new ring girl for each player.",
   "dmd-style-help-shuriken": "Shurikens stick into planks (one per multiplier, kunais for the bull); on a miss, they bounce off.",
   "dmd-style-help-skater": "A skater sprays the segment on a brick wall; on a miss, he trips on a stone.",
   "dmd-style-help-wave": "A Japanese print wave pulls back to reveal the segment; on a miss, the sun explodes. During the game: clouds and cherry petals.",
   "dmd-style-modern": "Modern",
   "dmd-style-pipes": "Pipe shooting",
   "dmd-style-random": "Random each game",
   "dmd-style-ringboy": "Ring boy",
   "dmd-style-ringgirl": "Ring girl",
   "dmd-style-shuriken": "The shuriken",
   "dmd-style-skater": "The skater",
   "dmd-style-wave": "The wave",
   "dmd-version-needed": "Modern and Duck hunting: Raspy2DMD 1.6.2.3 or later",
   "dmd-version-needed-1624": "This style: Raspy2DMD 1.6.2.4 or later",
   "dmd-version-old": "Modern and Duck hunting: Raspy2DMD 1.6.2.3 or later (installed: {}); the score stays Classic",
   "dmd-version-old-1624": "This style: Raspy2DMD 1.6.2.4 or later (installed: {}); Modern is used instead",
   "dmd-wait": "Waiting during the game",
   "dmd-wait-N": "Scene of the style",
   "dmd-wait-O": "Usual animation",
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
   "theme-align-center": "Centre",
   "theme-align-left": "Left",
   "theme-align-right": "Right",
   "theme-back": "Back",
   "theme-blue": "Blue",
   "theme-cancel": "Cancel",
   "theme-create": "Create a theme…",
   "theme-create-bad": "Theme name: letters, digits, spaces, - and _ ({most} characters at most)",
   "theme-create-copying": "Copying the theme…",
   "theme-create-done": "Theme {name} created from {theme}",
   "theme-create-exists": "This name is already used by a theme of the cabinet",
   "theme-create-failed": "The theme could not be created or deleted (see the log)",
   "theme-create-name": "Name of the new theme (copy of {theme})",
   "theme-create-space": "Not enough room on the card ({size} MB to copy)",
   "theme-customize": "Customise the theme",
   "theme-delete": "Delete a theme",
   "theme-delete-done": "Theme {name} deleted",
   "theme-delete-explain": "Its files (menus, colours, images, sounds, videos) will be erased from the cabinet",
   "theme-delete-none": "No theme to delete (the theme in use stays)",
   "theme-delete-question": "Delete the theme {name}?",
   "theme-export": "Export the theme",
   "theme-export-home": "On the cabinet (Home folder > Exports)",
   "theme-export-media": "Include the videos and sounds of the theme ({size} MB)?",
   "theme-export-media-explain": "No: a much lighter file (colours, menus, images and font)",
   "theme-export-none": "This theme has no folder to export",
   "theme-export-readonly": "This folder cannot be written",
   "theme-export-running": "An export is already running",
   "theme-export-started": "Exporting the theme in the background, to:",
   "theme-export-to-folder": "To a folder or a USB key",
   "theme-export-to-raspyhub": "To RaspyHub",
   "theme-export-where": "Export the theme: where?",
   "theme-export-where-hint": "Open the folder wanted (a USB key…), then « Choose this folder »",
   "theme-fine": "Fine setting",
   "theme-green": "Green",
   "theme-group-games": "Games",
   "theme-group-general": "General",
   "theme-group-menus": "Menus",
   "theme-help": "Click or arrows: a tag · Click or Enter: change its colour · Escape: the panels (*: colour chosen)",
   "theme-import": "Import a theme",
   "theme-import-copying": "Copying the theme…",
   "theme-import-exists": "Theme {theme} already exists. Replace it?",
   "theme-import-exists-explain": "Yes: the old one is kept aside · No: the new one gets another name",
   "theme-import-failed": "Import failed (see the log)",
   "theme-import-folder": "Import a folder",
   "theme-import-hint": "A .zip file, or a folder opened then « Choose this folder »",
   "theme-import-not-theme": "Not a theme: no Colorset.cfg file",
   "theme-import-raspyhub": "Download from RaspyHub",
   "theme-import-reading": "Reading the theme…",
   "theme-import-use": "Theme {theme} imported. Use it now?",
   "theme-import-zip": "Import a zipped folder (.zip)",
   "theme-keyboard-mouse": "Knob or arrows: choose - Validate: open or change - Long press or Esc: back",
   "theme-none": "None",
   "theme-origin": "Colour of the theme",
   "theme-origin-value": "Value of the theme",
   "theme-plate-bob27": "Bob's 27",
   "theme-plate-borders": "Borders and rounding",
   "theme-plate-description": "Description of a game",
   "theme-plate-fighters": "Fighters / Punch-Out",
   "theme-plate-game": "Game screen",
   "theme-plate-games": "Colours used by some games",
   "theme-plate-menus": "Main screen",
   "theme-plate-messages": "Messages",
   "theme-plate-players": "Colours of the players",
   "theme-plate-settings": "Lists of settings and state messages",
   "theme-plate-shortcuts": "Shortcuts and alignment of the texts",
   "theme-position-bottom": "Bottom margin",
   "theme-position-left": "Left margin",
   "theme-position-right": "Right margin",
   "theme-position-set": "Set the position…",
   "theme-position-title": "Position of the text in its place",
   "theme-position-top": "Top margin",
   "theme-red": "Red",
   "theme-round-max": "Maximum (pill)",
   "theme-save-question": "Save the theme?",
   "theme-shortcut-keys": "Keys F1, F2…",
   "theme-shortcut-none": "No shortcut",
   "theme-transparent": "Transparent",
   "theme-valign-bottom": "Bottom",
   "theme-valign-top": "Top",
   "theme-value": "Value…",
   "trophees": "Trophies and progress",
   "up": "Up",
   "usb-pads": "USB buttons, knobs and gamepads setup",
   "yes": "Yes"
  },
  "de": {
   "animations": "LED-Animationen",
   "autodarts": "Autodarts",
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
   "dmd-gif": "GIF der Würfe",
   "dmd-gif-N": "Nein",
   "dmd-gif-O": "Ja",
   "dmd-gif-short-N": "ohne GIF",
   "dmd-gif-short-O": "mit GIF",
   "dmd-inherit-general": "Wie für alle Spiele",
   "dmd-inherit-type": "Wie der Typ",
   "dmd-player-bank": "Spielerbank",
   "dmd-player-choice": "Spielerauswahl",
   "dmd-player-favorites": "Favorisierte Spieler",
   "dmd-score": "Anzeige der Punkte",
   "dmd-score-by-game": "Nach Typ und Spiel",
   "dmd-score-general": "Für alle Spiele",
   "dmd-score-try": "Anzeige der Punkte testen",
   "dmd-score-trying": "Test an die Anzeige gesendet",
   "dmd-score-whole-classic": "Alle klassischen Spiele",
   "dmd-score-whole-fun": "Alle Fun-Spiele",
   "dmd-score-whole-sport": "Alle Sportspiele",
   "dmd-server-favorites": "Favorisierte Server",
   "dmd-style": "Stil der Punkte",
   "dmd-style-camera": "Große Kamera",
   "dmd-style-cards": "Die Karten",
   "dmd-style-classic": "Klassisch",
   "dmd-style-drum": "Die Trommel",
   "dmd-style-duck": "Entenjagd",
   "dmd-style-ducks": "Entenschießen",
   "dmd-style-help-camera": "Wie Modern, mit großem Kamerafenster: Sie sucht und filmt das getroffene Segment in Nahaufnahme. Die Tabelle steht rechts.",
   "dmd-style-help-cards": "Spielkarten zeigen das Segment (eine Karte pro Multiplikator), dann eine große Karte; eine Karte dreht sich auf „MISS“.",
   "dmd-style-help-classic": "Die übliche Anzeige der drei Darts, ohne Hintergrund während des Spiels.",
   "dmd-style-help-drum": "Ein Schlegel schlägt die Trommel einmal pro Multiplikator, das Fell leuchtet auf; bei einem Fehlwurf trifft er den Rand.",
   "dmd-style-help-duck": "Ein Jagdhund kommt mit dem getroffenen Segment aus dem Gras und lacht über einen Fehlwurf. Während des Spiels Hintergrund: Nachthimmel, Bäume und Gras.",
   "dmd-style-help-ducks": "Derselbe Stand mit gelben Enten, die umkippen, wenn sie getroffen werden; bei einem Fehlwurf reißt der Vorhang.",
   "dmd-style-help-modern": "Eine Kamera filmt die Scheibe: Zoom auf das getroffene Segment, die Scheibe explodiert bei einem Fehlwurf. Während des Spiels Hintergrund: Ziegelmauer und Scheibe.",
   "dmd-style-help-pipes": "Ein Jahrmarktstand: Pfeifen zerplatzen (eine pro Multiplikator, eine Salve für das Bull); bei einem Fehlwurf reißt der Vorhang.",
   "dmd-style-help-random": "Zu Beginn jedes Spiels wird ein animierter Stil zufällig gewählt, für Abwechslung. Spiele mit eigenem Stil (Balltrap) behalten ihn.",
   "dmd-style-help-ringboy": "Derselbe Boxring mit einem Ringboy, der das Segment zeigt; Scheinwerfer und Konfetti für das Bull, bei einem Fehlwurf fliegt das Handtuch und das Publikum buht. Für jeden Spieler ein neuer Ringboy.",
   "dmd-style-help-ringgirl": "Ein Boxring bei Nacht: Ein Ringgirl kommt mit einem Schild, auf dem das Segment steht, dann erscheint es groß; Scheinwerfer und Konfetti für das Bull, bei einem Fehlwurf fliegt das Handtuch und das Publikum buht. Für jeden Spieler ein neues Ringgirl.",
   "dmd-style-help-shuriken": "Shuriken bleiben in Brettern stecken (einer pro Multiplikator, Kunais für das Bull); bei einem Fehlwurf prallen sie ab.",
   "dmd-style-help-skater": "Ein Skater sprüht das Segment auf eine Ziegelmauer; bei einem Fehlwurf stolpert er über einen Stein.",
   "dmd-style-help-wave": "Eine Welle im Stil japanischer Holzschnitte zieht sich zurück und zeigt das Segment; bei einem Fehlwurf explodiert die Sonne. Während des Spiels: Wolken und Kirschblüten.",
   "dmd-style-modern": "Modern",
   "dmd-style-pipes": "Pfeifenschießen",
   "dmd-style-random": "Zufällig je Spiel",
   "dmd-style-ringboy": "Ringboy",
   "dmd-style-ringgirl": "Ringgirl",
   "dmd-style-shuriken": "Der Shuriken",
   "dmd-style-skater": "Der Skater",
   "dmd-style-wave": "Die Welle",
   "dmd-version-needed": "Modern und Entenjagd: Raspy2DMD 1.6.2.3 oder neuer",
   "dmd-version-needed-1624": "Dieser Stil: Raspy2DMD 1.6.2.4 oder neuer",
   "dmd-version-old": "Modern und Entenjagd: Raspy2DMD 1.6.2.3 oder neuer (installiert: {}); die Punkte bleiben klassisch",
   "dmd-version-old-1624": "Dieser Stil: Raspy2DMD 1.6.2.4 oder neuer (installiert: {}); stattdessen Modern",
   "dmd-wait": "Warten während des Spiels",
   "dmd-wait-N": "Szene des Stils",
   "dmd-wait-O": "Übliche Animation",
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
   "theme-align-center": "Mitte",
   "theme-align-left": "Links",
   "theme-align-right": "Rechts",
   "theme-back": "Zurück",
   "theme-blue": "Blau",
   "theme-cancel": "Abbrechen",
   "theme-create": "Thema erstellen…",
   "theme-create-bad": "Themenname: Buchstaben, Ziffern, Leerzeichen, - und _ (höchstens {most} Zeichen)",
   "theme-create-copying": "Thema wird kopiert…",
   "theme-create-done": "Thema {name} aus {theme} erstellt",
   "theme-create-exists": "Dieser Name wird schon von einem Thema des Automaten verwendet",
   "theme-create-failed": "Das Thema konnte nicht erstellt oder gelöscht werden (siehe Protokoll)",
   "theme-create-name": "Name des neuen Themas (Kopie von {theme})",
   "theme-create-space": "Nicht genug Platz auf der Karte ({size} MB zu kopieren)",
   "theme-customize": "Thema anpassen",
   "theme-delete": "Thema löschen",
   "theme-delete-done": "Thema {name} gelöscht",
   "theme-delete-explain": "Seine Dateien (Menüs, Farben, Bilder, Töne, Videos) werden vom Automaten gelöscht",
   "theme-delete-none": "Kein Thema zum Löschen (das verwendete Thema bleibt)",
   "theme-delete-question": "Das Thema {name} löschen?",
   "theme-export": "Thema exportieren",
   "theme-export-home": "Auf dem Automaten (Persönlicher Ordner > Exports)",
   "theme-export-media": "Videos und Töne des Themas einschließen ({size} MB)?",
   "theme-export-media-explain": "Nein: eine viel kleinere Datei (Farben, Menüs, Bilder und Schrift)",
   "theme-export-none": "Dieses Thema hat keinen Ordner zum Exportieren",
   "theme-export-readonly": "In diesen Ordner kann nicht geschrieben werden",
   "theme-export-running": "Ein Export läuft bereits",
   "theme-export-started": "Thema wird im Hintergrund exportiert, nach:",
   "theme-export-to-folder": "In einen Ordner oder auf einen USB-Stick",
   "theme-export-to-raspyhub": "Zu RaspyHub",
   "theme-export-where": "Thema exportieren: wohin?",
   "theme-export-where-hint": "Öffnen Sie den gewünschten Ordner (USB-Stick…), dann « Diesen Ordner wählen »",
   "theme-fine": "Feineinstellung",
   "theme-green": "Grün",
   "theme-group-games": "Spiele",
   "theme-group-general": "Allgemein",
   "theme-group-menus": "Menüs",
   "theme-help": "Klick oder Pfeile: ein Tag · Klick oder Eingabe: Farbe ändern · Esc: die Tafeln (*: gewählte Farbe)",
   "theme-import": "Thema importieren",
   "theme-import-copying": "Thema wird kopiert…",
   "theme-import-exists": "Das Thema {theme} existiert bereits. Ersetzen?",
   "theme-import-exists-explain": "Ja: das alte wird aufbewahrt · Nein: das neue bekommt einen anderen Namen",
   "theme-import-failed": "Import fehlgeschlagen (siehe Protokoll)",
   "theme-import-folder": "Ordner importieren",
   "theme-import-hint": "Eine .zip-Datei, oder einen Ordner öffnen und dann « Diesen Ordner wählen »",
   "theme-import-not-theme": "Kein Thema: keine Datei Colorset.cfg",
   "theme-import-raspyhub": "Von RaspyHub herunterladen",
   "theme-import-reading": "Thema wird gelesen…",
   "theme-import-use": "Thema {theme} importiert. Jetzt verwenden?",
   "theme-import-zip": "Gezippten Ordner importieren (.zip)",
   "theme-keyboard-mouse": "Drehknopf oder Pfeile: wählen - Bestätigen: öffnen oder ändern - Lang drücken oder Esc: zurück",
   "theme-none": "Keine",
   "theme-origin": "Farbe des Themas",
   "theme-origin-value": "Wert des Themas",
   "theme-plate-bob27": "Bob's 27",
   "theme-plate-borders": "Rahmen und Rundungen",
   "theme-plate-description": "Spielbeschreibung",
   "theme-plate-fighters": "Fighters / Punch-Out",
   "theme-plate-game": "Spielbildschirm",
   "theme-plate-games": "Von manchen Spielen verwendete Farben",
   "theme-plate-menus": "Hauptbildschirm",
   "theme-plate-messages": "Meldungen",
   "theme-plate-players": "Spielerfarben",
   "theme-plate-settings": "Einstellungslisten und Statusmeldungen",
   "theme-plate-shortcuts": "Tastenkürzel und Textausrichtung",
   "theme-position-bottom": "Rand unten",
   "theme-position-left": "Rand links",
   "theme-position-right": "Rand rechts",
   "theme-position-set": "Position festlegen…",
   "theme-position-title": "Position des Textes in seinem Feld",
   "theme-position-top": "Rand oben",
   "theme-red": "Rot",
   "theme-round-max": "Maximum (Pille)",
   "theme-save-question": "Thema speichern?",
   "theme-shortcut-keys": "Tasten F1, F2…",
   "theme-shortcut-none": "Kein Kürzel",
   "theme-transparent": "Transparent",
   "theme-valign-bottom": "Unten",
   "theme-valign-top": "Oben",
   "theme-value": "Wert…",
   "trophees": "Trophäen und Fortschritt",
   "up": "Oben",
   "usb-pads": "USB-Tasten-, Drehregler- und Gamepad-Konfiguration",
   "yes": "Ja"
  },
  "es": {
   "animations": "Animaciones LED",
   "autodarts": "Autodarts",
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
   "dmd-gif": "GIF de los tiros",
   "dmd-gif-N": "No",
   "dmd-gif-O": "Sí",
   "dmd-gif-short-N": "sin GIF",
   "dmd-gif-short-O": "con GIF",
   "dmd-inherit-general": "Como para todos los juegos",
   "dmd-inherit-type": "Como el tipo",
   "dmd-player-bank": "Banco de jugadores",
   "dmd-player-choice": "Selección de jugadores",
   "dmd-player-favorites": "Jugadores favoritos",
   "dmd-score": "Visualización de la puntuación",
   "dmd-score-by-game": "Por tipo y por juego",
   "dmd-score-general": "Para todos los juegos",
   "dmd-score-try": "Probar la visualización de la puntuación",
   "dmd-score-trying": "Prueba enviada a la pantalla",
   "dmd-score-whole-classic": "Todos los juegos clásicos",
   "dmd-score-whole-fun": "Todos los juegos fun",
   "dmd-score-whole-sport": "Todos los juegos de deporte",
   "dmd-server-favorites": "Servidores favoritos",
   "dmd-style": "Estilo de la puntuación",
   "dmd-style-camera": "Cámara grande",
   "dmd-style-cards": "Las cartas",
   "dmd-style-classic": "Clásico",
   "dmd-style-drum": "El tambor",
   "dmd-style-duck": "Caza de patos",
   "dmd-style-ducks": "Tiro a los patos",
   "dmd-style-help-camera": "Como Moderno, con una gran ventana de cámara: busca y filma en primer plano el segmento acertado. El marcador está a la derecha.",
   "dmd-style-help-cards": "Unas cartas revelan el segmento (una por multiplicador) y luego una carta grande; una carta se da la vuelta en «MISS».",
   "dmd-style-help-classic": "La visualización habitual de los tres dardos, sin fondo durante la partida.",
   "dmd-style-help-drum": "Una baqueta golpea el tambor una vez por multiplicador y el parche se ilumina; en un fallo, golpea el borde.",
   "dmd-style-help-duck": "Un perro de caza sale de la hierba con el segmento acertado y se burla de un tiro fallado. Durante la partida, fondo: cielo nocturno, árboles y hierba.",
   "dmd-style-help-ducks": "La misma caseta, con patos amarillos que caen hacia atrás al acertarles; en un fallo, la cortina se rasga.",
   "dmd-style-help-modern": "Una cámara filma la diana: zoom en el segmento acertado, la diana explota con un tiro fallado. Durante la partida, fondo: muro de ladrillos y diana.",
   "dmd-style-help-pipes": "Una caseta de feria: las pipas estallan (una por multiplicador, una ráfaga para el bull); en un fallo, la cortina se rasga.",
   "dmd-style-help-random": "Un estilo animado elegido al azar al empezar cada partida, para variar. Los juegos con estilo propio (Balltrap) lo conservan.",
   "dmd-style-help-ringboy": "El mismo ring de boxeo, con un ring boy que presenta el segmento; focos y confeti para el bull, se tira la toalla y el público abuchea en un fallo. Un ring boy nuevo para cada jugador.",
   "dmd-style-help-ringgirl": "Un ring de boxeo de noche: una ring girl entra con un cartel con el segmento, que luego aparece en grande; focos y confeti para el bull, se tira la toalla y el público abuchea en un fallo. Una ring girl nueva para cada jugador.",
   "dmd-style-help-shuriken": "Los shurikens se clavan en tablas (uno por multiplicador, kunais para el bull); en un fallo, rebotan.",
   "dmd-style-help-skater": "Un skater pinta el segmento con spray en un muro de ladrillos; en un fallo, tropieza con una piedra.",
   "dmd-style-help-wave": "Una ola de estampa japonesa se retira y descubre el segmento; en un fallo, el sol explota. Durante la partida: nubes y pétalos de cerezo.",
   "dmd-style-modern": "Moderno",
   "dmd-style-pipes": "Tiro a las pipas",
   "dmd-style-random": "Aleatorio en cada partida",
   "dmd-style-ringboy": "Ring boy",
   "dmd-style-ringgirl": "Ring girl",
   "dmd-style-shuriken": "El shuriken",
   "dmd-style-skater": "El skater",
   "dmd-style-wave": "La ola",
   "dmd-version-needed": "Moderno y Caza de patos: Raspy2DMD 1.6.2.3 o posterior",
   "dmd-version-needed-1624": "Este estilo: Raspy2DMD 1.6.2.4 o posterior",
   "dmd-version-old": "Moderno y Caza de patos: Raspy2DMD 1.6.2.3 o posterior (instalado: {}); la puntuación queda en Clásico",
   "dmd-version-old-1624": "Este estilo: Raspy2DMD 1.6.2.4 o posterior (instalado: {}); se usa Moderno",
   "dmd-wait": "En espera durante la partida",
   "dmd-wait-N": "Escena del estilo",
   "dmd-wait-O": "Animación habitual",
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
   "theme-align-center": "Al centro",
   "theme-align-left": "A la izquierda",
   "theme-align-right": "A la derecha",
   "theme-back": "Volver",
   "theme-blue": "Azul",
   "theme-cancel": "Cancelar",
   "theme-create": "Crear un tema…",
   "theme-create-bad": "Nombre del tema: letras, cifras, espacios, - y _ ({most} caracteres como máximo)",
   "theme-create-copying": "Copiando el tema…",
   "theme-create-done": "Tema {name} creado a partir de {theme}",
   "theme-create-exists": "Este nombre ya lo usa un tema de la máquina",
   "theme-create-failed": "No se ha podido crear o eliminar el tema (ver el registro)",
   "theme-create-name": "Nombre del nuevo tema (copia de {theme})",
   "theme-create-space": "No hay espacio suficiente en la tarjeta ({size} MB que copiar)",
   "theme-customize": "Personalizar el tema",
   "theme-delete": "Eliminar un tema",
   "theme-delete-done": "Tema {name} eliminado",
   "theme-delete-explain": "Sus archivos (menús, colores, imágenes, sonidos, vídeos) se borrarán de la máquina",
   "theme-delete-none": "Ningún tema que eliminar (el tema en uso se queda)",
   "theme-delete-question": "¿Eliminar el tema {name}?",
   "theme-export": "Exportar el tema",
   "theme-export-home": "En la máquina (Carpeta personal > Exports)",
   "theme-export-media": "¿Incluir los vídeos y sonidos del tema ({size} MB)?",
   "theme-export-media-explain": "No: un archivo mucho más ligero (colores, menús, imágenes y fuente)",
   "theme-export-none": "Este tema no tiene carpeta que exportar",
   "theme-export-readonly": "No se puede escribir en esta carpeta",
   "theme-export-running": "Ya hay una exportación en curso",
   "theme-export-started": "Exportando el tema en segundo plano, a:",
   "theme-export-to-folder": "A una carpeta o una memoria USB",
   "theme-export-to-raspyhub": "A RaspyHub",
   "theme-export-where": "Exportar el tema: ¿dónde?",
   "theme-export-where-hint": "Abra la carpeta deseada (una llave USB…), luego « Elegir esta carpeta »",
   "theme-fine": "Ajuste fino",
   "theme-green": "Verde",
   "theme-group-games": "Juegos",
   "theme-group-general": "General",
   "theme-group-menus": "Menús",
   "theme-help": "Clic o flechas: una etiqueta · Clic o Intro: cambiar su color · Esc: los paneles (*: color elegido)",
   "theme-import": "Importar un tema",
   "theme-import-copying": "Copiando el tema…",
   "theme-import-exists": "El tema {theme} ya existe. ¿Sustituirlo?",
   "theme-import-exists-explain": "Sí: el antiguo se guarda aparte · No: el nuevo recibe otro nombre",
   "theme-import-failed": "Importación imposible (ver el registro)",
   "theme-import-folder": "Importar una carpeta",
   "theme-import-hint": "Un archivo .zip, o una carpeta abierta y luego « Elegir esta carpeta »",
   "theme-import-not-theme": "No es un tema: ningún archivo Colorset.cfg",
   "theme-import-raspyhub": "Descargar desde RaspyHub",
   "theme-import-reading": "Leyendo el tema…",
   "theme-import-use": "Tema {theme} importado. ¿Usarlo ahora?",
   "theme-import-zip": "Importar una carpeta comprimida (.zip)",
   "theme-keyboard-mouse": "Rueda o flechas: elegir - Validar: abrir o cambiar - Pulsación larga o Esc: volver",
   "theme-none": "Ninguno",
   "theme-origin": "Color del tema",
   "theme-origin-value": "Valor del tema",
   "theme-plate-bob27": "Bob's 27",
   "theme-plate-borders": "Bordes y redondeos",
   "theme-plate-description": "Descripción de un juego",
   "theme-plate-fighters": "Fighters / Punch-Out",
   "theme-plate-game": "Pantalla de juego",
   "theme-plate-games": "Colores usados por algunos juegos",
   "theme-plate-menus": "Pantalla principal",
   "theme-plate-messages": "Mensajes",
   "theme-plate-players": "Colores de los jugadores",
   "theme-plate-settings": "Listas de ajustes y mensajes de estado",
   "theme-plate-shortcuts": "Atajos y alineación de los textos",
   "theme-position-bottom": "Margen inferior",
   "theme-position-left": "Margen izquierdo",
   "theme-position-right": "Margen derecho",
   "theme-position-set": "Definir la posición…",
   "theme-position-title": "Posición del texto en su espacio",
   "theme-position-top": "Margen superior",
   "theme-red": "Rojo",
   "theme-round-max": "Máximo (píldora)",
   "theme-save-question": "¿Guardar el tema?",
   "theme-shortcut-keys": "Teclas F1, F2…",
   "theme-shortcut-none": "Sin atajo",
   "theme-transparent": "Transparente",
   "theme-valign-bottom": "Abajo",
   "theme-valign-top": "Arriba",
   "theme-value": "Valor…",
   "trophees": "Trofeos y progreso",
   "up": "Arriba",
   "usb-pads": "Configuración de botones, mandos y gamepads USB",
   "yes": "Sí"
  },
  "it": {
   "animations": "Animazioni LED",
   "autodarts": "Autodarts",
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
   "dmd-gif": "GIF dei tiri",
   "dmd-gif-N": "No",
   "dmd-gif-O": "Sì",
   "dmd-gif-short-N": "senza GIF",
   "dmd-gif-short-O": "con GIF",
   "dmd-inherit-general": "Come per tutti i giochi",
   "dmd-inherit-type": "Come il tipo",
   "dmd-player-bank": "Banca dei giocatori",
   "dmd-player-choice": "Scelta dei giocatori",
   "dmd-player-favorites": "Giocatori preferiti",
   "dmd-score": "Visualizzazione del punteggio",
   "dmd-score-by-game": "Per tipo e per gioco",
   "dmd-score-general": "Per tutti i giochi",
   "dmd-score-try": "Provare la visualizzazione del punteggio",
   "dmd-score-trying": "Prova inviata al display",
   "dmd-score-whole-classic": "Tutti i giochi classici",
   "dmd-score-whole-fun": "Tutti i giochi fun",
   "dmd-score-whole-sport": "Tutti i giochi sport",
   "dmd-server-favorites": "Server preferiti",
   "dmd-style": "Stile del punteggio",
   "dmd-style-camera": "Telecamera grande",
   "dmd-style-cards": "Le carte",
   "dmd-style-classic": "Classico",
   "dmd-style-drum": "Il tamburo",
   "dmd-style-duck": "Caccia alle anatre",
   "dmd-style-ducks": "Tiro alle anatre",
   "dmd-style-help-camera": "Come Moderno, con una grande finestra della telecamera: cerca e riprende da vicino il segmento colpito. Il tabellone è a destra.",
   "dmd-style-help-cards": "Delle carte rivelano il segmento (una per moltiplicatore), poi una carta grande; una carta si gira su «MISS».",
   "dmd-style-help-classic": "La visualizzazione abituale delle tre freccette, senza sfondo durante la partita.",
   "dmd-style-help-drum": "Una bacchetta colpisce il tamburo una volta per moltiplicatore e la pelle si illumina; su un tiro mancato, colpisce il bordo.",
   "dmd-style-help-duck": "Un cane da caccia esce dall'erba con il segmento colpito e prende in giro un tiro mancato. Durante la partita, sfondo: cielo notturno, alberi ed erba.",
   "dmd-style-help-ducks": "Lo stesso baraccone, con anatre gialle che cadono all'indietro quando colpite; su un tiro mancato, la tenda si strappa.",
   "dmd-style-help-modern": "Una telecamera riprende il bersaglio: zoom sul segmento colpito, il bersaglio esplode su un tiro mancato. Durante la partita, sfondo: muro di mattoni e bersaglio.",
   "dmd-style-help-pipes": "Un baraccone da fiera: le pipe esplodono (una per moltiplicatore, una raffica per il bull); su un tiro mancato, la tenda si strappa.",
   "dmd-style-help-random": "Uno stile animato scelto a caso all'inizio di ogni partita, per variare. I giochi con uno stile proprio (Balltrap) lo mantengono.",
   "dmd-style-help-ringboy": "Lo stesso ring di pugilato, con un ring boy che presenta il segmento; riflettori e coriandoli per il bull, su un tiro mancato si getta la spugna e il pubblico fischia. Un nuovo ring boy per ogni giocatore.",
   "dmd-style-help-ringgirl": "Un ring di pugilato di notte: una ring girl entra con un cartello con il segmento, che poi appare in grande; riflettori e coriandoli per il bull, su un tiro mancato si getta la spugna e il pubblico fischia. Una nuova ring girl per ogni giocatore.",
   "dmd-style-help-shuriken": "Gli shuriken si piantano nelle assi (uno per moltiplicatore, kunai per il bull); su un tiro mancato, rimbalzano.",
   "dmd-style-help-skater": "Uno skater dipinge il segmento con la bomboletta su un muro di mattoni; su un tiro mancato, inciampa in un sasso.",
   "dmd-style-help-wave": "Un'onda da stampa giapponese si ritira e scopre il segmento; su un tiro mancato, il sole esplode. Durante la partita: nuvole e petali di ciliegio.",
   "dmd-style-modern": "Moderno",
   "dmd-style-pipes": "Tiro alle pipe",
   "dmd-style-random": "Casuale a ogni partita",
   "dmd-style-ringboy": "Ring boy",
   "dmd-style-ringgirl": "Ring girl",
   "dmd-style-shuriken": "Lo shuriken",
   "dmd-style-skater": "Lo skater",
   "dmd-style-wave": "L'onda",
   "dmd-version-needed": "Moderno e Caccia alle anatre: Raspy2DMD 1.6.2.3 o successivo",
   "dmd-version-needed-1624": "Questo stile: Raspy2DMD 1.6.2.4 o successivo",
   "dmd-version-old": "Moderno e Caccia alle anatre: Raspy2DMD 1.6.2.3 o successivo (installato: {}); il punteggio resta Classico",
   "dmd-version-old-1624": "Questo stile: Raspy2DMD 1.6.2.4 o successivo (installato: {}); al suo posto Moderno",
   "dmd-wait": "In attesa durante la partita",
   "dmd-wait-N": "Scena dello stile",
   "dmd-wait-O": "Animazione abituale",
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
   "theme-align-center": "Al centro",
   "theme-align-left": "A sinistra",
   "theme-align-right": "A destra",
   "theme-back": "Indietro",
   "theme-blue": "Blu",
   "theme-cancel": "Annulla",
   "theme-create": "Crea un tema…",
   "theme-create-bad": "Nome del tema: lettere, cifre, spazi, - e _ ({most} caratteri al massimo)",
   "theme-create-copying": "Copia del tema…",
   "theme-create-done": "Tema {name} creato a partire da {theme}",
   "theme-create-exists": "Questo nome è già usato da un tema della postazione",
   "theme-create-failed": "Impossibile creare o eliminare il tema (vedere il registro)",
   "theme-create-name": "Nome del nuovo tema (copia di {theme})",
   "theme-create-space": "Spazio insufficiente sulla scheda ({size} MB da copiare)",
   "theme-customize": "Personalizzare il tema",
   "theme-delete": "Elimina un tema",
   "theme-delete-done": "Tema {name} eliminato",
   "theme-delete-explain": "I suoi file (menu, colori, immagini, suoni, video) saranno cancellati dalla postazione",
   "theme-delete-none": "Nessun tema da eliminare (il tema in uso resta)",
   "theme-delete-question": "Eliminare il tema {name}?",
   "theme-export": "Esportare il tema",
   "theme-export-home": "Sulla macchina (Cartella personale > Exports)",
   "theme-export-media": "Includere i video e i suoni del tema ({size} MB)?",
   "theme-export-media-explain": "No: un file molto più leggero (colori, menu, immagini e font)",
   "theme-export-none": "Questo tema non ha una cartella da esportare",
   "theme-export-readonly": "Impossibile scrivere in questa cartella",
   "theme-export-running": "Un'esportazione è già in corso",
   "theme-export-started": "Esportazione del tema in background, verso:",
   "theme-export-to-folder": "In una cartella o una chiavetta USB",
   "theme-export-to-raspyhub": "Su RaspyHub",
   "theme-export-where": "Esportare il tema: dove?",
   "theme-export-where-hint": "Aprite la cartella voluta (una chiavetta USB…), poi « Scegliere questa cartella »",
   "theme-fine": "Regolazione fine",
   "theme-green": "Verde",
   "theme-group-games": "Giochi",
   "theme-group-general": "Generale",
   "theme-group-menus": "Menu",
   "theme-help": "Clic o frecce: un'etichetta · Clic o Invio: cambiare il colore · Esc: i pannelli (*: colore scelto)",
   "theme-import": "Importare un tema",
   "theme-import-copying": "Copia del tema…",
   "theme-import-exists": "Il tema {theme} esiste già. Sostituirlo?",
   "theme-import-exists-explain": "Sì: il vecchio viene conservato · No: il nuovo prende un altro nome",
   "theme-import-failed": "Importazione non riuscita (vedi il log)",
   "theme-import-folder": "Importare una cartella",
   "theme-import-hint": "Un file .zip, o una cartella aperta poi « Scegliere questa cartella »",
   "theme-import-not-theme": "Non è un tema: nessun file Colorset.cfg",
   "theme-import-raspyhub": "Scaricare da RaspyHub",
   "theme-import-reading": "Lettura del tema…",
   "theme-import-use": "Tema {theme} importato. Usarlo ora?",
   "theme-import-zip": "Importare una cartella compressa (.zip)",
   "theme-keyboard-mouse": "Manopola o frecce: scegliere - Convalida: aprire o cambiare - Pressione lunga o Esc: indietro",
   "theme-none": "Nessuno",
   "theme-origin": "Colore del tema",
   "theme-origin-value": "Valore del tema",
   "theme-plate-bob27": "Bob's 27",
   "theme-plate-borders": "Bordi e arrotondamenti",
   "theme-plate-description": "Descrizione di un gioco",
   "theme-plate-fighters": "Fighters / Punch-Out",
   "theme-plate-game": "Schermata di gioco",
   "theme-plate-games": "Colori usati da alcuni giochi",
   "theme-plate-menus": "Schermata principale",
   "theme-plate-messages": "Messaggi",
   "theme-plate-players": "Colori dei giocatori",
   "theme-plate-settings": "Elenchi di impostazioni e messaggi di stato",
   "theme-plate-shortcuts": "Scorciatoie e allineamento dei testi",
   "theme-position-bottom": "Margine inferiore",
   "theme-position-left": "Margine sinistro",
   "theme-position-right": "Margine destro",
   "theme-position-set": "Definire la posizione…",
   "theme-position-title": "Posizione del testo nel suo spazio",
   "theme-position-top": "Margine superiore",
   "theme-red": "Rosso",
   "theme-round-max": "Massimo (pillola)",
   "theme-save-question": "Salvare il tema?",
   "theme-shortcut-keys": "Tasti F1, F2…",
   "theme-shortcut-none": "Nessuna scorciatoia",
   "theme-transparent": "Trasparente",
   "theme-valign-bottom": "In basso",
   "theme-valign-top": "In alto",
   "theme-value": "Valore…",
   "trophees": "Trofei e progressi",
   "up": "Su",
   "usb-pads": "Configurazione pulsanti, manopole e gamepad USB",
   "yes": "Sì"
  },
  "nl": {
   "animations": "Led-animaties",
   "autodarts": "Autodarts",
   "back": "Terug",
   "back-to-desktop": "Terug naar bureaublad",
   "backups": "Back-upbeheer",
   "btn_update": "Controleren op updates",
   "button-leds": "Knop-leds",
   "coins": "Muntinworp",
   "continue": "Doorgaan",
   "customization": "Spelaanpassing",
   "dmd-backup-menu": "Back-ups",
   "dmd-bestwin": "Moge de beste winnen!",
   "dmd-game-choice": "Spelkeuze",
   "dmd-game-classic": "Klassieke spellen",
   "dmd-game-favorites": "Favoriete spellen",
   "dmd-game-fun": "Fun spellen",
   "dmd-game-sport": "Sportspellen",
   "dmd-gif": "GIF van de worpen",
   "dmd-gif-N": "Nee",
   "dmd-gif-O": "Ja",
   "dmd-gif-short-N": "zonder GIF",
   "dmd-gif-short-O": "met GIF",
   "dmd-inherit-general": "Zoals voor alle spellen",
   "dmd-inherit-type": "Zoals het type",
   "dmd-player-bank": "Spelersbank",
   "dmd-player-choice": "Spelerskeuze",
   "dmd-player-favorites": "Favoriete spelers",
   "dmd-score": "Weergave van de score",
   "dmd-score-by-game": "Per type en per spel",
   "dmd-score-general": "Voor alle spellen",
   "dmd-score-try": "Weergave van de score proberen",
   "dmd-score-trying": "Test naar het display gestuurd",
   "dmd-score-whole-classic": "Alle klassieke spellen",
   "dmd-score-whole-fun": "Alle fun-spellen",
   "dmd-score-whole-sport": "Alle sportspellen",
   "dmd-server-favorites": "Favoriete servers",
   "dmd-style": "Stijl van de score",
   "dmd-style-camera": "Grote camera",
   "dmd-style-cards": "De kaarten",
   "dmd-style-classic": "Klassiek",
   "dmd-style-drum": "De trommel",
   "dmd-style-duck": "Eendenjacht",
   "dmd-style-ducks": "Eendjes schieten",
   "dmd-style-help-camera": "Zoals Modern, met een groot camerabeeld: de camera zoekt en filmt het geraakte segment van dichtbij. Het scorebord staat rechts.",
   "dmd-style-help-cards": "Speelkaarten tonen het segment (één kaart per vermenigvuldiger), daarna een grote kaart; een kaart draait om op \"MISS\".",
   "dmd-style-help-classic": "De gewone weergave van de drie pijlen, zonder achtergrond tijdens het spel.",
   "dmd-style-help-drum": "Een stok slaat één keer per vermenigvuldiger op de trommel en het vel licht op; bij een misser raakt hij de rand.",
   "dmd-style-help-duck": "Een jachthond komt uit het gras met het geraakte segment en lacht om een misser. Tijdens het spel achtergrond: nachtelijke hemel, bomen en gras.",
   "dmd-style-help-ducks": "Dezelfde kraam, met gele eendjes die omkiepen als ze geraakt worden; bij een misser scheurt het gordijn.",
   "dmd-style-help-modern": "Een camera filmt het bord: zoom op het geraakte segment, het bord ontploft bij een misser. Tijdens het spel achtergrond: bakstenen muur en bord.",
   "dmd-style-help-pipes": "Een kermiskraam: pijpjes spatten uiteen (één per vermenigvuldiger, een salvo voor de bull); bij een misser scheurt het gordijn.",
   "dmd-style-help-random": "Aan het begin van elk spel wordt willekeurig een geanimeerde stijl gekozen, voor afwisseling. Spellen met een eigen stijl (Balltrap) houden die.",
   "dmd-style-help-ringboy": "Dezelfde boksring, met een ringboy die het segment toont; spots en confetti voor de bull, bij een misser wordt de handdoek gegooid en joelt het publiek. Een nieuwe ringboy voor elke speler.",
   "dmd-style-help-ringgirl": "Een boksring bij nacht: een ringgirl komt op met een bord waarop het segment staat, daarna verschijnt het groot; spots en confetti voor de bull, bij een misser wordt de handdoek gegooid en joelt het publiek. Een nieuw ringgirl voor elke speler.",
   "dmd-style-help-shuriken": "Shurikens blijven in planken steken (één per vermenigvuldiger, kunais voor de bull); bij een misser stuiteren ze terug.",
   "dmd-style-help-skater": "Een skater spuit het segment op een bakstenen muur; bij een misser struikelt hij over een steen.",
   "dmd-style-help-wave": "Een golf in Japanse prentstijl trekt zich terug en toont het segment; bij een misser ontploft de zon. Tijdens het spel: wolken en kersenbloesem.",
   "dmd-style-modern": "Modern",
   "dmd-style-pipes": "Pijpjes schieten",
   "dmd-style-random": "Willekeurig per spel",
   "dmd-style-ringboy": "Ringboy",
   "dmd-style-ringgirl": "Ringgirl",
   "dmd-style-shuriken": "De shuriken",
   "dmd-style-skater": "De skater",
   "dmd-style-wave": "De golf",
   "dmd-version-needed": "Modern en Eendenjacht: Raspy2DMD 1.6.2.3 of nieuwer",
   "dmd-version-needed-1624": "Deze stijl: Raspy2DMD 1.6.2.4 of nieuwer",
   "dmd-version-old": "Modern en Eendenjacht: Raspy2DMD 1.6.2.3 of nieuwer (geïnstalleerd: {}); de score blijft Klassiek",
   "dmd-version-old-1624": "Deze stijl: Raspy2DMD 1.6.2.4 of nieuwer (geïnstalleerd: {}); in plaats daarvan Modern",
   "dmd-wait": "Wachten tijdens het spel",
   "dmd-wait-N": "Scène van de stijl",
   "dmd-wait-O": "Gewone animatie",
   "down": "Omlaag",
   "edit-screens": "Schermen bewerken",
   "exhibition": "Tentoonstellingsmodus",
   "exit": "Afsluiten",
   "favorite": "Favoriet",
   "favorite-add-game": "Toevoegen aan favorieten",
   "favorite-add-options": "Nieuwe favoriet met opties",
   "favorite-add-plain": "Nieuwe favoriet zonder opties",
   "favorite-ask": "Kiezen bij opstarten",
   "favorite-choose": "Kiezen uit de spelerslijst",
   "favorite-count": "Aantal spelers van de favoriet",
   "favorite-define-options": "opties instellen?",
   "favorite-edit-options": "Opties bewerken",
   "favorite-edit-players": "Spelers bewerken",
   "favorite-empty": "leeg",
   "favorite-exists": "Deze favoriet bestaat al",
   "favorite-generic": "Speler 1, Speler 2…",
   "favorite-last": "Laatst gekozen spelers",
   "favorite-no-options": "Zonder opties: deze worden bij elke start gekozen",
   "favorite-not-saved": "Favoriet kon niet worden opgeslagen",
   "favorite-numbered": "Ook opslaan als genummerde favoriet?",
   "favorite-numbered-remove": "Deze favoriet verwijderen",
   "favorite-numbered-sub": "Favoriet 1 t/m 9: verschijnt alleen in het hoofdmenu als het menubestand er een knop voor heeft (favorite:fav1…)",
   "favorite-options-legend": "Opt.: ingestelde opties, zonder optiesscherm",
   "favorite-options-mark": "Opt.",
   "favorite-options-title": "Opties van favoriet",
   "favorite-pick-sub": "Favoriete spelers en namenbank",
   "favorite-place-button": "Ook op een knop in het hoofdmenu plaatsen?",
   "favorite-player": "Speler",
   "favorite-players": "Spelers van de favoriet",
   "favorite-players-sub": "Met welke spelers starten?",
   "favorite-remove": "Verwijderen uit favorieten",
   "favorite-removed": "Favoriet {number} verwijderd",
   "favorite-replace": "Favoriet vervangen",
   "favorite-save": "Opslaan als favoriet",
   "favorite-save-sub": "Kies het nummer (een al opgeslagen favoriet wordt pas na bevestiging vervangen)",
   "favorite-saved": "Favoriet {number} opgeslagen",
   "favorite-to-button": "Plaatsen op een knop in het hoofdmenu",
   "favorite-too-few": "Er ontbreken spelers. Doorgaan?",
   "favorite-too-many": "Overtollige spelers worden verwijderd. Doorgaan?",
   "favorite-with-options": "met opties",
   "favorite-without-options": "zonder opties",
   "favorites-games": "Favoriete spellen",
   "favorites-players": "Favoriete spelers",
   "favorites-servers": "Favoriete servers",
   "gallery": "Galerij",
   "game-cat": "Spelcategorie",
   "game-list": "Spelkeuze",
   "game-options": "Spelopties",
   "game-type": "Spel",
   "game-type-local": "Lokaal spel",
   "game-type-manual": "Netwerkspel aanmaken",
   "game-type-master": "Deelnemen aan netwerkspel",
   "game-type-menu": "Raspydarts",
   "left": "Resterend",
   "miscellaneous": "Diversen (Favorieten, instellingen,...)",
   "music-player": "MP3-speler",
   "music-source": "Bron van de nummers",
   "no": "Nee",
   "online-accept": "Accepteren",
   "online-change-account": "Van account veranderen",
   "online-change-server": "Van server veranderen",
   "online-chat": "Spelers en chat",
   "online-create": "Spel aanmaken",
   "online-invite": "Uitnodigen",
   "online-logout": "Afmelden",
   "online-quick": "Snelle antwoorden",
   "online-ready": "Klaar om te spelen",
   "online-refuse": "Weigeren",
   "online-title": "Netwerkspel",
   "online-write": "Schrijven",
   "parameters": "Parameters",
   "players-bank": "Namenbank",
   "players-names": "Namen spelers",
   "players-names-subtitle": "Druk op + om toe te voegen, - om te verwijderen, / voor computerspeler, * voor spelerkleur, <Tab> om te schudden",
   "raspy2dmd": "DMD-display (Raspy2DMD)",
   "realy-stop": "Weet u zeker dat u wilt afsluiten?",
   "reset": "Resetten",
   "restart": "Opnieuw spelen",
   "right": "Rechts",
   "save": "Opslaan",
   "setup": "Instellingen",
   "setup-buttons": "Knoppen- en toys-instellingen",
   "setup-cam": "Camerainstellingen",
   "setup-couleurs-segments": "Instellingen originele segmentkleur",
   "setup-leds": "Led-toewijzing",
   "setup-pinsleds": "Led-instellingen",
   "test-buttons": "Knoppentest",
   "test-target": "Bordtest",
   "test-toys": "Toystest",
   "theme-align-center": "Midden",
   "theme-align-left": "Links",
   "theme-align-right": "Rechts",
   "theme-back": "Terug",
   "theme-blue": "Blauw",
   "theme-cancel": "Annuleren",
   "theme-create": "Thema maken…",
   "theme-create-bad": "Themanaam: letters, cijfers, spaties, - en _ (hoogstens {most} tekens)",
   "theme-create-copying": "Thema wordt gekopieerd…",
   "theme-create-done": "Thema {name} gemaakt op basis van {theme}",
   "theme-create-exists": "Deze naam wordt al gebruikt door een thema van de kast",
   "theme-create-failed": "Het thema kon niet worden gemaakt of verwijderd (zie het logboek)",
   "theme-create-name": "Naam van het nieuwe thema (kopie van {theme})",
   "theme-create-space": "Niet genoeg ruimte op de kaart ({size} MB te kopiëren)",
   "theme-customize": "Thema aanpassen",
   "theme-delete": "Thema verwijderen",
   "theme-delete-done": "Thema {name} verwijderd",
   "theme-delete-explain": "De bestanden (menu's, kleuren, afbeeldingen, geluiden, video's) worden van de kast gewist",
   "theme-delete-none": "Geen thema om te verwijderen (het gebruikte thema blijft)",
   "theme-delete-question": "Het thema {name} verwijderen?",
   "theme-export": "Thema exporteren",
   "theme-export-home": "Op de kast (Persoonlijke map > Exports)",
   "theme-export-media": "Video's en geluiden van het thema meenemen ({size} MB)?",
   "theme-export-media-explain": "Nee: een veel lichter bestand (kleuren, menu's, afbeeldingen en lettertype)",
   "theme-export-none": "Dit thema heeft geen map om te exporteren",
   "theme-export-readonly": "Kan niet in deze map schrijven",
   "theme-export-running": "Er loopt al een export",
   "theme-export-started": "Thema wordt op de achtergrond geëxporteerd, naar:",
   "theme-export-to-folder": "Naar een map of een USB-stick",
   "theme-export-to-raspyhub": "Naar RaspyHub",
   "theme-export-where": "Thema exporteren: waar?",
   "theme-export-where-hint": "Open de gewenste map (een USB-stick…), dan « Deze map kiezen »",
   "theme-fine": "Fijnafstelling",
   "theme-green": "Groen",
   "theme-group-games": "Spellen",
   "theme-group-general": "Algemeen",
   "theme-group-menus": "Menu's",
   "theme-help": "Klik of pijlen: een label · Klik of Enter: kleur wijzigen · Esc: de panelen (*: gekozen kleur)",
   "theme-import": "Thema importeren",
   "theme-import-copying": "Thema wordt gekopieerd…",
   "theme-import-exists": "Thema {theme} bestaat al. Vervangen?",
   "theme-import-exists-explain": "Ja: het oude wordt bewaard · Nee: het nieuwe krijgt een andere naam",
   "theme-import-failed": "Importeren mislukt (zie het logboek)",
   "theme-import-folder": "Map importeren",
   "theme-import-hint": "Een .zip-bestand, of een geopende map en dan « Deze map kiezen »",
   "theme-import-not-theme": "Geen thema: geen bestand Colorset.cfg",
   "theme-import-raspyhub": "Downloaden van RaspyHub",
   "theme-import-reading": "Thema wordt gelezen…",
   "theme-import-use": "Thema {theme} geïmporteerd. Nu gebruiken?",
   "theme-import-zip": "Gezipte map importeren (.zip)",
   "theme-keyboard-mouse": "Draaiknop of pijlen: kiezen - Bevestigen: openen of wijzigen - Lang drukken of Esc: terug",
   "theme-none": "Geen",
   "theme-origin": "Kleur van het thema",
   "theme-origin-value": "Waarde van het thema",
   "theme-plate-bob27": "Bob's 27",
   "theme-plate-borders": "Randen en afrondingen",
   "theme-plate-description": "Beschrijving van een spel",
   "theme-plate-fighters": "Fighters / Punch-Out",
   "theme-plate-game": "Spelscherm",
   "theme-plate-games": "Kleuren die sommige spellen gebruiken",
   "theme-plate-menus": "Hoofdscherm",
   "theme-plate-messages": "Berichten",
   "theme-plate-players": "Kleuren van de spelers",
   "theme-plate-settings": "Instellingslijsten en statusberichten",
   "theme-plate-shortcuts": "Sneltoetsen en uitlijning van de teksten",
   "theme-position-bottom": "Marge onder",
   "theme-position-left": "Marge links",
   "theme-position-right": "Marge rechts",
   "theme-position-set": "Positie instellen…",
   "theme-position-title": "Positie van de tekst in zijn vak",
   "theme-position-top": "Marge boven",
   "theme-red": "Rood",
   "theme-round-max": "Maximaal (pil)",
   "theme-save-question": "Thema opslaan?",
   "theme-shortcut-keys": "Toetsen F1, F2…",
   "theme-shortcut-none": "Geen sneltoets",
   "theme-transparent": "Transparant",
   "theme-valign-bottom": "Onder",
   "theme-valign-top": "Boven",
   "theme-value": "Waarde…",
   "trophees": "Trofeeën en voortgang",
   "up": "Omhoog",
   "usb-pads": "Instellingen USB-knoppen, draaiknoppen en gamepads",
   "yes": "Ja"
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
 },
 "themeEditor": {
  "plates": [
   {
    "name": "theme-plate-menus",
    "tags": [
     "menu-header",
     "menu-text",
     "menu-shortcut",
     "menu-border",
     "menu-favorite",
     "menu-inactive",
     "menu-selected",
     "menu-text-white",
     "menu-buttons",
     "menu-text-black"
    ],
    "points": [
     [
      "menu-header",
      0.15,
      0.06
     ],
     [
      "menu-text",
      0.5,
      0.06
     ],
     [
      "menu-shortcut",
      0.24,
      0.23
     ],
     [
      "menu-border",
      0.2,
      0.28
     ],
     [
      "menu-favorite",
      0.55,
      0.71
     ],
     [
      "menu-inactive",
      0.85,
      0.87
     ],
     [
      "menu-selected",
      0.8,
      0.23
     ],
     [
      "menu-text-white",
      0.55,
      0.23
     ],
     [
      "menu-buttons",
      0.85,
      0.39
     ],
     [
      "menu-text-black",
      0.6,
      0.39
     ]
    ],
    "drawing": [
     {
      "op": "fill"
     },
     {
      "op": "box",
      "x": 0.0,
      "y": 0.02,
      "w": 1.0,
      "h": 0.08,
      "tag": "menu-header",
      "radius": 0.0
     },
     {
      "op": "text",
      "text": "Raspydarts",
      "x": 0.0,
      "y": 0.02,
      "w": 1.0,
      "h": 0.08,
      "tag": "menu-text",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.2,
      "y": 0.17,
      "w": 0.7,
      "h": 0.12,
      "tag": "menu-selected",
      "radius": 0.009,
      "border": "menu-border",
      "borderWidth": 0.0045
     },
     {
      "op": "box",
      "x": 0.2,
      "y": 0.17,
      "w": 0.0967,
      "h": 0.12,
      "tag": "menu-shortcut",
      "radius": 0.009
     },
     {
      "op": "text",
      "text": "F1",
      "x": 0.2,
      "y": 0.17,
      "w": 0.0967,
      "h": 0.12,
      "tag": "menu-text-white",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "Partie simple",
      "x": 0.2967,
      "y": 0.17,
      "w": 0.6033,
      "h": 0.12,
      "tag": "menu-text-white",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.2,
      "y": 0.33,
      "w": 0.7,
      "h": 0.12,
      "tag": "menu-buttons",
      "radius": 0.009
     },
     {
      "op": "box",
      "x": 0.2,
      "y": 0.33,
      "w": 0.0967,
      "h": 0.12,
      "tag": "menu-shortcut",
      "radius": 0.009
     },
     {
      "op": "text",
      "text": "F2",
      "x": 0.2,
      "y": 0.33,
      "w": 0.0967,
      "h": 0.12,
      "tag": "menu-text-white",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "Partie en réseau",
      "x": 0.2967,
      "y": 0.33,
      "w": 0.6033,
      "h": 0.12,
      "tag": "menu-text-black",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.2,
      "y": 0.49,
      "w": 0.7,
      "h": 0.12,
      "tag": "menu-buttons",
      "radius": 0.009
     },
     {
      "op": "box",
      "x": 0.2,
      "y": 0.49,
      "w": 0.0967,
      "h": 0.12,
      "tag": "menu-shortcut",
      "radius": 0.009
     },
     {
      "op": "text",
      "text": "F3",
      "x": 0.2,
      "y": 0.49,
      "w": 0.0967,
      "h": 0.12,
      "tag": "menu-text-white",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "Divers",
      "x": 0.2967,
      "y": 0.49,
      "w": 0.6033,
      "h": 0.12,
      "tag": "menu-text-black",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.2,
      "y": 0.65,
      "w": 0.7,
      "h": 0.12,
      "tag": "menu-buttons",
      "radius": 0.009
     },
     {
      "op": "box",
      "x": 0.2,
      "y": 0.65,
      "w": 0.0967,
      "h": 0.12,
      "tag": "menu-shortcut",
      "radius": 0.009
     },
     {
      "op": "text",
      "text": "F4",
      "x": 0.2,
      "y": 0.65,
      "w": 0.0967,
      "h": 0.12,
      "tag": "menu-text-white",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "Cricket (favori)",
      "x": 0.2967,
      "y": 0.65,
      "w": 0.6033,
      "h": 0.12,
      "tag": "menu-favorite",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.2,
      "y": 0.81,
      "w": 0.7,
      "h": 0.12,
      "tag": "menu-inactive",
      "radius": 0.009
     },
     {
      "op": "text",
      "text": "Revenir sur le bureau",
      "x": 0.2,
      "y": 0.81,
      "w": 0.7,
      "h": 0.12,
      "tag": "menu-text-black",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     }
    ]
   },
   {
    "name": "theme-plate-settings",
    "tags": [
     "menu-alternate",
     "menu-item-black",
     "menu-item-white",
     "menu-ok",
     "menu-warning",
     "menu-ko"
    ],
    "points": [
     [
      "menu-alternate",
      0.2,
      0.22
     ],
     [
      "menu-item-black",
      0.12,
      0.62
     ],
     [
      "menu-item-white",
      0.5,
      0.6
     ],
     [
      "menu-ok",
      0.8,
      0.82
     ],
     [
      "menu-warning",
      0.8,
      0.88
     ],
     [
      "menu-ko",
      0.8,
      0.94
     ]
    ],
    "drawing": [
     {
      "op": "fill"
     },
     {
      "op": "box",
      "x": 0.05,
      "y": 0.12,
      "w": 0.9,
      "h": 0.1,
      "tag": "menu-buttons",
      "radius": 0.009
     },
     {
      "op": "box",
      "x": 0.05,
      "y": 0.12,
      "w": 0.225,
      "h": 0.1,
      "tag": "menu-alternate",
      "radius": 0.009
     },
     {
      "op": "text",
      "text": "Oui",
      "x": 0.05,
      "y": 0.12,
      "w": 0.225,
      "h": 0.1,
      "tag": "menu-text-white",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "Afficher le segment touché",
      "x": 0.275,
      "y": 0.12,
      "w": 0.675,
      "h": 0.1,
      "tag": "menu-text-black",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.05,
      "y": 0.26,
      "w": 0.9,
      "h": 0.1,
      "tag": "menu-buttons",
      "radius": 0.009
     },
     {
      "op": "box",
      "x": 0.05,
      "y": 0.26,
      "w": 0.225,
      "h": 0.1,
      "tag": "menu-alternate",
      "radius": 0.009
     },
     {
      "op": "text",
      "text": "20",
      "x": 0.05,
      "y": 0.26,
      "w": 0.225,
      "h": 0.1,
      "tag": "menu-text-white",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "Nombre de tours",
      "x": 0.275,
      "y": 0.26,
      "w": 0.675,
      "h": 0.1,
      "tag": "menu-text-black",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.05,
      "y": 0.4,
      "w": 0.9,
      "h": 0.1,
      "tag": "menu-buttons",
      "radius": 0.009
     },
     {
      "op": "box",
      "x": 0.05,
      "y": 0.4,
      "w": 0.225,
      "h": 0.1,
      "tag": "menu-alternate",
      "radius": 0.009
     },
     {
      "op": "text",
      "text": "Non",
      "x": 0.05,
      "y": 0.4,
      "w": 0.225,
      "h": 0.1,
      "tag": "menu-text-white",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "Mode compétition",
      "x": 0.275,
      "y": 0.4,
      "w": 0.675,
      "h": 0.1,
      "tag": "menu-text-black",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.05,
      "y": 0.52,
      "w": 0.55,
      "h": 0.22,
      "tag": "menu-item-black",
      "radius": 0.009
     },
     {
      "op": "text",
      "text": "Nouveautés…",
      "x": 0.05,
      "y": 0.52,
      "w": 0.55,
      "h": 0.22,
      "tag": "menu-item-white",
      "size": 0.3,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.62,
      "y": 0.79,
      "w": 0.36,
      "h": 0.055,
      "tag": "menu-ok",
      "radius": 0.0045
     },
     {
      "op": "text",
      "text": "Enregistré",
      "x": 0.62,
      "y": 0.79,
      "w": 0.36,
      "h": 0.055,
      "tag": "menu-text-white",
      "size": 0.7,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.62,
      "y": 0.855,
      "w": 0.36,
      "h": 0.055,
      "tag": "menu-warning",
      "radius": 0.0045
     },
     {
      "op": "text",
      "text": "Attention",
      "x": 0.62,
      "y": 0.855,
      "w": 0.36,
      "h": 0.055,
      "tag": "menu-text-white",
      "size": 0.7,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.62,
      "y": 0.92,
      "w": 0.36,
      "h": 0.055,
      "tag": "menu-ko",
      "radius": 0.0045
     },
     {
      "op": "text",
      "text": "Erreur",
      "x": 0.62,
      "y": 0.92,
      "w": 0.36,
      "h": 0.055,
      "tag": "menu-text-white",
      "size": 0.7,
      "align": "center",
      "valign": "center"
     }
    ]
   },
   {
    "name": "theme-plate-description",
    "tags": [
     "description-bg",
     "description-game",
     "description-text"
    ],
    "points": [
     [
      "description-bg",
      0.62,
      0.7
     ],
     [
      "description-game",
      0.75,
      0.2
     ],
     [
      "description-text",
      0.75,
      0.42
     ]
    ],
    "drawing": [
     {
      "op": "fill"
     },
     {
      "op": "circle",
      "cx": 0.095,
      "cy": 0.205,
      "r": 0.055,
      "color": [
       180,
       30,
       30
      ]
     },
     {
      "op": "circle",
      "cx": 0.095,
      "cy": 0.205,
      "r": 0.0275,
      "color": [
       240,
       240,
       240
      ]
     },
     {
      "op": "circle",
      "cx": 0.225,
      "cy": 0.205,
      "r": 0.055,
      "color": [
       180,
       30,
       30
      ]
     },
     {
      "op": "circle",
      "cx": 0.225,
      "cy": 0.205,
      "r": 0.0275,
      "color": [
       240,
       240,
       240
      ]
     },
     {
      "op": "circle",
      "cx": 0.355,
      "cy": 0.205,
      "r": 0.055,
      "color": [
       180,
       30,
       30
      ]
     },
     {
      "op": "circle",
      "cx": 0.355,
      "cy": 0.205,
      "r": 0.0275,
      "color": [
       240,
       240,
       240
      ]
     },
     {
      "op": "circle",
      "cx": 0.095,
      "cy": 0.405,
      "r": 0.055,
      "color": [
       180,
       30,
       30
      ]
     },
     {
      "op": "circle",
      "cx": 0.095,
      "cy": 0.405,
      "r": 0.0275,
      "color": [
       240,
       240,
       240
      ]
     },
     {
      "op": "circle",
      "cx": 0.225,
      "cy": 0.405,
      "r": 0.055,
      "color": [
       180,
       30,
       30
      ]
     },
     {
      "op": "circle",
      "cx": 0.225,
      "cy": 0.405,
      "r": 0.0275,
      "color": [
       240,
       240,
       240
      ]
     },
     {
      "op": "circle",
      "cx": 0.355,
      "cy": 0.405,
      "r": 0.055,
      "color": [
       180,
       30,
       30
      ]
     },
     {
      "op": "circle",
      "cx": 0.355,
      "cy": 0.405,
      "r": 0.0275,
      "color": [
       240,
       240,
       240
      ]
     },
     {
      "op": "circle",
      "cx": 0.095,
      "cy": 0.605,
      "r": 0.055,
      "color": [
       180,
       30,
       30
      ]
     },
     {
      "op": "circle",
      "cx": 0.095,
      "cy": 0.605,
      "r": 0.0275,
      "color": [
       240,
       240,
       240
      ]
     },
     {
      "op": "circle",
      "cx": 0.225,
      "cy": 0.605,
      "r": 0.055,
      "color": [
       180,
       30,
       30
      ]
     },
     {
      "op": "circle",
      "cx": 0.225,
      "cy": 0.605,
      "r": 0.0275,
      "color": [
       240,
       240,
       240
      ]
     },
     {
      "op": "circle",
      "cx": 0.355,
      "cy": 0.605,
      "r": 0.055,
      "color": [
       180,
       30,
       30
      ]
     },
     {
      "op": "circle",
      "cx": 0.355,
      "cy": 0.605,
      "r": 0.0275,
      "color": [
       240,
       240,
       240
      ]
     },
     {
      "op": "circle",
      "cx": 0.095,
      "cy": 0.805,
      "r": 0.055,
      "color": [
       180,
       30,
       30
      ]
     },
     {
      "op": "circle",
      "cx": 0.095,
      "cy": 0.805,
      "r": 0.0275,
      "color": [
       240,
       240,
       240
      ]
     },
     {
      "op": "circle",
      "cx": 0.225,
      "cy": 0.805,
      "r": 0.055,
      "color": [
       180,
       30,
       30
      ]
     },
     {
      "op": "circle",
      "cx": 0.225,
      "cy": 0.805,
      "r": 0.0275,
      "color": [
       240,
       240,
       240
      ]
     },
     {
      "op": "circle",
      "cx": 0.355,
      "cy": 0.805,
      "r": 0.055,
      "color": [
       180,
       30,
       30
      ]
     },
     {
      "op": "circle",
      "cx": 0.355,
      "cy": 0.805,
      "r": 0.0275,
      "color": [
       240,
       240,
       240
      ]
     },
     {
      "op": "box",
      "x": 0.45,
      "y": 0.12,
      "w": 0.52,
      "h": 0.12,
      "tag": "description-bg",
      "radius": 0.018
     },
     {
      "op": "text",
      "text": "Cricket",
      "x": 0.45,
      "y": 0.12,
      "w": 0.52,
      "h": 0.12,
      "tag": "description-game",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.45,
      "y": 0.28,
      "w": 0.52,
      "h": 0.62,
      "tag": "description-bg",
      "radius": 0.0269
     },
     {
      "op": "text",
      "text": "Fermez les chiffres de 15 à 20…",
      "x": 0.47,
      "y": 0.32,
      "w": 0.48,
      "h": 0.06,
      "tag": "description-text",
      "size": 0.7,
      "align": "left",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "Fermez les chiffres de 15 à 20…",
      "x": 0.47,
      "y": 0.39,
      "w": 0.48,
      "h": 0.06,
      "tag": "description-text",
      "size": 0.7,
      "align": "left",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "Fermez les chiffres de 15 à 20…",
      "x": 0.47,
      "y": 0.46,
      "w": 0.48,
      "h": 0.06,
      "tag": "description-text",
      "size": 0.7,
      "align": "left",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "Fermez les chiffres de 15 à 20…",
      "x": 0.47,
      "y": 0.53,
      "w": 0.48,
      "h": 0.06,
      "tag": "description-text",
      "size": 0.7,
      "align": "left",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "Fermez les chiffres de 15 à 20…",
      "x": 0.47,
      "y": 0.6,
      "w": 0.48,
      "h": 0.06,
      "tag": "description-text",
      "size": 0.7,
      "align": "left",
      "valign": "center"
     }
    ]
   },
   {
    "name": "theme-plate-messages",
    "tags": [
     "message-bg",
     "message-text"
    ],
    "points": [
     [
      "message-bg",
      0.2,
      0.5
     ],
     [
      "message-text",
      0.6,
      0.5
     ]
    ],
    "drawing": [
     {
      "op": "fill"
     },
     {
      "op": "box",
      "x": 0.0,
      "y": 0.42,
      "w": 1.0,
      "h": 0.16,
      "tag": "message-bg",
      "radius": 0.0
     },
     {
      "op": "text",
      "text": "Retirez les fléchettes et appuyez sur « Joueur suivant »",
      "x": 0.0,
      "y": 0.42,
      "w": 1.0,
      "h": 0.16,
      "tag": "message-text",
      "size": 0.45,
      "align": "center",
      "valign": "center"
     }
    ]
   },
   {
    "name": "theme-plate-game",
    "tags": [
     "game-bg",
     "bg-round-nb-header",
     "bg-round-nb",
     "game-round",
     "bg-darts-nb-header",
     "bg-darts-nb",
     "game-darts",
     "game-type",
     "game-option",
     "game-headers",
     "game-alt-headers",
     "game-player",
     "game-player-name",
     "game-score",
     "game-inactive",
     "game-dead",
     "game-table",
     "game-text",
     "game-title1",
     "game-title2"
    ],
    "points": [
     [
      "game-bg",
      0.05,
      0.5
     ],
     [
      "bg-round-nb-header",
      0.12,
      0.08
     ],
     [
      "bg-round-nb",
      0.12,
      0.2
     ],
     [
      "game-round",
      0.12,
      0.2
     ],
     [
      "bg-darts-nb-header",
      0.12,
      0.36
     ],
     [
      "bg-darts-nb",
      0.12,
      0.47
     ],
     [
      "game-darts",
      0.12,
      0.47
     ],
     [
      "game-type",
      0.12,
      0.66
     ],
     [
      "game-option",
      0.12,
      0.74
     ],
     [
      "game-headers",
      0.6,
      0.06
     ],
     [
      "game-alt-headers",
      0.85,
      0.06
     ],
     [
      "game-player",
      0.85,
      0.2
     ],
     [
      "game-player-name",
      0.5,
      0.2
     ],
     [
      "game-score",
      0.95,
      0.2
     ],
     [
      "game-inactive",
      0.85,
      0.34
     ],
     [
      "game-dead",
      0.85,
      0.48
     ],
     [
      "game-table",
      0.6,
      0.66
     ],
     [
      "game-text",
      0.75,
      0.8
     ],
     [
      "game-title1",
      0.6,
      0.93
     ],
     [
      "game-title2",
      0.6,
      0.93
     ]
    ],
    "drawing": [
     {
      "op": "fill",
      "tag": "game-bg"
     },
     {
      "op": "box",
      "x": 0.02,
      "y": 0.03,
      "w": 0.2,
      "h": 0.08,
      "tag": "bg-round-nb-header",
      "radius": 0.006
     },
     {
      "op": "text",
      "text": "Round",
      "x": 0.02,
      "y": 0.03,
      "w": 0.2,
      "h": 0.08,
      "tag": "game-headers",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.02,
      "y": 0.12,
      "w": 0.2,
      "h": 0.16,
      "tag": "bg-round-nb",
      "radius": 0.006
     },
     {
      "op": "text",
      "text": "1 / 20",
      "x": 0.02,
      "y": 0.12,
      "w": 0.2,
      "h": 0.16,
      "tag": "game-round",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.02,
      "y": 0.32,
      "w": 0.2,
      "h": 0.08,
      "tag": "bg-darts-nb-header",
      "radius": 0.006
     },
     {
      "op": "text",
      "text": "Darts",
      "x": 0.02,
      "y": 0.32,
      "w": 0.2,
      "h": 0.08,
      "tag": "game-headers",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.02,
      "y": 0.41,
      "w": 0.2,
      "h": 0.12,
      "tag": "bg-darts-nb",
      "radius": 0.006
     },
     {
      "op": "text",
      "text": "3",
      "x": 0.02,
      "y": 0.41,
      "w": 0.2,
      "h": 0.12,
      "tag": "game-darts",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "Cricket",
      "x": 0.02,
      "y": 0.62,
      "w": 0.2,
      "h": 0.08,
      "tag": "game-type",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "Paye ton coup : 200",
      "x": 0.02,
      "y": 0.71,
      "w": 0.2,
      "h": 0.06,
      "tag": "game-option",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.3,
      "y": 0.02,
      "w": 0.68,
      "h": 0.08,
      "tag": "game-alt-headers",
      "radius": 0.0
     },
     {
      "op": "text",
      "text": "Joueur          Score",
      "x": 0.3,
      "y": 0.02,
      "w": 0.68,
      "h": 0.08,
      "tag": "game-headers",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.3,
      "y": 0.13,
      "w": 0.68,
      "h": 0.12,
      "tag": "game-player",
      "radius": 0.0
     },
     {
      "op": "text",
      "text": "Joueur 1",
      "x": 0.3,
      "y": 0.13,
      "w": 0.408,
      "h": 0.12,
      "tag": "game-player-name",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "120",
      "x": 0.708,
      "y": 0.13,
      "w": 0.272,
      "h": 0.12,
      "tag": "game-score",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.3,
      "y": 0.27,
      "w": 0.68,
      "h": 0.12,
      "tag": "game-inactive",
      "radius": 0.0
     },
     {
      "op": "text",
      "text": "Joueur 2",
      "x": 0.3,
      "y": 0.27,
      "w": 0.408,
      "h": 0.12,
      "tag": "game-text",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "80",
      "x": 0.708,
      "y": 0.27,
      "w": 0.272,
      "h": 0.12,
      "tag": "game-score",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.3,
      "y": 0.41,
      "w": 0.68,
      "h": 0.12,
      "tag": "game-dead",
      "radius": 0.0
     },
     {
      "op": "text",
      "text": "Joueur 3",
      "x": 0.3,
      "y": 0.41,
      "w": 0.408,
      "h": 0.12,
      "tag": "game-text",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "0",
      "x": 0.708,
      "y": 0.41,
      "w": 0.272,
      "h": 0.12,
      "tag": "game-score",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "line",
      "x1": 0.3,
      "y1": 0.58,
      "x2": 0.98,
      "y2": 0.58,
      "tag": "game-table",
      "width": 0.003
     },
     {
      "op": "line",
      "x1": 0.3,
      "y1": 0.64,
      "x2": 0.98,
      "y2": 0.64,
      "tag": "game-table",
      "width": 0.003
     },
     {
      "op": "line",
      "x1": 0.3,
      "y1": 0.7,
      "x2": 0.98,
      "y2": 0.7,
      "tag": "game-table",
      "width": 0.003
     },
     {
      "op": "line",
      "x1": 0.3,
      "y1": 0.76,
      "x2": 0.98,
      "y2": 0.76,
      "tag": "game-table",
      "width": 0.003
     },
     {
      "op": "text",
      "text": "20   19   18   17",
      "x": 0.3,
      "y": 0.77,
      "w": 0.68,
      "h": 0.06,
      "tag": "game-text",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.3,
      "y": 0.88,
      "w": 0.68,
      "h": 0.1,
      "tag": "game-title1",
      "radius": 0.0
     },
     {
      "op": "text",
      "text": "Le gagnant est…",
      "x": 0.3,
      "y": 0.88,
      "w": 0.68,
      "h": 0.1,
      "tag": "game-title2",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     }
    ]
   },
   {
    "name": "theme-plate-players",
    "tags": [
     "player1",
     "player2",
     "player3",
     "player4",
     "player5",
     "player6",
     "player7",
     "player8",
     "player9",
     "player10",
     "player11",
     "player12"
    ],
    "points": [
     [
      "player1",
      0.08,
      0.3
     ],
     [
      "player2",
      0.25,
      0.3
     ],
     [
      "player3",
      0.42000000000000004,
      0.3
     ],
     [
      "player4",
      0.59,
      0.3
     ],
     [
      "player5",
      0.76,
      0.3
     ],
     [
      "player6",
      0.93,
      0.3
     ],
     [
      "player7",
      0.08,
      0.7
     ],
     [
      "player8",
      0.25,
      0.7
     ],
     [
      "player9",
      0.42000000000000004,
      0.7
     ],
     [
      "player10",
      0.59,
      0.7
     ],
     [
      "player11",
      0.76,
      0.7
     ],
     [
      "player12",
      0.93,
      0.7
     ]
    ],
    "drawing": [
     {
      "op": "fill"
     },
     {
      "op": "box",
      "x": 0.02,
      "y": 0.2,
      "w": 0.12,
      "h": 0.2,
      "tag": "player1",
      "radius": 0.012
     },
     {
      "op": "text",
      "text": "1",
      "x": 0.02,
      "y": 0.2,
      "w": 0.12,
      "h": 0.2,
      "tag": "color-black",
      "size": 0.5,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.19,
      "y": 0.2,
      "w": 0.12,
      "h": 0.2,
      "tag": "player2",
      "radius": 0.012
     },
     {
      "op": "text",
      "text": "2",
      "x": 0.19,
      "y": 0.2,
      "w": 0.12,
      "h": 0.2,
      "tag": "color-black",
      "size": 0.5,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.36,
      "y": 0.2,
      "w": 0.12,
      "h": 0.2,
      "tag": "player3",
      "radius": 0.012
     },
     {
      "op": "text",
      "text": "3",
      "x": 0.36,
      "y": 0.2,
      "w": 0.12,
      "h": 0.2,
      "tag": "color-black",
      "size": 0.5,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.53,
      "y": 0.2,
      "w": 0.12,
      "h": 0.2,
      "tag": "player4",
      "radius": 0.012
     },
     {
      "op": "text",
      "text": "4",
      "x": 0.53,
      "y": 0.2,
      "w": 0.12,
      "h": 0.2,
      "tag": "color-black",
      "size": 0.5,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.7,
      "y": 0.2,
      "w": 0.12,
      "h": 0.2,
      "tag": "player5",
      "radius": 0.012
     },
     {
      "op": "text",
      "text": "5",
      "x": 0.7,
      "y": 0.2,
      "w": 0.12,
      "h": 0.2,
      "tag": "color-black",
      "size": 0.5,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.87,
      "y": 0.2,
      "w": 0.12,
      "h": 0.2,
      "tag": "player6",
      "radius": 0.012
     },
     {
      "op": "text",
      "text": "6",
      "x": 0.87,
      "y": 0.2,
      "w": 0.12,
      "h": 0.2,
      "tag": "color-black",
      "size": 0.5,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.02,
      "y": 0.6,
      "w": 0.12,
      "h": 0.2,
      "tag": "player7",
      "radius": 0.012
     },
     {
      "op": "text",
      "text": "7",
      "x": 0.02,
      "y": 0.6,
      "w": 0.12,
      "h": 0.2,
      "tag": "color-black",
      "size": 0.5,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.19,
      "y": 0.6,
      "w": 0.12,
      "h": 0.2,
      "tag": "player8",
      "radius": 0.012
     },
     {
      "op": "text",
      "text": "8",
      "x": 0.19,
      "y": 0.6,
      "w": 0.12,
      "h": 0.2,
      "tag": "color-black",
      "size": 0.5,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.36,
      "y": 0.6,
      "w": 0.12,
      "h": 0.2,
      "tag": "player9",
      "radius": 0.012
     },
     {
      "op": "text",
      "text": "9",
      "x": 0.36,
      "y": 0.6,
      "w": 0.12,
      "h": 0.2,
      "tag": "color-black",
      "size": 0.5,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.53,
      "y": 0.6,
      "w": 0.12,
      "h": 0.2,
      "tag": "player10",
      "radius": 0.012
     },
     {
      "op": "text",
      "text": "10",
      "x": 0.53,
      "y": 0.6,
      "w": 0.12,
      "h": 0.2,
      "tag": "color-black",
      "size": 0.5,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.7,
      "y": 0.6,
      "w": 0.12,
      "h": 0.2,
      "tag": "player11",
      "radius": 0.012
     },
     {
      "op": "text",
      "text": "11",
      "x": 0.7,
      "y": 0.6,
      "w": 0.12,
      "h": 0.2,
      "tag": "color-black",
      "size": 0.5,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.87,
      "y": 0.6,
      "w": 0.12,
      "h": 0.2,
      "tag": "player12",
      "radius": 0.012
     },
     {
      "op": "text",
      "text": "12",
      "x": 0.87,
      "y": 0.6,
      "w": 0.12,
      "h": 0.2,
      "tag": "color-black",
      "size": 0.5,
      "align": "center",
      "valign": "center"
     }
    ]
   },
   {
    "name": "theme-plate-games",
    "tags": [
     "game-red",
     "game-green",
     "game-blue",
     "game-purple",
     "game-grey",
     "game-grey2",
     "game-gold",
     "game-silver",
     "game-bronze",
     "suggestion-color-allplayer"
    ],
    "points": [
     [
      "game-red",
      0.1,
      0.3
     ],
     [
      "game-green",
      0.3,
      0.3
     ],
     [
      "game-blue",
      0.5,
      0.3
     ],
     [
      "game-purple",
      0.7,
      0.3
     ],
     [
      "game-grey",
      0.9,
      0.3
     ],
     [
      "game-grey2",
      0.1,
      0.7
     ],
     [
      "game-gold",
      0.3,
      0.7
     ],
     [
      "game-silver",
      0.5,
      0.7
     ],
     [
      "game-bronze",
      0.7,
      0.7
     ],
     [
      "suggestion-color-allplayer",
      0.9,
      0.7
     ]
    ],
    "drawing": [
     {
      "op": "fill"
     },
     {
      "op": "swatch",
      "x": 0.03,
      "y": 0.2,
      "w": 0.14,
      "h": 0.2,
      "tag": "game-red",
      "radius": 0.012,
      "outline": [
       90,
       90,
       90
      ],
      "outlineWidth": 0.003
     },
     {
      "op": "swatch",
      "x": 0.23,
      "y": 0.2,
      "w": 0.14,
      "h": 0.2,
      "tag": "game-green",
      "radius": 0.012,
      "outline": [
       90,
       90,
       90
      ],
      "outlineWidth": 0.003
     },
     {
      "op": "swatch",
      "x": 0.43,
      "y": 0.2,
      "w": 0.14,
      "h": 0.2,
      "tag": "game-blue",
      "radius": 0.012,
      "outline": [
       90,
       90,
       90
      ],
      "outlineWidth": 0.003
     },
     {
      "op": "swatch",
      "x": 0.63,
      "y": 0.2,
      "w": 0.14,
      "h": 0.2,
      "tag": "game-purple",
      "radius": 0.012,
      "outline": [
       90,
       90,
       90
      ],
      "outlineWidth": 0.003
     },
     {
      "op": "swatch",
      "x": 0.83,
      "y": 0.2,
      "w": 0.14,
      "h": 0.2,
      "tag": "game-grey",
      "radius": 0.012,
      "outline": [
       90,
       90,
       90
      ],
      "outlineWidth": 0.003
     },
     {
      "op": "swatch",
      "x": 0.03,
      "y": 0.6,
      "w": 0.14,
      "h": 0.2,
      "tag": "game-grey2",
      "radius": 0.012,
      "outline": [
       90,
       90,
       90
      ],
      "outlineWidth": 0.003
     },
     {
      "op": "swatch",
      "x": 0.23,
      "y": 0.6,
      "w": 0.14,
      "h": 0.2,
      "tag": "game-gold",
      "radius": 0.012,
      "outline": [
       90,
       90,
       90
      ],
      "outlineWidth": 0.003
     },
     {
      "op": "swatch",
      "x": 0.43,
      "y": 0.6,
      "w": 0.14,
      "h": 0.2,
      "tag": "game-silver",
      "radius": 0.012,
      "outline": [
       90,
       90,
       90
      ],
      "outlineWidth": 0.003
     },
     {
      "op": "swatch",
      "x": 0.63,
      "y": 0.6,
      "w": 0.14,
      "h": 0.2,
      "tag": "game-bronze",
      "radius": 0.012,
      "outline": [
       90,
       90,
       90
      ],
      "outlineWidth": 0.003
     },
     {
      "op": "swatch",
      "x": 0.83,
      "y": 0.6,
      "w": 0.14,
      "h": 0.2,
      "tag": "suggestion-color-allplayer",
      "radius": 0.012,
      "outline": [
       90,
       90,
       90
      ],
      "outlineWidth": 0.003
     }
    ]
   },
   {
    "name": "theme-plate-bob27",
    "tags": [
     "bob27-bg",
     "bob27-blue",
     "bob27-green",
     "bob27-red",
     "bob27-hit",
     "bob27-miss",
     "bob27-text"
    ],
    "points": [
     [
      "bob27-bg",
      0.05,
      0.5
     ],
     [
      "bob27-blue",
      0.3,
      0.25
     ],
     [
      "bob27-green",
      0.3,
      0.5
     ],
     [
      "bob27-red",
      0.3,
      0.75
     ],
     [
      "bob27-hit",
      0.7,
      0.25
     ],
     [
      "bob27-miss",
      0.7,
      0.5
     ],
     [
      "bob27-text",
      0.62,
      0.75
     ]
    ],
    "drawing": [
     {
      "op": "fill",
      "tag": "bob27-bg"
     },
     {
      "op": "box",
      "x": 0.15,
      "y": 0.18,
      "w": 0.4,
      "h": 0.15,
      "tag": "bob27-blue",
      "radius": 0.009
     },
     {
      "op": "text",
      "text": "D1   D2   D3",
      "x": 0.15,
      "y": 0.18,
      "w": 0.4,
      "h": 0.15,
      "tag": "bob27-text",
      "size": 0.5,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.15,
      "y": 0.43,
      "w": 0.4,
      "h": 0.15,
      "tag": "bob27-green",
      "radius": 0.009
     },
     {
      "op": "text",
      "text": "27 points",
      "x": 0.15,
      "y": 0.43,
      "w": 0.4,
      "h": 0.15,
      "tag": "bob27-text",
      "size": 0.5,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "box",
      "x": 0.15,
      "y": 0.68,
      "w": 0.4,
      "h": 0.15,
      "tag": "bob27-red",
      "radius": 0.009
     },
     {
      "op": "text",
      "text": "Touché / Raté",
      "x": 0.15,
      "y": 0.68,
      "w": 0.4,
      "h": 0.15,
      "tag": "bob27-text",
      "size": 0.5,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "D1 : OK",
      "x": 0.6,
      "y": 0.18,
      "w": 0.25,
      "h": 0.15,
      "tag": "bob27-hit",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "D2 : X",
      "x": 0.6,
      "y": 0.43,
      "w": 0.25,
      "h": 0.15,
      "tag": "bob27-miss",
      "size": 0.6,
      "align": "center",
      "valign": "center"
     }
    ]
   },
   {
    "name": "theme-plate-fighters",
    "tags": [
     "fighters-actual-player",
     "fighters-alive-player",
     "fighters-dead-player",
     "fighters-medic",
     "fighters-targets",
     "fighters-scores",
     "fighters-darts",
     "fighters-round"
    ],
    "points": [
     [
      "fighters-actual-player",
      0.3,
      0.15
     ],
     [
      "fighters-alive-player",
      0.3,
      0.35
     ],
     [
      "fighters-dead-player",
      0.3,
      0.55
     ],
     [
      "fighters-medic",
      0.3,
      0.75
     ],
     [
      "fighters-targets",
      0.75,
      0.15
     ],
     [
      "fighters-scores",
      0.75,
      0.35
     ],
     [
      "fighters-darts",
      0.75,
      0.55
     ],
     [
      "fighters-round",
      0.75,
      0.75
     ]
    ],
    "drawing": [
     {
      "op": "fill"
     },
     {
      "op": "text",
      "text": "> Joueur 1",
      "x": 0.05,
      "y": 0.08,
      "w": 0.45,
      "h": 0.15,
      "tag": "fighters-actual-player",
      "size": 0.55,
      "align": "left",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "Joueur 2",
      "x": 0.05,
      "y": 0.28,
      "w": 0.45,
      "h": 0.15,
      "tag": "fighters-alive-player",
      "size": 0.55,
      "align": "left",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "Joueur 3 (KO)",
      "x": 0.05,
      "y": 0.48,
      "w": 0.45,
      "h": 0.15,
      "tag": "fighters-dead-player",
      "size": 0.55,
      "align": "left",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "+ Soin",
      "x": 0.05,
      "y": 0.68,
      "w": 0.45,
      "h": 0.15,
      "tag": "fighters-medic",
      "size": 0.55,
      "align": "left",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "20  19  18",
      "x": 0.55,
      "y": 0.08,
      "w": 0.4,
      "h": 0.15,
      "tag": "fighters-targets",
      "size": 0.55,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "120",
      "x": 0.55,
      "y": 0.28,
      "w": 0.4,
      "h": 0.15,
      "tag": "fighters-scores",
      "size": 0.55,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "o  o  o",
      "x": 0.55,
      "y": 0.48,
      "w": 0.4,
      "h": 0.15,
      "tag": "fighters-darts",
      "size": 0.55,
      "align": "center",
      "valign": "center"
     },
     {
      "op": "text",
      "text": "Round 3",
      "x": 0.55,
      "y": 0.68,
      "w": 0.4,
      "h": 0.15,
      "tag": "fighters-round",
      "size": 0.55,
      "align": "center",
      "valign": "center"
     }
    ]
   },
   {
    "name": "theme-plate-borders",
    "tags": [
     "border-size",
     "padding",
     "border-radius",
     "button-radius"
    ],
    "points": [
     [
      "border-size",
      0.25,
      0.26
     ],
     [
      "padding",
      0.3,
      0.32
     ],
     [
      "border-radius",
      0.88,
      0.5
     ],
     [
      "button-radius",
      0.8,
      0.84
     ]
    ],
    "drawing": [
     {
      "op": "fill"
     },
     {
      "op": "shapedRow",
      "x": 0.15,
      "y": 0.2,
      "w": 0.7,
      "h": 0.13,
      "label": "Partie simple",
      "chosen": true
     },
     {
      "op": "shapedRow",
      "x": 0.15,
      "y": 0.38,
      "w": 0.7,
      "h": 0.13,
      "label": "Partie en réseau",
      "chosen": false
     },
     {
      "op": "shapedRow",
      "x": 0.15,
      "y": 0.56,
      "w": 0.7,
      "h": 0.13,
      "label": "Divers",
      "chosen": false
     },
     {
      "op": "shapedButton",
      "x": 0.62,
      "y": 0.8,
      "w": 0.3,
      "h": 0.09,
      "label": "Sauvegarder"
     }
    ]
   },
   {
    "name": "theme-plate-shortcuts",
    "tags": [
     "main-sub-menu-shortcuts",
     "main-sub-menu-text-position",
     "parametrage-menu-shortcuts",
     "parametrage-menu-text-position",
     "players-menu-shortcuts",
     "players-menu-text-position",
     "game-options-menu-shortcuts",
     "main-sub-menu-text-align",
     "main-sub-menu-text-valign",
     "parametrage-menu-text-align",
     "parametrage-menu-text-valign",
     "players-menu-text-align",
     "players-menu-text-valign",
     "game-options-menu-text-align"
    ],
    "points": [
     [
      "main-sub-menu-shortcuts",
      0.08,
      0.15
     ],
     [
      "main-sub-menu-text-position",
      0.3,
      0.15
     ],
     [
      "parametrage-menu-shortcuts",
      0.08,
      0.4
     ],
     [
      "parametrage-menu-text-position",
      0.3,
      0.4
     ],
     [
      "players-menu-shortcuts",
      0.08,
      0.65
     ],
     [
      "players-menu-text-position",
      0.3,
      0.65
     ],
     [
      "game-options-menu-shortcuts",
      0.08,
      0.88
     ],
     [
      "main-sub-menu-text-align",
      0.7,
      0.15
     ],
     [
      "main-sub-menu-text-valign",
      0.7,
      0.2
     ],
     [
      "parametrage-menu-text-align",
      0.7,
      0.4
     ],
     [
      "parametrage-menu-text-valign",
      0.7,
      0.45
     ],
     [
      "players-menu-text-align",
      0.7,
      0.65
     ],
     [
      "players-menu-text-valign",
      0.7,
      0.7
     ],
     [
      "game-options-menu-text-align",
      0.7,
      0.88
     ]
    ],
    "drawing": [
     {
      "op": "fill"
     },
     {
      "op": "exampleRow",
      "x": 0.05,
      "y": 0.08,
      "w": 0.9,
      "h": 0.15,
      "prefix": "main-sub-menu",
      "label": "Partie simple",
      "radius": 0.009
     },
     {
      "op": "exampleRow",
      "x": 0.05,
      "y": 0.32,
      "w": 0.9,
      "h": 0.15,
      "prefix": "parametrage-menu",
      "label": "Paramétrage",
      "radius": 0.009
     },
     {
      "op": "exampleRow",
      "x": 0.05,
      "y": 0.56,
      "w": 0.9,
      "h": 0.15,
      "prefix": "players-menu",
      "label": "Joueur 1",
      "radius": 0.009
     },
     {
      "op": "exampleRow",
      "x": 0.05,
      "y": 0.8,
      "w": 0.9,
      "h": 0.15,
      "prefix": "game-options-menu",
      "label": "Nombre de tours",
      "radius": 0.009
     }
    ]
   }
  ],
  "mockup": {
   "reference": {
    "screen": [
     1920,
     1080
    ],
    "mockup": [
     912,
     668
    ]
   },
   "units": "x, w, cx, x1, x2, r : parts de la largeur de la maquette ; y, h, cy, y1, y2 : parts de sa hauteur ; radius, width, borderWidth, outlineWidth : parts de sa hauteur (pixels du jeu / 668)",
   "frame": {
    "color": [
     90,
     90,
     90
    ],
    "width": 0.003
   },
   "background": [
    40,
    40,
    44
   ],
   "rules": {
    "tag": "une couleur nommee (etiquette du Colorset) ; une etiquette a Aucune (None) : rien n'est dessine",
    "fill": "fond de toute la maquette : couleur de tag ; background sans tag, ou si tag est a Aucune",
    "box": "rectangle plein de tag (arrondi radius), puis, si border, son contour de border (epaisseur borderWidth)",
    "swatch": "si tag est a Aucune : contour outline (epaisseur outlineWidth, arrondi radius) ; sinon box de tag",
    "rect": "rectangle de couleur (tag ou color fixe) ; width 0 : plein, sinon contour de cette epaisseur",
    "text": "police du jeu, taille = max(8 px, (height si donne, sinon h) x size) ; un texte plus large que w - textSqueeze est ecrase en largeur a w - textSqueeze ; centre dans le rectangle, ou align left : a x + textMargin, right : a droite - textMargin ; valign top : colle en haut, bottom : en bas",
    "circle": "disque de couleur fixe color, centre (cx, cy), rayon r",
    "line": "trait de tag (ou color), de (x1, y1) a (x2, y2), epaisseur width",
    "shapedRow": "item de menu avec les formes du moment, s = referenceHeight (1080). Arrondi R : border-radius 'max' -> h / 2, sinon min(h / 2, border-radius / s) (une valeur illisible : 0). chosen : contour menu-border d'epaisseur B = 2 x border-size / s (si B > 0, arrondi R), puis l'interieur = le rectangle reduit de B + P de chaque cote (P = 2 x padding / s), plein de menu-selected, arrondi max(0, R - B - P), texte label (size 0.6) en menu-text-white dans l'interieur. Sinon : plein de menu-buttons arrondi R, texte label en menu-text-black",
    "shapedButton": "bouton du bas : plein de menu-buttons, arrondi button-radius 'max' -> h / 2, sinon min(h / 2, 2 x button-radius / s) (une valeur illisible : 0) ; texte label (size 0.6) en menu-text-black",
    "exampleRow": "item de menu dessine comme le theme : box menu-buttons (arrondi radius). Raccourci = valeur de <prefix>-shortcuts : '' -> 'F1', None -> pas de raccourci, sinon ce texte. Avec raccourci : a gauche un rectangle de hauteur h et de largeur shortcutRatio x h (en pixels), box menu-shortcut (arrondi radius) et le raccourci en menu-text-white (size 0.6). Le texte : le reste de l'item, moins les marges <prefix>-text-position (gauche, droite, haut, bas, en % de cette boite, chacune ramenee entre 0 et 90 ; si deux marges opposees depassent 90 a elles deux, la seconde (droite, bas) est reduite d'autant ; une valeur illisible : pas de marge) ; label en menu-text-black, size 0.55, height = la hauteur de l'item (avant les marges), align = <prefix>-text-align, valign = <prefix>-text-valign (en minuscules ; center sinon)"
   },
   "constants": {
    "textSqueeze": 0.0044,
    "textMargin": 0.0066,
    "shortcutRatio": 1.1,
    "referenceHeight": 1080
   },
   "texts": "les textes des maquettes sont ceux du jeu, en francais (le jeu ne les traduit pas)"
  },
  "groups": [
   [
    "theme-group-menus",
    [
     "theme-plate-menus",
     "theme-plate-settings",
     "theme-plate-description",
     "theme-plate-messages",
     "theme-plate-shortcuts",
     "theme-plate-borders"
    ]
   ],
   [
    "theme-group-games",
    [
     "theme-plate-game",
     "theme-plate-players",
     "theme-plate-games",
     "theme-plate-bob27",
     "theme-plate-fighters"
    ]
   ]
  ],
  "noneAllowed": [
   "menu-header",
   "game-bg",
   "game-option",
   "game-type",
   "game-darts",
   "fighters-dead-player",
   "suggestion-color-allplayer"
  ],
  "transparentAllowed": [
   "menu-buttons",
   "menu-item-black",
   "menu-item-white",
   "menu-selected",
   "menu-inactive",
   "menu-alternate",
   "message-bg",
   "description-bg",
   "bob27-bg",
   "bg-darts-nb",
   "bg-darts-nb-header",
   "bg-round-nb",
   "bg-round-nb-header",
   "game-table",
   "game-alt-headers",
   "game-inactive"
  ],
  "shortcutTags": [
   "main-sub-menu-shortcuts",
   "parametrage-menu-shortcuts",
   "players-menu-shortcuts",
   "game-options-menu-shortcuts"
  ],
  "shortcutChoices": [
   [
    "",
    "theme-shortcut-keys"
   ],
   [
    null,
    "theme-shortcut-none"
   ],
   [
    ">",
    ">"
   ],
   [
    "-",
    "-"
   ],
   [
    "*",
    "*"
   ],
   [
    "+",
    "+"
   ]
  ],
  "alignTags": [
   "main-sub-menu-text-align",
   "parametrage-menu-text-align",
   "players-menu-text-align",
   "game-options-menu-text-align"
  ],
  "alignChoices": [
   [
    "Left",
    "theme-align-left"
   ],
   [
    "Center",
    "theme-align-center"
   ],
   [
    "Right",
    "theme-align-right"
   ]
  ],
  "valignTags": [
   "main-sub-menu-text-valign",
   "parametrage-menu-text-valign",
   "players-menu-text-valign"
  ],
  "valignChoices": [
   [
    "Top",
    "theme-valign-top"
   ],
   [
    "Center",
    "theme-align-center"
   ],
   [
    "Bottom",
    "theme-valign-bottom"
   ]
  ],
  "positionTags": [
   "main-sub-menu-text-position",
   "parametrage-menu-text-position",
   "players-menu-text-position"
  ],
  "shapeTags": [
   "border-size",
   "padding",
   "border-radius",
   "button-radius"
  ],
  "radiusTags": [
   "border-radius",
   "button-radius"
  ],
  "shapeLimits": {
   "border-size": 15,
   "padding": 15,
   "border-radius": 40,
   "button-radius": 40
  },
  "palette": [
   [
    255,
    255,
    255
   ],
   [
    214,
    214,
    214
   ],
   [
    160,
    160,
    160
   ],
   [
    100,
    100,
    100
   ],
   [
    48,
    48,
    48
   ],
   [
    0,
    0,
    0
   ],
   [
    255,
    0,
    0
   ],
   [
    194,
    1,
    1
   ],
   [
    128,
    0,
    0
   ],
   [
    255,
    128,
    0
   ],
   [
    255,
    215,
    0
   ],
   [
    255,
    255,
    0
   ],
   [
    128,
    255,
    0
   ],
   [
    0,
    255,
    0
   ],
   [
    0,
    128,
    0
   ],
   [
    0,
    128,
    128
   ],
   [
    0,
    255,
    255
   ],
   [
    107,
    134,
    176
   ],
   [
    0,
    128,
    255
   ],
   [
    0,
    0,
    255
   ],
   [
    0,
    0,
    128
   ],
   [
    128,
    0,
    255
   ],
   [
    255,
    0,
    255
   ],
   [
    255,
    105,
    180
   ],
   [
    139,
    69,
    19
   ],
   [
    205,
    127,
    50
   ],
   [
    213,
    206,
    186
   ],
   [
    112,
    156,
    118
   ],
   [
    205,
    144,
    110
   ],
   [
    189,
    108,
    109
   ]
  ],
  "file": "Colorset_perso.cfg"
 }
};
