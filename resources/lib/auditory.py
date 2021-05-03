# -*- coding: utf-8 -*-
# Module: auditory
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import os
import json
import xbmc

from . import utils

class User:
    def __init__(self):
        self.phone = ""
        self.cookies = {}

    def watch(self, site):
        """

        :param site: Smotrim
        :return:
        """

        addon = site.get_addon()
        self.phone = addon.getSetting("phone")
        print("User phone is %s" % self.phone)\

        data_path = addon.get_data_path()
        self.load_cookies(data_path)

        uid_url = addon.getSetting("uid_url")

        site.begin()


    def load_cookies(self, data_path):
        try:
            with open(os.path.join(data_path, "cookies.json"), 'r+') as f:
                self.cookies = json.load(f)
        except IOError:
            xbmc.log("Cookie file is empty", xbmc.LOGDEBUG)

    def save_cookies(self, data_path):
        try:
            with open(os.path.join(data_path, "cookies.json"), 'w+') as f:
                json.dump(self.cookies, f)
        except IOError:
            xbmc.log("Couldn't save cookies", xbmc.LOGDEBUG)