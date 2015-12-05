########################################################################

"""\
i18n related utility functions
"""

########################################################################

import locale
import gettext
import os
import sys
from os.path import abspath, dirname, join

########################################################################

from . import log
from .version import text_domain

########################################################################

default_language = 'en'

languages = {
    'de': ('Deutsch', 'de_DE.UTF-8'),
    'en': ('English', 'en_US'),
    }

def print_language_list(outfile=None):
    if not outfile:
        outfile = sys.stdout
    print("List of output languages:", file=outfile)
    for lang in sorted(languages.keys()):
        language = languages[lang][0]
        if lang == default_language:
            print("   ", '%s (%s, program default)' % (lang, language), file=outfile)
        else:
            print("   ", '%s (%s)' % (lang, language), file=outfile)

########################################################################

def load_translation(lang=None):
    if lang == None or lang == default_language:
        locale.setlocale(locale.LC_ALL, '')
        log.warn('Using NULL translation')
        return gettext.NullTranslations()

    for l in (locale.LC_ALL, locale.LC_MESSAGES, locale.LC_TIME):
        locale.setlocale(l, languages[lang][1])

    locale_dir = join(abspath(dirname(__file__)), 'locale')
    log.debug('Looking for lang %s in %s', repr(lang), locale_dir)
    try:
        t = gettext.translation(text_domain, locale_dir,
                                    [languages[lang][1], lang])
        log.debug("Found %s translation in %s", repr(lang), locale_dir)
        return t
    except FileNotFoundError as e:
        log.error("Could not find translation for %s. I tried the following:",
                 repr(lang))
        log.error("    %s", locale_dir)
        sys.exit(1)

########################################################################

__trans_cache = {}

def get_translation(lang=None):
    if lang not in __trans_cache:
        __trans_cache[lang] = load_translation(lang)
    return __trans_cache[lang]

########################################################################

def install_translation(lang=None):
    log.verbose('set_lang(%s)', repr(lang))
    get_translation(lang).install()

########################################################################

# Install/set default locale/translations
locale.setlocale(locale.LC_ALL, '')
gettext.NullTranslations().install()

########################################################################
