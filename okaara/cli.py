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
from __future__ import absolute_import
from builtins import str
from builtins import object

import gettext
from optparse import OptionParser, Values, BadOptionError
import os
import sys

from .prompt import Prompt
from functools import reduce

t = gettext.translation('okaara', fallback=True)
if sys.version_info[0] < 3:
    _ = t.ugettext
else:
    _ = t.gettext

# -- exceptions ---------------------------------------------------------------

class InvalidStructure(Exception):
    """
    Indicates the programmer attempted to assemble a CLI with sections/commands
    that would conflict with each other (likely duplicates).
    """
    pass


class CommandUsage(Exception):
    """
    Indicates the command parameters were incorrect. If the usage error was the
    lack of required parameters, all required parameters that were missing can
    be specified.

    :param missing_options: optional list of missing required options
    :type  missing_options: list of Option

    :param unexpected_options: list of option names that are not defined on the
                               command but were specified
    :type  unexpected_options: list of str
    """
    def __init__(self, missing_options=None, unexpected_options=None):
        Exception.__init__(self)
        self.missing_options = missing_options
        self.unexpected_options = unexpected_options


class OptionValidationFailed(Exception):
    """
    Raised internal to the CLI structure to indicate a command execution
    failed because one of the options failed its validation function.
    """
    pass

# -- classes ------------------------------------------------------------------

class NoCatchErrorParser(OptionParser):
    """
    OptionParser's default behavior for handling errors is to print the output
    and exit. I'd rather go through the rest of the CLI's output methods, so
    change this behavior to throw my exception instead.
    """
    def exit(self, status=0, msg=None):
        raise CommandUsage()

    def print_help(self, file=None):
        # The CLI will take care of formatting the options for a --help call,
        # so do nothing here.
        pass

    def parse_args(self, args=None, values=None):
        """
        Copied directly from optparse with the change that an exception on
        _process_args isn't passed to error but rather converted into a
        CommandUsage. Bad optparse, passing a string version of the exception
        to error instead of the programmatically accessible data and letting
        error() do with it as it wishes.
        """
        rargs = self._get_args(args)
        if values is None:
            values = self.get_default_values()

        self.rargs = rargs
        self.largs = largs = []
        self.values = values

        try:
            self._process_args(largs, rargs, values)
        except BadOptionError as e:
            # Raise with the data, not a string version of the exception
            raise CommandUsage(unexpected_options=[e.opt_str])

        args = largs + rargs
        return self.check_values(values, args)


class Option(object):
    """
    Represents an input to a command, either optional or required.
    """
    def __init__(self, name, description, required=True, allow_multiple=False,
                 aliases=None, default=None, validate_func=None, parse_func=None):
        self.name = name
        self.description = description
        self.required = required
        self.allow_multiple = allow_multiple
        self.default = default
        self.validate_func = validate_func
        self.parse_func = parse_func

        if aliases is not None and not isinstance(aliases, (list, tuple)):
            aliases = [aliases]
        self.aliases = aliases

    def __str__(self):
        return 'Option [%s]' % self.name

    @property
    def keyword(self):
        """
        Returns the keyword the option will be stored under when parsed.

        :return: keyword to look up in the method handling the command
        :rtype:  str
        """
        return self.name.lstrip('-')


class Flag(Option):
    """
    Specific form of an option that does not take a value; it is meant to be
    either included in the command or excluded.
    """
    def __init__(self, name, description, aliases=None):
        Option.__init__(self, name, description, required=False, allow_multiple=False, aliases=aliases)


class OptionGroup(object):
    """
    Used purely for usage display purposes, options and flags added to a group
    will be rendered in their own section. Their behavior is still the same
    (i.e. they must still be unique across the command).
    """

    def __init__(self, name, description=None):
        self.name = name
        self.description = description

        self.options = []

    def add_option(self, option):
        """
        Adds an option that can be specified when executing this command. Options
        added in this fashion should not be added explicitly to the command,
        but rather the group is passed to the command and the options associated
        in that way.

        :param option: option (or flag) to add to the command
        :type  option: Option
        """
        self.options.append(option)


class Command(object):
    """
    Represents something that should be executed by the CLI. These nodes will be
    leaves in the CLI tree. Each command is tied to a single python method and
    will invoke that method with whatever arguments follow it.
    """

    # When printing the usage for a command, the description for any options
    # is prefixed with one of these two values depending on its required value
    REQUIRED_OPTION_PREFIX = _('(required) ')
    OPTIONAL_OPTION_PREFIX = ''

    def __init__(self, name, description, method, usage_description=None, parser=None):
        self.name = name
        self.description = description
        self.method = method
        self.usage_description = usage_description
        self.parser = parser

        self.options = []
        self.option_groups = []

    def __str__(self):
        return 'Command [%s]' % self.name

    def execute(self, prompt, args):
        """
        Executes this command, passing the remaining arguments into optparse to
        process.

        :param prompt: for any output the framework needs to display
        :type  prompt: Prompt

        :param args: any arguments that remained after parsing the command line
                     to determine the command to execute; these are considered
                     arguments to the command's execution itself
        :type  args: list of strings
        """

        # Parse the command arguments into a dictionary
        try:
            arg_list, kwarg_dict = self.parse_arguments(prompt, args)
        except OptionValidationFailed:
            return os.EX_DATAERR

        # Make sure all of the required arguments have been specified
        missing_required = [o for o in self.all_options()
                            if o.required and (o.name not in kwarg_dict or
                                               kwarg_dict[o.name] is None)]
        if len(missing_required) > 0:
            raise CommandUsage(missing_options=missing_required)

        # Flag entries that are not specified are parsed as None, but I'd rather
        # them explicitly be set to false. Iterate through each flag explicitly
        # setting the value to false if it was not specified
        for o in self.options:
            if isinstance(o, Flag) and kwarg_dict[o.name] is None:
                kwarg_dict[o.name] = False

        # Clean up option names
        clean_kwargs = dict([(k.lstrip('-'), v) for k, v in kwarg_dict.items()])

        return self.method(*arg_list, **clean_kwargs)

    def add_option(self, option):
        """
        Adds an option that can be specified when executing this command. When
        executing the command, the user specified arguments to the command are
        parsed according to options specified in this fashion.

        :param option: option (or flag) to add to the command
        :type  option: Option
        """
        self.options.append(option)

    def add_flag(self, flag):
        """
        Adds a flag that can be specified when executing this command. As Flag
        is a subclass of Option, this call has the same effect as add_option
        and is simply included as syntactic sugar for completeness.

        :param flag: flag to add to the command
        :type  flag: Flag
        """
        self.add_option(flag)

    def add_option_group(self, option_group):
        """
        Adds an option group to the command. Option groups will be rendered in
        the order they are added.

        :param option_group: option group
        :type  option_group: OptionGroup
        """
        self.option_groups.append(option_group)

    def create_option(self, name, description, aliases=None, required=True, allow_multiple=False,
                      default=None, validate_func=None, parse_func=None):
        """
        Creates a new option for this command. An option is an argument to the
        command line call that accepts a value.

        The given name must be unique across all options within this command.
        The option instance is returned and can be further edited except for
        its name.

        If the default parser is used by the command, the name must match the
        typical command line argument format, either:

        * -s - where s is a single character
        * --detail - where the argument is longer than one character

        The default parser will strip off the leading hyphens when it makes the
        values available to the command's method.

        The validate_func is run against the user-specified value to verify
        it. If the value is valid, this method should do nothing. In the event
        the value is invalid, a ValueError or TypeError should be raised.

        The signature of this method takes a single argument that is the
        user-specified value. This function will only be called if the option
        is specified by the user.

        The parse_func functions in a similar manner. If specified, it will be
        run against the user-specified value. The return from this call will
        replace the user-specified value and be passed to the command's
        execution. The arguments are the same as for validate_func. This
        function will only be called if the option is specified by the user.

        The parse_func may raise ValueError or TypeError as well. The behavior
        will be the same as for validate_func, allowing the parse_func, if
        applicable, to function as both the validation and parsing logic.

        :param name: trigger to set the option
        :type  name: str

        :param description: user-readable text describing what the option does
        :type  description: str

        :param aliases: list of other argument names that may be used to set
               the value for this option
        :type  aliases: list

        :param required: if true, the default parser will enforce the the user
               specifies this option and display a usage warning otherwise
        :type  required: bool

        :param allow_multiple: if true, the value of this option when parsed
               will be a list of values in the order in which the user entered them
        :type  allow_multiple: bool

        :param default: the default value for optional options
        :type  default: None

        :param validate_func: if specified, this function will be applied to
               the user-specified value
        :type  validate_func: callable

        :param parse_func: if specified, this function will be applied to the
               user-specified value and its return will replace that value
        :type  parse_func: callable

        :return: instance representing the option
        :rtype:  Option
        """
        option = Option(name, description, required=required, allow_multiple=allow_multiple, aliases=aliases,
                        default=default, validate_func=validate_func, parse_func=parse_func)
        self.add_option(option)
        return option

    def create_flag(self, name, description, aliases=None):
        """
        Creates a new flag for this command. A flag is an argument that accepts
        no value from the user. If specified, the value will be True when it
        is passed to the command's underlying method. Flags are, by their
        nature, always optional.

        The given name must be unique across all options within this command.
        The option instance is returned and can be further edited except for
        its name.

        If the default parser is used by the command, the name must match the
        typical command line argument format, either:

        * -s - where s is a single character
        * --detail - where the argument is longer than one character

        The default parser will strip off the leading hyphens when it makes the
        values available to the command's method.

        :param name: trigger to set the flag
        :type  name: str

        :param description: user-readable text describing what the option does
        :type  description: str

        :param aliases: list of other argument names that may be used to set
               the value for this flag
        :type  aliases: list

        :return: instance representing the flag
        :rtype:  Flag
        """
        flag = Flag(name, description, aliases=aliases)
        self.add_option(flag)
        return flag

    def all_options(self):
        """
        Returns a single list of all options in the command, both directly
        added and in a group.

        :return: list of all Option instances in the command
        :rtype:  list
        """
        all_options = list(self.options)
        for g in self.option_groups:
            all_options += g.options
        return all_options

    def parse_arguments(self, prompt, input_args):
        """
        Parses the arguments passed into this command based on the configured
        options.

        :return: mapping of argument to value
        :rtype:  dict
        """

        # If a specific parser is specified, don't bother creating our own based
        # on added options. This is a bypass in case the user doesn't want to
        # use the provided abstraction.
        parser = self.parser

        if parser is None:
            parser = NoCatchErrorParser()

            for o in self.all_options():
                if isinstance(o, Flag):
                    action = 'store_true'
                else:
                    if o.allow_multiple:
                        action = 'append'
                    else:
                        action = 'store'

                name_list = [o.name]
                if o.aliases is not None:
                    name_list += o.aliases

                parser.add_option(dest=o.name, help=o.description, action=action, default=o.default, *name_list)

        options, remaining_args = parser.parse_args(input_args)

        # Apply the validation function for any options that define it
        validate_options = [o for o in self.all_options() if isinstance(o, Option) and o.validate_func is not None]

        for vo in validate_options:
            try:
                value = options.__dict__[vo.name]
                if value is not None:
                    vo.validate_func(value)
            except (ValueError, TypeError) as e:
                # Only catch the expected validation error types; bubble up others
                self.print_validation_error(prompt, vo, e)
                raise OptionValidationFailed()

        # Apply the parsing function for any options that define it
        parse_options = [o for o in self.all_options() if isinstance(o, Option) and o.parse_func is not None]

        for po in parse_options:
            # Do the same exception handling as for validate to let users
            # combine validate and parse into a single call
            try:
                old_value = options.__dict__[po.name]
                if old_value is not None:
                    new_value = po.parse_func(old_value)
                    options.__dict__[po.name] = new_value
            except (ValueError, TypeError) as e:
                # Only catch the expected validation error types; bubble up others
                self.print_validation_error(prompt, po, e)
                raise OptionValidationFailed()

        return remaining_args, options.__dict__

    def print_validation_error(self, prompt, option, exception):
        """
        Called when an option's validation function raises a validation error.
        This call should display a message describing the option that failed
        and any explanation as to why it did.

        :param option: option instance that failed validation
        :type  option: Option

        :param exception: exception that was raised from the validation function
        :type  exception: Exception
        """
        prompt.write(_('Validation failed for argument [%s]:') % option.name)
        try:
            prompt.write('  %s' % exception.args[0])
        # Python 2.4 and older does not have an 'args' attribute on Exception.
        # There is also no guarantee that 'args' (an iterable) will have a member.
        except (AttributeError, IndexError):
            pass

    def print_command_usage(self, prompt, missing_required=None, unexpected=None,
                            indent=0, step=2):
        """
        Prints the details of a command, including all options that can be
        specified to it.

        :param prompt: prompt instance to print the usage to
        :type  prompt: Prompt

        :param missing_required: list of required options that were not
                                 specified on an invocation of the CLI
        :type  missing_required: list of Option

        :param unexpected: list of specified option names that do not exist
                           on the command
        :type  unexpected: list of str

        :param indent: number of spaces to indent the command
        :type  indent: int

        :param step: number of spaces to increment the indent the command's options
        :type  step: int
        """

        prompt.write(_('%sCommand: %s') % (' ' * indent, self.name))
        prompt.write(_('%sDescription: %s') % (' ' * indent, self.description))
        if self.usage_description is not None:
            prompt.write(_('%sUsage: %s') % (' ' * indent, self.usage_description))

        def _assemble_triggers(option):
            all_triggers = [option.name]
            if option.aliases is not None:
                all_triggers += option.aliases
            all_triggers = ', '.join(all_triggers)
            return all_triggers

        def print_option_list(options):
            # Calculate the longest trigger up front so we know the alignment width
            max_width = reduce(lambda x, y: max(x, len(_assemble_triggers(y))), options, 0)
            for o in options:
                triggers = _assemble_triggers(o)

                # Prefix the description accordingly
                if o.required:
                    description = self.__class__.REQUIRED_OPTION_PREFIX + o.description
                else:
                    description = self.__class__.OPTIONAL_OPTION_PREFIX + o.description

                # Generate template
                template = '%s' + '%-' + str(max_width) + 's - %s'
                output = template % (' ' * (indent + step), triggers, description)
                wrapped_output = prompt.wrap(output, remaining_line_indent=(indent + step + max_width + 3))

                prompt.write(wrapped_output, skip_wrap=True)

        # Header
        if len(self.options) > 0 or len(self.option_groups) > 0:
            prompt.write('')
            prompt.write(_('Available Arguments:'))
            prompt.write('')

        # Print any command-level options
        if len(self.options) > 0:
            print_option_list(self.options)

        if len(self.options) > 0 and len(self.option_groups) > 0:
            prompt.write('')

        # Handle any option groups on the command
        if len(self.option_groups) > 0:
            for group in self.option_groups:
                prompt.write(group.name)

                if group.description is not None:
                    wrapped_description = prompt.wrap(' ' * (indent + step) + group.description, remaining_line_indent=(indent + step))
                    prompt.write(wrapped_description, skip_wrap=True)
                    prompt.write('')

                print_option_list(group.options)
                prompt.write('')

        if missing_required:
            prompt.write(_('The following options are required but were not specified:'))
            for r in missing_required:
                prompt.write('%s%s' % (' ' * (indent + step), r.name))

        if unexpected:
            prompt.write(_('The following options were specified but do not exist on the command:'))
            for u in unexpected:
                prompt.write('%s%s' % (' ' * (indent + step), u))


class Section(object):
    """
    Represents a division of commands in the CLI. Sections may contain other
    sections, which creates a string of arguments used to get to a command
    (think namespaces).
    """
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.subsections = {}
        self.commands = {}

    def __str__(self):
        return 'Section [%s]' % self.name

    def add_subsection(self, section):
        """
        Adds another node to the CLI tree. Users will be able to specify the
        given name when specifying this section. Doing so will recurse into the
        subsection's subtree to continue parsing for other subsections or commands.

        :param section: section instance to add
        :type  section: Section
        """
        self.verify_new_structure(section.name)
        self.subsections[section.name] = section

    def add_command(self, command):
        """
        Adds a command that may be executed in this section (in other words, a
        leaf in this node of the CLI tree). Any arguments that were specified
        after the path used to identify this command will be passed to the
        command's execution itself.

        :param command: command object to add
        :type  command: Command
        """
        self.verify_new_structure(command.name)
        self.commands[command.name] = command

    def create_command(self, name, description, method, usage_description=None, parser=None):
        """
        Creates a new command in this section. The given name must be
        unique across all commands and subsections within this section.
        The command instance is returned and can be further edited except
        for its name.

        Commands created in this fashion do not need to be added to this
        section through the add_command method.

        :param name: trigger that will cause this command to run
        :type  name: str

        :param description: user-readable text describing what happens when
               running this command; displayed to users in the usage output
        :type  description: str

        :param method: method that will be invoked when this command is run
        :type  method: function

        :param usage_description: optional extra text that is only displayed
               when viewing the full usage of this command
        :type  usage_description: str or None

        :param parser: if specified, the remaining arguments to this command
               as specified by the user will be passed to this object to
               be handled; the results will be sent to the command's method
        :type  parser: OptionParser

        :return: instance representing the newly added command
        :rtype:  Command
        """
        command = Command(name, description, method, usage_description=usage_description, parser=parser)
        self.add_command(command)
        return command

    def create_subsection(self, name, description):
        """
        Creates a new subsection in this section. The given name must be unique
        across all commands and subsections within this section. The section
        instance is returned and can be further edited except for its name.

        Sections created in this fashion do not need to be added to this section
        through the add_section method.

        :param name: identifies the section
        :type  name: str

        :param description: user-readable text describing the contents of this
               subsection
        :type  description: str

        :return: instance representing the newly added section
        :rtype:  Section
        """
        subsection = Section(name, description)
        self.add_subsection(subsection)
        return subsection

    def find_subsection(self, name):
        """
        Returns the subsection of this section with the given name.

        :param name: required; name of the subsection to find
        :type  name: string

        :return: section object for the matching subsection if it exists; None otherwise
        :rtype:  Section
        """
        if name in self.subsections:
            return self.subsections[name]
        else:
            return None

    def find_command(self, name):
        """
        Returns the command under this section with the given name.

        :param name: required; name of the command to find
        :type  name: string

        :return: command object for the matching command if it exists; None otherwise
        :rtype:  Command
        """
        if name in self.commands:
            return self.commands[name]
        else:
            return None

    def remove_subsection(self, name):
        """
        Removes the subsection with the given name. If there is no subsection
        with the given name, this call does nothing (no error is raised).

        :param name: name of the section when it was added
        :type  name: str

        :return: subsection instance if one was removed; None if it didn't exist
        :rtype:  Section
        """
        return self.subsections.pop(name, None)

    def remove_command(self, name):
        """
        Removes the command with the given name. If there is no command with
        the given name, this call does nothing (no error is raised).

        :param name: name of the command when it was added
        :type  name: str

        :return: command instance if one was removed; None if it didn't exist
        :rtype:  Command
        """
        return self.commands.pop(name, None)

    def print_section(self, prompt, indent=0, step=2):
        """
        Prints the direct children of a single section; this call will not
        recurse into the children and print their hierarchy.

        :param prompt: required; prompt instance to print to
        :type  prompt: Prompt

        :param indent: number of spaces to indent each section
        :type  indent: int

        :param step: number of spaces to increment the indent on each iteration
                     into a section
        :type  step: int
        """
        launch_script = os.path.basename(sys.argv[0])
        prompt.write(_('Usage: %s [SUB_SECTION, ..] COMMAND') % launch_script)

        if self.description:
            prompt.write(_('Description: %s') % self.description)

        prompt.write('')

        if len(self.subsections) > 0:
            max_width = reduce(lambda x, y: max(x, len(y)), self.subsections, 0)
            template = '%s' + '%-' + str(max_width) + 's - %s'

            prompt.write(_('Available Sections:'))
            for subsection in sorted(self.subsections.values(), key=lambda x: x.name):
                wrapped_description = prompt.wrap(subsection.description, remaining_line_indent=(indent + step + max_width + 3))
                prompt.write(template % (' ' * (indent + step), subsection.name, wrapped_description), skip_wrap=True)

        if len(self.subsections) > 0 and len(self.commands) > 0:
            prompt.write('')

        if len(self.commands) > 0:
            max_width = reduce(lambda x, y: max(x, len(y)), self.commands, 0)
            template = '%s' + '%-' + str(max_width) + 's - %s'

            prompt.write(_('Available Commands:'))
            for command in sorted(self.commands.values(), key=lambda x: x.name):
                wrapped_description = prompt.wrap(command.description, remaining_line_indent=(indent + step + max_width + 3))
                prompt.write(template % (' ' * (indent + step), command.name, wrapped_description), skip_wrap=True)

    def verify_new_structure(self, name):
        """
        Integrity check to validate that the CLI has not been configured with an
        entity (subsection or command) with the given name.

        :param name: name of the subsection/command to look for
        :type  name: string

        :raise InvalidStructure: if there is an entity with the given name
        """
        # Make sure there isn't already a subsection with the same name
        if name in self.subsections:
            raise InvalidStructure()

        # Make sure there isn't already a command with the same name
        if name in self.commands:
            raise InvalidStructure()


class Cli(object):
    """
    Representation of the CLI being created. Coders should create an instance of
    this class as the basis for the CLI. At that point, calling add_* methods
    will return the nodes/leaves of the CLI tree to further manipulate and
    create the desired CLI hierarchy.
    """

    def __init__(self, prompt=None):
        self.prompt = prompt or Prompt()

        # Hidden, "special" Section that represents the base of the command structure;
        # this simplifies calls into the recursive methods
        self.root_section = Section('', '')

    def add_section(self, section):
        """
        Adds a new section to the CLI. Users will be able to specify the given
        name when specifying this section. Doing so will recurse into the
        section's subtree to continue parsing for other subsections or commands.

        :param section: section instance to add
        :type  section: Section
        """
        self.root_section.add_subsection(section)

    def add_command(self, command):
        """
        Adds a command that may be executed in this section (in other words, a
        leaf in this node of the CLI tree). Any arguments that were specified
        after the path used to identify this command will be passed to the
        command's execution itself.

        :param command: command object to add
        :type  command: Command
        """
        self.root_section.add_command(command)

    def create_section(self, name, description):
        """
        Creates a new subsection at the root of the CLI. The given name must be
        unique across all commands and subsections within this section. The
        section instance is returned and can be further edited except for its name.

        Sections created in this fashion do not need to be added  through the
        add_section method.

        :param name: identifies the section
        :type  name: str

        :param description: user-readable text describing the contents of this
               subsection
        :type  description: str

        :return: instance representing the newly added section
        :rtype:  Section
        """
        subsection = Section(name, description)
        self.add_section(subsection)
        return subsection

    def create_subsection(self, name, description):
        """
        Syntactic sugar method that functions identical to create_section.

        :rtype: Section
        """
        return self.create_section(name, description)

    def create_command(self, name, description, method, usage_description=None, parser=None):
        """
        Creates a new command in this section. The given name must be
        unique across all commands and subsections within this section.
        The command instance is returned and can be further edited except
        for its name.

        Commands created in this fashion do not need to be added to this
        section through the add_command method.

        :param name: trigger that will cause this command to run
        :type  name: str

        :param description: user-readable text describing what happens when
               running this command; displayed to users in the usage output
        :type  description: str

        :param method: method that will be invoked when this command is run
        :type  method: function

        :param usage_description: optional extra text that is only displayed
               when viewing the full usage of this command
        :type  usage_description: str or None

        :param parser: if specified, the remaining arguments to this command
               as specified by the user will be passed to this object to
               be handled; the results will be sent to the command's method
        :type  parser: OptionParser

        :return: instance representing the newly added command
        :rtype:  Command
        """
        command = Command(name, description, method, usage_description=usage_description, parser=parser)
        self.add_command(command)
        return command

    def find_section(self, name):
        """
        Returns the subsection of this section with the given name.

        :param name: required; name of the subsection to find
        :type  name: string

        :return: section object for the matching subsection if it exists; None otherwise
        :rtype:  Section
        """
        return self.root_section.find_subsection(name)

    def find_subsection(self, name):
        """
        Syntactic sugar method that functions identical to find_section.
        """
        return self.find_section(name)

    def find_command(self, name):
        """
        Returns the command under this section with the given name.

        :param name: required; name of the command to find
        :type  name: string

        :return: command object for the matching command if it exists; None otherwise
        :rtype:  Command
        """
        return self.root_section.find_command(name)

    def remove_section(self, name):
        """
        Removes the section with the given name. If no section exists with that
        name, this call has no effect (no error is raised).

        :param name: name of the section when it was added
        :type  name: str

        :return: subsection instance of one was removed; None otherwise
        :rtype:  Section
        """
        return self.root_section.remove_subsection(name)

    def remove_subsection(self, name):
        """
        Syntactic sugar method that functions identical to remove_section.
        """
        return self.remove_section(name)

    def remove_command(self, name):
        """
        Removes the command with the given name. If no command exists with that
        name, this call has no effect (no error is raised).

        :param name: name of the command to remove
        :type  name: str
        """
        return self.root_section.remove_command(name)

    def run(self, args):
        """
        Driver for the CLI. The specified arguments will be parsed to determine
        which command to execute, as well as any arguments to that command's
        execution. After assembling the CLI using the add_* calls, this method
        should be run to do the actual work.

        :param args: defines the command being invoked and any arguments to it
        :type  args: list

        :return: exit code as indicated by the command that is executed,
                 suitable for using as the executable exit code
        :rtype:  int
        """
        command_or_section, remaining_args = self._find_closest_match(self.root_section, args)

        if command_or_section is None:
            self.root_section.print_section(self.prompt)
            return os.EX_USAGE
        elif isinstance(command_or_section, Section):
            command_or_section.print_section(self.prompt)
            return os.EX_USAGE
        else:
            try:
                exit_code = command_or_section.execute(self.prompt, remaining_args)

                # Default handling; if no code specified, assume ok
                if exit_code is None:
                    exit_code = os.EX_OK

                return exit_code
            except CommandUsage as e:
                command_or_section.print_command_usage(
                    self.prompt, missing_required=e.missing_options,
                    unexpected=e.unexpected_options)
                return os.EX_USAGE

    def print_cli_map(self, indent=-2, step=2, show_options=False, section_color=None, command_color=None):
        """
        Prints the structure of the CLI in a tree-like structure to indicate
        section ownership.

        :param indent: number of spaces to indent each section
        :type  indent: int

        :param step: number of spaces to increment the indent on each iteration
                     into a section
        :type  step: int

        :param show_options: if true, command options will be displayed; defaults
               to false
        :type  show_options: bool

        :param section_color: if specified, section names will be highlighted
                              with this color
        :type  section_color: str

        :param command_color: if specified, command names will be highlighted
                              with this color
        :type  command_color: str
        """
        self._recursive_print_cli_map(self.root_section, indent=indent, step=step, show_options=show_options,
                                      section_color=section_color, command_color=command_color)

    def _recursive_print_cli_map(self, base_section, indent=-2, step=2, show_options=False,
                                 section_color=None, command_color=None):
        """
        Prints the contents of a section and all of its children (subsections
        and commands).
        """
        # Need a way to not print the root section of the CLI, which doesn't
        # represent an actual user section, so a ghetto check is to make sure
        # the name isn't blank
        if base_section.name != '':
            wrapped_description = self.prompt.wrap(base_section.description, remaining_line_indent=(len(base_section.name) + 2 + indent))
            highlighted_name = self.prompt.color(base_section.name, section_color)
            self.prompt.write('%s%s: %s' % (' ' * indent, highlighted_name, wrapped_description), skip_wrap=True)

        if len(base_section.commands) > 0:
            max_width = reduce(lambda x, y: max(x, len(y)), base_section.commands, 0) + 1 # +1 for the : later

            if section_color is not None:
                max_width += len(section_color)
                max_width += len(self.prompt.normal_color)

            template = '%s%-' + str(max_width) + 's %s'

            for command in sorted(base_section.commands.values()):
                highlighted_name = self.prompt.color(command.name, command_color)
                self.prompt.write(template % (' ' * (indent + step), highlighted_name + ':', command.description))

                if show_options and len(command.options) > 0:
                    for o in command.options:
                        highlighted_name = self.prompt.color(o.name, command_color)
                        self.prompt.write('%s%s: %s' % (' ' * (indent + (step * 2)), highlighted_name, o.description))

        if len(base_section.subsections) > 0:
            for subsection in sorted(base_section.subsections.values()):
                self._recursive_print_cli_map(subsection, indent=(indent + step), step=step,
                                              section_color=section_color, command_color=command_color)

        # Only put a blank line between highest level sections. This may not be
        # perfect for deep nesting of sections, but I think in most cases this
        # makes sense
        if indent <= 0:
            self.prompt.write('')

    def _find_closest_match(self, base_section, args):
        """
        Searches the CLI structure for the command that matches the path in the
        given arguments. If no command is found, the closest matching section
        is returned.

        For example, given the command: foo bar baz
        - If baz is a command in the correct location, the baz Command instance
          is returned
        - If baz is not a valid command but foo->bar is a valid section
          hierarchy, the bar Section instance is returned
        - If bar is not a valid section but foo is, the foo Section instance
          is returned

        Also returned are the remaining arguments that were not parsed.
        For example: foo bar baz --k v
        - If baz is a valid command, the second entry in the returned tuple will
          be a list of ['--k', 'v']
        - If baz is not a valid command but bar is a valid section, the returned
          list of args will be ['baz', '--k', 'v']
        - If bar is not a valid section, the args returned are
          ['bar', 'baz', '--k', 'v']

        :param base_section: root section from which to begin the search
        :type  base_section: Section

        :param args: list of arguments to use as the path to the command to search
        :type  args: list

        :return: tuple of the closest matching command or section based on the
                 argument list
        :rtype:  Command, list or Section, list
        """

        # If we've recursed so much that we ran out of arguments, we haven't
        # found a command yet, so we return the deepest section we found
        if len(args) is 0:
            return base_section, args[1:]

        find_me = args[0]

        # See if the argument represents a command and return that
        command = base_section.find_command(find_me)
        if command is not None:
            return command, args[1:]

        # Find the subsection
        subsection = base_section.find_subsection(find_me)
        if subsection is not None:

            # Don't recurse if we're at a section and the next argument is an option
            if len(args) > 1 and args[1].startswith('-'):
                return subsection, args[1:]

            found_in_subsection, sub_args = self._find_closest_match(subsection, args[1:])
            return found_in_subsection, sub_args

        # If we got this far, we didn't find a matching command or subsection,
        # so return where we are as the closest match
        return base_section, args # even include the bad one in the args

# -- arg parsers --------------------------------------------------------------

class UnknownArgsParser(object):
    """
    Duck-typed parser that can be passed to a Command. This implementation won't
    expect all of the possible options to be enumerated ahead of time. This is
    useful for any server-plugin-related call where the arguments will vary
    based on the type of plugin being manipulated.

    While this instance will support undefined options and flags, it is possible
    to provide a list of required options. These will factor into the usage
    display and be validated
    """

    class Unparsable(Exception): pass

    class MissingRequired(Exception): pass

    def __init__(self, prompt, path, required_options=None, exit_on_abort=True):
        """
        @param prompt: prompt instance to write the usage to
        @type  prompt: Prompt

        @param path: section/command path to reach the command currently executing
        @type  path: str

        @param required_options: list of tuples of option name to description
        @type  required_options: list

        @param exit_on_abort: flag that indicates how to proceed if the argument
               list cannot be parsed or is missing required values; if true,
               sys.exit will be called with the appropriate exit code; set to
               false during unit tests to cause an exception to raise instead
        @type  exit_on_abort: bool
        """

        self.prompt = prompt
        self.path = path
        self.required_options = required_options or []
        self.exit_on_abort = exit_on_abort

    def parse_args(self, args):
        """
        Parses arguments where the list of possible arguments isn't known ahead
        of time. This method will parse through the argument list and attempt to
        resolve the arguments into key/value pairs.

        The keys will be the name of the argument with any leading hyphens removed.
        The value will be one of three possibilties:

        * The string representation of the value immediately following it (common case)
        * The boolean True if no value or another argument definition follows it
        * A list of strings if the argument is specified more than once

        The argument/value pairs are returned as a dictionary. In the event an empty
        list of arguments is supplied, an empty dictionary is returned.

        @param args: tuple of arguments passed to the command
        @type  args: tuple

        @return: dictionary of argument name to value(s); see above for details
        @rtype:  dict
        """
        def arg_name(arg):
            if arg.startswith('--'):
                return arg[2:]
            elif arg.startswith('-'):
                return arg[1:]
            else:
                return None

        parsed = {}
        required_names = [r[0] for r in self.required_options]

        index = 0 # this won't necessarily step by 1 each time, so don't use something like enumerate
        while index < len(args):
            item = args[index]

            # The required names use the option name directly (with the hyphens)
            # so do the check here
            if item in required_names:
                required_names.remove(item)

            name = arg_name(item)

            if name is None or name in ('h', 'help'):
                self.usage()
                self.abort(exception_class=self.Unparsable)

            # If we're at the end there is nothing after it, it's also a flag.
            if (index + 1) == len(args):
                parsed[name] = True
                index += 1
                continue

            # If the next value is another argument, the current is a flag.
            if args[index + 1].startswith('-'):
                parsed[name] = True
                index += 1
                continue

            # If we're here, the next in the list is the value for the argument.
            value = args[index + 1]

            # If the argument already has a value, convert the value to a list and
            # add in the new one (preserving order).
            if name in parsed:
                if not isinstance(parsed[name], list):
                    parsed[name] = [parsed[name]]
                parsed[name].append(value)
            else:
                parsed[name] = value

            index += 2 # to take into account the value we read

        # If all of the required options haven't been removed yet, we're
        # missing at least one.
        if len(required_names) > 0:
            self.usage()
            self.abort(exception_class=self.MissingRequired)

        # The CLI is expecting the return result of OptionParser, which wraps
        # the dict in Values, so we do that here.
        return Values(parsed), []

    def usage(self):
        launch_script = os.path.basename(sys.argv[0])
        self.prompt.write(_('Usage: %s %s [OPTION, ..]') % (launch_script, self.path))
        self.prompt.write('')

        m = _('Valid options follow one of the following formats:')
        self.prompt.write(m)

        self.prompt.write(_('  --<option> <value>'))
        self.prompt.write(_('  --<flag>'))
        self.prompt.write('')

        if len(self.required_options) > 0:
            self.prompt.write(_('The following options are required:'))

            max_width = reduce(lambda x, y: max(x, len(y[0])), self.required_options, 0)
            template = '  %-' + str(max_width) + 's - %s'
            for r, d in self.required_options:
                self.prompt.write(template % (r, d))

    def abort(self, exception_class=None):
        """
        Called when the arguments are unparsable or missing. The actual
        OptionParser implementation calls sys.exit on a failed parse, so
        this method, by default, does the same (this is actually a cleaner
        implementation since it uses the EX_USAGE code where as OptionParser
        just exits with 2, but I digress).

        The instance variable exit_on_abort controls the behavior of this call.
        That variable should be set to false to avoid the sys.exit call in the
        case of a unit test.
        """
        if self.exit_on_abort:
            sys.exit(os.EX_USAGE)
        else:
            raise exception_class('Parsing aborted')


class PassThroughParser(object):
    """
    Duck-typed parser that can be passed to a Command. This implementation won't
    attempt any parsing or validation whatsoever on the command arguments.
    Instead, they are simply returned as a list and will be unpacked for the
    call into the command's method.
    """

    def __init__(self, prompt, path):
        """
        @param prompt: prompt instance to write the usage to
        @type  prompt: Prompt

        @param path: section/command path to reach the command currently executing
        @type  path: str
        """
        self.prompt = prompt
        self.path = path

    def parse_args(self, args):
        return args, {}

    def usage(self):
        launch_script = os.path.basename(sys.argv[0])
        self.prompt.write(_('Usage: %s %s [OPTION, ..]') % (launch_script, self.path))
