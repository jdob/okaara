# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

# -- constants ----------------------------------------------------------------

# Causes values in a column to be truncated if they exceed the col width
WRAP_POLICY_TRUNCATE = object()

# Causes values in a column to wrap to a second line if they exceed the col width
WRAP_POLICY_WRAP = object()

# Internal utility
_ALL_WRAP_POLICIES = (WRAP_POLICY_TRUNCATE, WRAP_POLICY_WRAP)

# -- classes ------------------------------------------------------------------

class InvalidBag(Exception): pass

class TableBag(object):
    def __init__(self, num_cols,
                 col_widths=None,
                 col_separator=' ',
                 table_max_width=None,
                 wrap_policy=WRAP_POLICY_TRUNCATE,
                 header_divider_tick='=', ):

        self.num_cols = num_cols

        self.col_widths = col_widths
        self.col_separator = col_separator
        self.wrap_policy = wrap_policy
        self.table_max_width = table_max_width

        self.header_divider_tick = header_divider_tick

        self.validate()

    def __setattr__(self, name, value):
        # Only start running validate on attribute changes, not the first addition.
        # The constructor will manually call validate after all of the initial
        # values are set.
        run_validate = hasattr(self, name)

        super(TableBag, self).__setattr__(name, value)

        if run_validate:
            self.validate()

    def validate(self):

        if self.num_cols < 1:
            raise InvalidBag('Number of columns must be greater than 0')

        if self.wrap_policy not in _ALL_WRAP_POLICIES:
            raise InvalidBag('Wrap policy must be one of the module constants')

        if self.col_widths is not None:
            max_column_width = reduce(lambda x, y: x + y, self.col_widths)
            if max_column_width > self.table_max_width:
                raise InvalidBag('Sum of maximum column widths must be less than or equal to the table width')

class Table(object):
    """
    :type prompt: Prompt

    :type table_bag: TableBag
    """

    def __init__(self, prompt, table_bag):
        super(Table, self).__init__()

        self.prompt = prompt
        self.table_bag = table_bag


    def render(self, data, headers=None):

        # Calculations
        table_width, col_widths = self.calculate_widths()

        # Render the header information if specified
        if headers is not None:
            self.render_line(col_widths, headers)
            header_divider = self.table_bag.header_divider_tick * table_width
            self.prompt.write(header_divider)

        # Render each line
        for line in data:
            self.render_line(col_widths, line)

    # -- render pieces --------------------------------------------------------

    def render_line(self, col_widths, line):

        # In the event of a wrap policy, this will track the text per column
        # to be wrapped
        overflow_lines = [[] for i in range(0, len(col_widths))]

        for i in range(0, len(col_widths)):
            width = col_widths[i]
            text = line[i]

            if self.table_bag.wrap_policy is WRAP_POLICY_TRUNCATE:
                text = text[0:width]
            elif self.table_bag.wrap_policy is WRAP_POLICY_WRAP:
                wrapped = self.prompt.wrap(text, wrap_width=width)

                split_lines = wrapped.split('\n')
                text = split_lines[0]
                overflow_lines[i] = split_lines[1:]

            # Pad the right side of the text with enough spaces to line up
            # the next column correctly
            text += ' ' * (width - len(text))

            # Tack on the column separator if not the last column
            if i < (len(col_widths) - 1):
                text += self.table_bag.col_separator

            # Time to finally write the column to the screen
            self.prompt.write(text, new_line=False, skip_wrap=True)

        # Finished with the first pass at the row, so add a newline
        self.prompt.write('', new_line=True)

        # Handle any overflow
        while len([o for o in overflow_lines if len(o) > 0]) > 0:

            # Loop over each overflow list and if present, write the first
            # item in the list
            for i, col_overflow_list in enumerate(overflow_lines):

                # No overflow for the column, write spaces
                if len(col_overflow_list) is 0:
                    text = ' ' * col_widths[i]

                else:
                    text = col_overflow_list.pop(0)
                    text += ' ' * (col_widths[i] - len(text))

                # Add in the column separator
                if i < (len(col_widths) - 1):
                    text += self.table_bag.col_separator

                self.prompt.write(text, new_line=False, skip_wrap=True)

            # End the line
            self.prompt.write('', new_line=True)

    # -- calculations ---------------------------------------------------------

    def calculate_widths(self):
        """
        Calculates the table width and width of each column.
        """

        # First step is an expected table width
        table_width = self.table_bag.table_max_width or self.prompt.terminal_size()[0]

        # Calculate the column widths if not specified
        col_widths = self.table_bag.col_widths

        # If not specified, evenly divide across the table width and throw
        # out any extra space
        if col_widths is None:
            each_col_width = table_width / (self.table_bag.num_cols + len(self.table_bag.col_separator))
            col_widths = [each_col_width for i in range(0, self.table_bag.num_cols)]

        # If the table width is greater than the total width of the columns,
        # reduce the table width so it looks nicer
        total_col_width = reduce(lambda x, y: x + y, col_widths)

        # Add in the width of the separators
        total_col_width += len(self.table_bag.col_separator) * (len(col_widths) - 1)
        table_width = min(table_width, total_col_width)

        return table_width, col_widths

if __name__ == '__main__':

    from okaara.prompt import Prompt
    prompt = Prompt()

    bag = TableBag(4, table_max_width=60, wrap_policy=WRAP_POLICY_WRAP, col_separator=' | ')
    table = Table(prompt, bag)

    data = [
        ['aaaaa', 'bbbbb', 'ccccc', 'ddddd'],
        ['eeeeeeee', 'ffff', 'gggggggg', 'hhhhhhhhhhhhhhh'],
    ]

    headers = ['Column 1', 'Column 2', 'Really Long Column 3','Column 4']

    table.render(data, headers=headers)