# -*- coding: utf-8 -*-
# Module: daemons
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html


import xbmc
import resources.lib.server.wsgi_app as wsgi_app
import resources.lib.server.wsgi_server as wsgi_server
import resources.lib.rssbuilder as rssbuilder
from wsgiref.simple_server import make_server


class Daemon:

    def __init__(self, site):
        self.site = site
        self.wsgi = None
        self.rb = None

    def load(self):
        if not self.site.addon.getSettingBool("infoservice"):
            xbmc.log("Smotrim.ru extended info service disabled, skipped", xbmc.LOGDEBUG)
            return

        self.rb = rssbuilder.RSSBuilder()
        self.rb.add_news_to_rss(self.site, self.site.addon.getSettingBool("addnewstorss"))

        xbmc.log("Starting Smotrim.ru extended info service on port %s ..." % str(self.site.server_port), xbmc.LOGDEBUG)
        self.wsgi = make_server('',
                                port=self.site.server_port,
                                app=wsgi_app.default_app,
                                server_class=wsgi_server.SmotrimWsgiServer)
        self.wsgi.start()
