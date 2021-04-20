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

TAGS = [{'tag': 2994, 'title': "Премьеры"},
        {'tag': 1083, 'title': "Художественные фильмы"},
        {'tag': 10000001,
         'title': "Документальные фильмы",
         'tags': [{'tag': 231079, 'title': "Сейчас смотрят"},
                  {'tag': 231099, 'title': "Биографии"},
                  {'tag': 231100, 'title': "Политика"},
                  {'tag': 231080, 'title': "Общество"},
                  {'tag': 231101, 'title': "История"},
                  {'tag': 231102, 'title': "Спорт"},
                  {'tag': 231081, 'title': "Культура/Искусство"}]},
        {'tag': 1045, 'title': "Сериалы"},
        {'tag': 1080, 'title': "Популярные шоу"},
        {'tag': 1269, 'title': "Наука"},
        {'tag': 2463, 'title': "Фильмы о любви"},
        {'tag': 231939, 'title': "Искусство"},
        {'tag': 18578, 'title': "Классика"},
        {'tag': 1120, 'title': "Детям"},
        {'tag': 223821, 'title': "Самое-самое"}]


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
        self.ihome = os.path.join(self.path, 'resources/icons/home.png')

        self.api_url = "https://api.smotrim.ru/api/v1"

        self.search_text = ""

        # to save current context
        self.context = "home"
        self.context_title = "Home"

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

        self.context = self.params['action'] if 'action' in self.params else "home"

        xbmc.log("Action: %s" % self.context, xbmc.LOGINFO)

        if self.params:
            if self.params['action'] == 'play':
                self.play()
            else:
                getattr(self, self.context)()
                self.get_categories()
                self.menu()
        else:
            # default context is home
            self.get_categories()
            self.menu()

    def menu(self):

        xbmcplugin.setPluginCategory(self.handle, self.context_title)

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
            if 'data' in self.episodes:
                self.context_title = self.episodes['data'][0]['brandTitle'] if len(self.episodes) > 0 else "Серии"

    # Search by tag
    def search_by_tag(self):

        tag = int(self.params['tags']) if 'tags' in self.params else None
        parent = int(self.params['parent']) if 'parent' in self.params else 0
        limit, offset = self.get_limit_offset()

        if parent != 0:
            tags = next(T for T in TAGS if T['tag'] == parent)['tags']
            tag_dict = next(T for T in tags if T['tag'] == tag)
        else:
            tag_dict = next(T for T in TAGS if T['tag'] == tag)


        self.context_title = tag_dict['title']

        if 'tags' in tag_dict:
            pass
        else:
            self.search_by_url(self.get_url(self.api_url + '/brands',
                                            tags=tag,
                                            limit=limit,
                                            offset=offset) if tag else None)

    # Search by text
    def search(self):
        self.context_title = "Поиск"
        self.search_text = self.params['search'] if 'search' in self.params else self.get_user_input()
        limit, offset = self.get_limit_offset()
        self.search_by_url(self.get_url(self.api_url + '/brands',
                                        search=self.search_text,
                                        limit=limit,
                                        offset=offset) if self.search_text else None)

    def search_by_url(self, url):
        if url:
            xbmc.log("Load search results for url [ %s ] " % url, xbmc.LOGDEBUG)
            resp = requests.get(url)
            self.brands = resp.json()
        else:
            self.context = "home"

    def get_limit_offset(self):
        offset = self.params['offset'] if 'offset' in self.params else 0
        limit = (self.addon.getSettingInt('itemsperpage') + 1) * 10
        return limit, offset

    def get_limit_offset_pages(self, resp_dict):
        if 'pagination' in resp_dict:
            offset = resp_dict['pagination']['offset'] if 'pagination' in resp_dict else 0
            limit = resp_dict['pagination']['limit'] if 'pagination' in resp_dict else 0
            pages = resp_dict['pagination']['pages'] if 'pagination' in resp_dict else 0
            return limit, offset, pages
        else:
            return 0, 0, 0

    # Get categories for the current context
    def get_categories(self):

        xbmc.log("self.URL is %s" % self.url, xbmc.LOGINFO)

        if self.context == 'home':
            self.add_search()
            self.add_searches_by_tags(TAGS)

            if self.addon.getSettingBool("addhistory"):
                self.add_history()

        offset = 0
        pages = 0
        url = ""

        if self.context == "search":
            if 'data' in self.brands:
                limit, offset, pages = self.get_limit_offset_pages(self.brands)
                for brand in self.brands['data']:
                    self.categories.append(self.create_brand_dict(brand))
                url = self.get_url(self.url, action=self.context,
                                   search=self.search_text,
                                   offset=offset + 1,
                                   limit=limit,
                                   url=self.url)
        elif self.context == "search_by_tag":
            if 'data' in self.brands:
                limit, offset, pages = self.get_limit_offset_pages(self.brands)
                for brand in self.brands['data']:
                    self.categories.append(self.create_brand_dict(brand))
                url = self.get_url(self.url, action=self.context,
                                   tags=self.params['tags'],
                                   offset=offset + 1,
                                   limit=limit,
                                   url=self.url)
            else:
                tag_dict = next(T for T in TAGS if T['tag'] == int(self.params['tags']))
                if 'tags' in tag_dict:
                    self.add_searches_by_tags(tag_dict['tags'], tag_dict['tag'])

        elif self.context == "get_episodes":
            if 'data' in self.episodes:
                limit, offset, pages = self.get_limit_offset_pages(self.episodes)
                for ep in self.episodes['data']:
                    self.categories.append(self.create_episode_dict(ep))
                url = self.get_url(self.url, action=self.context,
                                   brands=self.params['brands'],
                                   offset=offset + 1,
                                   limit=limit,
                                   url=self.url)
        else:
            if 'data' in self.brands:
                for brand in self.brands['data']:
                    self.categories.append(self.create_brand_dict(brand))

        if offset < pages - 1 and pages > 1:
            self.categories.append({'id': "home",
                                    'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % "В начало",
                                    'is_folder': True,
                                    'url': self.url,
                                    'info': {'plot': "Вернуться на главную страницу" },
                                    'art': {'icon': self.ihome}
                                    })
            self.categories.append({'id': "forward",
                                    'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % "Вперед",
                                    'is_folder': True,
                                    'url': url,
                                    'info': {'plot': "Страница %s из %s" % (offset + 1, pages)},
                                    'art': {'icon': self.inext}
                                    })

    # Add Search menu to categories
    def add_search(self):
        self.categories.append({'id': "search",
                                'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % "Поиск",
                                'is_folder': True,
                                'url': self.get_url(self.url, action='search', url=self.url),
                                'info': {'plot': "Поиск по сайту Smotrim.ru"},
                                'art': {'icon': "DefaultAddonsSearch.png"}
                                })

    def add_search_by_tag(self, tag, tagname, taginfo=None, tagicon="DefaultAddonsSearch.png", parent=0):
        self.categories.append({'id': "tag%s" % str(tag),
                                'label': "[B]%s[/B]" % tagname,
                                'is_folder': True,
                                'url': self.get_url(self.url,
                                                    action='search_by_tag',
                                                    tags=tag,
                                                    parent=parent,
                                                    url=self.url),
                                'info': {'plot': taginfo if taginfo else tagname},
                                'art': {'icon': tagicon}
                                })

    def add_searches_by_tags(self, tags, parent=0):
        for tag in tags:
            self.add_search_by_tag(tag['tag'], tag['title'], tag['title'], parent=parent)

    def history(self):
        self.context_title = "История"
        limit = self.get_limit_setting()
        data = (os.path.join(self.history_folder, fn) for fn in os.listdir(self.history_folder))
        data = ((os.stat(path), path) for path in data)

        data = ((stat[ST_CTIME], path)
                for stat, path in data if S_ISREG(stat[ST_MODE]))
        self.brands = {'data': [], }
        for cdate, path in sorted(data, reverse=True):
            with open(path, 'r+') as f:
                xbmc.log("history len = %s" % len(self.brands['data']), xbmc.LOGDEBUG)
                if len(self.brands['data']) < limit:
                    self.brands['data'].append(json.load(f))
                else:
                    # autocleanup
                    os.remove(path)

    def save_brand_to_history(self, brand):
        with open(os.path.join(self.history_folder, "brand_%s.json" % brand['id']), 'w+') as f:
            json.dump(brand, f)

    def add_history(self):
        self.categories.append({'id': "history",
                                'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % "История",
                                'is_folder': True,
                                'url': self.get_url(self.url, action='history', url=self.url),
                                'info': {'plot': "Ваша история просмотров видео Smotrim.ru"},
                                'art': {'icon': self.ihistory}
                                })

    def create_brand_dict(self, brand):
        return {'id': brand['id'],
                'is_folder': brand['hasManySeries'],
                'label': "[B]%s[/B]" % brand['title'] if brand['hasManySeries'] else brand['title'],
                'url': self.get_url(self.url,
                                    action="get_episodes",
                                    brands=brand['id'],
                                    url=self.url) if brand['hasManySeries']
                else self.get_url(self.url,
                                  action="play",
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
