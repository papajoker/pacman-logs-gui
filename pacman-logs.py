#!/usr/bin/python
#
# This file is part of pacman-logs.
#
# pacman-logs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pacman-logs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pacman-logs.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors: papajoke
#

#import os
import sys
import datetime
import gi
from alpmtransform import AlpmTransform

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GdkPixbuf

__version__ = '0.1.0'

class CalDialog(Gtk.Dialog):
    '''Calendar Dialog'''
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Select Date", parent, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self.set_default_size(300, 200)
        self.value = None
        box = self.get_content_area()
        calendar = Gtk.Calendar()
        calendar.set_detail_height_rows(1)
        calendar.set_property("show-details", True)
        calendar.set_detail_func(self.cal_entry)
        box.add(calendar)
        self.show_all()

    def cal_entry(self, calendar, year, month, date):
        self.value = calendar.get_date()

class MainApp:

    def __init__(self):
        """main app window"""
        builder = Gtk.Builder()
        builder.add_from_file('pacman-logs.glade')
        window = builder.get_object('window')
        self.window = window

        icon = "system-software-install"
        pix_buf24 = Gtk.IconTheme.get_default().load_icon(icon, 24, 0)
        pix_buf32 = Gtk.IconTheme.get_default().load_icon(icon, 32, 0)
        pix_buf48 = Gtk.IconTheme.get_default().load_icon(icon, 48, 0)
        pix_buf64 = Gtk.IconTheme.get_default().load_icon(icon, 64, 0)
        pix_buf96 = Gtk.IconTheme.get_default().load_icon(icon, 96, 0)
        window.set_icon_list([pix_buf24, pix_buf32, pix_buf48, pix_buf64, pix_buf96])

        window.set_position(Gtk.WindowPosition.CENTER_ALWAYS)

        window.connect('delete-event', Gtk.main_quit)
        window.connect('destroy', self.on_main_window_destroy)

        pickdate = builder.get_object('pickdate')
        pickdate.connect('clicked', self.on_date_clicked)

        self.entry = builder.get_object('Entry')
        self.entry.connect('search-changed', self.on_search_changed)
        self.entryd = builder.get_object('Entryd')
        self.entryd.connect('search-changed', self.on_search_changed)
        self.treeview = builder.get_object('treeview')
        self.treeview.props.has_tooltip = True
        self.treeview.connect("query-tooltip", self.query_tooltip_tree_view_cb)
        self.treeview.get_selection().connect("changed", self.selection_changed_cb)
        self.store = builder.get_object('logstore')
        self.init_logs()
        builder.get_object('headerbar').set_title(f"Pacman Logs - {len(self.store)}")
        window.show_all()
        builder.get_object('home').hide()
        builder.get_object('verbs').hide()
        builder.get_object('about').hide()

    def init_logs(self):
        """ set datas"""
        log = AlpmTransform()
        if len(sys.argv) > 1:
            try:
                log.max_day = int(sys.argv[1])
            except ValueError:
                log.max_day = 60
        log.logfile = "/var/log/pacman.log"
        log.convert("/tmp/pacman.json.log")

        # set logstore ... //GtkListStore
        self.store.clear()
        column = Gtk.TreeViewColumn('Date', Gtk.CellRendererText(), text=5)
        column.set_resizable(True)
        column.set_reorderable(True)
        column.set_sort_order(Gtk.SortType.DESCENDING)
        column.set_sort_column_id(0)
        self.treeview.append_column(column)
        column = Gtk.TreeViewColumn('Action', Gtk.CellRendererPixbuf(), icon_name=4)
        column.set_resizable(False)
        column.set_reorderable(True)
        column.set_sort_column_id(1)
        self.treeview.append_column(column)
        column = Gtk.TreeViewColumn('Package', Gtk.CellRendererText(), text=2)
        column.set_resizable(True)
        column.set_reorderable(True)
        column.set_sort_column_id(2)
        self.treeview.append_column(column)
        column = Gtk.TreeViewColumn('Version', Gtk.CellRendererText(), text=3)
        column.set_resizable(True)
        self.treeview.append_column(column)

        items = log.load_json("/tmp/pacman.json.log")
        print("count logs:", len(items))

        icons_verb = {
            'removed' : 'arrow-down', #'list-remove', # archive-remove
            'installed' : "arrow-right", #'list-add',  # archive-insert
            'reinstalled' : 'view-refresh', #media-playlist-repeat-symbolic-rtl',  # archive extract
            'upgraded' : 'arrow-up',# 'view-refresh', # media-playlist-repeat view-refresh
            'transaction' : 'home'
        }
        print(type(icons_verb, ), icons_verb)

        for item in reversed(items):
            if item['verb'] != 'transaction':
                adate = item['date']
                #adate = adate.local
                self.store.append([
                    str(item['date'])[:-3],
                    item['verb'],
                    item['pkg'],
                    item['ver'],
                    icons_verb.get(item['verb'], 'home'),
                    item['date'].strftime('%c').split(' ', 1)[1][:-4]      # local format date
                ])
        items = None
        self.filter = self.store.filter_new()
        self.filter.set_visible_func(self.filter_func)
        sorted_and_filtered_model = Gtk.TreeModelSort(self.filter)
        self.treeview.set_model(sorted_and_filtered_model)

    def filter_func(self, model, iter, data):
        """Tests if pkg name or date in the row"""
        current_filter = str(self.entry.props.text).lower()
        result = True
        if current_filter:
            result = current_filter in model[iter][2]
            if not result:
                return False
        current_filter = str(self.entryd.props.text)
        if current_filter:
            result = current_filter in model[iter][0]
        return result

    def query_tooltip_tree_view_cb(self, widget, x, y, keyboard_tip, tooltip):
        """tootips action"""
        if not widget.get_tooltip_context(x, y, keyboard_tip):
            return False
        else:
            ok, x, y, model, path, iter = widget.get_tooltip_context(x, y, keyboard_tip)
            if model:
                value = model.get(iter, 1)
                tooltip.set_text(value[0])
                widget.set_tooltip_row(tooltip, path)
                return True
        return False

    def selection_changed_cb(self, selection):
        self.treeview.trigger_tooltip_query()

    @staticmethod
    def on_main_window_destroy(widget):
        Gtk.main_quit()

    def main(self):
        Gtk.main()

    def on_search_changed(self, GtkSearchEntry):
        self.filter.refilter()

    def on_date_clicked(self, btn):
        """Open calender and get user selection"""
        dialog = CalDialog(self.window)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            tmpdate = datetime.datetime.strptime(f"{dialog.value.year}-{dialog.value.month+1}-{dialog.value.day}", '%Y-%m-%d')
            self.entryd.set_text(tmpdate.strftime('%Y-%m-%d'))
        dialog.destroy()

try:
    plog = MainApp()
    plog.main()

except KeyboardInterrupt:
    print("\n" + "Error: interrupted by the user.")
    exit(1)
