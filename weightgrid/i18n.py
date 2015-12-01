########################################################################

"""\
i18n related utility functions
"""

########################################################################

import locale
import gettext
import os
import sys

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

# TODO: Look for locale/ in directories we may be installed to.

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

        locale_dirs = [ os.path.abspath(p)
                        for p in ['locale', 'build/locale']]
        for locale_dir in locale_dirs:
            try:
                if lang:
                    trans = gettext.translation(text_domain, locale_dir,
                                                [languages[lang][1], lang])
                else:
                    trans = gettext.translation(text_domain, locale_dir)
                break
            except FileNotFoundError as e:
                continue

        if not trans:
            if lang:
                log.error("Could not find translation for %s. I tried the following:", repr(lang))
                for d in locale_dirs:
                    log.error("    %s", d)
                sys.exit(1)
            trans = gettext.NullTranslations()

        __trans_cache[lang] = trans

    __trans_cache[lang].install()

########################################################################
