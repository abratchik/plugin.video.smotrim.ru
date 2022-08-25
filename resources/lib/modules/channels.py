# -*- coding: utf-8 -*-
# Module: channels
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import os

import xbmc

import resources.lib.modules.pages as pages
from resources.lib.kodiutils import get_url


class Channel(pages.Page):
    def __init__(self, site):
        super(Channel, self).__init__(site)
        self.cache_enabled = True

    def preload(self):
        if self.site.addon.getSettingBool("iptv.enabled"):
            self.list_items.append(self.create_menu_li("lives", 30410, is_folder=False, is_playable=False,
                                                       url=get_url(self.site.url,
                                                                   action="tvguide",
                                                                   context="channels",
                                                                   url=self.site.url),
                                                       info={'plot': self.site.language(30224)}))

        self.cache_expire = 0

    def tvguide(self):
        xbmc.executebuiltin("ActivateWindow(TVGuide,,'%s')" % self.site.url)

    def get_load_url(self):
        return get_url(self.site.api_url + '/geo')

    def get_data_query(self):
        if self.is_cache_available():
            return self.get_data_from_cache()
        else:
            geo = self.site.request(self.get_load_url(), output="json")

            return {'metadata': geo.get('metadata', {}),
                    'data': geo['data'].get('channels', [])}

    def create_root_li(self):
        return self.create_menu_li("channels", 30400, is_folder=True, is_playable=True,
                                   url=get_url(self.site.url, action="load",
                                               context="channels",
                                               content="files",
                                               cache_expire="0",
                                               url=self.site.url),
                                   info={'plot': self.site.language(30400)})

    def create_element_li(self, element):
        return {'id': element['id'],
                'label': element['title'],
                'is_folder': True,
                'is_playable': False,
                'url': get_url(self.site.url,
                               action="load",
                               context="channelmenus",
                               channels=element['id'],
                               cache_expire="0",
                               title=element['title'].encode('utf-8', 'ignore'),
                               content="files",
                               url=self.site.url),
                'info': {'plot': element['title']},
                'art': {'thumb': self.get_pic_from_id(element['picId'], "lw"),
                        'icon': self.get_pic_from_id(element['picId'], "lw"),
                        'fanart': self.get_pic_from_id(element['picId'], "hd"),
                        'poster': self.get_pic_from_id(element['picId'], "it")}
                }

    def add_context_menu(self, category):
        self.context_menu_items.append((self.site.language(30405),
                                        "RunPlugin(%s)" %
                                        get_url(self.site.url,
                                                action="hide_empty_channels",
                                                context="extras",
                                                url=self.site.url)))

    def set_context_title(self):
        self.site.context_title = self.site.language(30400)

    def get_cache_filename(self):
        return os.path.join(self.site.data_path, "channels.json")
