"""The Cairo driver"""


########################################################################


import cairo
import datetime
import math
from pprint import pprint


########################################################################


import weightgrid
import weightgrid.drivers
from weightgrid.drivers.basic import PageDriver
import weightgrid.log as log


########################################################################


pt_in_mm = 25.4 / 72


########################################################################


class OutputFormatMetaClass(type):

    """Metaclass for registering different cairo output formats"""

    def __new__(mcs, clsname, bases, clsdict):
        cls = super(OutputFormatMetaClass, mcs).__new__(mcs, clsname, bases, clsdict)
        if not hasattr(mcs, 'formats'):
            mcs.formats = {}
        #print "mcs", mcs
        #print "cls", cls
        #print "clsname", clsname
        #print "bases", bases
        #print "clsdict", clsdict
        if 'name' in clsdict:
            fmt_name = clsdict['name']
            assert(fmt_name not in mcs.formats)
            log.verbose("Registering %s cairo output format %s", fmt_name, clsname)
            mcs.formats[fmt_name] = cls

            if 'default' in clsdict and clsdict['default'] == True:
                if hasattr(mcs, 'default_format'):
                    raise weightgrid.InternalLogicError("default_format already set to %s (new: %s)" % (mcs.default_format, fmt_name))
                mcs.default_format = fmt_name
        return cls

    def get_format(mcs, fmt):
        log.verbose('Looking up cairo output format %s', fmt)
        return mcs.formats[fmt]


########################################################################


class BaseOutputFormat(object, metaclass=OutputFormatMetaClass):

    """Abstract base class for cairo output formats"""

    pt_to_mm = 72 / 25.4

    def __init__(self, outfile, drv):
        super(BaseOutputFormat, self).__init__()
        self.outfile = outfile
        self.font_face = drv.font_face
        self.page_width = drv.page_width
        self.page_height = drv.page_height

    def open(self):
        pass

    def close(self):
        pass

    def get_context(self):
        return self.ctx


########################################################################


class PDFOutputFormat(BaseOutputFormat):

    """Write cairo output to PDF file"""

    name = 'pdf'
    default = True

    def open(self):
        self.sfc = cairo.PDFSurface(self.outfile,
                                    self.page_width  * self.pt_to_mm,
                                    self.page_height * self.pt_to_mm)
        self.ctx = cairo.Context(self.sfc)
        self.ctx.scale(self.pt_to_mm, self.pt_to_mm)
        self.ctx.set_source_rgb(0.0, 0.0, 0.0)
        self.ctx.select_font_face(self.font_face)
        self.ctx.set_font_size(10 * pt_in_mm)

    def close(self):
        self.sfc.show_page()


########################################################################


class EPSOutputFormat(BaseOutputFormat):

    """Write cairo output to EPS file"""

    name = 'eps'

    def open(self):
        self.sfc = cairo.PSSurface(self.outfile,
                                   self.page_width  * self.pt_to_mm,
                                   self.page_height * self.pt_to_mm)
        self.sfc.set_eps(True)
        self.ctx = cairo.Context(self.sfc)
        self.ctx.scale(self.pt_to_mm, self.pt_to_mm)
        self.ctx.set_source_rgb(0.0, 0.0, 0.0)
        self.ctx.select_font_face(self.font_face)
        self.ctx.set_font_size(10 * pt_in_mm)

    def close(self):
        self.sfc.show_page()


########################################################################


class SVGOutputFormat(BaseOutputFormat):

    """Write cairo output to SVG file"""

    name = 'svg'

    def open(self):
        self.sfc = cairo.SVGSurface(self.outfile,
                                    self.page_width  * self.pt_to_mm,
                                    self.page_height * self.pt_to_mm)
        self.ctx = cairo.Context(self.sfc)
        self.ctx.scale(self.pt_to_mm, self.pt_to_mm)
        self.ctx.set_source_rgb(0.0, 0.0, 0.0)
        self.ctx.select_font_face(self.font_face)
        self.ctx.set_font_size(10 * pt_in_mm)

    def close(self):
        self.sfc.finish()


########################################################################


class PNGOutputFormat(BaseOutputFormat):

    """Write cairo output to PNG file"""

    name = 'png'

    def open(self):
        self.sfc = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                      int(self.page_width  * self.pt_to_mm * 2),
                                      int(self.page_height * self.pt_to_mm * 2))
        self.ctx = cairo.Context(self.sfc)
        self.ctx.scale(self.pt_to_mm * 2, self.pt_to_mm * 2)
        self.ctx.set_source_rgb(1.0, 1.0, 1.0)
        self.ctx.paint()
        self.ctx.set_source_rgb(0.0, 0.0, 0.0)
        self.ctx.select_font_face(self.font_face)
        self.ctx.set_font_size(10 * pt_in_mm)

    def close(self):
        self.sfc.write_to_png(self.outfile)


########################################################################


class CairoOutputFormat(BaseOutputFormat):

    """Write cairo output to on-screen window or other cairo contexts"""

    name = 'CAIRO'

    def open(self):
        self.ctx = self.outfile
        self.ctx.set_source_rgb(0.0, 0.0, 0.0)
        self.ctx.select_font_face(self.font_face)
        self.ctx.set_font_size(8 * pt_in_mm)


########################################################################


format_keys = sorted(BaseOutputFormat.formats.keys())
format_keys.remove(BaseOutputFormat.default_format)
format_keys.remove(CairoOutputFormat.name)
format_list = [ BaseOutputFormat.default_format ] + format_keys


########################################################################


class CairoDriver(PageDriver):


    """Cairo driver with misc output formats"""


    driver_name = 'cairo'
    driver_formats = format_list


    font_face = 'sans'
    font_face = 'Bitstream Vera Sans'
    font_face = 'Latin Modern Sans Demi Cond' # has no bold

    # Looks VERY similar to \\sffamily. Coincidence?
    font_face = 'Latin Modern Sans'


    def _get_y(self, kg):
        y0 = self.page_height - self.sep_south
        eff_h = (self.page_height - self.sep_north - self.sep_south)
        return y0 - eff_h * (kg - self.min_kg) / self.range_kg


    def gen_outfile(self, outfile, output_format):
        pt_to_mm = 72/25.4

        fmt_cls = BaseOutputFormat.get_format(output_format)
        fmt = fmt_cls(outfile, self)
        fmt.open()

        ctx = fmt.get_context()
        self.render(ctx)

        fmt.close()


    def __render_text_init(self, ctx, x, y, rotate, bold, italic):
        ctx.save()

        if bold: cairo_bold = cairo.FONT_WEIGHT_BOLD
        else:    cairo_bold = cairo.FONT_WEIGHT_NORMAL

        # oblique is not supported here
        if italic: cairo_slant = cairo.FONT_SLANT_ITALIC
        else:      cairo_slant = cairo.FONT_SLANT_NORMAL

        ctx.select_font_face(self.font_face, cairo_slant, cairo_bold)

        ctx.translate(x, y)
        ctx.rotate(-rotate*math.pi/180)


    def __render_center_text(self, ctx, x, y, text_str,
                             rotate=0, bold=False, italic=False):
        self.__render_text_init(ctx, x, y, rotate, bold, italic)
        [tw, th] = ctx.text_extents(text_str)[2:4]

        # FIXME: Properly, consistently fill background before showing text.
        ctx.save()
        ctx.rectangle(-0.5*tw, -0.5*th, tw, th)
        ctx.set_source_rgba(1.0, 1.0, 1.0, 0.8)
        ctx.fill()
        ctx.restore()

        ctx.move_to(- 0.5*tw, +0.5*th)
        ctx.show_text(text_str)
        ctx.restore()


    def __render_left_text(self, ctx, x, y, text_str,
                           rotate=0, bold=False, italic=False):
        self.__render_text_init(ctx, x, y, rotate, bold, italic)
        [tw, th] = ctx.text_extents(text_str)[2:4]
        ctx.move_to(1.0, +0.5*th)
        ctx.show_text(text_str)
        ctx.restore()


    def __render_right_text(self, ctx, x, y, text_str,
                            rotate=0, bold=False, italic=False):
        self.__render_text_init(ctx, x, y, rotate, bold, italic)
        [tw, th] = ctx.text_extents(text_str)[2:4]
        ctx.move_to(-1.0*tw-1.0, +0.5*th)
        ctx.show_text(text_str)
        ctx.restore()


    def __render_north_text(self, ctx, x, y, text_str,
                            rotate=0, bold=False, italic=False):
        self.__render_text_init(ctx, x, y, rotate, bold, italic)
        [tw, th] = ctx.text_extents(text_str)[2:4]
        ctx.move_to(-0.5*tw, +1.0) # -2.0+1.0*th)
        ctx.show_text(text_str)
        ctx.restore()


    def __render_south_text(self, ctx, x, y, text_str,
                            rotate=0, bold=False, italic=False):
        self.__render_text_init(ctx, x, y, rotate, bold, italic)
        [tw, th] = ctx.text_extents(text_str)[2:4]
        ctx.move_to(-0.5*tw, +1.0)
        ctx.show_text(text_str)
        ctx.restore()


    def render_beginning(self, ctx):
        # Paint page background white
        ctx.save()
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.rectangle(0, 0, self.page_width, self.page_height)
        ctx.fill()
        ctx.restore()


    def render_ending(self, ctx):
        if False:
            self.__render_driver_name(ctx)

        if False:
            self.__render_hexdigest(ctx)

        if False:
            self.__render_punch_holes(ctx)


    def __render_hexdigest(self, ctx):
        ctx.save()
        ctx.set_source_rgba(0.00, 0.00, 0.00, 0.50)
        self.__render_center_text(ctx, 3, 0.5*self.page_height, prog_hexdigest, 90)
        self.__render_center_text(ctx, self.page_width-3, 0.5*self.page_height, prog_hexdigest, 90)
        ctx.restore()


    def __render_driver_name(self, ctx):
        ctx.save()
        ctx.set_source_rgba(0.00, 0.00, 0.00, 0.50)
        dx, dy = 4, 4
        self.__render_south_text(ctx,                 dx,                  dy,
                                 self.driver_name,  45)
        self.__render_south_text(ctx, self.page_width-dx,                  dy,
                                 self.driver_name, -45)
        self.__render_north_text(ctx, self.page_width-dx, self.page_height-dy,
                                 self.driver_name,  45)
        self.__render_north_text(ctx,                 dx, self.page_height-dy,
                                 self.driver_name, -45)
        ctx.restore()


    def __render_punch_holes(self, ctx):
        ctx.save()
        ctx.translate(0.5 * self.page_width, 12.0)
        self.__render_punch_hole(ctx, +40)
        self.__render_punch_hole(ctx, -40)
        ctx.restore()


    def __render_punch_hole(self, ctx, x):
        ctx.save()
        ctx.translate(x, 0)
        ctx.new_sub_path()
        ctx.arc(0.0, 0.0, 7.0, 0.0, 2 * math.pi)
        ctx.new_sub_path()
        ctx.arc(0.0, 0.0, 3.0, 0.0, 2 * math.pi)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.set_source_rgba(1.00, 0.00, 1.00, 0.05)
        ctx.fill_preserve()
        ctx.set_source_rgba(1.00, 0.00, 1.00, 0.20)
        ctx.set_line_width(0.7)
        ctx.stroke()
        ctx.restore()


    def __draw_plot_tick_circle(self, ctx, x, y):
        ctx.new_sub_path()
        ctx.arc(x, y, 0.9 * self.mark_delta,
               0.0, 2.0 * math.pi)


    def __draw_plot_tick_diag(self, ctx, x, y):
        md = self.mark_delta
        ctx.save()
        ctx.translate(x, y)
        ctx.move_to(-md, -md)
        ctx.line_to(+md, +md)
        ctx.move_to(+md, -md)
        ctx.line_to(-md, +md)
        ctx.restore()


    def __draw_plot_tick_cross(self, ctx, x, y):
        md = self.mark_delta * 1.41
        ctx.save()
        ctx.translate(x, y)
        ctx.move_to(-md,   0)
        ctx.line_to(+md,   0)
        ctx.move_to(  0, -md)
        ctx.line_to(  0, +md)
        ctx.restore()


    def render_plot_value_line_begin(self, ctx, shorten_segments):
        ctx.save()
        self.shorten_value_line_segments = shorten_segments


    def render_plot_value_line_end(self, ctx):
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_width(self.plot_line_width * pt_in_mm)
        ctx.set_source_rgb(*self.plot_color)
        ctx.stroke()
        ctx.restore()


    def render_plot_value_line_segment(self, ctx, point1, point2):
        (x1, y1) = point1
        (x2, y2) = point2
        if self.shorten_value_line_segments:
            # shorten the line at start and finish
            dx, dy = x2-x1, y2-y1
            dr = math.sqrt(dx*dx + dy*dy)
            f = self.plot_line_shorten/dr
            if f < 0.5:
                sx, sy = f*dx, f*dy
                ctx.move_to(x1+sx, y1+sy)
                ctx.line_to(x2-sx, y2-sy)
        else:
            ctx.move_to(x1, y1) # skip move_to() if we are already at (x1, y1)?!
            ctx.line_to(x2, y2)


    def render_plot_stem_point(self, ctx, point, color):
        (x, y) = point
        ctx.save()
        lw = self.plot_line_width * pt_in_mm
        ctx.set_line_width(lw)

        ctx.arc(x, y, self.plot_stem_point_radius, 0.0, 2*math.pi)
        ctx.set_source_rgb(1.00, 1.00, 1.00) # white
        ctx.fill_preserve()
        ctx.set_source_rgb(*color)
        ctx.stroke()

        ctx.restore()


    def render_plot_mavg_segment(self, ctx, point1, point2, color):
        # draw fat mavg line segment
        (x1, y1) = point1
        (x2, y2) = point2
        ctx.save()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        lw = 2.0 * self.plot_line_width * pt_in_mm
        ctx.set_source_rgb(*color)
        ctx.set_line_width(lw)
        ctx.move_to(x1, y1)
        ctx.line_to(x2, y2)
        ctx.stroke()
        ctx.restore()


    def render_plot_stem(self, ctx, coords, color):
        # draw stems to mavg line
        (x, y, ay) = coords
        ctx.save()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        lw = self.plot_line_width * pt_in_mm
        ctx.set_line_width(lw)

        ctx.move_to(x, ay)
        ctx.line_to(x, y)
        ctx.set_source_rgb(*color)
        ctx.stroke()

        ctx.restore()


    def render_plot_point(self, ctx, point):
        (x, y) = point
        ctx.save()

        ctx.move_to(x, y)
        ctx.line_to(x, y)

        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_width(2*self.plot_mark_line_width * pt_in_mm)
        ctx.set_source_rgb(*self.plot_color)
        ctx.stroke()
        ctx.restore()


    def render_plot_mark(self, ctx, point):
        (x, y) = point
        ctx.save()

        # self.__draw_plot_tick_cross(ctx, x, y)
        self.__draw_plot_tick_diag(ctx, x, y)
        # self.__draw_plot_tick_circle(ctx, x, y)

        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_width(self.plot_mark_line_width * pt_in_mm)
        ctx.set_source_rgb(*self.plot_color)
        ctx.stroke()
        ctx.restore()


    def __draw_vline(self, ctx, x, y1, y2):
        ctx.move_to(x, y1)
        ctx.line_to(x, y2)


    def render_calendar_range(self, ctx, date_range, is_first_last,
                              level, label_str, p, north=False):

        (begin_date, end_date) = date_range
        (begin_first, end_last) = is_first_last
        delta_x = self.delta_x_per_day
        range_distance = 1.25
        if delta_x >= range_distance:
            dx2 = 0.5 * (delta_x - range_distance)
        else:
            dx2 = 0.0

        begin_x = self._get_x(begin_date) - dx2
        end_x   = self._get_x(end_date)   + dx2

        # FIXME: set yofs in caller
        yofs = 2.0 + 1.5 + 3.5 * (level + 0)

        if north:
            y0 = self.sep_north - yofs
        else:
            y0 = self.page_height - self.sep_south + yofs

        ctx.save()
        # line along the range
        self.__draw_hline(ctx, begin_x, end_x, y0)

        # arrow tip for beginning of range
        if begin_first:
            self.__draw_vline(ctx, begin_x, y0-1.2, y0+1.2)
        else:
            ctx.move_to(begin_x+1.2, y0-1.2)
            #ctx.line_to(begin_x+0.0, y0+0.0)
            #ctx.line_to(begin_x+1.2, y0+1.2)

        # arrow tip for end of range
        if end_last:
            self.__draw_vline(ctx, end_x,   y0-1.2, y0+1.2)
        else:
            ctx.move_to(end_x-1.2, y0-1.2)
            #ctx.line_to(end_x-0.0, y0+0.0)
            #ctx.line_to(end_x-1.2, y0+1.2)

        ctx.set_line_width(p.line_width * pt_in_mm)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_source_rgb(*(p.line_color))
        ctx.stroke()

        if label_str:
            ctx.set_source_rgb(*(p.font_color))
            self.__render_center_text(ctx, 0.5*(begin_x + end_x), y0-0.25,
                                      label_str, bold=p.font_bold)
        ctx.restore()


    def render_time_tick(self, ctx, style, date, label_str, _id_str):
        x = self._get_x(date)
        north_ofs = style.begin_ofs
        south_ofs = style.end_ofs

        ctx.save()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.__draw_vline(ctx, x, north_ofs, self.page_height - south_ofs)
        ctx.set_source_rgb(*(style.line_color))
        ctx.set_line_width(style.line_width * pt_in_mm)
        ctx.stroke()
        ctx.restore()

        if style.do_label:
            ctx.save()
            ctx.set_source_rgb(*(style.font_color))
            bold = style.font_bold
            self.__render_north_text(ctx, x, north_ofs-2.0, label_str,
                                     bold=bold, rotate=style.rotate_labels)
            self.__render_south_text(ctx, x, self.page_height-south_ofs+2.3, label_str,
                                     bold=bold, rotate=style.rotate_labels)
            ctx.restore()


    def __draw_hline(self, ctx, x1, x2, y):
        ctx.move_to(x1, y)
        ctx.line_to(x2, y)


    def render_axis_kg_begin(self, ctx):
        ctx.save()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)


    def render_axis_kg_end(self, ctx):
        ctx.restore()


    def render_axis_kg_tick(self, ctx, y, kg_str, p):
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.__draw_hline(ctx, p.begin_ofs, self.page_width-p.end_ofs, y)
        ctx.set_line_width(p.line_width * pt_in_mm)
        ctx.stroke()

        if p.do_label:
            self.__render_right_text(ctx, p.begin_ofs, y,
                                     kg_str, bold=p.font_bold)
            self.__render_left_text(ctx, self.page_width-p.end_ofs, y,
                                    kg_str, bold=p.font_bold)


    def render_axis_bmi_begin(self, ctx):
        ctx.save()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)


    def render_axis_bmi_end(self, ctx):
        ctx.restore()


    def render_axis_bmi_tick(self, ctx, y, bmi, strbmi, p):
        ctx.set_line_width(p.line_width * pt_in_mm)

        self.__draw_hline(ctx, p.begin_ofs, self.page_width - p.end_ofs, y)
        ctx.set_source_rgb(*(p.line_color))
        ctx.stroke()

        if p.do_label:
            ctx.set_source_rgb(*(p.font_color))
            self.__render_right_text(ctx, p.begin_ofs, y, strbmi,
                                     bold=p.font_bold)
            self.__render_left_text(ctx, self.page_width-p.end_ofs, y,
                                    strbmi, bold=p.font_bold)


    def render_initials(self, ctx):
        ctx.set_source_rgb(0, 0, 0)
        # FIXME: Use different text rendering functions.
        # FIXME: Render text starting at TOP LEFT point
        self.__render_center_text(ctx,
                                  0 + 7.0,
                                  0 + 7.0,
                                  self.initials)
        # FIXME: Render text starting at BOTTOM LEFT point
        self.__render_center_text(ctx,
                                  0 + 7.0,
                                  self.page_height - 7.0,
                                  self.initials)
        # FIXME: Render text starting at TOP RIGHT point
        self.__render_center_text(ctx,
                                  self.page_width - 7.0,
                                  0 + 7.0,
                                  self.initials)
        # FIXME: Render text starting at BOTTOM RIGHT point
        self.__render_center_text(ctx,
                                  self.page_width - 7.0,
                                  self.page_height - 7.0,
                                  self.initials)


########################################################################
