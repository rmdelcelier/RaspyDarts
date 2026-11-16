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
PYDARTS_THEME="`grep 'colorset:' $PYDARTS_HOME/$PYDARTS_CFG 2> /dev/null | cut -d':' -f 2`"
PYDARTS_THEME_VIDEOS=$PYDARTS_HOME/themes/$PYDARTS_THEME/videos

# No intro video for this theme (Modifier les écrans > Vidéo d'introduction > Aucune)
if [ -s $PYDARTS_HOME/$PYDARTS_CFG -a -f $PYDARTS_THEME_VIDEOS/intro.none ]; then
	exit 0
fi

if [ -s $PYDARTS_HOME/$PYDARTS_CFG ]; then
	if [ -d $PYDARTS_THEME_VIDEOS -a `find $PYDARTS_THEME_VIDEOS -maxdepth 1 -type f -name "intro.mp4" -o -name "intro.mkv" | wc -l` -ge 1 ]; then
		echo "Find in $PYDARTS_THEME_VIDEOS"
		video=`find $PYDARTS_THEME_VIDEOS -maxdepth 1 -type f -name "intro.mp4" -o -name "intro.mkv" | shuf -n 1`
	elif [ -d $PYDARTS_THEME_VIDEOS/intro -a `find $PYDARTS_THEME_VIDEOS/intro -maxdepth 1 -type f -name "*.mp4" -o -name "*.mkv" | wc -l` -ge 1 ]; then
		echo "Find in $PYDARTS_THEME_VIDEOS/intro"
		video=`find $PYDARTS_THEME_VIDEOS/intro -maxdepth 1 -type f -name "*.mkv" -o -name "*.mp4" | shuf -n 1`
	fi
fi

if [ "$video" = "" ]; then
	if [ -d $PYDARTS_HOME/videos -a `find $PYDARTS_HOME/videos -maxdepth 1 -type f -name "intro.mp4" -o -name "intro.mkv" | wc -l` -ge 1 ]; then
		echo "Find in $PYDARTS_HOME/videos"
		video=`find $PYDARTS_HOME/videos -maxdepth 1 -type f -name "intro.mp4" -o -name "intro.mkv" | shuf -n 1`
	elif [ -d $PYDARTS_HOME/videos/intro -a `find $PYDARTS_HOME/videos/intro -maxdepth 1 -type f -name "*.mp4" -o -name "*.mkv" | wc -l` -ge 1 ] ;then
		echo "Find in $PYDARTS_HOME/videos/intro"
		video=`find $PYDARTS_HOME/videos/intro -maxdepth 1 -type f -name "*.mp4" -o -name "*.mkv" | shuf -n 1`
	elif [ -d $PYDARTS_VIDEOS -a `find $PYDARTS_VIDEOS -maxdepth 1 -type f -name "intro.mp4" -o -name "intro.mkv" | wc -l` -ge 1 ]; then
		echo "Find in $PYDARTS_VIDEOS"
		video=`find $PYDARTS_VIDEOS -maxdepth 1 -type f -name "intro.mp4" -o -name "intro.mkv" | shuf -n 1`
	elif [ -d $PYDARTS_VIDEOS/intro -a `find $PYDARTS_VIDEOS/intro -maxdepth 1 -type f -name "*.mp4" -o -name "*.mkv" | wc -l`-ge 1 ]; then
		echo "Find in $PYDARTS_VIDEOS/intro"
		video=`find $PYDARTS_VIDEOS/intro -maxdepth 1 -type f -name "*.mp4" -o -name "*.mkv" | shuf -n 1`
	else
		exit 0
	fi
fi

# Output of the sound, as the game (include/caudio.py) : PipeWire is not started yet, the card
# is used directly. auto (and usb) : a USB sound card when one is plugged, else HDMI
sound_output() {
	output="`grep '^sound_output:' $PYDARTS_HOME/$PYDARTS_CFG 2> /dev/null | cut -d':' -f 2 | tr -d ' \r'`"
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

# omxplayer only exists on Raspbian Buster
if command -v omxplayer > /dev/null 2>&1; then
	omxplayer -o "`sound_output`" "$video"
elif command -v cvlc > /dev/null 2>&1; then
	# The game starts at the same time : it loads behind the video and goes up to its menu
	# in a hidden window, shown as soon as this script is finished (see intro_is_playing
	# in include/cscreen.py)
	cvlc --play-and-exit --fullscreen --video-on-top --no-video-title-show --no-osd "$video" > /dev/null 2>&1 &
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
