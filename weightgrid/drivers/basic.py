"""The output driver infrastructure"""


########################################################################
#
# TODO: Try to make 0.1kg lines easy to draw with.
# TODO: Support closer day spacing for periods longer than 8 weeks.
#
########################################################################


import collections
import datetime
import math
from pprint import pprint


########################################################################


import weightgrid
# from weightgrid import get_latest_first
# from weightgrid import get_next_first

import weightgrid.drivers
import weightgrid.log as log


########################################################################


class ClassDefinitionError(Exception):
    """Some class has been defined in a wrong way"""
    pass


########################################################################


class NoSuchDriverError(Exception):
    """No such driver class has been found"""
    pass


########################################################################


class DriverMetaClass(type):

    """Driver registry metaclass.

    Also checks for the basic driver API."""

    def __new__(mcs, clsname, bases, clsdict):
        cls = super(DriverMetaClass, mcs).__new__(mcs, clsname, bases, clsdict)
        if not hasattr(mcs, 'drivers'):
            mcs.drivers = {}

        # Check presence and type of some required driver member constants.
        # Does not check for API member functions.
        fields = {'driver_name': str,
                  'driver_formats': list,
                  }
        fields_present = 0
        for k, t in fields.items():
            if k in clsdict:
                if type(clsdict[k]) != t:
                    raise ClassDefinitionError(
                        "Member %s of class %s must be of type %s"
                        % (repr(k), repr(clsname), repr(t)))
                fields_present += 1

        if fields_present == len(fields): # Register actual driver class.
            driver_name = clsdict['driver_name']
            if driver_name in mcs.drivers:
                if mcs.drivers == cls:
                    pass # we have already been registered
                else:
                    raise RuntimeError(
                        "Driver %s (class %s) already stored in driver list"
                        % (driver_name, clsname))
            log.verbose("Registering %s driver %s", driver_name, clsname)
            mcs.drivers[driver_name] = cls
        elif fields_present == 0: # Ignore abstract base class.
            pass
        else: # Throw error at half-assed job.
            raise ClassDefinitionError(
                'Driver class %s must define all members %s.'
                % (repr(clsname), repr(fields.keys)))

        return cls

    def get_driver(mcs, drv):
        log.verbose('Looking up driver %s in %s', drv, mcs.drivers)
        if drv in mcs.drivers:
            return mcs.drivers[drv]
        if drv == None: # default driver
            # Prefer TikZ over Cairo
            for k in ['tikz', 'cairo']:
                if k in mcs.drivers:
                    return mcs.drivers[k]
            # If neither tikz nor cairo drivers work, choose random driver.
            # If there are no drivers... exception is OK.
            return list(mcs.drivers.values())[0] # This fails if no driver works
        raise NoSuchDriverError(drv)


########################################################################


def is_first_day_of_month(date):
    return (date.day == 1)

def is_last_day_of_month(date):
    return (date.month != (date + datetime.timedelta(days=1)).month)

def is_first_day_of_year(date):
    return (date.day == 1) and (date.month == 1)

def is_last_day_of_year(date):
    return (date.day == 31) and (date.month == 12)


########################################################################


class GenericDriver(object, metaclass=DriverMetaClass):

    """Abstract base class for output drivers

    TODO: Define @abstractmethod methods here instead of just defining the same functions in child classes.
    """


    def __init__(self, height, kg_range, date_range,
                 plot_points=None,
                 keep_tmp_on_error=False,
                 history_mode=False,
                 initials=None):

        (min_kg, max_kg) = kg_range
        (begin_date, end_date) = date_range
        super(GenericDriver, self).__init__()

        self.height = height
        self.ticks_day = {6: [], 5: [], 4: [], 3: [], 2: [], 1: [], 0: []}

        self.min_kg = min_kg
        self.max_kg = max_kg

        self.begin_date = begin_date
        self.end_date   = end_date

        self.show_bmi = (not (not height))
        self.history_mode = history_mode

        self.initials = initials

        if plot_points:
            self.plot_points = plot_points
        else:
            self.plot_points = []

        self.keep_tmp_on_error = keep_tmp_on_error


    def count_axes(self):
        self.fix_dimensions()
        self.__setup_axis_kg()
        if self.show_bmi:
            self.__setup_axis_bmi()
        self.__setup_axis_time()


    def __setup_axis_kg(self):
        """count up kg axis in steps of 0.1kg ('hectogram')"""
        min_kg, max_kg = self.min_kg, self.max_kg
        range_kg = self.range_kg

        ofs_long = self.overhang
        ofs_shrt = 0.0

        LABEL_NONE = 0
        LABEL_NORMAL = 1
        LABEL_BOLD = 2

        SHRT = 0
        LONG = 1

        def avp(length, line_width, label=LABEL_NONE):
            if   length == SHRT: ofs = ofs_shrt
            elif length == LONG: ofs = ofs_long
            return AxisValueParams(line_width= line_width,
                                   font_bold= (label == LABEL_BOLD),
                                   begin_ofs= self.sep_west - ofs,
                                   end_ofs=   self.sep_east - ofs,
                                   do_label= (label != LABEL_NONE))

        as5_1 = avp(LONG, 1.5, LABEL_BOLD)
        as1_1 = avp(LONG, 1.0, LABEL_NORMAL)
        as1_2 = avp(LONG, 0.5)
        as1_10 = avp(SHRT, 0.15)

        self.kg_fmt = "%.0f" # FIXME: Ugly global variable
        if   range_kg > 48:
            subdiv = 1
            styles = { 20: as5_1,  5: as1_1, 1: as1_2}
        elif range_kg > 43:
            subdiv = 1
            styles = { 5: as5_1,  1: as1_1}
        elif range_kg > 30:
            subdiv = 2
            styles = {10: as5_1,  2: as1_1, 1: as1_10}
        elif range_kg > 15:
            subdiv = 5
            styles = {25: as5_1,  5: as1_1, 1: as1_10}
        elif range_kg > 8:
            subdiv = 10
            styles = {50: as5_1,
                      10: as1_1,
                      5: as1_2,
                      1: as1_10}
        elif range_kg > 4:
            subdiv = 10
            styles = {10: avp(LONG, 1.5, LABEL_BOLD),
                      5:  avp(LONG, 1.0, LABEL_NORMAL),
                      1:  avp(LONG, 0.25)}
            self.kg_fmt = "%.1f"
        else:
            subdiv = 10
            styles = {10: avp(LONG, 1.5, LABEL_BOLD),
                      5:  avp(LONG, 1.0, LABEL_BOLD),
                      1:  avp(LONG, 0.25, LABEL_NORMAL)}
            self.kg_fmt = "%.1f"


        self.axis_kg = Axis(
            min=min_kg, max=max_kg,
            subdivisions=subdiv,
            styles=styles
            )


    def __setup_axis_time(self):
        log.verbose('__setup_axis_time from %s to %s (%d days = %d weeks + %d days)',
                    self.begin_date, self.end_date, self.days,
                    self.days / 7, self.days % 7)

        begin_ofs = self.sep_north - self.overhang
        end_ofs   = self.sep_south - self.overhang

        days = self.days

        if days <= 366:
            if days > 14*7:
                non_sunday_labels = False
                rot = 0
            elif days >= 65:
                non_sunday_labels = True
                rot = 90
            else:
                non_sunday_labels = True
                rot = 0
            weekday_p = AxisValueParams(
                do_label = non_sunday_labels,
                rotate_labels=rot,
                line_width=0.15,
                begin_ofs=begin_ofs,
                end_ofs=end_ofs)
            saturday_p = AxisValueParams(
                do_label = non_sunday_labels,
                rotate_labels=rot,
                line_width=0.50,
                font_bold=True,
                begin_ofs=begin_ofs,
                end_ofs=end_ofs)
            sunday_p = AxisValueParams(
                do_label=True,
                rotate_labels=rot,
                line_width=1.00,
                font_bold=True,
                begin_ofs=begin_ofs,
                end_ofs=end_ofs)

            styles = {
                0: weekday_p,
                1: weekday_p,
                2: weekday_p,
                3: weekday_p,
                4: weekday_p,
                5: saturday_p,
                6: sunday_p,
                }
            self.axis_time = TimeAxisDays(self.begin_date,
                                          self.end_date,
                                          styles=styles)
        else:
            bold = AxisValueParams(
                do_label=True,
                line_width=1.0,
                font_bold=True,
                begin_ofs=begin_ofs,
                end_ofs=end_ofs)

            # make space for year range label
            if self.begin_date.month > 10:
                self.begin_date = self.begin_date.replace(month=10, day=1)
            if self.end_date.month < 3:
                log.info("CHANGING END_DATE %s", self.end_date)
                assert(self.end_date.day == 1)
                self.end_date = self.end_date.replace(month=3)

            # wishing for Ada/VHDL like syntax:
            # (1 => foo, 12 => foo, others => bar)

            class NormAxisValueParams(AxisValueParams):
                def __init__(self):
                    super(NormAxisValueParams, self).__init__(
                        do_label=True,
                        line_width=0.25,
                        begin_ofs=begin_ofs,
                        end_ofs=end_ofs)

            styles = collections.defaultdict(NormAxisValueParams)
            styles[1] = bold
            styles[12] = bold

            self.axis_time = TimeAxisMonths(self.begin_date,
                                            self.end_date,
                                            styles=styles)


    def __setup_axis_bmi(self):

        min_kg = self.min_kg
        max_kg = self.max_kg
        height = self.height

        LABEL_NONE = 0
        LABEL_NORMAL = 1
        LABEL_BOLD = 2

        oh = self.overhang + 6.5

        def avp(lw, lc=0.5, label=LABEL_NONE):
            return AxisValueParams(line_width= lw,
                                   line_color= (1.0, 1.0-lc, 1.0-lc),
                                   font_bold= (label == LABEL_BOLD),
                                   begin_ofs= self.sep_west - oh,
                                   end_ofs=   self.sep_east - oh,
                                   font_color='red',
                                   do_label= (label != LABEL_NONE))

        hp2 = height**2
        hm2 = 1.0 / hp2

        range_bmi = self.range_kg * hm2

        if   range_bmi > 15.0:
            subdiv = 1
            styles = {5:  avp(lw=1.5, lc=0.6, label=LABEL_BOLD),
                      1:  avp(lw=1.0, lc=0.4, label=LABEL_NORMAL)}
        elif range_bmi >  8.0:
            subdiv = 2
            styles = {10: avp(lw=2.0, lc=0.6, label=LABEL_BOLD),
                      2:  avp(lw=1.5, lc=0.4, label=LABEL_NORMAL),
                      1:  avp(lw=0.6, lc=0.4)}
        elif range_bmi >  5.0:
            subdiv = 2
            styles = {10: avp(lw=2.0, lc=0.6, label=LABEL_BOLD),
                      2:  avp(lw=1.5, lc=0.6, label=LABEL_BOLD),
                      1:  avp(lw=1.0, lc=0.4, label=LABEL_NORMAL)}
        elif range_bmi >  1.0:
            subdiv = 5
            styles = {25: avp(lw=2.0, lc=0.6, label=LABEL_BOLD),
                      5:  avp(lw=1.5, lc=0.6, label=LABEL_BOLD),
                      1:  avp(lw=1.0, lc=0.4, label=LABEL_NORMAL)}
        else:
            subdiv = 10
            styles = {10: avp(lw=1.5, lc=0.6, label=LABEL_BOLD),
                      5:  avp(lw=1.5, lc=0.6, label=LABEL_BOLD),
                      1:  avp(lw=1.0, lc=0.4, label=LABEL_NORMAL)}

        self.axis_bmi = Axis(
            min=min_kg*hm2, max=max_kg*hm2,
            subdivisions=subdiv,
            styles=styles,
            expand_range=False,
            factor=hp2)


    @property
    def range_kg(self):
        return self.max_kg - self.min_kg


    @property
    def days(self):
        return (self.end_date - self.begin_date).days


    def _get_x(self, _day):
        raise AbstractMethodError()


    def _get_y(self, kg):
        raise AbstractMethodError()


    @property
    def delta_x_per_day(self):
        name = '___delta_x_per_day'
        if not hasattr(self, name):
            one_day = datetime.timedelta(days=1)
            x1 = self._get_x(self.begin_date+one_day)
            x0 = self._get_x(self.begin_date)
            setattr(self, name, x1-x0)
        return getattr(self, name)


    def gen_outfile(self, outfile, output_format):
        raise AbstractMethodError()

    def fix_dimensions(self):
        raise AbstractMethodError()


########################################################################


def color_name_to_rgb(color):
    if type(color) == str:
        return {
            'black':   (0,0,0),
            'red':     (1,0,0),
            'green':   (0,1,0),
            'blue':    (0,0,1),
            'yellow':  (1,1,0),
            'magenta': (1,0,1),
            'cyan':    (0,1,1),
            'white':   (1,1,1),
            }[color]
    else:
        return color


########################################################################


class UndefinedPropertyError(Exception):

    """Accessing undefined property of StaticAxisParams"""

    pass


########################################################################


class StaticAxisParams(object):

    """Define a set of parameters for an axis"""

    constant_list = ['begin_ofs', 'end_ofs',
                     'font_bold', 'font_color',
                     'line_color', 'line_width',
                     'hide_labels', 'rotate_labels']

    # Define defaults in subclasses if you want to.
    # defaults = {'font_bold': False}

    def __init__(self, **kwargs):
        super(StaticAxisParams, self).__init__()

        self.set_props = {}
        self.runtime_param_dict = {}

        for k, v in kwargs.items():
            if k in StaticAxisParams.constant_list:
                if k in self.set_props:
                    raise InternalLogicError("Already set")
                self.set_props[k] = v
            else:
                self.runtime_param_dict[k] = v

        for k in StaticAxisParams.constant_list:
            if ((k in self.set_props) or
                (hasattr(self, 'defaults') and k in self.defaults)):
                pass
            else:
                raise UndefinedPropertyError(
                    '%s object must be initialized setting %s'
                    % (repr(self.__class__.__name__),
                       repr(k)))


    def __getattribute__(self, key):
        """Simulate our special properties.

        Property names ending in _color will be converted from
        string to RGB tuple if necessary."""

        if key in ['defaults', 'runtime_param_dict', 'set_props']:
            return super(StaticAxisParams, self).__getattribute__(key)

        if key in StaticAxisParams.constant_list:
            if key in self.set_props:
                value = self.set_props[key]
                if key.endswith('_color'):
                    return color_name_to_rgb(value)
                else:
                    return value

        if hasattr(self, 'defaults') and (key in self.defaults):
            value = self.defaults[key]
            if key.endswith('_color'):
                return color_name_to_rgb(value)
            else:
                return value

        if key in self.runtime_param_dict:
            return self.runtime_param_dict[key]

        return super(StaticAxisParams, self).__getattribute__(key)


    def __getitem__(self, key):
        if key in self.runtime_param_dict:
            return self.runtime_param_dict[key]
        elif key in self.set_props:
            return self.set_props[key]
        elif hasattr(self, 'defaults') and key in self.defaults:
            return self.defaults[key]
        else:
            return getattr(self, key)


    def __setitem__(self, key, value):
        self.runtime_param_dict[key] = value


    def __str__(self):
        return('StaticAxisParams('
               'set_props={%s}, '
               'defaults={%s}, '
               'runtime_params={%s}, '
               'others={%s})'
               % (', '.join(["%s: %s" % (repr(k), repr(self[k]))
                             for k in sorted(self.set_props.keys())]),
                  ', '.join(["%s: %s" % (repr(k), repr(self.defaults[k]))
                             for k in sorted(self.defaults.keys())]),
                  ', '.join(["%s: %s" % (repr(k), repr(self.runtime_param_dict[k]))
                             for k in sorted(self.runtime_param_dict)]),
                  ', '.join(["%s: %s" % (repr(k), repr(self[k]))
                             for k in sorted(dir(self))
                             if ((not k.startswith('__'))
                                 and (k not in self.constant_list)
                                 and (k not in ['defaults',
                                                'constant_list',
                                                'runtime_param_dict',
                                                'set_props'])
                                 and (k not in self.runtime_param_dict))])))

    def __repr__(self):
        return self.__str__()


########################################################################


class AxisValueParams(StaticAxisParams):

    """Axis parameter set with some useful defaults"""

    defaults = {'font_bold': False,
                'font_color': 'black',
                'line_color': 'black',
                'hide_labels': False,
                'rotate_labels': 0}


########################################################################


class AbstractAxis(object):

    """Abstract Axis"""

    def __init__(self, begin, end, styles):
        super(AbstractAxis, self).__init__()
        self.__begin = begin
        self.__end = end
        self.__styles = styles

    @property
    def begin(self):
        return self.__begin

    @property
    def end(self):
        return self.__end

    @property
    def styles(self):
        return self.__styles

    def style(self, key):
        return self.__styles[key]

    def count(self, receive):
        raise AbstractMethodError()


########################################################################


class Axis(AbstractAxis):


    """Axis"""


    def __init__(self, min, max, styles=[], subdivisions=10,
                 expand_range=True, factor=1.0):
        super(Axis, self).__init__(min, max, styles)

        # Sort out category styling and which categories to use.

        log.verbose("Axis init: %d styles for %d subdivs",
                    len(self.styles), subdivisions)

        self._subdiv = subdivisions
        self._step = 1.0 / subdivisions
        if expand_range:
            self._min_i = int(math.floor(min * subdivisions))
            self._max_i = int(math.ceil(max * subdivisions))
        else:
            self._min_i = int(math.ceil(min * subdivisions))
            self._max_i = int(math.floor(max * subdivisions))
        assert(self._min_i < self._max_i)

        self._factor = factor


    def count(self, receive):
        i = self._min_i
        # print "Axis.count(%s)" % receive
        # pprint(self._styles)
        while True:
            for mod in reversed(sorted(self.styles.keys())):
                if (i % mod) == 0:
                    value = i * self._step
                    pos_value = value * self._factor
                    style = self.styles[mod]
                    if False:
                        if style:
                            sss = ''
                        else:
                            sss = ' (skipped)'
                        if self._factor == 1.0:
                            log.verbose("axis tick %2d=mod "
                                        "value=%04.2f%s",
                                        mod, value, sss)
                        else:
                            log.verbose("axis tick %2d=mod "
                                        "value=%04.2f pos_value=%5.3f%s",
                                        mod, value, pos_value, sss)
                    if style:
                        receive(style, value, pos_value)
                    break
            i += 1
            if i > self._max_i:
                break


########################################################################


class TimeAxis(AbstractAxis):


    """Abstract time axis"""


    def __init__(self, begin, end, styles=[]):
        super(TimeAxis, self).__init__(
            begin=begin, end=end, styles=styles)


    def count(self, receive):
        foo, style = list(self._styles.items())[0]
        receive(style, self.begin)
        receive(style, self.end)


########################################################################


class TimeAxisDays(TimeAxis):


    """Time axis with unit of days"""


    def __init__(self, begin, end, styles=[]):
        super(TimeAxisDays, self).__init__(
            begin=begin, end=end, styles=styles)


    def count(self, receiver):

        def send_month_range(begin, end):
            # log.debug("send_month_range: %s to %s", begin, end)
            receiver.month_range(begin, end)

        def send_year_range(begin, end):
            # log.debug("send_year_range: %s to %s", begin, end)
            receiver.year_range(begin, end)

        day = self.begin
        prev_day = None
        first_day_of_month = None
        first_day_of_year = None
        one_day_delta = datetime.timedelta(days=1)

        while True:
            # log.debug("day_tick: %s", day)
            receiver.day_tick(self.style(day.weekday()), day)

            if not first_day_of_month:
                first_day_of_month = day
            elif day.month != first_day_of_month.month:
                send_month_range(first_day_of_month, prev_day)
                first_day_of_month = day

            if not first_day_of_year:
                first_day_of_year = day
            elif day.year != first_day_of_year.year:
                send_year_range(first_day_of_year, prev_day)
                first_day_of_year = day

            prev_day = day
            day += one_day_delta
            if day > self.end:
                break

        send_month_range(first_day_of_month, prev_day)
        send_year_range(first_day_of_year, prev_day)


########################################################################


class Receiver(object):

    """Wraps actual driver with context and styles data"""

    def __init__(self, obj, ctx, range_style):
        self.obj = obj
        self.ctx = ctx
        self.range_style = range_style

    def day_tick(self, style, date):
        # log.debug("Receiver.day_tick %s", date)
        self.obj.render_day_tick(self.ctx, style, date)

    def week_tick(self, style, date):
        log.debug("Receiver.week_tick %s", date)
        self.obj.render_week_tick(self.ctx, style, date)

    def month_tick(self, style, date):
        log.debug("Receiver.month_tick %s", date)
        self.obj.render_month_tick(self.ctx, style, date)

    def month_range(self, begin, end):
        log.debug("Receiver.month_range %s (from %s to %s)",
                  begin.strftime('%Y-%m'), begin, end)
        self.obj.render_month_range(self.ctx, self.range_style, begin, end)

    def year_range(self, begin, end):
        log.debug("Receiver.year_range %s (from %s to %s)",
                  begin.strftime('%Y'), begin, end)
        self.obj.render_year_range(self.ctx, self.range_style, begin, end)


########################################################################


class TimeAxisMonths(TimeAxis):


    """Time axis with unit of months"""


    def count(self, receiver):

        def year_range(begin, end):
            real_end = weightgrid.get_next_first(end) - datetime.timedelta(days=1)
            receiver.year_range(begin, real_end)

        day = weightgrid.get_latest_first(self.begin)
        prev_day = None
        first_day_of_year = day

        while True:
            receiver.month_tick(self.style(day.month), day)

            if not first_day_of_year:
                first_day_of_year = day
            elif day.year != first_day_of_year.year:
                year_range(first_day_of_year, prev_day)
                first_day_of_year = day

            prev_day = day
            day = weightgrid.get_next_first(day)
            if day > self.end:
                break

        year_range(first_day_of_year, prev_day)


########################################################################


class PageDriver(GenericDriver):

    """Abstract base class for output drivers writing to an A4 page"""

    page_width = 297.0
    page_height = 210.0

    sep_west = 24.5
    sep_east = sep_west

    # sufficient space to keep ISO punch holes outside the grid
    # (12mm + 0.5 * 6mm +- 1mm)
    sep_north = 20.0

    sep_south = 24.0

    overhang = 1.0

    mark_delta = 0.7
    plot_mark_line_width = 1.25
    plot_line_width = 1.25
    plot_line_shorten = 1.6

    plot_stem_point_radius = 1.41 * mark_delta

    plot_color = (0.00, 0.60, 0.00)
    plot_mavg_hi_color = (0.00, 0.00, 0.80)
    plot_mavg_lo_color = (0.85, 0.85, 0.85)
    plot_mavg_q_cutoff = 0.30


    def __init__(self, *args, **kwargs):
        super(PageDriver, self).__init__(*args, **kwargs)
        self.month_range_level = 0


    def fix_date_range(self):
        begin_date, end_date = self.begin_date, self.end_date
        log.verbose("fix_date_range for (begin, end) dates (%s, %s)",
                    begin_date, end_date)

        if begin_date and end_date:
            log.verbose("using given begin_date %s and end_date %s",
                        begin_date, end_date)
        elif begin_date and (not end_date):
            end_date = begin_date + datetime.timedelta(days=8*7)
            log.verbose("using given begin_date %s", begin_date)
            log.info("using default end_date %s", end_date)
        elif (not begin_date) and end_date:
            begin_date = end_date - datetime.timedelta(days=8*7)
            log.verbose("using given end_date %s", end_date)
            log.info("using default begin_date %s", begin_date)
        elif (not begin_date) and (not end_date):
            begin_date = datetime.date.today()
            begin_date = weightgrid.get_latest_sunday(begin_date)
            end_date = begin_date + datetime.timedelta(days=8*7)
            log.info("using default begin_date %s and end_date %s",
                     begin_date, end_date)

        if (end_date - begin_date).days >= 5*7+1:
            log.verbose("keep begin_date %s and end_date %s",
                        begin_date, end_date)
        else:
            begin_date = weightgrid.get_latest_sunday(begin_date)
            end_date = begin_date + datetime.timedelta(days=8*7)
            log.verbose("extended date range to begin_date %s and end_date %s",
                        begin_date, end_date)

        log.verbose("fix_date_range for (begin, end) dates result (%s, %s)",
                    begin_date, end_date)
        self.begin_date, self.end_date = begin_date, end_date


    def fix_kg_range(self):
        """set/adapt min_kg and max_kg"""

        (min_kg, max_kg) = (self.min_kg, self.max_kg)
        if self.height:
            height_str = "%.2f" % self.height
        else:
            height_str = "None"
        log.verbose("fix_kg_range for (min_kg, max_kg) of (%s, %s) (height %s)",
                    min_kg, max_kg, height_str)

        if min_kg and max_kg:
            pass
        elif self.height and (not min_kg) and (not max_kg):
            # guess a default kg range around the BMI
            avg_bmi = 22.0
            bmi_dev =  1.6
            min_kg = (avg_bmi-bmi_dev) * self.height**2
            max_kg = (avg_bmi+bmi_dev) * self.height**2
        else:
            raise InternalLogicError()

        if self.history_mode:
            minimum_kg_range = 2.0
        else:
            minimum_kg_range = 8.0

        if (max_kg - min_kg) < minimum_kg_range:
            min_kg -= 0.7
            max_kg += 0.7

        if self.height:
            while (max_kg - min_kg) < minimum_kg_range:
                if   max_kg/self.height**2 >= 30: max_kg += 0.15
                elif max_kg/self.height**2 >= 25: max_kg += 0.50
                elif max_kg/self.height**2 >= 20: max_kg += 1.00
                else:                        max_kg += 1.50

                if   min_kg/self.height**2 <= 18: min_kg -= 0.25
                elif min_kg/self.height**2 <= 20: min_kg -= 0.50
                elif min_kg/self.height**2 <= 25: min_kg -= 1.00
                else:                        min_kg -= 1.50

        # round to multiples of round_val
        round_val = 0.5
        round_val = 1.0
        min_kg = round_val * int(math.floor(min_kg / round_val))
        max_kg = round_val * int(math.ceil(max_kg / round_val))

        assert(max_kg > min_kg)

        log.verbose("fix_kg_range for (min_kg, max_kg) of (%s, %s) (height %s)",
                    min_kg, max_kg, height_str)
        self.min_kg, self.max_kg = min_kg, max_kg


    def fix_dimensions(self):
        self.fix_date_range()
        self.fix_kg_range()
        return

        self.mm_per_day = (
            (self.page_width - self.sep_west - self.sep_east)
            /
            (self.days)
            )

        log.verbose("mm_per_day %.1fmm on paper between day lines!",
                    self.mm_per_day)
        log.verbose("mm_per_day %.1fmm on paper between weeks!",
                    7 * self.mm_per_day)

        if self.mm_per_day < 3.3:
            log.warn("Only %.1fmm on paper between day lines!",
                     self.mm_per_day)


        self.mm_per_hg = (
            (self.page_height - self.sep_north - self.sep_south)
            /
            (10 * self.range_kg)
            )

        log.verbose("mm_per_hg: %.2fmm on paper between 0.1kg lines!",
                    self.mm_per_hg)
        log.verbose("mm_per_hg: %.2fmm on paper between 0.5kg lines!",
                    5*self.mm_per_hg)
        log.verbose("mm_per_hg: %.2fmm on paper between 1.0kg lines!",
                    10*self.mm_per_hg)

        if self.mm_per_hg < 2.0:
            log.warn("Only %.2fmm on paper between 0.1kg lines!",
                     self.mm_per_hg)

        if 5*self.mm_per_hg < 3.0:
            log.warn("The 0.5kg lines are too close. Not drawing them.")

        if self.mm_per_hg < 1.0:
            log.warn("The 0.1kg lines are too close. Not drawing them.")


    def _get_x(self, day):
        eff_days = (day - self.begin_date).days
        eff_w = (self.page_width - self.sep_west - self.sep_east)
        return (self.sep_west + eff_w * eff_days / self.days)


    def render(self, ctx):
        self.render_beginning(ctx)

        if self.show_bmi:
            self.__render_axis_bmi(ctx)
        self.__render_axis_time(ctx)
        self.__render_axis_kg(ctx)
        self.__render_plot(ctx,
                           ((self.end_date - self.begin_date).days < 250) )
        if self.initials:
            self.render_initials(ctx)

        self.render_ending(ctx)


    def render_initials(self, ctx):
        raise AbstractMethodError()


    def __render_plot(self, ctx, draw_marks):
        kg_points = [
            (self._get_x(d), self._get_y(kg))
            for d, kg, _avg in self.plot_points
            if kg ]

        def avg_color(q):
            assert(0.0 <= q and q <= 1.0)

            # rescale q
            cutoff = self.plot_mavg_q_cutoff
            if    q < cutoff: q = cutoff
            else:             q = (q - cutoff) / (1.0 - cutoff)

            color_a = self.plot_mavg_lo_color
            color_b = self.plot_mavg_hi_color
            assert(len(color_a) == len(color_b))
            if  len(color_a) == 3:
                ar, ag, ab = color_a
                br, bg, bb = color_b
                return ( (1.0-q)*ar + q*br, (1.0-q)*ag + q*bg,
                         (1.0-q)*ab + q*bb, )
            elif len(color_a) == 4:
                ar, ag, ab, aa = color_a
                br, bg, bb, ba = color_b
                return ( (1.0-q)*ar + q*br, (1.0-q)*ag + q*bg,
                         (1.0-q)*ab + q*bb, (1.0-q)*aa + q*ba, )
            else:
                raise InternalLogicError()

        stems = [
            ( avg_color(aq),
              self._get_x(day),
              self._get_y(kg),
              self._get_y(avg),
              )
            for day, kg, (avg, aq) in self.plot_points
            if kg and avg and aq >= self.plot_mavg_q_cutoff
            ]

        if not draw_marks:
            for point in kg_points:
                self.render_plot_point(ctx, point)

        if True:
            p_aq, p_day, p_kg, p_avg = None, None, None, None
            for day, kg, (avg, aq) in self.plot_points:
                if (p_aq
                    and p_aq >= self.plot_mavg_q_cutoff
                    and aq >= self.plot_mavg_q_cutoff):
                    self.render_plot_mavg_segment(ctx,
                                                  (self._get_x(p_day),
                                                   self._get_y(p_avg)),
                                                  (self._get_x(day),
                                                   self._get_y(avg)),
                                                  avg_color(p_aq))
                p_aq, p_day, p_kg, p_avg = aq, day, kg, avg

        if draw_marks:
            for point in kg_points:
                self.render_plot_mark(ctx, point)

        if (not self.history_mode) or (self.days < 185):
            stem_point_color = avg_color(1.0)
            for color, x, y, ay in stems:
                self.render_plot_stem(ctx, (x, y, ay), color)
                self.render_plot_stem_point(ctx, (x, y), stem_point_color)

        if (not self.history_mode) or (self.days < 185):
            self.render_plot_value_line_begin(ctx, shorten_segments=draw_marks)
            p_day, p_x, p_y = None, None, None
            for day, kg, _a in self.plot_points:
                if kg:
                    x = self._get_x(day)
                    y = self._get_y(kg)
                    if p_day and (day - p_day).days == 1:
                        self.render_plot_value_line_segment(ctx,
                                                            (p_x, p_y),
                                                            (x, y))
                    p_day, p_x, p_y = day, x, y
            self.render_plot_value_line_end(ctx)


    def render_plot_value_line_begin(self, ctx, shorten_segments):
        pass

    def render_plot_value_line_end(self, r):
        pass

    def render_plot_value_line_segment(self, ctx, point1, point2):
        (x1, y1) = point1
        (x2, y2) = point2
        raise AbstractMethodError()

    def render_plot_stem_point(self, ctx, point, color):
        (x, y) = point
        raise AbstractMethodError()

    def render_plot_mavg_segment(self, ctx, point1, point2, color):
        (x1, y1) = point1
        (x2, y2) = point2
        raise AbstractMethodError()

    def render_plot_stem(self, ctx, coords, color):
        (x, y, ay) = coords
        raise AbstractMethodError()

    def render_plot_point(self, ctx, point):
        (x, y) = point
        raise AbstractMethodError()

    def render_plot_mark(self, ctx, point):
        (x, y) = point
        raise AbstractMethodError()


    def render_beginning(self, ctx):
        pass


    def render_ending(self, ctx):
        pass


    def render_month_range(self, ctx, style, begin, end):
        self.month_range_level = 1

        days = (end - begin).days
        if   days > 6: # range should be wide enough for longest name of month
            label_str = begin.strftime('%B')
        elif days >= 3: # shortened name of month
            label_str = begin.strftime('%b')
        elif days >= 2: # number of month
            label_str = begin.strftime('%m')
        else: # no month label at all
            label_str = None

        self.render_calendar_range(ctx, (begin, end),
                                   (is_first_day_of_month(begin),
                                    is_last_day_of_month(end)),
                                   self.month_range_level,
                                   label_str, style)
        self.render_calendar_range(ctx, (begin, end),
                                   (is_first_day_of_month(begin),
                                    is_last_day_of_month(end)),
                                   self.month_range_level,
                                   label_str, style,
                                   north=True)


    def render_year_range(self, ctx, style, begin, end):

        days = (end - begin).days
        if days > 14:
            label_str = str(begin.year)
        else:
            label_str = None

        self.render_calendar_range(ctx, (begin, end),
                                   (is_first_day_of_year(begin),
                                    is_last_day_of_year(end)),
                                   self.month_range_level+1,
                                   label_str, style,
                                   north=False)
        self.render_calendar_range(ctx, (begin, end),
                                   (is_first_day_of_year(begin),
                                    is_last_day_of_year(end)),
                                   self.month_range_level+1,
                                   label_str, style,
                                   north=True)


    def __render_axis_time(self, ctx):

        range_style = AxisValueParams(
            line_width=0.5,
            begin_ofs=PageDriver.sep_west - PageDriver.overhang - 6.0,
            end_ofs=  PageDriver.sep_east - PageDriver.overhang - 6.0
            )

        self.render_comment(ctx, 'day tick lines and labels')
        self.render_time_begin(ctx)
        self.axis_time.count(Receiver(self, ctx, range_style))
        self.render_time_end(ctx)


    def render_time_begin(self, ctx):
        pass

    def render_time_end(self, ctx):
        pass


    def render_day_tick(self, ctx, style, date):
        label_str = date.strftime("%d")
        self.time_tick_id_fmt = "%Y-%m-%d"
        id_str = date.strftime(self.time_tick_id_fmt)
        self.render_time_tick(ctx, style, date, label_str, id_str)


    def render_month_tick(self, ctx, style, date):
        label_str = date.strftime("%b")[0]
        self.time_tick_id_fmt = "%Y-%m"
        id_str = date.strftime(self.time_tick_id_fmt)
        self.render_time_tick(ctx, style, date, label_str, id_str)


    def render_calendar_range(self, ctx, date_range, is_first_last,
                              level, label_str, p, north=False):
        (begin_date, end_date) = date_range
        (is_begin_first, is_end_last) = is_first_last
        raise AbstractMethodError()


    def __render_axis_bmi(self, ctx):
        self.render_axis_bmi_begin(ctx)

        def foo(params, bmi, kg):
            self.render_axis_bmi_tick(ctx,
                                      self._get_y(kg), bmi, "%.1f" % bmi,
                                      params)

        self.axis_bmi.count(foo)

        self.render_axis_bmi_end(ctx)


    def __render_axis_kg(self, ctx):
        self.render_axis_kg_begin(ctx)

        def foo(params, kg, *args):
            self.render_axis_kg_tick(ctx, self._get_y(kg),
                                     self.kg_fmt % kg, params)
        self.axis_kg.count(foo)

        self.render_axis_kg_end(ctx)


    def render_comment(self, ctx, msg):
        pass


########################################################################
