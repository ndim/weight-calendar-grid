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

level = INFO

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

    if level >= lvl:

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
