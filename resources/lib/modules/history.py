# -*- coding: utf-8 -*-
# Module: channels
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import os
import json
from stat import ST_CTIME, S_ISREG, ST_MODE

import resources.lib.modules.pages as pages

import resources.lib.modules.brands as brands

import xbmc


class History(pages.Page):
    def __init__(self, site):
        super(History, self).__init__(site)
        self.brand = brands.Brand(self.site)

    def get_data_query(self):

        cfiles = (os.path.join(self.site.history_path, fn) for fn in os.listdir(self.site.history_path))
        cfiles = ((os.stat(path), path) for path in cfiles)

        cfiles = ((stat[ST_CTIME], path)
                  for stat, path in cfiles if S_ISREG(stat[ST_MODE]))
        elements = {'data': [], }
        for cdate, path in sorted(cfiles, reverse=True):
            with open(path, 'r+') as f:
                xbmc.log("history len = %s" % len(elements['data']), xbmc.LOGDEBUG)
                if len(elements['data']) < self.limit:
                    elements['data'].append(json.load(f))
                else:
                    # autocleanup
                    os.remove(path)

        return elements

    def create_root_li(self):
        return {'id': "history",
                'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.site.language(30050),
                'is_folder': True,
                'is_playable': False,
                'url': self.site.get_url(self.site.url, action="load", context="history", url=self.site.url),
                'info': {'plot': self.site.language(30051)},
                'art': {'icon': self.site.get_media("history.png"),
                        'fanart': self.site.get_media("background.jpg")}
                }

    def set_context_title(self):
        self.site.context_title = self.site.language(30050)

    def create_element_li(self, element):
        return self.brand.create_element_li(element)
