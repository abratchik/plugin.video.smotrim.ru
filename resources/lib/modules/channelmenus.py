# -*- coding: utf-8 -*-
# Module: channelmenus
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import resources.lib.modules.pages as pages

import resources.lib.modules.brands as brands


class ChannelMenu(pages.Page):
    def __init__(self, site):
        super(ChannelMenu, self).__init__(site)
        self.brand = brands.Brand(site)
        self.cache_enabled = True

    def get_load_url(self):
        return self.site.get_url(self.site.api_url + '/menu/channels/' + self.params['channels'],
                                 limit=self.limit,
                                 offset=self.offset)

    def set_context_title(self):
        self.site.context_title = self.params['title']

    def create_element_li(self, element):
        return self.brand.create_search_by_tag_li(element['tags'][0]['id'],
                                                  element['title'].encode('utf-8', 'ignore'),
                                                  element['title'].encode('utf-8', 'ignore'),
                                                  tagicon=self.site.get_media("search.png"),
                                                  has_children=False,
                                                  cache_expire="86400")

    def get_cache_filename_prefix(self):
        return "channel_menu_%s" % self.params['channels']
