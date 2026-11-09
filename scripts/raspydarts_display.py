#!/usr/bin/python3
"""
RaspyDarts : adapte le mode HDMI du firmware a l'ecran branche (affichage gere par le
firmware, comme sous Buster). Installe en /usr/local/bin/raspydarts-display par
scripts/reglages_systeme.sh, lance a chaque demarrage (raspydarts-display.service).

Le firmware choisit seul le mode des ecrans standards. Pour un ecran qu'il met dans un autre
mode que son mode natif (lu dans l'EDID), ce mode est impose dans config.txt, puis le Pi
redemarre une fois :
  - de preference par son numero de mode standard (hdmi_group / hdmi_mode, liste de
    tvservice -m CEA / DMT) : le firmware prend ses propres timings, exacts ;
  - sinon (ex : 7 pouces en 1024x600) par des timings calcules depuis l'EDID (hdmi_timings).
Un mode impose est d'abord a l'essai : il est garde des qu'on se sert de la borne pendant le
demarrage qui l'utilise (le jeu lance « raspydarts-display --valider » a la premiere action :
flechette, bouton, touche, toucher). Eteinte ou redemarree sans aucune action (ecran noir),
la borne revient au choix du firmware et ne reessaie plus pour cet ecran.
La sortie HDMI est toujours forcee (hdmi_force_hotplug=1) : ecran allume apres le Pi, ou
lent a repondre.

  raspydarts-display                 au demarrage (service)
  raspydarts-display --diagnostic    ce qui est vu de l'ecran et ce qui est impose
  raspydarts-display --reinitialiser retour au choix du firmware (prend effet au redemarrage)
  raspydarts-display --valider       le mode a l'essai convient (lance par le jeu)
  raspydarts-display --modes         les modes proposes (annonces par l'ecran, puis courants)
  raspydarts-display --choisir G M   mode choisi (groupe 1 CEA / 2 DMT, numero), a l'essai
  raspydarts-display --choisir auto  retour au choix automatique

Choix manuel (Parametrage > Resolution de l'ecran, ou ecran.txt depose a la racine de la carte
SD : « resolution=1024x768 », « frequence=60 » facultatif, ou « resolution=auto ») : utile
quand l'ecran est branche par un convertisseur (HDMI vers VGA), qui annonce sa propre
resolution et non celle de l'ecran (image coupee). Il est lui aussi a l'essai : sans action sur
la borne au demarrage qui l'utilise, le reglage precedent est remis. Garde ensuite quel que
soit l'ecran branche, jusqu'a un autre choix.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

CONFIG = '/boot/firmware/config.txt'
STATE = '/var/lib/raspydarts/display'
# Mode a l'essai pendant ce demarrage : le jeu le valide a la premiere action
TRIAL = '/run/raspydarts-display-essai'
TVSERVICE = '/opt/vc/bin/tvservice'
EDID_FILE = '/run/raspydarts-edid.dat'
BEGIN = '# --- RaspyDarts : mode de l ecran (debut, gere par raspydarts-display) ---'
END = '# --- RaspyDarts : mode de l ecran (fin) ---'
# Toujours dans le bloc : la sortie HDMI meme sans ecran detecte au demarrage
BASE = ['hdmi_force_hotplug=1']
# Rapports d'image connus de hdmi_timings (dernier parametre)
ASPECTS = {1: 4 / 3, 2: 14 / 9, 3: 16 / 9, 4: 5 / 4, 5: 16 / 10, 6: 15 / 9, 7: 21 / 9, 8: 64 / 27}
# Reglage remis si le mode choisi a la main n'est pas confirme
PREVIOUS = STATE + '.avant-choix'
BOOT_DIRS = ('/boot/firmware', '/boot')
CHOICE_FILES = ('ecran.txt', 'ecran.txt.txt', 'écran.txt', 'écran.txt.txt')
CHOICE_RESULT = 'ecran-resultat.txt'
# Modes courants des moniteurs (DMT), proposes meme si l'ecran (ou son convertisseur) ne les
# annonce pas : 4/3, 5/4, 16/10, 16/9
COMMON_MODES = [(2, 4, 640, 480, 60), (2, 9, 800, 600, 60), (2, 16, 1024, 768, 60), (2, 32, 1280, 960, 60),
                (2, 35, 1280, 1024, 60), (2, 51, 1600, 1200, 60), (2, 28, 1280, 800, 60), (2, 47, 1440, 900, 60),
                (2, 58, 1680, 1050, 60), (2, 85, 1280, 720, 60), (2, 39, 1360, 768, 60), (2, 82, 1920, 1080, 60)]
MODE_LINE = re.compile(r'(\((?P<flags>[^)]*)\)\s*)?mode (?P<mode>\d+): (?P<w>\d+)x(?P<h>\d+) @ (?P<rate>\d+)Hz'
                       r'.*?(?P<scan>progressive|interlaced)')


def log(message):
    print(f"raspydarts-display : {message}", flush=True)


def tvservice(*args):
    return subprocess.run([TVSERVICE, *args], capture_output=True, text=True, check=False)


def native_mode(edid):
    """ Mode natif : premier descripteur de timing detaille de l'EDID """
    d = edid[54:72]
    clock = (d[0] | d[1] << 8) * 10000
    if clock == 0:
        return None
    h_active = d[2] | (d[4] & 0xF0) << 4
    h_blank = d[3] | (d[4] & 0x0F) << 8
    v_active = d[5] | (d[7] & 0xF0) << 4
    v_blank = d[6] | (d[7] & 0x0F) << 8
    h_front = d[8] | (d[11] & 0xC0) << 2
    h_sync = d[9] | (d[11] & 0x30) << 4
    v_front = (d[10] >> 4) | (d[11] & 0x0C) << 2
    v_sync = (d[10] & 0x0F) | (d[11] & 0x03) << 4
    if d[17] & 0x80:
        return None    # entrelace : laisse au firmware
    h_pol = 1 if d[17] & 0x02 else 0
    v_pol = 1 if d[17] & 0x04 else 0
    rate = round(clock / ((h_active + h_blank) * (v_active + v_blank)))
    aspect = min(ASPECTS, key=lambda key: abs(ASPECTS[key] - h_active / v_active))
    timings = (f"{h_active} {h_pol} {h_front} {h_sync} {h_blank - h_front - h_sync} "
               f"{v_active} {v_pol} {v_front} {v_sync} {v_blank - v_front - v_sync} "
               f"0 0 0 {rate} 0 {clock} {aspect}")
    return h_active, v_active, rate, timings


def standard_mode(width, height, rate):
    """
    Le mode standard de cette resolution parmi ceux que l'ecran declare (tvservice -m), en
    balayage progressif, a la frequence la plus proche : (groupe, numero, frequence) ou None.
    Groupe 1 (CEA, televisions) avant 2 (DMT, moniteurs), sauf mode marque natif
    """
    found = []
    for group, name in ((1, 'CEA'), (2, 'DMT')):
        for line in tvservice('-m', name).stdout.splitlines():
            match = MODE_LINE.search(line)
            if match and match['scan'] == 'progressive' and (int(match['w']), int(match['h'])) == (width, height):
                native = 'native' in (match['flags'] or '')
                found.append((not native, abs(int(match['rate']) - rate), group, int(match['mode']),
                              int(match['rate'])))
    if not found:
        return None
    _not_native, _gap, group, mode, mode_rate = min(found)
    return group, mode, mode_rate


def read_state():
    """ (empreinte de l'ecran, etat) : auto, essai, essai-vu, impose, refuse """
    try:
        with open(STATE, encoding='utf-8') as state:
            fingerprint, kind = state.read().split()[:2]
    except (OSError, ValueError):
        return None, None
    # Versions avant le 06/11 : « timings » = mode impose et garde
    return fingerprint, {'timings': 'impose'}.get(kind, kind)


def write_state(fingerprint, kind):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, 'w', encoding='utf-8') as state:
        state.write(f"{fingerprint} {kind}\n")


def imposed_lines():
    """ Les lignes du mode impose dans le bloc gere (sans les lignes de base) """
    try:
        with open(CONFIG, encoding='utf-8') as config:
            text = config.read()
    except OSError:
        return []
    block = re.search(re.escape(BEGIN) + r'(.*?)' + re.escape(END), text, flags=re.S)
    if block is None:
        return []
    return [line for line in block.group(1).splitlines()
            if line.strip() and line.strip() != '[all]' and line.strip() not in BASE]


def write_block(lines):
    """ Bloc gere dans config.txt : les lignes de base, puis celles du mode impose """
    with open(CONFIG, encoding='utf-8') as config:
        text = config.read()
    new = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END) + r'\n?', '', text, flags=re.S)
    if not new.endswith('\n'):
        new += '\n'
    # Section [all] : s'applique quel que soit le modele de Pi
    new += BEGIN + '\n[all]\n' + '\n'.join(BASE + list(lines)) + '\n' + END + '\n'
    if new != text:
        with open(CONFIG + '.raspydarts', 'w', encoding='utf-8') as config:
            config.write(new)
        os.replace(CONFIG + '.raspydarts', CONFIG)


def reboot(reason):
    log(f"{reason} : redemarrage")
    subprocess.run(['systemctl', '--no-block', 'reboot'], check=False)


def read_screen():
    """ (empreinte, mode natif, resolution actuelle) de l'ecran branche, ou None et la raison """
    if tvservice('-d', EDID_FILE).returncode != 0 or not os.path.exists(EDID_FILE):
        return None, "pas d'ecran (EDID illisible)"
    with open(EDID_FILE, 'rb') as edid_file:
        edid = edid_file.read()
    if len(edid) < 128 or edid[:8] != b'\x00\xff\xff\xff\xff\xff\xff\x00':
        return None, "EDID invalide"
    mode = native_mode(edid)
    if mode is None:
        return None, "pas de mode natif utilisable dans l'EDID"
    current = re.search(r'(\d+)x(\d+) @', tvservice('-s').stdout)
    current = (int(current.group(1)), int(current.group(2))) if current else None
    return (hashlib.sha1(edid[:128]).hexdigest()[:16], mode, current), None


def diagnostic():
    print(f"Etat HDMI      : {tvservice('-s').stdout.strip()}")
    screen, reason = read_screen()
    if screen is None:
        print(f"Ecran          : {reason}")
    else:
        fingerprint, (width, height, rate, timings), current = screen
        print(f"Ecran          : {fingerprint}, natif {width}x{height} @ {rate} Hz (timings : {timings})")
        print(f"Mode standard  : {standard_mode(width, height, rate) or 'aucun pour cette resolution'}")
    print(f"Memorise       : {' '.join(str(value) for value in read_state())}")
    print(f"Impose         : {imposed_lines() or 'rien (choix du firmware)'}")
    print(f"A l'essai      : {'oui' if os.path.exists(TRIAL) else 'non'}")
    for name in ('CEA', 'DMT'):
        print(f"--- modes {name} declares par l'ecran")
        print(tvservice('-m', name).stdout.rstrip())


def announced_modes():
    """ Les modes progressifs que l'ecran (ou son convertisseur) annonce : (groupe, numero, l, h, frequence, natif) """
    modes = []
    for group, name in ((1, 'CEA'), (2, 'DMT')):
        for line in tvservice('-m', name).stdout.splitlines():
            match = MODE_LINE.search(line)
            if match and match['scan'] == 'progressive':
                modes.append((group, int(match['mode']), int(match['w']), int(match['h']), int(match['rate']),
                              'native' in (match['flags'] or '')))
    return modes


def all_modes():
    """
    Les modes proposes : ceux annonces, puis les modes courants absents (meme resolution et
    frequence) : (groupe, numero, l, h, frequence, origine) ; origine : natif, ecran, courant
    """
    modes, seen = [], set()
    for group, mode, width, height, rate, native in announced_modes():
        if (width, height, rate) not in seen:
            seen.add((width, height, rate))
            modes.append((group, mode, width, height, rate, 'natif' if native else 'ecran'))
    for group, mode, width, height, rate in COMMON_MODES:
        if (width, height, rate) not in seen:
            seen.add((width, height, rate))
            modes.append((group, mode, width, height, rate, 'courant'))
    return sorted(modes, key=lambda item: (item[2] * item[3], item[4]))


def current_mode():
    """ (groupe, numero) du mode en cours, ou None """
    match = re.search(r'\[(CEA|DMT) \((\d+)\)', tvservice('-s').stdout)
    return (1 if match.group(1) == 'CEA' else 2, int(match.group(2))) if match else None


def choose(group, mode):
    """
    Mode choisi a la main, a l'essai : le reglage actuel est garde de cote pour etre remis si
    la borne n'est pas utilisee au demarrage suivant
    """
    fingerprint, kind = read_state()
    if kind not in ('choix-essai', 'choix-vu') or not os.path.exists(PREVIOUS):
        os.makedirs(os.path.dirname(PREVIOUS), exist_ok=True)
        with open(PREVIOUS, 'w', encoding='utf-8') as previous:
            json.dump({'lines': imposed_lines(), 'fingerprint': fingerprint, 'kind': kind}, previous)
    write_block([f'hdmi_group={group}', f'hdmi_mode={mode}'])
    write_state('manuel', 'choix-essai')
    log(f"mode {'CEA' if group == 1 else 'DMT'} {mode} choisi, a l'essai au prochain demarrage")


def choose_auto():
    """ Retour au choix automatique (celui du firmware, puis le mode natif de l'ecran) """
    write_block([])
    for path in (STATE, PREVIOUS):
        if os.path.exists(path):
            os.remove(path)
    log("retour au choix automatique : prend effet au prochain redemarrage")


def restore_previous():
    """ Le mode choisi n'a pas ete confirme : le reglage d'avant est remis """
    try:
        with open(PREVIOUS, encoding='utf-8') as previous:
            saved = json.load(previous)
    except (OSError, ValueError):
        saved = {}
    write_block(saved.get('lines') or [])
    if saved.get('kind') and saved.get('fingerprint'):
        write_state(saved['fingerprint'], saved['kind'])
    elif os.path.exists(STATE):
        os.remove(STATE)
    if os.path.exists(PREVIOUS):
        os.remove(PREVIOUS)


def mode_for(width, height, rate=None):
    """ Le mode propose de cette resolution (annonce de preference), a la frequence la plus proche """
    found = [item for item in all_modes() if (item[2], item[3]) == (width, height)]
    if not found:
        return None
    return min(found, key=lambda item: (abs(item[4] - (rate or 60)), item[5] == 'courant'))


def read_choice_file():
    """
    ecran.txt depose sur la partition de demarrage : (chemin, partition, texte) ou None.
    Ecrit par le Bloc-notes : UTF-8 avec ou sans BOM, UTF-16, ANSI
    """
    for boot in BOOT_DIRS:
        try:
            names = os.listdir(boot)
        except OSError:
            continue
        for name in names:
            if name.lower() in CHOICE_FILES:
                path = os.path.join(boot, name)
                with open(path, 'rb') as handle:
                    data = handle.read()
                if data[:2] in (b'\xff\xfe', b'\xfe\xff'):
                    text = data.decode('utf-16')
                else:
                    try:
                        text = data.decode('utf-8-sig')
                    except UnicodeDecodeError:
                        text = data.decode('cp1252', errors='replace')
                return path, boot, text
    return None


def apply_choice_file():
    """
    ecran.txt : le choix qu'il donne est applique (a l'essai), le fichier remplace par un
    compte rendu (ecran-resultat.txt). True : un redemarrage est necessaire
    """
    found = read_choice_file()
    if found is None:
        return False
    path, boot, text = found
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line[0] in '#;':
            continue
        if '=' in line or ':' in line:
            key, value = re.split(r'\s*[=:]\s*', line, maxsplit=1)
            values[key.strip().lower()] = value.strip().strip('"\'')
        else:
            values.setdefault('resolution', line)
    wanted = values.get('resolution', values.get('mode', '')).lower().replace(' ', '')
    rate_text = re.sub(r'\D', '', values.get('frequence', values.get('fr\u00e9quence', values.get('rate', ''))))
    rate = int(rate_text) if rate_text else None
    match = re.fullmatch(r'(\d+)[x\*](\d+)(?:@(\d+)(?:hz)?)?', wanted)
    changed = False
    if wanted in ('auto', 'automatique'):
        choose_auto()
        changed = True
        report = "Resolution : choix automatique (au prochain demarrage)"
    elif match:
        width, height = int(match.group(1)), int(match.group(2))
        mode = mode_for(width, height, int(match.group(3)) if match.group(3) else rate)
        if mode is None:
            sizes = sorted({(item[2], item[3]) for item in all_modes()})
            report = (f"Resolution {width}x{height} inconnue : rien n'a change. Possibles : "
                      + ', '.join(f'{w}x{h}' for w, h in sizes))
        else:
            choose(mode[0], mode[1])
            changed = True
            report = (f"Resolution {mode[2]}x{mode[3]} @ {mode[4]} Hz ({'CEA' if mode[0] == 1 else 'DMT'} {mode[1]}) "
                      "a l'essai : gardee des la premiere action sur la borne, sinon le reglage precedent revient")
    else:
        report = "resolution= manquante ou illisible (ex : resolution=1024x768) : rien n'a change"
    try:
        os.remove(path)
    except OSError:
        pass
    try:
        with open(os.path.join(boot, CHOICE_RESULT), 'w', encoding='utf-8', newline='\r\n') as handle:
            handle.write('RaspyDarts : ecran.txt\n\n' + report + '\n')
    except OSError:
        pass
    log(report)
    return changed


def main(args):
    if '--diagnostic' in args:
        diagnostic()
        return
    if '--reinitialiser' in args:
        choose_auto()
        return
    if '--modes' in args:
        current = current_mode()
        for group, mode, width, height, rate, origin in all_modes():
            print(f"{group} {mode} {width} {height} {rate} {origin}{' actuel' if (group, mode) == current else ''}")
        return
    if '--choisir' in args:
        rest = args[args.index('--choisir') + 1:]
        if rest[:1] == ['auto']:
            choose_auto()
        elif len(rest) >= 2 and rest[0] in ('1', '2') and rest[1].isdigit():
            choose(int(rest[0]), int(rest[1]))
        else:
            log("--choisir : auto, ou groupe (1 CEA, 2 DMT) et numero")
            sys.exit(2)
        return
    if '--valider' in args:
        fingerprint, kind = read_state()
        if kind == 'essai-vu':
            write_state(fingerprint, 'impose')
            log("mode a l'essai garde (la borne est utilisee)")
        if kind == 'choix-vu':
            write_state(fingerprint, 'choix')
            if os.path.exists(PREVIOUS):
                os.remove(PREVIOUS)
            log("mode choisi garde (la borne est utilisee)")
        if os.path.exists(TRIAL):
            os.remove(TRIAL)
        return

    if os.path.exists('/dev/dri/card0') or not os.path.exists(TVSERVICE):
        log("affichage gere par Linux (KMS) : rien a faire")
        return
    # Lignes de base a jour (prennent effet au prochain demarrage, sans redemarrer pour elles)
    write_block(imposed_lines())
    # Resolution deposee sur la carte SD (ecran.txt) : appliquee, a l'essai
    if apply_choice_file():
        reboot("resolution deposee sur la carte (ecran.txt)")
        return
    # Mode choisi a la main (meme sans EDID lisible : convertisseur) : a l'essai, garde, ou le
    # reglage precedent remis
    known, kind = read_state()
    if kind == 'choix-essai':
        write_state(known, 'choix-vu')
        with open(TRIAL, 'w', encoding='utf-8'):
            pass
        os.chmod(TRIAL, 0o644)
        log("mode choisi a l'essai : garde a la premiere action sur la borne")
        return
    if kind == 'choix-vu':
        restore_previous()
        reboot("mode choisi non confirme au demarrage precedent (ecran noir ?), reglage precedent remis")
        return
    if kind == 'choix':
        log(f"mode choisi a la main : {imposed_lines()}, garde")
        return
    screen, reason = read_screen()
    if screen is None:
        log(f"{reason} : rien a faire")
        return
    fingerprint, (width, height, rate, timings), current = screen
    known, kind = read_state()
    now = f"{current[0]}x{current[1]}" if current else "inconnu"

    if known == fingerprint and kind == 'essai':
        # Premier demarrage avec le mode impose : garde si la borne est utilisee
        write_state(fingerprint, 'essai-vu')
        with open(TRIAL, 'w', encoding='utf-8'):
            pass
        os.chmod(TRIAL, 0o644)
        log(f"mode impose a l'essai (ecran en {now}) : garde a la premiere action sur la borne")
        return
    if known == fingerprint and kind == 'essai-vu':
        # Demarrage precedent avec le mode impose sans aucune action : ecran noir, retour au firmware
        write_block([])
        write_state(fingerprint, 'refuse')
        reboot("mode impose non confirme au demarrage precedent (ecran noir ?), retour au choix du firmware")
        return

    if current == (width, height):
        log(f"ecran en mode natif {width}x{height} @ {rate} Hz")
        if known != fingerprint:
            write_state(fingerprint, 'impose' if imposed_lines() else 'auto')
        return
    if known == fingerprint and kind in ('impose', 'refuse'):
        log(f"ecran en {now} (natif {width}x{height}) : {'mode deja impose' if kind == 'impose' else 'mode natif refuse auparavant'}, rien de plus")
        return
    if imposed_lines():
        # Mode impose pour un autre ecran : le firmware choisit d'abord seul pour celui-ci
        write_block([])
        write_state(fingerprint, 'auto')
        reboot(f"nouvel ecran ({now}, natif {width}x{height}), mode impose retire")
        return
    standard = standard_mode(width, height, rate)
    if standard is not None:
        group, mode, mode_rate = standard
        write_block([f'hdmi_group={group}', f'hdmi_mode={mode}'])
        how = f"mode standard {'CEA' if group == 1 else 'DMT'} {mode} ({width}x{height} @ {mode_rate} Hz)"
    else:
        write_block(['hdmi_group=2', 'hdmi_mode=87', f'hdmi_timings={timings}', 'hdmi_drive=2'])
        how = f"timings de l'EDID ({width}x{height} @ {rate} Hz)"
    write_state(fingerprint, 'essai')
    reboot(f"ecran en {now} au lieu de son mode natif : {how} impose, a l'essai")


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except Exception as error:    # jamais bloquer le demarrage
        log(f"erreur : {error}")
        sys.exit(0)
