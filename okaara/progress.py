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
Contains classes related to rendering progress indicators. Each object will
take a Prompt as the output writer. The caller is responsible the iteration
and will call the appropriate method in each object to make it display the
current state.
"""
from __future__ import division
from future import standard_library
standard_library.install_aliases()
from builtins import object

import math
import threading
import time

import okaara.prompt


class ProgressBar(object):

    def __init__(self, prompt, width=40, show_trailing_percentage=True, fill='=', left_tick='[',
                 right_tick=']', in_progress_color=None, completed_color=None, render_tag=None):
        """
        :param prompt: prompt instance to write to
        :type  prompt: :py:class:`okaara.prompt.Prompt`

        :param width: number of characters wide the progress bar should be;
               this includes both the fill and the left/right ticks but does
               not include the trailing percentage if indicated
        :type  width: int

        :param show_trailing_percentage: if True, the current percentage complete
               will be listed after the progress bar; defaults to False
        :type  show_trailing_percentage: bool

        :param fill: character to use as the filled value of the progress bar;
               this must be a single character or the math gets messed up
        :type  fill: str

        :param left_tick: displayed on the left side of the progress bar
        :type  left_tick: str

        :param right_tick: displayed on the right side of the progress bar
        :type  right_tick: str

        :param in_progress_color: color to render the progress bar while it is
               incomplete (will also be used for completed bar if completed_color
               isn't specified)
        :type  in_progress_color: str

        :param completed_color: color to render the progress bar once it is
               completely filled
        :type  completed_color: str

        :param render_tag: if specified, when the bar itself is written to the
               prompt it will pass this tag
        :type  render_tag: object
        """
        self.prompt = prompt

        self.width = width
        self.show_trailing_percentage = show_trailing_percentage

        self.fill = fill
        self.left_tick = left_tick
        self.right_tick = right_tick

        self.in_progress_color = in_progress_color
        self.completed_color = completed_color

        self.render_tag = render_tag

        self.previous_lines_written = 0

    def render(self, step, total, message=None):
        """
        Renders the progress bar. The percentage filled will be calculated
        using the step and total parameters (step / total).

        If message is provided, it will be displayed below the progress bar.
        The message will be deleted on the next call to update and can be
        used to provide more information on the current step being rendered.
        """

        self.clear()

        # Generate bar
        total_fill_width = self.width - (len(self.left_tick) + len(self.right_tick))
        percentage = float(step) / float(total)
        fill_count = int(math.floor(percentage * total_fill_width))

        filled = self.fill * fill_count
        unfilled = ' ' * (total_fill_width - fill_count)
        fill_bar = '%s%s%s%s' % (self.left_tick, filled, unfilled, self.right_tick)

        if self.show_trailing_percentage:
            fill_bar += ' %s%%' % int(percentage * 100)

        # Determine the coloring if applicable
        bar_color = None
        if self.in_progress_color is not None:
            bar_color = self.in_progress_color
            if fill_count == total_fill_width:
                bar_color = self.completed_color

        # Never wrap the bar itself, that's just too much of a headache and the
        # caller should have pre-computed the size of the bar based on desired wrap.
        self.prompt.write(fill_bar, color=bar_color, tag=self.render_tag, skip_wrap=True)

        message_line_count = 0
        if message is not None:
            # We need an accurate count of how many lines will be written so we
            # can properly backtrack to re-render the bar. First step is to
            # not treat message as a single string and break it apart based on
            # the line breaks introduced by the caller.

            message_lines = message.split('\n')

            for l in message_lines:
                # It's possible the write call will want to wrap, but then it
                # won't tell us how many lines it ended up becoming. We explicitly
                # wrap it here so we can get the line count for our records and
                # then passed the already wrapped version into the write.
                wrapped = self.prompt.wrap(l)
                message_line_count += len(wrapped.split('\n'))

                self.prompt.write(wrapped, skip_wrap=True)

        # Save the number of lines written for the next iteration
        self.previous_lines_written = 1 + message_line_count

    def iterator(self, iterable, message_func=None):
        """
        Wraps an iterator to automatically make the appropriate calls into
        the progress bar on each iteration. The supplied message_func can
        be used to derive a message for each step in the iteration. For
        example::

          it = pb.iterator(items, message_func=lambda x : 'Generated message: %s' % x)
          for i in it:
            # do stuff

        :param iterable: iterator to wrap
        :type  iterable: iterator

        :param message_func: called on each step of the iteration, passing in
               the latest item retrieved from the iterator
        :type  message_func: function

        :return: iterator that will draw contents from the supplied iterator
                 and automatically update the progress bar
        :rtype:  iterator
        """

        total = len(iterable)
        message = None

        for step, item in enumerate(iterable):
            yield item

            if message_func is not None:
                message = message_func(item)

            self.render(step + 1, total, message=message)

    def clear(self):
        """
        Deletes anything rendered by the bar. This may be called after the
        long-running task has finished to remove the bar from the screen.
        This must be called before attemping to write anything new to the prompt.
        """
        if self.previous_lines_written > 0:
            self.prompt.move(okaara.prompt.MOVE_UP % self.previous_lines_written)
            self.prompt.clear(okaara.prompt.CLEAR_REMAINDER)


class Spinner(object):

    DEFAULT_SEQUENCE = '- \ | /'.split()

    def __init__(self, prompt, sequence=DEFAULT_SEQUENCE, left_tick='[', right_tick=']',
                 in_progress_color=None, completed_color=None, spin_tag=None):
        """
        :param prompt: prompt instance to write to
        :type  prompt: L{Prompt}

        :param sequence: list of characters to iterate over while spinning
        :type  sequence: list

        :param left_tick: displayed on the left side of the spinner
        :type  left_tick: str

        :param right_tick: displayed on the right side of the spinner
        :type  right_tick: str

        :param in_progress_color: color to render the spinner while it is
               incomplete (will also be used for completed bar if completed_color
               isn't specified)
        :type  in_progress_color: str

        :param completed_color: color to render the spinner once it is completely filled
        :type  completed_color: str

        :param spin_tag: if specified, this tag will be passed to the write call
               each time the spinner is updated
        :type  spin_tag: object
        """
        self.prompt = prompt

        self.sequence = sequence
        self.left_tick = left_tick
        self.right_tick = right_tick

        self.in_progress_color = in_progress_color
        self.completed_color = completed_color

        self.spin_tag = spin_tag

        self.counter = 0
        self.previous_lines_written = 0

    def next(self, message=None, finished=False):
        """
        Renders the next image in the spinner sequence.

        :param finished: if true, the spinner will apply coloring based on
               the completed_color field; defaults to false
        :param finished: bool
        """

        self.clear()

        index = self.counter % len(self.sequence)
        self.counter += 1

        output = '%s%s%s' % (self.left_tick, self.sequence[index], self.right_tick)

        color = None
        if self.in_progress_color is not None:
            color = self.in_progress_color

            if finished and self.completed_color is not None:
                color = self.completed_color

        self.prompt.write(output, color=color, tag=self.spin_tag)

        if message is not None:
            self.prompt.write(message)

        message_lines = 0
        if message is not None:
            # It's possible the write call to the message above will have wrapped
            # the message. We need to know how many lines the *wrapped* message
            # occupied so we backtrack the correct number of lines.
            wrapped = self.prompt.wrap(message)
            message_lines = len(wrapped.split('\n'))

        self.previous_lines_written = 1 + message_lines

    def iterator(self, iterable):
        """
        Wraps an iterator to automatically render the next step in the spinner
        sequence at each pass through it.

        :param iterable: iterator to wrap
        :type  iterable: iterator

        :return: iterator that will draw contents from the supplied iterator
                 and automatically update the progress bar
        :rtype:  iterator
        """

        for item in iterable:
            yield item
            next(self)

    def clear(self):
        """
        Deletes anything rendered by the spinner. This may be called after the
        long-running task has finished to remove the spinner from the screen.
        This must be called before attemping to write anything new to the prompt.
        """
        if self.previous_lines_written > 0:
            self.prompt.move(okaara.prompt.MOVE_UP % self.previous_lines_written)
            self.prompt.clear(okaara.prompt.CLEAR_REMAINDER)


class ThreadedSpinner(Spinner):
    """
    Renders a spinner in a separate thread at a regular interval. This is useful
    in cases where each step in the actual code executing while the spinner is
    running takes a variable amount of time; this will mask those differences
    from the user and result in a smooth spin.

    Once instantiated, the start() method is used to begin the rendering. Each
    step is rendered at a rate specified in refresh_seconds in the constructor.
    The spinner will continue to render until stop() is called. Callers should
    be careful to not use the prompt instance while the spinner is running.

    Due to its behavior, the iterator() method in the Spinner base class is
    not supported.
    """

    def __init__(self, prompt, refresh_seconds=.5, timeout_seconds=30, sequence=Spinner.DEFAULT_SEQUENCE,
                 left_tick='[', right_tick=']', in_progress_color=None,
                 completed_color=None, spin_tag=None):
        """
        :param refresh_seconds: time in seconds between rendering each step in
               the spinner's sequence
        :type  refresh_seconds: float

        :param timeout_seconds: time in seconds after which the spinner will
               automatically stop
        """
        Spinner.__init__(self, prompt, sequence, left_tick, right_tick,
                         in_progress_color, completed_color, spin_tag)

        self.refresh_seconds = refresh_seconds
        self.timeout_seconds = timeout_seconds

        self.running = False
        self._thread_running = False
        self.ellapsed_time = 0

    def start(self):
        """
        Causes the spinner to begin rendering steps. The rendering will be
        done through the prompt supplied in the constructor however it will be
        done in a separate thread. This call will immediately return and the
        spinning will begin.

        Callers should be careful to call stop() before attempting to use the
        prompt again. Bad things would happen if the spinner thread continued
        to attempt to update while other content was written to the prompt.

        If the spinner is already running from a previous call to start(), this
        call has no effect.
        """
        if self.running:
            return

        # Reset the state in case it's been started/stopped before
        self.previous_lines_written = 0

        self.running = True
        self.ellapsed_time = 0

        thread = threading.Thread(target=self._run)
        thread.start()

    def stop(self, clear=False):
        """
        Causes the spinner to stop spinning. The thread is not immediately
        killed but instead allowed to trigger one more step in the
        sequence. This call will block until that step has been rendered. This
        shouldn't be noticable except in cases of a very high value for
        refresh_seconds.
        """
        self.running = False

        # Wait until the thread indicates it has completed
        while self._thread_running:
            time.sleep(self.refresh_seconds)

        if clear:
            self.clear()

    def iterator(self, iterable):
        raise NotImplementedError()

    def _run(self):
        self._thread_running = True

        while self.running:
            next(self)
            time.sleep(self.refresh_seconds)
            self.ellapsed_time += self.refresh_seconds

            if self.ellapsed_time > self.timeout_seconds:
                self.running = False
        self.next(finished=True)

        self._thread_running = False
