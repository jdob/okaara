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

from okaara import parsers


class ParseCSVTests(unittest.TestCase):

    def test_basic_values(self):
        ret = parsers.parse_csv_string('a,b,c')
        self.assertEqual(ret, ['a', 'b', 'c'])

    def test_single_value(self):
        ret = parsers.parse_csv_string('a')
        self.assertEqual(ret, ['a'])

    def test_required(self):
        self.assertRaises(ValueError, parsers.parse_csv_string, None)

    def test_optional(self):
        ret = parsers.parse_optional_csv_string(None)
        self.assertEqual(ret, None)

    def test_optional_empty_string(self):
        ret = parsers.parse_optional_csv_string('')
        self.assertEqual(ret, None)

    def test_optional_value(self):
        ret = parsers.parse_optional_csv_string('a,b')
        self.assertEqual(ret, ['a', 'b'])


class ParseIntTests(unittest.TestCase):

    def test_valid(self):
        ret = parsers.parse_int('10')
        self.assertEqual(ret, 10)

    def test_invalid(self):
        self.assertRaises(ValueError, parsers.parse_int, 'int')


class ParsePostiveIntTests(unittest.TestCase):

    def test_valid(self):
        ret = parsers.parse_positive_int('31415')
        self.assertEqual(ret, 31415)

    def test_string(self):
        self.assertRaises(ValueError, parsers.parse_positive_int, 'foo')

    def test_zero(self):
        self.assertRaises(ValueError, parsers.parse_positive_int, '0')

    def test_negative(self):
        self.assertRaises(ValueError, parsers.parse_positive_int, '-314')

    def test_optional(self):
        ret = parsers.parse_optional_positive_int(None)
        self.assertEqual(ret, None)

    def test_optional_empty_string(self):
        ret = parsers.parse_optional_positive_int('')
        self.assertEqual(ret, None)

    def test_optional_valid(self):
        ret = parsers.parse_optional_positive_int('12345')
        self.assertEqual(ret, 12345)

    def test_optional_invalid(self):
        self.assertRaises(ValueError, parsers.parse_positive_int, 'foo')


class ParseNonNegativeIntTests(unittest.TestCase):

    def test_valid(self):
        ret = parsers.parse_non_negative_int('31415')
        self.assertEqual(ret, 31415)

    def test_string(self):
        self.assertRaises(ValueError, parsers.parse_non_negative_int, 'foo')

    def test_zero(self):
        ret = parsers.parse_non_negative_int('0')
        self.assertEqual(ret, 0)

    def test_negative(self):
        self.assertRaises(ValueError, parsers.parse_non_negative_int, '-314')

    def test_optional(self):
        ret = parsers.parse_optional_non_negative_int(None)
        self.assertEqual(ret, None)

    def test_optional_empty_string(self):
        ret = parsers.parse_optional_non_negative_int('')
        self.assertEqual(ret, None)

    def test_optional_valid(self):
        ret = parsers.parse_optional_non_negative_int('0')
        self.assertEqual(ret, 0)

    def test_optional_invalid(self):
        self.assertRaises(ValueError, parsers.parse_optional_non_negative_int, 'foo')


class ParseBooleanTests(unittest.TestCase):

    def test_valid_true(self):
        ret = parsers.parse_boolean('true')
        self.assertEqual(ret, True)

    def test_valid_false(self):
        ret = parsers.parse_boolean('false')
        self.assertEqual(ret, False)

    def test_invalid(self):
        self.assertRaises(ValueError, parsers.parse_boolean, 'foo')

    def test_required(self):
        self.assertRaises(ValueError, parsers.parse_boolean, None)

    def test_optional(self):
        ret = parsers.parse_optional_boolean(None)
        self.assertEqual(ret, None)

    def test_optional_empty_string(self):
        ret = parsers.parse_optional_boolean('')
        self.assertEqual(ret, None)

    def test_optional_valid(self):
        ret = parsers.parse_optional_boolean('true')
        self.assertEqual(ret, True)

    def test_optional_invalid(self):
        self.assertRaises(ValueError, parsers.parse_optional_boolean, 'foo')
