#!/bin/bash
# ============================================================
# RaspyDarts - Reglages du systeme de la borne
# ============================================================
#
# Les reglages du systeme qui evoluent avec RaspyDarts : lances par l'installation
# (scripts/install_on_pi.sh) et par le jeu a son lancement quand sa version a change
# (include/cupdate.py, apply_system_settings) : une borne deja installee les recoit avec
# la mise a jour, sans reinstaller.
#
#   sudo bash /raspydarts/scripts/reglages_systeme.sh [utilisateur]
#
# Chaque reglage est refait a l'identique : sans effet s'il est deja en place. A la fin,
# la version de RaspyDarts reglee est notee dans /var/lib/raspydarts/reglages-systeme.
#
# ============================================================

set -u

PYDARTS=$(cd "$(dirname "$0")/.." && pwd)
TARGET_USER="${1:-${SUDO_USER:-raspydarts}}"
TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
STATE=/var/lib/raspydarts/reglages-systeme

ok()   { printf '  \033[32m[+]\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m[!]\033[0m %s\n' "$1"; }

[ "$(id -u)" -eq 0 ] || { echo "A lancer avec sudo."; exit 1; }
[ -n "$TARGET_HOME" ] && [ -d "$TARGET_HOME" ] || { echo "Utilisateur $TARGET_USER inconnu."; exit 1; }

# ------------------------------------------------------------
# Serveur MQTT ouvert au reseau local
# ------------------------------------------------------------
# Raspy2DMD sur une autre machine se connecte au MQTT de la borne (raspydarts.local) pour
# recevoir ses messages. mosquitto 2 (Trixie) n'ecoute que sur la machine elle-meme si rien
# n'est dit ; mosquitto 1 (Buster) ecoutait sur le reseau, sans mot de passe.
# Une seule ecoute par port : deux fichiers qui declarent « listener 1883 » empechent mosquitto
# de demarrer (plus de LED, demarrage lent). L'installation de Raspy2DMD sur la borne pose deja
# la sienne (raspy2dmd.conf) : la notre n'est alors pas mise (constate le 05/11 sur la 4.6.2)
MQTT_CONF=/etc/mosquitto/conf.d/raspydarts.conf
if [ -d /etc/mosquitto/conf.d ]; then
    NEW_MQTT=$(printf '%s\n' \
        '# RaspyDarts (scripts/reglages_systeme.sh) : ecoute sur le reseau local, sans mot de passe,' \
        '# comme sous Buster : Raspy2DMD sur une autre machine recoit les messages de la borne' \
        'listener 1883' \
        'allow_anonymous true')
    OTHER_LISTENER=$(grep -l -E '^[[:space:]]*listener[[:space:]]+1883([[:space:]]|$)' \
        /etc/mosquitto/mosquitto.conf /etc/mosquitto/conf.d/*.conf 2>/dev/null | grep -v -x "$MQTT_CONF" | head -1)
    BEFORE_MQTT=$(cat "$MQTT_CONF" 2>/dev/null)
    if [ -n "$OTHER_LISTENER" ]; then
        rm -f "$MQTT_CONF"
    else
        printf '%s\n' "$NEW_MQTT" > "$MQTT_CONF"
    fi
    if [ "$(cat "$MQTT_CONF" 2>/dev/null)" != "$BEFORE_MQTT" ] || ! systemctl is-active --quiet mosquitto; then
        systemctl reset-failed mosquitto >/dev/null 2>&1
        systemctl restart mosquitto >/dev/null 2>&1
    fi
    if ! systemctl is-active --quiet mosquitto && [ -f "$MQTT_CONF" ]; then
        # Le serveur MQTT ne demarre pas avec notre ecoute : sans elle (LED d'abord)
        rm -f "$MQTT_CONF"
        systemctl reset-failed mosquitto >/dev/null 2>&1
        systemctl restart mosquitto >/dev/null 2>&1
        warn "mosquitto ne demarrait pas avec $MQTT_CONF : retire"
    elif [ -n "$OTHER_LISTENER" ]; then
        ok "Serveur MQTT ouvert au reseau local (par $OTHER_LISTENER)"
    else
        ok 'Serveur MQTT ouvert au reseau local (Raspy2DMD sur une autre machine)'
    fi
else
    warn 'mosquitto absent : MQTT non ouvert au reseau local'
fi

# ------------------------------------------------------------
# Ecran de demarrage : logo qui pulse, pourcentage et ce qui se passe (pix.script)
# ------------------------------------------------------------
# Les messages du systeme sont masques et remplaces par un pourcentage d'avancement et une
# phrase qui change en chemin ; « redemarrage » quand la borne redemarre sous l'image
patch_plymouth_script() {
    sed -i '/^# --- RaspyDarts (debut) ---$/,/^# --- RaspyDarts (fin) ---$/d' "$1"
    cat >> "$1" <<'EOF'
# --- RaspyDarts (debut) ---
fun raspydarts_no_status (text) {
}

Plymouth.SetUpdateStatusFunction (raspydarts_no_status);

progress_sprite = Sprite ();
stage_sprite = Sprite ();
global.progress_last = -1;
global.stage_last = "";
global.stage_fixed = 0;

# Ce qui se passe, selon l'avancement : la phrase du palier atteint
STAGE_PERCENT[0] = 0;  STAGE_TEXT[0] = "Réveil du Raspberry…";
STAGE_PERCENT[1] = 15; STAGE_TEXT[1] = "Affûtage des pointes…";
STAGE_PERCENT[2] = 30; STAGE_TEXT[2] = "Alignement des segments de la cible…";
STAGE_PERCENT[3] = 45; STAGE_TEXT[3] = "Échauffement du bras…";
STAGE_PERCENT[4] = 60; STAGE_TEXT[4] = "Recherche des triples 20…";
STAGE_PERCENT[5] = 75; STAGE_TEXT[5] = "Craie et ardoise en place…";
STAGE_PERCENT[6] = 90; STAGE_TEXT[6] = "Dernier coup d'œil à l'oche…";
STAGE_PERCENT[7] = 100; STAGE_TEXT[7] = "Game on !";
STAGE_COUNT = 8;
REBOOT_TEXT = "Petit tour au vestiaire : redémarrage en cours…";

fun show_stage (text) {
	if (text != global.stage_last) {
		global.stage_last = text;
		stage_image = Image.Text (text, 1, 1, 1, 0.85, "Sans 20");
		stage_sprite.SetImage (stage_image);
		stage_sprite.SetPosition ((Window.GetWidth () - stage_image.GetWidth ()) / 2, Window.GetHeight () * 0.93, 10000);
	}
}

fun progress_callback (duration, progress) {
	# duration : les secondes ecoulees depuis le debut du demarrage, l'horloge de la pulsation
	global.boot_seconds = duration;
	pulse ();
	percent = Math.Int (progress * 100);
	if (percent > 100)
		percent = 100;
	# Pendant un redemarrage, ni pourcentage ni palier : la phrase du redemarrage seule
	if (percent != global.progress_last && !global.stage_fixed) {
		global.progress_last = percent;
		progress_image = Image.Text (percent + " %", 1, 1, 1, 1, "Sans Bold 28");
		progress_sprite.SetImage (progress_image);
		progress_sprite.SetPosition ((Window.GetWidth () - progress_image.GetWidth ()) / 2, Window.GetHeight () * 0.88, 10000);
		stage = 0;
		for (i = 0; i < STAGE_COUNT; i++)
			if (percent >= STAGE_PERCENT[i])
				stage = i;
		show_stage (STAGE_TEXT[stage]);
	}
}

Plymouth.SetBootProgressFunction (progress_callback);

# Redemarrage : annonce par « plymouth display-message » (raspydarts-reboot-message.service)
# quand l'image de demarrage est encore affichee, ou image relancee pour le redemarrage
fun message_callback (text) {
	global.stage_fixed = 1;
	progress_sprite.SetOpacity (0);
	show_stage (text);
}

Plymouth.SetMessageFunction (message_callback);

if (Plymouth.GetMode () == "reboot") {
	global.stage_fixed = 1;
	show_stage (REBOOT_TEXT);
}

# Logo de RaspyDarts eclaire par derriere : sa lumiere (raspydarts_halo.png) pulse. Images
# faites pour un ecran de 1920 pixels de large (scripts/boot_logo.py), a l'echelle de l'ecran
if (Plymouth.GetMode () != "shutdown") {
	logo_scale = Window.GetWidth () / 1920;
	logo_image = Image ("raspydarts_logo.png");
	logo_image = logo_image.Scale (logo_image.GetWidth () * logo_scale, logo_image.GetHeight () * logo_scale);
	halo_image = Image ("raspydarts_halo.png");
	halo_image = halo_image.Scale (halo_image.GetWidth () * logo_scale, halo_image.GetHeight () * logo_scale);
	logo_x = (Window.GetWidth () - logo_image.GetWidth ()) / 2;
	logo_y = Window.GetHeight () * 0.43 - logo_image.GetHeight () / 2;
	halo_sprite = Sprite (halo_image);
	halo_sprite.SetPosition (logo_x - (halo_image.GetWidth () - logo_image.GetWidth ()) / 2,
	                         logo_y - (halo_image.GetHeight () - logo_image.GetHeight ()) / 2, -50);
	logo_sprite = Sprite (logo_image);
	logo_sprite.SetPosition (logo_x, logo_y, -40);
}

# Une pulsation en 2,5 s, calculee sur le temps ecoule et non sur le nombre d'images : le
# Raspberry Pi dessine sans carte graphique pendant que tout demarre, il en saute (compter
# les images faisait monter la lumiere au fil du chargement). 12 niveaux de lumiere : elle
# n'est redessinee que quand son niveau change (une dizaine de fois par seconde)
PULSE_PERIOD = 2.5;
PULSE_LEVELS = 12;
REFRESH_RATE = 15;
global.boot_seconds = 0;
global.pulse_level = -1;

fun pulse () {
	if (halo_sprite) {
		phase = 0.5 - 0.5 * Math.Cos (global.boot_seconds * 2 * Math.Pi / PULSE_PERIOD);
		level = Math.Int (phase * PULSE_LEVELS + 0.5);
		if (level != global.pulse_level) {
			global.pulse_level = level;
			halo_sprite.SetOpacity (0.25 + 0.75 * level / PULSE_LEVELS);
		}
	}
}

# Entre deux avancements du demarrage (qui redonnent l'heure exacte), le temps avance d'un
# appel a l'autre
fun pulse_callback () {
	global.boot_seconds = global.boot_seconds + 1 / REFRESH_RATE;
	pulse ();
}

Plymouth.SetRefreshRate (REFRESH_RATE);
Plymouth.SetRefreshFunction (pulse_callback);
# --- RaspyDarts (fin) ---
EOF
}

THEME=/usr/share/plymouth/themes/pix
PLYMOUTH_CONF=/etc/plymouth/plymouthd.conf
if [ -f "$THEME/pix.script" ] && [ -f "$PYDARTS/images/boot_background.png" ]; then
    BEFORE=$(cat "$THEME/splash.png" "$THEME/pix.script" "$THEME"/raspydarts_*.png "$PLYMOUTH_CONF" 2>/dev/null | md5sum)
    [ -f "$THEME/splash.png.origine" ] || cp "$THEME/splash.png" "$THEME/splash.png.origine" 2>/dev/null
    install -m 644 "$PYDARTS/images/boot_background.png" "$THEME/splash.png"
    for IMAGE in logo halo; do
        [ -f "$PYDARTS/images/boot_$IMAGE.png" ] && install -m 644 "$PYDARTS/images/boot_$IMAGE.png" "$THEME/raspydarts_$IMAGE.png"
    done
    [ -f "$THEME/pix.script.origine" ] || cp "$THEME/pix.script" "$THEME/pix.script.origine"
    patch_plymouth_script "$THEME/pix.script"
    # Delai d'attente des ecrans laisse a sa valeur au demarrage : raccourci dans plymouthd.conf,
    # l'image n'apparaissait plus (ecran gris, 05/11). Retire s'il a ete mis par une version
    # precedente de ce script
    [ -f "$PLYMOUTH_CONF" ] && sed -i '/^DeviceTimeout=0.5$/d' "$PLYMOUTH_CONF"
    # L'image de demarrage est embarquee dans l'initramfs : refait seulement si elle a change
    # (environ une minute sur un Pi 3)
    if [ "$(cat "$THEME/splash.png" "$THEME/pix.script" "$THEME"/raspydarts_*.png "$PLYMOUTH_CONF" 2>/dev/null | md5sum)" != "$BEFORE" ] \
        && command -v update-initramfs >/dev/null; then
        update-initramfs -u >/dev/null 2>&1 || warn "Reconstruction de l'initramfs echouee : image de demarrage precedente gardee"
    fi
    ok "Ecran de demarrage RaspyDarts : pourcentage d'avancement et ce qui se passe"
else
    warn 'Ecran de demarrage non personnalise (theme plymouth pix ou image absente)'
fi

# Redemarrage annonce sur l'image de demarrage. Quand la borne redemarre, l'arret ne dure que
# 3 s et plymouth-reboot.service ne demarre qu'apres l'arret du serveur graphique, une seconde
# avant la fin : son image n'avait pas le temps de venir (ecran noir, mesure le 05/11). Ce
# service, arrete parmi les premiers, relance plymouth en mode redemarrage s'il a quitte (il
# quitte a la fin du demarrage en laissant son image), annonce le redemarrage et attend 7 s :
# l'image met environ 4,5 s a venir sur un Pi 3 (mesure le 05/11), puis reste lisible
cat > /usr/local/sbin/raspydarts-reboot-message <<'EOF'
#!/bin/sh
# RaspyDarts (scripts/reglages_systeme.sh) : « redemarrage en cours » sur l'image de demarrage
systemctl list-jobs 2>/dev/null | grep -q 'reboot\.target' || exit 0
if ! plymouth --ping; then
    if [ ! -e /dev/dri/card0 ]; then
        # Affichage gere par le firmware (pas de carte DRM) : plymouth attend sinon 8 s une
        # carte DRM avant de prendre /dev/fb0. Valeurs par defaut de /run (effacees a chaque
        # demarrage), lues avant celles de /usr/share
        mkdir -p /run/plymouth
        printf '[Daemon]\nTheme=pix\nDeviceTimeout=0.5\n' > /run/plymouth/plymouthd.defaults
    fi
    plymouthd --mode=reboot --attach-to-session && plymouth show-splash
fi
plymouth display-message --text="Petit tour au vestiaire : redémarrage en cours…"
sleep 7
exit 0
EOF
chmod 755 /usr/local/sbin/raspydarts-reboot-message
cat > /etc/systemd/system/raspydarts-reboot-message.service <<'EOF'
[Unit]
Description=RaspyDarts : redemarrage annonce sur l'image de demarrage
# Dependances par defaut : demarre tard, donc arrete parmi les premiers a l'extinction
After=plymouth-start.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/true
ExecStop=/usr/local/sbin/raspydarts-reboot-message
TimeoutStopSec=20
# plymouth relance par le script reste jusqu'au redemarrage : systemd ne l'attend pas
KillMode=process

[Install]
WantedBy=multi-user.target
EOF
# Version precedente : plymouth-reboot.service raccourci (remplace par le service ci-dessus)
rm -f /etc/systemd/system/plymouth-reboot.service.d/raspydarts.conf
rmdir /etc/systemd/system/plymouth-reboot.service.d 2>/dev/null
systemctl daemon-reload
systemctl enable raspydarts-reboot-message.service >/dev/null 2>&1 \
    && ok "Redemarrage annonce sur l'image de demarrage" || warn 'Annonce du redemarrage non activee'

# ------------------------------------------------------------
# Bureau : barre en bas, menu reduit, fichiers caches visibles
# ------------------------------------------------------------
# Raccourci RaspyDarts du menu (et du bureau)
if [ -f "$PYDARTS/desktop/Raspydarts.desktop" ]; then
    mkdir -p /usr/local/share/applications
    { sed "s#/raspydarts/#$PYDARTS/#g; s/^Name=.*/Name=RaspyDarts/" "$PYDARTS/desktop/Raspydarts.desktop"
      grep -q '^Categories=' "$PYDARTS/desktop/Raspydarts.desktop" || echo 'Categories=Game;'; } \
        > /usr/local/share/applications/raspydarts.desktop
    chmod 644 /usr/local/share/applications/raspydarts.desktop
fi

# Menu : RaspyDarts, Chromium, Thonny, les parametres du systeme et « Deconnexion » (qui eteint
# ou redemarre). Le menu de la session (prefixe rpd-) est remplace pour cet utilisateur
# seulement
MENU="$TARGET_HOME/.config/menus/rpd-applications.menu"
mkdir -p "$(dirname "$MENU")"
cat > "$MENU" <<'EOF'
<?xml version="1.0"?>
<!-- RaspyDarts (scripts/reglages_systeme.sh) : menu reduit a ce qui sert sur une borne -->
<Menu>
	<Name>Applications</Name>
	<Directory>rpd-applications.directory</Directory>
	<DefaultAppDirs/>
	<DefaultDirectoryDirs/>
	<Include>
		<Filename>raspydarts.desktop</Filename>
		<Filename>chromium.desktop</Filename>
		<Filename>org.thonny.Thonny.desktop</Filename>
		<Filename>rpcc.desktop</Filename>
		<Filename>pishutdown.desktop</Filename>
	</Include>
	<Layout>
		<Filename>raspydarts.desktop</Filename>
		<Separator/>
		<Filename>chromium.desktop</Filename>
		<Filename>org.thonny.Thonny.desktop</Filename>
		<Separator/>
		<Filename>rpcc.desktop</Filename>
		<Separator/>
		<Filename>pishutdown.desktop</Filename>
	</Layout>
</Menu>
EOF

# Le menu en cache est refait a la prochaine ouverture de session
rm -rf "$TARGET_HOME/.cache/menus"

# Barre des taches en bas de l'ecran
PANEL_CONF="$TARGET_HOME/.config/lxpanel-pi/panels/panel"
if [ ! -f "$PANEL_CONF" ] && [ -f /etc/xdg/lxpanel-pi/panels/panel ]; then
    mkdir -p "$(dirname "$PANEL_CONF")"
    cp /etc/xdg/lxpanel-pi/panels/panel "$PANEL_CONF"
fi
if [ -f "$PANEL_CONF" ]; then
    if grep -q '^ *edge=' "$PANEL_CONF"; then
        sed -i 's/^\( *\)edge=.*/\1edge=bottom/' "$PANEL_CONF"
    else
        sed -i '0,/^Global {/s//Global {\n  edge=bottom/' "$PANEL_CONF"
    fi
    # Lanceurs de la barre (navigateur, fichiers, terminal) designes par leur fichier : le
    # panneau les cherche sinon dans le menu, qui ne les contient plus
    for LAUNCHER in x-www-browser.desktop pcmanfm.desktop x-terminal-emulator.desktop; do
        for DIR in /usr/share/raspi-ui-overrides/applications /usr/share/applications; do
            if [ -f "$DIR/$LAUNCHER" ]; then
                sed -i "s#^\( *\)id=\(.*/\)\?$LAUNCHER\$#\1id=$DIR/$LAUNCHER#" "$PANEL_CONF"
                break
            fi
        done
    done
fi

# Fichiers caches visibles dans le gestionnaire de fichiers (la configuration du jeu est
# dans ~/.raspydarts)
PCMANFM_CONF="$TARGET_HOME/.config/pcmanfm/default/pcmanfm.conf"
mkdir -p "$(dirname "$PCMANFM_CONF")"
[ -f "$PCMANFM_CONF" ] || cp /etc/xdg/pcmanfm/default/pcmanfm.conf "$PCMANFM_CONF" 2>/dev/null || printf '[ui]\n' > "$PCMANFM_CONF"
grep -q '^\[ui\]' "$PCMANFM_CONF" || printf '\n[ui]\n' >> "$PCMANFM_CONF"
if grep -q '^show_hidden=' "$PCMANFM_CONF"; then
    sed -i 's/^show_hidden=.*/show_hidden=1/' "$PCMANFM_CONF"
else
    sed -i '0,/^\[ui\]/s//[ui]\nshow_hidden=1/' "$PCMANFM_CONF"
fi
chown -R "$TARGET_USER:$TARGET_USER" "$TARGET_HOME/.config"
ok 'Bureau : barre en bas, menu RaspyDarts / Chromium / Thonny / Parametres, fichiers caches visibles'

# Version reglee : le jeu ne relance ce script qu'a la version suivante
mkdir -p "$(dirname "$STATE")"
head -n 1 "$PYDARTS/VERSION" 2>/dev/null > "$STATE"
