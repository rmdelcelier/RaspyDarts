"""
Donnees et images du configurateur de menus (docs/configurateur-menus.html), tirees du jeu :
- docs/menus-data.js : menus par defaut (menus/defaults.yaml), actions, jeux par categorie,
  textes traduits, couleurs et polices des themes clear et sombre ;
- docs/assets/ : vignettes des fonds et des logos (images allegees), polices.
A relancer quand defaults.yaml, un theme, un logo ou les traductions changent.
Usage : python docs/generer_menus.py   (depuis la racine du depot ; le theme sombre est lu dans
.raspydarts_example/themes/sombre)
"""
import ast
import configparser
import json
import os
import re
import shutil
import sys

import yaml
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from include import cmenus  # noqa: E402
from include import cmenustyle  # noqa: E402

DOCS = os.path.join(ROOT, 'docs')
ASSETS = os.path.join(DOCS, 'assets')
EXAMPLE_THEMES = os.path.join(ROOT, '.raspydarts_example', 'themes')
LANGUAGES = {'fr': 'fr_FR', 'en': 'en_GB', 'de': 'de_DE', 'es': 'es_ES', 'it': 'it_IT', 'nl': 'nl_NL'}
# Personnaliser le theme (include/cthemeeditor.py) : ce que le configurateur en reprend
THEME_EDITOR = ('PLATES', 'GROUPS', 'NONE_ALLOWED', 'TRANSPARENT_ALLOWED', 'SHORTCUT_TAGS', 'SHORTCUT_CHOICES', 'ALIGN_TAGS', 'ALIGN_CHOICES',
                'VALIGN_TAGS', 'VALIGN_CHOICES', 'POSITION_TAGS', 'SHAPE_TAGS', 'RADIUS_TAGS', 'SHAPE_LIMITS', 'PALETTE',
                'PERSO_NAME')
# Taille des vignettes (le plus grand cote) : fonds, logos
BACKGROUND_SIZE = 1280
LOGO_SIZE = 256


def colorset_clear():
    ''' ColorSet['clear'] de include/ColorSets.py (lu sans pygame) '''
    tree = ast.parse(open(os.path.join(ROOT, 'include', 'ColorSets.py'), encoding='utf-8').read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Subscript):
            target = node.targets[0]
            if getattr(target.value, 'id', '') == 'ColorSet' and ast.literal_eval(target.slice) == 'clear':
                return ast.literal_eval(node.value)
    raise SystemExit('ColorSet clear introuvable')


def theme_editor():
    ''' Les planches de Personnaliser le theme (include/cthemeeditor.py, lu sans pygame) '''
    tree = ast.parse(open(os.path.join(ROOT, 'include', 'cthemeeditor.py'), encoding='utf-8').read())
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in THEME_EDITOR:
            values[node.targets[0].id] = eval(compile(ast.Expression(node.value), 'cthemeeditor', 'eval'), {'range': range})  # noqa: S307
    missing = set(THEME_EDITOR) - set(values)
    if missing:
        raise SystemExit(f'cthemeeditor : {missing} introuvable(s)')
    # Une planche : son nom, ses etiquettes (gauche puis droite, sans doublon), leurs points et sa maquette
    drawings = mockup_drawings()
    plates = []
    for name, _drawer, left, right in values['PLATES']:
        tags = []
        for tag, _x, _y in list(left) + list(right):
            if tag not in tags:
                tags.append(tag)
        plates.append({'name': name, 'tags': tags, 'points': [[tag, x, y] for tag, x, y in list(left) + list(right)],
                       'drawing': drawings[_drawer]})
    return {'plates': plates, 'mockup': MOCKUP_FORMAT, 'groups': [[name, list(names)] for name, names in values['GROUPS']],
            'noneAllowed': list(values['NONE_ALLOWED']),
            # Transparente : (r, g, b, 0) dans Colorset_perso.cfg, la case non dessinee
            'transparentAllowed': list(values['TRANSPARENT_ALLOWED']), 'shortcutTags': list(values['SHORTCUT_TAGS']),
            'shortcutChoices': [list(item) for item in values['SHORTCUT_CHOICES']],
            'alignTags': list(values['ALIGN_TAGS']), 'alignChoices': [list(item) for item in values['ALIGN_CHOICES']],
            'valignTags': list(values['VALIGN_TAGS']), 'valignChoices': [list(item) for item in values['VALIGN_CHOICES']],
            'positionTags': list(values['POSITION_TAGS']), 'shapeTags': list(values['SHAPE_TAGS']),
            'radiusTags': list(values['RADIUS_TAGS']), 'shapeLimits': values['SHAPE_LIMITS'],
            'palette': [list(color) for color in values['PALETTE']], 'file': values['PERSO_NAME']}


# Maquettes de Personnaliser le theme : chaque draw_* de cthemeeditor joue sur un enregistreur
# (un faux pygame, sans fenetre). Coordonnees : parts de la maquette (x, w par sa largeur ; y, h
# par sa hauteur) ; les longueurs en pixels du jeu (arrondis, epaisseurs) : parts de sa hauteur.
# La maquette de reference : celle d'un ecran 1920 x 1080 (912 x 668 pixels)
REF_SCREEN = (1920, 1080)
REF_MOCKUP = (int(REF_SCREEN[0] * 7.6 / 16), int(REF_SCREEN[1] * 9.9 / 16))
ZOOM = 100  # maquette enregistree 100 fois plus grande : les int() du jeu ne decalent rien
MOCKUP_FORMAT = {
    'reference': {'screen': list(REF_SCREEN), 'mockup': list(REF_MOCKUP)},
    'units': "x, w, cx, x1, x2, r : parts de la largeur de la maquette ; y, h, cy, y1, y2 : parts de sa hauteur ; "
             "radius, width, borderWidth, outlineWidth : parts de sa hauteur (pixels du jeu / 668)",
    'frame': {'color': [90, 90, 90], 'width': round(2 / REF_MOCKUP[1], 4)},
    'background': [40, 40, 44],
    'rules': {
        'tag': "une couleur nommee (etiquette du Colorset) ; une etiquette a Aucune (None) : rien n'est dessine",
        'fill': "fond de toute la maquette : couleur de tag ; background sans tag, ou si tag est a Aucune",
        'box': "rectangle plein de tag (arrondi radius), puis, si border, son contour de border (epaisseur borderWidth)",
        'swatch': "si tag est a Aucune : contour outline (epaisseur outlineWidth, arrondi radius) ; sinon box de tag",
        'rect': "rectangle de couleur (tag ou color fixe) ; width 0 : plein, sinon contour de cette epaisseur",
        'text': "police du jeu, taille = max(8 px, (height si donne, sinon h) x size) ; un texte plus large que "
                "w - textSqueeze est ecrase en largeur a w - textSqueeze ; centre dans le rectangle, ou align left : "
                "a x + textMargin, right : a droite - textMargin ; valign top : colle en haut, bottom : en bas",
        'circle': "disque de couleur fixe color, centre (cx, cy), rayon r",
        'line': "trait de tag (ou color), de (x1, y1) a (x2, y2), epaisseur width",
        'shapedRow': "item de menu avec les formes du moment, s = referenceHeight (1080). Arrondi R : border-radius "
                     "'max' -> h / 2, sinon min(h / 2, border-radius / s) (une valeur illisible : 0). chosen : contour menu-border d'epaisseur "
                     "B = 2 x border-size / s (si B > 0, arrondi R), puis l'interieur = le rectangle reduit de B + P de "
                     "chaque cote (P = 2 x padding / s), plein de menu-selected, arrondi max(0, R - B - P), texte label "
                     "(size 0.6) en menu-text-white dans l'interieur. Sinon : plein de menu-buttons arrondi R, texte "
                     "label en menu-text-black",
        'shapedButton': "bouton du bas : plein de menu-buttons, arrondi button-radius 'max' -> h / 2, sinon "
                        "min(h / 2, 2 x button-radius / s) (une valeur illisible : 0) ; texte label (size 0.6) en menu-text-black",
        'exampleRow': "item de menu dessine comme le theme : box menu-buttons (arrondi radius). Raccourci = valeur de "
                      "<prefix>-shortcuts : '' -> 'F1', None -> pas de raccourci, sinon ce texte. Avec raccourci : a "
                      "gauche un rectangle de hauteur h et de largeur shortcutRatio x h (en pixels), box menu-shortcut "
                      "(arrondi radius) et le raccourci en menu-text-white (size 0.6). Le texte : le reste de l'item, "
                      "moins les marges <prefix>-text-position (gauche, droite, haut, bas, en % de cette boite, "
                      "chacune ramenee entre 0 et 90 ; si deux marges opposees depassent 90 a elles deux, la seconde "
                      "(droite, bas) est reduite d'autant ; une valeur illisible : pas de marge) ; label en "
                      "menu-text-black, size 0.55, height = la hauteur de l'item (avant les marges), align = "
                      "<prefix>-text-align, valign = <prefix>-text-valign (en minuscules ; center sinon)",
    },
    'constants': {'textSqueeze': round(4 / REF_MOCKUP[0], 4), 'textMargin': round(6 / REF_MOCKUP[0], 4),
                  'shortcutRatio': 1.1, 'referenceHeight': REF_SCREEN[1]},
    'texts': "les textes des maquettes sont ceux du jeu, en francais (le jeu ne les traduit pas)",
}


class _Rect:
    ''' pygame.Rect : ce que les maquettes en utilisent '''
    def __init__(self, *args):
        if len(args) == 1:
            args = tuple(args[0])
        self.x, self.y, self.width, self.height = (int(value) for value in args)

    def __iter__(self):
        return iter((self.x, self.y, self.width, self.height))

    w = property(lambda self: self.width)
    h = property(lambda self: self.height)
    right = property(lambda self: self.x + self.width)
    bottom = property(lambda self: self.y + self.height)
    centerx = property(lambda self: self.x + self.width // 2)
    centery = property(lambda self: self.y + self.height // 2)
    center = property(lambda self: (self.centerx, self.centery))
    topleft = property(lambda self: (self.x, self.y))
    bottomright = property(lambda self: (self.right, self.bottom))

    def inflate(self, dx, dy):
        return _Rect(self.x - dx // 2, self.y - dy // 2, self.width + dx, self.height + dy)


class _Tag(tuple):
    ''' La couleur d'une etiquette : son nom, pas sa valeur '''
    def __new__(cls, name):
        made = super().__new__(cls, (0, 0, 0))
        made.name = name
        return made


def _x(value):
    return round(value / (REF_MOCKUP[0] * ZOOM), 4)


def _y(value):
    return round(value / (REF_MOCKUP[1] * ZOOM), 4)


def _area(rect):
    rect = _Rect(rect)
    return {'x': _x(rect.x), 'y': _y(rect.y), 'w': _x(rect.width), 'h': _y(rect.height)}


def _length(pixels):
    ''' Une longueur en pixels du jeu (maquette de reference) : part de sa hauteur '''
    return round(pixels / REF_MOCKUP[1], 4)


def _color(color):
    return {'tag': color.name} if isinstance(color, _Tag) else {'color': [int(part) for part in color[:3]]}


def mockup_drawings():
    ''' {draw_* : ses operations dans l'ordre du dessin} pour les planches de cthemeeditor '''
    import importlib.util
    import types
    ops = []

    def rect(_surface, color, area, width=0, border_radius=0):
        ops.append({'op': 'rect', **_area(area), **_color(color), 'width': _length(width),
                    'radius': _length(border_radius)})

    def line(_surface, color, start, end, width=1):
        ops.append({'op': 'line', 'x1': _x(start[0]), 'y1': _y(start[1]), 'x2': _x(end[0]), 'y2': _y(end[1]),
                    **_color(color), 'width': _length(width)})

    def circle(_surface, color, center, radius, width=0):
        ops.append({'op': 'circle', 'cx': _x(center[0]), 'cy': _y(center[1]), 'r': _x(radius), **_color(color)})

    fake = types.ModuleType('pygame')
    fake.Rect = _Rect
    fake.draw = types.SimpleNamespace(rect=rect, line=line, circle=circle)
    saved = sys.modules.get('pygame')
    sys.modules['pygame'] = fake
    try:
        spec = importlib.util.spec_from_file_location('cthemeeditor_maquettes',
                                                      os.path.join(ROOT, 'include', 'cthemeeditor.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        if saved is None:
            del sys.modules['pygame']
        else:
            sys.modules['pygame'] = saved

    class Recorder(module.ThemeEditor):
        ''' Les appels des maquettes enregistres ; ce qui depend des valeurs du moment : en parametres '''
        def color(self, tag):
            return _Tag(tag)

        def fill(self, mockup, tag=None):
            ops.append({'op': 'fill', **({'tag': tag} if tag else {})})

        def box(self, area, tag, radius=6, border=None):
            op = {'op': 'box', **_area(area), 'tag': tag, 'radius': _length(radius)}
            if border is not None:
                op.update(border=border, borderWidth=_length(3))
            ops.append(op)

        def swatch(self, area, tag):
            ops.append({'op': 'swatch', **_area(area), 'tag': tag, 'radius': _length(8),
                        'outline': [90, 90, 90], 'outlineWidth': _length(2)})

        def text(self, text, area, tag, size=0.6, align='center', valign='center', height=None):
            op = {'op': 'text', 'text': text, **_area(area), 'tag': tag, 'size': size, 'align': align, 'valign': valign}
            if height is not None:
                op['height'] = _y(height)
            ops.append(op)

        def shaped_row(self, row, label, chosen, scale):
            ops.append({'op': 'shapedRow', **_area(row), 'label': label, 'chosen': chosen})

        def shaped_button(self, button, label, scale):
            ops.append({'op': 'shapedButton', **_area(button), 'label': label})

        def example_row(self, prefix, label, row, values=None):
            ops.append({'op': 'exampleRow', **_area(row), 'prefix': prefix, 'label': label, 'radius': _length(6)})

    recorder = Recorder.__new__(Recorder)
    recorder.screen = types.SimpleNamespace(screen=None)
    recorder.size = (REF_SCREEN[0] * ZOOM, REF_SCREEN[1] * ZOOM)
    recorder.work = {}
    drawings = {}
    for _name, drawer, _left, _right in module.PLATES:
        ops.clear()
        getattr(recorder, drawer)(_Rect(0, 0, REF_MOCKUP[0] * ZOOM, REF_MOCKUP[1] * ZOOM))
        drawings[drawer] = list(ops)
    return drawings


def colorset_file(path):
    ''' Un Colorset.cfg de theme (comme cconfig.read_colorset) '''
    parser = configparser.ConfigParser(inline_comment_prefixes='#')
    parser.optionxform = str
    parser.read(path, encoding='utf-8')
    values = {}
    for option in parser.options('Colorset'):
        try:
            values[option] = ast.literal_eval(parser.get('Colorset', option))
        except (ValueError, SyntaxError):
            values[option] = parser.get('Colorset', option)
    return values


def json_value(value):
    ''' Valeurs du colorset en JSON : tuples -> listes '''
    if isinstance(value, tuple):
        return list(value)
    return value


def thumbnail(source, target, size, opaque):
    ''' Vignette : jpg pour une image opaque, webp (avec transparence) sinon '''
    os.makedirs(os.path.dirname(target), exist_ok=True)
    image = Image.open(source)
    image.thumbnail((size, size))
    if opaque:
        image.convert('RGB').save(target, 'JPEG', quality=82)
    else:
        image.convert('RGBA').save(target, 'WEBP', quality=82)


def images_of(folder, prefix):
    ''' Images d'un dossier (fonds et logos de menu) : {chemin relatif : fichier} '''
    found = {}
    for sub in ('background', 'logos_menu'):
        base = os.path.join(folder, 'images')
        for root, _, files in os.walk(os.path.join(base, sub)):
            for name in files:
                if name.lower().endswith(('.png', '.jpg', '.jpeg')):
                    full = os.path.join(root, name)
                    found[os.path.relpath(full, folder).replace('\\', '/')] = full
    return found


def po_texts(lang_dir):
    ''' Traductions d'un .po : {msgid : msgstr} (chaines sur une ou plusieurs lignes) '''
    texts, msgid, msgstr, current = {}, None, None, None
    path = os.path.join(ROOT, 'locales', lang_dir, 'LC_MESSAGES', 'pydarts.po')
    for line in open(path, encoding='utf-8'):
        line = line.strip()
        if line.startswith('msgid '):
            if msgid is not None and msgstr is not None:
                texts[msgid] = msgstr
            msgid, msgstr, current = ast.literal_eval(line[6:]), None, 'id'
        elif line.startswith('msgstr '):
            msgstr, current = ast.literal_eval(line[7:]), 'str'
        elif line.startswith('"') and current == 'id':
            msgid += ast.literal_eval(line)
        elif line.startswith('"') and current == 'str':
            msgstr += ast.literal_eval(line)
    if msgid is not None and msgstr is not None:
        texts[msgid] = msgstr
    return texts


def main():
    defaults = yaml.safe_load(open(os.path.join(ROOT, 'menus', 'defaults.yaml'), encoding='utf-8'))

    # Jeux par categorie (comme Screen.get_games_list)
    games = {}
    for category in ('classic', 'fun', 'sport'):
        names = []
        for root, _, files in os.walk(os.path.join(ROOT, 'games', category)):
            for name in files:
                base, extension = os.path.splitext(name)
                if extension == '.py' and base != '__init__':
                    names.append(base)
        games[category] = sorted(names)

    # Images : officielles (images/) et themes ; vignettes dans docs/assets
    if os.path.isdir(os.path.join(ASSETS, 'img')):
        shutil.rmtree(os.path.join(ASSETS, 'img'))
    sources = {'official': (ROOT, images_of(ROOT, 'official'))}
    for theme in ('clear', 'sombre'):
        folder = os.path.join(EXAMPLE_THEMES, theme)
        sources[theme] = (folder, images_of(folder, theme) if os.path.isdir(folder) else {})
    images = {}
    for owner, (folder, found) in sources.items():
        images[owner] = {}
        for relative, full in sorted(found.items()):
            opaque = 'background' in relative and not relative.lower().endswith('.png') or relative.endswith('background.png')
            extension = '.jpg' if opaque else '.webp'
            target = os.path.join(ASSETS, 'img', owner, os.path.splitext(relative)[0] + extension)
            thumbnail(full, target, BACKGROUND_SIZE if 'background' in relative else LOGO_SIZE, opaque)
            images[owner][relative] = os.path.relpath(target, DOCS).replace('\\', '/')
    # Fonds officiels d'un theme (background.png, background_<theme>) : images/ a la racine
    for name in ('background.png', 'background_clear.png'):
        full = os.path.join(ROOT, 'images', name)
        target = os.path.join(ASSETS, 'img', 'official', 'images', os.path.splitext(name)[0] + '.jpg')
        thumbnail(full, target, BACKGROUND_SIZE, True)
        images['official'][f'images/{name}'] = os.path.relpath(target, DOCS).replace('\\', '/')

    # Polices : celles du jeu et celle du theme sombre
    fonts_dir = os.path.join(ASSETS, 'fonts')
    os.makedirs(fonts_dir, exist_ok=True)
    fonts = {}
    for name in sorted(os.listdir(os.path.join(ROOT, 'fonts'))):
        if name.lower().endswith(('.ttf', '.otf')):
            shutil.copyfile(os.path.join(ROOT, 'fonts', name), os.path.join(fonts_dir, name))
            fonts[name] = f'assets/fonts/{name}'

    # Themes : couleurs (clear, puis le Colorset.cfg du theme), police, fond
    clear = colorset_clear()
    themes = {}
    for theme in ('clear', 'sombre'):
        colors = dict(clear)
        font = 'MaPolice.ttf'
        cfg = os.path.join(EXAMPLE_THEMES, theme, 'other', 'Colorset.cfg')
        if theme != 'clear' and os.path.isfile(cfg):
            colors.update(colorset_file(cfg))
            if colors.get('font'):
                font_file = os.path.basename(str(colors['font']))
                source = os.path.join(EXAMPLE_THEMES, theme, 'font', font_file)
                if os.path.isfile(source):
                    shutil.copyfile(source, os.path.join(fonts_dir, font_file))
                    fonts[font_file] = f'assets/fonts/{font_file}'
                    font = font_file
        colors.pop('font', None)
        background = 'images/background/background.png' if 'images/background/background.png' in images.get(theme, {}) \
            else 'images/background.png'
        # Ses menus, comme le jeu les lit (themes/<theme>/menus.yaml, puis menu/menus.yaml) : le
        # configurateur part d'eux pour ce theme
        theme_menus = {}
        for path in (os.path.join(EXAMPLE_THEMES, theme, cmenus.FILE_NAME), os.path.join(EXAMPLE_THEMES, theme, cmenus.THEME_FILE)):
            if os.path.isfile(path):
                theme_menus = cmenus.merge(theme_menus, yaml.safe_load(open(path, encoding='utf-8')) or {})
        themes[theme] = {'colors': {key: json_value(value) for key, value in colors.items()},
                         'font': font, 'background': background, 'menus': theme_menus}

    # Textes : les cles des menus par defaut, des boutons et des ecrans du jeu
    keys = set()

    def collect(value):
        if isinstance(value, dict):
            for item in value.values():
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)
        elif isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_.-]+', value):
            keys.add(value)
    collect(defaults)
    keys.update(['back', 'save', 'continue', 'yes', 'no', 'game-list', 'players-names', 'players-names-subtitle',
                 'game-options', 'game-type-menu', 'categories', 'exit', 'realy-stop'])
    texts = {}
    for lang, lang_dir in LANGUAGES.items():
        all_texts = po_texts(lang_dir)
        prefixed = {key for key in all_texts if key.startswith(('game-type', 'favorite', 'dmd-', 'theme-'))}
        texts[lang] = {key: all_texts[key] for key in sorted(keys | prefixed) if key in all_texts and all_texts[key]}

    data = {
        'defaults': defaults,
        'actions': sorted(cmenus.ACTIONS),
        'prefixes': list(cmenus.ACTION_PREFIXES),
        'games': games,
        'themes': themes,
        'images': images,
        'fonts': fonts,
        'texts': texts,
        'styleDefaults': cmenustyle.STYLE_DEFAULTS,
        'layoutDefaults': cmenustyle.LAYOUT_DEFAULTS,
        'gapDefault': cmenustyle.GAP_DEFAULT,
        'themeEditor': theme_editor(),
    }
    with open(os.path.join(DOCS, 'menus-data.js'), 'w', encoding='utf-8', newline='\n') as file:
        file.write('// Genere par docs/generer_menus.py : ne pas modifier a la main\n')
        file.write('const MENUS_DATA = ' + json.dumps(data, ensure_ascii=False, indent=1) + ';\n')

    total = sum(os.path.getsize(os.path.join(root, name)) for root, _, files in os.walk(ASSETS) for name in files)
    print(f"menus-data.js : {os.path.getsize(os.path.join(DOCS, 'menus-data.js')) // 1024} ko ; "
          f"assets : {total // 1024} ko ; images {sum(len(v) for v in images.values())}, polices {len(fonts)}")


if __name__ == '__main__':
    main()
