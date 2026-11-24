"""
The compositor of the desktop (picom, set by the installer : it waits for the sweep of the screen,
no torn frames) lets RaspyDarts draw straight on the screen : --unredir-if-possible.

Measured on a Pi 3 in 1920 x 1080 (/dev/fb0, 24/11/2026) : through picom, 30 frames a second at
most and half of them lost on a big message ; straight on the screen, every frame of the
animated messages shown (60 a second), the screen sent 5 to 10 times faster.

The bornes installed before : at the start of the game, the line of picom of their session gets
the option (its file kept as .avant-unredir), and picom is started again with it at once.
"""

import os
import subprocess
import threading

OPTION = '--unredir-if-possible'
SESSIONS = ('/etc/xdg/lxsession/rpd-x/autostart',
            os.path.expanduser('~/.config/lxsession/rpd-x/autostart'))


def patched(text):
    '''
    The session with the option on the line of picom ; None if nothing to change
    '''
    lines = text.split('\n')
    changed = False
    for index, line in enumerate(lines):
        if line.startswith('@picom ') and OPTION not in line.split():
            lines[index] = f'{line.rstrip()} {OPTION}'
            changed = True
    return '\n'.join(lines) if changed else None


def patch_session(path, logs):
    '''
    The option added to the session file (sudo for the one of the system). True if changed
    '''
    try:
        with open(path, encoding='utf-8') as source:
            text = source.read()
    except OSError:
        return False
    content = patched(text)
    if content is None:
        return False
    try:
        if os.access(path, os.W_OK):
            with open(f'{path}.avant-unredir', 'w', encoding='utf-8') as backup:
                backup.write(text)
            with open(path, 'w', encoding='utf-8') as target:
                target.write(content)
        else:
            subprocess.run(['sudo', '-n', 'cp', path, f'{path}.avant-unredir'], check=True, timeout=10,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', '-n', 'tee', path], input=content, text=True, check=True, timeout=10,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError) as error:
        logs.warning(f"Compositor : {path} not changed ({error})")
        return False
    logs.info(f"Compositor : {OPTION} added to {path}")
    return True


def restart_picom(logs):
    '''
    picom running without the option : started again with it (its other options kept)
    '''
    try:
        found = subprocess.run(['pgrep', '-a', '-x', 'picom'], capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.SubprocessError):
        return
    lines = [line.split() for line in found.stdout.splitlines() if line.strip()]
    if not lines or any(OPTION in words for words in lines):
        return
    arguments = lines[0][2:] + [OPTION]
    try:
        subprocess.run(['pkill', '-x', 'picom'], timeout=5, check=False)
        subprocess.Popen(['picom'] + arguments, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,    # pylint: disable=consider-using-with
                         stderr=subprocess.DEVNULL, start_new_session=True)
        logs.info(f"Compositor : picom started again with {OPTION}")
    except OSError as error:
        logs.warning(f"Compositor : picom not started again ({error})")


def follow(logs):
    '''
    At the start of the game (in the background) : the sessions and picom with the option
    '''
    def work():
        for path in SESSIONS:
            patch_session(path, logs)
        restart_picom(logs)
    threading.Thread(target=work, daemon=True, name='compositor').start()
