#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
The machine RaspyDarts runs on : a Raspberry Pi, or another computer with Linux (a PC played
with Autodarts or a target plugged by USB). On another computer, everything proper to the
Raspberry is left aside : its pins (target matrix, MCP23017 boards, LED strips), its firmware
tools (vcgencmd, tvservice), the mode of its screen, omxplayer
'''

import os
import platform
from functools import lru_cache

MODEL_FILE = '/proc/device-tree/model'


@lru_cache(maxsize=None)
def model():
    '''
    Model told by the firmware ("Raspberry Pi 3 Model B Plus Rev 1.3"), '' on another computer
    '''
    try:
        with open(MODEL_FILE, encoding='utf-8', errors='ignore') as file:
            return file.read().replace('\x00', '').strip()
    except OSError:
        return ''


def is_raspberry():
    '''
    Running on a Raspberry Pi (Compute Modules and Pi 400 / 500 included)
    '''
    return 'Raspberry Pi' in model()


@lru_cache(maxsize=None)
def system_name():
    '''
    Name of the system ("Ubuntu 24.04.1 LTS"), '' if unknown
    '''
    try:
        with open('/etc/os-release', encoding='utf-8') as file:
            for line in file:
                if line.startswith('PRETTY_NAME='):
                    return line.split('=', 1)[1].strip().strip('"')
    except OSError:
        pass
    return ''


@lru_cache(maxsize=None)
def system_arch():
    '''
    Architecture of the system, not of the kernel (a 32 bits system on a 64 bits kernel, as on a
    Pi 5) : armhf (32 bits), arm64 (64 bits), amd64 (a PC)... ; '' if unknown
    '''
    import subprocess    # pylint: disable=import-outside-toplevel
    try:
        return subprocess.run(['dpkg', '--print-architecture'], capture_output=True, text=True,
                              timeout=5, check=False).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ''


def description():
    '''
    The machine in a few words : the model of the Raspberry, else "PC x86_64 (Ubuntu 24.04)"
    '''
    if is_raspberry():
        return model()
    name = system_name()
    return f"PC {platform.machine()}" + (f" ({name})" if name else '')


def has_gpio():
    '''
    Pins usable by the game (target matrix, buttons, LED) : a Raspberry with its GPIO device
    '''
    return is_raspberry() and (os.path.exists('/dev/gpiochip0') or os.path.exists('/dev/gpiomem'))
