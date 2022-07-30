# -*- coding: utf-8 -*-
# Module: wsgi_server
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
WSGI server for Smotrim.ru addon
"""

from wsgiref.simple_server import WSGIServer

import xbmc


class SmotrimWsgiServer(WSGIServer):
    monitor = None
    m_process = None

    def start(self):
        self.monitor = xbmc.Monitor()

        try:
            self.serve_forever()
        except StopIteration:
            xbmc.log("SmotrimWsgiServer - shutdown complete!", xbmc.LOGDEBUG)

    def service_actions(self) -> None:
        if self.monitor.abortRequested():
            xbmc.log("SmotrimWsgiServer - abortRequested!", xbmc.LOGDEBUG)
            raise StopIteration

# class SmotrimMonitor(xbmc.Monitor):
#     def __init__(self, wsgi: SmotrimWsgiServer):
#         self.wsgi = wsgi
#         super(SmotrimMonitor,self).__init__()
#
#     def onNotification(self, sender: str, method: str, data: str) -> None:
#         xbmc.log("Notification received: %s %s" % (sender, method), xbmc.LOGDEBUG)
