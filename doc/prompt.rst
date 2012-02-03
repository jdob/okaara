Prompt
======

In most cases, there is very little to configure when creating a new ``Prompt``
instance. The defaults will use standard input and output and will not record
any tag information passed into write calls. Simply instantiate and use::

 p = Prompt()
 p.write('Goodbye World')
 name = p.read('What is your name?')

Text Modifiers
^^^^^^^^^^^^^^

A few methods are used to modify text but not actually write it. The intention
here is to chain them together to pre-format the text. For example::

 p.write(p.center(p.color('Important', COLOR_RED)))

In some cases, shortcuts are provided in the write methods themselves.

Keyboard Interrupts
^^^^^^^^^^^^^^^^^^^

By default, Okaara will intercept KeyboardInterrupt exceptions (i.e. if the user
presses ctrl+C) and return to the caller a reference to the ``ABORT`` object
in the prompt module. This lets the caller easily distinguish between an empty
input from the user (will be an empty string) versus the user cancelling during
the read. This behavior can be overridden to allow KeyboardInterrupt exceptions
to be raised using the ``interruptable`` flag on the read method.

For a quick example::

  from okaara.prompt import Prompt, ABORT
  p = Prompt()

  age = p.read('How old are you?')
  if age is ABORT:
    p.write('Fine, be like that.')

Colors
^^^^^^

The prompt module defines a number of constants used for coloring text. The
``COLOR_*`` variables should be the only values passed to either the color
method or the color attribute on the write method.

Testing
=======

I'm a compulsive unit tester, so I wanted to provide an answer for some of the
difficulties in unit testing a user interface.

Testing Output
^^^^^^^^^^^^^^

One option to assert the output displayed to a user is to capture it and
compare it against expected results. This can get wonky as the UI evolves and
phrasing changes.

Okaara addresses by allowing a tag to be specified to each write call. The
tag should be something simple to identify what is being displayed in the call.
During unit testing, the prompt can be configured to capture these tags and
make them available in the test verification step.

For example, given the following UI::

  value = # some value from somewhere
  if value is True:
    p.write('Entered value was acceptable', tag='success')
  else:
    p.write('Invalid value, exiting', tag='error')

In the test case for this UI, recording of tags would be enabled and the test
would verify the correct output was displayed by checking the tags::

  p = Prompt(record_tags=True)
  # Pass p to the code being tested
  self.assertEqual('success', p.get_read_tags()[0])

Testing Input
^^^^^^^^^^^^^

The same tagging concept for writing is available to reading user input as well.
There is a corresponding ``get_write_tags`` method for retrieving these tags.

The prompt module also provides the ``ScriptedPrompt`` subclass to aid in testing.
This still needs a bit of work but the intention is to provide a list of values
that should be returned, in order, when the prompt attempts to read a value.
This lets a unit test script out user input to simulate user interaction.