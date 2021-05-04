# -*- coding: utf-8 -*-
# Module: auditory
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import datetime
import xbmc

from . import utils


class User:
    def __init__(self):
        self.phone = ""
        self.cookies = {}
        self.data_path = ""
        self.uid_url = ""

    def watch(self, site):
        """

        :param site: Smotrim
        :return:
        """

        self.phone = site.addon.getSetting("phone")
        self.data_path = site.data_path
        self.cookies = utils.load_cookies(self.data_path)
        self.uid_url = site.addon.getSetting("uid_url")

        if self.login():
            site.begin()

    def login(self):
        if not self.phone:
            xbmc.log("No Phone specified, login is not performed", xbmc.LOGDEBUG)
            return True

        xbmc.log("User phone is %s" % self.phone, xbmc.LOGDEBUG)
        ngx_uid = (utils.httpget(self.uid_url + "/?" + str(utils.get_date_millis()))).decode('utf-8')
        expires = datetime.datetime.today() + datetime.timedelta(days=7502)
        self.cookies['ngx_uid'] = {'value': ngx_uid,
                                   'path': "/",
                                   'domain': "smotrim.ru",
                                   'expires': expires.strftime("%a, %d %b %Y %I:%M:%S %p %Z"),
                                   'secure': "false"
                                   }
        utils.save_cookies(self.cookies, self.data_path)
        return True