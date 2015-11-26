"""The ReportLab driver"""

# http://www.reportlab.com/


########################################################################


from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas


########################################################################


from .basic import PageDriver
from .. import log


########################################################################


class ReportLabDriver(PageDriver):

    """ReportLab driver with PDF output"""
    # There might be more output formats in the future


    driver_name = 'reportlab'
    driver_formats = ['pdf']

    font_size = 10


    def __init__(self, *args, **kwargs):
        super(ReportLabDriver, self).__init__(*args, **kwargs)

    def gen_outfile(self, outfile, output_format):
        assert(output_format == 'pdf')
        pdf = canvas.Canvas(outfile, pagesize=landscape(A4))
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
        print('y', repr(y), 'bmi', repr(bmi),
              'strbmi', repr(strbmi), 'p', repr(p))

        pdf.saveState()

        pdf.setLineWidth(p.line_width)
        pdf.setStrokeColorRGB(*p.line_color)
        pdf.line(p.begin_ofs*mm, y, (self.page_width-p.end_ofs)*mm, y)

        pdf.setFillColorRGB(*p.font_color)
        if p.font_bold:
            pdf.setFont("Helvetica-Bold", self.font_size)
        else:
            pdf.setFont("Helvetica", self.font_size)
        # FIXME: Move top text vertically
        pdf.drawString((self.page_width - p.end_ofs)*mm, y, strbmi)
        pdf.drawRightString((p.begin_ofs)*mm, y, strbmi)
        pdf.restoreState()

    def render_time_tick(self, pdf, style, date, label_str, id_str):
        pdf.saveState()
        x = self._get_x(date)
        south_ofs = style.begin_ofs
        north_ofs = style.end_ofs
        pdf.setLineWidth(style.line_width)
        pdf.setStrokeColorRGB(0,0,0)
        pdf.line(x, north_ofs*mm, x, (self.page_height-south_ofs)*mm)

        if style.do_label:
            pdf.setFillColorRGB(0,0,0)
            if style.font_bold:
                pdf.setFont("Helvetica-Bold", self.font_size)
            else:
                pdf.setFont("Helvetica", self.font_size)
            pdf.drawCentredString(x, (style.end_ofs - 3.0)*mm, label_str)
            pdf.drawCentredString(x, (self.page_height-style.begin_ofs+1.0)*mm, label_str)
        pdf.restoreState()

    def render_initials(self, pdf):
        pdf.saveState()
        pdf.setFillColorRGB(0,0,0)
        pdf.drawString(7*mm, 7*mm, self.initials)
        pdf.drawRightString((self.page_width-7)*mm, 7*mm, self.initials)
        # FIXME: Move top text vertically
        pdf.drawString(7*mm, (self.page_height-7)*mm, self.initials)
        pdf.drawRightString((self.page_width-7)*mm, (self.page_height-7)*mm, self.initials)
        pdf.restoreState()

    def render_beginning(self, pdf):
        pass

    def render_ending(self, pdf):
        pdf.saveState()

        text = pdf.beginText()
        text.setTextOrigin(0, 0)
        text.setFont("Helvetica", self.font_size)
        text.textOut("weight in ")
        text.setFont("Helvetica-Bold", self.font_size)
        text.textOut("kg")
        x = text.getX();

        pdf.rotate(90)

        pdf.setFillColorRGB(0,0,0)
        text = pdf.beginText()
        text.setTextOrigin(0.5*self.page_height*mm-5*mm-x, -7*mm)
        text.setFont("Helvetica", self.font_size)
        text.textOut("weight in ")
        text.setFont("Helvetica-Bold", self.font_size)
        text.textOut("kg")
        pdf.drawText(text)

        pdf.setFillColorRGB(255,0,0)
        text = pdf.beginText()
        text.setTextOrigin(0.5*self.page_height*mm+5*mm, -7*mm)
        text.setFont("Helvetica-Bold", self.font_size)
        text.textOut('BMI')
        text.setFont("Helvetica", self.font_size)
        text.textOut(_(' for height %.2fm') % self.height)
        pdf.drawText(text)

        pdf.setFillColorRGB(0,0,0)
        text = pdf.beginText()
        text.setTextOrigin(0.5*self.page_height*mm-5*mm-x, (7-self.page_width)*mm)
        text.setFont("Helvetica", self.font_size)
        text.textOut("weight in ")
        text.setFont("Helvetica-Bold", self.font_size)
        text.textOut("kg")
        pdf.drawText(text)

        pdf.setFillColorRGB(255,0,0)
        text = pdf.beginText()
        text.setTextOrigin(0.5*self.page_height*mm+5*mm, (7-self.page_width)*mm)
        text.setFont("Helvetica-Bold", self.font_size)
        text.textOut('BMI')
        text.setFont("Helvetica", self.font_size)
        text.textOut(_(' for height %.2fm') % self.height)
        pdf.drawText(text)

        pdf.restoreState()

        pdf.saveState()
        # TODO: Use platypus Flowables to add the marks to the text.
        pdf.setFillColorRGB(0,0,0)
        textobject = pdf.beginText()
        textobject.setTextOrigin(self.sep_west*mm, 7*mm)
        textobject.setFont("Helvetica-Bold", self.font_size)
        print(textobject.getCursor())
        textobject.textOut(r"%s " % _("Use:"))
        textobject.setFont("Helvetica", self.font_size)
        print(textobject.getCursor())
        textobject.textOut(_("Print this page. "
                             "Keep in accessible place with pen. "
                             "Mark one "))
        print(textobject.getCursor())
        textobject.textOut(_(" every day. "
                             "Connect "))
        print(textobject.getCursor())
        textobject.textOut(_(" to yesterday's mark. "
                             "Type marked values into computer as deemed useful."))
        print(textobject.getCursor())
        pdf.drawText(textobject)
        pdf.restoreState()

    def render_plot_mark(self, pdf, point):
        (x, y) = point
        pass

    def render_plot_mavg_segment(self, pdf, point1, point2, color):
        (x1, y1) = point1
        (x2, y2) = point2
        pass

    def render_plot_point(self, pdf, point):
        (x, y) = point
        pass

    def render_plot_stem(self, pdf, coords, color):
        (x, y, ay) = coords
        pass

    def render_plot_stem_point(self, pdf, point, color):
        (x, y) = point
        pass

    def render_plot_value_line_segment(self, pdf, point1, point2):
        (x1, y1) = point1
        (x2, y2) = point2
        pass

    def render_calendar_range(self, pdf, date_range, is_first_last,
                              level, label_str, p, north=False):
        (begin_date, end_date) = date_range
        (is_begin_first, is_end_last) = is_first_last


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
            # FIXME: Move top text vertically
            pdf.drawString((self.page_width - p.end_ofs)*mm, y, kg_str)
            pdf.drawRightString((p.begin_ofs)*mm, y, kg_str)
        pdf.restoreState()

    def render_axis_kg_end(self, pdf):
        pass


########################################################################
