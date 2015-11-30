
"""Implement command line command"""


########################################################################


import argparse
import datetime
import os
import sys
import time

import locale
import gettext


from pprint import pprint


########################################################################


from . import generate_grid
from . import drivers
from . import log
from . import version
from .i18n import set_lang, languages, print_language_list


########################################################################


class KGRangeType(object):

    def __init__(self):
        super(KGRangeType, self).__init__()

    def __call__(self, string):
        if string == 'auto':
            return None
        s = string.split('+-')
        if len(s) == 1:
            s = string.split('-')
            if len(s) == 1:
                return float(string)
            elif len(s) == 2:
                (lhs, rhs) = s
                (lhs, rhs) = (float(lhs), float(rhs))
                assert(lhs < rhs)
                return (lhs, rhs)
            else:
                raise ValueError('invalid kg range')
        elif len(s) == 2:
            (lhs, rhs) = s
            (lhs, rhs) = (float(lhs), float(rhs))
            assert(rhs < lhs)
            return (lhs-rhs, lhs+rhs)
        else:
            raise ValueError('invalid kg range')

    def __repr__(self):
        return '%s' % (type(self).__name__, )


########################################################################


class DriverAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        driver_cls = drivers.get_driver(values)
        setattr(namespace, self.dest, driver_cls)


########################################################################


class OutputFormatAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        if not namespace.driver_cls:
            parser.error('driver must be specified before output format')
        if values not in namespace.driver_cls.driver_formats:
            parser.error('output format %s not handled by driver %s'
                         % (values, namespace.driver_cls.driver_name))
        setattr(namespace, self.dest, values)


########################################################################


class FooAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        log.info('%r %r %r', namespace, values, option_string)
        setattr(namespace, self.dest, values)


########################################################################


class OptionListAction(argparse.Action):

    def __init__(self, option_strings,
                 dest=argparse.SUPPRESS,
                 default=argparse.SUPPRESS,
                 help=None):
        super(OptionListAction, self).__init__(
            option_strings=option_strings,
            dest=dest,
            default=default,
            nargs=0,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        log.debug('%r %r %r', namespace, values, option_string)
        outfile = sys.stdout
        drivers.print_driver_list(outfile)
        print_language_list(outfile)
        print_plot_mode_list(outfile)
        parser.exit()
        # setattr(namespace, self.dest, values)


########################################################################


class DateAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        log.debug('%r %r %r', namespace, values, option_string)
        ts = time.strptime(values, '%Y-%m-%d')
        date = datetime.date(*(ts[0:3]))
        assert(date.isoformat() == values)
        setattr(namespace, self.dest, date)


########################################################################


class BeginDateAction(DateAction):

    def __call__(self, parser, namespace, values, option_string=None):
        super(BeginDateAction, self).__call__(
            parser, namespace, values, option_string)
        if namespace.end_date:
            if (namespace.end_date - namespace.begin_date).days <= 0:
                parser.error('begin date must be before end date')


########################################################################


class EndDateAction(DateAction):

    def __call__(self, parser, namespace, values, option_string=None):
        super(EndDateAction, self).__call__(
            parser, namespace, values, option_string)
        if namespace.begin_date:
            if (namespace.end_date - namespace.begin_date).days <= 0:
                parser.error('end date must be after begin date')


########################################################################


class OutFileWrapper(object):


    """Wrap output file to only open/generate the file when output occurs"""


    def __init__(self, filename, mode, bufsize):
        super(OutFileWrapper, self).__init__()
        self._filename = filename
        self._mode = mode
        self._bufsize = bufsize
        self._file = None
        self._dry_run = False


    def __del__(self):
        if self._file:
            self._file.close()


    def dry_run(self):
        log.debug('OutfileWrapper.dry_run() called')
        self._dry_run = True


    def __getattribute__(self, key):
        if key in ['_bufsize', '_filename', '_mode', '_file',
                   '_dry_run', 'dry_run']:
            return super(OutFileWrapper, self).__getattribute__(key)

        if not self._file:
            if key == 'name':
                return self._filename
            if key == 'isatty':
                def simulated_isatty():
                    return False
                return simulated_isatty
            log.debug('OutFileWrapper attr access for %s', repr(key))
            if self._dry_run:
                log.verbose('OutFileWrapper: Opening dummy dry-run output file %s for %s',
                            repr(self._filename), repr(key))
                self._file = open('/dev/null', self._mode, self._bufsize)
            else:
                log.verbose('OutFileWrapper: Opening actual output file %s for %s',
                            repr(self._filename), repr(key))
                self._file = open(self._filename, self._mode, self._bufsize)
            assert(self._file)

        return getattr(self._file, key)


########################################################################


class OutFileType(argparse.FileType):

    def __init__(self):
        super(OutFileType, self).__init__(mode='wb')

    def __call__(self, string):
        log.debug('OutFileType.__call__(%s) for %s', repr(string), self)
        if string == '-':
            return sys.stdout
        return OutFileWrapper(string, self._mode, self._bufsize)


########################################################################


def main(argv=None, simulated_infile=None):
    set_lang()
    parser = argparse.ArgumentParser(
        prog=version.program_name,
        description=_('plot weight/calendar grid for easy weight tracking'),
        add_help=False, # we want the help in a different place in the help
        epilog="""\
Note that the KG_RANGE can take one of four forms:
   'auto'    automatically generate a kg range from plot data or height.
   MIN-MAX   range from MIN kg to MAX kg.
   AVG       guessed range containing AVG kg.
   AVG+-DEV  range around AVG kg plus/minus DEV kg.
""")

    cmd_grp    = parser.add_argument_group('special commands not plotting a grid')
    date_grp   = parser.add_argument_group('date range')
    global_grp = parser.add_argument_group('global flags')
    mode_grp   = parser.add_argument_group('plotting mode')
    output_grp = parser.add_argument_group('output specification')
    person_grp = parser.add_argument_group('personal information')

    date_grp.add_argument(
        '-b', '--begin', '--begin-date',
        dest='begin_date',
        action=BeginDateAction,
        metavar='YYYY-MM-DD',
        help='begin date '
        '(default: first input file date or today if Sunday,'
        ' or the previous Sunday)')

    output_grp.add_argument(
        '-d', '--driver', metavar='DRIVER',
        dest='driver_cls', action=DriverAction,
        default=drivers.get_driver(None),
        help='use this output driver (--list-options for a list)')

    global_grp.add_argument(
        '-N', '--dry-run', action='store_true',
        dest='dry_run',
        help='do not actually write any files')

    date_grp.add_argument(
        '-e', '--end', '--end-date',
        dest='end_date',
        action=EndDateAction,
        metavar='YYYY-MM-DD',
        help='end date (default: begin date plus 8 weeks)')

    output_grp.add_argument(
        '-f', '--format', metavar='FORMAT',
        dest='output_format',
        action=OutputFormatAction,
        help='select output format to use '
        '(default: driver dependent, see --list-options)')

    person_grp.add_argument(
        '-H', '--height', type=float, metavar='HEIGHT',
        dest='height', default=None,
        help=("the person's height in m "
              "(give this to plot a BMI axis and BMI based estimations)"))

    cmd_grp.add_argument(
        '-h', '--help', action='help',
        help='show this help message and exit')

    person_grp.add_argument(
        '-I', '--initials', type=str, metavar='SHORT_STRING',
        dest='initials', default=None,
        help="person's initials to be printed on page (default: no initials)")

    mode_grp.add_argument(
        '-i', '--input', metavar='FILE',
        default=None,
        type=argparse.FileType(mode='r'),
        help='plot weight data into generated grid file')

    global_grp.add_argument(
        '-k', '--keep', action='store_true',
        dest='keep_tmp_on_error',
        help='keep temporary files when finished '
        '(default: delete them)')

    global_grp.add_argument(
        '-l', '--lang', '--language', metavar='LANG',
        dest='lang',
        choices=languages,
        help='the language to use (default: system locale)')

    cmd_grp.add_argument(
        '-L', '--list-options',
        action=OptionListAction,
        help='list all languages, output drivers, formats and exit')

    mode_grp.add_argument(
        '-m', '--mode', metavar='PLOTMODE',
        dest='plot_mode',
        choices=plot_mode_list,
        default=plot_mode_default,
        help='mode for plotting existing data '
        '(default: mode for noting down value marks)')

    output_grp.add_argument(
        '-o', '--output', metavar='FILE',
        default='-',
        type=OutFileType(),
        help='name of output grid file to write '
        '(default: <stdout> if not a TTY)')

    global_grp.add_argument(
        '-q', '--quiet', dest='quiet',
        action='count', default=0,
        help='make output more quiet')

    global_grp.add_argument(
        '-v', '--verbose', dest='verbose',
        action='count', default=0,
        help='make output more verbose')

    cmd_grp.add_argument(
        '-V', '--version', action='version',
        version = ('%(program_name)s (%(package_name)s) %(package_version)s'
                   % vars(version)))

    person_grp.add_argument(
        '-W', '--weight', type=KGRangeType(), metavar='KG_RANGE',
        default='auto',
        help="weight range (in kg) to plot (default: auto)")

    args = parser.parse_args(args=argv)

    ver_qu = args.verbose - args.quiet
    log.level = log.startup_level + ver_qu

    if args.weight and args.height:
        pass
    elif args.weight:
        pass
    elif args.height:
        pass
    else:
        parser.error("Cannot determine plot parameters without either "
                     "--height= or --weight= or both.")

    if args.lang:
        log.verbose('setting locale %s', args.lang)
        set_lang(args.lang)

    if simulated_infile and not args.input:
        log.debug("Using simulated input file")
        args.input = simulated_infile

    if args.output.isatty():
        parser.error('If you really want to output to the TTY, '
                     'pipe the output through cat. Otherwise, set --output.')

    if args.dry_run:
        if hasattr(args.output, 'dry_run'):
            args.output.dry_run()
        else:
            parser.error('--dry-run is incompatible with writing to <stdout>')

    log.debug('Given arguments: %s', args)

    if False:
        log.debug('foox debug')
        log.verbose('foox verbose')
        log.info('foox info')
        log.quiet('foox info')
        log.warn('foox warn')
        log.error('foox error')

    log.debug('locale %s', locale.getlocale())
    log.debug('locale LC_MESSAGES %s', locale.getlocale(locale.LC_MESSAGES))
    log.debug('locale LC_TIME %s', locale.getlocale(locale.LC_TIME))

    generate_grid(
        args.height,
        args.weight,
        (args.begin_date, args.end_date),
        args.input,
        args.driver_cls, args.output_format,
        args.output,
        args.keep_tmp_on_error,
        args.plot_mode == 'history',
        args.initials)

    sys.exit(0)


########################################################################


plot_mode_dict = {
    'mark': 'printout for marking down new measured values',
    'history': 'printout for showing history of values',
    }
plot_mode_list = sorted(plot_mode_dict.keys())

plot_mode_default = 'mark'
assert(plot_mode_default in plot_mode_dict)

def print_plot_mode_list(outfile=None):
    if not outfile:
        outfile = sys.stdout
    print("List of output plot modes:", file=outfile)
    for plot_mode in plot_mode_list:
        pm_descr = plot_mode_dict[plot_mode]
        if plot_mode == plot_mode_default:
            d_str = ' (program default)'
        else:
            d_str = ''

        print("   ", '%-8s %s%s' % ('%s:'%plot_mode, pm_descr, d_str), file=outfile)


########################################################################
