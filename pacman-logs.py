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

import os
import sys
import datetime
import subprocess
import gi
from alpmtransform import AlpmTransform

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GdkPixbuf, Gdk

__version__ = '0.4.2'

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

target_entry = [] # [Gtk.TargetEntry.new('DI', 1, 50)]
class MainApp:

    def __init__(self):
        """main app window"""
        builder = Gtk.Builder()
        builder.add_from_file('pacman-logs.glade')
        window = builder.get_object('window')
        self.window = window

        self.filter_action = None

        #builderm = Gtk.Builder(UI_MENU)
        #self.pop = builderm.get_object('PopupMenu')

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

        homebtn = builder.get_object('home')
        homebtn.connect('clicked', self.on_raz)

        self.entry = builder.get_object('Entry')
        self.entry.connect('search-changed', self.on_search_changed)
        self.entryd = builder.get_object('Entryd')
        self.entryd.connect('search-changed', self.on_search_changed)
        self.treeview = builder.get_object('treeview')
        self.treeview.props.has_tooltip = True
        self.treeview.connect("query-tooltip", self.query_tooltip_tree_view_cb)
        self.treeview.get_selection().connect("changed", self.selection_changed_cb)
        self.treeview.props.activate_on_single_click = False
        self.treeview.connect("row-activated", self.on_rowActivated);
        self.store = builder.get_object('logstore')
        self.init_logs()
        builder.get_object('headerbar').set_title(f"Pacman Logs - {len(self.store)}")
        window.show_all()
        #builder.get_object('home').hide()
        builder.get_object('verbs').hide()
        builder.get_object('about').hide()
        
        self.treeview.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, target_entry, Gdk.DragAction.COPY)
        self.treeview.connect("drag-data-get", self.on_drag_data_get)
        self.entry.drag_dest_set(Gtk.DestDefaults.ALL, target_entry, Gdk.DragAction.COPY)
        self.entry.connect("drag-data-received", self.on_drag_data_received)

        ######self.entry.drag_dest_set(target_entry, Gdk.DragAction.COPY)
        #print(dir(self.entry.drag_dest_get_target_list()))
        #for t in self.entry.drag_dest_get_target_list():
        #    print('drag_dest_get_target_list:',t)

        self.entry.drag_dest_set_target_list(None)
        self.entryd.drag_dest_set_target_list(None)
        self.treeview.drag_source_set_target_list(None)
        self.entry.drag_dest_add_text_targets()
        #self.entryd.drag_dest_add_text_targets()
        self.treeview.drag_source_add_text_targets()

        self.treeview.connect("button-press-event", self.on_click)

        self.create_actions()


        #self.entryd.drag_dest_set(Gtk.DestDefaults.ALL, target_entry, Gdk.DragAction.COPY)
        #self.entryd.connect("drag-data-received", self.on_drag_data_received)

    def create_actions(self):
        self.actions = Gtk.ActionGroup(name='Actions')

        action = Gtk.Action(name='filter_name', label="filter by package name", tooltip=None, stock_id=Gtk.STOCK_FIND)
        action.connect('activate', self.pop_action, 2, "pkg")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_date', label="filter by date", tooltip=None, stock_id=None)
        action.set_icon_name('view-calendar')
        action.connect('activate', self.pop_action, 0, "yyyy-mm-dd")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_removed', label="removed", tooltip=None, stock_id=None)
        action.set_icon_name('arrow-down')
        action.connect('activate', self.pop_action, 1, "removed")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_installed', label="installed", tooltip=None, stock_id=None)
        action.set_icon_name('arrow-right')
        action.connect('activate', self.pop_action, 1, "installed")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_reinstalled', label="reinstalled", tooltip=None, stock_id=None)
        action.set_icon_name('view-refresh')
        action.connect('activate', self.pop_action, 1, "reinstalled")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_upgraded', label="upgraded", tooltip=None, stock_id=None)
        action.set_icon_name('arrow-up')
        action.connect('activate', self.pop_action, 1, "upgraded")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_warning', label="warning", tooltip=None, stock_id=None)
        action.set_icon_name('dialog-warning')
        action.connect('activate', self.pop_action, 1, "warning")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_none', label="no filter", tooltip=None, stock_id=None)
        action.connect('activate', self.on_raz)
        self.actions.add_action(action)

        # recup action pour changer label


    def on_rowActivated(self, treeview, row, data):
        model, iter = self.treeview.get_selection().get_selected()
        if iter:
            line = model.get(iter, 7)[0]
            print('go to line:', line)
            if os.path.isfile('/usr/bin/code'):
                subprocess.call(f'/usr/bin/code --goto "/var/log/pacman.log:{line}"', shell=True)
                return
            if os.path.isfile('/usr/bin/code-insiders'):
                subprocess.call(f'/usr/bin/code-insiders --goto "/var/log/pacman.log:{line}"', shell=True)
                return
            if os.path.isfile('/usr/bin/kate'):
                subprocess.call(f"/usr/bin/kate /var/log/pacman.log --line {line}", shell=True)
                return
            if os.path.isfile('/usr/bin/gedit'):
                subprocess.call(f"/usr/bin/gedit /var/log/pacman.log +{line}", shell=True)
                return
            if os.path.isfile('/usr/bin/leafpad'):
                subprocess.call(f"/usr/bin/leafpad /var/log/pacman.log --jump={line}", shell=True)
                return

    def on_click(self, widget, event):
        if event.button == 3:
            """
            TODO ?
            cherche si treeview select
            """
            model, iter = self.treeview.get_selection().get_selected()
            if iter:
                print(model.get(iter, 2)[0])
                menu = Gtk.Menu() #

                action = self.actions.get_action("filter_name")
                action.set_label("filter " + model.get(iter, 2)[0])
                action.connect('activate', self.pop_action, 2, model.get(iter, 2)[0])
                menuitem = action.create_menu_item()
                menu.append(menuitem)

                action = self.actions.get_action("filter_date")
                action.set_label("filter " + model.get(iter, 0)[0][:10])
                action.connect('activate', self.pop_action, 0, model.get(iter, 0)[0][:10])
                menuitem = action.create_menu_item()
                menu.append(menuitem)

                imenu = Gtk.Menu()
                menu_filter = Gtk.MenuItem("Action filter")
                menu_filter.set_submenu(imenu)

                action = self.actions.get_action("filter_removed")
                menuitem = action.create_menu_item()
                imenu.append(menuitem)
                action = self.actions.get_action("filter_installed")
                menuitem = action.create_menu_item()
                imenu.append(menuitem)
                action = self.actions.get_action("filter_reinstalled")
                menuitem = action.create_menu_item()
                imenu.append(menuitem)
                action = self.actions.get_action("filter_upgraded")
                menuitem = action.create_menu_item()
                imenu.append(menuitem)

                imenu.append(Gtk.SeparatorMenuItem())
                action = self.actions.get_action("filter_warning")
                menuitem = action.create_menu_item()
                imenu.append(menuitem)

                menu.append(menu_filter)

                menu.append(Gtk.SeparatorMenuItem())
                action = self.actions.get_action("filter_none")
                menuitem = action.create_menu_item()
                menu.append(menuitem)

                menu.show_all()
                menu.popup(None, None, None, None, event.button, event.time)
                return True
        return False

    def pop_action(self, menuitem, action, text):
        #print(f"pop menu filter by {action}, {text}")
        if action == 2:
            self.entry.set_text(text)
        if action == 0:
            self.entryd.set_text(text)
        if action == 1:
            # filter by action ...
            self.filter_action = text
            self.filter.refilter()

    def on_raz(self, btn):
        self.entry.set_text('')
        self.entryd.set_text('')
        self.filter_action = None
        #TODO only if i change a value
        self.filter.refilter()
        

    def on_drag_data_get(self, treeview, context, selection, target_id, etime):
        treeselection = treeview.get_selection()
        model, iter = treeselection.get_selected()
        if model and iter:
            data = model.get_value(iter, 2) #+ ' * ' + model.get_value(iter, 0)
            #print('--drag:', data)
            #print('--target_id:', target_id)
            selection.set_text(data, -1)
        else:
            selection.set_text('', -1)

    def on_drag_data_received(self, treeview, context, x, y, selection, info, etime):
        return True
        text = selection.get_text()
        self.entry.set_text('')
        if text:
            print('', text.split(' * ')[0])
            # deja fait automatiquement !!!! self.entry.set_text(text.split(' * ')[0])
            #self.entry.set_focus(True)
        #self.entry.connect('search-changed', self.on_search_changed)

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
            'warning' : 'dialog-warning',
            'transaction' : 'home'
        }
        for item in reversed(items):
            if item['verb'] != 'transaction':
                msg = ''
                warning = ''
                if item['verb'] == 'warning':
                    msg = item.get('msg')
                    if msg.endswith('pacnew'):
                        warning = ' (pacnew)'
                    if msg.endswith('pacsave'):
                        warning = ' (pacsave)'
                    if msg.startswith('directory permissions'):
                        warning = ' (chmod)'
                self.store.append([
                    str(item['date'])[:-3],
                    item['verb'],
                    item['pkg'] + warning,
                    item['ver'],
                    icons_verb.get(item['verb'], 'home'),
                    item['date'].strftime('%c').split(' ', 1)[1][:-4],      # local format date
                    msg,
                    item['l']
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
            if not result:
                return False
        current_filter = self.filter_action
        if current_filter:
            result = current_filter == model[iter][1]
        return result

    def query_tooltip_tree_view_cb(self, widget, x, y, keyboard_tip, tooltip):
        """tootips action"""
        if not widget.get_tooltip_context(x, y, keyboard_tip):
            return False
        else:
            ok, x, y, model, path, iter = widget.get_tooltip_context(x, y, keyboard_tip)
            if model:
                tooltip.set_text(model.get(iter, 1)[0] + ' ' + model.get(iter, 6)[0])
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

    def on_search_changed(self, entry):
        if entry == self.entry:
            txt = self.entry.get_text()
            if txt and len(txt) < 3:
                return
        if entry == self.entryd:
            txt = self.entryd.get_text()
            if txt and len(txt) < 2:
                return
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
