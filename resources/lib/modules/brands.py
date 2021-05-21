# -*- coding: utf-8 -*-
# Module: brands
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import json
import os
import re

import resources.lib.modules.pages as pages

from ..kodiutils import clean_html


class Brand(pages.Page):
    def __init__(self, site):
        self.search_text = ""
        self.search_tag = ""
        super(Brand, self).__init__(site)
        self.TAGS = []
        with open(os.path.join(self.site.path, "resources/data/tags.json"), "r+") as f:
            self.TAGS = json.load(f)

        self.KEYWORDS = []
        with open(os.path.join(self.site.path, "resources/data/keywords.json"), "r+") as f:
            self.KEYWORDS = json.load(f)

    def search(self):
        if not ('search' in self.params):
            self.search_text = self.site.get_user_input()
            if self.search_text:
                import resources.lib.modules.searches as searches
                search = searches.Search(self.site)
                search.save_to_history(self.search_text)
        else:
            self.search_text = self.params['search']

        self.load()

    def search_by_tag(self):
        self.search_tag = self.params['tags'] if 'tags' in self.params else ""
        self.load()

    def create_search_li(self):
        return {'id': "search",
                'label': "[COLOR=FF00FF00][B]%s[/B][/COLOR]" % self.site.language(30010),
                'is_folder': True,
                'is_playable': False,
                'url': self.site.get_url(self.site.url, action="search", context="brands", url=self.site.url),
                'info': {'plot': self.site.language(30011)},
                'art': {'icon': self.site.get_media("search.png"),
                        'fanart': self.site.get_media("background.jpg")}
                }

    def create_search_by_tag_li(self, tag, tagname, taginfo=None, tagicon="DefaultAddonsSearch.png",
                                content="videos", has_children=False, cache_expire="0"):
        """

        @param tag: tag id
        @param tagname: tag name
        @param taginfo: tag description
        @param tagicon: tag icon
        @param content: content type in the context of this tag. Can be one of the following: videos (default),
        files, songs, musicvideos, tvshows, episodes, movies
        @param has_children: if true the eliement is interpreted as tag group (like submenu)
        @param cache_expire: number of seconds for cache to expire. Default is "0" meaning cache will never expire
        @return:
        """
        return {'id': "tag%s" % tag,
                'label': "[B]%s[/B]" % tagname,
                'is_folder': True,
                'is_playable': False,
                'url': self.site.get_url(self.site.url,
                                         action="search_by_tag",
                                         context="brands",
                                         tags=tag,
                                         tagname=tagname,
                                         has_children=has_children,
                                         content=content,
                                         cache_expire=cache_expire,
                                         url=self.site.url),
                'info': {'plot': taginfo if taginfo else tagname},
                'art': {'icon': tagicon,
                        'fanart': self.site.get_media("background.jpg")}
                }

    def create_search_by_tag_lis(self, tags=None):
        if tags is None:
            tags = self.TAGS

        for tag in tags:
            yield self.create_search_by_tag_li(str(tag['tag']),
                                               tagname=self.site.language(int(tag['titleId'])).encode('utf-8', 'ignore'),
                                               taginfo=self.site.language(int(tag['titleId'])).encode('utf-8', 'ignore'),
                                               tagicon=self.site.get_media(tag['icon']) if 'icon' in tag
                                               else "DefaultAddonsSearch.png",
                                               content=tag['content'] if 'content' in tag else "videos",
                                               has_children=True if 'tags' in tag else False)

    def set_context_title(self):
        if self.action == "search_by_tag":
            self.site.context_title = self.params['tagname']
        else:
            self.site.context_title = self.site.language(30010)

    def get_nav_url(self, offset=0):
        if self.action == "search" and self.search_text:
            return self.site.get_url(self.site.url, action=self.action,
                                     context="brands",
                                     search=self.search_text,
                                     offset=offset,
                                     limit=self.limit,
                                     url=self.site.url)
        elif self.action == "search_by_tag" and self.search_tag:
            return self.site.get_url(self.site.url, action=self.action,
                                     context="brands",
                                     tags=self.search_tag,
                                     tagname=self.params['tagname'],
                                     has_children=self.params['has_children'],
                                     content=self.params['content'],
                                     offset=offset,
                                     limit=self.limit,
                                     url=self.site.url)
        else:
            return self.site.get_url(self.site.url, action=self.action,
                                     context="brands",
                                     offset=offset,
                                     limit=self.limit,
                                     url=self.site.url)

    def get_data_query(self):
        if 'has_children' in self.params and self.params['has_children'] == "True":
            tag_dict = self.get_tag_by_id(self.TAGS, int(self.params['tags']))
            if 'tags' in tag_dict:
                return {'data': list(self.create_search_by_tag_lis(tag_dict['tags']))}
            return {}
        else:
            return super(Brand, self).get_data_query()

    def get_load_url(self):
        if self.action == "search" and self.search_text:
            return self.site.get_url(self.site.api_url + '/brands',
                                     search=self.search_text,
                                     limit=self.limit,
                                     offset=self.offset)
        elif self.action == "search_by_tag" and self.search_tag:
            return self.site.get_url(self.site.api_url + '/brands',
                                     tags=self.search_tag,
                                     limit=self.limit,
                                     offset=self.offset)
        else:
            return self.site.get_url(self.site.api_url + '/brands',
                                     limit=self.limit,
                                     offset=self.offset)

    def play(self):

        videos = self.site.request(self.site.get_url(self.site.api_url + '/videos', brands=self.params['brands']),
                                   output="json")
        if len(videos['data']) > 0:
            spath = videos['data'][0]['sources']['m3u8']['auto']

            self.play_url(spath, videos['data'][0])

    def create_element_li(self, element):

        if 'has_children' in self.params and self.params['has_children'] == "True":
            return super(Brand, self).create_element_li(element)
        else:
            is_folder = element['countVideos'] > 1 or element['countAudioEpisodes'] > 1
            is_music_folder = is_folder and element['countAudioEpisodes'] == element['countVideos']
            label = self.get_label(element)
            bp = self.parse_body(element['body'])
            return {'id': element['id'],
                    'is_folder': is_folder,
                    'is_playable': not is_folder,
                    'label': "[B]%s[/B]" % label if is_folder else label,
                    'url': self.site.get_url(self.site.url,
                                             action="load",
                                             context="audios" if is_music_folder else "videos",
                                             content="musicvideos" if is_music_folder else "episodes",
                                             brands=element['id'],
                                             cache_expire=str(self.cache_expire),
                                             url=self.site.url) if is_folder
                    else self.site.get_url(self.site.url,
                                           action="play",
                                           context="brands",
                                           brands=element['id'],
                                           url=self.site.url),
                    'info': {'title': element['title'],
                             'sorttitle': element['title'],
                             'originaltitle': element['titleOrig'],
                             'genre': element['genre'],
                             'mediatype': "tvshow" if is_folder else "movie",
                             'year': element['productionYearStart'],
                             'country': self.get_country(element['countries']),
                             'mpaa': self.get_mpaa(element['ageRestrictions']),
                             'plot': bp['plot'],
                             'cast': bp['cast'],
                             'director': bp['director'],
                             'writer': bp['writer'],
                             'plotoutline': element['anons'],
                             'rating': element['rank'],
                             'dateadded': self.format_date(element['dateRec'])
                             },
                    'art': {'thumb': "%s/pictures/%s/lw/redirect" % (self.site.api_url, element['picId']),
                            'icon': "%s/pictures/%s/lw/redirect" % (self.site.api_url, element['picId']),
                            'fanart': "%s/pictures/%s/hd/redirect" % (self.site.api_url, element['picId']),
                            'poster': "%s/pictures/%s/vhdr/redirect" % (self.site.api_url, element['picId'])
                            }
                    }

    def get_tag_by_id(self, tags, tag):
        for t in tags:
            if t['tag'] == tag:
                return t
            if 'tags' in t:
                ct = self.get_tag_by_id(t['tags'], tag)
                if ct:
                    return ct
        return {}

    @staticmethod
    def get_label(brand):
        rank = brand['rank']
        if rank:
            color = "FF00FF00" if rank >= 7.0 else "yellow" if (7.0 > rank >= 5.0) else "red"
            return "[COLOR %s][%s][/COLOR] %s" % (color, rank, brand['title'])
        else:
            return brand['title']

    def parse_body(self, body):
        result = {}

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
