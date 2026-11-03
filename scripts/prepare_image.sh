#!/bin/bash
# Prepare a RaspyDarts card for the image published with Raspberry Pi Imager
# (scripts/publish image GitHub/publish_image.bat) : on a card installed by install.sh and
# tested, everything the tests and the owner left is removed, the identity of the machine is
# made again at the first start of each card made from the image.
#
#   sudo bash /raspydarts/scripts/prepare_image.sh              shows what would be done
#   sudo bash /raspydarts/scripts/prepare_image.sh --appliquer  does it, then switches off
#
# Removed or reset :
#   - ~/.raspydarts : replaced by the archive of the release « exemple » (as install.sh puts it) :
#     settings, players, scores, favorites, online session, coin acceptor, gallery password...
#     and without raspydarts.cfg (made again by the game at the first start)
#   - Raspy2DMD (installed in mode Pico seul, required) : its configuration written again with
#     the settings of that installation only, its backups and logs removed
#   - photos and clips of the gallery, logs of the game, files left in the personal folder
#     (whatever is not a folder of a new Raspberry Pi OS or of the installation)
#   - Wi-Fi and network (NetworkManager, netplan), what Raspberry Pi Imager wrote on the boot
#     partition (user, Wi-Fi : user-data, network-config), state of cloud-init : the settings
#     chosen in Imager for each card are applied at its first start
#   - identity : machine-id (the SSH keys are made again at the first start :
#     regenerate_ssh_host_keys.service, ConditionFirstBoot), key of the VNC server, histories,
#     caches, known SSH hosts
# Kept : the user raspydarts / raspydarts, SSH and VNC enabled (checked here), the game in
# /raspydarts, the system and its settings (config.txt, boot screen...).

set -u

APPLY=0
[ "${1:-}" = "--appliquer" ] && APPLY=1

TARGET_USER=raspydarts
TARGET_HOME=/home/$TARGET_USER
USER_DIR=$TARGET_HOME/.raspydarts
GAME_DIR=/raspydarts
BOOT=/boot/firmware
EXAMPLE_URL="https://github.com/rmdelcelier/RaspyDarts/releases/download/exemple/raspydarts_example.zip"
# Folders and files of a new personal folder (Raspberry Pi OS with desktop) and of install.sh
HOME_KEEP=".bashrc .bash_logout .profile .config .local .raspydarts .Xauthority .vnc .ssh
Desktop Documents Downloads Music Pictures Public Templates Videos Bookshelf"
# Emptied (their folder kept)
HOME_EMPTY="Documents Downloads Music Pictures Public Templates Videos"

say()  { printf '%s\n' "$*"; }
step() { printf '\n== %s\n' "$*"; }
# A command shown, done with --appliquer only
run()  { if [ $APPLY -eq 1 ]; then "$@"; else say "   (ferait) $*"; fi; }
# A file or folder listed, removed with --appliquer only
remove() { say "   retire : ${1#$TARGET_HOME/}"; [ $APPLY -eq 1 ] && rm -rf "$1"; }

[ "$(id -u)" -eq 0 ] || { say "A lancer avec sudo."; exit 1; }
id "$TARGET_USER" >/dev/null 2>&1 || { say "Utilisateur $TARGET_USER absent : ce n'est pas une carte RaspyDarts."; exit 1; }
[ -d "$GAME_DIR" ] || { say "$GAME_DIR absent : ce n'est pas une carte RaspyDarts."; exit 1; }

if [ $APPLY -eq 0 ]; then
    say "SIMULATION : rien n'est modifie. Relancer avec --appliquer pour le faire (la carte s'eteint a la fin)."
fi

# Raspy2DMD is in the image, installed in mode « Pico seul » (Paramètres > Afficheur DMD)
if [ ! -f /Raspy2DMD/.pico_seul ]; then
    say "Raspy2DMD n'est pas installe en mode Pico seul (/Raspy2DMD/.pico_seul absent) : l'installer"
    say "d'abord depuis le jeu (Parametres > Afficheur DMD (Raspy2DMD)), puis relancer ce script."
    exit 1
fi

step "Jeu et Raspy2DMD arretes"
run pkill -f "RaspyDarts.sh"
run pkill -f "python3 raspydarts.py"
run pkill -f "Leds_Server"
run pkill -f "ctarget_reader"
run bash /Raspy2DMD/StopAllRaspy2DMD.sh

step "Donnees du jeu (~/.raspydarts) : remplacees par l'archive de la release exemple"
ARCHIVE=/tmp/raspydarts_example.zip
if [ $APPLY -eq 1 ]; then
    # Downloaded first : nothing is removed without it
    curl -fsSL --retry 3 -o "$ARCHIVE" "$EXAMPLE_URL" || { say "Telechargement de l'exemple impossible (Internet ?) : rien n'est modifie."; exit 1; }
    rm -rf "$USER_DIR"
    mkdir -p "$USER_DIR"
    python3 -m zipfile -e "$ARCHIVE" "$USER_DIR" || { say "Extraction de l'exemple echouee."; exit 1; }
    rm -f "$ARCHIVE"
    # The configuration of the game : made again by it at the first start (or the one put on
    # the boot partition from the page of the installation)
    rm -f "$USER_DIR/raspydarts.cfg" "$USER_DIR/pydarts.cfg"
    chown -R "$TARGET_USER:$TARGET_USER" "$USER_DIR"
    chmod -R 777 "$USER_DIR"
    say "   $(find "$USER_DIR" -type f | wc -l) fichiers remis, sans raspydarts.cfg (recree au 1er demarrage)"
else
    say "   (ferait) telecharger $EXAMPLE_URL, vider $USER_DIR et y extraire l'archive, sans raspydarts.cfg"
    find "$USER_DIR" -maxdepth 1 -type f -printf '   reglage retire : %f\n' 2>/dev/null
fi

step "Raspy2DMD : configuration remise a celle de son installation en mode Pico, journaux"
# Its general defaults would make sound and look for the game at raspydarts.local : the file is
# written again with the settings of its installation in mode Pico seul only
# (install_raspy2dmd.sh --pico-seul), what the tests changed is lost
R2D_CFG=/Medias/Raspy2DMD.cfg
say "   $R2D_CFG remis a neuf (sortie Pico, RaspyDarts sur cette machine, son coupe, sans bouton)"
if [ $APPLY -eq 1 ]; then
    # Its owner and rights kept (Raspy2DMD keeps it readable by itself only : 600)
    R2D_MODE=$(stat -c %a "$R2D_CFG" 2>/dev/null || echo 600)
    R2D_OWNER=$(stat -c %U:%G "$R2D_CFG" 2>/dev/null || echo raspy2dmd:raspy2dmd)
    cat > "$R2D_CFG" <<'R2DCFG'
[DMDRenderer]
pico_reconnect_timeout = 5
interrupteur = 0

[HDMI]
display_output = pico
hide_console = 0

[Pico]
pico_auto_detect = 1
pico_display_enabled = 1

[Running]
raspydarts_enabled = 1
raspydarts = localhost
raspydartscanal = raspydarts/dmd
default = 0

[Sound]
volume = 0
R2DCFG
    chown "$R2D_OWNER" "$R2D_CFG"
    chmod "$R2D_MODE" "$R2D_CFG"
fi
for path in /Medias/.config_backups /Medias/Logs/*; do
    [ -e "$path" ] || continue
    remove "$path"
done

step "Dossier personnel : fichiers laisses par les essais"
for entry in "$TARGET_HOME"/* "$TARGET_HOME"/.[!.]*; do
    [ -e "$entry" ] || continue
    name=$(basename "$entry")
    case " $(echo $HOME_KEEP) " in
        *" $name "*) continue ;;
    esac
    remove "$entry"
done
for name in $HOME_EMPTY; do
    [ -d "$TARGET_HOME/$name" ] || continue
    count=$(find "$TARGET_HOME/$name" -mindepth 1 | wc -l)
    [ "$count" -eq 0 ] && continue
    say "   $name vide ($count elements)"
    run find "$TARGET_HOME/$name" -mindepth 1 -delete
done
# Bureau : the shortcut of the game only
for entry in "$TARGET_HOME"/Desktop/*; do
    [ -e "$entry" ] || continue
    [ "$(basename "$entry")" = "Raspydarts.desktop" ] && continue
    remove "$entry"
done
# Histories, caches, recent files, browser, SSH : of the user and of root
for path in "$TARGET_HOME/.cache" "$TARGET_HOME/.local/share/recently-used.xbel" \
            "$TARGET_HOME/.local/share/Trash" "$TARGET_HOME/.config/chromium" \
            "$TARGET_HOME/.ssh/known_hosts" "$TARGET_HOME/.ssh/known_hosts.old" \
            "$TARGET_HOME/.ssh/authorized_keys" /root/.bash_history /root/.cache \
            /root/.ssh/known_hosts /root/.ssh/known_hosts.old /root/.wget-hsts /root/.npm \
            /root/netplan-sauvegarde /root/keyfiles-sauvegarde; do
    [ -e "$path" ] || continue
    remove "$path"
done

step "Jeu (/raspydarts) : journaux et fichiers de travail"
for path in "$GAME_DIR"/logs/* "$GAME_DIR"/restart "$GAME_DIR"/nohup.out; do
    [ -e "$path" ] || continue
    remove "$path"
done
count=$(find "$GAME_DIR" -name __pycache__ -type d | wc -l)
[ "$count" -gt 0 ] && { say "   $count dossiers __pycache__"; run find "$GAME_DIR" -name __pycache__ -type d -prune -exec rm -rf {} +; }

step "Reseau : Wi-Fi et connexions enregistrees"
for path in /etc/NetworkManager/system-connections/* /etc/netplan/*.yaml /etc/wpa_supplicant/wpa_supplicant.conf; do
    [ -e "$path" ] || continue
    remove "$path"
done

step "Partition de demarrage : ce que Raspberry Pi Imager y a ecrit"
for path in "$BOOT"/raspydarts.cfg "$BOOT"/raspydarts.cfg.* "$BOOT"/pydarts.cfg "$BOOT"/.raspydarts "$BOOT"/.pydarts \
            "$BOOT"/firstrun.sh "$BOOT"/wpa_supplicant.conf; do
    [ -e "$path" ] || continue
    remove "$path"
done
say "   user-data, network-config, meta-data : remis a neuf (ni utilisateur ni Wi-Fi)"
if [ $APPLY -eq 1 ]; then
    printf '#cloud-config\n# RaspyDarts : Raspberry Pi Imager remplace ce fichier par les reglages choisis\n' > "$BOOT/user-data"
    printf 'network:\n  version: 2\n  ethernets:\n    eth0:\n      dhcp4: true\n      optional: true\n' > "$BOOT/network-config"
    printf 'instance-id: raspydarts-image\n' > "$BOOT/meta-data"
fi
# Without a user in the settings of Imager (the page of the installation asks not to create
# one : raspydarts / raspydarts is in the image), cloud-init made its default user « pi »
say "   cloud-init : pas d'utilisateur « pi » cree quand Imager n'en demande pas"
if [ $APPLY -eq 1 ]; then
    printf '# RaspyDarts : l utilisateur raspydarts est dans l image\nusers: []\n' > /etc/cloud/cloud.cfg.d/91-raspydarts.cfg
fi
say "   cloud-init : etat efface, les reglages de Imager s'appliquent au 1er demarrage de chaque carte"
run cloud-init clean --logs

step "Identite de la machine (refaite au 1er demarrage de chaque carte)"
say "   machine-id vide : nouvel identifiant et nouvelles cles SSH au 1er demarrage"
if [ $APPLY -eq 1 ]; then
    echo uninitialized > /etc/machine-id
    rm -f /var/lib/dbus/machine-id
fi
if [ -f /root/.vnc/private.key ]; then
    say "   cle du serveur VNC : refaite au 1er demarrage"
    run rm -f /root/.vnc/private.key
fi

step "Acces a distance : SSH et VNC actives"
run systemctl enable ssh.service
run systemctl disable wayvnc.service
run systemctl enable vncserver-x11-serviced.service
if [ $APPLY -eq 1 ]; then
    systemctl is-enabled ssh.service >/dev/null 2>&1 && say "   SSH active" || say "   ATTENTION : SSH non active"
    systemctl is-enabled vncserver-x11-serviced.service >/dev/null 2>&1 && say "   VNC active" || say "   ATTENTION : VNC non active"
fi

step "Journaux et caches du systeme"
run apt-get clean
run journalctl --rotate
run journalctl --vacuum-time=1s
if [ $APPLY -eq 1 ]; then
    # The journal of systemd : by journalctl above (its files are not truncated)
    find /var/log -path /var/log/journal -prune -o -type f \( -name '*.gz' -o -name '*.[0-9]' -o -name '*.old' \) -print -delete >/dev/null
    find /var/log -path /var/log/journal -prune -o -type f -exec truncate -s 0 {} +
    rm -rf /var/tmp/* /tmp/* 2>/dev/null
else
    say "   (ferait) vider /var/log, /var/tmp et /tmp"
fi

if [ $APPLY -eq 1 ]; then
    step "Termine : la carte s'eteint. Ensuite : lire la carte en image (RaspyDarts_vX.Y.Z.img) et la publier"
    sync
    poweroff
else
    step "Simulation terminee : relire la liste ci-dessus, puis relancer avec --appliquer"
fi
