# -*- coding: utf-8 -*-
# Module: smotrim
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import json
import os
import sys
from stat import ST_CTIME, S_ISREG, ST_MODE

from urllib.parse import urlencode, parse_qsl

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

from . import utils


class Smotrim:

    def __init__(self):
        self.id = "plugin.video.smotrim.ru"
        self.addon = xbmcaddon.Addon(self.id)
        self.path = self.addon.getAddonInfo('path')
        self.mediapath = os.path.join(self.path, "resources/media")
        self.data_path = utils.create_folder(os.path.join(xbmc.translatePath(self.addon.getAddonInfo('profile')),
                                                          'data'))
        self.history_folder = utils.create_folder(os.path.join(self.data_path, 'history'))

        self.url = sys.argv[0]
        self.handle = int(sys.argv[1])
        self.params = {}

        self.isearch = os.path.join(self.mediapath, "search.png")
        self.inext = os.path.join(self.mediapath, 'next.png')
        self.ihistory = os.path.join(self.mediapath, 'history.png')
        self.iarticles = os.path.join(self.mediapath, 'news.png')
        self.ichannels = os.path.join(self.mediapath, 'channels.png')
        self.ihome = os.path.join(self.mediapath, 'home.png')
        self.background = os.path.join(self.mediapath, 'background.jpg')

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
        # list of episodes
        self.episodes = {}
        # list of articles
        self.articles = {}
        # list of channels
        self.channels = {}
        # channel menu
        self.channel_menu = {}

    def begin(self):
        xbmc.log("Addon: %s" % self.id, xbmc.LOGDEBUG)
        xbmc.log("Handle: %d" % self.handle, xbmc.LOGDEBUG)

        params_ = sys.argv[2]
        xbmc.log("Params: %s" % params_, xbmc.LOGDEBUG)
        self.params = dict(parse_qsl(params_[1:]))

        self.context = self.params['action'] if 'action' in self.params else "home"

        xbmc.log("Action: %s" % self.context, xbmc.LOGDEBUG)

        with open(os.path.join(self.path, "resources/data/tags.json"), "r+") as f:
            self.TAGS = json.load(f)

        self.load_cookies()

        if self.params:
            if self.params['action'] == 'play':
                self.play()
            else:
                getattr(self, self.context)()
                self.build_categories()
                self.menu()
        else:
            # default context is home
            self.build_categories()
            self.menu()

    def menu(self):

        xbmcplugin.setPluginCategory(self.handle, self.context_title)

        if self.context == "home":
            xbmcplugin.setContent(self.handle, "files")
        else:
            xbmcplugin.setContent(self.handle, self.params['content'] if "content" in self.params else "videos")

        # Iterate through categories
        for category in self.categories:
            # Create a list item with a text label and a thumbnail image.
            list_item = xbmcgui.ListItem(label=category['label'])

            url = category['url']

            is_folder = category['is_folder']
            list_item.setProperty('IsPlayable', str(category['is_playable']).lower())

            if 'info' in category:
                for info in category['info']:
                    list_item.setInfo('video', {info: category['info'][info]})
                    if info == 'mediatype':
                        list_item.addContextMenuItems([(self.language(30000),
                                                        "XBMC.Action(%s)" % ("Play"
                                                                             if category['info']['mediatype'] == "news"
                                                                             else "Info")
                                                        ), ])

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

        xbmc.log("items per page: %s" % limit, xbmc.LOGDEBUG)

        if brand:
            xbmc.log("Load episodes for brand [ %s ] " % brand, xbmc.LOGDEBUG)

            self.episodes = utils.httpget(self.get_url(self.api_url + '/episodes',
                                                       brands=brand,
                                                       limit=limit,
                                                       offset=offset))

            if 'data' in self.episodes:
                self.context_title = self.episodes['data'][0]['brandTitle'] \
                    if len(self.episodes) > 0 else self.language(30040)

    def get_channels(self):

        xbmc.log("Loading channels", xbmc.LOGDEBUG)

        self.channels = utils.httpget(self.get_url(self.api_url + "/channels"))
        self.context_title = self.language(30400)

    def get_channel_menu(self):
        offset = self.params['offset'] if 'offset' in self.params else 0
        limit = self.get_limit_setting()

        xbmc.log("items per page: %s" % limit, xbmc.LOGDEBUG)

        self.channel_menu = utils.httpget(self.get_url(self.api_url + '/menu/channels/' + self.params['channels'],
                                                       limit=limit,
                                                       offset=offset))

        self.context_title = self.params['title']

    # get artiles
    def get_articles(self):

        offset = self.params['offset'] if 'offset' in self.params else 0
        limit = self.get_limit_setting()

        xbmc.log("items per page: %s" % limit, xbmc.LOGDEBUG)

        self.articles = utils.httpget(self.get_url(self.api_url + '/articles',
                                                   limit=limit,
                                                   offset=offset))

        self.context_title = self.language(30301)

    # Search by tag
    def search_by_tag(self):

        tag = self.params['tags'] if 'tags' in self.params else None
        limit, offset = self.get_limit_offset()

        self.context_title = self.params['tagname']

        if 'has_children' in self.params and self.params['has_children'] == "True":
            pass
        else:
            self.search_by_url(self.get_url(self.api_url + '/brands',
                                            tags=tag,
                                            tagname=self.context_title,
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
        xbmc.log("Load search results for url [ %s ] " % url, xbmc.LOGDEBUG)
        if url:
            self.brands = utils.httpget(url)
        else:
            self.context = "home"

    def get_limit_offset(self):
        offset = self.params['offset'] if 'offset' in self.params else 0
        limit = (self.addon.getSettingInt('itemsperpage') + 1) * 10
        return limit, offset

    @staticmethod
    def get_limit_offset_pages(resp_dict):
        if 'pagination' in resp_dict:
            offset = resp_dict['pagination']['offset'] if 'pagination' in resp_dict else 0
            limit = resp_dict['pagination']['limit'] if 'pagination' in resp_dict else 0
            pages = resp_dict['pagination']['pages'] if 'pagination' in resp_dict else 0
            return limit, offset, pages
        else:
            return 0, 0, 0

    # Get categories for the current context
    def build_categories(self):

        xbmc.log("self.URL is %s" % self.url, xbmc.LOGDEBUG)

        if self.context == 'home':
            self.add_search()
            self.add_articles()
            self.add_channels()
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
                                   tagname=self.params['tagname'],
                                   offset=offset + 1,
                                   limit=limit,
                                   url=self.url)
            else:
                tag_dict = self.search_tag_by_id(self.TAGS, int(self.params['tags']))
                if 'tags' in tag_dict:
                    self.add_searches_by_tags(tag_dict['tags'])

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
        elif self.context == "get_articles":
            if 'data' in self.articles:
                limit, offset, pages = self.get_limit_offset_pages(self.articles)
                for ar in self.articles['data']:
                    self.categories.append(self.create_article_dict(ar))
                url = self.get_url(self.url, action=self.context,
                                   offset=offset + 1,
                                   limit=limit,
                                   url=self.url)
        elif self.context == "get_channels":
            if 'data' in self.channels:
                for ch in self.channels['data']:
                    self.categories.append(self.create_channel_dict(ch))
        elif self.context == "get_channel_menu":
            if 'data' in self.channel_menu:
                limit, offset, pages = self.get_limit_offset_pages(self.channel_menu)
                for cm in self.channel_menu['data']:
                    if cm['tags']:
                        self.add_search_by_tag(cm['tags'][0]['id'],
                                               cm['title'],
                                               cm['title'],
                                               tagicon=self.isearch,
                                               has_children=False)
                url = self.get_url(self.url,
                                   action=self.context,
                                   channels=self.params['channels'],
                                   title=self.params['title'],
                                   limit=limit,
                                   offset=offset + 1,
                                   url=self.url)
        else:
            if 'data' in self.brands:
                for brand in self.brands['data']:
                    self.categories.append(self.create_brand_dict(brand))

        if offset < pages - 1 and pages > 1:
            self.categories.append({'id': "home",
                                    'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.language(30020),
                                    'is_folder': True,
                                    'is_playable': False,
                                    'url': self.url,
                                    'info': {'plot': self.language(30021)},
                                    'art': {'icon': self.ihome}
                                    })
            self.categories.append({'id': "forward",
                                    'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.language(30030),
                                    'is_folder': True,
                                    'is_playable': False,
                                    'url': url,
                                    'info': {'plot': self.language(30031) % (offset + 1, pages)},
                                    'art': {'icon': self.inext}
                                    })

    # Add Search menu to categories
    def add_search(self):
        self.categories.append({'id': "search",
                                'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.language(30010),
                                'is_folder': True,
                                'is_playable': False,
                                'url': self.get_url(self.url, action='search', url=self.url),
                                'info': {'plot': self.language(30011)},
                                'art': {'icon': self.isearch,
                                        'fanart': self.background}
                                })

    def add_search_by_tag(self, tag, tagname,
                          taginfo=None, tagicon="DefaultAddonsSearch.png", content="videos", has_children=False):
        self.categories.append({'id': "tag%s" % str(tag),
                                'label': "[B]%s[/B]" % tagname,
                                'is_folder': True,
                                'is_playable': False,
                                'url': self.get_url(self.url,
                                                    action='search_by_tag',
                                                    tags=tag,
                                                    tagname=tagname,
                                                    has_children=has_children,
                                                    content=content,
                                                    url=self.url),
                                'info': {'plot': taginfo if taginfo else tagname},
                                'art': {'icon': tagicon,
                                        'fanart': self.background}
                                })

    def add_searches_by_tags(self, tags):
        for tag in tags:
            self.add_search_by_tag(tag['tag'],
                                   tagname=self.language(int(tag['titleId'])),
                                   taginfo=self.language(int(tag['titleId'])),
                                   tagicon=os.path.join(self.mediapath, tag['icon']) if 'icon' in tag
                                   else "DefaultAddonsSearch.png",
                                   content=tag['content'] if 'content' in tag else "videos",
                                   has_children=True if 'tags' in tag else False)

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

    def add_channels(self):
        self.categories.append({'id': "channels",
                                'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.language(30400),
                                'is_folder': True,
                                'is_playable': False,
                                'url': self.get_url(self.url, action='get_channels', url=self.url),
                                'info': {'plot': self.language(30400)},
                                'art': {'icon': self.ichannels,
                                        'fanart': self.background}
                                })

    def add_articles(self):
        self.categories.append({'id': "articles",
                                'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.language(30301),
                                'is_folder': True,
                                'is_playable': False,
                                'url': self.get_url(self.url, action='get_articles', url=self.url),
                                'info': {'plot': self.language(30301)},
                                'art': {'icon': self.iarticles,
                                        'fanart': self.background}
                                })

    def add_history(self):
        self.categories.append({'id': "history",
                                'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.language(30050),
                                'is_folder': True,
                                'is_playable': False,
                                'url': self.get_url(self.url, action='history', url=self.url),
                                'info': {'plot': self.language(30051)},
                                'art': {'icon': self.ihistory,
                                        'fanart': self.background}
                                })

    def create_article_dict(self, article):
        return {'id': article['id'],
                'is_folder': False,
                'is_playable': True if article['videos'] else False,
                'label': "[COLOR=FF00FFFF]%s[/COLOR] %s" % (self.language(30302), article['title'])
                if article['videos'] else article['title'],
                'url': self.get_url(self.url,
                                    action="play",
                                    articles=article['id'],
                                    videos=article['videos'][0]['id'],
                                    url=self.url) if article['videos'] else
                self.get_url(self.url,
                             action="play",
                             articles=article['id'],
                             url=self.url),
                'info': {'title': article['title'],
                         'mediatype': "video" if article['videos'] else "news",
                         'plot': utils.clean_html(article['body']),
                         'plotoutline': article['anons'],
                         'dateadded': article['datePub']
                         },
                'art': {'fanart': self.get_pic_from_plist(article['pictures'], 'hd'),
                        'icon': self.get_pic_from_plist(article['pictures'], 'lw'),
                        'thumb': self.get_pic_from_plist(article['pictures'], 'lw'),
                        'poster': self.get_pic_from_plist(article['pictures'], 'it')
                        }
                }

    def create_brand_dict(self, brand):
        is_folder = brand['hasManySeries'] or \
                    brand['countVideos'] > 1 or \
                    brand['countAudioEpisodes'] > 1
        is_music_folder = is_folder and brand['countAudioEpisodes'] == brand['countVideos']
        return {'id': brand['id'],
                'is_folder': is_folder,
                'is_playable': not is_folder,
                'label': "[B]%s[/B]" % brand['title'] if is_folder else brand['title'],
                'url': self.get_url(self.url,
                                    action="get_episodes",
                                    content="musicvideos" if is_music_folder else "episodes",
                                    brands=brand['id'],
                                    url=self.url) if is_folder
                else self.get_url(self.url,
                                  action="play",
                                  brands=brand['id'],
                                  url=self.url),

                'info': {'title': brand['title'],
                         'genre': brand['genre'],
                         'mediatype': "tvshow" if is_folder else "movie",
                         'year': brand['productionYearStart'],
                         'plot': utils.clean_html(brand['body']),
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

    def create_channel_dict(self, ch):
        return {'id': ch['id'],
                'label': ch['title'],
                'is_folder': True,
                'is_playable': False,
                'url': self.get_url(self.url,
                                    action="get_channel_menu",
                                    channels=ch['id'],
                                    title=ch['title'],
                                    url=self.url),
                'info': {'plot': ch['title']},
                'art': {'icon': self.get_channel_logo(ch, res="xxl"),
                        'fanart': self.background}
                }

    def create_episode_dict(self, ep):
        is_audio = ep['countAudios'] > 0
        return {'id': ep['id'],
                'label': ep['combinedTitle'],
                'is_folder': False,
                'is_playable': True,
                'url': self.get_url(self.url,
                                    action="play",
                                    brands=ep['brandId'],
                                    episodes=ep['id'],
                                    is_audio=is_audio,
                                    url=self.url),
                'info': {'title': ep['combinedTitle'],
                         'tvshowtitle': ep['brandTitle'],
                         'mediatype': "episode",
                         'plot': utils.clean_html(ep['body']),
                         'plotoutline': ep['anons'],
                         'episode': ep['series'],
                         'sortepisode': ep['series'],
                         'dateadded': ep['dateRec']
                         } if not is_audio else
                {'mediatype': "music",
                 'title': ep['title'],
                 'plot': "%s[CR]%s" % (ep['title'], ep['anons'])},
                'art': {'fanart': self.get_pic_from_plist(ep['pictures'], 'hd'),
                        'icon': self.get_pic_from_plist(ep['pictures'], 'lw'),
                        'thumb': self.get_pic_from_plist(ep['pictures'], 'lw'),
                        'poster': self.get_pic_from_plist(ep['pictures'], 'vhdr')
                        }
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
                    audios = utils.httpget(
                        self.get_url(self.api_url + '/audios', episodes=self.params['episodes']))
                    spath = audios['data'][0]['sources']['mp3']
                else:
                    videos = utils.httpget(
                        self.get_url(self.api_url + '/videos', episodes=self.params['episodes']))
                    spath = videos['data'][0]['sources']['m3u8']['auto']
            elif 'brands' in self.params:
                videos = utils.httpget(self.get_url(self.api_url + '/videos', brands=self.params['brands']))
                spath = videos['data'][0]['sources']['m3u8']['auto']
            elif 'articles' in self.params:
                articles = utils.httpget(self.get_url(self.api_url + '/articles/' + self.params['articles']))
                if articles['data']['videos']:
                    spath = articles['data']['videos'][0]['sources']['m3u8']['auto']
                else:
                    xbmcgui.Dialog().textviewer(articles['data']['title'], utils.clean_html(articles['data']['body']))
                    return
            elif 'videos' in self.params:
                videos = utils.httpget(self.api_url + '/videos/' + self.params['videos'])
                spath = videos['data']['sources']['m3u8']['auto']
            else:
                raise ValueError(self.language(30060))

            if self.addon.getSettingBool("addhistory") and 'brands' in self.params:
                resp = utils.httpget(self.api_url + '/brands/' + self.params['brands'])
                self.save_brand_to_history(resp['data'])
            play_item = xbmcgui.ListItem(path=spath)
            if '.m3u8' in spath:
                play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
                play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')

            xbmcplugin.setResolvedUrl(self.handle, True, listitem=play_item)
        except ValueError:
            utils.show_error_message(self.language(30060))

    @staticmethod
    def get_pic_from_plist(plist, res):
        try:
            ep_pics = plist[0]['sizes']
            pic = next(p for p in ep_pics if p['preset'] == res)
            return pic['url']
        except StopIteration:
            return ""
        except IndexError:
            return ""

    @staticmethod
    def get_channel_logo(ch, res="xxl"):
        try:
            return ch['logo'][res]['url']
        except KeyError:
            return ""

    def search_tag_by_id(self, tags, tag):
        for t in tags:
            if t['tag'] == tag:
                return t
            if 'tags' in t:
                ct = self.search_tag_by_id(t['tags'], tag)
                if ct:
                    return ct
        return {}

    def get_addon(self):
        return self.addon
    
    def get_data_path(self):
        return self.data_path

    # *** Add-on helpers


    def error(self, message):
        xbmc.log("%s ERROR: %s" % (self.id, message), xbmc.LOGDEBUG)

    def get_limit_setting(self):
        return (self.addon.getSettingInt('itemsperpage') + 1) * 10
