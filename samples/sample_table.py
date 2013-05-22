#!/usr/bin/python
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import okaara.prompt
from okaara.table import Table, WRAP_POLICY_WRAP, ALIGN_RIGHT, ALIGN_LEFT, ALIGN_CENTER

# -----------------------------------------------------------------------------

TEST_DATA = [
    ['1', 'Entry 1', 'Lorem ipsum dolor sit amet,'],
    ['2', 'Entry 2', 'consectetur adipisicing'],
    ['3', 'Entry 3', 'elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'],
    ['4', 'Entry 4', 'Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.'],
    ['5', 'Entry 5', 'Duis aute irure dolor'],
]
TEST_HEADERS = ['ID', 'Title', 'Description']

NUM_COLS = len(TEST_HEADERS)

PROMPT = okaara.prompt.Prompt()

# -----------------------------------------------------------------------------

def main():
    mappings = [
        ['Table defaults: no column separator, truncate wrap policy, table the width of the terminal', basic],
        ['Smaller table width with cell wrap policy set to wrap', wrapped],
        ['Custom formatting for header divider and column separator', custom_formatting],
        ['Alternating colored rows and header row colors', colored],
        ['Table defaults, no header data specified', no_headers],
        ['First column is right aligned, second center aligned, custom column widths', alignments],
        ['Header columns centered', header_alignments],
    ]

    menu_values = [m[0] for m in mappings]
    selected = PROMPT.prompt_menu('Select the table to demonstrate:', menu_values=menu_values)
    PROMPT.write('')

    if selected is okaara.prompt.ABORT:
        return

    func = mappings[selected][1]
    func()

# -- examples -----------------------------------------------------------------

def basic():
    PROMPT.write('Table rendered using the defaults.')
    PROMPT.write('')

    table = Table(PROMPT, NUM_COLS)
    table.render(TEST_DATA, headers=TEST_HEADERS)

def wrapped():
    PROMPT.write('Smaller table width with cell wrap policy set to wrap.')
    PROMPT.write('')

    table = Table(PROMPT, NUM_COLS, table_width=60, wrap_policy=WRAP_POLICY_WRAP)
    table.render(TEST_DATA, headers=TEST_HEADERS)

def custom_formatting():
    PROMPT.write('Custom formatting for header divider and column separator')
    PROMPT.write('')

    table = Table(PROMPT, NUM_COLS, table_width=60, wrap_policy=WRAP_POLICY_WRAP, header_divider_tick='*', col_separator=' | ')
    table.render(TEST_DATA, headers=TEST_HEADERS)

def colored():
    PROMPT.write('Alternating colored rows and header row colors')
    PROMPT.write('')

    table = Table(PROMPT, NUM_COLS, table_width=60, wrap_policy=WRAP_POLICY_WRAP)
    table.header_color=okaara.prompt.COLOR_BG_BLUE
    table.row_colors=[okaara.prompt.COLOR_LIGHT_BLUE, okaara.prompt.COLOR_LIGHT_PURPLE, okaara.prompt.COLOR_CYAN]

    table.render(TEST_DATA, headers=TEST_HEADERS)

def no_headers():
    PROMPT.write('Table defaults, no header data specified')
    PROMPT.write('')

    table = Table(PROMPT, NUM_COLS)
    table.render(TEST_DATA)

def alignments():
    PROMPT.write('First column is right aligned, second center aligned, custom column widths')
    PROMPT.write('')

    alignments = [ALIGN_LEFT for i in range(0, NUM_COLS)]
    alignments[0] = ALIGN_RIGHT
    alignments[1] = ALIGN_CENTER

    widths = [20 for i in range(0, NUM_COLS)]
    widths[0] = 5

    table = Table(PROMPT, NUM_COLS, col_alignments=alignments, col_widths=widths, wrap_policy=WRAP_POLICY_WRAP)
    table.render(TEST_DATA, headers=TEST_HEADERS)

def header_alignments():
    PROMPT.write('Header columns centered')
    PROMPT.write('')

    alignments = [ALIGN_CENTER for i in range(0, NUM_COLS)]

    table = Table(PROMPT, NUM_COLS, table_width=60, wrap_policy=WRAP_POLICY_WRAP, header_col_alignments=alignments)
    table.render(TEST_DATA, headers=TEST_HEADERS)

# -----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
