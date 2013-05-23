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

from okaara import prompt, cli


class FindClosestMatchTests(unittest.TestCase):

    def setUp(self):
        super(FindClosestMatchTests, self).setUp()

        def noop():
            pass

        self.prompt = prompt.Prompt()
        self.cli = cli.Cli(prompt=self.prompt)

        # Populate a CLI structure to test against
        self.marvel = self.cli.create_subsection('marvel', 'Marvel characters')

        self.avengers = self.marvel.create_subsection('avengers', 'Avengers members')
        self.leaders = self.avengers.create_command('leaders', 'Nick Fury', noop)

        self.movie = self.avengers.create_subsection('movie', 'Movie cast of Avengers')
        self.thor = self.movie.create_command('thor', 'God of Thunder', noop)
        self.hulk = self.movie.create_command('hulk', 'Bruce Banner', noop)

        self.new = self.avengers.create_subsection('new', 'Members of the New Avengers')
        self.spiderman = self.new.create_command('spiderman', 'Peter Parker', noop)
        self.cage = self.new.create_command('cage', 'Luke Cage', noop)

        self.xmen = self.marvel.create_subsection('xmen', 'X-Men members')
        self.wolverine = self.xmen.create_command('wolverine', 'Logan', noop)

        self.dc_section = self.cli.create_subsection('dc', 'DC characters')

        self.jla = self.dc_section.create_subsection('jla', 'Justice League')
        self.batman = self.jla.create_command('batman', 'Bruce Wayne', noop)
        self.superman = self.jla.create_command('superman', 'Clark Kent', noop)

        self.lanterns = self.dc_section.create_subsection('lanterns', 'Green Lantern Corps')
        self.hal = self.lanterns.create_command('hal', 'Hal Jordan', noop)
        self.kyle = self.lanterns.create_command('kyle', 'Kyle Rayner', noop)

    def test_successful_find_command(self):
        # Test
        args = 'marvel avengers movie hulk arg1 arg2'.split()
        found, remaining = self.cli._find_closest_match(self.cli.root_section, args)

        # Verify
        self.assertEqual(found, self.hulk)
        self.assertEqual(['arg1', 'arg2'], remaining)

    def test_found_section_not_command(self):
        # Test
        args = 'marvel avengers movie msmarvel'.split()
        found, remaining = self.cli._find_closest_match(self.cli.root_section, args)

        # Verify
        self.assertEqual(found, self.movie)
        self.assertEqual(['msmarvel'], remaining)

    def test_good_section_bad_section_good_section(self):
        # Test
        args = 'marvel avengers books thor'.split()
        found, remaining = self.cli._find_closest_match(self.cli.root_section, args)

        # Verify
        self.assertEqual(found, self.avengers)
        self.assertEqual(['books', 'thor'], remaining)

    def test_no_match_at_all(self):
        # Test
        args = 'image invincible mark'.split()
        found, remaining = self.cli._find_closest_match(self.cli.root_section, args)

        # Verify
        self.assertEqual(found, self.cli.root_section)
        self.assertEqual(args, remaining)
