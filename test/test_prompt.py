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

import mock

import okaara.prompt
from okaara.prompt import Prompt, Recorder, Script, ABORT


# -- mocks --------------------------------------------------------------------

class InterruptingPrompt(Prompt):

    def read(self, prompt, tag=None, interruptable=True):
        raise KeyboardInterrupt()

# -- test cases ---------------------------------------------------------------

class GeneralTests(unittest.TestCase):

    def test_read_interrupt(self):
        """
        Tests that having read catch interrupt correctly returns the abort code.
        """

        # Setup
        script = Script([Script.INTERRUPT])
        prompt = Prompt(input=script)

        # Test
        r = prompt.read('Thor', interruptable=True)

        # Verify
        self.assertEqual(ABORT, r)

    def test_color(self):
        """
        Tests the color call correctly wraps the text with the correct markers.
        """

        # Test
        prompt = Prompt()
        colored = prompt.color('Hulk', okaara.prompt.COLOR_GREEN)

        # Verify
        expected = okaara.prompt.COLOR_GREEN + 'Hulk' + okaara.prompt.COLOR_WHITE
        self.assertEqual(colored, expected)

    def test_write_color(self):
        """
        Tests the color functionality built into write works.
        """

        # Setup
        recorder = Recorder()
        prompt = Prompt(output=recorder)

        # Test
        prompt.write('Hulk', color=okaara.prompt.COLOR_RED, new_line=False)

        # Verify
        expected = okaara.prompt.COLOR_RED + 'Hulk' + okaara.prompt.COLOR_WHITE
        self.assertEqual(recorder.lines[1], expected)

    def test_write_with_wrap(self):
        """
        Tests using an auto-wrap value correctly wraps text.
        """

        # Setup
        recorder = Recorder()
        prompt = Prompt(output=recorder, wrap_width=10)

        # Test
        prompt.write('-' * 20)

        # Verify
        written_lines = recorder.lines[1].split('\n')
        self.assertEqual(3, len(written_lines))
        self.assertEqual('-' * 10, written_lines[0])
        self.assertEqual('-' * 10, written_lines[1])
        self.assertEqual('', written_lines[2])


class WrapTests(unittest.TestCase):

    def test_wrap_short_wrap(self):
        """
        Tests that chop correctly handled data longer than the chop length.
        """

        # Setup
        prompt = Prompt()

        # Test
        wrapped = prompt.wrap('Spiderman', 3)

        # Verify
        pieces = wrapped.split('\n')

        self.assertEqual(3, len(pieces))

    def test_wrap_long_wrap(self):
        """
        Tests that chop correctly handles data shorter than the chop length.
        """

        # Setup
        prompt = Prompt()

        # Test
        wrapped = prompt.wrap('Green Goblin', 100)

        # Verify
        pieces = wrapped.split('\n')

        self.assertEqual(1, len(pieces))

    def test_wrap_with_none(self):
        """
        Tests that chop with a None wrap width doesn't crash.
        """

        # Setup
        prompt = Prompt()

        # Test
        wrapped = prompt.wrap('Electro', None)

        # Verify
        pieces = wrapped.split('\n')

        self.assertEqual(1, len(pieces))

    def test_wrap_smart_split(self):
        """
        Tests smart wrapping to not break words.
        """

        # Setup
        text = 'abc def ghikl mno pqrs'
        prompt = Prompt()

        # Test
        wrapped = prompt.wrap(text, 5)

        # Verify
        expected = 'abc\ndef\nghikl\nmno\npqrs'
        self.assertEqual(expected, wrapped)


class PromptTest(unittest.TestCase):
    @mock.patch('getpass.getpass')
    def test_prompt_password(self, mock_getpass):
        """
        Make sure this correctly passes through to getpass one way or another
        """
        # Setup
        mock_getpass.return_value = 'letmein'
        prompt = Prompt()

        password = prompt.prompt_password('Password: ')

        self.assertEqual(password, 'letmein')
        self.assertEqual(mock_getpass.call_count, 1)
        self.assertEqual(mock_getpass.call_args[0][0], 'Password: ')

    def test_prompt_no_empty(self):
        """
        Tests that a prompt that does not allow empty values re-prompts the user
        and does nto error.
        """

        # Setup
        lines = ['', 'value']
        script = Script(lines)
        prompt = Prompt(input=script)

        # Test
        entered = prompt.prompt('Question')

        # Verify
        self.assertEqual(0, len(script.lines))
        self.assertEqual('value', entered)

    def test_prompt_allow_empty(self):
        """
        Tests that a prompt will accept empty and not error.
        """

        # Setup
        lines = ['', 'not used']
        script = Script(lines)
        prompt = Prompt(input=script)

        # Test
        entered = prompt.prompt('Question', allow_empty=True)

        # Verify
        self.assertEqual(1, len(script.lines))
        self.assertEqual('', entered)

    def test_prompt_non_interruptable(self):
        """
        Tests that a non-interruptable prompt properly raises an exception if interrupted.
        """

        # Setup
        prompt = InterruptingPrompt()

        # Test
        self.assertRaises(KeyboardInterrupt, prompt.prompt, 'Question')

    def test_prompt_menu(self):
        """
        Basic tests for prompting a menu of items and selecting a valid one.
        """

        # Setup
        lines = ['1', '2']
        script = Script(lines)
        prompt = Prompt(input=script)

        items = ['a', 'b', 'c']

        # Test
        index = prompt.prompt_menu('Question', items)

        # Verify
        self.assertEqual(0, index)
        self.assertEqual(1, len(script.lines))


def fake_py24_getpass(question):
    """
    Force the mocked getpass.getpass to behave as it would for python 2.4, in
    which case "question" is the only parameter allowed.
    """
    assert question == 'Password: '
    return 'letmein'


def fake_py26_getpass(question, stream=None):
    """
    Force the mocked getpass.getpass to behave as it would for python 2.6+, in
    which case the "stream" parameter is available for use.
    """
    assert question == 'Password: '
    assert stream is not None
    return 'letmein'


class TestGetPassword(unittest.TestCase):
    @mock.patch('getpass.getpass')
    def test_get_password(self, mock_getpass):
        # Setup
        mock_getpass.return_value = 'letmein'
        prompt = Prompt()

        password = prompt._get_password('Password: ')

        self.assertEqual(password, 'letmein')
        mock_getpass.assert_called_once_with('Password: ', stream=prompt.output)

    @mock.patch('getpass.getpass', new=fake_py24_getpass)
    def test_py24_behavior(self):
        prompt = Prompt()

        password = prompt._get_password('Password: ')

        self.assertEqual(password, 'letmein')
        
    @mock.patch('getpass.getpass', new=fake_py26_getpass)
    def test_py26_behavior(self):
        prompt = Prompt()

        password = prompt._get_password('Password: ')

        self.assertEqual(password, 'letmein')

