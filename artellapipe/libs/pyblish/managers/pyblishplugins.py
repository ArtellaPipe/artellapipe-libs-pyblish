#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains manager for Pyblish Plugins
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging
import inspect
import importlib
import traceback

import pyblish.api

import tpDcc
from tpDcc.libs.python import python

if python.is_python2():
    import pkgutil as loader
else:
    import importlib as loader

import artellapipe

LOGGER = logging.getLogger('artellapipe-libs-pyblish')


class PyblishPluginsManager(object):

    _config = None
    _registered_plugins = dict()

    @property
    def config(self):
        if not self.__class__._config:
            self.__class__._config = tpDcc.ConfigsMgr().get_config(
                config_name='artellapipe-pyblishplugins',
                package_name=artellapipe.project.get_clean_name(),
                root_package_name='artellapipe',
                environment=artellapipe.project.get_environment())

        return self.__class__._config

    @property
    def plugins(self):
        if not self.__class__._registered_plugins:
            self._register_plugins()

        return self.__class__._registered_plugins

    def get_plugin_info(self, plugin_name):
        """
        Returns dictionary with info of the given plugin
        :param plugin_name: str
        :return: dict
        """

        if plugin_name not in self.plugins:
            LOGGER.warning('Pyblish Plugin with name "{}" is not registered!'.format(plugin_name))
            return None

        return self.__class__._registered_plugins[plugin_name]

    def get_plugin(self, plugin_name):
        """
        Returns a registered plugin by its name
        :param plugin_name: str
        :return: class
        """

        plugin_info = self.get_plugin_info(plugin_name)
        if not plugin_info:
            return None

        return self.plugins[plugin_name]['class']

    def get_plugin_path(self, plugin_name):
        """
        Returns path where plugin is located
        :param plugin_name: str
        :return: str
        """

        plugin_info = self.get_plugin_info(plugin_name)
        if not plugin_info:
            return None

        return self.plugins[plugin_name]['path']

    def _register_plugins(self):

        pyblish_modules = self.config.get('pyblish_modules', default=list())
        if not pyblish_modules:
            LOGGER.warning('No Pyblish Modules to search Pyblish plugins in found!')
            return

        for pyblish_module in pyblish_modules:
            try:
                pyblish_mod = importlib.import_module(pyblish_module)
                pyblish_mod_dir = os.path.dirname(pyblish_mod.__file__)
                for sub_module in loader.walk_packages([pyblish_mod_dir]):
                    importer, sub_module_name, _ = sub_module
                    qname = pyblish_module + '.' + sub_module_name
                    try:
                        mod = importer.find_module(sub_module_name).load_module(sub_module_name)
                    except Exception as exc:
                        msg = 'Impossible to register Pyblish Plugin: {}. Exception raised: {} | {}'.format(
                            qname, exc, traceback.format_exc()
                        )
                        LOGGER.warning(msg)
                        continue

                    plugin_path = os.path.dirname(mod.__file__)
                    for cname, obj in inspect.getmembers(mod, inspect.isclass):
                        if issubclass(obj, (pyblish.api.InstancePlugin, pyblish.api.ContextPlugin)):
                            plugin_name = obj.__name__
                            if plugin_name in self.__class__._registered_plugins:
                                LOGGER.info(
                                    'Already registered a plugin with name: "{}". Overwriting ...'.format(plugin_name))
                            self.__class__._registered_plugins[obj.__name__] = {
                                'module': mod,
                                'path': plugin_path,
                                'class': obj
                            }
            except Exception as exc:
                LOGGER.error('Error while registering Pyblish plugins from: "{}" | {}'.format(pyblish_module, exc))
                continue

        if not self.__class__._registered_plugins:
            LOGGER.warning('No Pyblish Plugins found!')

        pyblish_plugins = self.config.get('plugins', default=dict())
        for plugin_name, plugin_info in self.__class__._registered_plugins.items():
            if plugin_name in pyblish_plugins:
                obj = plugin_info['class']
                for attr, attr_value in pyblish_plugins[plugin_name].items():
                    setattr(obj, attr, attr_value)
