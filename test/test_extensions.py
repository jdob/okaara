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

import os
import sys
import unittest

import mock
import pkg_resources

from okaara import extensions


DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')


class ExtensionsManagerTests(unittest.TestCase):

    def test_load(self):
        # Setup
        mock_init_func = mock.MagicMock()
        test_descriptor = extensions.ExtensionDescriptor('sample', mock_init_func, 3)

        mock_loader = mock.MagicMock()
        mock_loader.find_extension_descriptors.return_value = [test_descriptor]

        init_arg_list = ['a', 'b']
        init_kwargs_list = {'x' : 'x', 'y' : 'y'}

        manager = extensions.ExtensionsManager(init_arg_list=init_arg_list,
                                               init_kwargs_list=init_kwargs_list)
        manager.add_loader(mock_loader)

        # Test
        manager.load()

        # Verify
        mock_init_func.assert_called_once_with(*init_arg_list, **init_kwargs_list)

    def test_load_with_error(self):
        # Setup
        bad_mock_init_func = mock.MagicMock()
        bad_test_descriptor = extensions.ExtensionDescriptor('sample-bad',
                                                             bad_mock_init_func, 1)

        good_mock_init_func = mock.MagicMock()
        good_test_descriptor = extensions.ExtensionDescriptor('sample-good',
                                                              good_mock_init_func, 2)

        mock_loader = mock.MagicMock()
        mock_loader.find_extension_descriptors.return_value = [bad_test_descriptor,
                                                               good_test_descriptor]

        manager = extensions.ExtensionsManager()
        manager.add_loader(mock_loader)

        # Test
        try:
            manager.load()
        except extensions.LoadFailed as e:
            self.assertEqual(1, len(e.failed_descriptors))
            self.assertEqual('sample-bad', e.failed_descriptors[0].name)

        # Verify
        self.assertEqual(1, good_mock_init_func.call_count)
        self.assertEqual(1, bad_mock_init_func.call_count)


class DirectoryExtensionsLoader(unittest.TestCase):

    def test_valid_extensions(self):
        # Setup
        extensions_dir = os.path.join(DATA_DIR, 'valid_extensions')
        init_module_name = 'hook'
        init_function_name = 'initialize'
        loader = extensions.DirectoryExtensionsLoader(extensions_dir, init_module_name,
                                                      init_function_name)

        # Test
        descriptors = loader.find_extension_descriptors()

        # Verify
        self.assertEqual(2, len(descriptors))
        for d in descriptors:
            self.assertTrue(isinstance(d, extensions.ExtensionDescriptor))

        self.assertEqual(descriptors[0].name, 'ext_1')
        self.assertEqual(descriptors[0].init_method.__name__, init_function_name)
        self.assertEqual(descriptors[0].priority, extensions.DEFAULT_PRIORITY)

        self.assertEqual(descriptors[1].name, 'ext_2')
        self.assertEqual(descriptors[1].init_method.__name__, init_function_name)
        self.assertEqual(descriptors[1].priority, 10)


class EntryPointLoaderTests(unittest.TestCase):

    @mock.patch('pkg_resources.iter_entry_points')
    def ___test_valid_extensions(self, mock_iter):
        # Setup
        test_ep_dir = os.path.join(DATA_DIR, 'entry_point_extensions')
        if test_ep_dir not in sys.path:
            sys.path.append(test_ep_dir)

        distribution = pkg_resources.Distribution()
        ep_1 = pkg_resources.EntryPoint('ep-1', 'ext_1.hook',
                                        attrs=('initialize',), dist=distribution)
        ep_2 = pkg_resources.EntryPoint('ep-2', 'ext_2.hook',
                                        attrs=('initialize',), dist=distribution)
        mock_iter.return_value = iter([ep_1, ep_2])

        loader = extensions.EntryPointLoader('mocked')

        # Test
        descriptors = loader.find_extension_descriptors()

        # Verify
        self.assertEqual(2, len(descriptors))
        for d in descriptors:
            self.assertTrue(isinstance(d, extensions.ExtensionDescriptor))

        self.assertEqual(descriptors[0].name, 'ep-1')
        self.assertEqual(descriptors[0].init_method.__name__, 'initialize')
        self.assertEqual(descriptors[0].priority, extensions.DEFAULT_PRIORITY)

        self.assertEqual(descriptors[1].name, 'ep-2')
        self.assertEqual(descriptors[1].init_method.__name__, 'initialize')
        self.assertEqual(descriptors[1].priority, 1)
