#!/bin/bash
# ============================================================
# RaspyDarts - Installation sur une image Raspberry Pi OS neuve
# ============================================================
#
# Partie executee SUR le Pi. Elle est lancee par install.sh (racine du depot, depuis
# GitHub) ou copiee et lancee par install_raspydarts.ps1 (poste de developpement) :
#
#   sudo bash install_on_pi.sh <code.tar.gz> <home.tar.gz|home.zip|-> [--yes]
#
#   <code.tar.gz>  archive du depot (git archive, ou celle de GitHub avec son dossier de
#                  tete RaspyDarts-main/), extraite dans /raspydarts
#   <home...>      contenu de ~/.raspydarts : .tar.gz (.raspydarts_example) ou .zip
#                  (release exemple) ; "-" pour ne pas l'installer
#   --yes          repond oui aux confirmations (relance sans surveillance)
#
# Systeme prevu : Raspberry Pi OS 13 (Trixie) 32 bits avec bureau.
# RaspyDarts est installe pour l'utilisateur qui lance sudo (raspydarts).
#
# Le script peut etre relance sans risque : chaque modification de fichier
# systeme est encadree par des marqueurs et remplacee, pas dupliquee.
#
# ============================================================

set -u

# ============================================================
# Configuration
# ============================================================

TARGET_USER="${SUDO_USER:-raspydarts}"
PYDARTS=/raspydarts
USER_DIR_NAME=.raspydarts
MIN_FREE_KB=4000000

MARK_BEGIN='# --- RaspyDarts (debut) ---'
MARK_END='# --- RaspyDarts (fin) ---'

# Paquets systeme indispensables
APT_REQUIRED="python3-pip python3-dev python3-tk python3-pygame python3-numpy python3-pil python3-psutil
python3-requests python3-yaml python3-evdev python3-usb python3-rpi-lgpio python3-lgpio python3-libgpiod python3-smbus python3-serial python3-netifaces python3-qrcode python3-websocket
python3-googleapi python3-google-auth-oauthlib python3-google-auth-httplib2
i2c-tools vlc ffmpeg v4l-utils espeak mpg123 alsa-utils pipewire-alsa pulseaudio-utils
xdotool scrot feh picom gettext git curl swig
bluez libbluetooth-dev mosquitto mosquitto-clients"

# Paquets systeme facultatifs (un echec n'arrete pas l'installation)
#   afficheur DMD MAX7219, telecommande Bluetooth, camera, curseur masque
# fonts-noto-color-emoji : les emojis des textes du jeu (coupes des trophees) ; sans elle, ils sont omis
APT_OPTIONAL="python3-luma.led-matrix python3-bluez python3-picamera2 unclutter fonts-noto-color-emoji"

# Moteur de la voix francaise : absent de Raspberry Pi OS, present chez Debian
MBROLA_URL=https://deb.debian.org/debian/pool/contrib/m/mbrola/

# Services inutiles a une borne de flechettes, desactives pour accelerer le demarrage.
# winbind et NetworkManager-wait-online retardent a eux seuls l'ecran de connexion
# d'environ 25 secondes (attente du reseau).
SERVICES_OFF="NetworkManager-wait-online.service winbind.service samba-ad-dc.service
cups.service cups.socket cups.path cups-browsed.service
rpcbind.service rpcbind.socket nfs-blkmap.service nfs-client.target
apt-daily.timer apt-daily-upgrade.timer man-db.timer"

# Programmes lances a l'ouverture de session et retires ici :
#   pprompt  : avertissement de mot de passe
#   xcompmgr : compositeur d'origine, remplace par picom (voir patch_autostart)
SESSION_OFF="pprompt xcompmgr"

# Modules Python absents des paquets systeme (paho-mqtt 2, comme Raspy2DMD)
# Adafruit-Blinka-Raspberry-Pi-PWM : Blinka 10 le demande au demarrage sur un Raspberry
# (« Blinka detected missing or outdated platform dependencies… Install them? [Y/n] »)
PIP_REQUIRED="paho-mqtt>=2 Adafruit-Blinka Adafruit-Blinka-Raspberry-Pi-PWM>=1.0.2
adafruit-circuitpython-mcp230xx adafruit-circuitpython-neopixel rpi_ws281x"

# Modules Python facultatifs (Philips Hue)
PIP_OPTIONAL="rgbxy"

# Modules verifies en fin d'installation
PY_CHECK="pygame paho.mqtt.client netifaces qrcode websocket board busio digitalio adafruit_mcp230xx
adafruit_blinka_raspberry_pi_pwm
neopixel rpi_ws281x googleapiclient google_auth_oauthlib RPi.GPIO PIL numpy psutil
requests smbus tkinter"

# Langue, fuseau horaire et clavier par defaut de l'image
# omxplayer et bibliotheques du firmware compiles pour Trixie 32 bits (voir build_omxplayer.sh,
# sources jointes a la meme release)
OMX_RELEASE=installation-trixie
OMX_ASSET=raspydarts-omxplayer-trixie-armhf.tar.gz
OMX_URL="https://github.com/rmdelcelier/RaspyDarts/releases/download/$OMX_RELEASE/$OMX_ASSET"

DEFAULT_LOCALE=fr_FR.UTF-8
DEFAULT_TIMEZONE=Europe/Paris
DEFAULT_KEYBOARD=fr

# ============================================================
# Fonctions utilitaires
# ============================================================

STEP=0
TOTAL=8
WARNINGS=""

step() { STEP=$((STEP + 1)); printf '\n  \033[34m[%s/%s] %s\033[0m\n  --------------------------------------------------------\n' "$STEP" "$TOTAL" "$1"; }
ok()   { printf '  \033[32m[+]\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m[!]\033[0m %s\n' "$1"; WARNINGS="$WARNINGS\n    - $1"; }
die()  { printf '\n  \033[31m[ERREUR]\033[0m %s\n\n' "$1"; exit 1; }

confirm() {
    [ "$ASSUME_YES" = "1" ] && return 0
    printf '  %s (o/N) ' "$1"
    read -r answer
    [ "$answer" = "o" ] || [ "$answer" = "O" ]
}

# Supprime un bloc RaspyDarts deja present dans un fichier
remove_block() {
    sed -i "/^${MARK_BEGIN}\$/,/^${MARK_END}\$/d" "$1"
}

# ============================================================
# Modifications des fichiers systeme
# (une fonction par fichier, testable avec --test-patch <dossier>)
# ============================================================

# A l'ouverture de la session graphique : video d'introduction et jeu, lances ensemble
# (la video masque le chargement du jeu). La barre des taches et les icones du bureau
# ne sont lancees qu'ensuite : on passe de l'ecran de demarrage a la video sans voir
# le bureau.
#
# picom remplace le compositeur d'origine : il attend le balayage de l'ecran pour
# afficher, ce qui supprime les images "dechirees" (moitie ancienne, moitie nouvelle)
# pendant les animations. Rendu logiciel : celui par la carte graphique ne demarre pas
# sur les Pi sans acceleration du serveur graphique.
patch_autostart() {
    [ -f "$1.origine" ] || cp "$1" "$1.origine"
    sed -i "/^@lxpanel-pi\$/d; /^@pcmanfm-pi\$/d; /^@picom /d; \#^/usr/local/bin/raspydarts-#d; \#^sh $PYDARTS/scripts/Intro.sh\$#d; \#^$PYDARTS/RaspyDarts.sh\$#d" "$1"
    {
        echo "@picom --backend xrender --vsync"
        echo "/usr/local/bin/raspydarts-audio"
        # En mode Buster, l'intro et le jeu sont lances par leurs services (plus tot)
        if [ "${BUSTER_MODE:-0}" != "1" ]; then
            echo "sh $PYDARTS/scripts/Intro.sh"
            echo "$PYDARTS/RaspyDarts.sh"
        fi
        echo "/usr/local/bin/raspydarts-desktop"
    } >> "$1"
}

# Lance le bureau a la sortie du jeu (90 secondes au plus tard si le jeu ne demarre pas)
write_desktop_script() {
    cat > "$1" <<'EOF'
#!/bin/sh
# RaspyDarts : la barre des taches et les icones du bureau ne sont lancees qu'a la sortie
# du jeu ("Revenir sur le bureau"). Lancees avant, on voit le bureau entre la video
# d'introduction et le menu, et la barre des taches passe au-dessus du jeu a chaque fin
# de video.
i=0
while [ $i -lt 90 ] && ! pgrep -f RaspyDarts.sh > /dev/null 2>&1
do
	sleep 1
	i=$((i + 1))
done
while pgrep -f RaspyDarts.sh > /dev/null 2>&1
do
	sleep 2
done
lxpanel-pi &
pcmanfm-pi &
wait
EOF
}

# Regle le son sur la sortie HDMI a plein volume. Fait une seule fois par modele de Pi
# (l'image est flashee sur des Pi differents) : le choix fait ensuite par l'utilisateur
# dans le bureau est conserve.
write_audio_script() {
    cat > "$1" <<'EOF'
#!/bin/sh
# RaspyDarts : son sur la sortie HDMI, a plein volume, au premier demarrage sur ce Pi
MARK="$HOME/.config/raspydarts-audio"
MODEL="$(tr -d '\0' < /proc/device-tree/model 2> /dev/null)"
[ "$(cat "$MARK" 2> /dev/null)" = "$MODEL" ] && exit 0
i=0
while [ $i -lt 20 ]
do
	SINK="$(LC_ALL=C pactl list short sinks 2> /dev/null | awk '$2 ~ /hdmi/ {print $2; exit}')"
	if [ -n "$SINK" ]
	then
		pactl set-default-sink "$SINK"
		pactl set-sink-volume "$SINK" 100%
		pactl set-sink-mute "$SINK" 0
		echo "$MODEL" > "$MARK"
		exit 0
	fi
	sleep 1
	i=$((i + 1))
done
exit 0
EOF
}

# Au demarrage : recupere une configuration deposee sur la partition de demarrage
# (la seule lisible depuis Windows). Remplace l'ancien /etc/rc.local.
write_boot_script() {
    cat > "$1" <<EOF
#!/bin/sh
# RaspyDarts : configuration deposee sur la partition de demarrage
USER_DIR=$TARGET_HOME/$USER_DIR_NAME
CHANGED=0
for BOOT in /boot/firmware /boot; do
	# pydarts.cfg (ancien nom) est converti en raspydarts.cfg
	for CFG in pydarts.cfg raspydarts.cfg; do
		if [ -f "\$BOOT/\$CFG" ]; then
			# Une configuration existe deja : le fichier est mis de cote, le jeu propose
			# au demarrage d'en reprendre les valeurs nouvelles (ou le supprime)
			if [ -f "\$USER_DIR/raspydarts.cfg" ]; then
				mv "\$BOOT/\$CFG" "\$USER_DIR/raspydarts.cfg.depose"
			else
				rm -f "\$USER_DIR/pydarts.cfg"
				mv "\$BOOT/\$CFG" "\$USER_DIR/raspydarts.cfg"
			fi
			CHANGED=1
		fi
	done
	for DIR in .pydarts .raspydarts; do
		if [ -d "\$BOOT/\$DIR" ]; then
			cp -r "\$BOOT/\$DIR/." "\$USER_DIR/"
			rm -r "\$BOOT/\$DIR"
			CHANGED=1
		fi
	done
done
if [ "\$CHANGED" -eq 1 ]; then
	chown -R $TARGET_USER:$TARGET_USER "\$USER_DIR"
	chmod -R 777 "\$USER_DIR"
fi
exit 0
EOF
}

write_boot_unit() {
    cat > "$1" <<EOF
[Unit]
Description=RaspyDarts : configuration deposee sur la partition de demarrage
After=local-fs.target
Before=display-manager.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/raspydarts-boot

[Install]
WantedBy=multi-user.target
EOF
}

# Partages reseau : sauvegardes, journaux, personnalisation, photos et videos
patch_smb_conf() {
    remove_block "$1"
    cat >> "$1" <<EOF
$MARK_BEGIN
[Backup Raspydarts]
comment = Backup Raspydarts
path = $PYDARTS/backup
writable = yes
guest ok = yes
guest account = $TARGET_USER
guest only = yes
create mode = 0644
directory mode = 0777
share modes = yes
public = no
force user = $TARGET_USER
force group = $TARGET_USER

[Logs Raspydarts]
comment = Logs Raspydarts
path = $PYDARTS/logs
writable = yes
guest ok = yes
guest account = $TARGET_USER
guest only = yes
create mode = 0644
directory mode = 0777
share modes = yes
public = no
force user = $TARGET_USER
force group = $TARGET_USER

[Personnalisation Raspydarts]
comment = Personnalisation Raspydarts
path = $TARGET_HOME/$USER_DIR_NAME
writable = yes
create mode = 0664
directory mode = 0777
share modes = yes
read only = no
guest ok = yes
force user = $TARGET_USER
force group = $TARGET_USER

[Videos Cam]
comment = Videos obtenues en jeu via la camera
path = $TARGET_HOME/Videos
writable = yes
create mode = 0664
directory mode = 0777
share modes = yes
read only = no
guest ok = yes
force user = $TARGET_USER
force group = $TARGET_USER

[Images Cam]
comment = Images obtenues en jeu via la camera
path = $TARGET_HOME/Pictures
writable = yes
create mode = 0664
directory mode = 0777
share modes = yes
read only = no
guest ok = yes
force user = $TARGET_USER
force group = $TARGET_USER
$MARK_END
EOF
}

# Le serveur graphique ne peint pas l'ecran en noir a son lancement : l'image de
# demarrage reste affichee jusqu'a la premiere fenetre (la video d'introduction)
patch_lightdm() {
    if grep -q '^xserver-command=' "$1"; then
        grep -q '^xserver-command=.*-background none' "$1" || sed -i '/^xserver-command=/s/$/ -background none/' "$1"
    else
        sed -i '0,/^\[Seat:\*\]/s//[Seat:*]\nxserver-command=X -background none/' "$1"
    fi
    # Script lance par l'ecran de connexion des que le serveur graphique est pret
    if grep -q '^display-setup-script=' "$1"; then
        sed -i 's#^display-setup-script=.*#display-setup-script=/usr/local/bin/raspydarts-display-setup#' "$1"
    else
        sed -i '0,/^\[Seat:\*\]/s//[Seat:*]\ndisplay-setup-script=\/usr\/local\/bin\/raspydarts-display-setup/' "$1"
    fi
}

# Le lancement du serveur graphique efface l'ecran : l'image de demarrage est reaffichee
# aussitot, et reste jusqu'a la video d'introduction
write_display_setup_script() {
    cat > "$1" <<EOF
#!/bin/sh
# RaspyDarts : l'image de demarrage reste a l'ecran pendant l'ouverture de session
# Reglage d'ecran d'origine de Raspberry Pi OS
[ -x /usr/share/dispsetup.sh ] && /usr/share/dispsetup.sh
feh --no-fehbg --bg-fill $PYDARTS/images/background_clear.png 2> /dev/null
# pas de curseur de souris sur l'image (le jeu et le bureau ont le leur)
printf '#define b_width 1\n#define b_height 1\nstatic char b_bits[] = { 0x00 };\n' > /tmp/raspydarts-blank.xbm
xsetroot -cursor /tmp/raspydarts-blank.xbm /tmp/raspydarts-blank.xbm 2> /dev/null
exit 0
EOF
}

# Bulles de notification du panneau (connexion Wi-Fi, memoire, mises a jour...) :
# elles s'affichent par-dessus le jeu
patch_panel() {
    sed -i '/^ *notifications=/d' "$1"
    sed -i '0,/^Global {/s//Global {\n  notifications=0/' "$1"
}

# Fond de l'ecran de connexion (visible entre le splash et le bureau)
patch_greeter() {
    sed -i '/^wallpaper=/d; /^wallpaper_mode=/d' "$1"
    grep -q '^\[greeter\]' "$1" || echo '[greeter]' >> "$1"
    sed -i "/^\[greeter\]/a wallpaper=$PYDARTS/images/background_clear.png\nwallpaper_mode=crop" "$1"
}

# Fond du bureau : le meme que l'image de demarrage
patch_desktop() {
    if [ -f "$1" ] && grep -q '^wallpaper=' "$1"; then
        sed -i "s#^wallpaper=.*#wallpaper=$PYDARTS/images/background_clear.png#; s#^wallpaper_mode=.*#wallpaper_mode=crop#" "$1"
    else
        printf '[*]\nwallpaper_mode=crop\nwallpaper_common=1\nwallpaper=%s\nshow_documents=0\nshow_trash=1\nshow_mounts=0\n' "$PYDARTS/images/background_clear.png" > "$1"
    fi
}

# ------------------------------------------------------------
# Affichage et videos comme sous Buster : affichage gere par le firmware (sans le pilote KMS),
# videos jouees par omxplayer sur une couche du firmware, au-dessus de tout (console, serveur
# graphique, jeu). L'intro demarre des la fin de l'image de demarrage, le jeu se charge dessous
# et son menu est la a la fin de la video.
# ------------------------------------------------------------

# config.txt : affichage gere par le firmware, memoire pour son decodeur video
patch_config_txt() {
    sed -i 's/^dtoverlay=vc4-kms-v3d.*/#& (RaspyDarts : affichage gere par le firmware)/; s/^dtoverlay=vc4-fkms-v3d.*/#& (RaspyDarts : affichage gere par le firmware)/' "$1"
    remove_block "$1"
    sed -i '/^gpu_mem=/d' "$1"
    sed -i '/^disable_splash=/d' "$1"
    printf '%s\n[all]\n# memoire du decodeur video du firmware (omxplayer)\ngpu_mem=128\n# pas de nuancier de couleurs du firmware a la mise sous tension\ndisable_splash=1\n%s\n' "$MARK_BEGIN" "$MARK_END" >> "$1"
}

# cmdline.txt : messages du demarrage sur une console invisible (tty3), plus rien n'est ecrit
# par-dessus l'image de demarrage
patch_cmdline() {
    sed -i 's/console=tty1/console=tty3/; s/ loglevel=[0-9]//g; 1s/$/ loglevel=3/' "$1"
}

# Serveur graphique sur /dev/fb0 (pas de /dev/dri sans le pilote KMS)
write_xorg_fbdev() {
    cat > "$1" <<'EOF'
# RaspyDarts : affichage gere par le firmware (sans vc4-kms-v3d), comme sous Buster
Section "Device"
    Identifier "FBDEV"
    Driver "fbdev"
    Option "fbdev" "/dev/fb0"
EndSection

Section "Screen"
    Identifier "FBSCREEN"
    Device "FBDEV"
EndSection
EOF
}

# /dev/fb0 est l'ecran du siege seat0 : sans cela, logind repond CanGraphical=no et
# l'ecran de connexion ne lance pas le serveur graphique
write_fb_seat_rule() {
    cat > "$1" <<'EOF'
# RaspyDarts : affichage gere par le firmware (sans vc4-kms-v3d) : /dev/fb0 est l'ecran du siege seat0
SUBSYSTEM=="graphics", KERNEL=="fb0", TAG+="seat", TAG+="master-of-seat"
EOF
}

# Paves USB de touches et de molettes (1189:8890) : le jeu les programme lui-meme (pyusb,
# Parametres > Paves USB), sans etre root
write_usb_pads_rule() {
    cat > "$1" <<'EOF'
# RaspyDarts : paves USB de touches et de molettes (puce CH57x), programmes par le jeu
SUBSYSTEM=="usb", ATTR{idVendor}=="1189", ATTR{idProduct}=="8890", MODE="0660", GROUP="plugdev"
EOF
}

# Copie du service lightdm sans l'attente de /dev/dri/card0 (absent : 90 s perdues sinon)
write_lightdm_unit() {
    sed -e 's# dev-dri-card0.device dev-dri-renderD128.device##' -e '/^Wants=dev-dri-card0.device dev-dri-renderD128.device$/d' \
        -e '1i # RaspyDarts : copie du service du paquet lightdm, sans attente de /dev/dri/card0 (absent avec l affichage gere par le firmware)' \
        /usr/lib/systemd/system/lightdm.service > "$1"
}

# Video d'introduction lancee par le systeme, comme rc.local sous Buster
write_intro_unit() {
    cat > "$1" <<EOF
[Unit]
Description=RaspyDarts : video d'introduction, au-dessus de tout (comme rc.local sous Buster)
After=systemd-user-sessions.service
Before=lightdm.service

[Service]
Type=simple
ExecStart=/bin/sh $PYDARTS/scripts/Intro.sh

[Install]
WantedBy=graphical.target
EOF
}

# Le jeu, lance par le gestionnaire de services de l'utilisateur des l'ouverture de la session :
# plus tot que le demarrage automatique du bureau, il est pret avant la fin de l'intro
write_game_user_unit() {
    cat > "$1" <<EOF
[Unit]
Description=RaspyDarts : le jeu, lance des l'ouverture de la session (sous la video d'introduction)

[Service]
Type=simple
Environment=DISPLAY=:0
Environment=XAUTHORITY=%h/.Xauthority
# Le serveur graphique est pret avant l'ouverture de la session ; au cas ou, l'attendre 20 s au plus
ExecStartPre=/bin/sh -c 'i=0; while [ \$i -lt 100 ] && ! { [ -S /tmp/.X11-unix/X0 ] && [ -s "\$HOME/.Xauthority" ]; }; do sleep 0.2; i=\$((i + 1)); done'
ExecStart=$PYDARTS/RaspyDarts.sh

[Install]
WantedBy=default.target
EOF
}

# Mode HDMI adapte a l'ecran branche (lu dans son EDID)
write_display_unit() {
    cat > "$1" <<'EOF'
[Unit]
Description=RaspyDarts : mode HDMI adapte a l'ecran branche (lu dans son EDID)
DefaultDependencies=no
After=local-fs.target
Before=raspydarts-intro.service lightdm.service sysinit.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/raspydarts-display

[Install]
WantedBy=sysinit.target
EOF
}

# Connexions reseau enregistrees par NetworkManager lui-meme, sans netplan
write_network_unit() {
    cat > "$1" <<'EOF'
[Unit]
Description=RaspyDarts : connexions reseau enregistrees par NetworkManager, sans netplan
DefaultDependencies=no
After=local-fs.target cloud-init-local.service
Before=network-pre.target NetworkManager.service
Wants=network-pre.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/raspydarts-network

[Install]
WantedBy=NetworkManager.service
EOF
}

write_network_script() {
    cat > "$1" <<'PYEOF'
#!/usr/bin/python3
"""
RaspyDarts : connexions reseau enregistrees par NetworkManager lui-meme, sans netplan.

Raspberry Pi OS range les connexions de NetworkManager au format netplan (/etc/netplan),
et Raspberry Pi Imager y ecrit le Wi-Fi au premier demarrage (cloud-init). NetworkManager
reecrit alors ces fichiers a chaque demarrage, et chaque ecriture provoque un rechargement
complet de systemd (3 a 4 secondes chacun sur un Pi 3, plusieurs par demarrage).

Lance avant NetworkManager : les profils deja generes par netplan dans /run sont recopies en
profils NetworkManager ordinaires (/etc/NetworkManager/system-connections), puis les fichiers
netplan sont mis de cote. En cas de probleme, rien n'est retire : le reseau reste celui de
netplan.
"""
import configparser
import glob
import os
import shutil
import sys
import uuid

NETPLAN = '/etc/netplan'
GENERATED = '/run/NetworkManager/system-connections'
TARGET = '/etc/NetworkManager/system-connections'
BACKUP = '/var/backups/raspydarts-netplan'


def log(message):
    print(f"raspydarts-network : {message}", flush=True)


def keyfile(path):
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str    # cles sensibles a la casse
    parser.read(path, encoding='utf-8')
    return parser


def convert(path):
    """ Profil genere par netplan -> profil NetworkManager ordinaire. Retourne le nouveau fichier """
    profile = keyfile(path)
    if not profile.has_section('connection'):
        raise ValueError(f"{path} : pas de section [connection]")
    # netplan-<interface>-<nom> (Wi-Fi) ou netplan-<interface>
    rest = os.path.basename(path)[len('netplan-'):-len('.nmconnection')]
    interface = rest.split('-')[0]
    name = profile['connection'].get('id', rest)
    for prefix in ('netplan-', f'{interface}-'):
        if name.startswith(prefix) and len(name) > len(prefix):
            name = name[len(prefix):]
    profile['connection']['id'] = name
    profile['connection']['uuid'] = str(uuid.uuid4())
    profile['connection'].setdefault('interface-name', interface)
    target = os.path.join(TARGET, name.replace('/', '_') + '.nmconnection')
    if os.path.exists(target):
        target = os.path.join(TARGET, f"{name.replace('/', '_')}-{interface}.nmconnection")
    with open(target + '.tmp', 'w', encoding='utf-8') as out:
        profile.write(out, space_around_delimiters=False)
    os.chmod(target + '.tmp', 0o600)
    # Relu avant de remplacer l'ancien : jamais de profil illisible
    check = keyfile(target + '.tmp')
    if check['connection'].get('id') != name or check['connection'].get('type') != profile['connection'].get('type'):
        raise ValueError(f"{target} : profil relu different")
    os.replace(target + '.tmp', target)
    return target


def main():
    yamls = sorted(glob.glob(os.path.join(NETPLAN, '*.yaml')))
    if not yamls:
        return
    generated = sorted(glob.glob(os.path.join(GENERATED, 'netplan-*.nmconnection')))
    converted = []
    for path in generated:
        target = convert(path)
        converted.append(path)
        log(f"{os.path.basename(path)} -> {target}")
    # Tout est converti : les profils netplan ne sont plus utilises
    for path in converted:
        os.remove(path)
    os.makedirs(BACKUP, mode=0o700, exist_ok=True)
    for path in yamls:
        shutil.move(path, os.path.join(BACKUP, os.path.basename(path)))
    log(f"{len(converted)} connexion(s) convertie(s), fichiers netplan ranges dans {BACKUP}")


if __name__ == '__main__':
    try:
        main()
    except Exception as error:    # le reseau reste celui de netplan
        log(f"erreur, rien n'est retire : {error}")
        sys.exit(0)
PYEOF
}

if [ "${1:-}" = "--test-patch" ]; then
    TARGET_HOME=/home/$TARGET_USER
    patch_autostart "$2/autostart"
    write_desktop_script "$2/raspydarts-desktop"
    write_audio_script "$2/raspydarts-audio"
    write_boot_script "$2/raspydarts-boot"
    write_boot_unit "$2/raspydarts-boot.service"
    patch_smb_conf "$2/smb.conf"
    patch_lightdm "$2/lightdm.conf"
    write_display_setup_script "$2/raspydarts-display-setup"
    patch_panel "$2/panel"
    patch_greeter "$2/pi-greeter.conf"
    patch_desktop "$2/desktop-items-0.conf"
    patch_desktop "$2/desktop-absent.conf"
    patch_config_txt "$2/config.txt"
    patch_cmdline "$2/cmdline.txt"
    write_xorg_fbdev "$2/98-raspydarts-fbdev.conf"
    write_fb_seat_rule "$2/71-raspydarts-fb-seat.rules"
    [ -f /usr/lib/systemd/system/lightdm.service ] && write_lightdm_unit "$2/lightdm.service"
    write_intro_unit "$2/raspydarts-intro.service"
    write_game_user_unit "$2/raspydarts.service"
    write_display_unit "$2/raspydarts-display.service"
    cp "$(dirname "$0")/raspydarts_display.py" "$2/raspydarts-display"
    write_network_unit "$2/raspydarts-network.service"
    write_network_script "$2/raspydarts-network"
    exit 0
fi

CODE_ARCHIVE="${1:-}"
HOME_ARCHIVE="${2:--}"
ASSUME_YES=0
[ "${3:-}" = "--yes" ] && ASSUME_YES=1

printf '\n  \033[36m========================================================\n'
printf '    RaspyDarts - Installation sur le Pi\n'
printf '  ========================================================\033[0m\n'

# ============================================================
# ETAPE 1 : Verifications
# ============================================================

step 'Verifications...'

[ "$(id -u)" -eq 0 ] || die "A lancer avec sudo."
[ -f "$CODE_ARCHIVE" ] || die "Archive du code introuvable : $CODE_ARCHIVE"
[ "$HOME_ARCHIVE" = "-" ] || [ -f "$HOME_ARCHIVE" ] || die "Archive .pydarts introuvable : $HOME_ARCHIVE"
[ "$TARGET_USER" != "root" ] || die "A lancer avec sudo depuis le compte qui fera tourner RaspyDarts, pas en root."
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
[ -d "$TARGET_HOME" ] || die "L'utilisateur '$TARGET_USER' n'existe pas."
[ -f /etc/lightdm/lightdm.conf ] || die "Bureau graphique absent : utilisez l'image 'with desktop', pas la version Lite."
USER_DIR="$TARGET_HOME/$USER_DIR_NAME"
ok "Utilisateur : $TARGET_USER ($TARGET_HOME)"

. /etc/os-release
CODENAME="${VERSION_CODENAME:-inconnu}"
ok "Systeme : ${PRETTY_NAME:-?} ($(dpkg --print-architecture)) - $(tr -d '\0' < /proc/device-tree/model 2>/dev/null)"

if [ "$CODENAME" != "trixie" ]; then
    printf '  \033[33m[!]\033[0m Ce script est prevu pour Raspberry Pi OS 13 (Trixie).\n'
    printf '      Sur un autre systeme, la liste des paquets peut ne pas convenir.\n'
    confirm 'Continuer malgre tout ?' || exit 1
    WARNINGS="$WARNINGS\n    - Systeme non prevu : $CODENAME"
fi

FREE_KB=$(df --output=avail -k / | tail -1 | tr -d ' ')
[ "$FREE_KB" -ge "$MIN_FREE_KB" ] || die "Espace libre insuffisant sur / : $((FREE_KB / 1024)) Mo (4 Go necessaires)."
ok "Espace libre : $((FREE_KB / 1024)) Mo"

if [ -e "$PYDARTS" ]; then
    printf '  \033[33m[!]\033[0m %s existe deja : ses fichiers seront remplaces par ceux de l archive.\n' "$PYDARTS"
    confirm 'Continuer ?' || exit 1
fi

# ============================================================
# ETAPE 2 : Paquets systeme
# ============================================================

step 'Installation des paquets systeme (apt)...'

export DEBIAN_FRONTEND=noninteractive

apt-get update || die "apt-get update a echoue (connexion Internet ?)."

# shellcheck disable=SC2086
apt-get install -y $APT_REQUIRED || die "Installation des paquets indispensables echouee."
ok 'Paquets indispensables installes'

# Sans les paquets recommandes : ils ajoutent winbind, qui retarde le demarrage
apt-get install -y --no-install-recommends samba || die "Installation de samba echouee."
ok 'Samba installe (partages reseau)'

for package in $APT_OPTIONAL; do
    if apt-get install -y "$package" >/dev/null 2>&1; then
        ok "$package"
    else
        warn "Paquet facultatif non installe : $package"
    fi
done

# Voix francaise des noms de joueurs : espeak avec la voix mbrola fr1
if ! command -v mbrola >/dev/null; then
    MBROLA_DEB=$(curl -fsSL -m 30 "$MBROLA_URL" | grep -o "mbrola_[^\"<]*_$(dpkg --print-architecture)\.deb" | sort -uV | tail -1)
    if [ -n "$MBROLA_DEB" ] && curl -fsSL -m 120 -o "/var/cache/apt/archives/$MBROLA_DEB" "$MBROLA_URL$MBROLA_DEB"; then
        apt-get install -y "/var/cache/apt/archives/$MBROLA_DEB" >/dev/null 2>&1
    fi
fi
apt-get install -y mbrola-fr1 >/dev/null 2>&1
if command -v mbrola >/dev/null && [ -d /usr/share/mbrola/fr1 ]; then
    ok 'Voix francaise (mbrola fr1)'
else
    warn "Voix francaise mbrola non installee : les noms seront dits avec la voix de base d'espeak"
fi

# ============================================================
# ETAPE 3 : Modules Python
# ============================================================

step 'Installation des modules Python (pip)...'

# Installation pour tout le systeme : le serveur de LED tourne en root (sudo).
# --break-system-packages : pip refuse sinon d'installer hors d'un environnement virtuel.
PIP_INSTALL="pip3 install --break-system-packages --root-user-action=ignore"

for module in $PIP_REQUIRED; do
    $PIP_INSTALL "$module" || die "Installation du module Python $module echouee."
done
ok 'Modules indispensables installes'

for module in $PIP_OPTIONAL; do
    if $PIP_INSTALL "$module" >/dev/null 2>&1; then
        ok "$module"
    else
        warn "Module Python facultatif non installe : $module"
    fi
done

# Adafruit-Blinka installe l'ancien RPi.GPIO, qui masque celui du systeme (rpi-lgpio)
# et ne sait plus detecter les fronts sur les noyaux recents
if pip3 uninstall -y --break-system-packages --root-user-action=ignore RPi.GPIO >/dev/null 2>&1; then
    ok 'Ancien RPi.GPIO retire (rpi-lgpio le remplace)'
fi

# ============================================================
# ETAPE 4 : Code de RaspyDarts
# ============================================================

step "Installation du code dans $PYDARTS..."

mkdir -p "$PYDARTS"
# L'archive de GitHub range tout dans un dossier de tete (RaspyDarts-main/) : retire
TOP="$(tar -tzf "$CODE_ARCHIVE" 2>/dev/null | head -1 | cut -d/ -f1)"
STRIP=""
if [ -n "$TOP" ] && [ "$TOP" != "." ] && tar -tzf "$CODE_ARCHIVE" "$TOP/VERSION" >/dev/null 2>&1; then
    STRIP="--strip-components=1"
fi
# shellcheck disable=SC2086
tar -xzf "$CODE_ARCHIVE" -C "$PYDARTS" $STRIP || die "Extraction du code echouee."
mkdir -p "$PYDARTS/logs" "$PYDARTS/backup"

# Le depot ne conserve ni le droit d'execution ni forcement les fins de ligne Unix
find "$PYDARTS" -name '*.sh' -exec sed -i 's/\r$//' {} + -exec chmod 755 {} +
chown -R "$TARGET_USER:$TARGET_USER" "$PYDARTS"
chmod 777 "$PYDARTS/logs" "$PYDARTS/backup"

[ -s "$PYDARTS/VERSION" ] || die "Fichier VERSION absent de l'archive."
VERSION="$(cat "$PYDARTS/VERSION")"
ok "RaspyDarts $VERSION installe"

# ============================================================
# ETAPE 5 : Configuration utilisateur (.pydarts)
# ============================================================

step "Installation de la configuration d'exemple..."

mkdir -p "$USER_DIR" "$TARGET_HOME/Pictures" "$TARGET_HOME/Videos" "$TARGET_HOME/Desktop"
if [ "$HOME_ARCHIVE" != "-" ]; then
    case "$HOME_ARCHIVE" in
        # Release exemple de GitHub : un zip (python3 est toujours present)
        *.zip) python3 -m zipfile -e "$HOME_ARCHIVE" "$USER_DIR" || die "Extraction de la configuration echouee." ;;
        *)     tar -xzf "$HOME_ARCHIVE" -C "$USER_DIR" || die "Extraction de la configuration echouee." ;;
    esac
    ok "Themes, polices, sons et videos installes dans $USER_DIR"
else
    warn "Configuration d'exemple non fournie : $USER_DIR est vide"
fi
chown -R "$TARGET_USER:$TARGET_USER" "$USER_DIR" "$TARGET_HOME/Pictures" "$TARGET_HOME/Videos" "$TARGET_HOME/Desktop"
chmod -R 777 "$USER_DIR"

# ============================================================
# ETAPE 6 : Configuration du systeme
# ============================================================

step 'Configuration du systeme...'

# Le jeu lance ses serveurs de LED, l'arret du Pi et ses nettoyages avec sudo, sans
# personne pour saisir un mot de passe. Sur Trixie, sudo en demande un par defaut.
SUDOERS=/etc/sudoers.d/010_raspydarts-nopasswd
echo "$TARGET_USER ALL=(ALL) NOPASSWD: ALL" > "$SUDOERS.tmp"
if visudo -cf "$SUDOERS.tmp" >/dev/null 2>&1; then
    mv "$SUDOERS.tmp" "$SUDOERS"
    chmod 440 "$SUDOERS"
    ok "sudo sans mot de passe pour $TARGET_USER (LED, arret du Pi)"
else
    rm -f "$SUDOERS.tmp"
    warn "sudo sans mot de passe non configure : les LED ne demarreront pas"
fi

# RaspyDarts a besoin de X11 : fenetre plein ecran, videos par-dessus le jeu, xdotool, scrot
raspi-config nonint do_wayland W1 >/dev/null 2>&1 && ok 'Session graphique X11' || warn 'Passage en X11 echoue (raspi-config > Advanced > Wayland > X11)'
raspi-config nonint do_boot_behaviour B4 >/dev/null 2>&1 && ok 'Demarrage sur le bureau, session automatique' || warn 'Reglage du demarrage automatique echoue'
# Pas de console sur l'ecran : sa ligne de connexion et son curseur passaient entre
# l'image de demarrage et la video (les autres consoles restent sur Ctrl+Alt+F2..F6)
systemctl disable getty@tty1.service >/dev/null 2>&1
CMDLINE=/boot/firmware/cmdline.txt
[ -f "$CMDLINE" ] && ! grep -q 'vt.global_cursor_default=0' "$CMDLINE" && sed -i '1s/$/ vt.global_cursor_default=0/' "$CMDLINE"
ok 'Console masquee au demarrage'
raspi-config nonint do_i2c 0 && ok 'I2C active (MCP23017)' || warn "Activation de l'I2C echouee"
# Paves USB : lus (input) et programmes (plugdev) par le jeu
write_usb_pads_rule /etc/udev/rules.d/72-raspydarts-usb-pads.rules
usermod -aG input,plugdev "$TARGET_USER"
udevadm control --reload-rules >/dev/null 2>&1
ok 'Paves USB de touches et de molettes'
# raspi-config active wayvnc si la session en cours est encore Wayland (carte neuve) : le jeu
# tourne en X11, c'est le serveur RealVNC qu'il faut
raspi-config nonint do_vnc 0 >/dev/null 2>&1
systemctl disable wayvnc.service >/dev/null 2>&1
systemctl enable vncserver-x11-serviced.service >/dev/null 2>&1 && systemctl is-enabled vncserver-x11-serviced >/dev/null 2>&1 && ok 'VNC active (prise en main a distance)' || warn 'VNC non active (a regler dans raspi-config)'
# Pas de bulle "utilisateur connecte / deconnecte" par-dessus le jeu
VNC_CONF=/root/.vnc/config.d/vncserver-x11
mkdir -p "$(dirname "$VNC_CONF")"
touch "$VNC_CONF"
sed -i '/^ConnNotifyTimeout=/d' "$VNC_CONF"
echo 'ConnNotifyTimeout=0' >> "$VNC_CONF"
systemctl try-restart vncserver-x11-serviced >/dev/null 2>&1
raspi-config nonint do_blanking 1 >/dev/null 2>&1 && ok "Mise en veille de l'ecran desactivee" || warn "Mise en veille de l'ecran non desactivee (a regler dans raspi-config)"

raspi-config nonint do_change_locale "$DEFAULT_LOCALE" >/dev/null 2>&1 || warn "Langue $DEFAULT_LOCALE non appliquee"
raspi-config nonint do_change_timezone "$DEFAULT_TIMEZONE" >/dev/null 2>&1 || warn "Fuseau $DEFAULT_TIMEZONE non applique"
raspi-config nonint do_configure_keyboard "$DEFAULT_KEYBOARD" >/dev/null 2>&1 || warn "Clavier $DEFAULT_KEYBOARD non applique"
ok "Langue $DEFAULT_LOCALE, fuseau $DEFAULT_TIMEZONE, clavier $DEFAULT_KEYBOARD"

# Affichage et videos comme sous Buster (voir patch_config_txt) : seulement si omxplayer
# est installe, sinon l'affichage KMS et VLC sont conserves (videos dans des fenetres)
BUSTER_MODE=0
PI_MODEL="$(tr -d '\0' < /proc/device-tree/model 2>/dev/null)"
case "$PI_MODEL" in
    *"Raspberry Pi 5"*|*"Compute Module 5"*|*"Raspberry Pi 500"*)
        warn "$PI_MODEL : pas d'affichage gere par le firmware, videos par VLC"
        ;;
    *)
        OMX_ARCHIVE="/tmp/$OMX_ASSET"
        # Archive copiee avec ce script (install_raspydarts.ps1), sinon celle de la release
        OMX_LOCAL="$(dirname "$(readlink -f "$0")")/$OMX_ASSET"
        if [ -s "$OMX_LOCAL" ]; then
            mv -f "$OMX_LOCAL" "$OMX_ARCHIVE"
            ok "omxplayer : archive copiee avec le script"
        else
            curl -fsSL --retry 3 -o "$OMX_ARCHIVE" "$OMX_URL"
        fi
        if [ -s "$OMX_ARCHIVE" ] && tar -tzf "$OMX_ARCHIVE" ./usr/bin/omxplayer.bin >/dev/null 2>&1; then
            tar -xzf "$OMX_ARCHIVE" -C / --no-overwrite-dir
            rm -f "$OMX_ARCHIVE"
            ldconfig
            if omxplayer --version >/dev/null 2>&1; then
                BUSTER_MODE=1
                ok 'omxplayer installe (videos au-dessus de tout, comme sous Buster)'
            else
                warn 'omxplayer installe mais ne demarre pas : videos par VLC'
            fi
        else
            rm -f "$OMX_ARCHIVE"
            warn "omxplayer non telecharge ($OMX_URL) : videos par VLC"
        fi
        ;;
esac

if [ "$BUSTER_MODE" = "1" ]; then
    CONFIG_TXT=/boot/firmware/config.txt
    [ -f "$CONFIG_TXT.kms" ] || cp "$CONFIG_TXT" "$CONFIG_TXT.kms"
    patch_config_txt "$CONFIG_TXT"
    CMDLINE=/boot/firmware/cmdline.txt
    [ -f "$CMDLINE.kms" ] || cp "$CMDLINE" "$CMDLINE.kms"
    patch_cmdline "$CMDLINE"
    mkdir -p /etc/X11/xorg.conf.d
    write_xorg_fbdev /etc/X11/xorg.conf.d/98-raspydarts-fbdev.conf
    write_fb_seat_rule /etc/udev/rules.d/71-raspydarts-fb-seat.rules
    write_lightdm_unit /etc/systemd/system/lightdm.service
    ok "Affichage gere par le firmware (config.txt.kms : reglage d'origine)"

    # Mode de l'ecran : script du depot (scripts/raspydarts_display.py), remis a jour par
    # scripts/reglages_systeme.sh
    install -m 755 "$PYDARTS/scripts/raspydarts_display.py" /usr/local/bin/raspydarts-display
    write_display_unit /etc/systemd/system/raspydarts-display.service
    write_network_script /usr/local/bin/raspydarts-network
    chmod 755 /usr/local/bin/raspydarts-network
    write_network_unit /etc/systemd/system/raspydarts-network.service
    write_intro_unit /etc/systemd/system/raspydarts-intro.service
    USER_UNITS="$TARGET_HOME/.config/systemd/user"
    mkdir -p "$USER_UNITS/default.target.wants"
    write_game_user_unit "$USER_UNITS/raspydarts.service"
    ln -sf ../raspydarts.service "$USER_UNITS/default.target.wants/raspydarts.service"
    chown -R "$TARGET_USER:$TARGET_USER" "$TARGET_HOME/.config"
    systemctl daemon-reload
    systemctl enable raspydarts-display.service raspydarts-network.service raspydarts-intro.service >/dev/null 2>&1 \
        && ok "Video d'introduction des la fin de l'image de demarrage, jeu charge dessous" \
        || warn "Services de demarrage RaspyDarts non actives"
    ok "Mode de l'ecran lu dans son EDID a chaque demarrage (un redemarrage de plus si besoin)"
    ok 'Connexions reseau converties hors de netplan au premier demarrage (demarrage plus rapide)'
fi

AUTOSTART=/etc/xdg/lxsession/rpd-x/autostart
if [ -f "$AUTOSTART" ]; then
    write_desktop_script /usr/local/bin/raspydarts-desktop
    write_audio_script /usr/local/bin/raspydarts-audio
    chmod 755 /usr/local/bin/raspydarts-desktop /usr/local/bin/raspydarts-audio
    patch_autostart "$AUTOSTART"
    USER_AUTOSTART="$TARGET_HOME/.config/lxsession/rpd-x/autostart"
    [ -f "$USER_AUTOSTART" ] && patch_autostart "$USER_AUTOSTART"
    [ "$BUSTER_MODE" = "1" ] || ok "Video d'introduction et RaspyDarts lances a l'ouverture de session, bureau ensuite"
    ok 'Son regle sur la sortie HDMI a plein volume au premier demarrage'
    ok "Affichage synchronise sur l'ecran (picom)"
else
    warn "$AUTOSTART absent : lancement automatique non configure"
fi

write_boot_script /usr/local/sbin/raspydarts-boot
chmod 755 /usr/local/sbin/raspydarts-boot
write_boot_unit /etc/systemd/system/raspydarts-boot.service
systemctl daemon-reload
systemctl enable raspydarts-boot.service >/dev/null 2>&1 && ok 'Recuperation au demarrage de raspydarts.cfg / .raspydarts deposes sur la partition de demarrage' || warn 'Service raspydarts-boot non active'

if [ -f "$PYDARTS/desktop/Raspydarts.desktop" ]; then
    sed "s#/raspydarts/#$PYDARTS/#g" "$PYDARTS/desktop/Raspydarts.desktop" > "$TARGET_HOME/Desktop/Raspydarts.desktop"
    chown "$TARGET_USER:$TARGET_USER" "$TARGET_HOME/Desktop/Raspydarts.desktop"
    chmod 755 "$TARGET_HOME/Desktop/Raspydarts.desktop"
    ok 'Raccourci sur le bureau'
fi

# Habillage du demarrage (image de demarrage : scripts/reglages_systeme.sh, en fin d'etape),
# ecran de connexion et bureau aux couleurs de RaspyDarts
# L'image de demarrage reste a l'ecran jusqu'a la video d'introduction : elle n'est
# effacee ni a la fin du demarrage, ni au lancement du serveur graphique
mkdir -p /etc/systemd/system/plymouth-quit.service.d
printf '[Service]\nExecStart=\nExecStart=-/usr/bin/plymouth quit --retain-splash\n' > /etc/systemd/system/plymouth-quit.service.d/raspydarts.conf
write_display_setup_script /usr/local/bin/raspydarts-display-setup
chmod 755 /usr/local/bin/raspydarts-display-setup
patch_lightdm /etc/lightdm/lightdm.conf
systemctl daemon-reload
ok "Image de demarrage conservee jusqu'a la video d'introduction"

if [ -f /etc/lightdm/pi-greeter.conf ]; then
    patch_greeter /etc/lightdm/pi-greeter.conf
    ok "Fond de l'ecran de connexion"
fi

DESKTOP_CONF="$TARGET_HOME/.config/pcmanfm/default/desktop-items-0.conf"
mkdir -p "$(dirname "$DESKTOP_CONF")"
patch_desktop "$DESKTOP_CONF"
# Le raccourci RaspyDarts du bureau se lance sans demander "executer / ouvrir".
# pcmanfm-pi lit ce reglage dans son pcmanfm.conf (pas dans libfm/libfm.conf).
PCMANFM_CONF="$TARGET_HOME/.config/pcmanfm/default/pcmanfm.conf"
[ -f "$PCMANFM_CONF" ] || cp /etc/xdg/pcmanfm/default/pcmanfm.conf "$PCMANFM_CONF" 2>/dev/null || printf '[config]\n' > "$PCMANFM_CONF"
if grep -q '^quick_exec=' "$PCMANFM_CONF"; then
    sed -i 's/^quick_exec=.*/quick_exec=1/' "$PCMANFM_CONF"
else
    sed -i '0,/^\[config\]/s//[config]\nquick_exec=1/' "$PCMANFM_CONF"
fi
chown -R "$TARGET_USER:$TARGET_USER" "$TARGET_HOME/.config"
ok 'Fond du bureau, raccourci RaspyDarts lance sans question'

if [ -f /etc/samba/smb.conf ]; then
    patch_smb_conf /etc/samba/smb.conf
    systemctl restart smbd >/dev/null 2>&1
    ok 'Partages reseau (Backup, Logs, Personnalisation, Videos Cam, Images Cam)'
else
    warn 'Samba absent : partages reseau non configures'
fi

# Le serveur MQTT ne sert qu'en local (LED, DMD, Hue) : il n'a pas a attendre le reseau,
# sinon le jeu, pret avant lui, demarre sans ses LED
MQTT_UNIT=/usr/lib/systemd/system/mosquitto.service
if [ -f "$MQTT_UNIT" ]; then
    grep -v -E '^(After|Wants)=network(-online)?\.target$' "$MQTT_UNIT" > /etc/systemd/system/mosquitto.service
    systemctl daemon-reload
fi
systemctl enable mosquitto >/dev/null 2>&1 && ok 'Serveur MQTT (mosquitto) active, sans attendre le reseau' || warn 'mosquitto non active'

# Demarrage allege
DISABLED=""
for unit in $SERVICES_OFF; do
    if systemctl cat "$unit" >/dev/null 2>&1; then
        systemctl mask --now "$unit" >/dev/null 2>&1 && DISABLED="$DISABLED ${unit%.*}"
    fi
done
ok "Services inutiles desactives :$DISABLED"

# Par defaut, l'ouverture de session attend que le reseau soit pret. Sur Trixie, le
# demarrage du reseau prend une quinzaine de secondes : la borne n'a pas a l'attendre.
SESSIONS_UNIT=/usr/lib/systemd/system/systemd-user-sessions.service
if [ -f "$SESSIONS_UNIT" ] && grep -q '^After=.* network\.target' "$SESSIONS_UNIT"; then
    sed 's/^\(After=.*\) network\.target/\1/' "$SESSIONS_UNIT" > /etc/systemd/system/systemd-user-sessions.service
    systemctl daemon-reload
    ok "Ecran de connexion lance sans attendre le reseau"
else
    warn "Ouverture de session : dependance au reseau non retiree (demarrage plus long)"
fi

mkdir -p "$TARGET_HOME/.config/autostart"
for program in $SESSION_OFF; do
    if [ -f "/etc/xdg/autostart/$program.desktop" ]; then
        printf '[Desktop Entry]\nType=Application\nName=%s\nHidden=true\n' "$program" > "$TARGET_HOME/.config/autostart/$program.desktop"
    fi
done

PANEL_CONF="$TARGET_HOME/.config/lxpanel-pi/panels/panel"
if [ ! -f "$PANEL_CONF" ] && [ -f /etc/xdg/lxpanel-pi/panels/panel ]; then
    mkdir -p "$(dirname "$PANEL_CONF")"
    cp /etc/xdg/lxpanel-pi/panels/panel "$PANEL_CONF"
fi
if [ -f "$PANEL_CONF" ]; then
    patch_panel "$PANEL_CONF"
    ok 'Bulles de notification du bureau desactivees'
else
    warn 'Configuration du panneau introuvable : notifications non desactivees'
fi
chown -R "$TARGET_USER:$TARGET_USER" "$TARGET_HOME/.config"

# Reglages du systeme qui evoluent avec RaspyDarts (image de demarrage, MQTT, bureau) : le meme
# script est relance par le jeu apres une mise a jour (bornes deja installees)
if [ -f "$PYDARTS/scripts/reglages_systeme.sh" ]; then
    bash "$PYDARTS/scripts/reglages_systeme.sh" "$TARGET_USER"
else
    warn "$PYDARTS/scripts/reglages_systeme.sh absent : image de demarrage, MQTT et bureau non regles"
fi

# ============================================================
# ETAPE 7 : Controle de l'installation
# ============================================================

step "Controle de l'installation..."

MISSING=""
# Depuis le dossier personnel : RPi.GPIO (rpi-lgpio) cree un fichier dans le dossier courant,
# l'import echouait si le script etait lance depuis un dossier non inscriptible (/)
for module in $PY_CHECK; do
    # Sans la verification des dependances de Blinka 10 (comme le jeu, include/cgpio_extender.py) :
    # elle echoue au hasard sur un Pi occupe, ici pendant l'installation
    ( cd "$TARGET_HOME" && sudo -u "$TARGET_USER" BLINKA_SKIP_DEPENDENCY_CHECK=1 python3 -c "import $module" ) >/dev/null 2>&1 || MISSING="$MISSING $module"
done
if [ -z "$MISSING" ]; then
    ok "Tous les modules Python sont importables par $TARGET_USER"
else
    warn "Modules Python non importables :$MISSING"
fi
python3 -c "import rpi_ws281x" >/dev/null 2>&1 && ok 'rpi_ws281x importable en root (ruban de LED)' || warn 'rpi_ws281x non importable en root'
python3 -c "import RPi.GPIO as G, sys; sys.exit('/usr/local/' in G.__file__)" >/dev/null 2>&1 && ok 'GPIO fourni par rpi-lgpio' || warn 'RPi.GPIO ne vient pas de rpi-lgpio : la cible risque de ne pas repondre'
if [ "$BUSTER_MODE" = "1" ]; then
    omxplayer --version >/dev/null 2>&1 && ok 'omxplayer present (videos)' || warn 'omxplayer ne demarre pas : les videos ne fonctionneront pas'
else
    command -v cvlc >/dev/null && ok 'VLC present (videos)' || warn 'VLC absent : les videos ne fonctionneront pas'
fi
( cd "$PYDARTS" && sudo -u "$TARGET_USER" python3 -W error -m compileall -q games include addons raspydarts.py >/dev/null 2>&1 ) && ok "Tout le code compile avec $(python3 --version)" || warn "Une partie du code ne compile pas avec $(python3 --version)"

# ============================================================
# ETAPE 8 : Nettoyage
# ============================================================

step 'Nettoyage...'

rm -f "$CODE_ARCHIVE"
[ "$HOME_ARCHIVE" = "-" ] || rm -f "$HOME_ARCHIVE"
find "$PYDARTS" -name '__pycache__' -type d -prune -exec rm -rf {} +
apt-get clean
ok 'Archives et cache apt supprimes'

printf '\n  \033[32m========================================================\n'
printf '  [OK] RaspyDarts %s installe\n' "$VERSION"
printf '  ========================================================\033[0m\n'
if [ -n "$WARNINGS" ]; then
    printf '\n  \033[33mPoints a verifier :\033[0m'
    printf "$WARNINGS\n"
fi
printf '\n  Redemarrez le Pi pour appliquer la session X11 et le lancement automatique.\n\n'
