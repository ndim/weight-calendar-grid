"""Driver infrastructure for loading and finding drivers

This module loads all drivers which can actually be loaded on this
system.

Afterwards, you can print the list of drivers or get the driver class
you want.
"""


########################################################################


import datetime
import importlib
import sys


########################################################################


import weightgrid.log as log
from weightgrid.drivers.basic import GenericDriver


########################################################################


def get_driver(drv):
    """Find driver class by name"""
    return GenericDriver.get_driver(drv)


########################################################################


def print_driver_list(outfile=None):
    """Print driver list to given output file (or stdout)"""
    if not outfile:
        outfile = sys.stdout
    print("List of output drivers:", file=outfile)
    for drv in GenericDriver.drivers:
        print("   ", "driver", drv, file=outfile)
        formats = GenericDriver.drivers[drv].driver_formats
        default_fmt = formats[0]
        for fmt in sorted(formats):
            if fmt == default_fmt:
                print("   ", "   ", "format", fmt, '(driver default)', file=outfile)
            else:
                print("   ", "   ", "format", fmt, file=outfile)


########################################################################


def __load_drivers():

    for driver_module_name in ['Cairo', 'TikZ']:
        try:
            importlib.import_module('.'.join([__name__, driver_module_name]), __name__)
        except ImportError as e:
            log.warn("Could not load %s driver",
                     repr(driver_module_name),
                     exc_info=True)

    if len(GenericDriver.drivers) == 0:
        log.error("Error: No drivers found.")
        sys.exit(13)


__load_drivers()
del __load_drivers


########################################################################