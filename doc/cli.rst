Command Line Interface
======================

Overview
^^^^^^^^

A CLI in Okaara is an executable that uses a series of arguments to perform
different functions in an application. Commands, which are used to trigger
an action by the CLI, are grouped into sections and subsections to better
organize a wide array of functionality within a single executable. Options can
defined for a command and Okaara will parse and provide their values to the
appropriate code.

Below is an example of what some basic user operations might look like in a
Okaara CLI::

 $ my-app users create --login tstark --password okaara --group admin
 User successfully created.

 $ my-app users list --show-admins
 Users:
   tstark
   bbanner
   hpym

 $ my-app login --username tstark --password okaara
 User successfully logged in.

Getting Started
^^^^^^^^^^^^^^^

The root of everything is the ``CLI`` class. Once instantiated, it can be
populated with the appropriate sections and commands to provide its functionality.
A prompt instance may be provided if necessary, but otherwise the defaults should
be enough to get started.

A ``Section`` is used to organize a group of related commands or subsections.
A section works as a namespace when referring to a specific command in the CLI.
For example, the following is a possible call to a demo CLI::

  $ demo section1 subsection3 command2 --opt1 value --flag1

Okaara will translate the user call and navigate to the appropriate place in
the code. If the user call doesn't refer to a valid structure, Okaara will detect
the closest match and display its usage.

A ``Command`` may define either ``Option`` or ``Flag`` arguments. Okaara will use
the definitions to validate user input and make them available to the code that
handles the command.

Once the CLI has been assembled, it's invoked using the ``run`` method. This
call takes a list of strings to process; the expectation is to pass in
``sys.argv[1:]`` but that's up to the caller (for example, passing in a list of
known strings for unit tests).

Those are the basic concepts. Putting them all together can be seen in the
sample CLI code included in the source or at:
`<https://github.com/jdob/okaara/blob/master/samples/sample_cli.py>`_

Commands
^^^^^^^^

Command objects are used to link the framework to the actual code to execute
when the user runs the command. At instantiation, the following is provided:

* The name used to invoke the command from the command line.
* A description of the command, displayed in the command's usage.
* A reference to the method to invoke when the command is run is specified.

For example, a create user command might look like the following::

 class CreateUserCommand(Command):
   def __init__(self):
     Command.__init__(self, 'create', 'creates a new user', self.create)

   def create(self):
     # Create logic here

The next step is to support arguments to the command itself. Pulp provides
two classes to this end. The ``Option`` class is used for arguments that accept
a value, such as ``--username jdob``. The ``Flag`` class is used to describe
arguments whose presence implies true, such as ``--enabled``.

These classes take slightly different parameters, the most notable being that
there is no concept of required for flags; a required flag would always resolve
to true and not carry any meaning.

In both cases, the name parameter defines how Okaara will reference the value
for the argument. It is also what the user will use to refer to it when calling
the executable. Alternate command line triggers can be defined by passing a
list of them to the aliases parameter, however the Okaara name for the value
will always be the name of the command.

By default, Okaara uses optparse to handle parsing arguments to a command. Thus
the normal rules apply, such as multi-character names beginning with "--" and
single character names beginning with a single "-". In more rare cases, the
default optparse parser can be overridden in the Command object itself to
provide behavior not possible through the Okaara objects.

Okaara will verify that all options marked as required are present in the call.
If not, the user is displayed the command usage and a list of missing required
values. Okaara will pass all defined options to the command's configured method
when it invokes it as keyword arguments. Any options not specified by the user
will have a value of ``None``.

Taking the create example from above, below is an enhanced version that is
configured with options (both required and optional) and flags::

 class CreateUser(Command):
   def __init__(self):
     Command.__init__(self, 'create', 'creates a new user', self.create)

     self.create_option('--username', 'login for the new user', aliases=['-u'], required=True)
     self.create_option('--group', 'group to add the user to', required=False)
     self.create_flag('--disabled', 'do not allow logins to the new user')

   def create(self, **kwargs):
     username = kwargs['username']
     group = kwargs['group']
     disabled = kwargs['disabled']

     # Create the user
     if disabled:
       # Call to disable the user immediately

Commands are added either to a section or to the root of the CLI itself. The
create user command above can be added to a simple CLI using the following::

 cli = Cli()
 users_section = cli.create_section('users', 'user related operations')
 users_section.add_command(CreateUserCommand())

Advanced Usage
^^^^^^^^^^^^^^

Conventions
-----------

Throughout the APIs there are a number of methods that begin with either ``add_``
or ``create_``. The add methods are used with object instances directly, such
as to add a previously instantiated command to a section. The create methods
are syntactic sugar to shortcut the object creation and return the appropriate
instantiated object. The end result is the same, it's simply a matter of
stylistic preference.

Multiple Option Values
----------------------

If an option is created with the ``allow_multiple`` parameter set to true, users
can specify the option multiple times on the command line. All of the values will
be provided to the command's method when invoked. In this case, the value of the
option in the keyword arguments will *always* be a list, regardless of whether
or not the user elected to specify multiple values.

Option Description Prefixes
---------------------------

The ``Command`` class defines two constants, ``REQUIRED_OPTION_PREFIX`` and
``OPTIONAL_OPTION_PREFIX``. The values of each of the variables is added in
front of an option's description when its usage is displayed. Setting either
of these values provides a simple way to achieve consistency across a UI in
terms of flagging an option's usage.

UnknownArgsParser
-----------------

In most cases, a command will have a priori knowledge of its expected options
and flags. However, it is possible that a command would want to leave it entirely
open ended for the user. In these cases, the ``parser`` parameter on the Command
instance should be set to override the default optparse behavior.

The cli module provides a class called ``UnknownArgsParser`` for this need. If
an instance of this class is provided to the command, it will ignore any options
and flags defined for it. Instead, it will read in any user-supplied arguments
and make them available in the keyword arguments to the command's method. The
likely usage at that point will be to iterate over the keyword arguments for
each provided value.

CLI Map
-------

The ``print_cli_map`` method in the CLI is used to display the hierarchy of
sections, subsections, and commands in the CLI. This call can be wired to a
command in the CLI itself to provide this ability for users.
