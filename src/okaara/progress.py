# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""
Contains classes related to rendering progress indicators. Each object will
take a Prompt as the output writer. The caller is responsible the iteration
and will call the appropriate method in each object to make it display the
current state.
"""

import math
import threading
import time

import okaara.prompt

class ProgressBar:

    def __init__(self, prompt, width=40, show_trailing_percentage=True, fill='=', left_tick='[', right_tick=']',
                 in_progress_color=None, completed_color=None, render_tag=None):
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
        total_fill_width = self.width - (len(self.left_tick) + len(self.right_tick)) # subtract the leading/trailing ticks
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


class Spinner:

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
            self.next()

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
        self.ellapsed_time = 0

        self.lock = threading.Lock()

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

        self.lock.acquire()

        thread = threading.Thread(target=self._run)
        thread.start()

    def stop(self):
        """
        Causes the spinner to stop spinning. The thread is not immediately
        killed but instead allowed to have trigger one more step in the
        sequence. This call will block until that step has been rendered. This
        shouldn't be noticable except in cases of a very high value for
        refresh_seconds.
        """
        self.running = False
        self.lock.acquire() # block until the thread finishes so the user knows its done
        self.lock.release() # release so start() can be called again

    def iterator(self, iterable):
        raise NotImplementedError()

    def _run(self):
        while self.running:
            self.next()
            time.sleep(self.refresh_seconds)
            self.ellapsed_time += self.refresh_seconds

            if self.ellapsed_time > self.timeout_seconds:
                self.stop()
        self.next(finished=True)
        self.lock.release()

# -----------------------------------------------------------------------------

def demo():
    import okaara.prompt
    p = okaara.prompt.Prompt()

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
                     in_progress_color=okaara.prompt.COLOR_LIGHT_YELLOW, completed_color=okaara.prompt.COLOR_LIGHT_GREEN)

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
                      in_progress_color=okaara.prompt.COLOR_LIGHT_YELLOW, completed_color=okaara.prompt.COLOR_LIGHT_GREEN)

    total = 10
    for i in range(0, total):
        finished = i == (total - 1)

        spinner.next(finished=finished)
        time.sleep(.25)

    p.write('Completed second spinner example')
    p.write('')

    s = ThreadedSpinner(p, refresh_seconds=.1)

    p.write('Starting threaded spinner, spinner should keep moving while this thread sleeps')

    s.start()
    time.sleep(3) # spinner should keep moving
    s.stop()

    p.write('Threaded spinner stopped')
    p.write('')

def multi_call_demo():
    import okaara.prompt
    p = okaara.prompt.Prompt()

    s = ThreadedSpinner(p, refresh_seconds=3)

    s.start()
    time.sleep(.01)
    s.stop()
    p.write('Stopped 1')

    s.start()
    time.sleep(.01)
    s.stop()
    p.write('Stopped 2')

def test():
    import okaara.prompt
    p = okaara.prompt.Prompt(wrap_width=20)

    pb = ProgressBar(p)

    total = 21
    for i in range(0, total + 1):
        message  = 'Step: %d of %d\n' % (i, total)
        message += 'Second line 123456789012345678901234567890\n'
        message += 'Third line\n'
        message += 'Fourth line\n'

        pb.render(i, total, message)
        time.sleep(.15)

if __name__ == '__main__':
    test()
