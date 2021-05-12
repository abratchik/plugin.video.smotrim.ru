# -*- coding: utf-8 -*-
# Module: utils
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import os
import glob
import re

import json

from base64 import b64encode
from json import dumps

import xbmc
import xbmcvfs


def show_error_message(msg):
    xbmc.log(msg, xbmc.LOGDEBUG)
    xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(3 * 1000)))


def create_folder(folder):
    if not (os.path.exists(folder) and os.path.isdir(folder)):
        xbmcvfs.mkdirs(folder)
    return folder


def remove_files_by_pattern(pattern):
    for f in glob.glob(pattern):
        os.remove(f)


def clean_html(raw_html):
    try:
        cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext
    except TypeError:
        return raw_html


def upnext_signal(sender, next_info):
    """Send a signal to Kodi using JSON RPC"""

    data = [to_unicode(b64encode(dumps(next_info).encode()))]
    notify(sender=sender + '.SIGNAL', message='upnext_data', data=data)


def notify(sender, message, data):
    """Send a notification to Kodi using JSON RPC"""
    result = jsonrpc(method='JSONRPC.NotifyAll', params=dict(
        sender=sender,
        message=message,
        data=data,
    ))
    if result.get('result') != 'OK':
        xbmc.log('Failed to send notification: ' + result.get('error').get('message'), 4)
        return False
    return True


def jsonrpc(**kwargs):
    """Perform JSONRPC calls"""

    if kwargs.get('id') is None:
        kwargs.update(id=0)
    if kwargs.get('jsonrpc') is None:
        kwargs.update(jsonrpc='2.0')
    return json.loads(xbmc.executeJSONRPC(dumps(kwargs)))


def to_unicode(text, encoding='utf-8', errors='strict'):
    """Force text to unicode"""
    if isinstance(text, bytes):
        return text.decode(encoding, errors=errors)
    return text
