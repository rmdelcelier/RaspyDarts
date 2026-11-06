#!/bin/sh

# The game works from the folder where it is installed
cd "$(dirname "$(readlink -f "$0")")"
touch restart

cat to_delete.lst \
| while read f
do
	if [ -s "$f" ]
	then
		sudo rm -rf "$f"
	fi
done

# Leds, DMD and Hue are driven through the local MQTT broker : at boot, the session
# can open before it is started. Wait for it, 30 seconds at most.
# Already running : systemctl is slow while the Pi starts up (more than 2 seconds)
if ! pgrep -x mosquitto > /dev/null 2>&1 && systemctl is-enabled --quiet mosquitto 2> /dev/null
then
	i=0
	while [ $i -lt 30 ] && ! systemctl is-active --quiet mosquitto
	do
		sleep 1
		i=$((i + 1))
	done
fi

# Stopped by an error : started again (its report is shown, include/cerrors.py), but not for
# ever : the 3rd error in a row less than 2 minutes after its start stops it (back to the desktop)
QUICK_CRASHES=0
while [ -f restart ]
do
	rm -f restart

	if [ -s logs/raspydarts.log ]
	then
		cp logs/raspydarts.log logs/raspydarts.log.bck
	fi
	sudo kill -9 `ps -lef | grep 'Server.py' | sed -e 's/  */ /g' | cut -f4 -d' '` 2> /dev/null

	started=$(date +%s)
	python3 raspydarts.py > logs/raspydarts.log 2>&1
	status=$?
	# Stopped by an error : the end of its log here too (everything else goes to the log only)
	if [ $status -ne 0 ]
	then
		echo "RaspyDarts s'est arrete sur une erreur (code $status). Fin de logs/raspydarts.log :"
		tail -n 25 logs/raspydarts.log
		cp logs/raspydarts.log logs/raspydarts.log.plantage
		if [ $(($(date +%s) - started)) -lt 120 ]
		then
			QUICK_CRASHES=$((QUICK_CRASHES + 1))
		else
			QUICK_CRASHES=1
		fi
		# 1 : the error of the game (os._exit(1)) ; killed (code 128 + signal) : not started again
		if [ $status -eq 1 ] && [ $QUICK_CRASHES -lt 3 ]
		then
			echo "RaspyDarts redemarre apres l'erreur ($QUICK_CRASHES)"
			sleep 2
			touch restart
		elif [ $status -eq 1 ]
		then
			echo "Trop d'erreurs a la suite : RaspyDarts n'est pas relance (voir logs/raspydarts.log.plantage)"
		fi
	fi
done

