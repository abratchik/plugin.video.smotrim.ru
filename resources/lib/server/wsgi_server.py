# -*- coding: utf-8 -*-
# Module: wsgi_server
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
WSGI server for Smotrim.ru addon
"""

from wsgiref.simple_server import make_server

from resources.lib.server.wsgi_app import default_app

# Our callable object which is intentionally not compliant to the
# standard, so the validator is going to break
import xbmc

from resources.lib.smotrim import SERVER_PORT


class SmotrimWsgiServer:

    def __init__(self):
        self.port = SERVER_PORT
        self.httpd = None
        self.http_app = None

    def start(self, timeout=0):
        xbmc.log("Starting wsgi on port %s...." % str(self.port))
        self.http_app = default_app
        self.httpd = make_server('', self.port, self.http_app)
        self.httpd.serve_forever()

    def stop(self):
        xbmc.log("Shutdown wsgi on port %s...." % str(self.port))
        self.httpd.server_close()

