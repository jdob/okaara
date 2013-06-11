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

import re
import unittest

from okaara import validators


class ValidateBooleanTests(unittest.TestCase):

    def test_valid(self):
        validators.validate_boolean('true')
        # no exception raised

    def test_invalid(self):
        self.assertRaises(ValueError, validators.validate_boolean, 't')


class ValidateIntTests(unittest.TestCase):

    def test_valid(self):
        validators.validate_int('123')
        # no exception raised

    def test_invalid(self):
        self.assertRaises(ValueError, validators.validate_int, 'xyz')


class PartialValidateRegexTests(unittest.TestCase):

    def test_valid(self):
        regex = re.compile(r'[A-Za-z]+')
        validators.partial_validate_regex(regex, 'okaara')

    def test_invalid(self):
        regex = re.compile(r'[A-Za-z]+')
        self.assertRaises(ValueError, validators.partial_validate_regex, regex, '123')
