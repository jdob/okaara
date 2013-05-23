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

import sys

from okaara.prompt import COLOR_LIGHT_CYAN, COLOR_LIGHT_BLUE
from okaara.cli import Cli, Section, Command


class SampleSectionOne(Section):
    def __init__(self, prompt):
        Section.__init__(self, 'demo1', 'demo section #1')
        self.prompt = prompt

        # Optional Argument Demo
        usage = 'Unspecified required arguments are listed at the bottom. The full ' \
                'listing of specified arguments is displayed when successfully run.'
        opt_arg_command = Command('opt-args', 'configured with multiple arguments, many optional',
                                  self.optional_args,
                                  usage_description=usage)
        opt_arg_command.create_option('--required-1',
                                      'required argument before this command will actually run',
                                      required=True)
        opt_arg_command.create_option('--optional-1',
                                      'optional argument, value will be displayed when specified',
                                      required=False)
        opt_arg_command.create_option('--optional-2', 'another optional argument', required=False)
        self.add_command(opt_arg_command)

    def optional_args(self, **kwargs):
        self.prompt.write('Supplied Arguments:')
        for k, v in kwargs.items():
            self.prompt.write('Key: %-10s   Value: %s' % (k, v))


class UsersSection(Section):
    def __init__(self, prompt):
        Section.__init__(self, 'users', 'manages users in the system')
        self.prompt = prompt

        create_command = Command('create', 'creates a new user in the system', self.create)
        create_command.create_option('--username', 'username for the new user', required=True)
        create_command.create_option('--password', 'password for the new user', required=True)
        create_command.create_option('--group', 'group in which to assign the new user', required=False)

        self.add_command(create_command)

    def create(self, **kwargs):
        self.prompt.write('Creating User')
        self.prompt.write('Username: %s' % kwargs['username'])
        self.prompt.write('Password: %s' % kwargs['password'])
        self.prompt.write('Group:    %s' % kwargs['group'])


class SampleCli(Cli):
    def __init__(self):
        Cli.__init__(self)

        self.username = None

        # CLI-level commands

        # Creating the Command instance directly:
        login_command = Command('login', 'persists user information across multiple calls', self.login)
        login_command.create_option('--username', 'identifies the user', ['-u'], required=True)
        self.add_command(login_command)

        # Using syntactic sugar methods:
        self.create_command('logout', 'removes (fake) stored credentials', self.logout)
        self.create_command('map', 'prints the map of all capabilities in the CLI', self.map)

        # Sections
        self.add_section(SampleSectionOne(self.prompt))
        self.add_section(UsersSection(self.prompt))

        # Naturally, Section and Command can be subclassed and those instances
        # added in the above add_* calls depending on developer style preferences.

    def map(self):
        self.print_cli_map(section_color=COLOR_LIGHT_BLUE, command_color=COLOR_LIGHT_CYAN)

    def login(self, **kwargs):
        self.username = kwargs['username']
        self.prompt.write('Welcome %s' % self.username)

    def logout(self):
        self.username = None
        self.prompt.write('Successfully logged out')

if __name__ == '__main__':
    sys.exit(SampleCli().run(sys.argv[1:]))
