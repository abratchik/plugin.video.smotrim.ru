# -*- coding: utf-8 -*-
# Module: utils
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import datetime
import os
import re
import json

import xbmc

from urllib.request import urlopen


def show_error_message(msg):
    xbmc.log(msg, xbmc.LOGDEBUG)
    xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(3 * 1000)))


def create_folder(folder):
    if not (os.path.exists(folder) and os.path.isdir(folder)):
        os.makedirs(folder)
    return folder


def clean_html(raw_html):
    try:
        cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext
    except TypeError:
        return raw_html


def load_cookies(data_path):
    try:
        with open(os.path.join(data_path, "cookies.json"), 'r+') as f:
            return json.load(f)
    except IOError:
        xbmc.log("Cookie file is absent", xbmc.LOGDEBUG)
        return {}
    except json.decoder.JSONDecodeError:
        xbmc.log("Cookie file is wrong structure, ignoring", xbmc.LOGDEBUG)
        return {}

def save_cookies(cookies, data_path):
    try:
        with open(os.path.join(data_path, "cookies.json"), 'w+') as f:
            json.dump(cookies, f)
            return True
    except IOError:
        xbmc.log("Couldn't save cookies", xbmc.LOGDEBUG)
        return False


def get_date_millis():
    delta = (datetime.datetime.now() - datetime.datetime(1970, 1, 1))
    return int(delta.total_seconds() * 1000)


def httpget(url):
    response = urlopen(url)
    return response.read()
