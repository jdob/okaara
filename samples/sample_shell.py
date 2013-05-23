#!/usr/bin/python
#
# Copyright (c) 2011-2013 Jason Dobies
#
# This file is part of Okaara.
#
# Okaara is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# Okaara is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Okaara.
# If not, see <http://www.gnu.org/licenses/>.

from okaara.shell import Shell, Screen, MenuItem


class SampleShell(Shell):

    def __init__(self):
        Shell.__init__(self)

        self.add_screen(HomeScreen(self), is_home=True)

class HomeScreen(Screen):

    def __init__(self, shell):
        Screen.__init__(self, 'home')

        self.shell = shell
        self.prompt = shell.prompt

        self.add_menu_item(MenuItem(['s', 'simple'], 'simple prompt', self.simple))
        self.add_menu_item(MenuItem('e', 'exits the shell', self.shell.stop))

    def simple(self):
        name = self.prompt.prompt('Enter your name: ')
        self.prompt.write('Hello %s' % name)

if __name__ == '__main__':
    shell = SampleShell()
    shell.start()
