########################################################################

"""\
i18n related utility functions
"""

########################################################################

import locale
import gettext

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

def set_lang(lang=None):
    log.verbose('set_lang(%s)', repr(lang))

    if lang == default_language:
        lang = None

    if lang:
        for l in (locale.LC_ALL, locale.LC_MESSAGES, locale.LC_TIME):
            locale.setlocale(l, languages[lang][1])
    else:
        locale.setlocale(locale.LC_ALL, '')

    trans = None
    try:
        text_domain = 'plot-weight-calendar-grid'
        if lang:
            trans = gettext.translation(text_domain, 'locale',
                                        [languages[lang][1], lang])
        else:
            trans = gettext.translation(text_domain, 'locale')
    except IOError as e:
        if lang:
            log.error("Could not find translations", exc_info=True)
            sys.exit(1)

    if not trans:
        trans = gettext.NullTranslations()
    trans.install()

########################################################################
