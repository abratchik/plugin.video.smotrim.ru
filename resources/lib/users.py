# -*- coding: utf-8 -*-
# Module: users
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import requests

import xbmc
import xbmcgui

from . import utils


class User:
    def __init__(self):
        self.phone = ""
        self.domain = ""
        self.region = ""

        self.site = None

    def watch(self, site):
        """

        :param site: Smotrim
        :return:
        """
        self.site = site

        self.phone = site.addon.getSetting("phone")
        self.domain = site.addon.getSetting("domain")

        if self.login():
            site.show_to(self)

    def login(self):

        if not self.phone:
            xbmc.log("No Phone specified, login skipped", xbmc.LOGDEBUG)
            self.logout(self.site.cookies)
            return True
        else:
            xbmc.log("User phone is %s, logging in " % self.phone, xbmc.LOGDEBUG)
            if 'phone' in self.site.cookies:
                if not (self.site.cookies['phone'] == self.phone):
                    # phone has changed, logout
                    self.logout(self.site.cookies)
            else:
                self.site.cookies.set("phone", self.phone,
                                      expires=100 * 1000 * 60 * 60 * 24,
                                      domain=self.site.id,
                                      path="/")

        if utils.is_login(self.site.cookies):
            xbmc.log("User %s logged in" % self.phone, xbmc.LOGDEBUG)
            return True

        headers = {'User-agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:88.0) Gecko/20100101 Firefox/88.0",
                   'Accept-Language': "en-US,en;q=0.5",
                   'Origin': "https://%s" % self.domain,
                   'Referer': "https://%s/login" % self.domain,
                   'Sec-GPC': "1",
                   'X-Requested-With': "XMLHTTPRequest"}

        with requests.Session() as s:

            # Load site cookies to session
            if not (self.site.cookies is None):
                for c in self.site.cookies:
                    s.cookies.set_cookie(c)

            # If UID not in cookies, request it
            if not ('ngx_uid' in s.cookies):
                xbmc.log("Cookie file not found or missing UID, requesting from %s" % self.domain, xbmc.LOGDEBUG)
                s.get("https://%s" % self.domain)

            s.cookies.set("isNGX_UID", "true", domain=self.domain, path="/")

            xbmc.log("Determine region ...", xbmc.LOGDEBUG)
            geo = s.get(self.site.api_url + '/geo').json()
            try:
                self.region = geo['data']['locale']['region']
            except KeyError:
                xbmc.log("Login failure - could not get the region", xbmc.LOGDEBUG)
                return False

            s.cookies.set("region", self.region, expires=100 * 1000 * 60 * 60 * 24, domain=self.domain, path="/")
            self.region = s.cookies['region']
            xbmc.log("Region is %s" % s.cookies['region'], xbmc.LOGDEBUG)

            s.post("https://%s/login" % self.domain,
                   files={'phone': (None, self.phone)},
                   headers=headers)

            auth_code = xbmcgui.Dialog().numeric(0, self.site.language(30500), "")

            if not auth_code:
                self.logout(s.cookies)
                utils.save_cookies(s.cookies, self.site.data_path)
                return False

            xbmc.log("Send the code %s for authorization to %s" % (auth_code, self.domain), xbmc.LOGDEBUG)

            s.post("https://%s/login" % self.domain,
                   files={'code': (None, auth_code),
                          'phone': (None, self.phone)},
                   headers=headers)

            if utils.is_login(s.cookies):
                xbmc.log("User login SUCCESS, id=%s, usgr=%s" % (s.cookies['sm_id'], s.cookies['usgr']), xbmc.LOGDEBUG)
                for c in s.cookies:
                    self.site.cookies.set_cookie(c)
                utils.save_cookies(s.cookies, self.site.data_path)
                return True

        return False

    def logout(self, cookies):
        if 'sm_id' in cookies:
            cookies.clear(domain=self.domain, path="/", name="sm_id")
        if 'usgr' in cookies:
            cookies.clear(domain=self.domain, path="/", name="usgr")
