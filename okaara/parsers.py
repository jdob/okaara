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

"""
Contains methods suitable for passing to the parse_func parameter of the Option.

The parse_optional_* parsers treat both None and the empty string to indicate an omitted value.
This allows an option to be specified as --count= or --count="" in order to convey the idea of
null as the value of the command. Okaara will parse both of those as having a value of '' which
the parse_optional_* methods will translate to None upon parsing.
"""

import csv as csv_module
from gettext import gettext as _


# When parsing a boolean, the value is converted to lower case and checked to see
# if it exists in one of these lists. More/different values to represent true and false
# can be supported by manipulating these variables.
VALID_TRUE_STRINGS = ['true']
VALID_FALSE_STRINGS = ['false']


def parse_boolean(value):
    """
    Returns the boolean representation of the given user input, raising the
    appropriate exception if the user input cannot be parsed.

    :param value: user entered text extracted by the framework
    :type  value: str
    :rtype: bool
    """

    if value is None:
        raise ValueError(_('value is required'))
    if value.strip().lower() in VALID_TRUE_STRINGS:
        return True
    if value.strip().lower() in VALID_FALSE_STRINGS:
        return False
    else:
        raise ValueError(_('invalid boolean value'))


def parse_int(value):
    """
    Returns the int representation of the given user input, raising the appropriate
    exception if the user input cannot be parsed.

    :param value: user entered text extracted by the framework
    :type  value: str
    :rtype: int
    """
    return int(value)


def parse_optional_boolean(value):
    """
    Returns the boolean representation of the given user input. This call does not raise an
    exception in the event the specified value is None.

    :param value: user entered text extracted by the framework
    :type  value: str, None
    :rtype: bool
    """
    if value is None or value.strip() == '':
        return None

    return parse_boolean(value)


def parse_non_negative_int(value):
    """
    Returns an int representation of the user entered value, raising an
    exception if it is negative.

    :param value: user entered value
    :type  value: str
    :rtype: int
    """

    i = int(value)
    if i < 0:
        raise ValueError(_('value must be a non-negative integer'))
    return i


def parse_optional_non_negative_int(value):
    """
    Returns an int representation of the user entered value. This call does not raise an
    exception in the event the specified value is None.

    :param value: user entered value
    :type  value: str, None
    :rtype: int
    """

    if value is None or value.strip() == '':
        return None

    return parse_non_negative_int(value)


def parse_positive_int(value):
    """
    Returns an int representation of the user entered value, raising an
    exception if it is not a positive number.

    :param value: user entered value
    :type  value: str
    :rtype: int
    """

    i = int(value)
    if i < 1:
        raise ValueError(_('value must be a positive integer'))
    return i


def parse_optional_positive_int(value):
    """
    Returns an int representation of the user entered value. This call does not raise an
    exception in the event the specified value is None.

    :param value: user entered value
    :type  value: str, None
    :rtype: int
    """
    if value is None or value.strip() == '':
        return None

    return parse_positive_int(value)


def parse_csv_string(value):
    """
    Parses a comma-separated string of values into a list of separate items.

    :param value: user entered value
    :type  value: str
    :rtype: list
    """
    if value is None:
        raise ValueError(_('value is required'))

    return next(csv_module.reader((value,)))


def parse_optional_csv_string(value):
    """
    Parses a comma-separated string of values into a list of separate items. This call does not
    raise an exception in the event the specified value is None.

    :param value: user entered value
    :type  value: str, None
    :rtype: list
    """
    if value is None or value.strip() == '':
        return None

    return parse_csv_string(value)
