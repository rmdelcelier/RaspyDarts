
"""
Manage events
Send data on approriate topic, wait for ack, ...
"""

import random
# String to dict
import ast
# Regexp
import re
# time
import time

import paho.mqtt.client as mqtt


def new_mqtt_client(client_id=''):
    '''
    A client of paho-mqtt 2 (its callback API 2, as Raspy2DMD) : the bornes installed with
    paho-mqtt 1.x get it from scripts/update_lib.sh, run before this client is made
    '''
    return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
#from threading import Thread

class Event:
    """
    Main events class
    """
    def __init__(self, logs, preferences, broker=None, port=None, topic=None, subscribers=None):
        if broker is None:
            broker = 'localhost'
        if port is None:
            port = 1883
        if topic is None:
            topic = 'raspydarts'

        client_id = f'pydarts-mqtt-{random.randint(0,1000)}'
        self.broker = broker
        self.port = port
        self.target_topic = f'{topic}/targetLeds'
        self.strip_topic = f'{topic}/stripLeds'
        self.dmd_topic = f'{topic}/dmd'
        self.matrix_topic = f'{topic}/matrix'
        self.other_topic = f'{topic}/other'
        self.continue_list = []
        # Out of games with the light out of games : no animation of the events on the strip and
        # the target (only off and quit)
        self.quiet = False

        self.target_leds = False
        self.strip_leds = False
        self.dmd = False
        self.matrix = False
        self.other = False

        for subscriber in subscribers:
            if subscriber == 'Target':
                self.target_leds = True
            elif subscriber == 'Strip':
                self.strip_leds = True
            elif subscriber == 'Dmd':
                self.dmd = True
            elif subscriber == 'Matrix':
                self.matrix = True
            elif subscriber == 'Other':
                self.other = True

        self.dispatcher = preferences
        self.logs = logs
        self.rpi = None

        self.logs.debug(f"self.dispatcher={self.dispatcher}")
        self.logs.debug(f"broker={broker}")
        self.loop_running = False
        try:
            self.mqtt_client = new_mqtt_client(client_id)
            self.mqtt_client.connect(broker, port)
            # Network loop in the background : the keepalive pings are sent (without them the
            # broker closed the connection after a minute without message, and the first
            # message sent then was lost : the light of the target, a menu animation...), and
            # the connection is made again by itself
            self.mqtt_client.loop_start()
            self.loop_running = True
        except Exception as error: # pylint: disable=broad-except
            # Said : without it, nothing was published and nothing told why
            self.logs.error(f"Mqtt : no connection to {broker}:{port} ({type(error).__name__} : {error})")
            self.mqtt_client = None

    def add_rpi(self, rpi):
        self.rpi = rpi

    def base(self, target=None, strip=None):
        """
        Light of the background of the target and of the strip (an animation : 'Light,1,white,0',
        'Background', 'off') : the LED servers come back to it after each animation ; None : no
        more
        """
        if self.mqtt_client is None:
            return
        for available, topic, animation in ((self.target_leds, self.target_topic, target), (self.strip_leds, self.strip_topic, strip)):
            if available:
                self.mqtt_publish(topic, f"base:{animation or ''}")

    def get_events(self):
        """
        returns list of available events
        """
        return ['launch', 'menu', 'newgame', 'wait', 'SB', 'DB', '180', 'pressure', \
                'release', 'nextplayer', 'touch', 'miss', 'setwinner', 'winner', \
                'gameover', 'interrupt', 'quit']

    def get_strip(self):
        """
        return list of animations available for strip leds
        """
        liste = []
        with open("addons/CStrip.py", "r", encoding="utf-8") as file:
            for line in file:
                if re.search("def SA_", line):
                    liste.append(line.split("_")[1].split("(")[0])
        return liste

    def get_target(self):
        """
        return list of animations available for target leds
        """
        liste = []
        with open("addons/CStrip.py", "r", encoding="utf-8") as file:
            for line in file:
                if re.search("def TA_", line):
                    liste.append(line.split("_")[1].split("(")[0])
        liste.sort()
        return liste

    def get_colors(self):
        """
        return a list of colors
        """
        liste = []
        liste.append('random')
        with open("addons/Colors.py", "r", encoding="utf-8") as file:
            for line in file:
                if re.search("'[a-z][a-z]*[^1-9]'", line):
                    liste.append(line.split("'")[1])

        return liste

    def __message_is_ack(self, client, userdata, msg):
        """
        Function to execute on ack
        """
        if msg.payload.decode() == 'ack':
            i = 0
            for i in range(0, len(self.continue_list)):
                if self.continue_list[i] == msg.topic:
                    del self.continue_list[i]
                    break
            self.logs.debug(f"Wait for ack on {self.continue_list}")

    def wait_acks(self, topics, timeout):
        """
        Wait for ack from various servers (best effort).
        'timeout' is a real (wall-clock) duration in seconds : la sortie est
        garantie de se faire au plus tard apres 'timeout' secondes, meme si un
        serveur ne repond jamais (sinon l'ecran "Shutting down servers" reste
        bloque). Les acks ne sont qu'une courtoisie : le message 'quit' a deja
        ete envoye aux serveurs avant cette attente.
        """
        topic_list = []
        for topic in topics:
            if topic is not None:
                topic_list.append((topic + '-ack', 0))
                self.continue_list.append(topic + '-ack')
        if len(topic_list) == 0:
            return

        try:
            self.mqtt_client.on_message = self.__message_is_ack
            self.mqtt_client.subscribe(topic_list)
            self.logs.debug(f"Wait for ack on {self.continue_list} (max {timeout}s)")

            deadline = time.time() + timeout
            while self.continue_list and time.time() < deadline:
                # loop() borne a 0.2s : la deadline est donc respectee a 0.2s pres (la
                # boucle de fond, quand elle tourne, livre les acks : on attend seulement)
                if self.loop_running:
                    time.sleep(0.2)
                else:
                    self.mqtt_client.loop(timeout=0.2)

            if not self.continue_list:
                self.logs.debug("Ack received")
            else:
                self.logs.debug(f"Timeout reached, missing acks : {self.continue_list}")
        except Exception as ex: # pylint: disable=broad-except
            self.logs.error(f"wait_acks error (on continue anyway) : {ex}")
        finally:
            # On ne laisse jamais d'attente residuelle pour le prochain appel.
            self.continue_list = []

    def mqtt_publish(self, topic, message):
        """
        Mqtt publish function
        Retry on error, 50 times max
        """
        if len(message) < 1:
            self.logs.warning(f"Cannot publish on 0 length message")
            return
        self.logs.debug(f"Publish on {topic} : {message}")
        try:
            ret = self.mqtt_client.publish(topic, message)
        except Exception as ex: # pylint: disable=broad-except
            self.logs.error(f"Mqtt publish error (ignored) : {ex}")
            return
        if ret[0] != 0 :
            self.logs.debug(f"publish ret={ret}")
        # Quelques reconnexions seulement : un connect() peut bloquer si le
        # broker est injoignable, on ne veut pas figer l'appli (ex: ecran
        # "Shutting down servers"). Tout est protege pour ne jamais propager.
        i = 0
        while ret[0] != 0 and i < 5 :
            time.sleep(0.01)
            try:
                self.mqtt_client.disconnect()
                rc = self.mqtt_client.connect(self.broker, self.port)
                if rc == 0 :
                    ret = self.mqtt_client.publish(topic, message)
                    self.logs.debug(f"Send {message} on {topic}")
                else :
                    self.logs.debug(f"Cannot reconnect to {self.broker}:{self.port}")
            except Exception as ex: # pylint: disable=broad-except
                self.logs.error(f"Mqtt reconnect error (ignored) : {ex}")
                return
            i += 1
        if i == 5 :
            self.logs.error("Mqtt Send error")


    def send(self, device, topic, available, event, data, ack=False):
        """
        Sent a message on a topic
        """
        self.continue_list = []
        messages = []

        if device == 'DMD':
            if event in (self.dispatcher or {}):
                # An event of the game (wait, menu...) : the DMD commands set for it (Events of
                # the configuration), none : nothing. Its name alone was sent before, which the
                # DMD does not know (Raspy2DMD : "Unknown message format" every 90 s for wait)
                for message in (self.dispatcher.get(event) or {}).get('DMD') or []:
                    if '|' in str(message):
                        self.mqtt_publish(topic, message)
                return
            # A message (msg|..., time|...) : as it is
            self.mqtt_publish(topic, event)
            return

        if event == 'wait':
            thread = True
        else:
            thread = False

        if available:
            shutdown = False

            if event == 'quit':
                shutdown = True

            if event == 'stroke':
                # Special event for segment stroke ?
                try:
                    messages = self.dispatcher[data][device][::]
                except:
                    if data[:1:] in ('s', 'S') and device == 'STRIP':
                        messages.append('simple')
                    if data[:1:] == 'D' and device == 'STRIP':
                        messages.append('double')
                    if data[:1:] == 'T' and device == 'STRIP':
                        messages.append('triple')

                if device == 'TARGET' and len(messages) == 0:
                    messages.append(f"stroke:{data}")

            if len(messages) == 0:
                try:
                    messages = self.dispatcher[event][device][::]
                except:
                    pass

            if len(messages) == 0:
                if event == 'wait' and len(messages) > 1:
                    # Keep one message
                    # I hope the animation will change at every execution
                    for x in range(0, len(messages) - 1):
                        event_to_remove = random.randint(0, len(messages) - 1)
                        messages.pop(event_to_remove)

                if messages == [''] or len(messages) == 0:
                    if event == 'DB':
                        messages = ['stroke:DB']
                    elif event == 'SB':
                        messages = ['stroke:SB']
                    elif event == 'quit' and device == 'DMD':
                        # Nothing : powering off Raspy2DMD is the choice of « Éteindre Raspy2DMD
                        # avec RaspyDarts » (cdmd.shutdown) ; shutdwn| here powered it off anyway, and
                        # the one of this machine (Pico seul) powered the borne off at once
                        messages = ['']
                        ack = False
                    elif event == 'quit':
                        messages = ['quit']

            if len(messages) == 0:
                # Not found, send as receveid
                if data:
                    messages.append(f"{event}:{data}")
                else:
                    messages.append(event)

            # ICI pour envoyer plusieurs animations en une fois
            for message in messages:
                if message != '' :
                    if thread:
                        message = f'thread:{message}'
                    elif ack:
                        message = f'ack:{message}'
                    self.mqtt_publish(topic, message)

            if shutdown:
                time.sleep(0.5)
                self.mqtt_client.publish(topic, 'quit')

            if ack:
                return topic

        return None

    def publish(self, event, data=None, ack=False, limit=None):
        """
        Used by other modules
        Send data on various topics
        """
        threads = []
        self.logs.debug(f"Received {event} / {data} / limit = {limit}")
        if self.mqtt_client is not None and event is not None:
            if event == 'leds':
                self.mqtt_publish(self.target_topic, f"leds|{data}")
                
            elif event == 'reload':  
                self.mqtt_publish(self.target_topic, f"reload|{data}")

            elif event == 'special':
                for element in data.split('-'):
                    if len(element) == 0:
                        continue
                    
                    destination = element.split(':')[0]
                    anims = element.split(':')[1].split(';')

                    for anim in anims:
                        if self.target_leds and destination == 'TARGET':
                            self.mqtt_publish(self.target_topic, f'thread:{anim}')
                        elif self.strip_leds and destination == 'STRIP':
                            self.mqtt_publish(self.strip_topic, f'thread:{anim}')
                        elif self.dmd and destination == 'DMD':
                            self.mqtt_publish(self.dmd_topic, anim)
                        elif self.matrix and destination == 'MATRIX':
                            self.mqtt_publish(self.matrix_topic, anim)
                        elif self.matrix and destination == 'OTHER':
                            self.mqtt_publish(self.other_topic, anim)
                        time.sleep(0.001)
            else:
                ack_list = []
                if self.quiet and event not in ('off', 'quit'):
                    # The light out of games stays : the other devices only
                    limit = [device for device in (limit or ['TARGET', 'STRIP', 'DMD', 'MATRIX', 'OTHER']) if device not in ('TARGET', 'STRIP')]
                if limit is None or 'TARGET' in limit:
                    # Target Leds
                    ack_list.append(self.send('TARGET', self.target_topic, self.target_leds, \
                            event, data, ack))
                if limit is None or 'STRIP' in limit:
                    # Strip Leds
                    ack_list.append(self.send('STRIP', self.strip_topic, self.strip_leds, \
                            event, data, ack))
                if limit is None or 'DMD' in limit:
                    # Dmd
                    ack_list.append(self.send('DMD', self.dmd_topic, self.dmd, \
                            event, data, ack))
                if limit is None or 'MATRIX' in limit:
                    # Matrix Leds
                    ack_list.append(self.send('MATRIX', self.matrix_topic, self.matrix, \
                            event, data, ack))
                if limit is None or 'OTHER' in limit:
                    # Other device
                    ack_list.append(self.send('OTHER', self.other_topic, self.other, \
                            event, data, ack))

                # Attente courte et bornee : on revient au bureau / on eteint
                # rapidement meme si un serveur LEDs tarde ou ne repond pas.
                self.wait_acks(ack_list, 5)

                if event == 'quit':
                    try:
                        self.mqtt_client.disconnect()
                        if self.loop_running:
                            self.mqtt_client.loop_stop()
                            self.loop_running = False
                    except Exception as ex: # pylint: disable=broad-except
                        self.logs.error(f"Mqtt disconnect error (ignored) : {ex}")
        else:
            self.logs.error("Mqtt client not initialized")

        if event == 'stroke':
            event = data
        try:
            if limit is None or 'LIGHT' in limit:
                if self.dispatcher[event] == {} and (data not in ['SB', 'DB'] and data[:1] in ['S', 'D', 'T']):
                    if data[:1] == 'S':
                        event = 'simple'
                    elif data[:1] == 'D':
                        event = 'double'
                    elif data[:1] == 'T':
                        event = 'triple'
                for light in self.dispatcher[event]['LIGHT']:
                    self.rpi.light_toys([light.split(',')[0]], delay=int(light.split(',')[1]))
        except:
            pass

        try:
            if limit is None or 'STROBE' in limit:
                if self.dispatcher[event] == {} and (data not in ['SB', 'DB'] and data[:1] in ['S', 'D', 'T']):
                    if data[:1] == 'S':
                        event = 'simple'
                    elif data[:1] == 'D':
                        event = 'double'
                    elif data[:1] == 'T':
                        event = 'triple'
                for strobe in self.dispatcher[event].get('STROBE', []):
                    opts = strobe.split(',')
                    if len(opts) == 2:
                        threads += self.rpi.strobe_toys([opts[0]], iterations=int(opts[1]))
                    if len(opts) == 3:
                        threads += self.rpi.strobe_toys([opts[0]], iterations=int(opts[1]), delay_on=int(opts[2]))
                    if len(opts) == 4:
                        threads += self.rpi.strobe_toys([opts[0]], iterations=int(opts[1]), delay_on=int(opts[2]), delay_off=int(opts[3]))
        except Exception as error:
            self.logs.error(f"Error is {error}")
            pass
        return threads


    def string_to_pref(self, prefs):
        """
        Return dict from string
        """

        return ast.literal_eval(prefs)
