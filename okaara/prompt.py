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
from __future__ import division
from builtins import str
from builtins import object

from functools import reduce
import copy
import fcntl
import getpass
import gettext
import logging
import os
import struct
import sys
import termios

t = gettext.translation('okaara', fallback=True)
if sys.version_info[0] < 3:
    _ = t.ugettext
else:
    _ = t.gettext

# -- constants ----------------------------------------------------------------

LOG = logging.getLogger(__name__)

# Returned to indicate the user has interrupted the input
ABORT = object()

# Indicates the automatic wrap should use the current width of the screen,
# calculated at the time of rendering
WIDTH_TERMINAL = object()

COLOR_WHITE = '\033[0m'
COLOR_BRIGHT_WHITE = '\033[1m'

COLOR_GRAY = '\033[30m'
COLOR_RED = '\033[31m'
COLOR_GREEN = '\033[32m'
COLOR_YELLOW = '\033[33m'
COLOR_BLUE = '\033[34m'
COLOR_PURPLE = '\033[35m'
COLOR_CYAN = '\033[36m'

COLOR_LIGHT_GRAY = '\033[90m'
COLOR_LIGHT_RED = '\033[91m'
COLOR_LIGHT_GREEN = '\033[92m'
COLOR_LIGHT_YELLOW = '\033[93m'
COLOR_LIGHT_BLUE = '\033[94m'
COLOR_LIGHT_PURPLE = '\033[95m'
COLOR_LIGHT_CYAN = '\033[96m'

COLOR_BG_GRAY = '\033[40m'
COLOR_BG_RED = '\033[41m'
COLOR_BG_GREEN = '\033[42m'
COLOR_BG_YELLOW = '\033[43m'
COLOR_BG_BLUE = '\033[44m'
COLOR_BG_PURPLE = '\033[45m'
COLOR_BG_CYAN = '\033[46m'

POSITION_SAVE = '\033[s'
POSITION_RESET = '\033[u'

MOVE_UP = '\033[%dA' # sub in number of lines
MOVE_DOWN = '\033[%dB' # sub in number of lines
MOVE_FORWARD = '\033[%dC' # sub in number of characters
MOVE_BACKWARD = '\033[%dD' # sub in number of characters

CLEAR = '\033[2J'
CLEAR_EOL = '\033[K'
CLEAR_REMAINDER = '\033[J'

TAG_READ = 'read'
TAG_WRITE = 'write'

# -- classes ------------------------------------------------------------------

class Prompt(object):
    """
    Used to communicate between the application and the user. The Prompt class can be
    subclassed to provide custom implementations of read and write to alter the input/output
    sources. By default, stdin and stdout will be used.
    """

    def __init__(self, input=sys.stdin, output=sys.stdout, normal_color=COLOR_WHITE,
                 enable_color=True, wrap_width=None, record_tags=False):
        """
        Creates a new instance that will read and write to the given streams.

        :param input: stream to read from; defaults to stdin
        :type  input: file

        :param output: stream to write prompt statements to; defaults to stdout
        :type  output: file

        :param normal_color: color of the text to write; this will be used in the color
                             function to reset the text after coloring it
        :type  normal_color: str (one of the COLOR_* variables in this module)

        :param enable_color: determines if this prompt instance will output any modified
                             colors; if this is false the color() method will
                             always render the text as the normal_color
        :type  enable_color: bool

        :param wrap_width: if specified, content written by this prompt will
                           automatically be wrapped to this width
        :type  wrap_width: int or None

        :param record_tags: if true, the prompt will keep track of tags passed
                            to all write calls
        :type  record_tags: bool
        """
        self.input = input
        self.output = output
        self.normal_color = normal_color
        self.enable_color = enable_color
        self.wrap_width = wrap_width
        self.record_tags = record_tags

        self.tags = []

        # Initialize the screen with the normal color
        if self.enable_color:
            self.write(self.normal_color, new_line=False)

    # -- general --------------------------------------------------------------

    def read(self, prompt, tag=None, interruptable=True):
        """
        Reads user input. This will likely not be called in favor of one of the prompt_* methods.

        :param prompt: the prompt displayed to the user when the input is requested
        :type  prompt: string

        :return: the input specified by the user
        :rtype:  string
        """
        self._record_tag(TAG_READ, tag)
        self.write(prompt, new_line=False)

        try:
            r = self.input.readline().rstrip() # rstrip removes the trailing \n
            return r
        except (EOFError, KeyboardInterrupt) as e:
            if interruptable:
                self.write('') # the ^C won't cause a line break but we probably want one
                return ABORT
            else:
                raise e

    def write(self, content, new_line=True, center=False, color=None, tag=None, skip_wrap=False):
        """
        Writes content to the prompt's output stream.

        :param content: content to display to the user
        :type  content: string

        :param skip_wrap: if true, auto-wrapping won't be applied; defaults to false
        :type  skip_wrap: bool
        """
        self._record_tag(TAG_WRITE, tag)

        content = str(content)

        if not skip_wrap:
            content = self.wrap(content)

        if center: content = self.center(content)

        if color is not None: content = self.color(content, color)

        if new_line: content += '\n'

        self.output.write(content)

    def color(self, text, color):
        """
        Colors the given text with the given color, resetting the output back to whatever
        color is defined in this instance's normal_color. Nothing is output to the screen;
        the formatted string is returned.

        :param text: text to color
        :type  text: str

        :param color: coding for the color (see the COLOR_* variables in this module)
        :type  color: str

        :return: new string with the proper color escape sequences in place
        :rtype:  str
        """

        # Skip the wrapping if color is disabled at the instance level
        if not self.enable_color or color is None:
            return text

        return '%s%s%s' % (color, text, self.normal_color)

    def center(self, text, width=None):
        """
        Centers the given text. Nothing is output to the screen; the formatted string
        is returned. The width in which to center is the first non-None value
        in the following order:

         * Provided width parameter
         * Instance-level wrap_width value
         * Terminal width

        :param text: text to center
        :type  text: str

        :param width: width to center the text between
        :type  width: int

        :return: string with spaces padding the left to center it
        :rtype:  str
        """

        if width is None:
            if self.wrap_width is None or self.wrap_width is WIDTH_TERMINAL:
                width = self.terminal_size()[0]
            else:
                width = self.wrap_width

        if len(text) >= width:
            return text
        else:
            spacer = ' ' * ((width - len(text)) // 2)
            return spacer + text

    def wrap(self, content, wrap_width=None, remaining_line_indent=0):
        """
        If the wrap_width is specified, this call will introduce new line
        characters to maintain that width.

        :param content: text to wrap
        :type  content: str

        :param wrap_width: number of characters to wrap to
        :type  wrap_width: int

        :param remaining_line_indent: number of characters to indent any new
               lines generated from this call
        :type  remaining_line_indent: int

        :return: wrapped version of the content string
        :rtype:  str
        """

        # If it's not overridden, use the instance-configured wrap width
        if wrap_width is None:
            wrap_width = self.wrap_width

        # If the instance isn't configured with a wrap width, we're done
        if wrap_width is None:
            return content

        # If the instance is configured to dynamically calculate it based on
        # the terminal width, figure that value out now
        if wrap_width is WIDTH_TERMINAL:
            wrap_width = self.terminal_size()[0]

        # Actual splitting algorithm
        def _rightmost_space_index(str):
            for i in range(len(str) - 1, -1, -1):
                if str[i] == ' ' : return i
            return None

        lines = [] # running track of split apart lines; assemble at the end
        content = copy.copy(content)
        first_pass = True

        while True:
            # If there's nothing left, we're done
            if len(content) is 0:
                break

            # Strip off any leading whitespace to left justify the new line;
            # don't strip for the first pass through it in case the user indented.
            # After stipping off any accidental whitespace, add in the indent
            # for non-first lines.
            if not first_pass:
                content = content.lstrip()
                content = (' ' * remaining_line_indent) + content
            else:
                first_pass = False

            # Ideal situation is the text fills the width
            end_index = wrap_width
            chunk = content[:end_index]

            # If this is the last chunk left, we're done
            if end_index >= len(content):
                lines.append(chunk)
                break

            # If the next character is a space, we've broken at a good point
            if end_index < len(content) and content[end_index] == ' ':
                lines.append(chunk)
                content = content[end_index:]
                continue

            # This is the ugly case. Backtrack to the right-most space and make
            # that the new chunk.

            # I'd like to use rpartition here, but for outside reasons I have
            # to stay 2.4 compliant and that's a 2.5 method. Damn.

            last_space_index = _rightmost_space_index(chunk)

            # If we found a space we can backtrack to and split there, use that
            # as the chunk. If not, just leave the split as is.
            if last_space_index is not None:

                # In the case of a remaining line indent, we need to make sure
                # the right-most space isn't just the indent, otherwise we're
                # going to loop indefinitely.
                if remaining_line_indent is not None and last_space_index > remaining_line_indent:
                    end_index = last_space_index
                    chunk = content[:end_index]

            lines.append(chunk)
            content = content[end_index:]

        assembled = '\n'.join(lines)

        return assembled

    def move(self, direction):
        """
        Writes the given move cursor character to the screen without a new
        line character. Values for direction should be one of the MOVE_*
        variables.

        :param direction: move character to write
        :type  direction: str
        """
        self.write(direction, new_line=False)

    def clear(self, clear_character=CLEAR):
        """
        Writes one of the clear characters to the screen. If none is given,
        the entire screen is cleared. One of the CLEAR_* variables can be
        used to scope the cleared space.

        :param clear_character: character code to write; should be one of
               the CLEAR_* variables
        :type  clear_character: str
        """
        self.write(clear_character, new_line=False)

    def save_position(self):
        """
        Saves the current location of the cursor. The cursor can be moved back
        to this position by using the reset_position call.
        """
        self.write(POSITION_SAVE, new_line=False)

    def reset_position(self):
        """
        Moves the cursor back to the location of the cursor at the last point
        save_position was called.
        """
        self.write(POSITION_RESET, new_line=False)

    @classmethod
    def terminal_size(cls):
        """
        Returns the width and height of the terminal.

        :return: tuple of width and height values
        :rtype:  (int, int)
        """
        ioctl = fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0))
        h, w, hp, wp = struct.unpack('HHHH', ioctl)
        return w, h

    # -- prompts --------------------------------------------------------------

    def prompt_file(self, question, allow_directory=False, allow_empty=False, interruptable=True):
        """
        Prompts the user for the full path to a file, reprompting if the file does not
        exist. If allow_empty is specified, the validation will only be performed if the
        user enters a value.
        """
        f = self.prompt(question, allow_empty=allow_empty, interruptable=interruptable)

        if (f is None or f.strip() == '') and allow_empty:
            return f
        elif os.path.exists(f) and (allow_directory or os.path.isfile(f)):
            return f
        else:
            self.write(_('Cannot find file, please enter a valid path'))
            self.write('')
            return self.prompt_file(question, allow_directory=allow_directory, allow_empty=allow_empty, interruptable=interruptable)

    def prompt_values(self, question, values, interruptable=True):
        """
        Prompts the user for the answer to a question where only an enumerated set of values
        should be accepted.

        :param values: list of acceptable answers to the question
        :type  values: list

        :return: will be one of the entries in the values parameter
        :rtype:  string
        """
        a = None
        while a not in values:
            a = self.prompt(question, interruptable=interruptable)

        return a

    def prompt_y_n(self, question, interruptable=True):
        """
        Prompts the user for the answer to a yes/no question, assuming the value 'y' for yes and
        'n' for no. If neither is entered, the user will be re-prompted until one of the two is
        indicated.

        :return: True if 'y' was specified, False otherwise
        :rtype:  boolean
        """
        a = ''
        while a != 'y' and a != 'n' and a is not ABORT:
            a = self.prompt(question, interruptable=interruptable)

        if a is ABORT:
            return a

        return a.lower() == 'y'

    def prompt_range(self, question, high_number, low_number=1, interruptable=True):
        """
        Prompts the user to enter a number between the given range. If the input is invalid, the
        user wil be re-prompted until a valid number is provided.
        """
        while True:
            a = self.prompt_number(question, interruptable=interruptable)

            if a > high_number or a < low_number:
                self.write(_('Please enter a number between %d and %d') % (low_number, high_number))
                continue

            return a

    def prompt_number(self, question, allow_negatives=False, allow_zero=False, default_value=None, interruptable=True):
        """
        Prompts the user for a numerical input. If the given value does not represent a number,
        the user will be re-prompted until a valid number is provided.

        :return: number entered by the user that conforms to the parameters in this call
        :rtype:  int
        """
        while True:
            a = self.prompt(question, allow_empty=default_value is not None, interruptable=interruptable)

            if a is ABORT:
                return a

            if (a is None or a == '') and default_value is not None:
                return default_value

            try:
                i = int(a)
            except ValueError:
                self.write(_('Please enter a number'))
                continue

            if not allow_negatives and i < 0:
                self.write(_('Please enter a number greater than zero'))
                continue

            if not allow_zero and i == 0:
                self.write(_('Please enter a non-zero value'))
                continue

            return i

    def prompt_default(self, question, default_value, interruptable=True):
        """
        Prompts the user for an answer to the given question. If the user does not enter a value,
        the default will be returned.

        :param default_value: if the user does not enter a value, this value is returned
        :type  default_value: string
        """
        answer = self.prompt(question, allow_empty=True, interruptable=interruptable)

        if answer is None or answer == '':
            return default_value
        else:
            return answer

    def prompt_multiselect_menu(self, question, menu_values, interruptable=True):
        """
        Displays a list of items, allowing the user to select 1 or more items before continuing.
        The items selected by the user are returned.

        :return: list of indices of the items the user selected, empty list if none are selected;
                 ABORT is returned if the user selects to abort the menu
        :rtype:  list or ABORT
        """
        selected_indices = []

        q = _('Enter value (1-%s) to toggle selection, \'c\' to confirm selections, or \'?\' for more commands: ') % len(menu_values)

        while True:
            self.write(question)

            # Print the current state of the list
            for index, value in enumerate(menu_values):

                if index in selected_indices:
                    is_selected = 'x'
                else:
                    is_selected = '-'

                self.write('  %s  %-2d: %s' % (is_selected, index + 1, value))

            selection = self.prompt(q, interruptable=interruptable)
            self.write('')

            if selection is ABORT:
                return ABORT
            elif selection == '?':
                self.write(_('  <num> : toggles selection, value values between 1 and %s') % len(menu_values))
                self.write(_('  x-y  : toggle the selection of a range of items (example: "2-5" toggles items 2 through 5)'))
                self.write(_('  a    : select all items'))
                self.write(_('  n    : select no items'))
                self.write(_('  c    : confirm the currently selected items'))
                self.write(_('  b    : abort the item selection'))
                self.write(_('  l    : clears the screen and redraws the menu'))
                self.write('')
            elif selection == 'c':
                return selected_indices
            elif selection == 'a':
                selected_indices = list(range(0, len(menu_values)))
            elif selection == 'n':
                selected_indices = []
            elif selection == 'b':
                return ABORT
            elif selection == 'l':
                self.clear()
            elif self._is_range(selection, len(menu_values)):
                lower, upper = self._range(selection)
                for i in range(lower, upper + 1):
                    if i in selected_indices:
                        selected_indices.remove(i)
                    else:
                        selected_indices.append(i)
            elif selection.isdigit() and int(selection) < (len(menu_values) + 1):
                value_index = int(selection) - 1

                if value_index in selected_indices:
                    selected_indices.remove(value_index)
                else:
                    selected_indices.append(value_index)

    def prompt_multiselect_sectioned_menu(self, question, section_items, section_post_text=None, interruptable=True):
        """
        Displays a multiselect menu for the user where the items are broken up by section,
        however the numbering is consecutive to provide unique indices for the user to use
        for selection. Entries from one or more section may be toggled; the section
        headers are merely used for display purposes.

        Each key in section_items is displayed as the section header. Each item in the
        list at that key will be rendered as belonging to that section.

        The returned value will be a dict that maps each section header (i.e. key in section_items)
        and the value is a list of indices that were selected from the original list passed in
        section_items under that key. If no items were selected under a given section, an empty
        list is the value in the return for each section key.

        For example, given the input data::

            { 'Section 1' : ['Item 1.1', 'Item 1.2'],
              'Section 2' : ['Item 2.1'],}

        The following is rendered for the user::

            Section 1
              -  1 : Item 1.1
              -  2 : Item 1.2
            Section 2
              -  3 : Item 2.1

        If the user entered 1, 2, and 3, thus toggling them as selected, the following would be returned::

            { 'Section 1' : [0, 1],
              'Section 2' : [0],}

        However, if only 2 was toggled, the return would be::

            { 'Section 1' : [1],
              'Section 2' : [],}

        If the user chooses the "abort" option, None is returned.

        :param question: displayed to the user before displaying the menu
        :type  question: str

        :param section_items: data to be rendered; each key must be a string and each value must
                              be a list of strings
        :type  section_items: dict {str : list[str]}

        :param section_post_text: if specified, this string will be displayed on its own line between
                                  each section
        :type  section_post_text: str

        :return: selected indices for each list specified in each section; ABORT
                 if the user elected to abort the selection
        :rtype:  dict {str : list[int]} or ABORT
        """
        selected_index_map = {}
        for key in section_items:
            selected_index_map[key] = []

        total_item_count = reduce(lambda count, key: count + len(section_items[key]), list(section_items.keys()), 0)

        q = _('Enter value (1-%s) to toggle selection, \'c\' to confirm selections, or \'?\' for more commands: ') % total_item_count

        while True:
            self.write(question)

            # Print current state of the list, keeping a running tuple that maps the index
            # displayed to/used by the user to the section key and index that item was found in
            mapper = []
            counter = 1

            for key in section_items:

                # Write the section header
                self.write('  %s' % key)

                # Render the list, using an incrementing toggle number that transcends any one section
                for index, item in enumerate(section_items[key]):
                    if index in selected_index_map[key]:
                        is_selected = 'x'
                    else:
                        is_selected = '-'

                    self.write('    %s  %-2d: %s' % (is_selected, counter, item))
                    mapper.append((key, index))
                    counter += 1

                # If the caller wants something between sections, display it now
                if section_post_text is not None:
                    self.write(section_post_text)

            selection = self.prompt(q, interruptable=interruptable)
            self.write('')

            if selection is ABORT:
                return ABORT
            elif selection == '?':
                self.write(_('  <num> : toggles selection, value values between 1 and %s') % total_item_count)
                self.write(_('  x-y   : toggle the selection of a range of items (example: "2-5" toggles items 2 through 5)'))
                self.write(_('  a     : select all items'))
                self.write(_('  n     : select no items'))
                self.write(_('  c     : confirm the currently selected items'))
                self.write(_('  b     : abort the item selection'))
                self.write(_('  l     : clears the screen and redraws the menu'))
                self.write('')
            elif selection == 'c':
                return selected_index_map
            elif selection == 'a':
                # Recreate the selected index map, adding in indices for each item
                selected_index_map = {}
                for key in section_items:
                    selected_index_map[key] = list(range(0, len(section_items[key])))
            elif selection == 'n':
                selected_index_map = {}
                for key in section_items:
                    selected_index_map[key] = []
            elif selection == 'b':
                return ABORT
            elif selection == 'l':
                os.system('clear')
            elif self._is_range(selection, total_item_count):
                lower, upper = self._range(selection)
                for i in range(lower, upper + 1):
                    section_key = mapper[i][0]
                    section_index = mapper[i][1]

                    if section_index in selected_index_map[section_key]:
                        selected_index_map[section_key].remove(section_index)
                    else:
                        selected_index_map[section_key].append(section_index)
            elif selection.isdigit() and int(selection) < (total_item_count + 1):
                value_index = int(selection) - 1
                section_key = mapper[value_index][0]
                section_index = mapper[value_index][1]

                if section_index in selected_index_map[section_key]:
                    selected_index_map[section_key].remove(section_index)
                else:
                    selected_index_map[section_key].append(section_index)

    def prompt_menu(self, question, menu_values, interruptable=True):
        """
        Displays a list of items, allowing the user to select a single item in the
        list. The index of the selected item is returned. If interruptable is
        set to true and the user exits (through ctrl+c), the ABORT constant
        is returned.

        :param question: displayed to the user prior to rendering the list
        :type  question: str

        :param menu_values: list of items to display in the menu; the returned value
                            will be one of the items in this list
        :type  menu_values: list of str

        :return: index of the selected item; ABORT if the user elected to abort
        :rtype:  int or ABORT
        """

        self.write(question)

        for index, value in enumerate(menu_values):
            self.write('  %-2d - %s' % (index + 1, value))

        q = _('Enter value (1-%d) or \'b\' to abort: ') % len(menu_values)

        while True:
            selection = self.prompt(q, interruptable=interruptable)

            if selection is ABORT or selection == 'b':
                return ABORT
            elif selection.isdigit() and int(selection) < (len(menu_values) + 1):
                return int(selection) - 1 # to remove the +1 for display purposes

    def prompt_password(self, question, verify_question=None, unmatch_msg=None, interruptable=True):
        """
        Prompts the user for a password. If a verify question is specified, the
        user will be prompted to match the previously entered password (suitable
        for things such as changing a password). If it is not specified, the first
        value entered will be returned.

        The user entered text will not be echoed to the screen.

        :return: entered password
        :rtype:  str
        """
        while True:

            try:
                password_1 = self._get_password(question)
            except KeyboardInterrupt:
                if interruptable:
                    return ABORT
                raise

            if verify_question is None:
                return password_1

            try:
                password_2 = self._get_password(verify_question)
            except KeyboardInterrupt:
                if interruptable:
                    return ABORT
                raise

            if password_1 != password_2:
                self.write(unmatch_msg)
                self.write('')
            else:
                return password_1

    def _get_password(self, question):
        """
        Gets a password from the user interactively, supporting degraded
        behavior when called in python 2.4. The degraded behavior is explained
        in-line below.

        :param question: displayed to the user when prompting for input
        :type  question: str

        :return:    password that the user entered
        :rtype:     basestring
        """
        try:
            return getpass.getpass(question, stream=self.output)
        # In python 2.4, getpass.getpass does not have the "stream" parameter
        # and thus raises a TypeError for the above call. We will handle that
        # by simply not passing an argument for it, thus not allowing python
        # 2.4 users to take advantage of the self.output abstraction.
        except TypeError:
            return getpass.getpass(question)

    def prompt(self, question, allow_empty=False, interruptable=True):
        """
        Prompts the user for an answer to the given question, re-prompting if the answer is
        blank.

        :param question: displayed to the user when prompting for input
        :type  question: str

        :param allow_empty: if True, a blank line will be accepted as input
        :type  allow_empty: bool

        :param interruptable: if True, keyboard interrupts will be caught and None will
                              be returned; if False, keyboard interrupts will raise as
                              normal
        :type  interruptable: bool

        :return: answer to the given question or the ABORT constant in this
                 module if it was interrupted
        """
        answer = None
        while answer is None or answer.strip() == '':
            answer = self.read(question, interruptable=interruptable)
            if allow_empty: break
            if answer is ABORT: break

        return answer

    # -- utility --------------------------------------------------------------

    def get_tags(self):
        """
        Returns all tags for both read and write calls. Unlike read_tags and
        write_tags, the return value is a list of tuples. The first entry in
        the tuple will be one of [TAG_READ, TAG_WRITE] to indicate what
        triggered the tag. The second value in the tuple is the tag itself.

        :return: list of tag tuples: (tag_type, tag_value); empty list if
                 record_tags was set to false
        :rtype:  list
        """
        return self.tags

    def get_read_tags(self):
        """
        Returns the values for all tags that were passed to read calls.
        If record_tags is enabled on this instance and a tag was not
        specified, an empty string will be added in its place.

        :return: list of tag values; empty list if record_tags was set to false
        :rtype:  list
        """
        r = [t[1] for t in self.tags if t[0] == TAG_READ]
        return r

    def get_write_tags(self):
        """
        Returns the values for all tags that were passed to write calls.
        If record_tags is enabled on this instance and a tag was not
        specified, an empty string will be added in its place.

        :return: list of tag values; empty list if record_tags was set to false
        :rtype:  list
        """
        w = [t[1] for t in self.tags if t[0] == TAG_WRITE]
        return w

    # -- private --------------------------------------------------------------

    def _is_range(self, input, selectable_item_count):
        """
        :return: True if the input represents a range in a multiselect menu,
                 False otherwise
        :rtype:  bool
        """
        parsed = input.split('-')
        if len(parsed) != 2:
            return False

        lower = parsed[0].strip()
        upper = parsed[1].strip()

        return lower.isdigit() and int(lower) > 0 and \
            upper.isdigit() and int(upper) <= selectable_item_count and \
            int(lower) < int(upper)

    def _range(self, input):
        """
        If an input is determined to be a range by _is_range, this call will
        return the lower and upper indices of the range (the entered values
        will be subtracted by 1 to accomodate for UI view).

        :return: tuple of (lower boundary, upper boundary)
        :rtype: (int, int)
        """
        parsed = input.split('-')
        return int(parsed[0].strip()) - 1, int(parsed[1].strip()) - 1

    def _record_tag(self, io, tag):
        """
        Stores the given tag in the prompt if it is configued to track them.
        If tag is None, nothing is recorded.

        :param io: flag indicating if it's recording a read or a write;
               should be one of the TAG_* constants
        :type  io: str

        :param tag: value passed into the write call
        :type  tag: object
        """
        if not self.record_tags or tag is None:
            return

        # Store in a tuple with the io direction
        t = (io, tag or '')

        self.tags.append(t)

class Recorder(object):
    """
    Suitable for passing to the Prompt constructor as the output, an instance
    of this class will store every line written to it in an internal list.
    """

    def __init__(self):
        self.lines = []

    def write(self, line):
        self.lines.append(line)

class Script(object):
    """
    Suitable for passing to the Prompt constructor as the input, an instance
    of this class will return each line set within on each call to read.
    """

    # If this is present in the list of lines, a KeyboardInterrupt will be raised
    INTERRUPT = object()

    def __init__(self, lines):
        self.lines = lines

    def readline(self, size=None):
        value = self.lines.pop(0)

        if value is Script.INTERRUPT:
            raise KeyboardInterrupt()

        return value
