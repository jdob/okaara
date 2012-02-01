Progress Bars & Spinners
========================

Examples of the progress widgets in action can be seen by running the progress.py
module directly::

  cd src/okaara
  python progress.py

Progress Bars
-------------

When instantiated, the only required argument is the ``Prompt`` class instance
used to render the progress bar. The total number of values the bar will
represent, or for that matter the data itself, are not needed at instantiation time.

At each step of the iteration, the ``render`` method is called. This will redraw
the progress bar using the current step and total number of steps passed into it.
Additionally, a message for that step may be specified to be displayed under
the bar. This message may be a single line or contain \n characters to have it
display across multiple lines.

The simplest implementation of a progress bar can be seen in the following
code snippet (module imports omitted for brevity)::

  p = Prompt()
  pb = ProgressBar(p, show_trailing_percentage=True)

  total = 21
  for i in range(0, total + 1):
    pb.render(i, total)
    time.sleep(.25)

The output will continue to update as it executes and is difficult to capture in
documentation. The end result will appear as follows::

  [======================================] 100%

It's also possible to customize much of the rendering of the progress bar itself.
The following code snippet changes the default characters used for the bar
and disables the percentage indicator at the right::

  pb = ProgressBar(p, fill='*', left_tick='-<', right_tick='>-', show_trailing_percentage=False)

And the output at the end::

  -<************************************>-

Again, it's hard to show how the progress bar updates during execution. The following
code snippet shows how to add a message to the progress bar::

  for i in range(0, total + 1):
    message = 'Step: %d of %d' % (i, total)
    pb.render(i, total, message)

At the end of the execution, the final result displays::

  [======================================] 100%
  Step: 21 of 21

Instead of manually handling the call to ``render``, an iterator may be wrapped
by the progress bar to automatically render it at each step in the iteration.
When the iterator is wrapped, a function can be supplied that accepts the
current item being rendered and return a message string to use for that step.
For example, to automatically render a progress bar over a series of items::

  wrapped = pb.iterator(items, message_func=lambda x: 'Generated for item: %s' % x)

  for w in wrapped:
    # Do important stuff but don't worry about progress bar

Each time an item is iterated over, the progress bar will be updated, generating
a message custom for that particular item.

Spinners
--------

If progress bars were difficult to show in static documentation, spinners are
going to be near impossible. :)

A spinner is a sequence of characters that will render in place during a long
running operation. Unlike a progress bar, a spinner has no concept of how many
times it will be spun nor can it display a message at each step.

The simplest usage of a spinner is as follows::

  p = Prompt()
  spinner = Spinner(p)

  total = 10
  for i in range(0, total):
    spinner.spin()
    time.sleep(.25)

That example will use the default sequence (it looks like a line spinning around).
At the end of executing the above code, the last rendered iteration look like::

  [\]

A custom sequence of characters may be supplied, along with the left/right
boundaries of the spinner::

  sequence = '! @ # $ %'.split()
  spinner = Spinner(p, sequence=sequence, left_tick='{', right_tick='}')

With the custom ticks, the end output of a loop oer 10 items looks like::

  {%}

Again, not terribly interesting in static documentation. All of these examples
appear in the progress module itself and can be seen in action using the instructions
above.

The ``Spinner`` class also supports wrapping an iterator; the process is the same
as for progress bars.
