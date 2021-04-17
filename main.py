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
import re
import requests
from urllib import urlencode
from urlparse import parse_qsl
from bs4 import BeautifulSoup

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
        self.data_path = os.path.join(self.path, 'data')

        if not (os.path.exists(self.data_path) and os.path.isdir(self.data_path)):
            os.makedirs(self.data_path)

        self.url = sys.argv[0]
        self.handle = int(sys.argv[1])
        self.params = {}

        self.inext = os.path.join(self.path, 'resources/icons/next.png')
        self.ihistory = os.path.join(self.path, 'resources/icons/history.png')
        self.homepage = "https://smotrim.ru"

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
            if self.params['action'] == 'listing':
                # Load list items for current context
                self.get_episodes()
                self.get_categories()
                self.mainMenu()
            elif self.params['action'] == 'search':
                self.search()
                self.get_categories()
                self.mainMenu()
            elif self.params['action'] == 'history':
                self.get_categories()
                self.mainMenu()
            elif self.params['action'] == 'play':
                self.play_video(self.params['video'])
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

            if 'mediatype' in category:
                list_item.setInfo('video', {'mediatype': category['mediatype']})
            if 'genre' in category:
                list_item.setInfo('video', {'genre': category['genre']})
            if 'year' in category:
                list_item.setInfo('video', {'year': category['year']})
            if 'plot' in category:
                list_item.setInfo('video', {'plot': category['plot']})
            if 'plotoutline' in category:
                list_item.setInfo('video', {'plotoutline': category['plotoutline']})
            if 'episode' in category:
                list_item.setInfo('video', {'episode': category['episode']})

            if 'thumb' in category:
                list_item.setArt({'thumb': category['thumb']})
            if 'icon' in category:
                list_item.setArt({'icon': category['icon']})
            if 'fanart' in category:
                list_item.setArt({'fanart': category['fanart']})
            if 'poster' in category:
                list_item.setArt({'poster': category['poster']})


            if not is_folder:
                list_item.setProperty('IsPlayable', 'true')

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
        limit = (int(self.addon.getSetting('itemsperpage')) + 1) * 10

        xbmc.log("items per page: %s" % limit, xbmc.LOGINFO)

        if brand:
            xbmc.log("Load episodes for brand [ %s ] " % brand, xbmc.LOGINFO)

            resp = requests.get(self.get_url(self.api_url + '/episodes',
                                                             brands=brand,
                                                             limit=limit,
                                                             offset=offset))
            self.episodes = resp.json()

    # Search by name
    def search(self):

        self.query_string = self.params['search'] if 'search' in self.params else self.get_user_input()
        offset = self.params['offset'] if 'offset' in self.params else 0
        limit = (int(self.addon.getSetting('itemsperpage')) + 1) * 10

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
            #self.add_history()

        offset = self.brands['pagination']['offset'] if 'pagination' in self.brands else 0
        limit = self.brands['pagination']['limit'] if 'pagination' in self.brands else 0
        pages = self.brands['pagination']['pages'] if 'pagination' in self.brands else 0


        if 'data' in self.brands:
            for brand in self.brands['data']:
                brand_dict = dict()
                brand_dict['id'] = brand['id']

                brand_dict['href'] = brand['shareURL']
                brand_dict['is_folder'] = brand['hasManySeries']
                brand_dict['genre'] = brand['genre']
                if brand_dict['is_folder']:
                    brand_dict['label'] = "[B]%s[/B]" % brand['title']
                    brand_dict['url'] = self.get_url(self.url,
                                                     action="listing",
                                                     context="episodes",
                                                     brands=brand['id'],
                                                     url=self.url)
                else:
                    brand_dict['label'] = brand['title']
                    brand_dict['url'] = self.get_url(self.url,
                                                     action='play',
                                                     context=self.context,
                                                     video=brand['shareURL'],
                                                     url=self.url)
                brand_dict['thumb'] = "%s/pictures/%s/lw/redirect" % (self.api_url, brand['picId'])
                brand_dict['icon'] = "%s/pictures/%s/lw/redirect" % (self.api_url, brand['picId'])
                brand_dict['fanart'] = "%s/pictures/%s/hd/redirect" % (self.api_url, brand['picId'])
                brand_dict['poster'] = "%s/pictures/%s/vhdr/redirect" % (self.api_url, brand['picId'])

                brand_dict['mediatype'] = "tvshow" if brand['hasManySeries'] else "video"
                brand_dict['year'] = brand['productionYearStart']
                brand_dict['plot'] = self.cleanhtml(brand['body'])
                brand_dict['plotoutline'] = brand['anons']
                self.categories.append(brand_dict)
        elif 'data' in self.episodes:

            for ep in self.episodes['data']:
                ep_dict = dict()
                ep_dict['id'] = ep['id']
                ep_dict['label'] = ep['combinedTitle']
                ep_dict['href'] = ep['shareURL']
                ep_dict['is_folder'] = False

                ep_dict['url'] = self.get_url(self.url,
                                              action='play',
                                              context=self.context,
                                              video=ep['shareURL'],
                                              url=self.url)
                ep_dict['mediatype'] = "episode"
                ep_dict['plot'] = self.cleanhtml(ep['body'])
                ep_dict['plotoutline'] = ep['anons']
                ep_dict['fanart'] = self.get_pic_from_plist(ep['pictures'], 'hd')
                ep_dict['icon'] = self.get_pic_from_plist(ep['pictures'], 'lw')
                ep_dict['thumb'] = ep_dict['icon']
                ep_dict['poster'] = self.get_pic_from_plist(ep['pictures'], 'vhdr')
                ep_dict['episode'] = ep['series']
                self.categories.append(ep_dict)
                self.context_dict['episodes']['label'] = ep['brandTitle']


        if(offset < pages - 1 and pages > 1):
            brand_dict = dict()
            brand_dict['id'] = "forward"
            brand_dict['label'] = "[B]%s[/B]" % "Вперед"
            brand_dict['is_folder'] = True
            brand_dict['icon'] = self.inext
            brand_dict['plot'] = "Страница %s из %s" % (offset+1, pages)
            brand_dict['url'] = self.get_url(self.url, action=self.params['action'],
                                             context=self.params['context'],
                                             search=self.query_string,
                                             offset=offset + 1,
                                             limit=limit,
                                             url=self.url)
            self.categories.append(brand_dict)

    # Add Search menu to categories
    def add_search(self):
        search_dict = dict()
        search_dict['id'] = "search"
        search_dict['label'] = "[B]%s[/B]" % "Поиск"
        search_dict['is_folder'] = True
        search_dict['icon'] = "DefaultAddonsSearch.png"
        search_dict['url'] = self.get_url(self.url, action='search', context='search', url=self.url)
        search_dict['plot'] = "Поиск по сайту Smotrim.ru"
        self.categories.append(search_dict)

    def add_history(self):
        hist_dict = dict()
        hist_dict['id'] = "history"
        hist_dict['label'] = "[B]%s[/B]" % "История"
        hist_dict['is_folder'] = True
        hist_dict['icon'] = self.ihistory
        hist_dict['url'] = self.get_url(self.url, action='history', context='history', url=self.url)
        hist_dict['plot'] = "Ваша история просмотров видео Smotrim.ru"
        self.categories.append(hist_dict)

    def get_user_input(self):
        kbd = xbmc.Keyboard()
        kbd.setDefault('')
        kbd.setHeading("Поиск")
        kbd.doModal()
        keyword = None

        if kbd.isConfirmed():
            keyword = kbd.getText()

        return keyword

    def play_video(self, href):

        http_doc = requests.get(href)
        soup = BeautifulSoup(http_doc.text, 'html.parser')
        xbmc.log("Now we have SOUP %s, bon appetit!" % soup.name, xbmc.LOGINFO)

        path = ""
        playcontrol = soup.find_all("iframe", limit=1)
        if playcontrol:
            path = playcontrol[0]["src"]
        else:
            playcontrol = soup.find_all("div", "program-top__video", limit=1)
            if playcontrol:
                videoid = playcontrol[0].a['href'].split('/')[2]
                path = "https://player.vgtrk.com/iframe/video/id/%s/start_zoom/true/showZoomBtn/false/sid/smotrim" \
                       "/isPlay/true/mute/false/" % videoid

        xbmc.log("Play video %s" % path, xbmc.LOGINFO)
        quality = int(self.addon.getSetting("quality"))

        xbmc.log("Quality = %s" % quality, xbmc.LOGINFO)

        vid = se.getVideoInfo(path, quality = quality)

        if vid is None:
            self.show_error_message("Failed to extract video %s" % href)
            spath = path
        else:
            if vid.hasMultipleStreams():
                for stream in vid.streams():
                    print stream['formatID']
            else:
                print "Just one stream found - %s" % vid.streams()[0]['formatID']

            spath = vid.streamURL()

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

if __name__ == '__main__':
    Smotrim = Smotrim()
    Smotrim.main()
