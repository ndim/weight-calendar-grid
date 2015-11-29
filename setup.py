#!/usr/bin/python3


from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(name='weight-calendar-grid',
      version='0.2.0',
      description='print a grid on sheet of paper and mark your weight every day',
      long_description=readme(),
      url='https://github.com/ndim/weight-calendar-grid',
      author='Hans Ulrich Niedermann',
      author_email='hun@n-dimensional.de',
      license='MIT',
      packages=[
          'weightgrid',
          'weightgrid.drivers',
      ],
      install_requires=[
          'PyYAML',
      ],
      package_data={
          '': [
              '*.md',
              'LICENSE',
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
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=False)
