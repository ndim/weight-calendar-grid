########################################################################


from io import StringIO
import os
import sys
from unittest import TestCase


########################################################################


from ..cmdline import main


########################################################################


class TestCmdline(TestCase):

    def __init__(self, *args, **kwargs):
        super(TestCmdline, self).__init__(*args, **kwargs)
        self.stderr = sys.stderr
        self.pdf_fname_template = 'TESTCASE-%s.pdf'

        # TODO: Make this configurable at runtime.
        self.keep_pdf_files = True
        self.keep_pdf_files = False

    def setUp(self):
        sys.stderr = StringIO()

    def tearDown(self):
        sys.stderr = self.stderr

    def ___test_main(self, args, expected_code=0):
        try:
            main(argv=args)
            self.assertFalse(True, "main() should have exited first")
        except SystemExit as e:
            self.assertEqual(e.code, expected_code)

    def __test_main(self, args, expected_code=0):
        with self.assertRaises(SystemExit) as cm:
            main(argv=args)
        self.assertEqual(cm.exception.code, expected_code)

    def __test_pdf(self, args, pdf_fname=None, expected_code=0):
        with open('test.log', 'a') as logfile:
            logfile.write('testing with file %s\n' % pdf_fname)
        self.assertIsInstance(pdf_fname, str)
        self.__test_main(args + ['--output=%s' % pdf_fname],
                         expected_code)

        # Check generated PDF file has a reasonable size
        osr = os.stat(pdf_fname)
        self.assertNotEqual(osr.st_size, 0)
        self.assertTrue(osr.st_size >= 1024,
                        msg="PDF file appears a bit too small")

        # Clean up generated PDF file
        if not self.keep_pdf_files:
            try:
                os.unlink(pdf_fname)
            except FileNotFoundError:
                pass

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

    def test_101_cairo(self):
        self.__test_pdf(['--driver=cairo',
                         '--lang=de',
                         '--initials=tester',
                         '--begin-date=2015-11-22',
                         '--end-date=2016-01-17',
                         '--height=1.75',
                         '--weight=70-81',
        ], self.pdf_fname_template % sys._getframe().f_code.co_name)

    def test_102_reportlab(self):
        self.__test_pdf(['--driver=reportlab',
                         '--lang=de',
                         '--initials=tester',
                         '--begin-date=2015-11-22',
                         '--end-date=2016-01-17',
                         '--height=1.75',
                         '--weight=70-81',
        ], self.pdf_fname_template % sys._getframe().f_code.co_name)

    def test_103_tikz(self):
        self.__test_pdf(['--driver=tikz',
                         '--lang=de',
                         '--initials=tester',
                         '--begin-date=2015-11-22',
                         '--end-date=2016-01-17',
                         '--height=1.75',
                         '--weight=70-81',
        ], self.pdf_fname_template % sys._getframe().f_code.co_name)

    def test_111_cairo(self):
        self.__test_pdf(['--driver=cairo',
                         '--lang=de',
                         '--initials=tester',
                         '--begin-date=2015-11-22',
                         '--end-date=2016-01-17',
                         '--weight=70-81',
        ], self.pdf_fname_template % sys._getframe().f_code.co_name)

    def test_112_reportlab(self):
        self.__test_pdf(['--driver=reportlab',
                         '--lang=de',
                         '--initials=tester',
                         '--begin-date=2015-11-22',
                         '--end-date=2016-01-17',
                         '--weight=70-81',
        ], self.pdf_fname_template % sys._getframe().f_code.co_name)

    def test_113_tikz(self):
        self.__test_pdf(['--driver=tikz',
                         '--lang=de',
                         '--initials=tester',
                         '--begin-date=2015-11-22',
                         '--end-date=2016-01-17',
                         '--weight=70-81',
        ], self.pdf_fname_template % sys._getframe().f_code.co_name)

    def test_121_cairo(self):
        self.__test_pdf(['--driver=cairo',
                         '--lang=en',
                         '--initials=tester',
                         '--begin-date=2015-11-22',
                         '--end-date=2016-01-17',
                         '--height=1.75',
                         '--weight=70-81',
        ], self.pdf_fname_template % sys._getframe().f_code.co_name)

    def test_122_reportlab(self):
        self.__test_pdf(['--driver=reportlab',
                         '--lang=en',
                         '--initials=tester',
                         '--begin-date=2015-11-22',
                         '--end-date=2016-01-17',
                         '--height=1.75',
                         '--weight=70-81',
        ], self.pdf_fname_template % sys._getframe().f_code.co_name)

    def test_123_tikz(self):
        self.__test_pdf(['--driver=tikz',
                         '--lang=en',
                         '--initials=tester',
                         '--begin-date=2015-11-22',
                         '--end-date=2016-01-17',
                         '--height=1.75',
                         '--weight=70-81',
        ], self.pdf_fname_template % sys._getframe().f_code.co_name)

    # TODO: Test plotting actual weight data.


########################################################################
