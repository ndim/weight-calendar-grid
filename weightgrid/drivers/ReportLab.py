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


    def __init__(self, *args, **kwargs):
        super(ReportLabDriver, self).__init__(*args, **kwargs)

    def gen_outfile(self, outfile, output_format):
        assert(output_format == 'pdf')
        pdf = canvas.Canvas(outfile, pagesize=landscape(A4))
        self.render(pdf)
        pdf.save()

    def _get_x(self, _day):
        return None

    def _get_y(self, kg):
        return None

    def render_axis_bmi_begin(self, pdf):
        pass

    def render_axis_bmi_end(self, pdf):
        pass

    def render_axis_bmi_tick(self, pdf, y, bmi, strbmi, p):
        pass

    def render_time_tick(self, pdf, style, date, label_str, id_str):
        pass

    def render_initials(self, pdf):
        pass

    def render_beginning(self, pdf):
        for i in range(3, 19+1):
            pdf.setLineWidth(0.5 + 3 * i % 2)
            pdf.line((20-1.5)*mm, i*cm, (297-20+1.5)*mm, i*cm)
        for i in range(1, 27+1):
            pdf.setLineWidth(0.5 + 3 * i % 2)
            pdf.line(-1.5*mm+(i+1)*cm, 30*mm, -1.5*mm+(i+1)*cm, (210-20)*mm)


    def render_ending(self, pdf):
        # TODO: Use platypus Flowables to add the marks to the text.
        textobject = pdf.beginText()
        textobject.setTextOrigin(2*cm, 1*cm)
        textobject.setFont("Helvetica-Bold", 10)
        print(textobject.getCursor())
        textobject.textOut(r"%s " % _("Use:"))
        textobject.setFont("Helvetica", 10)
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
        pass


    def render_axis_kg_begin(self, pdf):
        pass

    def render_axis_kg_tick(self, pdf, y, kg_str, p):
        pass

    def render_axis_kg_end(self, pdf):
        pass


########################################################################
