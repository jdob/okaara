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
from builtins import range
from builtins import object

from functools import reduce
import copy

# -- constants ----------------------------------------------------------------

# Causes values in a column to be truncated if they exceed the col width
WRAP_POLICY_TRUNCATE = 'wrap-truncate'

# Causes values in a column to wrap to a second line if they exceed the col width
WRAP_POLICY_WRAP = 'wrap-wrap'

# Internal utility
_ALL_WRAP_POLICIES = (WRAP_POLICY_TRUNCATE, WRAP_POLICY_WRAP)

# Column alignment constants
ALIGN_LEFT = 'align-left'
ALIGN_RIGHT = 'align-right'
ALIGN_CENTER = 'align-center'

_ALL_ALIGNMENTS = (ALIGN_LEFT, ALIGN_RIGHT, ALIGN_CENTER)

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
                 col_alignments=None,
                 header_col_alignments=None,
                 col_separator=' ',
                 table_width=None,
                 wrap_policy=WRAP_POLICY_TRUNCATE,
                 header_divider_tick='=',
                 header_color=None,
                 row_colors=None,
                 color_separators=True):
        super(Table, self).__init__()

        self.prompt = prompt

        self.num_cols = num_cols

        # Width Calculations
        self.table_width = table_width
        self.col_widths = col_widths
        self.wrap_policy = wrap_policy

        # Look & Feel
        self.col_separator = col_separator
        self.col_alignments = col_alignments
        self.header_col_alignments = header_col_alignments
        self.header_divider_tick = header_divider_tick
        self.header_color = header_color
        self.row_colors = row_colors
        self.color_separators = color_separators

    def __str__(self):
        return 'table_max_width [%s] col_widths [%s]' % (self.table_width, self.col_widths)

    def validate(self, table_width, col_widths):

        if self.num_cols < 1:
            raise InvalidTableSettings('Number of columns must be greater than 0')

        if self.wrap_policy not in _ALL_WRAP_POLICIES:
            raise InvalidTableSettings('Wrap policy must be one of the module constants')

        if self.col_alignments is not None:
            illegal_alignments = [a for a in self.col_alignments if a not in _ALL_ALIGNMENTS]
            if len(illegal_alignments) > 0:
                raise InvalidTableSettings('Column alignment values must be one of the module constants')

            if len(self.col_alignments) != self.num_cols:
                raise InvalidTableSettings('One column alignment must be specified for each column')

        if self.header_col_alignments is not None:
            illegal_alignments = [a for a in self.header_col_alignments if a not in _ALL_ALIGNMENTS]
            if len(illegal_alignments) > 0:
                raise InvalidTableSettings('Header column alignment values must be one of the module constants')

            if len(self.header_col_alignments) != self.num_cols:
                raise InvalidTableSettings('One header column alignment must be specified for each column')

        max_column_width = reduce(lambda x, y: x + y, col_widths)

        if max_column_width > table_width:
            raise InvalidTableSettings('Sum of maximum column widths must be less than or equal to the table width')

        if self.num_cols != len(col_widths):
            raise InvalidTableSettings('Number of columns [%s] must equal the number of column widths specified [%s]' % (self.num_cols, len(self.col_widths)))

    # -- public ---------------------------------------------------------------

    def render(self, data, headers=None):

        # Recalculate and revalidate
        table_width, col_widths = self.calculate_widths()
        self.validate(table_width, col_widths)

        # Render the header information if specified
        if headers is not None:
            self.render_headers(headers, col_widths, self.header_color)
            self.render_header_divider(table_width)

        # Convert the data into table cells
        cells = self.parse_cells(data, col_widths)

        # Render each line
        for row_num, line in enumerate(cells):
            text_color = None

            # Alternate across each row color
            if self.row_colors is not None:
                text_color = self.row_colors[row_num % len(self.row_colors)]

            self.render_row(line, col_widths, text_color, self.col_alignments)
            self.render_row_divider(table_width, row_num)

    # -- render pieces --------------------------------------------------------

    def render_headers(self, headers, col_widths, text_color):
        header_cells = self.parse_cells([headers], col_widths)

        self.render_row(header_cells[0], col_widths, text_color, self.header_col_alignments)

    def render_header_divider(self, table_width):
        header_divider = self.header_divider_tick * table_width
        self.prompt.write(header_divider)

    def render_row(self, row_cells, col_widths, text_color, col_alignments):

        # Going to pop elements out of the cells, so copy them first
        row_cells = copy.deepcopy(row_cells)

        def has_more_content(cells):
            return len([c for c in cells if c.has_more_lines()]) > 0

        while has_more_content(row_cells):
            for i in range(0, len(row_cells)):
                cell = row_cells[i]
                width = col_widths[i]

                if not cell.has_more_lines():
                    text = ' ' * width
                else:
                    text = cell.pop_line()

                    # Align the column correctly
                    alignment = ALIGN_LEFT
                    if col_alignments is not None:
                        alignment = col_alignments[i]

                    padding = ' ' * (width - len(text))
                    if alignment == ALIGN_LEFT:
                        text += padding
                    elif alignment == ALIGN_RIGHT:
                        text = padding + text
                    else:
                        left_padding_count = (width - len(text)) // 2
                        right_padding_count = (width - len(text)) - left_padding_count

                        left_padding = ' ' * left_padding_count
                        right_padding = ' ' * right_padding_count

                        text = left_padding + text + right_padding

                    # Color the text if specified (before the separator is added)
                    if text_color is not None and not self.color_separators:
                        text = self.prompt.color(text, text_color)

                # Tack on the column separator if not the last column
                if i < (len(col_widths) - 1):
                    text += self.col_separator

                # If the separators should be colored, do them now
                if text_color is not None and self.color_separators:
                    text = self.prompt.color(text, text_color)

                # Time to finally write the column to the screen
                self.prompt.write(text, new_line=False, skip_wrap=True)

            # Finished with the first pass at the row, so add a newline
            self.prompt.write('', new_line=True)

    def render_row_divider(self, table_width, row_num):
        """
        Renders a divider after the given row.

        :param table_width: actual width the table will be
        :type  table_width: int

        :param row_num: indicates the last row that was rendered
        :type  row_num: int
        """
        pass

    # -- calculations ---------------------------------------------------------

    def calculate_widths(self):
        """
        Calculates the table width and width of each column.
        """

        # First step is an expected table width
        table_width = self.table_width or self.prompt.terminal_size()[0]

        col_widths = self.col_widths

        # If not specified, evenly divide across the table width and throw
        # out any extra space
        if col_widths is None:
            minus_separators = table_width - ((self.num_cols - 1) * len(self.col_separator))
            each_col_width = minus_separators // self.num_cols
            col_widths = [each_col_width for i in range(0, self.num_cols)]

        # If the table width is greater than the total width of the columns,
        # reduce the table width so it looks nicer
        total_col_width = reduce(lambda x, y: x + y, col_widths)

        # Add in the width of the separators
        total_col_width += len(self.col_separator) * (len(col_widths) - 1)
        table_width = min(table_width, total_col_width)

        return table_width, col_widths

    def parse_cells(self, data, col_widths):
        """
        For each of the given cells, breaks apart the contents into what
        should be in each cell of the table based on the table's configuration
        (column widths, column separator, etc.).

        @return:
        """

        cells = [[] for i in data] # initialize each row to a list
        for row_num, row in enumerate(data):

            for col_num in range(0, len(row)):
                cell = CellData()
                cells[row_num].append(cell) # each row is a list of cells

                col_width = col_widths[col_num]
                text = row[col_num]

                # Apply the wrap policy to transform the text

                if self.wrap_policy == WRAP_POLICY_TRUNCATE:
                    text = text[0:col_width]
                    cell.add_line(text)

                elif self.wrap_policy == WRAP_POLICY_WRAP:
                    wrapped = self.prompt.wrap(text, wrap_width=col_width)

                    split_lines = wrapped.split('\n')
                    for line in split_lines:
                        cell.add_line(line)

        return cells

class CellData(object):
    """
    Contains the contents of each cell after the wrap policy has been
    applied. The contents are stored as a list of strings; the list may be
    longer than 1 if the wrap policy dictates the cell be multi-line.
    """

    def __init__(self):
        super(CellData, self).__init__()

        self.lines = []

    def add_line(self, text):
        self.lines.append(text)

    def pop_line(self):
        return self.lines.pop(0)

    def has_more_lines(self):
        return len(self.lines) > 0
