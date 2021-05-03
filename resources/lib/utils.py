# -*- coding: utf-8 -*-
# Module: utils
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
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

def httpget(url):
    response = urlopen(url)
    return json.load(response)
