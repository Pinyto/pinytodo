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

import logging
logger = logging.getLogger('pinyto_desktop_todo')

from pinyto_desktop_todo_lib.AboutDialog import AboutDialog

# See pinyto_desktop_todo_lib.AboutDialog.py for more details about how this class works.
class AboutPinytoDesktopTodoDialog(AboutDialog):
    __gtype_name__ = "AboutPinytoDesktopTodoDialog"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the about dialog"""
        super(AboutPinytoDesktopTodoDialog, self).finish_initializing(builder)

        # Code for other initialization actions should be added here.

