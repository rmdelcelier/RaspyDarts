# Fichier de menus de RaspyDarts (`menus.yaml`)

> **Statut : version 1, programmée dans RaspyDarts 4.6.1.** Ce document décrit ce que le
> moteur de menus lit ; il sert de référence au jeu (Python : `include/cmenus.py`,
> `include/cmenustyle.py`), au configurateur de la page GitHub « Personnalisation des menus »
> (`docs/menus.html`, JavaScript) et à ceux qui écrivent leur fichier à la main.
>
> Le configurateur fabrique ce fichier avec un aperçu de la borne : ses règles de placement
> sont celles du jeu, vérifiées par `python docs/test_placement.py` (identiques au pixel en
> 1024×600 et en 1920×1080). Ses données et images viennent de `python docs/generer_menus.py`,
> à relancer quand `menus/defaults.yaml`, un thème ou un logo change.
>
> Dans l'aperçu, on clique un bouton pour le choisir, on le glisse (lâché sur une case de
> la zone des boutons : il y est fixé, `cell` ; ailleurs : placement libre, §7.5, avec des
> repères d'alignement aimantés sur le centre de l'écran et les bords des autres boutons)
> et on tire ses poignées pour le redimensionner (un bouton de la disposition : « tous les
> boutons » change `button_size`, sinon lui seul prend des cases entières, `span`). Le panneau de
> gauche montre ce qui est choisi : l'écran (disposition, colonnes, lignes, zone des boutons
> à poignées, titres, fond, raccourcis) ou le bouton (texte, action, position, aspect écrit
> sur ce bouton seul ou dans le style de l'écran). Un écran reste un seul écran : si ses
> boutons dépassent leur zone, le configurateur réduit `button_size.height`. Changer la
> disposition d'un menu au dessin classique la fait partir de la place qu'avaient ses
> boutons.

## 1. Ce que le fichier décrit, et ce qu'il ne décrit pas

Le fichier décrit **les menus** : menu principal, Divers, Paramètres, choix de la catégorie et
du jeu, options, joueurs, assistant, ainsi que les panneaux de favoris. Pour chacun : quels
boutons, dans quel ordre, où, avec quel aspect, quels raccourcis, et ce qu'ils déclenchent.

Il **ne décrit pas** les écrans de jeu (tableaux de scores, cibles, animations), dessinés par
chaque jeu de `games/` : ils gardent leur fonctionnement et le thème (`Colorset.cfg`).

Il **ne peut pas inventer d'action** : chaque bouton déclenche une action connue du jeu
(liste au §8). Un fichier mal écrit ne peut donc rien faire d'autre que mal afficher un menu.

## 2. Emplacements et priorité

Du plus prioritaire au moins prioritaire :

| Fichier | Rôle |
|---|---|
| `~/.raspydarts/themes/<thème>/menu/menus.yaml` | les menus du thème choisi (faits par la page d'installation, étape Menus, ou à la main) ; ses images dans `~/.raspydarts/themes/<thème>/images/` |
| `/raspydarts/menus/defaults.yaml` | les menus par défaut, livrés avec le jeu |

Chaque thème a ses menus : changer de thème change de menus. Le thème par défaut s'appelle
`sombre` (anciennement `remi` : une configuration qui nomme l'un prend le dossier qui existe).
Un ancien `~/.raspydarts/themes/<thème>/menus.yaml` (sans le dossier `menu`) est encore lu,
avant celui du dossier `menu`.

Un fichier ne contient que ce qu'il change ; le reste vient du niveau suivant. Les règles de
fusion :

- Les **dictionnaires** se fusionnent clé par clé (`defaults`, `styles`, un menu…).
- Une **liste de boutons** (`buttons:`) donnée par un fichier **remplace** celle du niveau
  suivant ; les boutons de ce niveau qu'elle ne nomme pas (un bouton d'une version plus
  récente du jeu) sont ajoutés après les siens, avant ceux du bas de l'écran, sauf ceux que
  le menu retire : `removed: [gallery]` (la page de configuration l'écrit quand on supprime
  un bouton du jeu). Pour ne changer qu'un bouton sans réécrire la liste, utiliser
  `button_changes:` (§7.3).
- Une valeur `null` (ou `~`) efface la valeur du niveau suivant.

Un fichier se déposait déjà sur la carte SD comme `raspydarts.cfg` : le service
`raspydarts-boot` copie au démarrage le contenu d'un dossier `.raspydarts` déposé sur la
partition `bootfs` dans `~/.raspydarts`. `menus.yaml` et le thème personnel s'y déposent
donc de la même façon.

## 3. Erreurs

- **Fichier illisible** (YAML mal formé) : il est ignoré en entier, le menu s'affiche avec le
  niveau suivant, un message bref s'affiche une fois au démarrage et le journal donne le
  fichier, la ligne et la colonne.
- **Valeur invalide** (couleur inconnue, action inconnue, image absente…) : seule cette
  valeur est ignorée (valeur du niveau suivant), avec une ligne dans le journal.
- **Clé inconnue** : ignorée, avec une ligne dans le journal (une faute de frappe se voit).
- La borne reste **toujours** utilisable : `defaults.yaml` ne peut pas être remplacé en
  entier, un menu sans aucun bouton visible garde ceux du niveau suivant.

## 4. Unités et résolution

```yaml
resolution: auto          # ou [1024, 600], [1920, 1080]…
```

- `auto` : toutes les positions et tailles sont des **fractions de l'écran**, de `0` à `1`
  (`x: 0.5` = milieu, `width: 0.25` = un quart de la largeur). Le même fichier convient à
  toutes les résolutions.
- `[largeur, hauteur]` : positions et tailles en **pixels de cette résolution**. Sur un écran
  différent, elles sont mises à l'échelle (x et largeurs par le rapport des largeurs, y et
  hauteurs par celui des hauteurs). Une valeur peut quand même être donnée en fraction en
  l'écrivant en pourcentage : `x: 50%`.
- Les **tailles de texte** sont toujours des fractions de la **hauteur** de l'écran
  (`size: 0.045`) ou, avec une résolution de référence, des pixels de cette hauteur.
- Les **valeurs par défaut** du jeu (zone des boutons, hauteur des boutons, écarts, tailles
  de texte, place du titre) sont des parts de l'écran, quelle que soit l'unité du fichier.

Résolutions de référence pour les essais : **1024×600** (Raspberry Pi de développement,
écran 7") et **1920×1080** (borne).

## 5. Valeurs communes

- **Couleur** : nom d'une couleur du thème (`menu-selected`, `menu-text`… : celles de
  `Colorset.cfg`), ou `'#RRGGBB'`, ou `'#RRGGBBAA'` (avec transparence). Les guillemets
  sont obligatoires pour `#` (sinon YAML y voit un commentaire).
- **Image** : chemin cherché, dans l'ordre, dans le dossier du thème, dans `~/.raspydarts`,
  puis dans `/raspydarts/images`. PNG ou JPG.
- **Police** : nom de fichier (`Kamikzon.ttf`) cherché dans `fonts/` du thème, dans
  `~/.raspydarts/fonts`, puis dans `/raspydarts/fonts`. Absente : la police du thème.
- **Texte affiché** :
  - une clé de traduction (`game-type-local`) : traduite dans la langue du jeu ;
  - un texte direct (`Mes parties`) : affiché tel quel si ce n'est pas une clé connue ;
  - un texte par langue : `{fr: Mes parties, en: My games, de: Meine Spiele}` (langue du
    jeu, sinon `en`, sinon la première donnée).
- **Touche** (raccourcis, navigation) : `F1`…`F12`, une lettre ou un chiffre (`'l'`,
  `'1'`), `enter`, `space`, `escape`, `backspace`, `tab`, `up`, `down`, `left`, `right`, ou
  un bouton de la borne : `btn:validate`, `btn:back`, `btn:cancel`, `btn:up`, `btn:down`,
  `btn:left`, `btn:right`, `btn:plus`, `btn:minus`, `btn:nextplayer`, `btn:game`, ou une
  fléchette : `dart:S20`, `dart:SB`, `dart:DB`… `none` : aucun. Comme raccourci, `escape`
  désigne toutes les touches `back` (§9).

## 6. Structure générale

```yaml
version: 1
resolution: auto
defaults: {…}            # réglages de tous les menus (§7.1)
styles: {…}              # styles de boutons nommés (§7.2)
navigation: {…}          # touches de navigation (§9)
encoder: {…}             # encodeur rotatif USB (§10)
virtual_keyboard: {…}    # clavier à l'écran (§11)
menus: {…}               # les menus (§7.3)
```

Toutes les sections sont facultatives.

### 6.1 Premier écran (`start`)

```yaml
start: main               # le menu principal (défaut)
```

| Valeur | Premier écran |
|---|---|
| `main` | le menu principal |
| `local_game` | le choix des joueurs d'une partie simple (comme l'option « Ne pas afficher le menu principal ») |
| `category:<nom>` | les joueurs, puis directement la liste des jeux de cette catégorie |
| `game:<Nom>` | les joueurs, puis directement les options de ce jeu |

Retour depuis les joueurs mène alors au menu principal. Les options du jeu « Ne pas afficher
le menu principal » et « Afficher uniquement les jeux favoris » (Paramètres > Personnalisation
> Général) restent prioritaires : un fichier ne peut pas les contredire.

Un bouton peut aussi sauter des écrans : `category:<nom>` et `game:<Nom>` dans le menu
principal passent par les joueurs puis vont directement à la liste ou aux options. Retour
depuis ces écrans revient aux joueurs (les écrans sautés ne sont pas réaffichés).

## 7. Aspect

### 7.1 `defaults` et cascade

L'aspect se décide à trois niveaux, chacun ne précisant que ce qui change :
**`defaults`** (tous les menus) → **le menu** → **le bouton**.

```yaml
defaults:
  background: images/background/menu.png   # fond du menu (§7.3 bis : image, couleur ou bloc)
  layout: list                             # disposition des boutons (§7.4)
  style: classic                           # style des boutons (§7.2)
  title:    {font: Kamikzon.ttf, size: 0.06, color: menu-header, bold: true,
             background: '#00000080'}      # bande derrière le titre (§7.3 bis)
  subtitle: {size: 0.035, color: menu-text}
  shortcuts: {show: true, format: '{key}', background: menu-shortcut, color: menu-text-black, position: left}
```

**Titre et sous-titre** : dans un menu, `title` et `subtitle` s'écrivent soit comme un
texte (`title: game-type-menu`), soit comme un bloc qui donne aussi l'aspect
(`title: {text: game-type-menu, size: 0.07}`). L'aspect se lit dans `defaults`, puis dans
le menu. Propriétés : `font`, `size`, `color`, `bold`, `shadow`, `align`, `background` (la
bande derrière le texte), `place` (`{x, y, width, height}` : placement libre de la bande ;
par défaut le titre est en haut et le sous-titre juste dessous). Sans aspect donné, le
bandeau de titre habituel du thème est gardé.

**Raccourcis** : `shortcuts.show: false` n'affiche plus les F1, F2… (ils restent actifs) ;
`true` les affiche. Sans `show`, ils s'affichent comme sur les boutons classiques du thème
(pas quand `main-sub-menu-shortcuts` du `Colorset.cfg` vaut `None`).
`format` permet `'> '` ou `'[{key}]'`. Dans les menus dessinés par un style (§7.2), la
touche est dans sa propre case, comme sur les boutons classiques : `background` (couleur de
la case, `menu-shortcut` par défaut ; `null` : la touche seule, sans case), `color` (couleur
de la touche : `menu-text-black` dans une case, `menu-shortcut` sans case), `font`, `bold`,
`position` (`left` ou `right` : sur le côté, le texte du bouton à côté ; `top_left`,
`top_right`, `bottom_left`, `bottom_right` : dans un coin ; par défaut `left`, et `top_left`
pour les tuiles) et `size` (part de la hauteur du bouton : 0.4 sur un côté, 0.15 dans un
coin par défaut).

### 7.2 Styles et états

```yaml
styles:
  classic:
    shape: rounded           # rounded | rectangle | pill | none (texte seul)
    radius: 12               # arrondi (pixels de référence ou fraction de la hauteur du bouton)
    background:              # fond du bouton (§7.3 bis)
      color: menu-buttons
      image: null
    border: {width: 0, color: menu-border}
    shadow: false
    text: {font: null, size: 0.045, color: menu-text, align: center, position: center,
           offset: [0, 0], shadow: false, bold: false, show: true}   # show: false : texte non écrit
    icon: {position: left, size: 0.7, fit: contain}   # taille relative à la hauteur du bouton
    # États : chacun ne précise que ce qui change par rapport à l'état normal
    selected: {background: {color: menu-selected}, text: {color: menu-text-white}}
    disabled: {background: {color: '#808080'}, text: {color: '#C0C0C0'}}
    pressed:  {scale: 0.96}
```

- `text.position` : `center`, `top`, `bottom`, `left`, `right` (dans le bouton) ;
  `offset` : décalage `[x, y]`.
- `scale` (dans un état) : agrandit ou réduit le bouton autour de son centre.
- Un bouton ou un menu peut prendre un style nommé (`style: tile`) **et/ou** changer des
  propriétés directement (`background: {color: '#C0392B'}`, `selected: {…}`,
  `text: {size: 0.05}`).
- `color: …` seul est un raccourci de `background: {color: …}`.
- Les valeurs ci-dessus sont celles d'un style qui ne dit rien. Le style **`classic`** des
  menus du jeu reproduit les boutons classiques du thème :
  `background: {color: 'menu-buttons*1.5'}` et
  `text: {size: auto, color: menu-text-black, align: theme}`. Un menu qui passe du dessin
  classique au dessin par la disposition garde donc l'aspect de ses boutons.
- `text.size: auto` : le texte suit la hauteur du bouton (comme les boutons classiques),
  réduit s'il est trop large. `text.align: theme` : l'alignement des boutons classiques du
  thème (`main-sub-menu-text-align` de `Colorset.cfg`).
- Une couleur `menu-buttons*1.5` est une couleur du thème éclaircie (ou assombrie sous 1),
  comme le fond des boutons classiques.

### 7.3 bis Fonds (boutons et menus)

Le même bloc décrit le fond d'un bouton (dans un style, un état ou un bouton) et le fond
d'un menu (`background` d'un menu ou de `defaults`) :

```yaml
background:
  color: menu-buttons          # couleur de fond, sous l'image (null : transparent)
  image: images/buttons/tile.png
  fit: stretch                 # comment l'image remplit la place (ci-dessous)
  position: center             # center | top | bottom | left | right | top_left | top_right
                               # | bottom_left | bottom_right
  offset: [0, 0]               # décalage depuis cette position
  size: [1.0, 1.0]             # taille de l'image, en part du bouton (fit: center)
  opacity: 1.0                 # 0 (invisible) à 1
  slice: 12                    # fit: slice : largeur des bords gardés intacts
```

| `fit` | Rendu |
|---|---|
| `stretch` | l'image occupe **tout** le bouton, déformée si besoin |
| `cover` | l'image occupe tout le bouton **sans déformation**, ce qui dépasse est coupé |
| `contain` | l'image entière **sans déformation**, centrée (ou selon `position`), des bandes de `color` comblent le reste |
| `center` | l'image à la taille `size`, placée selon `position` et `offset` |
| `tile` | l'image répétée en mosaïque |
| `slice` | l'image découpée en 9 (« 9-slice ») : les coins gardent leur taille, les bords et le centre s'étirent ; pour des boutons de toutes tailles avec un cadre net |

- L'image est coupée selon la **forme** du bouton (coins arrondis, pilule).
- Écritures courtes : `background: images/x.png` (image, `fit: stretch`) ;
  `background: '#123456'` ou `background: menu-buttons` (couleur seule).
- Chaque état (`selected`, `disabled`, `pressed`) peut changer tout ou partie du fond :
  `selected: {background: {image: images/buttons/tile_on.png}}`. L'état `pressed` est montré un
  instant quand le bouton est validé ; sans image propre, il garde celle de l'état normal.
- **Couleur `transparent`** : rien n'est dessiné (`color: null` ne convient pas : une valeur
  `null` d'un fichier efface la valeur, celle par défaut revient). Pour un bouton fait d'un PNG
  détouré : `background: {color: transparent, image: ...}` dans chaque état, et `shape:
  rectangle` (des coins arrondis couperaient l'image).
- **Bouton fait d'images** : une image par état, et `text: {show: false}` pour ne pas écrire son
  nom (il reste son nom pour l'écran DMD et l'éditeur ; une icône éventuelle se met au milieu).
  `show` se règle aussi par état (`selected: {text: {show: true}}` : le nom seulement quand le
  bouton est choisi). Dans le configurateur : groupe « Image du bouton ».

```yaml
    - id: x01
      background: {image: images/buttons/x01.png, fit: stretch}
      selected: {background: {image: images/buttons/x01_on.png}}
      pressed:  {background: {image: images/buttons/x01_down.png}}
      text: {show: false}
```
- Un fond de menu se règle pareil ; `fit: cover` est conseillé (aucune déformation, quelle
  que soit la résolution).

### 7.3 Menus et boutons

```yaml
menus:
  main:
    title: game-type-menu
    subtitle: null
    background: images/background/main.png
    layout: tiles
    columns: 3
    style: tile
    buttons:
      - id: play                     # facultatif : par défaut, l'action
        action: local_game
        text: game-type-local
        icon: images/icons/target.png
        shortcut: [F1, l]
        exhibition: true             # visible en mode exposition (défaut : false)
      - action: menu:miscellaneous
        place: {x: 0.92, y: 0.04, width: 0.06, height: 0.08}   # placement libre (§7.5)
        style: classic
      - action: shutdown
        confirm: realy-stop          # demande de confirmation (texte)
        space_before: 1.5            # écart au-dessus, en hauteurs de bouton (dispositions auto)
```

Propriétés d'un menu, en plus de l'aspect : `title`, `subtitle`, `show_version` (`true` :
la version à sa place habituelle, en bas à droite ; ou un bloc qui la place et l'habille :
`{x, y, width, height, color, font}`, le texte remplit sa boîte ; dessinée aussi sur un fond
de menu) (version
en bas à droite du fond), `info` (informations écrites sur le fond : `ips`, `rpi_version`,
`version`), `remember` (`true` : le menu rouvre sur le dernier bouton choisi de sa liste).

Propriétés d'un bouton :

| Clé | Rôle |
|---|---|
| `id` | nom du bouton dans le menu (par défaut : l'action) |
| `action` | ce qu'il déclenche (§8) — **obligatoire** |
| `text`, `icon` | texte et icône (par défaut : ceux de l'action) |
| `shortcut` | touche ou liste de touches (défaut : aucun) |
| `exhibition` | visible en mode exposition (défaut `false`, sauf `local_game`, `trophies`, `gallery`) |
| `visible` | `false` le cache (il reste joignable par son raccourci) |
| `confirm` | texte d'une confirmation Oui/Non avant l'action |
| `place` | placement libre (§7.5) ; sinon placé par la disposition du menu |
| `footer` | bouton du bas de l'écran : `left`, `center` ou `right` (comme Retour, Enregistrer) ; un bouton sans `footer` dans la liste du fichier est placé avec les autres (le configurateur le fait quand on glisse un bouton du bas) |
| `logo` | image du dossier `images/logos_menu` du thème (disposition `tiles` du style `classic`) ; un dossier de ce nom contenant plusieurs images : l'une d'elles au hasard. Dans un menu dessiné par un style, il sert d'icône au bouton qui n'en a pas (et un bouton à logo sans `text` ne montre que son logo) |
| `requires` | condition d'affichage : `favorite_games` (seulement s'il existe des jeux favoris) |
| `dmd` | texte envoyé sur l'afficheur DMD quand le bouton est sélectionné |
| `order` | rang dans l'ordre logique (§9), par défaut sa place dans la liste |
| `space_before` | écart au-dessus (dispositions `list` et `grid`) |
| `space_left` | écart à gauche, en parts de colonne (`0.25` : un quart de colonne) |
| `span` | cases prises dans la disposition : `{columns: 2, rows: 1}` ; les autres boutons se rangent dans les cases libres (§12) |
| `cell` | case fixe dans la disposition : `{row: 1, column: 2}` (comptées depuis 0) ; le bouton y reste, les autres se rangent autour (§12) |
| `style`, et toute propriété de style | aspect de ce bouton seul ; l'aspect de son texte s'écrit `text: {text: game-type-local, size: 0.05}` (son texte dans `text`, comme les titres) et celui de son icône `icon: {image: images/icons/target.png, size: 0.6}` |

Changer un bouton sans réécrire la liste (fichier de l'utilisateur ou du thème) :

```yaml
menus:
  main:
    button_changes:
      gallery: {visible: false}
      play: {text: {fr: Jouer, en: Play}, shortcut: [F1, enter]}
```

### 7.4 Dispositions automatiques

```yaml
    layout: list           # list | grid | tiles
    area: {x: 0.25, y: 0.18, width: 0.5, height: 0.75}   # zone où se placent les boutons
    columns: 1             # grid et tiles (list = 1)
    button_size: {width: 1.0, height: 0.09}   # largeur : fraction de la colonne ; hauteur : de l'écran
    gap: {x: 0.02, y: 0.015}
    align: center          # center | top (si les boutons ne remplissent pas la zone)
    overflow: fit          # fit | pages | scroll (quand ils ne tiennent pas ; fit : un seul écran)
```

- **`list`** : une colonne, les boutons les uns sous les autres.
- **`grid`** : `columns` colonnes, rangées de gauche à droite puis de haut en bas ; même
  aspect que `list`.
- **`tiles`** : comme `grid`, mais boutons carrés ou rectangulaires plus grands, l'icône
  au-dessus du texte (`text.position: bottom` par défaut).

**Plusieurs zones de boutons** : en plus de la sienne, un menu peut avoir d'autres zones,
chacune avec sa disposition ; un bouton y va par `zone: <nom>` (sans `zone`, ou un nom
inconnu : la première zone) :

```yaml
    zones:
      gauche: {layout: list, area: {x: 0.04, y: 0.19, width: 0.25, height: 0.74},
               button_size: {height: 0.067}}
    buttons:
      - {action: gallery, zone: gauche}
```

**Largeur d'un bouton en parts de colonne** : `span: {columns: 0.5}` (demi-colonne ; aussi
`0.25`, `0.333`, `0.667`, `0.75`) ; deux demi-boutons tiennent côte à côte sur une ligne,
même dans une liste.

**Règle de placement** (identique dans le jeu et dans le configurateur, §12) : les boutons
non placés librement et visibles sont rangés dans l'ordre de la liste, ligne par ligne ; la
hauteur d'une ligne est `button_size.height` ; `space_before` ajoute un écart avant la ligne
de ce bouton ; l'ensemble est centré horizontalement dans `area`, et verticalement si
`align: center`. Le détail des calculs (arrondis compris) est donné au §12.

### 7.5 Placement libre

```yaml
        place: {x: 0.92, y: 0.04, width: 0.06, height: 0.08, anchor: top_left}
```

`x`, `y` : position du point d'ancrage (`top_left` par défaut, ou `center`, `top_right`,
`bottom_left`, `bottom_right`). Un bouton placé librement ne prend pas de place dans la
disposition automatique : les autres se rangent comme s'il n'existait pas.

## 8. Actions

Une action par bouton. Le jeu refuse une action inconnue (§3).

**Menu principal**

| Action | Effet (aujourd'hui) |
|---|---|
| `local_game` | partie simple (F1) |
| `network` | partie en réseau (F2) : d'abord le compte de la borne sur le serveur (le premier des serveurs favoris, *Divers* > *Favoris*), puis les parties à rejoindre ou en cours, la création d'une partie, le chat, le changement de serveur ou de compte. Les touches et textes de ses boutons sont dans les menus `online_lobby` et `online_chat` |
| `online_players` | panneau des joueurs en ligne, placé comme un bouton (*Modifier les écrans* > *Ajouter un élément* > *Joueurs en ligne*) : le nombre et les noms des joueurs connectés au serveur, les messages non lus ; sans compte enregistré sur la borne, un QR code pour en créer un et *S'identifier*. Redessiné chaque seconde ; validé : *Partie en réseau* |
| `network_join`, `network_create` | anciens boutons « rejoindre » et « créer une partie en réseau » : ils ouvrent le même écran que `network` ; un fichier qui les a encore ne reçoit pas le bouton `network` en plus |
| `trophies` | trophées et progression (F5) |
| `gallery` | galerie des photos et vidéos (F6) |
| `infos` | informations (F9) |
| `restart` | relancer RaspyDarts (F11) |
| `desktop` | revenir sur le bureau (F12) |
| `shutdown` | éteindre le Raspberry Pi (Échap, avec confirmation) |

**Divers**

| Action | Effet |
|---|---|
| `favorite_players` | prénoms favoris |
| `favorite_games` | jeux favoris |
| `favorite_servers` | serveurs favoris |
| `customization` | personnalisation |
| `animations` | animations des LED |
| `players_bank` | banque de prénoms |
| `backups` | sauvegardes |
| `exhibition` | mode exposition |
| `edit_screens` | éditeur des écrans sur la borne : l'écran principal, Paramètres ou Paramétrage affiché tel quel (son titre en haut, les touches du moment dans une bande fine en bas), chaque bouton déplacé, redimensionné par ses poignées, son raccourci changé ou retiré (une touche déjà prise par un autre bouton lui est retirée si on le veut), sa forme choisie (`shape` écrit sur le bouton : rectangle, bords arrondis, rond ; ou comme les autres boutons, celle du style), ajouté ou supprimé ; au clavier (une touche maintenue se répète), aux boutons, aux fléchettes (touches de la navigation, §9 ; `+`/`-` : pas, d'un pixel à 5 % de l'écran ; Valider : poignée suivante), à la souris ou au doigt (cliquer, glisser un bouton ou ses poignées) ; le numéro de version de l'écran principal déplacé et redimensionné de même (écrit dans `show_version`, sa couleur et sa police gardées ; supprimé : `show_version: false`, remis par *Ajouter un élément*) ; Retour ou le bouton Menu : ajouter un élément, enregistrer, quitter, disposer automatiquement (une zone d'abord : celle de tous les boutons, changée par ses poignées ou glissée ; puis colonnes, lignes, espacement, tous les boutons ou ceux dont le centre est dans la zone : rangés dans l'ordre de lecture, tous de la même taille), aimantation (oui par défaut : un bord ou un centre glissé à moins de 1 % de l'écran se colle aux bords et centres des autres boutons, aux bords et au milieu de l'écran, lignes bleues ; aux flèches, le déplacement s'arrête sur la première ligne rencontrée, l'appui suivant la dépasse), fond d'écran (une liste : celui du thème, les images de `images/background` et `images/menus` du thème et de `~/.raspydarts`, les `background*` du jeu, et en dernier *Importer un fond d'écran* ; celui choisi est montré sous les boutons, les flèches ou un toucher à gauche / à droite passent aux autres, sans répétition de touche ; Valider le garde, Retour rend l'ancien ; écrit dans `background` du menu, `fit: cover` ; celui du thème : `background` retiré ; importer : une image de la carte choisie dossier par dossier, en partant des clés USB montées sous `/media` ou `/mnt`, du dossier personnel ou de toute la carte ; copiée dans `~/.raspydarts/images/menus`, puis montrée sous les boutons comme ci-dessus). La liste des écrans propose aussi, en lignes comme celles de la personnalisation (valeur dans une liste), le thème et la police du jeu (appliqués aussitôt à tous les écrans ; ils ne sont plus dans la personnalisation). L'écran est figé à l'ouverture (chaque bouton reçoit un placement libre, §7.5) et s'enregistre dans le `menus.yaml` du thème (l'ancien gardé en `menus.yaml.bak`) |
| `coins` | monnayeur (include/ccoins.py), derrière son mot de passe (haché, hors de raspydarts.cfg, fichier verrouillé `chattr +i`) : mode (désactivé, crédits par partie, temps de jeu), entrée (une broche libre d'un MCP23017 : impulsions gardées par l'interruption du MCP, jamais perdues ; pas de GPIO, ils servent aux grandes cibles), crédits ou minutes par pièce, joueurs par partie (libre ou N : 4 joueurs pour une partie de 2 = 2 crédits), prix par type (partie simple, réseau ; 0 = gratuit) et par jeu, crédits donnés à la main, compteur de pièces (une pièce insérée s'affiche : le test) ; crédits ou temps restants en rouge sur chaque écran (position et taille du bandeau réglables) ; pas assez de crédits au lancement : « Insérez une pièce » ; mode temps : le temps s'écoule pendant les parties, à zéro la partie s'arrête à la fin de la volée sauf pièce |
| `usb_pads` | « Paramétrage boutons et molettes USB » (menu Paramétrage, avant Test des boutons) : boîtiers USB de touches et de molettes (1189:8890, puce CH57x) : le boîtier choisi (plusieurs peuvent être branchés, reconnus par leur port USB), ses nombres de touches et de molettes, « Programmer le boîtier » (le jeu écrit ses propres codes dans le boîtier : livré, tout envoie « C »), puis une colonne par élément (touches ; molette gauche, appui, appui long — tenu 0,6 s —, droite) avec le bouton qu'il donne dans les menus et en partie (Valider, Retour, Haut… / Joueur suivant, Fléchette ratée, Arrêter la partie, volume du jeu ou du système) ; un élément actionné s'allume à l'écran. Pendant une saisie, la molette change le nombre (plus vite quand on tourne vite) ou fait défiler les caractères d'un texte (avec « < » effacer et « OK ») ; l'appui garde le caractère ou valide le nombre, l'appui long valide. Réglages dans `~/.raspydarts/usb_pads.json` |
| `raspy2dmd` | l'afficheur DMD Raspy2DMD sur la borne (panneaux pilotés par un Raspberry Pico en USB) : installé, QR code de sa page web, message d'essai, mire de test du Pico, horloge, démo (commandes publiées sur le sujet MQTT `raspy2dmd`), « Vérifier les mises à jour » (dernière release de Raspy2DMD comparée à `/Raspy2DMD/web/VERSION` ; acceptée, son moteur est relancé et l'installe, progression sur le DMD) ; pas installé, il propose de l'installer (mode « Pico seul », en tâche de fond) et suit l'installation (barre par étape, étape, temps écoulé), puis le démarre |
| `update` | vérifier les mises à jour |

**Paramètres**

| Action | Effet |
|---|---|
| `setup_buttons` | boutons |
| `setup_pins_leds` | broches des LED |
| `setup_leds` | LED de la cible |
| `setup_segment_colors` | couleurs des segments |
| `setup_camera` | webcam |
| `setup_encoder` | encodeur (nouveau, §10) |
| `test_buttons`, `test_target`, `test_toys` | tests |
| `reset` | réinitialisation |

**Générales**

| Action | Effet |
|---|---|
| `menu:<id>` | ouvre le menu `<id>` ; un menu imbriqué s'écrit `menu:settings/display` |
| `category:<nom>` | ouvre la liste des jeux de la catégorie `classic`, `fun`, `sport`, `favorites` |
| `game:<Nom>` | partie de ce jeu : joueurs, puis directement ses options (ex. `game:Cricket`, `game:High_Score`) ; un jeu inconnu est ignoré |
| `favorite:fav<N>` | lance le favori n° N (§13) |
| `back` | revient à l'écran précédent |

Les menus livrés : `main`, `miscellaneous`, `settings`, `categories`, et les menus dont les
boutons sont fabriqués par le jeu (§7.6).

### 7.6 Menus dont le jeu fournit les boutons

`games` (liste des jeux d'une catégorie), `options` (options d'un jeu), `players` (joueurs),
`wizard` (assistant de configuration) : leurs boutons viennent du jeu, le fichier n'en règle
que l'aspect, pas la liste (un `buttons:` y est ignoré).

| Réglage | `games` | `options`, `players`, `wizard` |
|---|---|---|
| `background` (§7.3 bis) | ✓ | ✓ |
| `title`, `subtitle` (texte et aspect, §7.1) | ✓ | ✓ (remplace le titre de chaque étape de l'assistant) |
| `style` : couleurs | ✓ | ✓ |
| `style` : forme, images, icône, ombre, `scale` | ✓ (tuiles) | — |
| `columns`, `area`, `gap`, `align` | ✓ | — (disposition propre à l'écran) |

- **`games`** : avec un style autre que `classic`, chaque jeu est une tuile du style, le
  logo du jeu en icône et son nom en texte ; un jeu qui ne convient pas au nombre de joueurs
  prend l'état `disabled`. Tous les jeux tiennent sur l'écran, dans `area` (par défaut la
  gauche de l'écran, la description du jeu à droite) : tuiles carrées (logo au-dessus du
  nom) ou, s'il y a trop de rangées pour des carrés, aussi larges que les colonnes (logo à
  gauche du nom). Avec `style: classic`, les logos de toujours ; `columns` s'applique aussi.
- **`options`, `players`, `wizard`** : leurs rangées (raccourci, texte, valeur, cases à
  cocher…) gardent leur disposition ; le style leur donne ses couleurs, le temps de l'écran :
  `background.color` (rangées), `selected.background.color` (rangée choisie),
  `disabled.background.color` (avertissements), `text.color` et `selected.text.color`,
  `border` (bordure de la rangée choisie), `shape`/`radius` (arrondi des rangées et des
  boutons du bas), `text.font` ; `shortcuts.color` colore la case du raccourci.

## 9. Navigation

```yaml
navigation:
  up: [up, btn:up]
  down: [down, btn:down]
  left: [left, btn:left]
  right: [right, btn:right]
  next: [tab]              # ordre logique (comme l'encodeur)
  previous: []
  validate: [enter, space, btn:validate]
  back: [escape, backspace, btn:back]
```

Deux logiques :

- **Flèches (haut, bas, gauche, droite) : géométrie.** On va au bouton le plus proche dans la
  direction demandée, d'après les **bords** des boutons à l'écran (placement libre compris),
  pas leurs centres : sous un bouton large comme l'écran, toute la rangée suivante est
  « en dessous », même loin de son centre. Candidats : les boutons au-delà de son bord dans
  cette direction (un léger chevauchement est admis : le bouton choisi est dessiné plus grand).
  Ceux qui lui font face (une partie de sa largeur pour haut/bas, de sa hauteur pour
  gauche/droite) passent d'abord : la rangée la plus proche, puis celui qui lui fait le plus
  face (en part de sa propre largeur, au dixième près), puis le premier dans le sens de
  lecture (le plus à gauche, le plus haut). Pour haut et bas seulement, les autres ensuite :
  `écart + 2 × écart perpendiculaire entre leurs bords` (un bouton proche en diagonale passe
  avant un bouton lointain aligné) ; droite et gauche restent sur la rangée (en diagonale, un
  placement libre tournait en rond sur trois boutons). Aucun candidat : droite et gauche continuent dans le sens de
  lecture (au bout d'une rangée, le premier bouton de la rangée suivante ; gauche, le
  précédent ; après le dernier, le premier) : tout le menu se parcourt avec droite seule.
  Haut et bas font le tour, vers le plus éloigné qui lui fait face du côté opposé.
- **`next` / `previous` et l'encodeur : ordre logique.** L'ordre des boutons dans le fichier
  (ou `order:`), en passant d'une ligne à la suivante, et en faisant le tour au bout.

`validate` déclenche le bouton sélectionné ; `back` revient à l'écran précédent. Un
raccourci (§7.3) déclenche son bouton directement, même s'il n'est pas sélectionné.

Touche secrète `c` (dans les menus ; en partie elle reste la fléchette de triche) : le raccourci de
chaque bouton s'affiche, même si le thème les cache ; un nouvel appui les cache de nouveau. Cela dure
jusqu'à la sortie du jeu. Pour cette raison, `c` ne peut pas être donné comme raccourci dans l'éditeur.

Avec la souris ou au doigt, un clic déclenche le bouton touché.

## 10. Encodeur rotatif

```yaml
encoder:
  device: auto             # auto = celui choisi dans Paramètres > Encodeur, ou son nom
  turn: [previous, next]   # sens de rotation : [sens inverse, sens horaire]
  press: validate
  long_press: back         # appui long (secondes : long_press_time)
  long_press_time: 0.6
```

L'encodeur USB est lu **à part** (son périphérique est réservé au jeu) : ses touches ne
passent pas par le clavier, il n'est jamais confondu avec lui, et l'appui long existe. Il
suit l'**ordre logique** (§9). L'écran Paramètres > Encodeur le détecte : « Tournez
l'encodeur ».

## 11. Clavier à l'écran

```yaml
virtual_keyboard:
  mode: touch              # touch (seulement au doigt) | always | never
  style: classic
```

`touch` : un champ de saisie touché **au doigt** ouvre un pavé numérique (broches, nombres ;
avec `,` et `.` pour les LED) ou un clavier (textes : AZERTY si le jeu est en français,
QWERTY sinon, avec Maj, Espace, `. - _ : @`, Effacer, Valider, Annuler) ; un clic de souris
ou une frappe au clavier ne l'ouvrent pas, et taper au clavier le referme. Si le clavier est
fermé, toucher le champ l'ouvre. Toutes les saisies du jeu en profitent (broches, nombres,
prénoms, mot de passe de la galerie, serveurs…).

## 12. Règles de placement exactes

Partagées par le jeu et le configurateur, et vérifiées par un test qui compare, pour une
série de fichiers d'exemple et pour 1024×600 et 1920×1080, les rectangles des boutons
calculés des deux côtés (ils doivent être identiques au pixel).

1. Les valeurs sont converties en pixels de l'écran réel (§4), arrondies à l'entier le plus
   proche (0,5 vers le haut), **une seule fois**, au moment de la conversion.
2. Boutons de la disposition automatique : visibles, non placés librement, dans l'ordre
   logique.
3. Largeur d'une colonne : `(area.width − (columns − 1) × gap.x) / columns` ; largeur
   d'un bouton : `button_size.width × colonne`.
4. Cases : les boutons à case fixe (`cell`) prennent d'abord la leur (une case déjà prise :
   le bouton se range avec les autres) ; puis chaque bouton prend `span.columns ×
   span.rows` cases (1 × 1 par défaut ; une colonne compte 12 parts : `0.5` en prend 6, et
   un bouton commence sur ses pas, une demie sur une demie), à la première place libre en lisant ligne par ligne depuis le haut (un bouton suivant peut
   donc combler un trou laissé avant). `span.columns` plus grand que `columns` : il prend
   toutes les colonnes, et sa largeur reste celle de `span.columns` colonnes, centrée.
   Largeur d'un bouton sur `n` colonnes : `button_size.width × colonne + (n − 1) ×
   (colonne + gap.x)` ; hauteur sur `m` lignes : du haut de sa première ligne au bas de
   sa dernière.
5. Ligne `i` : `y = area.y + Σ(hauteurs et écarts des lignes précédentes) + space_before`
   (les `space_before` des boutons qui commencent sur cette ligne).
6. Bloc entier centré dans `area` (horizontalement toujours, verticalement si
   `align: center`) ; une ligne de boutons d'une case, sans case fixe, remplie depuis la
   gauche et non traversée par un bouton de plusieurs lignes, est centrée (une dernière ligne
   incomplète aussi).
   Une ligne laissée vide reste vide (un espace voulu). `space_left` : un espace vide à
   gauche du bouton, en parts de colonne, pris avec ses cases (le bouton rétrécit si sa
   ligne est pleine). Chaque zone (`zones`) se place de même, dans sa propre `area`.
7. Plus de lignes que n'en tient `area` : par défaut (`overflow: fit`), **un seul écran** : les
   boutons sont réduits (jamais agrandis) pour que toutes les lignes y tiennent — un bouton
   ajouté à un menu plein par une nouvelle version ne crée pas de deuxième page.
   `overflow: pages` coupe en pages (les lignes
   reliées par un bouton de plusieurs lignes restent ensemble ; en bas à
   droite : la page affichée et des flèches vers les pages d'avant et d'après ; les
   flèches du clavier passent d'une page à l'autre), `scroll` fait défiler pour garder le
   bouton sélectionné visible.

## 13. Favoris

Les favoris se **créent dans RaspyDarts**, dans **Divers > Jeux favoris** (la liste où l'on
coche les jeux favoris) :

- **cocher un jeu** demande « définir ses options ? » (Oui / Non) :
  - **Oui** ouvre l'écran des options du jeu (boutons Retour et Sauvegarder) ; le jeu
    favori démarrera ensuite **sans écran d'options**, avec celles-ci, quel que soit le
    chemin (liste d'une catégorie, catégorie Favoris…). Puis : « l'enregistrer aussi comme
    favori numéroté ? » (ci-dessous) ; **Retour** dans les options ramène à la question ;
  - **Non** : jeu favori sans options fixées, demandées au moment de jouer ;
- **choisir un jeu déjà favori** propose « Modifier les options » ou « Retirer des
  favoris » (Retour dans les options ramène à ce choix).

Dans la liste, un jeu favori dont les options sont définies porte la marque **Opt.** (légende
en bas de l'écran).

Comme les jeux cochés, les options ne sont enregistrées qu'avec **Sauvegarder**.

### Favoris numérotés `fav1`, `fav2`… (boutons du menu principal)

Un jeu favori dont les options sont définies peut aussi être enregistré comme **favori
numéroté** : son numéro (1 à 9 : `fav1` à `fav9` ; un favori déjà enregistré est remplacé),
puis comment choisir ses joueurs. Il n'apparaît dans le menu principal que si le fichier de
menus lui donne un bouton (`favorite:fav1`, ci-dessous) ; la question le dit. Joueurs :

- `choose` : les **joueurs favoris** (Divers > Joueurs favoris), mémorisés avec le favori ;
- `generic` : Joueur 1, Joueur 2… ;
- `last` : les derniers joueurs choisis, ajustés au nombre prévu, avec un avertissement
  s'il y en a trop (« les joueurs en trop seront retirés ») ou pas assez (« il manquera des
  joueurs » : la partie se joue avec ceux qu'il y a), et le choix de continuer ;
- `ask` : choisis au lancement, dans l'écran des joueurs, puis la partie démarre avec les
  options du favori (ni liste des jeux, ni options).

Le fichier de menus ne fait que placer ces boutons :

```yaml
      - action: favorite:fav1        # texte et logo du jeu par défaut
        shortcut: [F7, '1']
```

Un bouton `favorite:` lance la partie aussitôt : ni choix des joueurs (sauf `ask`), ni liste
des jeux, ni options. Un favori vide (ou dont le jeu n'existe plus) affiche son bouton grisé (état
`disabled`), qui ne fait rien. Un favori ne peut pas être le premier écran (`start`) : sa
partie recommencerait à chaque retour.

### Fichier

Tout est écrit dans `~/.raspydarts/favorites.yaml` (gardé par les mises à jour) :

```yaml
games:                    # options des jeux favoris (Jeux favoris)
  Cricket: {max_round: 20, optioncrazy: false}
fav1:                     # bouton fav1 du menu principal
  game: Cricket
  options: {max_round: 20, optioncrazy: false}
  players: 2
  mode: choose            # choose | generic | last | ask
  names: [Rémi, Bob]      # choose seulement
```

Les petits écrans de ces choix sont des menus du fichier dont le jeu fournit les boutons :
`question` (Oui / Non ; titre : la question), `favorite_game` (titre : le jeu),
`favorite_save` et `favorite_players` (titre, sous-titre, aspect).

## 14. Exemple complet

```yaml
version: 1
resolution: auto

defaults:
  background: {image: images/background/menu.png, fit: cover}
  style: classic

styles:
  tile:
    shape: rounded
    radius: 18
    background: {image: images/buttons/tile.png, fit: slice, slice: 16}
    text: {size: 0.035, color: '#FFFFFF', position: bottom, shadow: true}
    selected: {background: {image: images/buttons/tile_on.png}, scale: 1.06}

menus:
  main:
    title: game-type-menu
    layout: tiles
    columns: 3
    area: {x: 0.1, y: 0.2, width: 0.8, height: 0.7}
    style: tile
    buttons:
      - action: local_game
        icon: images/icons/target.png
        shortcut: [F1, l]
        exhibition: true
      - action: favorite:fav1
        shortcut: F7
        exhibition: true
      - action: favorite:fav2
        shortcut: F8
        exhibition: true
      - action: trophies
        shortcut: F5
        exhibition: true
      - action: gallery
        shortcut: F6
        exhibition: true
      - action: network
        shortcut: F2
      - action: menu:miscellaneous
        icon: images/icons/gear.png
        shortcut: F4
        style: classic
        text: {size: 0}                       # icône seule
        place: {x: 0.94, y: 0.03, width: 0.05, height: 0.08}
      - action: shutdown
        shortcut: escape
        confirm: realy-stop
        visible: false                        # caché, joignable par Échap
```
