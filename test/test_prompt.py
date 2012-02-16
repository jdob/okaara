#!/usr/bin/python
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


import unittest

import okaara.prompt
from okaara.prompt import Prompt, Recorder, Script, ABORT


# -- mocks --------------------------------------------------------------------

class InterruptingPrompt(Prompt):

    def read(self, prompt, tag=None, interruptable=True):
        raise KeyboardInterrupt()

# -- test cases ---------------------------------------------------------------

class PromptTest(unittest.TestCase):

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

    def test_chop_short_wrap(self):
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

    def test_chop_long_wrap(self):
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

    def test_chop_with_none(self):
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