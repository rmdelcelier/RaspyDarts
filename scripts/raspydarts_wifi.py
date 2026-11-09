#!/usr/bin/env python3
"""
RaspyDarts : Wi-Fi déposé sur la partition de démarrage (la carte SD lue sous Windows).

Sous Raspberry Pi OS Trixie, wpa_supplicant.conf posé à la racine de la carte n'est plus lu
(le Wi-Fi est géré par NetworkManager). Ce script, lancé au démarrage avant NetworkManager
(raspydarts-wifi.service, installé par scripts/reglages_systeme.sh), lit à la racine de la
partition de démarrage :

  wifi.txt                  ssid=MaBox            (plusieurs réseaux : un ssid= par réseau,
                            motdepasse=secret      le premier est préféré)
                            pays=FR
                            cache=oui             (réseau masqué, facultatif)

  wpa_supplicant.conf       le fichier de Buster, tel quel : country=, network={ ssid= psk= }

Chaque réseau devient une connexion NetworkManager (prioritaire sur celles qui existaient,
celle du même nom est remplacée), le pays du Wi-Fi est réglé et le Wi-Fi débloqué. Le fichier
est ensuite supprimé (il contient le mot de passe) ; wifi-resultat.txt, à sa place, dit ce
qui a été fait (sans le mot de passe).
"""

import glob
import os
import re
import subprocess
import sys
import uuid

BOOT_DIRS = ('/boot/firmware', '/boot')
CONNECTIONS = '/etc/NetworkManager/system-connections'
PREFIX = 'raspydarts-wifi-'
RESULT = 'wifi-resultat.txt'
# Higher than the connections made by Raspberry Pi Imager (cloud-init, netplan : 0)
PRIORITY = 100
DEFAULT_COUNTRY = 'FR'

PASSWORD_KEYS = ('motdepasse', 'mot_de_passe', 'mot de passe', 'password', 'psk', 'cle', 'clé', 'key')
COUNTRY_KEYS = ('pays', 'country')
HIDDEN_KEYS = ('cache', 'caché', 'masque', 'masqué', 'hidden')
YES = ('1', 'oui', 'o', 'yes', 'y', 'true', 'vrai')


def run(*command):
    """
    A command of the system ; absent (iw, rfkill, raspi-config...) : not done, False
    """
    try:
        return subprocess.run(list(command), check=False, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode == 0
    except OSError:
        return False


def read_text(path):
    """
    A file written by the Notepad of Windows : UTF-8 (with or without BOM), UTF-16 or ANSI
    """
    with open(path, 'rb') as handle:
        data = handle.read()
    if data[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return data.decode('utf-16')
    try:
        return data.decode('utf-8-sig')
    except UnicodeDecodeError:
        return data.decode('cp1252', errors='replace')


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
        return value[1:-1]
    return value


def parse_wifi_txt(text):
    """
    wifi.txt : key=value (or key: value), one ssid= per network
    """
    networks, country, current = [], None, None
    for line in text.splitlines():
        line = line.strip()
        if not line or line[0] in '#;':
            continue
        match = re.match(r'^([^=:]+?)\s*[=:]\s*(.*)$', line)
        if not match:
            continue
        key, value = match.group(1).strip().lower(), unquote(match.group(2))
        if key == 'ssid':
            current = {'ssid': value, 'psk': '', 'hidden': False}
            networks.append(current)
        elif key in COUNTRY_KEYS:
            country = value
        elif current is not None and key in PASSWORD_KEYS:
            current['psk'] = value
        elif current is not None and key in HIDDEN_KEYS:
            current['hidden'] = value.strip().lower() in YES
    return networks, country


def parse_wpa_supplicant(text):
    """
    wpa_supplicant.conf of Buster : country=XX, network={ ssid="..." psk="..." ... }
    """
    country = None
    match = re.search(r'^\s*country\s*=\s*(\S+)', text, re.MULTILINE)
    if match:
        country = unquote(match.group(1))
    networks = []
    for block in re.findall(r'network\s*=\s*\{(.*?)\}', text, re.DOTALL):
        fields = {}
        for line in block.splitlines():
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                fields[key.strip().lower()] = value.strip()
        if 'ssid' not in fields:
            continue
        ssid = fields['ssid']
        # ssid="text" or the name in hexadecimal (without quotes)
        if ssid.startswith('"'):
            ssid = unquote(ssid)
        else:
            try:
                ssid = bytes.fromhex(ssid).decode('utf-8')
            except ValueError:
                pass
        psk = fields.get('psk', '')
        # psk="phrase" or the key already computed (64 hexadecimal characters, kept as it is)
        psk = unquote(psk) if psk.startswith('"') else psk
        if fields.get('key_mgmt', '').upper() == 'NONE':
            psk = ''
        networks.append({'ssid': ssid, 'psk': psk, 'hidden': fields.get('scan_ssid', '0') == '1',
                         'priority': int(fields['priority']) if fields.get('priority', '').isdigit() else None})
    return networks, country


def keyfile_escape(value):
    """
    A value of a keyfile of NetworkManager (GKeyFile)
    """
    value = value.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
    if value.startswith(' '):
        value = '\\s' + value[1:]
    return value


def ssid_bytes(ssid):
    """
    The name of the network as bytes for the keyfile (12;34;...;) : a name written as text that
    looks like numbers separated by ; would be read as bytes by NetworkManager
    """
    return ';'.join(str(byte) for byte in ssid.encode('utf-8')) + ';'


def ssid_of(path):
    """
    The name of the network of a keyfile, written as text or as bytes
    """
    try:
        for line in read_text(path).splitlines():
            if line.startswith('ssid='):
                value = line[5:].strip()
                if re.fullmatch(r'(\d{1,3};)+\d{0,3}', value):
                    return bytes(int(byte) for byte in value.split(';') if byte).decode('utf-8', errors='replace')
                return value.replace('\\s', ' ').replace('\\\\', '\\')
    except (OSError, ValueError):
        pass
    return None


def write_connection(network, priority):
    """
    The connection of NetworkManager of a network ; the one of the same name made before (by
    this script, or by Raspberry Pi Imager / by hand in /etc) is replaced
    """
    ssid = network['ssid']
    escaped = keyfile_escape(ssid)
    for path in glob.glob(os.path.join(CONNECTIONS, '*.nmconnection')):
        if ssid_of(path) == ssid:
            os.remove(path)
    name = re.sub(r'[^A-Za-z0-9_.-]+', '_', ssid).strip('_') or 'reseau'
    path = os.path.join(CONNECTIONS, f'{PREFIX}{name}.nmconnection')
    lines = ['[connection]', f'id={escaped}', f'uuid={uuid.uuid4()}', 'type=wifi', 'autoconnect=true',
             f'autoconnect-priority={priority}', '', '[wifi]', 'mode=infrastructure', f'ssid={ssid_bytes(ssid)}']
    if network.get('hidden'):
        lines.append('hidden=true')
    if network['psk']:
        lines += ['', '[wifi-security]', 'key-mgmt=wpa-psk', f"psk={keyfile_escape(network['psk'])}"]
    lines += ['', '[ipv4]', 'method=auto', '', '[ipv6]', 'addr-gen-mode=default', 'method=auto', '']
    os.makedirs(CONNECTIONS, mode=0o700, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
        handle.write('\n'.join(lines))
    os.chmod(path, 0o600)


def set_country(country):
    """
    Country of the Wi-Fi (allowed channels ; without it Raspberry Pi OS keeps the Wi-Fi
    blocked) : raspi-config when there (cmdline.txt, iw, rfkill), else cmdline.txt by hand
    """
    if run('raspi-config', 'nonint', 'do_wifi_country', country):
        return
    for boot in BOOT_DIRS:
        cmdline = os.path.join(boot, 'cmdline.txt')
        if os.path.isfile(cmdline):
            with open(cmdline, encoding='utf-8') as handle:
                words = [word for word in handle.read().split() if not word.startswith('cfg80211.ieee80211_regdom=')]
            with open(cmdline, 'w', encoding='utf-8') as handle:
                handle.write(' '.join(words + [f'cfg80211.ieee80211_regdom={country}']) + '\n')
            break
    run('iw', 'reg', 'set', country)


def current_country():
    for boot in BOOT_DIRS:
        cmdline = os.path.join(boot, 'cmdline.txt')
        if os.path.isfile(cmdline):
            match = re.search(r'cfg80211\.ieee80211_regdom=(\S+)', read_text(cmdline))
            return match.group(1) if match else None
    return None


def unblock():
    """
    The Wi-Fi unblocked now and at the next starts (state kept by systemd-rfkill)
    """
    run('rfkill', 'unblock', 'wifi')
    for state in glob.glob('/var/lib/systemd/rfkill/*:wlan'):
        try:
            with open(state, 'w', encoding='ascii') as handle:
                handle.write('0\n')
        except OSError:
            pass


def found_files(boot):
    """
    The files dropped : wifi.txt (also wifi.txt.txt, the Notepad adding its extension) and
    wpa_supplicant.conf (also .conf.txt, or .txt when Windows replaced its extension), whatever their case
    """
    files = []
    try:
        names = os.listdir(boot)
    except OSError:
        return files
    for name in sorted(names):
        lower = name.lower()
        if lower in ('wifi.txt', 'wifi.txt.txt', 'wifi'):
            files.append((os.path.join(boot, name), parse_wifi_txt))
        elif lower in ('wpa_supplicant.conf', 'wpa_supplicant.conf.txt', 'wpa_supplicant.txt'):
            files.append((os.path.join(boot, name), parse_wpa_supplicant))
    return files


def main():
    for boot in BOOT_DIRS:
        files = found_files(boot)
        if not files:
            continue
        report, networks, country = [], [], None
        for path, parse in files:
            try:
                found, found_country = parse(read_text(path))
            except OSError as error:
                report.append(f'{os.path.basename(path)} : illisible ({error})')
                continue
            networks += found
            country = found_country or country
            report.append(f'{os.path.basename(path)} : {len(found)} reseau(x)')
        # The first network written is the preferred one (priority of wpa_supplicant kept)
        count = len(networks)
        for index, network in enumerate(networks):
            if not network['ssid']:
                continue
            priority = PRIORITY + (network['priority'] if network.get('priority') is not None else count - index)
            try:
                write_connection(network, priority)
                kind = 'sans mot de passe' if not network['psk'] else 'avec mot de passe'
                report.append(f"Reseau « {network['ssid']} » ajoute ({kind}{', masque' if network.get('hidden') else ''})")
            except OSError as error:
                report.append(f"Reseau « {network['ssid']} » : erreur ({error})")
        if count:
            country = (country or current_country() or DEFAULT_COUNTRY).strip().upper()[:2]
            set_country(country)
            unblock()
            report.append(f'Pays du Wi-Fi : {country}')
        else:
            report.append('Aucun reseau trouve (ssid= manquant ?) : rien n\'a change')
        # The password must not stay on a partition readable by any computer
        for path, _parse in files:
            try:
                os.remove(path)
            except OSError:
                pass
        try:
            with open(os.path.join(boot, RESULT), 'w', encoding='utf-8', newline='\r\n') as handle:
                handle.write('RaspyDarts : Wi-Fi depose sur la carte\n\n' + '\n'.join(report) + '\n')
        except OSError:
            pass
        run('sync')
        print('\n'.join(report))
        # NetworkManager already running (the script started by hand) : it reads them again
        if run('systemctl', 'is-active', '--quiet', 'NetworkManager'):
            run('nmcli', 'connection', 'reload')
        break
    return 0


if __name__ == '__main__':
    sys.exit(main())
