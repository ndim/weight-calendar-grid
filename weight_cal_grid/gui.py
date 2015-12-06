########################################################################


"""Implement Graphical User Interface (GUI)"""


##################################################################################


import argparse
import datetime
import os
import subprocess
import sys
import yaml

from gi.repository import Gio, Gtk, cairo, GLib, Poppler
from pprint import pprint


##################################################################################


from .      import generate_grid
from .utils import get_earliest_sunday, get_latest_sunday
from .      import drivers
from .      import version
from .i18n  import install_translation
from .utils import InternalLogicError


##################################################################################


class User(object):

    def __init__(self, nick, lang, height_cm, weight_lo, weight_hi, print_user):
        super(User,self).__init__()
        self.nick = nick
        self.lang = lang
        self.height_cm = height_cm
        if weight_lo and weight_hi:
            self.weight_lo = weight_lo
            self.weight_hi = weight_hi
        elif weight_lo and not weight_hi:
            self.weight_lo = weight_lo
            self.weight_hi = self.weight_lo + 11
        elif weight_hi and not weight_lo:
            self.weight_hi = weight_hi
            self.weight_lo = self.weight_hi - 11
        else:
            assert(False) # We need at least one of weight_hi or weight_lo set
        self.print_user = print_user

    def __str__(self):
        return ('User(%s, lang=%s, %dcm, %dkg..%dkg, print=%s)' %
                (repr(self.nick), repr(self.lang), self.height_cm,
                 self.weight_lo, self.weight_hi, self.print_user))

    def for_yaml(self):
        return (self.nick,
                {
                    'print': self.print_user,
                    'lang': self.lang,
                    'height': self.height_cm,
                    'weight_lo': self.weight_lo,
                    'weight_hi': self.weight_hi,
                })

    @staticmethod
    def column_list():
        return [
            ('nick', str, ),
            ('lang', str, ),
            ('height', int, ),
            ('weight_lo', int, ),
            ('weight_hi', int, ),
            ('print', bool, ),
        ]

    @staticmethod
    def column_map():
        ls = [ (field_name, n)
               for n, (field_name, field_type, ) in enumerate(User.column_list()) ]
        return dict(ls)

    @staticmethod
    def new_list_store():
        ls = [ field_type
               for field_name, field_type in User.column_list() ]
        return Gtk.ListStore(*ls)

    @staticmethod
    def new_tree_view_column(field_name, renderer, colparm_name):
        return Gtk.TreeViewColumn(field_name, renderer,
                                  **{colparm_name: User.column_map()[field_name]})

##################################################################################


class SaneCalendar(Gtk.Calendar):

    def get_date(self):
        y, m, d = super(SaneCalendar, self).get_date()
        return (y, m+1, d)

    @property
    def datetime_date(self):
        y, m, d = self.get_date()
        return datetime.date(y, m, d)

    def select_month(self, month, year):
        return super(SaneCalendar, self).select_month(month-1, year)

    def get_property(self, propname):
        if propname == 'month':
            return super(SaneCalendar, self).get_property(propname)+1
        else:
            return super(SaneCalendar, self).get_property(propname)

    def set_property(self, propname, value):
        if propname == 'month':
            return super(SaneCalendar, self).set_property(propname, value-1)
        else:
            return super(SaneCalendar, self).set_property(propname, value)


##################################################################################


class WeightGrid(Gtk.DrawingArea):

    def __init__(self):
        super(WeightGrid, self).__init__()
        self.set_size_request(297, 210)
        self.begin_date = None
        self.end_date = None
        self.user_nick = None
        self.user_lang = None
        self.user_height = None
        self.user_weight_lo = None
        self.user_weight_hi = None

    def set_dates(self, begin_date, end_date):
        if ((self.begin_date == begin_date) and
            (self.end_date == end_date)):
            return False
        else:
            self.begin_date = begin_date
            self.end_date = end_date
            return True

    def set_user(self, nick, lang, height, weight_lo, weight_hi):
        if ((self.user_nick == nick) and
            (self.user_lang == lang) and
            (self.user_height == height) and
            (self.user_weight_lo == weight_lo) and
            (self.user_weight_hi == weight_hi)):
            return False
        else:
            self.user_nick = nick
            self.user_lang = lang
            self.user_height = height
            self.user_weight_lo = weight_lo
            self.user_weight_hi = weight_hi
            return True

    def do_draw(self, cr):
        if not (self.user_nick and self.user_height and
                self.user_weight_lo and self.user_weight_hi and
                self.begin_date and self.end_date):
            return

        # set up scaling
        drv = drivers.Cairo.CairoDriver
        width  = self.get_allocated_width()
        height = self.get_allocated_height()

        w_scale = float(width)  / float(drv.page_width)
        h_scale = float(height) / float(drv.page_height)
        if w_scale < h_scale:
            cr.scale(w_scale, w_scale)
        else:
            cr.scale(h_scale, h_scale)

        # draw the grid
        generate_grid(
            0.01 * self.user_height,
            (self.user_weight_lo, self.user_weight_hi),
            (self.begin_date, self.end_date),
            infile=None, # open('ndim.dat', 'r'),
            driver_cls=drivers.Cairo.CairoDriver,
            output_format=drivers.Cairo.CairoOutputFormat.name,
            outfile=cr,
            keep_tmp_on_error=False,
            history_mode=False,
            initials=self.user_nick,
            lang=self.user_lang)


##################################################################################


class WeightGridWindow(Gtk.Window):

    def __init__(self, app):
        title = _("Weight Calendar Grid")

        # Only start updating the storage after all the initial events
        # while setting up the GUI with still incomplete data have
        # finished firing.
        self.do_update_storage = False

        super(WeightGridWindow, self).__init__(title=title, application=app)

        self.set_icon_from_file(os.path.join(os.path.dirname(__file__),
                                             'wcg-gui-icon.png'))

        self.data_fname = os.path.expanduser('~/.weight-calendar-grid.yaml')

        self.weight_grid = WeightGrid()

        self.weight_delta = 11
        self.set_default_size(960, 960)
        self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        btn = Gtk.Button.new_with_mnemonic(_("_Quit program"))
        btn.set_tooltip_text(_("Quit the program. "
                               "Expect strange things if there are PDF "
                               "generation jobs or print jobs running "
                               "in the background."))
        btn.connect('clicked', self.on_quit_clicked)
        self.vbox.pack_start(btn, False, False, 0)

        self.vbox.pack_start(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL),
                             False, False, 0)

        lbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        al = Gtk.Label.new_with_mnemonic(_("_Begin date"))
        self.calendar_begin = SaneCalendar()
        self.calendar_begin.set_display_options(Gtk.CalendarDisplayOptions.SHOW_HEADING |
                                                Gtk.CalendarDisplayOptions.SHOW_DAY_NAMES |
                                                Gtk.CalendarDisplayOptions.SHOW_WEEK_NUMBERS)
        al.set_mnemonic_widget(self.calendar_begin)
        lbox.pack_start(al, False, False, 0)
        btn = Gtk.Button.new_with_mnemonic(_("_Today"))
        btn.set_tooltip_text(_("Set begin date to today"))
        btn.connect('clicked', self.on_today_clicked)
        lbox.pack_end(btn, False, False, 0)
        btn = Gtk.Button.new_with_mnemonic(_("_Latest Sun"))
        btn.set_tooltip_text(_("Move the begin date to latest sunday "
                               "(same day or in the past)"))
        btn.connect('clicked', self.on_latest_sunday_clicked)
        lbox.pack_end(btn, False, False, 0)
        btn = Gtk.Button.new_with_mnemonic(_("_Earliest Sun"))
        btn.set_tooltip_text(_("Move the begin date to earliest sunday "
                               "(same day or in the future)"))
        btn.connect('clicked', self.on_earliest_sunday_clicked)
        lbox.pack_end(btn, False, False, 0)
        self.vbox.pack_start(lbox, False, False, 0)
        self.vbox.pack_start(self.calendar_begin, False, False, 0)
        self.calendar_begin.connect('day-selected', self.on_begin_selected)

        self.end_label = Gtk.Label.new_with_mnemonic(_("_End"))
        self.end_label.set_property('xalign', 0)
        self.vbox.pack_start(self.end_label, False, False, 0)
        self.calendar_end = SaneCalendar()
        self.calendar_end.set_display_options(Gtk.CalendarDisplayOptions.SHOW_HEADING |
                                              Gtk.CalendarDisplayOptions.SHOW_DAY_NAMES |
                                              Gtk.CalendarDisplayOptions.SHOW_WEEK_NUMBERS)
        al.set_mnemonic_widget(self.calendar_end)
        self.vbox.pack_start(lbox, False, False, 0)
        self.vbox.pack_start(self.calendar_end, False, False, 0)
        self.calendar_end.connect('day-selected', self.on_end_selected)

        lbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        al = Gtk.Label.new_with_mnemonic(_("_Period"))
        lbox.pack_start(al, False, False, 0)
        btn = Gtk.Button.new_with_mnemonic(_("Ad_vance"))
        btn.set_tooltip_text(_("Move the dates one period into the future"))
        btn.connect('clicked', self.move_end_to_begin_clicked)
        lbox.pack_end(btn, False, False, 0)
        btn = Gtk.Button.new_with_mnemonic(_("Re_cede"))
        btn.set_tooltip_text(_("Move the dates one period into the past"))
        btn.connect('clicked', self.move_begin_to_end_clicked)
        lbox.pack_end(btn, False, False, 0)
        self.vbox.pack_start(lbox, False, False, 0)

        self.period_weeks = Gtk.SpinButton.new_with_range(6, 14, 1)
        self.period_weeks.set_tooltip_text(_("Duration of the period to display"))
        al.set_mnemonic_widget(self.period_weeks)
        self.vbox.pack_start(al, False, False, 0)
        lbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        lbox.pack_start(self.period_weeks, False, False, 0)
        lbox.pack_start(Gtk.Label(_("weeks")), False, False, 0)
        self.date_lbl = Gtk.Label("", selectable=True)
        lbox.pack_end(self.date_lbl, False, False, 0)
        self.vbox.pack_start(lbox, False, False, 0)
        self.period_weeks.connect('changed', self.on_period_weeks_changed)

        date_begin = get_latest_sunday(self.calendar_begin.datetime_date)

        self.vbox.pack_start(Gtk.Separator.new(Gtk.Orientation.HORIZONTAL),
                             False, False, 0)

        self.lang_store = Gtk.ListStore(str)
        self.lang_store.append([None])
        self.lang_store.append(['de'])
        self.lang_store.append(['en'])

        self.user_store = Gtk.ListStore(str, str, int, int, int, bool)
        self.__marked_users = 0

        self.yaml_data = None
        parsed_yaml_data = None
        try:
            with open(self.data_fname, 'r') as stream:
                self.yaml_data = stream.read()
                parsed_yaml_data = yaml.safe_load(self.yaml_data)
        except EnvironmentError as err:
            print("Error opening %s:" % repr(self.data_fname), err)
            # default values
            parsed_yaml_data = {'start_date': get_latest_sunday(datetime.date.today()),
                                'weeks': 8,
                                'users': {}}

        # pprint(parsed_yaml_data)
        self.period_weeks.set_value(parsed_yaml_data['weeks'])
        date_begin = parsed_yaml_data['start_date']
        for (nick, user_data) in parsed_yaml_data['users'].items():
            self.user_store.append([nick,
                                    user_data['lang'],
                                    user_data['height'],
                                    user_data['weight_lo'],
                                    user_data['weight_hi'],
                                    user_data['print']])
            if user_data['print']:
                self.__marked_users += 1
            else:
                pass

        self.calendar_begin.select_month(date_begin.month, date_begin.year)
        self.calendar_begin.select_day(date_begin.day)

        self.treeview = Gtk.TreeView(model=self.user_store)
        self.treeview.set_headers_clickable(True)

        renderer_print = Gtk.CellRendererToggle()
        renderer_print.connect('toggled', self.on_user_print_toggled)
        renderer_print.set_property('activatable', True)
        # column_print = Gtk.TreeViewColumn(_("print"), renderer_print, active=5)
        column_print = Gtk.TreeViewColumn(None, renderer_print, active=5)
        self.treeview.append_column(column_print)

        renderer_nick = Gtk.CellRendererText()
        renderer_nick.connect('edited', self.on_user_nick_edited)
        renderer_nick.set_property('editable', True)
        self.column_nick = Gtk.TreeViewColumn(_("nick"), renderer_nick, text=0)
        self.treeview.append_column(self.column_nick)

        renderer_lang = Gtk.CellRendererCombo()
        renderer_lang.set_property('editable', True)
        renderer_lang.set_property('model', self.lang_store)
        renderer_lang.set_property('text-column', 0)
        renderer_lang.set_property('has-entry', False)
        renderer_lang.connect('edited', self.on_user_lang_changed)
        column_lang  = Gtk.TreeViewColumn(_("lang"), renderer_lang, text=1)
        self.treeview.append_column(column_lang)

        height_adj = Gtk.Adjustment(lower=100, upper=280,
                                    step_increment=1, page_increment=10,
                                    page_size=10)

        renderer_height = Gtk.CellRendererSpin()
        renderer_height.set_property('adjustment', height_adj)
        renderer_height.connect('edited', self.on_user_height_edited)
        renderer_height.set_property('editable', True)
        column_height = Gtk.TreeViewColumn(_("height in cm"),
                                           renderer_height, text=2)
        column_height.set_resizable(True)
        column_height.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
        self.treeview.append_column(column_height)

        weight_adj = Gtk.Adjustment(lower=40, upper=400,
                                    step_increment=1, page_increment=10,
                                    page_size=10)

        renderer_weight_lo = Gtk.CellRendererSpin()
        renderer_weight_lo.set_property('adjustment', weight_adj)
        renderer_weight_lo.connect('edited', self.on_user_weight_lo_edited)
        renderer_weight_lo.set_property('editable', True)
        column_weight_lo = Gtk.TreeViewColumn(_("weight(min)"),
                                              renderer_weight_lo, text=3)
        self.treeview.append_column(column_weight_lo)

        renderer_weight_hi = Gtk.CellRendererSpin()
        renderer_weight_hi.set_property('adjustment', weight_adj)
        renderer_weight_hi.connect('edited', self.on_user_weight_hi_edited)
        renderer_weight_hi.set_property('editable', True)
        column_weight_hi = Gtk.TreeViewColumn(_("weight(max)"),
                                              renderer_weight_hi, text=4)
        self.treeview.append_column(column_weight_hi)

        self.__user_sel_widgets = []
        self.__users_marked_widgets = []

        self.print_user_btn = Gtk.Button.new_with_mnemonic(_("Print _selected user"))
        self.__user_sel_widgets.append(self.print_user_btn)
        self.print_user_btn.set_tooltip_text(_("Generate and print grid "
                                               "for the one selected user"))
        self.print_user_btn.connect('clicked', self.on_print_selected_user_clicked)
        self.vbox.pack_start(self.print_user_btn, False, False, 0)

        btn = Gtk.Button.new_with_mnemonic(_("Print _all marked users"))
        self.__users_marked_widgets.append(btn)
        btn.set_tooltip_text(_("Generate and print grid for all marked user"))
        btn.connect('clicked', self.on_print_user_list_clicked)
        self.vbox.pack_start(btn, False, False, 0)

        # Table of actions:
        #  (generate, print (ourselves), open in evince)
        #      x
        #  (one selected user, all marked users i.e. family)
        tbl = Gtk.Table(2, 3, False)
        def add_btn(x, y, title, fun, tooltip=None):
            btn = Gtk.Button(title)
            btn.connect('clicked', fun)
            if tooltip:
                btn.set_tooltip_text(tooltip)
            tbl.attach(btn, x, x+1, y, y+1)
            return btn
        self.gen1_btn = add_btn(0, 0, _("Generate1"), self.on_gen1_clicked,
                                _("Generate PDF for selected user"))
        self.prt1_btn = add_btn(1, 0, _("Print1"), self.on_prt1_clicked,
                                _("Print the PDF for selected user"))
        self.evi1_btn = add_btn(2, 0, _("View1"), self.on_evi1_clicked,
                                _("View the PDF for selected user in evince"))
        self.genf_btn = add_btn(0, 1, _("GenerateF"), self.on_genf_clicked,
                                _("Generate PDF for all marked users"))
        self.prtf_btn = add_btn(1, 1, _("PrintF"), self.on_prtf_clicked,
                                _("Print the PDF for all marked users"))
        self.evif_btn = add_btn(2, 1, _("ViewF"), self.on_evif_clicked,
                                _("View the PDF for all marked users in evince"))
        self.__user_sel_widgets.extend([self.gen1_btn, self.prt1_btn, self.evi1_btn])
        self.__users_marked_widgets.extend([self.genf_btn, self.prtf_btn, self.evif_btn])
        self.vbox.pack_start(tbl, False, False, 0)

        lbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        al = Gtk.Label.new_with_mnemonic(_("_User list"))
        al.set_mnemonic_widget(self.treeview)
        lbox.pack_start(al, False, False, 0)
        btn = Gtk.Button.new_with_mnemonic(_("_New user"))
        btn.set_tooltip_text(_("Add new user to list of users. "
                               "You must then enter a nick name."))
        btn.connect('clicked', self.on_new_user_clicked)
        lbox.pack_end(btn, False, False, 0)
        self.delete_user_btn = Gtk.Button.new_with_mnemonic(_("_Delete user"))
        self.__user_sel_widgets.append(self.delete_user_btn)
        self.delete_user_btn.set_tooltip_text(_("Remove selected user from "
                                                "the list of users"))
        self.delete_user_btn.connect('clicked', self.on_delete_user_clicked)
        lbox.pack_end(self.delete_user_btn, False, False, 0)
        self.vbox.pack_start(lbox, False, False, 0)
        self.vbox.pack_start(self.treeview, False, False, 0)

        self.user_selection = self.treeview.get_selection()
        self.user_selection.connect('changed', self.on_user_selection_changed)

        self.vbox.pack_start(Gtk.Label(_("All heights in <b>cm</b>. "
                                         "All weights in <b>kg</b>."), xalign=0,
                                       use_markup=True),
                             False, False, 0)

        self.hbox.pack_start(self.vbox, False, False, 6)

        self._user_sel_set_sensitive(False)
        self.users_marked_changed()

        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.ALWAYS, Gtk.PolicyType.ALWAYS)
        sw.add(self.weight_grid)
        #sw.add_with_viewport(self.weight_grid)
        self.hbox.pack_start(sw, True, True, 0)
        self.add(self.hbox)

        # Only start updating the storage after all the initial events
        # while setting up the GUI with still incomplete data have
        # finished firing.
        self.do_update_storage = True

    def on_gen1_clicked(self, widget):
        pass

    def on_prt1_clicked(self, widget):
        pass

    def on_evi1_clicked(self, widget):
        pass

    def on_genf_clicked(self, widget):
        pass

    def on_prtf_clicked(self, widget):
        pass

    def on_evif_clicked(self, widget):
        pass

    def on_quit_clicked(self, widget):
        # For some reason, the calling the documented Gtk.main_quit()
        # does not quit the program. self.destroy() does, however.
        self.destroy()

    @property
    def marked_users(self):
        return self.__marked_users

    @marked_users.setter
    def marked_users(self, value):
        changed = (self.__marked_users != value)
        self.__marked_users = value
        if changed:
            self.users_marked_changed()

    def users_marked_changed(self):
        """Reflect the number of marked users in GUI widget sensitivity"""
        self._users_marked_set_sensitive(bool(self.__marked_users))

    def _users_marked_set_sensitive(self, value):
        for btn in self.__users_marked_widgets:
            btn.set_sensitive(value)

    @property
    def period_in_days(self):
        return 7*self.period_weeks.get_value_as_int()

    def popen_print_user(self, output_fname, user):
        begin_str = self.calendar_begin.datetime_date.strftime('%Y-%m-%d')
        script_fname = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                    'wcg-cli')
        if user.lang:
            lang_args = ['--lang=%s' % user.lang]
        else:
            lang_args = []

        args = ([script_fname,
                 '--driver=%s' % 'tikz',
                 '--initials=%s' % user.nick,
                ]
                + lang_args +
                ['--output=%s' % output_fname,
                 '--height=%.2f' % (0.01 * user.height_cm),
                 '--begin-date=%s' % begin_str,
                 '--end-date=%s' % self.calendar_end.datetime_date.strftime('%Y-%m-%d'),
                 '--weight=%d-%d' % (user.weight_lo, user.weight_hi)
                ])
        print('CMD:', ' '.join(args))
        proc = subprocess.Popen(args,
                                executable=script_fname,
                                stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                close_fds=True,
                                shell=False)
        return proc

    def ask_save_filename(self, default_fname):
        dialog = Gtk.FileChooserDialog(_("Save as"),
                                       self,
                                       Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        dialog.set_do_overwrite_confirmation(True)
        if False:
            dialog.set_current_folder()
            dialog.set_filename()
        else:
            dialog.set_current_name(default_fname)

        filter_pdf = Gtk.FileFilter()
        filter_pdf.set_name(_("Portable Document Format (PDF)"))
        filter_pdf.add_mime_type("application/pdf")
        dialog.add_filter(filter_pdf)

        filter_any = Gtk.FileFilter()
        filter_any.set_name(_("Any files"))
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        response = dialog.run()
        fname = dialog.get_filename()
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            return fname
        elif response == Gtk.ResponseType.CANCEL:
            return None


    def on_print_selected_user_clicked(self, btn):
        model, treeiter = self.user_selection.get_selected()
        if treeiter == None:
            return

        user = User(*model[treeiter][:])
        if not user:
            return
        output_fname = self.ask_save_filename(self.output_filename(user))
        if not output_fname:
            return

        # FIXME: Show in UI when PDF generation is running.
        # FIXME: Properly handle UI quit while PDF generation is still running.

        print(_("Generating PDF for single user:"), output_fname)
        proc = self.popen_print_user(output_fname, user)
        while proc.returncode == None:
            while Gtk.events_pending():
                Gtk.main_iteration()
            proc.poll()

        print("Ret code for %s:" % output_fname, proc.returncode)
        # FIXME: hard coded charset
        sys.stdout.write(proc.stdout.read().decode('utf-8'))

        self.print_pdf(output_fname)

    def output_filename(self, user=None):
        # FIXME: We need unique file names even if two users have the same nick!
        begin_str = self.calendar_begin.datetime_date.strftime('%Y-%m-%d')
        if user:
            return 'WCG-USER-%s-%s.pdf' % (user.nick, begin_str, )
        else:
            return 'WCG-FAMILY-%s.pdf'% begin_str

    def print_pdf(self, pdf_fname):

        dlg = Gtk.MessageDialog(
            self,
            Gtk.DialogFlags.DESTROY_WITH_PARENT |
            Gtk.DialogFlags.MODAL,
            Gtk.MessageType.QUESTION,
            Gtk.ButtonsType.YES_NO,
            _("Continue printing %s? "
              "wcg-gui will print lines much thicker than they should be.") %
            pdf_fname
        )
        dlg.format_secondary_markup(
            _("We strongly suggest to open the generated "
              "PDF file in <i>evince</i> "
              "and print from <i>evince</i> instead."))
        response = dlg.run()
        dlg.destroy()
        if response == Gtk.ResponseType.YES:
            pass
        elif response == Gtk.ResponseType.NO:
            return
        else:
            raise InternalLogicError()

        # printsettings = print_op.get_print_settings()
        printsettings = Gtk.PrintSettings()
        printsettings.set_use_color(True)

        page_setup = Gtk.PageSetup()
        # page_setup.set_paper_size(Gtk.PaperSize.new("A4"))
        page_setup.set_orientation(Gtk.PageOrientation.LANDSCAPE)
        margin_top    = page_setup.get_top_margin(Gtk.Unit.MM)
        margin_right  = page_setup.get_right_margin(Gtk.Unit.MM)
        margin_bottom = page_setup.get_bottom_margin(Gtk.Unit.MM)
        margin_left   = page_setup.get_left_margin(Gtk.Unit.MM)
        # print "Page margins in mm:", margin_top, margin_right, margin_bottom, margin_left

        # page_setup.set_top_margin(   margin_right, Gtk.Unit.MM)
        # page_setup.set_right_margin( margin_bottom, Gtk.Unit.MM)
        # page_setup.set_bottom_margin(margin_left, Gtk.Unit.MM)
        # page_setup.set_left_margin(  margin_top, Gtk.Unit.MM)

        # FIXME: This page/paper margin setup is tupid hack!
        page_setup.set_top_margin(   0.0, Gtk.Unit.MM)
        page_setup.set_right_margin( 0.0, Gtk.Unit.MM)
        page_setup.set_bottom_margin(0.0, Gtk.Unit.MM)
        page_setup.set_left_margin(  0.0, Gtk.Unit.MM)

        print_op = Gtk.PrintOperation()
        print_op.set_print_settings(printsettings)
        print_op.set_job_name(pdf_fname)
        print_op.set_show_progress(True)
        print_op.set_default_page_setup(page_setup)
        print_op.set_track_print_status(True)
        print_op.connect('begin-print', self.begin_print, None)
        print_op.connect('draw-page', self.draw_page, None)

        uri = GLib.filename_to_uri(os.path.abspath(pdf_fname))
        self.doc = Poppler.Document.new_from_file(uri)

        res = print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, self)
        if res == Gtk.PrintOperationResult.ERROR:
            msg = print_op.get_error()
            dlg = Gtk.MessageDialog(self, 0,
                                    Gtk.MessageType.ERROR,
                                    Gtk.ButtonsType.CLOSE,
                                    msg)
            dlg.run()
            dlg.destroy()

        self.doc = None

    def begin_print(self, operation, print_ctx, print_data):
        operation.set_n_pages(self.doc.get_n_pages())

    def draw_page(self, oepration, print_ctx, page_num, print_data):
        cr = print_ctx.get_cairo_context()
        page = self.doc.get_page(page_num)
        page.render(cr)

    def on_print_user_list_clicked(self, btn):

        # FIXME: Show in UI when PDF generation is running.
        # FIXME: Properly handle UI quit while PDF generation is still running.

        family_fname = self.ask_save_filename(self.output_filename())
        if not family_fname:
            return

        # FIXME: Use temp file names for per user PDFs?
        # FIXME: Store all files (family and per user) in specific folder?

        def func(model, path, treeiter, proc_list):
            user = User(*model[treeiter][:])
            if user.print_user:
                print(_("Generating PDF for single user"), user)
                output_fname = self.ask_save_filename(self.output_filename(user))
                proc = self.popen_print_user(output_fname, user)
                proc_list.append((proc, output_fname, ))
            return False

        proc_list = []
        model = self.user_store
        model.foreach(func, proc_list)

        while True:
            while Gtk.events_pending():
                Gtk.main_iteration()

            running = 0
            for proc, fname in proc_list:
                proc.poll()
                if proc.returncode == None:
                    running = running+1

            if running == 0:
                break

        file_names = []
        for proc, fname in proc_list:
            print("Ret code for %s:" % fname, proc.returncode)
            # FIXME: hard coded charset
            sys.stdout.write(proc.stdout.read().decode('utf-8'))
            file_names.append(fname)
        file_names.sort()

        args = (['pdfjoin',
                 '-o', family_fname,
                 '--landscape',
                 '--paper', 'a4paper',
        ] + file_names)
        print(_("Generating family PDF"), family_fname)
        print('CMD:', ' '.join(args))
        proc = subprocess.Popen(args,
                                executable='/usr/bin/pdfjoin',
                                stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                close_fds=True,
                                shell=False)
        while proc.returncode == None:
            while Gtk.events_pending():
                Gtk.main_iteration()
            proc.poll()
        print("Ret code for %s:" % family_fname, proc.returncode)
        # FIXME: hard coded charset
        sys.stdout.write(proc.stdout.read().decode('utf-8'))

        self.print_pdf(family_fname)

    def update_dates(self):
        if self.weight_grid.set_dates(self.calendar_begin.datetime_date,
                                      self.calendar_end.datetime_date):
            self.weight_grid.queue_draw()
            begin_str = self.calendar_begin.datetime_date.strftime('%Y-%m-%d')
            end_str = self.calendar_end.datetime_date.strftime('%Y-%m-%d')
            m = {'begin': begin_str,
                 'end': end_str}
            self.date_lbl.set_text(_("(from %(begin)s to %(end)s)") % m)

    def on_today_clicked(self, btn):
        date_begin = datetime.date.today()
        o = self.calendar_begin.get_date()
        if o == date_begin:
            return
        self.calendar_begin.select_month(date_begin.month, date_begin.year)
        self.calendar_begin.select_day(date_begin.day)
        self.update_storage()
        self.update_dates()

    def on_latest_sunday_clicked(self, btn):
        o = self.calendar_begin.datetime_date
        #print "on_latest_sunday for ", year, month, day
        date_begin = get_latest_sunday(o)
        if o == date_begin:
            return
        self.calendar_begin.select_month(date_begin.month, date_begin.year)
        self.calendar_begin.select_day(date_begin.day)
        self.update_storage()
        self.update_dates()

    def on_earliest_sunday_clicked(self, btn):
        o = self.calendar_begin.datetime_date
        #print "on_earliest_sunday for ", year, month, day
        date_begin = get_earliest_sunday(o)
        if o == date_begin:
            return
        self.calendar_begin.select_month(date_begin.month, date_begin.year)
        self.calendar_begin.select_day(date_begin.day)
        self.update_storage()
        self.update_dates()

    def on_begin_selected(self, calendar):
        date_begin = calendar.datetime_date
        #print "on_begin_selected", year, month, day

        date_end   = date_begin + datetime.timedelta(days=self.period_in_days)
        o = self.calendar_end.datetime_date
        if o == date_end:
            return
        self.calendar_end.select_month(date_end.month, date_end.year)
        self.calendar_end.select_day(date_end.day)
        self.update_storage()
        self.update_dates()

    def on_end_selected(self, calendar):
        date_end = calendar.datetime_date
        #print "on_end_selected", year, month, day

        o = self.calendar_begin.datetime_date
        date_begin = date_end - datetime.timedelta(days=self.period_in_days)
        if o == date_begin:
            return
        self.calendar_begin.select_month(date_begin.month, date_begin.year)
        self.calendar_begin.select_day(date_begin.day)
        self.update_storage()
        self.update_dates()

    def on_period_weeks_changed(self, spin_button):
        #value = spin_button.get_value_as_int()
        #print "on_period_weeks_changed", value, "days"

        date_begin = self.calendar_begin.datetime_date
        date_end   = date_begin + datetime.timedelta(days=self.period_in_days)
        self.calendar_end.select_month(date_end.month, date_end.year)
        self.calendar_end.select_day(date_end.day)
        self.update_storage()
        self.update_dates()

    def move_begin_to_end_clicked(self, btn):
        year, month, day = self.calendar_begin.get_date()
        self.calendar_end.select_month(month, year)
        self.calendar_end.select_day(day)
        self.update_storage()
        self.update_dates()

    def move_end_to_begin_clicked(self, btn):
        year, month, day = self.calendar_end.get_date()
        self.calendar_begin.select_month(month, year)
        self.calendar_begin.select_day(day)
        self.update_storage()
        self.update_dates()

    def on_user_selection_changed(self, selection):
        self._user_sel_set_sensitive(True)
        self.update_user()

    def _user_sel_set_sensitive(self, value):
        for btn in self.__user_sel_widgets:
            btn.set_sensitive(value)

    def update_user(self):
        model, treeiter = self.user_selection.get_selected()
        if treeiter != None:
            if self.weight_grid.set_user(*model[treeiter][:5]):
                self.weight_grid.queue_draw()

    def on_new_user_clicked(self, btn):#
        print("on_new_user_clicked")
        treeiter = self.user_store.append([None, None, 175, 70, 81, False])
        path = self.user_store.get_path(treeiter)
        self.treeview.set_cursor(path, self.column_nick, start_editing=True)
        self.update_storage()

    def on_delete_user_clicked(self, btn):#
        print("on_delete_user_clicked")
        model, treeiter = self.user_selection.get_selected()
        if treeiter != None:
            model.remove(treeiter)
            self.update_storage()

    def on_user_nick_edited(self, widget, path, value):
        # print "on_user_nick_edited", path, value
        self.user_store[path][0] = value
        self.update_storage()
        self.update_user()

    def on_user_lang_changed(self, widget, path, text):
        # print "on_user_lang_changed", widget, path, text
        self.user_store[path][1] = text
        self.update_storage()
        self.update_user()

    def on_user_height_edited(self, widget, path, value):
        # print "on_user_height_edited", path, value
        self.user_store[path][2] = int(value)
        self.update_storage()
        self.update_user()

    def on_user_weight_lo_edited(self, widget, path, value):
        # print "on_user_weight_lo_edited", path, value
        self.user_store[path][3] = int(value)
        self.user_store[path][4] = int(value) + self.weight_delta
        self.update_storage()
        self.update_user()

    def on_user_weight_hi_edited(self, widget, path, value):
        # print "on_user_weight_hi_edited", path, value
        self.user_store[path][4] = int(value)
        self.user_store[path][3] = int(value) - self.weight_delta
        self.update_storage()
        self.update_user()

    def on_user_print_toggled(self, widget, path):
        # print "on_user_print_toggled", "path=%s" % path
        self.user_store[path][5] = not self.user_store[path][5]
        if self.user_store[path][5]:
            self.marked_users += 1
        else:
            self.marked_users -= 1
        self.update_storage()
        self.update_user()

    def update_storage(self):
        # Only start updating the storage after all the initial events
        # while setting up the GUI with still incomplete data have
        # finished firing.
        if not self.do_update_storage:
            return

        year, month, day = self.calendar_begin.get_date()
        s = yaml.dump({'start_date': datetime.date(year,month,day),
                       'weeks': self.period_weeks.get_value_as_int(),
                       'users': dict([ User(*row[:]).for_yaml()
                                       for row in self.user_store ]),
        }, default_flow_style=False)
        if self.yaml_data != s:
            open(self.data_fname, 'w').write(s)
            self.yaml_data = s


##################################################################################


class WeightGridApp(Gtk.Application):

    def __init__(self):
        super(WeightGridApp, self).__init__(
            application_id="net.lauft.app.wcg.gtk",
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.args = None # store for parsed command line options
        install_translation()

    def do_activate(self):
        win = WeightGridWindow(self)
        win.connect('delete_event', self.on_quit)
        win.show_all()
        win.end_label.hide()
        win.calendar_end.hide()

    def do_startup(self,):
        #super(WeightGridApp, self).do_startup()
        Gtk.Application.do_startup(self)

    def do_command_line(self, args):
        # super(WeightGridApp, self).do_command_line(args)
        Gtk.Application.do_command_line(self, args)

        parser = argparse.ArgumentParser(prog=version.program_name_gui)
        parser.add_argument(
            '-V', '--version', action='version',
            version = ('%(program_name_gui)s (%(package_name)s) %(package_version)s'
                       % vars(version)))

        # parse the command line stored in args, but skip the first
        # element (the program name)
        self.args = parser.parse_args(args.get_arguments()[1:])

        self.do_activate()
        return 0

    def do_shutdown(self):
        Gtk.Application.do_shutdown(self)

    def on_quit(self, widget, data):
        self.quit()


##################################################################################


def main(argv=None):
    if not argv:
        argv = sys.argv
    app = WeightGridApp()
    exit_status = app.run(argv)
    sys.exit(exit_status)


##################################################################################
