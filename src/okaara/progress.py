#!/usr/bin/python
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import math

import okaara.prompt

class ProgressBar:

    def __init__(self, prompt, width=40, show_trailing_percentage=False, fill='=', left_tick='[', right_tick=']'):
        """
        @param prompt: prompt instance to write to
        @type  prompt: L{Prompt}

        @param width: number of characters wide the progress bar should be;
               this includes both the fill and the left/right ticks but does
               not include the trailing percentage if indicated
        @type  width: int

        @param show_trailing_percentage: if True, the current percentage complete
               will be listed after the progress bar; defaults to False
        @type  show_trailing_percentage: bool

        @param fill: character to use as the filled value of the progress bar;
               this must be a single character or the math gets messed up
        @type  fill: str

        @param left_tick: displayed on the left side of the progress bar
        @type  left_tick: str

        @param right_tick: displayed on the right side of the progress bar
        @type  right_tick: str
        """
        self.prompt = prompt

        self.width = width
        self.show_trailing_percentage = show_trailing_percentage

        self.fill = fill
        self.left_tick = left_tick
        self.right_tick = right_tick

        self.previous_lines_written = 0

    def render(self, step, total, message=None):
        """
        Renders the progress bar. The percentage filled will be calculated
        using the step and total parameters (step / total).

        If message is provided, it will be displayed below the progress bar.
        The message will be deleted on the next call to update and can be
        used to provide more information on the current step being rendered.
        """

        if self.previous_lines_written > 0:
            self.prompt.move(okaara.prompt.MOVE_UP % self.previous_lines_written)
            self.prompt.clear(okaara.prompt.CLEAR_REMAINDER)

        # Generate bar
        total_fill_width = self.width - (len(self.left_tick) + len(self.right_tick)) # subtract the leading/trailing ticks
        percentage = float(step) / float(total)
        fill_count = int(math.floor(percentage * total_fill_width))

        filled = self.fill * fill_count
        unfilled = ' ' * (total_fill_width - fill_count)
        fill_bar = '%s%s%s%s' % (self.left_tick, filled, unfilled, self.right_tick)

        if self.show_trailing_percentage:
            fill_bar += ' %s%%' % int(percentage * 100)

        self.prompt.write(fill_bar)

        if message is not None:
            self.prompt.write(message)

        # Save the number of lines written for the next iteration
        message_lines = 0
        if message is not None:
            message_lines = len(message.split('\n'))

        self.previous_lines_written = 1 + message_lines

class Spinner:

    DEFAULT_SEQUENCE = '- \ | /'.split()

    def __init__(self, prompt, sequence=DEFAULT_SEQUENCE, left_tick='[', right_tick=']'):
        """
        @param prompt: prompt instance to write to
        @type  prompt: L{Prompt}

        @param sequence: list of characters to iterate over while spinning
        @type  sequence: list

        @param left_tick: displayed on the left side of the spinner
        @type  left_tick: str

        @param right_tick: displayed on the right side of the spinner
        @type  right_tick: str

        """
        self.prompt = prompt

        self.sequence = sequence
        self.left_tick = left_tick
        self.right_tick = right_tick

        self.counter = 0

    def spin(self):
        """
        Renders the next image in the spinner sequence.
        """

        if self.counter > 0:
            self.prompt.move(okaara.prompt.MOVE_UP % 1)
            self.prompt.clear(okaara.prompt.CLEAR_REMAINDER)

        index = self.counter % len(self.sequence)
        self.counter += 1

        output = '%s%s%s' % (self.left_tick, self.sequence[index], self.right_tick)
        self.prompt.write(output)

# -----------------------------------------------------------------------------

if __name__ == '__main__':

    import time
    import okaara.prompt

    p = okaara.prompt.Prompt()

    pb = ProgressBar(p, show_trailing_percentage=True)

    total = 21
    for i in range(0, total + 1):
        multi_line = False

        message = 'Step: %d of %d' % (i, total)

        if i % 3 is 0:
            message += '\nSecond line in message'
            multi_line = True

        if i % 6 is 0:
            message += '\nThird line in message'
            multi_line = True

        pb.render(i, total, message)
        time.sleep(.1)

        # Sleep a bit longer on the second line messages so it doesn't flicker as much
        if multi_line:
            time.sleep(.25)

    p.write('Completed first progress bar example')
    p.write('')

    pb = ProgressBar(p, fill='*', left_tick='-<', right_tick='>-')

    total = 17
    for i in range(0, total + 1):
        pb.render(i, total)
        time.sleep(.1)

    p.write('Completed second progress bar example')
    p.write('')

    spinner = Spinner(p)

    total = 10
    for i in range(0, total):
        spinner.spin()
        time.sleep(.25)

    p.write('Completed first spinner example')
    p.write('')

    sequence = '! @ # $ %'.split()
    spinner = Spinner(p, sequence=sequence, left_tick='{', right_tick='}')

    total = 10
    for i in range(0, total):
        spinner.spin()
        time.sleep(.25)

    p.write('Completed second spinner example')