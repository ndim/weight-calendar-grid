########################################################################


import os
import sys
import subprocess
from unittest import TestCase


########################################################################


from ..gui import main


########################################################################


class TestGui(TestCase):

    def __test(self, args, expect_code=0, expect_stdout=None, expect_stderr=None):
        # The GObject/Gtk Magic does not let us call gui.main(args)
        # with the arguments to test, so we must call the GUI in a
        # separate process.
        with subprocess.Popen([sys.executable,
                               'gui-wcg'] + args,
                              stdin=subprocess.DEVNULL,
                              stderr=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              shell=False) as proc:
            try:
                outs, errs = proc.communicate(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
                outs, errs = proc.communicate(timeout=15)
            self.assertEqual(proc.returncode, expect_code)
            if expect_stderr != None:
                self.assertEqual(errs, expect_stderr)
            if expect_stdout != None:
                self.assertEqual(outs, expect_stdout)

    def test_001_version(self):
        self.__test(['--version'],
                    expect_stdout=b'gui-wcg (weight-calendar-grid) 0.1.1\n')

    def test_002_help(self):
        self.__test(['--help'])


########################################################################
