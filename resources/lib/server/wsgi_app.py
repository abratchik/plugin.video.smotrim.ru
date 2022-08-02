# -*- coding: utf-8 -*-
# Module: wsgi_app
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
WSGI application for Smotrim.ru addon
"""
import re
import xbmc
from urllib import unquote

import resources.lib.modules.persons as persons
from resources.lib.smotrim import SERVER_ADDR


def default_app(environ, start_response):
    params = parse_params(environ)

    if params['brand_id'] and params['person_name'] and environ.get("REMOTE_ADDR") == SERVER_ADDR:
        image_url = persons.get_person_remote_thumbnail_url(params['brand_id'], params['person_name'])
        if image_url:
            status = '302 Found'
            headers = [('Location', image_url)]
            start_response(status, headers)
            return [image_url.encode("utf-8")]
        else:
            status = '404 Not Found'
            headers = [('Content-type', 'text/plain; charset=utf-8')]
            start_response(status, headers)
            return [status.encode('utf-8')]

    status = '400 Bad Request'
    headers = [('Content-type', 'text/plain; charset=utf-8')]
    start_response(status, headers)
    return [status.encode('utf-8')]


def parse_params(environ):
    path_info = environ.get("PATH_INFO", "")
    query_string = environ.get("QUERY_STRING", "")

    brand_id = ""
    m1 = re.match(r'\/brands\/(\d+)', path_info)
    if m1:
        brand_id = m1.group(1)

    person_name = ""
    m2 = re.match(r'(\?|\&|)person_name=(.+)([\&]|\b)', query_string)
    if m2:
        person_name = unquote(m2.group(2))

    xbmc.log("brand_id=%s, person_name=%s" % (brand_id, person_name))

    return {'brand_id': brand_id, 'person_name': person_name}
