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
import re
import argparse
#from alpmtransform import AlpmTransform

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject, GdkPixbuf, Gdk

__version__ = '0.4.4'

class AlpmLog():
    """gui const"""
    # icons
    REMOVED, INSTALLED, REINSTALLED, UPGRADED, WARNING, TRANSACTION = list(range(6))
    actions = {
        'removed' : '⮜', #'list-remove', # archive-remove
        'installed' : "⮞", #'list-add',  # archive-insert
        'reinstalled' : '🗘', #media-playlist-repeat-symbolic-rtl',  # archive extract
        'upgraded' : '⮝',# 'view-refresh', # media-playlist-repeat view-refresh
        'warning' : '⚠',
        #'transaction' : '🏠'
    }
    # columns store for treeview
    DATE, ACTION, PKG, VERSION, ICON, DATEL, MSG, LINE = list(range(8))
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


    def __init__(self, max_day: int = 60, log_file: str = '/var/log/pacman.log'):
        self.max_day = max_day
        self.log_file = log_file
        self.items = []

    def parse_log(self, log_fh):
        """parse logs"""
        currentDict = {}
        good_verbs = self.list_actions()
        regex = re.compile(r'\[(.+)\] \[ALPM\] ([a-z]+)[: | ](.*)') #[\((.+)\)|.*]
        subregex = re.compile(r'(\S+) \((.*)\)')
        i = 0
        for line in log_fh:
            i += 1
            matchs = regex.match(line)
            if not matchs:
                continue
            if matchs.lastindex < 3:
                continue
            if not matchs.group(2) in good_verbs:
                continue

            logdate = datetime.datetime.strptime(matchs.group(1), '%Y-%m-%d %H:%M')
            diffdate = datetime.datetime.today() - logdate
            # only last days
            if diffdate.days > self.max_day:
                continue

            currentDict = {
                "date": logdate,
                #"type": 'ALPM',
                "pkg": '',
                "ver": '',
                "verb": matchs.group(2),
                "l": i
            }

            # warning
            if currentDict['verb'] == "warning":
                currentDict['msg'] = matchs.group(3)
                if 'directory permissions differ' in currentDict['msg']:
                    currentDict['msg'] = currentDict['msg'] + ' ' + next(log_fh).rstrip()
                    i += 1
                yield currentDict
                continue

            matchs = subregex.match(matchs.group(3))
            if matchs:
                currentDict['pkg'] = matchs.group(1)
                currentDict['ver'] = matchs.group(2)
                if "->" in currentDict['ver']:
                    currentDict['ver'] = currentDict['ver'].split(" ", 2)[2]
                yield currentDict

    def load_file(self):
        """load pacman log"""
        with open(self.log_file) as fin:
            self.items = list(self.parse_log(fin))
        if self.items:
            self.items = list(reversed(self.items))
        return self.items

    @classmethod
    def list_actions(cls):
        return cls.actions.keys()

    def filters(self, aname="", adate="", aaction=""):
        """
        filter name, date or action
        """
        for item in self.items:
            result = True
            if aname:
                if aname.endswith(" "):
                    result = aname == item['pkg']+" "
                    if not result:
                        continue
                else:
                    result = aname in item['pkg']
                    if not result:
                        continue
            if adate:
                result = aname in item['date'] # convert to yy-mm-dd
                if not result:
                    continue
            if aaction:
                result = aaction == item['verb']
            if result:
                yield item


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

    def __init__(self, classlog: AlpmLog):
        """main app window"""
        self.alpm = classlog
        self.filter = None
        builder = Gtk.Builder()
        builder.add_from_file('pacman-logs.glade')
        window = builder.get_object('window')
        self.window = window

        self.filter_action = None

        stack = builder.get_object('stack')
        self.info = builder.get_object('info')
        #self.info_bar_title.connect("response", self.on_remove_title_box)
        self.title_label = Gtk.Label()
        self.title_label.set_markup(f"texte dans info ")
        # pack title info
        self.stack = builder.get_object("stack")
        self.info.pack_start(self.title_label, expand=True, fill=True, padding=0)
        #self.stack.set_visible_child_name("page2")

        scrolled_window = builder.get_object('detail')
        viewport = Gtk.Viewport(border_width=10)
        label = Gtk.Label(wrap=True)
        label.set_markup(f"texte dans page <b>info</b> ")
        viewport.add(label)
        scrolled_window.add(viewport)
        self.stack.set_visible_child_name("page1")

        '''
        self.info_bar_title = Gtk.InfoBar()
        self.info_bar_title.set_message_type(Gtk.MessageType.OTHER)
        self.info_bar_title.set_show_close_button(True)
        self.info_bar_title.set_revealed(True)
        
        # title label
        
        # pack title info to app browser box
        
        logs.pack_start(self.info_bar_title)#, expand=False, fill=True, padding=0)
        '''

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
        self.treeview.connect("row-activated", self.on_rowActivated)

        # set icon style dark/light
        bgcolor = self.treeview.get_style_context().get_background_color(Gtk.StateType.NORMAL)
        color = self.treeview.get_style_context().get_color(Gtk.StateType.NORMAL)
        print('bg: ', bgcolor)
        print('color: ', color, color.to_string())

        # https://lazka.github.io/pgi-docs/Gtk-3.0/flags.html#Gtk.StateFlags
        color = self.treeview.get_style_context().get_background_color(Gtk.StateFlags(4))
        print('bgcolor ACTIVE: ', color, color.to_string())

        if bgcolor.red < 0.5 and bgcolor.blue < 0.5:
            print("dark theme")
        else:
            print("light theme")

        self.title = builder.get_object('headerbar')
        self.store = builder.get_object('logstore')
        self.init_logs()
        window.show_all()
        #builder.get_object('home').hide()
        builder.get_object('verbs').hide()
        builder.get_object('about').hide()

        self.treeview.enable_model_drag_source(Gdk.ModifierType.BUTTON1_MASK, target_entry, Gdk.DragAction.COPY)
        self.treeview.connect("drag-data-get", self.on_drag_data_get)
        self.entry.drag_dest_set(Gtk.DestDefaults.ALL, target_entry, Gdk.DragAction.COPY)

        self.entry.drag_dest_set_target_list(None)
        self.entryd.drag_dest_set_target_list(None)
        self.treeview.drag_source_set_target_list(None)
        self.entry.drag_dest_add_text_targets()
        self.treeview.drag_source_add_text_targets()

        self.treeview.connect("button-press-event", self.on_click)

        self.create_actions()

    def set_title(self):
        nb = len(self.store)
        if self.filter:
            nb = len(self.filter)
        self.title.set_title(f"Pacman Logs - {nb}")


    def create_actions(self):
        self.actions = Gtk.ActionGroup(name='Actions')

        action = Gtk.Action(name='filter_name', label="filter by package name", tooltip=None, stock_id=Gtk.STOCK_FIND)
        action.connect('activate', self.pop_action, self.alpm.PKG, "pkg")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_date', label="filter by date", tooltip=None, stock_id=None)
        action.set_icon_name('view-calendar')
        action.connect('activate', self.pop_action, self.alpm.DATE, "yyyy-mm-dd")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_removed', label="⮜  removed", tooltip=None, stock_id=None)
        #action.set_icon_name(config.icons_verb['removed'])
        action.connect('activate', self.pop_action, self.alpm.ACTION, "removed")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_installed', label="⮞  installed", tooltip=None, stock_id=None)
        #action.set_icon_name(config.icons_verb['installed'])
        action.connect('activate', self.pop_action, self.alpm.ACTION, "installed")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_reinstalled', label="🗘  reinstalled", tooltip=None, stock_id=None)
        #action.set_icon_name(config.icons_verb['reinstalled'])
        action.connect('activate', self.pop_action, self.alpm.ACTION, "reinstalled")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_upgraded', label="⮝  upgraded", tooltip=None, stock_id=None)
        #action.set_icon_name(config.icons_verb['upgraded'])
        action.connect('activate', self.pop_action, self.alpm.ACTION, "upgraded")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_warning', label="⚠  warning", tooltip=None, stock_id=None)
        #action.set_icon_name(config.icons_verb['warning'])
        action.connect('activate', self.pop_action, self.alpm.ACTION, "warning")
        self.actions.add_action(action)

        action = Gtk.Action(name='filter_none', label="no filter", tooltip=None, stock_id=Gtk.STOCK_HOME)
        action.connect('activate', self.on_raz)
        self.actions.add_action(action)

        # recup action pour changer label

    def on_rowActivated(self, treeview, row, data):
        model, iter = self.treeview.get_selection().get_selected()
        if iter:
            line = model.get(iter, self.alpm.LINE)[0]
            command = None
            print('go to line:', line)
            if os.path.isfile('/usr/bin/kate'):
                command = f"/usr/bin/kate {self.alpm.log_file} --line {line}"
            if os.path.isfile('/usr/bin/leafpad'):
                command = f"/usr/bin/leafpad {self.alpm.log_file} --jump={line}"
            if os.path.isfile('/usr/bin/gedit'):
                command = f"/usr/bin/gedit {self.alpm.log_file} +{line}"
            if os.path.isfile('/usr/bin/code'):
                command = f'/usr/bin/code --goto "{self.alpm.log_file}:{line}"'
            if os.path.isfile('/usr/bin/code-insiders'):
                command = f'/usr/bin/code-insiders --goto "{self.alpm.log_file}:{line}"'
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
                action.set_label("filter " + model.get(iter, self.alpm.PKG)[0])
                action.connect('activate', self.pop_action, self.alpm.PKG, model.get(iter, self.alpm.PKG)[0])
                menuitem = action.create_menu_item()
                menu.append(menuitem)

                action = self.actions.get_action("filter_date")
                action.set_label("filter " + model.get(iter, self.alpm.DATE)[0][:10])
                action.connect('activate', self.pop_action, self.alpm.DATE, model.get(iter, self.alpm.DATE)[0][:10])
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
        if action == self.alpm.PKG:
            self.entry.set_text(text+" ")
        if action == self.alpm.DATE:
            self.entryd.set_text(text)
        if action == self.alpm.ACTION:
            # filter by action ...
            self.filter_action = text
            # TODO
            #très très lent !!!!!
            #tester si possible de dévalider le tri puis remettre après filtre
            #replace filter.refilter() by 
            # - treeview_populate
            # - or treeview.line.visible = false ??? je ne pense pas
            print('filter.refilter()', 'begin')
            self.filter.refilter()
            #self.populate()
            print('filter.refilter()', 'END')
            self.set_title()

    def on_raz(self, btn):
        self.entry.set_text('')
        self.entryd.set_text('')
        self.filter_action = None
        #TODO only if i change a value
        self.filter.refilter()
        #self.populate()
        self.set_title()
        self.stack.set_visible_child_name("page0")

    def on_drag_data_get(self, treeview, context, selection, target_id, etime):
        treeselection = treeview.get_selection()
        model, iter = treeselection.get_selected()
        if model and iter:
            data = model.get_value(iter, self.alpm.PKG)+" " #+ ' * ' + model.get_value(iter, 0)
            #print('--target_id:', target_id)
            # fix dbl call by reset self.entry
            self.entry.set_text('')
            selection.set_text(data, -1)
            return True
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

    def populate(self):
        self.store.clear()
        items = list(self.alpm.filters( adate=str(self.entryd.props.text), aname=str(self.entry.props.text).lower(), aaction=self.filter_action))
        for item in self.alpm.items:
            if item['verb'] != 'transaction':
                msg = ''
                warning = ''
                if item['verb'] == 'warning':
                    msg = item.get('msg')
                    if msg.endswith('pacnew'):
                        warning = ' (pacnew)'
                    if msg.endswith('pacsave'):
                        warning = ' (pacsave)'
                    if 'directory permissions' in msg:
                        warning = ' (chmod)'
                self.store.append([
                    str(item['date'])[:-3],
                    item['verb'],
                    item['pkg'],
                    item['ver'] + warning,
                    "" + self.alpm.actions.get(item['verb'], 'home'),
                    item['date'].strftime('%c').split(' ', 1)[1][:-4],      # local format date
                    msg,
                    item['l']
                ])

    def init_logs(self):
        """ set datas"""
        # set logstore ... //GtkListStore
        #self.store.clear()
        column = Gtk.TreeViewColumn('Date', Gtk.CellRendererText(), text=5)
        column.set_resizable(True)
        column.set_reorderable(True)
        column.set_sort_order(Gtk.SortType.DESCENDING)
        column.set_sort_column_id(self.alpm.DATE)
        self.treeview.append_column(column)

        renderer = Gtk.CellRendererText()
        renderer.set_alignment(0.5, 0.5)
        column = Gtk.TreeViewColumn('Action', renderer, text=4)
        column.set_resizable(False)
        column.set_reorderable(True)
        column.set_sort_column_id(self.alpm.ACTION)
        self.treeview.append_column(column)
        column = Gtk.TreeViewColumn('Package', Gtk.CellRendererText(), text=2)
        column.set_resizable(True)
        column.set_reorderable(True)
        column.set_sort_column_id(self.alpm.PKG)
        self.treeview.append_column(column)
        column = Gtk.TreeViewColumn('Version', Gtk.CellRendererText(), text=3)
        column.set_resizable(True)
        self.treeview.append_column(column)

        self.populate()
        self.alpm.items.clear() # no re-use populate
        self.set_title()

        self.filter = self.store.filter_new()
        self.filter.set_visible_func(self.filter_func)
        sorted_and_filtered_model = Gtk.TreeModelSort(self.filter)
        self.treeview.set_model(sorted_and_filtered_model)

    def filter_func(self, model, iter, data):
        """Tests if pkg name or date in the row"""
        current_filter = str(self.entry.props.text).lower()
        result = True
        # test if speed NUT NOT with > 10 000 items !!!
        #return True
        if current_filter:
            if current_filter.endswith(" "):
                result = current_filter == model[iter][self.alpm.PKG]+" "
                if not result:
                    return False
            else:
                result = current_filter in model[iter][self.alpm.PKG]
                if not result:
                    return False
        current_filter = str(self.entryd.props.text)
        if current_filter:
            result = current_filter in model[iter][self.alpm.DATE]
            if not result:
                return False
        current_filter = self.filter_action
        if current_filter:
            result = current_filter == model[iter][self.alpm.ACTION]
        return result

    @staticmethod
    def pkg_is_installed(package: str) -> (bool, str):
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
                pkg = model.get(iter, self.alpm.PKG)[0]
                if pkg:
                    is_installed, dep = self.pkg_is_installed(pkg)
                    if is_installed:
                        more_txt = f" (installed {dep}) "

                tooltip.set_text(model.get(iter, self.alpm.ACTION)[0] + ' ' + more_txt + model.get(iter, self.alpm.MSG)[0])
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
        l = len(self.entry.get_text())
        if l != 1:
            print('filter.refilter()', 'begin')
            self.filter.refilter()
            #self.populate()
            print('filter.refilter()', 'END')
            self.set_title()

    def on_date_clicked(self, btn):
        """Open calender and get user selection"""
        dialog = CalDialog(self.window)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            tmpdate = datetime.datetime.strptime(f"{dialog.value.year}-{dialog.value.month+1}-{dialog.value.day}", '%Y-%m-%d')
            self.entryd.set_text(tmpdate.strftime('%Y-%m-%d'))
        dialog.destroy()

try:
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--days", help="history age", type=int, default=60)
    parser.add_argument("-f", "--file", help="pacman log", type=argparse.FileType('r'), default='/var/log/pacman.log')
    args = parser.parse_args()
    print('days:', args.days)
    print('log:', args.file.name)

    logs = AlpmLog(max_day=args.days, log_file=args.file.name)
    logs.load_file()
    print("count logs:", len(logs.items))

    applog = MainApp(classlog=logs)
    applog.main()

except KeyboardInterrupt:
    print("\n" + "Error: interrupted by the user.")
    exit(1)
