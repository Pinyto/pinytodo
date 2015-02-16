# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

#######################################################################
# Pinytodo - A Pinyto synced ToDo-List for Gtk+
# Copyright (C) 2105 Johannes Merkert <jonny@pinyto.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#######################################################################

from locale import gettext as _

from gi.repository import Gtk, GObject  # pylint: disable=E0611
import logging
logger = logging.getLogger('pinyto_desktop_todo')

import dbus
import dbus.mainloop.glib

from pinyto_desktop_todo_lib import Window
from pinyto_desktop_todo.AboutPinytoDesktopTodoDialog import AboutPinytoDesktopTodoDialog
from pinyto_desktop_todo.PreferencesPinytoDesktopTodoDialog import PreferencesPinytoDesktopTodoDialog

import json
import copy


class TodoItem(Gtk.Box):
    def __init__(self, on_checkbutton_toggled, on_up_button_clicked, on_delete_button_clicked,
                 text="", done=False, time="", priority=0, _id=""):
        self._id = _id
        self.time = time
        self.priority = priority
        super(TodoItem, self).__init__(spacing=0)
        self.checkbutton = Gtk.CheckButton()
        self.checkbutton.set_active(done)
        self.checkbutton.connect("toggled", on_checkbutton_toggled)
        self.text_entry = Gtk.Entry()
        self.text_entry.set_placeholder_text(_("_whatDoYouWantToDo_"))
        self.text_entry.set_text(text)
        self.up_button = Gtk.Button()
        self.up_button.connect("clicked", on_up_button_clicked)
        self.up_button.set_image(Gtk.Image(stock=Gtk.STOCK_GOTO_TOP))
        self.delete_button = Gtk.Button()
        self.delete_button.connect("clicked", on_delete_button_clicked)
        self.delete_button.set_image(Gtk.Image(stock=Gtk.STOCK_DELETE))
        self.pack_start(self.checkbutton, expand=False, fill=True, padding=0)
        self.pack_start(self.text_entry, expand=True, fill=True, padding=0)
        self.pack_start(self.up_button, expand=False, fill=True, padding=0)
        self.pack_start(self.delete_button, expand=False, fill=True, padding=0)
        self.delete_button.show()
        self.up_button.show()
        self.text_entry.show()
        self.checkbutton.show()
        self.show()

    def set_id(self, _id):
        self._id = _id

    def get_id(self):
        return self._id

    def has_id(self):
        return len(self._id) > 0

    def set_text(self, text):
        self.get_children()[1].set_text(text)

    def get_text(self):
        return unicode(self.get_children()[1].get_text(), encoding='utf-8')

    def set_finished(self, finished):
        self.get_children()[0].set_active(finished)

    def get_finished(self):
        return self.get_children()[0].get_active()

    def set_time(self, time):
        self.time = time

    def get_time(self):
        return self.time

    def has_time(self):
        return len(self.time) > 0

    def set_priority(self, priority):
        self.priority = priority

    def get_priority(self):
        return self.priority


# See pinyto_desktop_todo_lib.Window.py for more details about how this class works
class PinytoDesktopTodoWindow(Window):
    __gtype_name__ = "PinytoDesktopTodoWindow"
    
    def finish_initializing(self, builder):  # pylint: disable=E1002
        """Set up the main window"""
        super(PinytoDesktopTodoWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutPinytoDesktopTodoDialog
        self.PreferencesDialog = PreferencesPinytoDesktopTodoDialog

        # Code for other initialization actions should be added here.
        self.add_button = self.builder.get_object("add_button")
        self.toolbar = self.builder.get_object("toolbar")
        self.toolbar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        self.item_list = self.builder.get_object("item_list")
        self.sync_switch = self.builder.get_object("sync_switch")
        self.status_label = self.builder.get_object("status_label")

        self.cloud_list = []

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SessionBus()
        try:
            self.assembly_interface = bus.get_object(
                "de.pinyto.daemon",
                "/Assembly")
        except dbus.DBusException:
            self.sync_switch.destroy()
            self.status_label.set_text(_("_noConnectionToPinytoDaemon_"))

        self.load_list()
        GObject.timeout_add(10000, self.check_for_sync)

    def check_if_document_is_changed(self, document):
        for item in self.cloud_list:
            if item['_id'] == document.get_id():
                if item['data']['text'] != document.get_text() or \
                   item['data']['finished'] != document.get_finished or \
                   item['data']['priority'] != document.get_priority():
                    return True
        return False

    @staticmethod
    def save_success_callback(raw_data, document):
        data = json.loads(raw_data)
        if 'success' in data and data['success']:
            document.set_id(data['_id'])
        if 'error' in data:
            print(data['error'])

    @staticmethod
    def save_error_callback(data):
        print(data)

    def get_document_priority(self, document):
        unfinished_offset = 0
        for index, candidate in enumerate(self.item_list.get_children()):
            if not candidate.get_finished():
                unfinished_offset = index
            if candidate == document:
                if candidate.get_finished():
                    return index - unfinished_offset - 1
                else:
                    return index

    def create_transmission_document(self, document):
        transmission_document = {
            'type': 'todo',
            'data': {
                'text': document.get_text(),
                'priority': self.get_document_priority(document)
            }
        }
        _id = document.get_id()
        if len(_id) > 0:
            transmission_document['_id'] = _id
        if document.has_time():
            transmission_document['time'] = document.get_time()
        if document.get_finished():
            transmission_document['data']['finished'] = 1
        else:
            transmission_document['data']['finished'] = 0
        return transmission_document

    def save_document_if_necessary(self, document):
        if document.has_id():
            if self.check_if_document_is_changed(document):
                self.assembly_interface.ApiCall(
                    'pinyto', 'Todo', 'save',
                    json.dumps({'document': self.create_transmission_document(document)}),
                    dbus_interface='de.pinyto.daemon.api',
                    reply_handler=lambda raw_data: self.save_success_callback(raw_data, document),
                    error_handler=self.save_error_callback
                )
        else:
            self.assembly_interface.ApiCall(
                'pinyto', 'Todo', 'save',
                json.dumps({'document': self.create_transmission_document(document)}),
                dbus_interface='de.pinyto.daemon.api',
                reply_handler=lambda raw_data: self.save_success_callback(raw_data, document),
                error_handler=self.save_error_callback
            )

    def delete_callback(self, raw_data, position, document):
        try:
            data = json.loads(raw_data)
        except ValueError:
            self.cloud_list.insert(position, document)
            print(raw_data)
            return False
        if 'success' not in data or not data['success']:
            self.cloud_list.insert(position, document)
            if 'error' in data:
                print(data['error'])
            else:
                print(raw_data)
            return False
        return True

    def sync_documents(self):
        print("Syncing documents.")
        for document in self.item_list.get_children():
            document.set_priority(self.get_document_priority(document))
            self.save_document_if_necessary(document)
        for index, cloud_document in enumerate(self.cloud_list):
            found = False
            for document in self.item_list.get_children():
                if cloud_document['_id'] == document.get_id():
                    found = True
            if not found:
                self.assembly_interface.ApiCall(
                    'pinyto', 'Todo', 'delete',
                    json.dumps({'document': {'_id': cloud_document['_id']}}),
                    dbus_interface='de.pinyto.daemon.api',
                    reply_handler=lambda raw_data: self.delete_callback(raw_data, index, cloud_document),
                    error_handler=lambda raw_data: self.delete_callback(raw_data, index, cloud_document)
                )
                self.cloud_list.pop(index)

    def check_for_sync(self):
        self.load_list()
        return True

    def sort_items_for_priority(self):
        sorted_list = sorted(self.item_list.get_children(), key=lambda doc: doc.get_priority(), reverse=True)
        for document in self.item_list.get_children():
            self.item_list.remove(document)
        for document in sorted_list:
            if document.get_finished():
                self.item_list.pack_end(document, expand=False, fill=True, padding=0)
            else:
                self.item_list.pack_start(document, expand=False, fill=True, padding=0)
                self.item_list.reorder_child(document, 0)

    def load_list_success(self, string_data):
        data = json.loads(string_data)
        if 'error' in data:
            print(data['error'])
            return True
        self.cloud_list = []
        if 'result' not in data:
            print("The cloud returned no results. This is not an empty list but an error.")
            return True
        for item in data['result']:
            priority = 0
            if 'priority' in item['data']:
                try:
                    priority = int(item['data']['priority'])
                except ValueError:
                    priority = 0
            if item['data']['finished']:
                item['data']['finished'] = True
            else:
                item['data']['finished'] = False
            self.cloud_list.append(copy.deepcopy(item))
            found = False
            for document in self.item_list.get_children():
                if document.get_id() == item['_id']:
                    found = True
                    document.set_text(item['data']['text'])
                    document.set_time(item['time'])
                    document.set_priority(priority)
                    document.set_finished(item['data']['finished'])
                    if item['data']['finished']:
                        self.item_list.reorder_child(document, -1)
                    else:
                        self.item_list.reorder_child(document, 0)
            if not found:
                new_item = TodoItem(
                    self.on_checkbutton_toggled,
                    self.on_up_button_clicked,
                    self.on_delete_button_clicked,
                    text=item['data']['text'],
                    done=item['data']['finished'],
                    time=item['time'],
                    priority=priority,
                    _id=item['_id'])
                if item['data']['finished']:
                    self.item_list.pack_start(new_item, expand=False, fill=True, padding=0)
                    self.item_list.reorder_child(new_item, 0)
                else:
                    self.item_list.pack_end(new_item, expand=False, fill=True, padding=0)
        self.sort_items_for_priority()
        self.sync_documents()

    @staticmethod
    def load_list_error(data):
        print(data)

    def load_list(self):
        self.assembly_interface.ApiCall(
            'pinyto', 'Todo', 'get_list', json.dumps({}),
            dbus_interface='de.pinyto.daemon.api',
            reply_handler=self.load_list_success,
            error_handler=self.load_list_error
        )

    def on_up_button_clicked(self, widget):
        if widget.get_parent().get_children()[0].get_active():
            self.item_list.reorder_child(widget.get_parent(), -1)
        else:
            self.item_list.reorder_child(widget.get_parent(), 0)
        self.sync_documents()

    def on_delete_button_clicked(self, widget):
        widget.get_parent().destroy()
        self.sync_documents()

    def on_checkbutton_toggled(self, widget):
        item = widget.get_parent()
        self.item_list.remove(item)
        if widget.get_active():
            self.item_list.pack_end(item, expand=False, fill=True, padding=0)
        else:
            self.item_list.pack_start(item, expand=False, fill=True, padding=0)
            self.item_list.reorder_child(item, 0)
        self.sync_documents()

    def on_add_button_clicked(self):
        new_item = TodoItem(self.on_checkbutton_toggled, self.on_up_button_clicked, self.on_delete_button_clicked)
        self.item_list.pack_start(new_item, expand=False, fill=True, padding=0)
        self.item_list.reorder_child(new_item, 0)
        self.sort_items_for_priority()
        self.sync_documents()