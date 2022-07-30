# -*- coding: utf-8 -*-
# Module: daemons
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import inspect

import resources.lib.smotrim as smotrim
import resources.lib.server.wsgi_server as wsgi_server

import xbmc
import json

from importlib import import_module

from resources.lib.kodiutils import notify


class SmotrimMonitor(xbmc.Monitor):

    def __init__(self, site):
        self.monitor = None
        self.site = site
        self.wsgi = None
        self.q = []
        super(SmotrimMonitor, self).__init__()

    def load(self):

        xbmc.log("Smotrim daemon started", level=xbmc.LOGDEBUG)
        self.start_wsgi()
        xbmc.log("Smotrim daemon stopped", level=xbmc.LOGDEBUG)

        # self.monitor = xbmc.Monitor()
        # while not self.monitor.abortRequested():
        #     if self.monitor.waitForAbort(30):
        #         xbmc.log("Smotrim daemon stopped", level=xbmc.LOGDEBUG)
        #         break
        #
        # self.stop_wsgi()

    def start_wsgi(self):
        self.wsgi = wsgi_server.SmotrimWsgiServer()
        self.wsgi.start()

    def stop_wsgi(self):
        self.wsgi.stop()

    # def onNotification(self, sender: str, method: str, data: str) -> None:
    #     xbmc.log("Smotrim daemon received %s, %s" % (sender, method), level=xbmc.LOGDEBUG)
    #     if sender == smotrim.ADDON_ID:
    #
    #         try:
    #             _ = next(p for p in self.q if p.get('method', "") == method and p.get('data', "") == data)
    #             return
    #         except StopIteration:
    #             self.q.append({'method': method, 'data': data})
    #
    #         xbmc.log("Smotrim: %d daemons running" % len(self.q), level=xbmc.LOGDEBUG)
    #
    #         # try:
    #         cm = method.split(".")
    #         mod = import_module("resources.lib.modules.%s" % cm[1])
    #         classes = [cls for _, cls in inspect.getmembers(mod, inspect.isclass(mod))]
    #         if data:
    #             getattr(classes[0](self.site), cm[2])(data)
    #         else:
    #             getattr(classes[0](self.site), cm[2])()
    #         # except Exception as ex:
    #         #     xbmc.log("%s %s" % (method, getattr(ex, 'message', repr(ex))), xbmc.LOGERROR)
    #
    #         xbmc.log("Smotrim daemon processed %s, %s" % (sender, method), level=xbmc.LOGDEBUG)
    #
    #         for index, p in enumerate(self.q):
    #             if p.get('method', "") == method and p.get('data', "") == data:
    #                 self.q.pop(index)
    #                 break
