########################################################################


import os
import sys
import subprocess
from unittest import TestCase


########################################################################


from ..gui import main
from ..version import package_name, package_version


########################################################################


class TestGui(TestCase):

    def test_000_nothing(self):
        pass

    def __test(self, args, expect_code=0, expect_stdout=None, expect_stderr=None):
        # The GObject/Gtk Magic does not let us call gui.main(args)
        # with the arguments to test, so we must call the GUI in a
        # separate process.
        with subprocess.Popen([sys.executable,
                               'wcg-gui'] + args,
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
                self.assertEqual(errs.decode(), expect_stderr)
            if expect_stdout != None:
                self.assertEqual(outs.decode(), expect_stdout)

    def test_001_version(self):
        self.__test(['--version'],
                    expect_stdout=('wcg-gui (%s) %s\n' %
                                   (package_name, package_version)))

    def test_002_help(self):
        self.__test(['--help'])


########################################################################
