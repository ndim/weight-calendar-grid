########################################################################


"""The ReportLab driver"""

# http://www.reportlab.com/


########################################################################


import os
from os.path import dirname, join

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import white, red, black
from reportlab.pdfgen import canvas

# we know some glyphs are missing, suppress warnings
import reportlab.rl_config
reportlab.rl_config.warnOnMissingFontGlyphs = 0
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


########################################################################


from .basic import PageDriver
from .. import log
from .. import version
from ..utils import InternalLogicError


########################################################################

class FontNotFound(Exception):
    """Given font has not been found"""
    pass

########################################################################

class ClassDefinitionError(Exception):
    """Some class has been defined in a wrong way"""
    pass

########################################################################

class FontSetMeta(type):
    def __new__(mcs, clsname, bases, clsdict):

        required_members = {
            'regular':    [str],
            'bold':       [str],
            'italic':     [str],
            'bolditalic': [str],
            'size':       [float,int],
        }

        # Extend the list of required members if class defines
        # required_constants list.
        if 'required_constants' in clsdict:
            for k in clsdict['required_constants']:
                if k not in required_members:
                    required_members[k] = [float,int,str]

        # Check presence and type of some required FontSet member
        # constants.
        missing_members = []
        for k, types in required_members.items():
            if k in clsdict:
                if type(clsdict[k]) not in types:
                    raise ClassDefinitionError(
                        'Class %s member %s value %s has type %s. Must have a type from %s'
                        % (repr(clsname), repr(k), clsdict[k],
                           repr(type(clsdict[k])), repr(types)))
            else:
                missing_members.append(k)

        # If we miss all required members, we are an abstract base
        # class. If all required members are present, we are OK.
        # In all in between cases, raise an exception.
        if len(missing_members) == len(required_members):
            # We are an abstract base class. That is OK.
            pass
        elif len(missing_members) == 0:
            # We define all members. That is OK.
            pass
        else:
            raise ClassDefinitionError(
                'Class %s member constants undefined: %s'
                % (repr(clsname), ', '.join(missing_members)))

        return super(FontSetMeta, mcs).__new__(mcs, clsname, bases, clsdict)

########################################################################

class FontSet(object, metaclass=FontSetMeta):
    pass

########################################################################

class HelveticaSet(FontSet):
    size       = 9.5
    regular    = 'Helvetica'
    bold       = 'Helvetica-Bold'
    italic     = 'Helvetical-Oblique'
    bolditalic = 'Helvetical-BoldOblique'

########################################################################

class TTFSet(FontSet):

    required_constants = ['font_dir']

    def __init__(self):
        font_list = []
        for font_name in [self.regular, self.bold,
                          self.italic, self.bolditalic]:
            font_fpath = join(self.font_dir, '%s.ttf' % font_name)
            if not os.path.exists(font_fpath):
                raise FontNotFound(font_fpath)
            font_list.append((font_name, font_fpath))
        for font_name, font_fpath in font_list:
            pdfmetrics.registerFont(TTFont(font_name, font_fpath))

########################################################################

class ReportLabVeraSet(TTFSet):
    font_dir   = join(dirname(reportlab.__file__),'fonts')
    size       = 9
    regular    = 'Vera'
    bold       = 'VeraBd'
    italic     = 'VeraIt'
    bolditalic = 'VeraBI'

########################################################################

class DejaVuSet(TTFSet):
    font_dir = '/usr/share/fonts/dejavu'

########################################################################

class DejaVuSansSet(DejaVuSet):
    size       = 9
    regular    = 'DejaVuSans'
    bold       = 'DejaVuSans-Bold'
    italic     = 'DejaVuSans-Oblique'
    bolditalic = 'DejaVuSans-BoldOblique'

########################################################################

class DejaVuSansCondensedSet(DejaVuSet):
    size       = 9
    regular    = 'DejaVuSansCondensed'
    bold       = 'DejaVuSansCondensed-Bold'
    italic     = 'DejaVuSansCondensed-Oblique'
    bolditalic = 'DejaVuSansCondensed-BoldOblique'

########################################################################

class LiberationSet(TTFSet):
    font_dir   = '/usr/share/fonts/liberation'

########################################################################

class LiberationSansSet(LiberationSet):
    size       = 9.5
    regular    = 'LiberationSans-Regular'
    bold       = 'LiberationSans-Bold'
    italic     = 'LiberationSans-Italic'
    bolditalic = 'LiberationSans-BoldItalic'

########################################################################

class LiberationSansNarrowSet(LiberationSet):
    size       = 10
    regular    = 'LiberationSansNarrow-Regular'
    bold       = 'LiberationSansNarrow-Bold'
    italic     = 'LiberationSansNarrow-Italic'
    bolditalic = 'LiberationSansNarrow-BoldItalic'

########################################################################

class LiberationMonoSet(LiberationSet):
    size       = 6
    regular    = 'LiberationMono-Regular'
    bold       = 'LiberationMono-Bold'
    italic     = 'LiberationMono-Italic'
    bolditalic = 'LiberationMono-BoldItalic'

class DejaVuSansMonoSet(DejaVuSet):
    size       = 6
    regular    = 'DejaVuSansMono'
    bold       = 'DejaVuSansMono-Bold'
    italic     = 'DejaVuSansMono-Oblique'
    bolditalic = 'DejaVuSansMono-BoldOblique'

class CourierSet(FontSet):
    size       = 6
    regular    = 'Courier'
    bold       = 'Courier-Bold'
    italic     = 'Courier-Oblique'
    bolditalic = 'Courier-BoldOblique'


########################################################################


class ReportLabDriver(PageDriver):

    """ReportLab driver with PDF output"""
    # There might be more output formats in the future


    driver_name = 'reportlab'
    driver_formats = ['pdf']

    def __init__(self, *args, **kwargs):
        super(ReportLabDriver, self).__init__(*args, **kwargs)

    def gen_outfile(self, outfile, output_format):
        assert(output_format == 'pdf')
        pdf = canvas.Canvas(outfile, pagesize=landscape(A4))
        pdf.setCreator('%s %s' % (version.package_name, version.package_version))
        pdf.setTitle(self._("Weight Calendar Grid"))
        pdf.setSubject(self._("Draw one mark a day and graphically watch your weight"))

        self.load_fontset_mono()
        self.load_fontset_sans()

        self.render(pdf)
        pdf.save()

    def load_fontset_sans(self):
        # Note that font_sets must contain one of the PDF standard
        # fonts in the end, so that we can actually use some font even
        # if we do not find any TTF files.
        font_sets = [LiberationSansSet,
                     LiberationSansNarrowSet,
                     DejaVuSansCondensedSet,
                     DejaVuSansSet,
                     ReportLabVeraSet,
                     HelveticaSet]
        for klass in font_sets:
            try:
                font_set = klass()
                self.fontname_regular    = font_set.regular
                self.fontname_bold       = font_set.bold
                self.fontname_italic     = font_set.italic
                self.fontname_bolditalic = font_set.bolditalic
                self.font_size           = font_set.size
                assert(self.font_size)
                assert(self.fontname_regular)
                assert(self.fontname_bold)
                assert(self.fontname_italic)
                assert(self.fontname_bolditalic)
                return
            except FontNotFound:
                pass
        raise InternalLogicError()

    def load_fontset_mono(self):
        # Note that font_sets must contain one of the PDF standard
        # fonts in the end, so that we can actually use some font even
        # if we do not find any TTF files.
        font_sets = [LiberationMonoSet,
                     DejaVuSansMonoSet,
                     CourierSet]
        for klass in font_sets:
            try:
                font_set = klass()
                self.fontname_mono_regular    = font_set.regular
                self.fontname_mono_bold       = font_set.bold
                self.fontname_mono_italic     = font_set.italic
                self.fontname_mono_bolditalic = font_set.bolditalic
                self.font_size_small          = font_set.size
                assert(self.font_size_small)
                assert(self.fontname_mono_regular)
                assert(self.fontname_mono_bold)
                assert(self.fontname_mono_italic)
                assert(self.fontname_mono_bolditalic)
                return
            except FontNotFound:
                pass
        raise InternalLogicError()

    def _get_y(self, kg):
        y0 = self.sep_south # self.page_height - self.sep_south
        eff_h = self.page_height - self.sep_north - self.sep_south
        return (y0 + eff_h * (kg - self.min_kg) / self.range_kg)*mm

    def _get_x(self, _day):
        return super(ReportLabDriver, self)._get_x(_day)*mm

    def render_axis_bmi_begin(self, pdf):
        pass

    def render_axis_bmi_end(self, pdf):
        pass

    def render_axis_bmi_tick(self, pdf, y, bmi, strbmi, p):
        pdf.saveState()

        pdf.setLineWidth(p.line_width)
        pdf.setStrokeColorRGB(*p.line_color)
        pdf.line(p.begin_ofs*mm, y, (self.page_width-p.end_ofs)*mm, y)

        pdf.setFillColorRGB(*p.font_color)
        if p.font_bold:
            pdf.setFont(self.fontname_bold, self.font_size)
        else:
            pdf.setFont(self.fontname_regular, self.font_size)
        pdf.drawString((self.page_width - p.end_ofs + 0.5)*mm, y-1.25*mm, strbmi)
        pdf.drawRightString((p.begin_ofs-0.5)*mm, y-1.25*mm, strbmi)
        pdf.restoreState()

    def render_time_tick(self, pdf, style, date, label_str, id_str):
        pdf.saveState()
        x = self._get_x(date)
        south_ofs = style.begin_ofs
        north_ofs = style.end_ofs
        pdf.setLineWidth(style.line_width)
        pdf.setStrokeColor(black)
        pdf.line(x, north_ofs*mm, x, (self.page_height-south_ofs)*mm)

        if style.do_label:
            pdf.setFillColor(black)
            if style.font_bold:
                pdf.setFont(self.fontname_bold, self.font_size)
            else:
                pdf.setFont(self.fontname_regular, self.font_size)
            pdf.drawCentredString(x, (style.end_ofs - 3.0)*mm, label_str)
            pdf.drawCentredString(x, (self.page_height-style.begin_ofs+1.0)*mm, label_str)
        pdf.restoreState()

    def render_cmdline(self, pdf, sep_west, sep_south, cmdline):
        pdf.saveState()
        pdf.setFillColor(black)
        pdf.setFont(self.fontname_mono_regular, self.font_size_small)
        pdf.drawString(sep_west*mm, sep_south*mm, cmdline)
        pdf.restoreState()

    def render_initials(self, pdf):
        pdf.saveState()
        pdf.setFillColor(black)
        pdf.setFont(self.fontname_regular, self.font_size)
        pdf.drawString(7*mm, 7*mm, self.initials)
        pdf.drawRightString((self.page_width-7)*mm, 7*mm, self.initials)
        pdf.drawString(7*mm, (self.page_height-7)*mm-0.5*self.font_size, self.initials)
        pdf.drawRightString((self.page_width-7)*mm,
                            (self.page_height-7)*mm-0.5*self.font_size, self.initials)
        pdf.restoreState()

    def render_beginning(self, pdf):
        pass

    def render_ending(self, pdf):
        pdf.saveState()

        # Determine text width (can't use .stringWidth due to different fonts)
        text = pdf.beginText()
        text.setTextOrigin(0, 0)
        text.setFont(self.fontname_regular, self.font_size)
        text.textOut(self._("weight in "))
        text.setFont(self.fontname_bold, self.font_size)
        text.textOut("kg")
        w = text.getX();

        # Determine em size
        em = pdf.stringWidth('m', self.fontname_bold, self.font_size)

        pdf.rotate(90)

        # rotated coordinates
        if self.height:
            rx = 0.5*self.page_height*mm - 2*em - w
            ry_left = -7*mm
            ry_right = 5*mm - self.page_width*mm
        else:
            rx = 0.5*self.page_height*mm - 0.5*2*em
            ry_left = -self.sep_west*mm + 10*mm
            ry_right = self.sep_east*mm - self.page_width*mm - 10*mm - self.font_size

        pdf.setFillColor(black)
        text = pdf.beginText()
        text.setTextOrigin(rx, ry_left)
        text.setFont(self.fontname_regular, self.font_size)
        text.textOut(self._("weight in "))
        text.setFont(self.fontname_bold, self.font_size)
        text.textOut("kg")
        pdf.drawText(text)

        text = pdf.beginText()
        text.setTextOrigin(rx, ry_right)
        text.setFont(self.fontname_regular, self.font_size)
        text.textOut(self._("weight in "))
        text.setFont(self.fontname_bold, self.font_size)
        text.textOut("kg")
        pdf.drawText(text)

        if self.height:
            pdf.setFillColor(red)
            text = pdf.beginText()
            text.setTextOrigin(0.5*self.page_height*mm+5*mm, -7*mm)
            text.setFont(self.fontname_bold, self.font_size)
            text.textOut('BMI')
            text.setFont(self.fontname_regular, self.font_size)
            text.textOut(self._(" for height %.2fm") % self.height)
            pdf.drawText(text)

            text = pdf.beginText()
            text.setTextOrigin(0.5*self.page_height*mm+5*mm, (5-self.page_width)*mm)
            text.setFont(self.fontname_bold, self.font_size)
            text.textOut('BMI')
            text.setFont(self.fontname_regular, self.font_size)
            text.textOut(self._(" for height %.2fm") % self.height)
            pdf.drawText(text)

        pdf.restoreState()

        pdf.saveState()
        # TODO: Use platypus Flowables to add the marks to the text.
        pdf.setFillColor(black)
        textobject = pdf.beginText()
        textobject.setTextOrigin(self.sep_west*mm, 7*mm)
        textobject.setFont(self.fontname_bold, self.font_size)
        # print(textobject.getCursor())
        textobject.textOut(r"%s " % self._("Use:"))
        textobject.setFont(self.fontname_regular, self.font_size)
        # print(textobject.getCursor())
        textobject.textOut(self._("Print this page. "
                             "Keep in accessible place with pen. "
                             "Mark one "))
        # print(textobject.getCursor())
        textobject.setFont(self.fontname_bold, self.font_size)
        textobject.textOut('x')
        textobject.setFont(self.fontname_regular, self.font_size)
        textobject.textOut(self._(" every day. "
                             "Connect "))
        # print(textobject.getCursor())
        textobject.setFont(self.fontname_bold, self.font_size)
        textobject.textOut('x-x')
        textobject.setFont(self.fontname_regular, self.font_size)
        textobject.textOut(self._(" to yesterday's mark. "
                             "Type marked values into computer as deemed useful."))
        # print(textobject.getCursor())
        pdf.drawText(textobject)
        pdf.restoreState()

    # TODO: Actually plot weight data
    def render_plot_mark(self, pdf, point):
        (x, y) = point

    # TODO: Actually plot weight data
    def render_plot_mavg_segment(self, pdf, point1, point2, color):
        (x1, y1) = point1
        (x2, y2) = point2

    # TODO: Actually plot weight data
    def render_plot_point(self, pdf, point):
        (x, y) = point

    # TODO: Actually plot weight data
    def render_plot_stem(self, pdf, coords, color):
        (x, y, ay) = coords

    # TODO: Actually plot weight data
    def render_plot_stem_point(self, pdf, point, color):
        (x, y) = point

    # TODO: Actually plot weight data
    def render_plot_value_line_segment(self, pdf, point1, point2):
        (x1, y1) = point1
        (x2, y2) = point2

    def render_calendar_range(self, pdf, date_range, is_first_last,
                              level, label_str, p, north=False):
        (begin_date, end_date) = date_range
        (is_begin_first, is_end_last) = is_first_last

        delta_x = self.delta_x_per_day
        range_distance = 3
        if delta_x >= range_distance:
            dx2 = 0.5 * (delta_x - range_distance)
        else:
            dx2 = 0.0

        begin_x = self._get_x(begin_date) - dx2
        end_x   = self._get_x(end_date)   + dx2

        # FIXME: set yofs in caller
        yofs = 2.0 + 1.5 + 3.5 * (level + 0)

        if north:
            y0 = self.page_height - self.sep_north + yofs
        else:
            y0 = self.sep_south - yofs
        y0 = y0*mm

        pdf.saveState()

        pdf.setLineWidth(p.line_width)
        pdf.setStrokeColorRGB(*(p.line_color))

        # line along the range
        pdf.line(begin_x, y0, end_x, y0)

        # arrow tip for beginning of range
        if is_begin_first:
            pdf.line(begin_x, y0-1.2*mm, begin_x, y0+1.2*mm)
        else:
            pass

        # arrow tip for end of range
        if is_end_last:
            pdf.line(end_x, y0-1.2*mm, end_x, y0+1.2*mm)
        else:
            pass

        if label_str:
            if p.font_bold:
                w = pdf.stringWidth(label_str, self.fontname_bold, self.font_size)
                pdf.setFont(self.fontname_bold, self.font_size)
            else:
                w = pdf.stringWidth(label_str, self.fontname_regular, self.font_size)
                pdf.setFont(self.fontname_regular, self.font_size)

            cx = 0.5*(begin_x+end_x)
            cy = y0-1.25*mm
            pdf.setFillColor(white)
            pdf.rect(cx-0.5*w-0.5*mm, cy-0.5*mm, w+2*0.5*mm,
                     self.font_size, stroke=0, fill=1)
            pdf.setFillColorRGB(*(p.font_color))
            pdf.drawCentredString(cx, cy, label_str)
        pdf.restoreState()

    def render_axis_kg_begin(self, pdf):
        pass

    def render_axis_kg_tick(self, pdf, y, kg_str, p):
        pdf.saveState()
        pdf.setLineWidth(p.line_width)
        pdf.setStrokeColorRGB(*p.line_color)
        pdf.line(p.begin_ofs*mm, y, (self.page_width-p.end_ofs)*mm, y)

        if p.do_label:
            pdf.setFillColorRGB(*p.font_color)
            if p.font_bold:
                pdf.setFont(self.fontname_bold, self.font_size)
            else:
                pdf.setFont(self.fontname_regular, self.font_size)
            pdf.drawString((self.page_width - p.end_ofs + 0.5)*mm, y-1.25*mm, kg_str)
            pdf.drawRightString((p.begin_ofs-0.5)*mm, y-1.25*mm, kg_str)
        pdf.restoreState()

    def render_axis_kg_end(self, pdf):
        pass


########################################################################
