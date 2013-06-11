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
Contains methods suitable for passing to the validate_func parameter of the Option.
"""

from gettext import gettext as _

from okaara import parsers


def validate_boolean(value):
    """
    Ensures a valid boolean value was specified, raising the appropriate exception if
    it is not.

    :param value: user entered text extracted by the framework
    :type  value: str
    """
    parsers.parse_boolean(value) # will raise an exception if not valid


def validate_int(value):
    """
    Ensures a valid integer value was specified, raising the appropriate exception if
    it is not.

    :param value: user entered text extracted by the framework
    :type  value: str
    """
    parsers.parse_int(value) # will raise an exception if not valid


def partial_validate_regex(regex, value):
    """
    Applies the given regular expression as the validation for the given user input.
    The intention is to use this method as part of a partial and pass the result to
    the validate_func property of an Option.

    :param regex: compiled regular expression to use to validate against
    :type  regex: SRE_Pattern
    :param value: user entered text extracted by the framework
    :type  value: str
    """
    if regex.match(value) is None:
        msg = _('%(input)s does not match %(regex)s')
        raise ValueError(msg % {'input' : value, 'regex' : regex.pattern})
