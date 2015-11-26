"""Misc. utility and common functions"""


########################################################################


import datetime
import math
import time


########################################################################


from . import drivers
from . import log


########################################################################


def read_plot_data(infile, kg_range, date_range,
                   history_mode):
    """If present, read plot data and adapt min_kg, max_kg"""
    (min_kg, max_kg) = kg_range
    (begin_date, end_date) = date_range
    plot_points = []

    if infile:
        log.verbose("Reading plot data from %s", infile.name)

        plot_begin  = None
        plot_end    = None

        for line in iter(infile):
            line = line.strip()
            if len(line) == 0 or line[0] == '#':
                continue
            line = line.split()

            date_str, kg_str = line[:2]
            ts = time.strptime(date_str, '%Y-%m-%d')
            plot_date = datetime.date(*ts[0:3])

            if (not plot_begin) or (plot_date < plot_begin):
                plot_begin = plot_date
            if (not plot_end) or (plot_date > plot_end):
                plot_end   = plot_date

            plot_kg = float(kg_str)

            log.debug('read plot point %s %5.2fkg', plot_date, plot_kg)
            plot_points.append((plot_date, plot_kg))

        log.verbose("Read %d plot points from %s",
                    len(plot_points), infile.name)

        # calculate moving average
        i = 0
        depth = 10
        depthm1 = 1.0 / depth
        q = []

        cur_date, plot_kg = plot_points[i]
        prev_date = None
        avg_points = []

        while True:
            if len(q) < depth:
                q.insert(0, plot_kg)
            else:
                q.pop()
                q.insert(0, plot_kg)

            qsum = 0.0
            qcnt = 0
            for qval in q:
                if qval != None:
                    qsum += qval
                    qcnt += 1
            if qcnt > 0:
                qavg = qsum / qcnt
                qual = qcnt * depthm1
            else:
                qavg = None
                qual = 0.0

            avg_points.append((cur_date, plot_kg, (qavg, qual)))

            prev_date = cur_date
            cur_date += datetime.timedelta(days=1)
            if cur_date > plot_end:
                break

            # next plot point if date is past current one
            if cur_date > plot_points[i][0]:
                i += 1

            # if date is exact match, set plot_kg to proper value, None otherwise
            if cur_date == plot_points[i][0]:
                _plot_date, plot_kg = plot_points[i]
            else:
                plot_kg = None

        plot_points = avg_points

        if (begin_date, end_date) == (None, None):
            log.debug("Setting (begin, end) to plot dates (%s, %s)",
                      plot_begin, plot_end)
            (begin_date, end_date) = (plot_begin, plot_end)

        # Adapt date range to allow for entering more data.
        # TODO: Implement "just plot old data" mode.
        if history_mode:
            if (end_date - begin_date).days >= 185:
                begin_date = get_latest_first(begin_date)
                end_date   = get_next_first(end_date)
            else:
                begin_date = get_latest_sunday(begin_date)
                end_date   = get_earliest_sunday(end_date)
        else:
            begin_date = get_latest_sunday(end_date - datetime.timedelta(days=10))
            end_date = begin_date + datetime.timedelta(days=8*7)
            plot_points = [ (d, w, a)
                            for d, w, a in plot_points
                            if begin_date <= d and d <= end_date ]
            d, _w, _a = plot_points[0]
            if d != begin_date:
                begin_date = get_latest_sunday(d)
                end_date = begin_date + datetime.timedelta(days=8*7)

        plot_min_kg = None
        plot_max_kg = None

        for _d, plot_kg, _a in plot_points:
            if plot_kg:
                if (not plot_max_kg) or (plot_kg > plot_max_kg):
                    plot_max_kg = plot_kg
                if (not plot_min_kg) or (plot_kg < plot_min_kg):
                    plot_min_kg = plot_kg

        if (not min_kg) or (plot_min_kg < min_kg):
            min_kg = plot_min_kg
        if (not max_kg) or (plot_max_kg > max_kg):
            max_kg = plot_max_kg

    filtered_points = [ (d, w, a)
                        for d, w, a in plot_points
                        if begin_date <= d and d <= end_date ]
    log.verbose("Date filtered plot points: %d", len(filtered_points))

    return ((min_kg, max_kg), (begin_date, end_date), filtered_points)


########################################################################


def parse_kg_range(kg_range):
    if kg_range == None:
        return (None, None)
    elif type(kg_range) == float:
        return (kg_range, kg_range)
    elif type(kg_range) == tuple:
        return kg_range


########################################################################


def generate_grid(height,
                  kg_range,
                  date_range,
                  infile,
                  driver_cls,
                  output_format,
                  outfile,
                  keep_tmp_on_error,
                  history_mode,
                  initials):

    """Generate the things to plot and hand them to the driver."""
    (begin_date, end_date) = date_range
    min_kg, max_kg = parse_kg_range(kg_range)

    kg_range, date_range, plot_points = read_plot_data(infile, (min_kg, max_kg),
                                                       (begin_date, end_date),
                                                       history_mode)

    min_kg, max_kg = kg_range

    begin_date, end_date = date_range

    if height:
        height_str = "%.2fm" % height
    else:
        height_str = "None"
    log.info("driver=%s output_format=%s height=%s initials=%s"
             % (repr(driver_cls.driver_name),
                repr(output_format), height_str,
                repr(initials)))

    if not output_format:
        output_format = driver_cls.driver_formats[0]

    # set up driver
    driver = driver_cls(height, (min_kg, max_kg),
                        (begin_date, end_date),
                        plot_points=plot_points,
                        keep_tmp_on_error=keep_tmp_on_error,
                        history_mode=history_mode,
                        initials=initials)

    driver.count_axes()

    driver.gen_outfile(outfile, output_format)


########################################################################
