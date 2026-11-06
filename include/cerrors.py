"""
Errors to report : a crash of the game (an error not caught, RaspyDarts.sh starts it again) or
a serious error caught (a game which fails). Its report is kept in logs/erreur.json, shown at
the next menu (cscreen.error_report_screen) with a QR code : scanned with a phone, it opens a
new issue on GitHub filled with it (the account of whoever scans it : no secret on the borne).

Kept in the report : what happened (crash or error, its type, its message, the end of its
trace with the files of the game only), the version, the Raspberry, the system, the game
played. Never a name, an address or a password : the paths are cut at the folder of the game.
Shown once : renamed before being shown (a crash on that screen does not show it again).
"""
import json
import os
import platform
import sys
import time
import traceback
from urllib.parse import quote

REPORT = os.path.join('logs', 'erreur.json')
SHOWN = os.path.join('logs', 'erreur-vue.json')
ISSUES = 'https://github.com/rmdelcelier/RaspyDarts/issues/new'
# Length of the address of the QR code at most : read by a phone on the screen of the borne
MAX_URL = 1500
# Lines of the trace kept at most (its end : where it stopped)
MAX_FRAMES = 6
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def os_codename():
    '''
    Codename of the system (trixie, bookworm...)
    '''
    try:
        with open('/etc/os-release', encoding='utf-8') as file:
            for line in file:
                if line.startswith('VERSION_CODENAME='):
                    return line.split('=', 1)[1].strip().strip('"')
    except OSError:
        pass
    return platform.system()


def model():
    '''
    Model of the Raspberry
    '''
    try:
        with open('/proc/device-tree/model', encoding='utf-8') as file:
            return file.read().replace('Raspberry ', '').rstrip('\x00').strip()
    except OSError:
        return platform.machine()


def short_path(path):
    '''
    Path of a file of the game from its folder (games/classic/Cricket.py) ; another one (a
    library) : its name only
    '''
    path = os.path.abspath(path)
    if path.startswith(ROOT + os.sep):
        return os.path.relpath(path, ROOT).replace(os.sep, '/')
    return os.path.basename(path)


def frames(trace):
    '''
    End of a trace : « file:line function », the last one where it stopped
    '''
    return [f"{short_path(frame.filename)}:{frame.lineno} {frame.name}"
            for frame in traceback.extract_tb(trace)[-MAX_FRAMES:]]


def record(kind, version, exc_info=None, context='', game=''):
    '''
    Keeps the report of an error (kind : crash or error) : the current exception, or the one
    given (sys.exc_info()). Never raises : called while the game stops on an error
    '''
    try:
        error_type, error, trace = exc_info or sys.exc_info()
        report = {'kind': kind,
                  'time': time.strftime('%Y-%m-%d %H:%M'),
                  'version': str(version),
                  'pi': model(),
                  'os': os_codename(),
                  'python': platform.python_version(),
                  'game': str(game or ''),
                  'context': str(context or ''),
                  'error': f"{error_type.__name__ if error_type else '?'}: {str(error)[:300]}",
                  'trace': frames(trace) if trace else []}
        os.makedirs(os.path.dirname(REPORT), exist_ok=True)
        with open(REPORT + '.tmp', 'w', encoding='utf-8') as file:
            json.dump(report, file, ensure_ascii=False, indent=1)
        os.replace(REPORT + '.tmp', REPORT)
        return report
    except Exception:    # pylint: disable=broad-except
        return None


def take():
    '''
    Report to show, None if there is none. Taken : it is not shown again
    '''
    if not os.path.isfile(REPORT):
        return None
    try:
        os.replace(REPORT, SHOWN)
        with open(SHOWN, encoding='utf-8') as file:
            report = json.load(file)
        return report if isinstance(report, dict) else None
    except (OSError, ValueError):
        return None


def issue_url(report):
    '''
    Address of a new issue on GitHub filled with the report, short enough for a QR code (the
    trace shortened first)
    '''
    kind = 'Plantage' if report.get('kind') == 'crash' else 'Erreur'
    title = f"{kind} {report.get('version', '')} : {report.get('error', '')}"[:120]
    trace = list(report.get('trace', []))
    error = report.get('error', '')
    while True:
        lines = [f"**{kind}** du {report.get('time', '')}",
                 '',
                 f"- Version : {report.get('version', '')}",
                 f"- Raspberry : {report.get('pi', '')}",
                 f"- Système : {report.get('os', '')} (Python {report.get('python', '')})"]
        if report.get('game'):
            lines.append(f"- Jeu : {report['game']}")
        if report.get('context'):
            lines.append(f"- Moment : {report['context']}")
        lines += ['', '```', error] + trace + ['```', '',
                  "Ce que je faisais quand c'est arrivé : "]
        url = f"{ISSUES}?title={quote(title)}&body={quote(chr(10).join(lines))}"
        if len(url) <= MAX_URL or (not trace and len(error) <= 40):
            return url
        # Too long : the oldest line of the trace first, then the message of the error
        if trace:
            trace.pop(0)
        else:
            error = error[:max(40, len(error) - 60)]
