########################################################################


from io import StringIO
import itertools
import os
import sys
import tempfile
from unittest import TestCase


########################################################################


from ..cmdline import main


########################################################################


tempdir = None

def setup():
    global tempdir
    tempdir = tempfile.mkdtemp(prefix='weight-calendar-grid',
                               suffix='.test-output')

def teardown():
    global tempdir
    assert(os.path.isdir(tempdir))
    for fname in os.listdir(tempdir):
        os.unlink(os.path.join(tempdir, fname))
    os.rmdir(tempdir)
    tempdir = None


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

    def __test_main(self, args, expected_code=0):
        with self.assertRaises(SystemExit) as cm:
            main(argv=args)
        self.assertEqual(cm.exception.code, expected_code)

    def __test_pdf(self, args, pdf_fname=None, expected_code=0):
        with open(os.path.join(tempdir, 'test.log'), 'a') as logfile:
            print('testing with file', pdf_fname, file=logfile)

        pdf_path = os.path.join(tempdir, pdf_fname)
        self.assertIsInstance(pdf_fname, str)
        self.__test_main(args + ['--output=%s' % pdf_path],
                         expected_code)

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
        self.__test_main(['--version'])

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


def test_comprehensive():
    # try all combinations of the following arguments

    arg_driver = ArgList('--driver')
    arg_driver.append('cairo')
    arg_driver.append('reportlab')
    arg_driver.append('tikz')

    arg_lang = ArgList('--lang', [None, 'en', 'de'])
    arg_height = ArgList('--height', [None, 1.75])
    arg_initials = ArgList('--initials', [None, 'Tester'])

    iterators = [
        arg_driver,
        arg_lang,
        arg_height,
        arg_initials,
    ]

    for no, args in enumerate(itertools.product(*iterators)):
        aa = []
        for a in args:
            aa.extend(a)
        yield check_args, no+1, aa


########################################################################


def check_args(no, args):
    common_args = [
        '--begin-date=2015-11-22',
        '--end-date=2016-01-17',
        '--weight=70-81',
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
