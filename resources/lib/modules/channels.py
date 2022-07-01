# -*- coding: utf-8 -*-
# Module: channels
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import os

import resources.lib.modules.pages as pages


class Channel(pages.Page):
    def __init__(self, site):
        super(Channel, self).__init__(site)
        self.cache_enabled = True

    def get_load_url(self):
        return self.site.get_url(self.site.api_url + '/channels')

    def create_root_li(self):
        return {'id': "channels",
                'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.site.language(30400),
                'is_folder': True,
                'is_playable': False,
                'url': self.site.get_url(self.site.url, action="load",
                                         context="channels",
                                         content="files",
                                         url=self.site.url),
                'info': {'plot': self.site.language(30400)},
                'art': {'icon': self.site.get_media("channels.png"),
                        'fanart': self.site.get_media("background.jpg")}
                }

    def create_element_li(self, element):
        return {'id': element['id'],
                'label': element['title'],
                'is_folder': True,
                'is_playable': False,
                'url': self.site.get_url(self.site.url,
                                         action="load",
                                         context="channelmenus",
                                         channels=element['id'],
                                         title=element['title'].encode('utf-8', 'ignore'),
                                         content="files",
                                         url=self.site.url),
                'info': {'plot': element['title']},
                'art': {'thumb': self.get_pic_from_id(element['picId'], "lw"),
                        'icon': self.get_pic_from_id(element['picId'], "lw"),
                        'fanart': self.get_pic_from_id(element['picId'], "hd"),
                        'poster': self.get_pic_from_id(element['picId'], "vhdr")}
                }

    def add_context_menu(self, category):
        self.context_menu_items.append((self.site.language(30405),
                                        "RunPlugin(%s)" %
                                        self.site.get_url(action="hide_empty_channels",
                                                          context="extras",
                                                          url=self.site.url)))

    def set_context_title(self):
        self.site.context_title = self.site.language(30400)

    def get_cache_filename(self):
        return os.path.join(self.site.data_path, "channels.json")
