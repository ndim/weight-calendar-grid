Summary
=======

The lowest threshold way to record your body weight is to use a
printed page of custom grid paper and make a pen mark on the page
every day.

Initial setup:

  1. Print a page with your grid.

  2. Hang printed page on wall or put it in similarly easily available
     space close to the scale.

  3. Keep a dedicated pen at that very location.

Daily:

  1. Step on scale and read the weight.

  2. Mark that day's weight on the page.

Every few weeks or months:

  1. Print a new page and replace the old page with it.

  2. Optionally, type the marked values into some computer file.

NOTE: The documentation is a bit out of date.

To print a page, create a PDF file with `wcg-cli` and print that.

Example for someone of 1.78m height and a weight of around 85kg:

    $ ./wcg-cli -o my-weight.pdf --height=1.78 --weight=80-90

Example for someone of  unspecified height and a weight of around 85kg:

    $ ./wcg-cli -o my-weight.pdf --weight=85+-5

Example for someone of 1.78m height and normal weight:

    $ ./wcg-cli -o my-weight.pdf --height=1.78

For detailed information on how to call `wcg-cli`, read the output of

    $ ./wcg-cli --help


Rationale
=========

I need a very low overhead way to record my weight to reliably do it.
However, just writing down a numerical value on paper does not help
much as I cannot immediately see how that value relates to the
previous ones.

Typing the value into a computer program and letting the program plot
the values helps, but is too much hassle. The same applies to
smartphone apps.

Recording values on common off the shelf grid paper does not work as
the 5x5mm or 1x1mm grids are not well suited for date and kg ranges.

So I need a custom type of grid paper to record my weight on. This
custom grid paper does multiple things:

  * I can immediately see how the last recorded value relates to the
    previous ones and reasonably estimate a trend.

  * Marking the current value is a matter of seconds and has
    instantanous results: The visual extrapolation is instantaneous.

  * If I want to keep longer term records on the computer, I have
    recorded values with 0.1kg precision which can easily be read from
    the diagram and then typed into the computer.

So as long as the scale can neither record the weight nor display the
graph, this turns out to be the best way to keep track of my weight.


Recording Details
=================

This program can plot recorded weight values into the grid paper it
prints.  For this to happen, you need to keep long term records of
your measured weights in a simple text file `foo.dat` where every line
looks as follows:

    # my weights

    # YYYY-MM-DD   kg
    2011-05-23     82.3
    2011-05-24     81.7
    2011-05-25     82.1
    2011-05-26     82.5

    2011-06-03     81.6
    2011-06-04     81.8
    2011-06-05     81.3
    2011-06-06     81.7

Feed this file to `wcg-cli` with the `--input=` option and play
around with the `--begin` date for an actual plot.  The `auto` weight
range might be useful.


GUI
===

The Gtk3 based GUI script `wcg-gui` is a definite Work In Progress.


Web Service
===========

A web service with an HTML5 webapp might be an interesting way to
supply many people with weight calendar grid PDFs for printing out
themselves.  We have nothing implemented yet in this department,
though.


Requirements
============

  * [Python3](https://www.python.org/)

  * pdflatex and TikZ if you want really nice looking PDFs

  * Gtk3 if you want to run the GUI

  * [cairo](http://cairographics.org/) and
    [pycairo](http://cairographics.org/pycairo/) if you want basic
    PDFs without pdflatex or if you want the GUI

  * [ReportLab](http://www.reportlab.com) if you want to hack on the
    ReportLab based PDF driver

  * [gettext](http://www.gnu.org/software/gettext/) for the translations


Build and Install
=================

After the `git clone`, run

    $ python3 setup.py compile_catalog
    $ python3 setup.py build

(We are working on hooking `compile_catalog` into `build`.)

After that, you can run `./wcg-cli` and `./wcg-gui` from the source
tree or install the `weight-calendar-grid` with

    $ python3 setup.py install

Run with `--help` for details on installing somewhere.


Development
===========

Debugging
---------

When running `wcg-cli`, you can set up the startup log level by
setting `WCG_LOG_LEVEL` like so:

    $ env WCG_LOG_LEVEL=verbose ./wcg-cli

Additional -q and -v parameters are optional and make the output one
level more quiet or more verbose, respectively.

Testing
-------

To run the set suite:

    $ python3 setup.py test

You can set a few environment variables to influence the tests:

  * WCG_TEST_KEEP=yes Keep around the files the tests generate.

  * WCG_TEST_DRIVERS=cairo,reportlab,tikz

    Only test the drivers listed here in the comprehensive tests as
    those tests are many and tikz/pdflatex runs SO much longer than
    the other drivers. The valid drivers are the same as listed by
	`wcg-cli --list-options`.

Translations
------------

  * After adding, changing or removing translated strings in the Python source code:

        $ python3 setup.py extract_messages
        $ python3 setup.py update_catalog

  * After updating a translation in
    `weightgrid/locale/${LANG}/LC_MESSAGES/weight-calendar-grid.po`,
    compile that file to its binary equivalent
    `weightgrid/locale/${LANG}/LC_MESSAGES/weight-calendar-grid.mo`:

        $ python3 setup.py compile_catalog

  * Create translation for a new language:

        $ python3 setup.py init_catalog --locale=${NEW_LANG}
