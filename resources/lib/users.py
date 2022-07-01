# -*- coding: utf-8 -*-
# Module: users
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import os
import re
import pickle

import requests

import xbmc
import xbmcgui

NEVER = 100 * 1000 * 60 * 60 * 24

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0"


class User:
    def __init__(self):
        self.phone = ""
        self.domain = ""
        self._geo = {}

        self._site = None
        self.session = None

        self._headers = {}

        self._cookies_file = ""

    def watch(self, site, context=""):
        """

        :param site: Smotrim
        :return:
        @param site: assumed Smotrim class
        @param context: context to load. If empty then site will use CLI arguments
        """
        self._site = site

        self.phone = site.addon.getSetting("phone")
        self.domain = site.domain

        self.session = requests.Session()

        self._headers = {
            'User-Agent': USER_AGENT,
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            'Accept-Encoding': "gzip, deflate, br",
            'Accept-Language': "en-US,en;q=0.5",
            'Connection': "keep-alive",
            'Sec-Fetch-Dest': "document",
            'Sec-Fetch-Mode': "navigate",
            'Sec-Fetch-Site': "none",
            'Sec-Fetch-User': "?1",
            'Sec-GPC': "1",
            'Upgrade-Insecure-Requests': "1"}

        # Load saved cookies
        self._cookies_file = os.path.join(self._site.data_path, "cookies.dat")
        self._load_cookies()

        # If UID not in cookies, request it
        if not ('ngx_uid' in self.session.cookies):
            xbmc.log("Cookie file not found or missing UID, requesting from %s" % self.domain, xbmc.LOGDEBUG)
            self.get_http("https://%s" % self.domain)
            self._save_cookies()

        if self._login():
            site.show_to(self, context)

        self.session.close()

    def _login(self):

        if not self.phone:
            self._logout()
            return True
        else:
            if 'phone' in self.session.cookies:
                if not (self.session.cookies['phone'] == self.phone):
                    # phone has changed, logout
                    self._logout()
            else:
                self.session.cookies.set("phone", self.phone,
                                         expires=NEVER,
                                         domain=self._site.id,
                                         path="/")
                self._save_cookies()

        if self._is_login():
            return True

        login_url = "https://" + self.domain + "/personal/login?redirect=%2F"

        # Set region
        self.load_geo()
        self.session.cookies.set("region", self.get_region(), expires=NEVER, domain=self.domain, path="/")
        xbmc.log("Region is %s" % self.session.cookies['region'], xbmc.LOGDEBUG)

        # Set headers
        headers = ({'User-Agent': USER_AGENT,
                    'Accept': "*/*",
                    'Accept-Encoding': "gzip, deflate, br",
                    'Accept-Language': "en-US,en;q=0.5",
                    'Connection': "keep-alive",
                    'Host': self.domain,
                    'Referer': "https://%s/" % self.domain,
                    'Sec-Fetch-Dest': "empty",
                    'Sec-Fetch-Mode': "same-origin",
                    'Sec-Fetch-Site': "same-origin",
                    'Sec-GPC': "1",
                    'X-Requested-With': "XMLHTTPRequest"
                    })

        # Try to login - first load the form
        resp = self.session.get(login_url, headers=headers)
        if resp.status_code != 200:
            xbmc.log("Couldn't load the login page %s, error %a" % (login_url, resp.status_code), xbmc.LOGDEBUG)
            self._logout()
            self._save_cookies()
            return False

        self._save_cookies()

        # Read the token
        token = self._get_token(resp.text)
        if token == "":
            xbmc.log("Failed to retrieve the secure token from the login page %s" % login_url)
            self._logout()
            return False

        xbmc.log("Token retrieved successfully: % s" % token)

        headers.update({'Origin': "https://%s" % self.domain,
                        'Referer': login_url})

        self.session.post(login_url,
                          files={'phone': (None, self.phone),
                                 '_token': (None, token)},
                          headers=headers)

        auth_code = xbmcgui.Dialog().numeric(0, self._site.language(30500), "")

        if not auth_code:
            self._logout()
            self._save_cookies()
            return False

        xbmc.log("Send the code %s for authorization to %s" % (auth_code, self.domain), xbmc.LOGDEBUG)

        self.session.post(login_url,
                          files={'code': (None, auth_code),
                                 'phone': (None, self.phone)},
                          headers=headers)

        if self._is_login():
            xbmc.log("User login SUCCESS, id=%s, usgr=%s" %
                     (self.session.cookies['smid'], self.session.cookies['usgr']), xbmc.LOGDEBUG)
            self._save_cookies()
            return True

        return False

    def load_geo(self):
        if not ('data' in self._geo):
            xbmc.log("Loading geo data", xbmc.LOGDEBUG)
            self._geo = self.get_http(self._site.api_url + '/geo').json()
        return self._geo

    def get_region(self):
        try:
            return self._geo['data']['locale']['region']
        except KeyError:
            return ""

    def get_headers(self, type="dict"):
        if type == "dict":
            return self._headers
        elif type == "str":
            return "&".join(str(key) + "=" + str(value) for key, value in self._headers.items())
        else:
            return ""

    def get_http(self, url):
        self._set_host(url)
        xbmc.log(str(self._headers), xbmc.LOGDEBUG)
        return self.session.get(url, headers=self._headers)

    def _set_host(self, url):
        host = url.split("://")[1].split("/")[0]
        self._headers.update({'Host': host})

    def _logout(self):
        if 'smid' in self.session.cookies:
            self.session.cookies.clear(domain=self.domain, path="/", name="smid")
        if 'usgr' in self.session.cookies:
            self.session.cookies.clear(domain=self.domain, path="/", name="usgr")

    def _is_login(self):
        return ('smid' in self.session.cookies) and ('usgr' in self.session.cookies)

    def _save_cookies(self):
        with open(self._cookies_file, "wb") as f:
            pickle.dump(self.session.cookies, f)

    def _load_cookies(self):
        if os.path.exists(self._cookies_file):
            with open(self._cookies_file, 'rb') as f:
                cj = pickle.load(f)
                for c in cj:
                    xbmc.log("ck %s " % str(c), xbmc.LOGDEBUG)
                    self.session.cookies.set_cookie(c)

    def _get_token(self, html_text):
        # xbmc.log(html_text, xbmc.LOGDEBUG)
        input_match = re.search(r"<input.*\"_token\".*>", html_text)
        if input_match:
            # xbmc.log("Found token field %s" % input_match.group(0), xbmc.LOGDEBUG)
            token_match = re.search(r"(value\s*=\s*\")(.+)(\">)", input_match.group(0))
            if token_match and (len(token_match.group()) > 1):
                return token_match.group(2)
        return ""