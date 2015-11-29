"""The TikZ/pdflatex driver"""


########################################################################


import os
import re
import subprocess
import sys
import tempfile


########################################################################


def __import_check():
    for path in os.getenv('PATH').split(os.path.pathsep):
        if os.path.exists(os.path.join(path, 'pdflatex')):
            return True
    raise ImportError('The TikZ driver requires pdflatex')

__import_check()
del __import_check


########################################################################


from .basic import PageDriver
from .. import log


########################################################################


def _latex_to_pdf(texstr, keep_tmp_on_error, outfile):

    basename = 'weight-calendar-grid'

    workdir = tempfile.mkdtemp(prefix='%s.' % basename, suffix='.wd')
    log.debug("created workdir %s", workdir)

    def cleanup_workdir():
        for (dirpath, dirnames, filenames) in os.walk(workdir, topdown=False):
            for f in filenames:
                os.unlink(os.path.join(dirpath, f))
        for d in dirnames:
            os.rmdir(os.path.join(dirpath, d))
        os.rmdir(workdir)
        log.debug("cleaned up workdir %s", workdir)

    texfname = os.path.join(workdir, '%s.tex' % basename)
    with open(texfname, 'w') as texfile:
        texfile.write(texstr)

    def run_latex(stage, stages):
        global stage_counter # hack
        log.verbose("pdflatex run %d/%d for %s",
                    stage, stages, outfile.name)
        proc = subprocess.Popen(['pdflatex', basename],
                                 cwd = workdir,
                                 stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=False)
        try:
            outs, errs = proc.communicate(timeout=300)
        except TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate()
            raise
        if proc.returncode != 0:
            log.error("Error running pdflatex (retcode=%d). Aborting.",
                      proc.returncode)
            sys.exit(1)
        return outs

    try:
        stage  = 1
        stages = 2
        while True:
            tty_text = run_latex(stage, stages)
            stage += 1
            if stage > stages:
                break
    except:
        sys.stdout.write(tty_text)
        if not keep_tmp_on_error:
            cleanup_workdir()
            log.warn("To examine the workdir, run with '--keep' option.")
        else:
            log.warn("kept workdir %s", workdir)
            log.warn("examine %s", texfname)
            r = re.compile(r'^l\.(\d+) ', re.MULTILINE)
            line_no = 0
            try:
                a = r.findall(tty_text)
                if a:
                    line_no = int(a[-1])
                    print("%s:%d: hello emacs" % (texfname, line_no, ),
                          file=sys.stderr)
            except:
                pass
        raise # re-raise error while running pdflatex

    with open(os.path.join(workdir, "%s.pdf" % basename), 'rb') as pdf_file:
        pdf_data = pdf_file.read()
    cleanup_workdir()

    outfile.write(pdf_data)
    outfile.close()


########################################################################


class TikZDriver(PageDriver):


    """TikZ/pdflatex output driver"""


    driver_name = 'tikz'
    driver_formats = ['pdf']


    def __init__(self, *args, **kwargs):
        super(TikZDriver, self).__init__(*args, **kwargs)

        self.bmi_label_nodes = []
        self.kg_label_nodes = []


    def _get_y(self, kg):
        eff_h = (self.page_height - self.sep_north - self.sep_south)
        return self.sep_south + eff_h * (kg - self.min_kg) / self.range_kg


    def gen_outfile(self, outfile, output_format):
        assert(output_format == 'pdf')

        tex_lines = []
        self.render(tex_lines)

        for lines in tex_lines:
            for line in lines.splitlines():
                log.data(line)

        tex_data = '\n'.join(tex_lines)
        _latex_to_pdf(tex_data, self.keep_tmp_on_error,
                      outfile)


    def render_beginning(self, ctx):
        d = dict(globals())
        d['mark_delta'] = self.mark_delta
        d['plot_line_shorten'] = self.plot_line_shorten
        d['plot_line_width'] = self.plot_line_width
        d['plot_mark_line_width'] = self.plot_mark_line_width
        d['plot_point_line_width'] = 2* self.plot_mark_line_width
        d['plot_stem_point_radius'] = self.plot_stem_point_radius

        # for e.g. German, babel_opt should translate to "english,ngerman"
        babel_opt   = _('<language specific options to LaTeX babel package>')
        if babel_opt == '<language specific options to LaTeX babel package>':
            babel_opt = 'english'
        d['babel_opt'] = babel_opt

        ctx.append(r"""\documentclass[a4paper,10pt,landscape]{article}

\usepackage[%(babel_opt)s]{babel}
\usepackage[T1]{fontenc}
\usepackage{microtype}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}

\pagestyle{empty}
\usepackage[rgb]{xcolor}
\usepackage{tikz}
\usetikzlibrary{arrows}
\usetikzlibrary{chains}
\usetikzlibrary{fit}
\usetikzlibrary{backgrounds}
\usetikzlibrary{decorations.pathmorphing}
\usepgflibrary{decorations.pathreplacing}
\usetikzlibrary{shapes}
\usetikzlibrary{shapes.callouts}
\usetikzlibrary{shapes.multipart}
\usetikzlibrary{calc}
\usetikzlibrary{intersections}
\usetikzlibrary{positioning}

\def\TikZ{Ti\emph{k}Z}
""" % d)
        ctx.append(r'\definecolor{plotlinecolor}{rgb}{%f, %f, %f}' % self.plot_color)
        ctx.append(r"""
\tikzset{plot line/.style={draw=plotlinecolor,
                           line cap=round,
                           line width=%(plot_line_width)fpt,
                           shorten <=%(plot_line_shorten)fmm}}
\tikzset{plot marked line/.style={plot line,
                           shorten <=%(plot_line_shorten)fmm,
                           shorten >=%(plot_line_shorten)fmm}}
\tikzset{plot mark/.style={draw=plotlinecolor,
                           line cap=round,
                           line width=%(plot_mark_line_width)fpt}}
\tikzset{plot stem point/.style={draw=plotlinecolor,
                                 line width=%(plot_mark_line_width)fpt,
                                 radius=%(plot_stem_point_radius)fmm,
                                 fill=white}}
\tikzset{plot point/.style={draw=plotlinecolor,
                           line cap=round,
                           line width=%(plot_point_line_width)fpt}}
\tikzset{every node/.style={}}

\newcommand{\plotmark}[2]{%%
\draw[plot mark,xshift=#1,yshift=#2]
   (-%(mark_delta)fmm,-%(mark_delta)fmm) -- (+%(mark_delta)fmm,+%(mark_delta)fmm)
   (-%(mark_delta)fmm,+%(mark_delta)fmm) -- (+%(mark_delta)fmm,-%(mark_delta)fmm);
}

\begin{document}

\begin{tikzpicture}[remember picture, overlay, font=\sffamily]

\begin{scope}[every node/.style={inner xsep=1.5pt}]
""" % d)


    def render_ending(self, ctx):
        d = dict(globals())
        d['sep_east'] = self.sep_east
        d['sep_west'] = self.sep_west
        d['mark_delta'] = self.mark_delta
        d['driver_name'] = self.driver_name
        # d['height'] = self.height
        d['bmilabels'] = ' '.join(self.bmi_label_nodes)
        d['kglabels'] = ' '.join(self.kg_label_nodes)

        if self.bmi_label_nodes:
            ctx.append(r'\node[inner sep=0,fit=%(bmilabels)s] (bmilabel bounding box) {};' % d)
        if self.kg_label_nodes:
            ctx.append(r'\node[inner sep=0,fit=%(kglabels)s]  (kglabel bounding box) {};' % d)

        if False:
            ctx.append(r"""
\draw[green] ([xshift=+5mm,yshift=+5mm]current page.south west)
   rectangle ([xshift=-5mm,yshift=-5mm]current page.north east);
\draw[green] ([xshift=+8mm,yshift=+8mm]current page.south west)
   rectangle ([xshift=-8mm,yshift=-8mm]current page.north east);
\draw[green] ([xshift=+10mm,yshift=+10mm]current page.south west)
   rectangle ([xshift=-10mm,yshift=-10mm]current page.north east);
""" % d)

        if False: # print program version
            ctx.append(r"""
\begin{scope}[every node/.style={inner sep=0,text=black!50!white,font=\ttfamily\scriptsize}]
  \node[anchor=north east]
    at ([xshift=-%(sep_east)fmm,yshift=-5mm]current page.north east)
    (east version) {%(prog_name)s %(prog_version)s};

  \node[anchor=north west]
    at ([xshift=+%(sep_east)fmm,yshift=-5mm]current page.north west)
    (west version) {%(prog_name)s %(prog_version)s};
\end{scope}""" % d)

        if not self.history_mode: # print usage note
            mdleft  = 0.5 * self.mark_delta
            mdright = 0.5 * self.mark_delta
            if self.show_bmi:
                # If we know the BMI, make the instructions suggest
                # increasing/decreasing the weight if
                # underweight/overweight.
                center_kg = 0.5 * (self.min_kg + self.max_kg)
                center_bmi = center_kg/self.height**2
                if   center_bmi < 20:
                    mdleft  = 0.0
                    mdright = self.mark_delta
                elif center_bmi > 25:
                    mdleft  = self.mark_delta
                    mdright = 0.0
            d['mark_delta_left']  = mdleft
            d['mark_delta_right'] = mdright
            # TODO: Only print Use: line if scaling of axes actually allow entering data.
            d['use_text'] = (r"\textbf{%s} " % _("Use:") +
                             _("Print this page. "
                              "Keep in accessible place with pen. "
                              "Mark one ") +
                             "{\marktikz}" +
                             _(" every day. "
                               "Connect ") +
                             "{\connectmarktikz}" +
                             _(" to yesterday's mark. "
                               "Type marked values into computer as deemed useful."))
            ctx.append(r"""
\begin{scope}[every node/.style={inner sep=0}]
  \newcommand{\marktikz}{\tikz[baseline=-%(mark_delta)fmm]{\plotmark{0mm}{0mm}}}
  \newcommand{\connectmarktikz}{\tikz[baseline=-%(mark_delta)fmm]{
        \begin{scope}[yshift=-0.3mm]
           \draw[plot line,shorten <=1.6mm,shorten >=1.6mm]
             (0,%(mark_delta_left)fmm)
             -- (4.5mm,%(mark_delta_right)fmm);
           \plotmark{0mm}{%(mark_delta_left)fmm}
           \plotmark{4.5mm}{%(mark_delta_right)fmm}
        \end{scope}}}
  \node[anchor=south west]
    at ([xshift=%(sep_west)fmm,yshift=+7.5mm]current page.south west)
    (use text)
    {%(use_text)s};
\end{scope}""" % d)

        if False: # TikZ driver mark in corners
            ctx.append(r"""
\begin{scope}[every node/.style={text=black!50!white,font=}]
  \node[rotate=+45,anchor=north] at ([xshift=+5mm,yshift=-5mm]current page.north west) {\TikZ};
  \node[rotate=-45,anchor=north] at ([xshift=-5mm,yshift=-5mm]current page.north east) {\TikZ};
%%  \node[rotate=-45,anchor=south] at ([xshift=+5mm,yshift=+5mm]current page.south west) {\TikZ};
%%  \node[rotate=+45,anchor=south] at ([xshift=-5mm,yshift=+5mm]current page.south east) {\TikZ};
\end{scope}""" % d)

        if False: # punch hole marks
            ctx.append(r"""
\begin{scope}[every node/.style={},shape=circle,opacity=0.2]
  \begin{scope}[every node/.style={draw=black!30!white,thin,minimum size=14mm}]
    \draw ([yshift=-12mm,xshift=  40mm]current page.north) node {};
    \draw ([yshift=-12mm,xshift= -40mm]current page.north) node {};
%%     \draw ([yshift=-12mm,xshift= 120mm]current page.north) node {};
%%     \draw ([yshift=-12mm,xshift=-120mm]current page.north) node {};
  \end{scope}
  \begin{scope}[every node/.style={draw=black!30!white,line width=0.75mm,minimum size=6mm}]
    \draw ([yshift=-12mm,xshift=  40mm]current page.north) node {};
    \draw ([yshift=-12mm,xshift= -40mm]current page.north) node {};
%%     \draw ([yshift=-12mm,xshift= 120mm]current page.north) node {};
%%     \draw ([yshift=-12mm,xshift=-120mm]current page.north) node {};
  \end{scope}
\end{scope}""" % d)

        d['weight_label_text'] = _(r'weight in %s') % r'\bfseries kg'
        if self.show_bmi: # label vertical axes
            d['bmi_label_text']    = (_(r'%s for height %.2f\,m')
                                      % (r'\textbf{BMI}', self.height))
            ctx.append(r"""
%% axis labels
\begin{scope}[every node/.style={rotate=90,inner sep=0}]
  \coordinate (bmi axis label top)    at ([yshift=+2em]current page.center);
  \coordinate (bmi axis label bottom) at ([yshift=-2em]current page.center);
  \coordinate (bmi axis label west)   at ([xshift=-0.7ex]bmilabel bounding box.west);
  \coordinate (bmi axis label east)   at ([xshift=+2.2ex]bmilabel bounding box.east);

  \node[anchor=base east,text=black] at (bmi axis label bottom -| bmi axis label east) {%(weight_label_text)s};
  \node[anchor=base west,text=red]   at (bmi axis label top    -| bmi axis label east) {%(bmi_label_text)s};

  \node[anchor=base east,text=black] at (bmi axis label bottom -| bmi axis label west) {%(weight_label_text)s};
  \node[anchor=base west,text=red]   at (bmi axis label top    -| bmi axis label west) {%(bmi_label_text)s};
\end{scope}""" % d)
        else:
            ctx.append(r"""
%% axis labels
\begin{scope}[every node/.style={rotate=90,inner sep=0}]
  \coordinate (kg axis label west)   at ([xshift=-1.7ex]kglabel bounding box.west);
  \coordinate (kg axis label east)   at ([xshift=+3.2ex]kglabel bounding box.east);

  \node[anchor=base] at (current page.center -| kg axis label east) {%(weight_label_text)s};
  \node[anchor=base] at (current page.center -| kg axis label west) {%(weight_label_text)s};
\end{scope}""" % d)

        ctx.append(r"""
\end{scope}
\end{tikzpicture}
\end{document}
""" % d)


    def render_plot_value_line_begin(self, ctx, shorten_segments):
        self.render_comment(ctx, 'plot line and points')
        if shorten_segments:
            ctx.append(r'\begin{scope}[plot marked line]')
        else:
            ctx.append(r'\begin{scope}[plot line]')


    def render_plot_value_line_end(self, ctx):
        ctx.append(r'\end{scope}')


    def render_plot_value_line_segment(self, ctx, point1, point2):
        (x1, y1) = point1
        (x2, y2) = point2
        ctx.append('\\draw[] '
                   '([xshift=%fmm,yshift=%fmm]current page.south west) -- '
                   '([xshift=%fmm,yshift=%fmm]current page.south west)'
                   ';' % (x1, y1, x2, y2))


    def render_plot_stem_point(self, ctx, point, color):
        (x, y) = point
        d = { 'x': x,
              'y': y,
              }
        ctx.append(r'\definecolor{plotmavglinecolor}{rgb}{%f, %f, %f}' % color)
        ctx.append('\\path[plot stem point,draw=plotmavglinecolor] '
                   '([xshift=%(x)fmm,yshift=%(y)fmm]current page.south west) '
                   'circle'
                   ';'
                   % d)


    def render_plot_mavg_segment(self, ctx, point1, point2, color):
        (x1, y1) = point1
        (x2, y2) = point2
        ctx.append(r'\definecolor{plotmavglinecolor}{rgb}{%f, %f, %f}' % color)
        d = { 'x1': x1,
              'y1': y1,
              'x2': x2,
              'y2': y2,
              'lw': 2.0 * self.plot_line_width,
              }
        ctx.append(r'\draw[line width=%(lw)fpt,draw=plotmavglinecolor,line cap=round] '
                   '([xshift=%(x1)fmm,yshift=%(y1)fmm]current page.south west) -- '
                   '([xshift=%(x2)fmm,yshift=%(y2)fmm]current page.south west);'
                   % d)


    def render_plot_stem(self, ctx, coords, color):
        (x, y, ay) = coords
        d = { 'x': x,
              'y': y,
              'ay': ay,
              'lw': self.plot_line_width,
              }
        ctx.append(r'\definecolor{plotstemcolor}{rgb}{%f, %f, %f}' % color)
        ctx.append('\\draw[line width=%(lw)fpt,draw=plotstemcolor,line cap=round]'
                   '([xshift=%(x)fmm,yshift=%(y)fmm]current page.south west) -- '
                   '([xshift=%(x)fmm,yshift=%(ay)fmm]current page.south west)'
                   ';'
                   % d)


    def render_plot_point(self, ctx, point):
        (x, y) = point
        d = { 'x': x,
              'y': y,
              }
        ctx.append('\\draw[plot point]'
                   '([xshift=%(x)fmm,yshift=%(y)fmm]current page.south west) -- '
                   '([xshift=%(x)fmm,yshift=%(y)fmm]current page.south west)'
                   ';'
                   % d)


    def render_plot_mark(self, ctx, point):
        (x, y) = point
        md = self.mark_delta
        d = { 'x1': x-md,
              'x2': x+md,
              'y1': y-md,
              'y2': y+md,
              }
        ctx.append('\\draw[plot mark]'
                   '([xshift=%(x1)fmm,yshift=%(y1)fmm]current page.south west) -- '
                   '([xshift=%(x2)fmm,yshift=%(y2)fmm]current page.south west)'
                   '([xshift=%(x2)fmm,yshift=%(y1)fmm]current page.south west) -- '
                   '([xshift=%(x1)fmm,yshift=%(y2)fmm]current page.south west)'
                   ';'
                   % d)


    def render_comment(self, ctx, msg):
        ctx.append('%% %s' % msg)


    def render_day_begin(self, ctx):
        ctx.append('\\begin{scope}['
                   'every rectangle node/.style={inner xsep=0,anchor=base},'
                   'line cap=round]')


    def render_day_end(self, ctx):
        ctx.append('\\end{scope}\n')


    def render_time_tick(self, ctx, style, date, label_str, id_str):
        d = style
        ctx.append('\definecolor{daylinecolor}{rgb}{%f, %f, %f}' % d.line_color)
        ctx.append('\definecolor{daytextcolor}{rgb}{%f, %f, %f}' % d.font_color)
        d['day_line_style'] = "line width=%fpt,draw=daylinecolor" % d.line_width

        if d.font_bold:
            d['day_text_style'] = "rotate=%d,text=daytextcolor,font=\\sffamily\\bfseries" % style.rotate_labels
        else:
            d['day_text_style'] = "rotate=%d,text=daytextcolor,font=\\sffamily" % style.rotate_labels

        x = self._get_x(date)
        ctx.append('%% date %s' % id_str)
        ctx.append('\\draw[%s] '
                   '([xshift=%fmm,yshift=-%fmm]current page.north west)'
                   ' -- '
                   '([xshift=%fmm,yshift=%fmm]current page.south west)'
                   ';' % (d.day_line_style, x, d.begin_ofs, x, d.end_ofs))
        if d.do_label:
            yshift = 2.0
            ctx.append('\\node[%s] at '
                       '([xshift=%fmm,yshift=-%fmm]current page.north west)'
                       '{%s}'
                       ';' % (d.day_text_style, x, d.begin_ofs-yshift, label_str))
            ctx.append('\\node[%s] at '
                       '([xshift=%fmm,yshift=+%fmm]current page.south west)'
                       '{%s}'
                       ';' % (d.day_text_style, x, d.end_ofs-yshift, label_str))


    def render_axis_bmi_begin(self, ctx):
        ctx.append('\\begin{scope}[on background layer]')


    def render_axis_bmi_end(self, ctx):
        ctx.append('\\end{scope}\n')


    def render_axis_bmi_tick(self, ctx, y, bmi, strbmi, p):
        p['line_style'] = "line width=%fpt, draw=bmilinecolor, line cap=round" % p.line_width

        if p.font_bold:
            p['text_style'] = "text=bmitextcolor, font=\\sffamily\\bfseries"
        else:
            p['text_style'] = "text=bmitextcolor, font=\\sffamily"

        ctx.append('\definecolor{bmilinecolor}{rgb}{%f, %f, %f}' % p.line_color)
        ctx.append('\definecolor{bmitextcolor}{rgb}{%f, %f, %f}' % p.font_color)

        p.y = y
        p['bmil'] = strbmi.replace('.','_')
        p['strbmi'] = strbmi
        fs = ['%% BMI %(strbmi)s',
              '\\draw[%(line_style)s]'
              ' ([xshift=%(begin_ofs)fmm,yshift=%(y)fmm]current page.south west)'
              ' -- ([xshift=-%(end_ofs)fmm,yshift=%(y)fmm]current page.south east);']
        if p.do_label:
            fs.extend([
                    '\\node[anchor=east,%(text_style)s] '
                    'at ([xshift=%(begin_ofs)fmm,yshift=%(y)fmm]current page.south west)'
                    ' (bmi label west %(bmil)s)'
                    ' {%(strbmi)s};',
                    '\\node[anchor=west,%(text_style)s]'
                    ' at ([xshift=-%(end_ofs)fmm,yshift=%(y)fmm]current page.south east)'
                    ' (bmi label east %(bmil)s)'
                    ' {%(strbmi)s};',
                    ''])
            self.bmi_label_nodes.append('(bmi label west %(bmil)s)' % p)
            self.bmi_label_nodes.append('(bmi label east %(bmil)s)' % p)
        ctx.extend([s % p for s in fs])


    def render_calendar_range(self, ctx, date_range, is_first_last,
                              level, label_str, p, north=False):

        # Caution: render_ticks_days() must be run earlier so that
        #          nodes with lables will be available when referenced.

        (begin_date, end_date) = date_range
        (begin_first, end_last) = is_first_last
        yofs = 2.0 + 1.5 + 3.5 * (level + 0)

        if north:
            p.relnode = 'current page.north west'
            p.yofs = - (self.sep_north - yofs)
        else:
            p.relnode = 'current page.south west'
            p.yofs = + (self.sep_south - yofs)

        ctx.append('%% level %d range %s from %s to %s'
                 % (level, label_str, begin_date, end_date))

        delta_x = self.delta_x_per_day
        range_distance = 1.25
        if delta_x >= range_distance:
            dx2 = 0.5 * (delta_x - range_distance)
        else:
            dx2 = 0.0

        # FIXME: Idea: Add locals() to p as another dict to look up stuff from?
        p.begin_x = self._get_x(begin_date) - dx2
        p.end_x   = self._get_x(end_date)   + dx2
        p.label_str = label_str

        # TODO: Support unused line color, font bold, etc. pp.
        if begin_first: a1 = '|'
        else:           a1 = ''
        if end_last:    a2 = '|'
        else:           a2 = ''
        p.arrows = '%s-%s' % (a1, a2)

        # print "Cal range %s (%s): %s to %s" % (label, yofs, first_day, last_day)
        ctx.append('\definecolor{calrangelinecolor}{rgb}{%f, %f, %f}' % p.line_color)
        ctx.append('\definecolor{calrangetextcolor}{rgb}{%f, %f, %f}' % p.font_color)
        ctx.append('\\path[draw=calrangelinecolor, line width=%(line_width)fpt, '
                   '       arrows=%(arrows)s, >=angle 90, line cap=round]'
                   ' ([xshift=%(begin_x)fmm,yshift=%(yofs)fmm]%(relnode)s)'
                   ' -- ([xshift=%(end_x)fmm,yshift=%(yofs)fmm]%(relnode)s)' % p)
        if label_str:
            ctx.append('  node[midway,fill=white,inner xsep=1pt,inner ysep=0,text=calrangetextcolor] {%(label_str)s}' % p)
        ctx.append(';')


    def render_axis_kg_begin(self, ctx):
        self.render_comment(ctx, 'kg axis lines')
        ctx.append('\\begin{scope}[line cap=round]')


    def render_axis_kg_end(self, ctx):
        ctx.append('\\end{scope}')
        ctx.append('')


    def render_axis_kg_tick(self, ctx, y, kg_str, p):
        ctx.append('\definecolor{kglinecolor}{rgb}{%f, %f, %f}' % p.line_color)
        ctx.append('\definecolor{kgtextcolor}{rgb}{%f, %f, %f}' % p.font_color)
        p['line_style'] = "line width=%fpt,draw=kglinecolor" % p.line_width

        if p.font_bold:
            p['text_style'] = "text=kgtextcolor,font=\\sffamily\\bfseries"
        else:
            p['text_style'] = "text=kgtextcolor,font=\\sffamily"

        p.y = y
        p.kg_str = kg_str
        p.kg_str_id = kg_str.replace('.', '_')

        fs = ['%% %(kg_str)s kg',
              '\\draw[%(line_style)s]'
              ' ([xshift=%(begin_ofs)fmm,yshift=%(y)fmm]current page.south west)'
              ' -- ([xshift=-%(end_ofs)fmm,yshift=%(y)fmm]current page.south east);',
              ]
        ctx.extend([ s % p for s in fs ])

        if p.do_label:
            fs = ['\\node[anchor=east,%(text_style)s]'
                  ' at ([xshift=%(begin_ofs)fmm,yshift=%(y)fmm]current page.south west)'
                  ' (kg label west %(kg_str_id)s)'
                  ' {%(kg_str)s};',
                  '\\node[anchor=west,%(text_style)s]'
                  ' at ([xshift=-%(end_ofs)fmm,yshift=%(y)fmm]current page.south east)'
                  ' (kg label east %(kg_str_id)s)'
                  ' {%(kg_str)s};',
                  ]
            self.kg_label_nodes.append('(kg label west %(kg_str_id)s)' % p)
            self.kg_label_nodes.append('(kg label east %(kg_str_id)s)' % p)
            ctx.extend([ s % p for s in fs ])

        ctx.append('')


    def render_initials(self, ctx):
        ctx.append('\\node[anchor=south east]'
                   ' at ([xshift=%fmm,yshift=%fmm]current page.south east)'
                   ' {%s};' % (-7.0, +7.0, self.initials))
        ctx.append('\\node[anchor=south west]'
                   ' at ([xshift=%fmm,yshift=%fmm]current page.south west)'
                   ' {%s};' % (+7.0, +7.0, self.initials))
        ctx.append('\\node[anchor=north east]'
                   ' at ([xshift=%fmm,yshift=%fmm]current page.north east)'
                   ' {%s};' % (-7.0, -7.0, self.initials))
        ctx.append('\\node[anchor=north west]'
                   ' at ([xshift=%fmm,yshift=%fmm]current page.north west)'
                   ' {%s};' % (+7.0, -7.0, self.initials))
        ctx.append('')


########################################################################
