#!/usr/bin/python
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


import unittest

from okaara.prompt import Prompt, ScriptedPrompt, ABORT


# -- mocks --------------------------------------------------------------------

class InterruptingPrompt(Prompt):

    def read(self, prompt):
        raise KeyboardInterrupt()


# -- test cases ---------------------------------------------------------------

class PromptTest(unittest.TestCase):

    def test_prompt_no_empty(self):
        """
        Tests that a prompt that does not allow empty values re-prompts the user
        and does nto error.
        """

        # Setup
        prompt = ScriptedPrompt()
        prompt.read_values.append('')
        prompt.read_values.append('value')

        # Test
        entered = prompt.prompt('Question')

        # Verify
        self.assertEqual(0, len(prompt.read_values))
        self.assertEqual('value', entered)

    def test_prompt_allow_empty(self):
        """
        Tests that a prompt will accept empty and not error.
        """

        # Setup
        prompt = ScriptedPrompt()
        prompt.read_values.append('')
        prompt.read_values.append('not used')

        # Test
        entered = prompt.prompt("Question", allow_empty=True)

        # Verify
        self.assertEqual(1, len(prompt.read_values))
        self.assertEqual('', entered)

    def test_prompt_interruptable(self):
        """
        Tests that interrupting the prompt when allowed does not throw an exception.
        """

        # Setup
        prompt = InterruptingPrompt()

        # Test
        entered = prompt.prompt('Question', interruptable=True)

        # Verify
        self.assertEqual(ABORT, entered)

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
        prompt = ScriptedPrompt()
        prompt.read_values.append('1')
        prompt.read_values.append('2')

        items = ['a', 'b', 'c']

        # Test
        index = prompt.prompt_menu('Question', items)

        # Verify
        self.assertEqual(0, index)
        self.assertEqual(1, len(prompt.read_values))
        