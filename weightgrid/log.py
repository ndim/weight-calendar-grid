"""Generic and custom log message infrastructure"""

########################################################################

"""\
log - simple logging module

This is so much simpler than Python's stock 'logging' module and thus
much less error prone in use.
"""

########################################################################

import os
import sys
import traceback

########################################################################

DATA    =  3
DEBUG   =  2
VERBOSE =  1
INFO    =  0
QUIET   = -1
WARN    = -2
ERROR   = -3

########################################################################

level = None
startup_level = INFO

########################################################################

outfile = sys.stderr

########################################################################

try:
    # Two variants possible: For make -j processing with PID, and without.
    # No way to distinguish between the cases, so always print the PID.
    try:
        _prog = os.path.basename(sys.argv[0])
    except:
        from .version import program_name as _prog
    prog = "%s(%d)" % (_prog, os.getpid())
    del _prog
except ImportError:
    prog = None

########################################################################

def log(lvl, msg, *args, **kwargs):

    """Generic logging function"""

    if ((level != None) and (level >= lvl)) or (startup_level >= lvl):

        if 'exc_info' in kwargs:
            exc_info = kwargs['exc_info']
            if not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()

            traceback.print_exception(
                exc_info[0], exc_info[1], exc_info[2],
                None, sys.stderr)

        if msg:
            p = {}

            if args:
                p['message'] = msg % args
            else:
                p['message'] = msg

            p['prog'] = prog

            p['catmsg'] = {
                DATA:    'DATA:  ',
                DEBUG:   'DEBUG: ',
                VERBOSE: 'VERB:  ',
                INFO:    'INFO:  ',
                QUIET:   'QUIET: ',
                WARN:    'WARN:  ',
                ERROR:   'ERROR: ',
                }[lvl]

            print("%(prog)s: %(catmsg)s%(message)s" % p, file=outfile)

########################################################################

def data(msg=None, *args, **kwargs):
    """Log message at DATA level"""
    log(DATA, msg, *args, **kwargs)

########################################################################

def debug(msg=None, *args, **kwargs):
    """Log message at DEBUG level"""
    log(DEBUG, msg, *args, **kwargs)

########################################################################

def verbose(msg=None, *args, **kwargs):
    """Log message at VERBOSE level"""
    log(VERBOSE, msg, *args, **kwargs)

########################################################################

def info(msg=None, *args, **kwargs):
    """Log message at INFO level"""
    log(INFO, msg, *args, **kwargs)

########################################################################

def quiet(msg=None, *args, **kwargs):
    """Log message at QUIET level"""
    log(QUIET, msg, *args, **kwargs)

########################################################################

def warn(msg=None, *args, **kwargs):
    """Log message at WARN level"""
    log(WARN, msg, *args, **kwargs)

########################################################################

def error(msg=None, *args, **kwargs):
    """Log message at ERROR level"""
    log(ERROR, msg, *args, **kwargs)

########################################################################

env_name = 'WCG_LOG_LEVEL'

if env_name in os.environ:
    env_value = os.environ[env_name]
    value_map = {'data':    DATA,    'DATA':    DATA,
                 '3':       DATA,    '+3':      DATA,
                 'debug':   DEBUG,   'DEBUG':   DEBUG,
                 '2':       DEBUG,   '+2':      DEBUG,
                 'verbose': VERBOSE, 'VERBOSE': VERBOSE,
                 '1':       VERBOSE, '+1':      VERBOSE,
                 'info':    INFO,    'INFO':    INFO,
                 '0':       INFO,    '+0':      INFO,    '-0': INFO,
                 '':        INFO,
                 'quiet':   QUIET,   'QUIET':   QUIET,   '-1': QUIET,
                 'warn':    WARN,    'WARN':    WARN,    '-2': WARN,
                 'error':   ERROR,   'ERROR':   ERROR,   '-3': ERROR,
    }
    if env_value in value_map:
        startup_level = value_map[env_value]
    else:
        error('Invalid value for %s OS environment variable: %s',
              env_name, repr(env_value))
        error('%s must be one of:', env_name)
        rev_map = {}
        for k, v in value_map.items():
            if v not in rev_map:
                rev_map[v] = ([], [])
            if k == '':
                # rev_map[v][1].append("''")
                pass
            else:
                try:
                    i = int(k)
                    rev_map[v][0].append(k)
                except ValueError:
                    rev_map[v][1].append(k)
        for n in range(3, -3-1, -1):
            error('  %-10s %s',
                  ' '.join(["%2s" % a
                            for a in sorted(rev_map[n][0])]),
                  ' '.join(["%-7s" % a
                            for a in reversed(sorted(rev_map[n][1]))]))
        error('If %s is unset or empty, the startup log level is INFO.',
              env_name)
        sys.exit(2)

########################################################################
