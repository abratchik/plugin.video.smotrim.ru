# -*- coding: utf-8 -*-
# Module: brands
# Author: Alex Bratchik
# Created on: 03.04.2021
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
import json
import os

import xbmc

import resources.lib.modules.pages as pages
import resources.lib.modules.persons as persons

from resources.lib.kodiutils import notify, get_url


class Brand(pages.Page):
    def __init__(self, site):
        self.search_text = ""
        self.search_tag = ""
        self.search_person = ""
        super(Brand, self).__init__(site)
        self.TAGS = []
        with open(os.path.join(self.site.path, "resources/data/tags.json"), "r+") as f:
            self.TAGS = json.load(f)

    def search(self):
        if not ('search' in self.params):
            self.search_text = self.site.get_user_input()
            if self.search_text:
                import resources.lib.modules.searches as searches
                search = searches.Search(self.site)
                search.save_to_history(self.search_text)

                url = self.get_nav_url(offset=0)

                xbmc.executebuiltin("Container.Update(%s)" % url)
                return
        else:
            self.search_text = self.params['search']

        self.load()

    def search_by_tag(self):
        self.search_tag = self.params.get('tags', "")
        self.load()

    def search_by_person(self):
        self.search_person = self.params.get('persons', "")
        self.cache_enabled = True
        self.load()

    def create_search_by_tag_li(self, tag, tagname, taginfo=None, tagicon="DefaultAddonsSearch.png",
                                content="videos", has_children=False, cache_expire="0"):
        """

        @param tag: tag id
        @param tagname: tag name
        @param taginfo: tag description
        @param tagicon: tag icon
        @param content: content type in the context of this tag. Can be one of the following: videos (default),
        files, songs, musicvideos, tvshows, episodes, movies
        @param has_children: if true the element is interpreted as tag group (like submenu)
        @param cache_expire: number of seconds for cache to expire. Default is "0" meaning cache will never expire
        @return:
        """
        return {'id': "tag%s" % tag,
                'label': "[B]%s[/B]" % tagname,
                'is_folder': True,
                'is_playable': False,
                'url': get_url(self.site.url,
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
                                               tagname=self.site.language(int(tag['titleId'])),
                                               taginfo=self.site.language(int(tag['titleId'])),
                                               tagicon=self.site.get_media(tag['icon']) if 'icon' in tag
                                               else "DefaultAddonsSearch.png",
                                               content=tag['content'] if 'content' in tag else "videos",
                                               has_children=True if 'tags' in tag else False,
                                               cache_expire="86400")

    def set_context_title(self):
        if self.action == "search_by_tag":
            self.site.context_title = self.params['tagname']
        else:
            self.site.context_title = self.site.language(30010)

    def get_nav_url(self, offset=0):
        if self.action == "search" and self.search_text:
            return get_url(self.site.url, action=self.action,
                           context="brands",
                           search=self.search_text,
                           cache_expire=str(self.cache_expire),
                           offset=offset,
                           limit=self.limit,
                           url=self.site.url)
        elif self.action == "search_by_tag" and self.search_tag:
            return get_url(self.site.url, action=self.action,
                           context="brands",
                           tags=self.search_tag,
                           tagname=self.params.get('tagname'),
                           has_children=self.params.get('has_children'),
                           content=self.params.get('content'),
                           cache_expire=str(self.cache_expire),
                           offset=offset,
                           limit=self.limit,
                           url=self.site.url)
        elif self.action == "search_by_person" and self.search_person:
            return get_url(self.site.url, action=self.action,
                           context="brands",
                           persons=self.search_person,
                           cache_expire=str(self.cache_expire),
                           offset=offset,
                           limit=self.limit,
                           url=self.site.url)
        else:
            return get_url(self.site.url, action=self.action,
                           context="brands",
                           offset=offset,
                           cache_expire=str(self.cache_expire),
                           limit=self.limit,
                           url=self.site.url)

    def get_data_query(self):
        action = self.params.get('action', "")
        if action == "search_by_tag":
            if self.params.get('has_children', "False") == "True":
                tag_dict = self.get_tag_by_id(self.TAGS, int(self.params['tags']))
                if 'tags' in tag_dict:
                    return {'data': list(self.create_search_by_tag_lis(tag_dict['tags']))}
                return {}
        elif action == "search_by_person":
            if self.is_cache_available():
                return self.get_data_from_cache()
            else:
                person = self.site.request(self.get_load_url(), "json")
                roles = person['data'].get('brands', None)
                brands = {'data': []}
                if roles:
                    for r in roles:
                        brand = self.site.request(get_url(self.site.api_url + '/brands/' + str(r['id'])), "json")
                        brands['data'].append(brand['data'])

                return brands
        return super(Brand, self).get_data_query()

    def get_cache_filename(self):
        if "persons" in self.params:
            return os.path.join(self.site.data_path, "person_brands_%s.json" % self.params['persons'])
        else:
            return super(Brand, self).get_cache_filename()

    def get_load_url(self):
        if self.action == "search" and self.search_text:
            return get_url(self.site.api_url + '/msearch',
                           q=self.search_text,
                           limit=self.limit,
                           offset=self.offset)
        elif self.action == "search_by_tag" and self.search_tag:
            return get_url(self.site.api_url + '/brands',
                           tags=self.search_tag,
                           limit=self.limit,
                           offset=self.offset)
        elif self.action == "search_by_person" and self.search_person:
            return get_url(self.site.api_url + '/persons/' + self.search_person)
        else:
            return get_url(self.site.api_url + '/brands',
                           limit=self.limit,
                           offset=self.offset)

    def get_element_url(self, element, is_folder, is_music_folder):
        url_params = {'action': "play" if not is_folder else "load",
                      'url': self.site.url}

        if url_params['action'] == "play":
            url_params['context'] = "brands"
            url_params['brands'] = element['id']
        else:
            url_params['cache_expire'] = str(self.cache_expire)
            if is_music_folder:
                url_params['context'] = "audios"
                url_params['content'] = "musicvideos"
                if element.get('type', "") == "podcast":
                    url_params['rubrics'] = element['id']
                else:
                    url_params['brands'] = element['id']
            else:
                if element.get('type', "") == "person":
                    url_params['action'] = "search_by_person"
                    url_params['context'] = "brands"
                    url_params['content'] = "videos"
                    url_params['persons'] = element['id']
                else:
                    url_params['context'] = "videos"
                    url_params['content'] = "episodes"
                    url_params['brands'] = element['id']

        return get_url(self.site.url, **url_params)

    def play(self):

        videos = self.site.request(get_url(self.site.api_url + '/videos', brands=self.params['brands']),
                                   output="json")
        if len(videos.get('data', [])) > 0:
            spath = self.get_video_url(videos['data'][0]['sources'])

            self.play_url(spath, videos['data'][0])

    def create_element_li(self, element):

        if 'has_children' in self.params and self.params['has_children'] == "True":
            return super(Brand, self).create_element_li(element)
        else:

            is_folder, is_music_folder = self.is_folder(element)
            label = self.get_label(element)
            bp = self.parse_body(element)
            if 'picId' in element:
                picId = element.get('picId')
            elif 'picIds' in element:
                picId = element.get('picIds')[0] if len(element.get('picIds')) > 0 else ""
            else:
                picId = ""

            return {'id': element['id'],
                    'is_folder': is_folder,
                    'is_playable': not is_folder,
                    'label': "[B]%s[/B]" % label if is_folder else label,
                    'url': self.get_element_url(element, is_folder, is_music_folder),
                    'info': {'title': element.get('title'),
                             'sorttitle': element.get('title'),
                             'originaltitle': element.get('titleOrig', element.get('title')),
                             'genre': element.get('genre'),
                             'mediatype': "tvshow" if is_folder else "movie",
                             'year': element.get('productionYearStart'),
                             'country': self.get_country(element.get('countries')),
                             'mpaa': self.get_mpaa(element.get('ageRestrictions')),
                             'plot': bp.get('plot', element.get('anons')),
                             'artist': bp.get('cast', []),
                             'director': bp.get('director'),
                             'writer': bp.get('writer'),
                             'plotoutline': element.get('anons'),
                             'rating': element.get('rank'),
                             'dateadded': self.format_date(element.get('dateRec'))
                             },
                    'art': {'thumb': self.get_pic_from_id(picId, "lw"),
                            'icon': self.get_pic_from_id(picId, "lw"),
                            'fanart': self.get_pic_from_id(picId, "hd"),
                            'poster': self.get_pic_from_id(picId, "vhdr")
                            },
                    'cast': self.get_cast(element['id'], bp.get('cast', []))
                    }

    def enrich_info_tag(self, list_item, episode, brand):
        bp = self.parse_body(brand)
        list_item.setInfo("video", {"title": episode.get('combinedTitle'),
                                    "mediatype": "movie",
                                    "plot": episode.get('anons', bp.get('plot')),
                                    "year": brand.get('productionYearStart'),
                                    "country": self.get_country(brand.get('countries')),
                                    "genre": brand.get('genre'),
                                    "mpaa": self.get_mpaa(brand.get('ageRestrictions')),
                                    "director": bp.get('director'),
                                    "writer": bp.get('writer'),
                                    "rating": brand.get('rank')})

        list_item.setCast(self.get_cast(brand['id'], bp.get('cast', [])))

    def get_cast(self, brand_id, person_list):

        actors = []
        for person_name in person_list:
            actors.append({'name': person_name,
                           'thumbnail': persons.get_person_thumbnail(brand_id, person_name)})

        return actors

    def add_context_menu(self, category):
        pass
        # if category.get("type", "video") == "video":
        #     self.context_menu_items.append(("Set quality",
        #                                     "ActivateWindow(Dialog.OK)" ))

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
        if 'rank' in brand:
            rank = brand['rank']
            if rank:
                color = "FF00FF00" if rank >= 7.0 else "yellow" if (7.0 > rank >= 5.0) else "red"
                return "[COLOR %s][%s][/COLOR] %s" % (color, rank, brand['title'])
            else:
                return brand['title']
        else:
            return brand['title']

    @staticmethod
    def is_folder(element):

        if 'countVideos' in element or 'countAudioEpisodes' in element:
            is_folder = element['countVideos'] > 1 or element['countAudioEpisodes'] > 1
            is_music_folder = is_folder and element['countAudioEpisodes'] == element['countVideos']
        elif 'videos' in element:
            if len(element['videos']) >= 1:
                is_folder = len(element['videos']) > 1
                is_music_folder = False
            else:
                is_folder = True
                is_music_folder = True
        elif element.get('type', "") == "person":
            is_folder = True
            is_music_folder = False
        elif element.get('type', "") == "podcast":
            is_folder = True
            is_music_folder = True
        else:
            is_folder = False
            is_music_folder = False

        return is_folder, is_music_folder
