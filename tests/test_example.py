#!/usr/bin/python
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

import sys
import os.path
import unittest
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

from pinyto_desktop_todo import AboutPinytoDesktopTodoDialog

class TestExample(unittest.TestCase):
    def setUp(self):
        self.AboutPinytoDesktopTodoDialog_members = [
        'AboutDialog', 'AboutPinytoDesktopTodoDialog', 'gettext', 'logger', 'logging']

    def test_AboutPinytoDesktopTodoDialog_members(self):
        all_members = dir(AboutPinytoDesktopTodoDialog)
        public_members = [x for x in all_members if not x.startswith('_')]
        public_members.sort()
        self.assertEqual(self.AboutPinytoDesktopTodoDialog_members, public_members)

if __name__ == '__main__':    
    unittest.main()
