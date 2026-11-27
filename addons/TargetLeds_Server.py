
import sys
import re
import ast
import time

from threading import Thread
from threading import Event
from threading import Lock
from threading import Timer

# Mqtt
import paho.mqtt.client as mqtt
# Perso
import CStrip as CStrip
import Colors as CColors

SON = None

def usage(msg):
    print("")
    print(f"TargetLeds_Server.py [-host={MQTT_HOST}] [-type='grb'] [-leds=raspyleds] [-bgcolors='blue,red,white'] [-bgbrightness=10] <DMA_CHANNEL> <TOPIC> <CONFIG> <PIN> <BRIGHTNESS>")
    print("")
    print(f" ERROR : {msg}")
    print("")
    sys.exit(9)

# The callback for when the client receives a connect response from the server.
def on_connect(client, userdata, flags, reason_code, properties):
    # on_connect() means that if we lose the connection and reconnect then subscriptions will be renewed.
    client.subscribe(MQTT_TOPIC)
    print(f"[DEBUG] TargetLeds_Server : Listen {MQTT_TOPIC} on {MQTT_HOST}", flush=True)

# Light of the background (base:<animation>, sent by the game out of games, option idle_light) :
# set at once, and set again at the end of each animation (not after one stopped by a new one)
BASE = None


def apply_base():
    if BASE:
        animation(None, BASE, True)


# In a game : the segments to hit (goal:...), those blinking (blink:...) and the background of the
# target (Background) set by the game are kept, and lit again after an animation of an event
# (Joueur suivant, a dart...) which put them out : several animations in a row for an event
# ended in the dark (or the segments of the game lit, then put out by the next animation).
# Lit again when no message came for RESTORE_DELAY after the end of the animation (a next one
# already waiting comes first) ; nogoal (end of a turn, nothing to hit) and off forget them
GOAL = None
BLINK = None
BG = False
RESTORE_DELAY = 0.25
LOCK = Lock()
MESSAGES = 0
# Messages which set the state, not an animation to light again after
STATE = ('goal', 'blink:', 'nogoal', 'Background', 'off', 'quit', 'base:', 'leds', 'reload', 'brightness')


def keep_state(msg):
    '''
    The state of the game given by a message (before it is shown)
    '''
    global GOAL, BLINK, BG
    # off as the game sends it : off,,, (its animation in the events)
    name = msg.split(',')[0]
    if msg.startswith('goal:'):
        GOAL = msg[5:] or None
    elif msg.startswith('blink:'):
        BLINK = msg
    elif msg == 'nogoal':
        GOAL = BLINK = None
    elif name == 'Background':
        BG = True
    elif name in ('off', 'quit'):
        GOAL = BLINK = None
        BG = False


def restore(expected):
    '''
    The segments of the game lit again, if no message came since the end of the animation
    '''
    global SON
    with LOCK:
        if MESSAGES != expected or not (GOAL or BLINK):
            return
        print(f"[DEBUG] TargetLeds_Server : segments of the game lit again", flush=True)
        try:
            if BG:
                CStrip.Background()
            if GOAL:
                CStrip.Segment(50, None, 3, GOAL, False)
            if BLINK:
                t_event.clear()
                SON = Thread(target=animation, args=(t_event, BLINK, True))
                SON.start()
        except Exception as error:    # pylint: disable=broad-except
            print(f"[ERROR] TargetLeds_Server : segments not lit again ({error})", flush=True)


def animation(t_event, msg, restoring=False):
    global BASE

    if msg.startswith('base:'):
        BASE = msg[5:] or None
        print(f"[DEBUG] TargetLeds_Server : base {BASE}", flush=True)
        apply_base()
        return

    C = None

    if msg[0:3:1] == 'ack':
        Ack = True
        msg = msg[4::]
    else :
        Ack = False

    if msg[0:5:1] == 'Light':
        animation = 'Light'
        iterations = 1
        color = msg.replace(' ','').split(",",2)[2].replace('(','').replace(')','')
        try:
            red = int(color.split(",")[0])
            green = int(color.split(",")[1])
            blue = int(color.split(",")[2])
            C = (red,green,blue)
        except:
            color = msg.split(',')[2]

        delay = None
    elif msg[0:4:1] == 'Wait':
        animation = 'Wait'
        try:
            wait_time = int(msg.split(",")[1]) * int(msg.split(",")[3])
        except:
            wait_time = 500
    elif msg[0:4:1] != 'leds' and msg[0:4:1] != 'goal' and msg[0:6:1] != 'reload':
        try:
            animation = msg.split(',')[0]
            iterations = int(msg.split(',')[1])
            color = msg.split(',')[2]
            delay = int(msg.split(',')[3])
            try:
                add = msg.split(',')[4]
            except:
                add = None
        except:
            iterations = 1
            delay = 10
            color = None
    else:
        animation = msg
        iterations = 1

    if C is None:
        try:
            C = Colors.GetColor(color)
        except:
            C = Colors.GetColor()
    
    print(f"[DEBUG] TargetLeds_Server : Launch {animation}", flush=True)
    try:
        if animation == 'quit' :
            print("[DEBUG] TargetLeds_Server : Disconnect. Sleep 1s", flush=True)
            BASE = None
            time.sleep(1)
            client.publish(MQTT_TOPIC + '-ack',"ack")
            client.disconnect()

        elif animation == 'Wait':
            CStrip.Wait(wait_time)

        elif animation == 'off' :
            CStrip.AllLeds(Colors.GetColor('black'))

        # Animations
        elif animation == 'Alain':
            CStrip.TA_Alain(t_event, delay, C, iterations)
        elif animation == 'Alain2':
            CStrip.TA_Alain2(t_event, delay, C, iterations)
        elif animation.startswith('blink:'):
            pattern = re.compile("^blink:.*$")
            if (pattern.match(animation)):
                CStrip.TA_Blink(t_event, 150, C, animation.split(':')[1])
        elif animation == 'Alfred':
            CStrip.TA_Alfred(t_event, delay, C, iterations)
        elif animation == 'DoubleBull':
            CStrip.TA_DoubleBull(t_event, delay, C, iterations)
        elif animation == 'FadeInOut':
            CStrip.TA_FadeInOut(t_event, delay, C, iterations)
        elif animation == 'FadeRGB':
            CStrip.TA_FadeRGB(t_event, delay, C, iterations)
        elif animation == 'Hue':
            CStrip.TA_Hue(t_event, delay, C, iterations)
        elif animation == 'Light':
            CStrip.TA_Light(C)
        elif animation == 'Lotus':
            CStrip.TA_Lotus(t_event, delay, C, iterations)
        elif animation == 'Mireille':
            CStrip.TA_Mireille(t_event, delay, C, iterations)
        elif animation == 'Pacman':
            CStrip.TA_Pacman(t_event, delay, C, iterations)
        elif animation == 'Police':
            CStrip.TA_Police(t_event, delay, C, iterations)
        elif animation == 'Rainbow':
            CStrip.TA_Rainbow(t_event, delay, C, iterations)
        elif animation == 'Rainbow2':
            CStrip.TA_Rainbow2(t_event, delay, C, iterations)
        elif animation == 'RandomColor':
            CStrip.TA_RandomColor(t_event, delay, C, iterations)
        elif animation == 'Ring':
            CStrip.TA_Ring(t_event, delay, C, iterations)
        elif animation == 'Snake':
            CStrip.TA_Snake(t_event, delay, C, iterations)
        elif animation == 'Simone' or animation == 'Daisy':
            CStrip.TA_Daisy(t_event, delay, C, iterations)  
        elif animation == 'SimpleBull':
            CStrip.TA_SimpleBull(t_event, delay, C, iterations)
        elif animation == 'Sparkle':
            CStrip.TA_Sparkle(t_event, delay, C, iterations)
        elif animation == 'Strobe':
            CStrip.TA_Strobe(t_event, delay, C, iterations)
        elif animation == 'TheaterChase':
            CStrip.TA_TheaterChase(t_event, delay, C, iterations)
        elif animation == 'Twinkle':
            CStrip.TA_Twinkle(t_event, delay, C, iterations)

        elif animation.startswith('custom'):
            CStrip.TA_Perso(animation)

        elif animation == 'stroke:DB':
            C = Colors.GetColor("gold")
            CStrip.DoubleBull(t_event, 5, C, 3)
        elif animation == 'stroke:SB':
            C = Colors.GetColor("silver")
            CStrip.SimpleBull(t_event, 5, C, 2)
        elif animation.split('|')[0] == 'leds' :
            CStrip.TestSegment(animation.split('|')[1])
        elif animation.split('|')[0] == 'reload' :
            CStrip.ReloadSegmentsColors(animation.split('|')[1:])

        elif animation == 'Debug':
            CStrip.Debug(delay,C,1)
        elif animation == 'DebugSeg':
            CStrip.DebugSeg(delay,C,1,int(add))
        elif animation == 'Background':
            CStrip.Background()
        elif animation == 'brightness':
            # Change brightness
            CStrip.SetBrightness(animation.split(':')[1])

        elif animation.startswith('stroke:'):
            # Dart stroke segment
            pattern = re.compile("^stroke:[S,D,T][0-9][0-9]?$")
            if (pattern.match(animation) or animation == 'stroke:SB' ):
                C = Colors.GetColor()
                CStrip.Segment(50,C,3,animation.split(':')[1],True)

        elif animation.startswith('goal:'):
            # Segment(s) to be stroked
            pattern = re.compile("^goal:.*$")
            if pattern.match(animation) :
                print(f"Target : animation = {animation}", flush=True)
                CStrip.Segment(50,None,3,animation.split(':')[1],False)

        elif animation.startswith('simon:'):
            # Segment(s) to be stroked
            pattern = re.compile("^simon:.*$")
            if pattern.match(animation) :
                CStrip.Simon(50,None,3,animation.split(':')[1],False)
    except:
        print(f"[ERROR] TargetLeds_Server : Animation error : {animation}", flush=True)

    if Ack :
        print(f"[DEBUG] TargetLeds_Server : publish Ack", flush=True)
        client.publish(MQTT_TOPIC,"ack")

    # Back to the light of the background (not after quit, nor when a new message stopped it)
    if BASE and not restoring and not msg.startswith('quit') and (t_event is None or not t_event.is_set()):
        apply_base()

    # The segments of the game put out by this animation : lit again (see GOAL)
    if (GOAL or BLINK) and not restoring and not msg.startswith(STATE) and (t_event is None or not t_event.is_set()):
        Timer(RESTORE_DELAY, restore, args=(MESSAGES,)).start()

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global SON, MESSAGES
    message = msg.payload.decode().replace(' ','')
    # Waits for the segments being lit again (restore), then no more of it for an older animation
    with LOCK:
        MESSAGES += 1
    if message != 'ack':
        keep_state(message.replace('thread:', '').replace('ack:', ''))

    try:
        if SON.is_alive():
            # Stop old thread
            t_event.set()
            while SON.is_alive():
                time.sleep(0.01)
            t_event.clear()
            SON.join()
    except:
        pass
    if message != 'ack' and (message.startswith('thread') or message.startswith('blink')):
        message = message.replace('thread:', '')
        SON = Thread(target=animation, args=(t_event, message))
        SON.start()
    elif message != 'ack':
        animation(None, message)


MQTT_HOST = "localhost"
MQTT_TOPIC = "pydarts/TargetLeds"
DMA = 10
LEDS_TYPE = None
BGBRIGHTNESS = None
BGCOLORS = None
STRIP_TYPE = 'grb'

if len(sys.argv) < 5 or len(sys.argv) > 10:
    usage("Bad number of arguments : {}".format(len(sys.argv)))
else :
    Colors = CColors.CColors()

    i = 1
    if sys.argv[i][0:6] == '-host=' :
        MQTT_HOST = sys.argv[i].split('=')[1]
        i += 1

    if sys.argv[i][0:6] == '-type=' :
        if sys.argv[i].split('=')[1] == 'rgb':
            STRIP_TYPE = 'rgb'
        if sys.argv[i].split('=')[1] == 'grb':
            STRIP_TYPE = 'grb'
        i += 1

    if sys.argv[i][0:6] == '-leds=' :
        if sys.argv[i].split('=')[1] == 'raspyleds':
            LEDS_TYPE = 'raspyleds'
        i += 1

    if sys.argv[i][0:10] == '-bgcolors=':
        if sys.argv[i].split('=')[1].find("_") >= 0:
            colors = sys.argv[i].split('=')[1].split('_')
        else:
            colors = sys.argv[i].split('=')[1].split(',')
        BGCOLORS = []

        for color in colors:
            try:
                BGCOLORS.append(Colors.GetColor(color))
            except:
                usage("Unknown background color {}".format(color))
        i += 1

    if sys.argv[i][0:14] == '-bgbrightness=':
        try:
            BGBRIGHTNESS = int(sys.argv[i].split('=')[1])
            if BGBRIGHTNESS < 0 or BGBRIGHTNESS > 100:
                usage("bgbrightness must be an interger between 0 and 100 : {} not allowed".format(sys.argv[i].split('=')[1]))
        except:
            usage("bgbrightness must be an interger between 0 and 100")
        i += 1

    try:
        DMA = int(sys.argv[i])
    except:
        usage("DMA {} not -- allowed (Only 9/10)".format(sys.argv[i]))

    if DMA not in [9, 10]:
        usage("DMA {} not allowed (Only 9/10)".format(DMA))

    MQTT_TOPIC = sys.argv[i+1]

    CONFIG = sys.argv[i+2]
    try:
        conf = ast.literal_eval(CONFIG)
    except:
        usage("CONFIG must be a valid dict")

    try:
        PIN = int(sys.argv[i+3])
    except:
        usage("PIN {} not allowed (Only 10/12/18/21)".format(PIN))

    try:
        BRIGHTNESS = float(sys.argv[i+4])
    except:
        usage("BRIGHTNESS must be a float between 0 and 1")
    if BRIGHTNESS > 1 and BRIGHTNESS <= 100:
        BRIGHTNESS /= 100

    if BRIGHTNESS < 0 or BRIGHTNESS > 1 :
        usage("BRIGHTNESS must be a float between 0 and 1")

    # Compute NB_PIXELS
    NB_PIXELS = 0
    for c in conf :
        for pixel in conf[c].split(','):
            if pixel != '' and int(pixel) >= NB_PIXELS:
                NB_PIXELS = int(pixel)+1

    CStrip = CStrip.CStrip(PIN, NB_PIXELS, BRIGHTNESS, DMA, 'TARGET', configuration=CONFIG, leds_type=LEDS_TYPE, bgcolors=BGCOLORS, bgbrightness=BGBRIGHTNESS, strip_type=STRIP_TYPE)

    if CStrip.target_leds_count == 0:
        print("[WARNING] No leds configured")
        sys.exit(0)

    print(f"[DEBUG] TargetLeds_Server : Starting server with following parameters")
    print(f"[DEBUG] TargetLeds_Server : host={MQTT_HOST}")
    print(f"[DEBUG] TargetLeds_Server : Dma channel={DMA}")
    print(f"[DEBUG] TargetLeds_Server : Pin={PIN}")
    print(f"[DEBUG] TargetLeds_Server : Type={STRIP_TYPE}")
    print(f"[DEBUG] TargetLeds_Server : Topic={MQTT_TOPIC}")
    print(f"[DEBUG] TargetLeds_Server : Nb pixels={NB_PIXELS}")
    print(f"[DEBUG] TargetLeds_Server : Brightness={BRIGHTNESS}")
    print(f"[DEBUG] TargetLeds_Server : config={CONFIG}", flush=True)

    if BGBRIGHTNESS is not None:
        print(f"[DEBUG] TargetLeds_Server : bgbrightness={BGBRIGHTNESS}", flush=True)
    if BGCOLORS is not None:
        print(f"[DEBUG] TargetLeds_Server : bgcolors={BGCOLORS}", flush=True)

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)    # paho-mqtt 2
        client.on_connect = on_connect
        t_event = Event()
        client.on_message = on_message

        client.connect(MQTT_HOST, 1883, 60)
        print("[INFO] TargetLeds_Server : Connected", flush=True)
        client.loop_forever()

    except:
        print("[ERROR] TargetLeds_Server : Cannot connect to",MQTT_HOST)
        sys.exit(9)

