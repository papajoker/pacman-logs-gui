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
import glob
import datetime
import subprocess
import gi
from alpmtransform import AlpmTransform

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GdkPixbuf, Gdk

__version__ = '0.4.3'

class config():
    """gui const"""
    # icons
    icons_verb = {
        'removed' : '⮜', #'list-remove', # archive-remove
        'installed' : "⮞", #'list-add',  # archive-insert
        'reinstalled' : '🗘', #media-playlist-repeat-symbolic-rtl',  # archive extract
        'upgraded' : '⮝',# 'view-refresh', # media-playlist-repeat view-refresh
        'warning' : '⚠',
        'transaction' : '🏠'
    }
    # columns store for treeview
    cols = {
        'date':0,
        'verb':1,
        'pkg':2,
        'ver':3,
        'ico':4,
        'datel':5,
        'msg':6,
        'line':7
    }
    log = '/var/log/pacman.log'

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

        # set icon style dark/light
        bgcolor = self.treeview.get_style_context().get_background_color(Gtk.StateType.NORMAL)
        color = self.treeview.get_style_context().get_color(Gtk.StateType.NORMAL)
        print('bg: ',bgcolor)
        print('color: ', color, color.to_string())

        # https://lazka.github.io/pgi-docs/Gtk-3.0/flags.html#Gtk.StateFlags
        color = self.treeview.get_style_context().get_background_color(Gtk.StateFlags(4))
        print('bgcolor ACTIVE: ', color, color.to_string())

        if bgcolor.red < 0.5 and bgcolor.blue < 0.5:
            print ("dark theme")
        else:
            print ("light theme")

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



    def create_actions(self):
        self.actions = Gtk.ActionGroup(name='Actions')

        action = Gtk.Action(name='filter_name', label="filter by package name", tooltip=None, stock_id=Gtk.STOCK_FIND)
        action.connect('activate', self.pop_action, config.cols['pkg'], "pkg")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_date', label="filter by date", tooltip=None, stock_id=None)
        action.set_icon_name('view-calendar')
        action.connect('activate', self.pop_action, config.cols['date'], "yyyy-mm-dd")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_removed', label="⮜  removed", tooltip=None, stock_id=None)
        #action.set_icon_name(config.icons_verb['removed'])
        action.connect('activate', self.pop_action, config.cols['verb'], "removed")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_installed', label="⮞  installed", tooltip=None, stock_id=None)
        #action.set_icon_name(config.icons_verb['installed'])
        action.connect('activate', self.pop_action, config.cols['verb'], "installed")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_reinstalled', label="🗘  reinstalled", tooltip=None, stock_id=None)
        #action.set_icon_name(config.icons_verb['reinstalled'])
        action.connect('activate', self.pop_action, config.cols['verb'], "reinstalled")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_upgraded', label="⮝  upgraded", tooltip=None, stock_id=None)
        #action.set_icon_name(config.icons_verb['upgraded'])
        action.connect('activate', self.pop_action, config.cols['verb'], "upgraded")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_warning', label="⚠  warning", tooltip=None, stock_id=None)
        #action.set_icon_name(config.icons_verb['warning'])
        action.connect('activate', self.pop_action, config.cols['verb'], "warning")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_none', label="no filter", tooltip=None, stock_id=None)
        action.connect('activate', self.on_raz)
        self.actions.add_action(action)

        # recup action pour changer label

    def on_rowActivated(self, treeview, row, data):
        model, iter = self.treeview.get_selection().get_selected()
        if iter:
            line = model.get(iter, config.cols['line'])[0]
            command = None
            print('go to line:', line)
            if os.path.isfile('/usr/bin/kate'):
                command = f"/usr/bin/kate {config.log} --line {line}"
            if os.path.isfile('/usr/bin/leafpad'):
                command = f"/usr/bin/leafpad {config.log} --jump={line}"
            if os.path.isfile('/usr/bin/gedit'):
                command = f"/usr/bin/gedit {config.log} +{line}"
            if os.path.isfile('/usr/bin/code'):
                command = f'/usr/bin/code --goto "{config.log}:{line}"'
            if os.path.isfile('/usr/bin/code-insiders'):
                command = f'/usr/bin/code-insiders --goto "{config.log}:{line}"'
            if command:
                subprocess.call(command, shell=True)

    def on_click(self, widget, event):
        if event.button == 3:
            """
            TODO ?
            cherche si treeview select
            """
            model, iter = self.treeview.get_selection().get_selected()
            if iter:
                menu = Gtk.Menu() #

                action = self.actions.get_action("filter_name")
                action.set_label("filter " + model.get(iter, config.cols['pkg'])[0])
                action.connect('activate', self.pop_action, config.cols['pkg'], model.get(iter, config.cols['pkg'])[0])
                menuitem = action.create_menu_item()
                menu.append(menuitem)

                action = self.actions.get_action("filter_date")
                action.set_label("filter " + model.get(iter, config.cols['date'])[0][:10])
                action.connect('activate', self.pop_action, config.cols['date'], model.get(iter, config.cols['date'])[0][:10])
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
        if action == config.cols['pkg']:
            self.entry.set_text(text)
        if action == config.cols['date']:
            self.entryd.set_text(text)
        if action == config.cols['verb']:
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
            data = model.get_value(iter, config.cols['pkg']) #+ ' * ' + model.get_value(iter, 0)
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
        log.logfile = config.log
        log.convert("/tmp/pacman.json.log")

        # set logstore ... //GtkListStore
        self.store.clear()
        column = Gtk.TreeViewColumn('Date', Gtk.CellRendererText(), text=5)
        column.set_resizable(True)
        column.set_reorderable(True)
        column.set_sort_order(Gtk.SortType.DESCENDING)
        column.set_sort_column_id(config.cols['date'])
        self.treeview.append_column(column)

        renderer = Gtk.CellRendererText()
        renderer.set_alignment(0.5, 0.5)
        column = Gtk.TreeViewColumn('Action', renderer, text=4)
        #column = Gtk.TreeViewColumn('Action', Gtk.CellRendererPixbuf(), icon_name=4)
        column.set_resizable(False)
        column.set_reorderable(True)
        column.set_sort_column_id(config.cols['verb'])
        self.treeview.append_column(column)
        column = Gtk.TreeViewColumn('Package', Gtk.CellRendererText(), text=2)
        column.set_resizable(True)
        column.set_reorderable(True)
        column.set_sort_column_id(config.cols['pkg'])
        self.treeview.append_column(column)
        column = Gtk.TreeViewColumn('Version', Gtk.CellRendererText(), text=3)
        column.set_resizable(True)
        self.treeview.append_column(column)

        items = log.load_json("/tmp/pacman.json.log")
        print("count logs:", len(items))

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
                    ""+config.icons_verb.get(item['verb'], 'home'),
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
            result = current_filter in model[iter][config.cols['pkg']]
            if not result:
                return False
        current_filter = str(self.entryd.props.text)
        if current_filter:
            result = current_filter in model[iter][config.cols['date']]
            if not result:
                return False
        current_filter = self.filter_action
        if current_filter:
            result = current_filter == model[iter][config.cols['verb']]
        return result

    @staticmethod
    def pkg_is_installed(package: str) -> (bool,str):
        dep = ""
        if not package:
            return False, dep
        dirs = glob.glob(f"/var/lib/pacman/local/{package}-[0-9]*")
        if dirs:
            with open(dirs[0]+"/desc", "r") as f:
                if "%REASON%\n" in f.readlines():
                    dep = " as dependency "
            return True, dep
        return False, dep

    def query_tooltip_tree_view_cb(self, widget, x, y, keyboard_tip, tooltip):
        """tootips action, show action + msg"""
        if not widget.get_tooltip_context(x, y, keyboard_tip):
            return False
        else:
            ok, x, y, model, path, iter = widget.get_tooltip_context(x, y, keyboard_tip)
            if model:

                # TODO
                # too long, prefer action after a select and not mouse_over
                more_txt = ''
                pkg = model.get(iter, config.cols['pkg'])[0]
                if pkg:
                    is_installed, dep = self.pkg_is_installed(pkg)
                    if is_installed:
                        more_txt = f" (installed {dep}) "

                tooltip.set_text(model.get(iter, config.cols['verb'])[0] + ' ' + more_txt + model.get(iter, config.cols['msg'])[0])
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
