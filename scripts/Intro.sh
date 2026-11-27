#!/bin/sh


RASPYDARTS_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [ "$(id -u)" -eq 0 ]; then
	# Launched by root (rc.local) : configuration is in the home of the owner of the game
	USER_HOME="$(getent passwd "$(stat -c %U "$RASPYDARTS_DIR")" | cut -d: -f6)"
else
	USER_HOME="$HOME"
fi

# ~/.raspydarts and raspydarts.cfg, or ~/.pydarts and pydarts.cfg before the renaming
PYDARTS_HOME="${USER_HOME:-/home/pi}/.raspydarts"
if [ ! -d "$PYDARTS_HOME" -a -d "${USER_HOME:-/home/pi}/.pydarts" ]; then
	PYDARTS_HOME="${USER_HOME:-/home/pi}/.pydarts"
fi
PYDARTS_CFG=raspydarts.cfg
if [ ! -s "$PYDARTS_HOME/$PYDARTS_CFG" ]; then
	PYDARTS_CFG=pydarts.cfg
fi
PYDARTS_VIDEOS="$RASPYDARTS_DIR/videos"
# The name of a theme can have spaces (Porsche V2.0 By ...) : every path is quoted
PYDARTS_THEME="`grep '^colorset:' "$PYDARTS_HOME/$PYDARTS_CFG" 2> /dev/null | head -n 1 | cut -d':' -f 2- | tr -d '\r'`"
PYDARTS_THEME_VIDEOS="$PYDARTS_HOME/themes/$PYDARTS_THEME/videos"

# A video of a folder : intro.mp4 / intro.mkv there, else one of its folder intro (at random)
find_intro() {
	if [ -d "$1" ] && [ `find "$1" -maxdepth 1 -type f \( -name "intro.mp4" -o -name "intro.mkv" \) | wc -l` -ge 1 ]; then
		echo "Find in $1" >&2
		find "$1" -maxdepth 1 -type f \( -name "intro.mp4" -o -name "intro.mkv" \) | shuf -n 1
	elif [ -d "$1/intro" ] && [ `find "$1/intro" -maxdepth 1 -type f \( -name "*.mp4" -o -name "*.mkv" \) | wc -l` -ge 1 ]; then
		echo "Find in $1/intro" >&2
		find "$1/intro" -maxdepth 1 -type f \( -name "*.mp4" -o -name "*.mkv" \) | shuf -n 1
	fi
}

# No intro video for this theme (Modifier les écrans > Vidéo d'introduction > Aucune)
if [ -s "$PYDARTS_HOME/$PYDARTS_CFG" ] && [ -f "$PYDARTS_THEME_VIDEOS/intro.none" ]; then
	exit 0
fi

video=""
if [ -s "$PYDARTS_HOME/$PYDARTS_CFG" ]; then
	# A video chosen (Modifier les écrans > Vidéo d'introduction > Choisir une vidéo)
	if [ -f "$PYDARTS_THEME_VIDEOS/intro-perso.mp4" ]; then
		video="$PYDARTS_THEME_VIDEOS/intro-perso.mp4"
	elif [ -f "$PYDARTS_THEME_VIDEOS/intro-perso.mkv" ]; then
		video="$PYDARTS_THEME_VIDEOS/intro-perso.mkv"
	else
		video="`find_intro "$PYDARTS_THEME_VIDEOS"`"
	fi
fi

# Else the one of the user, else the one of the game
if [ "$video" = "" ]; then
	video="`find_intro "$PYDARTS_HOME/videos"`"
fi
if [ "$video" = "" ]; then
	video="`find_intro "$PYDARTS_VIDEOS"`"
fi
if [ "$video" = "" ]; then
	exit 0
fi

# Output of the sound, as the game (include/caudio.py) : PipeWire is not started yet, the card
# is used directly. auto (and usb) : a USB sound card when one is plugged, else HDMI
sound_output() {
	output="`grep '^sound_output:' "$PYDARTS_HOME/$PYDARTS_CFG" 2> /dev/null | cut -d':' -f 2 | tr -d ' \r'`"
	# A USB card with a playback (a webcam is a USB card too, with a microphone only)
	usb=""
	for card in /proc/asound/card[0-9]*; do
		if [ -f "$card/usbid" ] && ls -d "$card"/pcm*p > /dev/null 2>&1; then
			usb="`cat "$card/id"`"
			break
		fi
	done
	case "$output" in
		jack) echo local ;;
		hdmi) echo hdmi ;;
		*) if [ -n "$usb" ]; then echo "alsa:plughw:CARD=$usb"; else echo hdmi; fi ;;
	esac
}

# The volume of the videos of the game (include/cvideos.py set_volume) : the setting of the volume
# and the multiplier of the videos ; played at the level of its file, the intro was about 9 dB
# louder than the videos and the sounds of the game (measured : -8.8 LUFS, the others -12 to -18)
setting() {
	grep "^$1:" "$PYDARTS_HOME/$PYDARTS_CFG" 2> /dev/null | head -n 1 | cut -d':' -f 2 | tr -d ' \r'
}
volume="`setting soundvolume`"
multiplier="`setting videosound_multiplier`"
millibels="`awk -v v="${volume:-100}" -v m="${multiplier:-1}" 'BEGIN { x = int(v / 3 * m); if (x < 1) x = 1; printf "%d", -int(4000 - log(x) / log(10) * 2000) }' 2> /dev/null`"
millibels="${millibels:-0}"
gain="`awk -v mb="$millibels" 'BEGIN { printf "%.3f", 10 ^ (mb / 2000) }' 2> /dev/null`"

# omxplayer only exists on Raspbian Buster
if command -v omxplayer > /dev/null 2>&1; then
	omxplayer --vol "$millibels" -o "`sound_output`" "$video"
elif command -v cvlc > /dev/null 2>&1; then
	# The game starts at the same time : it loads behind the video and goes up to its menu
	# in a hidden window, shown as soon as this script is finished (see intro_is_playing
	# in include/cscreen.py)
	cvlc --play-and-exit --fullscreen --video-on-top --no-video-title-show --no-osd --gain "${gain:-1}" "$video" > /dev/null 2>&1 &
	vlc=$!
	if command -v xdotool > /dev/null 2>&1; then
		# VLC needs some time to close after the end of the video, its window is already
		# gone : the script ends with the window, the menu of the game appears at once.
		# Its existence is watched, not its visibility : it is hidden for a moment when
		# going full screen
		i=0
		while [ $i -lt 100 ] && kill -0 $vlc 2> /dev/null && ! xdotool search --class vlc > /dev/null 2>&1
		do
			sleep 0.1
			i=$((i + 1))
		done
		missing=0
		while kill -0 $vlc 2> /dev/null && [ $missing -lt 2 ]
		do
			if xdotool search --class vlc > /dev/null 2>&1
			then
				missing=0
			else
				missing=$((missing + 1))
			fi
			sleep 0.1
		done
	else
		wait $vlc
	fi
fi
