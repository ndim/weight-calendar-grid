Note that some of these TODOs may have been implemented already.

  * Separate handling of UI and output translations in the code so
    that we can have the UI in a language other than the output grid
    language.

  * Separate translations of UI strings and output grid strings into
    disjunct text domains?

  * Write a web app serving PNGs and PDFs and allowing users to get
    grids for their data without locally running any special
    software. This requires a few things:

      1. Move ReportLab driver from drawing onto Canvas to defining a
         Drawing object.

      2. Have ReportLab driver generate PNG and possibly SVG in
         addition to PDF.

      3. Produce PNGs and PDFs via WSGI for inclusion into web server.

      4. Write web app using the PNGs and PDFs generated via WSGI.

  * Add reasonable logic for choosing the best quality driver for a
	given output format like PNG and PDF.

  * Optionally print for non-color printers, probably without BMI.

  * Rename Python package from `weightgrid` to `weight_cal_grid` or
    something else similarly containing the calendar word as well.

  * baseline align the month/year range labels (cairo/tikz)

  * Add `--date` `--date-range` argument, possibly replacing `-b` and `-e`.

    `--date=2011`      from 2011-01-01 to 2011-12-31

    `--date=2011-02`   from 2011-02-01 to 2011-02-28

    `--date=2011-02-01..2011-04-30`   from 2011-02-01 to 2011-04-30
      Problem: Should be the same range char as in kg range.

  * Time support for `--plot-mode`. Keep day axis in 8 week mode for
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

  * Add `--show-punch-holes`: Show punch hole location.

  * Add `--show-filing-info`: Add dates to corners for easy retrieval
    from file.

  * Add `--show-meta-info`: Add meta information like the data file, the
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
