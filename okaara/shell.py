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
from builtins import object

import gettext
import logging
import os
import sys

from okaara.prompt import Prompt

t = gettext.translation('okaara', fallback=True)
if sys.version_info[0] < 3:
    _ = t.ugettext
else:
    _ = t.gettext


LOG = logging.getLogger(__name__)

class Exit(Exception):
    """
    May be raised by any menu item function to stop the shell loop.
    """
    pass


class Shell(object):
    """
    Represents a single shell interface. A shell constists of one or more screens
    that drive the different sections of the shell. At any given time, only one
    screen is active. Only the active screen's menu will be used when interacting
    with the user's input. Based on the user's decisions, the state of the shell
    may be transitioned between different screens.

    This class contains methods screens and actions may use for transitioning
    between screens and interacting with user input.
    """

    def __init__(self, prompt=None, auto_render_menu=False, include_long_triggers=True):
        """
        Creates an empty shell. At least one screen must be added to the shell
        before it is used.

        :param prompt: specifies a prompt object to use for reading/writing to the
                       console; if not specified will default to L{Prompt}
        :type  prompt: L{Prompt}

        :param auto_render_menu: if True, the menu will automatically be rendered after
                                 the execution of each menu item; defaults to False
        :type  auto_render_menu: bool

        :param include_long_triggers: if True, the long versions of default triggers will
                                      be added, if False only single-character triggers
                                      will be added; defaults to True
        :type  include_long_triggers: bool
        """
        self.home_screen = None
        self.current_screen = None
        self.previous_screen = None
        self.screens = {}
        self.auto_render_menu = auto_render_menu

        # Set the default prompt prefix to substitute in the current screen ID
        self.prompt_prefix = '($s) => '

        # Create a default prompt if one was not explicitly specified
        self.prompt = prompt or Prompt()

        # Create the shell-level menu; these can be changed before the shell is run
        previous_triggers = ['<']
        home_triggers = ['^']
        quit_triggers = ['q']
        help_triggers = ['?']
        clear_triggers = ['/']

        if include_long_triggers:
            home_triggers.append('home')

            quit_triggers.append('quit')
            quit_triggers.append('exit')

            help_triggers.append('help')

            clear_triggers.append('clear')

        self.shell_menu_items = {}
        self.ordered_menu_items = [] # kinda ghetto, need to replace with ordered dict for menu_items
        self.add_menu_item(MenuItem(home_triggers, _('move to the home screen'), self.home))
        self.add_menu_item(MenuItem(previous_triggers, _('move to the previous screen'), self.previous))
        self.add_menu_item(MenuItem(help_triggers, _('display help'), self.render_menu))
        self.add_menu_item(MenuItem(clear_triggers, _('clears the screen'), self.clear_screen))
        self.add_menu_item(MenuItem(quit_triggers, _('exit'), self.stop))

    def add_screen(self, screen, is_home=False):
        """
        Adds a new screen for the shell. If a screen was previously added with the
        same screen ID, the newly added screen will replace it.

        :param screen: describes a screen in the shell; may not be None
        :type  screen: L{Screen}
        """
        if screen is None:
            raise ValueError('screen may not be None')

        # Overwrite a previously added screen if one exists
        self.screens[screen.id] = screen

        # If there is no current screen set, use the newly added one
        if self.current_screen is None:
            self.current_screen = screen

        # If the screen is indicated as the home screen or one has not been set,
        # set the home screen
        if is_home or self.home_screen is None:
            self.home_screen = screen

    def add_menu_item(self, menu_item):
        """
        Adds a new menu item that will be available anywhere in the shell.
        Each menu item added to this screen must have a unique trigger.
        If a menu item with the same trigger already exists, it will be
        removed from the menu and replaced by the newly added item.

        :param menu_item: new item to add to the shell; may not be None
        :type  menu_item: L{MenuItem}
        """
        if menu_item is None:
            raise ValueError('menu_item may not be None')

        # Overwrite the existing menu item with the same trigger if one exists
        for trigger in menu_item.triggers:
            self.shell_menu_items[trigger] = menu_item

        if menu_item not in self.ordered_menu_items:
            self.ordered_menu_items.append(menu_item)

    # -- user input handling -----------------------------------------------------------------------

    def start(self, show_menu=True, clear=True):
        """
        Starts the loop to listen for user input and handle according to the current
        screen.
        """

        if clear:
            self.clear_screen()

        if show_menu:
            self.render_menu()

        running = True
        while running:

            # Read the next input from the user
            try:
                input = self.prompt.prompt(self._prompt_prefix())
            except (EOFError, KeyboardInterrupt):
                self.prompt.write('\n')
                return

            # Make sure the user entered something
            if input is None or input.strip() == '':
                continue

            trigger = input.split()[0]
            command_args = input.split()[1:]

            # Search the shell for the menu item first
            item = None
            if trigger in self.shell_menu_items:
                item = self.shell_menu_items[trigger]

            # If a menu item wasn't found in the shell items, try the screen
            if item is None:
                item = self.current_screen.item(trigger)
                if item is None:
                    self.prompt.write(_('Invalid menu item; type "?" for a list of available commands'))
                    continue

            # Call the function for the menu item if one was found
            try:
                args = item.args + tuple(command_args)
                self.execute(item.func, *args, **item.kwargs)
            except Exit:
                break

            # If the menu is set to auto-render, render it before moving on
            if self.auto_render_menu:
                self.render_menu()

    def safe_start(self, show_menu=True, clear=True):
        """
        Launches the shell in an exception block to catch all unexpected exceptions
        to prevent the entire thing from crashing. If an exception is caught, the
        start loop will be restarted.
        """

        try:
            self.start(show_menu=show_menu, clear=clear)
        except SystemExit:
            sys.exit(0)
        except:
            LOG.exception('Unexpected error caught at the shell level')
            self.prompt.write('')
            self.prompt.write(_('An unexpected error has occurred during the last operation.'))
            self.prompt.write(_('More information can be found in the log.'))
            self.prompt.write('')
            self.safe_start(show_menu=False, clear=False)

    def stop(self):
        """
        Causes the shell to stop listening for user commands.
        """
        raise Exit()

    def execute(self, func, *args, **kwargs):
        """
        Executes a function selected by the user from a menu item. This
        call may raise Exit in order to quit the shell.

        Subclasses should override this method to inject pre-run and post-run functionality.
        """
        func(*args, **kwargs)

    # -- screen transition calls -------------------------------------------------------------------

    def transition(self, to_screen_id, show_menu=False, clear=False):
        """
        Transitions the state of the shell to the identified screen. If no screen
        exists with the given ID, the shell will be transitioned to the home screen.

        :param to_screen_id: identifies the screen to change the shell to; may not
                             be None
        :type  to_screen_id: string

        :param show_menu: if True, the menu for the newly transitioned to screen
                          will be displayed
        :type  show_menu: bool

        :param clear: if True, the screen will be cleared before the transition is made
        :type  clear: bool
        """

        if to_screen_id is None or to_screen_id not in self.screens:
            LOG.error('Attempt to transition to non-existent screen [%s]' % to_screen_id)
            to_screen_id = self.home_screen.id

        if clear:
            self.clear_screen()

        self.previous_screen = self.current_screen
        self.current_screen = self.screens[to_screen_id]

        if show_menu:
            self.render_menu(display_shell_menu=False)

    def previous(self):
        """
        Transitions the state of the shell to the previous screen. If there is no
        previous screen, the shell will be transitioned to the home screen.
        """
        if self.previous_screen is None:
            self.home()
        else:
            self.transition(self.previous_screen.id)

    def home(self):
        """
        Transitions the state of the shell to the home screen.
        """
        self.transition(self.home_screen.id)

    # -- display related calls ---------------------------------------------------------------------

    def clear_screen(self):
        """
        Calls to the command line to clear the console.
        """
        os.system('clear')

    def render_menu(self, display_shell_menu=True):
        """
        Renders the menu for the current screen to the screen.
        """

        # Screen menu items
        self.prompt.write('')
        for item in self.current_screen.items():
            self._render_menu_item(', '.join(item.triggers), item.description)

        # Shell triggers
        if display_shell_menu:

            self.prompt.write('')

            # Shell menu items
            if len(self.shell_menu_items) > 0:
                self.prompt.write('')
                for item in self.ordered_menu_items:
                    self._render_menu_item(', '.join(item.triggers), item.description)

        self.prompt.write('')

    def _render_menu_item(self, trigger, description):
        """
        Writes a single menu item to the screen, wrapping appropriately for long triggers
        """
        if len(trigger) < 4:
            self.prompt.write('   %-4s%s' % (trigger, description))
        else:
            self.prompt.write('   %s' % trigger)
            self.prompt.write('       %s' % description)

    def _prompt_prefix(self):
        """
        Returns the prompt prefix, substituting in any variables that have been defined.
        """
        p = self.prompt_prefix.replace('$s', self.current_screen.id)
        return p


class Screen(object):
    """
    A screen is an individual "section" of a shell. The granularity of its use will
    vary based on the application but can most easily be related to different
    screens in a graphical UI.
    """

    def __init__(self, id):
        """
        :param id: uniquely identifies this screen instance in a shell; may not
                   be None
        :type  id: string
        """
        if id is None:
            raise ValueError('id may not be None')

        self.id = id
        self.menu_items = {}
        self.ordered_menu_items = [] # kinda ghetto, need to replace with ordered dict for menu_items

    def __str__(self):
        return 'ID [%s]' % self.id

    def add_menu_item(self, menu_item):
        """
        Adds a new menu item that will be available on this screen. Each menu item
        added to this screen must have a unique trigger. If a menu item with
        the same trigger already exists, it will be removed from the menu and
        replaced by the newly added item.

        :param menu_item: new item to add to this screen; may not be None
        :type  menu_item: L{MenuItem}
        """

        if menu_item is None:
            raise ValueError('menu_item may not be None')

        # Overwrite the existing menu item with the same trigger if one exists
        for trigger in menu_item.triggers:
            self.menu_items[trigger] = menu_item

        if menu_item not in self.ordered_menu_items:
            self.ordered_menu_items.append(menu_item)

    def item(self, trigger):
        """
        Returns the menu item for the given trigger if one exists; None otherwise.

        :param trigger: identifies the menu item being searched for
        :type  trigger: string

        :return: menu item for the given trigger if one is found; None otherwise
        :rtype:  L{MenuItem} or None
        """
        return self.menu_items.get(trigger)

    def items(self):
        """
        Returns a list of menu items in this screen.

        :return: list of menu items; empty list if none have been added
        :rtype:  list of L{MenuItem}
        """
        return tuple(self.ordered_menu_items)


def noop():
    """
    Stub method used as the default in menu items to facilitate prototyping of
    the menu without needing to have all the method implementations in place.
    """
    pass

class MenuItem(object):
    """
    An individual menu item the user can interact with. The shell instance will
    take care of determining which menu item the user has selected and invoking
    its associated function. Any extra arguments input by the user when calling
    the menu item will be passed to the function on invocation.

    The shell reserves certain triggers for general use. Be sure that a menu
    item trigger does not overlap with one of the shell-level triggers defined
    in the shell instance.
    """

    def __init__(self, triggers, description, func=noop, *args, **kwargs):
        """
        :param triggers: character or string (or list of them) the user will
                         input to cause the associated function to be invoked;
                         may not be None
        :type  triggers: str or list

        :param description: short (1-2 line) description of what the menu item
                            does; displayed
        :type  description: string

        :param func: function to invoke when this menu item is selected; extra
                     arguments specified after the trigger will be passed to
                     this function; may not be None
        :type  func: function

        :param args: arguments that will be passed to the function when it is
                     executed

        :param kwargs: key word arguments to be passed to the function when it
                       is executed
        """
        if triggers is None:
            raise ValueError('trigger may not be None')

        if func is None:
            raise ValueError('func may not be None')

        # Make sure it's in list form
        if not isinstance(triggers, list) and not isinstance(triggers, tuple):
            triggers = [triggers]

        self.triggers = triggers
        self.description = description
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return 'Triggers: [%s], Description [%s], Function: [%s]' % (', '.join(self.triggers), self.description, self.func.__name__)

    def __eq__(self, other):
        return self.triggers == other.triggers
