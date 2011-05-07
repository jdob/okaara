#!/usr/bin/python
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


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

    def simple(self):
        name = self.prompt.prompt('Enter your name:')
        self.prompt.write('Hello %s' % name)

if __name__ == '__main__':
    shell = SampleShell()
    shell.start()
