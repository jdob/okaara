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

import unittest

from okaara import prompt, table

class TableTests(unittest.TestCase):

    def setUp(self):
        super(TableTests, self).setUp()

        self.prompt = prompt.Prompt()

    def test_equal_table_and_cols_no_separator(self):
        # Setup
        col_widths = [10, 10, 10]
        max_size = sum(col_widths)
        t = table.Table(self.prompt, len(col_widths),
                        col_widths=col_widths, table_width=max_size,
                        col_separator='')

        # Verify
        self.assertEqual(t.col_widths, col_widths)
        self.assertEqual(t.table_width, max_size)

    def test_equal_table_and_cols_with_separator(self):
        # Setup
        col_widths = [8, 8, 10]
        separator = ' |'
        max_size = sum(col_widths) + ((len(col_widths) - 1) * len(separator))
        t = table.Table(self.prompt, len(col_widths),
                        col_widths=col_widths, table_width=max_size,
                        col_separator=separator)

        # Verify
        self.assertEqual(t.col_widths, col_widths)
        self.assertEqual(t.table_width, max_size)

    def test_larger_col_widths(self):
        # Setup
        col_widths = [10, 10, 10]
        max_size = 5

        try:
            t = table.Table(self.prompt, len(col_widths), col_widths=col_widths, table_width=max_size)
            tw, cw = t.calculate_widths()
            t.validate(tw, cw)
            self.fail()
        except table.InvalidTableSettings:
            pass

    def test_larger_table_width(self):
        # Setup
        col_widths = [10, 10]
        max_size = 40
        t = table.Table(self.prompt, len(col_widths),
                        col_widths=col_widths, table_width=max_size,
                        col_separator='')
        tw, cw = t.calculate_widths()

        # Verify
        self.assertEqual(cw, col_widths)
        self.assertEqual(tw, sum(t.col_widths))

    def test_table_width_no_col_widths(self):
        # Setup
        num_cols = 4
        max_size = 60
        separator = ' '
        t = table.Table(self.prompt, num_cols,
                        table_width=max_size, col_separator=separator)

        tw, cw = t.calculate_widths()

        # Verify
        expected_col_widths = [14, 14, 14, 14]
        self.assertEqual(expected_col_widths, cw)

        expected_table_width = sum(expected_col_widths) + ((len(expected_col_widths) - 1) * len(separator))
        self.assertEqual(expected_table_width, tw)
