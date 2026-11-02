"""
Beta : the installation told by a QR code (screen of the technical informations, F9). Scanned,
it opens the page of the beta testers with what the borne is and what is plugged on it, after
a « # » : nothing reaches a server before the tester sends a report from the page.

Never a password, a token, a name nor an address : the identifier of the Raspberry is its
serial hashed (cupdate.machine_id, the one of the statistics and of Raspy2DMD).

Fields (format f=1) : id identifier, v version, pi model, os codename, res resolution, lang,
th theme, touch touchscreens, usb pads (port:keysk knobsm, by « , »), mcp extension chips,
in / out pins of the target matrix, seg segments calibrated (on 82), tled LEDs of the target
(pin, 0 : none), lseg segments lit by them, strip LEDs of the strip, shock sensor (1/0), cam
webcam (1/0), coin coin acceptor (off, games, time ; +in : its input chosen), snd output of
the sound, dmd version of Raspy2DMD (0 : none), expo exhibition mode (1/0)
"""
import os
import re
from urllib.parse import urlencode

from . import cupdate

# Page of the beta testers (SectionGlobals > beta_page changes it)
PAGE = 'https://raspystats.raspyhub.fr/beta'
FORMAT = 1
# Segments of a target : singles (inner and outer), doubles, triples, bull and double bull
SEGMENTS = [f'{mult}{num}' for mult in ('s', 'S', 'D', 'T') for num in range(1, 21)] + ['SB', 'DB']


def filled(values):
    '''
    Values set (not empty, not 0)
    '''
    return [value for value in values if str(value).strip() not in ('', '0', 'False', 'None')]


def os_codename():
    try:
        with open('/etc/os-release', encoding='utf-8') as file:
            found = re.search(r'^VERSION_CODENAME=(.*)$', file.read(), re.M)
        return found.group(1).strip('"') if found else '?'
    except OSError:
        return '?'


def touchscreens():
    '''
    Touchscreens plugged : the input devices which point directly at the screen
    '''
    try:
        import evdev    # pylint: disable=import-outside-toplevel
        count = 0
        for path in evdev.list_devices():
            device = evdev.InputDevice(path)
            if evdev.ecodes.INPUT_PROP_DIRECT in device.input_props():
                count += 1
            device.close()
        return count
    except Exception:    # pylint: disable=broad-except
        return 0


def raspy2dmd_version():
    try:
        with open('/Raspy2DMD/web/VERSION', encoding='utf-8') as file:
            return file.read().strip() or '0'
    except OSError:
        return '0'


def infos(config, rpi, version, model, resolution):
    '''
    What the borne is and what is plugged on it, as the fields of the QR code
    '''
    sections = config.config
    keys = sections.get('SectionKeys', {})
    leds = sections.get('Raspberry_Leds', {})
    pins = sections.get('Raspberry', {})
    pads = getattr(rpi, 'usb_pads', None)
    plugged = []
    if pads is not None:
        for port in pads.plugged():
            settings = pads.settings_of(port)
            plugged.append(f"{port}:{settings.get('keys', 0)}k{settings.get('knobs', 0)}m")
    coins = getattr(rpi, 'coins', None)
    coin = 'off'
    if coins is not None:
        coin = str(coins.settings.get('mode') or 'off') + ('+in' if coins.settings.get('mcp') else '')
    extender = getattr(rpi, 'gpio', None)
    return {
        'f': FORMAT,
        'id': cupdate.machine_id() or '?',
        'v': version,
        'pi': model,
        'os': os_codename(),
        'res': f'{resolution[0]}x{resolution[1]}',
        'lang': config.get_value('SectionGlobals', 'locale', False),
        'th': config.get_value('SectionGlobals', 'colorset', False),
        'touch': touchscreens(),
        'usb': ','.join(plugged) or '0',
        'mcp': len(getattr(extender, 'chips', []) or []),
        'in': len(filled(sections.get('Raspberry_BoardPinsIns', {}).values())),
        'out': len(filled(sections.get('Raspberry_BoardPinsOuts', {}).values())),
        'seg': len(filled(keys.get(segment, '') for segment in SEGMENTS)),
        'tled': leds.get('PIN_TARGETLED', 0) or 0,
        'lseg': len(filled(sections.get('LEDTarget', {}).values())),
        'strip': leds.get('NBR_STRIPLED', 0) if filled([leds.get('PIN_STRIPLED', 0)]) else 0,
        'shock': int(bool(filled([pins.get('PIN_MISSDART', ''), keys.get('MISSDART', ''), keys.get('SHOCKSENSOR', '')]))),
        'cam': int(str(sections.get('Camera', {}).get('camera_id', '-1')) not in ('-1', '', 'False')),
        'coin': coin,
        'snd': config.get_value('SectionGlobals', 'sound_output', False) or 'auto',
        'dmd': raspy2dmd_version(),
        'expo': int(bool(config.get_value('SectionGlobals', 'exhibition_mode', False))),
    }


def url(config, fields):
    '''
    Address of the page of the beta testers, the fields after its « # »
    '''
    page = config.get_value('SectionGlobals', 'beta_page', False) or PAGE
    return f"{page}#{urlencode(fields)}"

