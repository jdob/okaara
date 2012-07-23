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

class InvalidTableSettings(Exception): pass

class Table(object):
    """
    :param prompt:
    :type  prompt: Prompt
    """

    def __init__(self,
                 prompt,
                 num_cols,
                 col_widths=None,
                 col_separator=' ',
                 table_max_width=None,
                 wrap_policy=WRAP_POLICY_TRUNCATE,
                 header_divider_tick='=',
                 header_color=None,
                 row_colors=None,
                 color_separators=True):
        super(Table, self).__init__()

        self.prompt = prompt

        self.num_cols = num_cols

        # Width Calculations
        self.col_widths = col_widths
        self.wrap_policy = wrap_policy
        self.table_max_width = table_max_width

        # Look & Feel
        self.col_separator = col_separator
        self.header_divider_tick = header_divider_tick
        self.header_color = header_color
        self.row_colors = row_colors
        self.color_separators = color_separators

        # Calculated Values
        self.__dict__['table_width'], self.__dict__['col_widths'] = self.calculate_widths()

        # Make sure the values are sane
        self.validate()

    def __setattr__(self, name, value):
        # Only start running validate on attribute changes, not the first addition.
        # The constructor will manually call validate after all of the initial
        # values are set.
        is_change = hasattr(self, name)

        super(Table, self).__setattr__(name, value)

        if is_change:
            self.validate()
            self.__dict__['table_width'], self.__dict__['col_widths'] = self.calculate_widths()

    def validate(self):

        if self.num_cols < 1:
            raise InvalidTableSettings('Number of columns must be greater than 0')

        if self.wrap_policy not in _ALL_WRAP_POLICIES:
            raise InvalidTableSettings('Wrap policy must be one of the module constants')

        if self.col_widths is not None:
            max_column_width = reduce(lambda x, y: x + y, self.col_widths)
            if max_column_width > self.table_max_width:
                raise InvalidTableSettings('Sum of maximum column widths must be less than or equal to the table width')

    def render(self, data, headers=None):

        # Render the header information if specified
        if headers is not None:
            self.render_headers(headers, self.header_color)
            self.render_header_divider()

        # Render each line
        for i, line in enumerate(data):
            text_color = None

            # Alternate across each row color
            if self.row_colors is not None:
                text_color = self.row_colors[i % len(self.row_colors)]

            self.render_line(line, text_color)

    # -- render pieces --------------------------------------------------------

    def render_headers(self, headers, text_color):
        self.render_line(headers, text_color)

    def render_header_divider(self):
        header_divider = self.header_divider_tick * self.table_width
        self.prompt.write(header_divider)

    def render_line(self, line, text_color):

        # In the event of a wrap policy, this will track the text per column
        # to be wrapped
        overflow_lines = [[] for i in range(0, len(self.col_widths))]

        for i in range(0, len(self.col_widths)):
            width = self.col_widths[i]
            text = line[i]

            if self.wrap_policy is WRAP_POLICY_TRUNCATE:
                text = text[0:width]
            elif self.wrap_policy is WRAP_POLICY_WRAP:
                wrapped = self.prompt.wrap(text, wrap_width=width)

                split_lines = wrapped.split('\n')
                text = split_lines[0]
                overflow_lines[i] = split_lines[1:]

            # Pad the right side of the text with enough spaces to line up
            # the next column correctly
            text += ' ' * (width - len(text))

            # Color the text if specified (before the separator is added)
            if text_color is not None and not self.color_separators:
                text = self.prompt.color(text, text_color)

            # Tack on the column separator if not the last column
            if i < (len(self.col_widths) - 1):
                text += self.col_separator

            # If the separators should be colored, do them now
            if text_color is not None and self.color_separators:
                text = self.prompt.color(text, text_color)

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
                    text = ' ' * self.col_widths[i]

                else:
                    text = col_overflow_list.pop(0)
                    text += ' ' * (self.col_widths[i] - len(text))

                # Color the text if specified (before the separator is added)
                if text_color is not None and not self.color_separators:
                    text = self.prompt.color(text, text_color)

                # Add in the column separator
                if i < (len(self.col_widths) - 1):
                    text += self.col_separator

                # If the separators should be colored, do them now
                if text_color is not None and self.color_separators:
                    text = self.prompt.color(text, text_color)

                self.prompt.write(text, new_line=False, skip_wrap=True)

            # End the line
            self.prompt.write('', new_line=True)

    # -- calculations ---------------------------------------------------------

    def calculate_widths(self):
        """
        Calculates the table width and width of each column.
        """

        # First step is an expected table width
        table_width = self.table_max_width or self.prompt.terminal_size()[0]

        # Calculate the column widths if not specified
        col_widths = self.col_widths

        # If not specified, evenly divide across the table width and throw
        # out any extra space
        if col_widths is None:
            each_col_width = table_width / (self.num_cols + len(self.col_separator))
            col_widths = [each_col_width for i in range(0, self.num_cols)]

        # If the table width is greater than the total width of the columns,
        # reduce the table width so it looks nicer
        total_col_width = reduce(lambda x, y: x + y, col_widths)

        # Add in the width of the separators
        total_col_width += len(self.col_separator) * (len(col_widths) - 1)
        table_width = min(table_width, total_col_width)

        return table_width, col_widths

    
if __name__ == '__main__':

    import okaara.prompt
    p = okaara.prompt.Prompt()

    table = Table(p, 4, table_max_width=60, wrap_policy=WRAP_POLICY_WRAP, col_separator=' ')

    data = [
        ['aaaaa', 'bbbbb', 'ccccc', 'ddddd'],
        ['eeeeeeee', 'ffff', 'gggggggg', 'hhhhhhhhhhhhhhh'],
        ['iiii', 'jjjj', 'kk', 'lllllllllllll'],
        ['m', 'n', 'ooo', 'ppppppp'],
        ['qqqqqq', 'rrrr', 'sss', 't']
    ]

    headers = ['Column 1', 'Column 2', 'Really Long Column 3','Column 4']

    table.render(data, headers=headers)

    p.write('')
    p.write('')

    table.col_separator = ' | '
    table.table_max_width = 70

    table.render(data, headers=headers)

    p.write('')
    p.write('')

    table.header_color = okaara.prompt.COLOR_BG_BLUE
    table.row_colors = [okaara.prompt.COLOR_BG_CYAN + okaara.prompt.COLOR_BLUE, okaara.prompt.COLOR_LIGHT_PURPLE, okaara.prompt.COLOR_CYAN]
    table.color_separators = True

    table.render(data, headers=headers)

    p.write('')
    p.write('')

    table.color_separators = False

    table.render(data, headers=headers)