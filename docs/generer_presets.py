"""
Modeles de cartes de la page de configuration (docs/index.html), tires du code du jeu :
a relancer quand une carte est ajoutee ou modifiee dans include/cconfig.py.
Usage : python docs/generer_presets.py   (depuis la racine du depot)
"""
import ast
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from include import cconfig  # noqa: E402

# Choix de l'assistant (Screen.wizard) : code -> (nom affiche, modele, cible a l'interieur)
CARDS = {
    'Ji': ('RaspyCard', 'JiCardConfig', False),
    'Jiz': ('RaspyZcard', 'JizCardConfig', False),
    'Ji3': ('RaspYDartsCard', 'Ji2CardConfig', False),
    'Ji2': ('RaspyCard V4', 'Ji2CardConfig', False),
    'GB': ('RaspyBoard', 'GBCardConfig', True),
    'ED': ('ED900', 'ED900Config', True),
    'Jo': ('Cible ED110 7*10', 'JoCardConfig', False),
    'Jo416': ('Cible Pro 4*16', 'Jo416CardConfig', False),
    'Ch': ('La Chti Raspycard', 'ClkCardConfig', False),
    'Jt': ('Carte de Julien V1', 'JtCardConfig', False),
    'Jt2': ('Carte de Julien V2', 'Jt2CardConfig', False),
    'Mm': ('MM-Workshop DartCab', 'JiCardConfig', False),
    'MMWVdarts': ('MM-Workshop VDarts', 'MMWorksVDartsCardConfig', False),
    'Re': ('DartBoard', 'JoCardConfig', False),
}
# Menus de l'assistant : groupes puis cartes
GROUPS = [
    ('Cartes de Jimmy', ['Ji', 'Jiz', 'Ji3', 'Ji2', 'GB', 'ED']),
    ('Carte de Joffrey', ['Jo', 'Jo416']),
    ('', ['Ch', 'Jt', 'Jt2', 'Mm', 'MMWVdarts', 'Re']),
]


def extender_defaults():
    """ DEFAULTS de include/cgpio_extender.py (le module demande le materiel : lu sans l'importer) """
    tree = ast.parse(open(os.path.join(ROOT, 'include', 'cgpio_extender.py'), encoding='utf-8').read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'DEFAULTS':
            return ast.literal_eval(node.value)
    raise SystemExit('DEFAULTS introuvable dans cgpio_extender.py')


presets = {}
for code, (name, model, interior) in CARDS.items():
    config = getattr(cconfig, model)
    presets[code] = {
        'name': name,
        'inputs': config['INPUT'],
        'outputs': config['OUTPUT'],
        'keys': config['KEYS'],
        'extended': {key: str(value) for key, value in config['EXTENDED'].items()},
        'interior': interior,
        'target_leds': 'mmworks' if code == 'MMWVdarts' else 'ji',
    }

def po_labels(keys):
    """ Noms des boutons, lumieres et jouets dans les langues du jeu (locales/*/pydarts.po) """
    labels = {}
    for language in ('fr_FR', 'en_GB', 'de_DE', 'es_ES', 'it_IT'):
        texts, msgid = {}, None
        for line in open(os.path.join(ROOT, 'locales', language, 'LC_MESSAGES', 'pydarts.po'), encoding='utf-8'):
            line = line.strip()
            if line.startswith('msgid "'):
                msgid = line[7:-1]
            elif line.startswith('msgstr "') and msgid in keys:
                texts[msgid] = line[8:-1].replace('\\"', '"')
        labels[language[:2]] = texts
    return labels


data = {
    'groups': GROUPS,
    'cards': presets,
    'target_leds': {'ji': cconfig.JiLedsConfig, 'mmworks': cconfig.MMWorkshopVdartsLedsConfig},
    # Boutons, lumieres et jouets de la carte d'extension, et leur broche par defaut
    'extender': {key: str(value) for key, value in extender_defaults().items()},
    'inputs': list(cconfig.DefaultConfig['Raspberry_BoardPinsIns']),
    'outputs': list(cconfig.DefaultConfig['Raspberry_BoardPinsOuts']),
    'keys': list(cconfig.DefaultConfig['SectionKeys']),
    'labels': po_labels(set(extender_defaults())),
}
path = os.path.join(ROOT, 'docs', 'presets.js')
with open(path, 'w', encoding='utf-8', newline='\n') as file:
    file.write('// Genere par docs/generer_presets.py a partir de include/cconfig.py : ne pas modifier a la main\n')
    file.write(f'const PRESETS = {json.dumps(data, ensure_ascii=False, separators=(',', ':'))};\n')
print(f'{path} : {len(presets)} cartes')
