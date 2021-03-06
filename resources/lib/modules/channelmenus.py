# -*- coding: utf-8 -*-
# Module: channelmenus
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import json
import os
import sys

import xbmc

import resources.lib.modules.pages as pages

import resources.lib.modules.brands as brands

from resources.lib import kodiutils
from resources.lib.kodiutils import get_url


class ChannelMenu(pages.Page):
    def __init__(self, site):
        super(ChannelMenu, self).__init__(site)
        self.brand = brands.Brand(site)
        self.cache_enabled = True

        # self.vitrina_url = "https://media.mediavitrina.ru"
        # with open(os.path.join(self.site.path, "resources/data/vitrina.json"), "r+") as f:
        #     self.VITRINA = json.load(f)

    def preload(self):
        spath = self.get_stream_url_from_double(self.params['channels'])
        if spath:
            self.list_items.append({'id': "livetv",
                                    'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.site.language(30410),
                                    'is_folder': False,
                                    'is_playable': True,
                                    'url': get_url(self.site.url,
                                                   action="play",
                                                   context="channelmenus",
                                                   channels=self.params['channels'],
                                                   url=self.site.url),
                                    'info': {'plot': self.site.language(30410)},
                                    'art': {'icon': self.site.get_media("lives.png")}
                                    })
        return

    def get_load_url(self):
        return self.get_load_url_ext(self.params['channels'], self.limit, self.offset)

    def get_nav_url(self, offset=0):
        return get_url(self.site.url,
                       action="load",
                       context=self.site.context,
                       channels=self.params.get('channels'),
                       title=self.params.get('title'),
                       limit=self.limit, offset=offset, url=self.site.url)

    def get_load_url_ext(self, ch_id, limit, offset):
        return get_url('%s/menu/channels/%s' % (self.site.api_url, str(ch_id)),
                       limit=limit,
                       offset=offset)

    def set_context_title(self):
        self.site.context_title = self.params.get('title')

    def create_element_li(self, element):
        if len(element['tags']) > 0:
            tags = ":".join([str(t['id']) for t in element['tags']])
            return self.brand.create_search_by_tag_li(tags,
                                                      element['title'],
                                                      taginfo=element['title'],
                                                      tagicon=self.site.get_media("search.png"),
                                                      has_children=False,
                                                      cache_expire="86400")
        else:
            return {'id': element['id'],
                    'label': "[B]%s[/B]" % element['title'],
                    'is_folder': True,
                    'is_playable': False,
                    'url': get_url(self.site.url,
                                   action="search",
                                   context="brands",
                                   search=element['title'],
                                   cache_expire="86400",
                                   url=self.site.url),
                    'info': {'plot': "%s [%s]" % (self.site.language(30010), element['title'])},
                    'art': {'icon': self.site.get_media("search.png"),
                            'fanart': self.site.get_media("background.jpg")}
                    }

    def get_cache_filename_prefix(self):
        return "channel_menu_%s" % self.params['channels']

    def play(self):
        spath = self.get_stream_url_from_double(self.params.get("channels"))
        self.play_url(spath)

    def get_stream_url_from_double(self, channel_id):
        try:
            _, live = self.get_channel_live_double(channel_id)
            return live
        except:
            xbmc.log("Error in finding live stream for the channel %s" % channel_id, xbmc.LOGERROR)
            return ""

    def get_channel_live_double(self, channel_id):

        # if str(channel_id) in self.VITRINA:
        #     return self.get_vitrina_live_double(channel_id, self.VITRINA[str(channel_id)])

        headers = self.site.user.get_headers().copy()

        headers['Sec-Fetch-Site'] = "cross-site"

        doublemap = self.site.request('%s/live-double/channel_id/%s' % (self.site.liveapi_url,
                                                                        channel_id),
                                      output="json", headers=headers)

        if doublemap.get('live_id'):
            try:
                datalive = self.site.request('%s/datalive/id/%s' % (self.site.liveapi_url,
                                                                    doublemap['live_id']),
                                             output="json", headers=headers)
                medialist = datalive['data']['playlist']['medialist'][0]
                return doublemap, self.get_video_url(medialist.get('sources'))
            except KeyError:
                return doublemap, ""
        else:
            return doublemap, ""

    # def get_vitrina_live_double(self, channel_id, vitrina_code):
    #     """
    #     Get the live stream from Vitrina TV.
    #     @param channel_id: ID of the channel on smotrim.ru
    #     @param vitrina_code: alphanumeric code of the channel on Vitrina TV
    #     @return: channel ID map and a stream URL
    #     """
    #     doublemap = {"channel_id": str(channel_id),
    #                  "double_id": "1",
    #                  "vitrina_code": vitrina_code}
    #     result = self.site.request('%s/get_token' % self.vitrina_url, output="json")
    #     try:
    #         token = result['result']['token']
    #
    #         xbmc.log("Vitrina TV token=%s" % token)
    #
    #         vitrinalive = self.site.request('%s/api/v2/%s/playlist/%s_as_array.json?token=%s' %
    #                                         (self.vitrina_url,
    #                                          vitrina_code,
    #                                          vitrina_code,
    #                                          token),
    #                                         output="json")
    #
    #         return doublemap, vitrinalive['hls'][0]
    #     except KeyError:
    #         return doublemap, {}

    def get_channel_tvguide(self, channel_id, double_id):

        thisdate = kodiutils.get_date_from_timestamp()

        tvguide = self.site.request('%s/tvps/channels/%s/doubles/%s/?from=%s&depth=2' % (self.site.api_url,
                                                                                         channel_id,
                                                                                         double_id,
                                                                                         thisdate),
                                    output="json")

        if "data" in tvguide:
            return tvguide["data"]
        else:
            if "metadata" in tvguide:
                xbmc.log("Error querying TV Guide for %s:%s - %s %s" %
                         (channel_id, double_id, tvguide['metadata']['code'], tvguide['metadata']['errorMessage']))
            return []
