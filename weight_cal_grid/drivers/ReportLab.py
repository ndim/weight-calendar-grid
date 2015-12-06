########################################################################


"""The ReportLab driver"""

# http://www.reportlab.com/


########################################################################


from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import white, red, black
from reportlab.pdfgen import canvas


########################################################################


from .basic import PageDriver
from .. import log
from .. import version


########################################################################


class ReportLabDriver(PageDriver):

    """ReportLab driver with PDF output"""
    # There might be more output formats in the future


    driver_name = 'reportlab'
    driver_formats = ['pdf']

    font_size = 9.5


    def __init__(self, *args, **kwargs):
        super(ReportLabDriver, self).__init__(*args, **kwargs)

    def gen_outfile(self, outfile, output_format):
        assert(output_format == 'pdf')
        pdf = canvas.Canvas(outfile, pagesize=landscape(A4))
        pdf.setCreator('%s %s' % (version.package_name, version.package_version))
        pdf.setTitle(self._("Weight Calendar Grid"))
        pdf.setSubject(self._("Draw one mark a day and graphically watch your weight"))
        self.render(pdf)
        pdf.save()

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
            pdf.setFont("Helvetica-Bold", self.font_size)
        else:
            pdf.setFont("Helvetica", self.font_size)
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
                pdf.setFont("Helvetica-Bold", self.font_size)
            else:
                pdf.setFont("Helvetica", self.font_size)
            pdf.drawCentredString(x, (style.end_ofs - 3.0)*mm, label_str)
            pdf.drawCentredString(x, (self.page_height-style.begin_ofs+1.0)*mm, label_str)
        pdf.restoreState()

    def render_initials(self, pdf):
        pdf.saveState()
        pdf.setFillColor(black)
        pdf.setFont("Helvetica", self.font_size)
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
        text.setFont("Helvetica", self.font_size)
        text.textOut(self._("weight in "))
        text.setFont("Helvetica-Bold", self.font_size)
        text.textOut("kg")
        w = text.getX();

        # Determine em size
        text = pdf.beginText()
        text.setTextOrigin(0, 0)
        text.setFont("Helvetica", self.font_size)
        text.textOut('m')
        em = text.getX();

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
        text.setFont("Helvetica", self.font_size)
        text.textOut(self._("weight in "))
        text.setFont("Helvetica-Bold", self.font_size)
        text.textOut("kg")
        pdf.drawText(text)

        text = pdf.beginText()
        text.setTextOrigin(rx, ry_right)
        text.setFont("Helvetica", self.font_size)
        text.textOut(self._("weight in "))
        text.setFont("Helvetica-Bold", self.font_size)
        text.textOut("kg")
        pdf.drawText(text)

        if self.height:
            pdf.setFillColor(red)
            text = pdf.beginText()
            text.setTextOrigin(0.5*self.page_height*mm+5*mm, -7*mm)
            text.setFont("Helvetica-Bold", self.font_size)
            text.textOut('BMI')
            text.setFont("Helvetica", self.font_size)
            text.textOut(self._(" for height %.2fm") % self.height)
            pdf.drawText(text)

            text = pdf.beginText()
            text.setTextOrigin(0.5*self.page_height*mm+5*mm, (5-self.page_width)*mm)
            text.setFont("Helvetica-Bold", self.font_size)
            text.textOut('BMI')
            text.setFont("Helvetica", self.font_size)
            text.textOut(self._(" for height %.2fm") % self.height)
            pdf.drawText(text)

        pdf.restoreState()

        pdf.saveState()
        # TODO: Use platypus Flowables to add the marks to the text.
        pdf.setFillColor(black)
        textobject = pdf.beginText()
        textobject.setTextOrigin(self.sep_west*mm, 7*mm)
        textobject.setFont("Helvetica-Bold", self.font_size)
        # print(textobject.getCursor())
        textobject.textOut(r"%s " % self._("Use:"))
        textobject.setFont("Helvetica", self.font_size)
        # print(textobject.getCursor())
        textobject.textOut(self._("Print this page. "
                             "Keep in accessible place with pen. "
                             "Mark one "))
        # print(textobject.getCursor())
        textobject.setFont("Helvetica-Bold", self.font_size)
        textobject.textOut('x')
        textobject.setFont("Helvetica", self.font_size)
        textobject.textOut(self._(" every day. "
                             "Connect "))
        # print(textobject.getCursor())
        textobject.setFont("Helvetica-Bold", self.font_size)
        textobject.textOut('x-x')
        textobject.setFont("Helvetica", self.font_size)
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
                w = pdf.stringWidth(label_str, "Helvetica-Bold", self.font_size)
                pdf.setFont("Helvetica-Bold", self.font_size)
            else:
                w = pdf.stringWidth(label_str, "Helvetica", self.font_size)
                pdf.setFont("Helvetica", self.font_size)

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
                pdf.setFont("Helvetica-Bold", self.font_size)
            else:
                pdf.setFont("Helvetica", self.font_size)
            pdf.drawString((self.page_width - p.end_ofs + 0.5)*mm, y-1.25*mm, kg_str)
            pdf.drawRightString((p.begin_ofs-0.5)*mm, y-1.25*mm, kg_str)
        pdf.restoreState()

    def render_axis_kg_end(self, pdf):
        pass


########################################################################
