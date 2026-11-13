"""
The I2C bus (GPIO 2 and 3) and the wiring of the cabinet.

The installation turns the I2C bus on (dtparam=i2c_arm=on) for the MCP23017 extension cards :
its pins, GPIO 2 (SDA) and GPIO 3 (SCL), are then kept by the kernel. A cabinet wired on GPIO 2
or 3 (target, buttons) without a MCP card could not use them : its target reader failed and the
game stopped. At the start, the setting of the Raspberry follows the wiring declared :

- GPIO 2 or 3 used : the I2C bus turned off ;
- buttons declared on a MCP card (A0, B3...) and GPIO 2 and 3 free : the I2C bus turned on.

The change is written in config.txt and applies at the next start of the Raspberry (asked).
"""

import os
import re
import subprocess

CONFIG_FILES = ('/boot/firmware/config.txt', '/boot/config.txt')
I2C_PINS = {2, 3}
PARAM = re.compile(r'^\s*dtparam=(?:i2c_arm|i2c)=(on|off)\s*$')


def config_file():
    return next((path for path in CONFIG_FILES if os.path.isfile(path)), None)


def gpio_used(config):
    '''
    The GPIO of the wiring declared : the target (inputs, outputs), the buttons on GPIO
    '''
    used = set()
    sections = [config.config.get('Raspberry_BoardPinsIns') or {}, config.config.get('Raspberry_BoardPinsOuts') or {}]
    keys = config.config.get('SectionKeys') or {}
    buttons = getattr(config, 'GPIO_BUTTONS_CONFIG', ())
    sections.append({key: value for key, value in keys.items() if key in buttons})
    for section in sections:
        for value in section.values():
            if str(value).strip().isdigit():
                used.add(int(value))
    return used


def mcp_declared(config):
    '''
    Buttons, lights or toys declared on a MCP card (A0, B3...)
    '''
    return any(re.match(r'^[A-P]\d{1,2}$', str(value).strip().upper()) for value in (config.config.get('Raspberry') or {}).values())


def enabled_in_config():
    '''
    The I2C bus asked in config.txt (the last line found wins), None : no config.txt
    '''
    path = config_file()
    if path is None:
        return None
    state = False
    try:
        with open(path, encoding='utf-8', errors='replace') as source:
            for line in source:
                match = PARAM.match(line)
                if match:
                    state = match.group(1) == 'on'
    except OSError:
        return None
    return state


def active():
    '''
    The I2C bus on now (since the start of the Raspberry)
    '''
    return os.path.exists('/dev/i2c-1')


def write(state):
    '''
    config.txt : the I2C bus turned on or off (its lines changed, one added if none). True : done
    '''
    path = config_file()
    if path is None:
        return False
    value = 'on' if state else 'off'
    try:
        with open(path, encoding='utf-8', errors='replace') as source:
            lines = source.read().splitlines()
    except OSError:
        return False
    found = False
    for index, line in enumerate(lines):
        if PARAM.match(line):
            lines[index] = f'dtparam=i2c_arm={value}'
            found = True
    if not found:
        lines.append(f'dtparam=i2c_arm={value}')
    content = '\n'.join(lines) + '\n'
    try:
        subprocess.run(['sudo', '-n', 'cp', path, f'{path}.avant-i2c'], check=True, timeout=10,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['sudo', '-n', 'tee', path], input=content, text=True, check=True, timeout=10,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return False
    return True


def follow_wiring(config, logs):
    '''
    At the start : the I2C bus set as the wiring wants. Returns None (nothing to do), or
    ('off' | 'on', written) : the change asked, written in config.txt or not (no rights)
    '''
    used = gpio_used(config) & I2C_PINS
    asked = enabled_in_config()
    if used:
        if asked or active():
            done = write(False) if asked else True
            logs.warning(f"I2C : GPIO {', '.join(str(pin) for pin in sorted(used))} used by the wiring, "
                         f"I2C bus turned off ({'written' if done else 'not written'}), restart needed")
            return 'off', done
        return None
    if mcp_declared(config) and asked is False and not active():
        done = write(True)
        logs.warning(f"I2C : MCP card declared, I2C bus turned on ({'written' if done else 'not written'}), restart needed")
        return 'on', done
    return None


def pins_reserved(config):
    '''
    GPIO 2 or 3 in the wiring : the extension cards are not looked for (their bus is off)
    '''
    return bool(gpio_used(config) & I2C_PINS)
