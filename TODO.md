Note that some of these TODOs have already been implemented.

  * Optionally print for non-color printers, probably without BMI.

  * baseline align the month/year range labels (cairo/tikz)

  * Add --date --date-range argument, possibly replacing -b and -e.

    --date=2011      from 2011-01-01 to 2011-12-31

    --date=2011-02   from 2011-02-01 to 2011-02-28

    --date=2011-02-01..2011-04-30   from 2011-02-01 to 2011-04-30
      Problem: Should be the same range char as in kg range.

  * Add --weight parameter.

    --weight=80.0-90.5
    --weight=86.5+4.0-6.0
    --weight=85.0+-5
    --weight=85

  * Add --height parameter. If not given, do not plot BMI or make BMI
    based guesses.

  * Time support for --plot-mode. Keep day axis in 8 week mode for
    manually marking values in non-plot-mode. Otherwise, allow
    plotting

      * showing every day in the grid, plotting every value

      * showing every weekend in the grid, plotting every value

      * showing every month in the grid, plotting every value

      * showing every year in the grid, plotting monthly summary
        values

    Similarly, keep kg range in nice mark-able range for non-plot-mode
    for noting down new values, allow smaller and larger kg ranges in
    plot-mode. [kg range implemented]

  * Pass the args Namespace object down to improve decision making
    deeper down.

  * Add --show-punch-holes: Show punch hole location.

  * Add --show-filing-info: Add dates to corners for easy retrieval
    from file.

  * Add --show-meta-info: Add meta information like the data file, the
    options, the driver used, etc.

  * Support different units for weight scale: lbs, or lbs and st.

  * Negotiation protocol between tick generator and page layouter as
    to how many kg and days can be reasonably displayed.

  * Move axis tick generation and style set use into common Axis
    class.

  * Make line widths such that 600dpi printers can better cope with
    them. E.g. a 0.1pt line is less than one 600dpi dot wide which
    does not work properly. Done, but needs verification.

  * Support quarter-BMI ticks:

      * labeled bold text bold line for .0

      * unlabeled thin line for .25

      * labeled thin line for .5

      * unlabeled thin line for 0.75
