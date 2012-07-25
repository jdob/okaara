# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import okaara.prompt
import okaara.table

p = okaara.prompt.Prompt()

table = okaara.table.Table(p, 4, table_max_width=60, wrap_policy=okaara.table.WRAP_POLICY_WRAP, col_separator=' ')

data = [
    ['aaaaa', 'bbbbb', 'ccccc', 'ddddd'],
    ['eeeeeeee', 'ffff', 'gggggggg', 'hhhhhhhhhhhhhhh'],
    ['iiii', 'jjjj', 'kk', 'lllllllllllll'],
    ['m', 'n', 'ooo', 'ppppppp'],
    ['qqqqqq', 'rrrr', 'sss', 't']
]

headers = ['Column 1', 'Column 2', 'Really Long Column 3','Column 4']

table.render(data, headers=headers)

p.write('')
p.write('')

table = okaara.table.Table(p, 4, table_max_width=60, wrap_policy=okaara.table.WRAP_POLICY_WRAP, col_separator=' | ')
table.render(data, headers=headers)

p.write('')
p.write('')

table = okaara.table.Table(p, 4, table_max_width=60, wrap_policy=okaara.table.WRAP_POLICY_WRAP, col_separator=' | ',
                           header_color=okaara.prompt.COLOR_BG_BLUE, row_colors=[okaara.prompt.COLOR_BG_CYAN + okaara.prompt.COLOR_BLUE, okaara.prompt.COLOR_LIGHT_PURPLE, okaara.prompt.COLOR_CYAN],
                           color_separators=True)
table.render(data, headers=headers)

p.write('')
p.write('')

table = okaara.table.Table(p, 4, table_max_width=60, wrap_policy=okaara.table.WRAP_POLICY_WRAP, col_separator=' | ',
                           header_color=okaara.prompt.COLOR_BG_BLUE, row_colors=[okaara.prompt.COLOR_BG_CYAN + okaara.prompt.COLOR_BLUE, okaara.prompt.COLOR_LIGHT_PURPLE, okaara.prompt.COLOR_CYAN],
                           color_separators=False)
table.render(data, headers=headers)