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
import urllib2
from urllib import urlencode
from urlparse import parse_qsl

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

Addon = xbmcaddon.Addon(id='plugin.video.smotrim.ru')


# Main addon class
class Smotrim():

    def __init__(self):
        self.id = Addon.getAddonInfo('id')
        self.addon = xbmcaddon.Addon(self.id)
        self.path = self.addon.getAddonInfo('path').decode('utf-8')
        self.iconpath = os.path.join(self.path, "resources/icons")
        self.data_path = self.create_folder(os.path.join(self.path, 'data'))
        self.history_folder = self.create_folder(os.path.join(self.data_path, 'history'))

        self.url = sys.argv[0]
        self.handle = int(sys.argv[1])
        self.params = {}

        self.inext = os.path.join(self.iconpath, 'next.png')
        self.ihistory = os.path.join(self.iconpath, 'history.png')
        self.ihome = os.path.join(self.iconpath, 'home.png')

        self.api_url = "https://api.smotrim.ru/api/v1"

        self.search_text = ""

        self.language = self.addon.getLocalizedString

        # to save current context
        self.context = "home"
        self.context_title = self.language(30300)

        # list to hold current listing
        self.categories = []

        # list of brands
        self.brands = {}
        self.episodes = {}

        self.TAGS = [{'tag': 2994, 'title': self.language(30200), 'icon': "premieres.png"},
                     {'tag': 1083, 'title': self.language(30201), 'icon': "cinema.png"},
                     {'tag': 10000002,
                      'title': self.language(30202),
                      'tags': [{'tag': 231079, 'title': self.language(30203)},
                               {'tag': 231099, 'title': self.language(30204)},
                               {'tag': 231100, 'title': self.language(30205)},
                               {'tag': 231080, 'title': self.language(30206)},
                               {'tag': 231101, 'title': self.language(30207)},
                               {'tag': 231102, 'title': self.language(30208)},
                               {'tag': 231081, 'title': self.language(30209)}],
                      'icon': "documentary.png"},
                     {'tag': 1045, 'title': self.language(30210), 'icon': "series.png"},
                     {'tag': 1080, 'title': self.language(30211), 'icon': "tvshow.png"},
                     {'tag': 1269, 'title': self.language(30212), 'icon': "sience.png"},
                     {'tag': 1048, 'title': self.language(30213), 'icon': "drama.png"},
                     {'tag': 2463, 'title': self.language(30214), 'icon': "lovestories.png"},
                     {'tag': 4038, 'title': self.language(30215), 'icon': "melodrama.png"},
                     {'tag': 1108, 'title': self.language(30216), 'icon': "crime.png"},
                     {'tag': 1049, 'title': self.language(30217), 'icon': "screenversions.png"},
                     {'tag': 231939, 'title': self.language(30218), 'icon': "art.png"},
                     {'tag': 18578, 'title': self.language(30219), 'icon': "classics.png"},
                     {'tag': 3931, 'title': self.language(30220), 'icon': "historical.png"},
                     {'tag': 1120, 'title': self.language(30221), 'icon': "children.png"},
                     {'tag': 223821, 'title': self.language(30222), 'icon': "ourpicks.png"},
                     {'tag': 1072, 'title': self.language(30223), 'icon': "comedy.png"}]

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

        if self.context == "home":
            xbmcplugin.setContent(self.handle, 'files')
        else:
            xbmcplugin.setContent(self.handle, 'videos')

        # Iterate through categories
        for category in self.categories:
            # Create a list item with a text label and a thumbnail image.
            list_item = xbmcgui.ListItem(label=category['label'])

            url = category['url']

            is_folder = category['is_folder']
            list_item.setProperty('IsPlayable', 'false' if is_folder else 'true')
            if not is_folder:
                list_item.addContextMenuItems([(self.language(30000), 'XBMC.Action(Info)'), ])

            if 'info' in category:
                for info in category['info']:
                    list_item.setInfo('video', {info: category['info'][info]})

            if 'art' in category:
                for art in category['art']:
                    list_item.setArt({art: category['art'][art]})

            xbmcplugin.addDirectoryItem(self.handle, url, list_item, is_folder)

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

            self.episodes = self.get(self.get_url(self.api_url + '/episodes',
                                                  brands=brand,
                                                  limit=limit,
                                                  offset=offset))

            if 'data' in self.episodes:
                self.context_title = self.episodes['data'][0]['brandTitle'] \
                    if len(self.episodes) > 0 else self.language(30040)

    # Search by tag
    def search_by_tag(self):

        tag = int(self.params['tags']) if 'tags' in self.params else None
        parent = int(self.params['parent']) if 'parent' in self.params else 0
        limit, offset = self.get_limit_offset()

        if parent != 0:
            tags = next(T for T in self.TAGS if T['tag'] == parent)['tags']
            tag_dict = next(T for T in tags if T['tag'] == tag)
        else:
            tag_dict = next(T for T in self.TAGS if T['tag'] == tag)

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
        self.context_title = self.language(30010)
        self.search_text = self.params['search'] if 'search' in self.params else self.get_user_input()
        limit, offset = self.get_limit_offset()
        self.search_by_url(self.get_url(self.api_url + '/brands',
                                        search=self.search_text,
                                        limit=limit,
                                        offset=offset) if self.search_text else None)

    def search_by_url(self, url):
        if url:
            xbmc.log("Load search results for url [ %s ] " % url, xbmc.LOGDEBUG)
            self.brands = self.get(url)
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
            self.add_searches_by_tags(self.TAGS)

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
                tag_dict = next(T for T in self.TAGS if T['tag'] == int(self.params['tags']))
                if 'tags' in tag_dict:
                    self.add_searches_by_tags(tag_dict['tags'], tag_dict['tag'])

        elif self.context == "get_episodes":
            if 'data' in self.episodes:
                limit, offset, pages = self.get_limit_offset_pages(self.episodes)
                for ep in self.episodes['data']:
                    if ep['countVideos'] > 0 or ep['countAudios'] > 0:
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
                                    'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.language(30020),
                                    'is_folder': True,
                                    'url': self.url,
                                    'info': {'plot': self.language(30021)},
                                    'art': {'icon': self.ihome}
                                    })
            self.categories.append({'id': "forward",
                                    'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.language(30030),
                                    'is_folder': True,
                                    'url': url,
                                    'info': {'plot': self.language(30031) % (offset + 1, pages)},
                                    'art': {'icon': self.inext}
                                    })

    # Add Search menu to categories
    def add_search(self):
        self.categories.append({'id': "search",
                                'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.language(30010),
                                'is_folder': True,
                                'url': self.get_url(self.url, action='search', url=self.url),
                                'info': {'plot': self.language(30011)},
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
            self.add_search_by_tag(tag['tag'],
                                   tagname=tag['title'],
                                   taginfo=tag['title'],
                                   tagicon=os.path.join(self.iconpath, tag['icon']) if 'icon' in tag
                                   else "DefaultAddonsSearch.png",
                                   parent=parent)

    def history(self):
        self.context_title = self.language(30050)
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
                                'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.language(30050),
                                'is_folder': True,
                                'url': self.get_url(self.url, action='history', url=self.url),
                                'info': {'plot': self.language(30051)},
                                'art': {'icon': self.ihistory}
                                })

    def create_brand_dict(self, brand):
        is_folder = brand['hasManySeries'] or \
                    brand['countVideos'] > 1 or \
                    brand['countAudioEpisodes'] > 1
        return {'id': brand['id'],
                'is_folder': is_folder,
                'label': "[B]%s[/B]" % brand['title'] if is_folder else brand['title'],
                'url': self.get_url(self.url,
                                    action="get_episodes",
                                    brands=brand['id'],
                                    url=self.url) if is_folder
                else self.get_url(self.url,
                                  action="play",
                                  brands=brand['id'],
                                  url=self.url),

                'info': {'title': brand['title'],
                         'genre': brand['genre'],
                         'mediatype': "tvshow" if is_folder else "video",
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
        is_audio = ep['countAudios'] > 0
        return {'id': ep['id'],
                'label': ep['combinedTitle'],
                'is_folder': False,
                'url': self.get_url(self.url,
                                    action="play",
                                    brands=ep['brandId'],
                                    episodes=ep['id'],
                                    is_audio=is_audio,
                                    url=self.url),
                'info': {'title': ep['combinedTitle'],
                         'mediatype': "episode",
                         'plot': self.cleanhtml(ep['body']),
                         'plotoutline': ep['anons'],
                         'episode': ep['series'],
                         'dateadded': ep['dateRec']
                         } if not is_audio else
                {'mediatype': "music",
                 'plot': ep['title']},
                'art': {'fanart': self.get_pic_from_plist(ep['pictures'], 'hd'),
                        'icon': self.get_pic_from_plist(ep['pictures'], 'lw'),
                        'thumb': self.get_pic_from_plist(ep['pictures'], 'lw'),
                        'poster': self.get_pic_from_plist(ep['pictures'], 'vhdr')
                        } if not is_audio else
                {'icon': "DefaultAudio.png",
                 'thumb': "DefaultAudio.png"}
                }

    def get_user_input(self):
        kbd = xbmc.Keyboard()
        kbd.setDefault('')
        kbd.setHeading(self.language(30010))
        kbd.doModal()
        keyword = None

        if kbd.isConfirmed():
            keyword = kbd.getText()

        return keyword

    def play(self):

        try:
            if 'episodes' in self.params:
                if json.loads(self.params['is_audio'].lower()):
                    audios = self.get(
                        self.get_url(self.api_url + '/audios', episodes=self.params['episodes']))
                    spath = audios['data'][0]['sources']['mp3']
                else:
                    videos = self.get(
                        self.get_url(self.api_url + '/videos', episodes=self.params['episodes']))
                    spath = videos['data'][0]['sources']['m3u8']['auto']
            else:
                videos = self.get(self.get_url(self.api_url + '/videos', brands=self.params['brands']))
                spath = videos['data'][0]['sources']['m3u8']['auto']

            if self.addon.getSettingBool("addhistory"):
                resp = self.get(self.get_url(self.api_url + '/brands/' + self.params['brands']))
                self.save_brand_to_history(resp['data'])
            play_item = xbmcgui.ListItem(path=spath)
            if '.m3u8' in spath:
                play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
                play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
            xbmcplugin.setResolvedUrl(self.handle, True, listitem=play_item)
        except:
            self.show_error_message(self.language(30060))

    def cleanhtml(self, raw_html):
        try:
            cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
            cleantext = re.sub(cleanr, '', raw_html)
            return cleantext
        except:
            return raw_html

    # *** Add-on helpers

    def get(self, url):
        response = urllib2.urlopen(url)
        return json.load(response)

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
