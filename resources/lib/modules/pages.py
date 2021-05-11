# -*- coding: utf-8 -*-
# Module: pages
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import json
import os

import xbmc
import xbmcgui
import xbmcplugin


class Page(object):

    def __init__(self, site):
        self.site = site
        self.data = {}
        self.params = site.params
        self.action = site.action
        self.context = site.context
        self.list_items = []
        self.offset = 0
        self.limit = 0
        self.pages = 0

    def load(self):

        self.offset = self.params['offset'] if 'offset' in self.params else 0
        self.limit = self.get_limit_setting()

        xbmc.log("Items per page: %s" % self.limit, xbmc.LOGDEBUG)

        self.data = self.get_data_query()

        self.set_context_title()

        self.set_limit_offset_pages()

        if 'data' in self.data:
            for element in self.data['data']:
                self.append_li_for_element(element)

        if self.pages > 1:
            self.list_items.append({'id': "home",
                                    'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.site.language(30020),
                                    'is_folder': True,
                                    'is_playable': False,
                                    'url': self.site.url,
                                    'info': {'plot': self.site.language(30021)},
                                    'art': {'icon': self.site.get_media("home.png")}
                                    })
            if self.offset < self.pages - 1:
                self.list_items.append({'id': "forward",
                                        'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.site.language(30030),
                                        'is_folder': True,
                                        'is_playable': False,
                                        'url': self.get_nav_url(offset=self.offset),
                                        'info': {'plot': self.site.language(30031) % (self.offset + 1, self.pages)},
                                        'art': {'icon': self.site.get_media("next.png")}
                                        })
        self.show_list_items()

    def play(self):
        pass

    def play_url(self, url):
        if self.site.addon.getSettingBool("addhistory") and 'brands' in self.params:
            resp = self.site.request(self.site.api_url + '/brands/' + self.params['brands'], output="json")
            self.save_brand_to_history(resp['data'])

        print("Player url is %s" % url)
        play_item = xbmcgui.ListItem(path=url)
        if '.m3u8' in url:
            play_item.setMimeType('application/x-mpegURL')
            play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
            play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')


        xbmcplugin.setResolvedUrl(self.site.handle, True, listitem=play_item)

    def create_element_li(self, element):
        return element

    def create_root_li(self):
        return {}

    def get_load_url(self):
        return ""

    def set_context_title(self):
        self.site.context_title = self.context.title()

    def get_data_query(self):
        return self.site.request(self.get_load_url(), output="json")

    def get_nav_url(self, offset=0):
        return self.site.get_url(self.site.url,
                                 action=self.site.action,
                                 context=self.site.context,
                                 limit=self.limit, offset=offset + 1, url=self.site.url)

    def append_li_for_element(self, element):
        self.list_items.append(self.create_element_li(element))

    def get_limit_setting(self):
        return (self.site.addon.getSettingInt('itemsperpage') + 1) * 10

    def set_limit_offset_pages(self):
        if 'pagination' in self.data:
            self.offset = self.data['pagination']['offset'] if 'offset' in self.data['pagination'] else 0
            self.limit = self.data['pagination']['limit'] if 'limit' in self.data['pagination'] else 0
            self.pages = self.data['pagination']['pages'] if 'pages' in self.data['pagination'] else 0

    @staticmethod
    def get_pic_from_plist(plist, res):
        try:
            ep_pics = plist[0]['sizes'] if type(plist) is list else plist['sizes']
            pic = next(p for p in ep_pics if p['preset'] == res)
            return pic['url']
        except StopIteration:
            return ""
        except IndexError:
            return ""

    @staticmethod
    def get_logo(ch, res="xxl"):
        try:
            return ch['logo'][res]['url']
        except KeyError:
            return ""

    def show_list_items(self):

        xbmcplugin.setPluginCategory(self.site.handle, self.site.context_title)

        if self.context == "home":
            xbmcplugin.setContent(self.site.handle, "files")
        else:
            xbmcplugin.setContent(self.site.handle, self.params['content'] if "content" in self.params else "videos")

        # Iterate through categories
        for category in self.list_items:
            # Create a list item with a text label and a thumbnail image.
            list_item = xbmcgui.ListItem(label=category['label'])

            url = category['url']

            is_folder = category['is_folder']
            list_item.setProperty('IsPlayable', str(category['is_playable']).lower())

            if 'info' in category:
                for info in category['info']:
                    list_item.setInfo('video', {info: category['info'][info]})
                    if info == 'mediatype':
                        list_item.addContextMenuItems([(self.site.language(30000),
                                                        "XBMC.Action(%s)" % ("Play"
                                                                             if category['info']['mediatype'] == "news"
                                                                             else "Info")
                                                        ), ])

            if 'art' in category:
                for art in category['art']:
                    list_item.setArt({art: category['art'][art]})

            xbmcplugin.addDirectoryItem(self.site.handle, url, list_item, is_folder)

        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.site.handle)

    def save_brand_to_history(self, brand):
        with open(os.path.join(self.site.history_path, "brand_%s.json" % brand['id']), 'w+') as f:
            json.dump(brand, f)
