#!/usr/bin/python
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import math

class ProgressBar:

    def __init__(self, prompt, width=40, fill='=', left_tick='[', right_tick=']'):
        self.prompt = prompt

        self.width = width
        self.fill = fill
        self.left_tick = left_tick
        self.right_tick = right_tick

        self.position_saved = False

    def update(self, step, total, message=None):

        if self.position_saved:
            self.prompt.reset_position()

        self.prompt.save_position()
        self.position_saved = True

        # Generate bar
        total_fill_width = self.width - (len(self.left_tick) + len(self.right_tick)) # subtract the leading/trailing ticks
        percentage = float(step) / float(total)
        fill_count = int(math.floor(percentage * total_fill_width))

        filled = self.fill * fill_count
        unfilled = ' ' * (total_fill_width - fill_count)
        fill_bar = '%s%s%s%s' % (self.left_tick, filled, unfilled, self.right_tick)

        self.prompt.write(fill_bar)

        if message is not None:
            self.prompt.write(message)

if __name__ == '__main__':

    import time
    import okaara.prompt

    p = okaara.prompt.Prompt()

    pb = ProgressBar(p)

    total = 20
    for i in range(0, total + 1):
        pb.update(i, total, 'Step: %d of %d' % (i, total))
        time.sleep(.1)

    p.write('Completed')