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
from builtins import object

from gettext import gettext as _
import logging
import os
import sys

import pkg_resources

# -- constants ----------------------------------------------------------------

_LOG = logging.getLogger(__name__)

PRIORITY_VAR = 'PRIORITY'
DEFAULT_PRIORITY = 5

# -- client functionality -----------------------------------------------------

def priority(value=DEFAULT_PRIORITY):
    """
    Use this to put a decorator on the initialize method for an extension to
    will set that extension's priority level.

    :param value: priority value
    :type  value: int

    :return: decorator
    """
    def decorator(f):
        setattr(f, PRIORITY_VAR, value)
        return f
    return decorator

# -- loading ------------------------------------------------------------------

class ExtensionsManager(object):

    def __init__(self, init_arg_list=None, init_kwargs_list=None):
        self.init_arg_list = init_arg_list or []
        self.init_kwargs_list = init_kwargs_list or {}
        self.extension_loaders = []

    def add_loader(self, extension_loader):
        self.extension_loaders.append(extension_loader)

    def load(self):

        # Load packs from all loading schemes
        descriptors = []
        for loader in self.extension_loaders:
            found_descriptors = loader.find_extension_descriptors()
            descriptors.extend(found_descriptors)

        # Sort each pack by priority
        descriptors.sort()

        # Best effort to load all extensions, describing all errors at once
        error_descriptors = []
        for descriptor in descriptors:
            try:
                self._initialize_extension(descriptor)
            except ExtensionLoaderException:
                # Do a best-effort attempt to load all extensions. If any fail,
                # the cause will be logged by _load_pack. This method should
                # continue to load extensions so all of the errors are logged.
                error_descriptors.append(descriptor)

        if len(error_descriptors) > 0:
            raise LoadFailed(error_descriptors)

    def _initialize_extension(self, descriptor):
        descriptor.init_method(*self.init_arg_list, **self.init_kwargs_list)


class ExtensionDescriptor(object):

    def __init__(self, name, init_method, priority):
        super(ExtensionDescriptor, self).__init__()
        self.name = name
        self.init_method = init_method
        self.priority = priority

    def __lt__(self, other):
        """
        Orders by priority first, then ascending by name.
        """
        if self.priority != other.priority:
            return self.priority < other.priority
        else:
            return self.name < other.name

# -- loaders ------------------------------------------------------------------

class BaseExtensionsLoader(object):

    def find_extension_descriptors(self):
        raise NotImplementedError()


class DirectoryExtensionsLoader(BaseExtensionsLoader):

    def __init__(self, extensions_dir, init_module_name, init_function_name):
        super(DirectoryExtensionsLoader, self).__init__()
        self.extensions_dir = extensions_dir
        self.init_module_name = init_module_name
        self.init_function_name = init_function_name

    def find_extension_descriptors(self):
        """

        :return: description of all extensions found in the directory
        :rtype:  list of ExtensionDescriptor
        """

        # Add the extensions directory to the path so each extension can be
        # loaded as a python module
        if self.extensions_dir not in sys.path:
            sys.path.append(self.extensions_dir)

        # Load the modules that contain the init method
        descriptors = []

        extension_package_name = sorted(os.listdir(self.extensions_dir))
        for name in extension_package_name:
            if name.startswith('.'):
                continue

            descriptor = self._load_extension_descriptor(name)
            descriptors.append(descriptor)

        return descriptors

    def _load_extension_descriptor(self, extension_package_name):

        # Check for the file's existence first to ease error handling
        ext_mod_filename = os.path.join(self.extensions_dir,
                                        extension_package_name,
                                        self.init_module_name + '.py')
        if not os.path.exists(ext_mod_filename):
            raise InitializeFileNotFound

        # Figure out the full package name for the module and import it.
        try:
            ext_module = __import__('%s.%s' % (extension_package_name, self.init_module_name))
        except Exception:
            raise ImportFailed(extension_package_name)

        # Get a handle on the initialize function
        try:
            init_module = getattr(ext_module, self.init_module_name)
            init_func = getattr(init_module, self.init_function_name)
        except AttributeError as e:
            raise NoInitFunction()

        # Load the priority
        try:
            priority = int(getattr(ext_module, PRIORITY_VAR))
        except AttributeError:
            # Priority is optional; the default is applied here
            priority = DEFAULT_PRIORITY

        descriptor = ExtensionDescriptor(extension_package_name, init_func, priority)
        return descriptor


class EntryPointLoader(BaseExtensionsLoader):

    def __init__(self, entry_point_name):
        super(EntryPointLoader, self).__init__()
        self.entry_point_name = entry_point_name

    def find_extension_descriptors(self):
        descriptors = []
        for entry_point in pkg_resources.iter_entry_points(self.entry_point_name):
            init_func = entry_point.load()
            priority = getattr(init_func, PRIORITY_VAR, DEFAULT_PRIORITY)
            descriptor = ExtensionDescriptor(entry_point.name, init_func, priority)
            descriptors.append(descriptor)

        return descriptors

# -- exceptions ---------------------------------------------------------------

class ExtensionLoaderException(Exception):
    """ Base class for all loading-related exceptions. """
    pass


class LoadFailed(ExtensionLoaderException):
    """
    Raised if one or more of the extensions failed to load. All failed
    descriptors will be listed in the exception, however the causes are logged
    rather than carried in this exception.
    """
    def __init__(self, failed_descriptors):
        ExtensionLoaderException.__init__(self)
        self.failed_descriptors = failed_descriptors

    def __str__(self):
        failed_names = [d.name for d in self.failed_descriptors]
        return _('The following extension packs failed to load: [%s]' % ', '.join(failed_names))

# DirectoryExtensionsLoader Exceptions ----------

class ImportFailed(ExtensionLoaderException):
    def __init__(self, module_name):
        ExtensionLoaderException.__init__(self)
        self.module_name = module_name

class NoInitFunction(ExtensionLoaderException): pass

class InitializeFileNotFound(ExtensionLoaderException):

    def __init__(self, filename):
        ExtensionLoaderException.__init__(self)
        self.filename = filename

    def __str__(self):
        return _('Extension file not found: [%(f)s]') % {'f' : self.filename}
