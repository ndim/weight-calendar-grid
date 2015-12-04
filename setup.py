#!/usr/bin/python3

########################################################################

from setuptools import setup, find_packages

from os      import chdir
from os.path import abspath, dirname

########################################################################

chdir(dirname(abspath(__file__)))

########################################################################

version_ns_global, version_ns_local = {}, {}
with open('weightgrid/version.py') as f:
    exec(f.read(), version_ns_global, version_ns_local)

class Version(object): pass
version = Version()
version.__dict__ = version_ns_local

########################################################################

with open('README.md') as readme_file:
    long_description = readme_file.read()

########################################################################

setup(
    name=version.package_name,
    version=version.package_version,
    description='print a grid on sheet of paper and mark your weight every day',
    long_description=long_description,
    url='https://github.com/ndim/weight-calendar-grid',
    author='Hans Ulrich Niedermann',
    author_email='hun@n-dimensional.de',
    license='MIT',
    packages=find_packages(exclude=[
        '*.tests',
    ]),
    install_requires=[
        'PyYAML',
    ],
    package_data={
        '': [
            '*.md',
            'LICENSE',
        ],
        'weightgrid': [
            '*.png',
            'locale/weight-calendar-grid.pot',
            'locale/*/LC_MESSAGES/*.mo',
        ],
    },
    include_package_data=True,
    extras_require={
        'GUI': ['cairo'],
        'PDF-reportlab': ['reportlab'],
        'PDF-pdflatex': ['pdflatex', 'TikZ'],
    },
    entry_points = {
        'console_scripts': [
            'wcg-cli=weightgrid.cli:main',
        ],
        'gui_scripts': [
            'wcg-gui=weightgrid.gui:main',
        ],
    },
    setup_requires = [
        'polib',
        'Babel>=1.3',
    ],
    test_suite='nose.collector',
    tests_require=['nose'],
    zip_safe=False
)

########################################################################
