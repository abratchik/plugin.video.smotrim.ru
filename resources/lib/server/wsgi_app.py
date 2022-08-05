# -*- coding: utf-8 -*-
# Module: wsgi_app
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
WSGI application for Smotrim.ru addon
"""
import re
from urllib import unquote
from urlparse import parse_qsl

import resources.lib.modules.persons as persons
import resources.lib.modules.articles as articles

from resources.lib.smotrim import SERVER_ADDR


def default_app(environ, start_response):
    params = parse_params(environ)

    if environ.get("REMOTE_ADDR") == SERVER_ADDR:
        if params.get('brand_id', "") and params.get('person_name', ""):
            image_url = persons.get_person_remote_thumbnail_url(params['brand_id'], params['person_name'])
            if image_url:
                status = '302 Found'
                headers = [('Location', image_url)]
                start_response(status, headers)
                return [image_url.encode("utf-8")]
            else:
                return http_response('404 Not Found', start_response)
        elif params.get('articles', ""):
            rss = articles.get_RSS()
            status = '200 OK'
            headers = [('Content-type', 'text/xml; charset=utf-8')]
            start_response(status, headers)
            return [rss]

        return http_response('400 Bad Request', start_response)
    else:
        return http_response('403 Forbidden', start_response)


def http_response(status, start_response):
    headers = [('Content-type', 'text/plain; charset=utf-8')]
    start_response(status, headers)
    return [status.encode('utf-8')]


def parse_params(environ):
    ret = {}

    m1 = re.match(r'\/brands\/(\d+)', environ.get("PATH_INFO", ""))
    if m1:
        ret['brand_id'] = m1.group(1)
    else:
        m1 = re.match(r'\/articles', environ.get("PATH_INFO", ""))
        if m1:
            ret['articles'] = True

    ret.update(dict(parse_qsl(environ.get("QUERY_STRING", ""))))

    return ret
