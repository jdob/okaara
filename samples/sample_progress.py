#!/usr/bin/python
#
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

import time

from okaara.prompt import Prompt, COLOR_LIGHT_YELLOW, COLOR_LIGHT_GREEN
from okaara.progress import ProgressBar, Spinner, ThreadedSpinner


def progress_bar_demo():
    p = Prompt()

    pb = ProgressBar(p)

    total = 21
    for i in range(0, total + 1):
        message = 'Step: %d of %d' % (i, total)

        if i % 3 is 0:
            message += '\nSecond line in message'

        if i % 6 is 0:
            message += '\nThird line in message'

        pb.render(i, total, message)
        time.sleep(.25)

    p.write('Completed first progress bar example')
    p.write('')

    pb = ProgressBar(p, fill='*', left_tick='-<', right_tick='>-', show_trailing_percentage=False,
                     in_progress_color=COLOR_LIGHT_YELLOW, completed_color=COLOR_LIGHT_GREEN)

    total = 17
    for i in range(0, total + 1):
        pb.render(i, total)
        time.sleep(.1)

    p.write('Completed second progress bar example')
    p.write('')

    pb = ProgressBar(p)

    items = 'a b c d e f g h i j k l m n o p'.split()
    wrapped = pb.iterator(items, message_func=lambda x: 'Generated for item: %s' % x)

    for w in wrapped:
        # Do important stuff but don't worry about progress bar
        time.sleep(.3)

    p.write('Completed wrapped iteration through progress bar')
    p.write('')


def spinner_demo():
    p = Prompt()
    spinner = Spinner(p)

    total = 10
    for i in range(0, total):
        spinner.next()
        time.sleep(.25)

    spinner.clear()
    p.write('Completed first spinner example')
    p.write('')

    sequence = '! @ # $ %'.split()
    spinner = Spinner(p, sequence=sequence, left_tick='{', right_tick='}',
                      in_progress_color=COLOR_LIGHT_YELLOW, completed_color=COLOR_LIGHT_GREEN)

    total = 10
    for i in range(0, total):
        finished = i == (total - 1)

        spinner.next(finished=finished, message='Message: %s' % i)
        time.sleep(.25)

    p.write('Completed second spinner example')
    p.write('')


def threaded_spinner_demo():
    p = Prompt()
    s = ThreadedSpinner(p, refresh_seconds=.1)

    p.write('Starting threaded spinner, spinner should keep moving while this thread sleeps')

    s.start()
    time.sleep(3)  # spinner should keep moving
    s.stop()

    p.write('Threaded spinner stopped')
    p.write('')

    s = ThreadedSpinner(p, refresh_seconds=.1, timeout_seconds=2)

    p.write('Starting threaded spinner, spinner will time out while the execution thread is working')

    s.start()
    time.sleep(3)  # spinner should keep moving
    s.stop()

    p.write('Threaded spinner timed out')
    p.write('')

    s = ThreadedSpinner(p, refresh_seconds=.1)

    p.write('Starting threaded spinner with auto-clear')

    s.start()
    time.sleep(3)  # spinner should keep moving
    s.stop(clear=True)

    p.write('Threaded spinner stopped')
    p.write('')


    s = ThreadedSpinner(p, refresh_seconds=3)

    p.write('Starting threaded spinner reuse test')

    s.start()
    time.sleep(.01)
    s.stop()
    p.write('Stopped 1')

    s.start()
    time.sleep(.01)
    s.stop()
    p.write('Stopped 2')


if __name__ == '__main__':
    progress_bar_demo()
    spinner_demo()
    threaded_spinner_demo()
