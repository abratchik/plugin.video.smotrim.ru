# -*- coding: utf-8 -*-
# Module: smotrim
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import json
import os
import sys
import inspect

from importlib import import_module

from urllib import urlencode
from urlparse import parse_qsl

import xbmc
import xbmcaddon

from . import utils


class Smotrim:

    def __init__(self):
        self.id = "plugin.video.smotrim.ru"
        self.addon = xbmcaddon.Addon(self.id)
        self.path = self.addon.getAddonInfo('path').decode('utf-8')
        self.media_path = os.path.join(self.path, "resources/media")
        self.data_path = utils.create_folder(os.path.join(xbmc.translatePath(self.addon.getAddonInfo('profile')),
                                                          'data'))
        self.history_path = utils.create_folder(os.path.join(self.data_path, 'history'))

        self.user = None

        self.url = sys.argv[0]
        self.handle = int(sys.argv[1])
        self.params = {}

        self.api_url = self.addon.getSetting("api_url")

        self.language = self.addon.getLocalizedString

        # to save current context
        self.context = "home"
        self.action = "load"
        self.context_title = self.language(30300)

    def show_to(self, user):

        self.user = user

        xbmc.log("Addon: %s" % self.id, xbmc.LOGDEBUG)
        xbmc.log("Handle: %d" % self.handle, xbmc.LOGDEBUG)
        xbmc.log("User: %s" % user.phone, xbmc.LOGDEBUG)

        params_ = sys.argv[2]
        xbmc.log("Params: %s" % params_, xbmc.LOGDEBUG)
        self.params = dict(parse_qsl(params_[1:]))

        self.context = self.params['context'] if self.params and ('context' in self.params) else "home"
        self.action = self.params['action'] if self.params and ('action' in self.params) else "load"
        xbmc.log("Context: %s" % self.context, xbmc.LOGDEBUG)
        xbmc.log("Action: %s" % self.action, xbmc.LOGDEBUG)

        self.load_context_items()

    # load items from self.context
    def load_context_items(self):
        mod = import_module("resources.lib.modules.%s" % self.context)
        classes = [cls for _, cls in inspect.getmembers(mod, inspect.isclass(mod))]
        getattr(classes[0](self), self.action)()

    def request(self, url, output="text"):
        response = self.user.session.get(url)
        if output == "json":
            return response.json()
        elif output == "text":
            return response.text
        else:
            return response

    # *** Add-on helpers
    def get_url(self, baseurl=None, **kwargs):
        baseurl_ = baseurl if baseurl else self.url
        url = '{}?{}'.format(baseurl_, urlencode(kwargs))
        return url

    def get_media(self, file_name):
        return os.path.join(self.media_path, file_name)

    def get_user_input(self):
        kbd = xbmc.Keyboard()
        kbd.setDefault('')
        kbd.setHeading(self.language(30010))
        kbd.doModal()
        keyword = None

        if kbd.isConfirmed():
            keyword = kbd.getText()

        return keyword
