Okaara
======

Overview
--------

Okaara is a series of utilities for writing command line interfaces in Python.
The provided functionality can be broken down into three categories: reading and
writing utilities, an interactive shell framework, and a command line interface
framework.

Input & Output
^^^^^^^^^^^^^^

Okaara provides a wrapper around accepting user input and displaying output.
At it's most basic level, the read/write methods allow standard input/output
to be replaced transparent from the code that uses them. More useful is the
ability to script input and capture and tag output for use in unit tests.

In addition to being an abstraction from standard output, the Okaara prompt
provides a number of utilities for more advanced output, such as:

* Automatically wrapping text to either a set width or the current size of the screen
* Colored text
* Centering text
* Arbitrary cursor placement in the terminal

The okaara prompt also may be configured to tag output written to it. This
ability may be used in unit tests to assert the correct messages are being
displayed to the user. More information and examples of this can be found on
the :doc:`prompt usage and examples page <prompt>`.

The other major piece of functionality in the Okaara prompt is comprised of a
series of formatted prompts to request input from the user. A user prompt can
be configured to allow or deny empty responses, allow the user to indicate the
prompt has been aborted and no input was specificed, and capture a keyboard
interrupt to allow the caller to react gracefully from it. Many prompt calls
include input validation where applicable and will automatically reprompt the
user in the event of an invalid input. The prompt functionality includes:

* Ensuring the user inputs one in a series of enumerated values
* Simple yes/no prompt
* Requiring a numeric input, optionally indicating non-zero or positive number restrictions
* Range-based numeric input
* File or directory name input, ensuring the existence of the entered file/directory
* Menu-based inputs, including the ability to select more than one value from the menu before proceeding
* Hidden password input

More information can be found on the :doc:`usage and examples page <prompt>`
or in the :doc:`prompt module API documentation <prompt-api>`.

Okaara also provides a progress module for rendering progress indicators for
long running operations. Progress bars and spinners are supported, both of which
may be configured with custom rendering ticks and can automatically wrap an
iterator to simplify the update of the widget.

For more information on the progress module, see :doc:`some examples <progress>`
or the :doc:`progress module API documentation <progress-api>`.

Shell
^^^^^

Okaara provides the framework around creating interactive shell interfaces. A
shell consists of one or more screens, each with their own menu of possible
commands. Okaara provides the structure for navigating between screens, rendering
of a screen's menu, and accepting the appropriate trigger to execute a menu's command.

For more information on the shell module, see the :doc:`usage and examples page<shell>`
or the :doc:`shell module API documentation <shell-api>`.

CLI
^^^

In Okaara, a CLI provides the ability to structure and execute multiple, different
commands to a single script. Commands may be grouped into sections to provide a
flexible organizational structure for the provided functionality.

Download
--------

Built RPMs can be found at: `<http://jdob.fedorapeople.org/repo/>`_

Source code can be found at: `<https://github.com/jdob/okaara/>`_

Usage Documentation
-------------------

.. toctree::
   :maxdepth: 1

   prompt
   progress
   shell

API Documentation
-----------------

.. toctree::
   :maxdepth: 2

   prompt-api
   progress-api
   shell-api
   cli-api
