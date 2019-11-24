#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom tool definition for Pyblish based tools
"""

from __future__ import print_function, division, absolute_import

__author__ = "Tomas Poveda"
__license__ = "MIT"
__maintainer__ = "Tomas Poveda"
__email__ = "tpovedatd@gmail.com"

import os
import logging

import pyblish.api
import pyblish_lite

import tpDccLib as tp

import artellapipe.register

LOGGER = logging.getLogger()


class ArtellaPyblishTool(artellapipe.Tool, object):
    def __init__(self, project, config):

        self._pyblish_window = None
        self._registered_plugins = list()

        super(ArtellaPyblishTool, self).__init__(project=project, config=config)
        self._setup_host()

    def post_attacher_set(self):
        pyblish_win = pyblish_lite.show()
        self.set_pyblish_window(pyblish_win)
        pyblish_win.setStyleSheet(pyblish_win.styleSheet() + """\n
              #Header {
              background: "#555";
              border: 1px solid "#444";
          }

          #Header QRadioButton {
              border-right: 1px solid #333;
              left: 2px;
          }

          #Header QRadioButton::indicator {
              width: 65px;
              height: 40px;
              border: 0px solid "transparent";
              border-bottom: 3px solid "transparent";
              background-repeat: no-repeat;
              background-position: center center;
          }

          #Header QRadioButton::indicator:checked {
              width: 65px;
              height: 40px;
              border: 0px solid "transparent";
              border-bottom: 3px solid "transparent";
              background-repeat: no-repeat;
              background-position: center center;
              image: none;
          }

          #Header QRadioButton:checked {
              background-color: rgba(255, 255, 255, 20);
              border-bottom: 3px solid "lightblue";
          }

          #Header QRadioButton::indicator:unchecked {
              image: none;
          }
          """)

        self._register_plugins()

    def close_tool(self):
        self._deregister_plugins()
        super(ArtellaPyblishTool, self).close_tool()

    def set_pyblish_window(self, pyblish_window):
        """
        Sets the Pyblish window wrapped by this window
        :param pyblish_window:
        """

        if self._pyblish_window:
            return

        # print(type(pyblish_window.controller.context))
        # pyblish_window.controller.context.data['project'] = self._project
        # pyblish_window.refresh()

        pyblish_window.controller.was_reset.connect(self._on_controller_reset)

        self.main_layout.addWidget(pyblish_window)
        self._pyblish_window = pyblish_window

    def register_plugin(self, plugin_class):
        """
        Registers given plugin path
        :param plugin_path: str
        """

        if not plugin_class or plugin_class in self._registered_plugins:
            return
        LOGGER.info('Registering Pyblish Plugin: {}'.format(plugin_class))
        pyblish.api.register_plugin(plugin_class)
        self._registered_plugins.append(plugin_class)

    def _setup_host(self):
        """
        Internal function that sets the host of the tool
        :return:
        """

        # TODO: Should we do this in a central place (not per tool)?

        if tp.is_maya():
            pyblish.api.register_host('maya')
        elif tp.is_houdini():
            pyblish.api.register_host('houdini')

    def _register_plugins(self):
        """
        Internal function that registers current available plugins in project
        """

        plugins_to_register = self.config.get('pyblish_plugins', list())
        if not plugins_to_register:
            LOGGER.warning('No Pyblish Plugins defined to load')
            return

        for plugin_name in plugins_to_register:
            plguin_class = artellapipe.PyblishMgr().get_plugin(plugin_name)
            self.register_plugin(plguin_class)

    def _deregister_plugins(self):
        """
        Internal function that deregister current registered plugin paths
        """

        for p in self._registered_plugins:
            pyblish.api.deregister_plugin(p)

    def _on_controller_reset(self):
        self._pyblish_window.controller.context.data['project'] = self._project


artellapipe.register.register_class('PyblishTool', ArtellaPyblishTool)
