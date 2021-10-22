# coding=utf-8
# Module: service
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
Video plugin for Smotrim.ru portal
"""
import xbmc
import time

from resources.lib.smotrim import Smotrim
from resources.lib.users import User

if __name__ == '__main__':
    Smotrim = Smotrim()
    User = User()

    User.watch(Smotrim, "extras")

    monitor = xbmc.Monitor()
    while not monitor.abortRequested():

        if monitor.waitForAbort(3600):
            break

        if 3 <= int(time.strftime("%H")) <= 4:
            User.watch(Smotrim, "extras")
