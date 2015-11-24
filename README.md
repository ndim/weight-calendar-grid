Summary
=======

The lowest threshold way to record your body weight is to use a
printed page of custom grid paper and make a pen mark on the page
every day.

Initial setup:

  1. Print a page.
  2. Hang printed page on wall or put it in similarly available space.
  3. Keep a dedicated pen at that very location.

Daily:

  1. Step on scale and read the weight.
  2. Mark that day's weight on the page.

Every few weeks or months:

  1. Print a new page and replace the old page with it.
  2. Optionally, type the marked values into some computer file.

NOTE: The documentation is a bit out of date.

To print a page, create a PDF file with `plot-wcg` and print that.

Example for someone of 1.78m height and a weight of around 85kg:

    $ ./plot-wcg -o my-weight.pdf --height=1.78 --weight=80-90

Example for someone of  unspecified height and a weight of around 85kg:

    $ ./plot-wcg -o my-weight.pdf --weight=85+-5

Example for someone of 1.78m height and normal weight:

    $ ./plot-wcg -o my-weight.pdf --height=1.78

For detailed information on how to call `plot-wcg`, read the output of

    $ ./plot-wcg --help



Rationale
=========

I need a very low overhead way to record my weight to reliably do it.
However, just writing down a numerical value on paper does not help
much as I cannot immediately see how that value relates to the
previous ones.  Typing the value into the computer and letting the
computer plot the values helps, but has too much overhead.

So recording the weight on this custom grid paper does multiple
things:

  * I can immediately see how the last recorded value relates to the
    previous ones and guess a trend.

  * Marking the current value is a matter of seconds and has
    instantanous results.

  * If I want to keep longer term records on the computer, I have
    recorded values with 0.1kg precision which can easily be typed
    into the computer.

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

Feed this file to `plot-wcg` with the `--input=` option and play
around with the `--begin` date for an actual plot.  The `auto` weight
range might be useful.


GUI
===

The Gtk3 based GUI script `gui-wcg` is a definite Work In Progress.


Web Service
===========

A web service with an HTML5 webapp might be an interesting way to
supply many people with weight calendar grids. We have nothing
implemented yet in this department, though.


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

After the `git clone`, run `make`.

After that, you can run `./plot-wcg` and `./gui-wcg`.

Installing the software anywhere is not supported yet, so you have to
run the programs from the source tree.
