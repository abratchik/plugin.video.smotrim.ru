# coding=utf-8
# Module: main
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
Video plugin for Smotrim.ru portal
"""
import os
import sys
import time
from stat import S_ISREG, ST_CTIME, ST_MODE
import re
import json
import requests
from urllib import urlencode
from urlparse import parse_qsl

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

import lib.streamextractor as se

Addon = xbmcaddon.Addon(id='plugin.video.smotrim.ru')


# Main addon class
class Smotrim():

    def __init__(self):
        self.id = Addon.getAddonInfo('id')
        self.addon = xbmcaddon.Addon(self.id)
        self.path = self.addon.getAddonInfo('path').decode('utf-8')
        self.data_path = self.create_folder(os.path.join(self.path, 'data'))
        self.history_folder = self.create_folder(os.path.join(self.data_path, 'history'))

        self.url = sys.argv[0]
        self.handle = int(sys.argv[1])
        self.params = {}

        self.inext = os.path.join(self.path, 'resources/icons/next.png')
        self.ihistory = os.path.join(self.path, 'resources/icons/history.png')

        self.api_url = "https://api.smotrim.ru/api/v1"
        self.query_string = ""

        # file and dictionary to save current context
        self.context = "home"
        self.context_dict = {'home': {'label': 'Home'},
                             'search': {'label': 'Поиск'},
                             'episodes': {'label': 'Серии'},
                             'history': {'label': 'История'}}

        # list to hold current listing
        self.categories = []

        # list of brands
        self.brands = {}
        self.episodes = {}

        self.debug = True

    def main(self):
        xbmc.log("Addon: %s" % self.id, xbmc.LOGINFO)
        xbmc.log("Handle: %d" % self.handle, xbmc.LOGINFO)
        xbmc.log("Params: %s" % self.params, xbmc.LOGINFO)

        params_ = sys.argv[2]

        self.params = dict(parse_qsl(params_[1:]))

        if self.params:
            self.context = self.params['context'] if 'context' in self.params else self.context
            if self.params['action'] == 'episodes':
                self.get_episodes()
                self.get_categories()
                self.mainMenu()
            elif self.params['action'] == 'search':
                self.search()
                self.get_categories()
                self.mainMenu()
            elif self.params['action'] == 'history':
                self.history()
                self.get_categories()
                self.mainMenu()
            elif self.params['action'] == 'play':
                self.play()
            else:
                raise ValueError('Invalid paramstring: {}!'.format(params_))
        else:
            # default context is home
            self.get_categories()
            self.mainMenu()

    def mainMenu(self):

        xbmcplugin.setPluginCategory(self.handle, self.context_dict[self.context]['label'])

        xbmcplugin.setContent(self.handle, 'videos')

        # Iterate through categories
        for category in self.categories:
            # Create a list item with a text label and a thumbnail image.
            list_item = xbmcgui.ListItem(label=category['label'])

            list_item.setInfo('video', {'title': category['label']})

            url = category['url']

            is_folder = category['is_folder']
            list_item.setProperty('IsPlayable', 'false' if is_folder else 'true')
            if not is_folder:
                list_item.addContextMenuItems([('Information', 'XBMC.Action(Info)'), ])

            if 'info' in category:
                for info in category['info']:
                    list_item.setInfo('video', {info: category['info'][info]})

            if 'art' in category:
                for art in category['art']:
                    list_item.setArt({art: category['art'][art]})

            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(self.handle, url, list_item, is_folder)
        # Add a sort method for the virtual folder items (alphabetically)
        # xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_LABEL)
        # Finish creating a virtual folder.
        xbmcplugin.endOfDirectory(self.handle)

    def get_url(self, baseurl=None, **kwargs):
        baseurl_ = baseurl if baseurl else self.url
        url = '{}?{}'.format(baseurl_, urlencode(kwargs))
        return url

    # get series
    def get_episodes(self):

        brand = self.params['brands']

        offset = self.params['offset'] if 'offset' in self.params else 0
        limit = self.get_limit_setting()

        xbmc.log("items per page: %s" % limit, xbmc.LOGINFO)

        if brand:
            xbmc.log("Load episodes for brand [ %s ] " % brand, xbmc.LOGINFO)

            resp = requests.get(self.get_url(self.api_url + '/episodes',
                                             brands=brand,
                                             limit=limit,
                                             offset=offset))
            self.episodes = resp.json()

    # TODO: add more options for search
    def get_brands_by_tag(self):
        pass


    # Search by name
    def search(self):

        self.query_string = self.params['search'] if 'search' in self.params else self.get_user_input()
        offset = self.params['offset'] if 'offset' in self.params else 0
        limit = (self.addon.getSettingInt('itemsperpage') + 1) * 10

        xbmc.log("items per page: %s" % limit, xbmc.LOGINFO)

        if self.query_string:
            xbmc.log("Load search results for query [ %s ] " % self.query_string, xbmc.LOGINFO)

            resp = requests.get(self.get_url(self.api_url + '/brands',
                                             search=self.query_string,
                                             limit=limit,
                                             offset=offset))
            self.brands = resp.json()
        else:
            self.context = "home"

    # Get categories for the current context
    def get_categories(self):

        xbmc.log("self.URL is %s" % self.url, xbmc.LOGINFO)

        if self.context == 'home':
            self.add_search()
            if self.addon.getSettingBool("addhistory"):
                self.add_history()

        offset = self.brands['pagination']['offset'] if 'pagination' in self.brands else 0
        limit = self.brands['pagination']['limit'] if 'pagination' in self.brands else 0
        pages = self.brands['pagination']['pages'] if 'pagination' in self.brands else 0

        if 'data' in self.brands:
            for brand in self.brands['data']:
                self.categories.append(self.create_brand_dict(brand))

        elif 'data' in self.episodes:
            for ep in self.episodes['data']:
                self.categories.append(self.create_episode_dict(ep))
                self.context_dict['episodes']['label'] = ep['brandTitle']

        if (offset < pages - 1 and pages > 1):
            self.categories.append({'id': "forward",
                                    'label': "[B]%s[/B]" % "Вперед",
                                    'is_folder': True,
                                    'url': self.get_url(self.url, action=self.params['action'],
                                                        context=self.params['context'],
                                                        search=self.query_string,
                                                        offset=offset + 1,
                                                        limit=limit,
                                                        url=self.url),
                                    'info': {'plot': "Страница %s из %s" % (offset + 1, pages)},
                                    'art': {'icon': self.inext}
                                    })

    # Add Search menu to categories
    def add_search(self):
        self.categories.append({'id': "search",
                                'label': "[B]%s[/B]" % "Поиск",
                                'is_folder': True,
                                'url': self.get_url(self.url, action='search', context='search', url=self.url),
                                'info': {'plot': "Поиск по сайту Smotrim.ru"},
                                'art': {'icon': "DefaultAddonsSearch.png"}
                                })

    def history(self):
        limit = self.get_limit_setting()
        data = (os.path.join(self.history_folder, fn) for fn in os.listdir(self.history_folder))
        data = ((os.stat(path), path) for path in data)

        data = ((stat[ST_CTIME], path)
                for stat, path in data if S_ISREG(stat[ST_MODE]))
        self.brands = {'data': [], }
        for cdate, path in sorted(data, reverse=True):
            with open(path, 'r+') as f:
                print "history len = %s" % len(self.brands['data'])
                if len(self.brands['data']) < limit:
                       self.brands['data'].append(json.load(f))
                else:
                    # autocleanup
                    # TODO: add history pagination
                    os.remove(path)
                    

    def save_brand_to_history(self, brand):
        with open(os.path.join(self.history_folder, "brand_%s.json" % brand['id']), 'w+') as f:
            json.dump(brand, f)

    def add_history(self):
        self.categories.append({'id': "history",
                                'label': "[B]%s[/B]" % "История",
                                'is_folder': True,
                                'url': self.get_url(self.url, action='history', context='history', url=self.url),
                                'info': {'plot': "Ваша история просмотров видео Smotrim.ru"},
                                'art': {'icon': self.ihistory}
                                })

    def create_brand_dict(self, brand):
        return {'id': brand['id'],
                'is_folder': brand['hasManySeries'],
                'label': "[B]%s[/B]" % brand['title'] if brand['hasManySeries'] else brand['title'],
                'url': self.get_url(self.url,
                                    action="episodes",
                                    context="episodes",
                                    search=self.query_string,
                                    brands=brand['id'],
                                    url=self.url) if brand['hasManySeries']
                else self.get_url(self.url,
                                  action="play",
                                  context=self.context,
                                  search=self.query_string,
                                  brands=brand['id'],
                                  url=self.url),

                'info': {'genre': brand['genre'],
                         'mediatype': "tvshow" if brand['hasManySeries'] else "video",
                         'year': brand['productionYearStart'],
                         'plot': self.cleanhtml(brand['body']),
                         'plotoutline': brand['anons'],
                         'rating': brand['rank'],
                         'dateadded': brand['dateRec']
                         },
                'art': {'thumb': "%s/pictures/%s/lw/redirect" % (self.api_url, brand['picId']),
                        'icon': "%s/pictures/%s/lw/redirect" % (self.api_url, brand['picId']),
                        'fanart': "%s/pictures/%s/hd/redirect" % (self.api_url, brand['picId']),
                        'poster': "%s/pictures/%s/vhdr/redirect" % (self.api_url, brand['picId'])
                        }
                }

    def create_episode_dict(self, ep):
        return {'id': ep['id'],
                'label': ep['combinedTitle'],
                'is_folder': False,
                'url': self.get_url(self.url,
                                    action="play",
                                    context=self.context,
                                    search=self.query_string,
                                    brands=ep['brandId'],
                                    episodes=ep['id'],
                                    url=self.url),
                'info': {'mediatype': "episode",
                         'plot': self.cleanhtml(ep['body']),
                         'plotoutline': ep['anons'],
                         'episode': ep['series'],
                         'dateadded': ep['dateRec']
                         },
                'art': {'fanart': self.get_pic_from_plist(ep['pictures'], 'hd'),
                        'icon': self.get_pic_from_plist(ep['pictures'], 'lw'),
                        'thumb': self.get_pic_from_plist(ep['pictures'], 'lw'),
                        'poster': self.get_pic_from_plist(ep['pictures'], 'vhdr')
                        }
                }

    def get_user_input(self):
        kbd = xbmc.Keyboard()
        kbd.setDefault('')
        kbd.setHeading("Поиск")
        kbd.doModal()
        keyword = None

        if kbd.isConfirmed():
            keyword = kbd.getText()

        return keyword

    def play(self):

        if 'episodes' in self.params:
            videos = requests.get(self.get_url(self.api_url + '/videos', episodes=self.params['episodes'])).json()
        else:
            videos = requests.get(self.get_url(self.api_url + '/videos', brands=self.params['brands'])).json()

        try:
            player = videos['data'][0]['sources']['player']
            xbmc.log("Play video %s" % player, xbmc.LOGDEBUG)
            quality = self.addon.getSettingInt("quality")
            xbmc.log("Quality = %s" % quality, xbmc.LOGDEBUG)
            vid = se.getVideoInfo(player, quality=quality)
        except:
            vid = None

        if vid is None:
            self.show_error_message("Не удалось получить информацию о видео")
            return
        else:
            if vid.hasMultipleStreams():
                for stream in vid.streams():
                    xbmc.log("Found stream %s" % stream['formatID'], xbmc.LOGDEBUG)
            else:
                xbmc.log("Just one stream found - %s" % vid.streams()[0]['formatID'], xbmc.LOGDEBUG)

            spath = vid.streamURL()

        if self.addon.getSettingBool("addhistory"):
            resp = requests.get(self.get_url(self.api_url + '/brands/' + self.params['brands'])).json()
            self.save_brand_to_history(resp['data'])

        # Create a playable item with a path to play.
        play_item = xbmcgui.ListItem(path=spath)
        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(self.handle, True, listitem=play_item)

    def cleanhtml(self, raw_html):
        try:
            cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
            cleantext = re.sub(cleanr, '', raw_html)
            return cleantext
        except:
            return raw_html

    # *** Add-on helpers

    def create_folder(self, folder):
        if not (os.path.exists(folder) and os.path.isdir(folder)):
            os.makedirs(folder)
        return folder

    def error(self, message):
        xbmc.log("%s ERROR: %s" % (self.id, message), xbmc.LOGERROR)

    def show_error_message(self, msg):
        xbmc.log(msg, xbmc.LOGERROR)
        xbmc.executebuiltin("XBMC.Notification(%s,%s, %s)" % ("ERROR", msg, str(3 * 1000)))

    def get_pic_from_plist(self, plist, res):
        try:
            ep_pics = plist[0]['sizes']
            pic = next(p for p in ep_pics if p['preset'] == res)
            return pic['url']
        except:
            return ""

    def get_limit_setting(self):
        return (self.addon.getSettingInt('itemsperpage') + 1) * 10

if __name__ == '__main__':
    Smotrim = Smotrim()
    Smotrim.main()
