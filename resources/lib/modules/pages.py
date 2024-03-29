# -*- coding: utf-8 -*-
# Module: pages
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import json
import os
import time
import re

import xbmc
import xbmcgui
import xbmcplugin
import hashlib

from urllib.parse import quote as encode4url
from ..kodiutils import remove_files_by_pattern, upnext_signal, kodi_version_major, get_url
import resources.lib.kodiplayer as kodiplayer
from ..smotrim import USER_AGENT
from ..kodiutils import clean_html

MAXRECORDS = 9999


class Page(object):

    def __init__(self, site):
        self.site = site
        self.data = {}
        self.params = site.params
        self.action = site.action
        self.context = site.context
        self.list_items = []
        self.context_menu_items = []
        self.offset = 0
        self.limit = 0
        self.pages = 0

        self.cache_enabled = False
        self.cache_file = ""
        self.cache_expire = int(self.params.get('cache_expire', 0))

        self.KEYWORDS = []
        with open(os.path.join(self.site.path, "resources/data/keywords.json"), "r+", encoding="utf-8") as f:
            self.KEYWORDS = json.load(f)

        self.VQUALITY = ["auto", "fhd-wide", "hd-wide", "high-wide", "high", "medium-wide", "medium", "low-wide", "low"]

    def load(self):

        self.offset = self.params.get('offset', 0)
        self.limit = self.get_limit_setting()

        xbmc.log("Items per page: %s" % self.limit, xbmc.LOGDEBUG)

        self.preload()

        self.cache_file = self.get_cache_filename()

        xbmc.log("Cache file name: %s" % self.cache_file)

        self.data = self.get_data_query()

        self.set_context_title()

        self.set_limit_offset_pages()

        if self.pages > 1:
            if self.offset > 0:
                self.list_items.append(self.create_menu_li("previous",
                                                           label=30032, is_folder=True, is_playable=False,
                                                           url=self.get_nav_url(offset=self.offset - 1),
                                                           info={'plot': self.site.language(30031) %
                                                                         (self.offset + 1, self.pages)}))
            if self.offset > 1:
                self.list_items.append(self.create_menu_li("first", label=30033, is_folder=True, is_playable=False,
                                                           url=self.get_nav_url(offset=0),
                                                           info={'plot': self.site.language(30031) %
                                                                         (self.offset + 1, self.pages)}))

            self.list_items.append(self.create_menu_li("home", label=30020, is_folder=True, is_playable=False,
                                                       url=self.site.url,
                                                       info={'plot': self.site.language(30021)}))

        if 'data' in self.data:
            for element in self.data['data']:
                self.append_li_for_element(element)

            self.cache_data()

        if self.pages > 1:
            if self.offset < self.pages - 1:
                self.list_items.append(self.create_menu_li("last", label=30034, is_folder=True, is_playable=False,
                                                           url=self.get_nav_url(offset=self.pages - 1),
                                                           info={'plot': self.site.language(30031) % (
                                                               self.offset + 1, self.pages)}))
                self.list_items.append(self.create_menu_li("next", label=30030, is_folder=True, is_playable=False,
                                                           url=self.get_nav_url(offset=self.offset + 1),
                                                           info={'plot': self.site.language(30031) % (
                                                               self.offset + 1, self.pages)}))

        self.postload()

        self.show_list_items()

    def preload(self):
        """
        Override this function if it is necessary to perform some actions before preparing the list items
        @return:
        """
        pass

    def postload(self):
        """
        Override this function if it is necessary to perform some actions after preparing the list items
        @return:
        """
        pass

    def play(self):
        pass

    def play_url(self, url, this_episode=None, next_episode=None, stream_type="video"):

        xbmc.log("Play url: %s" % url, xbmc.LOGDEBUG)

        if next_episode is None:
            next_episode = {}

        brand = {}
        if 'brands' in self.params:
            resp = self.site.request(self.site.api_url + '/brands/' + self.params['brands'], output="json")
            if 'data' in resp:
                brand = resp['data']
            if self.site.addon.getSettingBool("addhistory"):
                self.save_brand_to_history(brand)

        play_item = xbmcgui.ListItem(path=self.site.prepare_url(url))

        play_item.setMimeType('application/x-mpegURL')
        if '.m3u8' in url:
            if kodi_version_major() >= 19:
                play_item.setProperty('inputstream', 'inputstream.adaptive')
            else:
                play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
            play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')

        if this_episode:
            play_item.setLabel(this_episode['combinedTitle'])

            self.enrich_info_tag(play_item, this_episode, brand)

            play_item.setArt({'fanart': get_pic_from_element(this_episode, 'hd'),
                              'icon': get_pic_from_element(this_episode, 'lw'),
                              'thumb': get_pic_from_element(this_episode, 'lw'),
                              'poster': get_pic_from_element(this_episode, 'vhdr')
                              })

            play_item.setProperty('IsPlayable', 'true')

            play_item.addStreamInfo(stream_type, {'duration': this_episode.get('duration')})

        xbmcplugin.setResolvedUrl(self.site.handle, True, listitem=play_item)

        if not self.site.addon.getSettingBool("upnext"):
            return

        # Wait for playback to start
        kodi_player = kodiplayer.KodiPlayer()
        if not kodi_player.waitForPlayBack(url=url):
            # Playback didn't start
            return

        if not (next_episode is None) and 'combinedTitle' in next_episode:
            upnext_signal(sender=self.site.id, next_info=self.get_next_info(this_episode, next_episode))

    def get_this_and_next_episode(self, episode_id):
        self.offset = self.params['offset'] if 'offset' in self.params else 0
        self.limit = self.get_limit_setting()

        self.cache_file = self.get_cache_filename()

        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r+') as f:
                self.data = json.load(f)
            for i, episode in enumerate(self.data['data']):
                if str(episode['id']) == episode_id:
                    return episode, self.data['data'][i + 1] if i < min(self.limit, len(self.data['data'])) - 1 else {}

            xbmc.log("Reached page bottom, loading next page?")
            return {}, {}
        else:
            return {}, {}

    def get_next_info(self, this_episode, next_episode):
        return {'current_episode': self.create_next_info(this_episode),
                'next_episode': self.create_next_info(next_episode),
                'play_url': self.get_play_url(next_episode)}

    def get_play_url(self, element):
        return ""

    def create_next_info(self, episode):
        """
        Returns the structure needed for service.upnext addon for playback of next episode.
        Called by get_next_info method.
        This method is to be overridden in case if the episode structure is not compatible

        @param episode:
        @return: nex_info structure for the specified episode
        """
        return {'episodeid': episode['id'],
                'tvshowid': self.params['brands'],
                'title': episode['episodeTitle'],
                'art': {'thumb': get_pic_from_element(episode, 'lw'),
                        'fanart': get_pic_from_element(episode, 'hd'),
                        'icon': get_pic_from_element(episode, 'lw'),
                        'poster': get_pic_from_element(episode, 'vhdr')
                        },
                'episode': episode['series'],
                'showtitle': episode['brandTitle'],
                'plot': episode['anons'],
                'playcount': 0,
                'runtime': episode['duration']
                }

    def create_element_li(self, element):
        return element

    def create_root_li(self):
        """
        This method can be optionally overridden if the the module class wants to expose a root-level menu.
        Usage is mainly from the lib.modules.home module.

        @return: the structure defining the list item
        """
        return {}

    def get_load_url(self):
        """
        This method is to be overridden in the child class to provide the url for querying the site. It is used in the
        get_data_query method and can be ignored if get_data_query is overriden in the child class.
        @return:
        """
        return ""

    def set_context_title(self):
        """
        This method is setting the title of the context by setting self.site.context_title attribute. Override if
        you want to create custom title, otherwise the context name will be used by default.
        """
        self.site.context_title = self.context.title()

    def get_data_query(self):

        if self.is_cache_available():
            return self.get_data_from_cache()
        else:
            return self.site.request(self.get_load_url(), output="json")

    def is_cache_available(self):
        is_refresh = 'refresh' in self.params and self.params['refresh'] == "true"
        if is_refresh:
            remove_files_by_pattern(os.path.join(self.site.data_path, "%s*.json" % self.get_cache_filename_prefix()))
        return (not is_refresh) and self.cache_enabled and \
               os.path.exists(self.cache_file) and not (self.is_cache_expired())

    def get_data_from_cache(self):
        with open(self.cache_file, 'r+') as f:
            xbmc.log("Loading from cache file: %s" % self.cache_file, xbmc.LOGDEBUG)
            return json.load(f)

    def is_cache_expired(self):

        if self.cache_expire == 0:
            # cache never expires
            return False

        mod_time = os.path.getmtime(self.cache_file)
        now = time.time()

        return int(now - mod_time) > self.cache_expire

    def get_nav_url(self, offset=0):
        return get_url(self.site.url,
                       action=self.site.action,
                       context=self.site.context,
                       limit=self.limit, offset=offset, url=self.site.url)

    def get_element_by_id(self, id):
        response = self.site.request(get_url("%s/%s/%s" % (self.site.api_url, self.context, str(id))), "json")
        return response.get('data', {})

    def append_li_for_element(self, element):
        li = self.create_element_li(element)
        if li:
            self.list_items.append(li)

    def get_limit_setting(self):
        return (self.site.addon.getSettingInt('itemsperpage') + 1) * 10

    def set_limit_offset_pages(self):
        if self.data.get('pagination'):
            self.offset = self.data['pagination'].get('offset', 0)
            self.limit = self.data['pagination'].get('limit', 0)
            self.pages = self.data['pagination'].get('pages', 0)

            if self.pages * self.limit >= MAXRECORDS:
                self.pages = int(MAXRECORDS / self.limit)
                xbmc.log("Max page limited to %d" % self.pages, xbmc.LOGDEBUG)

    def create_menu_li(self, label_id, label, is_folder, is_playable, url,
                       info=None, art=None,
                       lbl_format="[B][COLOR=FF00FF00]%s[/COLOR][/B]"):
        label_text = label if type(label) == str else self.site.language(label)
        return {'id': label_id, 'label': lbl_format % label_text, 'is_folder': is_folder, 'is_playable': is_playable,
                'url': url,
                'info': {'plot': label_text} if info is None else info,
                'art': {'icon': self.site.get_media("%s.png" % label_id),
                        'fanart': self.site.get_media("background.jpg")} if art is None else art}

    def get_pic_from_id(self, pic_id, res="lw"):
        if pic_id:
            return "|".join(["%s/pictures/%s/%s/redirect" % (self.site.cdnapi_url, pic_id, res),
                             "User-Agent=%s" % encode4url(USER_AGENT)])
        else:
            if res == "hd":
                return self.site.get_media("background.jpg")
            else:
                return ""

    @staticmethod
    def format_date(s):
        if s:
            return "%s-%s-%s %s:%s:%s" % (s[6:10], s[3:5], s[0:2], s[11:13], s[14:16], s[17:19])
        else:
            return ""

    @staticmethod
    def get_mpaa(age):
        if age == u'':
            return 'G'
        elif age == 6:
            return 'PG'
        elif age == 12:
            return 'PG-13'
        elif age == 16:
            return 'R'
        elif age == 18:
            return 'NC-17'
        else:
            return ''

    @staticmethod
    def get_country(countries):
        if countries:
            if type(countries) is list and len(countries) > 0:
                if type(countries[0]) is dict:
                    return countries[0].get('title')
                else:
                    return countries[0]

        return ""

    @staticmethod
    def get_logo(ch, res="xxl"):
        try:
            return ch['logo'][res]['url']
        except KeyError:
            return ""

    def get_person_thumbnail(self, name):
        name_hash = hashlib.md5(name.encode())
        return "%s/p%s.jpg" % (self.site.thumb_path, name_hash.hexdigest())

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

            if self.cache_enabled:
                self.context_menu_items = [(self.site.language(30001),
                                            "ActivateWindow(Videos, %s&refresh=true)" %
                                            self.get_nav_url(offset=0)), ]
            else:
                self.context_menu_items.clear()

            self.add_context_menu(category)

            if self.context_menu_items:
                list_item.addContextMenuItems(self.context_menu_items)

            if 'info' in category:
                list_item.setInfo(category['type'] if 'type' in category else "video", category['info'])

            if 'art' in category:
                list_item.setArt(category['art'])

            if 'cast' in category:
                list_item.setCast(category['cast'])

            xbmcplugin.addDirectoryItem(self.site.handle, url, list_item, is_folder)

        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.site.handle, cacheToDisc=False)

    def enrich_info_tag(self, list_item, episode, brand):
        """
        This function can be overridden to enrich the information available on the list item before passing to the
        player
        @param list_item: ListItem to be enriched
        @param episode: the element, which will be played
        @param brand: the element brand used for enrichment
        """
        pass

    def add_context_menu(self, category):
        """
        This function can be overriden to add context menu items
        @param category:
        @return:
        """
        pass

    def save_brand_to_history(self, brand):
        with open(os.path.join(self.site.history_path, "brand_%s.json" % brand['id']), 'w+') as f:
            json.dump(brand, f)

    def cache_data(self):
        if self.cache_enabled and len(self.data.get('data', [])) > 0 and \
                not (os.path.exists(self.cache_file) and not self.is_cache_expired()):
            with open(self.cache_file, 'w+') as f:
                json.dump(self.data, f)

    def get_cache_filename(self):
        return os.path.join(self.site.data_path,
                            "%s_%s_%s.json" % (self.get_cache_filename_prefix(),
                                               self.limit,
                                               self.offset))

    def get_cache_filename_prefix(self):
        return self.context

    def get_video_url(self, sources):
        if sources:
            vquality = int(self.site.addon.getSetting("vquality"))
            xbmc.log("Quality = %s" % vquality)
            if vquality > 0 and 'mp4' in sources:
                for vq in self.VQUALITY[vquality:]:
                    if vq in sources['mp4']:
                        return sources['mp4'].get(vq)

            return sources['m3u8'].get('auto')
        return ""

    def parse_body(self, element, tag='body'):
        result = {}
        if tag in element:
            body = element[tag]
            body_parts = clean_html(body).splitlines() if body else []
            delimiter = re.compile(r',|;')
            for key in self.KEYWORDS:
                if len(body_parts) > 0:
                    lbgroups = ["(%s)" % kw for kw in self.KEYWORDS[key]]
                    pattern = re.compile(r"(?:%s)(?P<text>.*)" % '|'.join(lbgroups), re.UNICODE)
                    for part in body_parts:
                        m = pattern.search(part)
                        if m:
                            result[key] = [x.strip() for x in delimiter.split(m.group('text'))]
                if not (key in result):
                    result[key] = []

            result['plot'] = "\r\n".join(body_parts)

        return result


def get_pic_from_plist(plist, res, append_headers=True):
    if plist:
        ep_pics = None
        if 'sizes' in plist:
            ep_pics = plist.get('sizes')
        elif len(plist) > 0:
            ep_pics = plist[0].get('sizes')

        if ep_pics:
            pic = next(p for p in ep_pics if p['preset'] == res)
            if append_headers:
                return "|".join([pic.get('url', ""), "User-Agent=%s" % encode4url(USER_AGENT)])
            else:
                return pic.get('url', "")

    return ""


def get_pic_from_element(element, res, append_headers=True):
    try:
        return get_pic_from_plist(element['pictures'], res, append_headers)
    except KeyError:
        return ""
