#!/usr/bin/python
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.


from optparse import OptionParser


# -- exceptions ----------------------------------------------------------------------

class InvalidStructure(Exception):
    """
    Indicates the programmer attempted to assemble a CLI with sections/commands that would
    conflict with each other (likely duplicates).
    """
    pass

class CommandUsage(Exception):
    """
    Indicates the command parameters were incorrect. If the usage error was the lack of
    required parameters, all required parameters that were missing can be specified.

    @param missing_options: optional list of options that are required but missing
    @type  missing_options: list of L{Option}
    """
    def __init__(self, missing_options=None):
        self.missing_options = missing_options

# -- classes ----------------------------------------------------------------------

class NoCatchErrorParser(OptionParser):
    """
    OptionParser's default behavior for handling errors is to print the output and exit.
    I'd rather go through the rest of the CLI's output methods, so change this behavior to
    throw my exception instead.
    """
    def exit(self, status=0, msg=None):
        raise CommandUsage(None)

class Option():
    """
    Represents an input to a command, either optional or required.
    """
    def __init__(self, name, description, required=True):
        self.name = name
        self.description = description
        self.required = required

    def __str__(self):
        return 'Option [%s]' % self.name

class Flag(Option):
    """
    Specific form of an option that does not take a value; it is meant to be either included
    in the command or excluded.
    """
    def __init__(self, name, description):
        Option.__init__(self, name, description, False)
    
class Command():
    """
    Represents something that should be executed by the CLI. These nodes will be leaves
    in the CLI tree. Each command is tied to a single python method and will invoke that
    method with whatever arguments follow it.
    """
    def __init__(self, name, description, method):
        self.name = name
        self.description = description
        self.method = method
        self.options = []

    def __str__(self):
        return 'Command [%s]' % self.name

    def execute(self, args):
        """
        Executes this command, passing the remaining arguments into OptParse to process.

        @param args: any arguments that remained after parsing the command line to determine
                     the command to execute; these are considered arguments to the command's
                     execution itself
        @type  args: list of strings
        """

        # Parse the command arguments into a dictionary
        arg_dict = self._parse_arguments(args)

        # Make sure all of the required arguments have been specified
        missing_required = [o for o in self.options if o.required and
                                                       (not arg_dict.has_key(o.name) or
                                                       arg_dict[o.name] is None)]
        if len(missing_required) > 0:
            raise CommandUsage(missing_required)

        # Flag entries that are not specified are parsed as None, but I'd rather them
        # explicitly be set to false. Iterate through each flag explicitly setting the
        # value to false if it was not specified
        for o in self.options:
            if isinstance(o, Flag):
                if arg_dict[o.name] is None:
                    arg_dict[o.name] = False

        self.method(**arg_dict)

    def add_option(self, option):
        """
        Adds an option that can be specified when executing this command. When executing the
        command, the user specified arguments to the command are parsed according to options
        specified in this fashion.

        @param option: option (or flag) to add to the command
        @type  option: L{Option} or L{Flag}
        """
        self.options.append(option)

    def _parse_arguments(self, args):
        """
        Parses the arguments passed into this command based on the configured options.

        @return: mapping of argument to value
        @rtype:  dict
        """
        parser = NoCatchErrorParser()

        for o in self.options:
            if isinstance(o, Flag):
                action = 'store_true'
            else:
                action = 'store'

            parser.add_option(o.name, dest=o.name, help=o.description, action=action)

        options, remaining_args = parser.parse_args(args)
        return dict(options.__dict__)
            
class Section():
    """
    Represents a division of commands in the CLI. Sections may contain other sections, which
    creates a string of arguments used to get to a command (think namespaces).
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
        Adds another node to the CLI tree. Users will be able to specify the given name when
        specifying this section. Doing so will recurse into the subsection's subtree to
        continue parsing for other subsections or commands.

        @param section: section instance to add
        @type  section: L{Section}
        """
        self._verify_new_structure(section.name)
        self.subsections[section.name] = section

    def add_command(self, command):
        """
        Adds a command that may be executed in this section (in other words, a leaf in this
        node of the CLI tree). Any arguments that were specified after the path used to
        identify this command will be passed to the command's execution itself.

        @param command: command object to add
        @type  command: L{Command}
        """
        self._verify_new_structure(command.name)
        self.commands[command.name] = command

    def find_subsection(self, name):
        """
        Returns the subsection of this section with the given name.

        @param name: required; name of the subsection to find
        @type  name: string

        @return: section object for the matching subsection if it exists; None otherwise
        @rtype:  L{Section} or None
        """
        if self.subsections.has_key(name):
            return self.subsections[name]
        else:
            return None

    def find_command(self, name):
        """
        Returns the command under this section with the given name.

        @param name: required; name of the command to find
        @type  name: string

        @return: command object for the matching command if it exists; None otherwise
        @rtype:  L{Command} or None
        """
        if self.commands.has_key(name):
            return self.commands[name]
        else:
            return None

    def _verify_new_structure(self, name):
        """
        Integrity check to validate that the CLI has not been configured with an entity
        (subsection or command) with the given name.

        @param name: name of the subsection/command to look for
        @type  name:  string

        @raise InvalidStructure: if there is an entity with the given name
        """
        # Make sure there isn't already a subsection with the same name
        if self.subsections.has_key(name):
            raise InvalidStructure()

        # Make sure there isn't already a command with the same name
        if self.commands.has_key(name):
            raise InvalidStructure()

class Cli():
    """
    Representation of the CLI being created. Coders should create an instance of this class
    as the basis for the CLI. At that point, calling add_* methods will return the nodes/leaves
    of the CLI tree to further manipulate and create the desired CLI hierarchy.
    """

    def __init__(self):
        # Hidden, "special" Section that represents the base of the command structure;
        # this simplifies calls into the recursive methods
        self.root_section = Section('', '')

    def add_section(self, section):
        """
        Adds a new section to the CLI. Users will be able to specify the given name when
        specifying this section. Doing so will recurse into the section's subtree to
        continue parsing for other subsections or commands.

        @param section: section instance to add
        @type  section: L{Section}
        """
        self.root_section.add_subsection(section)

    def run(self, args):
        """
        Driver for the CLI. The specified arguments will be parsed to determine which command
        to execute, as well as any arguments to that command's execution. After assembling
        the CLI using the add_* calls, this method should be run to do the actual work.

        @param args: defines the command being invoked and any arguments to it
        @type  args: list of string
        """
        command_or_section, remaining_args = self._find_closest_match(self.root_section, args)

        if command_or_section is None:
            self._print_section(self.root_section)
        elif isinstance(command_or_section, Section):
            self._print_section(command_or_section)
        else:
            try:
                command_or_section.execute(remaining_args)
            except CommandUsage, e:
                self._print_command_usage(command_or_section, missing_required=e.missing_options)

    def print_cli_map(self, indent=-4, step=4):
        """
        Prints the structure of the CLI in a tree-like structure to indicate section ownership.

        @param indent: number of spaces to indent each section
        @type  indent: int

        @param step: number of spaces to increment the indent on each iteration into a section
        @type  step: int
        """
        self._recursive_print_section(self.root_section, indent=indent, step=step)

    def _recursive_print_section(self, base_section, indent=-4, step=4):
        """
        Prints the contents of a section and all of its children (subsections and commands).

        @param indent: number of spaces to indent each section
        @type  indent: int

        @param step: number of spaces to increment the indent on each iteration into a section
        @type  step: int        
        """
        # Need a way to not print the root section of the CLI, which doesn't represent
        # an actual user section, so a ghetto check is to make sure the name isn't blank
        if base_section.name != '':
            print('%s%s: %s' % (' ' * indent, base_section.name, base_section.description))

        if len(base_section.commands) > 0:
            for command in sorted(base_section.commands.values()):
                print('%s%s - %s' % (' ' * (indent + step), command.name, command.description))
                if len(command.options) > 0:
                    for o in command.options:
                        print('%s%s - %s' % (' ' * (indent + (step * 2)), o.name, o.description))

        if len(base_section.subsections) > 0:
            for subsection in sorted(base_section.subsections.values()):
                self._recursive_print_section(subsection, indent=(indent + step), step=step)

    def _print_section(self, section, indent=0, step=4):
        """
        Prints the direct children of a single section; this call will not recurse into the
        children and print their hierarchy.

        @param section: required; section to print
        @type  section: L{Section}

        @param indent: number of spaces to indent each section
        @type  indent: int

        @param step: number of spaces to increment the indent on each iteration into a section
        @type  step: int
        """
        if section.name != '':
            print('%s%s' % (' ' * indent, section.description))
        else:
            print('Usage:')

        if len(section.commands) > 0:
            for command in sorted(section.commands.values()):
                print('%s%s - %s' % (' ' * (indent + step), command.name, command.description))

        if len(section.subsections) > 0:
            for subsection in sorted(section.subsections.values()):
                print('%s%-10s: %s' % (' ' * (indent + step), subsection.name, subsection.description))

    def _print_command_usage(self, command, missing_required=None, indent=0, step=4):
        """
        Prints the details of a command, including all options that can be specified to it.

        @param command: command to print
        @type  command: L{Command}

        @param missing_required: list of required options that were not specified on an
                                 invocation of the CLI
        @type  missing_required: list of L{Option}

        @param indent: number of spaces to indent the command
        @type  indent: int

        @param step: number of spaces to increment the indent the command's options
        @type  step: int
        """

        print('%s%s: %s' % (' ' * indent, command.name, command.description))

        if len(command.options) > 0:
            for o in command.options:
                if o.required:
                    print('%s%s - %s (required)' % (' ' * (indent + step), o.name, o.description))
                else:
                    print('%s%s - %s' % (' ' * (indent + step), o.name, o.description))

        if missing_required:
            print('')
            print('The following options are required but were not specified:')
            for r in missing_required:
                print('%s%s' % (' ' * (indent + step), r.name))

    def _find_closest_match(self, base_section, args):
        """
        Searches the CLI structure for the command that matches the path in the given arguments.
        If no command is found,

        @param base_section: root section from which to begin the search
        @type  base_section: L{Section}

        @param args: list of arguments to use as the path to the command to search
        @type  args: list

        @return: tuple of the closest matching command or section based on the argument list
        @rtype:  L{Command}, list or L{Section}, list
        """

        # If we've recursed so much that we ran out of arguments, we haven't found a command yet,
        # so we return the deepest section we found
        if len(args) == 0:
            return base_section, args[1:]

        find_me = args[0]

        # See if the argument represents a command and return that
        command = base_section.find_command(find_me)
        if command is not None:
            return command, args[1:]

        # If we're not at a command yet, recurse into the next level of subsections
        found_in_subsection = None
        sub_args = None

        # Find the subsection
        subsection = base_section.find_subsection(find_me)
        if subsection is not None:
            found_in_subsection, sub_args = self._find_closest_match(subsection, args[1:])

        return found_in_subsection, sub_args
