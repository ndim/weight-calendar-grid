########################################################################


from io import StringIO
import itertools
import os
import sys
import tempfile
from unittest import TestCase


########################################################################


from ..cli import main
from .. import log
from ..version import package_name, package_version
from .. import drivers


########################################################################


tempdir = None

def setup():
    global tempdir
    tempdir = tempfile.mkdtemp(prefix='weight-calendar-grid.',
                               suffix='.test-output')

def teardown():
    global tempdir
    assert(os.path.isdir(tempdir))
    if 'WCG_TEST_KEEP' in os.environ and os.environ['WCG_TEST_KEEP'] == 'yes':
        log.quiet('keeping test files in %s', tempdir)
    else:
        for fname in os.listdir(tempdir):
            os.unlink(os.path.join(tempdir, fname))
        os.rmdir(tempdir)
    tempdir = None


########################################################################


class DuplicateStdout(object):

    def __init__(self):
        super(DuplicateStdout, self).__init__()
        self.sio = StringIO()
        self.stdout = sys.stdout
        self.outs = None

    def write(self, data):
        self.sio.write(data)
        self.stdout.write(data)

    def getvalue(self):
        return self.outs

    def __enter__(self):
        print("Enter DS", file=sys.stderr)
        sys.stdout = self
        return self

    def __exit__(self, *exc_info):
        print("Leave DS", file=sys.stderr)
        self.outs = self.sio.getvalue()
        print("  outs =", repr(self.outs))
        self.sio.close()
        sys.stdout = self.stdout
        return False


########################################################################


class TestCmdline(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestCmdline, self).__init__(*args, **kwargs)
        self.stderr = sys.stderr
        self.pdf_fname_template = 'TESTCASE-%s.pdf'

    def setUp(self):
        sys.stderr = StringIO()

    def tearDown(self):
        sys.stderr = self.stderr

    def __test_main(self, args, expect_code=0, expect_stdout=None):
        outs = ''
        with self.assertRaises(SystemExit) as cm:
            with DuplicateStdout() as ds:
                main(argv=args)
        self.assertEqual(cm.exception.code, expect_code)
        if expect_stdout != None:
            self.assertEqual(ds.getvalue(), expect_stdout)

    def __test_pdf(self, args, pdf_fname=None, expect_code=0):
        with open(os.path.join(tempdir, 'test.log'), 'a') as logfile:
            print('testing with file', pdf_fname, file=logfile)

        pdf_path = os.path.join(tempdir, pdf_fname)
        self.assertIsInstance(pdf_fname, str)
        self.__test_main(args + ['--output=%s' % pdf_path],
                         expect_code)

        # Check generated PDF file has a reasonable size
        osr = os.stat(pdf_path)
        self.assertNotEqual(osr.st_size, 0)
        self.assertTrue(osr.st_size >= 1024,
                        msg="PDF file appears a bit too small")

    def test_000_nothing(self):
        # First, make sure the empty test succeeds

        # Note the above is not a docstring, as unittest or nose would
        # print that and completely ruin the output on the TTY.
        pass

    def test_001_version(self):
        self.__test_main(
            ['--version'],
            expect_stdout=('wcg-cli (%s) %s\n' % (package_name,
                                                  package_version)))

    def test_002_help(self):
        self.__test_main(['--help'])

    def test_003_list_options(self):
        self.__test_main(['--list-options'])

    # TODO: Test plotting actual weight data.


########################################################################


class ArgList(object):

    def __init__(self, arg_name, value_list=None):
        super(ArgList, self).__init__()
        self.arg_name = arg_name
        if value_list:
            self.value_list = value_list
        else:
            self.value_list = []

    def append(self, value):
        self.value_list.append(value)

    def __iter__(self):
        for value in self.value_list:
            if value:
                yield ['%s=%s' % (self.arg_name, value)]
            else:
                yield []


########################################################################


class ArgPairList(object):

    def __init__(self, *args):
        super(ArgPairList, self).__init__()
        self.iterators = []
        for n in range(0, len(args), 2):
            if isinstance(args[n+1], str):
                self.iterators.append(ArgList(args[n], [None, args[n+1]]))
            elif isinstance(args[n+1], list):
                self.iterators.append(ArgList(args[n], [None]+ args[n+1]))
            else:
                assert(False)

    def __iter__(self):
        for t in itertools.product(*self.iterators):
            a = []
            for e in t:
                a.extend(e)
            yield a


########################################################################


def test_comprehensive():
    # try all combinations of the following arguments

    arg_driver = ArgList('--driver')
    if 'WCG_TEST_DRIVERS' in os.environ:
        drv_list = os.environ['WCG_TEST_DRIVERS'].split(',')
        for drv in drv_list:
            if drv == '':
                continue
            elif drv in drivers.GenericDriver.drivers:
                arg_driver.append(drv)
            else:
                log.error('Did not find driver %s in list of drivers (%s)',
                          repr(drv), ', '.join(drivers.GenericDriver.drivers))
                sys.exit(1)
    else:
        for drv in drivers.GenericDriver.drivers:
            arg_driver.append(drv)

    arg_lang = ArgList('--lang', [None, 'en', 'de'])
    arg_height = ArgList('--height', [None, 1.75])
    arg_initials = ArgList('--initials', [None, 'Tester'])
    arg_dates = ArgPairList('--begin-date', '2015-11-22',
                            '--end-date', ['2016-01-17', '2016-02-14',
                                           '2016-05-15'])
    arg_weight = ArgList('--weight', ['70-81', '75', '75+-5'])

    iterators = [
        arg_driver,
        arg_lang,
        arg_height,
        arg_initials,
        arg_dates,
        arg_weight,
    ]

    for no, args in enumerate(itertools.product(*iterators)):
        aa = []
        for a in args:
            aa.extend(a)
        yield check_args, no+1, aa


########################################################################


def check_args(no, args):
    common_args = [
    ]

    with open(os.path.join(tempdir, 'test.log'), 'a') as logfile:
        print('TESTCASE', no, file=logfile)

        argv = list(common_args)
        argv.extend(args)
        print('  argv', argv, file=logfile)
        pdf_fname = ('TESTCASE-%03d___%s.pdf' %
                     (no, '_'.join(argv).replace('.','_')))
        print('  ', pdf_fname, file=logfile)

        assert(isinstance(pdf_fname, str))

        pdf_path = os.path.join(tempdir, pdf_fname)
        argv.extend(['--output=%s' % pdf_path])
        print('  args', argv, file=logfile)
        try:
            main(argv=argv)
            assert(False)
        except SystemExit as se:
            if se.code == 0:
                pass
            else:
                raise

        # Check generated PDF file has a reasonable size
        osr = os.stat(pdf_path)
        assert(osr.st_size > 0)     # PDF file must be non-empty
        assert(osr.st_size >= 1024) # PDF file appears a bit too small

        print('  status', 'SUCCESS', file=logfile)


########################################################################
