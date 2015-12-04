########################################################################

"""\
i18n related utility functions
"""

########################################################################

import locale
import gettext
import os
import sys
from os.path import abspath, dirname

########################################################################

from . import log

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

__trans_cache = {}

def set_lang(lang=None):
    log.verbose('set_lang(%s)', repr(lang))

    if lang not in __trans_cache:
        if lang == default_language:
            lang = None

        if lang:
            for l in (locale.LC_ALL, locale.LC_MESSAGES, locale.LC_TIME):
                locale.setlocale(l, languages[lang][1])
        else:
            locale.setlocale(locale.LC_ALL, '')

        text_domain = 'weight-calendar-grid'

        trans = None

        locale_dirs = []
        last_dir = None
        curr_dir = abspath(dirname(__file__))
        while last_dir != curr_dir:
            for rel_dir in [os.path.join('share', 'locale'), 'locale']:
                locale_dir = os.path.join(curr_dir, rel_dir)
                locale_dirs.append(locale_dir)
            last_dir = curr_dir
            curr_dir = abspath(os.path.join(curr_dir, os.pardir))

        if lang:
            locale_dirs = [abspath('build/locale')] + locale_dirs
            for locale_dir in locale_dirs:
                log.debug('Looking for lang %s in %s', repr(lang), locale_dir)
                try:
                    trans = gettext.translation(text_domain, locale_dir,
                                                [languages[lang][1], lang])
                    log.debug("Found %s translation in %s", repr(lang), locale_dir)
                    break
                except FileNotFoundError as e:
                    continue

            if not trans:
                log.error("Could not find translation for %s. I tried the following:",
                         repr(lang))
                for d in locale_dirs:
                    log.error("    %s", d)
                sys.exit(1)

        else:
            log.warn('Using NULL translation')
            trans = gettext.NullTranslations()

        __trans_cache[lang] = trans

    __trans_cache[lang].install()

########################################################################
