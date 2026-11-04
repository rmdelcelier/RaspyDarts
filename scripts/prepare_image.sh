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
#   - photos and clips of the gallery, logs of the game, files left in the personal folder
#     (whatever is not a folder of a new Raspberry Pi OS or of the installation)
#   - Wi-Fi and network (NetworkManager, netplan), what Raspberry Pi Imager wrote on the boot
#     partition (user, Wi-Fi : user-data, network-config), state of cloud-init : the settings
#     chosen in Imager for each card are applied at its first start
#   - Firefox, guide and books of Raspberry Pi OS ; translations of the system other than the
#     languages of the game, documentation of the packages (not put back by the updates)
#   - identity : machine-id (the SSH keys are made again at the first start :
#     regenerate_ssh_host_keys.service, ConditionFirstBoot), key of the VNC server, histories,
#     caches, known SSH hosts
# Refused : a card where Raspy2DMD is installed (the image compressed went over the 2 GiB of a
# file of a GitHub release : 2989 MB with it, 03/11/2026) ; it is installed from the game.
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

# Raspy2DMD is not in the image : installed from the game (Paramètres > Afficheur DMD)
if [ -d /Raspy2DMD ] || [ -d /Medias ]; then
    say "Raspy2DMD est installe (/Raspy2DMD, /Medias) : l'image depasserait les 2 Gio d'un fichier"
    say "de release GitHub. Partir d'une carte sans Raspy2DMD."
    exit 1
fi

if [ $APPLY -eq 1 ]; then
    # What is done is also written here, shown on the screen of the cabinet (below)
    LOG=/run/prepare_image.log
    : > "$LOG"
    chmod 644 "$LOG"
    exec > >(tee -a "$LOG") 2>&1
fi

step "Jeu arrete"
run pkill -f "RaspyDarts.sh"
run pkill -f "python3 raspydarts.py"
run pkill -f "Leds_Server"
run pkill -f "ctarget_reader"

if [ $APPLY -eq 1 ] && [ -S /tmp/.X11-unix/X0 ]; then
    # The game stopped : the progress on the screen of the cabinet, in a terminal on the desktop
    sudo -u "$TARGET_USER" DISPLAY=:0 XAUTHORITY="$TARGET_HOME/.Xauthority" setsid \
        lxterminal --geometry=110x35 --title="RaspyDarts : preparation de l'image" \
        -e "tail -n +1 -f $LOG" >/dev/null 2>&1 &
fi

step "Donnees du jeu (~/.raspydarts) : remplacees par l'archive de la release exemple"
# On the disk : /tmp is in the memory of the Pi (435 MB on a Pi 3), the archive (390 MB) filled it
# and the download stopped
ARCHIVE=/var/tmp/raspydarts_example.zip
if [ $APPLY -eq 1 ]; then
    # Downloaded first : nothing is removed without it
    say "   telechargement de l'archive exemple (environ 390 Mo)..."
    curl -fL -# --retry 3 -o "$ARCHIVE" "$EXAMPLE_URL" || { rm -f "$ARCHIVE"; say "Telechargement de l'exemple impossible (Internet ?) : rien n'est modifie."; exit 1; }
    say "   extraction..."
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

step "Partition agrandie au 1er demarrage de chaque carte"
# « resize » in cmdline.txt : at the first start, the initramfs grows the partition to the whole
# card (resize_early), gives the card a disk id of its own (set_partuuid) and removes the word ;
# rpi-resize.service grows the file system (first boot, see machine-id below). The image is
# shrunk without its own growing (pishrink.sh -s, publish_image.ps1)
say "   cmdline.txt : « resize » ajoute, identifiant de Raspberry Pi Imager (ds=nocloud;i=...) retire"
if [ $APPLY -eq 1 ]; then
    sed -i 's/ ds=nocloud;[^ ]*//g; s/ resize\b//g; s/[[:space:]]*$/ resize/' "$BOOT/cmdline.txt"
    say "   $(cat "$BOOT/cmdline.txt")"
fi
run systemctl enable rpi-resize.service

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

step "Logiciels inutiles a une borne, traductions et documentation du systeme (place dans l'image)"
# Firefox (Chromium kept), guide and books of Raspberry Pi OS, its wallpapers (the desktop and
# the login screen show the one of the game), Vulkan (used by neither the game nor Chromium on the
# Pi), English speech recognition (the announcements are made by espeak), headers of the kernel
# (to build drivers only), kernel v6 (Pi 1 and Zero, not supported) ; Thonny kept (some use it)
UNUSED_PACKAGES="firefox rpi-firefox-mods rpi-userguide rp-bookshelf rpd-wallpaper rpd-wallpaper-trixie
mesa-vulkan-drivers pocketsphinx-en-us linux-headers-* linux-image-rpi-v6 linux-image-*-rpi-v6"
# The patterns are for dpkg-query, not for the shell
set -f
installed=$(dpkg-query -W -f='${db:Status-Abbrev} ${Package}\n' $UNUSED_PACKAGES 2>/dev/null | awk '/^ii/ {print $2}')
set +f
if [ -n "$installed" ]; then
    apt-get -s purge --autoremove $installed 2>/dev/null | awk '/^Purg/ {print "   retire : paquet " $2}'
    [ $APPLY -eq 1 ] && DEBIAN_FRONTEND=noninteractive apt-get purge -y -q --autoremove $installed >/dev/null
fi
# Translations : the languages of the game only ; the updates do not put the others back
keep_lang() { case "$1" in fr*|en*|de*|es*|it*|nl*|C|locale.alias) return 0 ;; esac; return 1; }
freed=0
for base in /usr/share/locale /usr/share/help /usr/lib/chromium/locales; do
    for entry in "$base"/*; do
        [ -e "$entry" ] || continue
        keep_lang "$(basename "$entry")" && continue
        freed=$((freed + $(du -sk "$entry" | cut -f1)))
        [ $APPLY -eq 1 ] && rm -rf "$entry"
    done
done
# Documentation of the packages : their licence (copyright) kept
freed=$((freed + $(find /usr/share/doc -mindepth 1 ! -type d ! -name copyright -print0 | du -ck --files0-from=- 2>/dev/null | tail -1 | cut -f1)))
if [ $APPLY -eq 1 ]; then
    find /usr/share/doc -mindepth 1 ! -type d ! -name copyright -exec rm -f {} +
    find /usr/share/doc -mindepth 1 -type d -empty -delete
    cat > /etc/dpkg/dpkg.cfg.d/raspydarts-allegement <<'DPKG'
# RaspyDarts (scripts/prepare_image.sh) : traductions des langues du jeu seulement, sans documentation
path-exclude=/usr/share/locale/*
path-include=/usr/share/locale/locale.alias
path-exclude=/usr/share/help/*
path-include=/usr/share/help/C/*
path-exclude=/usr/lib/chromium/locales/*
path-exclude=/usr/share/doc/*
path-include=/usr/share/doc/*/copyright
DPKG
    for lang in fr en de es it nl; do
        printf 'path-include=/usr/share/locale/%s*\npath-include=/usr/share/help/%s*\npath-include=/usr/lib/chromium/locales/%s*\n' \
            "$lang" "$lang" "$lang" >> /etc/dpkg/dpkg.cfg.d/raspydarts-allegement
    done
fi
say "   traductions (hors fr, en, de, es, it, nl) et documentation : $((freed / 1024)) Mo retires"
say "   /etc/dpkg/dpkg.cfg.d/raspydarts-allegement : les mises a jour ne les remettent pas"

step "Journaux et caches du systeme"
run apt-get clean
run journalctl --rotate
run journalctl --vacuum-time=1s
if [ $APPLY -eq 1 ]; then
    # The journal of systemd : by journalctl above (its files are not truncated)
    # -exec rm, not -delete : find refuses -delete with -prune (the old logs were kept)
    find /var/log -path /var/log/journal -prune -o -type f \( -name '*.gz' -o -name '*.[0-9]' -o -name '*.old' \) -exec rm -f {} +
    find /var/log -path /var/log/journal -prune -o -type f -exec truncate -s 0 {} +
    rm -rf /var/tmp/* /tmp/* 2>/dev/null
else
    say "   (ferait) vider /var/log, /var/tmp et /tmp"
fi

step "Place occupee sur la carte (l'image compressee doit rester sous 2 Gio)"
df -h / | sed 's/^/   /'
du -xsh /usr /raspydarts "$USER_DIR" /var /opt /home 2>/dev/null | sort -rh | sed 's/^/   /'

if [ $APPLY -eq 1 ]; then
    step "Termine : la carte s'eteint dans 20 secondes. Ensuite : la lire en image (RaspyDarts_vX.Y.Z.img) SANS la redemarrer, et la publier"
    sync
    sleep 20
    poweroff
else
    step "Simulation terminee : relire la liste ci-dessus, puis relancer avec --appliquer"
fi
