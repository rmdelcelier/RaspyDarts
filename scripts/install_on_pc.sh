#!/bin/bash
# ==============================================================================
# RaspyDarts - Installation sur un ordinateur sous Linux (pas un Raspberry Pi)
# ==============================================================================
#
# Pour jouer avec Autodarts (ses cameras lisent les flechettes) ou une cible branchee en USB.
# Lance par install.sh quand il ne trouve pas de Raspberry Pi :
#
#   curl -fsSL https://raw.githubusercontent.com/rmdelcelier/RaspyDarts/main/install.sh | sudo bash
#
# Utilisation directe : sudo bash install_on_pc.sh <archive du code .tar.gz> <archive .raspydarts | -> [--yes]
#
# Debian 12/13, Ubuntu 24.04 ou leurs derivees (apt), avec un bureau graphique. Rien de ce qui est
# propre au Raspberry : ni broches (matrice de la cible, cartes MCP23017, rubans de LED), ni
# reglages du firmware, ni omxplayer (les videos passent par VLC). Le jeu le detecte de lui-meme
# (include/cplatform.py).
# ==============================================================================

set -u

TARGET_USER="${SUDO_USER:-}"
PYDARTS=/raspydarts
USER_DIR_NAME=.raspydarts
MIN_FREE_KB=4000000

# Paquets systeme indispensables (les memes que sur le Pi, sans ce qui sert aux broches)
APT_REQUIRED="python3-pip python3-dev python3-tk python3-pygame python3-numpy python3-pil python3-psutil
python3-requests python3-yaml python3-evdev python3-usb python3-serial python3-netifaces python3-qrcode
python3-websocket python3-googleapi python3-google-auth-oauthlib python3-google-auth-httplib2 python3-paho-mqtt
vlc ffmpeg v4l-utils espeak mpg123 alsa-utils pulseaudio-utils xdotool scrot gettext git curl unzip
mosquitto mosquitto-clients"

# Facultatifs (un echec n'arrete pas l'installation) : emojis des textes, curseur masque, voix francaise
APT_OPTIONAL="fonts-noto-color-emoji unclutter mbrola mbrola-fr1"

# Modules Python verifies en fin d'installation
PY_CHECK="pygame paho.mqtt.client netifaces qrcode websocket evdev usb serial googleapiclient
google_auth_oauthlib PIL numpy psutil requests yaml tkinter"

STEP=0
TOTAL=6
WARNINGS=""
ASSUME_YES=0

step() { STEP=$((STEP + 1)); printf '\n  \033[34m[%s/%s] %s\033[0m\n  --------------------------------------------------------\n' "$STEP" "$TOTAL" "$1"; }
ok()   { printf '  \033[32m[+]\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m[!]\033[0m %s\n' "$1"; WARNINGS="$WARNINGS\n    - $1"; }
die()  { printf '\n  \033[31m[ERREUR]\033[0m %s\n\n' "$1"; exit 1; }

confirm() {
    [ "$ASSUME_YES" = "1" ] && return 0
    printf '  %s [O/n] ' "$1"
    read -r answer
    case "$answer" in [nN]*) return 1 ;; *) return 0 ;; esac
}

CODE_ARCHIVE="${1:-}"
HOME_ARCHIVE="${2:--}"
[ "${3:-}" = "--yes" ] && ASSUME_YES=1

printf '\n  \033[36m========================================================\n'
printf '    RaspyDarts - Installation sur un ordinateur (Linux)\n'
printf '  ========================================================\033[0m\n'

# ------------------------------------------------------------------------------
step 'Verifications...'

[ "$(id -u)" -eq 0 ] || die "A lancer avec sudo."
[ -n "$TARGET_USER" ] && [ "$TARGET_USER" != "root" ] \
    || die "A lancer avec sudo depuis le compte qui fera tourner RaspyDarts, pas en root."
[ -f "$CODE_ARCHIVE" ] || die "Archive du code introuvable : $CODE_ARCHIVE"
[ "$HOME_ARCHIVE" = "-" ] || [ -f "$HOME_ARCHIVE" ] || die "Archive de la configuration introuvable : $HOME_ARCHIVE"
command -v apt-get >/dev/null || die "Systeme sans apt : prevu pour Debian, Ubuntu et leurs derivees."
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
[ -d "$TARGET_HOME" ] || die "L'utilisateur '$TARGET_USER' n'existe pas."
USER_DIR="$TARGET_HOME/$USER_DIR_NAME"
ok "Utilisateur : $TARGET_USER ($TARGET_HOME)"

. /etc/os-release
ok "Systeme : ${PRETTY_NAME:-?} ($(dpkg --print-architecture))"
if grep -q 'Raspberry Pi' /proc/device-tree/model 2>/dev/null; then
    die "C'est un Raspberry Pi : utilisez scripts/install_on_pi.sh (install.sh le choisit de lui-meme)."
fi

FREE_KB=$(df --output=avail -k / | tail -1 | tr -d ' ')
[ "$FREE_KB" -ge "$MIN_FREE_KB" ] || die "Espace libre insuffisant sur / : $((FREE_KB / 1024)) Mo (4 Go necessaires)."
ok "Espace libre : $((FREE_KB / 1024)) Mo"

if [ -e "$PYDARTS" ]; then
    printf '  \033[33m[!]\033[0m %s existe deja : ses fichiers seront remplaces par ceux de l archive.\n' "$PYDARTS"
    confirm 'Continuer ?' || exit 1
fi

# ------------------------------------------------------------------------------
step 'Installation des paquets systeme (apt)...'

export DEBIAN_FRONTEND=noninteractive
apt-get update || die "apt-get update a echoue (connexion Internet ?)."
apt-get install -y $APT_REQUIRED || die "Installation des paquets indispensables echouee."
ok 'Paquets indispensables installes'
for package in $APT_OPTIONAL; do
    if apt-get install -y "$package" >/dev/null 2>&1; then
        ok "$package"
    else
        warn "Paquet facultatif non installe : $package"
    fi
done

# paho-mqtt 2 (celui de Raspy2DMD et du Pi) : Ubuntu 24.04 n'a que la 1.6
if ! python3 -c 'import paho.mqtt, sys; sys.exit(0 if int(paho.mqtt.__version__.split(".")[0]) >= 2 else 1)' 2>/dev/null; then
    pip3 install --break-system-packages --root-user-action=ignore 'paho-mqtt>=2' \
        || pip3 install 'paho-mqtt>=2' || die "Installation de paho-mqtt 2 echouee."
    ok 'paho-mqtt 2 installe (pip)'
fi

# ------------------------------------------------------------------------------
step "Installation du code dans $PYDARTS..."

mkdir -p "$PYDARTS"
# Archive de GitHub : un dossier racine (RaspyDarts-main/) a retirer
TOP="$(tar -tzf "$CODE_ARCHIVE" 2>/dev/null | head -1 | cut -d/ -f1)"
STRIP=""
if [ -n "$TOP" ] && [ "$TOP" != "." ] && tar -tzf "$CODE_ARCHIVE" "$TOP/VERSION" >/dev/null 2>&1; then
    STRIP="--strip-components=1"
fi
tar -xzf "$CODE_ARCHIVE" -C "$PYDARTS" $STRIP || die "Extraction du code echouee."
mkdir -p "$PYDARTS/logs" "$PYDARTS/backup"
find "$PYDARTS" -name '*.sh' -exec sed -i 's/\r$//' {} + -exec chmod 755 {} +
chown -R "$TARGET_USER:$TARGET_USER" "$PYDARTS"
chmod 777 "$PYDARTS/logs" "$PYDARTS/backup"
[ -s "$PYDARTS/VERSION" ] || die "Fichier VERSION absent de l'archive."
ok "RaspyDarts $(cat "$PYDARTS/VERSION") installe"

# ------------------------------------------------------------------------------
step "Installation de la configuration d'exemple..."

mkdir -p "$USER_DIR"
if [ "$HOME_ARCHIVE" != "-" ]; then
    case "$HOME_ARCHIVE" in
        *.zip) python3 -m zipfile -e "$HOME_ARCHIVE" "$USER_DIR" || die "Extraction de la configuration echouee." ;;
        *)     tar -xzf "$HOME_ARCHIVE" -C "$USER_DIR" || die "Extraction de la configuration echouee." ;;
    esac
    ok "Themes, polices, sons et videos installes dans $USER_DIR"
else
    warn "Configuration d'exemple non fournie : $USER_DIR est vide"
fi
chown -R "$TARGET_USER:$TARGET_USER" "$USER_DIR"

# ------------------------------------------------------------------------------
step 'Configuration du systeme...'

# Le jeu eteint l'ordinateur (Quitter), installe Autodarts et nettoie ses fichiers avec sudo
SUDOERS=/etc/sudoers.d/010_raspydarts-nopasswd
if confirm "Autoriser $TARGET_USER a utiliser sudo sans mot de passe (Quitter eteint l'ordinateur, installation d'Autodarts depuis le jeu) ?"; then
    echo "$TARGET_USER ALL=(ALL) NOPASSWD: ALL" > "$SUDOERS.tmp"
    if visudo -cf "$SUDOERS.tmp" >/dev/null 2>&1; then
        mv "$SUDOERS.tmp" "$SUDOERS"
        chmod 440 "$SUDOERS"
        ok "sudo sans mot de passe pour $TARGET_USER"
    else
        rm -f "$SUDOERS.tmp"
        warn "sudo sans mot de passe non configure"
    fi
else
    warn "sudo demandera un mot de passe : Quitter et l'installation d'Autodarts ne marcheront pas depuis le jeu"
fi

# Paves USB a boutons et molettes : lus (input) et programmes (plugdev) par le jeu
cat > /etc/udev/rules.d/72-raspydarts-usb-pads.rules <<'EOF'
# RaspyDarts : pave USB a boutons (1189:8890), programme par le jeu
SUBSYSTEM=="usb", ATTR{idVendor}=="1189", ATTR{idProduct}=="8890", MODE="0660", GROUP="plugdev"
EOF
udevadm control --reload-rules >/dev/null 2>&1
usermod -aG input,plugdev,video,audio "$TARGET_USER"
ok "Paves USB, camera et son accessibles a $TARGET_USER (a la prochaine ouverture de session)"

# Serveur MQTT local (LED, afficheur DMD, Philips Hue, Raspy2DMD sur une autre machine)
systemctl enable --now mosquitto >/dev/null 2>&1 && ok 'Serveur MQTT (mosquitto) active' || warn 'mosquitto non active'

# RaspyDarts a l'ouverture de la session (tous les bureaux : GNOME, KDE, Xfce...) et sur le bureau
AUTOSTART_DIR="$TARGET_HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cat > "$AUTOSTART_DIR/raspydarts.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=RaspyDarts
Comment=RaspyDarts a l'ouverture de la session
Exec=$PYDARTS/RaspyDarts.sh
Icon=$PYDARTS/images/icon.png
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
DESKTOP_DIR="$(sudo -u "$TARGET_USER" xdg-user-dir DESKTOP 2>/dev/null || echo "$TARGET_HOME/Desktop")"
mkdir -p "$DESKTOP_DIR"
if [ -f "$PYDARTS/desktop/Raspydarts.desktop" ]; then
    sed "s#/raspydarts/#$PYDARTS/#g" "$PYDARTS/desktop/Raspydarts.desktop" > "$DESKTOP_DIR/Raspydarts.desktop"
    chmod 755 "$DESKTOP_DIR/Raspydarts.desktop"
fi
mkdir -p /usr/local/share/applications
sed "s#/raspydarts/#$PYDARTS/#g" "$PYDARTS/desktop/Raspydarts.desktop" > /usr/local/share/applications/raspydarts.desktop 2>/dev/null
chown -R "$TARGET_USER:$TARGET_USER" "$AUTOSTART_DIR" "$DESKTOP_DIR"
ok "RaspyDarts lance a l'ouverture de la session, raccourci sur le bureau et dans le menu"

# ------------------------------------------------------------------------------
step 'Verification...'

MISSING=""
for module in $PY_CHECK; do
    sudo -u "$TARGET_USER" python3 -c "import $module" >/dev/null 2>&1 || MISSING="$MISSING $module"
done
if [ -z "$MISSING" ]; then
    ok "Tous les modules Python sont importables par $TARGET_USER"
else
    warn "Modules Python manquants :$MISSING"
fi
( cd "$PYDARTS" && sudo -u "$TARGET_USER" python3 -m compileall -q games include addons raspydarts.py >/dev/null 2>&1 ) \
    && ok "Tout le code compile avec $(python3 --version)" || warn "Une partie du code ne compile pas avec $(python3 --version)"
command -v cvlc >/dev/null && ok 'Videos par VLC' || warn 'VLC absent : pas de videos'

printf '\n  \033[36m========================================================\033[0m\n'
if [ -n "$WARNINGS" ]; then
    printf '  \033[33mInstallation terminee avec des avertissements :\033[0m'
    printf "$WARNINGS\n"
else
    printf '  \033[32mInstallation terminee.\033[0m\n'
fi
printf '\n  RaspyDarts demarre a la prochaine ouverture de session, ou maintenant par\n'
printf '  le raccourci du bureau. Pour les flechettes : Parametres > Autodarts (adresse\n'
printf '  de votre Autodarts), ou une cible branchee en USB.\n\n'
exit 0
